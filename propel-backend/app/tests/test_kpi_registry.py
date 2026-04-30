from app.analytics.kpi_registry import (
    SOFTWARE_KPI_BY_SOURCE_COLUMN,
    SOFTWARE_KPI_REGISTRY,
    get_software_kpi_definition,
)


def test_software_registry_contains_pdf_kpi_set():
    assert len(SOFTWARE_KPI_REGISTRY) == 20
    assert [item.canonical_code for item in SOFTWARE_KPI_REGISTRY][:5] == [
        "KPI-1 GTO",
        "KPI-2 ZTO",
        "KPI-3 GKE",
        "KPI-4 KKKE",
        "KPI-5 BY",
    ]


def test_software_registry_resolves_legacy_aliases():
    assert get_software_kpi_definition("KPI-4 KKE").canonical_code == "KPI-4 KKKE"
    assert get_software_kpi_definition("KPI-5 BO").canonical_code == "KPI-5 BY"
    assert get_software_kpi_definition("KPI-7 CKO").canonical_code == "KPI-7 CRKO"
    assert get_software_kpi_definition("KPI-8 ODS").canonical_code == "KPI-8 OPDS"
    assert get_software_kpi_definition("KPI-11 TTY").canonical_code == "KPI-11 TYO"


def test_software_registry_marks_risk_direction_correctly():
    assert get_software_kpi_definition("KPI-5 BY").higher_is_better is False
    assert get_software_kpi_definition("KPI-6 KBO").higher_is_better is False
    assert get_software_kpi_definition("KPI-8 OPDS").higher_is_better is False
    assert get_software_kpi_definition("KPI-19 ARS").higher_is_better is False
    assert get_software_kpi_definition("KPI-1 GTO").higher_is_better is True


def test_software_registry_maps_uploaded_dataset_columns():
    assert SOFTWARE_KPI_BY_SOURCE_COLUMN["KPI-1_Gorev_Tamamlama_Orani_GTO"].canonical_code == "KPI-1 GTO"
    assert SOFTWARE_KPI_BY_SOURCE_COLUMN["KPI-7_Code_Review_Kabul_Orani_CRKO"].canonical_code == "KPI-7 CRKO"
    assert SOFTWARE_KPI_BY_SOURCE_COLUMN["KPI-19_Ayrilma_Riski_Skoru_ARS"].canonical_code == "KPI-19 ARS"
