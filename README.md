# AI Healthcare Chatbot

A full-stack AI-powered healthcare chatbot with user authentication, BMI calculator, and personalized health assistance. The chatbot accepts symptoms in natural language, predicts the most likely illness using a trained ML model, and provides conversational responses with remedies, medications, severity assessment, and specialist recommendations.

## 🚀 Features

### 🔐 User Authentication
- **Register**: Create account with name, email, password
- **Login**: Secure JWT-based authentication
- **Protected routes**: Only logged-in users can access chatbot features

### 💬 Smart Chatbot
- **Natural language input**: Describe symptoms in plain English
- **ML-powered diagnosis**: Disease prediction with confidence scores
- **Smart follow-up questions**: "Since how many days?", "Any other symptoms?"
- **Emergency detection**: Detects serious keywords (chest pain, breathing difficulty)
- **Severity-based suggestions**:
  - 🏠 **Low** → Home remedies
  - ⚠️ **Medium** → Precautions + tips
  - 🏥 **High** → Doctor consultation

### 📊 Chat History
- Save all user messages and chatbot replies
- Browse previous conversations
- Personalized responses based on past data

### ⚖️ BMI Calculator
- Enter height (cm) and weight (kg)
- Get BMI value with category (underweight/normal/overweight/obese)
- Fun motivational messages 😄💪
- Health suggestions based on category
- **BMI History**: Track progress over time
- **Compare**: Old vs new BMI with trend analysis

### 🧠 Personalization
- User-specific health history
- Similar past symptoms detection
- Smarter suggestions based on patterns

## Architecture

```
User: "I have a headache and fever"
        │
        ▼
  Auth Check (JWT) ──► Verified User
        │
        ▼
  Symptom Parser (LLM) ──► ["headache", "high_fever"]
        │
        ▼
  ML Predictor (RandomForest) ──► {disease: "Common Cold", confidence: 87%}
        │
        ├──► Severity Service ──► {level: "mild", score: 0.3}
        ├──► Emergency Detection ──► Check for serious keywords
        │
        ▼
  LLM Response Generator ──► Empathetic explanation + remedies + specialist
        │
        ▼
  Chat UI with diagnosis card + severity suggestions
```

**Hybrid AI approach**: scikit-learn RandomForest handles disease classification (deterministic, fast, no hallucination). LLM handles natural language understanding (symptom extraction) and response generation (explanations, remedies, conversation).

## Tech Stack

- **Backend**: Python, FastAPI
- **ML**: scikit-learn RandomForestClassifier (41 diseases, 110 symptoms)
- **LLM**: OpenRouter API (Qwen3/Gemma free tier) with model fallback chain
- **Database**: SQLite + SQLAlchemy
- **Authentication**: JWT + bcrypt password hashing
- **Frontend**: Vanilla HTML/CSS/JS

## Setup

### Prerequisites

- Python 3.10+
- An [OpenRouter](https://openrouter.ai) API key (free)

### Installation

```bash
# Clone
git clone git@github.com:Sufail07/Healthcare-Chatbot.git
cd Healthcare-Chatbot

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OpenRouter API key

# Train the ML model
python scripts/train_model.py

# Start the server
uvicorn app.main:app --reload
```

Open http://localhost:8000 in your browser.

## Project Structure

```
app/
├── main.py                  # FastAPI entry point
├── config.py                # Settings (loads .env)
├── database.py              # SQLAlchemy setup (SQLite)
├── routers/
│   ├── auth.py              # POST /api/auth/register, /api/auth/login
│   ├── chat.py              # POST /api/chat, /api/chat/new
│   ├── bmi.py               # POST /api/bmi/calculate, GET /api/bmi/history
│   ├── diagnosis.py         # POST /api/diagnose
│   └── history.py           # GET/DELETE /api/history
├── services/
│   ├── auth_service.py      # JWT token, password hashing
│   ├── bmi_service.py       # BMI calculation, comparison
│   ├── diagnosis_service.py # Orchestrator: ML + severity + LLM + emergency
│   ├── ml_service.py        # Model loading and prediction
│   ├── llm_service.py       # LLM API calls with retry + fallback
│   ├── symptom_parser.py    # LLM symptom extraction from text
│   └── severity_service.py  # Weighted severity scoring
├── ml/
│   ├── preprocessor.py      # CSV → binary feature matrix
│   ├── train.py             # Trains RandomForestClassifier
│   └── predictor.py         # Symptom vector → top-3 diseases
├── models/
│   ├── schemas.py           # Pydantic request/response models
│   └── db_models.py         # SQLAlchemy ORM models (User, BMI, Disease)
├── static/
│   ├── css/                 # styles.css, auth.css, bmi.css
│   └── js/                  # chat.js
└── templates/
    ├── index.html           # Chat UI
    ├── login.html           # Login page
    ├── register.html        # Register page
    └── bmi.html             # BMI Calculator page
```

## API Endpoints

### Authentication
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/auth/register` | Create new account |
| POST | `/api/auth/login` | Login, get JWT token |
| GET | `/api/auth/me` | Get current user profile |

### Chat (Requires Auth)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Chat UI |
| POST | `/api/chat/new` | Create new conversation |
| POST | `/api/chat` | Send message, get diagnosis |

### BMI (Requires Auth)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/bmi` | BMI Calculator UI |
| POST | `/api/bmi/calculate` | Calculate and save BMI |
| GET | `/api/bmi/history` | Get BMI history with comparison |
| GET | `/api/bmi/latest` | Get most recent BMI |
| DELETE | `/api/bmi/{id}` | Delete BMI record |

### History (Requires Auth)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/history` | List user's conversations |
| GET | `/api/history/{id}` | Get conversation messages |
| DELETE | `/api/history/{id}` | Delete conversation |

### Other
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/diagnose` | Direct symptom list → diagnosis |

## Running Tests

```bash
python -m pytest tests/ -v
```

## Security

- Passwords are hashed using bcrypt
- JWT tokens for stateless authentication
- Protected routes require valid Bearer token
- User data is isolated per account

## Disclaimer

This chatbot is for **informational purposes only**. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional.
