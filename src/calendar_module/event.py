import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EventStatus(Enum):
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"


class RecurrenceFrequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass
class RecurrenceRule:
    frequency: RecurrenceFrequency
    interval: int = 1
    count: int | None = None
    until: datetime | None = None
    by_day: list[str] = field(default_factory=list)
    by_month: list[int] = field(default_factory=list)
    by_month_day: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "frequency": self.frequency.value,
            "interval": self.interval,
            "count": self.count,
            "until": self.until.isoformat() if self.until else None,
            "by_day": self.by_day,
            "by_month": self.by_month,
            "by_month_day": self.by_month_day,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecurrenceRule":
        return cls(
            frequency=RecurrenceFrequency(data["frequency"]),
            interval=data.get("interval", 1),
            count=data.get("count"),
            until=datetime.fromisoformat(data["until"]) if data.get("until") else None,
            by_day=data.get("by_day", []),
            by_month=data.get("by_month", []),
            by_month_day=data.get("by_month_day", []),
        )


@dataclass
class Reminder:
    reminder_id: str
    event_id: str
    remind_at: datetime
    method: str
    sent: bool = False

    def __post_init__(self):
        if self.method not in ["email", "push", "sms"]:
            raise ValueError(f"Invalid reminder method: {self.method}")

    def to_dict(self) -> dict:
        return {
            "reminder_id": self.reminder_id,
            "event_id": self.event_id,
            "remind_at": self.remind_at.isoformat(),
            "method": self.method,
            "sent": self.sent,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Reminder":
        return cls(
            reminder_id=data["reminder_id"],
            event_id=data["event_id"],
            remind_at=datetime.fromisoformat(data["remind_at"]),
            method=data["method"],
            sent=data.get("sent", False),
        )


@dataclass
class Event:
    event_id: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    location: str = ""
    attendees: list[str] = field(default_factory=list)
    reminders: list[Reminder] = field(default_factory=list)
    recurrence: RecurrenceRule | None = None
    status: EventStatus = EventStatus.CONFIRMED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if self.start_time >= self.end_time:
            raise ValueError("Start time must be before end time")

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "location": self.location,
            "attendees": self.attendees,
            "reminders": [r.to_dict() for r in self.reminders],
            "recurrence": self.recurrence.to_dict() if self.recurrence else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        return cls(
            event_id=data["event_id"],
            title=data["title"],
            description=data["description"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            location=data.get("location", ""),
            attendees=data.get("attendees", []),
            reminders=[Reminder.from_dict(r) for r in data.get("reminders", [])],
            recurrence=RecurrenceRule.from_dict(data["recurrence"])
            if data.get("recurrence")
            else None,
            status=EventStatus(data.get("status", "confirmed")),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())

    def update_timestamp(self):
        self.updated_at = datetime.now()
