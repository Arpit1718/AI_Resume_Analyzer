from dotenv import load_dotenv

load_dotenv()  # must run before importing modules that read environment variables

import os
import json

import PyPDF2
import docx
from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

from db import Base, engine, SessionLocal
import models
from ai import analyze_resume

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # reject uploads over 5 MB

Base.metadata.create_all(bind=engine)


# Home
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")


# Sign up
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email:
            return render_template("signup.html", error="Enter your email.")

        if len(password) < 8:
            return render_template("signup.html", error="Password must be at least 8 characters.")

        with SessionLocal() as db:
            existing_user = db.query(models.User).filter_by(email=email).first()
            if existing_user:
                return render_template("signup.html", error="An account with this email already exists.")

            user = models.User(
                email=email,
                password=generate_password_hash(password),  # store the hash, never the password
            )
            db.add(user)
            db.commit()

        return redirect("/login")

    return render_template("signup.html")


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with SessionLocal() as db:
            user = db.query(models.User).filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user"] = user.email
            return redirect("/dashboard")

        return render_template("login.html", error="Wrong email or password.")

    return render_template("login.html")


# Dashboard
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    result = None

    if request.method == "POST":
        user_goal = request.form.get("role", "").strip()
        resume_text = request.form.get("resume", "").strip()
        file = request.files.get("file")

        # File handling: an uploaded file replaces any pasted text
        if file and file.filename:
            name = file.filename.lower()
            try:
                if name.endswith(".pdf"):
                    reader = PyPDF2.PdfReader(file)
                    resume_text = "".join(p.extract_text() or "" for p in reader.pages).strip()
                elif name.endswith(".docx"):
                    document = docx.Document(file)
                    resume_text = "\n".join(p.text for p in document.paragraphs).strip()
                else:
                    result = {"error": "Only PDF and DOCX files are supported."}
            except Exception as e:
                app.logger.error("File read error: %s", e)
                result = {"error": "We couldn't read that file. Try another file or paste the text."}

        if result is None:
            if not user_goal or not resume_text:
                result = {"error": "Enter a target role and add your resume as a file or as text."}
            else:
                result = analyze_resume(resume_text, user_goal)

                if "error" in result:
                    # Log the real error, show the user a safe message, don't save to the database
                    app.logger.error("AI error: %s", result["error"])
                    result = {"error": "The analysis failed. Please try again in a minute."}
                else:
                    with SessionLocal() as db:
                        user = db.query(models.User).filter_by(email=session["user"]).first()
                        if user is None:
                            session.pop("user", None)
                            return redirect("/login")

                        db.add(models.Report(
                            user_id=user.id,
                            resume_text=resume_text,
                            result=json.dumps(result),
                        ))
                        db.commit()

    return render_template("dashboard.html", user=session["user"], result=result)


# History
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    parsed_reports = []

    with SessionLocal() as db:
        user = db.query(models.User).filter_by(email=session["user"]).first()
        if user is None:
            session.pop("user", None)
            return redirect("/login")

        reports = (
            db.query(models.Report)
            .filter_by(user_id=user.id)
            .order_by(models.Report.id.desc())  # newest first
            .all()
        )

        # Convert the saved JSON string back into a dict
        for r in reports:
            try:
                parsed_result = json.loads(r.result)
            except (TypeError, json.JSONDecodeError):
                parsed_result = {}

            parsed_reports.append({
                "resume": r.resume_text or "",
                "result": parsed_result,
            })

    return render_template("history.html", reports=parsed_reports)


# Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


if __name__ == "__main__":
    # Debug mode is for local development only; turn it off when deploying
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")