"""
SkillSync — AI-Based Internship Recommendation Engine for PM Internship Scheme
Flask web app implementing every module from the project PPT:
  1. Text Extraction     4. Semantic Similarity (SBERT)
  2. Formatting Check     5. Skill Gap Detection
  3. Keyword Matching     6. Gemini AI Layer (summary, explanations, chatbot, interview)
Plus:
  - Domain selection, Internship Recommendation, Mock Interview + Assessment report.
  - User Authentication (Login, Logout, Signup) with secure password hashing.
  - User Dashboard tracking ATS scores and mock interview performance history.
"""
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from pathlib import Path
from urllib.parse import urlparse, urljoin

PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DATA_DIR = PROJECT_ROOT / "data"

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except Exception:
    pass  # .env file unreadable — use fallback below

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    flash,
)

from backend import db
from backend.utils.resume_parser import extract_text_from_pdf, check_formatting
from backend.utils.scorer import (
    keyword_match,
    semantic_similarity,
    skill_gap,
    compute_ats_score,
    rank_internships_for_resume,
)
from backend.utils.skills_data import DOMAINS, INTERVIEW_QUESTIONS
from backend.utils import gemini_helper
from backend.utils.aicte_internships import get_recommendations

app = Flask(
    __name__,
    template_folder=str(FRONTEND_DIR / "templates"),
    static_folder=str(FRONTEND_DIR / "static"),
    static_url_path="/static",
)
app.secret_key = os.environ.get("SECRET_KEY", "skillsync-dev-secret-key-change-in-prod")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB upload limit
# Firebase's web configuration is intentionally safe to expose in the browser.
# Keep the values in environment variables in production so a deployment can use
# a different Firebase project without a code change.
app.config["FIREBASE_CONFIG"] = {
    "apiKey": os.environ.get("FIREBASE_API_KEY", "AIzaSyDGTw51opzCyTk3I_yZaXTrVKngHOWesB4"),
    "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN", "skillsync-f84cb.firebaseapp.com"),
    "projectId": os.environ.get("FIREBASE_PROJECT_ID", "skillsync-f84cb"),
    "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET", "skillsync-f84cb.firebasestorage.app"),
    "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID", "144312228609"),
    "appId": os.environ.get("FIREBASE_APP_ID", "1:144312228609:web:f8ddb11ad7a5c28eb31900"),
    "measurementId": os.environ.get("FIREBASE_MEASUREMENT_ID", "G-W0JTGCTHJL"),
}

# Initialize SQLite database schema
db.init_db(app)

UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# In-memory store for active session analysis
ANALYSES = {}


# -----------------------------------------------------------------------------
# Auth Helpers & Middleware
# -----------------------------------------------------------------------------

def is_safe_url(target):
    """Ensure a redirection target is safe and belongs to the same host."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def login_required(f):
    """Decorator to require login on protected views."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_current_user():
    """Inject current authenticated user into all Jinja templates."""
    user_id = session.get("user_id")
    if user_id:
        user = db.get_user_by_id(user_id)
        return {"current_user": user, "firebase_config": app.config["FIREBASE_CONFIG"]}
    return {"current_user": None, "firebase_config": app.config["FIREBASE_CONFIG"]}


# -----------------------------------------------------------------------------
# Authentication Routes (Signup, Login, Logout, Dashboard)
# -----------------------------------------------------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Create a new user account with validated input and hashed password."""
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        full_name = request.form.get("full_name", "").strip()

        is_valid, error = db.validate_signup_input(
            username, email, password, confirm_password, full_name
        )
        if not is_valid:
            flash(error, "error")
            return render_template(
                "signup.html",
                username=username,
                email=email,
                full_name=full_name,
            ), 400

        user = db.create_user(username, email, password, full_name)
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome to SkillSync, {user['full_name'] or user['username']}! You can now check your resume or practice interviews.", "success")
            return redirect(url_for("index"))
        else:
            flash("An unexpected error occurred while creating your account. Please try again.", "error")
            return render_template(
                "signup.html",
                username=username,
                email=email,
                full_name=full_name,
            ), 500

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate existing users with username/email and password."""
    if "user_id" in session:
        return redirect(url_for("index"))

    next_url = request.args.get("next") or request.form.get("next")

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        if not identifier or not password:
            flash("Please enter both your username/email and password.", "error")
            return render_template("login.html", identifier=identifier, next=next_url), 400

        user = db.authenticate_user(identifier, password)
        if not user:
            flash("Invalid username/email or password.", "error")
            return render_template("login.html", identifier=identifier, next=next_url), 401

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        flash(f"Welcome back, {user['full_name'] or user['username']}!", "success")

        if next_url and is_safe_url(next_url):
            return redirect(next_url)
        return redirect(url_for("index"))

    return render_template("login.html", next=next_url)


@app.route("/logout")
def logout():
    """Clear the user session and sign out."""
    session.pop("user_id", None)
    session.pop("username", None)
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    """User profile dashboard displaying past analyses, interview history, and applications."""
    user = db.get_user_by_id(session["user_id"])
    stats = db.get_user_stats(session["user_id"])
    analyses = db.get_user_analyses(session["user_id"], limit=10)
    interviews = db.get_user_interviews(session["user_id"], limit=10)
    applications = db.get_user_applications(session["user_id"], limit=10)
    return render_template(
        "dashboard.html",
        user=user,
        stats=stats,
        analyses=analyses,
        interviews=interviews,
        applications=applications,
    )


@app.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    """Collect a student's 1-5 star rating and optional SkillSync feedback."""
    if request.method == "POST":
        rating = request.form.get("rating")
        message = request.form.get("message", "").strip()

        if len(message) > 1000:
            flash("Feedback must be 1000 characters or fewer.", "error")
            return render_template("feedback.html", rating=rating, message=message), 400

        if not db.save_feedback(session.get("user_id"), rating, message):
            flash("Please select a star rating from 1 to 5.", "error")
            return render_template("feedback.html", rating=rating, message=message), 400

        flash("Thank you! Your feedback has been saved.", "success")
        return redirect(url_for("feedback"))

    return render_template("feedback.html")


