from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np

from backend.config import BASE_DIR
from backend.domain import BRANCH_META, get_course_recommendations


@lru_cache(maxsize=1)
def load_artifacts():
    model = joblib.load(BASE_DIR / "CS_students_career_predictor.pkl")
    metadata = joblib.load(BASE_DIR / "model_metadata.pkl")
    return model, metadata


def predict_branch(age: int, gender: str, preferred_branch: str, module_grades: dict[str, float]) -> dict:
    model, metadata = load_artifacts()
    gender_classes = metadata["gender_classes"]
    feature_names = metadata["feature_names"]
    gender_map = {name: index for index, name in enumerate(gender_classes)}

    feature_values = {"Gender": gender_map.get(gender, 0), "Age": age}
    feature_values.update(module_grades)
    features = np.array([[feature_values.get(name, 0.0) for name in feature_names]])

    prediction = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0].astype(float)
    classes = list(model.classes_)
    probabilities_map = {branch: float(prob) for branch, prob in zip(classes, probabilities)}
    recommended_courses = []
    message = f"Your academic profile already aligns with {preferred_branch}."

    if prediction != preferred_branch:
        recommended_courses = get_course_recommendations(prediction, preferred_branch)
        message = f"Grades currently align more with {prediction}, while the preferred branch is {preferred_branch}."

    return {
        "predicted_branch": prediction,
        "predicted_branch_full": BRANCH_META[prediction]["full"],
        "probabilities": probabilities_map,
        "gap_analysis": {
            "preferred_branch": preferred_branch,
            "matches_preference": prediction == preferred_branch,
            "message": message,
        },
        "recommended_courses": recommended_courses,
        "model_version": str(Path(BASE_DIR / "CS_students_career_predictor.pkl").stat().st_mtime),
    }
