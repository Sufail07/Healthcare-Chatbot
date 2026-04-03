"""Convenience script to train the disease prediction model."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ml.train import train_model

if __name__ == "__main__":
    clf, features, accuracy = train_model()
    print(f"\nTraining complete! Accuracy: {accuracy:.2%}")
    print(f"Model ready with {len(features)} features and {len(clf.classes_)} diseases")
