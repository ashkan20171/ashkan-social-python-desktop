# Ashkan Social — Python Desktop Community Platform

A polished, offline-first desktop social networking MVP built with **Python, PySide6 and SQLite**. The application is intended as an extensible portfolio project, not a production-hosted social network.

## Features
- Secure PBKDF2 password hashing with per-user random salt and constant-time comparison
- Account registration and sign-in
- Posts, likes, comments and follow/unfollow
- Feed search, following feed, saved posts and user discovery
- Direct messages and notifications (local database, not live network messaging)
- Profile editing, community statistics, post deletion and content reporting
- Dark visual theme, responsive resizable desktop window
- SQLite foreign keys, useful indexes and parameterized queries
- Unit tests for authentication and social service operations

## Windows setup
```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

The database is created automatically at `%USERPROFILE%\.ashkan_social\social.db`.

## Run tests
```powershell
python -m unittest discover -s tests -v
```

## Architecture
- `src/ashkan_social/app.py` — Qt user interface
- `src/ashkan_social/services.py` — social application logic
- `src/ashkan_social/db.py` — persistence and schema
- `src/ashkan_social/auth.py` — authentication
- `tests/` — regression tests

## Limitations and next milestones
This is a **single-machine application**. Messages are not sent over the Internet; users share one local SQLite database. No realtime WebSocket server, remote accounts, encryption at rest, media uploads, moderation console, or distributed deployment is provided. Future milestones: FastAPI backend, PostgreSQL, WebSocket chat, media storage, rate limiting, admin moderation, and full FA/EN localization.

## GitHub
**Repository:** `ashkan-social-python-desktop`

**About:** Modern Python desktop social network MVP | PySide6, SQLite, clean service architecture, secure authentication, community feeds & messaging.

Built as a portfolio-ready software engineering learning project.

## Version 3 additions
- Light/dark theme toggle in the main navigation.
- Edit your own posts (server-side ownership check in SQL UPDATE).
- Private local draft composer, draft list, publish and delete actions.
- Block/unblock users; blocked pairs cannot follow or send new messages.
- Existing local SQLite databases are upgraded automatically using CREATE TABLE IF NOT EXISTS.

### Important limitations
This is a local desktop prototype, not a production multi-user social network. No network synchronization, end-to-end encryption, moderation console, real-time messaging, image uploads, or full Persian localization is provided yet. The desktop interface requires a graphical Windows environment and has not been visually smoke-tested here.
"# ashkan-social-python-desktop" 
