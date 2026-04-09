import asyncio
import json
import logging
import os
import uuid
from datetime import datetime

from .event import Event, EventStatus, Reminder
from .reminder import ReminderService

logger = logging.getLogger(__name__)


class CalendarManager:
    def __init__(self, data_dir: str = "data/calendar"):
        self.data_dir = data_dir
        self.events_file = os.path.join(data_dir, "events.json")
        self.events: dict[str, Event] = {}
        self.reminder_service = ReminderService()
        self._ensure_data_dir()
        self._load_events()

    def _ensure_data_dir(self):
        os.makedirs(self.data_dir, exist_ok=True)

    def _load_events(self):
        if os.path.exists(self.events_file):
            try:
                with open(self.events_file, encoding="utf-8") as f:
                    data = json.load(f)
                    self.events = {
                        event_id: Event.from_dict(event_data)
                        for event_id, event_data in data.items()
                    }
                logger.info(f"Loaded {len(self.events)} events from storage")
            except Exception as e:
                logger.error(f"Failed to load events: {e}")
                self.events = {}

    def _save_events(self):
        try:
            data = {
                event_id: event.to_dict() for event_id, event in self.events.items()
            }
            with open(self.events_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.events)} events to storage")
        except Exception as e:
            logger.error(f"Failed to save events: {e}")

    def create_event(self, event_data: dict) -> Event:
        event_id = event_data.get("event_id", Event.generate_id())

        if event_id in self.events:
            raise ValueError(f"Event with ID {event_id} already exists")

        event = Event(
            event_id=event_id,
            title=event_data["title"],
            description=event_data.get("description", ""),
            start_time=event_data["start_time"]
            if isinstance(event_data["start_time"], datetime)
            else datetime.fromisoformat(event_data["start_time"]),
            end_time=event_data["end_time"]
            if isinstance(event_data["end_time"], datetime)
            else datetime.fromisoformat(event_data["end_time"]),
            location=event_data.get("location", ""),
            attendees=event_data.get("attendees", []),
            reminders=event_data.get("reminders", []),
            recurrence=event_data.get("recurrence"),
            status=EventStatus(event_data.get("status", "confirmed")),
        )

        self.events[event_id] = event
        self._save_events()

        for reminder in event.reminders:
            asyncio.create_task(self.reminder_service.schedule_reminder(reminder))

        logger.info(f"Created event {event_id}: {event.title}")
        return event

    def update_event(self, event_id: str, event_data: dict) -> Event | None:
        if event_id not in self.events:
            logger.warning(f"Event {event_id} not found")
            return None

        event = self.events[event_id]

        if "title" in event_data:
            event.title = event_data["title"]
        if "description" in event_data:
            event.description = event_data["description"]
        if "start_time" in event_data:
            event.start_time = (
                event_data["start_time"]
                if isinstance(event_data["start_time"], datetime)
                else datetime.fromisoformat(event_data["start_time"])
            )
        if "end_time" in event_data:
            event.end_time = (
                event_data["end_time"]
                if isinstance(event_data["end_time"], datetime)
                else datetime.fromisoformat(event_data["end_time"])
            )
        if "location" in event_data:
            event.location = event_data["location"]
        if "attendees" in event_data:
            event.attendees = event_data["attendees"]
        if "status" in event_data:
            event.status = EventStatus(event_data["status"])

        event.update_timestamp()
        self._save_events()

        logger.info(f"Updated event {event_id}")
        return event

    def delete_event(self, event_id: str) -> bool:
        if event_id not in self.events:
            logger.warning(f"Event {event_id} not found")
            return False

        event = self.events[event_id]

        for reminder in event.reminders:
            asyncio.create_task(self.reminder_service.cancel_reminder(reminder.reminder_id))

        del self.events[event_id]
        self._save_events()

        logger.info(f"Deleted event {event_id}")
        return True

    def get_event(self, event_id: str) -> Event | None:
        return self.events.get(event_id)

    def list_events(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[Event]:
        events = list(self.events.values())

        if start_date:
            events = [e for e in events if e.start_time >= start_date]

        if end_date:
            events = [e for e in events if e.end_time <= end_date]

        events.sort(key=lambda e: e.start_time)
        return events

    def search_events(self, query: str) -> list[Event]:
        query_lower = query.lower()
        results = []

        for event in self.events.values():
            if (
                query_lower in event.title.lower()
                or query_lower in event.description.lower()
                or query_lower in event.location.lower()
                or any(query_lower in attendee.lower() for attendee in event.attendees)
            ):
                results.append(event)

        results.sort(key=lambda e: e.start_time)
        return results

    def add_reminder(self, event_id: str, reminder_data: dict) -> Reminder | None:
        event = self.get_event(event_id)
        if not event:
            logger.warning(f"Event {event_id} not found")
            return None

        reminder = Reminder(
            reminder_id=reminder_data.get("reminder_id", str(uuid.uuid4())),
            event_id=event_id,
            remind_at=reminder_data["remind_at"]
            if isinstance(reminder_data["remind_at"], datetime)
            else datetime.fromisoformat(reminder_data["remind_at"]),
            method=reminder_data["method"],
        )

        event.reminders.append(reminder)
        event.update_timestamp()
        self._save_events()

        asyncio.create_task(self.reminder_service.schedule_reminder(reminder))

        logger.info(f"Added reminder {reminder.reminder_id} to event {event_id}")
        return reminder

    def remove_reminder(self, event_id: str, reminder_id: str) -> bool:
        event = self.get_event(event_id)
        if not event:
            logger.warning(f"Event {event_id} not found")
            return False

        for i, reminder in enumerate(event.reminders):
            if reminder.reminder_id == reminder_id:
                asyncio.create_task(self.reminder_service.cancel_reminder(reminder_id))
                event.reminders.pop(i)
                event.update_timestamp()
                self._save_events()
                logger.info(f"Removed reminder {reminder_id} from event {event_id}")
                return True

        logger.warning(f"Reminder {reminder_id} not found in event {event_id}")
        return False

    def get_statistics(self) -> dict:
        total_events = len(self.events)
        confirmed = sum(1 for e in self.events.values() if e.status == EventStatus.CONFIRMED)
        tentative = sum(1 for e in self.events.values() if e.status == EventStatus.TENTATIVE)
        cancelled = sum(1 for e in self.events.values() if e.status == EventStatus.CANCELLED)

        now = datetime.now()
        upcoming = sum(1 for e in self.events.values() if e.start_time > now and e.status != EventStatus.CANCELLED)
        past = sum(1 for e in self.events.values() if e.end_time <= now)

        return {
            "total_events": total_events,
            "confirmed": confirmed,
            "tentative": tentative,
            "cancelled": cancelled,
            "upcoming": upcoming,
            "past": past,
        }
