# JungAI v0.2 — Public Patch Notes

Date: 2026-02-26

## Highlights

- First-time onboarding flow.  
  New users now see a guided onboarding with a welcome step and an “About me” step to improve dream analysis context.

- Dream list UX improvements.  
  The main screen keeps the chat-like dream list layout, with cleaner metadata placement and improved readability.

- Better dream metadata pipeline.  
  Dream title length support was expanded, and analysis output now enriches dreams with meaningful title and visual metadata.

- Voice input quality updates.  
  Recording sessions are longer and dictation now appends to existing text instead of replacing it.

- Profile analytics upgrade.  
  Dream activity visualization now focuses on the last 14 calendar days and archetype trends.

## What’s New

- Onboarding (first login):
  - Welcome + About Me steps
  - Skip option supported
  - Completion stored per user account

- Dream list refinements:
  - clearer title/date hierarchy
  - visual separators between items
  - top-positioned notifications to avoid blocking bottom controls

- Editable dream date/time:
  - available from list context menu and dream screen menu
  - protected by backend validation

- Analysis metadata from LLM:
  - generated title (up to 64 chars)
  - dream gradient colors
  - archetype delta for profile aggregation

- Archetypes in profile:
  - top archetypes with counts
  - horizontal bar-style visualization

- Search foundation improvements:
  - groundwork for semantic search mode with embeddings

## UX and Behavior Changes

- “About me” context is now part of the initial experience and directly improves analysis quality.
- Voice dictation is designed for multi-pass writing (dictate -> edit -> dictate more).
- Analysis output now affects both content and visuals in the dream list.

## Notes

- Some improvements in this patch are foundational and enable later upgrades (including richer semantic retrieval and map-based memory features in subsequent versions).
