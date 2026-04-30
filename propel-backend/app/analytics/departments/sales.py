from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.analytics.contracts import AnalyticsLayerDefinition, DepartmentAnalyticsDefinition, DepartmentAnalyticsOverview, OverviewMetricCard
from app.analytics.departments.base import DepartmentAnalyticsAdapter
from app.db.models.user import User


class SalesAnalyticsAdapter(DepartmentAnalyticsAdapter):
    definition = DepartmentAnalyticsDefinition(
        key="sales",
        label="Satis",
        description="Satis KPI seti, quota ve donusum bazli feature engineering ile ayni analytics omurgasina baglanacak.",
        readiness_status="awaiting_dataset",
        supports_live_data=False,
        planned_targets=[
            "quota_risk_band",
            "attrition_risk_band",
        ],
        supported_teams=["Field Sales", "Inside Sales", "Account Management"],
        layers=[
            AnalyticsLayerDefinition("features", "Katman 1: Ozellik Zenginlestirme", "Quota attainment, donusum, gorusme hizi ve musteri kalitesi gibi KPI'lar normalize edilir."),
            AnalyticsLayerDefinition("base_models", "Katman 2: Baz Ogreniciler", "XGBoost, Random Forest ve LightGBM satis KPI seti icin tekrar egitilir."),
            AnalyticsLayerDefinition("meta_model", "Katman 3: Meta-Model", "Departmana ozel baz model ciktilari lojistik regresyon ile birlestirilir."),
            AnalyticsLayerDefinition("action_layer", "Katman 4: Cikti ve Aksiyon", "Kritik satis KPI sapmalari ve aksiyon onerileri yoneticiye sunulur."),
        ],
    )

    def build_overview(
        self,
        db: Session,
        current_user: User,
        team: Optional[str] = None,
        employee_id: Optional[int] = None,
    ) -> DepartmentAnalyticsOverview:
        return DepartmentAnalyticsOverview(
            definition=self.definition,
            department_name=self.definition.label,
            selected_team=team,
            selected_employee_id=employee_id,
            latest_period=None,
            metrics=[
                OverviewMetricCard("readiness", "Durum", "Veri Bekleniyor", "warning", "Satis departmani adapter'i hazir, fakat canli veri importu henuz yapilmadi."),
                OverviewMetricCard("contract", "Analytics Sozlesmesi", "Hazir", "info", "Ayni core engine uzerinden yeni satis mapper'i baglanabilecek durumda."),
            ],
            team_summaries=[],
            employee_summaries=[],
            notes=[
                "Satis departmani icin ayrica KPI registry ve Excel mapper katmani eklenecek.",
                "Bu placeholder ekran, ayni ensemble mimarinin departmanlar arasi yeniden kullanilacagini gosterir.",
            ],
            sprint_focus=[
                "Satis KPI registry olusturulacak",
                "Excel mapper eklenecek",
                "Departman ozel baseline model egitilecek",
            ],
        )
