from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline

from app.analytics.features.software import SoftwareFeatureBuilder


SoftwareBaselineModel = Literal["logistic_regression", "random_forest", "hist_gradient_boosting"]


@dataclass
class SoftwareTrainingResult:
    target_column: str
    model_name: str
    train_count: int
    test_count: int
    labels: list[str]
    metrics: dict[str, Any]
    top_features: list[dict[str, float]]
    validation_summary: dict[str, Any]
    pipeline: Pipeline


class SoftwareBaselineTrainer:
    @staticmethod
    def _build_pipeline(model_name: SoftwareBaselineModel) -> Pipeline:
        if model_name == "logistic_regression":
            classifier = LogisticRegression(
                class_weight="balanced",
                max_iter=2000,
                multi_class="auto",
                random_state=42,
            )
        elif model_name == "random_forest":
            classifier = RandomForestClassifier(
                class_weight="balanced",
                n_estimators=250,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=1,
            )
        elif model_name == "hist_gradient_boosting":
            classifier = HistGradientBoostingClassifier(
                learning_rate=0.06,
                max_iter=150,
                random_state=42,
            )
        else:
            raise ValueError(f"Desteklenmeyen model: {model_name}")

        return Pipeline(
            steps=[
                ("vectorizer", DictVectorizer(sparse=False)),
                ("imputer", SimpleImputer(strategy="median")),
                ("classifier", classifier),
            ]
        )

    @staticmethod
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

    @staticmethod
    def _top_features(pipeline: Pipeline, limit: int = 15) -> list[dict[str, float]]:
        vectorizer: DictVectorizer = pipeline.named_steps["vectorizer"]
        classifier = pipeline.named_steps["classifier"]
        feature_names = vectorizer.get_feature_names_out()

        if hasattr(classifier, "feature_importances_"):
            scores = classifier.feature_importances_
        elif hasattr(classifier, "coef_"):
            coefs = classifier.coef_
            scores = abs(coefs).mean(axis=0) if len(coefs.shape) > 1 else abs(coefs)
        else:
            return []

        ranked = sorted(
            zip(feature_names, scores),
            key=lambda item: float(item[1]),
            reverse=True,
        )
        return [
            {"feature": feature_name, "importance": round(float(score), 6)}
            for feature_name, score in ranked[:limit]
        ]

    @staticmethod
    def train(
        rows: list[dict[str, Any]],
        target_column: str,
        model_name: SoftwareBaselineModel = "random_forest",
        test_period_count: int = 12,
    ) -> SoftwareTrainingResult:
        dataset = SoftwareFeatureBuilder.build_from_rows(rows)
        train_periods, test_periods = SoftwareBaselineTrainer._split_by_last_periods(
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
                y_train.append(target)
            elif period_key in test_periods:
                x_test.append(feature_row)
                y_test.append(target)

        if len(set(y_train)) < 2:
            raise ValueError(f"{target_column} icin egitim setinde en az iki sinif olmali.")
        if not x_test:
            raise ValueError(f"{target_column} icin test seti bos kaldi.")

        pipeline = SoftwareBaselineTrainer._build_pipeline(model_name)
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

        return SoftwareTrainingResult(
            target_column=target_column,
            model_name=model_name,
            train_count=len(x_train),
            test_count=len(x_test),
            labels=labels,
            metrics=metrics,
            top_features=SoftwareBaselineTrainer._top_features(pipeline),
            validation_summary=dataset.validation_summary,
            pipeline=pipeline,
        )
