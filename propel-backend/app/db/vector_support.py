from sqlalchemy import text

from app.core.config import settings


def ensure_pgvector_support(engine) -> bool:
    """
    Enables pgvector when the database image supports it and safely adds
    a vector column/index without breaking existing JSON embedding fallback.
    """
    if not settings.ENABLE_PGVECTOR:
        return False

    if engine.dialect.name != "postgresql":
        return False

    dimension = max(int(settings.EMBEDDING_DIMENSION or 128), 32)

    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

            table_exists = conn.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_name = 'feedback_memory_chunks'
                    )
                    """
                )
            ).scalar()

            if not table_exists:
                return True

            column_exists = conn.execute(
                text(
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

            if not column_exists:
                conn.execute(
                    text(
                        f"""
                        ALTER TABLE feedback_memory_chunks
                        ADD COLUMN embedding_vector_pg vector({dimension})
                        """
                    )
                )

            conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS ix_feedback_memory_chunks_employee_id
                    ON feedback_memory_chunks (employee_id)
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS ix_feedback_memory_chunks_department_id
                    ON feedback_memory_chunks (department_id)
                    """
                )
            )
            conn.execute(
                text(
                    f"""
                    CREATE INDEX IF NOT EXISTS ix_feedback_memory_chunks_embedding_vector_pg
                    ON feedback_memory_chunks
                    USING ivfflat (embedding_vector_pg vector_cosine_ops)
                    WITH (lists = {max(settings.PGVECTOR_INDEX_LISTS, 10)})
                    """
                )
            )
        return True
    except Exception as exc:
        print(f"pgvector setup skipped: {exc}")
        return False


def ensure_weekly_pulse_columns(engine) -> bool:
    """
    Adds weekly pulse columns to survey_responses for existing databases that
    were created before raw NLP fields were introduced.
    """
    if engine.dialect.name != "postgresql":
        return False

    try:
        with engine.begin() as conn:
            table_exists = conn.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_name = 'survey_responses'
                    )
                    """
                )
            ).scalar()

            if not table_exists:
                return True

            columns = {
                "raw_data": "JSONB",
                "mte_score": "DOUBLE PRECISION",
                "ars_score": "DOUBLE PRECISION",
            }

            for column_name, column_type in columns.items():
                column_exists = conn.execute(
                    text(
                        """
                        SELECT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_name = 'survey_responses'
                              AND column_name = :column_name
                        )
                        """
                    ),
                    {"column_name": column_name},
                ).scalar()

                if not column_exists:
                    conn.execute(
                        text(
                            f"""
                            ALTER TABLE survey_responses
                            ADD COLUMN {column_name} {column_type}
                            """
                        )
                    )
        return True
    except Exception as exc:
        print(f"weekly pulse schema setup skipped: {exc}")
        return False
