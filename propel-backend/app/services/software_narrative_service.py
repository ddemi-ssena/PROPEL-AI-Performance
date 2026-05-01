from __future__ import annotations

import json
from typing import Any

from app.core.config import settings
from app.schemas.analytics import SoftwarePredictionResponse
from app.services.ai_service import AIService


class SoftwareNarrativeService:
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
            "department": "Software",
            "target_column": target_column,
            "prediction_count": prediction_count,
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "top_reasons": [{"name": name, "count": count} for name, count in top_reasons],
            "team_summaries": team_summaries,
        }
        fallback = SoftwareNarrativeService._department_fallback(payload)
        if not allow_llm:
            return fallback
        return SoftwareNarrativeService._build_aggregate_with_llm(
            payload=payload,
            fallback=fallback,
            scope_label="departman",
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
                **summary,
            }
            fallback = SoftwareNarrativeService._team_fallback(payload)
            should_use_llm = allow_llm and selected_team and str(summary.get("team", "")).strip().lower() == selected_team
            narrative = (
                SoftwareNarrativeService._build_aggregate_with_llm(
                    payload=payload,
                    fallback=fallback,
                    scope_label=f"{summary.get('team', 'takim')} takimi",
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
                f"Software departmani icin genel risk seviyesi {risk_label}. "
                f"{prediction_count} kisinin {high} tanesi yuksek riskte, {medium} tanesi izleme seviyesinde. "
                f"En yaygin sinyal {top_reason}; risk {', '.join(risky_teams) if risky_teams else 'belirgin bir takimda'} tarafinda yogunlasiyor."
            ),
            "risk_interpretation": (
                f"Departman risk yorumu, toplu prediction dagilimi ve tekrar eden KPI driver'larindan uretildi. "
                f"{top_reason} sinyalinin birden fazla kiside one cikmasi, tekil performans sorunundan cok ekip ritmi, kapasite veya motivasyon baglaminda incelenmesi gerektigini gosterir."
            ),
            "action_plan": [
                {
                    "title": "Riskin yogunlastigi takimlarla haftalik kapasite ve odak gorusmesi yap.",
                    "reason": f"Yuksek/orta risk sinyalleri {', '.join(risky_teams) if risky_teams else 'takimlar'} uzerinde yogunlasiyor.",
                    "owner": "Departman yoneticisi",
                    "timeframe": "Bu hafta",
                    "expected_impact": "Takim bazli kapasite ve blokaj gorunurlugu artar.",
                },
                {
                    "title": f"{top_reason} sinyalini takim liderleriyle kok neden seviyesinde incele.",
                    "reason": f"Toplu analizde en yaygin risk nedeni {top_reason} olarak gorunuyor.",
                    "owner": "Departman yoneticisi + takim liderleri",
                    "timeframe": "Bu hafta",
                    "expected_impact": "Tekil aksiyon yerine ortak risk paterni uzerinden karar alinabilir.",
                },
            ],
            "leadership_talking_points": [
                "Bu haftaki risk sinyallerini kisi bazli yargilamadan once takim ritmi ve kapasiteyle birlikte okuyalim.",
                "Riskin en cok hangi takimlarda biriktigini ve bunun sprint planina etkisini netlestirelim.",
                "Bir hafta icinde etkisini gorecegimiz iki somut mudahale secelim.",
            ],
            "confidence_note": "Bu yorum model tahmini ve KPI driver tekrarlarindan uretilen karar destek ozetidir; yonetici gorusmeleriyle dogrulanmalidir.",
        }

    @staticmethod
    def _team_fallback(payload: dict[str, Any]) -> dict[str, Any]:
        team = payload.get("team") or "Takim"
        high = int(payload.get("high") or 0)
        medium = int(payload.get("medium") or 0)
        total = int(payload.get("total") or 0)
        top_reason = payload.get("topReason") or payload.get("top_reason") or "KPI sinyali"
        tone = "yuksek" if high else "orta" if medium else "dusuk"

        return {
            "source": "deterministic",
            "fallback_used": True,
            "manager_summary": (
                f"{team} takimi icin risk seviyesi {tone}. {total} kisilik takimda {high} kisi yuksek riskte, "
                f"{medium} kisi izleme seviyesinde. Ana sinyal {top_reason}."
            ),
            "risk_interpretation": (
                f"{team} takiminda {top_reason} sinyalinin one cikmasi, takim liderinin bu haftaki planlama, kapasite ve destek ritmini gozden gecirmesi gerektigini gosterir."
            ),
            "action_plan": [
                {
                    "title": f"{team} takim lideriyle haftalik kapasite ve blokaj gorusmesi yap.",
                    "reason": f"{team} icinde {high + medium} kisi izleme listesinde ve ana sinyal {top_reason}.",
                    "owner": "Departman yoneticisi + takim lideri",
                    "timeframe": "Bu hafta",
                    "expected_impact": "Takim icindeki riskin ekip ritmi mi yoksa bireysel destek ihtiyaci mi oldugu netlesir.",
                }
            ],
            "leadership_talking_points": [
                f"{team} icinde bu hafta hangi isler kapasiteyi en cok zorluyor?",
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
        prompt = SoftwareNarrativeService._aggregate_prompt(payload, scope_label)
        raw_output, provider, model_name, errors = SoftwareNarrativeService._generate_llm_json(
            prompt,
            timeout_seconds=18,
        )
        if not provider:
            return SoftwareNarrativeService._llm_fallback(
                fallback,
                provider=None,
                reason="LLM provider ayarli degil; deterministik KPI yorumu kullanildi.",
            )

        sanitized = SoftwareNarrativeService._sanitize_aggregate(raw_output)
        if not sanitized:
            return SoftwareNarrativeService._llm_fallback(
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

            for fallback_model in ("gemini-flash-lite-latest", "gemma-3-1b-it"):
                raw_output = AIService._generate_with_gemini(
                    prompt,
                    timeout_seconds=timeout_seconds,
                    json_mode=False,
                    model_name_override=fallback_model,
                )
                if raw_output:
                    return raw_output, "gemini", fallback_model, errors
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
            "Sen deneyimli bir yazilim departmani yoneticisi ve people analytics danismanisin.\n"
            f"Asagidaki {scope_label} KPI/ML ozetini yoneticinin bu hafta karar alacagi sekilde Turkce yorumla.\n"
            "Cikti, haftalik yonetici toplantisinda kullanilacak kisa karar notu gibi olsun.\n"
            "Kurallar:\n"
            "- Sadece JSON dondur.\n"
            "- Yeni veri veya kesin hukum uydurma.\n"
            "- Riskleri kisi suclayan dille degil, kapasite/surec/motivasyon baglaminda yorumla.\n"
            "- Departman yorumunda genel risk resmi, tekrar eden nedenler ve bu hafta alinacak yonetim karari net olsun.\n"
            "- Takim yorumunda takim lideriyle konusulacak kapasite, blokaj, motivasyon veya kalite basliklari net olsun.\n"
            "- Aksiyonlar takim lideri veya departman yoneticisinin bu hafta uygulayabilecegi kadar somut olsun.\n"
            "- leadership_talking_points yoneticinin haftalik takim lideri gorusmesinde kullanabilecegi 3 cumle olsun.\n"
            "- manager_summary 3-5 cumle olsun; aksiyon listesini buraya yigmak yerine karar baglamini aciklasin.\n"
            "- action_plan maddeleri generic olmasin; topReason, risk sayilari ve takim adina baglansin.\n"
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
            text = text[start : end + 1]
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return None
        manager_summary = SoftwareNarrativeService._clean_text(payload.get("manager_summary"), 900)
        risk_interpretation = SoftwareNarrativeService._clean_text(payload.get("risk_interpretation"), 1200)
        if not manager_summary or not risk_interpretation:
            return None
        return {
            "manager_summary": manager_summary,
            "risk_interpretation": risk_interpretation,
            "action_plan": SoftwareNarrativeService._sanitize_aggregate_action_plan(payload.get("action_plan")),
            "leadership_talking_points": SoftwareNarrativeService._sanitize_text_list(
                payload.get("leadership_talking_points"),
                3,
                220,
            ),
            "confidence_note": SoftwareNarrativeService._clean_text(payload.get("confidence_note"), 500),
        }

    @staticmethod
    def _sanitize_aggregate_action_plan(value: Any) -> list[dict[str, str]]:
        if not isinstance(value, list):
            return []
        plans: list[dict[str, str]] = []
        for item in value[:3]:
            if not isinstance(item, dict):
                continue
            title = SoftwareNarrativeService._clean_text(item.get("title"), 220)
            if not title:
                continue
            plans.append(
                {
                    "title": title,
                    "reason": SoftwareNarrativeService._clean_text(item.get("reason"), 420),
                    "owner": SoftwareNarrativeService._clean_text(item.get("owner"), 100) or "Departman yoneticisi",
                    "timeframe": SoftwareNarrativeService._clean_text(item.get("timeframe"), 80) or "Bu hafta",
                    "expected_impact": SoftwareNarrativeService._clean_text(item.get("expected_impact"), 260),
                }
            )
        return plans

    @staticmethod
    def build(
        prediction: SoftwarePredictionResponse,
        *,
        allow_llm: bool = False,
    ) -> dict[str, Any]:
        fallback = SoftwareNarrativeService._fallback(prediction)
        if not allow_llm:
            return fallback

        prompt = SoftwareNarrativeService._prompt(prediction)
        raw_output, provider, model_name, errors = SoftwareNarrativeService._generate_llm_json(
            prompt,
            timeout_seconds=18,
        )

        sanitized = SoftwareNarrativeService._sanitize(raw_output)
        if not sanitized:
            return SoftwareNarrativeService._llm_fallback(
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
    def _fallback(prediction: SoftwarePredictionResponse) -> dict[str, Any]:
        primary_driver = prediction.top_drivers[0] if prediction.top_drivers else {}
        primary_action = prediction.recommended_actions[0] if prediction.recommended_actions else "KPI kirilimlari incelenmeli."
        metric_name = primary_driver.get("metric_name") or "ana KPI sinyali"
        threshold_status = primary_driver.get("threshold_status") or "izleme gerektiriyor"
        trend_signal = primary_driver.get("trend_signal") or "trend yorumu sinirli"
        action_plan = SoftwareNarrativeService._action_plan(prediction)
        employee_label = (
            prediction.summary_payload.get("employee_name")
            or prediction.summary_payload.get("display_label")
            or f"Dataset #{prediction.employee_id}"
        )

        return {
            "source": "deterministic",
            "model": None,
            "fallback_used": True,
            "action_source": "KPI Registry action_when_risky + KPI esik/trend kurallari",
            "manager_summary": (
                f"{employee_label} icin model {prediction.predicted_band} sonucunu "
                f"%{round(prediction.confidence * 100, 1)} guvenle uretti. En belirgin sinyal {metric_name}."
            ),
            "risk_interpretation": (
                f"{metric_name} su anda {threshold_status.lower()} ve {trend_signal.lower()}. "
                "Bu yorum KPI Registry esikleri ve son donem trendinden uretildi."
            ),
            "next_best_actions": [item["title"] for item in action_plan] or [primary_action],
            "action_plan": action_plan,
            "confidence_note": (
                "Bu metin deterministik explain payload'indan uretildi; model karari yerine gecmez, "
                "yonetici incelemesi icin onceliklendirme saglar."
            ),
        }

    @staticmethod
    def _action_plan(prediction: SoftwarePredictionResponse) -> list[dict[str, str]]:
        plans: list[dict[str, str]] = []
        team = str(prediction.summary_payload.get("team") or "ilgili takim")
        for index, driver in enumerate(prediction.top_drivers[:3]):
            metric_name = str(driver.get("metric_name") or "KPI sinyali")
            category = str(driver.get("category") or "Genel")
            threshold_status = str(driver.get("threshold_status") or "Izleme seviyesinde")
            trend_signal = str(driver.get("trend_signal") or "Trend verisi sinirli")
            fallback_action = (
                prediction.recommended_actions[index]
                if index < len(prediction.recommended_actions)
                else "Ilgili KPI kirilimi ekip lideriyle birlikte incelenmeli."
            )

            plans.append(
                {
                    "title": SoftwareNarrativeService._contextual_action_title(
                        base_action=fallback_action,
                        metric_name=metric_name,
                        team=team,
                    ),
                    "reason": (
                        f"{team} baglaminda {metric_name} {threshold_status.lower()} ve {trend_signal.lower()}. "
                        f"Bu nedenle {category.lower()} basliginda hedefli takip oneriliyor."
                    ),
                    "owner": SoftwareNarrativeService._owner_for_category(category),
                    "timeframe": "Bu hafta",
                    "expected_impact": SoftwareNarrativeService._expected_impact_for_driver(
                        metric_name=metric_name,
                        threshold_status=threshold_status,
                        trend_signal=trend_signal,
                    ),
                    "conversation_goal": SoftwareNarrativeService._conversation_goal_for_driver(metric_name),
                    "manager_talking_points": SoftwareNarrativeService._manager_talking_points_for_driver(
                        metric_name=metric_name,
                        team=team,
                    ),
                    "employee_questions": SoftwareNarrativeService._employee_questions_for_driver(metric_name),
                    "success_signal": SoftwareNarrativeService._success_signal_for_driver(metric_name),
                    "metric_name": metric_name,
                    "metric_code": str(driver.get("metric_code") or ""),
                }
            )

        if plans:
            return plans

        return [
            {
                "title": "Calisanin son KPI kirilimlari takim lideriyle birlikte incelenmeli.",
                "reason": "Model tahmini geldi ancak aciklanabilir surucu listesi sinirli.",
                "owner": "Takim lideri",
                "timeframe": "Bu hafta",
                "expected_impact": "Gorunurluk artar; 1 hafta icinde dogru odak alani netlesir.",
                "conversation_goal": "Kisiyi zorlayan temel nedenleri netlestirmek ve guvenli destek plani cikarmak.",
                "manager_talking_points": [
                    "Son donemde zorlandigin noktayi birlikte anlamak istiyorum.",
                    "Bu gorusmenin amaci performans yargisi degil, blokajlari kaldirmak.",
                    "Onumuzdeki bir hafta icin seni rahatlatacak iki somut destek belirleyelim.",
                ],
                "employee_questions": [
                    "Is akisinda en cok nerede sikisiyorsun?",
                    "Hangi destek olursa bu haftayi daha dengeli gecirebilirsin?",
                    "Hangi gorevlerin kapsaminda netlestirme ihtiyacin var?",
                ],
                "success_signal": "Gorusme sonunda iki net destek adimi ve takip tarihi uzerinde anlasilmis olur.",
                "metric_name": "Genel KPI",
                "metric_code": "",
            }
        ]

    @staticmethod
    def _contextual_action_title(base_action: str, metric_name: str, team: str) -> str:
        normalized_metric = metric_name.lower()
        if "motivasyon" in normalized_metric:
            return f"{team} icinde motivasyon dususu gorulen kisilerle 1:1 gorusme planla."
        if "is yuku" in normalized_metric or "fazla" in normalized_metric or "toplanti" in normalized_metric:
            return f"{team} sprint kapasitesini ve gorev dagilimini yeniden dengele."
        if "bug" in normalized_metric or "review" in normalized_metric or "kalite" in normalized_metric:
            return f"{team} icin kod kalitesi ve review kontrol listesini gozden gecir."
        if "teslim" in normalized_metric or "gorev" in normalized_metric:
            return f"{team} teslim blokajlarini ve task kapsamlarini netlestir."
        return base_action

    @staticmethod
    def _owner_for_category(category: str) -> str:
        normalized = category.lower()
        if "duygu" in normalized or "gelisim" in normalized:
            return "Takim lideri + calisan"
        if "is yuku" in normalized or "uretim" in normalized or "uretkenlik" in normalized:
            return "Takim lideri"
        if "kalite" in normalized:
            return "Tech lead"
        if "is birligi" in normalized or "organizasyon" in normalized:
            return "Takim lideri + ekip"
        return "Takim lideri"

    @staticmethod
    def _expected_impact_for_driver(metric_name: str, threshold_status: str, trend_signal: str) -> str:
        normalized_metric = metric_name.lower()
        normalized_threshold = threshold_status.lower()
        normalized_trend = trend_signal.lower()

        if "motivasyon" in normalized_metric:
            return (
                "1:1 gorusmelerle baglilik sinyali toparlanir; kisa vadede motivasyon odakli geri bildirim kalitesi artar."
            )
        if "is yuku" in normalized_metric or "fazla" in normalized_metric or "toplanti" in normalized_metric:
            return (
                "Kapasite dengesi iyilesir; hafta sonunda teslim riski ve tuklenmislik sinyali azalir."
            )
        if "bug" in normalized_metric or "review" in normalized_metric or "kalite" in normalized_metric:
            return (
                "Kod kalitesi varyansi duser; sonraki sprintte hata geri donusu ve rework ihtiyaci azalir."
            )

        if "kritik" in normalized_threshold or "dusus" in normalized_trend or "negatif" in normalized_trend:
            return "Yuksek riskli sinyalde erken mudahale saglanir; bir sonraki haftada KPI dususu sinirlanir."
        return "Odakli takip ile yonetici karar kalitesi artar; kisa vadede oncelikler netlesir."

    @staticmethod
    def _conversation_goal_for_driver(metric_name: str) -> str:
        normalized = metric_name.lower()
        if "motivasyon" in normalized:
            return "Motivasyon dususunun kokenini netlestirmek ve calisanin aidiyetini guclendirecek destek tipini belirlemek."
        if "is yuku" in normalized or "toplanti" in normalized or "fazla" in normalized:
            return "Kapasiteyi zorlayan alanlari tespit edip yuk dagilimini daha surdurulebilir hale getirmek."
        if "bug" in normalized or "review" in normalized or "kalite" in normalized:
            return "Kalite sorununu besleyen teknik veya surecsel nedenleri ayristirip netlestirmek."
        if "teslim" in normalized or "gorev" in normalized:
            return "Teslim gecikmesine yol acan belirsizlik ve bagimliliklari gorunur hale getirmek."
        return "KPI sinyalini etkileyen ana davranissal ve operasyonel etkenleri netlestirmek."

    @staticmethod
    def _manager_talking_points_for_driver(metric_name: str, team: str) -> list[str]:
        normalized = metric_name.lower()
        if "motivasyon" in normalized:
            return [
                f"{team} icindeki mevcut tempo ve baski seviyesini birlikte degerlendirelim.",
                "Bu gorusme performans etiketi koymak icin degil, motivasyonu dusuren nedenleri anlamak icin.",
                "Calisma gununu kolaylastiracak 1-2 destek adimini birlikte kararlastiralim.",
            ]
        if "is yuku" in normalized or "toplanti" in normalized or "fazla" in normalized:
            return [
                "Bu hafta en cok enerji tuketen gorevleri birlikte siralayalim.",
                "Oncelik dusurulebilecek veya devredilebilecek isleri netlestirelim.",
                "Toplanti ve odak zamani dengesini koruyacak yeni bir ritim belirleyelim.",
            ]
        if "bug" in normalized or "review" in normalized or "kalite" in normalized:
            return [
                "Son donemde hata cikaran adimlarda tekrar eden paterni birlikte gorelim.",
                "Kod review beklentilerini ve kalite kontrol noktasini netlestirelim.",
                "Kaliteyi artirirken teslim ritmini bozmayacak pratik iyilestirmeleri secelim.",
            ]
        return [
            "Bu KPI sinyalinin gunluk ise nasil yansidigini birlikte netlestirelim.",
            "Seni zorlayan iki ana nedeni ve yonetici destegi ihtiyacini aciklastiralim.",
            "Bir hafta icinde etkisini gorecegimiz somut bir takip plani olusturalim.",
        ]

    @staticmethod
    def _employee_questions_for_driver(metric_name: str) -> list[str]:
        normalized = metric_name.lower()
        if "motivasyon" in normalized:
            return [
                "Son 2 haftada motivasyonunu en cok dusuren durum neydi?",
                "Seni motive eden is tipleriyle mevcut is dagilimi ne kadar uyumlu?",
                "Yonetimden hangi destek gelirse bu hafta daha dengeli hissedersin?",
            ]
        if "is yuku" in normalized or "toplanti" in normalized or "fazla" in normalized:
            return [
                "Hangi gorevler beklenenden fazla zaman aliyor?",
                "Hangi toplantilar deger katmiyor veya boluyor?",
                "Bu hafta hangi isi delege etmek veya kapsam daraltmak en gercekci olur?",
            ]
        if "bug" in normalized or "review" in normalized or "kalite" in normalized:
            return [
                "Hatalar en cok hangi adimda ortaya cikiyor?",
                "Review geri bildirimlerinde tekrar eden konu ne?",
                "Kaliteyi artirmak icin hangi checklist veya otomasyon sana en cok yardim eder?",
            ]
        return [
            "Bu KPI sinyalini etkileyen en kritik iki neden sence neler?",
            "Hangi bagimliliklar isini yavaslatiyor?",
            "Yonetici destegiyle bu hafta neyi daha iyi hale getirebiliriz?",
        ]

    @staticmethod
    def _success_signal_for_driver(metric_name: str) -> str:
        normalized = metric_name.lower()
        if "motivasyon" in normalized:
            return "Gorusme sonunda calisanin enerji dusuren iki nedeni netlesir ve en az bir destek adimi uzerinde mutabakat saglanir."
        if "is yuku" in normalized or "toplanti" in normalized or "fazla" in normalized:
            return "Haftalik is listesinde en az bir kapsam daraltma/delege karari alinmis ve odak zamani korunmus olur."
        if "bug" in normalized or "review" in normalized or "kalite" in normalized:
            return "Bir sonraki teslime kadar uygulanacak net kalite kontrol adimi ve sahibi belirlenmis olur."
        return "Bir hafta icinde takip edilecek net hedef, sahip ve kontrol tarihi belirlenmis olur."

    @staticmethod
    def _prompt(prediction: SoftwarePredictionResponse) -> str:
        compact_payload = {
            "employee_id": prediction.employee_id,
            "employee_name": prediction.summary_payload.get("employee_name"),
            "display_label": prediction.summary_payload.get("display_label"),
            "team": prediction.summary_payload.get("team"),
            "role": prediction.summary_payload.get("role"),
            "position": prediction.summary_payload.get("position"),
            "target_column": prediction.target_column,
            "predicted_band": prediction.predicted_band,
            "confidence": prediction.confidence,
            "risk_summary": prediction.risk_summary,
            "top_drivers": prediction.top_drivers[:3],
            "recommended_actions": prediction.recommended_actions[:3],
            "summary_payload": prediction.summary_payload,
        }
        return (
            "Sen kidemli bir yazilim muduru ve people analytics danismanisin.\n"
            "Gorevin: KPI model ciktisini yoneticinin bu hafta karar alip uygulayabilecegi sekilde yorumlamak.\n"
            "Cikti rapor gibi aksin: durum ozeti -> riskin olasi kokenleri -> haftalik aksiyon plani.\n"
            "Baglam kurallari:\n"
            "- Sadece MODEL_PAYLOAD verisini kullan; yeni KPI, yeni olay veya kesin hukum uydurma.\n"
            "- Kisiyi mumkunse isim/rol/takimla an; sadece ID kullanma.\n"
            "- confidence bir guven seviyesidir, performans puani gibi anlatma.\n"
            "- Tahmin bandi kesin karar degil; yonetici icin onceliklendirme sinyalidir.\n"
            "- Top drivers KPI Registry esik ve trend kurallarindan geliyor; yorumu bunlara bagla.\n"
            "- Veri eksikse belirsizligi acikla ve dusuk riskli dogrulama adimi oner.\n"
            "Icerik beklentisi:\n"
            "- manager_summary 3-5 cumle olsun; once durum, sonra etkisi, sonra yonetici karari.\n"
            "- manager_summary icinde haftalik aksiyon onerisi, 'bu hafta sunu yap' gibi yonlendirme veya gorev listesi verme.\n"
            "- manager_summary yalnizca yoneticinin nasil bir karar almasi gerektigini, nedenleriyle aciklasin.\n"
            "- risk_interpretation tek paragraf olsun; en az iki driver'i threshold/trend ile iliskilendir.\n"
            "- next_best_actions oncelik sirasinda 3 aksiyon olsun; her birinde ne yapilacagi + beklenen kisa etki acik olsun.\n"
            "- action_plan her maddede title, reason, owner, timeframe, expected_impact, conversation_goal, manager_talking_points, employee_questions, success_signal icersin.\n"
            "- title generic olmasin; takim/rol/KPI baglamina gore ozellestir.\n"
            "- reason, hangi KPI/trend nedeniyle secildigini acikca soylesin.\n"
            "- expected_impact, 1 hafta icinde beklenen operasyonel etkisini net anlatsin.\n"
            "- manager_talking_points yoneticiye gorusmede kullanabilecegi 3 profesyonel cumle olsun.\n"
            "- employee_questions calisana sorulacak 3 acik uclu soru olsun; tani koyma degil, neden bulma odakli olsun.\n"
            "- success_signal, aksiyonun basarili oldugunu hafta sonunda nasil anlayacagimizi anlatsin.\n"
            "- confidence_note 1-2 cumle, temkinli ve karar destegi odakli olsun.\n"
            "Yazim tarzi:\n"
            "- Net, olculu ve suclamayan yonetici dili kullan.\n"
            "- Genelleme yerine payload sinyaline referans ver.\n"
            "- Acil yapilacaklar ile izleme adimlarini ayir.\n"
            "- Aksiyon cagrisi sadece next_best_actions ve action_plan alanlarinda yer alsin.\n"
            "- Ciktilar proaktif, faydaci ve uygulanabilir olsun; genel tavsiye cumlelerinden kacin.\n"
            "Sadece gecerli JSON dondur.\n"
            "JSON semasi:\n"
            "{"
            '"manager_summary": "string", '
            '"risk_interpretation": "string", '
            '"next_best_actions": ["string"], '
            '"action_plan": [{"title": "string", "reason": "string", "owner": "string", "timeframe": "string", "expected_impact": "string", "conversation_goal": "string", "manager_talking_points": ["string"], "employee_questions": ["string"], "success_signal": "string"}], '
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
            text = text[start : end + 1]

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return None

        manager_summary = SoftwareNarrativeService._clean_text(payload.get("manager_summary"), 900)
        risk_interpretation = SoftwareNarrativeService._clean_text(payload.get("risk_interpretation"), 1200)
        confidence_note = SoftwareNarrativeService._clean_text(payload.get("confidence_note"), 500)
        actions = [
            SoftwareNarrativeService._clean_text(item, 180)
            for item in (payload.get("next_best_actions") or [])
            if SoftwareNarrativeService._clean_text(item, 180)
        ][:3]
        action_plan = SoftwareNarrativeService._sanitize_action_plan(payload.get("action_plan"))

        if not manager_summary or not risk_interpretation:
            return None
        if SoftwareNarrativeService._looks_like_action_text(manager_summary):
            return None

        return {
            "manager_summary": manager_summary,
            "risk_interpretation": risk_interpretation,
            "next_best_actions": actions,
            "action_plan": action_plan,
            "confidence_note": confidence_note,
        }

    @staticmethod
    def _clean_text(value: Any, max_len: int) -> str:
        if not isinstance(value, str):
            return ""
        text = " ".join(value.split())
        return text[:max_len].strip()

    @staticmethod
    def _sanitize_action_plan(value: Any) -> list[dict[str, str]]:
        if not isinstance(value, list):
            return []

        plans: list[dict[str, Any]] = []
        for item in value[:3]:
            if not isinstance(item, dict):
                continue
            title = SoftwareNarrativeService._clean_text(item.get("title"), 220)
            reason = SoftwareNarrativeService._clean_text(item.get("reason"), 420)
            owner = SoftwareNarrativeService._clean_text(item.get("owner"), 80)
            timeframe = SoftwareNarrativeService._clean_text(item.get("timeframe"), 80)
            expected_impact = SoftwareNarrativeService._clean_text(item.get("expected_impact"), 220)
            conversation_goal = SoftwareNarrativeService._clean_text(item.get("conversation_goal"), 220)
            manager_talking_points = SoftwareNarrativeService._sanitize_text_list(item.get("manager_talking_points"), 3, 180)
            employee_questions = SoftwareNarrativeService._sanitize_text_list(item.get("employee_questions"), 3, 180)
            success_signal = SoftwareNarrativeService._clean_text(item.get("success_signal"), 220)
            if not title:
                continue
            plans.append(
                {
                    "title": title,
                    "reason": reason,
                    "owner": owner or "Takim lideri",
                    "timeframe": timeframe or "Bu hafta",
                    "expected_impact": expected_impact or "Bu hafta icinde ilgili KPI sinyalinde iyilesme beklenir.",
                    "conversation_goal": conversation_goal or "Gorusmenin amaci KPI sinyalinin kok nedenini netlestirmek.",
                    "manager_talking_points": manager_talking_points,
                    "employee_questions": employee_questions,
                    "success_signal": success_signal or "Hafta sonunda aksiyon etkisini gosteren en az bir olumlu sinyal gorulur.",
                }
            )
        return plans

    @staticmethod
    def _sanitize_text_list(value: Any, max_items: int, max_len: int) -> list[str]:
        if not isinstance(value, list):
            return []
        items: list[str] = []
        for raw_item in value[:max_items]:
            cleaned = SoftwareNarrativeService._clean_text(raw_item, max_len)
            if cleaned:
                items.append(cleaned)
        return items

    @staticmethod
    def _looks_like_action_text(text: str) -> bool:
        normalized = text.lower()
        markers = (
            "bu hafta",
            "hemen",
            "aksiyon",
            "planla",
            "yapilmali",
            "gorusme yap",
            "baslat",
            "uygula",
            "adim",
            "onumuzdeki hafta",
        )
        return any(marker in normalized for marker in markers)
