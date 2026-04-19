"""Tests for the Flask web frontend and agentic model selection."""
import sys
from pathlib import Path

import pytest

# Add project root to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.webapp import create_app


SIMPLE_CODE = """
def add(a, b):
    return a + b
"""


COMPLEX_CODE = """
import pickle
import sqlite3


class ReportBuilder:
    def build(self, user_id, role, token):
        query = "SELECT * FROM users WHERE id = '" + user_id + "' AND role = '" + role + "'"
        if role == "admin":
            for _ in range(3):
                try:
                    if token:
                        pickle.loads(token)
                        return query
                except Exception:
                    pass
        return query
"""


@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


def test_recommend_model_prefers_svm_for_simple_code(client):
    response = client.post(
        "/api/recommend-model",
        json={"code": SIMPLE_CODE, "filename": "simple.py"},
    )

    assert response.status_code == 200
    payload = response.get_json()

    assert payload["recommended_model"] == "svm"
    assert payload["confidence"] >= 0.55
    assert payload["agentic_actions"]


def test_recommend_model_prefers_randomforest_for_complex_code(client):
    response = client.post(
        "/api/recommend-model",
        json={"code": COMPLEX_CODE, "filename": "complex.py"},
    )

    assert response.status_code == 200
    payload = response.get_json()

    assert payload["recommended_model"] == "randomforest"
    assert payload["feature_snapshot"]["security_signals"] >= 2


def test_analyze_code_auto_mode_returns_selected_model(client):
    response = client.post(
        "/api/analyze/code",
        json={
            "code": SIMPLE_CODE,
            "filename": "simple.py",
            "model_name": "auto",
            "use_ml": False,
            "min_confidence": 0.0,
        },
    )

    assert response.status_code == 200
    payload = response.get_json()

    assert payload["selected_model"] == "svm"
    assert payload["model_recommendation"]["recommended_model"] == "svm"
    assert payload["summary"]["files_analyzed"] == 1
    assert "severity_breakdown" in payload


def test_analyze_code_can_return_fixed_code(client):
    insecure = "password = 'secret'\nprint(password)"
    response = client.post(
        "/api/analyze/code",
        json={
            "code": insecure,
            "filename": "inline.py",
            "model_name": "auto",
            "use_ml": False,
            "apply_fixes": True,
            "min_confidence": 0.0,
            "min_severity": "LOW",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert "fixed_code" in payload
    assert isinstance(payload["fixed_code"], str)