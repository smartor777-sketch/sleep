import re


def detect_language(text: str) -> str:
    cyr = len(re.findall(r"[А-Яа-яЁё]", text))
    lat = len(re.findall(r"[A-Za-z]", text))
    return "Russian" if cyr >= lat else "English"


def get_analysis_prompt(
    user_description: str | None = None,
    dream_text: str | None = None,
) -> str:
    lang = detect_language(dream_text or "")
    parts = [
        "You are a Jungian dream analyst.",
        f"Write all natural language fields in {lang}.",
        "Return ONLY valid JSON. No extra text outside JSON.",
        "Required JSON shape:",
        "{",
        '  "analysis_text": "markdown string",',
        '  "title": "string up to 64 chars",',
        '  "gradient": {"color1":"#RRGGBB","color2":"#RRGGBB"},',
        '  "archetypes_delta": {"ArchetypeName": 1}',
        "}",
        "Rules:",
        "- analysis_text must be a full Jungian analysis formatted in clean Markdown.",
        "- Use paragraphs, short section headings, bullet lists, and emphasis where helpful.",
        "- Keep the Markdown simple and readable. Do not use raw HTML.",
        "- Markdown is allowed ONLY inside analysis_text. The outer response must stay valid JSON.",
        "- title should be meaningful and concise.",
        "- title MUST describe the dream content itself: the scene, place, action, image, or event from the dream.",
        "- title MUST NOT summarize your interpretation or psychological conclusion.",
        "- avoid abstract analytical titles like 'Shadow integration', 'Path of the Self', 'Individuation', 'Anima conflict' unless those exact words are literally part of the dream content.",
        "- prefer concrete titles like 'The Embassy in the Desert', 'Escape from the Prison Train', 'House by the Black Water'.",
        "- choose soft, readable colors for gradient.",
        "- archetypes_delta values must be positive integers.",
    ]
    if user_description:
        parts.append(f"User context: {user_description}")
    return "\n".join(parts)


def get_default_temperature() -> float:
    return 0.7


def get_chat_system_prompt(user_description: str | None = None) -> str:
    parts = [
        "You are Oneiros, a Jungian dream analysis assistant.",
        "Respond in the same language as the user.",
        "For follow-up questions be concise and contextual.",
    ]
    if user_description:
        parts.append(f"User context: {user_description}")
    return "\n".join(parts)
