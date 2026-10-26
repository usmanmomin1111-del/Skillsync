"""
Module 6 from the PPT: Gemini AI Layer.
Generates the resume summary, explains why missing skills matter, powers the advisory
chatbot, and evaluates mock-interview answers.

Everything here degrades gracefully: if Gemini is unavailable, each function returns
a clear rule-based fallback instead of crashing the app. The app therefore remains
usable while an API key, network connection, or API quota is unavailable.
"""
import json
import os

_configured = False
_client = None
_last_error = None
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-3.8-flash")
# A lightweight, stable alternate model for temporary capacity errors on the
# primary model.  It can be overridden in .env without changing code.
GEMINI_FALLBACK_MODEL = os.environ.get(
    "GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite"
)


def _get_client():
    """Create one Gemini client per process without exposing API credentials."""
    global _configured, _client, _last_error
    if _configured:
        return _client

    _configured = True
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        _last_error = "GEMINI_API_KEY is not configured."
        return None

    try:
        from google import genai
        from google.genai import types

        # Keep interactive chatbot/interview requests responsive if Gemini is
        # temporarily overloaded.  The app can then use its safe fallback
        # instead of making the student wait through several SDK retries.
        _client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=6_000,
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        )
    except ImportError:
        _last_error = "The Google GenAI SDK is not installed. Run: python -m pip install -r requirements.txt"
    except Exception as exc:
        _last_error = str(exc)

    if _client is None:
        print(f"[SkillSync] Gemini unavailable: {_last_error}")
    return _client


def _ask_gemini(prompt: str, fallback: str) -> str:
    client = _get_client()
    if client is None:
        return fallback

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=prompt,
        )
        return (response.text or "").strip() or fallback
    except Exception as primary_error:
        # 429/503/504 are capacity or temporary availability errors.  A
        # different Flash model can often answer immediately in this case.
        if (
            getattr(primary_error, "code", None) in {429, 503, 504}
            and GEMINI_FALLBACK_MODEL != GEMINI_MODEL_NAME
        ):
            try:
                response = client.models.generate_content(
                    model=GEMINI_FALLBACK_MODEL,
                    contents=prompt,
                )
                text = (response.text or "").strip()
                if text:
                    print(
                        f"[SkillSync] Gemini primary unavailable; "
                        f"used fallback model {GEMINI_FALLBACK_MODEL}."
                    )
                    return text
            except Exception as fallback_error:
                print(
                    f"[SkillSync] Gemini fallback failed ({GEMINI_FALLBACK_MODEL}): "
                    f"{fallback_error}"
                )

        # Keep API or quota details out of the browser, but preserve them in the
        # server log for troubleshooting.
        print(
            f"[SkillSync] Gemini call failed ({GEMINI_MODEL_NAME}): "
            f"{primary_error}"
        )
        return fallback


def build_local_resume_summary(role: str, matched_skills: list, missing_skills: list) -> str:
    """Fast, deterministic resume guidance for the main analysis result."""
    matched = ", ".join(matched_skills[:4]) or "no core skills yet"
    if missing_skills:
        next_skill = missing_skills[0]
        return (
            f"For the {role} role, your strongest detected skills are {matched}. "
            f"Your next best improvement is {next_skill}; add a small project or a "
            "specific resume bullet that demonstrates it."
        )
    return (
        f"For the {role} role, your resume shows strong alignment through {matched}. "
        "Make the impact clearer by adding measurable outcomes to your project and experience bullets."
    )


def build_local_skill_gap_explanation(role: str, missing_skills: list) -> str:
    """Explain missing skills without blocking the ATS result on an AI call."""
    if not missing_skills:
        return f"No major {role} skill gaps were detected from the selected role profile."
    priorities = ", ".join(missing_skills[:3])
    return (
        f"Prioritise {priorities} first. Build one focused {role} project and mention "
        "the tools, your contribution, and a measurable result in the resume."
    )


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
        "You are SkillSync's resume advisor. Answer ONLY using the candidate context below. "
        "Do not give generic career advice, project roadmaps, interview preparation, headings, "
        "or follow-up questions. Keep the answer to 2 short sentences or at most 3 short bullet points. "
        "If the context does not support an answer, say what specific resume detail is missing.\n\n"
        f"Candidate context:\n{context[:2000]}\n\nStudent question: {message}"
    )
    fallback = (
        "Gemini is temporarily unavailable, but generally: focus on "
        "quantifying achievements, matching keywords from the job description, and closing "
        "the skill gaps listed above."
    )
    return _ask_gemini(prompt, fallback)


def evaluate_interview_answer(question: str, answer: str, role: str) -> dict:
    """Score one interview answer using a consistent Gemini JSON rubric."""
    answer = (answer or "").strip()
    fallback_score = min(10, max(1, len(answer.split()) // 8)) if answer else 0
    fallback = {
        "score": fallback_score,
        "feedback": "Add a direct answer, one relevant technical detail, and a concrete example.",
    }

    if not answer:
        return fallback

    prompt = (
        "You are a fair technical interviewer. Assess the candidate's answer against the exact "
        "question, not against writing length. Use this 0-10 rubric: 0=no answer; 1-2=irrelevant "
        "or fundamentally incorrect; 3-4=very incomplete; 5-6=partly correct but missing important "
        "details; 7-8=correct and relevant with a clear explanation; 9-10=precise, complete, and "
        "demonstrates strong practical understanding. Consider technical correctness (5 points), "
        "relevance (2 points), clarity (2 points), and a concrete example or trade-off when appropriate "
        "(1 point). Do not award a high score merely because an answer is long.\n\n"
        f"Role: {role}\nQuestion: {question}\nCandidate answer: {answer}\n\n"
        "Return valid JSON only in this shape: {\"score\": number, \"feedback\": \"max two short sentences; name one strength and one improvement\"}."
    )

    client = _get_client()
    if client is None:
        return fallback

    try:
        from google.genai import types

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
            max_output_tokens=180,
        )
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt,
                config=config,
            )
        except Exception as primary_error:
            if (
                getattr(primary_error, "code", None) not in {429, 503, 504}
                or GEMINI_FALLBACK_MODEL == GEMINI_MODEL_NAME
            ):
                raise
            response = client.models.generate_content(
                model=GEMINI_FALLBACK_MODEL,
                contents=prompt,
                config=config,
            )
            print(
                f"[SkillSync] Gemini interview scoring used fallback model "
                f"{GEMINI_FALLBACK_MODEL}."
            )
        result = json.loads(response.text or "{}")
        score = round(float(result.get("score")), 1)
        feedback = str(result.get("feedback", "")).strip()
        if not feedback:
            raise ValueError("Gemini returned no interview feedback")
        return {"score": max(0, min(10, score)), "feedback": feedback[:500]}
    except Exception as exc:
        print(f"[SkillSync] Gemini interview scoring failed ({GEMINI_MODEL_NAME}): {exc}")
        return fallback


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
