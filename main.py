from flask import Flask, render_template, url_for, make_response, request, jsonify, redirect, flash, session as flask_session
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from models.base import Base
from models.user_model import User
from models.workout_model import Workout, Exercise, StoredExercise, workout_exercise_table
from models.meal_model import Meal, Food
from dotenv import load_dotenv
import os
import datetime
import re

app = Flask(__name__)
load_dotenv()

app.secret_key = os.getenv("SECRET_KEY")
DEFAULT_EMAILS = os.getenv("DEFAULT_EMAILS", "").split(",")
DEFAULT_PASSWORD = os.getenv("DEFAULT_PASSWORD")

engine = create_engine("sqlite:///users.db", echo=True)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_REQUIREMENTS = (
    "Passwords must be 8-64 characters long, include at least one uppercase letter, "
    "one lowercase letter, and one special character."
)
SET_LABEL_PATTERN = re.compile(r"^(?:W|[1-9][0-9]*)$")

def ensure_users_email_column():
    inspector = inspect(engine)
    if "Users" not in inspector.get_table_names():
        return

    existing_columns = {col["name"] for col in inspector.get_columns("Users")}
    if "email" in existing_columns:
        return
    if "username" not in existing_columns:
        return

    with engine.begin() as conn:
        conn.execute(text('ALTER TABLE "Users" RENAME TO "Users_old"'))
        conn.execute(
            text(
                'CREATE TABLE "Users" ('
                'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                'email VARCHAR NOT NULL UNIQUE, '
                'password VARCHAR NOT NULL'
                ')'
            )
        )
        conn.execute(
            text(
                'INSERT INTO "Users" (id, email, password) '
                'SELECT id, username, password FROM "Users_old"'
            )
        )
        conn.execute(text('DROP TABLE "Users_old"'))

ensure_users_email_column()

Base.metadata.create_all(bind=engine)

def ensure_workout_user_column():
    inspector = inspect(engine)
    if "Workouts" not in inspector.get_table_names():
        return

    existing_columns = {col["name"] for col in inspector.get_columns("Workouts")}
    if "user_id" in existing_columns:
        return

    with engine.begin() as conn:
        conn.execute(text('ALTER TABLE "Workouts" ADD COLUMN user_id INTEGER'))


def ensure_exercise_columns():
    inspector = inspect(engine)
    if "Exercises" not in inspector.get_table_names():
        return

    stored_table_names = inspector.get_table_names()
    if "StoredExercises" not in stored_table_names:
        StoredExercise.__table__.create(bind=engine, checkfirst=True)

    inspector = inspect(engine)
    existing_columns = {col["name"] for col in inspector.get_columns("Exercises")}

    with engine.begin() as conn:
        if "intensity" in existing_columns:
            conn.execute(text('ALTER TABLE "Exercises" RENAME TO "Exercises_old"'))
            conn.execute(text(
                'CREATE TABLE "Exercises" ('
                'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                'name VARCHAR NOT NULL, '
                'repetitions INTEGER NOT NULL, '
                'weight FLOAT NOT NULL, '
                'set_label VARCHAR NOT NULL DEFAULT \'1\', '
                'stored_exercise_id INTEGER, '
                'FOREIGN KEY(stored_exercise_id) REFERENCES "StoredExercises"(id)'
                ')'
            ))

            select_parts = ['id', 'name', 'repetitions', 'weight']
            if "set_label" in existing_columns:
                select_parts.append('set_label')
            else:
                select_parts.append("'1'")
            if "stored_exercise_id" in existing_columns:
                select_parts.append('stored_exercise_id')
            else:
                select_parts.append('NULL')

            conn.execute(text(
                f'INSERT INTO "Exercises" (id, name, repetitions, weight, set_label, stored_exercise_id) '
                f'SELECT {", ".join(select_parts)} FROM "Exercises_old"'
            ))
            conn.execute(text('DROP TABLE "Exercises_old"'))
            existing_columns.discard("intensity")
            existing_columns.update({"set_label", "stored_exercise_id"})

        if "set_label" not in existing_columns:
            conn.execute(text('ALTER TABLE "Exercises" ADD COLUMN set_label VARCHAR DEFAULT \'1\''))
        if "stored_exercise_id" not in existing_columns:
            conn.execute(text('ALTER TABLE "Exercises" ADD COLUMN stored_exercise_id INTEGER'))

