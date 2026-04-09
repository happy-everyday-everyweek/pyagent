from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.calendar_module import AIScheduler, CalendarManager

router = APIRouter(prefix="/calendar", tags=["calendar"])

calendar_manager = CalendarManager()
ai_scheduler = AIScheduler(calendar_manager)


class EventCreate(BaseModel):
    title: str
    description: str = ""
    start_time: str
    end_time: str
    location: str = ""
    attendees: list[str] = Field(default_factory=list)
    status: str = "confirmed"


class EventUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = None
    attendees: list[str] | None = None
    status: str | None = None


class ReminderCreate(BaseModel):
    remind_at: str
    method: str


class SuggestTimesRequest(BaseModel):
    duration_minutes: int = 60
    preferences: dict | None = None
    days_ahead: int = 7


class AutoScheduleRequest(BaseModel):
    task_description: str


@router.post("/events", response_model=dict)
async def create_event(event_data: EventCreate):
    try:
        event_dict = event_data.dict()
        event = calendar_manager.create_event(event_dict)
        return {"success": True, "event": event.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/events/{event_id}", response_model=dict)
async def get_event(event_id: str):
    event = calendar_manager.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"success": True, "event": event.to_dict()}


@router.put("/events/{event_id}", response_model=dict)
async def update_event(event_id: str, event_data: EventUpdate):
    event = calendar_manager.update_event(event_id, event_data.dict(exclude_none=True))
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"success": True, "event": event.to_dict()}


@router.delete("/events/{event_id}")
async def delete_event(event_id: str):
    success = calendar_manager.delete_event(event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"success": True, "message": f"Event {event_id} deleted"}


@router.get("/events", response_model=dict)
async def list_events(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
):
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None

    events = calendar_manager.list_events(start, end)
    return {
        "success": True,
        "events": [e.to_dict() for e in events],
        "count": len(events),
    }


@router.get("/events/search", response_model=dict)
async def search_events(query: str = Query(..., min_length=1)):
    events = calendar_manager.search_events(query)
    return {
        "success": True,
        "events": [e.to_dict() for e in events],
        "count": len(events),
    }


@router.post("/events/{event_id}/reminders", response_model=dict)
async def add_reminder(event_id: str, reminder_data: ReminderCreate):
    reminder = calendar_manager.add_reminder(event_id, reminder_data.dict())
    if not reminder:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"success": True, "reminder": reminder.to_dict()}


@router.delete("/events/{event_id}/reminders/{reminder_id}")
async def remove_reminder(event_id: str, reminder_id: str):
    success = calendar_manager.remove_reminder(event_id, reminder_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event or reminder not found")
    return {"success": True, "message": f"Reminder {reminder_id} removed"}


@router.get("/statistics", response_model=dict)
async def get_statistics():
    stats = calendar_manager.get_statistics()
    return {"success": True, "statistics": stats}


@router.post("/ai/suggest-times", response_model=dict)
async def suggest_times(request: SuggestTimesRequest):
    suggestions = await ai_scheduler.suggest_times(
        request.duration_minutes, request.preferences, request.days_ahead
    )
    return {
        "success": True,
        "suggestions": suggestions,
        "count": len(suggestions),
    }


@router.post("/ai/auto-schedule", response_model=dict)
async def auto_schedule(request: AutoScheduleRequest):
    event = await ai_scheduler.auto_schedule(request.task_description)
    if not event:
        raise HTTPException(
            status_code=400, detail="No available time slots found"
        )
    return {"success": True, "event": event.to_dict()}


@router.post("/ai/analyze", response_model=dict)
async def analyze_calendar():
    analysis = await ai_scheduler.analyze_calendar()
    return {"success": True, "analysis": analysis}


@router.post("/ai/detect-conflicts/{event_id}", response_model=dict)
async def detect_conflicts(event_id: str):
    event = calendar_manager.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    conflicts = await ai_scheduler.detect_conflicts(event)
    return {
        "success": True,
        "event_id": event_id,
        "conflicts": [e.to_dict() for e in conflicts],
        "has_conflicts": len(conflicts) > 0,
    }


@router.get("/ai/free-slots", response_model=dict)
async def find_free_slots(
    date: str = Query(...),
    duration_minutes: int = Query(60),
    work_start_hour: int = Query(9),
    work_end_hour: int = Query(18),
):
    date_obj = datetime.fromisoformat(date)
    slots = await ai_scheduler.find_free_slots(
        date_obj, duration_minutes, work_start_hour, work_end_hour
    )
    return {
        "success": True,
        "date": date,
        "free_slots": slots,
        "count": len(slots),
    }


@router.get("/ai/optimize", response_model=dict)
async def optimize_schedule(date: str = Query(...)):
    date_obj = datetime.fromisoformat(date)
    optimization = await ai_scheduler.optimize_schedule(date_obj)
    return {"success": True, "optimization": optimization}
