from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline

from app.analytics.features.sales import SalesFeatureBuilder


@dataclass
class SalesTrainingResult:
    target_column: str
    model_name: str
    train_count: int
    test_count: int
    labels: list[str]
    metrics: dict[str, Any]
    top_features: list[dict[str, float]]
    validation_summary: dict[str, Any]
    pipeline: Pipeline


def _build_simple_pipeline() -> Pipeline:
    """Fallback pipeline when class distribution is too imbalanced for stacking."""
    rf = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        min_samples_leaf=1,
        random_state=42,
        n_jobs=1,
    )
    return Pipeline(
        steps=[
            ("vectorizer", DictVectorizer(sparse=False)),
            ("imputer", SimpleImputer(strategy="median")),
            ("classifier", rf),
        ]
    )


def _build_stacking_pipeline() -> Pipeline:
    try:
        from lightgbm import LGBMClassifier
        lgbm = LGBMClassifier(
            n_estimators=150,
            learning_rate=0.05,
            num_leaves=31,
            class_weight="balanced",
            random_state=42,
            n_jobs=1,
            verbose=-1,
        )
    except ImportError:
        lgbm = None

    try:
        from xgboost import XGBClassifier
        xgb = XGBClassifier(
            n_estimators=150,
            learning_rate=0.05,
            max_depth=5,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
            n_jobs=1,
            verbosity=0,
        )
    except ImportError:
        xgb = None

    rf = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        min_samples_leaf=2,
        random_state=42,
        n_jobs=1,
    )

    estimators = []
    if lgbm is not None:
        estimators.append(("lgbm", lgbm))
    if xgb is not None:
        estimators.append(("xgb", xgb))
    estimators.append(("rf", rf))

    meta_learner = LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=42,
    )

    stacking = StackingClassifier(
        estimators=estimators,
        final_estimator=meta_learner,
        passthrough=False,
        cv=3,
        n_jobs=1,
    )

    return Pipeline(
        steps=[
            ("vectorizer", DictVectorizer(sparse=False)),
            ("imputer", SimpleImputer(strategy="median")),
            ("classifier", stacking),
        ]
    )


def _split_by_last_periods(
    metadata_rows: list[dict[str, Any]],
    test_period_count: int,
) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    periods = sorted({(row["year"], row["week"]) for row in metadata_rows})
    if len(periods) <= test_period_count:
        raise ValueError("Test icin ayrilacak donem sayisi toplam donem sayisindan kucuk olmali.")
    test_periods = set(periods[-test_period_count:])
    train_periods = set(periods[:-test_period_count])
    return train_periods, test_periods


def _top_features_from_stacking(pipeline: Pipeline, limit: int = 15) -> list[dict[str, float]]:
    vectorizer: DictVectorizer = pipeline.named_steps["vectorizer"]
    classifier: StackingClassifier = pipeline.named_steps["classifier"]
    feature_names = vectorizer.get_feature_names_out()

    scores_list = []
    for estimator in classifier.estimators_:
        if hasattr(estimator, "feature_importances_"):
            scores_list.append(estimator.feature_importances_)
        elif hasattr(estimator, "coef_"):
            coefs = estimator.coef_
            scores_list.append(
                abs(coefs).mean(axis=0) if len(coefs.shape) > 1 else abs(coefs[0])
            )

    if not scores_list:
        final_est = classifier.final_estimator_
        if hasattr(final_est, "coef_"):
            return []
        return []

    import numpy as np
    combined = np.mean(scores_list, axis=0) if len(scores_list) > 1 else scores_list[0]

    ranked = sorted(
        zip(feature_names, combined),
        key=lambda item: float(item[1]),
        reverse=True,
    )
    return [
        {"feature": feature_name, "importance": round(float(score), 6)}
        for feature_name, score in ranked[:limit]
    ]


class SalesStackingTrainer:
    @staticmethod
    def train(
        rows: list[dict[str, Any]],
        target_column: str,
        test_period_count: int = 8,
    ) -> SalesTrainingResult:
        dataset = SalesFeatureBuilder.build_from_rows(rows)
        train_periods, test_periods = _split_by_last_periods(
            dataset.metadata_rows,
            test_period_count,
        )

        x_train: list[dict[str, Any]] = []
        y_train: list[str] = []
        x_test: list[dict[str, Any]] = []
        y_test: list[str] = []

        for feature_row, target_row, metadata_row in zip(
            dataset.feature_rows,
            dataset.target_rows,
            dataset.metadata_rows,
        ):
            target = target_row.get(target_column)
            if not target:
                continue

            period_key = (metadata_row["year"], metadata_row["week"])
            if period_key in train_periods:
                x_train.append(feature_row)
                y_train.append(str(target))
            elif period_key in test_periods:
                x_test.append(feature_row)
                y_test.append(str(target))

        if len(set(y_train)) < 2:
            raise ValueError(f"{target_column} icin egitim setinde en az iki sinif olmali.")
        if not x_test:
            raise ValueError(f"{target_column} icin test seti bos kaldi.")

        from collections import Counter
        class_counts = Counter(y_train)
        min_class_count = min(class_counts.values())
        # Stacking requires at least cv*2 samples per class; fall back to simple RF if not enough
        use_stacking = min_class_count >= 6
        pipeline = _build_stacking_pipeline() if use_stacking else _build_simple_pipeline()
        pipeline.fit(x_train, y_train)
        y_pred = pipeline.predict(x_test)
        labels = sorted(set(y_train) | set(y_test) | set(y_pred))

        metrics = {
            "accuracy": round(float(accuracy_score(y_test, y_pred)), 6),
            "macro_f1": round(float(f1_score(y_test, y_pred, average="macro", zero_division=0)), 6),
            "weighted_f1": round(float(f1_score(y_test, y_pred, average="weighted", zero_division=0)), 6),
            "classification_report": classification_report(
                y_test,
                y_pred,
                labels=labels,
                zero_division=0,
                output_dict=True,
            ),
            "confusion_matrix": confusion_matrix(y_test, y_pred, labels=labels).tolist(),
        }

        model_name = "stacking_lgbm_xgb_rf_lr" if use_stacking else "random_forest_fallback"
        return SalesTrainingResult(
            target_column=target_column,
            model_name=model_name,
            train_count=len(x_train),
            test_count=len(x_test),
            labels=labels,
            metrics=metrics,
            top_features=_top_features_from_stacking(pipeline),
            validation_summary=dataset.validation_summary,
            pipeline=pipeline,
        )
