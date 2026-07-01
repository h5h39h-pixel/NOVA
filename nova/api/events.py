# -*- coding: utf-8 -*-
"""Event-log routes — search/filter the unified event log, get a single event (with stack trace +
context), timeline stats, and clear. Backed by nova.core.eventlog."""
from fastapi import APIRouter
from nova.core import eventlog

router = APIRouter()


@router.get("/api/events")
def api_events(level: str = "", category: str = "", source: str = "", actor: str = "",
               status: str = "", q: str = "", since: float = None, until: float = None,
               limit: int = 200, offset: int = 0):
    return eventlog.query(level=level, category=category, source=source, actor=actor,
                          status=status, q=q, since=since, until=until,
                          limit=min(int(limit), 1000), offset=int(offset))


@router.get("/api/events/stats")
def api_events_stats(hours: int = 24, buckets: int = 48):
    return eventlog.stats(hours=int(hours), buckets=min(int(buckets), 200))


@router.get("/api/events/meta")
def api_events_meta():
    return {"levels": list(eventlog.LEVELS), "categories": list(eventlog.CATEGORIES)}


@router.get("/api/events/{event_id}")
def api_event_one(event_id: int):
    e = eventlog.get(event_id)
    return e or {"error": "not found"}


@router.delete("/api/events")
def api_events_clear():
    eventlog.clear()
    return {"ok": True}
