import sqlite3

import pytest
from werkzeug.security import check_password_hash

import database.db as db

VALID = {
    "name": "Alice",
    "email": "alice@example.com",
    "password": "password123!",
}

DUPLICATE_MSG = b"An account with that email already exists."


def user_count():
    conn = db.get_db()
    try:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    finally:
        conn.close()


def test_get_register_renders_form(client):
    r = client.get("/register")
    assert r.status_code == 200
    assert b'action="/register"' in r.data


def test_valid_registration_redirects_to_login(client):
    before = user_count()
    r = client.post("/register", data=VALID)
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/login")
    assert user_count() == before + 1


def test_password_is_hashed(client):
    client.post("/register", data=VALID)
    row = db.get_user_by_email(VALID["email"])
    assert row["password_hash"] != VALID["password"]
    assert row["password_hash"].startswith(("scrypt:", "pbkdf2:"))
    assert check_password_hash(row["password_hash"], VALID["password"])


def test_email_stored_stripped_and_lowercase(client):
    client.post("/register", data={**VALID, "email": "  New@Example.COM "})
    row = db.get_user_by_email("new@example.com")
    assert row is not None
    assert row["email"] == "new@example.com"


@pytest.mark.parametrize("email", ["demo@spendly.com", "Demo@Spendly.com"])
def test_duplicate_email_rejected(client, email):
    before = user_count()
    r = client.post("/register", data={**VALID, "email": email})
    assert r.status_code == 200
    assert DUPLICATE_MSG in r.data
    assert user_count() == before


@pytest.mark.parametrize(
    "field, value, message",
    [
        ("name", "  ", b"Please enter your name."),
        ("email", "", b"Please enter your email address."),
        ("password", "", b"Please enter a password."),
    ],
)
def test_missing_required_fields_rejected(client, field, value, message):
    before = user_count()
    r = client.post("/register", data={**VALID, field: value})
    assert r.status_code == 200
    assert message in r.data
    assert user_count() == before


def test_short_password_rejected(client):
    before = user_count()
    r = client.post("/register", data={**VALID, "password": "1234567"})
    assert r.status_code == 200
    assert b"Password must be at least 8 characters." in r.data
    assert user_count() == before


@pytest.mark.parametrize("password", ["Pass@123", "!@#$%^&*", "pass_word1!"])
def test_password_with_special_char_and_min_length_accepted(client, password):
    r = client.post("/register", data={**VALID, "password": password})
    assert r.status_code == 302


@pytest.mark.parametrize("password", ["Pass 123!", " password1!", "password1! "])
def test_password_with_whitespace_rejected(client, password):
    before = user_count()
    r = client.post("/register", data={**VALID, "password": password})
    assert r.status_code == 200
    assert b"Password must not contain spaces." in r.data
    assert user_count() == before


@pytest.mark.parametrize("password", ["password123", "12345678", "ABCDEFGH"])
def test_password_without_special_char_rejected(client, password):
    before = user_count()
    r = client.post("/register", data={**VALID, "password": password})
    assert r.status_code == 200
    assert b"Password must contain at least one special character." in r.data
    assert user_count() == before


def test_password_length_checked_before_special_char(client):
    r = client.post("/register", data={**VALID, "password": "abc"})
    assert b"Password must be at least 8 characters." in r.data


@pytest.mark.parametrize(
    "email", ["nodomain", "a@", "@x.com", "a@b", "a b@x.com"]
)
def test_invalid_email_rejected(client, email):
    before = user_count()
    r = client.post("/register", data={**VALID, "email": email})
    assert r.status_code == 200
    assert b"Please enter a valid email address." in r.data
    assert user_count() == before


def test_error_keeps_name_and_email_but_not_password(client):
    r = client.post(
        "/register",
        data={"name": "Alice", "email": "alice@example.com", "password": "abc123"},
    )
    assert r.status_code == 200
    assert b'value="Alice"' in r.data
    assert b'value="alice@example.com"' in r.data
    assert b'value="abc123"' not in r.data


def test_race_on_duplicate_email_is_handled(client, monkeypatch):
    # Simulate two concurrent requests both passing the pre-check.
    monkeypatch.setattr("app.get_user_by_email", lambda email: None)
    before = user_count()
    r = client.post("/register", data={**VALID, "email": "demo@spendly.com"})
    assert r.status_code == 200
    assert DUPLICATE_MSG in r.data
    assert user_count() == before


def test_empty_post_body_does_not_crash(client):
    r = client.post("/register", data={})
    assert r.status_code == 200
    assert b"Please enter your name." in r.data


def test_get_user_by_email_unknown_returns_none(client):
    assert db.get_user_by_email("nobody@example.com") is None


def test_create_user_duplicate_email_raises(client):
    db.create_user("Bob", "bob@example.com", "password1")
    with pytest.raises(sqlite3.IntegrityError):
        db.create_user("Bobby", "BOB@example.com", "password2")
