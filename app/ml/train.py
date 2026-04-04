"""Trains a RandomForestClassifier on the processed symptom data."""

import json
import joblib
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

from app.ml.preprocessor import load_and_preprocess


def train_model(raw_dir: str = "data/raw", processed_dir: str = "data/processed",
                model_dir: str = "data/models"):
    """Train and save the disease prediction model."""
    model_path = Path(model_dir)
    model_path.mkdir(parents=True, exist_ok=True)
    
    processed_path = Path(processed_dir)
    raw_path = Path(raw_dir)

    # Check if we can use already processed data
    if (processed_path / "training_data.csv").exists() and not (raw_path / "dataset.csv").exists():
        print("Using existing processed data...")
        df = pd.read_csv(processed_path / "training_data.csv")
        with open(processed_path / "symptom_list.json") as f:
            symptom_list = json.load(f)
    else:
        # Preprocess data
        df, symptom_list = load_and_preprocess(raw_dir, processed_dir)

    # Prepare features and labels
    feature_columns = [c for c in df.columns if c != "disease"]
    X = df[feature_columns].values
    y = df["disease"].values

    # Train Random Forest
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        random_state=42,
        n_jobs=-1,
    )

    # Cross-validation (use min 3 folds, adapting to smallest class size)
    min_class_count = pd.Series(y).value_counts().min()
    cv_folds = min(5, min_class_count)
    scores = cross_val_score(clf, X, y, cv=cv_folds, scoring="accuracy")
    print(f"Cross-validation accuracy: {scores.mean():.4f} (+/- {scores.std():.4f})")

    # Train on full data
    clf.fit(X, y)

    # Save artifacts
    joblib.dump(clf, model_path / "disease_model.joblib")
    with open(model_path / "feature_columns.json", "w") as f:
        json.dump(feature_columns, f, indent=2)

    print(f"Model saved to {model_path / 'disease_model.joblib'}")
    print(f"Feature columns ({len(feature_columns)}) saved to {model_path / 'feature_columns.json'}")

    return clf, feature_columns, scores.mean()
