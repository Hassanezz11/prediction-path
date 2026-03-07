import streamlit as st
import joblib
import numpy as np

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CS Career Predictor",
    page_icon=":mortar_board:",
    layout="centered",
)

# ── Load model & metadata ─────────────────────────────────────────────────────
@st.cache_resource
def load_artifacts():
    model    = joblib.load("CS_students_career_predictor.pkl")
    metadata = joblib.load("model_metadata.pkl")
    return model, metadata

model, metadata = load_artifacts()

GENDER_CLASSES = metadata["gender_classes"]   # ['Female', 'Male']
FEATURE_NAMES  = metadata["feature_names"]    # exact order the model expects

GENDER_MAP = {name: i for i, name in enumerate(GENDER_CLASSES)}

BRANCH_OPTIONS = ["AI", "Cyber Security", "Development"]

BRANCH_INFO = {
    "AI": {
        "description": (
            "Your academic profile fits the **Artificial Intelligence** track. "
            "You excel in mathematics, data, and analytical thinking. "
            "Typical careers: Data Scientist, ML Engineer, Computer Vision Engineer, NLP Engineer."
        ),
    },
    "Cyber Security": {
        "description": (
            "Your academic profile fits the **Cyber Security** track. "
            "You have strengths in networks, systems, and security-oriented thinking. "
            "Typical careers: Ethical Hacker, Security Analyst, Digital Forensics Specialist."
        ),
    },
    "Development": {
        "description": (
            "Your academic profile fits the **Development** track. "
            "You are strong in software engineering, tools, and building real applications. "
            "Typical careers: Software Engineer, Web Developer, Mobile App Developer, DevOps Engineer."
        ),
    },
}

# list of recommended courses
COURSE_RECOMMENDATIONS = {
    ("AI", "Development"): [
        ("Web Development", "Master HTML, CSS, and JavaScript, then a framework like React or Vue."),
        ("Backend Development", "Learn Node.js, Django, or Spring Boot to build server-side systems."),
        ("Databases & SQL", "Strengthen your relational DB skills — PostgreSQL, MySQL, and ORM tools."),
        ("Software Design Patterns", "Study SOLID principles, MVC, and common design patterns."),
        ("DevOps & CI/CD", "Learn Docker, GitHub Actions, and cloud deployment basics."),
        ("Mobile App Development", "Pick up Flutter or React Native to build cross-platform apps."),
        ("Version Control & Agile", "Deepen Git workflow knowledge and practice Agile/Scrum methods."),
    ],
    ("AI", "Cyber Security"): [
        ("Network Security Fundamentals", "Study TCP/IP, firewalls, VPNs, and intrusion detection systems."),
        ("Ethical Hacking & Penetration Testing", "Practice with tools like Metasploit, Burp Suite, and Nmap."),
        ("Cryptography & PKI", "Learn symmetric/asymmetric encryption, hashing, and certificates."),
        ("Linux System Administration", "Get comfortable with Linux CLI, permissions, and scripting."),
        ("OWASP Top 10 & Web Security", "Understand the most critical web vulnerabilities and how to fix them."),
        ("Digital Forensics", "Learn evidence collection, memory analysis, and log investigation."),
        ("Security Certifications", "Target CompTIA Security+, CEH, or eJPT as starting points."),
    ],
    ("Development", "AI"): [
        ("Linear Algebra & Probability", "Revise vectors, matrices, eigenvalues, and probability distributions."),
        ("Python for Data Science", "Master NumPy, Pandas, and Matplotlib for data manipulation."),
        ("Machine Learning (Scikit-learn)", "Learn supervised & unsupervised ML algorithms with hands-on projects."),
        ("Deep Learning", "Study neural networks with TensorFlow or PyTorch."),
        ("Statistics & Statistical Modeling", "Focus on hypothesis testing, regression, and Bayesian thinking."),
        ("Natural Language Processing", "Explore text processing, transformers, and Hugging Face."),
        ("Data Visualization", "Build dashboards with Plotly, Seaborn, or Tableau."),
    ],
    ("Development", "Cyber Security"): [
        ("Network Protocols & Architecture", "Study OSI model, TCP/IP stack, DNS, HTTP/S, and routing."),
        ("Ethical Hacking & Penetration Testing", "Practice CTF challenges and use tools like Kali Linux."),
        ("Cryptography", "Learn encryption algorithms, TLS/SSL, and secure coding practices."),
        ("Linux & Bash Scripting", "Automate security tasks and get fluent in the Linux environment."),
        ("OWASP Top 10 & Web Security", "Understand SQL injection, XSS, CSRF, and secure coding."),
        ("Incident Response & Forensics", "Learn how to detect, contain, and investigate security incidents."),
        ("Security Certifications", "Aim for CompTIA Security+, CEH, or OSCP."),
    ],
    ("Cyber Security", "AI"): [
        ("Linear Algebra & Statistics", "Build the math foundation: vectors, matrices, probability, distributions."),
        ("Python for Machine Learning", "Learn ML-focused Python — NumPy, Pandas, Scikit-learn."),
        ("Machine Learning Fundamentals", "Study classification, regression, clustering, and model evaluation."),
        ("Deep Learning & Neural Networks", "Explore CNNs, RNNs, and transformers using PyTorch or TensorFlow."),
        ("Data Analysis & Visualization", "Practice EDA, data cleaning, and storytelling with data."),
        ("Research Methods in AI", "Learn to read papers, reproduce experiments, and benchmark models."),
        ("Big Data Processing", "Get familiar with Spark, Hadoop, or cloud data platforms."),
    ],
    ("Cyber Security", "Development"): [
        ("Software Engineering Principles", "Study clean code, SOLID, design patterns, and architecture."),
        ("Web Development (Full Stack)", "Learn HTML/CSS/JS on the front end and a framework on the back end."),
        ("Database Design & SQL", "Practice schema design, query optimization, and ORM usage."),
        ("Object-Oriented Programming", "Deepen OOP skills in Python, Java, or C++."),
        ("API Design & REST Services", "Build and consume RESTful APIs; study OpenAPI/Swagger."),
        ("Cloud Computing", "Get started with AWS, Azure, or GCP — focus on deployment and storage."),
        ("Agile Development", "Practice Scrum and Kanban; use tools like Jira or Trello."),
    ],
}

