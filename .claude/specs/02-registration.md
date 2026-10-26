# Spec: Registration

## Overview
Add the `POST /register` handler so visitors can create a Spendly account from the existing registration form. The `GET /register` route already renders `register.html`; this step makes the form submit work. It validates the name, email and password, stores the new user with a hashed password through a helper in `database/db.py`, and redirects to the login page on success. Registration is the first way users enter data into the `users` table, so it is the foundation for login (Step 3) and everything that follows it.

## Depends on
- Step 1 — Database setup: `get_db()`, the `users` table with a UNIQUE `email` constraint, and `werkzeug.security` hashing must all exist.

## Routes
- `GET /register` — already implemented, renders `register.html` — public
- `POST /register` — validates form data, creates the user, redirects to `/login` on success, re-renders the form with an error on failure — public

## Database changes
No schema changes. The existing `users` table (`name`, `email` UNIQUE, `password_hash`) is sufficient.

New helper in `database/db.py`:
- `create_user(name, email, password)` — hashes the password with `generate_password_hash`, inserts with a parameterised `INSERT`, commits, and returns the new user id. It lets `sqlite3.IntegrityError` propagate so the route can report a duplicate email.
- `get_user_by_email(email)` — returns the matching row or `None`. Used for the duplicate-email check before insert, so the route does not depend on catching database errors for the common case.

## Templates
- **Create:** none
- **Modify:**
  - `templates/register.html` — no structural change required. The existing `{% if error %}` block and `auth-error` class display validation messages. Keep the submitted `name` and `email` values in the form on error (`value="{{ name or '' }}"`, `value="{{ email or '' }}"`) so the user does not retype them. Never re-populate the password field.

## Files to change
- `app.py` — add `methods=["GET", "POST"]` to the `/register` route; on POST, read form fields, validate, call the db helpers, and either redirect to `login` or re-render `register.html` with `error`. Add `redirect` to the Flask import.
- `database/db.py` — add `create_user()` and `get_user_by_email()`.

## Files to create
- None

## New dependencies
No new dependencies. `flask.redirect`, `flask.request`, `flask.url_for` and `werkzeug.security` are already available.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders). Never build SQL with f-strings
- Passwords hashed with `werkzeug.security.generate_password_hash`. Never store or log plaintext passwords
- Route function does one job: read the form, call helpers, pick the response. All SQL lives in `database/db.py`
- Validation failures re-render `register.html` with a clear message. Use `abort()` only for genuine HTTP errors (for example a malformed request), not for form validation
- Validation rules:
  - `name`: required, stripped of surrounding whitespace, non-empty
  - `email`: required, stripped, lowercased before storage and lookup, must contain `@` and a domain part
  - `password`: required, minimum 8 characters, must not contain whitespace, must contain at least one special character (any character that is not a letter or digit). Checks run in this order and the first failure is shown
  - `password` is not stripped before validation or hashing
- Duplicate email returns the same kind of error message as other validation failures; it does not crash
- Use CSS variables from `static/css/style.css` for any new styling. Never hardcode hex values
- All templates extend `base.html`
- Use `url_for()` for every internal link, including the redirect target (`url_for('login')`)
- Do not implement login session handling here. Successful registration only redirects to `/login`; it does not sign the user in
- Do not touch the `/logout`, `/profile` or other stub routes

## Definition of done
- [x] `GET /register` still renders the form with status 200
- [x] Submitting the form with all valid fields creates one new row in `users` and redirects to `/login`
- [x] The stored `password_hash` is not equal to the plaintext password and starts with a werkzeug hash prefix (for example `scrypt:` or `pbkdf2:`)
- [x] Submitting an email already in the database (for example `demo@spendly.com`) re-renders the form with an error message and creates no new row
- [x] Submitting the same email with different casing (for example `Demo@Spendly.com`) is rejected as a duplicate
- [x] Submitting an empty name, empty email, or empty password re-renders the form with an error and creates no row
- [x] Submitting a password shorter than 8 characters re-renders the form with an error and creates no row
- [x] Submitting a password containing whitespace (leading, trailing or in the middle) re-renders the form with an error and creates no row
- [x] Submitting a password without a special character (for example `password123`) re-renders the form with an error and creates no row
- [x] Submitting a password of 8+ characters with at least one special character and no whitespace (for example `Pass@123`) creates the account
- [x] Submitting an email without `@` or a domain re-renders the form with an error and creates no row
- [x] On error, the name and email fields keep the submitted values; the password field is empty
- [ ] Registering a new account and then running `sqlite3 expense_tracker.db "SELECT name, email FROM users"` shows the new row with the email in lowercase
- [ ] The `/register` page still renders correctly on a phone-width viewport (no horizontal scroll)
- [x] `pytest` passes, including tests for: successful registration, duplicate email, each validation rule, and password hashing
- [x] No f-strings appear in any SQL added in this step (`grep -n "f\"" database/db.py` shows no SQL f-strings)
