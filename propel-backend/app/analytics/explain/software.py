from __future__ import annotations

from typing import Any

from app.analytics.kpi_registry import KPIDefinition, get_software_kpi_by_feature_name


class SoftwareExplanationBuilder:
    @staticmethod
    def _risk_level(target_column: str, predicted_band: str) -> str:
        if target_column == "attrition_risk_band":
            return {"Yuksek": "high", "Orta": "medium", "Dusuk": "low"}.get(predicted_band, "medium")
        return {"Riskli": "high", "Stabil": "medium", "Yuksek": "low", "Guclu": "low"}.get(
            predicted_band,
            "medium",
        )

    @staticmethod
    def _format_value(value: Any) -> float | str | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return round(float(value), 4)
        return str(value)

    @staticmethod
    def _numeric_value(value: Any) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _threshold_status(definition: KPIDefinition, current_value: Any) -> str:
        value = SoftwareExplanationBuilder._numeric_value(current_value)
        if value is None:
            return "Veri yorumu icin sayisal deger yok"

        thresholds = definition.thresholds
        if definition.direction == "optimal_range":
            if thresholds.optimal_min is not None and value < thresholds.optimal_min:
                return "Optimal araligin altinda"
            if thresholds.optimal_max is not None and value > thresholds.optimal_max:
                return "Optimal araligin ustunde"
            return "Optimal aralikta"

        if definition.direction == "lower_is_better":
            if thresholds.risk is not None and value > thresholds.risk:
                return "Risk esiginin ustunde"
            if thresholds.strong is not None and value <= thresholds.strong:
                return "Guclu seviyede"
            return "Izleme seviyesinde"

        if thresholds.risk is not None and value < thresholds.risk:
            return "Risk esiginin altinda"
        if thresholds.strong is not None and value >= thresholds.strong:
            return "Guclu seviyede"
        return "Izleme seviyesinde"

    @staticmethod
    def _trend_signal(definition: KPIDefinition, trend_value: Any) -> str:
        trend = SoftwareExplanationBuilder._numeric_value(trend_value)
        if trend is None:
            return "Trend verisi yok"
        if abs(trend) < 0.0001:
            return "Trend yatay"

        if definition.direction == "lower_is_better":
            return "Trend olumsuzlesiyor" if trend > 0 else "Trend iyilesiyor"
        return "Trend iyilesiyor" if trend > 0 else "Trend olumsuzlesiyor"

    @staticmethod
    def _driver_signal(feature_name: str, value: Any, definition: KPIDefinition) -> str:
        if feature_name.endswith("_trend_4"):
            return SoftwareExplanationBuilder._trend_signal(definition, value)

        if feature_name.endswith("_rolling_4"):
            return "Son 4 haftalik ortalama sinyali"

        if feature_name.endswith("_lag_1"):
            return "Onceki hafta sinyali"

        return "Guncel KPI sinyali"

    @staticmethod
    def _driver_rationale(
        definition: KPIDefinition,
        current_value: Any,
        trend_value: Any,
        predicted_band: str,
        target_column: str,
    ) -> str:
        threshold_status = SoftwareExplanationBuilder._threshold_status(definition, current_value)
        trend_signal = SoftwareExplanationBuilder._trend_signal(definition, trend_value)
        value_text = SoftwareExplanationBuilder._format_value(current_value)
        target_label = "performans" if target_column == "performance_band" else "ayrilma riski"

        return (
            f"{definition.display_name} {target_label} tahmininde one cikan bir surucu. "
            f"Guncel deger {value_text}; durum: {threshold_status}. "
            f"Son 4 haftalik yorum: {trend_signal}. "
            f"Bu nedenle model {predicted_band} sonucunu destekleyen sinyallerden biri olarak degerlendirdi."
        )

    @staticmethod
    def build(
        target_column: str,
        predicted_band: str,
        confidence: float,
        feature_row: dict[str, Any],
        top_features: list[dict[str, float]],
        limit: int = 5,
    ) -> dict[str, Any]:
        drivers: list[dict[str, Any]] = []
        actions: list[str] = []
        seen_actions: set[str] = set()

        for item in top_features:
            feature_name = str(item.get("feature", ""))
            definition = get_software_kpi_by_feature_name(feature_name)
            if not definition:
                continue

            value = feature_row.get(feature_name)
            base_feature = feature_name
            for suffix in ("_lag_1", "_rolling_4", "_trend_4"):
                if base_feature.endswith(suffix):
                    base_feature = base_feature[: -len(suffix)]
                    break

            current_value = feature_row.get(base_feature)
            trend_value = feature_row.get(f"{base_feature}_trend_4")
            threshold_status = SoftwareExplanationBuilder._threshold_status(definition, current_value)
            trend_signal = SoftwareExplanationBuilder._trend_signal(definition, trend_value)

            drivers.append(
                {
                    "feature": feature_name,
                    "metric_code": definition.canonical_code,
                    "metric_name": definition.display_name,
                    "category": definition.category,
                    "direction": definition.direction,
                    "importance": round(float(item.get("importance", 0)), 6),
                    "value": SoftwareExplanationBuilder._format_value(value),
                    "current_value": SoftwareExplanationBuilder._format_value(current_value),
                    "trend_4": SoftwareExplanationBuilder._format_value(trend_value),
                    "threshold_status": threshold_status,
                    "trend_signal": trend_signal,
                    "signal": SoftwareExplanationBuilder._driver_signal(feature_name, value, definition),
                    "rationale": SoftwareExplanationBuilder._driver_rationale(
                        definition=definition,
                        current_value=current_value,
                        trend_value=trend_value,
                        predicted_band=predicted_band,
                        target_column=target_column,
                    ),
                }
            )

            if definition.action_when_risky not in seen_actions:
                seen_actions.add(definition.action_when_risky)
                actions.append(definition.action_when_risky)

            if len(drivers) >= limit:
                break

        risk_summary = SoftwareExplanationBuilder._summary_text(
            target_column=target_column,
            predicted_band=predicted_band,
            confidence=confidence,
            drivers=drivers,
        )

        return {
            "risk_summary": risk_summary,
            "top_drivers": drivers,
            "recommended_actions": actions[:limit],
        }

    @staticmethod
    def _summary_text(
        target_column: str,
        predicted_band: str,
        confidence: float,
        drivers: list[dict[str, Any]],
    ) -> str:
        target_label = "performans" if target_column == "performance_band" else "ayrilma riski"
        confidence_percent = round(confidence * 100, 1)
        risk_level = SoftwareExplanationBuilder._risk_level(target_column, predicted_band)
        if risk_level == "high":
            posture = "Oncelikli takip gerektiren"
        elif risk_level == "medium":
            posture = "Izleme gerektiren"
        else:
            posture = "Korunmasi gereken"

        if drivers:
            unique_driver_names: list[str] = []
            for driver in drivers:
                if driver["metric_name"] not in unique_driver_names:
                    unique_driver_names.append(driver["metric_name"])
            driver_names = ", ".join(unique_driver_names[:3])
            return (
                f"Model {target_label} icin {predicted_band} sonucunu %{confidence_percent} guvenle uretti. "
                f"Bu {posture.lower()} bir sonuc. Kararda en cok {driver_names} sinyalleri etkili gorunuyor."
            )

        return (
            f"Model {target_label} icin {predicted_band} sonucunu %{confidence_percent} guvenle uretti. "
            "Aciklanabilir surucu listesi bu model icin henuz olusmadi."
        )
