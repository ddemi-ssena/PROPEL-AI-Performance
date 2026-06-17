from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from math import ceil
import re
from typing import Any, Dict, Iterable, Optional

from sqlalchemy.orm import Session

from app.db.models.department import Department
from app.db.models.employee import Employee
from app.db.models.feedback import Feedback, FeedbackResponse, EmployeeBadge, BadgeType, BadgeLevel
from app.db.models.kpi import KPIRecord
from app.db.models.nlp import (
    EmployeeNLPProfile,
    EmployeeNLPReview,
    FeedbackNLPAnalysis,
    NLPPeriodType,
    NLPReviewStatus,
    NLPSourceType,
    RiskLevel,
    SentimentLabel,
)
from app.schemas.nlp import FeedbackNLPAnalysisCreate
from app.services.ai_service import AIService
from app.services.analytics_service import AnalyticsService
from app.services.rag_service import RAGService
from app.schemas.feedback import BadgeResponse


class NLPService:
    MONTHLY_BADGE_RULES: dict[BadgeType, dict[str, Any]] = {
        BadgeType.communicator: {
            "title": "Quality Gatekeeper",
            "keywords": ["code review", "pr", "pull request", "ogretici", "öğretici", "titiz", "yapici", "yapıcı", "kod kalitesi", "review"],
            "min_matches": 2,
        },
        BadgeType.reliable: {
            "title": "Legacy Hunter",
            "keywords": ["teknik borc", "technical debt", "legacy", "refactor", "refactoring", "modernize", "modernizasyon"],
            "min_matches": 2,
        },
        BadgeType.team_player: {
            "title": "Team Catalyst",
            "keywords": ["motivasyon", "pozitif enerji", "enerji", "ekip uyumu", "destekleyici", "guven veren", "güven veren"],
            "min_matches": 2,
        },
        BadgeType.problem_solver: {
            "title": "Block Buster",
            "keywords": ["blokaj", "engel", "cozum", "çözüm", "kriz", "sorumluluk alan", "hizli cozum", "hızlı çözüm"],
            "min_matches": 2,
        },
        BadgeType.mentor: {
            "title": "Knowledge Lighthouse",
            "keywords": ["mentor", "mentorluk", "ogretici", "öğretici", "yol gosteren", "yol gösteren", "bilgi paylasimi", "bilgi paylaşımı"],
            "min_matches": 2,
        },
        BadgeType.innovator: {
            "title": "Agile Mindset",
            "keywords": ["gelisime aciklik", "gelişime açıklık", "adaptasyon", "merak", "yeni kutuphane", "yeni kütüphane", "framework", "cevik", "çevik"],
            "min_matches": 2,
        },
    }

    @staticmethod
    def _get_latest_badge_period(
        db: Session,
        employee_id: int,
    ) -> Optional[date]:
        return (
            db.query(EmployeeBadge.period_date)
            .filter(EmployeeBadge.employee_id == employee_id)
            .order_by(EmployeeBadge.period_date.desc())
            .limit(1)
            .scalar()
        )
    @staticmethod
    def _raw_list_item(analysis: FeedbackNLPAnalysis, key: str) -> list[str]:
        raw_analysis = analysis.raw_analysis or {}
        value = raw_analysis.get(key)
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    @staticmethod
    def _week_of_month_from_datetime(value) -> int:
        target_date = value.date()
        first_day = target_date.replace(day=1)
        adjusted_dom = target_date.day + first_day.weekday()
        week_of_month = ceil(adjusted_dom / 7)
        return min(max(week_of_month, 1), 4)

    @staticmethod
    def _risk_from_average(value: Optional[float]) -> Optional[RiskLevel]:
        if value is None:
            return None
        if value >= 4:
            return RiskLevel.low
        if value >= 2.5:
            return RiskLevel.medium
        return RiskLevel.high

    @staticmethod
    def _dominant_items(values: Iterable[list[str] | None], limit: int = 3) -> list[str]:
        counter: Counter[str] = Counter()
        for group in values:
            for item in group or []:
                normalized = item.strip()
                if normalized:
                    counter[normalized] += 1
        return [item for item, _ in counter.most_common(limit)]

    @staticmethod
    def _extract_float(payload: Dict[str, Any], key: str) -> Optional[float]:
        value = payload.get(key)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _extract_enum(enum_cls, value):
        if value in (None, ""):
            return None
        try:
            return enum_cls(value)
        except ValueError:
            return None

    @staticmethod
    def _quality_signal(analysis: FeedbackNLPAnalysis) -> dict[str, Any]:
        raw_analysis = analysis.raw_analysis or {}
        value = raw_analysis.get("quality_signal")
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _reciprocity_signal(analysis: FeedbackNLPAnalysis) -> dict[str, Any]:
        raw_analysis = analysis.raw_analysis or {}
        value = raw_analysis.get("reciprocity_signal")
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _trusted_analyses(analyses: list[FeedbackNLPAnalysis]) -> list[FeedbackNLPAnalysis]:
        trusted = [
            analysis
            for analysis in analyses
            if not NLPService._quality_signal(analysis).get("is_low_quality")
        ]
        return trusted or analyses

    @staticmethod
    def _rag_quality_context(analyses: list[FeedbackNLPAnalysis]) -> dict[str, Any]:
        low_quality_items = [
            analysis for analysis in analyses
            if NLPService._quality_signal(analysis).get("is_low_quality")
        ]
        bias_items = [
            analysis for analysis in analyses
            if NLPService._reciprocity_signal(analysis).get("reciprocity_bias_suspected")
        ]

        return {
            "total_analysis_count": len(analyses),
            "low_quality_count": len(low_quality_items),
            "bias_suspected_count": len(bias_items),
            "low_quality_ratio": round((len(low_quality_items) / len(analyses)), 2) if analyses else 0.0,
            "bias_ratio": round((len(bias_items) / len(analyses)), 2) if analyses else 0.0,
            "low_quality_topics": NLPService._dominant_items(
                [NLPService._quality_signal(item).get("quality_reasons") or [] for item in low_quality_items],
                limit=4,
            ),
            "bias_topics": NLPService._dominant_items(
                [NLPService._reciprocity_signal(item).get("reciprocity_bias_reasons") or [] for item in bias_items],
                limit=4,
            ),
            "trusted_analysis_count": len(NLPService._trusted_analyses(analyses)),
        }

    @staticmethod
    def _trend_direction(values: list[Optional[float]]) -> str:
        numeric_values = [value for value in values if value is not None]
        if len(numeric_values) < 2:
            return "stabil"

        deltas = [
            numeric_values[index + 1] - numeric_values[index]
            for index in range(len(numeric_values) - 1)
        ]
        delta = numeric_values[-1] - numeric_values[0]
        average_delta = sum(deltas) / len(deltas)
        positive_steps = sum(1 for item in deltas if item > 0.12)
        negative_steps = sum(1 for item in deltas if item < -0.12)

        if delta > 0.35 and average_delta > 0.08 and positive_steps >= negative_steps:
            return "yukselis"
        if delta < -0.35 and average_delta < -0.08 and negative_steps >= positive_steps:
            return "dusus"
        return "stabil"

    @staticmethod
    def _weighted_numeric_average(
        values: Iterable[tuple[Optional[float], float]]
    ) -> Optional[float]:
        total = 0.0
        weight_total = 0.0
        for value, weight in values:
            if value is None:
                continue
            total += float(value) * weight
            weight_total += weight
        if weight_total <= 0:
            return None
        return round(total / weight_total, 1)

    @staticmethod
    def _weekly_average_series(analyses: list[FeedbackNLPAnalysis], field_name: str) -> list[float]:
        grouped: dict[int, list[float]] = {}
        for analysis in analyses:
            value = getattr(analysis, field_name)
            if value is None:
                continue
            week = NLPService._week_of_month_from_datetime(analysis.created_at)
            grouped.setdefault(week, []).append(float(value))
        return [
            round(sum(values) / len(values), 2)
            for week, values in sorted(grouped.items())
            if values
        ]

    @staticmethod
    def _count_raw_items(analyses: list[FeedbackNLPAnalysis], keys: list[str], limit: int = 5) -> list[tuple[str, int]]:
        counter: Counter[str] = Counter()
        for analysis in analyses:
            raw = analysis.raw_analysis or {}
            for key in keys:
                value = raw.get(key)
                if not isinstance(value, list):
                    continue
                for item in value:
                    normalized = " ".join(str(item).strip().lower().split())
                    if normalized:
                        counter[normalized] += 1
        return counter.most_common(limit)

    @staticmethod
    def _risk_level_from_driver_count(driver_count: int) -> Optional[str]:
        if driver_count >= 3:
            return "high"
        if driver_count >= 2:
            return "medium"
        if driver_count == 1:
            return "low"
        return None

    @staticmethod
    def _burnout_risk_drivers(
        analyses: list[FeedbackNLPAnalysis],
        *,
        motivation_trend: list[float] | None = None,
        safety_trend: list[float] | None = None,
        top_complaints: list[str] | None = None,
    ) -> tuple[list[dict[str, Any]], list[str], Optional[str]]:
        trusted = NLPService._trusted_analyses(analyses)
        motivation_series = motivation_trend if motivation_trend is not None else NLPService._weekly_average_series(trusted, "motivation_score")
        safety_series = safety_trend if safety_trend is not None else NLPService._weekly_average_series(trusted, "psychological_safety_score")
        drivers: list[dict[str, Any]] = []
        evidence: list[str] = []

        if len(motivation_series) >= 2:
            first = motivation_series[0]
            last = motivation_series[-1]
            delta = round(last - first, 2)
            if delta <= -0.5:
                text = f"Son {len(motivation_series)} haftada motivasyon {first:.1f} -> {last:.1f} dustu."
                drivers.append({
                    "label": "Motivasyon dususu",
                    "evidence": text,
                    "severity": "high" if delta <= -1.0 else "medium",
                })
                evidence.append(text)

        if len(safety_series) >= 2:
            first = safety_series[0]
            last = safety_series[-1]
            delta = round(last - first, 2)
            if delta <= -0.4:
                text = f"Psikolojik guven {first:.1f} -> {last:.1f} geriledi."
                drivers.append({
                    "label": "Psikolojik guven azalmasi",
                    "evidence": text,
                    "severity": "high" if delta <= -0.8 else "medium",
                })
                evidence.append(text)

        workload_terms = {
            "is yuku",
            "asiri yuk",
            "kapasite",
            "toplanti yogunlugu",
            "deadline",
            "quota baskisi",
            "blokaj",
            "oncelik",
            "stres",
            "yorgunluk",
            "burnout",
            "tukenmislik",
            "tukennislik",
        }
        counted_topics = NLPService._count_raw_items(
            trusted,
            ["complaint_topics", "support_needs", "risk_flags", "theme_labels"],
            limit=12,
        )
        visible_complaints = set(top_complaints or [])
        for topic, count in counted_topics:
            normalized = topic.lower()
            if not any(term in normalized for term in workload_terms) and topic not in visible_complaints:
                continue
            if count < 2:
                continue
            text = f"'{topic}' temasi {count} kez tekrarlandi."
            drivers.append({
                "label": "Tekrarlayan is yuku veya destek ihtiyaci",
                "evidence": text,
                "count": count,
                "severity": "high" if count >= 5 else "medium",
            })
            evidence.append(text)
            break

        explicit_burnout = sum(1 for analysis in trusted if analysis.burnout_risk == RiskLevel.high)
        if explicit_burnout:
            text = f"{explicit_burnout} geri bildirim kaydinda burnout riski high isaretlendi."
            drivers.append({
                "label": "Tekil NLP burnout sinyali",
                "evidence": text,
                "count": explicit_burnout,
                "severity": "high" if explicit_burnout >= 2 else "medium",
            })
            evidence.append(text)

        if not drivers:
            return [], [], None

        high_count = sum(1 for item in drivers if item.get("severity") == "high")
        medium_count = sum(1 for item in drivers if item.get("severity") == "medium")
        risk_level = "high" if high_count >= 1 or len(drivers) >= 3 else "medium" if medium_count or len(drivers) >= 2 else "low"
        return drivers[:4], evidence[:4], risk_level

    @staticmethod
    def _badge_level_for_unique_reviewers(unique_reviewer_count: int) -> Optional[BadgeLevel]:
        if unique_reviewer_count >= 4:
            return BadgeLevel.gold
        if unique_reviewer_count >= 3:
            return BadgeLevel.silver
        if unique_reviewer_count >= 2:
            return BadgeLevel.bronze
        return None

    @staticmethod
    def _analysis_text_blob(analysis: FeedbackNLPAnalysis) -> str:
        parts: list[str] = []
        parts.extend([str(item) for item in (analysis.key_strengths or [])])
        parts.extend([str(item) for item in (analysis.keywords or [])])
        if analysis.weekly_feedback and analysis.weekly_feedback.response_text:
            parts.append(str(analysis.weekly_feedback.response_text))
        if analysis.classic_feedback:
            parts.extend(
                [
                    str(analysis.classic_feedback.strength_text or ""),
                    str(analysis.classic_feedback.improvement_text or ""),
                    str(analysis.classic_feedback.general_comment or ""),
                ]
            )

        raw = analysis.raw_analysis or {}
        if isinstance(raw, dict):
            for key in [
                "praise_topics",
                "complaint_topics",
                "flight_risk_reasons",
                "theme_labels",
                "entity_mentions",
                "dominant_emotions",
                "support_needs",
                "manager_summary",
                "action_recommendation",
            ]:
                value = raw.get(key)
                if isinstance(value, list):
                    parts.extend([str(item) for item in value])
                elif isinstance(value, str):
                    parts.append(value)

        return " ".join(" ".join(parts).lower().split())

    @staticmethod
    def _distinctive_feedback_phrases(
        analyses: list[FeedbackNLPAnalysis],
        *,
        kind: str,
        limit: int = 3,
    ) -> list[str]:
        positive_patterns = [
            "code review sahiplenmesi",
            "test otomasyonu disiplini",
            "api entegrasyon takibi",
            "deploy sorumlulugu",
            "arayuz detay kalitesi",
            "bilgi paylasimi",
            "musteri takip disiplini",
            "crm kayit kalitesi",
            "pipeline onceliklendirme",
            "sikayet kapatma hizi",
            "mentorluk katkisi",
            "net durum guncellemesi",
            "sorumluluk alma",
            "psikolojik guven",
        ]
        negative_patterns = [
            "blokaj eskalasyonu gecikmesi",
            "test kapsaminda acik",
            "dokumantasyon eksigi",
            "deploy sonrasi takip eksigi",
            "arayuz kabul kriteri belirsizligi",
            "api bagimliligi gec bildirme",
            "crm guncelleme gecikmesi",
            "pipeline yaslanmasi",
            "quota baskisi",
            "musteri itirazlarini gec kapatma",
            "destek talebini gec acma",
            "oncelik degisikliklerinde zorlanma",
            "toplanti yogunlugu",
            "motivasyon dususu",
        ]
        theme_patterns = [
            "code review",
            "test otomasyonu",
            "api entegrasyonu",
            "deploy stabilitesi",
            "arayuz teslimi",
            "sprint planlama",
            "musteri takip",
            "crm disiplini",
            "pipeline sagligi",
            "quota yonetimi",
            "sikayet yonetimi",
            "mentorluk",
            "ekip koordinasyonu",
            "psikolojik guven",
        ]
        patterns = {
            "positive": positive_patterns,
            "negative": negative_patterns,
            "theme": theme_patterns,
        }[kind]
        generic = {
            "backend",
            "frontend",
            "qa",
            "devops",
            "junior",
            "mid",
            "senior",
            "engineer",
            "rol",
            "genel",
            "delivery",
            "quality",
            "growth",
            "risk",
            "leadership",
            "collaboration",
        }

        counter: Counter[str] = Counter()
        for analysis in analyses:
            blob = NLPService._analysis_text_blob(analysis)
            raw = analysis.raw_analysis or {}
            if kind == "negative":
                for key in ("complaint_topics", "flight_risk_reasons", "support_needs"):
                    for item in raw.get(key) or []:
                        normalized = " ".join(str(item).strip().lower().split())
                        if normalized:
                            counter[normalized] += 3
            if kind == "positive":
                for item in list(raw.get("praise_topics") or []) + list(analysis.key_strengths or []):
                    normalized = " ".join(str(item).strip().lower().split())
                    if normalized:
                        counter[normalized] += 3
            if kind == "theme":
                for item in raw.get("entity_mentions") or []:
                    normalized = " ".join(str(item).strip().lower().split())
                    if len(normalized) < 4 or normalized in generic:
                        continue
                    if re.fullmatch(r"[a-z]+", normalized) and normalized in generic:
                        continue
                    counter[normalized] += 3

            for pattern in patterns:
                if pattern in blob:
                    counter[pattern] += 1

        return [item for item, _ in counter.most_common(limit)]

    @staticmethod
    def _filter_topic_items(items: list[str], employee: Optional[Employee] = None, limit: int = 5) -> list[str]:
        generic = {
            "backend",
            "frontend",
            "qa",
            "devops",
            "junior",
            "mid",
            "senior",
            "engineer",
            "developer",
            "rol",
            "genel",
            "delivery",
            "quality",
            "growth",
            "risk",
            "leadership",
            "collaboration",
        }
        blocked: set[str] = set(generic)
        if employee:
            blocked.add(" ".join((employee.team or "").strip().lower().split()))
            blocked.add(" ".join((employee.position or "").strip().lower().split()))
            if employee.user:
                blocked.add(" ".join((employee.user.full_name or "").strip().lower().split()))

        filtered: list[str] = []
        for item in items:
            normalized = " ".join(str(item).strip().lower().split())
            if not normalized or normalized in blocked:
                continue
            if any(token in generic for token in normalized.split()) and len(normalized.split()) <= 3:
                continue
            if normalized not in filtered:
                filtered.append(normalized)
            if len(filtered) >= limit:
                break
        return filtered

    @staticmethod
    def _filter_generic_items(items: list[str], generic_items: set[str], limit: int = 5) -> list[str]:
        specific: list[str] = []
        generic: list[str] = []
        for item in items:
            normalized = " ".join(str(item).strip().lower().split())
            if not normalized:
                continue
            target = generic if normalized in generic_items else specific
            if normalized not in target:
                target.append(normalized)
        return (specific + generic)[:limit]

    @staticmethod
    def _raw_dominant_items(
        analyses: list[FeedbackNLPAnalysis],
        keys: list[str],
        *,
        limit: int = 3,
    ) -> list[str]:
        counter: Counter[str] = Counter()
        for analysis in analyses:
            raw = analysis.raw_analysis or {}
            for key in keys:
                for item in raw.get(key) or []:
                    normalized = " ".join(str(item).strip().lower().split())
                    if normalized:
                        counter[normalized] += 1
        return [item for item, _ in counter.most_common(limit)]

    @staticmethod
    def _matching_badge_analyses(
        analyses: list[FeedbackNLPAnalysis],
        *,
        keywords: list[str],
    ) -> list[FeedbackNLPAnalysis]:
        matches: list[FeedbackNLPAnalysis] = []
        for analysis in analyses:
            blob = NLPService._analysis_text_blob(analysis)
            if any(keyword.lower() in blob for keyword in keywords):
                matches.append(analysis)
        return matches

    @staticmethod
    def refresh_employee_monthly_badges(
        db: Session,
        *,
        employee_id: int,
        period_year: int,
        period_month: int,
    ) -> list[EmployeeBadge]:
        period_date = datetime(period_year, period_month, 1).date()
        analyses = db.query(FeedbackNLPAnalysis).filter(
            FeedbackNLPAnalysis.employee_id == employee_id,
            FeedbackNLPAnalysis.source_type == NLPSourceType.weekly_feedback,
        ).all()
        analyses = [
            item for item in analyses
            if item.created_at.year == period_year and item.created_at.month == period_month
        ]
        trusted_analyses = NLPService._trusted_analyses(analyses)

        existing_badges = db.query(EmployeeBadge).filter(
            EmployeeBadge.employee_id == employee_id,
            EmployeeBadge.period_date == period_date,
            EmployeeBadge.badge_type.in_(list(NLPService.MONTHLY_BADGE_RULES.keys())),
        ).all()
        for badge in existing_badges:
            db.delete(badge)
        db.flush()

        created_badges: list[EmployeeBadge] = []
        for badge_type, rule in NLPService.MONTHLY_BADGE_RULES.items():
            matched = NLPService._matching_badge_analyses(
                trusted_analyses,
                keywords=rule["keywords"],
            )
            unique_reviewers = {
                analysis.reviewer_employee_id
                for analysis in matched
                if analysis.reviewer_employee_id is not None
            }
            if len(matched) < rule["min_matches"]:
                continue

            badge_level = NLPService._badge_level_for_unique_reviewers(len(unique_reviewers))
            if not badge_level:
                continue

            source_feedback_ids = [
                analysis.weekly_feedback_id
                for analysis in matched
                if analysis.weekly_feedback_id is not None
            ][:10]

            badge = EmployeeBadge(
                employee_id=employee_id,
                badge_type=badge_type,
                badge_level=badge_level,
                period_date=period_date,
                source_feedback_ids=source_feedback_ids,
            )
            db.add(badge)
            created_badges.append(badge)

        db.flush()
        return created_badges

    @staticmethod
    def save_weekly_analysis(
        db: Session,
        feedback_response: FeedbackResponse,
        analysis_payload: Dict[str, Any],
        *,
        analysis_version: str = "v1",
        model_provider: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> FeedbackNLPAnalysis:
        question = feedback_response.question

        data = FeedbackNLPAnalysisCreate(
            source_type=NLPSourceType.weekly_feedback,
            weekly_feedback_id=feedback_response.id,
            employee_id=feedback_response.receiver_id,
            reviewer_employee_id=feedback_response.sender_id,
            department_id=feedback_response.receiver.department_id if feedback_response.receiver else None,
            direction=question.direction.value if question and question.direction else None,
            theme=question.category if question else None,
            analysis_version=analysis_version,
            model_provider=model_provider,
            model_name=model_name,
            sentiment_label=NLPService._extract_enum(SentimentLabel, analysis_payload.get("sentiment_label")),
            sentiment_score=NLPService._extract_float(analysis_payload, "sentiment_score"),
            motivation_score=NLPService._extract_float(analysis_payload, "motivation_score"),
            burnout_risk=NLPService._extract_enum(RiskLevel, analysis_payload.get("burnout_risk")),
            flight_risk=NLPService._extract_enum(RiskLevel, analysis_payload.get("flight_risk")),
            psychological_safety_score=NLPService._extract_float(analysis_payload, "psychological_safety_score"),
            collaboration_score=NLPService._extract_float(analysis_payload, "collaboration_score"),
            growth_signal_score=NLPService._extract_float(analysis_payload, "growth_signal_score"),
            leadership_support_score=NLPService._extract_float(analysis_payload, "leadership_support_score"),
            key_strengths=analysis_payload.get("key_strengths") or [],
            risk_flags=analysis_payload.get("risk_flags") or [],
            support_needs=analysis_payload.get("support_needs") or [],
            keywords=analysis_payload.get("keywords") or [],
            manager_summary=analysis_payload.get("manager_summary"),
            raw_analysis=analysis_payload,
        )

        existing = db.query(FeedbackNLPAnalysis).filter(
            FeedbackNLPAnalysis.weekly_feedback_id == feedback_response.id
        ).first()

        if existing:
            for field, value in data.model_dump().items():
                setattr(existing, field, value)
            record = existing
        else:
            record = FeedbackNLPAnalysis(**data.model_dump())
            db.add(record)

        feedback_response.nlp_analysis = analysis_payload
        db.flush()
        return record

    @staticmethod
    def save_classic_feedback_analysis(
        db: Session,
        feedback: Feedback,
        analysis_payload: Dict[str, Any],
        *,
        analysis_version: str = "v1",
        model_provider: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> FeedbackNLPAnalysis:
        data = FeedbackNLPAnalysisCreate(
            source_type=NLPSourceType.classic_feedback,
            classic_feedback_id=feedback.id,
            employee_id=feedback.reviewee_id,
            reviewer_employee_id=feedback.reviewer_id,
            department_id=feedback.reviewee.department_id if feedback.reviewee else None,
            direction=feedback.feedback_type.value if feedback.feedback_type else None,
            theme=None,
            analysis_version=analysis_version,
            model_provider=model_provider,
            model_name=model_name,
            sentiment_label=NLPService._extract_enum(SentimentLabel, analysis_payload.get("sentiment_label")),
            sentiment_score=NLPService._extract_float(analysis_payload, "sentiment_score"),
            motivation_score=NLPService._extract_float(analysis_payload, "motivation_score"),
            burnout_risk=NLPService._extract_enum(RiskLevel, analysis_payload.get("burnout_risk")),
            flight_risk=NLPService._extract_enum(RiskLevel, analysis_payload.get("flight_risk")),
            psychological_safety_score=NLPService._extract_float(analysis_payload, "psychological_safety_score"),
            collaboration_score=NLPService._extract_float(analysis_payload, "collaboration_score"),
            growth_signal_score=NLPService._extract_float(analysis_payload, "growth_signal_score"),
            leadership_support_score=NLPService._extract_float(analysis_payload, "leadership_support_score"),
            key_strengths=analysis_payload.get("key_strengths") or [],
            risk_flags=analysis_payload.get("risk_flags") or [],
            support_needs=analysis_payload.get("support_needs") or [],
            keywords=analysis_payload.get("keywords") or [],
            manager_summary=analysis_payload.get("manager_summary"),
            raw_analysis=analysis_payload,
        )

        existing = db.query(FeedbackNLPAnalysis).filter(
            FeedbackNLPAnalysis.classic_feedback_id == feedback.id
        ).first()

        if existing:
            for field, value in data.model_dump().items():
                setattr(existing, field, value)
            record = existing
        else:
            record = FeedbackNLPAnalysis(**data.model_dump())
            db.add(record)

        feedback.nlp_result = analysis_payload
        db.flush()
        return record

    @staticmethod
    def rebuild_employee_profile(
        db: Session,
        *,
        employee_id: int,
        period_type: NLPPeriodType,
        period_year: int,
        period_month: int,
        period_week: Optional[int] = None,
    ) -> EmployeeNLPProfile:
        analyses = db.query(FeedbackNLPAnalysis).filter(
            FeedbackNLPAnalysis.employee_id == employee_id,
        ).all()

        analyses = [
            item for item in analyses
            if item.created_at.year == period_year
            and item.created_at.month == period_month
            and (
                period_type != NLPPeriodType.weekly
                or (
                    period_week is not None
                    and NLPService._week_of_month_from_datetime(item.created_at) == period_week
                )
            )
        ]

        def avg(field_name: str) -> Optional[float]:
            values = [getattr(item, field_name) for item in analyses if getattr(item, field_name) is not None]
            if not values:
                return None
            return round(sum(values) / len(values), 2)

        feedback_count = len(analyses)
        avg_sentiment = avg("sentiment_score")
        avg_motivation = avg("motivation_score")
        avg_psych_safety = avg("psychological_safety_score")
        avg_collaboration = avg("collaboration_score")
        avg_growth = avg("growth_signal_score")

        top_strengths = NLPService._dominant_items(
            list(item.key_strengths or []) + NLPService._raw_list_item(item, "praise_topics")
            for item in analyses
        )
        top_risk_areas = NLPService._dominant_items(
            list(item.risk_flags or [])
            + NLPService._raw_list_item(item, "complaint_topics")
            + NLPService._raw_list_item(item, "flight_risk_reasons")
            for item in analyses
        )
        top_support_needs = NLPService._dominant_items(item.support_needs for item in analyses)

        latest_summary = next((item.manager_summary for item in reversed(analyses) if item.manager_summary), None)
        latest_action = next(
            (
                (item.raw_analysis or {}).get("action_recommendation")
                for item in reversed(analyses)
                if isinstance(item.raw_analysis, dict) and (item.raw_analysis or {}).get("action_recommendation")
            ),
            None,
        )

        existing = db.query(EmployeeNLPProfile).filter(
            EmployeeNLPProfile.employee_id == employee_id,
            EmployeeNLPProfile.period_type == period_type,
            EmployeeNLPProfile.period_year == period_year,
            EmployeeNLPProfile.period_month == period_month,
            EmployeeNLPProfile.period_week == period_week,
        ).first()

        payload = {
            "employee_id": employee_id,
            "department_id": analyses[-1].department_id if analyses else None,
            "period_type": period_type,
            "period_year": period_year,
            "period_month": period_month,
            "period_week": period_week,
            "feedback_count": feedback_count,
            "avg_sentiment_score": avg_sentiment,
            "avg_motivation_score": avg_motivation,
            "avg_psychological_safety_score": avg_psych_safety,
            "avg_collaboration_score": avg_collaboration,
            "avg_growth_signal_score": avg_growth,
            "burnout_risk_level": NLPService._risk_from_average(avg_motivation),
            "flight_risk_level": NLPService._risk_from_average(avg_psych_safety),
            "top_strengths": top_strengths,
            "top_risk_areas": top_risk_areas,
            "top_support_needs": top_support_needs,
            "manager_summary": latest_summary,
            "recommended_action": latest_action or (top_support_needs[0] if top_support_needs else None),
        }

        if existing:
            for field, value in payload.items():
                setattr(existing, field, value)
            profile = existing
        else:
            profile = EmployeeNLPProfile(**payload)
            db.add(profile)

        db.flush()
        return profile

    @staticmethod
    def get_employee_profile(
        db: Session,
        *,
        employee_id: int,
        period_type: NLPPeriodType,
        period_year: int,
        period_month: int,
        period_week: Optional[int] = None,
    ) -> Optional[EmployeeNLPProfile]:
        return db.query(EmployeeNLPProfile).filter(
            EmployeeNLPProfile.employee_id == employee_id,
            EmployeeNLPProfile.period_type == period_type,
            EmployeeNLPProfile.period_year == period_year,
            EmployeeNLPProfile.period_month == period_month,
            EmployeeNLPProfile.period_week == period_week,
        ).first()

    @staticmethod
    def get_or_build_employee_profile(
        db: Session,
        *,
        employee_id: int,
        period_type: NLPPeriodType,
        period_year: int,
        period_month: int,
        period_week: Optional[int] = None,
    ) -> EmployeeNLPProfile:
        profile = NLPService.get_employee_profile(
            db,
            employee_id=employee_id,
            period_type=period_type,
            period_year=period_year,
            period_month=period_month,
            period_week=period_week,
        )
        if profile:
            return profile
        return NLPService.rebuild_employee_profile(
            db,
            employee_id=employee_id,
            period_type=period_type,
            period_year=period_year,
            period_month=period_month,
            period_week=period_week,
        )

    @staticmethod
    def get_employee_nlp_review(
        db: Session,
        *,
        employee_id: int,
        period_type: NLPPeriodType,
        period_year: int,
        period_month: int,
        period_week: Optional[int] = None,
    ) -> Optional[EmployeeNLPReview]:
        return db.query(EmployeeNLPReview).filter(
            EmployeeNLPReview.employee_id == employee_id,
            EmployeeNLPReview.period_type == period_type,
            EmployeeNLPReview.period_year == period_year,
            EmployeeNLPReview.period_month == period_month,
            EmployeeNLPReview.period_week == period_week,
        ).first()

    @staticmethod
    def upsert_employee_nlp_review(
        db: Session,
        *,
        employee_id: int,
        department_id: Optional[int],
        reviewer_user_id: int,
        reviewer_employee_id: Optional[int],
        period_type: NLPPeriodType,
        period_year: int,
        period_month: int,
        period_week: Optional[int],
        status: NLPReviewStatus,
        note: Optional[str] = None,
        manager_acknowledged: bool = True,
    ) -> EmployeeNLPReview:
        existing = NLPService.get_employee_nlp_review(
            db,
            employee_id=employee_id,
            period_type=period_type,
            period_year=period_year,
            period_month=period_month,
            period_week=period_week,
        )

        payload = {
            "employee_id": employee_id,
            "department_id": department_id,
            "reviewer_user_id": reviewer_user_id,
            "reviewer_employee_id": reviewer_employee_id,
            "period_type": period_type,
            "period_year": period_year,
            "period_month": period_month,
            "period_week": period_week,
            "status": status,
            "note": note,
            "manager_acknowledged": manager_acknowledged,
            "reviewed_at": datetime.utcnow(),
        }

        if existing:
            for field, value in payload.items():
                setattr(existing, field, value)
            review = existing
        else:
            review = EmployeeNLPReview(**payload)
            db.add(review)

        db.commit()
        db.refresh(review)
        return review

    @staticmethod
    def get_recent_360_analyses(
        db: Session,
        *,
        employee_id: int,
        limit: int = 10,
    ) -> list[FeedbackNLPAnalysis]:
        return db.query(FeedbackNLPAnalysis).filter(
            FeedbackNLPAnalysis.employee_id == employee_id,
        ).order_by(FeedbackNLPAnalysis.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_recent_weekly_analyses(
        db: Session,
        *,
        employee_id: int,
        limit: int = 10,
    ) -> list[FeedbackNLPAnalysis]:
        return db.query(FeedbackNLPAnalysis).filter(
            FeedbackNLPAnalysis.employee_id == employee_id,
            FeedbackNLPAnalysis.source_type == NLPSourceType.weekly_feedback,
        ).order_by(FeedbackNLPAnalysis.created_at.desc()).limit(limit).all()

    @staticmethod
    def _filter_employees_by_team(
        employees: list[Employee],
        team: Optional[str] = None,
    ) -> list[Employee]:
        if not team:
            return employees
        normalized = team.strip().lower()
        return [
            employee
            for employee in employees
            if (employee.team or "").strip().lower() == normalized
        ]

    @staticmethod
    def _team_scope_label(team: Optional[str]) -> str:
        return f"{team} Takimi" if team else "Departman"

    @staticmethod
    def get_department_weekly_summary(
        db: Session,
        *,
        department_id: int,
        period_year: int,
        period_month: int,
        period_week: int,
        team: Optional[str] = None,
    ) -> dict:
        employees = db.query(Employee).filter(Employee.department_id == department_id).all()
        employees = NLPService._filter_employees_by_team(employees, team)
        profiles = [
            NLPService.get_or_build_employee_profile(
                db,
                employee_id=employee.id,
                period_type=NLPPeriodType.weekly,
                period_year=period_year,
                period_month=period_month,
                period_week=period_week,
            )
            for employee in employees
        ]

        active_profiles = [profile for profile in profiles if profile.feedback_count > 0]

        def avg(field_name: str) -> Optional[float]:
            values = [getattr(profile, field_name) for profile in active_profiles if getattr(profile, field_name) is not None]
            if not values:
                return None
            return round(sum(values) / len(values), 2)

        def risk_count(field_name: str, level: RiskLevel) -> int:
            return sum(1 for profile in active_profiles if getattr(profile, field_name) == level)

        top_strengths = NLPService._dominant_items(profile.top_strengths for profile in active_profiles)
        top_risk_areas = NLPService._dominant_items(profile.top_risk_areas for profile in active_profiles)
        top_support_needs = NLPService._dominant_items(profile.top_support_needs for profile in active_profiles)

        burnout_high = risk_count("burnout_risk_level", RiskLevel.high)
        flight_high = risk_count("flight_risk_level", RiskLevel.high)

        if burnout_high or flight_high:
            headline = f"{NLPService._team_scope_label(team)} icin dikkat isteyen risk sinyalleri var."
        elif active_profiles:
            headline = f"{NLPService._team_scope_label(team)} haftalik duygu ve risk gorunumu dengeli."
        else:
            headline = f"Bu hafta {NLPService._team_scope_label(team).lower()} icin yeterli NLP verisi olusmadi."

        recommended_action = top_support_needs[0] if top_support_needs else None

        return {
            "department_id": department_id,
            "period_year": period_year,
            "period_month": period_month,
            "period_week": period_week,
            "employee_count": len(employees),
            "analyzed_employee_count": len(active_profiles),
            "avg_sentiment_score": avg("avg_sentiment_score"),
            "avg_motivation_score": avg("avg_motivation_score"),
            "avg_psychological_safety_score": avg("avg_psychological_safety_score"),
            "avg_collaboration_score": avg("avg_collaboration_score"),
            "avg_growth_signal_score": avg("avg_growth_signal_score"),
            "high_burnout_count": burnout_high,
            "high_flight_risk_count": flight_high,
            "top_strengths": top_strengths,
            "top_risk_areas": top_risk_areas,
            "top_support_needs": top_support_needs,
            "headline": headline,
            "recommended_action": recommended_action,
            "team": team,
        }

    @staticmethod
    def _risk_level_from_score(value: Optional[float]) -> Optional[str]:
        if value is None:
            return None
        if value >= 4:
            return "low"
        if value >= 2.5:
            return "medium"
        return "high"

    @staticmethod
    def _display_score(value: Optional[float], suffix: str = "/5") -> str:
        return f"{value:.1f}{suffix}" if value is not None else "-"

    @staticmethod
    def _short_text(value: Optional[str], limit: int = 140) -> str:
        text = " ".join((value or "").split())
        if len(text) <= limit:
            return text
        return text[: limit - 3].rstrip() + "..."

    @staticmethod
    def _score_phrase(label: str, value: Optional[float]) -> Optional[str]:
        if value is None:
            return None
        return f"{label} {value:.1f}/5"

    @staticmethod
    def _latest_feedback_quote(analyses: list[FeedbackNLPAnalysis]) -> Optional[str]:
        for analysis in analyses:
            if analysis.weekly_feedback and analysis.weekly_feedback.response_text:
                return NLPService._short_text(analysis.weekly_feedback.response_text, 150)
            if analysis.classic_feedback:
                parts = [
                    analysis.classic_feedback.strength_text,
                    analysis.classic_feedback.improvement_text,
                    analysis.classic_feedback.general_comment,
                ]
                for part in parts:
                    if part:
                        return NLPService._short_text(part, 150)
        return None

    @staticmethod
    def _latest_kpi_context(db: Session, employee_id: int) -> dict[str, Any]:
        records = (
            db.query(KPIRecord)
            .filter(KPIRecord.employee_id == employee_id)
            .order_by(KPIRecord.period_date.asc())
            .all()
        )
        if not records:
            return {
                "has_data": False,
                "score": None,
                "trend": None,
                "status": "no_data",
                "record_count": 0,
                "latest_period": None,
                "strongest_label": None,
            }

        periods = sorted({record.period_date for record in records if record.period_date})
        latest_period = periods[-1] if periods else None
        last_four_periods = periods[-4:]
        latest_records = [record for record in records if record.period_date == latest_period]

        score = AnalyticsService._performance_score_for_records(latest_records)
        sparkline_values: list[float] = []
        for period in last_four_periods:
            period_score = AnalyticsService._performance_score_for_records([
                record for record in records if record.period_date == period
            ])
            if period_score is not None:
                sparkline_values.append(period_score)

        trend = None
        if len(sparkline_values) >= 2:
            trend = round(sparkline_values[-1] - sparkline_values[0], 1)

        strongest_label = None
        if latest_records:
            scored_records = []
            for record in latest_records:
                label = record.kpi.name if record.kpi else f"KPI #{record.kpi_id}"
                scored_records.append((AnalyticsService._normalize_kpi_value(float(record.value)), label))
            if scored_records:
                strongest_label = sorted(scored_records, key=lambda item: item[0], reverse=True)[0][1]

        return {
            "has_data": True,
            "score": score,
            "trend": trend,
            "status": AnalyticsService._status_for(score, trend),
            "record_count": len(records),
            "latest_period": latest_period,
            "strongest_label": strongest_label,
        }

    @staticmethod
    def _employee_manager_summary(
        *,
        employee: Employee,
        profile: EmployeeNLPProfile,
        analyses: list[FeedbackNLPAnalysis],
        kpi_context: dict[str, Any],
        burnout_evidence: list[str],
        badge_titles: list[str],
        low_quality_count: int,
        bias_count: int,
    ) -> tuple[str, list[str], str]:
        employee_name = employee.user.full_name if employee.user else f"Calisan #{employee.id}"
        first_name = employee_name.split()[0] if employee_name else "Calisan"

        evidence: list[str] = []
        score = kpi_context.get("score")
        trend = kpi_context.get("trend")
        if score is not None:
            trend_text = "trend yok"
            if trend is not None:
                trend_text = f"{trend:+.1f} trend"
            evidence.append(f"KPI skoru {score:.1f}/100, {trend_text}.")
        if kpi_context.get("strongest_label"):
            evidence.append(f"En guclu KPI sinyali: {kpi_context['strongest_label']}.")

        for item in [
            NLPService._score_phrase("Motivasyon", profile.avg_motivation_score),
            NLPService._score_phrase("psikolojik guven", profile.avg_psychological_safety_score),
            NLPService._score_phrase("is birligi", profile.avg_collaboration_score),
        ]:
            if item:
                evidence.append(item + ".")

        if profile.top_strengths:
            evidence.append(f"Tekrarlayan guclu yon: {profile.top_strengths[0]}.")
        if profile.top_risk_areas:
            evidence.append(f"One cikan risk alani: {profile.top_risk_areas[0]}.")
        if profile.top_support_needs:
            evidence.append(f"Destek ihtiyaci: {profile.top_support_needs[0]}.")
        if profile.flight_risk_level:
            confidence = f" ({profile.flight_risk_confidence:.0%} guven)" if profile.flight_risk_confidence is not None else ""
            evidence.append(f"Flight risk {profile.flight_risk_level.value}{confidence}.")
        if profile.burnout_risk_level:
            confidence = f" ({profile.burnout_risk_confidence:.0%} guven)" if profile.burnout_risk_confidence is not None else ""
            evidence.append(f"Burnout risk {profile.burnout_risk_level.value}{confidence}.")
        if burnout_evidence:
            evidence.append(burnout_evidence[0])
        if badge_titles:
            evidence.append(f"Kazandigi rozetler: {', '.join(badge_titles[:3])}.")

        quote = NLPService._latest_feedback_quote(analyses)
        if quote:
            evidence.append(f"Son geri bildirim kaniti: \"{quote}\"")

        if low_quality_count:
            evidence.append(f"{low_quality_count} kayitta veri kalitesi uyarisi var.")
        if bias_count:
            evidence.append(f"{bias_count} kayitta karsilikli bias supheleri var.")

        risk_signals = [
            bool(score is not None and score < 80),
            bool(trend is not None and trend < -1),
            bool(profile.avg_motivation_score is not None and profile.avg_motivation_score < 3),
            bool(profile.avg_psychological_safety_score is not None and profile.avg_psychological_safety_score < 3),
            bool(profile.flight_risk_level and profile.flight_risk_level.value in {"medium", "high"}),
            bool(profile.burnout_risk_level and profile.burnout_risk_level.value in {"medium", "high"}),
        ]
        positive_signals = [
            bool(score is not None and score >= 85),
            bool(trend is not None and trend > 0),
            bool(profile.avg_motivation_score is not None and profile.avg_motivation_score >= 4),
            bool(profile.avg_collaboration_score is not None and profile.avg_collaboration_score >= 4),
            bool(badge_titles),
        ]

        risk_count = sum(1 for item in risk_signals if item)
        positive_count = sum(1 for item in positive_signals if item)

        if not evidence:
            summary = (
                f"{employee_name} icin bu hafta guvenilir bir 360/KPI sinyali henuz olusmadi. "
                "Yonetici yorumu uretmek icin once KPI kaydi veya geri bildirim verisi artirilmalidir."
            )
            return summary, [], "Veri topla"

        if risk_count >= 3:
            opening = f"{employee_name} icin bu hafta yakin yonetici takibi gerektiren bir tablo var."
            action = "Bu hafta bire bir gorusme planla; motivasyon, is yuku ve destek ihtiyacini ayni gorusmede netlestir."
        elif risk_count >= 1:
            opening = f"{employee_name} icin tablo karisik; performans ve insan sinyalleri birlikte izlenmeli."
            action = "Kisa bir kontrol gorusmesiyle risk alanini dogrula ve bir sonraki hafta ayni metrikleri takip et."
        elif positive_count >= 3:
            opening = f"{employee_name} bu hafta guclu ve istikrarli katkilar gosteriyor."
            action = "Mevcut guclu alani gorunur kil; ekip icinde bilgi paylasimi veya mentorluk firsati ver."
        else:
            opening = f"{employee_name} icin bu hafta belirgin bir kritik risk yok, ancak takip gerektiren sinyaller var."
            action = "Duzenli takip yeterli; ozellikle tekrar eden tema ve KPI trendi bir sonraki hafta yeniden kontrol edilmeli."

        evidence_sentence = " ".join(evidence[:4])
        summary = f"{opening} Kanitlar: {evidence_sentence} Yonetici aksiyonu: {action}"
        return summary, evidence[:8], action

    @staticmethod
    def build_employee_360_summary_report(
        db: Session,
        *,
        employee_id: int,
        period_year: int,
        period_month: int,
        period_week: int,
    ) -> dict:
        employee = db.query(Employee).join(Employee.user).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError("Employee not found")

        profile = NLPService.get_or_build_employee_profile(
            db,
            employee_id=employee_id,
            period_type=NLPPeriodType.weekly,
            period_year=period_year,
            period_month=period_month,
            period_week=period_week,
        )
        recent_analyses = NLPService.get_recent_360_analyses(db, employee_id=employee_id, limit=8)

        quality_items = []
        bias_items = []
        low_quality_count = 0
        bias_count = 0

        for analysis in recent_analyses:
            quality_signal = NLPService._quality_signal(analysis)
            reciprocity_signal = NLPService._reciprocity_signal(analysis)

            if quality_signal.get("is_low_quality"):
                low_quality_count += 1
                reasons = quality_signal.get("quality_reasons") or []
                if reasons:
                    quality_items.extend([str(reason) for reason in reasons[:2]])
                else:
                    quality_items.append("kisa veya genel geçer yanit")

            if reciprocity_signal.get("reciprocity_bias_suspected"):
                bias_count += 1
                reasons = reciprocity_signal.get("reciprocity_bias_reasons") or []
                if reasons:
                    bias_items.extend([str(reason) for reason in reasons[:2]])
                else:
                    bias_items.append("ayni hafta karsilikli puan supheleri")

        burnout_drivers, burnout_evidence, burnout_driver_level = NLPService._burnout_risk_drivers(
            recent_analyses,
            top_complaints=profile.top_risk_areas or [],
        )
        kpi_context = NLPService._latest_kpi_context(db, employee_id)

        period_date = datetime(period_year, period_month, 1).date()
        badges = db.query(EmployeeBadge).filter(
            EmployeeBadge.employee_id == employee.id,
            EmployeeBadge.period_date == period_date,
        ).order_by(EmployeeBadge.created_at.desc()).all()
        if not badges:
            latest_period = NLPService._get_latest_badge_period(db, employee.id)
            if latest_period:
                badges = db.query(EmployeeBadge).filter(
                    EmployeeBadge.employee_id == employee.id,
                    EmployeeBadge.period_date == latest_period,
                ).order_by(EmployeeBadge.created_at.desc()).all()

        badge_titles = [
            NLPService.MONTHLY_BADGE_RULES.get(item.badge_type, {}).get("title", item.badge_type.value)
            for item in badges
        ]

        metrics = [
            {
                "label": "Motivasyon",
                "value": profile.avg_motivation_score,
                "display_value": NLPService._display_score(profile.avg_motivation_score),
                "risk_level": NLPService._risk_level_from_score(profile.avg_motivation_score),
                "description": "Haftalik geri bildirimlerden uretilen motivasyon skoru",
            },
            {
                "label": "Psikolojik Guven",
                "value": profile.avg_psychological_safety_score,
                "display_value": NLPService._display_score(profile.avg_psychological_safety_score),
                "risk_level": NLPService._risk_level_from_score(profile.avg_psychological_safety_score),
                "description": "Calisanin ekip icinde ne kadar guvende hissettigine dair sinyal",
            },
            {
                "label": "Is Birligi",
                "value": profile.avg_collaboration_score,
                "display_value": NLPService._display_score(profile.avg_collaboration_score),
                "risk_level": NLPService._risk_level_from_score(profile.avg_collaboration_score),
                "description": "Ekip uyumu ve destek davranislarina dair sinyal",
            },
            {
                "label": "Flight Risk",
                "value": None,
                "display_value": (profile.flight_risk_level.value if profile.flight_risk_level else "unknown").upper(),
                "risk_level": profile.flight_risk_level.value if profile.flight_risk_level else None,
                "confidence": profile.flight_risk_confidence,
                "description": "Aidiyet ve kopma sinyallerinin seviye ozeti",
            },
            {
                "label": "Burnout Risk",
                "value": None,
                "display_value": (profile.burnout_risk_level.value if profile.burnout_risk_level else "unknown").upper(),
                "risk_level": burnout_driver_level or (profile.burnout_risk_level.value if profile.burnout_risk_level else None),
                "confidence": profile.burnout_risk_confidence,
                "drivers": burnout_drivers,
                "description": "Yorgunluk ve tukennislik sinyallerinin seviye ozeti",
            },
        ]

        summary, manager_evidence, recommended_action = NLPService._employee_manager_summary(
            employee=employee,
            profile=profile,
            analyses=recent_analyses,
            kpi_context=kpi_context,
            burnout_evidence=burnout_evidence,
            badge_titles=badge_titles,
            low_quality_count=low_quality_count,
            bias_count=bias_count,
        )

        sections = [
            {"title": "Guclu Yonler", "items": profile.top_strengths or []},
            {"title": "Risk Alanlari", "items": profile.top_risk_areas or []},
            {"title": "Destek Ihtiyaclari", "items": profile.top_support_needs or []},
        ]
        if manager_evidence:
            sections.insert(0, {
                "title": "Yonetici Kanitlari",
                "items": manager_evidence,
            })
        if burnout_evidence:
            sections.append({
                "title": "Burnout Risk Drivers",
                "items": burnout_evidence,
            })
        if low_quality_count:
            sections.append({
                "title": "Veri Kalitesi Uyarilari",
                "items": [f"{low_quality_count} geri bildirim dusuk veri kalitesi sinyali tasiyor."] + NLPService._dominant_items([quality_items], limit=3),
            })
        if bias_count:
            sections.append({
                "title": "Bias Supheleri",
                "items": [f"{bias_count} kayitta karsilikli puanlama supheleri izlendi."] + NLPService._dominant_items([bias_items], limit=3),
            })

        return {
            "employee_id": employee.id,
            "employee_name": employee.user.full_name,
            "department_id": employee.department_id,
            "department_name": employee.department.name if employee.department else None,
            "team": employee.team,
            "position": employee.position,
            "period_year": period_year,
            "period_month": period_month,
            "period_week": period_week,
            "report_title": "Kisisel 360 Feedback Summary",
            "report_summary": summary,
            "recommended_action": profile.recommended_action or recommended_action,
            "badges": [BadgeResponse.model_validate(item) for item in badges],
            "metrics": metrics,
            "sections": sections,
        }

    @staticmethod
    def build_department_360_summary_report(
        db: Session,
        *,
        department_id: int,
        period_year: int,
        period_month: int,
        period_week: int,
        team: Optional[str] = None,
    ) -> dict:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise ValueError("Department not found")

        snapshot = NLPService.get_department_weekly_summary(
            db,
            department_id=department_id,
            period_year=period_year,
            period_month=period_month,
            period_week=period_week,
            team=team,
        )
        team_employee_ids = {
            employee.id
            for employee in NLPService._filter_employees_by_team(
                db.query(Employee).filter(Employee.department_id == department_id).all(),
                team,
            )
        }
        analyses = db.query(FeedbackNLPAnalysis).filter(
            FeedbackNLPAnalysis.department_id == department_id,
        ).all()
        analyses = [
            item for item in analyses
            if item.created_at.year == period_year
            and item.created_at.month == period_month
            and NLPService._week_of_month_from_datetime(item.created_at) == period_week
            and (not team_employee_ids or item.employee_id in team_employee_ids)
        ]
        low_quality_count = sum(1 for item in analyses if NLPService._quality_signal(item).get("is_low_quality"))
        bias_count = sum(1 for item in analyses if NLPService._reciprocity_signal(item).get("reciprocity_bias_suspected"))
        quality_topics = NLPService._dominant_items(
            [NLPService._quality_signal(item).get("quality_reasons") or [] for item in analyses],
            limit=3,
        )
        bias_topics = NLPService._dominant_items(
            [NLPService._reciprocity_signal(item).get("reciprocity_bias_reasons") or [] for item in analyses],
            limit=3,
        )

        metrics = [
            {
                "label": "Departman Motivasyonu",
                "value": snapshot["avg_motivation_score"],
                "display_value": NLPService._display_score(snapshot["avg_motivation_score"]),
                "risk_level": NLPService._risk_level_from_score(snapshot["avg_motivation_score"]),
                "description": "Departmandaki haftalik motivasyon ortalamasi",
            },
            {
                "label": "Psikolojik Guven",
                "value": snapshot["avg_psychological_safety_score"],
                "display_value": NLPService._display_score(snapshot["avg_psychological_safety_score"]),
                "risk_level": NLPService._risk_level_from_score(snapshot["avg_psychological_safety_score"]),
                "description": "Departmandaki guven ve aidiyet sinyal ortalamasi",
            },
            {
                "label": "Is Birligi",
                "value": snapshot["avg_collaboration_score"],
                "display_value": NLPService._display_score(snapshot["avg_collaboration_score"]),
                "risk_level": NLPService._risk_level_from_score(snapshot["avg_collaboration_score"]),
                "description": "Departman ici is birligi ve iletisim sinyali",
            },
            {
                "label": "Yuksek Flight Risk",
                "value": float(snapshot["high_flight_risk_count"]),
                "display_value": str(snapshot["high_flight_risk_count"]),
                "risk_level": "high" if snapshot["high_flight_risk_count"] else "low",
                "description": "Kritik kopma sinyali tasiyan calisan sayisi",
            },
            {
                "label": "Yuksek Burnout Risk",
                "value": float(snapshot["high_burnout_count"]),
                "display_value": str(snapshot["high_burnout_count"]),
                "risk_level": "high" if snapshot["high_burnout_count"] else "low",
                "description": "Kritik tukennislik sinyali tasiyan calisan sayisi",
            },
        ]

        sections = [
            {"title": "Departmanin Guclu Yonleri", "items": snapshot["top_strengths"]},
            {"title": "Departman Risk Temalari", "items": snapshot["top_risk_areas"]},
            {"title": "One Cikan Destek Ihtiyaclari", "items": snapshot["top_support_needs"]},
        ]
        if low_quality_count:
            sections.append({
                "title": "Veri Kalitesi Uyarilari",
                "items": [f"{low_quality_count} feedback kaydinda dusuk veri kalitesi sinyali var."] + quality_topics,
            })
        if bias_count:
            sections.append({
                "title": "Bias Supheleri",
                "items": [f"{bias_count} kayitta karsilikli puanlama supheleri izlendi."] + bias_topics,
            })

        scope_label = f"{department.name} / {team}" if team else f"{department.name} departmani"
        summary = (
            f"{scope_label} icin haftalik 360 feedback raporu: "
            f"{snapshot['headline']} "
            f"Analiz edilen {snapshot['analyzed_employee_count']} calisan icinde "
            f"{snapshot['high_flight_risk_count']} kiside yuksek flight risk, "
            f"{snapshot['high_burnout_count']} kiside yuksek burnout riski goruldu."
        )
        if low_quality_count:
            summary += f" Veri kalitesi sinyali {low_quality_count} kayitta izlendi."
        if bias_count:
            summary += f" Karsilikli bias supheleri {bias_count} kayitta tespit edildi."

        return {
            "department_id": department.id,
            "department_name": department.name,
            "period_year": period_year,
            "period_month": period_month,
            "period_week": period_week,
            "report_title": "Departman 360 Feedback Summary",
            "report_summary": summary,
            "recommended_action": snapshot["recommended_action"],
            "metrics": metrics,
            "sections": sections,
        }

    @staticmethod
    def build_department_nlp_charts(
        db: Session,
        *,
        department_id: int,
        period_year: int,
        period_month: int,
        team: Optional[str] = None,
    ) -> dict:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise ValueError("Department not found")

        employees = db.query(Employee).filter(Employee.department_id == department_id).all()
        employees = NLPService._filter_employees_by_team(employees, team)
        employee_ids = [employee.id for employee in employees]

        motivation_trend = []
        safety_trend = []

        for week in range(1, 5):
            week_profiles = [
                NLPService.get_or_build_employee_profile(
                    db,
                    employee_id=employee_id,
                    period_type=NLPPeriodType.weekly,
                    period_year=period_year,
                    period_month=period_month,
                    period_week=week,
                )
                for employee_id in employee_ids
            ]
            active_profiles = [profile for profile in week_profiles if profile.feedback_count > 0]

            def avg(field_name: str) -> float:
                values = [getattr(profile, field_name) for profile in active_profiles if getattr(profile, field_name) is not None]
                if not values:
                    return 0.0
                return round(sum(values) / len(values), 2)

            motivation_trend.append({"label": f"Hafta {week}", "value": avg("avg_motivation_score")})
            safety_trend.append({"label": f"Hafta {week}", "value": avg("avg_psychological_safety_score")})

        week_profiles_by_week: dict[int, list[EmployeeNLPProfile]] = {}
        for week in range(1, 5):
            week_profiles_by_week[week] = [
                NLPService.get_or_build_employee_profile(
                    db,
                    employee_id=employee_id,
                    period_type=NLPPeriodType.weekly,
                    period_year=period_year,
                    period_month=period_month,
                    period_week=week,
                )
                for employee_id in employee_ids
            ]

        active_week = 4
        for week in range(4, 0, -1):
            if any(profile.feedback_count > 0 for profile in week_profiles_by_week[week]):
                active_week = week
                break

        current_profiles = [profile for profile in week_profiles_by_week[active_week] if profile.feedback_count > 0]

        def count_risk(field_name: str, level: RiskLevel) -> int:
            return sum(1 for profile in current_profiles if getattr(profile, field_name) == level)

        risk_analyses = db.query(FeedbackNLPAnalysis).filter(
            FeedbackNLPAnalysis.department_id == department_id,
        ).all()
        risk_analyses = [
            analysis for analysis in risk_analyses
            if analysis.created_at.year == period_year and analysis.created_at.month == period_month
            and analysis.employee_id in employee_ids
        ]
        risk_counter = Counter()
        for analysis in risk_analyses:
            for item in analysis.risk_flags or []:
                normalized = item.strip()
                if normalized:
                    risk_counter[normalized] += 1

        return {
            "department_id": department.id,
            "department_name": department.name,
            "period_year": period_year,
            "period_month": period_month,
            "motivation_trend": motivation_trend,
            "psychological_safety_trend": safety_trend,
            "flight_risk_distribution": [
                {"label": "Dusuk", "value": count_risk("flight_risk_level", RiskLevel.low)},
                {"label": "Orta", "value": count_risk("flight_risk_level", RiskLevel.medium)},
                {"label": "Yuksek", "value": count_risk("flight_risk_level", RiskLevel.high)},
            ],
            "burnout_risk_distribution": [
                {"label": "Dusuk", "value": count_risk("burnout_risk_level", RiskLevel.low)},
                {"label": "Orta", "value": count_risk("burnout_risk_level", RiskLevel.medium)},
                {"label": "Yuksek", "value": count_risk("burnout_risk_level", RiskLevel.high)},
            ],
            "top_risk_themes": [
                {"label": label, "value": count}
                for label, count in risk_counter.most_common(5)
            ],
        }

    @staticmethod
    def build_employee_monthly_deep_analysis(
        db: Session,
        *,
        employee_id: int,
        period_year: int,
        period_month: int,
    ) -> dict:
        employee = db.query(Employee).join(Employee.user).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError("Employee not found")

        analyses = db.query(FeedbackNLPAnalysis).filter(
            FeedbackNLPAnalysis.employee_id == employee_id,
        ).all()
        analyses = [
            item for item in analyses
            if item.created_at.year == period_year and item.created_at.month == period_month
        ]
        analyses.sort(key=lambda item: item.created_at)
        trusted_analyses = NLPService._trusted_analyses(analyses)

        motivation_trend = NLPService._weekly_average_series(trusted_analyses, "motivation_score")
        sentiment_trend = NLPService._weekly_average_series(trusted_analyses, "sentiment_score")
        top_complaints = NLPService._dominant_items(
            NLPService._raw_list_item(item, "complaint_topics") for item in trusted_analyses
        )
        distinctive_complaints = NLPService._distinctive_feedback_phrases(
            trusted_analyses,
            kind="negative",
            limit=3,
        )
        top_complaints = list(dict.fromkeys(distinctive_complaints + top_complaints))[:5]
        raw_complaints = NLPService._raw_dominant_items(
            trusted_analyses,
            ["complaint_topics", "flight_risk_reasons"],
            limit=4,
        )
        top_complaints = list(dict.fromkeys(raw_complaints + top_complaints))[:5]
        top_praises = NLPService._dominant_items(
            NLPService._raw_list_item(item, "praise_topics") + list(item.key_strengths or [])
            for item in trusted_analyses
        )
        distinctive_praises = NLPService._distinctive_feedback_phrases(
            trusted_analyses,
            kind="positive",
            limit=3,
        )
        top_praises = list(dict.fromkeys(distinctive_praises + top_praises))[:5]
        top_praises = NLPService._filter_generic_items(
            top_praises,
            {"psikolojik guven", "sorumluluk alma", "is birligi", "gelisime aciklik", "liderlik destegi"},
            limit=5,
        )
        raw_praises = NLPService._raw_dominant_items(
            trusted_analyses,
            ["praise_topics", "key_strengths"],
            limit=4,
        )
        top_praises = NLPService._filter_generic_items(
            list(dict.fromkeys(raw_praises + top_praises)),
            {"psikolojik guven", "sorumluluk alma", "is birligi", "gelisime aciklik", "liderlik destegi"},
            limit=5,
        )
        top_themes = NLPService._dominant_items(
            ((
                NLPService._raw_list_item(item, "theme_labels")
                + NLPService._raw_list_item(item, "entity_mentions")
            )
            for item in trusted_analyses),
            limit=5,
        )
        distinctive_themes = NLPService._distinctive_feedback_phrases(
            trusted_analyses,
            kind="theme",
            limit=4,
        )
        top_themes = list(dict.fromkeys(distinctive_themes + top_themes))[:6]
        raw_themes = NLPService._raw_dominant_items(
            trusted_analyses,
            ["theme_labels", "entity_mentions"],
            limit=5,
        )
        top_themes = list(dict.fromkeys(raw_themes + top_themes))[:8]
        top_themes = NLPService._filter_topic_items(top_themes, employee, limit=6)
        avg_flight_score = NLPService._weighted_numeric_average(
            (
                NLPService._extract_float(item.raw_analysis or {}, "flight_risk_score") if isinstance(item.raw_analysis, dict) else None,
                0.35 if NLPService._quality_signal(item).get("is_low_quality") else 1.0,
            )
            for item in analyses
        )
        action_recommendation = next(
            (
                (item.raw_analysis or {}).get("action_recommendation")
                for item in reversed(trusted_analyses)
                if isinstance(item.raw_analysis, dict) and (item.raw_analysis or {}).get("action_recommendation")
            ),
            None,
        )
        safety_trend = NLPService._weekly_average_series(trusted_analyses, "psychological_safety_score")
        burnout_drivers, burnout_evidence, burnout_risk_level = NLPService._burnout_risk_drivers(
            trusted_analyses,
            motivation_trend=motivation_trend,
            safety_trend=safety_trend,
            top_complaints=top_complaints,
        )

        return {
            "employee_id": employee.id,
            "employee_name": employee.user.full_name,
            "period_year": period_year,
            "period_month": period_month,
            "feedback_count": len(analyses),
            "motivation_trend_direction": NLPService._trend_direction(motivation_trend),
            "sentiment_trend_direction": NLPService._trend_direction(sentiment_trend),
            "top_complaint_topics": top_complaints,
            "top_praise_topics": top_praises,
            "top_themes": top_themes,
            "flight_risk_score": avg_flight_score,
            "flight_risk_reasons": NLPService._dominant_items(
                NLPService._raw_list_item(item, "flight_risk_reasons") for item in trusted_analyses
            ),
            "burnout_risk_level": burnout_risk_level,
            "burnout_risk_drivers": burnout_drivers,
            "burnout_risk_evidence": burnout_evidence,
            "action_recommendation": action_recommendation,
        }

    @staticmethod
    def build_department_monthly_deep_analysis(
        db: Session,
        *,
        department_id: int,
        period_year: int,
        period_month: int,
        team: Optional[str] = None,
    ) -> dict:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise ValueError("Department not found")

        team_employee_ids = {
            employee.id
            for employee in NLPService._filter_employees_by_team(
                db.query(Employee).filter(Employee.department_id == department_id).all(),
                team,
            )
        }
        analyses = db.query(FeedbackNLPAnalysis).filter(
            FeedbackNLPAnalysis.department_id == department_id,
        ).all()
        analyses = [
            item for item in analyses
            if item.created_at.year == period_year and item.created_at.month == period_month
            and (not team_employee_ids or item.employee_id in team_employee_ids)
        ]
        analyses.sort(key=lambda item: item.created_at)
        trusted_analyses = NLPService._trusted_analyses(analyses)

        motivation_trend = NLPService._weekly_average_series(trusted_analyses, "motivation_score")
        sentiment_trend = NLPService._weekly_average_series(trusted_analyses, "sentiment_score")
        top_complaints = NLPService._dominant_items(
            NLPService._raw_list_item(item, "complaint_topics") for item in trusted_analyses
        )
        distinctive_complaints = NLPService._distinctive_feedback_phrases(
            trusted_analyses,
            kind="negative",
            limit=4,
        )
        top_complaints = list(dict.fromkeys(distinctive_complaints + top_complaints))[:6]
        top_praises = NLPService._dominant_items(
            NLPService._raw_list_item(item, "praise_topics") + list(item.key_strengths or [])
            for item in trusted_analyses
        )
        distinctive_praises = NLPService._distinctive_feedback_phrases(
            trusted_analyses,
            kind="positive",
            limit=4,
        )
        top_praises = list(dict.fromkeys(distinctive_praises + top_praises))[:6]
        top_praises = NLPService._filter_generic_items(
            top_praises,
            {"psikolojik guven", "sorumluluk alma", "is birligi", "gelisime aciklik", "liderlik destegi"},
            limit=6,
        )
        top_themes = NLPService._dominant_items(
            ((
                NLPService._raw_list_item(item, "theme_labels")
                + NLPService._raw_list_item(item, "entity_mentions")
            )
            for item in trusted_analyses),
            limit=6,
        )
        distinctive_themes = NLPService._distinctive_feedback_phrases(
            trusted_analyses,
            kind="theme",
            limit=5,
        )
        top_themes = list(dict.fromkeys(distinctive_themes + top_themes))[:7]
        top_flight_risk_reasons = NLPService._dominant_items(
            NLPService._raw_list_item(item, "flight_risk_reasons") for item in trusted_analyses
        )

        avg_flight_risk_score = NLPService._weighted_numeric_average(
            (
                NLPService._extract_float(analysis.raw_analysis or {}, "flight_risk_score") if isinstance(analysis.raw_analysis, dict) else None,
                0.35 if NLPService._quality_signal(analysis).get("is_low_quality") else 1.0,
            )
            for analysis in analyses
        )
        action_recommendation = next(
            (
                (item.raw_analysis or {}).get("action_recommendation")
                for item in reversed(trusted_analyses)
                if isinstance(item.raw_analysis, dict) and (item.raw_analysis or {}).get("action_recommendation")
            ),
            None,
        )

        analyzed_employee_count = len({item.employee_id for item in analyses})

        return {
            "department_id": department.id,
            "department_name": department.name,
            "period_year": period_year,
            "period_month": period_month,
            "analyzed_feedback_count": len(analyses),
            "analyzed_employee_count": analyzed_employee_count,
            "motivation_trend_direction": NLPService._trend_direction(motivation_trend),
            "sentiment_trend_direction": NLPService._trend_direction(sentiment_trend),
            "avg_flight_risk_score": avg_flight_risk_score,
            "top_complaint_topics": top_complaints,
            "top_praise_topics": top_praises,
            "top_themes": top_themes,
            "top_flight_risk_reasons": top_flight_risk_reasons,
            "action_recommendation": action_recommendation,
        }

    @staticmethod
    def build_employee_monthly_rag_report(
        db: Session,
        *,
        employee_id: int,
        period_year: int,
        period_month: int,
    ) -> dict:
        employee = db.query(Employee).join(Employee.user).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError("Employee not found")

        deep_analysis = NLPService.build_employee_monthly_deep_analysis(
            db,
            employee_id=employee_id,
            period_year=period_year,
            period_month=period_month,
        )
        analyses = db.query(FeedbackNLPAnalysis).filter(
            FeedbackNLPAnalysis.employee_id == employee_id,
        ).all()
        analyses = [
            item for item in analyses
            if item.created_at.year == period_year and item.created_at.month == period_month
        ]
        quality_context = NLPService._rag_quality_context(analyses)
        deep_analysis["quality_context"] = quality_context

        query_terms = (
            deep_analysis.get("top_themes")
            or deep_analysis.get("top_complaint_topics")
            or quality_context.get("bias_topics")
            or ["genel durum"]
        )
        query_text = " ".join(query_terms)
        retrieved_memories = RAGService.retrieve_similar_memories(
            db,
            query_text=query_text,
            employee_id=employee_id,
            limit=5,
        )
        if not retrieved_memories:
            retrieved_memories = RAGService.retrieve_similar_memories(
                db,
                query_text=query_text,
                employee_id=employee_id,
                limit=5,
                min_score=0.0,
            )

        if not retrieved_memories:
            top_complaints = deep_analysis.get("top_complaint_topics") or []
            top_praises = deep_analysis.get("top_praise_topics") or []
            key_takeaways = deep_analysis.get("top_themes") or []
            risk_score = deep_analysis.get("flight_risk_score")
            if risk_score is None:
                retention_level = "unknown"
            elif risk_score >= 7:
                retention_level = "high"
            elif risk_score >= 4:
                retention_level = "medium"
            else:
                retention_level = "low"

            if deep_analysis.get("feedback_count", 0) <= 1:
                report_summary = (
                    f"{employee.user.full_name} icin bu ay kisiyi ayirt edecek kadar zengin 360 NLP hafizasi olusmadi. "
                    "Ekrandaki sinyaller yalnizca mevcut tekil feedback analizinden uretilmistir."
                )
                trend_summary = (
                    "Benzer gecmis kayit bulunmadigi icin RAG karsilastirmasi yapilmadi; trend yorumu sinirli guvenle okunmalidir."
                )
            else:
                report_summary = (
                    f"{employee.user.full_name} icin bu ay RAG belleğinde benzer kayit bulunmadi; "
                    "ozet mevcut 360 NLP analizlerinin toplu sinyallerinden olusturuldu."
                )
                trend_summary = (
                    f"Motivasyon trendi {deep_analysis.get('motivation_trend_direction')}, "
                    f"duygu trendi {deep_analysis.get('sentiment_trend_direction')} gorunuyor."
                )

            return {
                "employee_id": employee.id,
                "employee_name": employee.user.full_name,
                "department_id": employee.department_id,
                "department_name": employee.department.name if employee.department else None,
                "team": employee.team,
                "period_year": period_year,
                "period_month": period_month,
                "report_summary": report_summary,
                "trend_summary": trend_summary,
                "flight_risk_score": risk_score,
                "retention_risk_level": retention_level,
                "top_complaint_topics": top_complaints,
                "top_praise_topics": top_praises,
                "key_takeaways": key_takeaways,
                "action_recommendation": deep_analysis.get("action_recommendation") or "Daha guvenilir analiz icin bu calisan hakkinda ek 360 feedback toplayin.",
                "retrieved_memory_count": 0,
                "retrieved_memory_summaries": [],
                "model_provider": "deterministic",
                "model_name": "no-rag-memory-v1",
                "confidence": 0.35 if deep_analysis.get("feedback_count", 0) <= 1 else 0.55,
            }

        if any(item.model_provider == "synthetic_seed_360_history" for item in analyses):
            rag_payload = AIService._fallback_monthly_rag_report(
                subject_label=employee.user.full_name,
                deep_analysis=deep_analysis,
                retrieved_memories=retrieved_memories,
            )
            return {
                "employee_id": employee.id,
                "employee_name": employee.user.full_name,
                "department_id": employee.department_id,
                "department_name": employee.department.name if employee.department else None,
                "team": employee.team,
                "period_year": period_year,
                "period_month": period_month,
                "report_summary": rag_payload.get("report_summary"),
                "trend_summary": rag_payload.get("trend_summary"),
                "flight_risk_score": rag_payload.get("flight_risk_score"),
                "retention_risk_level": rag_payload.get("retention_risk_level"),
                "top_complaint_topics": rag_payload.get("top_complaint_topics") or deep_analysis.get("top_complaint_topics") or [],
                "top_praise_topics": rag_payload.get("top_praise_topics") or deep_analysis.get("top_praise_topics") or [],
                "key_takeaways": rag_payload.get("key_takeaways") or deep_analysis.get("top_themes") or [],
                "action_recommendation": rag_payload.get("action_recommendation") or deep_analysis.get("action_recommendation"),
                "retrieved_memory_count": len(retrieved_memories),
                "retrieved_memory_summaries": [
                    item.get("content_summary") or item.get("content_text", "")[:180]
                    for item in retrieved_memories
                ],
                "model_provider": "heuristic",
                "model_name": "synthetic-history-rag-fallback-v1",
                "confidence": rag_payload.get("confidence"),
            }

        rag_payload, provider, model_name = AIService.analyze_monthly_rag_report(
            subject_label=employee.user.full_name,
            dept_name=employee.department.name if employee.department else "Genel",
            period_label=f"{period_month}/{period_year}",
            deep_analysis=deep_analysis,
            retrieved_memories=retrieved_memories,
        )

        return {
            "employee_id": employee.id,
            "employee_name": employee.user.full_name,
            "department_id": employee.department_id,
            "department_name": employee.department.name if employee.department else None,
            "team": employee.team,
            "period_year": period_year,
            "period_month": period_month,
            "report_summary": rag_payload.get("report_summary"),
            "trend_summary": rag_payload.get("trend_summary"),
            "flight_risk_score": rag_payload.get("flight_risk_score"),
            "retention_risk_level": rag_payload.get("retention_risk_level"),
            "top_complaint_topics": rag_payload.get("top_complaint_topics") or deep_analysis.get("top_complaint_topics") or [],
            "top_praise_topics": rag_payload.get("top_praise_topics") or deep_analysis.get("top_praise_topics") or [],
            "key_takeaways": rag_payload.get("key_takeaways") or deep_analysis.get("top_themes") or [],
            "action_recommendation": rag_payload.get("action_recommendation") or deep_analysis.get("action_recommendation"),
            "retrieved_memory_count": len(retrieved_memories),
            "retrieved_memory_summaries": [
                item.get("content_summary") or item.get("content_text", "")[:180]
                for item in retrieved_memories
            ],
            "model_provider": provider,
            "model_name": model_name,
            "confidence": rag_payload.get("confidence"),
        }

    @staticmethod
    def build_department_monthly_rag_report(
        db: Session,
        *,
        department_id: int,
        period_year: int,
        period_month: int,
        team: Optional[str] = None,
    ) -> dict:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise ValueError("Department not found")

        deep_analysis = NLPService.build_department_monthly_deep_analysis(
            db,
            department_id=department_id,
            period_year=period_year,
            period_month=period_month,
            team=team,
        )
        team_employee_ids = {
            employee.id
            for employee in NLPService._filter_employees_by_team(
                db.query(Employee).filter(Employee.department_id == department_id).all(),
                team,
            )
        }
        analyses = db.query(FeedbackNLPAnalysis).filter(
            FeedbackNLPAnalysis.department_id == department_id,
        ).all()
        analyses = [
            item for item in analyses
            if item.created_at.year == period_year and item.created_at.month == period_month
            and (not team_employee_ids or item.employee_id in team_employee_ids)
        ]
        quality_context = NLPService._rag_quality_context(analyses)
        deep_analysis["quality_context"] = quality_context

        query_terms = (
            deep_analysis.get("top_themes")
            or deep_analysis.get("top_complaint_topics")
            or quality_context.get("bias_topics")
            or ["genel durum"]
        )
        query_text = " ".join(query_terms)
        retrieved_memories = RAGService.retrieve_similar_memories(
            db,
            query_text=query_text,
            department_id=department_id,
            limit=7,
        )

        rag_payload, provider, model_name = AIService.analyze_monthly_rag_report(
            subject_label=f"{department.name} Departmani",
            dept_name=department.name,
            period_label=f"{period_month}/{period_year}",
            deep_analysis=deep_analysis,
            retrieved_memories=retrieved_memories,
        )

        return {
            "department_id": department.id,
            "department_name": department.name,
            "period_year": period_year,
            "period_month": period_month,
            "report_summary": rag_payload.get("report_summary"),
            "trend_summary": rag_payload.get("trend_summary"),
            "flight_risk_score": rag_payload.get("flight_risk_score"),
            "retention_risk_level": rag_payload.get("retention_risk_level"),
            "top_complaint_topics": rag_payload.get("top_complaint_topics") or deep_analysis.get("top_complaint_topics") or [],
            "top_praise_topics": rag_payload.get("top_praise_topics") or deep_analysis.get("top_praise_topics") or [],
            "key_takeaways": rag_payload.get("key_takeaways") or deep_analysis.get("top_themes") or [],
            "action_recommendation": rag_payload.get("action_recommendation") or deep_analysis.get("action_recommendation"),
            "retrieved_memory_count": len(retrieved_memories),
            "retrieved_memory_summaries": [
                item.get("content_summary") or item.get("content_text", "")[:180]
                for item in retrieved_memories
            ],
            "model_provider": provider,
            "model_name": model_name,
            "confidence": rag_payload.get("confidence"),
        }
