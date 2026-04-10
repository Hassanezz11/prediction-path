import streamlit as st
import joblib
import numpy as np
import pandas as pd
import os
import io
import requests
from pypdf import PdfReader

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IIR Branch Predictor",
    page_icon=None,
    layout="wide",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
# Dark theme is set in .streamlit/config.toml — all native Streamlit components
# (inputs, tabs, labels, selectboxes) go dark automatically with correct contrast.
# This block only styles custom HTML elements: hero, result cards, conf bars.
st.markdown("""
<style>
[data-testid="stHeader"] { background: transparent; }

/* ---- Hero ---- */
.hero {
    background: #111827;
    border-radius: 14px;
    padding: 40px 44px 34px;
    margin-bottom: 32px;
    border-left: 6px solid #3b82f6;
    box-shadow: 0 4px 24px rgba(0,0,0,0.5);
}

/* ---- Section label ---- */
.section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 1.6px;
    text-transform: uppercase;
    color: #60a5fa;
    margin: 0 0 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid #2d3748;
}

/* ---- Result cards — dark tinted bg + colored border + white text ---- */
.result-card {
    border-radius: 12px;
    padding: 28px 32px;
    margin-bottom: 8px;
    border-left: 6px solid;
    box-shadow: 0 2px 12px rgba(0,0,0,0.4);
}
.result-card.iadata { background: #0c1e3d; border-color: #3b82f6; }
.result-card.dsi    { background: #0a2218; border-color: #22c55e; }
.result-card.cir    { background: #2c0b0b; border-color: #f87171; }

.result-card .rc-tag {
    font-size: 0.72rem; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; margin-bottom: 8px;
}
.result-card.iadata .rc-tag { color: #93c5fd; }
.result-card.dsi    .rc-tag { color: #86efac; }
.result-card.cir    .rc-tag { color: #fca5a5; }

.result-card .rc-branch { font-size: 2rem; font-weight: 800; color: #f1f5f9; margin-bottom: 4px; }
.result-card .rc-full   { font-size: 0.97rem; color: #94a3b8; }

/* ---- Confidence bars ---- */
.conf-wrap  { margin-bottom: 16px; }
.conf-head  { display: flex; justify-content: space-between; margin-bottom: 6px; }
.conf-name  { font-size: 0.88rem; font-weight: 600; color: #e2e8f0; }
.conf-pct   { font-size: 0.88rem; font-weight: 600; color: #94a3b8; }
.conf-track { background: #1e293b; border-radius: 99px; height: 10px; overflow: hidden; }
.conf-fill  { height: 100%; border-radius: 99px; transition: width 0.6s ease; }

/* ---- Submit button ---- */
div[data-testid="stFormSubmitButton"] > button {
    background: #2563eb;
    color: #ffffff;
    font-size: 1rem;
    font-weight: 700;
    border: none;
    border-radius: 10px;
    padding: 14px 0;
    width: 100%;
    letter-spacing: 0.5px;
    box-shadow: 0 2px 10px rgba(37,99,235,0.4);
}
div[data-testid="stFormSubmitButton"] > button:hover {
    background: #1d4ed8;
    box-shadow: 0 4px 18px rgba(37,99,235,0.55);
}
</style>
""", unsafe_allow_html=True)

# ── Load model & metadata ──────────────────────────────────────────────────────
@st.cache_resource
def load_artifacts():
    model    = joblib.load("CS_students_career_predictor.pkl")
    metadata = joblib.load("model_metadata.pkl")
    return model, metadata

model, metadata = load_artifacts()

GENDER_CLASSES = metadata["gender_classes"]
FEATURE_NAMES  = metadata["feature_names"]
GENDER_MAP     = {name: i for i, name in enumerate(GENDER_CLASSES)}

BRANCH_OPTIONS = ["IADATA", "DSI", "CIR"]

