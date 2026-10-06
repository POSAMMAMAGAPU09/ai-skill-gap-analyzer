from flask import Flask, render_template, request, send_file, redirect, url_for, session
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


app = Flask(__name__)

app.secret_key = "ai-skill-gap-secret-key"


# --------------------------------------------------
# FOLDERS
# --------------------------------------------------

UPLOAD_FOLDER = "uploads"
REPORT_FOLDER = "reports"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)


# --------------------------------------------------
# JOB SKILLS
# --------------------------------------------------

JOB_SKILLS = {

    "Frontend Developer":
        ["HTML", "CSS", "JavaScript", "React", "Git"],

    "Python Developer":
        ["Python", "SQL", "Git", "Flask", "Django"],

    "Data Analyst":
        ["Python", "SQL", "Excel", "Power BI", "Statistics"],

    "Embedded Engineer":
        ["C", "C++", "Microcontrollers",
         "Embedded Systems", "Arduino"],

    "AI/ML Engineer":
        ["Python", "Machine Learning",
         "Deep Learning", "TensorFlow", "SQL"]

}


# --------------------------------------------------
# RECOMMENDATIONS
# --------------------------------------------------

RECOMMENDATIONS = {

    "HTML": "Learn HTML structure, forms, tables and semantic elements.",

    "CSS": "Learn CSS layouts, Flexbox, Grid and responsive design.",

    "JavaScript": "Learn JavaScript fundamentals, DOM and events.",

    "React": "Learn React components, props, state and hooks.",

    "Git": "Learn Git commands, repositories and version control.",

    "Python": "Practice Python syntax, functions, lists and dictionaries.",

    "SQL": "Learn SQL queries, SELECT, JOIN, GROUP BY and databases.",

    "Flask": "Learn Flask routing, templates, forms and APIs.",

    "Django": "Learn Django models, views, URLs and templates.",

    "Excel": "Learn Excel formulas, charts, sorting and filtering.",

    "Power BI": "Learn Power BI dashboards, reports and data visualization.",

    "Statistics": "Learn averages, probability and basic statistics.",

    "C": "Learn C programming, pointers, arrays and functions.",

    "C++": "Learn C++ classes, objects and object-oriented programming.",

    "Microcontrollers": "Learn microcontroller architecture and programming.",

    "Embedded Systems": "Learn embedded hardware and software concepts.",

    "Arduino": "Learn Arduino programming and sensor projects.",

    "Machine Learning": "Learn supervised learning, classification and regression.",

    "Deep Learning": "Learn neural networks and deep learning fundamentals.",

    "TensorFlow": "Learn TensorFlow models, tensors and neural networks."

}


# --------------------------------------------------
# LEARNING PLANS
# --------------------------------------------------

