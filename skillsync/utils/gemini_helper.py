"""
Module 6 from the PPT: Gemini AI Layer.
Generates the resume summary, explains why missing skills matter, powers the advisory
chatbot, and evaluates mock-interview answers.

Everything here degrades gracefully: if GEMINI_API_KEY is not set (or the call fails),
each function returns a clear rule-based fallback instead of crashing the app, so the
rest of SkillSync (scoring, skill gaps, recommendations, interview flow) still works
while you're wiring up your own API key.
"""
import os

_configured = False
_model = None
GEMINI_MODEL_NAME = "gemini-2.0-flash"


def _get_model():
    global _configured, _model
    if _configured:
        return _model
    _configured = True
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        _model = None
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    except Exception as exc:
        print(f"[SkillSync] Gemini unavailable ({exc})")
        _model = None
    return _model


def _ask_gemini(prompt: str, fallback: str) -> str:
    model = _get_model()
    if model is None:
        return fallback
    try:
        response = model.generate_content(prompt)
        return (response.text or "").strip() or fallback
    except Exception as exc:
        print(f"[SkillSync] Gemini call failed: {exc}")
        return fallback


def generate_resume_summary(resume_text: str, role: str) -> str:
    prompt = (
        f"Summarize this candidate's resume in 3-4 sentences for a {role} internship "
        f"application. Be specific and encouraging.\n\nResume:\n{resume_text[:4000]}"
    )
    fallback = (
        f"This candidate's resume was analyzed against the {role} role. "
        "Connect a Gemini API key to generate a personalized AI summary here."
    )
    return _ask_gemini(prompt, fallback)


def explain_skill_gaps(missing_skills: list, role: str) -> str:
    if not missing_skills:
        return "No major skill gaps detected — this resume covers the core skills for this role well."
    skills_str = ", ".join(missing_skills)
    prompt = (
        f"A candidate applying for a {role} internship is missing these skills: {skills_str}. "
        "In 3-4 sentences, explain why these specific skills matter for the role and how "
        "the candidate could start closing the gap."
    )
    fallback = (
        f"The following skills are commonly expected for {role} roles but weren't found in the resume: "
        f"{skills_str}. Building small projects that use these skills is a good way to close the gap."
    )
    return _ask_gemini(prompt, fallback)


def chatbot_reply(message: str, context: str) -> str:
    prompt = (
        "You are SkillSync's advisory chatbot, helping a student improve their resume and "
        "internship readiness. Be concise and practical.\n\n"
        f"Context about the candidate:\n{context[:2000]}\n\nStudent question: {message}"
    )
    fallback = (
        "I can't reach Gemini right now (no API key configured), but generally: focus on "
        "quantifying achievements, matching keywords from the job description, and closing "
        "the skill gaps listed above."
    )
    return _ask_gemini(prompt, fallback)


def evaluate_interview_answer(question: str, answer: str, role: str) -> dict:
    """Module: Response Analysis + Communication Scoring + Technical Skill Assessment."""
    prompt = (
        f"A candidate for a {role} internship was asked: \"{question}\"\n"
        f"They answered: \"{answer}\"\n\n"
        "Rate the answer from 0-10 for relevance/technical correctness and give one sentence "
        "of feedback. Respond in the exact format:\nScore: <number>\nFeedback: <one sentence>"
    )
    fallback_score = min(10, max(2, len(answer.split()) // 8))
    fallback = f"Score: {fallback_score}\nFeedback: Try to give a more detailed, structured answer with a concrete example."
    raw = _ask_gemini(prompt, fallback)

    score, feedback = fallback_score, "Answer recorded."
    for line in raw.splitlines():
        if line.lower().startswith("score:"):
            try:
                score = float(line.split(":", 1)[1].strip().split()[0])
            except (ValueError, IndexError):
                pass
        elif line.lower().startswith("feedback:"):
            feedback = line.split(":", 1)[1].strip()
    return {"score": score, "feedback": feedback}


def generate_final_report(role: str, qa_pairs: list) -> str:
    transcript = "\n".join(f"Q: {q}\nA: {a}\nScore: {s}/10" for q, a, s in qa_pairs)
    prompt = (
        f"Here is a mock interview transcript for a {role} internship candidate:\n\n{transcript}\n\n"
        "Write a short, explainable performance report (4-5 sentences): overall readiness, "
        "one strength, one area to improve, and one actionable next step."
    )
    avg = sum(s for _, _, s in qa_pairs) / len(qa_pairs) if qa_pairs else 0
    fallback = (
        f"Average score: {avg:.1f}/10 across {len(qa_pairs)} questions. "
        "Connect a Gemini API key to generate a detailed, explainable report here."
    )
    return _ask_gemini(prompt, fallback)
