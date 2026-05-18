from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Literal


MetricDirection = Literal["higher_is_better", "lower_is_better", "optimal_range"]


@dataclass(frozen=True)
class KPIThresholds:
    strong: float | None = None
    stable: float | None = None
    risk: float | None = None
    optimal_min: float | None = None
    optimal_max: float | None = None


@dataclass(frozen=True)
class KPIDefinition:
    canonical_code: str
    legacy_codes: tuple[str, ...]
    short_code: str
    display_name: str
    category: str
    direction: MetricDirection
    unit: str
    formula: str
    action_when_risky: str
    source_columns: tuple[str, ...] = field(default_factory=tuple)
    thresholds: KPIThresholds = field(default_factory=KPIThresholds)
    is_model_feature: bool = True
    is_target_candidate: bool = False

    @property
    def all_codes(self) -> tuple[str, ...]:
        return (self.canonical_code, *self.legacy_codes)

    @property
    def higher_is_better(self) -> bool:
        return self.direction != "lower_is_better"


SOFTWARE_KPI_REGISTRY: tuple[KPIDefinition, ...] = (
    KPIDefinition(
        canonical_code="KPI-1 GTO",
        legacy_codes=(),
        short_code="GTO",
        display_name="Gorev Tamamlama Orani",
        category="Uretkenlik",
        direction="higher_is_better",
        unit="ratio",
        formula="Tamamlanan Gorev / Atanan Gorev",
        thresholds=KPIThresholds(strong=0.85, stable=0.65, risk=0.65),
        action_when_risky="Gorev karmasikligi veya motivasyon analizi yapilmali.",
        source_columns=("task_completion_rate", "KPI-1_Gorev_Tamamlama_Orani_GTO"),
    ),
    KPIDefinition(
        canonical_code="KPI-2 ZTO",
        legacy_codes=(),
        short_code="ZTO",
        display_name="Zamaninda Teslim Orani",
        category="Uretkenlik",
        direction="higher_is_better",
        unit="ratio",
        formula="Deadline oncesi tamamlanan gorev / Toplam gorev",
        thresholds=KPIThresholds(strong=0.80, stable=0.60, risk=0.60),
        action_when_risky="Planlama, teknik borc ve teslim blokajlari incelenmeli.",
        source_columns=("on_time_delivery_rate", "KPI-2_Zamaninda_Teslim_Orani_ZTO"),
    ),
    KPIDefinition(
        canonical_code="KPI-3 GKE",
        legacy_codes=(),
        short_code="GKE",
        display_name="Goreli Katki Endeksi",
        category="Uretkenlik",
        direction="higher_is_better",
        unit="ratio",
        formula="Kisinin tamamladigi story point / Takim ortalama story point",
        thresholds=KPIThresholds(strong=1.15, stable=0.85, risk=0.85),
        action_when_risky="Katki dusukse gorev dagilimi, deneyim seviyesi ve destek ihtiyaci kontrol edilmeli.",
        source_columns=("commit_score", "KPI-3_Goreli_Katki_Endeksi_GKE"),
    ),
    KPIDefinition(
        canonical_code="KPI-4 KKKE",
        legacy_codes=("KPI-4 KKE",),
        short_code="KKKE",
        display_name="Kod Katki Kalite Endeksi",
        category="Kalite",
        direction="higher_is_better",
        unit="score",
        formula="0.35*ECO + 0.20*HDS + 0.25*CTO_score + 0.20*OCH_score",
        thresholds=KPIThresholds(strong=0.75, stable=0.55, risk=0.55),
        action_when_risky="Commit kalitesi, sprint sonu yuklenme ve task-commit dengesi incelenmeli.",
        source_columns=("project_complexity", "KPI-4_Kod_Katki_Kalite_Endeksi_KKKE"),
    ),
    KPIDefinition(
        canonical_code="KPI-5 BY",
        legacy_codes=("KPI-5 BO",),
        short_code="BY",
        display_name="Bug Yogunlugu",
        category="Kalite",
        direction="lower_is_better",
        unit="bugs_per_kloc",
        formula="Toplam bug / 1.000 satir kod",
        thresholds=KPIThresholds(strong=0.30, stable=0.60, risk=0.60),
        action_when_risky="Kod kalitesi, test kapsami ve teknik borc kaynaklari incelenmeli.",
        source_columns=("bug_density", "KPI-5_Bug_Yogunlugu_BY"),
    ),
    KPIDefinition(
        canonical_code="KPI-6 KBO",
        legacy_codes=(),
        short_code="KBO",
        display_name="Kritik Bug Orani",
        category="Kalite",
        direction="lower_is_better",
        unit="ratio",
        formula="Kritik bug / Toplam bug",
        action_when_risky="Kritik hata kaynaklari ve release kalite kapilari gozden gecirilmeli.",
        source_columns=("critical_bug_ratio", "KPI-6_Kritik_Bug_Orani_KBO"),
    ),
    KPIDefinition(
        canonical_code="KPI-7 CRKO",
        legacy_codes=("KPI-7 CKO", "KPI-7 EKO"),
        short_code="CRKO",
        display_name="Code Review Kabul Orani",
        category="Kalite",
        direction="higher_is_better",
        unit="ratio",
        formula="Ilk/erken review kabul edilen PR / Toplam PR",
        action_when_risky="Review geri donusleri, kod standartlari ve mentorluk ihtiyaci degerlendirilmeli.",
        source_columns=("code_review_acceptance", "KPI-7_Code_Review_Kabul_Orani_CRKO"),
    ),
    KPIDefinition(
        canonical_code="KPI-8 OPDS",
        legacy_codes=("KPI-8 ODS", "KPI-8 UPDS"),
        short_code="OPDS",
        display_name="Ortalama PR Duzeltme Sayisi",
        category="Kalite",
        direction="lower_is_better",
        unit="count",
        formula="PR basina ortalama duzeltme sayisi",
        action_when_risky="PR kalitesi, acceptance criteria ve review oncesi kontrol listesi iyilestirilmeli.",
        source_columns=("avg_pr_revision", "KPI-8_Ortalama_PR_Duzeltme_Sayisi_OPDS"),
    ),
    KPIDefinition(
        canonical_code="KPI-9 IYE",
        legacy_codes=("KPI-9 İYE",),
        short_code="IYE",
        display_name="Is Yuku Endeksi",
        category="Is Yuku ve Surdurulebilirlik",
        direction="optimal_range",
        unit="index",
        formula="Atanan is hacmi ve kapasite dengesini olcen endeks",
        action_when_risky="Is yuku dengelemesi ve sprint kapasite planlamasi yapilmali.",
        source_columns=("workload_index", "KPI-9_Is_Yuku_Endeksi_IYE"),
    ),
    KPIDefinition(
        canonical_code="KPI-10 SAYS",
        legacy_codes=("KPI-10 AIYS",),
        short_code="SAYS",
        display_name="Surekli Asiri Yuk Skoru",
        category="Is Yuku ve Surdurulebilirlik",
        direction="lower_is_better",
        unit="score",
        formula="Tekrarlayan yuksek kapasite kullanimini olcen risk skoru",
        action_when_risky="Suren asiri yuk, burnout riski ve kaynak ihtiyaci incelenmeli.",
        source_columns=("KPI-10_Surekli_Asiri_Yuk_Skoru_SAYS",),
    ),
    KPIDefinition(
        canonical_code="KPI-11 TYO",
        legacy_codes=("KPI-11 TTY",),
        short_code="TYO",
        display_name="Toplanti Yuku Orani",
        category="Is Yuku ve Surdurulebilirlik",
        direction="lower_is_better",
        unit="ratio",
        formula="Toplanti suresi / Calisma suresi",
        action_when_risky="Toplanti yogunlugu ve odakli calisma zamani gozden gecirilmeli.",
        source_columns=("team_collaboration_score", "KPI-11_Toplanti_Yuku_Orani_TYO"),
    ),
    KPIDefinition(
        canonical_code="KPI-12 EKS",
        legacy_codes=(),
        short_code="EKS",
        display_name="Ekip Katki Skoru",
        category="Ekip Etkisi ve Is Birligi",
        direction="higher_is_better",
        unit="score",
        formula="Review, mentorluk ve ekip destek katkisi",
        action_when_risky="Ekip ici destek, mentorluk ve bilgi paylasimi artirilmali.",
        source_columns=("management_quality", "KPI-12_Ekip_Katki_Skoru_EKS"),
    ),
    KPIDefinition(
        canonical_code="KPI-13 360-GBS",
        legacy_codes=("KPI-13 360GBS",),
        short_code="360-GBS",
        display_name="360 Geri Bildirim Skoru",
        category="Ekip Etkisi ve Is Birligi",
        direction="higher_is_better",
        unit="score",
        formula="360 derece geri bildirim ortalamasi",
        action_when_risky="Geri bildirim temalari ve yonetsel destek ihtiyaci incelenmeli.",
        source_columns=("feedback_score", "KPI-13_360_Geri_Bildirim_Skoru_360GBS"),
    ),
    KPIDefinition(
        canonical_code="KPI-14 OMS",
        legacy_codes=(),
        short_code="OMS",
        display_name="Organizasyonel Merkezilik Skoru",
        category="Ekip Etkisi ve Is Birligi",
        direction="higher_is_better",
        unit="score",
        formula="Ag icindeki etkilesim ve kritik rol seviyesi",
        action_when_risky="Ekip baglantilari, bilgi akisi ve izolasyon riski incelenmeli.",
        source_columns=("org_centrality_score", "KPI-14_Organizasyonel_Merkezilik_Skoru_OMS"),
    ),
    KPIDefinition(
        canonical_code="KPI-15 MS",
        legacy_codes=(),
        short_code="MS",
        display_name="Motivasyon Skoru",
        category="Duygu ve Gelisim",
        direction="higher_is_better",
        unit="score",
        formula="Pulse ve duygu sinyallerinden motivasyon seviyesi",
        action_when_risky="Motivasyon dususu icin birebir gorusme ve engel analizi yapilmali.",
        source_columns=("motivation_score", "KPI-15_Motivasyon_Skoru_MS"),
    ),
    KPIDefinition(
        canonical_code="KPI-16 MTE",
        legacy_codes=(),
        short_code="MTE",
        display_name="Motivasyon Trend Egimi",
        category="Duygu ve Gelisim",
        direction="higher_is_better",
        unit="slope",
        formula="Motivasyon skorunun zaman icindeki egimi",
        action_when_risky="Negatif motivasyon trendi icin kok neden ve takim iklimi analizi yapilmali.",
        source_columns=("KPI-16_Motivasyon_Trend_Egimi_MTE",),
    ),
    KPIDefinition(
        canonical_code="KPI-17 GKS",
        legacy_codes=(),
        short_code="GKS",
        display_name="Gelisim Katilim Skoru",
        category="Duygu ve Gelisim",
        direction="higher_is_better",
        unit="score",
        formula="Egitim ve gelisim etkinliklerine katilim",
        action_when_risky="Gelisim plani ve ogrenme firsatlari netlestirilmeli.",
        source_columns=("KPI-17_Gelisim_Katilim_Skoru_GKS",),
    ),
    KPIDefinition(
        canonical_code="KPI-18 GPS",
        legacy_codes=(),
        short_code="GPS",
        display_name="Genel Performans Skoru",
        category="Bilesik KPI",
        direction="higher_is_better",
        unit="score",
        formula="Performans sinyallerini birlestiren ust seviye skor",
        action_when_risky="Alt KPI kirilimlari uzerinden performans dususu analiz edilmeli.",
        source_columns=("general_performance_score", "KPI-18_Genel_Performans_Skoru_GPS"),
        is_model_feature=False,
        is_target_candidate=True,
    ),
    KPIDefinition(
        canonical_code="KPI-19 ARS",
        legacy_codes=(),
        short_code="ARS",
        display_name="Ayrilma Riski Skoru",
        category="Bilesik KPI",
        direction="lower_is_better",
        unit="score",
        formula="Ayrilma riski sinyallerini birlestiren ust seviye skor",
        action_when_risky="Ayrilma riski icin motivasyon, yuk ve yonetici destek sinyalleri incelenmeli.",
        source_columns=("attrition_risk_score", "KPI-19_Ayrilma_Riski_Skoru_ARS"),
        is_model_feature=False,
        is_target_candidate=True,
    ),
    KPIDefinition(
        canonical_code="KPI-20 PPE",
        legacy_codes=(),
        short_code="PPE",
        display_name="Potansiyel Performans Endeksi",
        category="Bilesik KPI",
        direction="higher_is_better",
        unit="score",
        formula="Yuksek potansiyel sinyallerini birlestiren endeks",
        action_when_risky="Potansiyel dusukse gelisim, mentorluk ve rol uyumu degerlendirilmeli.",
        source_columns=("KPI-20_Potansiyel_Performans_Endeksi_PPE",),
    ),
)


