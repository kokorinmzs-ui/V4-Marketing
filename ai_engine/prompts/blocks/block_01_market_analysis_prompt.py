"""
Block 01 — Анализ ниши / Market Analysis.
Use only the exact schema fields.
"""

VERSION = "1.1.1"

BLOCK_01_MARKET_ANALYSIS_PROMPT = """
# BLOCK 01 — Анализ ниши / Market Analysis

## GOAL
Understand the market, not the company or product.

## OUTPUT
Return ONLY JSON in the block schema format:
{
  "status": "success",
  "data": { ... }
}

## REQUIRED
- JSON only
- traceable conclusions
- confidence score for uncertain data
- continuity with avatar -> pain -> offer -> CTA whenever applicable

## FORBIDDEN
- invented facts or numbers
- marketing fluff without evidence
- markdown explanations
- hallucinated assumptions

## QUALITY RULES
- Keep the answer specific and traceable.
- Prefer low confidence over invented certainty.
- Use exact schema keys only.

## JSON SCHEMA HINT
Expected canonical fields:
market_overview, market_size, seasonality, buying_triggers,
buying_barriers, growth_opportunities, channels, risks, confidence

Use the exact schema from shared/schemas/blocks.py.

## PROJECT MEMORY
- Preserve context from the brief and prior blocks.
- Prefer source data over assumptions.
- If something is missing, fail closed with low confidence.
"""
