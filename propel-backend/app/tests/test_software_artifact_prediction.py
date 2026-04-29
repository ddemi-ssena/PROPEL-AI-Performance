import csv
from pathlib import Path

from app.analytics.artifacts.software import SoftwareArtifactStore
from app.analytics.prediction.software import SoftwarePredictionService
from app.analytics.training.software import SoftwareBaselineTrainer


def test_software_train_save_load_predict(tmp_path: Path):
    rows = []
    for week in range(1, 15):
        rows.append(
            {
                "employee_id": "1",
                "team": "Backend",
                "role": "Mid",
                "experience_years": "5",
                "week": str(week),
                "year": "2025",
                "KPI-1_Gorev_Tamamlama_Orani_GTO": "0.90" if week < 10 else "0.60",
                "KPI-5_Bug_Yogunlugu_BY": "0.25" if week < 10 else "0.75",
                "KPI-15_Motivasyon_Skoru_MS": "80" if week < 10 else "55",
                "performance_band": "Stabil" if week < 10 else "Riskli",
            }
        )

    result = SoftwareBaselineTrainer.train(
        rows,
        target_column="performance_band",
        model_name="random_forest",
        test_period_count=4,
    )
    store = SoftwareArtifactStore(tmp_path)
    saved = store.save_training_result(result)
    loaded = store.load("performance_band")

    assert saved.model_path.exists()
    assert saved.metadata_path.exists()
    prediction = SoftwarePredictionService.predict_latest(loaded, rows[-3:])

    assert prediction.department == "software"
    assert prediction.target_column == "performance_band"
    assert prediction.predicted_band in {"Riskli", "Stabil"}
    assert prediction.summary_payload["employee_id"] == 1
