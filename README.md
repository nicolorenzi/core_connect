# Core Connect
Core Connect is a full-stack fitness workspace that combines authenticated workout logging, nutrition tracking, and progress analytics. It keeps session state on the server, normalizes exercise input, and stores logs alongside a user-scoped exercise library so dashboards stay focused and light.

---

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment](#environment)
- [Running the app](#running-the-app)
- [Testing](#testing)
- [API](#api)

---

## Features

- **Authentication & sessions** – email/password login and registration backed by `werkzeug.security` hashing, protected routes, and Flask sessions with a required `SECRET_KEY`.
- **Calorie, nutrition, and workout dashboards** – dedicated templates for the calculator, nutrition tracker, and workout tracker rely on Tailwind CSS and static assets compiled through the `tailwind` task.
- **Structured workout logging** – workouts are grouped by date and user, exercise names are normalized (capitalized words) and stored in a `StoredExercises` catalog so history can be reused, and every set records reps, weight, and a set label (`W` for warmup or a count).
- **Progress analyzer** – stored exercises expose detailed progress on `/progress-tracker` plus a drill-down view that graphs daily max 1RM (weight × (1 + reps/30)) and highlights the strongest/heaviest sets per exercise.
- **Nutrition tracker & logs** – placeholder routes wired for nutrient input and day-to-day workout logs so UI work can attach to the authenticated API surfaces.
- **API helpers** – authenticated endpoints to list workouts (`GET /api/workouts`) and delete an exercise (`DELETE /api/exercises/<id>`), with ownership enforced via joins against the current user.

## Prerequisites

- Python 3.10+ (see `requirements.txt` for explicit dependency versions)
- Node.js + npm 18+ (for Tailwind CSS CLI)
- SQLite (default) or PostgreSQL if you point `DATABASE_URL` at a managed database.

## Installation

1. Clone the repo and enter it:
   ```bash
   git clone https://github.com/nicolorenzi/core_connect.git
   cd core_connect
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # .\venv\Scripts\activate  # Windows
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install Node dependencies once (needed for Tailwind CLI):
   ```bash
   npm install
   ```

## Environment

Create a `.env` file in the project root and set the following (examples):

```
SECRET_KEY=your-long-random-secret-key
DATABASE_URL=sqlite:///users.db  # or a PostgreSQL URL
DB_PASSWORD=postgres-password-if-you-use-ssl
DEFAULT_EMAILS=you@example.com
DEFAULT_PASSWORD=YourStrongPassw0rd!
```

- `SECRET_KEY` is mandatory for secure Flask sessions.
- `DATABASE_URL` must be a SQLAlchemy URL targeting PostgreSQL (with optional `DB_PASSWORD` for managed services requiring a separate secret) or SQLite.
- `DEFAULT_EMAILS`/`DEFAULT_PASSWORD` together seed admin users when those values satisfy the password policy; both are optional.

## Running the app

- `make tailwind` – runs `npx tailwindcss` in watch mode to compile `static/css/input.css` → `static/css/output.css`.
- `make run` – starts the Flask app via `python main.py`.
- `make dev` – runs `tailwind` and `run` in parallel so the UI stays in sync with Tailwind while you iterate.
- `tailwind` must run before the app unless you wire the CLI into another build tool; the templates expect `static/css/output.css` to exist.

When you start the app, visit `http://127.0.0.1:5000` and register or login to reach the dashboard and secondary trackers.

## Testing

Run the calorie calculator unit tests:

```bash
pytest tests/test_calorie_calculator.py
```

## API

- `GET /api/workouts` – returns all of the authenticated user’s workouts, ordered by date desc, with embedded exercise sets.
- `DELETE /api/exercises/<int:exercise_id>` – removes an exercise that belongs to the current user by clearing its workout associations and deleting the row.
