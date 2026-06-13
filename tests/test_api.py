"""
Unit tests for the FastAPI backend endpoint contracts.

Run: pytest tests/test_api.py -v

NOTE: this assumes a FastAPI app instance importable as `app` from your
backend module (e.g. `from main import app` or `from app.main import app`).
Adjust the import below to match your actual entrypoint. If endpoints hit
AWS services (Redshift, S3) directly, mock those clients so tests run
without live AWS credentials.
"""

import pytest
from fastapi.testclient import TestClient

# Adjust this import to your actual FastAPI app location, e.g.:
#   from main import app
#   from app.main import app
from main import app  # noqa: E402

client = TestClient(app)


# ── /health ────────────────────────────────────────────────────────────────────

def test_health_endpoint_returns_200():
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_endpoint_has_expected_keys():
    resp = client.get("/health")
    body = resp.json()
    assert "status" in body
    assert "models_loaded" in body


# ── /metrics/overview ─────────────────────────────────────────────────────────

def test_overview_endpoint_returns_200():
    resp = client.get("/metrics/overview")
    assert resp.status_code == 200


def test_overview_endpoint_has_expected_fields():
    resp = client.get("/metrics/overview")
    body = resp.json()
    expected_fields = {"dau", "mau", "avg_session_secs", "high_churn_count"}
    assert expected_fields.issubset(body.keys())


def test_overview_numeric_fields_are_non_negative():
    resp = client.get("/metrics/overview")
    body = resp.json()
    for field in ("dau", "mau", "avg_session_secs", "high_churn_count"):
        assert body[field] is None or body[field] >= 0


# ── /metrics/dau ───────────────────────────────────────────────────────────────

def test_dau_endpoint_respects_days_param():
    resp = client.get("/metrics/dau?days=8")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) <= 8


def test_dau_rows_have_expected_shape():
    resp = client.get("/metrics/dau?days=8")
    body = resp.json()
    if body:
        row = body[0]
        for key in ("event_date", "dau", "total_events", "total_sessions"):
            assert key in row


# ── /metrics/segments ─────────────────────────────────────────────────────────

def test_segments_endpoint_returns_list():
    resp = client.get("/metrics/segments")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_segments_percentages_are_plausible():
    """Segment percentages should each be between 0 and 100."""
    resp = client.get("/metrics/segments")
    for seg in resp.json():
        assert 0 <= seg.get("pct", 0) <= 100


# ── /users/at-risk ───────────────────────────────────────────────────────────────

def test_at_risk_endpoint_respects_limit():
    resp = client.get("/users/at-risk?limit=30")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) <= 30


def test_at_risk_churn_scores_in_valid_range():
    resp = client.get("/users/at-risk?limit=30")
    for user in resp.json():
        score = user.get("churn_score")
        if score is not None:
            assert 0.0 <= score <= 1.0


def test_at_risk_churn_risk_is_valid_category():
    resp = client.get("/users/at-risk?limit=30")
    valid = {"high", "medium", "low"}
    for user in resp.json():
        risk = user.get("churn_risk")
        if risk is not None:
            assert risk in valid


# ── Error handling ─────────────────────────────────────────────────────────────

def test_unknown_endpoint_returns_404():
    resp = client.get("/this/does/not/exist")
    assert resp.status_code == 404


def test_at_risk_invalid_limit_does_not_500():
    """Negative/invalid limit should not crash the server with a 500."""
    resp = client.get("/users/at-risk?limit=-1")
    assert resp.status_code != 500
