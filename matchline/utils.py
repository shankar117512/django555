"""
Core logic for Matchline: extracting text from uploaded files and
comparing a resume against a job description.
"""

import json
import re
import string
from collections import Counter

STOPWORDS = set("""
    a about above after again against all am an and any are aren't as at be because
    been before being below between both but by can't cannot could couldn't did
    didn't do does doesn't doing don't down during each few for from further had
    hadn't has hasn't have haven't having he he'd he'll he's her here here's hers
    herself him himself his how how's i i'd i'll i'm i've if in into is isn't it
    it's its itself let's me more most mustn't my myself no nor not of off on once
    only or other ought our ours ourselves out over own same shan't she she'd
    she'll she's should shouldn't so some such than that that's the their theirs
    them themselves then there there's these they they'd they'll they're they've
    this those through to too under until up very was wasn't we we'd we'll we're
    we've were weren't what what's when when's where where's which while who
    who's whom why why's with won't would wouldn't you you'd you'll you're
    you've your yours yourself yourselves
    """.split())

# Generic resume/JD filler words that rarely help differentiate a match.
GENERIC_FILLER = {
    "experience",
    "work",
    "team",
    "years",
    "strong",
    "ability",
    "skills",
    "including",
    "etc",
    "role",
    "company",
    "job",
    "responsibilities",
    "requirements",
    "preferred",
    "required",
    "candidate",
    "please",
    "using",
}


def extract_text(uploaded_file):
    """Extract plain text from an uploaded PDF, DOCX, or TXT file."""
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return _extract_pdf(uploaded_file)
    elif name.endswith(".docx"):
        return _extract_docx(uploaded_file)
    else:
        raw = uploaded_file.read()
        return raw.decode("utf-8", errors="ignore")


def _extract_pdf(f):
    import pdfplumber

    text_parts = []
    with pdfplumber.open(f) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def _extract_docx(f):
    import docx

    document = docx.Document(f)
    return "\n".join(p.text for p in document.paragraphs)


def _tokenize(text):
    text = text.lower()
    # Keep tech-flavored tokens like "c++", "node.js", "ci/cd"
    words = re.findall(r"[a-z][a-z0-9+.#/-]{1,}", text)
    cleaned = []
    for w in words:
        w = w.strip(string.punctuation)
        if not w or len(w) < 3:
            continue
        if w in STOPWORDS or w in GENERIC_FILLER:
            continue
        cleaned.append(w)
    return cleaned


def compute_match(resume_text, jd_text, top_n=60, result_limit=30):
    """Keyword-overlap based matching between a resume and a job description."""
    jd_counts = Counter(_tokenize(jd_text))
    resume_tokens = set(_tokenize(resume_text))

    jd_keywords_ranked = [w for w, _ in jd_counts.most_common(top_n)]

    matched = [w for w in jd_keywords_ranked if w in resume_tokens]
    missing = [w for w in jd_keywords_ranked if w not in resume_tokens]

    total = len(jd_keywords_ranked) or 1
    score = round((len(matched) / total) * 100)

    return {
        "score": score,
        "matched_keywords": matched[:result_limit],
        "missing_keywords": missing[:result_limit],
        "total_jd_keywords": len(jd_keywords_ranked),
    }


def ai_enhance_match(resume_text, jd_text, keyword_result):
    """
    Optional second pass using the Claude API for a more nuanced read
    of the match (beyond raw keyword overlap). Returns None if no API
    key is configured or if the call fails, so the page still works
    with keyword-only results.
    """
    from django.conf import settings

    api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
    if not api_key:
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""You are helping a job seeker understand how well their resume matches a job description.

RESUME:
{resume_text[:6000]}

JOB DESCRIPTION:
{jd_text[:6000]}

Keyword-overlap score so far: {keyword_result['score']}%

Respond ONLY with valid JSON, no preamble or markdown fences, in this exact shape:
{{
  "summary": "2-3 sentence assessment of the overall fit",
  "strengths": ["short phrase", "short phrase", "short phrase"],
  "gaps": ["short phrase", "short phrase", "short phrase"],
  "suggested_score": 0
}}"""

        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = "".join(
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text"
        ).strip()
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        return json.loads(raw_text)
    except Exception:
        # Fail quietly -- keyword-based results are still returned to the page.
        return None
