# 🎓 CS Student Career Predictor

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.0%2B-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A machine learning-powered web application that predicts career paths for Computer Science students based on their academic performance, skills, and personal attributes. Built with Streamlit and scikit-learn.

## 🌟 Features

- **Intelligent Prediction**: Uses Gradient Boosting Classifier to predict career branches (AI, Cyber Security, Development)
- **Interactive Web App**: Clean, user-friendly interface built with Streamlit
- **Data-Driven Insights**: Based on comprehensive student data analysis
- **Real-time Results**: Instant predictions with detailed explanations
- **Career Guidance**: Provides specific career recommendations for each branch

## 📋 What the App Does

This application helps Computer Science students understand their potential career trajectories by analyzing their:

- Academic scores and performance
- Technical skills and competencies
- Project experience and internships
- Personal attributes and interests

The model predicts one of three main career branches:
- 🤖 **AI**: Data Science, Machine Learning, Computer Vision, NLP
- 🔒 **Cyber Security**: Ethical Hacking, Security Analysis, Digital Forensics
- 💻 **Development**: Software Engineering, Web Development, DevOps

## 🚀 Installation & Setup

Follow these steps to run the application locally:

### Prerequisites

- Python 3.8 or higher
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/Hassanezz11/prediction-path.git
cd prediction-path
```

### Step 2: Create Virtual Environment

```bash
# On Windows
python -m venv myenv
myenv\Scripts\activate

# On macOS/Linux
# python -m venv myenv
# source myenv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist, install these packages manually:

```bash
pip install streamlit pandas numpy scikit-learn joblib
```

### Step 4: Train the Model (Optional)

If you want to retrain the model with the latest data:

```bash
python train.py
```

This will generate the model files (`CS_students_career_predictor.pkl` and `model_metadata.pkl`).

### Step 5: Run the Application

```bash
streamlit run app.py
.\myenv\Scripts\python.exe -m streamlit run app.py
```

The app will open in your default web browser at `http://localhost:8501`.

## 📊 Dataset

The application uses `cs_students_IIR_modules.xlsx` containing anonymized student data with features like:
- Academic scores
- Technical skills ratings
- Project experience
- Internship history
- Personal attributes

## 🛠️ Technologies Used

- **Streamlit**: Web application framework
- **scikit-learn**: Machine learning algorithms
- **pandas**: Data manipulation and analysis
- **NumPy**: Numerical computations
- **joblib**: Model serialization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

For questions or suggestions, please open an issue on GitHub.

---

*Empowering CS students to make informed career decisions through data-driven insights!* 🚀