# -----------------------------------------------------------------------------
# Core SkillSync Routes (Resume Analysis & Mock Interview)
# -----------------------------------------------------------------------------

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", domains=DOMAINS.keys())


@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    domain = request.form.get("domain")
    resume_file = request.files.get("resume")

    if not domain or domain not in DOMAINS:
        return render_template("index.html", domains=DOMAINS.keys(), error="Please choose a valid domain.")
    if not resume_file or resume_file.filename == "":
        return render_template("index.html", domains=DOMAINS.keys(), error="Please upload a resume PDF.")
    if not resume_file.filename.lower().endswith(".pdf"):
        return render_template("index.html", domains=DOMAINS.keys(), error="Please upload a PDF file.")

    # 1. Text Extraction
    resume_text = extract_text_from_pdf(resume_file.stream)
    if not resume_text.strip():
        return render_template("index.html", domains=DOMAINS.keys(),
                                error="Couldn't read text from that PDF — try a text-based (not scanned) resume.")

    # 2. Formatting Check
    formatting = check_formatting(resume_text)

    role_data = DOMAINS[domain]

    # 3. Keyword Matching
    km = keyword_match(resume_text, role_data["skills"])

    # 5. Skill Gap Detection
    gap = skill_gap(km["matched"], km["missing"])

    # Semantic scoring, optional Gemini feedback, and public internship lookup
    # do not depend on each other.  Run them together so the user waits for the
    # slowest service, rather than the combined time of all four operations.
    # The displayed score and recommendation data are unchanged.
    with ThreadPoolExecutor(max_workers=4) as executor:
        semantic_future = executor.submit(
            semantic_similarity,
            resume_text,
            role_data["description"],
            role_data["skills"],
        )
        summary_future = executor.submit(
            gemini_helper.generate_resume_summary, resume_text, domain
        )
        gap_explanation_future = executor.submit(
            gemini_helper.explain_skill_gaps, gap["missing"], domain
        )
        internships_future = executor.submit(get_recommendations, domain)

        sem = semantic_future.result()
        summary = summary_future.result()
        gap_explanation = gap_explanation_future.result()
        live_internships = internships_future.result()

    # Hybrid ATS score
    ats_score = compute_ats_score(km["score"], sem["score"])

    analysis_id = str(uuid.uuid4())
    ANALYSES[analysis_id] = {
        "resume_text": resume_text,
        "domain": domain,
        "matched": gap["matched"],
        "missing": gap["missing"],
    }
    session["analysis_id"] = analysis_id
    session["domain"] = domain

    # Persist analysis to database for logged in user
    user_id = session.get("user_id")
    if user_id:
        db.save_resume_analysis(
            user_id=user_id,
            analysis_id=analysis_id,
            domain=domain,
            ats_score=ats_score,
            keyword_score=km["score"],
            semantic_score=sem["score"],
            matched_skills=gap["matched"],
            missing_skills=gap["missing"],
        )

    # Use only public, currently open AICTE listings.  Each details URL is
    # verified against AICTE's individual-listing endpoint before display.
    ranked_internships = rank_internships_for_resume(live_internships, gap["matched"])
    applied_ids = db.get_user_applied_ids(user_id) if user_id else set()

    return render_template(
        "result.html",
        domain=domain,
        ats_score=ats_score,
        keyword_score=km["score"],
        semantic_score=sem["score"],
        semantic_engine=sem["engine"],
        matched=gap["matched"],
        missing=gap["missing"],
        formatting=formatting,
        summary=summary,
        gap_explanation=gap_explanation,
        internships=ranked_internships,
        applied_ids=applied_ids,
        analysis_id=analysis_id,
    )