# ── UI ────────────────────────────────────────────────────────────────────────
st.title("CS Student Branch Predictor")
st.markdown(
    "Enter your academic grades and the model will predict the best branch for you. "
    "If your prediction differs from your preferred branch, you will receive tailored course recommendations."
)
st.divider()

with st.form("prediction_form"):
    tab1, tab2, tab3 = st.tabs(["Personal Info", "Semester 5 Grades", "Semester 6 Grades"])

    # ── Tab 1: Personal Info ──────────────────────────────────────────────────
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            gender  = st.selectbox("Gender", options=GENDER_CLASSES, key="gender")
            age     = st.number_input("Age", min_value=18, max_value=50, value=21, step=1, key="age")
        with col2:
            note_20 = st.number_input("Overall Grade (/20)", min_value=0.0,
                                      max_value=20.0, value=15.0, step=0.5, key="note_20")
            preferred_branch = st.selectbox(
                "Preferred Branch",
                options=BRANCH_OPTIONS,
                key="preferred_branch",
                help="The branch you are most interested in pursuing.",
            )

    # ── Tab 2: Semester 5 ─────────────────────────────────────────────────────
    with tab2:
        st.caption("Enter your group averages for Semester 5 (out of 20)")
        c1, c2 = st.columns(2)
        with c1:
            moy_langues1   = st.number_input("Languages Average — S5",        0.0, 20.0, 13.0, 0.5, key="moy_langues1")
            moy_compnum    = st.number_input("Computer Skills Average",        0.0, 20.0, 13.0, 0.5, key="moy_compnum")
            moy_poo        = st.number_input("OOP Average",                    0.0, 20.0, 12.0, 0.5, key="moy_poo")
            moy_si_bd1     = st.number_input("Info Systems & DB Average — S5", 0.0, 20.0, 13.0, 0.5, key="moy_si_bd1")
        with c2:
            moy_progsys1   = st.number_input("System Programming Average",     0.0, 20.0, 12.0, 0.5, key="moy_progsys1")
            moy_reseaux1   = st.number_input("Networks Average — S5",          0.0, 20.0, 13.0, 0.5, key="moy_reseaux1")
            moy_outilsdev1 = st.number_input("Dev Tools Average — S5",         0.0, 20.0, 13.0, 0.5, key="moy_outilsdev1")

    # ── Tab 3: Semester 6 ─────────────────────────────────────────────────────
    with tab3:
        st.caption("Enter your group averages for Semester 6 (out of 20)")
        c1, c2 = st.columns(2)
        with c1:
            java            = st.number_input("Java Grade",                    0.0, 20.0, 12.0, 0.5, key="java")
            python          = st.number_input("Python Grade",                  0.0, 20.0, 14.0, 0.5, key="python")
            moy_langues2    = st.number_input("Languages Average — S6",        0.0, 20.0, 13.0, 0.5, key="moy_langues2")
            moy_compcult    = st.number_input("Cultural Competencies Avg",     0.0, 20.0, 13.0, 0.5, key="moy_compcult")
            moy_mathsappliq = st.number_input("Applied Maths Average",         0.0, 20.0, 13.0, 0.5, key="moy_mathsappliq")
        with c2:
            moy_outilsdev2  = st.number_input("Dev Tools Average — S6",        0.0, 20.0, 13.0, 0.5, key="moy_outilsdev2")
            moy_si_bd2      = st.number_input("Info Systems & DB Average — S6",0.0, 20.0, 13.0, 0.5, key="moy_si_bd2")
            moy_approchesci = st.number_input("Scientific Approach Avg",       0.0, 20.0, 13.0, 0.5, key="moy_approchesci")
            moy_reseaux2    = st.number_input("Networks Average — S6",         0.0, 20.0, 13.0, 0.5, key="moy_reseaux2")

        st.divider()
        submitted = st.form_submit_button(
            "Predict My Branch", use_container_width=True, type="primary"
        )

