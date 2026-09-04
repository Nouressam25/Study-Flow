from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime
from flask import session
import calendar

from config import Config
from models import db, Course, Task, User

from functools import wraps
def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated_function


app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/courses")
@login_required
def courses():

    courses = Course.query.filter_by(
        user_id=session["user_id"]
    ).all()

    return render_template(
        "courses.html",
        courses=courses
    )

@app.route("/courses/add", methods=["GET", "POST"])
@login_required
def add_course():

    if request.method == "POST":

        course_name = request.form.get("name")
        course_color = request.form.get("color")

        new_course = Course(
            name=course_name,
            color=course_color,
            user_id=session["user_id"]
        )

        db.session.add(new_course)
        db.session.commit()

        flash("Course added successfully!", "success")

        return redirect(url_for("courses"))

    return render_template("add_course.html")

@app.route("/courses/delete/<int:id>")
@login_required
def delete_course(id):

    course = Course.query.get_or_404(id)

    db.session.delete(course)

    db.session.commit()

    flash("Course deleted successfully!", "danger")

    return redirect(url_for("courses"))

@app.route("/courses/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_course(id):

    course = Course.query.get_or_404(id)

    if request.method == "POST":

        course_name = request.form.get("name")
        course_color = request.form.get("color")

        course.name = course_name
        course.color = course_color

        db.session.commit()

        flash("Course updated successfully!", "info")

        return redirect(url_for("courses"))

    return render_template(
        "edit_course.html",
        course=course
    )

@app.route("/courses/<int:id>/tasks")
@login_required
def course_tasks(id):

    course = Course.query.get_or_404(id)

    return render_template(
        "tasks.html",
        course=course
    )

@app.route("/tasks")
@login_required
def all_tasks():

    tasks = Task.query.join(Course).filter(
        Course.user_id == session["user_id"]
    ).all()

    return render_template(
        "all_tasks.html",
        tasks=tasks
    )

@app.route("/courses/<int:id>/tasks/add", methods=["GET", "POST"])
@login_required
def add_task(id):

    course = Course.query.get_or_404(id)

    if request.method == "POST":

        task_title = request.form.get("title")

        due_date = datetime.strptime(
            request.form.get("due_date"),
            "%Y-%m-%d"
        ).date()

        new_task = Task(
            title=task_title,
            due_date=due_date
        )

        course.tasks.append(new_task)

        db.session.commit()

        flash("Task added successfully!", "success")

        return redirect(
            url_for("course_tasks", id=course.id)
        )

    return render_template(
        "add_task.html",
        course=course
    )

@app.route("/tasks/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_task(id):

    task = Task.query.get_or_404(id)

    if request.method == "POST":

        task.title = request.form.get("title")

        task.due_date = datetime.strptime(
            request.form["due_date"],
            "%Y-%m-%d"
        )

        db.session.commit()

        flash("Task updated successfully!", "info")

        return redirect(url_for("course_tasks", id=task.course_id))

    return render_template(
        "edit_task.html",
        task=task
    )

@app.route("/tasks/delete/<int:id>")
@login_required
def delete_task(id):

    task = Task.query.get_or_404(id)

    course_id = task.course_id

    db.session.delete(task)

    db.session.commit()

    flash("Task deleted successfully!", "success")

    return redirect(
        url_for("course_tasks", id=course_id)
    )

@app.route("/tasks/toggle/<int:id>")
@login_required
def toggle_task(id):

    task = Task.query.get_or_404(id)

    task.completed = not task.completed

    db.session.commit()

    return redirect(
        url_for("course_tasks", id=task.course_id)
    )

@app.route("/tasks/completed")
@login_required
def completed_tasks():

    tasks = Task.query.filter(
        Task.completed == True
    ).all()

    return render_template(
        "completed_tasks.html",
        tasks=tasks
    )

@app.route("/calendar")
@login_required
def study_calendar():

    today = datetime.today()

    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)

    prev_month = month - 1
    prev_year = year

    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    next_month = month + 1
    next_year = year

    if next_month == 13:
        next_month = 1
        next_year += 1

    weeks = calendar.monthcalendar(year, month)

    tasks = Task.query.join(Course).filter(
        Course.user_id == session["user_id"]
    ).all()

    return render_template(
        "calendar.html",
        year=year,
        month=month,
        weeks=weeks,
        tasks=tasks,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year

    )

@app.route("/dashboard")
@login_required
def dashboard():

    today = datetime.today().date()

    courses = Course.query.filter_by(
        user_id=session["user_id"]
    ).all()
    course_count = len(courses)

    tasks = Task.query.join(Course).filter(
        Course.user_id == session["user_id"]
    ).all()
    task_count = len(tasks)

    completed_tasks = Task.query.join(Course).filter(
        Course.user_id == session["user_id"],
        Task.completed.is_(True)
    ).all()

    completed_count = len(completed_tasks)

    upcoming_tasks = Task.query.join(Course).filter(
        Course.user_id == session["user_id"],
        Task.due_date >= today,
        Task.completed.is_(False)
    ).order_by(
        Task.due_date.asc()
    ).all()

    return render_template(
        "dashboard.html",
        courses=courses,
        course_count=course_count,
        task_count=task_count,
        completed_count=completed_count,
        upcoming_tasks=upcoming_tasks
    )

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already exists!", "error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully!", "success")

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            session["user_id"] = user.id

            flash("Login successful!", "success")

            return redirect(url_for("dashboard"))

        flash("Invalid email or password!", "error")

    return render_template("login.html")

@app.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully!", "info")

    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)