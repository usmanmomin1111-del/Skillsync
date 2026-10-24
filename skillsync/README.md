# SkillSync — AI-Based Internship Recommendation Engine

A Flask website implementing the full SkillSync pipeline from the project PPT:

1. **Text Extraction** — parses uploaded PDF resumes (`PyPDF2`)
2. **Formatting Check** — rule-based checks for sections, bullets, contact info
3. **Keyword Matching** — resume terms vs. required domain skills
4. **Semantic Similarity** — **Sentence-BERT** (`all-MiniLM-L6-v2`) embeddings, cosine similarity
   (falls back to TF-IDF cosine similarity automatically if the SBERT model can't be
   downloaded, e.g. no internet on first run — the UI labels which engine was used)
5. **Skill Gap Detection** — matched vs. missing skills
6. **Gemini AI Layer** — resume summary, skill-gap explanations, an advisory chatbot, and
   AI-scored mock-interview answers with a final explainable performance report

Plus: domain selection, **AICTE & PM Internship Scheme recommendation engine**, full mock-interview flow, and **complete user authentication with an SQLite backend**.

## Tech stack (matches the PPT's Software slide)

- Python
- Flask (web framework)
- SQLite3 & Werkzeug Security (user authentication, password hashing, persistent storage)
- HTML & CSS (front-end interface, server-rendered Jinja2 templates)
- Sentence-BERT (`sentence-transformers`)
- Gemini AI API (`google-genai`)

## Features & Recommendation Architecture

- **AICTE & PM Internship Scheme Alignment**: Authentic postings from CISCO & AICTE, IBM SkillsBuild, Google Cloud & AICTE, TULIP (MoHUA), TCS iON, and Infosys Springboard.
- **Dynamic Candidate Compatibility Ranking**: Automatically compares the student's resume skills against internship prerequisites, calculates a **% Resume Fit**, and sorts the highest matches first.
- **Direct Application System (`/apply/<id>`)**: Students can directly apply using their evaluated resume, with applications tracked on their personal dashboard and redirected to the official portal.
- **User Authentication (`/signup`, `/login`, `/logout`)**: Secure PBKDF2/SHA-256 password hashing and session management.
- **Protected Student Dashboard (`/dashboard`)**: Displays evaluation statistics, recent ATS reports, completed mock interviews, and submitted internship applications.
- **Flash Notifications**: Styled alert banners for success, warnings, info, and error notifications.

## Setup

```bash
cd skillsync
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configure Gemini (optional but recommended)

Get an API key from [Google AI Studio](https://aistudio.google.com/app/apikey), then:

```bash
export GEMINI_API_KEY="your-key-here"     # Windows: set GEMINI_API_KEY=your-key-here
export SECRET_KEY="any-random-string"
```

Without a key, the app still runs end-to-end — the Gemini-powered summary, gap
explanation, chatbot, and interview feedback just fall back to clear rule-based text
instead of AI-generated text.

### Run

```bash
python app.py
```

Visit **http://localhost:5000**.

### Run Tests

```bash
python test_auth.py
```

## Project structure

```
skillsync/
├── app.py                  # Flask start file: python app.py
├── test_auth.py            # Automated tests for auth, validation & persistence
├── requirements.txt
├── frontend/
│   ├── templates/          # HTML (Jinja2: base, index, login, signup, dashboard, etc.)
│   └── static/             # CSS and browser Firebase JavaScript
├── backend/
│   ├── db.py               # SQLite database models, hashing, and queries
│   └── utils/
│       ├── resume_parser.py    # Text extraction + formatting check
│       ├── scorer.py           # Keyword matching + SBERT semantic similarity
│       ├── skills_data.py      # Domain skill sets and interview questions
│       ├── gemini_helper.py    # Gemini AI layer
│       └── aicte_internships.py # Verified live AICTE listings
├── data/
│   ├── uploads/            # Uploaded resume PDFs
│   └── skillsync.db        # Local SQLite database
└── docs/PROJECT_STRUCTURE.md
```

## Notes

- The resume must be a **text-based PDF** (not a scanned image) — extraction uses `PyPDF2`.
- The first request that needs Sentence-BERT downloads the `all-MiniLM-L6-v2` model
  (~90 MB) from Hugging Face; it's cached locally after that.
- Internship recommendations use the public AICTE catalogue; exact detail links are verified before display.
- User accounts, resume history, and interview reports are persisted in `data/skillsync.db`.

## Firebase connection

The Firebase Web SDK is loaded on every page and initialized with the
`skillsync-f84cb` project configuration. Browser code can access the initialized
services through `window.skillSyncFirebase`:

```js
window.addEventListener("skillsync:firebase-ready", () => {
  const { app, auth, db } = window.skillSyncFirebase;
  // Use Firebase Auth, Firestore, or Storage from page-specific JavaScript.
});
```

New signups also create a Firebase Authentication email/password account and a
Firestore profile document at `users/{firebaseUid}`. Passwords are never stored
in Firestore. The existing Flask username/password flow and SQLite history remain unchanged.
To move those records to Firebase, enable the relevant product in the Firebase
console (for example Email/Password in Authentication or Cloud Firestore) and
add the corresponding application flow. Do not put a Firebase Admin SDK service
account JSON file in `frontend/static/` or commit it to the repository.
