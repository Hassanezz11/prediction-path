from __future__ import annotations

import pandas as pd

from backend.config import BASE_DIR


BRANCH_OPTIONS = ["IADATA", "DSI", "CIR"]

BRANCH_META = {
    "IADATA": {
        "full": "Intelligence Artificielle & Data",
        "description": "Strong fit for AI, machine learning, analytics, and applied data work.",
    },
    "DSI": {
        "full": "Developpement des Systemes d'Information",
        "description": "Strong fit for software engineering, application delivery, and product development.",
    },
    "CIR": {
        "full": "Cybersecurite, Infrastructure & Reseaux",
        "description": "Strong fit for security operations, infrastructure engineering, and networking.",
    },
}

SEMESTERS = {
    "S1": {
        "title": "Semester 1 - AP Year 1",
        "modules": [
            ("S1_Francais", "Francais Intermediaire 1", 1.5),
            ("S1_English", "Elementary English 1", 1.5),
            ("S1_Analyse", "Analyse 1", 2.0),
            ("S1_Algebre", "Algebre 1", 1.5),
            ("S1_CircuitsElect", "Circuits Electroniques 1", 2.0),
            ("S1_CircuitsNumer", "Circuits Numeriques 1", 1.5),
            ("S1_Algo", "Algorithmique 1", 3.0),
            ("S1_LangProg", "Langage de Programmation 1", 3.5),
            ("S1_Comptab", "Comptabilite Generale", 2.0),
            ("S1_OrgEntr", "Organisation d'Entreprise", 1.5),
            ("S1_MethoTrav", "Methodologie Travail Universitaire", 3.0),
        ],
    },
    "S2": {
        "title": "Semester 2 - AP Year 1",
        "modules": [
            ("S2_Francais", "Francais Intermediaire 2", 1.5),
            ("S2_English", "Elementary English 2", 1.5),
            ("S2_Analyse", "Analyse 2", 2.0),
            ("S2_Algebre", "Algebre 2", 1.5),
            ("S2_Algo", "Algorithmique 2", 3.0),
            ("S2_LangProg", "Langage de Programmation 2", 3.5),
            ("S2_CircuitsElect", "Circuits Electroniques 2", 1.5),
            ("S2_CircuitsNumer", "Circuits Numeriques 2", 2.0),
            ("S2_Thermo", "Thermodynamique", 1.5),
            ("S2_Electromag", "Electromagnetisme", 1.5),
            ("S2_TechRed", "Techniques de Redaction", 1.5),
            ("S2_InitIA", "Initiation a l'IA", 1.5),
        ],
    },
    "S3": {
        "title": "Semester 3 - AP Year 2",
        "modules": [
            ("S3_Francais", "Francais Avance 1", 1.5),
            ("S3_English", "Pre-Intermediate English 1", 1.5),
            ("S3_Analyse", "Analyse 3", 2.0),
            ("S3_Proba", "Probabilites", 1.5),
            ("S3_ElecAnalog", "Electronique Analogique 1", 3.0),
            ("S3_ProgAvSD", "Prog. Avancee & Struct. Donnees 1", 3.0),
            ("S3_ConceptionSI", "Conception SI", 2.5),
            ("S3_Microproc", "Microprocesseurs", 2.0),
            ("S3_SysExploit", "Systemes d'Exploitation", 1.5),
            ("S3_Tafatoh", "Tafatoh", 3.0),
        ],
    },
    "S4": {
        "title": "Semester 4 - AP Year 2",
        "modules": [
            ("S4_Francais", "Francais Avance 2", 1.5),
            ("S4_English", "Pre-Intermediate English 2", 1.5),
            ("S4_Analyse", "Analyse 4", 2.0),
            ("S4_Stats", "Statistiques Descriptives", 1.5),
            ("S4_ElecAnalog", "Electronique Analogique 2", 3.0),
            ("S4_ProgAvSD", "Prog. Avancee & Struct. Donnees 2", 3.0),
            ("S4_BaseDonnees", "Bases de Donnees Relationnelles", 2.0),
            ("S4_DevWeb", "Developpement Web", 1.5),
            ("S4_AutomatSeq", "Automatisme Sequentiel", 2.0),
            ("S4_InfoIndust", "Informatique Industrielle", 1.5),
            ("S4_DevPers", "Developpement Personnel", 3.0),
        ],
    },
    "S5": {
        "title": "Semester 5 - IIR Year 3",
        "modules": [
            ("S5_CommProf", "Communication Professionnelle 1", 1.5),
            ("S5_English", "Intermediate English 1", 1.5),
            ("S5_DevNumer", "Developpement Numerique", 1.5),
            ("S5_InfoResp", "Informatique Responsable", 1.5),
            ("S5_POO", "POO", 3.5),
            ("S5_ConcSI", "Conception SI", 2.0),
            ("S5_SQL", "SQL / PL-SQL", 1.5),
            ("S5_Unix", "Unix", 2.0),
            ("S5_Compilation", "Compilation", 1.5),
            ("S5_Reseaux", "Reseaux Informatiques 1", 3.5),
            ("S5_OutilsDev", "Outils de Developpement 1", 3.0),
        ],
    },
    "S6": {
        "title": "Semester 6 - IIR Year 3",
        "modules": [
            ("S6_CommProf", "Communication Professionnelle 2", 1.5),
            ("S6_English", "Intermediate English 2", 1.5),
            ("S6_CompCult", "Competences Culturelles", 3.0),
            ("S6_ModelStat", "Modeles Statistiques", 2.0),
            ("S6_ProgLineaire", "Programmation Lineaire", 1.5),
            ("S6_Java", "Java", 2.0),
            ("S6_Python", "Python & Framework", 1.5),
            ("S6_ConcOO", "Conception Orientee Objet", 2.0),
            ("S6_SQLServer", "SQL Server", 1.5),
            ("S6_RechScient", "Recherche Scientifique", 2.0),
            ("S6_ProjetInfo", "Projet Informatique", 1.0),
            ("S6_Reseaux", "Reseaux Informatiques 2", 3.5),
        ],
    },
    "S7": {
        "title": "Semester 7 - IIR Year 4",
        "modules": [
            ("S7_CommProf", "Communication Professionnelle 3", 1.5),
            ("S7_English", "Advanced English 1", 1.5),
            ("S7_IntroIA", "Intro IA & Ethique", 1.5),
            ("S7_ML", "Machine Learning", 1.5),
            ("S7_ProgAvancee", "Programmation Avancee", 3.5),
            ("S7_NoSQL", "NoSQL", 1.5),
            ("S7_AdminOracle", "Administration Oracle 1", 2.0),
            ("S7_DotNet", "Technologie .NET", 2.0),
            ("S7_DevMobile", "Developpement Mobile", 1.5),
            ("S7_AdminUnix", "Administration UNIX", 2.0),
            ("S7_Virtualisation", "Virtualisation", 1.5),
            ("S7_AnalyseDonnees", "Analyse de Donnees", 1.5),
            ("S7_RechercheOper", "Recherche Operationnelle", 1.5),
        ],
    },
}