Session = sessionmaker(bind=engine)
db = Session()

def seed_default_users():
    existing_users = {
        user.email for user in db.query(User).filter(User.email.in_(DEFAULT_EMAILS)).all()
    }

    new_users = []
    for email in DEFAULT_EMAILS:
        if email not in existing_users:
            new_users.append(User(email=email, password=generate_password_hash(DEFAULT_PASSWORD)))

    if not new_users:
        return

    db.add_all(new_users)
    try:
        db.commit()
    except Exception:
        db.rollback()

def is_valid_email(email):
    return bool(EMAIL_REGEX.fullmatch((email or "").strip()))

def is_strong_password(password):
    if not password:
        return False
    if not (8 <= len(password) <= 64):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[^A-Za-z0-9]", password):
        return False
    return True


def normalize_exercise_name(value):
    if not value:
        return ""
    normalized_words = [word.capitalize() for word in value.strip().split() if word]
    return " ".join(normalized_words)


def normalize_set_label(value):
    candidate = (value or "").strip().upper()
    if not candidate:
        return "1"
    if SET_LABEL_PATTERN.fullmatch(candidate):
        return candidate
    return None

ensure_workout_user_column()
ensure_exercise_columns()
seed_default_users()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in flask_session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("main"))
        return f(*args, **kwargs)
    return decorated


