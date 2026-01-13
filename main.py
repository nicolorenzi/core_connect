from flask import Flask, render_template, url_for, request, jsonify, redirect, flash
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user_model import Base, User
from models.workout_model import Workout, Exercise
import datetime


app = Flask(__name__)
app.secret_key = "pass"

engine = create_engine("sqlite:///users.db", echo=True)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
db_session = Session()

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db_session.get(User, int(user_id))


@app.route("/", methods=["GET"])
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = db_session.query(User).filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid credentials. Please try again.", "danger")

    return render_template("login.html", login_reference=url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if db_session.query(User).filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        user = User(username=username, email=email)
        user.set_password(password)

        db_session.add(user)
        db_session.commit()

        login_user(user)
        return redirect(url_for("dashboard"))

    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    return render_template("dashboard.html", calorie_calculator_reference=url_for("calculator"), workout_tracker_reference=url_for("workout"), progress_tracker_reference=url_for("progress_tracker"))

@app.route("/calorie-calculator", methods=["GET"])
@login_required
def calculator():
    return render_template("calorie-calculator.html")

@app.route("/workout-tracker", methods=["GET", "POST"])
@login_required
def workout():
    if (request.method == "POST"):
        exercise_name = request.form["exercise"]
        reps = request.form['repetitions']
        exercise_weight = request.form['weight']
        intensity_level = request.form['intensity']

        exercise = Exercise(name=exercise_name, 
                            repetitions=reps,
                            weight=exercise_weight,
                            intensity=intensity_level)
        
        date = datetime.date.today()
        workout = session.query(Workout).filter_by(date=date).first()
        if not (workout):
            workout = Workout(date=date)
            session.add(workout)

        workout.exercises.append(exercise)

        try: 
            session.commit()
            return redirect(url_for("dashboard"))
        except:
            return 'There was an issue adding your workout'


    return render_template("workout-tracker.html")

@app.route("/progress-tracker", methods=["GET"])
@login_required
def progress_tracker():
    print("Navigating to progress tracker page")
    return render_template("progress-tracker.html")

@app.route("/api/workouts", methods=["GET"])
@login_required
def get_workouts():
    workouts = session.query(Workout).order_by(Workout.date.desc()).all()
    return jsonify([w.to_dict() for w in workouts])


if __name__ == "__main__":
    app.run(debug=True)