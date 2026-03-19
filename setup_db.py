from main import (
    engine,
    Base,
    ensure_users_email_column,
    ensure_workout_user_column,
    ensure_exercise_columns,
    seed_default_users,
    DATABASE_BACKEND,
    db_url,
)
import os

print("Running DB setup...")

if not os.getenv("DATABASE_URL"):
    print("WARNING: DATABASE_URL not set; defaulting to local SQLite for development.")
else:
    print("Using database backend:", DATABASE_BACKEND, "host:", db_url.split("@")[-1] if "@" in db_url else db_url)

ensure_users_email_column()
ensure_workout_user_column()
ensure_exercise_columns()
Base.metadata.create_all(bind=engine)
seed_default_users()

print("DB setup complete")