# ── Branch info ────────────────────────────────────────────────────────────────
BRANCH_META = {
    "IADATA": {
        "full":  "Intelligence Artificielle & Data",
        "css":   "iadata",

        "description": (
            "Your academic profile is best suited for the **IADATA** track — "
            "Intelligence Artificielle & Data. You excel in mathematics, "
            "programming, and analytical reasoning. "
            "Typical careers: Data Scientist, Machine Learning Engineer, "
            "NLP Engineer, Computer Vision Engineer, AI Researcher."
        ),
    },
    "DSI": {
        "full":  "Développement des Systèmes d'Information",
        "css":   "dsi",

        "description": (
            "Your academic profile is best suited for the **DSI** track — "
            "Développement des Systèmes d'Information. You have strong skills "
            "in software engineering, databases, and building real-world systems. "
            "Typical careers: Software Engineer, Web Developer, "
            "Database Administrator, DevOps Engineer, Mobile Developer."
        ),
    },
    "CIR": {
        "full":  "Cybersécurité, Infrastructure & Réseaux",
        "css":   "cir",

        "description": (
            "Your academic profile is best suited for the **CIR** track — "
            "Cybersécurité, Infrastructure & Réseaux. You have strengths in "
            "networks, systems administration, and security. "
            "Typical careers: Ethical Hacker, Security Analyst, "
            "Network Administrator, Digital Forensics Specialist."
        ),
    },
}

# ── Course recommendations — loaded from CSV ───────────────────────────────────
@st.cache_data
def load_courses():
    df = pd.read_csv("courses.csv")
    df["title_lower"] = df["title"].str.lower()
    return df

COURSES_DF = load_courses()

# Keywords that map each branch gap to relevant course titles
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

def get_courses_for_gap(predicted, preferred, n=8):
    keywords = GAP_KEYWORDS.get((predicted, preferred), [])
    if not keywords:
        return pd.DataFrame()
    mask = COURSES_DF["title_lower"].str.contains("|".join(keywords), na=False)
    matched = COURSES_DF[mask].copy()
    matched = matched.sort_values("rating", ascending=False)
    return matched.head(n)

# ── CV analyzer helpers ────────────────────────────────────────────────────────
def extract_pdf_text(uploaded_file) -> str:
    reader = PdfReader(io.BytesIO(uploaded_file.read()))
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def analyze_cv(cv_text: str, model: str = "llama3.2") -> str:
    prompt = f"""You are an academic advisor for a Computer Science school that offers three specialization branches:

- IADATA — Intelligence Artificielle & Data (AI, Machine Learning, Deep Learning, Data Science, NLP, Computer Vision)
- DSI — Développement des Systèmes d'Information (Web development, Software engineering, Mobile apps, Databases, DevOps)
- CIR — Cybersécurité, Infrastructure & Réseaux (Networks, Cybersecurity, Systems administration, Infrastructure, Ethical hacking)

Analyze the student CV below. Focus only on their projects and technical skills.

Reply in this exact format:
**Recommended Branch:** <IADATA | DSI | CIR>
**Confidence:** <High | Medium | Low>

**Key evidence from CV:**
- <bullet 1>
- <bullet 2>
- <bullet 3>

**Justification:** <2–3 sentences explaining why this branch fits the student>

**To strengthen another branch, the student should work on:** <one sentence>

---
CV:
{cv_text[:4000]}"""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["response"]

