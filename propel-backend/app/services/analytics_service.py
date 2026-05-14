from __future__ import annotations

from dataclasses import asdict
from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session

from app.analytics import get_department_adapter, list_department_adapters
from app.analytics.kpi_registry import get_software_kpi_definition
from app.db.models.employee import Employee
from app.db.models.kpi import KPIRecord
from app.db.models.user import User, UserRole
from app.schemas.analytics import (
    DepartmentAnalyticsConfigResponse,
    DepartmentAnalyticsOverviewResponse,
    DepartmentPerformanceSummaryResponse,
    PerformanceActionGroupResponse,
    PerformanceEmployeeRowResponse,
    PerformanceInsightResponse,
    PerformanceKpiSummaryResponse,
    PerformanceRoleSummaryResponse,
    PerformanceStrengthResponse,
    PerformanceTeamSummaryResponse,
)


class AnalyticsService:
    @staticmethod
    def _average(values: list[float]) -> float | None:
        return round(sum(values) / len(values), 1) if values else None

    @staticmethod
    def _normalize_kpi_value(value: float) -> float:
        if value <= 5:
            return round(value * 20, 1)
        if value <= 10:
            return round(value * 10, 1)
        return round(max(0, min(100, value)), 1)

    @staticmethod
    def _kpi_definition(record: KPIRecord):
        description = record.kpi.description if record.kpi else None
        metric_code = (description or "").split("|", 1)[0].strip() or None
        return get_software_kpi_definition(metric_code)

    @staticmethod
    def _performance_score_for_records(records: list[KPIRecord]) -> float | None:
        if not records:
            return None

        scored_records: list[tuple[KPIRecord, float]] = []
        for record in records:
            definition = AnalyticsService._kpi_definition(record)
            normalized = AnalyticsService._normalize_kpi_value(float(record.value))
            if definition and definition.canonical_code == "KPI-18 GPS":
                return normalized
            if definition and definition.canonical_code == "KPI-19 ARS":
                continue
            if definition and definition.direction == "lower_is_better":
                normalized = round(100 - normalized, 1)
            scored_records.append((record, normalized))

        return AnalyticsService._average([score for _, score in scored_records])

    @staticmethod
    def _role_level(position: str | None, experience_years: float | None) -> str:
        role = (position or "").lower()
        years = float(experience_years or 0)
        if "lead" in role or "manager" in role:
            return "lead"
        if "senior" in role or years >= 5:
            return "senior"
        if "junior" in role or years <= 2:
            return "junior"
        return "mid"

    @staticmethod
    def _status_for(score: float | None, trend: float | None) -> str:
        if score is None:
            return "no_data"
        trend_value = trend or 0
        if score < 80 or trend_value < -2:
            return "risk"
        if score < 90 or trend_value < -0.2:
            return "watch"
        return "stable"

    @staticmethod
    def _scope_employee_query(db: Session, current_user, department_id: int | None, team: str | None):
        query = (
            db.query(Employee)
            .options(joinedload(Employee.user), joinedload(Employee.department))
            .join(Employee.user)
            .filter(User.role == UserRole.employee)
        )

        if current_user.role == UserRole.admin:
            if department_id:
                query = query.filter(Employee.department_id == department_id)
        else:
            current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
            if not current_employee:
                raise HTTPException(status_code=404, detail="Calisan kaydiniz bulunamadi")
            if current_user.role == UserRole.department_manager:
                query = query.filter(Employee.department_id == current_employee.department_id)
            else:
                query = query.filter(Employee.id == current_employee.id)

        if team and team != "all":
            query = query.filter(Employee.team == team)

        return query

    @staticmethod
    def get_performance_summary(
        db: Session,
        current_user,
        department_id: int | None = None,
        team: str | None = None,
    ) -> DepartmentPerformanceSummaryResponse:
        employees = AnalyticsService._scope_employee_query(db, current_user, department_id, team).all()
        employee_ids = [employee.id for employee in employees]
        records: list[KPIRecord] = []
        if employee_ids:
            records = (
                db.query(KPIRecord)
                .options(joinedload(KPIRecord.kpi))
                .filter(KPIRecord.employee_id.in_(employee_ids))
                .all()
            )

        records_by_employee: dict[int, list[KPIRecord]] = defaultdict(list)
        for record in records:
            records_by_employee[record.employee_id].append(record)

        rows: list[PerformanceEmployeeRowResponse] = []
        latest_periods = [record.period_date for record in records if record.period_date]
        scope_latest_period = max(latest_periods) if latest_periods else None

        for employee in employees:
            employee_records = sorted(records_by_employee.get(employee.id, []), key=lambda item: item.period_date)
            periods = sorted({record.period_date for record in employee_records if record.period_date})
            last_four_periods = periods[-4:]
            latest_period = periods[-1] if periods else None
            latest_records = [record for record in employee_records if record.period_date == latest_period]

            kpi_score = AnalyticsService._performance_score_for_records(latest_records)

            sparkline_values: list[float] = []
            for period in last_four_periods:
                period_average = AnalyticsService._performance_score_for_records([
                    record for record in employee_records if record.period_date == period
                ])
                if period_average is not None:
                    sparkline_values.append(period_average)

            trend = None
            if len(sparkline_values) >= 2:
                trend = round(sparkline_values[-1] - sparkline_values[0], 1)

            strength = None
            if latest_records:
                kpi_scores = []
                for record in latest_records:
                    label = record.kpi.name if record.kpi else f"KPI #{record.kpi_id}"
                    kpi_scores.append((AnalyticsService._normalize_kpi_value(float(record.value)), label))
                strongest_score, strongest_label = sorted(kpi_scores, key=lambda item: item[0], reverse=True)[0]
                strength = PerformanceStrengthResponse(
                    label=strongest_label,
                    tooltip=f"Son donemde en yuksek normalize KPI sinyali: {strongest_score}/100.",
                )

            role_level = AnalyticsService._role_level(employee.position, employee.experience_years)
            rows.append(
                PerformanceEmployeeRowResponse(
                    employee_id=employee.id,
                    employee_name=employee.full_name,
                    external_employee_code=employee.external_employee_code,
                    department_id=employee.department_id,
                    department_name=employee.department_name,
                    team=employee.team,
                    position=employee.position,
                    experience_years=employee.experience_years,
                    role_level=role_level,
                    kpi_score=kpi_score,
                    trend=trend,
                    sparkline_values=sparkline_values,
                    strength=strength,
                    status=AnalyticsService._status_for(kpi_score, trend),
                    latest_period=latest_period,
                    record_count=len(employee_records),
                    has_kpi_data=bool(employee_records),
                )
            )

        analyzed_rows = [row for row in rows if row.kpi_score is not None]
        average_kpi = AnalyticsService._average([row.kpi_score for row in analyzed_rows if row.kpi_score is not None])
        average_trend = AnalyticsService._average([row.trend for row in analyzed_rows if row.trend is not None])
        top_performers = [row for row in analyzed_rows if (row.kpi_score or 0) > 92]
        declining = [row for row in analyzed_rows if (row.trend or 0) < 0]
        junior_rows = [row for row in analyzed_rows if row.role_level == "junior"]
        senior_rows = [row for row in analyzed_rows if row.role_level in {"senior", "lead"}]

        teams: list[PerformanceTeamSummaryResponse] = []
        for team_name in sorted({row.team or "Takimsiz" for row in rows}):
            members = [row for row in rows if (row.team or "Takimsiz") == team_name]
            analyzed_members = [row for row in members if row.kpi_score is not None]
            teams.append(
                PerformanceTeamSummaryResponse(
                    team=team_name,
                    employee_count=len(members),
                    analyzed_count=len(analyzed_members),
                    average_kpi=AnalyticsService._average([row.kpi_score for row in analyzed_members if row.kpi_score is not None]),
                    average_trend=AnalyticsService._average([row.trend for row in analyzed_members if row.trend is not None]),
                    declining_count=len([row for row in analyzed_members if (row.trend or 0) < 0]),
                    top_performer_count=len([row for row in analyzed_members if (row.kpi_score or 0) > 92]),
                )
            )

        role_labels = {"junior": "Junior", "mid": "Mid", "senior": "Senior", "lead": "Lead"}
        roles: list[PerformanceRoleSummaryResponse] = []
        for role_level, label in role_labels.items():
            members = [row for row in rows if row.role_level == role_level]
            analyzed_members = [row for row in members if row.kpi_score is not None]
            sorted_by_kpi = sorted(analyzed_members, key=lambda row: row.kpi_score or 0, reverse=True)
            highest = sorted_by_kpi[0] if sorted_by_kpi else None
            lowest = sorted_by_kpi[-1] if sorted_by_kpi else None
            roles.append(
                PerformanceRoleSummaryResponse(
                    role_level=role_level,
                    label=label,
                    employee_count=len(members),
                    analyzed_count=len(analyzed_members),
                    average_kpi=AnalyticsService._average([row.kpi_score for row in analyzed_members if row.kpi_score is not None]),
                    average_trend=AnalyticsService._average([row.trend for row in analyzed_members if row.trend is not None]),
                    highest_employee_name=highest.employee_name if highest else None,
                    highest_kpi=highest.kpi_score if highest else None,
                    lowest_employee_name=lowest.employee_name if lowest else None,
                    lowest_kpi=lowest.kpi_score if lowest else None,
                )
            )

        riskiest_team = sorted(teams, key=lambda item: (item.declining_count, -(item.average_kpi or 0)), reverse=True)[0] if teams else None
        strongest_team = sorted(teams, key=lambda item: item.average_trend or -999, reverse=True)[0] if teams else None
        senior_avg = AnalyticsService._average([row.kpi_score for row in senior_rows if row.kpi_score is not None])
        junior_avg = AnalyticsService._average([row.kpi_score for row in junior_rows if row.kpi_score is not None])
        senior_junior_gap = round((senior_avg or 0) - (junior_avg or 0), 1) if senior_avg is not None and junior_avg is not None else None

        insights = [
            PerformanceInsightResponse(
                title="Genel Durum",
                icon="📊",
                tone="neutral",
                text=(
                    f"{len(rows)} calisandan {len(analyzed_rows)} kisi gercek KPI kaydiyla analiz edildi. "
                    f"Ortalama performans {average_kpi}/100, genel trend {average_trend}."
                    if analyzed_rows
                    else "Bu kapsamda henuz KPI kaydi bulunamadigi icin performans analizi uretilemedi."
                ),
            ),
            PerformanceInsightResponse(
                title="Risk Tespiti",
                icon="⚠️",
                tone="warning",
                text=(
                    f"{riskiest_team.team} takiminda {riskiest_team.declining_count} calisan dusus trendinde."
                    if riskiest_team
                    else "Risk tespiti icin yeterli takim verisi yok."
                ),
            ),
            PerformanceInsightResponse(
                title="Basari Hikayesi",
                icon="✅",
                tone="success",
                text=(
                    f"{strongest_team.team} takimi ortalama {strongest_team.average_trend} trend ile en guclu gelisimi gosteriyor."
                    if strongest_team
                    else "Basari hikayesi icin yeterli trend verisi yok."
                ),
            ),
            PerformanceInsightResponse(
                title="Junior-Senior Farki",
                icon="📈",
                tone="info",
                text=(
                    f"Senior/Lead grup Junior gruptan ortalama {senior_junior_gap} puan onde."
                    if senior_junior_gap is not None
                    else "Junior-Senior farki icin iki grupta da yeterli KPI verisi yok."
                ),
            ),
        ]

        risk_people = sorted(declining, key=lambda row: row.trend or 0)[:5]
        success_people = sorted(
            [row for row in analyzed_rows if (row.trend or 0) > 0],
            key=lambda row: (row.trend or 0, row.kpi_score or 0),
            reverse=True,
        )[:3]

        action_groups = [
            PerformanceActionGroupResponse(
                title="Kisa Vadeli (Bu Hafta)",
                items=[
                    f"Dusus gosteren {len(declining)} calisanla 1-on-1 gorusme planla.",
                    f"{riskiest_team.team if riskiest_team else 'Oncelikli'} takiminda is yuku ve KPI kirilimini incele.",
                    "KPI kaydi eksik calisanlar icin veri tamamlama kontrolu yap.",
                ],
            ),
            PerformanceActionGroupResponse(
                title="Orta Vadeli (Bu Ay)",
                items=[
                    "Rol bazli performans farklarini gelisim planina cevir.",
                    f"{success_people[0].employee_name if success_people else 'Top performer'} icin bilgi paylasimi veya mentorluk oturumu planla.",
                    "Takim hedefleri ve kapasite planini KPI trendlerine gore dengele.",
                ],
            ),
            PerformanceActionGroupResponse(
                title="Uzun Vadeli (Bu Ceyrek)",
                items=[
                    "Kariyer gelisim patikalarini rol seviyelerine gore netlestir.",
                    "Cross-team bilgi paylasimi ritmini performans verisiyle takip et.",
                    "Performans degerlendirme sistemini KPI veri kalitesiyle birlikte gozden gecir.",
                ],
            ),
        ]

        return DepartmentPerformanceSummaryResponse(
            scope_department_id=department_id,
            scope_team=team,
            latest_period=scope_latest_period,
            summary=PerformanceKpiSummaryResponse(
                total_employees=len(rows),
                analyzed_employees=len(analyzed_rows),
                team_count=len(teams),
                average_kpi=average_kpi,
                average_trend=average_trend,
                top_performer_count=len(top_performers),
                declining_count=len(declining),
                junior_average=junior_avg,
                junior_count=len(junior_rows),
                senior_average=senior_avg,
                senior_count=len(senior_rows),
            ),
            employees=rows,
            teams=teams,
            roles=roles,
            insights=insights,
            risk_people=risk_people,
            success_people=success_people,
            action_groups=action_groups,
        )

    @staticmethod
    def list_department_configs(current_user: User) -> list[DepartmentAnalyticsConfigResponse]:
        from app.db.session import SessionLocal

        configs: list[DepartmentAnalyticsConfigResponse] = []
        
        # Determine allowed department keys
        allowed_keys = None
        if current_user.role == UserRole.department_manager:
            db = SessionLocal()
            try:
                employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
                if employee and employee.department:
                    # Map department name to analytics key
                    # This is a bit brittle, but works for Software/Sales
                    dept_name = employee.department.name.lower()
                    if "yazilim" in dept_name or "software" in dept_name:
                        allowed_keys = ["software"]
                    elif "satis" in dept_name or "sales" in dept_name:
                        allowed_keys = ["sales"]
            finally:
                db.close()

        for adapter in list_department_adapters():
            definition = adapter.definition
            
            # Skip if not in allowed keys (for managers)
            if allowed_keys is not None and definition.key not in allowed_keys:
                continue

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
