# PASSWORD_HASHING Security Report

## Status: N/A

## Findings

HADES delegates all authentication to Supabase Auth. Passwords are never seen, stored, or hashed by application code. Supabase Auth uses bcrypt internally for password hashing.

`gui.py` receives a password string from the login form and passes it directly to `db.sign_in(email, password)` → `supabase.auth.sign_in_with_password({"email": ..., "password": ...})`. The password travels over HTTPS to Supabase and is never written to disk or logged by the application.

## Recommendations

N/A.
