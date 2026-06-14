"""
Block 14 — Triggers.
Use only the exact schema fields.
"""

VERSION = "1.1.1"

BLOCK_14_TRIGGERS_PROMPT = """
# BLOCK 14 — Triggers

## GOAL
Map pains to triggers that change the buying decision.

## OUTPUT
Return ONLY JSON:
{
  "status": "success",
  "data": { ... }
}

## REQUIRED
- JSON only
- exact schema keys
- trigger text tied to pain and avatar

## FORBIDDEN
- generic trigger language
- markdown explanations
- unrelated actions

## QUALITY RULES
- Every trigger must map to a pain and avatar.
- Use exact schema keys only.

## JSON SCHEMA HINT
Expected canonical fields:
triggers, confidence

Use the exact schema from shared/schemas/blocks.py.
"""
