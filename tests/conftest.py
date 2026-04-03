"""Shared test fixtures."""

import os
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Override env before importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./db/test_chatbot.db"
os.environ["DEEPSEEK_API_KEY"] = "sk-test-fake-key"
os.environ["DEEPSEEK_BASE_URL"] = "https://api.deepseek.com"
os.environ["DEEPSEEK_MODEL"] = "deepseek-reasoner"

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402


test_engine = create_engine(
    "sqlite:///./db/test_chatbot.db",
    connect_args={"check_same_thread": False},
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def mock_openai():
    """Mock DeepSeek R1 API calls."""
    mock_response = AsyncMock()
    mock_response.choices = [
        AsyncMock(message=AsyncMock(content='["headache", "high_fever"]'))
    ]

    mock_diagnosis_response = AsyncMock()
    mock_diagnosis_response.choices = [
        AsyncMock(message=AsyncMock(content=(
            "Based on your symptoms, this could be a **Common Cold**.\n\n"
            "**Recommendations:**\n"
            "- Rest and stay hydrated\n"
            "- Take over-the-counter pain relievers\n\n"
            "REMEDIES: Rest | Stay hydrated | Warm fluids\n"
            "MEDICATIONS: Acetaminophen | Ibuprofen\n"
            "SPECIALIST: General Practitioner"
        )))
    ]

    with patch("app.services.symptom_parser._get_client") as mock_parser_client, \
         patch("app.services.llm_service._get_client") as mock_llm_client:

        parser_instance = AsyncMock()
        parser_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_parser_client.return_value = parser_instance

        llm_instance = AsyncMock()
        llm_instance.chat.completions.create = AsyncMock(return_value=mock_diagnosis_response)
        mock_llm_client.return_value = llm_instance

        yield {
            "parser": parser_instance,
            "llm": llm_instance,
        }
