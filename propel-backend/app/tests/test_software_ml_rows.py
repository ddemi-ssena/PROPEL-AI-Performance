import json
from pathlib import Path

import pandas as pd
import pytest

from app.services.software_ml_service import SoftwareMLService


def test_load_rows_supports_xlsx(tmp_path: Path):
    path = tmp_path / "software.xlsx"
    pd.DataFrame(
        [
            {
                "employee_id": 1,
                "team": "Backend",
                "week": 1,
                "performance_band": "Stabil",
            }
        ]
    ).to_excel(path, index=False)

    rows = SoftwareMLService._load_rows(path)

    assert rows == [
        {
            "employee_id": 1,
            "team": "Backend",
            "week": 1,
            "performance_band": "Stabil",
        }
    ]


def test_load_rows_rejects_invalid_json_shape(tmp_path: Path):
    path = tmp_path / "software.json"
    path.write_text(json.dumps("not-a-row"), encoding="utf-8")

    with pytest.raises(Exception) as exc_info:
        SoftwareMLService._load_rows(path)

    assert "JSON icerigi" in exc_info.value.detail