LEARNING_PLANS = {

    "Frontend Developer":
        "Practice HTML, CSS and JavaScript by building responsive web projects.",

    "Python Developer":
        "Practice Python, SQL and Flask by building backend applications.",

    "Data Analyst":
        "Practice Python, SQL, Excel and Power BI using real datasets.",

    "Embedded Engineer":
        "Practice C, C++ and Arduino through microcontroller projects.",

    "AI/ML Engineer":
        "Practice Python, Machine Learning and Deep Learning through projects."

}


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def init_db():

    connection = sqlite3.connect("users.db")

    cursor = connection.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0
)
    """)

    # Analysis history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job TEXT NOT NULL,
            match_percentage INTEGER NOT NULL,
            skills_found TEXT,
            missing_skills TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    connection.commit()

    connection.close()

init_db()


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():

    return render_template("index.html")


# --------------------------------------------------
# REGISTER PAGE
# --------------------------------------------------

@app.route("/register")
def register():

    return render_template("register.html")


# --------------------------------------------------
# REGISTER USER
# --------------------------------------------------

@app.route("/register", methods=["POST"])
def register_user():

    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    hashed_password = generate_password_hash(password)

    try:

        connection = sqlite3.connect("users.db")

        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hashed_password)
        )

        connection.commit()

        connection.close()

        return redirect(url_for("login"))

    except sqlite3.IntegrityError:

        return """
        <h2>Email already registered.</h2>
        <a href="/register">Try again</a>
        """


# --------------------------------------------------
# LOGIN PAGE
# --------------------------------------------------

@app.route("/login")
def login():

    return render_template("login.html")


# --------------------------------------------------
# LOGIN USER
# --------------------------------------------------

@app.route("/login", methods=["POST"])
def login_user():

    email = request.form["email"]
    password = request.form["password"]

    connection = sqlite3.connect("users.db")

    cursor = connection.cursor()

    cursor.execute(
    "SELECT id, name, email, password, is_admin FROM users WHERE email = ?",
    (email,)
)

    user = cursor.fetchone()

    connection.close()

    if user and check_password_hash(user[3], password):

        session["user_id"] = user[0]
        session["user_name"] = user[1]
        session["user_email"] = user[2]
        session["is_admin"]=user[4]

        return redirect(url_for("home"))

    return """
    <h2>Invalid email or password.</h2>
    <a href="/login">Try again</a>
    """


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    # Total analyses
    cursor.execute("""
        SELECT COUNT(*)
        FROM analysis_history
        WHERE user_id = ?
    """, (session["user_id"],))

    total_analyses = cursor.fetchone()[0]

    # Average skill match
    cursor.execute("""
        SELECT AVG(match_percentage)
        FROM analysis_history
        WHERE user_id = ?
    """, (session["user_id"],))

    average_result = cursor.fetchone()[0]

    if average_result is not None:
        average_score = round(average_result)
    else:
        average_score = 0

    # Latest target job
    cursor.execute("""
        SELECT job
        FROM analysis_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (session["user_id"],))

    latest_result = cursor.fetchone()

    if latest_result:
        latest_job = latest_result[0]
    else:
        latest_job = "None"

    # Recent analyses
    cursor.execute("""
        SELECT *
        FROM analysis_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 5
    """, (session["user_id"],))

    recent_analyses = cursor.fetchall()

    connection.close()

    return render_template(
        "dashboard.html",
        total_analyses=total_analyses,
        average_score=average_score,
        latest_job=latest_job,
        recent_analyses=recent_analyses
    )
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))

