from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
import math
import re
from typing import Any

from app.analytics.kpi_registry import KPIDefinition, SALES_KPI_REGISTRY, sales_kpi_feature_name


SALES_TARGET_COLUMNS = (
    "Performance_Drop_Target",
    "Burnout_Target",
    "Resignation_Target",
    "High_Risk_Target",
)

SALES_DIRECT_COLUMNS = (
    "Total_Activity",
    "Lead_to_Win_Conversion",
    "Average_Sales_Cycle_Days",
    "Average_Sale_Value",
    "Won_Deal_Count",
    "Sales_Workload_Index",
    "Followup_OnTime_Rate",
    "Customer_Satisfaction",
    "CRM_Usage_Rate",
    "Motivation_Score",
    "Peer_Support_Count",
    "Mentorship_Count",
)


@dataclass
class SalesFeatureDataset:
    feature_rows: list[dict[str, Any]]
    target_rows: list[dict[str, Any]]
    metadata_rows: list[dict[str, Any]]
    feature_columns: list[str]
    target_columns: list[str]
    warnings: list[str] = field(default_factory=list)
    validation_summary: dict[str, Any] = field(default_factory=dict)


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    """Lowercase all keys so column name casing doesn't matter."""
    return {k.lower(): v for k, v in row.items()}


def _parse_employee_id_raw(value: Any) -> int | None:
    """Parse EMP_001, SE-001, 1, '1', etc. → integer."""
    if value in (None, ""):
        return None
    text = str(value).strip()
    # Try direct int
    try:
        return int(float(text))
    except ValueError:
        pass
    # Try extracting digits from prefixed codes like EMP_001, SA-003, SE-005
    digits = re.sub(r"[^0-9]", "", text)
    if digits:
        return int(digits)
    return None


