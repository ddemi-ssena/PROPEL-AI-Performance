from __future__ import annotations

from collections import Counter
from datetime import datetime
from math import ceil
from typing import Any, Dict, Iterable, Optional

from sqlalchemy.orm import Session

from app.db.models.department import Department
from app.db.models.employee import Employee
from app.db.models.feedback import Feedback, FeedbackResponse, EmployeeBadge, BadgeType, BadgeLevel
from app.db.models.nlp import (
    EmployeeNLPProfile,
    FeedbackNLPAnalysis,
    NLPPeriodType,
    NLPSourceType,
    RiskLevel,
    SentimentLabel,
)
from app.schemas.nlp import FeedbackNLPAnalysisCreate
from app.services.ai_service import AIService
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

        if positive_steps and negative_steps:
            return "stabil"

        if delta > 0.35 and average_delta > 0.18:
            return "yukselis"
        if delta < -0.35 and average_delta < -0.18:
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

        raw = analysis.raw_analysis or {}
        if isinstance(raw, dict):
            for key in [
                "praise_topics",
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
    def get_department_weekly_summary(
        db: Session,
        *,
        department_id: int,
        period_year: int,
        period_month: int,
        period_week: int,
    ) -> dict:
        employees = db.query(Employee).filter(Employee.department_id == department_id).all()
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
            headline = "Departmanda dikkat isteyen risk sinyalleri var."
        elif active_profiles:
            headline = "Departmanin haftalik duygu ve risk gorunumu dengeli."
        else:
            headline = "Bu hafta departman icin yeterli NLP verisi olusmadi."

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
        recent_analyses = NLPService.get_recent_weekly_analyses(db, employee_id=employee_id, limit=8)

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
                "description": "Aidiyet ve kopma sinyallerinin seviye ozeti",
            },
            {
                "label": "Burnout Risk",
                "value": None,
                "display_value": (profile.burnout_risk_level.value if profile.burnout_risk_level else "unknown").upper(),
                "risk_level": profile.burnout_risk_level.value if profile.burnout_risk_level else None,
                "description": "Yorgunluk ve tukennislik sinyallerinin seviye ozeti",
            },
        ]

        summary_parts = []
        if profile.avg_motivation_score is not None:
            summary_parts.append(f"motivasyon skoru {profile.avg_motivation_score:.1f}/5")
        if profile.flight_risk_level:
            summary_parts.append(f"flight risk seviyesi {profile.flight_risk_level.value}")
        if profile.top_support_needs:
            summary_parts.append(f"en belirgin destek ihtiyaci {profile.top_support_needs[0]}")
        if low_quality_count:
            summary_parts.append(f"veri kalitesi uyarisi {low_quality_count} kayitta goruldu")
        if bias_count:
            summary_parts.append(f"karsilikli bias supheleri {bias_count} kayitta izlendi")

        summary = profile.manager_summary or (
            f"Bu haftaki 360 feedback ozetine gore {employee.user.full_name} icin "
            + ", ".join(summary_parts)
            + "."
            if summary_parts
            else f"Bu hafta {employee.user.full_name} icin anlamli bir 360 feedback sinyali henuz olusmadi."
        )

        sections = [
            {"title": "Guclu Yonler", "items": profile.top_strengths or []},
            {"title": "Risk Alanlari", "items": profile.top_risk_areas or []},
            {"title": "Destek Ihtiyaclari", "items": profile.top_support_needs or []},
        ]
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

        return {
            "employee_id": employee.id,
            "employee_name": employee.user.full_name,
            "department_id": employee.department_id,
            "department_name": employee.department.name if employee.department else None,
            "position": employee.position,
            "period_year": period_year,
            "period_month": period_month,
            "period_week": period_week,
            "report_title": "Kisisel 360 Feedback Summary",
            "report_summary": summary,
            "recommended_action": profile.recommended_action,
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
        )
        analyses = db.query(FeedbackNLPAnalysis).filter(
            FeedbackNLPAnalysis.department_id == department_id,
            FeedbackNLPAnalysis.source_type == NLPSourceType.weekly_feedback,
        ).all()
        analyses = [
            item for item in analyses
            if item.created_at.year == period_year
            and item.created_at.month == period_month
            and NLPService._week_of_month_from_datetime(item.created_at) == period_week
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

        summary = (
            f"{department.name} departmani icin haftalik 360 feedback raporu: "
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
    ) -> dict:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise ValueError("Department not found")

        employees = db.query(Employee).filter(Employee.department_id == department_id).all()
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
            FeedbackNLPAnalysis.source_type == NLPSourceType.weekly_feedback,
        ).all()
        risk_analyses = [
            analysis for analysis in risk_analyses
            if analysis.created_at.year == period_year and analysis.created_at.month == period_month
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
            FeedbackNLPAnalysis.source_type == NLPSourceType.weekly_feedback,
        ).all()
        analyses = [
            item for item in analyses
            if item.created_at.year == period_year and item.created_at.month == period_month
        ]
        analyses.sort(key=lambda item: item.created_at)
        trusted_analyses = NLPService._trusted_analyses(analyses)

        motivation_trend = [item.motivation_score for item in trusted_analyses]
        sentiment_trend = [item.sentiment_score for item in trusted_analyses]
        top_complaints = NLPService._dominant_items(
            NLPService._raw_list_item(item, "complaint_topics") for item in trusted_analyses
        )
        top_praises = NLPService._dominant_items(
            NLPService._raw_list_item(item, "praise_topics") + list(item.key_strengths or [])
            for item in trusted_analyses
        )
        top_themes = NLPService._dominant_items(
            ((
                NLPService._raw_list_item(item, "theme_labels")
                + NLPService._raw_list_item(item, "entity_mentions")
            )
            for item in trusted_analyses),
            limit=5,
        )
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
            "action_recommendation": action_recommendation,
        }

    @staticmethod
    def build_department_monthly_deep_analysis(
        db: Session,
        *,
        department_id: int,
        period_year: int,
        period_month: int,
    ) -> dict:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise ValueError("Department not found")

        analyses = db.query(FeedbackNLPAnalysis).filter(
            FeedbackNLPAnalysis.department_id == department_id,
            FeedbackNLPAnalysis.source_type == NLPSourceType.weekly_feedback,
        ).all()
        analyses = [
            item for item in analyses
            if item.created_at.year == period_year and item.created_at.month == period_month
        ]
        analyses.sort(key=lambda item: item.created_at)
        trusted_analyses = NLPService._trusted_analyses(analyses)

        motivation_trend = [item.motivation_score for item in trusted_analyses]
        sentiment_trend = [item.sentiment_score for item in trusted_analyses]
        top_complaints = NLPService._dominant_items(
            NLPService._raw_list_item(item, "complaint_topics") for item in trusted_analyses
        )
        top_praises = NLPService._dominant_items(
            NLPService._raw_list_item(item, "praise_topics") + list(item.key_strengths or [])
            for item in trusted_analyses
        )
        top_themes = NLPService._dominant_items(
            ((
                NLPService._raw_list_item(item, "theme_labels")
                + NLPService._raw_list_item(item, "entity_mentions")
            )
            for item in trusted_analyses),
            limit=6,
        )
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
            FeedbackNLPAnalysis.source_type == NLPSourceType.weekly_feedback,
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
    ) -> dict:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise ValueError("Department not found")

        deep_analysis = NLPService.build_department_monthly_deep_analysis(
            db,
            department_id=department_id,
            period_year=period_year,
            period_month=period_month,
        )
        analyses = db.query(FeedbackNLPAnalysis).filter(
            FeedbackNLPAnalysis.department_id == department_id,
            FeedbackNLPAnalysis.source_type == NLPSourceType.weekly_feedback,
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
