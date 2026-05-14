from __future__ import annotations

import json
from typing import Any

from app.core.config import settings
from app.services.ai_service import AIService


SALES_TARGET_LABELS = {
    "Performance_Drop_Target": "performans dususu",
    "Burnout_Target": "tukenmislik",
    "Resignation_Target": "istifa riski",
    "High_Risk_Target": "yuksek risk",
}


class SalesNarrativeService:
    @staticmethod
    def build_department_narrative(
        *,
        target_column: str,
        prediction_count: int,
        high_risk_count: int,
        medium_risk_count: int,
        low_risk_count: int,
        top_reasons: list[tuple[str, int]],
        team_summaries: list[dict[str, Any]],
        allow_llm: bool = False,
    ) -> dict[str, Any]:
        payload = {
            "scope": "department",
            "department": "Sales",
            "target_column": target_column,
            "target_label": SALES_TARGET_LABELS.get(target_column, target_column),
            "prediction_count": prediction_count,
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "top_reasons": [{"name": name, "count": count} for name, count in top_reasons],
            "team_summaries": team_summaries,
        }
        fallback = SalesNarrativeService._department_fallback(payload)
        if not allow_llm:
            return fallback
        return SalesNarrativeService._build_aggregate_with_llm(
            payload=payload,
            fallback=fallback,
            scope_label="satis departmani",
        )

    @staticmethod
    def build_team_narratives(
        *,
        target_column: str,
        team_summaries: list[dict[str, Any]],
        allow_llm: bool = False,
        llm_team: str | None = None,
    ) -> list[dict[str, Any]]:
        narratives: list[dict[str, Any]] = []
        selected_team = (llm_team or "").strip().lower()
        for summary in team_summaries:
            payload = {
                "scope": "team",
                "target_column": target_column,
                "target_label": SALES_TARGET_LABELS.get(target_column, target_column),
                **summary,
            }
            fallback = SalesNarrativeService._team_fallback(payload)
            should_use_llm = allow_llm and selected_team and str(summary.get("team", "")).strip().lower() == selected_team
            narrative = (
                SalesNarrativeService._build_aggregate_with_llm(
                    payload=payload,
                    fallback=fallback,
                    scope_label=f"{summary.get('team', 'takim')} satis takimi",
                )
                if should_use_llm
                else fallback
            )
            narrative["team"] = summary.get("team")
            narratives.append(narrative)
        return narratives

    @staticmethod
    def _department_fallback(payload: dict[str, Any]) -> dict[str, Any]:
        prediction_count = int(payload.get("prediction_count") or 0)
        high = int(payload.get("high_risk_count") or 0)
        medium = int(payload.get("medium_risk_count") or 0)
        target_label = payload.get("target_label", "risk")
        top_reason = (payload.get("top_reasons") or [{}])[0].get("name", "KPI sinyali")
        risky_teams = [
            item.get("team")
            for item in payload.get("team_summaries", [])
            if item.get("high", 0) or item.get("medium", 0)
        ][:3]
        risk_label = "yuksek" if high >= 4 or (prediction_count and high / prediction_count >= 0.25) else "orta" if high or medium else "dusuk"

        return {
            "source": "deterministic",
            "fallback_used": True,
            "manager_summary": (
                f"Satis departmani icin {target_label} risk seviyesi {risk_label}. "
                f"{prediction_count} kisinin {high} tanesi yuksek riskte, {medium} tanesi izleme seviyesinde. "
                f"En yaygin sinyal {top_reason}; risk {', '.join(risky_teams) if risky_teams else 'belirgin bir takimda'} tarafinda yogunlasiyor."
            ),
            "risk_interpretation": (
                f"Satis departmani {target_label} yorumu, toplu prediction dagilimi ve tekrar eden KPI driver'larindan uretildi. "
                f"{top_reason} sinyalinin birden fazla satis temsilcisinde one cikmasi, bireysel performans sorunundan cok takim satisi, kapasite veya motivasyon baglaminda incelenmesi gerektigini gosterir."
            ),
            "action_plan": [
                {
                    "title": "Riskin yogunlastigi takimlarla haftalik satis ritmi ve kapasite gorusmesi yap.",
                    "reason": f"Yuksek/orta risk sinyalleri {', '.join(risky_teams) if risky_teams else 'takimlar'} uzerinde yogunlasiyor.",
                    "owner": "Satis departmani yoneticisi",
                    "timeframe": "Bu hafta",
                    "expected_impact": "Takim bazli kapasite ve satis blokajlari gorunur hale gelir.",
                },
                {
                    "title": f"{top_reason} sinyalini takim liderleriyle kok neden seviyesinde incele.",
                    "reason": f"Toplu analizde en yaygin risk nedeni {top_reason} olarak gorunuyor.",
                    "owner": "Satis yoneticisi + takim liderleri",
                    "timeframe": "Bu hafta",
                    "expected_impact": "Tekil aksiyon yerine ortak risk paterni uzerinden karar alinabilir.",
                },
            ],
            "leadership_talking_points": [
                "Bu haftaki risk sinyallerini kisi bazli yargilamadan once takim satis ritmi ve kapasiteyle birlikte okuyalim.",
                "Riskin en cok hangi takimlarda biriktigini ve bunun bu haftaki satis hedefine etkisini netlestirelim.",
                "Bir hafta icinde etkisini gorecegimiz iki somut mudahale secelim.",
            ],
            "confidence_note": "Bu yorum model tahmini ve KPI driver tekrarlarindan uretilen karar destek ozetidir; yonetici gorusmesiyle dogrulanmalidir.",
        }

    @staticmethod
    def _team_fallback(payload: dict[str, Any]) -> dict[str, Any]:
        team = payload.get("team") or "Takim"
        high = int(payload.get("high") or 0)
        medium = int(payload.get("medium") or 0)
        total = int(payload.get("total") or 0)
        target_label = payload.get("target_label", "risk")
        top_reason = payload.get("topReason") or payload.get("top_reason") or "KPI sinyali"
        tone = "yuksek" if high else "orta" if medium else "dusuk"

        return {
            "source": "deterministic",
            "fallback_used": True,
            "manager_summary": (
                f"{team} satis takimi icin {target_label} risk seviyesi {tone}. {total} kisilik takimda {high} kisi yuksek riskte, "
                f"{medium} kisi izleme seviyesinde. Ana sinyal {top_reason}."
            ),
            "risk_interpretation": (
                f"{team} takiminda {top_reason} sinyalinin one cikmasi, takim liderinin bu haftaki satis planlama, "
                f"kapasite ve motivasyon ritmini gozden gecirmesi gerektigini gosterir."
            ),
            "action_plan": [
                {
                    "title": f"{team} takim lideriyle haftalik satis kapasite ve blokaj gorusmesi yap.",
                    "reason": f"{team} icinde {high + medium} kisi izleme listesinde ve ana sinyal {top_reason}.",
                    "owner": "Satis yoneticisi + takim lideri",
                    "timeframe": "Bu hafta",
                    "expected_impact": "Takim icindeki riskin satis ritmi mi yoksa bireysel destek ihtiyaci mi oldugu netlesir.",
                }
            ],
            "leadership_talking_points": [
                f"{team} icinde bu hafta hangi satis aktiviteleri kapasiteyi en cok zorluyor?",
                f"{top_reason} sinyalini artiran ortak bir surec veya planlama nedeni var mi?",
                "Bu hafta hangi isi ertelemek, bolmek veya yeniden dagitmak en gercekci olur?",
            ],
            "confidence_note": "Takim yorumu toplu prediction ve driver tekrarlarina dayanir; takim lideri gorusmesiyle dogrulanmalidir.",
        }

    @staticmethod
    def _build_aggregate_with_llm(
        *,
        payload: dict[str, Any],
        fallback: dict[str, Any],
        scope_label: str,
    ) -> dict[str, Any]:
        prompt = SalesNarrativeService._aggregate_prompt(payload, scope_label)
        raw_output, provider, model_name, errors = SalesNarrativeService._generate_llm_json(
            prompt,
            timeout_seconds=24,
        )
        if not provider:
            return SalesNarrativeService._llm_fallback(
                fallback,
                provider=None,
                reason="LLM provider ayarli degil; deterministik KPI yorumu kullanildi.",
            )

        sanitized = SalesNarrativeService._sanitize_aggregate(raw_output)
        if not sanitized:
            return SalesNarrativeService._llm_fallback(
                fallback,
                provider=provider,
                reason=(
                    f"LLM yaniti alinamadi veya beklenen JSON formatinda degildi ({'; '.join(errors)}); "
                    "deterministik KPI yorumu kullanildi."
                ),
            )
        sanitized["source"] = provider or "llm"
        sanitized["model"] = model_name
        sanitized["fallback_used"] = False
        return sanitized

    @staticmethod
    def _llm_fallback(
        fallback: dict[str, Any],
        *,
        provider: str | None,
        reason: str,
    ) -> dict[str, Any]:
        enriched = dict(fallback)
        enriched["llm_attempted"] = bool(provider)
        enriched["requested_source"] = provider
        enriched["fallback_reason"] = reason
        return enriched

    @staticmethod
    def _generate_llm_json(
        prompt: str,
        *,
        timeout_seconds: int,
    ) -> tuple[str | None, str | None, str | None, list[str]]:
        errors: list[str] = []
        attempted_provider = None

        if AIService.GEMINI_API_KEY:
            attempted_provider = "gemini"
            raw_output = AIService._generate_with_gemini(
                prompt,
                timeout_seconds=timeout_seconds,
                json_mode=True,
            )
            model_name = AIService._RESOLVED_GEMINI_MODEL or AIService.GEMINI_MODEL or "gemini"
            if raw_output:
                return raw_output, "gemini", model_name, errors
            if AIService.LAST_LLM_ERROR:
                errors.append(AIService.LAST_LLM_ERROR)

        if settings.USE_LOCAL_LLM or settings.OLLAMA_URL:
            attempted_provider = attempted_provider or "ollama"
            raw_output = AIService._generate_with_ollama(
                prompt,
                timeout_seconds=timeout_seconds,
                json_mode=True,
            )
            model_name = AIService._RESOLVED_OLLAMA_MODEL or AIService.OLLAMA_MODEL or "ollama"
            if raw_output:
                return raw_output, "ollama", model_name, errors
            if AIService.LAST_LLM_ERROR:
                errors.append(AIService.LAST_LLM_ERROR)

        return None, attempted_provider, None, errors or ["LLM provider cevap dondurmedi"]

    @staticmethod
    def _aggregate_prompt(payload: dict[str, Any], scope_label: str) -> str:
        return (
            "Sen deneyimli bir satis departmani yoneticisi ve people analytics danismanisin.\n"
            f"Asagidaki {scope_label} KPI/ML ozetini yoneticinin bu hafta karar alacagi sekilde Turkce yorumla.\n"
            "Cikti, haftalik satis yonetici toplantisinda kullanilacak kisa karar notu gibi olsun.\n"
            "Kurallar:\n"
            "- Sadece JSON dondur.\n"
            "- Yeni veri veya kesin hukum uydurma.\n"
            "- Riskleri kisi suclayan dille degil, satis kapasite/surec/motivasyon baglaminda yorumla.\n"
            "- Departman yorumunda genel risk resmi, tekrar eden nedenler ve bu hafta alinacak satis yonetim karari net olsun.\n"
            "- Takim yorumunda takim lideriyle konusulacak quota, pipeline, donusum veya musteri memnuniyeti basliklari net olsun.\n"
            "JSON semasi: {"
            '"manager_summary": "string", '
            '"risk_interpretation": "string", '
            '"action_plan": [{"title": "string", "reason": "string", "owner": "string", "timeframe": "string", "expected_impact": "string"}], '
            '"leadership_talking_points": ["string"], '
            '"confidence_note": "string"'
            "}\n"
            f"PAYLOAD:\n{json.dumps(payload, ensure_ascii=False)}"
        )

    @staticmethod
    def _sanitize_aggregate(raw_output: str | None) -> dict[str, Any] | None:
        if not raw_output:
            return None
        text = raw_output.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start: end + 1]
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return None
        manager_summary = SalesNarrativeService._clean_text(payload.get("manager_summary"), 900)
        risk_interpretation = SalesNarrativeService._clean_text(payload.get("risk_interpretation"), 1200)
        if not manager_summary or not risk_interpretation:
            return None
        return {
            "manager_summary": manager_summary,
            "risk_interpretation": risk_interpretation,
            "action_plan": SalesNarrativeService._sanitize_aggregate_action_plan(payload.get("action_plan")),
            "leadership_talking_points": SalesNarrativeService._sanitize_text_list(
                payload.get("leadership_talking_points"), 3, 220,
            ),
            "confidence_note": SalesNarrativeService._clean_text(payload.get("confidence_note"), 500),
        }

    @staticmethod
    def _sanitize_aggregate_action_plan(value: Any) -> list[dict[str, str]]:
        if not isinstance(value, list):
            return []
        plans: list[dict[str, str]] = []
        for item in value[:3]:
            if not isinstance(item, dict):
                continue
            title = SalesNarrativeService._clean_text(item.get("title"), 220)
            if not title:
                continue
            plans.append(
                {
                    "title": title,
                    "reason": SalesNarrativeService._clean_text(item.get("reason"), 420),
                    "owner": SalesNarrativeService._clean_text(item.get("owner"), 100) or "Satis yoneticisi",
                    "timeframe": SalesNarrativeService._clean_text(item.get("timeframe"), 80) or "Bu hafta",
                    "expected_impact": SalesNarrativeService._clean_text(item.get("expected_impact"), 260),
                }
            )
        return plans

    @staticmethod
    def build(
        prediction: Any,
        *,
        allow_llm: bool = False,
    ) -> dict[str, Any]:
        fallback = SalesNarrativeService._fallback(prediction)
        if not allow_llm:
            return fallback

        prompt = SalesNarrativeService._prompt(prediction)
        raw_output, provider, model_name, errors = SalesNarrativeService._generate_llm_json(
            prompt,
            timeout_seconds=18,
        )

        sanitized = SalesNarrativeService._sanitize(raw_output)
        if not sanitized:
            return SalesNarrativeService._llm_fallback(
                fallback,
                provider=provider,
                reason=(
                    f"LLM yaniti alinamadi veya beklenen JSON formatinda degildi ({'; '.join(errors)}); "
                    "deterministik KPI yorumu kullanildi."
                ),
            )

        sanitized["source"] = provider or "llm"
        sanitized["model"] = model_name
        sanitized["fallback_used"] = False
        return sanitized

    @staticmethod
    def _fallback(prediction: Any) -> dict[str, Any]:
        primary_driver = prediction.top_drivers[0] if prediction.top_drivers else {}
        primary_action = prediction.recommended_actions[0] if prediction.recommended_actions else "KPI kirilimlari incelenmeli."
        metric_name = primary_driver.get("metric_name") or "ana satis KPI sinyali"
        threshold_status = primary_driver.get("threshold_status") or "izleme gerektiriyor"
        trend_signal = primary_driver.get("trend_signal") or "trend yorumu sinirli"
        target_label = SALES_TARGET_LABELS.get(prediction.target_column, "hedef")
        action_plan = SalesNarrativeService._action_plan(prediction)
        employee_label = (
            prediction.summary_payload.get("employee_name")
            or prediction.summary_payload.get("display_label")
            or f"Dataset #{prediction.employee_id}"
        )

        return {
            "source": "deterministic",
            "model": None,
            "fallback_used": True,
            "action_source": "Sales KPI Registry action_when_risky + KPI esik/trend kurallari",
            "manager_summary": (
                f"{employee_label} icin model {target_label} tahmini olarak {prediction.predicted_band} sonucunu "
                f"%{round(prediction.confidence * 100, 1)} guvenle uretti. En belirgin sinyal {metric_name}."
            ),
            "risk_interpretation": (
                f"{metric_name} su anda {threshold_status.lower()} ve {trend_signal.lower()}. "
                "Bu yorum Satis KPI Registry esikleri ve son donem trendinden uretildi."
            ),
            "next_best_actions": [item["title"] for item in action_plan] or [primary_action],
            "action_plan": action_plan,
            "confidence_note": (
                "Bu metin deterministik explain payload'indan uretildi; model karari yerine gecmez, "
                "yonetici incelemesi icin onceliklendirme saglar."
            ),
        }

    @staticmethod
    def _action_plan(prediction: Any) -> list[dict[str, str]]:
        plans: list[dict[str, str]] = []
        team = str(prediction.summary_payload.get("team") or "ilgili satis takimi")
        target_label = SALES_TARGET_LABELS.get(prediction.target_column, "hedef")

        for index, driver in enumerate(prediction.top_drivers[:3]):
            metric_name = str(driver.get("metric_name") or "KPI sinyali")
            category = str(driver.get("category") or "Genel")
            threshold_status = str(driver.get("threshold_status") or "Izleme seviyesinde")
            trend_signal = str(driver.get("trend_signal") or "Trend verisi sinirli")
            fallback_action = (
                prediction.recommended_actions[index]
                if index < len(prediction.recommended_actions)
                else "Ilgili satis KPI kirilimi ekip lideriyle birlikte incelenmeli."
            )

            plans.append(
                {
                    "title": SalesNarrativeService._contextual_action_title(
                        base_action=fallback_action,
                        metric_name=metric_name,
                        team=team,
                        target_label=target_label,
                    ),
                    "reason": (
                        f"{team} baglaminda {metric_name} {threshold_status.lower()} ve {trend_signal.lower()}. "
                        f"Bu nedenle {category.lower()} basliginda hedefli takip oneriliyor."
                    ),
                    "owner": SalesNarrativeService._owner_for_category(category),
                    "timeframe": "Bu hafta",
                    "expected_impact": SalesNarrativeService._expected_impact_for_driver(metric_name),
                    "metric_name": metric_name,
                    "metric_code": str(driver.get("metric_code") or ""),
                }
            )

        if plans:
            return plans

        return [
            {
                "title": "Calisanin son satis KPI kirilimlari takim lideriyle birlikte incelenmeli.",
                "reason": "Model tahmini geldi ancak aciklanabilir surucu listesi sinirli.",
                "owner": "Satis takim lideri",
                "timeframe": "Bu hafta",
                "expected_impact": "Gorunurluk artar; 1 hafta icinde dogru odak alani netlesir.",
                "metric_name": "Genel Satis KPI",
                "metric_code": "",
            }
        ]

    @staticmethod
    def _contextual_action_title(base_action: str, metric_name: str, team: str, target_label: str) -> str:
        normalized = metric_name.lower()
        if "hedef" in normalized or "quota" in normalized or "gerceklesme" in normalized:
            return f"{team} icinde hedef altinda kalan kisilerle haftalik satis planlama gorusmesi yap."
        if "motivasyon" in normalized:
            return f"{team} icinde motivasyon dususu gorulen satis temsilcileriyle 1:1 gorusme planla."
        if "is yuku" in normalized or "stres" in normalized:
            return f"{team} satis is yukunu ve hesap dagilimini yeniden dengele."
        if "donusum" in normalized or "kapani" in normalized or "kazan" in normalized:
            return f"{team} icin teklif ve kapani taktiklerini gozden gecir."
        if "musteri" in normalized or "memnuniyet" in normalized or "sikayet" in normalized:
            return f"{team} icinde musteri memnuniyet dususu icin kok neden analizi yap."
        if "pipeline" in normalized:
            return f"{team} pipeline kalitesi ve prospecting aktiviteleri guclendirilmeli."
        return base_action

    @staticmethod
    def _owner_for_category(category: str) -> str:
        normalized = category.lower()
        if "duygu" in normalized or "gelisim" in normalized:
            return "Satis takim lideri + calisan"
        if "is yuku" in normalized or "surdurulebilirlik" in normalized:
            return "Satis takim lideri"
        if "musteri" in normalized or "csat" in normalized or "crm" in normalized:
            return "Satis takim lideri"
        if "donusum" in normalized or "hedef" in normalized:
            return "Satis yoneticisi + takim lideri"
        return "Satis takim lideri"

    @staticmethod
    def _expected_impact_for_driver(metric_name: str) -> str:
        normalized = metric_name.lower()
        if "hedef" in normalized or "gerceklesme" in normalized:
            return "Haftalik hedef gerceklesme orani gorunurlugu artar; blokajlar erkenden tespit edilir."
        if "motivasyon" in normalized:
            return "1:1 gorusmelerle motivasyon sinyali toparlanir; satis enerjisi yeniden yukselir."
        if "donusum" in normalized or "kapani" in normalized:
            return "Teklif kalitesi ve kapani becerisi gorunur hale gelir; kayip analizi netlenir."
        if "musteri" in normalized or "memnuniyet" in normalized:
            return "Musteri memnuniyeti kaynagi tespit edilir; uzun vadeli hesap sagligi korunur."
        if "pipeline" in normalized:
            return "Pipeline dolulugu ve kalitesi iyilesir; gelecek haftalarin satis ritmini destekler."
        return "Odakli takip ile satis karar kalitesi artar; kisa vadede oncelikler netlesir."

    @staticmethod
    def _prompt(prediction: Any) -> str:
        compact_payload = {
            "employee_id": prediction.employee_id,
            "employee_name": prediction.summary_payload.get("employee_name"),
            "display_label": prediction.summary_payload.get("display_label"),
            "team": prediction.summary_payload.get("team"),
            "role": prediction.summary_payload.get("role"),
            "target_column": prediction.target_column,
            "target_label": SALES_TARGET_LABELS.get(prediction.target_column, prediction.target_column),
            "predicted_band": prediction.predicted_band,
            "confidence": prediction.confidence,
            "risk_summary": prediction.risk_summary,
            "top_drivers": prediction.top_drivers[:3],
            "recommended_actions": prediction.recommended_actions[:3],
        }
        return (
            "Sen kidemli bir satis muduru ve people analytics danismanisin.\n"
            "Gorevin: Satis KPI model ciktisini yoneticinin bu hafta karar alip uygulayabilecegi sekilde yorumlamak.\n"
            "Baglam kurallari:\n"
            "- Sadece MODEL_PAYLOAD verisini kullan; yeni KPI veya kesin hukum uydurma.\n"
            "- Riskleri kisi bazli degil, satis sureci, kapasite ve motivasyon baglaminda ele al.\n"
            "- Aksiyonlar satis takim liderinin bu hafta uygulayabilecegi kadar somut olsun.\n"
            "Sadece gecerli JSON dondur.\n"
            "JSON semasi:\n"
            "{"
            '"manager_summary": "string", '
            '"risk_interpretation": "string", '
            '"next_best_actions": ["string"], '
            '"action_plan": [{"title": "string", "reason": "string", "owner": "string", "timeframe": "string", "expected_impact": "string"}], '
            '"confidence_note": "string"'
            "}\n"
            f"MODEL_PAYLOAD:\n{json.dumps(compact_payload, ensure_ascii=False)}"
        )

    @staticmethod
    def _sanitize(raw_output: str | None) -> dict[str, Any] | None:
        if not raw_output:
            return None
        text = raw_output.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start: end + 1]
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return None

        manager_summary = SalesNarrativeService._clean_text(payload.get("manager_summary"), 900)
        risk_interpretation = SalesNarrativeService._clean_text(payload.get("risk_interpretation"), 1200)
        if not manager_summary or not risk_interpretation:
            return None

        return {
            "manager_summary": manager_summary,
            "risk_interpretation": risk_interpretation,
            "next_best_actions": [
                SalesNarrativeService._clean_text(item, 180)
                for item in (payload.get("next_best_actions") or [])
                if SalesNarrativeService._clean_text(item, 180)
            ][:3],
            "action_plan": SalesNarrativeService._sanitize_action_plan(payload.get("action_plan")),
            "confidence_note": SalesNarrativeService._clean_text(payload.get("confidence_note"), 500),
        }

    @staticmethod
    def _sanitize_action_plan(value: Any) -> list[dict[str, str]]:
        if not isinstance(value, list):
            return []
        plans: list[dict[str, Any]] = []
        for item in value[:3]:
            if not isinstance(item, dict):
                continue
            title = SalesNarrativeService._clean_text(item.get("title"), 220)
            if not title:
                continue
            plans.append(
                {
                    "title": title,
                    "reason": SalesNarrativeService._clean_text(item.get("reason"), 420),
                    "owner": SalesNarrativeService._clean_text(item.get("owner"), 80) or "Satis takim lideri",
                    "timeframe": SalesNarrativeService._clean_text(item.get("timeframe"), 80) or "Bu hafta",
                    "expected_impact": SalesNarrativeService._clean_text(item.get("expected_impact"), 220) or "Bu hafta icinde ilgili satis KPI sinyalinde iyilesme beklenir.",
                }
            )
        return plans

    @staticmethod
    def _sanitize_text_list(value: Any, max_items: int, max_len: int) -> list[str]:
        if not isinstance(value, list):
            return []
        items: list[str] = []
        for raw_item in value[:max_items]:
            cleaned = SalesNarrativeService._clean_text(raw_item, max_len)
            if cleaned:
                items.append(cleaned)
        return items

    @staticmethod
    def _clean_text(value: Any, max_len: int) -> str:
        if not isinstance(value, str):
            return ""
        text = " ".join(value.split())
        return text[:max_len].strip()
