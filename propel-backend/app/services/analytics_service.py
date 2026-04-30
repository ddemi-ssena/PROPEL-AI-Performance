from __future__ import annotations

from dataclasses import asdict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.analytics import get_department_adapter, list_department_adapters
from app.schemas.analytics import DepartmentAnalyticsConfigResponse, DepartmentAnalyticsOverviewResponse


class AnalyticsService:
    @staticmethod
    def list_department_configs() -> list[DepartmentAnalyticsConfigResponse]:
        configs: list[DepartmentAnalyticsConfigResponse] = []
        for adapter in list_department_adapters():
            definition = adapter.definition
            configs.append(
                DepartmentAnalyticsConfigResponse(
                    key=definition.key,
                    label=definition.label,
                    description=definition.description,
                    readiness_status=definition.readiness_status,
                    supports_live_data=definition.supports_live_data,
                    planned_targets=definition.planned_targets,
                    supported_teams=definition.supported_teams,
                    layers=[
                        {
                            "key": layer.key,
                            "title": layer.title,
                            "summary": layer.summary,
                        }
                        for layer in definition.layers
                    ],
                )
            )
        return configs

    @staticmethod
    def get_department_overview(
        db: Session,
        current_user,
        department_key: str,
        team: str | None = None,
        employee_id: int | None = None,
    ) -> DepartmentAnalyticsOverviewResponse:
        try:
            adapter = get_department_adapter(department_key)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Bilinmeyen analytics departmani: {department_key}") from exc

        overview = adapter.build_overview(
            db=db,
            current_user=current_user,
            team=team,
            employee_id=employee_id,
        )

        return DepartmentAnalyticsOverviewResponse(
            definition=DepartmentAnalyticsConfigResponse(
                key=overview.definition.key,
                label=overview.definition.label,
                description=overview.definition.description,
                readiness_status=overview.definition.readiness_status,
                supports_live_data=overview.definition.supports_live_data,
                planned_targets=overview.definition.planned_targets,
                supported_teams=overview.definition.supported_teams,
                layers=[
                    {
                        "key": layer.key,
                        "title": layer.title,
                        "summary": layer.summary,
                    }
                    for layer in overview.definition.layers
                ],
            ),
            department_name=overview.department_name,
            selected_team=overview.selected_team,
            selected_employee_id=overview.selected_employee_id,
            latest_period=overview.latest_period,
            metrics=[
                asdict(item)
                for item in overview.metrics
            ],
            team_summaries=[asdict(item) for item in overview.team_summaries],
            employee_summaries=[asdict(item) for item in overview.employee_summaries],
            notes=overview.notes,
            sprint_focus=overview.sprint_focus,
        )
