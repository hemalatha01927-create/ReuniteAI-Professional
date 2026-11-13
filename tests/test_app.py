import io
import pytest
from app import create_app
from app.extensions import orm
from app.models import User, Case

@pytest.fixture()
def app():
    app = create_app("config.TestConfig")
    with app.app_context():
        orm.create_all()
        yield app
        orm.session.remove()
        orm.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, email="member@example.com"):
    return client.post("/register", data={
        "full_name": "Test Member", "email": email,
        "password": "a-very-strong-password", "confirm_password": "a-very-strong-password"
    }, follow_redirects=True)


def test_public_landing_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Bring the right people" in response.data


def test_registration_creates_member_account(client, app):
    response = register(client)
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email="member@example.com").first()
        assert user is not None
        assert user.role == "member"
        assert user.check_password("a-very-strong-password")


def test_case_directory_is_accessible_without_login(client):
    assert client.get("/cases/").status_code == 200


def test_case_submission_starts_private_and_pending_review(client, app):
    register(client)
    response = client.post("/cases/new", data={
        "report_type": "missing", "person_name": "Example Person", "age": "24",
        "location_city": "Nagapattinam", "location_state": "Tamil Nadu", "location_country": "India",
        "description": "Private test details", "public_summary": "Public-safe test summary", "photo_public": ""
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        case = Case.query.first()
        assert case is not None
        assert case.status == "pending_review"
        assert case.case_code.startswith("RAI-")
        assert case.photo_public is False


def test_unapproved_case_not_public(client, app):
    with app.app_context():
        user = User(full_name="Owner", email="owner@example.com", role="member")
        user.set_password("a-very-strong-password")
        orm.session.add(user)
        orm.session.flush()
        case = Case(case_code="RAI-TEST-000001", report_type="missing", person_name="Private Person",
                    location_city="Nagapattinam", location_state="Tamil Nadu", description="Private case", public_summary="Safe public summary",
                    reporter_id=user.id, status="pending_review")
        orm.session.add(case)
        orm.session.commit()
        case_id = case.id
    response = client.get(f"/cases/{case_id}")
    assert response.status_code == 404


def test_attribute_matcher_explains_non_biometric_signals():
    from app.utils.matching import score_pair
    missing = Case(case_code="RAI-A-1", report_type="missing", person_name="A",
                   age=26, gender="Female", last_seen_date=__import__("datetime").date(2026, 1, 1),
                   location_city="Nagapattinam", location_state="Tamil Nadu",
                   description="blue shirt black backpack", clothing="blue shirt")
    found = Case(case_code="RAI-B-1", report_type="found", person_name="B",
                 age=27, gender="Female", last_seen_date=__import__("datetime").date(2026, 1, 2),
                 location_city="Nagapattinam", location_state="Tamil Nadu",
                 description="person with blue shirt and backpack", clothing="blue shirt")
    score, reasons = score_pair(missing, found)
    assert score >= 35
    assert any("Same city" in reason for reason in reasons)
    assert all("face" not in reason.lower() for reason in reasons)


def test_health_endpoint_returns_ok(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json["status"] == "ok"
