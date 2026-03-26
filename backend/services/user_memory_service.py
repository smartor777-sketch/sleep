"""Service for managing user.md long-term memory documents."""

import logging
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_memory import UserMemoryDoc

logger = logging.getLogger(__name__)

MEMORY_SECTIONS = ("recurring", "archetypes", "emotional_shift", "phase")

EMPTY_MEMORY_MD = "\n\n".join(f"## {s}\n" for s in MEMORY_SECTIONS)


async def get_or_create(db: AsyncSession, user_id: uuid.UUID) -> UserMemoryDoc:
    """Get existing memory doc or create a blank one."""
    result = await db.execute(
        select(UserMemoryDoc).where(UserMemoryDoc.user_id == user_id)
    )
    doc = result.scalar_one_or_none()
    if doc is not None:
        return doc

    doc = UserMemoryDoc(
        id=uuid.uuid4(),
        user_id=user_id,
        content_md="",
        version=1,
        updated_at=datetime.now(timezone.utc),
    )
    db.add(doc)
    await db.flush()
    return doc


async def apply_memory_update(
    db: AsyncSession,
    user_id: uuid.UUID,
    memory_update: dict,
    current_version: int,
) -> UserMemoryDoc | None:
    """Apply a diff from LLM analysis to the user memory doc.

    Uses optimistic concurrency: only updates if version matches.
    Returns updated doc, or None if version conflict (caller should retry once).

    memory_update format:
    {
        "recurring": {"action": "replace", "value": "..."},
        "archetypes": {"action": "replace", "value": "..."},
        ...
    }
    """
    doc = await get_or_create(db, user_id)

    if doc.version != current_version:
        logger.warning(
            "Version conflict for user %s: expected %d, got %d",
            user_id, current_version, doc.version,
        )
        return None

    # Parse current content
    sections = _parse_memory_md(doc.content_md)

    # Apply updates
    for section_name in MEMORY_SECTIONS:
        update_data = memory_update.get(section_name)
        if not update_data or not isinstance(update_data, dict):
            continue
        action = update_data.get("action", "replace")
        value = update_data.get("value", "").strip()
        if action == "replace" and value:
            sections[section_name] = value

    # Rebuild markdown
    new_content = _build_memory_md(sections)

    # Optimistic update
    stmt = (
        update(UserMemoryDoc)
        .where(
            UserMemoryDoc.user_id == user_id,
            UserMemoryDoc.version == current_version,
        )
        .values(
            content_md=new_content,
            version=current_version + 1,
            updated_at=datetime.now(timezone.utc),
        )
    )
    result = await db.execute(stmt)
    if result.rowcount == 0:
        logger.warning("Optimistic lock failed for user %s", user_id)
        return None

    await db.flush()

    # Refresh doc
    doc.content_md = new_content
    doc.version = current_version + 1
    return doc


def _parse_memory_md(content: str) -> dict[str, str]:
    """Parse memory markdown into section dict."""
    sections = {s: "" for s in MEMORY_SECTIONS}
    if not content.strip():
        return sections

    current_section = None
    lines = content.split("\n")
    for line in lines:
        match = re.match(r"^##\s+(\w+)", line)
        if match:
            name = match.group(1).lower()
            if name in sections:
                current_section = name
                continue
        if current_section is not None:
            existing = sections[current_section]
            sections[current_section] = (existing + "\n" + line).strip()

    return sections


def _build_memory_md(sections: dict[str, str]) -> str:
    """Build memory markdown from section dict."""
    parts = []
    for name in MEMORY_SECTIONS:
        value = sections.get(name, "").strip()
        parts.append(f"## {name}\n{value}")
    return "\n\n".join(parts)
