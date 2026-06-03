# NLP Benchmark Report

- Date: 2026-06-02T13:04:20Z
- Mode: `heuristic`
- Cases: 50
- Exact match accuracy: 68.0%
- Providers: {'heuristic': 50}

## Field Metrics

| Field | Accuracy | Macro Precision | Macro Recall | Macro F1 | Ordinal MAE |
|---|---:|---:|---:|---:|---:|
| sentiment_label | 86.0% | 86.3% | 88.3% | 84.3% | 0.14 |
| burnout_risk | 94.0% | 93.2% | 94.7% | 93.9% | 0.06 |
| flight_risk | 84.0% | 84.2% | 83.9% | 84.0% | 0.16 |

## Mismatches

- `N007` flight_risk: medium -> high
- `N009` burnout_risk: medium -> high
- `B001` flight_risk: high -> medium
- `B003` flight_risk: high -> medium
- `B004` flight_risk: medium -> high
- `B010` flight_risk: high -> medium
- `F001` burnout_risk: high -> medium
- `F007` burnout_risk: medium -> high
- `M001` sentiment_label: neutral -> positive
- `M002` sentiment_label: neutral -> positive, flight_risk: low -> medium
- `M003` sentiment_label: neutral -> positive, flight_risk: medium -> low
- `M004` sentiment_label: neutral -> positive
- `M005` sentiment_label: neutral -> positive
- `M006` sentiment_label: neutral -> positive
- `M007` flight_risk: medium -> low
- `M010` sentiment_label: neutral -> positive
