from app.analytics.features.software import SoftwareFeatureBuilder


def test_software_feature_builder_maps_kpis_and_targets():
    dataset = SoftwareFeatureBuilder.build_from_rows(
        [
            {
                "employee_id": "1",
                "team": "Backend",
                "role": "Mid",
                "experience_years": "5.8",
                "week": "1",
                "year": "2025",
                "assigned_tasks": "10",
                "completed_tasks": "8",
                "KPI-1_Gorev_Tamamlama_Orani_GTO": "0.82",
                "KPI-5_Bug_Yogunlugu_BY": "0.57",
                "KPI-18_Genel_Performans_Skoru_GPS": "71.3",
                "KPI-19_Ayrilma_Riski_Skoru_ARS": "0.18",
                "performance_band": "Stabil",
                "attrition_risk_band": "Dusuk",
            }
        ]
    )

    assert dataset.validation_summary["row_count"] == 1
    assert dataset.feature_rows[0]["kpi_1_gto"] == 0.82
    assert dataset.feature_rows[0]["kpi_5_by"] == 0.57
    assert "kpi_18_gps" not in dataset.feature_rows[0]
    assert "kpi_19_ars" not in dataset.feature_rows[0]
    assert dataset.target_rows[0]["performance_band"] == "Stabil"
    assert dataset.target_rows[0]["attrition_risk_band"] == "Dusuk"


def test_software_feature_builder_adds_employee_time_features():
    dataset = SoftwareFeatureBuilder.build_from_rows(
        [
            {
                "employee_id": "1",
                "team": "Backend",
                "role": "Mid",
                "week": "1",
                "year": "2025",
                "KPI-1_Gorev_Tamamlama_Orani_GTO": "0.80",
            },
            {
                "employee_id": "1",
                "team": "Backend",
                "role": "Mid",
                "week": "2",
                "year": "2025",
                "KPI-1_Gorev_Tamamlama_Orani_GTO": "0.90",
            },
        ]
    )

    assert dataset.feature_rows[0]["kpi_1_gto_lag_1"] is None
    assert dataset.feature_rows[1]["kpi_1_gto_lag_1"] == 0.80
    assert dataset.feature_rows[1]["kpi_1_gto_rolling_4"] == 0.80
    assert round(dataset.feature_rows[1]["kpi_1_gto_trend_4"], 6) == 0.10