def nocache(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        response = make_response(f(*args, **kwargs))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        return response
    return decorated


def current_user_id():
    return flask_session["user_id"]


@app.route("/", methods=["GET", "POST"])
def main():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        if not is_valid_email(email):
            flash("Please enter a valid email address.", "danger")
            return redirect(url_for("main"))

        user = db.query(User).filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            flask_session["user_id"] = user.id
            flask_session.permanent = True
            return redirect(url_for("dashboard"))

        flash("Invalid credentials. Please try again.", "danger")
        return redirect(url_for("main"))

    return render_template(
        "login.html",
        login_reference=url_for("main"),
        register_reference=url_for("register"),
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if not is_valid_email(email):
            flash("Please enter a valid email address.", "danger")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        if not is_strong_password(password):
            flash(PASSWORD_REQUIREMENTS, "danger")
            return redirect(url_for("register"))

        existing = db.query(User).filter_by(email=email).first()
        if existing:
            flash("That email is already registered.", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password)
        db.add(new_user)
        db.commit()

        flask_session["user_id"] = new_user.id
        flask_session.permanent = True
        return redirect(url_for("dashboard"))

    return render_template(
        "register.html",
        register_reference=url_for("register"),
        login_reference=url_for("main"),
        password_requirements=PASSWORD_REQUIREMENTS,
    )


@app.route("/logout")
@login_required
def logout():
    flask_session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main"))


@app.route("/dashboard", methods=["GET"])
@login_required
@nocache
def dashboard():
    return render_template(
        "dashboard.html",
        calorie_calculator_reference=url_for("calculator"),
        workout_tracker_reference=url_for("workout"),
        nutrition_tracker_reference=url_for("nutrition_tracker"),
        workout_logs_reference=url_for("workout_logs"),
        progress_tracker_reference=url_for("progress_tracker"),
    )


@app.route("/calorie-calculator", methods=["GET"])
@login_required
@nocache
def calculator():
    return render_template("calorie-calculator.html")


@app.route("/nutrition-tracker", methods=["GET"])
@login_required
@nocache
def nutrition_tracker():
    return render_template("nutrition-tracker.html")


@app.route("/workout-tracker", methods=["GET", "POST"])
@login_required
@nocache
def workout():
    user_id = current_user_id()

    stored_exercises = (
        db.query(StoredExercise)
        .filter_by(user_id=user_id)
        .order_by(StoredExercise.name)
        .all()
    )

    if request.method == "POST":
        exercise_name = request.form.get("exercise", "")
        repetitions_value = request.form.get("repetitions", "")
        weight_value = request.form.get("weight", "")
        set_label_value = request.form.get("set_label", "")

        normalized_name = normalize_exercise_name(exercise_name)
        set_label = normalize_set_label(set_label_value)

        if not normalized_name:
            flash("Exercise name cannot be empty.", "danger")
            return redirect(url_for("workout"))

        if set_label is None:
            flash("Set must be a number or W for warmup.", "danger")
            return redirect(url_for("workout"))

        try:
            repetitions = int(repetitions_value)
            weight = float(weight_value)
        except ValueError:
            flash("Reps must be an integer and weight must be a number.", "danger")
            return redirect(url_for("workout"))

        stored_exercise = (
            db.query(StoredExercise)
            .filter_by(user_id=user_id, name=normalized_name)
            .first()
        )

        if not stored_exercise:
            stored_exercise = StoredExercise(user_id=user_id, name=normalized_name)
            db.add(stored_exercise)
            db.flush()

        exercise = Exercise(
            name=normalized_name,
            repetitions=repetitions,
            weight=weight,
            set_label=set_label,
            stored_exercise_id=stored_exercise.id,
        )

        date = datetime.date.today()
        workout_entry = db.query(Workout).filter_by(date=date, user_id=user_id).first()
        if not workout_entry:
            workout_entry = Workout(date=date, user_id=user_id)
            db.add(workout_entry)

        workout_entry.exercises.append(exercise)

        try:
            db.commit()
            return redirect(url_for("dashboard"))
        except Exception as exc:
            db.rollback()
            app.logger.exception("Failed to log workout")
            return "There was an issue adding your workout", 500

    return render_template(
        "workout-tracker.html",
        stored_exercises=[se.name for se in stored_exercises],
    )


@app.route("/workout-logs", methods=["GET"])
@login_required
@nocache
def workout_logs():
    return render_template("workout-logs.html")


@app.route("/progress-tracker", methods=["GET"])
@login_required
@nocache
def progress_tracker():
    user_id = current_user_id()

    exercises = (
        db.query(StoredExercise)
        .filter_by(user_id=user_id)
        .order_by(StoredExercise.name)
        .all()
    )

    return render_template("progress-tracker.html", exercises=exercises)


@app.route("/progress-tracker/exercise/<int:stored_exercise_id>", methods=["GET"])
@login_required
@nocache
def progress_tracker_exercise_detail(stored_exercise_id):
    user_id = current_user_id()

    exercise = (
        db.query(StoredExercise)
        .filter_by(id=stored_exercise_id, user_id=user_id)
        .first()
    )

    if not exercise:
        flash("Exercise not found.", "warning")
        return redirect(url_for("progress_tracker"))

    daily_max_1rm = {}
    strongest_set = None
    heaviest_set = None
    for log in exercise.logs:
        if not log.workouts:
            continue
        workout = log.workouts[0]
        if workout.user_id != user_id:
            continue
        date_key = workout.date.isoformat()
        reps = log.repetitions or 0
        weight = log.weight or 0.0
        one_rm = weight * (1 + reps / 30)
        existing = daily_max_1rm.get(date_key)
        if existing is None or one_rm > existing:
            daily_max_1rm[date_key] = one_rm

        if strongest_set is None or one_rm > strongest_set["one_rm"]:
            strongest_set = {
                "date": date_key,
                "weight": weight,
                "reps": reps,
                "one_rm": round(one_rm, 2),
            }

        if heaviest_set is None or weight > heaviest_set["weight"]:
            heaviest_set = {
                "date": date_key,
                "weight": weight,
                "reps": reps,
            }

    chart_data = [
        {"date": date, "one_rm": round(value, 2)}
        for date, value in sorted(daily_max_1rm.items())
    ]

    return render_template(
        "progress-tracker-detail.html",
        exercise=exercise,
        chart_data=chart_data,
        strongest_set=strongest_set,
        heaviest_set=heaviest_set,
    )


@app.route("/api/workouts", methods=["GET"])
@login_required
def get_workouts():
    user_id = current_user_id()
    workouts = (
        db.query(Workout)
        .filter_by(user_id=user_id)
        .order_by(Workout.date.desc())
        .all()
    )
    return jsonify([w.to_dict() for w in workouts])


@app.route("/api/exercises/<int:exercise_id>", methods=["DELETE"])
@login_required
def delete_exercise(exercise_id):
    user_id = current_user_id()
    exercise = (
        db.query(Exercise)
        .join(workout_exercise_table)
        .join(Workout)
        .filter(Exercise.id == exercise_id, Workout.user_id == user_id)
        .first()
    )
    if not exercise:
        return jsonify({"error": "Exercise not found."}), 404

    exercise.workouts = []
    db.delete(exercise)
    try:
        db.commit()
    except Exception:
        db.rollback()
        return jsonify({"error": "Failed to remove exercise."}), 500

    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True)
