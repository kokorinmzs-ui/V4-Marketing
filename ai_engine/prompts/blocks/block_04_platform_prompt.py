"""
Block 04 — Marketing Platform.
Use only the exact schema fields.
"""

VERSION = "1.1.1"

BLOCK_04_PLATFORM_PROMPT = """
# BLOCK 04 — Marketing Platform

## GOAL
Build the brand foundation: positioning, USP, big idea, tone of voice, proof points.

## OUTPUT
Return ONLY JSON:
{
  "status": "success",
  "data": { ... }
}

## REQUIRED
- JSON only
- exact schema keys
- traceable decisions
- no made-up claims

## FORBIDDEN
- invented positioning or proof points
- generic brand slogans
- markdown explanations

## QUALITY RULES
- Keep positioning specific and usable.
- Make the USP traceable to source data.
- Use exact schema keys only.

## JSON SCHEMA HINT
Expected canonical fields:
positioning, usp, big_idea, tone_of_voice, proof_points, confidence

Use the exact schema from shared/schemas/blocks.py.
"""
