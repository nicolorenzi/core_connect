from main import (
    engine,
    Base,
    ensure_users_email_column,
    ensure_workout_user_column,
    ensure_exercise_columns,
    seed_default_users,
    DATABASE_URL_OBJECT,
)
import os

def _describe_database_url(url_obj):
    if not url_obj:
        return "unknown database"
    backend = url_obj.get_backend_name()
    if backend == "sqlite":
        path = url_obj.database or "users.db"
        return f"SQLite file {path}"
    host = url_obj.host or "localhost"
    port = f":{url_obj.port}" if url_obj.port else ""
    database = f"/{url_obj.database}" if url_obj.database else ""
    return f"{backend} database on {host}{port}{database}"

print("Running DB setup...")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("WARNING: DATABASE_URL not set; defaulting to local SQLite for development.")
else:
    print(
        "Using database:",
        _describe_database_url(DATABASE_URL_OBJECT),
    )

ensure_users_email_column()
ensure_workout_user_column()
ensure_exercise_columns()
Base.metadata.create_all(bind=engine)
seed_default_users()

print("DB setup complete")
