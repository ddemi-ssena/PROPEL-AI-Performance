import json
from typing import Optional

import requests

from app.core.config import settings
from app.db.models.user import UserRole


class AIService:
    OLLAMA_URL = settings.OLLAMA_URL or "http://host.docker.internal:11434/api/generate"
    OLLAMA_MODEL = settings.OLLAMA_MODEL or "llama3"
    GEMINI_API_KEY = settings.GEMINI_API_KEY
    GEMINI_MODEL = settings.GEMINI_MODEL or "gemini-1.5-flash"
    _RESOLVED_OLLAMA_MODEL: Optional[str] = None
    _RESOLVED_GEMINI_MODEL: Optional[str] = None

    DEPARTMENT_ROLE_MATRIX = {
        "Yazilim Gelistirme": {
            "manager": [
                "technical debt",
                "sprint planlama",
                "kod kalitesi standartlari",
                "ekip velocity",
                "release riski",
                "mentorluk kalitesi",
            ],
            "employee": [
                "code review katkisi",
                "dokumantasyon disiplini",
                "yeni kutuphanelere adaptasyon",
                "bug cozme hizi",
                "pull request kalitesi",
                "test disiplini",
            ],
        },
        "Insan Kaynaklari": {
            "manager": [
                "ise alim verimliligi",
                "calisan bagliligi stratejileri",
                "yetenek yonetimi",
                "ic iletisim ritmi",
                "onboarding kalitesi",
            ],
            "employee": [
                "aday deneyimi",
                "ic iletisim seffafligi",
                "bordro sureclerinde hatasizlik",
                "mulakat koordinasyonu",
                "egitim operasyonlari",
            ],
        },
        "Pazarlama": {
            "manager": [
                "kampanya ROI",
                "marka algisi yonetimi",
                "stratejik butce kullanimi",
                "kanal performansi",
                "talep yaratma kalitesi",
            ],
            "employee": [
                "kreatif icerik kalitesi",
                "sosyal medya etkilesim oranlari",
                "veri odakli raporlama",
                "kampanya optimizasyonu",
                "musteri icgorusu uretimi",
            ],
        },
        "Satis": {
            "manager": [
                "pipeline yonetimi",
                "tahmin dogrulugu",
                "ekip koclugu",
                "hedef kapama disiplini",
                "CRM hijyeni",
            ],
            "employee": [
                "itiraz yonetimi",
                "musteri guveni olusturma",
                "lead donusum kalitesi",
                "takip disiplini",
                "kapanis becerisi",
            ],
        },
    }

    WEEK_THEME_GUIDANCE = {
        "Surecler & Blokajlar": "calisanin surec akisindaki engelleri, darboazlari ve is yapma akisini gorunur kil",
        "Motivasyon & Psikolojik Durum": "enerji, aidiyet, psikolojik guven ve tukenmislik sinyallerini ortaya cikar",
        "Is Birligi & Seffaflik": "ekip ici iletisim, guven, geri bildirim kalitesi ve destek davranislarini yokla",
        "Gelisim & Vizyon": "ogrenme, sahiplenme, kariyer yonu ve gelisim beklentilerini olc",
    }

    ROLE_BEHAVIOR_GUIDANCE = {
        "manager": "mentorluk kalitesi, blokajlari kaldirma hizi, ekibin onunu acma becerisi ve psikolojik guven yaratma davranislari",
        "employee": "uygulama disiplini, ekip uyumu, gorev sahiplenme, yapici iletisim ve teslim kalitesi",
    }

    WEEK_SIGNAL_GUIDANCE = {
        "Surecler & Blokajlar": "inisiyatif, teknik borc riski, blokajlari erken fark etme, surec akisini yavaslatan davranislar",
        "Motivasyon & Psikolojik Durum": "isteklilik, ekip hedeflerine inanc, aidiyet, guvende hissetme, tukenmislik veya kopma sinyalleri",
        "Is Birligi & Seffaflik": "kriz anindaki iletisim, yardim isteme, yardim sunma, yapici geri bildirim ve ekip enerjisine etki",
        "Gelisim & Vizyon": "ogrenme disiplini, yeni yaklasimlari deneme, gelisim alanini kabul etme ve destek ihtiyacini ifade etme",
    }

    WEEK_TEMPLATE_TARGETS = {
        "Surecler & Blokajlar": {
            "manager": "blokajlari kaldirma hizi, ekibin onunu acma becerisi, teknik veya operasyonel riski erken fark etme",
            "employee": "uygulama disiplini, sureci yavaslatan davranis, teknik borc veya hata riski olusturan aliskanlik",
        },
        "Motivasyon & Psikolojik Durum": {
            "manager": "ekibe guven verme, stres altinda destek olma, kopma veya guvensizlik hissini azaltma",
            "employee": "isteklilik, ekip hedeflerine inanc, aidiyet ve motivasyon dususu sinyali",
        },
        "Is Birligi & Seffaflik": {
            "manager": "acik iletisim kurma, ekip ici guveni guclendirme, kriz aninda yon gosterebilme",
            "employee": "ekip uyumu, yapici iletisim, kriz aninda sakinlik ve cozum odakli davranis",
        },
        "Gelisim & Vizyon": {
            "manager": "mentorluk kalitesi, gelisimi destekleme, ekibin onunu acan yonlendirme",
            "employee": "ogrenme istegi, yeni yaklasimlari deneme, gelisimde durgunluk veya sahiplenme sinyali",
        },
    }

    WEEKLY_ANALYSIS_JSON_CONTRACT = {
        "sentiment_label": "positive | neutral | negative",
        "sentiment_score": "number between -1 and 1",
        "motivation_score": "number between 1 and 5",
        "burnout_risk": "low | medium | high",
        "flight_risk": "low | medium | high",
        "flight_risk_score": "integer between 1 and 10",
        "psychological_safety_score": "number between 1 and 5",
        "collaboration_score": "number between 1 and 5",
        "growth_signal_score": "number between 1 and 5",
        "leadership_support_score": "number between 1 and 5 or null",
        "emotion_spectrum": [
            {"label": "heyecanli | stabil | hayal_kirikligi | tukenmis | kaygili", "score": "number between 0 and 1"}
        ],
        "dominant_emotions": ["top 3 emotion labels in Turkish"],
        "theme_labels": ["short Turkish business themes"],
        "entity_mentions": ["specific work topics or entities from the text"],
        "complaint_topics": ["top complaint topics if any"],
        "praise_topics": ["top praise topics if any"],
        "flight_risk_reasons": ["short Turkish reasons"],
        "burnout_signals": ["short Turkish burnout signals"],
        "key_strengths": ["short Turkish phrases"],
        "risk_flags": ["short Turkish phrases"],
        "support_needs": ["short Turkish phrases"],
        "keywords": ["important Turkish keywords from the text"],
        "manager_summary": "one short Turkish summary for managers",
        "action_recommendation": "one short Turkish recommendation for manager or HR",
        "confidence": "number between 0 and 1",
    }

    MONTHLY_RAG_REPORT_CONTRACT = {
        "report_summary": "short Turkish executive summary",
        "trend_summary": "short Turkish summary of monthly emotional and motivation trend",
        "flight_risk_score": "integer between 1 and 10",
        "retention_risk_level": "low | medium | high",
        "top_complaint_topics": ["short Turkish complaint topics"],
        "top_praise_topics": ["short Turkish praise topics"],
        "key_takeaways": ["short Turkish findings"],
        "action_recommendation": "short Turkish manager or HR action recommendation",
        "confidence": "number between 0 and 1",
    }

    EMOTION_LABELS = ["heyecanli", "stabil", "hayal_kirikligi", "tukenmis", "kaygili"]

    BASE_THEME_LABELS = [
        "teknik borc",
        "code review",
        "toplanti yogunlugu",
        "mentorluk eksikligi",
        "deadline baskisi",
        "surec yavasligi",
        "psikolojik guven",
        "aidiyet",
        "motivasyon dususu",
        "is birligi",
        "is yuku",
        "dokumantasyon",
        "blokaj yonetimi",
        "iletisim kalitesi",
        "liderlik destegi",
    ]

    DEPARTMENT_THEME_HINTS = {
        "Yazilim Gelistirme": [
            "technical debt",
            "teknik borc",
            "code review",
            "pull request",
            "mentorluk eksikligi",
            "deadline baskisi",
            "dokumantasyon",
            "test disiplini",
            "surec yavasligi",
        ],
        "Insan Kaynaklari": [
            "aday deneyimi",
            "ise alim sureci",
            "ic iletisim",
            "mentorluk eksikligi",
            "toplanti yogunlugu",
            "deadline baskisi",
        ],
        "Pazarlama": [
            "kampanya baskisi",
            "deadline baskisi",
            "is birligi",
            "toplanti yogunlugu",
            "liderlik destegi",
        ],
        "Satis": [
            "hedef baskisi",
            "deadline baskisi",
            "crm disiplini",
            "liderlik destegi",
            "motivasyon dususu",
        ],
    }

    @staticmethod
    def _normalize_text(value: str) -> str:
        replacements = {
            "ı": "i",
            "İ": "I",
            "ğ": "g",
            "Ğ": "G",
            "ü": "u",
            "Ü": "U",
            "ş": "s",
            "Ş": "S",
            "ö": "o",
            "Ö": "O",
            "ç": "c",
            "Ç": "C",
        }
        normalized = value
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        return normalized

    @staticmethod
    def _role_bucket(target_role: UserRole) -> str:
        return "manager" if target_role in (UserRole.admin, UserRole.department_manager) else "employee"

    @staticmethod
    def _build_prompt(
        dept_name: str,
        target_role: UserRole,
        week_theme: str,
        direction_label_tr: str,
    ) -> tuple[str, list[str]]:
        normalized_dept = AIService._normalize_text(dept_name)
        normalized_theme = AIService._normalize_text(week_theme)
        role_bucket = AIService._role_bucket(target_role)
        role_label_tr = "Yonetici" if role_bucket == "manager" else "Calisan"
        dept_matrix = AIService.DEPARTMENT_ROLE_MATRIX.get(normalized_dept, {})
        required_terms = dept_matrix.get(
            role_bucket,
            ["is birligi", "surec disiplini", "gelisim ihtiyaci"],
        )
        theme_goal = AIService.WEEK_THEME_GUIDANCE.get(
            normalized_theme,
            "calisanin performansini ve ihtiyaclarini gorunur kil",
        )
        role_focus = AIService.ROLE_BEHAVIOR_GUIDANCE.get(role_bucket, "uygulama disiplini ve ekip davranislari")
        signal_focus = AIService.WEEK_SIGNAL_GUIDANCE.get(
            normalized_theme,
            "performans, davranis ve destek ihtiyaci sinyalleri",
        )
        hint = ", ".join(required_terms)

        prompt = (
            "SISTEM TALIMATI:\n"
            "Sen her departmanin uzmanlik dilini konusabilen kidemli bir IK stratejisti ve organizasyon psikologusun.\n"
            "Gorevin, haftalik 360 geri bildirim akisi icin kisa, analitik, aksiyon odakli Turkce soru uretmektir.\n\n"
            "DEGERLENDIRILEN KISI BAGLAMI:\n"
            f"- Departman: {normalized_dept}\n"
            f"- Rol: {role_label_tr}\n"
            f"- Haftanin temasi: {normalized_theme}\n"
            f"- Geri bildirim yonu: {direction_label_tr}\n"
            f"- Tematik amac: {theme_goal}\n"
            f"- Rol odagi: {role_focus}\n"
            f"- Davranissal/NLP sinyal odagi: {signal_focus}\n"
            f"- Zorunlu odak kelimeleri: {hint}\n\n"
            "SORU URETIM KURALLARI:\n"
            "- Cikti maksimum 2 cumle olsun.\n"
            "- Yalnizca soru cumlesini don, aciklama ekleme.\n"
            "- Her soruda yalnizca TEK spesifik yetkinlik veya davranisa odaklan.\n"
            "- Ayni soruda birden fazla ana yetkinligi birlestirme.\n"
            "- Soyut kavramlar yerine somut ve gozlemlenebilir davranis sor.\n"
            "- En az bir zorunlu odak kelimesini aynen kullan.\n"
            "- Sorunun icinde motivasyon kaybi, aidiyet zayiflamasi, tukenmislik veya flight risk sinyali yakalanabilecek bir nufans olsun.\n"
            "- Yonetici icin soru, mentorluk kalitesi veya ekibin onunu acma becerisine odaklansin.\n"
            "- Calisan icin soru, uygulama disiplini veya ekip uyumuna odaklansin.\n"
            "- Soru 1-5 ile puanlanabilir veya kisa gozlemle desteklenebilir bir yapi tasiyabilir.\n"
            "- Genel ve geveze kaliplardan kacin.\n"
            "- Enum, degisken adi, markdown veya sistem etiketi yazma.\n"
        )
        return prompt, required_terms

    @staticmethod
    def _build_compact_prompt(
        dept_name: str,
        target_role: UserRole,
        week_theme: str,
        direction_label_tr: str,
    ) -> tuple[str, list[str]]:
        normalized_dept = AIService._normalize_text(dept_name)
        normalized_theme = AIService._normalize_text(week_theme)
        role_bucket = AIService._role_bucket(target_role)
        role_label_tr = "yonetici" if role_bucket == "manager" else "calisan"
        dept_matrix = AIService.DEPARTMENT_ROLE_MATRIX.get(normalized_dept, {})
        required_terms = dept_matrix.get(
            role_bucket,
            ["is birligi", "surec disiplini", "gelisim ihtiyaci"],
        )
        focus_term = required_terms[0]
        role_focus = AIService.ROLE_BEHAVIOR_GUIDANCE.get(role_bucket, "uygulama disiplini")
        signal_focus = AIService.WEEK_SIGNAL_GUIDANCE.get(normalized_theme, "motivasyon veya performans sinyali")
        prompt = (
            "Tek gorevin tek cumlelik Turkce bir haftalik geri bildirim sorusu yazmak.\n"
            f"Departman: {normalized_dept}\n"
            f"Rol: {role_label_tr}\n"
            f"Tema: {normalized_theme}\n"
            f"Yon: {direction_label_tr}\n"
            f"Rol odagi: {role_focus}\n"
            f"Sinyal odagi: {signal_focus}\n"
            f"Zorunlu ifade: {focus_term}\n"
            "Kurallar:\n"
            "- Sadece soruyu yaz.\n"
            "- Maksimum 2 cumle olsun.\n"
            "- Tek bir davranis veya yetkinlige odaklan.\n"
            "- Soruda zorunlu ifade aynen gecsin.\n"
            "- Soru somut, gozlemlenebilir ve kisa olsun.\n"
            "- Tukenmislik, aidiyet kaybi veya flight risk sinyali yakalanabilecek nufans tasiyabilsin.\n"
        )
        return prompt, required_terms

    @staticmethod
    def _generate_with_ollama(prompt: str) -> Optional[str]:
        model_name = AIService._resolve_ollama_model()
        if not model_name:
            return None
        try:
            res = requests.post(
                AIService.OLLAMA_URL,
                json={"model": model_name, "prompt": prompt, "stream": False},
                timeout=20,
            )
            if res.ok:
                return (res.json().get("response") or "").strip() or None
        except Exception:
            return None
        return None

    @staticmethod
    def _resolve_ollama_model() -> Optional[str]:
        if AIService._RESOLVED_OLLAMA_MODEL:
            return AIService._RESOLVED_OLLAMA_MODEL

        configured_model = (AIService.OLLAMA_MODEL or "").strip()
        try:
            tags_url = AIService.OLLAMA_URL.rsplit("/", 1)[0] + "/tags"
            res = requests.get(tags_url, timeout=10)
            if not res.ok:
                return configured_model or None

            models = [item.get("name", "").strip() for item in res.json().get("models", []) if item.get("name")]
            if not models:
                return configured_model or None

            if configured_model in models:
                AIService._RESOLVED_OLLAMA_MODEL = configured_model
                return configured_model

            prefix_match = next(
                (name for name in models if configured_model and name.startswith(configured_model)),
                None,
            )
            if prefix_match:
                AIService._RESOLVED_OLLAMA_MODEL = prefix_match
                return prefix_match

            llama_match = next((name for name in models if "llama" in name.lower()), None)
            if llama_match:
                AIService._RESOLVED_OLLAMA_MODEL = llama_match
                return llama_match

            AIService._RESOLVED_OLLAMA_MODEL = models[0]
            return models[0]
        except Exception:
            return configured_model or None

    @staticmethod
    def _generate_with_gemini(prompt: str) -> Optional[str]:
        if not AIService.GEMINI_API_KEY:
            return None
        model_name = AIService._resolve_gemini_model()
        if not model_name:
            return None
        try:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model_name}:generateContent?key={AIService.GEMINI_API_KEY}"
            )
            body = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(url, json=body, timeout=20)
            if not res.ok:
                return None
            candidates = res.json().get("candidates", [])
            if not candidates:
                return None
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return None
            return (parts[0].get("text") or "").strip() or None
        except Exception:
            return None

    @staticmethod
    def _resolve_gemini_model() -> Optional[str]:
        if AIService._RESOLVED_GEMINI_MODEL:
            return AIService._RESOLVED_GEMINI_MODEL

        configured_model = (AIService.GEMINI_MODEL or "").strip()
        try:
            list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={AIService.GEMINI_API_KEY}"
            res = requests.get(list_url, timeout=15)
            if not res.ok:
                return configured_model or None

            models = []
            for item in res.json().get("models", []):
                name = (item.get("name") or "").replace("models/", "").strip()
                methods = item.get("supportedGenerationMethods", [])
                if name and "generateContent" in methods:
                    models.append(name)

            if not models:
                return configured_model or None

            if configured_model in models:
                AIService._RESOLVED_GEMINI_MODEL = configured_model
                return configured_model

            prefix_match = next(
                (name for name in models if configured_model and name.startswith(configured_model)),
                None,
            )
            if prefix_match:
                AIService._RESOLVED_GEMINI_MODEL = prefix_match
                return prefix_match

            preferred_match = next(
                (name for name in models if name.startswith("gemini-2.5-flash")),
                None,
            ) or next(
                (name for name in models if name.startswith("gemini-2.0-flash")),
                None,
            )
            if preferred_match:
                AIService._RESOLVED_GEMINI_MODEL = preferred_match
                return preferred_match

            AIService._RESOLVED_GEMINI_MODEL = models[0]
            return models[0]
        except Exception:
            return configured_model or None

    @staticmethod
    def _clean_generated_question(raw_text: str) -> Optional[str]:
        cleaned = raw_text.strip().strip('"').strip("'")
        if not cleaned:
            return None

        lines = [line.strip(" -\"'") for line in cleaned.splitlines() if line.strip()]
        question_line = next((line for line in lines if "?" in line), None)
        if question_line is None and lines:
            question_line = lines[-1]

        if not question_line:
            return None

        blocked_markers = [
            "sistem talimati",
            "gereklilikler",
            "soru uretimi",
            "kurallar",
            "departman:",
            "rol:",
            "tema:",
            "yon:",
        ]
        lowered = question_line.lower()
        if any(marker in lowered for marker in blocked_markers):
            return None

        question = AIService._normalize_text(question_line)
        question = question.replace("`", "").replace("*", "")
        question = question.replace("[Degerlendirilen Kisi]'nin", "bu kisinin")
        question = question.replace("[Degerlendirilen Kisi]", "bu kisi")
        question = question.replace("[Isim]'in", "bu kisinin")
        question = question.replace("[Isim]", "bu kisi")
        question = question.replace("[Calisan Adi]'nin", "bu kisinin")
        question = question.replace("[Calisan Adi]", "bu kisi")
        question = question.strip().strip('"').strip("'")
        if not question.endswith("?"):
            question += "?"
        if len(question.split()) < 6:
            return None
        return question

    @staticmethod
    def _matches_required_terms(question: str, terms: list[str]) -> bool:
        lowered = question.lower()
        for term in terms:
            normalized_term = AIService._normalize_text(term).lower()
            if normalized_term in lowered:
                return True

            term_tokens = [token for token in normalized_term.split() if len(token) > 3]
            if term_tokens and sum(token in lowered for token in term_tokens) >= max(1, min(2, len(term_tokens))):
                return True
        return False

    @staticmethod
    def _extract_json_object(raw_text: str) -> Optional[dict]:
        if not raw_text:
            return None

        cleaned = raw_text.strip()
        if "```" in cleaned:
            cleaned = cleaned.replace("```json", "```").replace("```JSON", "```")
            parts = [part.strip() for part in cleaned.split("```") if part.strip()]
            for part in parts:
                try:
                    parsed = json.loads(part)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    continue

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(cleaned[start:end + 1])
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                return None
        return None

    @staticmethod
    def _bound_score(value, default: float = 3.0) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = default
        return round(min(max(numeric, 1.0), 5.0), 2)

    @staticmethod
    def _bound_sentiment(value, default: float = 0.0) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = default
        return round(min(max(numeric, -1.0), 1.0), 2)

    @staticmethod
    def _bound_unit_interval(value, default: float = 0.5) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = default
        return round(min(max(numeric, 0.0), 1.0), 2)

    @staticmethod
    def _bound_int(value, minimum: int, maximum: int, default: int) -> int:
        try:
            numeric = int(round(float(value)))
        except (TypeError, ValueError):
            numeric = default
        return min(max(numeric, minimum), maximum)

    @staticmethod
    def _list_of_strings(value, limit: int = 5) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()][:limit]
        return []

    @staticmethod
    def _emotion_spectrum_value(value) -> list[dict]:
        if not isinstance(value, list):
            return []
        emotions = []
        for item in value:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or "").strip().lower()
            if label not in AIService.EMOTION_LABELS:
                continue
            emotions.append({
                "label": label,
                "score": AIService._bound_unit_interval(item.get("score"), 0.0),
            })
        deduped = {}
        for item in emotions:
            deduped[item["label"]] = max(item["score"], deduped.get(item["label"], 0.0))
        sorted_items = sorted(
            [{"label": label, "score": score} for label, score in deduped.items()],
            key=lambda item: item["score"],
            reverse=True,
        )
        return sorted_items[:5]

    @staticmethod
    def _detect_theme_labels(text: str, question_text: str, dept_name: str) -> list[str]:
        combined = f"{AIService._normalize_text(question_text)} {AIService._normalize_text(text)}".lower()
        candidates = list(AIService.BASE_THEME_LABELS)
        candidates.extend(AIService.DEPARTMENT_THEME_HINTS.get(AIService._normalize_text(dept_name), []))
        found = []
        for label in candidates:
            normalized_label = AIService._normalize_text(label).lower()
            label_tokens = [token for token in normalized_label.split() if len(token) > 3]
            if normalized_label in combined or (
                label_tokens and sum(token in combined for token in label_tokens) >= min(2, len(label_tokens))
            ):
                found.append(normalized_label)
        seen = set()
        ordered = []
        for item in found:
            if item not in seen:
                seen.add(item)
                ordered.append(item)
        return ordered[:6]

    @staticmethod
    def _derive_emotion_spectrum(
        sentiment_score: float,
        motivation_score: float,
        psychological_safety_score: float,
        negative_hits: int,
        positive_hits: int,
    ) -> list[dict]:
        heyecanli = AIService._bound_unit_interval(
            max(0.0, (sentiment_score + 1) / 2 * 0.55 + max(motivation_score - 3, 0) * 0.12 + positive_hits * 0.06),
            0.2,
        )
        stabil = AIService._bound_unit_interval(
            max(0.0, 0.45 + (1 - abs(sentiment_score)) * 0.3 - abs(motivation_score - 3) * 0.08),
            0.5,
        )
        hayal_kirikligi = AIService._bound_unit_interval(
            max(0.0, negative_hits * 0.16 + max(3 - motivation_score, 0) * 0.16 + max(-sentiment_score, 0) * 0.4),
            0.2,
        )
        tukenmis = AIService._bound_unit_interval(
            max(0.0, negative_hits * 0.15 + max(3 - motivation_score, 0) * 0.2 + max(3 - psychological_safety_score, 0) * 0.08),
            0.15,
        )
        kaygili = AIService._bound_unit_interval(
            max(0.0, negative_hits * 0.14 + max(3 - psychological_safety_score, 0) * 0.18 + max(-sentiment_score, 0) * 0.25),
            0.2,
        )
        spectrum = [
            {"label": "heyecanli", "score": heyecanli},
            {"label": "stabil", "score": stabil},
            {"label": "hayal_kirikligi", "score": hayal_kirikligi},
            {"label": "tukenmis", "score": tukenmis},
            {"label": "kaygili", "score": kaygili},
        ]
        return sorted(spectrum, key=lambda item: item["score"], reverse=True)

    @staticmethod
    def _sanitize_analysis_payload(payload: dict) -> Optional[dict]:
        if not isinstance(payload, dict):
            return None

        sentiment_label = str(payload.get("sentiment_label") or "neutral").lower()
        if sentiment_label not in {"positive", "neutral", "negative"}:
            sentiment_label = "neutral"

        def risk_value(key: str) -> str:
            value = str(payload.get(key) or "medium").lower()
            return value if value in {"low", "medium", "high"} else "medium"

        manager_summary = AIService._sanitize_rag_text(payload.get("manager_summary"), max_len=500, min_words=5)
        action_recommendation = AIService._sanitize_rag_text(payload.get("action_recommendation"), max_len=300, min_words=3)

        sanitized = {
            "sentiment_label": sentiment_label,
            "sentiment_score": AIService._bound_sentiment(payload.get("sentiment_score"), 0.0),
            "motivation_score": AIService._bound_score(payload.get("motivation_score"), 3.0),
            "burnout_risk": risk_value("burnout_risk"),
            "flight_risk": risk_value("flight_risk"),
            "flight_risk_score": AIService._bound_int(payload.get("flight_risk_score"), 1, 10, 5),
            "psychological_safety_score": AIService._bound_score(payload.get("psychological_safety_score"), 3.0),
            "collaboration_score": AIService._bound_score(payload.get("collaboration_score"), 3.0),
            "growth_signal_score": AIService._bound_score(payload.get("growth_signal_score"), 3.0),
            "leadership_support_score": None if payload.get("leadership_support_score") is None else AIService._bound_score(payload.get("leadership_support_score"), 3.0),
            "emotion_spectrum": AIService._emotion_spectrum_value(payload.get("emotion_spectrum")),
            "dominant_emotions": AIService._list_of_strings(payload.get("dominant_emotions"), 3),
            "theme_labels": AIService._list_of_strings(payload.get("theme_labels"), 6),
            "entity_mentions": AIService._list_of_strings(payload.get("entity_mentions"), 6),
            "complaint_topics": AIService._list_of_strings(payload.get("complaint_topics"), 5),
            "praise_topics": AIService._list_of_strings(payload.get("praise_topics"), 5),
            "flight_risk_reasons": AIService._list_of_strings(payload.get("flight_risk_reasons"), 5),
            "burnout_signals": AIService._list_of_strings(payload.get("burnout_signals"), 5),
            "key_strengths": AIService._list_of_strings(payload.get("key_strengths"), 5),
            "risk_flags": AIService._list_of_strings(payload.get("risk_flags"), 5),
            "support_needs": AIService._list_of_strings(payload.get("support_needs"), 5),
            "keywords": AIService._list_of_strings(payload.get("keywords"), 6),
            "manager_summary": manager_summary,
            "action_recommendation": action_recommendation,
            "confidence": AIService._bound_unit_interval(payload.get("confidence"), 0.65),
        }

        if not sanitized["manager_summary"]:
            sentiment_text = {
                "positive": "olumlu",
                "neutral": "karışık",
                "negative": "olumsuz",
            }.get(sanitized["sentiment_label"], "karışık")
            theme_source = (
                sanitized["theme_labels"]
                or sanitized["complaint_topics"]
                or sanitized["praise_topics"]
                or ["genel durum"]
            )
            sanitized["manager_summary"] = (
                f"Çalışan geri bildiriminde {sentiment_text} bir ton öne çıkıyor; "
                f"motivasyon skoru {sanitized['motivation_score']}/5 ve ayrılma riski seviyesi {sanitized['flight_risk']} görünüyor. "
                f"Öne çıkan tema: {theme_source[0]}."
            )

        if not sanitized["action_recommendation"]:
            if sanitized["flight_risk"] == "high" or sanitized["burnout_risk"] == "high":
                sanitized["action_recommendation"] = "Acil birebir görüşme yapın ve ana blokajları kaldırın."
            elif sanitized["support_needs"]:
                sanitized["action_recommendation"] = f"{sanitized['support_needs'][0]} konusunda kısa bir destek planı hazırlayın."
            else:
                sanitized["action_recommendation"] = "Olumlu davranışları görünür kılın ve düzenli geri bildirim döngüsünü koruyun."
        return sanitized

    @staticmethod
    def _looks_like_placeholder_text(value: str) -> bool:
        normalized = AIService._normalize_text(value).lower().strip()
        if not normalized:
            return True

        placeholder_fragments = [
            "short turkish executive summary",
            "short turkish summary",
            "monthly emotional and motivation trend",
            "executive summary",
            "summary here",
            "placeholder",
            "lorem ipsum",
            "performed",
            "teamine",
            "employee satisfaction",
            "daily feedback trend",
        ]
        if any(fragment in normalized for fragment in placeholder_fragments):
            return True

        if normalized.startswith("{") or normalized.startswith("["):
            return True

        return False

    @staticmethod
    def _sanitize_rag_text(value: object, *, max_len: int, min_words: int = 5) -> str:
        if not isinstance(value, str):
            return ""

        cleaned = " ".join(value.strip().split())[:max_len]
        if AIService._looks_like_placeholder_text(cleaned):
            return ""

        word_count = len([token for token in cleaned.split(" ") if token.strip()])
        if word_count < min_words:
            return ""

        return cleaned

    @staticmethod
    def _sanitize_monthly_rag_payload(payload: dict) -> Optional[dict]:
        if not isinstance(payload, dict):
            return None

        retention_risk_level = str(payload.get("retention_risk_level") or "medium").lower()
        if retention_risk_level not in {"low", "medium", "high"}:
            retention_risk_level = "medium"

        report_summary = AIService._sanitize_rag_text(payload.get("report_summary"), max_len=700, min_words=6)
        trend_summary = AIService._sanitize_rag_text(payload.get("trend_summary"), max_len=500, min_words=5)
        action_recommendation = AIService._sanitize_rag_text(payload.get("action_recommendation"), max_len=300, min_words=3)
        key_takeaways = [
            item for item in AIService._list_of_strings(payload.get("key_takeaways"), 6)
            if not AIService._looks_like_placeholder_text(item) and len(item.split()) >= 3
        ]

        sanitized = {
            "report_summary": report_summary,
            "trend_summary": trend_summary,
            "flight_risk_score": AIService._bound_int(payload.get("flight_risk_score"), 1, 10, 5),
            "retention_risk_level": retention_risk_level,
            "top_complaint_topics": AIService._list_of_strings(payload.get("top_complaint_topics"), 5),
            "top_praise_topics": AIService._list_of_strings(payload.get("top_praise_topics"), 5),
            "key_takeaways": key_takeaways,
            "action_recommendation": action_recommendation,
            "confidence": AIService._bound_unit_interval(payload.get("confidence"), 0.65),
        }

        if not sanitized["report_summary"] or not sanitized["trend_summary"]:
            return None
        if not sanitized["action_recommendation"]:
            return None
        if len(sanitized["key_takeaways"]) < 2:
            return None

        return sanitized

    @staticmethod
    def _monthly_rag_prompt(
        *,
        subject_label: str,
        dept_name: str,
        period_label: str,
        deep_analysis: dict,
        retrieved_memories: list[dict],
    ) -> str:
        memory_lines = []
        for index, memory in enumerate(retrieved_memories[:5], start=1):
            memory_lines.append(
                f"{index}. skor={memory.get('score')} | tema={', '.join(memory.get('theme_labels') or [])} | "
                f"ozet={memory.get('content_summary') or memory.get('content_text')}"
            )

        deep_analysis_json = json.dumps(deep_analysis, ensure_ascii=True)
        memories_block = "\n".join(memory_lines) if memory_lines else "Benzer gecmis yorum bulunamadi."

        return (
            "SISTEM TALIMATI:\n"
            "Sen IK analitigi, organizasyon psikolojisi ve calisan deneyimi alaninda uzman kidemli bir analistsin.\n"
            "Gorevin, aylik geri bildirim trendi ile semantik olarak benzer gecmis yorumlari birlestirerek karar destek raporu cikarmak.\n"
            "Veri kalitesi ve karsilikli puanlama bias sinyallerini de yorumuna kat; kanit zayifsa daha temkinli konus.\n"
            "SADECE gecerli JSON don. Ek metin veya markdown yazma.\n\n"
            "JSON KONTRATI:\n"
            f"{json.dumps(AIService.MONTHLY_RAG_REPORT_CONTRACT, ensure_ascii=True)}\n\n"
            "BAGLAM:\n"
            f"- Incelenen hedef: {subject_label}\n"
            f"- Departman: {AIService._normalize_text(dept_name)}\n"
            f"- Donem: {period_label}\n"
            f"- Aylik derin analiz ozeti: {deep_analysis_json}\n"
            f"- Benzer gecmis yorumlar:\n{memories_block}\n\n"
            "KURALLAR:\n"
            "- report_summary yoneticinin hizli okuyacagi kadar net olsun.\n"
            "- trend_summary degisimin nedenini aciklasin.\n"
            "- flight_risk_score sadece mevcut kanita gore verilsin.\n"
            "- deep_analysis.quality_context icindeki low_quality_count veya bias_suspected_count yuksekse bunu dolayli olarak trend_summary ve action_recommendation icinde dikkate al.\n"
            "- Veri kalitesi dusukse kesin hukum kurma; 'temkinli yorum' mantigiyla yaz.\n"
            "- top_complaint_topics ve top_praise_topics tekrarlanan konulara dayansin.\n"
            "- key_takeaways alaninda 3-6 somut bulgu yaz.\n"
            "- action_recommendation kisa, uygulanabilir ve yonetsel olsun.\n"
        )

    @staticmethod
    def _fallback_monthly_rag_report(
        *,
        subject_label: str,
        deep_analysis: dict,
        retrieved_memories: list[dict],
    ) -> dict:
        flight_risk_score = AIService._bound_int(deep_analysis.get("flight_risk_score"), 1, 10, 5)
        if flight_risk_score >= 8:
            retention_risk_level = "high"
        elif flight_risk_score >= 5:
            retention_risk_level = "medium"
        else:
            retention_risk_level = "low"

        top_complaints = list(deep_analysis.get("top_complaint_topics") or [])[:5]
        top_praises = list(deep_analysis.get("top_praise_topics") or [])[:5]
        quality_context = deep_analysis.get("quality_context") or {}
        low_quality_count = int(quality_context.get("low_quality_count") or 0)
        bias_suspected_count = int(quality_context.get("bias_suspected_count") or 0)
        low_quality_topics = list(quality_context.get("low_quality_topics") or [])[:3]
        bias_topics = list(quality_context.get("bias_topics") or [])[:3]
        memory_topics = []
        memory_summaries = []
        for memory in retrieved_memories[:5]:
            memory_topics.extend(memory.get("theme_labels") or [])
            summary = memory.get("content_summary")
            if isinstance(summary, str) and summary.strip():
                memory_summaries.append(summary.strip())
        merged_takeaways = list(dict.fromkeys((deep_analysis.get("top_themes") or []) + memory_topics))[:5]

        if deep_analysis.get("motivation_trend_direction") == "dusus":
            trend_phrase = "son haftalarda dusus egilimi gosteriyor"
        elif deep_analysis.get("motivation_trend_direction") == "yukselis":
            trend_phrase = "son haftalarda toparlanma ve yukselis sinyali veriyor"
        else:
            trend_phrase = "genel olarak stabil seyrediyor"

        report_summary = (
            f"{subject_label} için aylık geri bildirimler {trend_phrase}. "
            f"En belirgin şikayet alanları {', '.join(top_complaints) if top_complaints else 'sınırlı'}; "
            f"elde tutma riski seviyesi ise {retention_risk_level} görünüyor."
        )
        if low_quality_count:
            report_summary += f" Ancak {low_quality_count} kayitta veri kalitesi sinyali oldugu icin yorum temkinli okunmali."
        trend_summary = (
            f"Tekrarlanan şikayet konuları: {', '.join(top_complaints) if top_complaints else 'belirgin şikayet yok'}. "
            f"Olumlu sinyaller: {', '.join(top_praises) if top_praises else 'belirgin övgü yok'}. "
            f"Geçmiş benzer yorumlar {len(retrieved_memories)} kayıtta özellikle {', '.join(memory_topics[:3]) if memory_topics else 'ek tema vermedi'}."
        )
        if bias_suspected_count:
            trend_summary += f" Ayrica {bias_suspected_count} kayitta karsilikli puanlama bias supheleri ({', '.join(bias_topics) if bias_topics else 'benzer puanlama davranislari'}) izlendi."
        if low_quality_count and low_quality_topics:
            trend_summary += f" Veri kalitesi acisindan en cok goze carpan sinyaller: {', '.join(low_quality_topics)}."
        action = deep_analysis.get("action_recommendation") or "Yönetsel birebir görüşme ile ana blokajları netleştirin."
        if bias_suspected_count:
            action += " Supheli karsilikli puanlamalari manuel olarak gozden gecirin."
        elif low_quality_count:
            action += " Kisa ve genelleyici geri bildirimlere karsi ekipte daha somut yorum beklentisini netlestirin."

        enriched_takeaways = merged_takeaways[:]
        if not enriched_takeaways and top_complaints:
            enriched_takeaways.extend(top_complaints[:3])
        if top_praises:
            enriched_takeaways.extend([item for item in top_praises if item not in enriched_takeaways][:2])
        if memory_summaries:
            enriched_takeaways.append(memory_summaries[0][:140])
        if low_quality_count:
            enriched_takeaways.append(f"veri kalitesi uyarisi:{low_quality_count}")
        if bias_suspected_count:
            enriched_takeaways.append(f"bias supheleri:{bias_suspected_count}")

        return {
            "report_summary": report_summary,
            "trend_summary": trend_summary,
            "flight_risk_score": flight_risk_score,
            "retention_risk_level": retention_risk_level,
            "top_complaint_topics": top_complaints,
            "top_praise_topics": top_praises,
            "key_takeaways": enriched_takeaways[:6],
            "action_recommendation": action,
            "confidence": 0.58,
        }

    @staticmethod
    def _analysis_prompt(
        *,
        dept_name: str,
        target_role: UserRole,
        week_theme: str,
        direction_label_tr: str,
        question_text: str,
        response_text: str,
        score_communication: float,
        score_teamwork: float,
        score_leadership: float,
        score_technical: float,
    ) -> str:
        normalized_dept = AIService._normalize_text(dept_name)
        normalized_theme = AIService._normalize_text(week_theme)
        role_bucket = AIService._role_bucket(target_role)
        role_label_tr = "Yonetici" if role_bucket == "manager" else "Calisan"
        role_focus = AIService.ROLE_BEHAVIOR_GUIDANCE.get(role_bucket, "uygulama disiplini ve ekip davranislari")
        signal_focus = AIService.WEEK_SIGNAL_GUIDANCE.get(normalized_theme, "motivasyon, risk ve destek ihtiyaci")

        return (
            "SISTEM TALIMATI:\n"
            "Sen Turkce calisan geri bildirimlerini yorumlayan analitik bir IK stratejisti ve organizasyon psikologusun.\n"
            "Amacin bir haftalik feedback cevabindan flight risk, burnout, motivasyon ve ekip sinyallerini cikarmak.\n"
            "SADECE gecerli JSON don. Ek metin, markdown, aciklama veya code block yazma.\n\n"
            "JSON KONTRATI:\n"
            f"{json.dumps(AIService.WEEKLY_ANALYSIS_JSON_CONTRACT, ensure_ascii=True)}\n\n"
            "BAGLAM:\n"
            f"- Departman: {normalized_dept}\n"
            f"- Degerlendirilen rol: {role_label_tr}\n"
            f"- Tema: {normalized_theme}\n"
            f"- Yon: {direction_label_tr}\n"
            f"- Rol odagi: {role_focus}\n"
            f"- Analiz sinyali odagi: {signal_focus}\n"
            f"- Soru: {AIService._normalize_text(question_text)}\n"
            f"- Cevap: {AIService._normalize_text(response_text)}\n"
            f"- Puanlar: iletisim={score_communication}, takim={score_teamwork}, liderlik={score_leadership}, teknik={score_technical}\n\n"
            "KURALLAR:\n"
            "- Sentiment label ve score birbiriyle tutarli olsun.\n"
            "- emotion_spectrum icinde heyecanli, stabil, hayal_kirikligi, tukenmis ve kaygili etiketlerinden uygun olanlari skorla.\n"
            "- dominant_emotions alaninda en baskin 3 duyguyu yaz.\n"
            "- theme_labels ve entity_mentions alanlari yorumun neden bahsettigini acikca gostersin.\n"
            "- flight_risk_score 1-10 arasinda olsun ve flight_risk_reasons ile aciklanabilsin.\n"
            "- complaint_topics ve praise_topics ayri ayri listelensin.\n"
            "- Risk seviyelerini sadece mevcut kanita gore ver, abartma.\n"
            "- manager_summary bir yoneticinin hizla okuyacagi kadar kisa olsun.\n"
            "- action_recommendation cok kisa, somut ve yonetsel bir aksiyon icersin.\n"
            "- keywords, risk_flags ve support_needs cok genel degil, metne dayali olsun.\n"
            "- Eger rol calisan ise leadership_support_score yine de yorumdan cikiyorsa ver, aksi halde null yaz.\n"
        )

    @staticmethod
    def _fallback_weekly_analysis(
        dept_name: str,
        response_text: str,
        question_text: str,
        score_communication: float,
        score_teamwork: float,
        score_leadership: float,
        score_technical: float,
    ) -> dict:
        normalized_text = AIService._normalize_text(response_text).lower()
        avg_score = round((score_communication + score_teamwork + score_leadership + score_technical) / 4, 2)

        strong_negative_keywords = [
            "tukend", "ayril", "kop", "onemsem", "isteksiz", "bagi zayif",
            "yalniz", "guvensiz", "destek yok", "yorulmus", "cok yorul",
        ]
        moderate_negative_keywords = [
            "stres", "baski", "deadline", "toplanti yogunlugu", "blokaj",
            "yavas", "cekingen", "geri cekil", "zorluk", "kararsiz",
        ]
        strong_positive_keywords = [
            "guven veren", "hevesli", "istekli", "olumlu tutum", "sahiplen",
            "destekleyici", "hizli donus", "yapici", "guclu", "takdir",
        ]
        moderate_positive_keywords = [
            "destek", "guven", "uyum", "gelisim", "ogren", "yardim",
            "acik", "seffaf", "cozum", "toparlan", "iyi",
        ]

        strong_negative_hits = sum(1 for keyword in strong_negative_keywords if keyword in normalized_text)
        moderate_negative_hits = sum(1 for keyword in moderate_negative_keywords if keyword in normalized_text)
        strong_positive_hits = sum(1 for keyword in strong_positive_keywords if keyword in normalized_text)
        moderate_positive_hits = sum(1 for keyword in moderate_positive_keywords if keyword in normalized_text)

        negative_signal = strong_negative_hits * 1.0 + moderate_negative_hits * 0.55
        positive_signal = strong_positive_hits * 0.95 + moderate_positive_hits * 0.45
        signal_balance = positive_signal - negative_signal

        sentiment_score = round(
            max(min(((avg_score - 3) / 2) + signal_balance * 0.1, 1), -1),
            2,
        )
        if sentiment_score > 0.2:
            sentiment_label = "positive"
        elif sentiment_score < -0.2:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"

        motivation_score = round(
            min(max(avg_score - negative_signal * 0.18 + positive_signal * 0.16, 1), 5),
            2,
        )
        psychological_safety_score = round(
            min(max(score_teamwork - negative_signal * 0.16 + positive_signal * 0.14, 1), 5),
            2,
        )
        collaboration_score = round(min(max((score_communication + score_teamwork) / 2, 1), 5), 2)
        growth_signal_score = round(
            min(max((score_technical + avg_score) / 2 - negative_signal * 0.1 + positive_signal * 0.08, 1), 5),
            2,
        )
        leadership_support_score = round(
            min(max(score_leadership - negative_signal * 0.14 + positive_signal * 0.08, 1), 5),
            2,
        )

        def risk_from_score(score: float, *, negative_signal_weight: float = 0.0, positive_signal_weight: float = 0.0) -> str:
            adjusted = score - negative_signal_weight + positive_signal_weight
            if adjusted >= 3.9:
                return "low"
            if adjusted >= 2.7:
                return "medium"
            return "high"

        burnout_risk = risk_from_score(
            motivation_score,
            negative_signal_weight=negative_signal * 0.28,
            positive_signal_weight=min(positive_signal * 0.18, 0.45),
        )
        flight_risk = risk_from_score(
            psychological_safety_score,
            negative_signal_weight=negative_signal * 0.3,
            positive_signal_weight=min(positive_signal * 0.2, 0.55),
        )

        extracted_keywords = []
        for candidate in ["blokaj", "destek", "guven", "motivasyon", "teknik borc", "code review", "iletisim", "uyum", "mentorluk"]:
            if candidate in normalized_text or candidate in AIService._normalize_text(question_text).lower():
                extracted_keywords.append(candidate)

        theme_labels = AIService._detect_theme_labels(response_text, question_text, dept_name)

        risk_flags = []
        if burnout_risk != "low":
            risk_flags.append("motivasyon dususu")
        if flight_risk == "high":
            risk_flags.append("aidiyet ve guven zayifligi")
        if "blokaj" in normalized_text or "engell" in normalized_text:
            risk_flags.append("surec blokaji")
        if "deadline" in normalized_text or "yetism" in normalized_text:
            risk_flags.append("deadline baskisi")
        if positive_signal >= negative_signal + 1.2:
            risk_flags = [flag for flag in risk_flags if flag != "motivasyon dususu"]

        strengths = []
        if collaboration_score >= 3.5:
            strengths.append("ekip uyumu")
        if growth_signal_score >= 3.5:
            strengths.append("gelisime aciklik")
        if leadership_support_score >= 3.5:
            strengths.append("destekleyici liderlik")

        support_needs = []
        if leadership_support_score < 3:
            support_needs.append("yonetsel destek")
        if psychological_safety_score < 3:
            support_needs.append("psikolojik guven")
        if growth_signal_score < 3:
            support_needs.append("gelisim yonlendirmesi")

        complaint_topics = []
        if ("blokaj" in normalized_text or "engell" in normalized_text) and positive_signal < negative_signal + 0.8:
            complaint_topics.append("surec yavasligi")
        if "toplanti" in normalized_text:
            complaint_topics.append("toplanti yogunlugu")
        if "mentorluk" in normalized_text or ("yonetici" in normalized_text and leadership_support_score < 3):
            complaint_topics.append("mentorluk eksikligi")
        if "deadline" in normalized_text or "yetism" in normalized_text:
            complaint_topics.append("deadline baskisi")

        praise_topics = []
        if "destek" in normalized_text:
            praise_topics.append("liderlik destegi")
        if "guven" in normalized_text:
            praise_topics.append("psikolojik guven")
        if "code review" in normalized_text or "pull request" in normalized_text:
            praise_topics.append("code review")
        if "uyum" in normalized_text or collaboration_score >= 3.8:
            praise_topics.append("is birligi")

        flight_risk_score = 3
        if flight_risk == "medium":
            flight_risk_score = 5
        elif flight_risk == "high":
            flight_risk_score = 8
        if "onemsem" in normalized_text or "benim gorevim degil" in normalized_text:
            flight_risk_score = min(flight_risk_score + 1, 10)
        if "gelecek" in normalized_text or "onumuzdeki yil" in normalized_text:
            flight_risk_score = max(flight_risk_score - 1, 1)
        if positive_signal >= negative_signal + 1.5 and avg_score >= 4.0:
            flight_risk_score = max(flight_risk_score - 2, 1)
        elif positive_signal > negative_signal and avg_score >= 3.6:
            flight_risk_score = max(flight_risk_score - 1, 1)

        flight_risk_reasons = []
        if "benim gorevim degil" in normalized_text or "onemsem" in normalized_text:
            flight_risk_reasons.append("bag kopuklugu ifadesi")
        if "surecler izin vermiyor" in normalized_text or "elimden geleni yapiyorum ama" in normalized_text:
            flight_risk_reasons.append("pasif agresif surec elestirisi")
        if flight_risk != "low" and negative_signal >= positive_signal:
            flight_risk_reasons.append("motivasyon ve psikolojik guven dususu")

        burnout_signals = []
        if "yoruld" in normalized_text or "tukend" in normalized_text:
            burnout_signals.append("yorgunluk ifadesi")
        if "stres" in normalized_text or "baski" in normalized_text:
            burnout_signals.append("stres ve baski sinyali")
        if burnout_risk == "high":
            burnout_signals.append("puanlarda genel dusus")

        emotion_spectrum = AIService._derive_emotion_spectrum(
            sentiment_score=sentiment_score,
            motivation_score=motivation_score,
            psychological_safety_score=psychological_safety_score,
            negative_hits=max(int(round(negative_signal)), 0),
            positive_hits=max(int(round(positive_signal)), 0),
        )
        dominant_emotions = [item["label"] for item in emotion_spectrum[:3]]

        action_recommendation = "Rutini koruyun ve olumlu davranislari takdir edin."
        if flight_risk == "high" or burnout_risk == "high":
            action_recommendation = "Acil birebir gorusme yapin ve blokajlari temizleyin."
        elif support_needs:
            action_recommendation = f"{support_needs[0]} konusunda yonetsel destek planlayin."

        manager_summary = (
            "Calisan geri bildiriminde "
            f"{'olumsuz' if sentiment_label == 'negative' else 'karisik' if sentiment_label == 'neutral' else 'olumlu'} bir ton var; "
            f"motivasyon skoru {motivation_score} ve flight risk seviyesi {flight_risk}. "
            f"Temel tema: {(theme_labels or complaint_topics or praise_topics or ['genel durum'])[0]}."
        )

        return {
            "sentiment_label": sentiment_label,
            "sentiment_score": sentiment_score,
            "motivation_score": motivation_score,
            "burnout_risk": burnout_risk,
            "flight_risk": flight_risk,
            "flight_risk_score": flight_risk_score,
            "psychological_safety_score": psychological_safety_score,
            "collaboration_score": collaboration_score,
            "growth_signal_score": growth_signal_score,
            "leadership_support_score": leadership_support_score,
            "emotion_spectrum": emotion_spectrum,
            "dominant_emotions": dominant_emotions,
            "theme_labels": theme_labels,
            "entity_mentions": list(dict.fromkeys(extracted_keywords + theme_labels))[:6],
            "complaint_topics": complaint_topics[:4],
            "praise_topics": praise_topics[:4],
            "flight_risk_reasons": flight_risk_reasons[:4],
            "burnout_signals": burnout_signals[:4],
            "key_strengths": strengths[:3],
            "risk_flags": risk_flags[:3],
            "support_needs": support_needs[:3],
            "keywords": extracted_keywords[:5],
            "manager_summary": manager_summary,
            "action_recommendation": action_recommendation,
            "confidence": 0.62,
        }

    @staticmethod
    def build_template_question(dept_name: str, target_role: UserRole, week_theme: str) -> str:
        normalized_dept = AIService._normalize_text(dept_name)
        normalized_theme = AIService._normalize_text(week_theme)
        role_bucket = AIService._role_bucket(target_role)
        dept_matrix = AIService.DEPARTMENT_ROLE_MATRIX.get(normalized_dept, {})
        focus_term = dept_matrix.get(role_bucket, ["is birligi"])[0]

        if normalized_theme == "Surecler & Blokajlar":
            if role_bucket == "manager":
                return (
                    f"Yoneticinin bu hafta ekipteki blokajlari kaldirma hizini, ozellikle {focus_term} konusunda ekibin onunu acma becerisi acisindan nasil degerlendirirsin? "
                    "Eksik kaldigini dusundugun somut bir nokta var mi?"
                )
            return (
                f"Bu kisinin bu hafta {focus_term} konusunda sergiledigi uygulama disiplini, ekibin is akisini yavaslatacak veya teknik borc biriktirecek bir risk tasiyor mu? "
                "Gozlemini paylas."
            )

        if normalized_theme == "Motivasyon & Psikolojik Durum":
            if role_bucket == "manager":
                return (
                    f"Yoneticinin bu hafta {focus_term} tarafindaki destegi, seni ve ekibi ne kadar guvende hissettirdi? "
                    "Motivasyon kaybi veya kopma riski olusturan bir eksiklik gozlemledin mi?"
                )
            return (
                f"Bu kisinin bu hafta {focus_term} sirasindaki istekliligi ve ekip hedeflerine olan inanci, motivasyon dususu veya kopma sinyali veriyor mu? "
                "Gozlemini paylas."
            )

        if normalized_theme == "Is Birligi & Seffaflik":
            if role_bucket == "manager":
                return (
                    f"Yoneticinin {focus_term} konusundaki iletisim tarzi ve ekibin onunu acma becerisi, ekip ici guveni ve acikligi guclendiriyor mu? "
                    "Kisa gozlemini paylas."
                )
            return (
                f"Bu kisinin bu hafta {focus_term} sirasindaki iletisimi ve ekip uyumu, takim enerjisini olumlu mu yoksa zorlayici mi etkiledi? "
                "Gozlemini paylas."
            )

        if role_bucket == "manager":
            return (
                f"Yoneticinin bu hafta {focus_term} alanindaki mentorluk kalitesi, ekibin gelisim hizini gercekten destekliyor mu? "
                "Eksik kaldigini dusundugun bir nokta var mi?"
            )
        return (
            f"Bu kisinin bu hafta {focus_term} alanindaki ogrenme istegi ve gelisim disiplini, sahiplenme gucunu mu gosteriyor yoksa durgunluk sinyali mi veriyor? "
            "Gozlemini paylas."
        )

    @staticmethod
    def generate_weekly_question(
        dept_name: str,
        target_role: UserRole,
        week_theme: str,
        direction_label_tr: str,
    ) -> Optional[str]:
        full_prompt, required_terms = AIService._build_prompt(
            dept_name,
            target_role,
            week_theme,
            direction_label_tr,
        )
        compact_prompt, compact_terms = AIService._build_compact_prompt(
            dept_name,
            target_role,
            week_theme,
            direction_label_tr,
        )

        attempts: list[tuple[Optional[str], list[str]]] = []
        if AIService.GEMINI_API_KEY:
            attempts.append((AIService._generate_with_gemini(full_prompt), required_terms))
        else:
            attempts.append((AIService._generate_with_ollama(compact_prompt), compact_terms))
            attempts.append((AIService._generate_with_ollama(full_prompt), required_terms))

        for raw_question, terms in attempts:
            if not raw_question:
                continue
            cleaned = AIService._clean_generated_question(raw_question)
            if not cleaned:
                continue
            if terms and not AIService._matches_required_terms(cleaned, terms):
                continue
            return cleaned
        return None

    @staticmethod
    def analyze_weekly_feedback(
        *,
        dept_name: str,
        target_role: UserRole,
        week_theme: str,
        direction_label_tr: str,
        question_text: str,
        response_text: str,
        score_communication: float,
        score_teamwork: float,
        score_leadership: float,
        score_technical: float,
    ) -> tuple[dict, str, str]:
        prompt = AIService._analysis_prompt(
            dept_name=dept_name,
            target_role=target_role,
            week_theme=week_theme,
            direction_label_tr=direction_label_tr,
            question_text=question_text,
            response_text=response_text,
            score_communication=score_communication,
            score_teamwork=score_teamwork,
            score_leadership=score_leadership,
            score_technical=score_technical,
        )

        if AIService.GEMINI_API_KEY:
            raw_output = AIService._generate_with_gemini(prompt)
            parsed = AIService._extract_json_object(raw_output or "")
            sanitized = AIService._sanitize_analysis_payload(parsed) if parsed else None
            if sanitized:
                return sanitized, "gemini", AIService._resolve_gemini_model() or AIService.GEMINI_MODEL or "gemini"

        raw_output = AIService._generate_with_ollama(prompt)
        parsed = AIService._extract_json_object(raw_output or "")
        sanitized = AIService._sanitize_analysis_payload(parsed) if parsed else None
        if sanitized:
            return sanitized, "ollama", AIService._resolve_ollama_model() or AIService.OLLAMA_MODEL or "ollama"

        fallback = AIService._fallback_weekly_analysis(
            dept_name=dept_name,
            response_text=response_text,
            question_text=question_text,
            score_communication=score_communication,
            score_teamwork=score_teamwork,
            score_leadership=score_leadership,
            score_technical=score_technical,
        )
        return fallback, "heuristic", "local-fallback-v1"

    @staticmethod
    def analyze_monthly_rag_report(
        *,
        subject_label: str,
        dept_name: str,
        period_label: str,
        deep_analysis: dict,
        retrieved_memories: list[dict],
    ) -> tuple[dict, str, str]:
        prompt = AIService._monthly_rag_prompt(
            subject_label=subject_label,
            dept_name=dept_name,
            period_label=period_label,
            deep_analysis=deep_analysis,
            retrieved_memories=retrieved_memories,
        )

        if AIService.GEMINI_API_KEY:
            raw_output = AIService._generate_with_gemini(prompt)
            parsed = AIService._extract_json_object(raw_output or "")
            sanitized = AIService._sanitize_monthly_rag_payload(parsed) if parsed else None
            if sanitized:
                return sanitized, "gemini", AIService._resolve_gemini_model() or AIService.GEMINI_MODEL or "gemini"

        raw_output = AIService._generate_with_ollama(prompt)
        parsed = AIService._extract_json_object(raw_output or "")
        sanitized = AIService._sanitize_monthly_rag_payload(parsed) if parsed else None
        if sanitized:
            return sanitized, "ollama", AIService._resolve_ollama_model() or AIService.OLLAMA_MODEL or "ollama"

        fallback = AIService._fallback_monthly_rag_report(
            subject_label=subject_label,
            deep_analysis=deep_analysis,
            retrieved_memories=retrieved_memories,
        )
        return fallback, "heuristic", "local-rag-fallback-v1"