class SalesFeatureBuilder:
    @staticmethod
    def _feature_name(definition: KPIDefinition) -> str:
        return sales_kpi_feature_name(definition)

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
        number = SalesFeatureBuilder._parse_float(value)
        return int(number) if number is not None else None

    @staticmethod
    def _period_date(year: int, week: int) -> date | None:
        try:
            return date.fromisocalendar(year, week, 1)
        except ValueError:
            return None

    @staticmethod
    def _safe_div(numerator: float | None, denominator: float | None) -> float | None:
        if numerator is None or denominator is None or denominator == 0:
            return None
        return round(numerator / denominator, 6)

    @staticmethod
    def _compute_derived(row: dict[str, Any]) -> dict[str, Any]:
        """
        Row must already be lowercase-normalized.
        Use pre-computed columns when available, otherwise compute from raw columns.
        """
        derived: dict[str, Any] = {}

        # KPI-1 SHGO: use pre-computed or compute from revenue/target
        shgo = SalesFeatureBuilder._parse_float(row.get("sales_target_achievement"))
        if shgo is None:
            revenue = SalesFeatureBuilder._parse_float(row.get("weekly_sales_revenue"))
            target = SalesFeatureBuilder._parse_float(row.get("weekly_sales_target"))
            shgo = SalesFeatureBuilder._safe_div(revenue, target)
        if shgo is not None:
            derived["sales_goal_attainment"] = shgo

        # KPI-3 NMKO: use pre-computed or compute
        nmko = SalesFeatureBuilder._parse_float(row.get("new_customer_acquisition_rate"))
        if nmko is None:
            new_cust = SalesFeatureBuilder._parse_float(row.get("new_customer_count"))
            total_cust = SalesFeatureBuilder._parse_float(row.get("total_customer_count"))
            nmko = SalesFeatureBuilder._safe_div(new_cust, total_cust)
        if nmko is not None:
            derived["new_customer_rate"] = nmko

        # KPI-5 TKO: use proposal_win_rate if available, else compute
        tko = SalesFeatureBuilder._parse_float(row.get("proposal_win_rate"))
        if tko is None:
            won = SalesFeatureBuilder._parse_float(row.get("won_deal_count"))
            lost = SalesFeatureBuilder._parse_float(row.get("lost_deal_count"))
            if won is not None and lost is not None:
                tko = SalesFeatureBuilder._safe_div(won, won + lost)
        if tko is not None:
            derived["win_rate"] = tko

        # KPI-10 PSO: use pipeline_health_ratio or compute
        pso = SalesFeatureBuilder._parse_float(row.get("pipeline_health_ratio"))
        if pso is None:
            pipeline = SalesFeatureBuilder._parse_float(row.get("pipeline_value"))
            target = SalesFeatureBuilder._parse_float(row.get("weekly_sales_target"))
            pso = SalesFeatureBuilder._safe_div(pipeline, target)
        if pso is not None:
            derived["pipeline_coverage"] = pso

        # KPI-11 PYO: use pipeline_aging_rate or compute
        pyo = SalesFeatureBuilder._parse_float(row.get("pipeline_aging_rate"))
        if pyo is None:
            aged = SalesFeatureBuilder._parse_float(row.get("aged_opportunity_count"))
            open_opp = SalesFeatureBuilder._parse_float(row.get("open_opportunity_count"))
            pyo = SalesFeatureBuilder._safe_div(aged, open_opp)
        if pyo is not None:
            derived["aged_pipeline_rate"] = pyo

        # KPI-16 SO: use complaint_rate or compute
        so = SalesFeatureBuilder._parse_float(row.get("complaint_rate"))
        if so is None:
            complaints = SalesFeatureBuilder._parse_float(row.get("complaint_count"))
            won = SalesFeatureBuilder._parse_float(row.get("won_deal_count"))
            so = SalesFeatureBuilder._safe_div(complaints, won)
        if so is not None:
            derived["complaint_rate_derived"] = so

        # KPI-18 SEKS: use team_contribution_score or compute
        seks = SalesFeatureBuilder._parse_float(row.get("team_contribution_score"))
        if seks is None:
            mentorship = SalesFeatureBuilder._parse_float(row.get("mentorship_count"))
            peer = SalesFeatureBuilder._parse_float(row.get("peer_support_count"))
            if mentorship is not None and peer is not None:
                seks = round(mentorship + peer, 6)
            elif mentorship is not None:
                seks = mentorship
            elif peer is not None:
                seks = peer
        if seks is not None:
            derived["team_contribution"] = seks

        # KPI-22 GKS: use development_participation_rate or compute
        gks = SalesFeatureBuilder._parse_float(row.get("development_participation_rate"))
        if gks is None:
            completed = SalesFeatureBuilder._parse_float(row.get("completed_training_count"))
            recommended = SalesFeatureBuilder._parse_float(row.get("recommended_training_count"))
            gks = SalesFeatureBuilder._safe_div(completed, recommended)
        if gks is not None:
            derived["training_completion"] = gks

        return derived

    @staticmethod
    def _build_base_feature_row(row: dict[str, Any], derived: dict[str, Any]) -> dict[str, Any]:
        feature_row: dict[str, Any] = {
            "team": row.get("region") or row.get("team") or row.get("department"),
            "role": row.get("role_level") or row.get("role"),
        }

        week = SalesFeatureBuilder._parse_int(row.get("week"))
        if week is not None:
            feature_row["week"] = week
            feature_row["week_sin"] = round(math.sin(2 * math.pi * week / 52), 6)
            feature_row["week_cos"] = round(math.cos(2 * math.pi * week / 52), 6)

        seniority = SalesFeatureBuilder._parse_float(row.get("seniority_years"))
        if seniority is not None:
            feature_row["seniority_years"] = seniority

        # Direct numeric columns (lowercase lookup)
        direct_cols = [
            "total_activity", "lead_to_win_conversion", "average_sales_cycle_days",
            "average_sale_value", "won_deal_count", "lost_deal_count",
            "sales_workload_index", "followup_ontime_rate", "customer_satisfaction",
            "crm_usage_rate", "motivation_score", "peer_support_count",
            "mentorship_count", "pipeline_value", "aged_opportunity_count",
            "open_opportunity_count", "complaint_count", "new_customer_count",
            "total_customer_count", "weekly_call_count", "weekly_email_count",
            "weekly_meeting_count", "weekly_proposal_count", "weekly_followup_count",
            "upsell_crosssell_revenue", "upsell_crosssell_rate", "lead_count",
            "completed_training_count", "recommended_training_count",
        ]
        for col in direct_cols:
            val = SalesFeatureBuilder._parse_float(row.get(col))
            if val is not None:
                feature_row[col] = val

        return feature_row

    @staticmethod
    def _source_value(row: dict[str, Any], derived: dict[str, Any], definition: KPIDefinition) -> tuple[str, Any] | None:
        augmented = {**row, **derived}
        for column_name in definition.source_columns:
            key = column_name.lower()
            if key in augmented and augmented[key] not in (None, ""):
                return key, augmented[key]
        return None

    @staticmethod
    def _normalize_kpi_value(value: Any, definition: KPIDefinition) -> float | None:
        number = SalesFeatureBuilder._parse_float(value)
        if number is None:
            return None
        if definition.unit == "ratio" and number > 1.5:
            return round(number / 100, 6)
        return round(number, 6)

    @staticmethod
    def _add_kpi_features(row: dict[str, Any], derived: dict[str, Any], feature_row: dict[str, Any]) -> None:
        for definition in SALES_KPI_REGISTRY:
            if not definition.is_model_feature:
                continue
            source = SalesFeatureBuilder._source_value(row, derived, definition)
            if not source:
                continue
            _, raw_value = source
            value = SalesFeatureBuilder._normalize_kpi_value(raw_value, definition)
            if value is None:
                continue
            feature_row[SalesFeatureBuilder._feature_name(definition)] = value

    @staticmethod
    def _add_time_features(feature_rows: list[dict[str, Any]], metadata_rows: list[dict[str, Any]]) -> None:
        combined = list(zip(feature_rows, metadata_rows))
        combined.sort(key=lambda item: (item[1]["employee_id"], item[1]["year"], item[1]["week"]))

        kpi_columns = sorted(
            {
                key
                for feature_row in feature_rows
                for key, value in feature_row.items()
                if key.startswith("kpi_") and isinstance(value, (int, float))
            }
        )

        history_by_employee: dict[int, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        siy_history_by_employee: dict[int, list[float]] = defaultdict(list)

        for feature_row, metadata in combined:
            eid = metadata["employee_id"]
            employee_history = history_by_employee[eid]

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

            # KPI-13 SIYS: rolling overload score
            siy_raw = feature_row.get("sales_workload_index") or feature_row.get("kpi_12_siye")
            if siy_raw is not None:
                siy_hist = siy_history_by_employee[eid]
                siy_hist.append(float(siy_raw))
                recent = siy_hist[-4:]
                overload_weeks = sum(1 for s in recent if s > 1.2)
                feature_row["overload_score"] = float(overload_weeks)

            # KPI-21 MTE: motivation trend slope over last 4 weeks
            ms_value = feature_row.get("motivation_score") or feature_row.get("kpi_19_ms")
            if isinstance(ms_value, (int, float)):
                ms_hist = employee_history["motivation_score_hist"]
                ms_hist.append(float(ms_value))
                recent_ms = ms_hist[-4:]
                if len(recent_ms) >= 2:
                    n = len(recent_ms)
                    xs = list(range(n))
                    mean_x = sum(xs) / n
                    mean_y = sum(recent_ms) / n
                    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, recent_ms))
                    den = sum((x - mean_x) ** 2 for x in xs)
                    feature_row["motivation_trend"] = round(num / den, 6) if den != 0 else 0.0

    @staticmethod
    def _add_team_relative_features(
        feature_rows: list[dict[str, Any]],
        metadata_rows: list[dict[str, Any]],
        revenue_rows: list[float | None],
    ) -> None:
        team_period_revenues: dict[tuple[str, str], list[float]] = defaultdict(list)
        for meta, rev in zip(metadata_rows, revenue_rows):
            if rev is None:
                continue
            key = (str(meta.get("team") or ""), str(meta.get("period_date") or ""))
            team_period_revenues[key].append(rev)

        for feature_row, meta, rev in zip(feature_rows, metadata_rows, revenue_rows):
            if rev is None:
                continue
            key = (str(meta.get("team") or ""), str(meta.get("period_date") or ""))
            team_revs = team_period_revenues.get(key, [])
            if not team_revs:
                continue
            team_avg = sum(team_revs) / len(team_revs)
            if team_avg > 0:
                feature_row["revenue_vs_team"] = round(rev / team_avg, 6)

    @staticmethod
    def build_from_rows(
        rows: list[dict[str, Any]],
        include_time_features: bool = True,
    ) -> SalesFeatureDataset:
        feature_rows: list[dict[str, Any]] = []
        target_rows: list[dict[str, Any]] = []
        metadata_rows: list[dict[str, Any]] = []
        revenue_rows: list[float | None] = []
        warnings: list[str] = []

        for row_number, raw_row in enumerate(rows, start=1):
            # Normalize all keys to lowercase
            row = _normalize_row(raw_row)

            # Parse employee_id — handle EMP_001, SE-001, integers
            employee_id = _parse_employee_id_raw(
                row.get("employee_id") or row.get("employee id")
            )
            if employee_id is None:
                warnings.append(f"Row {row_number}: employee_id eksik/gecersiz, atlandi.")
                continue

            # Parse week
            week = SalesFeatureBuilder._parse_int(row.get("week"))
            if week is None:
                warnings.append(f"Row {row_number}: week eksik, atlandi.")
                continue

            # Parse year — not always present, default to 2024
            year = SalesFeatureBuilder._parse_int(row.get("year"))
            if year is None:
                year = 2024

            period_date = SalesFeatureBuilder._period_date(year, week)
            if period_date is None:
                warnings.append(f"Row {row_number}: gecersiz ISO hafta ({year}, {week}), atlandi.")
                continue

            derived = SalesFeatureBuilder._compute_derived(row)
            feature_row = SalesFeatureBuilder._build_base_feature_row(row, derived)
            SalesFeatureBuilder._add_kpi_features(row, derived, feature_row)

            # Targets — handle both int (0/1) and string ('0'/'1')
            target_row = {}
            for target_col in SALES_TARGET_COLUMNS:
                val = row.get(target_col.lower())
                if val not in (None, ""):
                    target_row[target_col] = str(int(float(val)))

            revenue = SalesFeatureBuilder._parse_float(row.get("weekly_sales_revenue"))
            revenue_rows.append(revenue)
            feature_rows.append(feature_row)
            target_rows.append(target_row)
            metadata_rows.append(
                {
                    "employee_id": employee_id,
                    "team": feature_row.get("team"),
                    "role": feature_row.get("role"),
                    "year": year,
                    "week": week,
                    "period_date": period_date.isoformat(),
                }
            )

        if include_time_features:
            SalesFeatureBuilder._add_time_features(feature_rows, metadata_rows)
            SalesFeatureBuilder._add_team_relative_features(feature_rows, metadata_rows, revenue_rows)

        feature_columns = sorted({key for row in feature_rows for key in row})
        target_columns = sorted({key for row in target_rows for key in row})

        validation_summary = {
            "row_count": len(feature_rows),
            "employee_count": len({row["employee_id"] for row in metadata_rows}),
            "period_count": len({row["period_date"] for row in metadata_rows}),
            "feature_count": len(feature_columns),
            "target_columns": target_columns,
            "target_distribution": {
                target_col: dict(Counter(row.get(target_col) for row in target_rows if row.get(target_col)))
                for target_col in SALES_TARGET_COLUMNS
            },
            "excluded_target_like_kpis": [
                definition.canonical_code
                for definition in SALES_KPI_REGISTRY
                if definition.is_target_candidate and not definition.is_model_feature
            ],
            "warnings_count": len(warnings),
        }

        return SalesFeatureDataset(
            feature_rows=feature_rows,
            target_rows=target_rows,
            metadata_rows=metadata_rows,
            feature_columns=feature_columns,
            target_columns=target_columns,
            warnings=warnings,
            validation_summary=validation_summary,
        )
