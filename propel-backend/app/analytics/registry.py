from __future__ import annotations

from app.analytics.departments.base import DepartmentAnalyticsAdapter
from app.analytics.departments.sales import SalesAnalyticsAdapter
from app.analytics.departments.software import SoftwareAnalyticsAdapter


_ADAPTERS: dict[str, DepartmentAnalyticsAdapter] = {
    "software": SoftwareAnalyticsAdapter(),
    "sales": SalesAnalyticsAdapter(),
}


def get_department_adapter(key: str) -> DepartmentAnalyticsAdapter:
    normalized = (key or "").strip().lower()
    if normalized not in _ADAPTERS:
        raise KeyError(normalized)
    return _ADAPTERS[normalized]


def list_department_adapters() -> list[DepartmentAnalyticsAdapter]:
    return list(_ADAPTERS.values())
