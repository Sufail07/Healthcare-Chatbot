"""Preprocesses raw symptom CSV data into a binary feature matrix for training."""

import json
import pandas as pd
from pathlib import Path


def load_and_preprocess(raw_dir: str = "data/raw", output_dir: str = "data/processed"):
    """Load dataset.csv, one-hot encode symptoms, save processed data."""
    raw_path = Path(raw_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(raw_path / "dataset.csv")

    # Collect all unique symptoms
    symptom_cols = [c for c in df.columns if c.startswith("Symptom")]
    all_symptoms = set()
    for col in symptom_cols:
        vals = df[col].dropna().str.strip().str.replace(" ", "_").str.lower()
        all_symptoms.update(vals[vals != ""].tolist())

    all_symptoms.discard("")
    symptom_list = sorted(all_symptoms)

    # Save symptom list
    with open(out_path / "symptom_list.json", "w") as f:
        json.dump(symptom_list, f, indent=2)

    # Create binary feature matrix
    feature_rows = []
    for _, row in df.iterrows():
        symptoms_in_row = set()
        for col in symptom_cols:
            val = row[col]
            if pd.notna(val) and str(val).strip():
                symptoms_in_row.add(str(val).strip().replace(" ", "_").lower())
        feature_row = {s: (1 if s in symptoms_in_row else 0) for s in symptom_list}
        feature_row["disease"] = row["Disease"].strip()
        feature_rows.append(feature_row)

    processed_df = pd.DataFrame(feature_rows)
    processed_df.to_csv(out_path / "training_data.csv", index=False)

    print(f"Processed {len(processed_df)} rows with {len(symptom_list)} symptom features")
    print(f"Diseases: {processed_df['disease'].nunique()}")
    return processed_df, symptom_list
