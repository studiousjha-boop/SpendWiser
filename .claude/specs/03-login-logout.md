---# Spec: Login and Logout

## Overview
Implement user authentication workflow including registration, login, and secure logout. This enables users to securely manage their accounts and protect personal financial data.

## Depends on
- 01 Database Setup (must have functional SQL tables)
- 02 Registration (basic account creation form)

## Routes
- `POST /register` – Register new user (public)
- `POST /login` – Authenticate existing user (public)
- `GET /logout` – Terminate session (logged-in)

## Database changes
- Add `users` table with columns: `id`, `username`, `password_hash`, `created_at`
- Add `sessions` table with columns: `id`, `user_id`, `token`, `expiry`

## Templates
- **Create:**
  - `templates/register.html` (new registration form)
  - `templates/login.html` (existing login form)
  - `templates/logout.html` (logout confirmation)

## Files to change
- `app.py` (add new routes and login logic)
- `database/db.py` (implement user/session models)

## Files to create
- `static/css/auth.css` (new authentication-specific styles)

## New dependencies
- no new dependencies

## Rules for implementation
- Use werkzeug's `generate_password_hash` for password storage
- Implement JWT-based session tokens with 15-minute expiry
- Store session tokens in encrypted cookies
- Use CSS variables for primary color (`$primary-color`) in auth styles
- All templates must extend `base.html`

## Definition of done
- Register/logout routes functional
- Passwords stored hashed
- Sessions encoded in JWT
- Login form validates user input
- Logout clears session cookie