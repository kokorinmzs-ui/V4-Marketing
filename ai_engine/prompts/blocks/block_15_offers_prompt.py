"""
Block 15 — Offers.
Use only the exact schema fields.
"""

VERSION = "1.1.1"

BLOCK_15_OFFERS_PROMPT = """
# BLOCK 15 — Offers

## GOAL
Create offers that directly close a specific pain.

## OUTPUT
Return ONLY JSON:
{
  "status": "success",
  "data": { ... }
}

## REQUIRED
- JSON only
- exact schema keys
- clear value proposition
- linked pain, avatar, CTA

## FORBIDDEN
- vague offers
- markdown explanations
- offers without a pain connection

## QUALITY RULES
- Every offer must close a specific pain.
- Keep the CTA actionable and traceable.
- Use exact schema keys only.

## JSON SCHEMA HINT
Expected canonical fields:
offers, confidence

Use the exact schema from shared/schemas/blocks.py.
"""
