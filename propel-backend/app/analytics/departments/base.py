from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy.orm import Session

from app.analytics.contracts import DepartmentAnalyticsDefinition, DepartmentAnalyticsOverview
from app.db.models.user import User


class DepartmentAnalyticsAdapter(ABC):
    definition: DepartmentAnalyticsDefinition

    @abstractmethod
    def build_overview(
        self,
        db: Session,
        current_user: User,
        team: Optional[str] = None,
        employee_id: Optional[int] = None,
    ) -> DepartmentAnalyticsOverview:
        raise NotImplementedError
