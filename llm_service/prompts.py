import re


def detect_language(text: str) -> str:
    cyr = len(re.findall(r"[А-Яа-яЁё]", text))
    lat = len(re.findall(r"[A-Za-z]", text))
    return "Russian" if cyr >= lat else "English"


def get_analysis_prompt(
    user_description: str | None = None,
    dream_text: str | None = None,
    user_memory_md: str | None = None,
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
        '  "archetypes_delta": {"ArchetypeName": 1},',
        '  "symbol_entities": [',
        '    {',
        '      "canonical_name": "ONE general noun, nominative singular (archetypal image)",',
        '      "display_label": "specific 2-3 word image from the dream",',
        '      "entity_type": "symbol|place|figure|object|motif|event",',
        '      "weight": 0.0,',
        '      "source_chunk_indexes": [0],',
        '      "related_archetypes": ["ArchetypeName"]',
        '    }',
        '  ],',
        '  "memory_update": {',
        '    "recurring": {"action": "replace", "value": "themes / patterns"},',
        '    "archetypes": {"action": "replace", "value": "dominant archetypes"},',
        '    "emotional_shift": {"action": "replace", "value": "direction of change"},',
        '    "phase": {"action": "replace", "value": "current psychological phase"}',
        '  }',
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
        "- symbol_entities are the dream's core symbolic images. Pick the 4-8 MOST salient/archetypal ones — NOT an exhaustive list of every detail.",
        "- canonical_name MUST be ONE general noun in nominative singular, lowercase: the abstract archetypal image. The SAME recurring symbol across different dreams MUST get the SAME canonical_name so it can be tracked over time.",
        "- Generalize specifics into their archetypal core: 'тайные тропы' -> canonical 'тропа'; 'главный герой-разработчик' -> 'герой'; 'магический vpn' -> 'портал'; 'туалет у входа' -> 'туалет'; 'чёрная вода' -> 'вода'.",
        "- canonical_name MUST NOT be a multi-word phrase, a proper name, a brand/technology, or a character name.",
        "- display_label is the specific 2-3 word image as it appears in the dream (e.g. 'тёмный лес', 'тайные тропы'); it may stay concrete.",
        "- NEVER output pronouns, prepositions, helper/filler words, verbs, or speech fragments in either field.",
        "- good canonical_name examples: 'лес', 'вода', 'дом', 'женщина', 'вокзал', 'дорога', 'тень', 'мост'.",
        "",
        "memory_update rules:",
        "- memory_update captures the evolving psychological profile of the user across all their dreams.",
        "- 'recurring': key themes, symbols, or conflicts that appear repeatedly (e.g. 'control / chaos / water / bridges').",
        "- 'archetypes': dominant Jungian archetypes and their trajectory (e.g. 'shadow (growing), anima (emerging)').",
        "- 'emotional_shift': direction of emotional change over time (e.g. 'anxiety -> exploration -> acceptance').",
        "- 'phase': current stage in individuation or life (e.g. 'transition', 'integration', 'crisis').",
        "- Each section value should be a SHORT string (max ~100 chars). Do not write essays.",
        "- Update based on THIS dream combined with the existing profile. Evolve, don't overwrite blindly.",
        "- If this is the first dream (no existing profile), create the profile from scratch.",
        "",
        "Temporal dynamics rules:",
        "- Past dream chunks are provided in chronological order with timestamps.",
        "- Compare past and present: identify how symbols, emotions, and archetypes evolve over time.",
        "- Note recurring cycles (e.g. symbols that appear, disappear, and return).",
        "- Highlight developmental shifts: what has changed since the earliest dreams?",
        "- Use temporal language: 'earlier dreams showed...', 'over the past weeks...', 'a new pattern emerging...'.",
    ]
    if user_description:
        parts.append(f"User context: {user_description}")
    if user_memory_md and user_memory_md.strip():
        parts.append("")
        parts.append("Current user psychological profile (from previous analyses):")
        parts.append(user_memory_md.strip())
        parts.append("Update memory_update based on this dream AND the existing profile above.")
    return "\n".join(parts)


def get_default_temperature() -> float:
    return 0.7


def get_chat_system_prompt(user_description: str | None = None) -> str:
    parts = [
        "You are InnerCore, a Jungian dream analysis assistant.",
        "Respond in the same language as the user.",
        "For follow-up questions be concise and contextual.",
    ]
    if user_description:
        parts.append(f"User context: {user_description}")
    return "\n".join(parts)
