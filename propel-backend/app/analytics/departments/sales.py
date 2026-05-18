from __future__ import annotations

from collections import defaultdict
from datetime import date
from statistics import mean
from typing import Optional

from sqlalchemy.orm import Session

from app.analytics.contracts import (
    AnalyticsLayerDefinition,
    DepartmentAnalyticsDefinition,
    DepartmentAnalyticsOverview,
    EmployeeAnalyticsSnapshot,
    OverviewMetricCard,
    TeamAnalyticsSnapshot,
)
from app.analytics.departments.base import DepartmentAnalyticsAdapter
from app.analytics.kpi_registry import get_sales_kpi_definition
from app.db.models.department import Department
from app.db.models.employee import Employee
from app.db.models.kpi import KPIRecord
from app.db.models.user import User, UserRole


class SalesAnalyticsAdapter(DepartmentAnalyticsAdapter):
    definition = DepartmentAnalyticsDefinition(
        key="sales",
        label="Satis",
        description="Satis KPI seti, quota attainment, donusum, musteri odakliligi ve surdurulebilirlik sinyalleriyle stacking ensemble modeline beslenir.",
        readiness_status="live",
        supports_live_data=True,
        planned_targets=[
            "Performance_Drop_Target",
            "Burnout_Target",
            "Resignation_Target",
            "High_Risk_Target",
        ],
        supported_teams=["Kurumsal Satis", "Bireysel Satis", "Musteri Basarisi"],
        layers=[
            AnalyticsLayerDefinition("features", "Katman 1: Ozellik Zenginlestirme", "Quota attainment, donusum, musteri memnuniyeti, is yuku ve motivasyon sinyalleri normalize edilerek 25 KPI'a donusturulur."),
            AnalyticsLayerDefinition("base_models", "Katman 2: Baz Ogreniciler", "LightGBM, XGBoost ve Random Forest farkli satis hata oruntuleri icin paralel calisir."),
            AnalyticsLayerDefinition("meta_model", "Katman 3: Meta-Model", "Baz modellerin olasilik ciktilari Lojistik Regresyon ile birlestirilir (Stacking Ensemble)."),
            AnalyticsLayerDefinition("action_layer", "Katman 4: Cikti ve Aksiyon", "Nihai risk skoru, aciklanabilir satis KPI sapmalari ve yonetici aksiyon onerileri uretilir."),
        ],
    )

    @staticmethod
    def _resolve_department(db: Session) -> Optional[Department]:
        return db.query(Department).filter(Department.name == "Satis").first()

    @staticmethod
    def _metric_code(record: KPIRecord) -> str:
        if record.kpi and record.kpi.description:
            return record.kpi.description.split("|", 1)[0].strip()
        return record.kpi.name if record.kpi else "UNKNOWN"

    @staticmethod
    def _normalize_score(record: KPIRecord) -> Optional[float]:
        if not record.kpi or record.kpi.target_value in (None, 0):
            return None

        metric = get_sales_kpi_definition(SalesAnalyticsAdapter._metric_code(record))
        higher_is_better = metric.higher_is_better if metric else True
        target = float(record.kpi.target_value)
        value = float(record.value)

        if higher_is_better:
            raw_score = (value / target) * 100
        else:
            raw_score = (target / max(value, 0.001)) * 100

        return round(max(0.0, min(130.0, raw_score)), 2)

    @staticmethod
    def _risk_band(score: float) -> str:
        if score >= 100:
            return "Guclu"
        if score >= 80:
            return "Stabil"
        return "Izleme Gerekli"

    @staticmethod
    def _employee_scope(
        db: Session,
        department_id: int,
        team: Optional[str],
        employee_id: Optional[int],
    ) -> list[Employee]:
        query = (
            db.query(Employee)
            .join(Employee.user)
            .filter(
                Employee.department_id == department_id,
                User.role == UserRole.employee,
            )
        )
        if team:
            query = query.filter(Employee.team == team)
        if employee_id:
            query = query.filter(Employee.id == employee_id)
        return query.all()

    @staticmethod
    def _aggregate_employee_snapshot(
        employee: Employee,
        latest_records: list[KPIRecord],
        previous_records: list[KPIRecord],
    ) -> EmployeeAnalyticsSnapshot:
        latest_scores: list[float] = []
        previous_scores: list[float] = []
        category_scores: dict[str, list[float]] = defaultdict(list)

        for record in latest_records:
            score = SalesAnalyticsAdapter._normalize_score(record)
            if score is None:
                continue
            latest_scores.append(score)
            metric = get_sales_kpi_definition(SalesAnalyticsAdapter._metric_code(record))
            category = metric.category if metric else "Diger"
            category_scores[category].append(score)

        for record in previous_records:
            score = SalesAnalyticsAdapter._normalize_score(record)
            if score is not None:
                previous_scores.append(score)

        latest_average = round(mean(latest_scores), 1) if latest_scores else 0.0
        previous_average = round(mean(previous_scores), 1) if previous_scores else None
        trend_delta = round(latest_average - previous_average, 1) if previous_average is not None else None

        strongest_category = None
        weakest_category = None
        if category_scores:
            category_averages = {key: mean(values) for key, values in category_scores.items()}
            strongest_category = max(category_averages, key=category_averages.get)
            weakest_category = min(category_averages, key=category_averages.get)

        return EmployeeAnalyticsSnapshot(
            employee_id=employee.id,
            employee_name=employee.user.full_name if employee.user else f"Employee {employee.id}",
            team=employee.team,
            position=employee.position,
            external_employee_code=employee.external_employee_code,
            latest_score=latest_average,
            previous_score=previous_average,
            trend_delta=trend_delta,
            strongest_category=strongest_category,
            weakest_category=weakest_category,
            risk_band=SalesAnalyticsAdapter._risk_band(latest_average),
        )

    def build_overview(
        self,
        db: Session,
        current_user: User,
        team: Optional[str] = None,
        employee_id: Optional[int] = None,
    ) -> DepartmentAnalyticsOverview:
        department = self._resolve_department(db)
        if not department:
            return DepartmentAnalyticsOverview(
                definition=self.definition,
                department_name=self.definition.label,
                selected_team=team,
                selected_employee_id=employee_id,
                latest_period=None,
                metrics=[
                    OverviewMetricCard("readiness", "Durum", "Veri bekleniyor", "warning", "Satis departmani verisi henuz bulunamadi."),
                ],
                team_summaries=[],
                employee_summaries=[],
                notes=["Canli KPI kaydi bulunamadigi icin satis ekrani placeholder modunda acildi."],
                sprint_focus=[
                    "Satis KPI registry aktif",
                    "Excel upload ile veri aktarimi baslatilabilir",
                    "Stacking ensemble egitime hazir",
                ],
            )

        employees = self._employee_scope(db, department.id, team, employee_id)
        employee_ids = [employee.id for employee in employees]
        if not employee_ids:
            return DepartmentAnalyticsOverview(
                definition=self.definition,
                department_name=department.name,
                selected_team=team,
                selected_employee_id=employee_id,
                latest_period=None,
                metrics=[
                    OverviewMetricCard("scope", "Secili Kapsam", "0 calisan", "neutral", "Secili filtre icin calisan bulunamadi."),
                ],
                team_summaries=[],
                employee_summaries=[],
                notes=["Takim filtresi gecerli fakat bu kapsamda kayit bulunamadi."],
                sprint_focus=[
                    "Takim bazli KPI izleme",
                    "Calisan bazli satis trend kartlari",
                    "ML risk skoru entegrasyonu",
                ],
            )

        latest_period = (
            db.query(KPIRecord.period_date)
            .filter(KPIRecord.employee_id.in_(employee_ids))
            .order_by(KPIRecord.period_date.desc())
            .limit(1)
            .scalar()
        )

        previous_period = None
        if latest_period:
            previous_period = (
                db.query(KPIRecord.period_date)
                .filter(KPIRecord.employee_id.in_(employee_ids), KPIRecord.period_date < latest_period)
                .order_by(KPIRecord.period_date.desc())
                .limit(1)
                .scalar()
            )

        latest_records = (
            db.query(KPIRecord)
            .filter(KPIRecord.employee_id.in_(employee_ids), KPIRecord.period_date == latest_period)
            .all()
            if latest_period
            else []
        )
        previous_records = (
            db.query(KPIRecord)
            .filter(KPIRecord.employee_id.in_(employee_ids), KPIRecord.period_date == previous_period)
            .all()
            if previous_period
            else []
        )

        latest_by_employee: dict[int, list[KPIRecord]] = defaultdict(list)
        previous_by_employee: dict[int, list[KPIRecord]] = defaultdict(list)
        for record in latest_records:
            latest_by_employee[record.employee_id].append(record)
        for record in previous_records:
            previous_by_employee[record.employee_id].append(record)

        employee_summaries = [
            self._aggregate_employee_snapshot(
                employee,
                latest_by_employee.get(employee.id, []),
                previous_by_employee.get(employee.id, []),
            )
            for employee in employees
        ]
        employee_summaries.sort(key=lambda item: item.latest_score, reverse=True)

        team_buckets: dict[str, list[EmployeeAnalyticsSnapshot]] = defaultdict(list)
        for snapshot in employee_summaries:
            team_buckets[snapshot.team or "Takimsiz"].append(snapshot)

        team_summaries: list[TeamAnalyticsSnapshot] = []
        for team_name, snapshots in sorted(team_buckets.items()):
            deltas = [item.trend_delta for item in snapshots if item.trend_delta is not None]
            team_summaries.append(
                TeamAnalyticsSnapshot(
                    team=team_name,
                    employee_count=len(snapshots),
                    average_score=round(mean(item.latest_score for item in snapshots), 1),
                    average_trend_delta=round(mean(deltas), 1) if deltas else None,
                    watchlist_count=sum(1 for item in snapshots if item.latest_score < 80),
                )
            )

        latest_scores = [item.latest_score for item in employee_summaries]
        latest_average = round(mean(latest_scores), 1) if latest_scores else 0.0
        watchlist_count = sum(1 for item in employee_summaries if item.latest_score < 80)
        improving_count = sum(1 for item in employee_summaries if (item.trend_delta or 0) > 0)

        metrics = [
            OverviewMetricCard("scope", "Kapsamdaki Calisan", str(len(employee_summaries)), "neutral", "Secili takim ve calisan filtresine gore canli kapsami gosterir."),
            OverviewMetricCard("score", "Ortalama KPI Skoru", f"{latest_average}/100", "primary", "Son donemde normalize edilen satis KPI ortalamasi."),
            OverviewMetricCard("watchlist", "Izleme Gereken Kisi", str(watchlist_count), "warning", "KPI skoru 80 altina dusen kisiler."),
            OverviewMetricCard("momentum", "Yukselen Trend", str(improving_count), "success", "Bir onceki doneme gore KPI ortalamasi yukselen kisiler."),
            OverviewMetricCard("readiness", "ML Hazirlik Durumu", "Aktif", "info", "Stacking Ensemble (LightGBM+XGB+RF→LR) modeli egitime hazir."),
        ]

        notes = [
            "Satis KPI omurgasi canli durumda; 25 KPI hesaplanmakta.",
            "Model egitimi Admin > Veri Yonetimi uzerinden Excel/CSV yuklemesiyle tetiklenir.",
            "Her calisan icin 4 hedef: Performans Dususu, Tukenmislik, Istifa Riski, Yuksek Risk.",
        ]

        sprint_focus = [
            "Satis KPI registry ve normalization canli durumda",
            "Stacking Ensemble (LightGBM+XGB+RF->LR) hazir",
            "Admin yuklemesiyle model egitimi ve toplu tahmin destekleniyor",
        ]

        return DepartmentAnalyticsOverview(
            definition=self.definition,
            department_name=department.name,
            selected_team=team,
            selected_employee_id=employee_id,
            latest_period=latest_period,
            metrics=metrics,
            team_summaries=team_summaries,
            employee_summaries=employee_summaries,
            notes=notes,
            sprint_focus=sprint_focus,
        )
