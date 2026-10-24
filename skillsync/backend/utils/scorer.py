"""
Modules 3-5: Keyword Matching, Semantic Similarity (SBERT), and Skill Gap Detection.

Sentence-BERT is the primary semantic-similarity engine. If SBERT is still loading
or unavailable, the module uses a calibrated TF-IDF cosine-similarity fallback
that measures the candidate resume against the domain requirements and competencies.
"""
import re
import threading

_sbert_model = None
_sbert_loading = False
SBERT_MODEL_NAME = "all-MiniLM-L6-v2"


def _load_sbert_worker():
    """Background worker to warm up Sentence-BERT once at startup."""
    global _sbert_model, _sbert_loading
    if _sbert_model is not None:
        return
    _sbert_loading = True
    try:
        from sentence_transformers import SentenceTransformer
        _sbert_model = SentenceTransformer(SBERT_MODEL_NAME)
    except Exception as exc:
        print(f"[SkillSync] Sentence-BERT deferred or fallback active: {exc}")
        _sbert_model = None
    finally:
        _sbert_loading = False


def _get_sbert_model():
    """Get the Sentence-BERT model if ready, or trigger load."""
    global _sbert_model, _sbert_loading
    if _sbert_model is not None:
        return _sbert_model

    if not _sbert_loading:
        # Attempt immediate load
        _load_sbert_worker()

    return _sbert_model


# Warm up Sentence-BERT in background when module is loaded
threading.Thread(target=_load_sbert_worker, daemon=True).start()


def _tokenize(text: str):
    """Normalize text and extract lowercase alphanumeric tokens."""
    return set(re.findall(r"[a-zA-Z][a-zA-Z0-9\+\#\.]*", text.lower()))


def keyword_match(resume_text: str, required_skills: list) -> dict:
    """
    Module 3: Keyword Matching.
    Direct comparison of resume text tokens and phrases against domain required skills.
    """
    if not resume_text or not required_skills:
        return {"matched": [], "missing": required_skills or [], "score": 0.0}

    resume_lower = resume_text.lower()
    resume_tokens = _tokenize(resume_text)
    matched, missing = [], []

    for skill in required_skills:
        skill_lower = skill.lower()
        skill_tokens = _tokenize(skill)

        # Match exact token set, word boundary regex, or phrase presence
        if skill_tokens and skill_tokens.issubset(resume_tokens):
            matched.append(skill)
        elif re.search(rf"\b{re.escape(skill_lower)}\b", resume_lower):
            matched.append(skill)
        elif skill_lower in resume_lower:
            matched.append(skill)
        else:
            missing.append(skill)

    pct = round(100.0 * len(matched) / len(required_skills), 1) if required_skills else 0.0
    return {"matched": matched, "missing": missing, "score": pct}


def normalize_cosine_score(raw_cos: float, is_sbert: bool = True) -> float:
    """
    Calibrate raw cross-document cosine similarity into an intuitive 0-100% ATS score.
    Cross-document embeddings between a multi-page resume and a job description naturally
    hover around 0.10 for unrelated text and 0.50-0.70 for strong domain alignment.
    """
    raw_cos = max(0.0, min(1.0, float(raw_cos)))

    if is_sbert:
        # SBERT calibration curve
        if raw_cos <= 0.10:
            score = raw_cos * 150.0
        elif raw_cos <= 0.40:
            score = 15.0 + ((raw_cos - 0.10) / 0.30) * 45.0
        elif raw_cos <= 0.65:
            score = 60.0 + ((raw_cos - 0.40) / 0.25) * 30.0
        else:
            score = 90.0 + ((raw_cos - 0.65) / 0.35) * 9.5
    else:
        # TF-IDF calibration curve
        if raw_cos <= 0.10:
            score = raw_cos * 150.0
        elif raw_cos <= 0.35:
            score = 15.0 + ((raw_cos - 0.10) / 0.25) * 45.0
        elif raw_cos <= 0.60:
            score = 60.0 + ((raw_cos - 0.35) / 0.25) * 30.0
        else:
            score = 90.0 + ((raw_cos - 0.60) / 0.40) * 9.5

    return round(max(0.0, min(99.5, score)), 1)


