from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .utils import ai_enhance_match, compute_match, extract_text


def index(request):
    return render(request, "matchline/index.html")


@require_POST
def run_match(request):
    try:
        resume_text = _get_text(request, "resume")
        jd_text = _get_text(request, "jd")

        if not resume_text or not jd_text:
            return JsonResponse(
                {"error": "Please provide both a resume and a job description."},
                status=400,
            )

        result = compute_match(resume_text, jd_text)

        use_ai = request.POST.get("use_ai") == "true"
        if use_ai:
            ai_result = ai_enhance_match(resume_text, jd_text, result)
            if ai_result:
                result["ai"] = ai_result
            else:
                result["ai_unavailable"] = True

        return JsonResponse(result)

    except Exception as exc:  # noqa: BLE001 -- surface a friendly error to the UI
        return JsonResponse({"error": f"Couldn't process that file: {exc}"}, status=500)


def _get_text(request, prefix):
    """Prefer pasted text; fall back to an uploaded file for the given field."""
    pasted = request.POST.get(f"{prefix}_text", "").strip()
    if pasted:
        return pasted

    uploaded = request.FILES.get(f"{prefix}_file")
    if uploaded:
        return extract_text(uploaded)

    return ""
