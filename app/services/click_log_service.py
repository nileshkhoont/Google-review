"""Business logic for recording and reading button-click activity logs."""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.models.click_log import build_click_log_document
from app.repositories.business_repository import BusinessRepository
from app.repositories.click_log_repository import ClickLogRepository
from app.utils.helper import serialize_doc

# India Standard Time has no DST, so a fixed UTC+5:30 offset is always
# correct (unlike most timezones, this doesn't need the IANA tzdata).
IST = timezone(timedelta(hours=5, minutes=30))


def _parse_ist_day(date_str: str) -> datetime:
    """Parses a "YYYY-MM-DD" calendar date (as picked in the admin's IST-facing UI)."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=IST)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date, expected YYYY-MM-DD.")


def _ist_range_to_utc(start_date: str | None, end_date: str | None) -> tuple[datetime, datetime] | tuple[None, None]:
    """
    Turns an inclusive "YYYY-MM-DD" to "YYYY-MM-DD" IST calendar-date range
    into the [start, end) UTC datetime range covering it, since
    `created_at` is stored in UTC but displayed to admins in IST. A single
    open end defaults to the other end, so picking just one date scopes to
    that single day.
    """
    if not start_date and not end_date:
        return None, None
    start_date = start_date or end_date
    end_date = end_date or start_date

    start = _parse_ist_day(start_date).astimezone(timezone.utc)
    end = _parse_ist_day(end_date).astimezone(timezone.utc) + timedelta(days=1)
    if start >= end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must not be after end_date.")
    return start, end


class ClickLogService:
    def __init__(self, click_log_repo: ClickLogRepository, business_repo: BusinessRepository):
        self.click_log_repo = click_log_repo
        self.business_repo = business_repo

    async def record_click(self, slug: str, page: str, action: str) -> None:
        if page == "social":
            business = await self.business_repo.get_by_social_slug(slug)
        elif page == "combined":
            business = await self.business_repo.get_by_combined_slug(slug)
        else:
            business = await self.business_repo.get_by_slug(slug)
        if not business:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found.")

        doc = build_click_log_document(
            business_id=business["_id"],
            business_name=business["business_name"],
            page=page,
            action=action,
        )
        await self.click_log_repo.create(doc)

    async def get_business_summary(
        self,
        owner_id: str,
        business_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        business = await self.business_repo.get_by_id(business_id)
        if not business:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found.")
        if business["owner_id"] != owner_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")

        start, end = _ist_range_to_utc(start_date, end_date)
        rows = await self.click_log_repo.aggregate_action_counts(business_id, start=start, end=end)
        return [
            {
                "page": row["_id"]["page"],
                "action": row["_id"]["action"],
                "count": row["count"],
                "last_clicked_at": row["last_clicked_at"],
            }
            for row in rows
        ]

    async def get_global_logs(
        self, limit: int = 50, skip: int = 0, business_id: str | None = None
    ) -> dict:
        docs = await self.click_log_repo.list_recent(limit=limit, skip=skip, business_id=business_id)
        total = await self.click_log_repo.count(business_id=business_id)
        return {"items": [serialize_doc(d) for d in docs], "total": total}

    async def get_business_totals(self) -> list[dict]:
        rows = await self.click_log_repo.aggregate_business_totals()
        return [
            {
                "business_id": row["_id"],
                "business_name": row["business_name"],
                "total_clicks": row["total_clicks"],
                "last_activity_at": row["last_activity_at"],
            }
            for row in rows
        ]