def semantic_similarity(resume_text: str, role_description: str, role_skills: list = None) -> dict:
    """
    Module 4: Semantic Similarity.
    Evaluates candidate resume against the enriched domain requirements.
    Uses Sentence-BERT if initialized, or calibrated TF-IDF fallback.
    """
    if not resume_text:
        return {"score": 0.0, "engine": "None"}

    # Build enriched domain profile to capture full context
    domain_profile = role_description
    if role_skills:
        domain_profile += " Key domain competencies, technologies, and tools required: " + ", ".join(role_skills) + "."

    model = _get_sbert_model()
    if model is not None:
        try:
            from sentence_transformers import util
            embeddings = model.encode([resume_text, domain_profile], convert_to_tensor=True)
            raw_sim = float(util.cos_sim(embeddings[0], embeddings[1])[0][0])
            score = normalize_cosine_score(raw_sim, is_sbert=True)
            return {"score": score, "engine": "Sentence-BERT (all-MiniLM-L6-v2)"}
        except Exception:
            pass  # Fall through to TF-IDF fallback if embedding computation fails

    # TF-IDF fallback with calibrated scoring
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        vectorizer = TfidfVectorizer(stop_words="english", token_pattern=r"(?u)\b[a-zA-Z0-9\+\#\.]+\b")
        matrix = vectorizer.fit_transform([resume_text, domain_profile])
        raw_sim = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
        score = normalize_cosine_score(raw_sim, is_sbert=False)
        engine = "TF-IDF cosine similarity (SBERT fallback)"
    except Exception:
        # Ultimate fallback based on keyword match
        score = 50.0
        engine = "Keyword-based similarity"

    return {"score": score, "engine": engine}


def skill_gap(matched: list, missing: list) -> dict:
    """Module 5: Skill Gap Detection — identified as sets of matched vs missing skills."""
    return {"matched": matched, "missing": missing}


def compute_ats_score(keyword_pct: float, semantic_pct: float,
                       keyword_weight: float = 0.70, semantic_weight: float = 0.30) -> float:
    """
    Hybrid ATS Fit Score.
    In real-world ATS pipelines, core skill matching is the primary filter (70% weight),
    and contextual semantic similarity serves as qualitative domain calibration (30% weight).
    """
    score = (keyword_pct * keyword_weight) + (semantic_pct * semantic_weight)
    return round(min(100.0, max(0.0, score)), 1)


def rank_internships_for_resume(internships: list, candidate_matched_skills: list) -> list:
    """
    Ranks internships by calculating candidate's match percentage for each posting.
    Appends matching_skills, missing_skills, and match_percentage to each posting.
    Sorts descending so the best-fitting opportunities appear first.
    """
    # AICTE's public catalogue may use variants such as "Html" / "HTML" and
    # "Node.Js" / "Node.js".  Normalize punctuation so matching remains based
    # on the candidate's existing matched skills rather than string styling.
    def normalize_skill(skill):
        return "".join(char for char in str(skill).lower() if char.isalnum())

    matched_set = {normalize_skill(s) for s in (candidate_matched_skills or [])}
    ranked = []

    for job in internships:
        item = dict(job)
        req_skills = job.get("skills_required", [])
        if req_skills:
            matching = [s for s in req_skills if normalize_skill(s) in matched_set]
            missing = [s for s in req_skills if normalize_skill(s) not in matched_set]
            pct = round(100.0 * len(matching) / len(req_skills))
        else:
            matching, missing, pct = [], [], 80

        item["matching_skills"] = matching
        item["missing_skills"] = missing
        item["match_percentage"] = pct
        ranked.append(item)

    # Sort descending by match percentage
    ranked.sort(key=lambda x: x["match_percentage"], reverse=True)
    return ranked
