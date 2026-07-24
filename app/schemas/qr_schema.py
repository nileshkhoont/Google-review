"""Pydantic schemas for QR code responses."""

from datetime import datetime

from pydantic import BaseModel


class QRResponse(BaseModel):
    id: str
    business_id: str
    file_path: str
    target_url: str
    created_at: datetime
    updated_at: datetime
