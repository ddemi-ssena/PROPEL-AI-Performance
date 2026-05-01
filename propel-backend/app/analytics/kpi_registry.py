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
