import pytest
from datetime import datetime, timedelta

from src.calendar_module import (
    Event,
    Reminder,
    EventStatus,
    RecurrenceFrequency,
    RecurrenceRule,
    CalendarManager,
    AIScheduler,
    ReminderService,
)


def test_event_creation():
    now = datetime.now()
    event = Event(
        event_id="test-1",
        title="Test Event",
        description="Test Description",
        start_time=now,
        end_time=now + timedelta(hours=1),
    )
    
    assert event.event_id == "test-1"
    assert event.title == "Test Event"
    assert event.status == EventStatus.CONFIRMED
    assert len(event.attendees) == 0


def test_event_serialization():
    now = datetime.now()
    event = Event(
        event_id="test-2",
        title="Test Event",
        description="Test Description",
        start_time=now,
        end_time=now + timedelta(hours=1),
        location="Test Location",
        attendees=["user1@example.com"],
    )
    
    event_dict = event.to_dict()
    assert event_dict["event_id"] == "test-2"
    assert event_dict["title"] == "Test Event"
    assert event_dict["location"] == "Test Location"
    
    restored_event = Event.from_dict(event_dict)
    assert restored_event.event_id == event.event_id
    assert restored_event.title == event.title


def test_event_invalid_times():
    now = datetime.now()
    with pytest.raises(ValueError, match="Start time must be before end time"):
        Event(
            event_id="test-3",
            title="Invalid Event",
            description="Invalid",
            start_time=now + timedelta(hours=1),
            end_time=now,
        )


def test_reminder_creation():
    now = datetime.now()
    reminder = Reminder(
        reminder_id="reminder-1",
        event_id="event-1",
        remind_at=now + timedelta(minutes=15),
        method="email",
    )
    
    assert reminder.reminder_id == "reminder-1"
    assert reminder.method == "email"
    assert not reminder.sent


def test_reminder_invalid_method():
    now = datetime.now()
    with pytest.raises(ValueError, match="Invalid reminder method"):
        Reminder(
            reminder_id="reminder-2",
            event_id="event-1",
            remind_at=now + timedelta(minutes=15),
            method="invalid",
        )


def test_recurrence_rule():
    rule = RecurrenceRule(
        frequency=RecurrenceFrequency.WEEKLY,
        interval=2,
        count=10,
    )
    
    assert rule.frequency == RecurrenceFrequency.WEEKLY
    assert rule.interval == 2
    assert rule.count == 10
    
    rule_dict = rule.to_dict()
    restored_rule = RecurrenceRule.from_dict(rule_dict)
    assert restored_rule.frequency == rule.frequency
    assert restored_rule.interval == rule.interval


def test_calendar_manager_create_event():
    manager = CalendarManager(data_dir="data/test_calendar")
    
    now = datetime.now()
    event_data = {
        "title": "Test Meeting",
        "description": "Test meeting description",
        "start_time": now.isoformat(),
        "end_time": (now + timedelta(hours=1)).isoformat(),
        "location": "Conference Room",
    }
    
    event = manager.create_event(event_data)
    assert event.title == "Test Meeting"
    assert event.location == "Conference Room"
    assert event.event_id in manager.events


def test_calendar_manager_update_event():
    manager = CalendarManager(data_dir="data/test_calendar")
    
    now = datetime.now()
    event_data = {
        "title": "Original Title",
        "description": "Original Description",
        "start_time": now.isoformat(),
        "end_time": (now + timedelta(hours=1)).isoformat(),
    }
    
    event = manager.create_event(event_data)
    
    updated_event = manager.update_event(
        event.event_id,
        {"title": "Updated Title", "location": "New Location"},
    )
    
    assert updated_event.title == "Updated Title"
    assert updated_event.location == "New Location"


def test_calendar_manager_delete_event():
    manager = CalendarManager(data_dir="data/test_calendar")
    
    now = datetime.now()
    event_data = {
        "title": "Event to Delete",
        "description": "Will be deleted",
        "start_time": now.isoformat(),
        "end_time": (now + timedelta(hours=1)).isoformat(),
    }
    
    event = manager.create_event(event_data)
    assert event.event_id in manager.events
    
    success = manager.delete_event(event.event_id)
    assert success
    assert event.event_id not in manager.events


def test_calendar_manager_search_events():
    manager = CalendarManager(data_dir="data/test_calendar")
    
    now = datetime.now()
    
    manager.create_event({
        "title": "Python Workshop",
        "description": "Learn Python",
        "start_time": now.isoformat(),
        "end_time": (now + timedelta(hours=1)).isoformat(),
    })
    
    manager.create_event({
        "title": "JavaScript Training",
        "description": "Learn JavaScript",
        "start_time": (now + timedelta(days=1)).isoformat(),
        "end_time": (now + timedelta(days=1, hours=1)).isoformat(),
    })
    
    results = manager.search_events("Python")
    assert len(results) >= 1
    assert any("Python" in e.title for e in results)


def test_calendar_manager_statistics():
    manager = CalendarManager(data_dir="data/test_calendar")
    
    now = datetime.now()
    
    for i in range(3):
        manager.create_event({
            "title": f"Event {i}",
            "description": f"Description {i}",
            "start_time": (now + timedelta(days=i)).isoformat(),
            "end_time": (now + timedelta(days=i, hours=1)).isoformat(),
        })
    
    stats = manager.get_statistics()
    assert stats["total_events"] >= 3
    assert "confirmed" in stats
    assert "upcoming" in stats


@pytest.mark.asyncio
async def test_ai_scheduler_suggest_times():
    manager = CalendarManager(data_dir="data/test_calendar")
    scheduler = AIScheduler(manager)
    
    suggestions = await scheduler.suggest_times(60, days_ahead=7)
    assert isinstance(suggestions, list)
    assert len(suggestions) <= 10


@pytest.mark.asyncio
async def test_ai_scheduler_analyze_calendar():
    manager = CalendarManager(data_dir="data/test_calendar")
    scheduler = AIScheduler(manager)
    
    analysis = await scheduler.analyze_calendar()
    assert "total_events" in analysis
    assert "average_duration_minutes" in analysis


@pytest.mark.asyncio
async def test_reminder_service_schedule():
    service = ReminderService()
    
    now = datetime.now()
    reminder = Reminder(
        reminder_id="test-reminder",
        event_id="test-event",
        remind_at=now + timedelta(minutes=30),
        method="push",
    )
    
    success = await service.schedule_reminder(reminder)
    assert success
    assert service.get_scheduled_count() == 1
    
    await service.cancel_reminder(reminder.reminder_id)
    assert service.get_scheduled_count() == 0
