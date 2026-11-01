import os
import sqlite3

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from database.db import (
    create_user,
    get_db,
    get_user_by_email,
    get_user_by_id,
    init_db,
    seed_db,
)

# Development-only fallback. Set the SECRET_KEY environment variable in any real deployment.
DEV_SECRET_KEY = "dev-only-insecure-secret-key-change-me"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", DEV_SECRET_KEY)

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


DUPLICATE_EMAIL_ERROR = "An account with that email already exists."


def _validate_registration(name, email, password):
    if not name:
        return "Please enter your name."
    if not email:
        return "Please enter your email address."
    if any(ch.isspace() for ch in email) or email.count("@") != 1:
        return "Please enter a valid email address."
    local, domain = email.split("@")
    if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
        return "Please enter a valid email address."
    if not password:
        return "Please enter a password."
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if any(ch.isspace() for ch in password):
        return "Password must not contain spaces."
    if password.isalnum():
        return "Password must contain at least one special character."
    return None


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    error = _validate_registration(name, email, password)
    if error is None and get_user_by_email(email) is not None:
        error = DUPLICATE_EMAIL_ERROR
    if error is None:
        try:
            create_user(name, email, password)
        except sqlite3.IntegrityError:
            error = DUPLICATE_EMAIL_ERROR

    if error is not None:
        return render_template("register.html", error=error, name=name, email=email)
    return redirect(url_for("login"))


INVALID_CREDENTIALS_ERROR = "Invalid email or password."
MISSING_CREDENTIALS_ERROR = "Email and password are required."


def _validate_login(email, password):
    if not email or not password:
        return MISSING_CREDENTIALS_ERROR
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    error = _validate_login(email, password)
    if error is None:
        user = get_user_by_email(email)
        if user is None or not check_password_hash(user["password_hash"], password):
            error = INVALID_CREDENTIALS_ERROR

    if error is not None:
        return render_template("login.html", error=error, email=email)

    session.clear()
    session["user_id"] = user["id"]
    return redirect(url_for("landing"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    # Known gap: logout is a GET request, so it is open to CSRF. Out of scope for Step 3.
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