SOFTWARE_KPI_BY_CODE: dict[str, KPIDefinition] = {
    code: definition
    for definition in SOFTWARE_KPI_REGISTRY
    for code in definition.all_codes
}

SOFTWARE_KPI_BY_SOURCE_COLUMN: dict[str, KPIDefinition] = {
    column: definition
    for definition in SOFTWARE_KPI_REGISTRY
    for column in definition.source_columns
}


def get_software_kpi_definition(metric_code: str | None) -> KPIDefinition | None:
    if not metric_code:
        return None
    return SOFTWARE_KPI_BY_CODE.get(metric_code.strip())


def iter_software_import_columns() -> tuple[tuple[str, KPIDefinition], ...]:
    return tuple(SOFTWARE_KPI_BY_SOURCE_COLUMN.items())


def software_kpi_feature_name(definition: KPIDefinition) -> str:
    code = definition.canonical_code.lower().replace("-", "_")
    return re.sub(r"[^a-z0-9]+", "_", code).strip("_")


SOFTWARE_KPI_BY_FEATURE_NAME: dict[str, KPIDefinition] = {
    software_kpi_feature_name(definition): definition
    for definition in SOFTWARE_KPI_REGISTRY
}


def get_software_kpi_by_feature_name(feature_name: str | None) -> KPIDefinition | None:
    if not feature_name:
        return None

    normalized = feature_name
    for suffix in ("_lag_1", "_rolling_4", "_trend_4"):
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
            break

    return SOFTWARE_KPI_BY_FEATURE_NAME.get(normalized)


