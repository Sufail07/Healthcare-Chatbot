# AI Healthcare Chatbot

A full-stack AI-powered healthcare chatbot that accepts symptoms in natural language, predicts the most likely illness using a trained ML model, and provides conversational responses with remedies, medications, severity assessment, and specialist recommendations.

## Architecture

```
User: "I have a headache and fever"
        │
        ▼
  Symptom Parser (LLM) ──► ["headache", "high_fever"]
        │
        ▼
  ML Predictor (RandomForest) ──► {disease: "Common Cold", confidence: 87%}
        │
        ├──► Severity Service ──► {level: "mild", score: 0.3}
        │
        ▼
  LLM Response Generator ──► Empathetic explanation + remedies + specialist
        │
        ▼
  Chat UI with diagnosis card
```

**Hybrid AI approach**: scikit-learn RandomForest handles disease classification (deterministic, fast, no hallucination). LLM handles natural language understanding (symptom extraction) and response generation (explanations, remedies, conversation).

## Tech Stack

- **Backend**: Python, FastAPI
- **ML**: scikit-learn RandomForestClassifier (41 diseases, 110 symptoms)
- **LLM**: OpenRouter API (Qwen3/Gemma free tier) with model fallback chain
- **Database**: SQLite + SQLAlchemy
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
│   ├── chat.py              # POST /api/chat, /api/chat/new
│   ├── diagnosis.py         # POST /api/diagnose
│   └── history.py           # GET/DELETE /api/history
├── services/
│   ├── diagnosis_service.py # Orchestrator: ML + severity + LLM
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
│   └── db_models.py         # SQLAlchemy ORM models
├── static/                  # CSS + JS
└── templates/               # Chat UI HTML
```

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Chat UI |
| POST | `/api/chat/new` | Create new conversation |
| POST | `/api/chat` | Send message, get diagnosis |
| POST | `/api/diagnose` | Direct symptom list → diagnosis |
| GET | `/api/history` | List conversations |
| GET | `/api/history/{id}` | Get conversation messages |
| DELETE | `/api/history/{id}` | Delete conversation |

## Features

- Symptom extraction from natural language via LLM
- ML-based disease prediction with confidence scores (top 3)
- Severity assessment with color-coded badges (mild/moderate/severe/emergency)
- Conversational follow-ups (specialist recommendations, medication questions)
- Chat history with sidebar navigation
- Template-based fallback when LLM API is unavailable
- Model fallback chain across multiple free LLM providers
- Responsive UI with mobile sidebar

## Running Tests

```bash
python -m pytest tests/ -v
```

## Disclaimer

This chatbot is for **informational purposes only**. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional.
