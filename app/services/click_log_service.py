"""Business logic for recording and reading button-click activity logs."""

from fastapi import HTTPException, status

from app.models.click_log import build_click_log_document
from app.repositories.business_repository import BusinessRepository
from app.repositories.click_log_repository import ClickLogRepository
from app.utils.helper import serialize_doc


class ClickLogService:
    def __init__(self, click_log_repo: ClickLogRepository, business_repo: BusinessRepository):
        self.click_log_repo = click_log_repo
        self.business_repo = business_repo

    async def record_click(self, slug: str, page: str, action: str) -> None:
        business = (
            await self.business_repo.get_by_social_slug(slug)
            if page == "social"
            else await self.business_repo.get_by_slug(slug)
        )
        if not business:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found.")

        doc = build_click_log_document(
            business_id=business["_id"],
            business_name=business["business_name"],
            page=page,
            action=action,
        )
        await self.click_log_repo.create(doc)

    async def get_business_summary(self, owner_id: str, business_id: str) -> list[dict]:
        business = await self.business_repo.get_by_id(business_id)
        if not business:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found.")
        if business["owner_id"] != owner_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")

        rows = await self.click_log_repo.aggregate_action_counts(business_id)
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
