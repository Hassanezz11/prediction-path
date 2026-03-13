"""
Retrains the career prediction model on IIR_Dataset_Complet_S1_S7.xlsx.
Run: myenv/Scripts/python.exe train.py

Strategy:
  - Tries 4 candidate models via stratified 5-fold CV on the full dataset.
  - Picks the best CV-accuracy model and saves it.
  - Handles class imbalance (CIR=38, DSI=74, IADATA=68) with balanced weights.
  - Uses all 82 features (the averaging approach loses discriminative signal).
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.metrics import classification_report
import joblib

# ── Column rename map ──────────────────────────────────────────────────────────
RENAME_MAP = {
    "Genre": "Gender",
    "Âge": "Age",
    # S1
    "Français\nInterm. 1\n(coef 1.5)":  "S1_Francais",
    "Elem.\nEnglish 1\n(coef 1.5)":     "S1_English",
    "Analyse 1\n(coef 2)":              "S1_Analyse",
    "Algèbre 1\n(coef 1.5)":            "S1_Algebre",
    "Circuits\nélect. 1\n(coef 2)":     "S1_CircuitsElect",
    "Circuits\nnumér. 1\n(coef 1.5)":   "S1_CircuitsNumer",
    "Algorith.\n1\n(coef 3)":           "S1_Algo",
    "Langage\nProg. 1\n(coef 3.5)":     "S1_LangProg",
    "Comptab.\ngén.\n(coef 2)":         "S1_Comptab",
    "Org.\nentr.\n(coef 1.5)":          "S1_OrgEntr",
    "Métho.\nTrav.Univ.\n(coef 3)":     "S1_MethoTrav",
    # S2
    "Français\nInterm. 2\n(coef 1.5)":  "S2_Francais",
    "Elem.\nEnglish 2\n(coef 1.5)":     "S2_English",
    "Analyse 2\n(coef 2)":              "S2_Analyse",
    "Algèbre 2\n(coef 1.5)":            "S2_Algebre",
    "Algorith.\n2\n(coef 3)":           "S2_Algo",
    "Langage\nProg. 2\n(coef 3.5)":     "S2_LangProg",
    "Circuits\nélect. 2\n(coef 1.5)":   "S2_CircuitsElect",
    "Circuits\nnumér. 2\n(coef 2)":     "S2_CircuitsNumer",
    "Thermo-\ndynamique\n(coef 1.5)":   "S2_Thermo",
    "Electro-\nmagnét.\n(coef 1.5)":    "S2_Electromag",
    "Techniques\nréd.\n(coef 1.5)":     "S2_TechRed",
    "Initiation\nà l'IA\n(coef 1.5)":  "S2_InitIA",
    # S3
    "Français\nAvancé 1\n(coef 1.5)":   "S3_Francais",
    "Pre-Interm.\nEnglish 1\n(coef 1.5)": "S3_English",
    "Analyse 3\n(coef 2)":              "S3_Analyse",
    "Probabilité\n(coef 1.5)":          "S3_Proba",
    "Elec.\nanalog. 1\n(coef 3)":       "S3_ElecAnalog",
    "Prog. av.\n& SD 1\n(coef 3)":      "S3_ProgAvSD",
    "Conception\nSI\n(coef 2.5)":       "S3_ConceptionSI",
    "Micro-\nprocesseurs\n(coef 2)":    "S3_Microproc",
    "Systèmes\nexploit.\n(coef 1.5)":   "S3_SysExploit",
    "Tafatoh\n(التفتح)\n(coef 3)":      "S3_Tafatoh",
    # S4
    "Français\nAvancé 2\n(coef 1.5)":   "S4_Francais",
    "Pre-Interm.\nEnglish 2\n(coef 1.5)": "S4_English",
    "Analyse 4\n(coef 2)":              "S4_Analyse",
    "Statistiques\ndescr.\n(coef 1.5)": "S4_Stats",
    "Elec.\nanalog. 2\n(coef 3)":       "S4_ElecAnalog",
    "Prog. av.\n& SD 2\n(coef 3)":      "S4_ProgAvSD",
    "Bases de\ndonnées rel.\n(coef 2)": "S4_BaseDonnees",
    "Dév.\nWeb\n(coef 1.5)":            "S4_DevWeb",
    "Automat.\nséq.\n(coef 2)":         "S4_AutomatSeq",
    "Inform.\nIndust.\n(coef 1.5)":     "S4_InfoIndust",
    "Dév.\npers.\n(coef 3)":            "S4_DevPers",
    # S5
    "Comm.\nProf. 1\n(coef 1.5)":       "S5_CommProf",
    "Interm.\nEng. 1\n(coef 1.5)":      "S5_English",
    "Dév.\nNumér.\n(coef 1.5)":         "S5_DevNumer",
    "Info.\nResp.\n(coef 1.5)":         "S5_InfoResp",
    "POO\n(coef 3.5)":                  "S5_POO",
    "Conc. SI\n(coef 2)":               "S5_ConcSI",
    "SQL,\nPL/SQL\n(coef 1.5)":         "S5_SQL",
    "Unix\n(coef 2)":                   "S5_Unix",
    "Comp-\nilation\n(coef 1.5)":       "S5_Compilation",
    "Réseaux\nInfo. 1\n(coef 3.5)":     "S5_Reseaux",
    "Outils\nDev. 1\n(coef 3)":         "S5_OutilsDev",
    # S6
    "Comm.\nProf. 2\n(coef 1.5)":       "S6_CommProf",
    "Interm.\nEng. 2\n(coef 1.5)":      "S6_English",
    "Comp.\nCult.\n(coef 3)":           "S6_CompCult",
    "Modèles\nStat.\n(coef 2)":         "S6_ModelStat",
    "Prog.\nLinéaire\n(coef 1.5)":      "S6_ProgLineaire",
    "JAVA\n(coef 2)":                   "S6_Java",
    "Python &\nFwk\n(coef 1.5)":        "S6_Python",
    "Conc.\nOO\n(coef 2)":              "S6_ConcOO",
    "SQL\nServer\n(coef 1.5)":          "S6_SQLServer",
    "Rech.\nScient.\n(coef 2)":         "S6_RechScient",
    "Projet\nInfo.\n(coef 1)":          "S6_ProjetInfo",
    "Réseaux\nInfo. 2\n(coef 3.5)":     "S6_Reseaux",
    # S7
    "Comm.\nProf. 3\n(coef 1.5)":       "S7_CommProf",
    "Adv.\nEng. 1\n(coef 1.5)":         "S7_English",
    "Intro IA\n& Éthique\n(coef 1.5)":  "S7_IntroIA",
    "Machine\nLearning\n(coef 1.5)":    "S7_ML",
    "Prog.\nAvancée\n(coef 3.5)":       "S7_ProgAvancee",
    "NoSQL\n(coef 1.5)":                "S7_NoSQL",
    "Admin.\nOracle 1\n(coef 2)":       "S7_AdminOracle",
    "Tech.\n.Net\n(coef 2)":            "S7_DotNet",
    "Dev.\nMobile\n(coef 1.5)":         "S7_DevMobile",
    "Admin.\nUNIX\n(coef 2)":           "S7_AdminUnix",
    "Virtualisa-\ntion\n(coef 1.5)":    "S7_Virtualisation",
    "Analyse\ndonnées\n(coef 1.5)":     "S7_AnalyseDonnees",
    "Recherche\nopér.\n(coef 1.5)":     "S7_RechercheOper",
    "🎯 Branche\n(DSI/IADATA/CIR)":     "Branch",
}

# ── Load & clean ───────────────────────────────────────────────────────────────
df = pd.read_excel("IIR_Dataset_Complet_S1_S7.xlsx", header=1)
print(f"Loaded {len(df)} rows, {len(df.columns)} columns.")
df.rename(columns=RENAME_MAP, inplace=True)
df.drop(columns=["ID", "Nom", "Filière", "Domaine", "Carrière"], errors="ignore", inplace=True)
before = len(df)
df.drop_duplicates(inplace=True)
print(f"Removed {before - len(df)} duplicate rows. Remaining: {len(df)}")

gender_encoder = LabelEncoder()
df["Gender"] = gender_encoder.fit_transform(df["Gender"])

# Drop any remaining non-numeric columns (e.g. Projects, extra text fields)
# except the target Branch column which is a string we keep intentionally.
non_numeric = [c for c in df.columns
               if c != "Branch" and df[c].dtype == object]
if non_numeric:
    print(f"Dropping non-numeric columns: {non_numeric}")
    df.drop(columns=non_numeric, inplace=True)

feature_cols = [c for c in df.columns if c != "Branch"]
X = df[feature_cols]
y = df["Branch"]

print(f"\nFeatures: {len(feature_cols)} | Samples: {len(df)}")
print("Branch distribution:")
print(df["Branch"].value_counts())

# ── Candidate models ───────────────────────────────────────────────────────────
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

candidates = {
    "RandomForest": Pipeline([
        ("clf", RandomForestClassifier(
            n_estimators=500, class_weight="balanced",
            max_features="sqrt", random_state=42, n_jobs=-1))
    ]),
    "GradientBoosting": Pipeline([
        ("clf", GradientBoostingClassifier(
            n_estimators=300, learning_rate=0.05,
            max_depth=3, subsample=0.8, random_state=42))
    ]),
    "LogisticRegression": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            C=1.0, max_iter=2000, class_weight="balanced",
            random_state=42))
    ]),
    "SVM": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", SVC(kernel="rbf", C=10, gamma="scale",
                    class_weight="balanced", probability=True, random_state=42))
    ]),
}

print("\n--- Model comparison (5-fold stratified CV) ---")
results = {}
for name, pipe in candidates.items():
    scores = cross_val_score(pipe, X, y, cv=cv, scoring="accuracy", n_jobs=-1)
    results[name] = scores.mean()
    print(f"  {name:<22}  {scores.mean()*100:5.1f}%  (+/- {scores.std()*100:.1f}%)")

best_name = max(results, key=results.get)
print(f"\nBest model: {best_name}  ({results[best_name]*100:.1f}% CV accuracy)")

# ── Tune the best model ────────────────────────────────────────────────────────
print(f"\nTuning {best_name}…")

if best_name == "RandomForest":
    param_grid = {"clf__n_estimators": [300, 500, 800],
                  "clf__max_depth": [None, 10, 20],
                  "clf__min_samples_leaf": [1, 2]}
elif best_name == "GradientBoosting":
    param_grid = {"clf__n_estimators": [200, 400],
                  "clf__learning_rate": [0.05, 0.1],
                  "clf__max_depth": [3, 4]}
elif best_name == "LogisticRegression":
    param_grid = {"clf__C": [0.1, 0.5, 1.0, 5.0, 10.0]}
else:  # SVM
    param_grid = {"clf__C": [1, 10, 50, 100],
                  "clf__gamma": ["scale", 0.01, 0.05, 0.1]}

grid = GridSearchCV(candidates[best_name], param_grid,
                    cv=cv, scoring="accuracy", n_jobs=-1, verbose=0)
grid.fit(X, y)
best_model = grid.best_estimator_
print(f"Best params : {grid.best_params_}")
print(f"Tuned CV acc: {grid.best_score_*100:.1f}%")

# ── Final report ───────────────────────────────────────────────────────────────
best_model.fit(X, y)
print("\nClassification report on full training set (indicative):")
print(classification_report(y, best_model.predict(X), zero_division=0))

# ── Save ───────────────────────────────────────────────────────────────────────
joblib.dump(best_model, "CS_students_career_predictor.pkl")
joblib.dump({"gender_classes": list(gender_encoder.classes_),
             "feature_names":  list(X.columns)},
            "model_metadata.pkl")
print("Saved: CS_students_career_predictor.pkl")
print("Saved: model_metadata.pkl")
print("Done.")
