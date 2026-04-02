from __future__ import annotations

import hashlib
import math
import re
from typing import Any, Optional

import requests
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.feedback import Feedback, FeedbackResponse
from app.db.models.rag import FeedbackMemoryChunk, FeedbackMemorySourceType


class RAGService:
    @staticmethod
    def _vector_literal(vector: list[float]) -> str:
        return "[" + ",".join(f"{float(value):.6f}" for value in vector) + "]"

    @staticmethod
    def _pgvector_available(db: Session, dimension: int) -> bool:
        if not settings.ENABLE_PGVECTOR:
            return False
        if db.bind is None or db.bind.dialect.name != "postgresql":
            return False

        try:
            extension_ready = db.execute(
                sql_text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_extension
                        WHERE extname = 'vector'
                    )
                    """
                )
            ).scalar()
            if not extension_ready:
                return False

            column_ready = db.execute(
                sql_text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'feedback_memory_chunks'
                          AND column_name = 'embedding_vector_pg'
                    )
                    """
                )
            ).scalar()
            if not column_ready:
                return False

            return bool(dimension >= 32)
        except Exception:
            return False

    @staticmethod
    def _sync_pgvector_column(db: Session, memory_id: int, vector: list[float], dimension: int) -> None:
        if not RAGService._pgvector_available(db, dimension):
            return

        try:
            db.execute(
                sql_text(
                    """
                    UPDATE feedback_memory_chunks
                    SET embedding_vector_pg = CAST(:vector_literal AS vector)
                    WHERE id = :memory_id
                    """
                ),
                {
                    "memory_id": memory_id,
                    "vector_literal": RAGService._vector_literal(vector),
                },
            )
            db.flush()
        except Exception:
            # JSON embedding fallback remains the source of truth.
            pass

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
    def _tokenize(text: str) -> list[str]:
        normalized = RAGService._normalize_text(text).lower()
        return [token for token in re.findall(r"[a-z0-9_]+", normalized) if len(token) > 2]

    @staticmethod
    def _hash_embedding(text: str, dimension: int) -> list[float]:
        vector = [0.0] * dimension
        tokens = RAGService._tokenize(text)
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            weight = 1.0 + (digest[5] / 255.0)
            vector[index] += sign * weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [round(value / norm, 6) for value in vector]

    @staticmethod
    def _generate_with_gemini_embedding(text: str) -> Optional[tuple[list[float], str, str]]:
        if not settings.GEMINI_API_KEY:
            return None

        try:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{settings.GEMINI_EMBEDDING_MODEL}:embedContent?key={settings.GEMINI_API_KEY}"
            )
            body = {
                "content": {
                    "parts": [{"text": text}],
                }
            }
            res = requests.post(url, json=body, timeout=20)
            if not res.ok:
                return None
            values = res.json().get("embedding", {}).get("values", [])
            if not values:
                return None
            vector = [round(float(item), 6) for item in values]
            return vector, "gemini", settings.GEMINI_EMBEDDING_MODEL
        except Exception:
            return None

    @staticmethod
    def generate_embedding(text: str) -> tuple[list[float], str, str, int]:
        provider = (settings.EMBEDDING_PROVIDER or "hash").lower().strip()
        if provider == "gemini":
            gemini_result = RAGService._generate_with_gemini_embedding(text)
            if gemini_result:
                vector, model_provider, model_name = gemini_result
                return vector, model_provider, model_name, len(vector)

        dimension = max(int(settings.EMBEDDING_DIMENSION or 128), 32)
        vector = RAGService._hash_embedding(text, dimension)
        return vector, "hash", "hash-v1", dimension

    @staticmethod
    def _compose_memory_text(
        question_text: str,
        response_text: str,
        analysis_payload: dict[str, Any] | None,
    ) -> tuple[str, Optional[str], list[str], dict[str, Any]]:
        analysis_payload = analysis_payload or {}
        summary = analysis_payload.get("manager_summary")
        themes = analysis_payload.get("theme_labels") or []
        content_text = (
            f"Soru: {RAGService._normalize_text(question_text)}\n"
            f"Cevap: {RAGService._normalize_text(response_text)}"
        )
        metadata = {
            "theme_labels": themes,
            "complaint_topics": analysis_payload.get("complaint_topics") or [],
            "praise_topics": analysis_payload.get("praise_topics") or [],
            "flight_risk_score": analysis_payload.get("flight_risk_score"),
            "flight_risk_reasons": analysis_payload.get("flight_risk_reasons") or [],
            "dominant_emotions": analysis_payload.get("dominant_emotions") or [],
            "action_recommendation": analysis_payload.get("action_recommendation"),
        }
        return content_text, summary, themes, metadata

    @staticmethod
    def upsert_weekly_feedback_memory(
        db: Session,
        *,
        feedback_response: FeedbackResponse,
        analysis_payload: dict[str, Any] | None,
    ) -> FeedbackMemoryChunk:
        question_text = feedback_response.question.question_text if feedback_response.question else ""
        content_text, content_summary, theme_labels, metadata = RAGService._compose_memory_text(
            question_text=question_text,
            response_text=feedback_response.response_text,
            analysis_payload=analysis_payload,
        )
        vector, provider, model_name, dimension = RAGService.generate_embedding(content_text)

        existing = db.query(FeedbackMemoryChunk).filter(
            FeedbackMemoryChunk.weekly_feedback_id == feedback_response.id
        ).first()

        payload = {
            "source_type": FeedbackMemorySourceType.weekly_feedback,
            "weekly_feedback_id": feedback_response.id,
            "employee_id": feedback_response.receiver_id,
            "reviewer_employee_id": feedback_response.sender_id,
            "department_id": feedback_response.receiver.department_id if feedback_response.receiver else None,
            "content_text": content_text,
            "content_summary": content_summary,
            "theme_labels": theme_labels,
            "metadata_json": metadata,
            "embedding_provider": provider,
            "embedding_model": model_name,
            "embedding_dimension": dimension,
            "embedding_vector": vector,
        }

        if existing:
            for field, value in payload.items():
                setattr(existing, field, value)
            record = existing
        else:
            record = FeedbackMemoryChunk(**payload)
            db.add(record)

        db.flush()
        RAGService._sync_pgvector_column(db, record.id, vector, dimension)
        return record

    @staticmethod
    def upsert_classic_feedback_memory(
        db: Session,
        *,
        feedback: Feedback,
        analysis_payload: dict[str, Any] | None,
    ) -> FeedbackMemoryChunk:
        response_text = " ".join(
            [
                feedback.strength_text or "",
                feedback.improvement_text or "",
                feedback.general_comment or "",
            ]
        ).strip()
        content_text, content_summary, theme_labels, metadata = RAGService._compose_memory_text(
            question_text="Klasik 360 feedback yorumu",
            response_text=response_text,
            analysis_payload=analysis_payload,
        )
        vector, provider, model_name, dimension = RAGService.generate_embedding(content_text)

        existing = db.query(FeedbackMemoryChunk).filter(
            FeedbackMemoryChunk.classic_feedback_id == feedback.id
        ).first()

        payload = {
            "source_type": FeedbackMemorySourceType.classic_feedback,
            "classic_feedback_id": feedback.id,
            "employee_id": feedback.reviewee_id,
            "reviewer_employee_id": feedback.reviewer_id,
            "department_id": feedback.reviewee.department_id if feedback.reviewee else None,
            "content_text": content_text,
            "content_summary": content_summary,
            "theme_labels": theme_labels,
            "metadata_json": metadata,
            "embedding_provider": provider,
            "embedding_model": model_name,
            "embedding_dimension": dimension,
            "embedding_vector": vector,
        }

        if existing:
            for field, value in payload.items():
                setattr(existing, field, value)
            record = existing
        else:
            record = FeedbackMemoryChunk(**payload)
            db.add(record)

        db.flush()
        RAGService._sync_pgvector_column(db, record.id, vector, dimension)
        return record

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return round(numerator / (left_norm * right_norm), 4)

    @staticmethod
    def retrieve_similar_memories(
        db: Session,
        *,
        query_text: str,
        employee_id: int | None = None,
        department_id: int | None = None,
        limit: int = 5,
        min_score: float = 0.18,
    ) -> list[dict[str, Any]]:
        query_vector, _, _, dimension = RAGService.generate_embedding(query_text)
        if RAGService._pgvector_available(db, dimension):
            pgvector_matches = RAGService._retrieve_similar_memories_pgvector(
                db,
                query_vector=query_vector,
                employee_id=employee_id,
                department_id=department_id,
                limit=limit,
                min_score=min_score,
                dimension=dimension,
            )
            if pgvector_matches:
                return pgvector_matches

        memories_query = db.query(FeedbackMemoryChunk).filter(
            FeedbackMemoryChunk.embedding_dimension == dimension
        )
        if employee_id is not None:
            memories_query = memories_query.filter(FeedbackMemoryChunk.employee_id == employee_id)
        if department_id is not None:
            memories_query = memories_query.filter(FeedbackMemoryChunk.department_id == department_id)

        matches = []
        for item in memories_query.all():
            vector = item.embedding_vector or []
            if not isinstance(vector, list):
                continue
            try:
                candidate_vector = [float(value) for value in vector]
            except (TypeError, ValueError):
                continue
            score = RAGService._cosine_similarity(query_vector, candidate_vector)
            if score < min_score:
                continue
            matches.append(
                {
                    "memory_id": item.id,
                    "score": score,
                    "content_text": item.content_text,
                    "content_summary": item.content_summary,
                    "theme_labels": item.theme_labels or [],
                    "metadata": item.metadata_json or {},
                    "employee_id": item.employee_id,
                    "department_id": item.department_id,
                }
            )

        matches.sort(key=lambda item: item["score"], reverse=True)
        return matches[:limit]

    @staticmethod
    def backfill_pgvector_embeddings(db: Session, *, limit: int = 500) -> int:
        dimension = max(int(settings.EMBEDDING_DIMENSION or 128), 32)
        if not RAGService._pgvector_available(db, dimension):
            return 0

        records = db.query(FeedbackMemoryChunk).filter(
            FeedbackMemoryChunk.embedding_dimension == dimension
        ).all()

        updated = 0
        for record in records[: max(limit, 1)]:
            vector = record.embedding_vector or []
            if not isinstance(vector, list) or not vector:
                continue
            try:
                numeric_vector = [float(value) for value in vector]
            except (TypeError, ValueError):
                continue

            RAGService._sync_pgvector_column(db, record.id, numeric_vector, dimension)
            updated += 1

        db.commit()
        return updated

    @staticmethod
    def _retrieve_similar_memories_pgvector(
        db: Session,
        *,
        query_vector: list[float],
        employee_id: int | None,
        department_id: int | None,
        limit: int,
        min_score: float,
        dimension: int,
    ) -> list[dict[str, Any]]:
        conditions = [
            "embedding_dimension = :dimension",
            "embedding_vector_pg IS NOT NULL",
        ]
        params: dict[str, Any] = {
            "dimension": dimension,
            "limit": limit,
            "query_vector": RAGService._vector_literal(query_vector),
        }
        if employee_id is not None:
            conditions.append("employee_id = :employee_id")
            params["employee_id"] = employee_id
        if department_id is not None:
            conditions.append("department_id = :department_id")
            params["department_id"] = department_id

        query = f"""
            SELECT
                id,
                content_text,
                content_summary,
                theme_labels,
                metadata_json,
                employee_id,
                department_id,
                1 - (embedding_vector_pg <=> CAST(:query_vector AS vector)) AS score
            FROM feedback_memory_chunks
            WHERE {' AND '.join(conditions)}
            ORDER BY embedding_vector_pg <=> CAST(:query_vector AS vector)
            LIMIT :limit
        """

        try:
            rows = db.execute(sql_text(query), params).mappings().all()
        except Exception:
            return []

        matches = []
        for row in rows:
            score = round(float(row.get("score") or 0.0), 4)
            if score < min_score:
                continue
            matches.append(
                {
                    "memory_id": row["id"],
                    "score": score,
                    "content_text": row["content_text"],
                    "content_summary": row["content_summary"],
                    "theme_labels": row["theme_labels"] or [],
                    "metadata": row["metadata_json"] or {},
                    "employee_id": row["employee_id"],
                    "department_id": row["department_id"],
                }
            )
        return matches
