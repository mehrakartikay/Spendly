# Spec: Login and Logout

## Overview
Make sign-in work end to end. `POST /login` checks the submitted email and password against the `users` table using `werkzeug.security.check_password_hash`, and on success stores the user's id in the Flask session. `GET /logout` clears that session. The navbar then reflects whether a visitor is signed in. This is the step that turns the registered accounts from Step 2 into authenticated sessions, and it is required before the profile page (Step 4) and expense pages (Steps 7–9) can know which user is acting. Sessions need a `SECRET_KEY`, so this step also sets one up in `app.py`.

## Depends on
- Step 1 — Database setup: `get_db()`, the `users` table, and `PRAGMA foreign_keys = ON`.
- Step 2 — Registration: `get_user_by_email()` in `database/db.py`, and accounts with hashed passwords in the `users` table.

## Routes
- `GET /login` — renders `login.html`. If the visitor is already signed in, redirects to `/` — public
- `POST /login` — validates the form, checks the credentials, sets the session on success, re-renders the form with a generic error on failure — public
- `GET /logout` — clears the session and redirects to `/` — logged-in (an anonymous visit is harmless and also redirects to `/`)

## Database changes
No schema changes. The existing `users` table already has `email` (UNIQUE) and `password_hash`.

New helper in `database/db.py`:
- `get_user_by_id(user_id)` — returns the matching row or `None`, parameterised, closes the connection. Used by the navbar and later steps to look up the signed-in user.

## Templates
- **Create:** none
- **Modify:**
  - `templates/login.html` — change the hardcoded `action="/login"` to `action="{{ url_for('login') }}"`. Show `{% if error %}<div class="auth-error">…</div>{% endif %}` (same pattern as `register.html`). Keep the submitted email with `value="{{ email or '' }}"`. Never re-populate the password.
  - `templates/base.html` — in the navbar, when `session.get('user_id')` is set, show a "Sign out" link to `url_for('logout')` instead of "Sign in" and "Get started". Otherwise leave the navbar as it is.

## Files to change
- `app.py` — set `app.secret_key` from the `SECRET_KEY` environment variable, with a clearly marked development fallback. Add `session` to the Flask import, and `check_password_hash` / `get_user_by_id` to the existing imports. Add `methods=["GET", "POST"]` to `/login`, and add the POST handling and the signed-in redirect. Replace the `/logout` placeholder body with session clearing and a redirect to `/`. Do not touch `/profile` or the other stubs.
- `database/db.py` — add `get_user_by_id(user_id)`.
- `templates/login.html` — form action, error block, email re-population.
- `templates/base.html` — conditional navbar links.

## Files to create
- `tests/test_login_logout.py` — tests for the login and logout behaviour listed in the definition of done.

## New dependencies
No new dependencies. `flask.session` and `werkzeug.security.check_password_hash` are already available.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders). Never build SQL with f-strings
- Verify passwords with `werkzeug.security.check_password_hash`. Never store, compare or log plaintext passwords
- Route functions do one job: read the form, call helpers, set or clear the session, pick the response. All SQL lives in `database/db.py`
- Normalise the email with `.strip().lower()` before lookup, matching how registration stores it
- Use one generic error message, `Invalid email or password.`, for both an unknown email and a wrong password, so the form cannot be used to discover which accounts exist
- Empty email or password re-renders the form with an error and does not query the database
- `app.secret_key` is read from the `SECRET_KEY` environment variable. A development fallback is acceptable, but it must be a visibly named constant, and the code must not print it
- Logout calls `session.clear()`
- Use `abort()` only for genuine HTTP errors. Credential failures re-render `login.html` with an error
- Use CSS variables from `static/css/style.css` for any new styling. Never hardcode hex values
- All templates extend `base.html`
- Use `url_for()` for every internal link and redirect target, including `url_for('landing')` for `/`, `url_for('login')`, and `url_for('logout')`
- Do not implement `/profile`, `/expenses/*`, or any other stub route
- CSRF protection on `/logout` is out of scope for this step. Note it as a known gap for later

## Definition of done
- [x] `GET /login` still renders the form with status 200 when signed out
- [x] Signing in with `demo@spendly.com` / `demo123` redirects to `/` and the navbar shows "Sign out"
- [x] Signing in with a correct email and a wrong password re-renders the form with `Invalid email or password.` and does not set the session
- [x] Signing in with an unknown email shows the same `Invalid email or password.` message
- [x] Signing in with the email in different casing (for example `DEMO@spendly.com`) succeeds
- [x] Submitting an empty email or empty password re-renders the form with an error
- [x] On a failed sign-in, the email field keeps the submitted value and the password field is empty
- [x] After a successful sign-in, a later request in the same browser session still shows "Sign out" in the navbar
- [x] `GET /logout` clears the session, redirects to `/`, and the navbar shows "Sign in" and "Get started" again
- [x] `GET /logout` with no session redirects to `/` without an error
- [x] `GET /login` while signed in redirects to `/`
- [x] `/logout` no longer returns the placeholder string "Logout — coming in Step 3"
- [x] `/profile` and the expense routes still return their placeholder responses
- [x] `grep -n "f\"" database/db.py` shows no SQL built with f-strings
- [ ] The login page renders correctly on a phone-width viewport (no horizontal scroll)
- [x] `pytest` passes, including tests for: successful sign-in, wrong password, unknown email, email case-insensitivity, empty fields, session persistence, logout, and redirect when already signed in