# ── Prediction ────────────────────────────────────────────────────────────────
if submitted:
    values = {
        "Gender":           GENDER_MAP[gender],
        "Age":              age,
        "Note_20":          note_20,
        "Moy_Langues1":     moy_langues1,
        "Moy_CompNum":      moy_compnum,
        "Moy_POO":          moy_poo,
        "Moy_SI_BD1":       moy_si_bd1,
        "Moy_ProgSys1":     moy_progsys1,
        "Moy_Reseaux1":     moy_reseaux1,
        "Moy_OutilsDev1":   moy_outilsdev1,
        "Java":             java,
        "Python":           python,
        "Moy_Langues2":     moy_langues2,
        "Moy_CompCult":     moy_compcult,
        "Moy_MathsAppliq":  moy_mathsappliq,
        "Moy_OutilsDev2":   moy_outilsdev2,
        "Moy_SI_BD2":       moy_si_bd2,
        "Moy_ApprocheSci":  moy_approchesci,
        "Moy_Reseaux2":     moy_reseaux2,
    }

    features = np.array([[values[f] for f in FEATURE_NAMES]])

    prediction    = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0].copy().astype(float)
    classes       = model.classes_

    # ── Networks excellence: probability floor for Cyber Security ────────────
    # A multiplicative boost fails when the base probability is tiny.
    # Instead, enforce a minimum probability floor that scales with Networks avg:
    #   avg 14 -> 0 % floor  |  avg 17 -> 45 % floor  |  avg 20 -> 90 % floor
    avg_networks = (moy_reseaux1 + moy_reseaux2) / 2
    if avg_networks > 14.0:
        cyber_idx = list(classes).index("Cyber Security")
        min_cyber = (avg_networks - 14.0) / 6.0 * 0.9
        if probabilities[cyber_idx] < min_cyber:
            remaining = 1.0 - min_cyber
            other_sum = sum(probabilities[i] for i in range(len(classes)) if i != cyber_idx)
            for i in range(len(classes)):
                if i != cyber_idx:
                    probabilities[i] = probabilities[i] / other_sum * remaining
            probabilities[cyber_idx] = min_cyber
        prediction = classes[int(np.argmax(probabilities))]

    info = BRANCH_INFO[prediction]

    st.divider()

    # ── Prediction result ─────────────────────────────────────────────────────
    st.success(f"### Recommended Branch: **{prediction}**")
    st.markdown(info["description"])

    st.divider()
    st.markdown("#### Model Confidence per Branch")
    for branch, prob in sorted(zip(classes, probabilities), key=lambda x: -x[1]):
        st.progress(float(prob), text=f"{branch}  —  {prob*100:.1f}%")

    # ── Preferred branch comparison ───────────────────────────────────────────
    st.divider()

    if prediction == preferred_branch:
        st.success(
            f"### Perfect Match\n"
            f"Your grades already align with your preferred branch — **{preferred_branch}**. "
            f"Keep it up and focus on deepening your skills in this area."
        )
    else:
        st.warning(
            f"### Preferred Branch: {preferred_branch}\n"
            f"Your grades currently point toward **{prediction}**, but you want to go into "
            f"**{preferred_branch}**. Here are the courses we recommend to bridge that gap:"
        )

        courses = COURSE_RECOMMENDATIONS.get((prediction, preferred_branch), [])
        if courses:
            for i, (title, desc) in enumerate(courses, start=1):
                with st.expander(f"{i}. {title}"):
                    st.markdown(desc)
