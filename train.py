"""
Retrains the career prediction model on cs_students_IIR_modules.xlsx.
Run this script whenever you want to retrain: python train.py

Target: predicts the best BRANCH for the student — one of:
    • AI
    • Cyber Security
    • Development
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

# ── Branch mapping ─────────────────────────────────────────────────────────────
# Every specific career in the dataset is grouped into one of the 3 branches.
BRANCH_MAP = {
    # AI branch — data, research, intelligence, automation
    "AI Researcher":               "AI",
    "Bioinformatician":            "AI",   # uses ML/data for biology
    "Computer Vision Engineer":    "AI",
    "Data Analyst":                "AI",
    "Data Scientist":              "AI",
    "Geospatial Analyst":          "AI",   # spatial data analysis
    "Machine Learning Engineer":   "AI",
    "Machine Learning Researcher": "AI",
    "NLP Engineer":                "AI",
    "NLP Research Scientist":      "AI",
    "Quantum Computing Researcher":"AI",
    "Robotics Engineer":           "AI",   # heavily AI-driven

    # Cyber Security branch — protection, forensics, ethical hacking
    "Data Privacy Specialist":     "Cyber Security",
    "Digital Forensics Specialist":"Cyber Security",
    "Ethical Hacker":              "Cyber Security",
    "Information Security Analyst":"Cyber Security",
    "Security Analyst":            "Cyber Security",

    # Development branch — building software, systems, apps
    "Blockchain Engineer":         "Development",
    "Cloud Solutions Architect":   "Development",
    "Database Administrator":      "Development",
    "DevOps Engineer":             "Development",
    "Distributed Systems Engineer":"Development",
    "Embedded Software Engineer":  "Development",
    "Game Developer":              "Development",
    "Graphics Programmer":         "Development",
    "Healthcare IT Specialist":    "Development",
    "IoT Developer":               "Development",
    "Mobile App Developer":        "Development",
    "SEO Specialist":              "Development",
    "Software Engineer":           "Development",
    "UX Designer":                 "Development",
    "VR Developer":                "Development",
    "Web Developer":               "Development",
}

# ── Load ───────────────────────────────────────────────────────────────────────
df = pd.read_excel("cs_students_IIR_modules.xlsx")
print(f"Loaded {len(df)} rows, {len(df.columns)} columns.")

# ── Drop columns not useful for prediction ─────────────────────────────────────
# Student ID / Name / Major (all same) / Projects → identifiers/text, no signal
# Individual module grades → we keep only the group averages (Moy_*) to avoid
#   redundancy; Python & Java are kept individually because they matter most.
# Derived totals → Moyenne_S5, Moyenne_S6, Moyenne_Annuelle are computed from
#   the Moy_* averages, so including them would cause multicollinearity.
drop_cols = [
    "Student ID", "Name", "Major", "Projects",
    # Interested Domain is excluded so the model predicts purely from grades
    "Interested Domain",
    # individual S5 grades
    "CommProf1", "English1", "DevNumerique", "InfoResponsable",
    "POO", "ConceptionSI", "SQL_PLSQL", "Unix", "Compilation",
    "Reseaux1", "OutilsDev1",
    # individual S6 grades (Python & Java kept separately)
    "CommProf2", "English2", "CompCulturelles", "ModelesStat", "ProgLineaire",
    "ConceptionOO", "SQLServer", "RechercheSci", "ProjetInfo", "Reseaux2",
    # derived totals
    "Moyenne_S5", "Moyenne_S6", "Moyenne_Annuelle",
]
df.drop(columns=drop_cols, inplace=True)

# ── Drop duplicates ────────────────────────────────────────────────────────────
before = len(df)
df.drop_duplicates(inplace=True)
print(f"Removed {before - len(df)} duplicate rows. Remaining: {len(df)}")

# ── Encode categorical columns ─────────────────────────────────────────────────
gender_encoder = LabelEncoder()
df["Gender"] = gender_encoder.fit_transform(df["Gender"])

print("\nFeatures used for training:")
feature_cols = [c for c in df.columns if c != "Future Career" and c != "Branch"]
for f in feature_cols:
    print(f"  - {f}")

# ── Map careers → branches ─────────────────────────────────────────────────────
df["Branch"] = df["Future Career"].map(BRANCH_MAP)
unmapped = df["Branch"].isna().sum()
if unmapped > 0:
    print(f"WARNING: {unmapped} rows could not be mapped to a branch:")
    print(df[df["Branch"].isna()]["Future Career"].unique())
df.drop(columns=["Future Career"], inplace=True)

print("\nBranch distribution:")
print(df["Branch"].value_counts())

# ── Split ──────────────────────────────────────────────────────────────────────
X = df[feature_cols]
y = df["Branch"]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ── Train ──────────────────────────────────────────────────────────────────────
model = GradientBoostingClassifier(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

# ── Evaluate ───────────────────────────────────────────────────────────────────
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"\nTest Accuracy: {acc * 100:.1f}%")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, zero_division=0))

# ── Save model + metadata ──────────────────────────────────────────────────────
joblib.dump(model, "CS_students_career_predictor.pkl")
joblib.dump(
    {
        "gender_classes": list(gender_encoder.classes_),   # ['Female', 'Male']
        "feature_names":  list(X.columns),
    },
    "model_metadata.pkl",
)
print("\nSaved: CS_students_career_predictor.pkl")
print("Saved: model_metadata.pkl")
print("Done.")
