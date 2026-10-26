"""
Database management module for SkillSync.
Provides SQLite database connection handling, user authentication,
and persistence for resume analyses and mock interviews.
"""

import os
import re
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from flask import g, has_app_context
from werkzeug.security import generate_password_hash, check_password_hash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = str(PROJECT_ROOT / "data" / "skillsync.db")
# India has a fixed UTC+05:30 offset and does not observe daylight saving time.
# Using the standard-library offset keeps the app portable on Windows hosts
# that do not ship the IANA time-zone database.
USAGE_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


def get_db():
    """Get SQLite connection for Flask context or standalone execution."""
    if has_app_context():
        if "db" not in g:
            g.db = sqlite3.connect(DB_PATH)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON;")
        return g.db

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def close_db(e=None):
    """Close the database connection if open."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app=None):
    """Initialize database tables and indexes."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL COLLATE NOCASE,
            email TEXT UNIQUE NOT NULL COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Resume Analyses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resume_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            analysis_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            ats_score INTEGER NOT NULL,
            keyword_score INTEGER NOT NULL,
            semantic_score INTEGER NOT NULL,
            matched_skills TEXT,
            missing_skills TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    # Interview Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            domain TEXT NOT NULL,
            avg_score REAL NOT NULL,
            qa_json TEXT,
            report_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    # Internship Applications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS internship_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            internship_id TEXT NOT NULL,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            portal_type TEXT NOT NULL,
            stipend TEXT,
            location TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    # Student feedback submitted from the in-app Feedback page.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    # Stored server-side so a page refresh or new browser tab cannot bypass
    # the per-user Gemini chatbot limit.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chatbot_daily_usage (
            user_id INTEGER NOT NULL,
            usage_date TEXT NOT NULL,
            message_count INTEGER NOT NULL DEFAULT 0 CHECK (message_count >= 0),
            PRIMARY KEY (user_id, usage_date),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_user ON resume_analyses(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_interviews_user ON interview_sessions(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_apps_user ON internship_applications(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id);")

    conn.commit()
    conn.close()

    if app is not None:
        app.teardown_appcontext(close_db)


# Validation helpers
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_.-]{3,30}$")


def validate_signup_input(username, email, password, confirm_password, full_name=None):
    """
    Validate user signup inputs.
    Returns (is_valid: bool, error_message: str or None)
    """
    username = (username or "").strip()
    email = (email or "").strip().lower()
    password = password or ""
    confirm_password = confirm_password or ""

    if not username:
        return False, "Username is required."
    if not USERNAME_REGEX.match(username):
        return False, "Username must be 3-30 characters and contain only letters, numbers, dashes, or underscores."

    if not email:
        return False, "Email address is required."
    if not EMAIL_REGEX.match(email):
        return False, "Please enter a valid email address."

    if not password:
        return False, "Password is required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."

    if password != confirm_password:
        return False, "Passwords do not match."

    # Check database for existing username or email
    db = get_db()
    existing_user = db.execute(
        "SELECT id, username, email FROM users WHERE username = ? OR email = ?",
        (username, email)
    ).fetchone()

    if existing_user:
        if existing_user["username"].lower() == username.lower():
            return False, "Username is already taken. Please choose another."
        if existing_user["email"].lower() == email:
            return False, "An account with this email already exists."

    return True, None


def create_user(username, email, password, full_name=None):
    """
    Create a new user with hashed password.
    Returns the newly created user dict or None if creation failed.
    """
    username = username.strip()
    email = email.strip().lower()
    full_name = full_name.strip() if full_name else None
    password_hash = generate_password_hash(password)

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO users (username, email, password_hash, full_name)
        VALUES (?, ?, ?, ?)
        """,
        (username, email, password_hash, full_name)
    )
    db.commit()
    user_id = cursor.lastrowid
    return get_user_by_id(user_id)


def authenticate_user(identifier, password):
    """
    Authenticate a user by username or email and password.
    Returns user row if valid, None otherwise.
    """
    identifier = (identifier or "").strip()
    if not identifier or not password:
        return None

    db = get_db()
    user = db.execute(
        """
        SELECT * FROM users
        WHERE username = ? OR email = ?
        """,
        (identifier, identifier.lower())
    ).fetchone()

    if user and check_password_hash(user["password_hash"], password):
        return user
    return None


def get_user_by_id(user_id):
    """Fetch user by primary key ID."""
    if not user_id:
        return None
    db = get_db()
    return db.execute(
        "SELECT id, username, email, full_name, created_at FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()


def get_user_by_username(username):
    """Fetch user by username."""
    if not username:
        return None
    db = get_db()
    return db.execute(
        "SELECT id, username, email, full_name, created_at FROM users WHERE username = ?",
        (username.strip(),)
    ).fetchone()


def get_user_by_email(email):
    """Fetch user by email."""
    if not email:
        return None
    db = get_db()
    return db.execute(
        "SELECT id, username, email, full_name, created_at FROM users WHERE email = ?",
        (email.strip().lower(),)
    ).fetchone()


# History persistence functions
def save_resume_analysis(user_id, analysis_id, domain, ats_score, keyword_score, semantic_score, matched_skills, missing_skills):
    """Record a resume evaluation for a user."""
    if not user_id:
        return None
    db = get_db()
    db.execute(
        """
        INSERT INTO resume_analyses (
            user_id, analysis_id, domain, ats_score, keyword_score, semantic_score,
            matched_skills, missing_skills
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            analysis_id,
            domain,
            int(ats_score),
            int(keyword_score),
            int(semantic_score),
            json.dumps(matched_skills or []),
            json.dumps(missing_skills or [])
        )
    )
    db.commit()


