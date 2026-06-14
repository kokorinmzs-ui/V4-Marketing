"""Schema Normalizer — maps live AI output keys to expected Pydantic schema keys.

Evidence from live_chain_10_blocks.json:
- Block 01: AI returns `market_trends`, `price_benchmark`, `key_insights` instead of `market_overview`, `buying_triggers`
- Block 04: AI returns `usp` instead of `unique_selling_proposition`
- Block 11: AI returns `avatar_list` instead of `avatars`
- Block 14: AI returns `trigger_list` instead of `triggers`
- Block 15: AI returns `offer_list` instead of `offers`

This module provides a mapping layer so valuable AI insights are not discarded.
"""

from typing import Any


SCHEMA_ALIASES: dict[str, dict[str, str]] = {
    "01_market_analysis": {
        "market_trends": "market_overview",
        "price_benchmark": "buying_barriers",
        "key_insights": "growth_opportunities",
        "confidence_score": "confidence",
        "recommendations": "growth_opportunities",
    },
    "02_business_diagnosis": {
        "bottlenecks": "constraints",
        "critical_bottleneck": "growth_barriers",
        "bottleneck_impact_on_kpi": "focus_areas",
        "bottleneck_root_causes": "constraints",
        "bottleneck_priority_score": "confidence",
    },
    "03_competitors": {
        "competitor_list": "competitors",
        "differentiation_angles": "advantages",
        "market_gaps": "gaps",
    },
    "04_platform": {
        "unique_selling_proposition": "usp",
    },
    "06_product_system": {
        "product_lineup": "lead_magnets",
        "entry_offer": "tripwires",
        "main_offer": "core_products",
        "premium_offer": "flagship_products",
    },
    "10_audience": {
        "audience_segments": "segments",
        "max_segment_count": "max_segments",
    },
    "11_avatars": {
        "avatar_list": "avatars",
        "avatar_profiles": "avatars",
        "similarity_index": "similarity_score",
    },
    "13_pains": {
        "pain_list": "pains",
        "pain_points": "pains",
    },
    "14_triggers": {
        "trigger_list": "triggers",
        "marketing_triggers": "triggers",
    },
    "15_offers": {
        "offer_list": "offers",
        "marketing_offers": "offers",
    },
}

FIELD_DEFAULTS: dict[str, dict[str, Any]] = {
    "01_market_analysis": {
        "market_overview": "Рынок не определён — недостаточно данных в brief",
        "market_size": "Неизвестно",
        "seasonality": [],
        "buying_triggers": [],
        "buying_barriers": [],
        "growth_opportunities": [],
        "channels": [],
        "risks": [],
        "confidence": "low",
    },
    "04_platform": {
        "positioning": "Не определено",
        "usp": "Не определено",
        "big_idea": "Не определена",
        "tone_of_voice": "Не определён",
        "proof_points": [],
        "confidence": "low",
    },
    "11_avatars": {
        "avatars": [],
        "similarity_score": 0.0,
        "confidence": "low",
    },
    "14_triggers": {
        "triggers": [],
        "confidence": "low",
    },
    "15_offers": {
        "offers": [],
        "confidence": "low",
    },
}


def normalize(block_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Apply schema aliases and fill missing fields with safe defaults.

    Args:
        block_id: e.g., "01_market_analysis"
        data: raw AI output dict

    Returns:
        Normalized dict matching expected Pydantic schema
    """
    if not isinstance(data, dict):
        return data

    aliases = SCHEMA_ALIASES.get(block_id, {})
    defaults = FIELD_DEFAULTS.get(block_id, {})

    result = {}
    for key, value in data.items():
        # Skip status wrapper keys
        if key in ("status", "confidence_score"):
            # Map confidence_score → confidence
            if key == "confidence_score":
                result["confidence"] = str(value) if value else "low"
            continue

        # Apply alias mapping
        mapped_key = aliases.get(key, key)
        result[mapped_key] = value

    # Fill missing required fields with safe defaults
    for field, default_value in defaults.items():
        if field not in result:
            result[field] = default_value

    return result