# ── Semester definitions (key → display label) ─────────────────────────────────
SEMESTERS = {
    "S1": {
        "title": "Semestre 1 — 1ère Année AP",
        "modules": [
            ("S1_Francais",      "Français Intermédiaire 1",          1.5),
            ("S1_English",       "Elementary English 1",              1.5),
            ("S1_Analyse",       "Analyse 1",                         2.0),
            ("S1_Algebre",       "Algèbre 1",                         1.5),
            ("S1_CircuitsElect", "Circuits Électroniques 1",          2.0),
            ("S1_CircuitsNumer", "Circuits Numériques 1",             1.5),
            ("S1_Algo",          "Algorithmique 1",                   3.0),
            ("S1_LangProg",      "Langage de Programmation 1",        3.5),
            ("S1_Comptab",       "Comptabilité Générale",             2.0),
            ("S1_OrgEntr",       "Organisation d'Entreprise",         1.5),
            ("S1_MethoTrav",     "Méthodo. Travail Universitaire",    3.0),
        ],
    },
    "S2": {
        "title": "Semestre 2 — 1ère Année AP",
        "modules": [
            ("S2_Francais",      "Français Intermédiaire 2",          1.5),
            ("S2_English",       "Elementary English 2",              1.5),
            ("S2_Analyse",       "Analyse 2",                         2.0),
            ("S2_Algebre",       "Algèbre 2",                         1.5),
            ("S2_Algo",          "Algorithmique 2",                   3.0),
            ("S2_LangProg",      "Langage de Programmation 2",        3.5),
            ("S2_CircuitsElect", "Circuits Électroniques 2",          1.5),
            ("S2_CircuitsNumer", "Circuits Numériques 2",             2.0),
            ("S2_Thermo",        "Thermodynamique",                   1.5),
            ("S2_Electromag",    "Électromagnétisme",                 1.5),
            ("S2_TechRed",       "Techniques de Rédaction",           1.5),
            ("S2_InitIA",        "Initiation à l'IA",                 1.5),
        ],
    },
    "S3": {
        "title": "Semestre 3 — 2ème Année AP",
        "modules": [
            ("S3_Francais",      "Français Avancé 1",                 1.5),
            ("S3_English",       "Pre-Intermediate English 1",        1.5),
            ("S3_Analyse",       "Analyse 3",                         2.0),
            ("S3_Proba",         "Probabilités",                      1.5),
            ("S3_ElecAnalog",    "Électronique Analogique 1",         3.0),
            ("S3_ProgAvSD",      "Prog. Avancée & Struct. Données 1", 3.0),
            ("S3_ConceptionSI",  "Conception SI",                     2.5),
            ("S3_Microproc",     "Microprocesseurs",                  2.0),
            ("S3_SysExploit",    "Systèmes d'Exploitation",           1.5),
            ("S3_Tafatoh",       "Tafatoh (التفتح)",                  3.0),
        ],
    },
    "S4": {
        "title": "Semestre 4 — 2ème Année AP",
        "modules": [
            ("S4_Francais",      "Français Avancé 2",                 1.5),
            ("S4_English",       "Pre-Intermediate English 2",        1.5),
            ("S4_Analyse",       "Analyse 4",                         2.0),
            ("S4_Stats",         "Statistiques Descriptives",         1.5),
            ("S4_ElecAnalog",    "Électronique Analogique 2",         3.0),
            ("S4_ProgAvSD",      "Prog. Avancée & Struct. Données 2", 3.0),
            ("S4_BaseDonnees",   "Bases de Données Relationnelles",   2.0),
            ("S4_DevWeb",        "Développement Web",                 1.5),
            ("S4_AutomatSeq",    "Automatisme Séquentiel",            2.0),
            ("S4_InfoIndust",    "Informatique Industrielle",         1.5),
            ("S4_DevPers",       "Développement Personnel",           3.0),
        ],
    },
    "S5": {
        "title": "Semestre 5 — 3ème Année IIR",
        "modules": [
            ("S5_CommProf",   "Communication Professionnelle 1",  1.5),
            ("S5_English",    "Intermediate English 1",           1.5),
            ("S5_DevNumer",   "Développement Numérique",          1.5),
            ("S5_InfoResp",   "Informatique Responsable",         1.5),
            ("S5_POO",        "POO",                              3.5),
            ("S5_ConcSI",     "Conception SI",                    2.0),
            ("S5_SQL",        "SQL / PL-SQL",                     1.5),
            ("S5_Unix",       "Unix",                             2.0),
            ("S5_Compilation","Compilation",                      1.5),
            ("S5_Reseaux",    "Réseaux Informatiques 1",          3.5),
            ("S5_OutilsDev",  "Outils de Développement 1",        3.0),
        ],
    },
    "S6": {
        "title": "Semestre 6 — 3ème Année IIR",
        "modules": [
            ("S6_CommProf",     "Communication Professionnelle 2", 1.5),
            ("S6_English",      "Intermediate English 2",          1.5),
            ("S6_CompCult",     "Compétences Culturelles",         3.0),
            ("S6_ModelStat",    "Modèles Statistiques",            2.0),
            ("S6_ProgLineaire", "Programmation Linéaire",          1.5),
            ("S6_Java",         "Java",                            2.0),
            ("S6_Python",       "Python & Framework",              1.5),
            ("S6_ConcOO",       "Conception Orientée Objet",       2.0),
            ("S6_SQLServer",    "SQL Server",                      1.5),
            ("S6_RechScient",   "Recherche Scientifique",          2.0),
            ("S6_ProjetInfo",   "Projet Informatique",             1.0),
            ("S6_Reseaux",      "Réseaux Informatiques 2",         3.5),
        ],
    },
    "S7": {
        "title": "Semestre 7 — 4ème Année IIR",
        "modules": [
            ("S7_CommProf",       "Communication Professionnelle 3", 1.5),
            ("S7_English",        "Advanced English 1",              1.5),
            ("S7_IntroIA",        "Intro IA & Éthique",              1.5),
            ("S7_ML",             "Machine Learning",                1.5),
            ("S7_ProgAvancee",    "Programmation Avancée",           3.5),
            ("S7_NoSQL",          "NoSQL",                           1.5),
            ("S7_AdminOracle",    "Administration Oracle 1",         2.0),
            ("S7_DotNet",         "Technologie .NET",                2.0),
            ("S7_DevMobile",      "Développement Mobile",            1.5),
            ("S7_AdminUnix",      "Administration UNIX",             2.0),
            ("S7_Virtualisation", "Virtualisation",                  1.5),
            ("S7_AnalyseDonnees", "Analyse de Données",              1.5),
            ("S7_RechercheOper",  "Recherche Opérationnelle",        1.5),
        ],
    },
}

