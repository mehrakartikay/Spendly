import pytest

import database.db as db

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"
INVALID = b"Invalid email or password."
MISSING = b"Email and password are required."
SIGN_OUT = b"Sign out"
SIGN_IN = b"Sign in"
GET_STARTED = b"Get started"


def _login(client, email, password):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )


def _demo_user_id():
    return db.get_user_by_email(DEMO_EMAIL)["id"]


def test_get_login_renders_form(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert b'action="/login"' in r.data


def test_login_success_redirects_to_landing(client):
    r = _login(client, DEMO_EMAIL, DEMO_PASSWORD)
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/")


def test_login_success_navbar_shows_sign_out(client):
    _login(client, DEMO_EMAIL, DEMO_PASSWORD)
    r = client.get("/", follow_redirects=True)
    assert SIGN_OUT in r.data
    assert GET_STARTED not in r.data


def test_login_wrong_password(client):
    r = _login(client, DEMO_EMAIL, "wrongpass")
    assert r.status_code == 200
    assert INVALID in r.data
    with client.session_transaction() as s:
        assert "user_id" not in s


def test_login_unknown_email(client):
    r = _login(client, "nobody@spendly.com", DEMO_PASSWORD)
    assert r.status_code == 200
    assert INVALID in r.data
    with client.session_transaction() as s:
        assert "user_id" not in s


def test_unknown_email_and_wrong_password_return_same_error(client):
    wrong_password = _login(client, DEMO_EMAIL, "wrongpass")
    unknown_email = _login(client, "nobody@spendly.com", DEMO_PASSWORD)
    assert INVALID in wrong_password.data
    assert INVALID in unknown_email.data


@pytest.mark.parametrize("email", ["DEMO@spendly.com", "  Demo@Spendly.com  "])
def test_login_email_is_case_insensitive_and_trimmed(client, email):
    r = _login(client, email, DEMO_PASSWORD)
    assert r.status_code == 302
    with client.session_transaction() as s:
        assert s["user_id"] == _demo_user_id()


@pytest.mark.parametrize(
    "email, password",
    [("", DEMO_PASSWORD), (DEMO_EMAIL, ""), ("", "")],
)
def test_login_empty_fields_show_error(client, email, password):
    r = _login(client, email, password)
    assert r.status_code == 200
    assert MISSING in r.data
    with client.session_transaction() as s:
        assert "user_id" not in s


def test_login_empty_fields_skip_database(client, monkeypatch):
    def fail(_email):
        raise AssertionError("database must not be queried for empty fields")

    monkeypatch.setattr("app.get_user_by_email", fail)
    r = _login(client, "", "")
    assert r.status_code == 200
    assert MISSING in r.data


def test_failed_login_keeps_email_and_not_password(client):
    r = _login(client, DEMO_EMAIL, "wrongpw123")
    assert b'value="demo@spendly.com"' in r.data
    assert b"wrongpw123" not in r.data


def test_session_persists_across_requests(client):
    _login(client, DEMO_EMAIL, DEMO_PASSWORD)
    r = client.get("/")
    assert SIGN_OUT in r.data
    with client.session_transaction() as s:
        assert s["user_id"] == _demo_user_id()


def test_logout_clears_session_and_redirects(client):
    _login(client, DEMO_EMAIL, DEMO_PASSWORD)
    r = client.get("/logout", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/")
    with client.session_transaction() as s:
        assert "user_id" not in s


def test_logout_navbar_reverts_to_signed_out(client):
    _login(client, DEMO_EMAIL, DEMO_PASSWORD)
    client.get("/logout")
    r = client.get("/", follow_redirects=True)
    assert SIGN_IN in r.data
    assert GET_STARTED in r.data
    assert SIGN_OUT not in r.data


def test_anonymous_logout_redirects(client):
    r = client.get("/logout", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/")


def test_logout_no_longer_placeholder(client):
    r = client.get("/logout")
    assert b"coming in Step 3" not in r.data


def test_login_page_redirects_when_signed_in(client):
    _login(client, DEMO_EMAIL, DEMO_PASSWORD)
    r = client.get("/login", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/")


@pytest.mark.parametrize("method", ["get", "post"])
def test_register_redirects_when_signed_in(client, method):
    _login(client, DEMO_EMAIL, DEMO_PASSWORD)
    if method == "get":
        r = client.get("/register", follow_redirects=False)
    else:
        r = client.post(
            "/register",
            data={"name": "Eve", "email": "eve@spendly.com", "password": "Pass@123"},
            follow_redirects=False,
        )
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/")
    assert db.get_user_by_email("eve@spendly.com") is None


def test_login_post_redirects_when_signed_in(client):
    _login(client, DEMO_EMAIL, DEMO_PASSWORD)
    r = _login(client, DEMO_EMAIL, DEMO_PASSWORD)
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/")


def test_profile_stub_still_placeholder(client):
    r = client.get("/profile")
    assert r.status_code == 200
    assert b"coming in Step 4" in r.data


def test_get_user_by_id_returns_row_or_none(client):
    user_id = _demo_user_id()
    row = db.get_user_by_id(user_id)
    assert row is not None
    assert row["email"] == DEMO_EMAIL
    assert db.get_user_by_id(99999) is None