@app.route("/history")
def history():

    # User must be logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    # HOST / ADMIN
    if session.get("is_admin") == 1:

        cursor.execute("""
            SELECT
                analysis_history.*,
                users.name,
                users.email
            FROM analysis_history
            JOIN users
            ON analysis_history.user_id = users.id
            ORDER BY analysis_history.created_at DESC
        """)

    # NORMAL USER
    else:

        cursor.execute("""
            SELECT *
            FROM analysis_history
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (session["user_id"],))

    history_data = cursor.fetchall()

    connection.close()

    return render_template(
        "history.html",
        history=history_data,
        is_admin=session.get("is_admin") == 1
    )
# --------------------------------------------------
# ANALYZE RESUME
# --------------------------------------------------

@app.route("/analyze", methods=["POST"])
def analyze():
    if "user_id" not in session:
        return redirect(url_for("login"))

    resume = request.files["resume"]
    job = request.form["job"]

    filename = resume.filename

    file_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    resume.save(file_path)

    reader = PdfReader(file_path)

    resume_text = ""

    for page in reader.pages:

        text = page.extract_text()

        if text:
            resume_text += text + "\n"


    # --------------------------------------------------
    # SKILL MATCHING
    # --------------------------------------------------

    required_skills = JOB_SKILLS.get(job, [])

    skills_found = []
    missing_skills = []

    resume_lower = resume_text.lower()

    for skill in required_skills:

        skill_lower = skill.lower()

        aliases = {
            "javascript": ["javascript", "js"],
            "python": ["python", "python3"],
            "c++": ["c++", "cpp"],
            "machine learning": ["machine learning", "ml"],
            "deep learning": ["deep learning", "dl"],
            "sql": ["sql", "mysql", "postgresql"],
            "microcontrollers": ["microcontrollers", "microcontroller"],
            "embedded systems": ["embedded systems", "embedded"],
            "power bi": ["power bi", "powerbi"]
        }

        keywords = aliases.get(
            skill_lower,
            [skill_lower]
        )

        found = False

        for keyword in keywords:

            if keyword in resume_lower:
                found = True
                break

        if found:

            skills_found.append(skill)

        else:

            missing_skills.append(skill)

    total_skills = len(required_skills)

    if total_skills > 0:

        match_percentage = round(
            (len(skills_found) / total_skills) * 100
        )

    else:

        match_percentage = 0


    # --------------------------------------------------
    # AI ANALYSIS
    # --------------------------------------------------

    if match_percentage >= 80:

        analysis = (
            "Your resume shows strong alignment with the "
            + job
            + " role."
        )

    elif match_percentage >= 50:

        analysis = (
            "Your resume shows a moderate skill match "
            "for the "
            + job
            + " role. Focus on the missing skills."
        )

    else:

        analysis = (
            "Your resume currently has several skill gaps "
            "for the "
            + job
            + " role. Follow the learning plan to improve."
        )


    # --------------------------------------------------
    # RECOMMENDATIONS
    # --------------------------------------------------

    recommendations = {}

    for skill in missing_skills:

        if skill in RECOMMENDATIONS:

            recommendations[skill] = RECOMMENDATIONS[skill]


    learning_plan = LEARNING_PLANS.get(
        job,
        "Build projects and practice the missing skills."
    )


    # --------------------------------------------------
    # SAVE ANALYSIS HISTORY
    # --------------------------------------------------

    if "user_id" in session:

        connection = sqlite3.connect("users.db")

        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO analysis_history
            (user_id, job, match_percentage, skills_found, missing_skills)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            job,
            match_percentage,
            ", ".join(skills_found),
            ", ".join(missing_skills)
        ))

        connection.commit()

        connection.close()


    # --------------------------------------------------
    # RESULT PAGE
    # --------------------------------------------------

    return render_template(
        "result.html",
        job=job,
        job_skills=required_skills,
        skills_found=skills_found,
        missing_skills=missing_skills,
        match_percentage=match_percentage,
        analysis=analysis,
        recommendations=recommendations,
        learning_plan=learning_plan,
        resume_text=resume_text
    )

# --------------------------------------------------
# DOWNLOAD PDF REPORT
# --------------------------------------------------

@app.route("/download_report")
def download_report():

    job = request.args.get("job", "Unknown Job")

    score = request.args.get("score", "0")

    skills = request.args.get("skills", "")

    missing = request.args.get("missing", "")

    report_path = os.path.join(
        REPORT_FOLDER,
        "skill_gap_report.pdf"
    )

    pdf = canvas.Canvas(
        report_path,
        pagesize=A4
    )

    width, height = A4

    y = height - 50


    pdf.setFont("Helvetica-Bold", 20)

    pdf.drawString(
        50,
        y,
        "AI Skill Gap Analyzer Report"
    )

    y -= 40


    pdf.setFont("Helvetica", 12)

    pdf.drawString(
        50,
        y,
        "Target Job: " + job
    )

    y -= 25

    pdf.drawString(
        50,
        y,
        "Skill Match: " + score + "%"
    )

    y -= 40


    pdf.setFont("Helvetica-Bold", 14)

    pdf.drawString(
        50,
        y,
        "Skills Found:"
    )

    y -= 25

    pdf.setFont("Helvetica", 11)

    for skill in skills.split(","):

        if skill.strip():

            pdf.drawString(
                70,
                y,
                "• " + skill.strip()
            )

            y -= 20


    y -= 15

    pdf.setFont("Helvetica-Bold", 14)

    pdf.drawString(
        50,
        y,
        "Missing Skills:"
    )

    y -= 25

    pdf.setFont("Helvetica", 11)

    for skill in missing.split(","):

        if skill.strip():

            pdf.drawString(
                70,
                y,
                "• " + skill.strip()
            )

            y -= 20


    pdf.save()


    return send_file(
        report_path,
        as_attachment=True,
        download_name="skill_gap_report.pdf"
    )


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    app.run(debug=True)