# Core Connect
CoreConnect is a comprehensive fitness application designed to help users monitor their caloric intake, track workouts, and achieve their health goals efficiently, keeping the user motivated and consistent.

---

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Technologies Used](#technologies-used)

---

## Features

- **Caloric Calculator**: Track daily caloric intake goals for each body type.
- **Workout Tracker**: Log workouts with details like type, duration, and calories burned.
- **Nutrition Tracker**: Record meals and snacks to monitor calorie consumption.
- **Workout Logs**: View day-to-day logs to track workouts over time.

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/nicolorenzi/core_connect.git
   cd core_connect
   ```

2. **Create a virtual environment (only needed once):**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   ```bash
   # Mac/Linux:
   source venv/bin/activate
   # Windows:
   .\venv\Scripts\activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create a `.env` file in the project root with the following:**
   ```
   SECRET_KEY=your-long-random-secret-key
   DEFAULT_EMAILS=you@example.com
   DEFAULT_PASSWORD=YourPassword123#
   ```

6. **Run the app:**
   ```bash
   make dev
   ```

7. **Open your browser and navigate to:**
   ```
   http://127.0.0.1:5000
   ```

---

## Technologies Used

- **Frontend:** HTML, CSS, JavaScript, Tailwind CSS
- **Backend:** Flask (Python)
- **Database:** SQLite