# ---------------------------------------------------------------------------
# Sales KPI Registry
# ---------------------------------------------------------------------------

SALES_KPI_REGISTRY: tuple[KPIDefinition, ...] = (
    # --- Uretkenlik & Hedef ---
    KPIDefinition(
        canonical_code="KPI-1 SHGO",
        legacy_codes=(),
        short_code="SHGO",
        display_name="Satis Hedef Gerceklesme Orani",
        category="Uretkenlik ve Hedef",
        direction="higher_is_better",
        unit="ratio",
        formula="Weekly_Sales_Revenue / Weekly_Sales_Target",
        thresholds=KPIThresholds(strong=1.0, stable=0.80, risk=0.80),
        action_when_risky="Hedef altinda kalan haftalar icin satis taktigi ve pipeline kalitesi gozden gecirilmeli.",
        source_columns=("sales_goal_attainment", "kpi-1_shgo", "Sales_Target_Achievement", "sales_target_achievement"),
    ),
    KPIDefinition(
        canonical_code="KPI-2 SAY",
        legacy_codes=(),
        short_code="SAY",
        display_name="Satis Aktivite Yogunlugu",
        category="Uretkenlik ve Hedef",
        direction="higher_is_better",
        unit="count",
        formula="Total_Activity",
        thresholds=KPIThresholds(strong=30.0, stable=15.0, risk=15.0),
        action_when_risky="Aktivite dususu icin musteri gorusme plani ve outreach ritmi gozden gecirilmeli.",
        source_columns=("Total_Activity",),
    ),
    KPIDefinition(
        canonical_code="KPI-3 NMKO",
        legacy_codes=(),
        short_code="NMKO",
        display_name="Yeni Musteri Kazanim Orani",
        category="Uretkenlik ve Hedef",
        direction="higher_is_better",
        unit="ratio",
        formula="New_Customer_Count / Total_Customer_Count",
        thresholds=KPIThresholds(strong=0.30, stable=0.15, risk=0.15),
        action_when_risky="Yeni musteri kazanim kanalları ve prospecting aktiviteleri guclendirilmeli.",
        source_columns=("new_customer_rate", "kpi-3_nmko", "New_Customer_Acquisition_Rate", "new_customer_acquisition_rate"),
    ),
    # --- Donusum ---
    KPIDefinition(
        canonical_code="KPI-4 LMDO",
        legacy_codes=(),
        short_code="LMDO",
        display_name="Lead Musteriye Donusturme Orani",
        category="Donusum",
        direction="higher_is_better",
        unit="ratio",
        formula="Lead_to_Win_Conversion",
        thresholds=KPIThresholds(strong=0.25, stable=0.10, risk=0.10),
        action_when_risky="Nitelendirme kriterleri, demo kalitesi ve takip ritmi incelenmeli.",
        source_columns=("Lead_to_Win_Conversion",),
    ),
    KPIDefinition(
        canonical_code="KPI-5 TKO",
        legacy_codes=(),
        short_code="TKO",
        display_name="Tekliften Kazanima Donusum Orani",
        category="Donusum",
        direction="higher_is_better",
        unit="ratio",
        formula="Won_Deal_Count / (Won_Deal_Count + Lost_Deal_Count)",
        thresholds=KPIThresholds(strong=0.50, stable=0.30, risk=0.30),
        action_when_risky="Kaybedilen teklif analizi yapilmali; fiyat, kapsam ve rekabetci faktorler incelenmeli.",
        source_columns=("win_rate", "kpi-5_tko", "Proposal_Win_Rate", "proposal_win_rate"),
    ),
    KPIDefinition(
        canonical_code="KPI-6 OSDS",
        legacy_codes=(),
        short_code="OSDS",
        display_name="Ortalama Satis Dongusu Suresi",
        category="Donusum",
        direction="lower_is_better",
        unit="days",
        formula="Average_Sales_Cycle_Days",
        thresholds=KPIThresholds(strong=30.0, stable=60.0, risk=60.0),
        action_when_risky="Uzayan dongulerde karar engelleri ve onay surecleri analiz edilmeli.",
        source_columns=("Average_Sales_Cycle_Days",),
    ),
    KPIDefinition(
        canonical_code="KPI-7 OSD",
        legacy_codes=(),
        short_code="OSD",
        display_name="Ortalama Satis Degeri",
        category="Donusum",
        direction="higher_is_better",
        unit="currency",
        formula="Average_Sale_Value",
        thresholds=KPIThresholds(strong=15000.0, stable=7500.0, risk=7500.0),
        action_when_risky="Dusuk degerli firsatlarda upsell ve cross-sell stratejisi gelistirilmeli.",
        source_columns=("Average_Sale_Value",),
    ),
    # --- Gelir Kalitesi ---
    KPIDefinition(
        canonical_code="KPI-8 GKP",
        legacy_codes=(),
        short_code="GKP",
        display_name="Goreli Kazanim Performansi",
        category="Gelir Kalitesi",
        direction="higher_is_better",
        unit="ratio",
        formula="Weekly_Sales_Revenue / team_avg_revenue",
        thresholds=KPIThresholds(strong=1.15, stable=0.85, risk=0.85),
        action_when_risky="Takim ortalamasinin altinda kalan kisilerle satis taktigi ve hesap planlama gorusmesi yapilmali.",
        source_columns=("Revenue_vs_Team", "KPI-8_GKP"),
    ),
    KPIDefinition(
        canonical_code="KPI-9 KKS",
        legacy_codes=(),
        short_code="KKS",
        display_name="Kazanim Kalite Skoru",
        category="Gelir Kalitesi",
        direction="higher_is_better",
        unit="count",
        formula="Won_Deal_Count",
        thresholds=KPIThresholds(strong=5.0, stable=2.0, risk=2.0),
        action_when_risky="Kazanim sayisi dusukse pipeline kalitesi ve nitelendirme asamasi incelenmeli.",
        source_columns=("Won_Deal_Count",),
    ),
    # --- Pipeline Sagligi ---
    KPIDefinition(
        canonical_code="KPI-10 PSO",
        legacy_codes=(),
        short_code="PSO",
        display_name="Pipeline Saglik Orani",
        category="Pipeline Sagligi",
        direction="higher_is_better",
        unit="ratio",
        formula="Pipeline_Value / Weekly_Sales_Target",
        thresholds=KPIThresholds(strong=3.0, stable=1.5, risk=1.5),
        action_when_risky="Pipeline dolulugu icin prospecting ve fırsat acma aktiviteleri arttirilmali.",
        source_columns=("pipeline_coverage", "kpi-10_pso", "Pipeline_Health_Ratio", "pipeline_health_ratio"),
    ),
    KPIDefinition(
        canonical_code="KPI-11 PYO",
        legacy_codes=(),
        short_code="PYO",
        display_name="Pipeline Yasta Olma Orani",
        category="Pipeline Sagligi",
        direction="lower_is_better",
        unit="ratio",
        formula="Aged_Opportunity_Count / Open_Opportunity_Count",
        thresholds=KPIThresholds(strong=0.20, stable=0.40, risk=0.40),
        action_when_risky="Yasli firsatlar temizlenmeli; uzayan dongulerin kok nedeni analiz edilmeli.",
        source_columns=("aged_pipeline_rate", "kpi-11_pyo", "Pipeline_Aging_Rate", "pipeline_aging_rate"),
    ),
    # --- Is Yuku ve Surdurulebilirlik ---
    KPIDefinition(
        canonical_code="KPI-12 SIYE",
        legacy_codes=(),
        short_code="SIYE",
        display_name="Satis Is Yuku Endeksi",
        category="Is Yuku ve Surdurulebilirlik",
        direction="optimal_range",
        unit="index",
        thresholds=KPIThresholds(optimal_min=0.7, optimal_max=1.2),
        formula="Sales_Workload_Index",
        action_when_risky="Is yuku dengelemesi icin hesap dagilimi ve gorev onceliklendirmesi yapilmali.",
        source_columns=("Sales_Workload_Index",),
    ),
    KPIDefinition(
        canonical_code="KPI-13 SIYS",
        legacy_codes=(),
        short_code="SIYS",
        display_name="Surekli Is Yuku Stres Skoru",
        category="Is Yuku ve Surdurulebilirlik",
        direction="lower_is_better",
        unit="score",
        formula="rolling_4_hafta_ort(SIYE) > 1.2 → artan risk skoru",
        thresholds=KPIThresholds(strong=0.0, stable=1.0, risk=2.0),
        action_when_risky="Suren yuksek is yuku burnout riski olusturur; kaynak dengeleme planlanmali.",
        source_columns=("overload_score", "kpi-13_siys"),
    ),
    # --- Musteri Odakliligi ---
    KPIDefinition(
        canonical_code="KPI-14 TDO",
        legacy_codes=(),
        short_code="TDO",
        display_name="Takip Disiplini Orani",
        category="Musteri Odakliligi",
        direction="higher_is_better",
        unit="ratio",
        formula="Followup_OnTime_Rate",
        thresholds=KPIThresholds(strong=0.90, stable=0.70, risk=0.70),
        action_when_risky="Zamaninda takip disiplini icin CRM hatirlaticlari ve gorev planlama incelenmeli.",
        source_columns=("Followup_OnTime_Rate",),
    ),
    KPIDefinition(
        canonical_code="KPI-15 CSAT",
        legacy_codes=(),
        short_code="CSAT",
        display_name="Musteri Memnuniyeti",
        category="Musteri Odakliligi",
        direction="higher_is_better",
        unit="score",
        formula="Customer_Satisfaction",
        thresholds=KPIThresholds(strong=4.5, stable=3.5, risk=3.5),
        action_when_risky="Dusuk memnuniyet skorlarinda musteri gorusmesi ve sikayet koku analizi yapilmali.",
        source_columns=("Customer_Satisfaction",),
    ),
    KPIDefinition(
        canonical_code="KPI-16 SO",
        legacy_codes=(),
        short_code="SO",
        display_name="Sikayet Orani",
        category="Musteri Odakliligi",
        direction="lower_is_better",
        unit="ratio",
        formula="Complaint_Count / Won_Deal_Count",
        thresholds=KPIThresholds(strong=0.05, stable=0.15, risk=0.15),
        action_when_risky="Sikayet kaynaklari tespit edilmeli; urun uyum ve teslimat sureci gozden gecirilmeli.",
        source_columns=("complaint_rate_derived", "complaint_rate", "kpi-16_so"),
    ),
    # --- CRM Disiplini ---
    KPIDefinition(
        canonical_code="KPI-17 CRMD",
        legacy_codes=(),
        short_code="CRMD",
        display_name="CRM Disiplin Metrigi",
        category="CRM Disiplini",
        direction="higher_is_better",
        unit="ratio",
        formula="CRM_Usage_Rate",
        thresholds=KPIThresholds(strong=0.90, stable=0.70, risk=0.70),
        action_when_risky="CRM kullanim disiplini icin egitim ve sure sureci hatirlaticlari uygulanmali.",
        source_columns=("CRM_Usage_Rate",),
    ),
    # --- Ekip Katki ---
    KPIDefinition(
        canonical_code="KPI-18 SEKS",
        legacy_codes=(),
        short_code="SEKS",
        display_name="Satis Ekibi Katki Skoru",
        category="Ekip Etkisi ve Is Birligi",
        direction="higher_is_better",
        unit="count",
        formula="Mentorship_Count + Peer_Support_Count",
        thresholds=KPIThresholds(strong=5.0, stable=2.0, risk=2.0),
        action_when_risky="Ekip katki dusukse mentoring programi ve bilgi paylasim ritmi desteklenmeli.",
        source_columns=("team_contribution", "kpi-18_seks", "Team_Contribution_Score", "team_contribution_score"),
    ),
    KPIDefinition(
        canonical_code="KPI-19 MS",
        legacy_codes=(),
        short_code="MS",
        display_name="Motivasyon Skoru",
        category="Duygu ve Gelisim",
        direction="higher_is_better",
        unit="score",
        formula="Motivation_Score",
        thresholds=KPIThresholds(strong=4.0, stable=3.0, risk=3.0),
        action_when_risky="Motivasyon dususu icin 1:1 gorusme ve engel analizi yapilmali.",
        source_columns=("Motivation_Score",),
    ),
    KPIDefinition(
        canonical_code="KPI-20 EKS",
        legacy_codes=(),
        short_code="EKS",
        display_name="Ekip Destek Katki Skoru",
        category="Ekip Etkisi ve Is Birligi",
        direction="higher_is_better",
        unit="count",
        formula="Peer_Support_Count",
        thresholds=KPIThresholds(strong=3.0, stable=1.0, risk=1.0),
        action_when_risky="Akran destek eksikligi icin takim ici isbirligi aktiviteleri arttirilmali.",
        source_columns=("Peer_Support_Count",),
    ),
    KPIDefinition(
        canonical_code="KPI-21 MTE",
        legacy_codes=(),
        short_code="MTE",
        display_name="Motivasyon Trend Egimi",
        category="Duygu ve Gelisim",
        direction="higher_is_better",
        unit="slope",
        formula="Motivation_Score son 4 haftalik dogrusal egim",
        thresholds=KPIThresholds(strong=0.1, stable=-0.1, risk=-0.1),
        action_when_risky="Negatif motivasyon trendi icin kok neden ve takim iklimi analizi yapilmali.",
        source_columns=("motivation_trend", "kpi-21_mte"),
    ),
    KPIDefinition(
        canonical_code="KPI-22 GKS",
        legacy_codes=(),
        short_code="GKS",
        display_name="Gelisim Katilim Skoru",
        category="Duygu ve Gelisim",
        direction="higher_is_better",
        unit="ratio",
        formula="Completed_Training_Count / Recommended_Training_Count",
        thresholds=KPIThresholds(strong=1.0, stable=0.60, risk=0.60),
        action_when_risky="Egitim katilim plani ve gelisim hedefleri netlestirilmeli.",
        source_columns=("training_completion", "kpi-22_gks", "Development_Participation_Rate", "development_participation_rate"),
    ),
    # --- Bilesik KPI (target candidates, not model features) ---
    KPIDefinition(
        canonical_code="KPI-23 SPS",
        legacy_codes=(),
        short_code="SPS",
        display_name="Satis Performans Skoru",
        category="Bilesik KPI",
        direction="higher_is_better",
        unit="score",
        formula="Hedef gerceklesme, donusum ve musteri odakliligi sinyallerini birlestiren skor",
        action_when_risky="Alt KPI kirilimlari uzerinden satis performans dususu analiz edilmeli.",
        source_columns=("KPI-23_SPS",),
        is_model_feature=False,
        is_target_candidate=True,
    ),
    KPIDefinition(
        canonical_code="KPI-24 BRS",
        legacy_codes=(),
        short_code="BRS",
        display_name="Burnout Risk Skoru",
        category="Bilesik KPI",
        direction="lower_is_better",
        unit="score",
        formula="Is yuku, motivasyon ve surekli stres sinyallerini birlestiren burnout risk skoru",
        action_when_risky="Burnout riski icin is yuku, motivasyon ve destek sinyalleri birlikte incelenmeli.",
        source_columns=("KPI-24_BRS",),
        is_model_feature=False,
        is_target_candidate=True,
    ),
    KPIDefinition(
        canonical_code="KPI-25 PPE",
        legacy_codes=(),
        short_code="PPE",
        display_name="Potansiyel Performans Endeksi",
        category="Bilesik KPI",
        direction="higher_is_better",
        unit="score",
        formula="Yuksek potansiyel sinyallerini birlestiren satis odakli endeks",
        action_when_risky="Potansiyel dusukse gelisim, mentorluk ve hesap planlama destegi degerlendirilmeli.",
        source_columns=("KPI-25_PPE",),
        is_model_feature=False,
        is_target_candidate=True,
    ),
)


