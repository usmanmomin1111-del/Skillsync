# SkillSync Project Structure

Use `python app.py` from the project root to run the website.  The root
`app.py` connects the folders below; do not move files without updating it.

```text
frontend/          Browser-facing code
  templates/       HTML pages rendered by Flask
  static/          CSS and browser JavaScript (including Firebase)

backend/           Server-side Python code
  db.py            SQLite schema, users, analyses and saved listings
  utils/           Resume parsing, ATS scoring, Gemini, AICTE integration

data/              Runtime data, not source code
  uploads/         User-uploaded resumes
  skillsync.db     Local SQLite database

docs/              Project documentation for development and faculty review
```

## Quick file guide

| Need to change | File or folder |
| --- | --- |
| Flask routes and page flow | `app.py` |
| HTML page design | `frontend/templates/` |
| CSS / Firebase browser scripts | `frontend/static/` |
| ATS score and skill match | `backend/utils/scorer.py` |
| Resume PDF reading | `backend/utils/resume_parser.py` |
| Gemini chatbot/interview feedback | `backend/utils/gemini_helper.py` |
| Domains and interview questions | `backend/utils/skills_data.py` |
| Live AICTE internship links | `backend/utils/aicte_internships.py` |
| Database operations | `backend/db.py` |
