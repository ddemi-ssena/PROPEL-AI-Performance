import requests

from app.services.ai_service import AIService


class _Response:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self):
        return self._payload


def test_gemini_retries_transient_timeout(monkeypatch):
    calls = {"count": 0}

    def fake_post(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise requests.exceptions.ReadTimeout("slow")
        return _Response(
            200,
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": '{"manager_summary": "ok"}'}],
                        }
                    }
                ]
            },
        )

    monkeypatch.setattr(AIService, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(AIService, "_LLM_RETRY_BASE_SECONDS", 0)
    monkeypatch.setattr(requests, "post", fake_post)

    output = AIService._generate_with_gemini("prompt", model_name_override="gemini-test")

    assert calls["count"] == 2
    assert output == '{"manager_summary": "ok"}'


def test_gemini_does_not_retry_expired_key(monkeypatch):
    calls = {"count": 0}

    def fake_post(*args, **kwargs):
        calls["count"] += 1
        return _Response(400, text='{"error": {"message": "API key expired"}}')

    monkeypatch.setattr(AIService, "GEMINI_API_KEY", "expired-key")
    monkeypatch.setattr(AIService, "_LLM_RETRY_BASE_SECONDS", 0)
    monkeypatch.setattr(requests, "post", fake_post)

    output = AIService._generate_with_gemini("prompt", model_name_override="gemini-test")

    assert calls["count"] == 1
    assert output is None
    assert "API key expired" in (AIService.LAST_LLM_ERROR or "")