def get_user_analyses(user_id, limit=20):
    """Retrieve past resume analyses for a user."""
    if not user_id:
        return []
    db = get_db()
    rows = db.execute(
        """
        SELECT * FROM resume_analyses
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (user_id, limit)
    ).fetchall()

    result = []
    for r in rows:
        item = dict(r)
        try:
            item["matched_skills"] = json.loads(item["matched_skills"])
        except Exception:
            item["matched_skills"] = []
        try:
            item["missing_skills"] = json.loads(item["missing_skills"])
        except Exception:
            item["missing_skills"] = []
        result.append(item)
    return result


def save_interview_session(user_id, domain, avg_score, qa_list, report_text):
    """Record an interview session for a user."""
    if not user_id:
        return None
    db = get_db()
    db.execute(
        """
        INSERT INTO interview_sessions (
            user_id, domain, avg_score, qa_json, report_text
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            domain,
            float(avg_score),
            json.dumps(qa_list or []),
            report_text or ""
        )
    )
    db.commit()


def get_user_interviews(user_id, limit=20):
    """Retrieve past interview sessions for a user."""
    if not user_id:
        return []
    db = get_db()
    rows = db.execute(
        """
        SELECT * FROM interview_sessions
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (user_id, limit)
    ).fetchall()

    result = []
    for r in rows:
        item = dict(r)
        try:
            item["qa_list"] = json.loads(item["qa_json"])
        except Exception:
            item["qa_list"] = []
        result.append(item)
    return result


def get_user_stats(user_id):
    """Compute dashboard statistics for a user."""
    if not user_id:
        return {"total_resumes": 0, "total_interviews": 0, "avg_ats": 0, "avg_interview": 0, "total_applications": 0}

    db = get_db()
    resumes_stat = db.execute(
        "SELECT COUNT(*) as count, AVG(ats_score) as avg_ats FROM resume_analyses WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    interviews_stat = db.execute(
        "SELECT COUNT(*) as count, AVG(avg_score) as avg_score FROM interview_sessions WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    apps_stat = db.execute(
        "SELECT COUNT(*) as count FROM internship_applications WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    return {
        "total_resumes": resumes_stat["count"] if resumes_stat else 0,
        "avg_ats": round(resumes_stat["avg_ats"], 1) if (resumes_stat and resumes_stat["avg_ats"] is not None) else 0,
        "total_interviews": interviews_stat["count"] if interviews_stat else 0,
        "avg_interview": round(interviews_stat["avg_score"], 1) if (interviews_stat and interviews_stat["avg_score"] is not None) else 0,
        "total_applications": apps_stat["count"] if apps_stat else 0,
    }


def save_application(user_id, internship_id, title, company, portal_type, stipend=None, location=None):
    """Save an internship application for a user. Returns True if created, False if already exists."""
    if not user_id or not internship_id:
        return False
    db = get_db()
    existing = db.execute(
        "SELECT id FROM internship_applications WHERE user_id = ? AND internship_id = ?",
        (user_id, internship_id)
    ).fetchone()
    if existing:
        return False

    db.execute(
        """
        INSERT INTO internship_applications (
            user_id, internship_id, title, company, portal_type, stipend, location
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, internship_id, title, company, portal_type, stipend, location)
    )
    db.commit()
    return True


def get_user_applications(user_id, limit=20):
    """Retrieve all internship applications submitted by a user."""
    if not user_id:
        return []
    db = get_db()
    rows = db.execute(
        """
        SELECT * FROM internship_applications
        WHERE user_id = ?
        ORDER BY applied_at DESC
        LIMIT ?
        """,
        (user_id, limit)
    ).fetchall()
    return [dict(r) for r in rows]


def get_user_applied_ids(user_id):
    """Return a set of internship IDs already applied for by user."""
    if not user_id:
        return set()
    db = get_db()
    rows = db.execute(
        "SELECT internship_id FROM internship_applications WHERE user_id = ?",
        (user_id,)
    ).fetchall()
    return {r["internship_id"] for r in rows}


def save_feedback(user_id, rating, message=""):
    """Store one authenticated user's SkillSync rating and optional comment."""
    if not user_id:
        return False

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return False

    if rating not in range(1, 6):
        return False

    message = (message or "").strip()
    db = get_db()
    db.execute(
        """
        INSERT INTO feedback (user_id, rating, message)
        VALUES (?, ?, ?)
        """,
        (user_id, rating, message or None),
    )
    db.commit()
    return True


def _usage_date():
    """Return today's date in the student-facing India time zone."""
    return datetime.now(USAGE_TIMEZONE).date().isoformat()


def get_chatbot_remaining(user_id, daily_limit=10):
    """Return the number of chatbot requests still available today."""
    if not user_id:
        return 0

    db = get_db()
    row = db.execute(
        """
        SELECT message_count FROM chatbot_daily_usage
        WHERE user_id = ? AND usage_date = ?
        """,
        (user_id, _usage_date()),
    ).fetchone()
    used = int(row["message_count"]) if row else 0
    return max(0, daily_limit - used)


def consume_chatbot_message(user_id, daily_limit=10):
    """Consume one chatbot request, returning ``(allowed, remaining)``."""
    if not user_id:
        return False, 0

    usage_date = _usage_date()
    db = get_db()
    db.execute(
        """
        INSERT OR IGNORE INTO chatbot_daily_usage (user_id, usage_date, message_count)
        VALUES (?, ?, 0)
        """,
        (user_id, usage_date),
    )
    cursor = db.execute(
        """
        UPDATE chatbot_daily_usage
        SET message_count = message_count + 1
        WHERE user_id = ? AND usage_date = ? AND message_count < ?
        """,
        (user_id, usage_date, daily_limit),
    )
    db.commit()
    return cursor.rowcount == 1, get_chatbot_remaining(user_id, daily_limit)
