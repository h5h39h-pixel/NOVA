# -*- coding: utf-8 -*-
"""Proactive intelligence routes — insight tips, the daily briefing, and the co-pilot
suggestion. Logic lives in nova.services.insights."""
from fastapi import APIRouter
from nova.services.insights import insights, build_briefing, copilot

router = APIRouter()

@router.get("/api/insights")
def api_insights(): return insights()

@router.get("/api/briefing")
def api_briefing(): return build_briefing()

@router.get("/api/copilot")
def api_copilot(): return copilot()