GAP_KEYWORDS = {
    ("IADATA", "DSI"): [
        "web", "javascript", "react", "node", "java", "spring", "sql",
        "database", "docker", "mobile", "flutter", "angular", "vue",
        "backend", "fullstack", "full-stack", "devops", "kubernetes",
    ],
    ("IADATA", "CIR"): [
        "security", "hacking", "network", "linux", "cyber", "cryptography",
        "penetration", "forensics", "kali", "ethical", "firewall", "comptia",
    ],
    ("DSI", "IADATA"): [
        "machine learning", "data science", "python", "deep learning",
        "neural", "nlp", "statistics", "tensorflow", "pytorch",
        "data analysis", "artificial intelligence",
    ],
    ("DSI", "CIR"): [
        "security", "hacking", "network", "linux", "cyber", "cryptography",
        "penetration", "forensics", "ethical", "comptia",
    ],
    ("CIR", "IADATA"): [
        "machine learning", "data science", "python", "deep learning",
        "neural", "statistics", "tensorflow", "pytorch", "data analysis",
        "artificial intelligence",
    ],
    ("CIR", "DSI"): [
        "web", "javascript", "react", "java", "sql", "database", "mobile",
        "flutter", "backend", "fullstack", "devops", "software", "django",
        "spring", "node",
    ],
}


def load_courses() -> pd.DataFrame:
    path = BASE_DIR / "courses.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "title" in df.columns:
        df["title_lower"] = df["title"].astype(str).str.lower()
    return df


COURSES_DF = load_courses()


def get_course_recommendations(predicted: str, preferred: str, limit: int = 8) -> list[dict]:
    if COURSES_DF.empty:
        return []
    keywords = GAP_KEYWORDS.get((predicted, preferred), [])
    if not keywords:
        return []
    mask = COURSES_DF["title_lower"].str.contains("|".join(keywords), na=False)
    columns = [col for col in ["title", "url", "rating", "num_reviews", "duration", "image"] if col in COURSES_DF.columns]
    return (
        COURSES_DF.loc[mask, columns]
        .sort_values("rating", ascending=False)
        .head(limit)
        .fillna("")
        .to_dict(orient="records")
    )


ALL_MODULE_KEYS = [
    module_key
    for semester in SEMESTERS.values()
    for module_key, _label, _coef in semester["modules"]
]
