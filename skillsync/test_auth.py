"""
Automated test suite for SkillSync Authentication Gate and Core Workflow.
"""
import unittest
import os
import sqlite3

# Set test environment
os.environ["SECRET_KEY"] = "test-secret-key"

from backend import db
from app import app


class SkillSyncAuthTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

        # Re-initialize DB
        db.init_db()

        # Clean existing test data if any
        conn = sqlite3.connect(db.DB_PATH)
        conn.execute("DELETE FROM resume_analyses;")
        conn.execute("DELETE FROM interview_sessions;")
        conn.execute("DELETE FROM users;")
        conn.commit()
        conn.close()

    def test_first_page_is_login_for_guests(self):
        """Test that first page (/) and interview page redirect unauthenticated users to /login."""
        # Root route redirects to login
        res = self.client.get("/")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers["Location"])

        # Following redirect leads to login page
        res_follow = self.client.get("/", follow_redirects=True)
        self.assertEqual(res_follow.status_code, 200)
        self.assertIn(b"Log in to SkillSync", res_follow.data)
        self.assertIn(b"STEP 1: AUTHENTICATION", res_follow.data)

        # Interview route is also protected
        res_interview = self.client.get("/interview", follow_redirects=True)
        self.assertEqual(res_interview.status_code, 200)
        self.assertIn(b"Log in to SkillSync", res_interview.data)

        # Login and Signup pages load directly
        res_login = self.client.get("/login")
        self.assertEqual(res_login.status_code, 200)

        res_signup = self.client.get("/signup")
        self.assertEqual(res_signup.status_code, 200)
        self.assertIn(b"Create your account", res_signup.data)

    def test_signup_validation(self):
        """Test validation rules on signup."""
        # Missing fields
        res = self.client.post("/signup", data={
            "username": "",
            "email": "bad",
            "password": "123",
            "confirm_password": "456",
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 400)
        self.assertIn(b"Username is required", res.data)

        # Short password
        res = self.client.post("/signup", data={
            "username": "alexj",
            "email": "alex@example.com",
            "password": "123",
            "confirm_password": "123",
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 400)
        self.assertIn(b"Password must be at least 6 characters", res.data)

        # Mismatched passwords
        res = self.client.post("/signup", data={
            "username": "alexj",
            "email": "alex@example.com",
            "password": "password123",
            "confirm_password": "password456",
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 400)
        self.assertIn(b"Passwords do not match", res.data)

    def test_signup_then_access_resume_and_interview(self):
        """Test that after signup, the user immediately gets access to resume review and interview."""
        # 1. Sign up
        res = self.client.post("/signup", data={
            "full_name": "Alex Johnson",
            "username": "alexj",
            "email": "alex@example.com",
            "password": "mypassword123",
            "confirm_password": "mypassword123",
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        # Verify user is now on the Resume feedback page (index)
        self.assertIn(b"Target role", res.data)
        self.assertIn(b"Review my resume", res.data)
        self.assertIn(b"alexj", res.data)

        # 2. Can now access the Interview practice page
        res_interview = self.client.get("/interview")
        self.assertEqual(res_interview.status_code, 200)
        self.assertIn(b"Enter interview room", res_interview.data)

        # 3. Log out then duplicate username should fail
        self.client.get("/logout")
        res2 = self.client.post("/signup", data={
            "full_name": "Another Alex",
            "username": "alexj",
            "email": "alex2@example.com",
            "password": "mypassword123",
            "confirm_password": "mypassword123",
        }, follow_redirects=True)
        self.assertEqual(res2.status_code, 400)
        self.assertIn(b"Username is already taken", res2.data)

        # 4. Failed login with wrong password
        res4 = self.client.post("/login", data={
            "identifier": "alexj",
            "password": "wrongpassword",
        }, follow_redirects=True)
        self.assertEqual(res4.status_code, 401)
        self.assertIn(b"Invalid username/email or password", res4.data)

        # 5. Successful login leads directly to Resume feedback page (index)
        res5 = self.client.post("/login", data={
            "identifier": "alexj",
            "password": "mypassword123",
        }, follow_redirects=True)
        self.assertEqual(res5.status_code, 200)
        self.assertIn(b"Target role", res5.data)
        self.assertIn(b"Review my resume", res5.data)

    def test_protected_routes(self):
        """Test that protected routes redirect unauthenticated users."""
        res = self.client.get("/dashboard", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Log in to SkillSync", res.data)
        self.assertIn(b"Please log in to continue", res.data)

        # Sign up, then access /dashboard
        self.client.post("/signup", data={
            "username": "janedoe",
            "email": "jane@example.com",
            "password": "secretpassword",
            "confirm_password": "secretpassword",
        })

        res_auth = self.client.get("/dashboard")
        self.assertEqual(res_auth.status_code, 200)
        self.assertIn(b"janedoe", res_auth.data)
        self.assertIn(b"Recent Resume Evaluations", res_auth.data)

    def test_data_persistence(self):
        """Test that analyses and interviews are saved in the user's account."""
        self.client.post("/signup", data={
            "username": "tester",
            "email": "tester@example.com",
            "password": "password123",
            "confirm_password": "password123",
        })

        with self.client.session_transaction() as sess:
            user_id = sess.get("user_id")

        self.assertIsNotNone(user_id)

        with app.app_context():
            db.save_resume_analysis(
                user_id=user_id,
                analysis_id="test-analysis-1",
                domain="Data Analytics",
                ats_score=85,
                keyword_score=80,
                semantic_score=90,
                matched_skills=["Python", "SQL", "Tableau"],
                missing_skills=["Power BI"],
            )

            db.save_interview_session(
                user_id=user_id,
                domain="Data Analytics",
                avg_score=8.5,
                qa_list=[["What is SQL?", "Structured Query Language", 9, "Strong response"]],
                report_text="Excellent analytical communication.",
            )

        res = self.client.get("/dashboard")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Data Analytics", res.data)
        self.assertIn(b"85%", res.data)
        self.assertIn(b"8.5/10", res.data)

    def test_interview_report_persists_for_logged_in_user(self):
        """Test that completing an interview saves to the user's account."""
        self.client.post("/signup", data={
            "username": "interviewee",
            "email": "interviewee@example.com",
            "password": "password123",
            "confirm_password": "password123",
        })

        with self.client.session_transaction() as sess:
            sess["interview_domain"] = "Python Development"
            sess["interview_qa"] = [
                ["What is a Python decorator?", "A wrapper function modifying behavior.", 9.0, "Great answer."],
                ["What is GIL?", "Global Interpreter Lock in CPython.", 8.0, "Accurate."],
            ]

        res = self.client.get("/interview/report")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Python Development", res.data)

        res_dash = self.client.get("/dashboard")
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn(b"Python Development", res_dash.data)
        self.assertIn(b"8.5/10", res_dash.data)

    def test_internship_application_flow(self):
        """Test applying for an AICTE internship and tracking in dashboard."""
        self.client.post("/signup", data={
            "username": "applicant",
            "email": "applicant@example.com",
            "password": "password123",
            "confirm_password": "password123",
        })

        # Apply for CISCO AICTE internship
        res = self.client.post("/apply/aicte-web-cisco", data={
            "title": "Full Stack Web Developer Virtual Intern",
            "company": "CISCO Networking Academy & AICTE",
            "portal_type": "AICTE Official Partner",
            "stipend": "₹10,000 / month",
            "location": "Virtual / Work from Home",
            "portal_url": "https://internship.aicte-india.org/",
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Check dashboard shows the application
        res_dash = self.client.get("/dashboard")
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn(b"Full Stack Web Developer Virtual Intern", res_dash.data)
        self.assertIn(b"CISCO Networking Academy", res_dash.data)
        self.assertIn(b"AICTE Official Partner", res_dash.data)
        self.assertIn(b"Internships Applied", res_dash.data)


if __name__ == "__main__":
    unittest.main()
