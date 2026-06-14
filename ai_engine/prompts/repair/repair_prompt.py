"""
Repair Prompt - used ONLY when validation FAILED.
Fixes only erroneous fields, does NOT rewrite the entire block.
"""

VERSION = "1.0.0"

REPAIR_PROMPT = """
# REPAIR PROMPT - Marketing OS v4

## INSTRUCTION
You are fixing validation errors in a previously generated block.
DO NOT rewrite the entire block.
Fix ONLY the fields listed in "errors".
Keep all other fields EXACTLY as they were.
Act like a patch engineer: minimal diff, no collateral changes, preserve context.

## INPUT FORMAT
{
  "block": "block_name",
  "errors": [
    {"code": "missing_cta", "field": "offers[0].cta", "message": "CTA is missing"},
    {"code": "kpi_vague", "field": "metric", "message": "Use numeric KPI"}
  ],
  "original_data": { ... original block JSON ... }
}

## RULES
1. Fix ONLY the fields listed in "errors".
2. Do NOT add new data to other fields.
3. Do NOT regenerate content for fields without errors.
4. Return ONLY the corrected JSON.
5. Format: {"status": "success", "data": { ... corrected block ... }}
6. If you cannot fix an error: {"status": "error", "unfixable": ["error_code"]}
7. If the block is missing core context, fail closed instead of inventing it.

## FORBIDDEN
- Rewriting the entire block
- Adding new content not requested
- Removing fields that passed validation
- Writing explanations
- Writing markdown
- Silent context drift
"""
