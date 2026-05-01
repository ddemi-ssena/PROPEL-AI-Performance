from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
import math
from typing import Any

from app.analytics.kpi_registry import KPIDefinition, SOFTWARE_KPI_REGISTRY, software_kpi_feature_name


SOFTWARE_TARGET_COLUMNS = ("performance_band", "attrition_risk_band")

SOFTWARE_OPERATIONAL_COLUMNS = (
    "assigned_tasks",
    "completed_tasks",
    "story_points_completed",
    "actual_work_hours",
    "project_complexity",
    "management_quality",
)


@dataclass
class SoftwareFeatureDataset:
    feature_rows: list[dict[str, Any]]
    target_rows: list[dict[str, Any]]
    metadata_rows: list[dict[str, Any]]
    feature_columns: list[str]
    target_columns: list[str]
    warnings: list[str] = field(default_factory=list)
    validation_summary: dict[str, Any] = field(default_factory=dict)


class SoftwareFeatureBuilder:
    @staticmethod
    def _feature_name(definition: KPIDefinition) -> str:
        return software_kpi_feature_name(definition)

    @staticmethod
    def _parse_float(value: Any) -> float | None:
        if value in (None, ""):
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if math.isnan(number) or math.isinf(number):
            return None
        return number

    @staticmethod
    def _parse_int(value: Any) -> int | None:
        number = SoftwareFeatureBuilder._parse_float(value)
        return int(number) if number is not None else None

    @staticmethod
    def _period_date(year: int, week: int) -> date | None:
        try:
            return date.fromisocalendar(year, week, 1)
        except ValueError:
            return None

    @staticmethod
    def _source_value(row: dict[str, Any], definition: KPIDefinition) -> tuple[str, Any] | None:
        for column_name in definition.source_columns:
            if column_name in row and row[column_name] not in (None, ""):
                return column_name, row[column_name]
        return None

    @staticmethod
    def _normalize_kpi_value(value: Any, definition: KPIDefinition) -> float | None:
        number = SoftwareFeatureBuilder._parse_float(value)
        if number is None:
            return None

        # CSV exports may express ratios either as 0-1 values or as percentages.
        if definition.unit == "ratio" and number > 1.5:
            return round(number / 100, 6)

        return round(number, 6)

    @staticmethod
    def _build_base_feature_row(row: dict[str, Any]) -> dict[str, Any]:
        feature_row: dict[str, Any] = {
            "team": row.get("team"),
            "role": row.get("role"),
            "experience_years": SoftwareFeatureBuilder._parse_float(row.get("experience_years")),
        }

        week = SoftwareFeatureBuilder._parse_int(row.get("week"))
        if week is not None:
            feature_row["week"] = week
            feature_row["week_sin"] = round(math.sin(2 * math.pi * week / 52), 6)
            feature_row["week_cos"] = round(math.cos(2 * math.pi * week / 52), 6)

        for column_name in SOFTWARE_OPERATIONAL_COLUMNS:
            if column_name in row:
                feature_row[column_name] = SoftwareFeatureBuilder._parse_float(row.get(column_name))

        assigned = feature_row.get("assigned_tasks")
        completed = feature_row.get("completed_tasks")
        if assigned not in (None, 0) and completed is not None:
            feature_row["task_completion_delta"] = round(completed - assigned, 6)

        return feature_row

    @staticmethod
    def _add_kpi_features(row: dict[str, Any], feature_row: dict[str, Any]) -> None:
        for definition in SOFTWARE_KPI_REGISTRY:
            if not definition.is_model_feature:
                continue

            source = SoftwareFeatureBuilder._source_value(row, definition)
            if not source:
                continue

            _, raw_value = source
            value = SoftwareFeatureBuilder._normalize_kpi_value(raw_value, definition)
            if value is None:
                continue

            feature_row[SoftwareFeatureBuilder._feature_name(definition)] = value

    @staticmethod
    def _add_time_features(feature_rows: list[dict[str, Any]], metadata_rows: list[dict[str, Any]]) -> None:
        combined = list(zip(feature_rows, metadata_rows))
        combined.sort(key=lambda item: (item[1]["employee_id"], item[1]["year"], item[1]["week"]))

        history_by_employee: dict[int, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        kpi_columns = sorted(
            {
                key
                for feature_row in feature_rows
                for key, value in feature_row.items()
                if key.startswith("kpi_") and isinstance(value, (int, float))
            }
        )

        for feature_row, metadata in combined:
            employee_history = history_by_employee[metadata["employee_id"]]
            for column_name in kpi_columns:
                value = feature_row.get(column_name)
                if not isinstance(value, (int, float)):
                    continue

                previous_values = employee_history[column_name]
                if previous_values:
                    feature_row[f"{column_name}_lag_1"] = previous_values[-1]
                    rolling_values = previous_values[-4:]
                    feature_row[f"{column_name}_rolling_4"] = round(sum(rolling_values) / len(rolling_values), 6)
                    feature_row[f"{column_name}_trend_4"] = round(value - feature_row[f"{column_name}_rolling_4"], 6)
                else:
                    feature_row[f"{column_name}_lag_1"] = None
                    feature_row[f"{column_name}_rolling_4"] = None
                    feature_row[f"{column_name}_trend_4"] = None

                previous_values.append(value)

    @staticmethod
    def build_from_rows(
        rows: list[dict[str, Any]],
        include_time_features: bool = True,
    ) -> SoftwareFeatureDataset:
        feature_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        metadata_rows: list[dict[str, Any]] = []
        warnings: list[str] = []

        for row_number, row in enumerate(rows, start=1):
            employee_id = SoftwareFeatureBuilder._parse_int(row.get("employee_id"))
            year = SoftwareFeatureBuilder._parse_int(row.get("year"))
            week = SoftwareFeatureBuilder._parse_int(row.get("week"))
            if employee_id is None or year is None or week is None:
                warnings.append(f"Row {row_number}: employee_id/year/week eksik oldugu icin atlandi.")
                continue

            period_date = SoftwareFeatureBuilder._period_date(year, week)
            if period_date is None:
                warnings.append(f"Row {row_number}: gecersiz ISO hafta bilgisi ({year}, {week}) oldugu icin atlandi.")
                continue

            feature_row = SoftwareFeatureBuilder._build_base_feature_row(row)
            SoftwareFeatureBuilder._add_kpi_features(row, feature_row)

            target_row = {
                target_column: row.get(target_column)
                for target_column in SOFTWARE_TARGET_COLUMNS
                if target_column in row and row.get(target_column) not in (None, "")
            }

            feature_rows.append(feature_row)
            target_rows.append(target_row)
            metadata_rows.append(
                {
                    "employee_id": employee_id,
                    "team": row.get("team"),
                    "role": row.get("role"),
                    "year": year,
                    "week": week,
                    "period_date": period_date.isoformat(),
                }
            )

        if include_time_features:
            SoftwareFeatureBuilder._add_time_features(feature_rows, metadata_rows)

        feature_columns = sorted({key for row in feature_rows for key in row})
        target_columns = sorted({key for row in target_rows for key in row})

        validation_summary = {
            "row_count": len(feature_rows),
            "employee_count": len({row["employee_id"] for row in metadata_rows}),
            "period_count": len({row["period_date"] for row in metadata_rows}),
            "feature_count": len(feature_columns),
            "target_columns": target_columns,
            "target_distribution": {
                target_column: dict(Counter(row.get(target_column) for row in target_rows if row.get(target_column)))
                for target_column in SOFTWARE_TARGET_COLUMNS
            },
            "excluded_target_like_kpis": [
                definition.canonical_code
                for definition in SOFTWARE_KPI_REGISTRY
                if definition.is_target_candidate and not definition.is_model_feature
            ],
        }

        return SoftwareFeatureDataset(
            feature_rows=feature_rows,
            target_rows=target_rows,
            metadata_rows=metadata_rows,
            feature_columns=feature_columns,
            target_columns=target_columns,
            warnings=warnings,
            validation_summary=validation_summary,
        )
