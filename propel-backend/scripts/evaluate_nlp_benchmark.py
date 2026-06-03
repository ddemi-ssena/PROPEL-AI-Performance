from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.db.models.user import UserRole
from app.services.ai_service import AIService


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CASES_PATH = ROOT_DIR / "app" / "analytics" / "evaluation" / "nlp_benchmark_cases.json"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "scratch" / "nlp_benchmark"

CLASS_ORDER = {
    "sentiment_label": ["negative", "neutral", "positive"],
    "burnout_risk": ["low", "medium", "high"],
    "flight_risk": ["low", "medium", "high"],
}

ORDINAL_VALUE = {
    "sentiment_label": {"negative": -1, "neutral": 0, "positive": 1},
    "burnout_risk": {"low": 0, "medium": 1, "high": 2},
    "flight_risk": {"low": 0, "medium": 1, "high": 2},
}


@dataclass
class CaseResult:
    case_id: str
    text: str
    expected: dict[str, str]
    predicted: dict[str, str]
    provider: str
    model: str
    manager_summary: str
    action_recommendation: str


def load_cases(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        cases = json.load(handle)
    if not isinstance(cases, list):
        raise ValueError("Benchmark file must contain a list of cases.")
    return cases


def force_heuristic_mode() -> None:
    AIService.GEMINI_API_KEY = None
    AIService._generate_with_ollama = staticmethod(lambda *args, **kwargs: None)
    AIService._RESOLVED_OLLAMA_MODEL = None


def analyze_case(case: dict[str, Any]) -> CaseResult:
    scores = case.get("scores") or {}
    analysis, provider, model = AIService.analyze_weekly_feedback(
        dept_name=case.get("department_name") or "Yazilim Gelistirme",
        target_role=UserRole(case.get("target_role") or "employee"),
        week_theme=case.get("week_theme") or "Motivasyon & Psikolojik Durum",
        direction_label_tr=case.get("direction_label") or "Akran geri bildirimi",
        question_text=case.get("question_text")
        or "Bu hafta ekip icinde motivasyon, destek ihtiyaci veya risk sinyali gosteren somut davranisi ve etkisini hangi ornekle aciklarsin?",
        response_text=case["text"],
        score_communication=float(scores.get("communication", 3)),
        score_teamwork=float(scores.get("teamwork", 3)),
        score_leadership=float(scores.get("leadership", 3)),
        score_technical=float(scores.get("technical", 3)),
    )
    expected = dict(case["expected"])
    predicted = {
        "sentiment_label": str(analysis.get("sentiment_label") or ""),
        "burnout_risk": str(analysis.get("burnout_risk") or ""),
        "flight_risk": str(analysis.get("flight_risk") or ""),
    }
    return CaseResult(
        case_id=str(case["id"]),
        text=str(case["text"]),
        expected=expected,
        predicted=predicted,
        provider=provider,
        model=model,
        manager_summary=str(analysis.get("manager_summary") or ""),
        action_recommendation=str(analysis.get("action_recommendation") or ""),
    )


def safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def field_metrics(results: list[CaseResult], field: str) -> dict[str, Any]:
    labels = CLASS_ORDER[field]
    total = len(results)
    correct = sum(1 for item in results if item.expected[field] == item.predicted[field])
    per_label = {}
    confusion: dict[str, Counter[str]] = {label: Counter() for label in labels}

    for item in results:
        expected = item.expected[field]
        predicted = item.predicted[field]
        confusion.setdefault(expected, Counter())[predicted] += 1

    for label in labels:
        tp = sum(1 for item in results if item.expected[field] == label and item.predicted[field] == label)
        fp = sum(1 for item in results if item.expected[field] != label and item.predicted[field] == label)
        fn = sum(1 for item in results if item.expected[field] == label and item.predicted[field] != label)
        precision = safe_divide(tp, tp + fp)
        recall = safe_divide(tp, tp + fn)
        f1 = safe_divide(2 * precision * recall, precision + recall)
        per_label[label] = {
            "support": sum(1 for item in results if item.expected[field] == label),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }

    ordinal_errors = []
    ordinal_map = ORDINAL_VALUE[field]
    for item in results:
        if item.expected[field] in ordinal_map and item.predicted[field] in ordinal_map:
            ordinal_errors.append(abs(ordinal_map[item.expected[field]] - ordinal_map[item.predicted[field]]))

    return {
        "accuracy": round(safe_divide(correct, total), 4),
        "macro_precision": round(sum(item["precision"] for item in per_label.values()) / len(labels), 4),
        "macro_recall": round(sum(item["recall"] for item in per_label.values()) / len(labels), 4),
        "macro_f1": round(sum(item["f1"] for item in per_label.values()) / len(labels), 4),
        "mae": round(sum(ordinal_errors) / len(ordinal_errors), 4) if ordinal_errors else None,
        "per_label": per_label,
        "confusion_matrix": {
            expected: {predicted: confusion.get(expected, Counter()).get(predicted, 0) for predicted in labels}
            for expected in labels
        },
    }


def aggregate_metrics(results: list[CaseResult]) -> dict[str, Any]:
    exact_match = sum(
        1
        for item in results
        if all(item.expected[field] == item.predicted[field] for field in CLASS_ORDER)
    )
    provider_counts = Counter(item.provider for item in results)
    field_level = {field: field_metrics(results, field) for field in CLASS_ORDER}
    return {
        "case_count": len(results),
        "exact_match_accuracy": round(safe_divide(exact_match, len(results)), 4),
        "providers": dict(provider_counts),
        "fields": field_level,
    }


def mismatches(results: list[CaseResult]) -> list[dict[str, Any]]:
    rows = []
    for item in results:
        diff = {
            field: {"expected": item.expected[field], "predicted": item.predicted[field]}
            for field in CLASS_ORDER
            if item.expected[field] != item.predicted[field]
        }
        if diff:
            rows.append({"id": item.case_id, "text": item.text, "diff": diff})
    return rows


def percent(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:.1f}%"


def build_markdown_report(metrics: dict[str, Any], mode: str, results: list[CaseResult]) -> str:
    lines = [
        "# NLP Benchmark Report",
        "",
        f"- Date: {datetime.utcnow().isoformat(timespec='seconds')}Z",
        f"- Mode: `{mode}`",
        f"- Cases: {metrics['case_count']}",
        f"- Exact match accuracy: {percent(metrics['exact_match_accuracy'])}",
        f"- Providers: {metrics['providers']}",
        "",
        "## Field Metrics",
        "",
        "| Field | Accuracy | Macro Precision | Macro Recall | Macro F1 | Ordinal MAE |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for field, item in metrics["fields"].items():
        lines.append(
            "| "
            + " | ".join(
                [
                    field,
                    percent(item["accuracy"]),
                    percent(item["macro_precision"]),
                    percent(item["macro_recall"]),
                    percent(item["macro_f1"]),
                    str(item["mae"]),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Mismatches", ""])
    misses = mismatches(results)
    if not misses:
        lines.append("No mismatches.")
    else:
        for row in misses[:20]:
            diff_text = ", ".join(
                f"{field}: {payload['expected']} -> {payload['predicted']}"
                for field, payload in row["diff"].items()
            )
            lines.append(f"- `{row['id']}` {diff_text}")
    lines.append("")
    return "\n".join(lines)


def write_outputs(output_dir: Path, mode: str, results: list[CaseResult], metrics: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": mode,
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "metrics": metrics,
        "mismatches": mismatches(results),
        "results": [
            {
                "id": item.case_id,
                "expected": item.expected,
                "predicted": item.predicted,
                "provider": item.provider,
                "model": item.model,
                "manager_summary": item.manager_summary,
                "action_recommendation": item.action_recommendation,
            }
            for item in results
        ],
    }
    (output_dir / "nlp_benchmark_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "nlp_benchmark_report.md").write_text(
        build_markdown_report(metrics, mode, results),
        encoding="utf-8",
    )


def print_summary(metrics: dict[str, Any], mode: str, output_dir: Path | None) -> None:
    print(f"NLP benchmark mode={mode} cases={metrics['case_count']} exact_match={percent(metrics['exact_match_accuracy'])}")
    for field, item in metrics["fields"].items():
        print(
            f"{field}: accuracy={percent(item['accuracy'])} "
            f"macro_f1={percent(item['macro_f1'])} mae={item['mae']}"
        )
    if output_dir:
        print(f"Report written to: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate 360 feedback NLP analysis on labelled Turkish benchmark cases.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH, help="Path to labelled benchmark cases JSON.")
    parser.add_argument(
        "--mode",
        choices=["heuristic", "live"],
        default="heuristic",
        help="heuristic disables Gemini/Ollama for reproducible fallback evaluation; live uses configured LLM providers.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for JSON and Markdown reports.")
    parser.add_argument("--no-write", action="store_true", help="Print metrics without writing report files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "heuristic":
        force_heuristic_mode()

    cases = load_cases(args.cases)
    results = [analyze_case(case) for case in cases]
    metrics = aggregate_metrics(results)
    output_dir = None if args.no_write else args.output_dir
    if output_dir:
        write_outputs(output_dir, args.mode, results, metrics)
    print_summary(metrics, args.mode, output_dir)


if __name__ == "__main__":
    main()
