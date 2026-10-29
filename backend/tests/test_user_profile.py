"""
User Profile Tests - persona profile endpoints

Covers GET/POST /api/v1/user/profile. Authentication is replaced with a
fake decoded token so these tests don't need a real Firebase login.
"""

import uuid

import pytest
from app import app
from authentication.auth_service import verify_token
from config.database import get_db
from fastapi.testclient import TestClient
from models.user_persona import UserPersona

PROFILE_URL = "/api/v1/user/profile"


def _login_as(user_id):
    """Make verify_token return a decoded token for user_id."""
    app.dependency_overrides[verify_token] = lambda: {"uid": user_id}


@pytest.fixture
def user_id():
    return f"profile_user_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def profile_client(user_id):
    _login_as(user_id)
    yield TestClient(app)
    app.dependency_overrides.pop(verify_token, None)


def test_get_profile_before_saving(profile_client, user_id):
    resp = profile_client.get(PROFILE_URL)

    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == user_id
    assert data["has_profile"] is False
    assert data["focus_areas"] == []
    assert data["communication_style"] is None


def test_save_and_get_profile(profile_client, user_id):
    payload = {
        "focus_areas": ["nutrition", "sleep_rest", "nutrition"],
        "communication_style": "direct",
        "barriers": ["Not enough time", " not enough time ", "Low energy"],
    }
    resp = profile_client.post(PROFILE_URL, json=payload)
    assert resp.status_code == 200

    data = profile_client.get(PROFILE_URL).json()
    assert data["has_profile"] is True
    assert data["focus_areas"] == ["nutrition", "sleep_rest"]
    assert data["communication_style"] == "direct"
    assert data["barriers"] == [
        {"text": "Not enough time", "source": "onboarding"},
        {"text": "Low energy", "source": "onboarding"},
    ]


@pytest.mark.parametrize(
    "payload",
    [
        {"communication_style": "sarcastic"},
        {"focus_areas": ["juggling"]},
        {"barriers": ["x" * 201]},
        {"barriers": [f"barrier {i}" for i in range(11)]},
    ],
)
def test_invalid_profile_rejected(profile_client, payload):
    resp = profile_client.post(PROFILE_URL, json=payload)
    assert resp.status_code == 422


def test_resubmit_keeps_session_barriers(profile_client, user_id):
    profile_client.post(PROFILE_URL, json={"barriers": ["Work schedule"]})

    # Simulate a barrier learned during Session 2
    db = next(get_db())
    try:
        persona = db.query(UserPersona).filter(UserPersona.user_id == user_id).first()
        persona.barriers = persona.barriers + [{"text": "Evenings are hectic", "source": 2}]
        db.commit()
    finally:
        db.close()

    profile_client.post(PROFILE_URL, json={"barriers": ["Cost of healthy food"]})

    barriers = profile_client.get(PROFILE_URL).json()["barriers"]
    assert barriers == [
        {"text": "Cost of healthy food", "source": "onboarding"},
        {"text": "Evenings are hectic", "source": 2},
    ]


def test_users_only_see_their_own_profile(profile_client, user_id):
    profile_client.post(PROFILE_URL, json={"communication_style": "encouraging"})

    _login_as(f"other_{user_id}")
    data = profile_client.get(PROFILE_URL).json()

    assert data["has_profile"] is False
    assert data["communication_style"] is None


def test_profile_requires_login():
    resp = TestClient(app).get(PROFILE_URL)
    assert resp.status_code == 401