@app.route("/apply/<internship_id>", methods=["POST"])
@login_required
def apply_internship(internship_id):
    """Save an official listing locally; applications stay on the AICTE portal."""
    user_id = session.get("user_id")
    title = request.form.get("title", "Internship Role")
    company = request.form.get("company", "AICTE Partner")
    portal_type = request.form.get("portal_type", "AICTE Portal")
    stipend = request.form.get("stipend", "")
    location = request.form.get("location", "")
    portal_url = request.form.get("portal_url", "https://internship.aicte-india.org/")

    is_new = db.save_application(
        user_id=user_id,
        internship_id=internship_id,
        title=title,
        company=company,
        portal_type=portal_type,
        stipend=stipend,
        location=location,
    )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify({
            "success": True,
            "already_applied": not is_new,
            "portal_url": portal_url,
            "message": f"Saved '{title}' to your SkillSync dashboard. Open the official details page to apply on AICTE.",
        })

    if is_new:
        flash(f"Saved '{title}' at {company}. Open the official AICTE details page to apply.", "success")
    else:
        flash(f"'{title}' is already saved in your dashboard.", "info")

    return redirect(request.referrer or url_for("dashboard"))


@app.route("/chatbot", methods=["POST"])
@login_required
def chatbot():
    data = request.get_json(force=True)
    message = (data or {}).get("message", "").strip()
    analysis_id = session.get("analysis_id")
    analysis = ANALYSES.get(analysis_id, {})

    if not message:
        return jsonify({"reply": "Ask me anything about your resume or the internship role!"})

    context = ""
    if analysis:
        context = (
            f"Domain: {analysis.get('domain')}. "
            f"Matched skills: {', '.join(analysis.get('matched', [])) or 'none'}. "
            f"Missing skills: {', '.join(analysis.get('missing', [])) or 'none'}."
        )
    reply = gemini_helper.chatbot_reply(message, context)
    return jsonify({"reply": reply})


@app.route("/interview")
@login_required
def interview_start():
    return render_template("interview.html", domains=DOMAINS.keys(), question=None)


@app.route("/interview/begin", methods=["POST"])
@login_required
def interview_begin():
    domain = request.form.get("domain")
    if domain not in DOMAINS:
        return redirect(url_for("interview_start"))
    session["interview_domain"] = domain
    session["interview_index"] = 0
    session["interview_qa"] = []
    return redirect(url_for("interview_question"))


@app.route("/interview/question")
@login_required
def interview_question():
    domain = session.get("interview_domain")
    idx = session.get("interview_index", 0)
    if not domain:
        return redirect(url_for("interview_start"))

    questions = INTERVIEW_QUESTIONS.get(domain, [])
    if idx >= len(questions):
        return redirect(url_for("interview_report"))

    return render_template(
        "interview.html",
        domains=DOMAINS.keys(),
        question=questions[idx],
        q_num=idx + 1,
        q_total=len(questions),
        domain=domain,
    )


@app.route("/interview/answer", methods=["POST"])
@login_required
def interview_answer():
    domain = session.get("interview_domain")
    idx = session.get("interview_index", 0)
    questions = INTERVIEW_QUESTIONS.get(domain, [])
    if not domain or idx >= len(questions):
        return redirect(url_for("interview_start"))

    answer = request.form.get("answer", "").strip()
    question = questions[idx]

    # Response Analysis + Communication Scoring + Technical Skill Assessment
    result = gemini_helper.evaluate_interview_answer(question, answer, domain)

    qa = session.get("interview_qa", [])
    qa.append([question, answer, result["score"], result["feedback"]])
    session["interview_qa"] = qa
    session["interview_index"] = idx + 1

    return redirect(url_for("interview_question"))


@app.route("/interview/report")
@login_required
def interview_report():
    domain = session.get("interview_domain")
    qa = session.get("interview_qa", [])
    if not domain or not qa:
        return redirect(url_for("interview_start"))

    avg_score = round(sum(item[2] for item in qa) / len(qa), 1)
    report = gemini_helper.generate_final_report(domain, [(q, a, s) for q, a, s, _ in qa])

    # Persist interview to database if user is logged in
    user_id = session.get("user_id")
    if user_id:
        db.save_interview_session(
            user_id=user_id,
            domain=domain,
            avg_score=avg_score,
            qa_list=qa,
            report_text=report,
        )

    return render_template(
        "interview_result.html",
        domain=domain,
        qa=qa,
        avg_score=avg_score,
        report=report,
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