SALES_KPI_BY_CODE: dict[str, KPIDefinition] = {
    code: definition
    for definition in SALES_KPI_REGISTRY
    for code in definition.all_codes
}

SALES_KPI_BY_SOURCE_COLUMN: dict[str, KPIDefinition] = {
    column: definition
    for definition in SALES_KPI_REGISTRY
    for column in definition.source_columns
}


def get_sales_kpi_definition(metric_code: str | None) -> KPIDefinition | None:
    if not metric_code:
        return None
    return SALES_KPI_BY_CODE.get(metric_code.strip())


def sales_kpi_feature_name(definition: KPIDefinition) -> str:
    code = definition.canonical_code.lower().replace("-", "_")
    return re.sub(r"[^a-z0-9]+", "_", code).strip("_")


SALES_KPI_BY_FEATURE_NAME: dict[str, KPIDefinition] = {
    sales_kpi_feature_name(definition): definition
    for definition in SALES_KPI_REGISTRY
}


def get_sales_kpi_by_feature_name(feature_name: str | None) -> KPIDefinition | None:
    if not feature_name:
        return None

    normalized = feature_name
    for suffix in ("_lag_1", "_rolling_4", "_trend_4"):
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
            break

    return SALES_KPI_BY_FEATURE_NAME.get(normalized)
