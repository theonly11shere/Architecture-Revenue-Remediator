# solutions_50.py

SOLUTIONS_DATABASE = {
    "CHK_01": {
        "leak_id": "CHK_01",
        "title": "Unlinked Contact Form / Missing Tap-To-Call",
        "impact": "Losing mobile leads due to manual typing friction.",
        "remediation": "Replace text phone numbers with 'tel:' protocol links and auto-populating form handlers."
    },
    "CHK_02": {
        "leak_id": "CHK_02",
        "title": "Missing Meta / Retargeting Pixel",
        "impact": "Bleeding 98% of non-converting bounce traffic with zero retargeting.",
        "remediation": "Inject Meta Pixel and Google Tag Manager code into the document header."
    },
    "CHK_03": {
        "leak_id": "CHK_03",
        "title": "Generic LLM AI Headline Detected",
        "impact": "Triggers immediate consumer distrust and sameness penalty.",
        "remediation": "Rewrite headline to state specific customer outcome within 3 seconds."
    }
}

def resolve_solutions(top_leaks: list) -> list:
    """Maps failed checkpoints to solution database entries."""
    resolved = []
    for leak in top_leaks:
        leak_id = leak.get("id")
        solution = SOLUTIONS_DATABASE.get(leak_id, {
            "leak_id": leak_id,
            "title": f"Conversion Friction Point ({leak.get('name')})",
            "impact": "Negative impact on total page conversions.",
            "remediation": "Apply standard conversion optimization guidelines."
        })
        resolved.append(solution)
    return resolved