# ── Hero header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1 style="color:#ffffff;font-size:2.1rem;font-weight:800;margin:0 0 10px;letter-spacing:-0.4px;">
    IIR Branch Predictor
  </h1>
  <p style="color:rgba(255,255,255,0.72);font-size:1rem;margin:0;line-height:1.6;">
    Enter your grades across all 7 semesters and the model will recommend
    the branch that best matches your academic profile —
    <strong style="color:rgba(255,255,255,0.95);">IADATA</strong>,
    <strong style="color:rgba(255,255,255,0.95);">DSI</strong>, or
    <strong style="color:rgba(255,255,255,0.95);">CIR</strong>.
  </p>
</div>
""", unsafe_allow_html=True)

# ── Top-level tabs ────────────────────────────────────────────────────────────
tab_grades, tab_cv = st.tabs(["Grade Predictor", "CV Analyzer"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Grade Predictor
# ══════════════════════════════════════════════════════════════════════════════
with tab_grades:
    with st.form("prediction_form"):

        # Personal Info
        st.markdown('<p class="section-label">Personal Information</p>', unsafe_allow_html=True)
        pi1, pi2, pi3 = st.columns([1, 1, 1])
        with pi1:
            gender = st.selectbox("Gender", options=GENDER_CLASSES, key="gender")
        with pi2:
            age = st.number_input("Age", min_value=17, max_value=35, value=21, step=1, key="age")
        with pi3:
            preferred_branch = st.selectbox(
                "Preferred Branch",
                options=BRANCH_OPTIONS,
                format_func=lambda b: f"{b} — {BRANCH_META[b]['full']}",
                key="preferred_branch",
                help="The branch you are most interested in. Only used for gap analysis.",
            )

        st.markdown('<p class="section-label" style="margin-top:20px;">Module Grades — out of 20</p>', unsafe_allow_html=True)

        tab_labels = [f"S{i}" for i in range(1, 8)]
        tabs = st.tabs(tab_labels)
        grade_inputs: dict[str, float] = {}

        for tab_obj, (sem_key, sem_info) in zip(tabs, SEMESTERS.items()):
            with tab_obj:
                st.caption(sem_info["title"])
                modules = sem_info["modules"]
                mid = (len(modules) + 1) // 2
                col_left, col_right = st.columns(2)
                for idx, (feat_key, label, coef) in enumerate(modules):
                    col = col_left if idx < mid else col_right
                    with col:
                        grade_inputs[feat_key] = st.number_input(
                            f"{label}  *(coef {coef})*",
                            min_value=0.0,
                            max_value=20.0,
                            value=12.0,
                            step=0.25,
                            key=feat_key,
                        )

        st.markdown("")
        submitted = st.form_submit_button(
            "Predict My Branch",
            use_container_width=True,
            type="primary",
        )

    # ── Prediction ────────────────────────────────────────────────────────────
    if submitted:
        feature_values = {"Gender": GENDER_MAP[gender], "Age": age}
        feature_values.update(grade_inputs)
        features = np.array([[feature_values[f] for f in FEATURE_NAMES]])

        prediction    = model.predict(features)[0]
        probabilities = model.predict_proba(features)[0].astype(float)
        classes       = list(model.classes_)

        meta    = BRANCH_META[prediction]
        css_cls = meta["css"]

        st.markdown("---")
        st.markdown(
            f"""
            <div class="result-card {css_cls}">
              <div class="rc-tag">Recommended Branch</div>
              <div class="rc-branch">{prediction}</div>
              <div class="rc-full">{meta['full']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(meta["description"])

        st.markdown("---")
        st.markdown("#### Model Confidence")
        sorted_preds = sorted(zip(classes, probabilities), key=lambda x: -x[1])
        bar_colors = {"IADATA": "#2563eb", "DSI": "#16a34a", "CIR": "#dc2626"}
        for branch, prob in sorted_preds:
            pct = prob * 100
            color = bar_colors.get(branch, "#64748b")
            st.markdown(
                f"""
                <div class="conf-wrap">
                  <div class="conf-head">
                    <span class="conf-name">{branch}</span>
                    <span class="conf-pct">{pct:.1f}%</span>
                  </div>
                  <div class="conf-track">
                    <div class="conf-fill" style="width:{pct:.1f}%; background:{color};"></div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        if prediction == preferred_branch:
            st.success(
                f"**Perfect Match!**  \n"
                f"Your academic profile already aligns with **{preferred_branch} — "
                f"{BRANCH_META[preferred_branch]['full']}**. Keep it up!"
            )
        else:
            st.warning(
                f"**Gap Analysis**  \n"
                f"Your grades point toward **{prediction}**, but your preferred branch is "
                f"**{preferred_branch}**. Here are the courses we recommend to bridge that gap:"
            )
            courses = get_courses_for_gap(prediction, preferred_branch)
            if not courses.empty:
                udemy_base = "https://www.udemy.com"
                for i, row in enumerate(courses.itertuples(), start=1):
                    course_url = udemy_base + row.url if str(row.url).startswith("/") else row.url
                    with st.expander(f"{i}.  {row.title}"):
                        col_img, col_info = st.columns([1, 3])
                        with col_img:
                            st.image(row.image, use_container_width=True)
                        with col_info:
                            st.markdown(f"**Rating:** {row.rating:.2f} ⭐  |  **Reviews:** {int(row.num_reviews):,}  |  **Duration:** {row.duration}")
                            st.markdown(f"**Lectures:** {int(row.num_published_lectures)}  |  **Last updated:** {str(row.last_update_date)[:10]}")
                            st.markdown(f"[Open on Udemy]({course_url})", unsafe_allow_html=False)
            else:
                st.info("No matching courses found in the catalogue.")

        for tmp in ("_temp_cols.json", "_temp_cols2.json",
                    "_temp_info.json", "_temp_indexed_cols.json"):
            if os.path.exists(tmp):
                os.remove(tmp)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — CV Analyzer
# ══════════════════════════════════════════════════════════════════════════════
with tab_cv:
    st.markdown('<p class="section-label">CV / Resume Analyzer — powered by Ollama (local AI)</p>', unsafe_allow_html=True)
    st.write(
        "Upload your CV as a PDF. The analyzer reads your **projects and skills** "
        "and recommends the best branch — runs **100% locally**, no API key needed."
    )

    ollama_model = st.selectbox(
        "Ollama model",
        options=["llama3.2", "mistral", "gemma2", "llama3.1"],
        help="Must be pulled first: e.g. `ollama pull llama3.2`",
    )
    uploaded_cv = st.file_uploader("Upload CV (PDF)", type=["pdf"])

    if st.button("Analyze CV", type="primary", use_container_width=True):
        if uploaded_cv is None:
            st.error("Please upload a PDF file.")
        else:
            with st.spinner(f"Analyzing with {ollama_model} — this may take 20–60 seconds..."):
                try:
                    cv_text = extract_pdf_text(uploaded_cv)
                    if not cv_text.strip():
                        st.error("Could not extract text from this PDF. Make sure it is not a scanned image.")
                    else:
                        result = analyze_cv(cv_text, ollama_model)
                        st.markdown("---")
                        st.markdown("### Analysis Result")
                        st.markdown(result)
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to Ollama. Make sure it is running (`ollama serve`) and the model is pulled (`ollama pull llama3.2`).")
                except Exception as e:
                    st.error(f"Error: {e}")
