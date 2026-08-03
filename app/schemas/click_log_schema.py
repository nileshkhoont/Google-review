"""Pydantic schemas for button-click activity logging."""

from datetime import datetime

from pydantic import BaseModel, Field


class TrackClickRequest(BaseModel):
    action: str = Field(min_length=1, max_length=100)


class ClickLogEntry(BaseModel):
    id: str
    business_id: str
    business_name: str
    page: str
    action: str
    created_at: datetime


class ActionCount(BaseModel):
    page: str
    action: str
    count: int
    last_clicked_at: datetime


class BusinessClickSummary(BaseModel):
    business_id: str
    business_name: str
    total_clicks: int
    last_activity_at: datetime


class ClickLogListResponse(BaseModel):
    items: list[ClickLogEntry]
    total: int
