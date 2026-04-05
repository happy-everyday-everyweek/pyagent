import logging
from collections import defaultdict
from datetime import datetime, timedelta

from src.calendar.event import Event, EventStatus
from src.calendar.manager import CalendarManager

logger = logging.getLogger(__name__)


class AIScheduler:
    def __init__(self, calendar_manager: CalendarManager):
        self.calendar_manager = calendar_manager

    async def analyze_calendar(self) -> dict:
        events = self.calendar_manager.list_events()

        if not events:
            return {
                "total_events": 0,
                "average_duration_minutes": 0,
                "busiest_days": [],
                "common_times": [],
                "meeting_patterns": {},
            }

        total_duration = 0
        day_counts = defaultdict(int)
        hour_counts = defaultdict(int)
        location_counts = defaultdict(int)

        for event in events:
            if event.status == EventStatus.CANCELLED:
                continue

            duration = (event.end_time - event.start_time).total_seconds() / 60
            total_duration += duration

            day_counts[event.start_time.strftime("%Y-%m-%d")] += 1
            hour_counts[event.start_time.hour] += 1

            if event.location:
                location_counts[event.location] += 1

        avg_duration = total_duration / len(events) if events else 0

        busiest_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        common_times = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_events": len(events),
            "average_duration_minutes": round(avg_duration, 2),
            "busiest_days": busiest_days,
            "common_times": common_times,
            "common_locations": dict(sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
        }

    async def suggest_times(
        self,
        duration_minutes: int,
        preferences: dict | None = None,
        days_ahead: int = 7,
    ) -> list[dict]:
        preferences = preferences or {}
        work_start_hour = preferences.get("work_start_hour", 9)
        work_end_hour = preferences.get("work_end_hour", 18)
        preferred_days = preferences.get("preferred_days", [0, 1, 2, 3, 4])

        now = datetime.now()
        end_date = now + timedelta(days=days_ahead)

        existing_events = self.calendar_manager.list_events(now, end_date)

        busy_times = []
        for event in existing_events:
            if event.status != EventStatus.CANCELLED:
                busy_times.append((event.start_time, event.end_time))

        suggestions = []
        current_date = now.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)

        while current_date < end_date:
            if current_date.weekday() in preferred_days:
                slot_start = current_date.replace(hour=work_start_hour)
                slot_end = current_date.replace(hour=work_end_hour)

                current_slot = slot_start
                while current_slot < slot_end:
                    slot_end_time = current_slot + timedelta(minutes=duration_minutes)

                    if slot_end_time <= slot_end:
                        is_free = True
                        for busy_start, busy_end in busy_times:
                            if current_slot < busy_end and slot_end_time > busy_start:
                                is_free = False
                                break

                        if is_free:
                            suggestions.append({
                                "start_time": current_slot.isoformat(),
                                "end_time": slot_end_time.isoformat(),
                                "date": current_slot.strftime("%Y-%m-%d"),
                                "day_of_week": current_slot.strftime("%A"),
                            })

                            if len(suggestions) >= 10:
                                return suggestions

                    current_slot += timedelta(minutes=30)

            current_date += timedelta(days=1)

        return suggestions

    async def auto_schedule(self, task_description: str) -> Event | None:
        duration_minutes = 60
        preferences = {}

        if "quick" in task_description.lower() or "short" in task_description.lower():
            duration_minutes = 30
        elif "long" in task_description.lower() or "extended" in task_description.lower():
            duration_minutes = 120

        if "morning" in task_description.lower():
            preferences["work_start_hour"] = 8
            preferences["work_end_hour"] = 12
        elif "afternoon" in task_description.lower():
            preferences["work_start_hour"] = 13
            preferences["work_end_hour"] = 18

        suggestions = await self.suggest_times(duration_minutes, preferences)

        if not suggestions:
            logger.warning("No available time slots found for auto-scheduling")
            return None

        best_slot = suggestions[0]

        event_data = {
            "title": f"Auto-scheduled: {task_description}",
            "description": task_description,
            "start_time": best_slot["start_time"],
            "end_time": best_slot["end_time"],
        }

        event = self.calendar_manager.create_event(event_data)
        logger.info(f"Auto-scheduled event {event.event_id} for {best_slot['start_time']}")

        return event

    async def detect_conflicts(self, new_event: Event) -> list[Event]:
        conflicts = []

        for event in self.calendar_manager.events.values():
            if event.event_id == new_event.event_id:
                continue

            if event.status == EventStatus.CANCELLED:
                continue

            if new_event.start_time < event.end_time and new_event.end_time > event.start_time:
                conflicts.append(event)

        return conflicts

    async def find_free_slots(
        self,
        date: datetime,
        duration_minutes: int = 60,
        work_start_hour: int = 9,
        work_end_hour: int = 18,
    ) -> list[dict]:
        day_start = date.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=work_end_hour, minute=0, second=0, microsecond=0)

        day_events = self.calendar_manager.list_events(day_start, day_end)

        busy_times = []
        for event in day_events:
            if event.status != EventStatus.CANCELLED:
                busy_times.append((event.start_time, event.end_time))

        busy_times.sort(key=lambda x: x[0])

        free_slots = []
        current_time = day_start

        for busy_start, busy_end in busy_times:
            if current_time < busy_start:
                slot_duration = (busy_start - current_time).total_seconds() / 60
                if slot_duration >= duration_minutes:
                    free_slots.append({
                        "start_time": current_time.isoformat(),
                        "end_time": busy_start.isoformat(),
                        "duration_minutes": int(slot_duration),
                    })

            current_time = max(current_time, busy_end)

        if current_time < day_end:
            slot_duration = (day_end - current_time).total_seconds() / 60
            if slot_duration >= duration_minutes:
                free_slots.append({
                    "start_time": current_time.isoformat(),
                    "end_time": day_end.isoformat(),
                    "duration_minutes": int(slot_duration),
                })

        return free_slots

    async def optimize_schedule(self, date: datetime) -> dict:
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=23, minute=59, second=59, microsecond=0)

        day_events = self.calendar_manager.list_events(day_start, day_end)

        active_events = [e for e in day_events if e.status != EventStatus.CANCELLED]

        if not active_events:
            return {
                "date": date.strftime("%Y-%m-%d"),
                "total_events": 0,
                "total_duration_minutes": 0,
                "gaps": [],
                "suggestions": ["No events scheduled for this day"],
            }

        total_duration = sum(
            (e.end_time - e.start_time).total_seconds() / 60 for e in active_events
        )

        gaps = await self.find_free_slots(date, 30)

        suggestions = []
        if len(gaps) > 3:
            suggestions.append("Consider filling some gaps with shorter meetings")
        if total_duration > 480:
            suggestions.append("You have more than 8 hours of meetings, consider rescheduling some")

        return {
            "date": date.strftime("%Y-%m-%d"),
            "total_events": len(active_events),
            "total_duration_minutes": int(total_duration),
            "gaps": gaps,
            "suggestions": suggestions,
        }
