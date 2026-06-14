"""
Block 11 — Avatars.
Use only the exact schema fields.
"""

VERSION = "1.1.1"

BLOCK_11_AVATARS_PROMPT = """
# BLOCK 11 — Avatars

## GOAL
Create distinct customer avatars grounded in audience segments.

## OUTPUT
Return ONLY JSON:
{
  "status": "success",
  "data": { ... }
}

## REQUIRED
- JSON only
- exact schema keys
- distinct avatars
- traceable motivations and fears

## FORBIDDEN
- duplicate avatars
- vague persona descriptions
- markdown explanations

## QUALITY RULES
- Make avatars meaningfully different.
- Preserve continuity with audience segments.
- Use exact schema keys only.

## JSON SCHEMA HINT
Expected canonical fields:
avatars, similarity_score, confidence

Use the exact schema from shared/schemas/blocks.py.
"""
