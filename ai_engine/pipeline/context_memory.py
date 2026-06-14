"""Context Memory Layer — compact summary of upstream blocks to reduce token usage."""

from typing import Any


class ContextMemory:
    """Builds and maintains a compact memory from FinalData blocks.

    Instead of passing raw 30K+ JSON context to downstream blocks,
    creates a structured summary that preserves critical IDs and insights.
    """

    MAX_MEMORY_CHARS = 4000

    def build(self, block_data: dict[str, Any], up_to_block: str) -> dict[str, Any]:
        """Build compact memory from all available blocks up to the given block.

        Args:
            block_data: dict of block_id → block output data
            up_to_block: last block ID to include (e.g., "10_audience")

        Returns:
            Compact memory dict
        """
        memory = {}

        market = block_data.get("01_market_analysis", {})
        if market:
            memory["market_summary"] = f"{market.get('market_overview', '')} | Size: {market.get('market_size', '?')} | Channels: {market.get('channels', [])}"

        diag = block_data.get("02_business_diagnosis", {})
        if diag:
            memory["constraints"] = diag.get("constraints", [])[:3]
            memory["quick_wins"] = diag.get("quick_wins", [])[:3]
            memory["focus_areas"] = diag.get("focus_areas", [])[:2]

        comps = block_data.get("03_competitors", {})
        if comps:
            memory["competitors_count"] = len(comps.get("competitors", []))
            memory["top_competitors"] = [c.get("name") for c in comps.get("competitors", [])[:3]]

        plat = block_data.get("04_platform", {})
        if plat:
            memory["positioning"] = plat.get("positioning", "")
            memory["usp"] = plat.get("usp", "")
            memory["tone_of_voice"] = plat.get("tone_of_voice", "")

        owner = block_data.get("05_owner_portrait", {})
        if owner:
            memory["owner_expertise"] = owner.get("expertise", "")

        prods = block_data.get("06_product_system", {})
        if prods:
            keys = ["lead_magnets", "tripwires", "core_products", "flagship_products", "upsells"]
            for k in keys:
                if prods.get(k):
                    memory[f"product_{k}"] = prods[k][:3]

        aud = block_data.get("10_audience", {})
        if aud:
            memory["audience_segments"] = [s.get("segment_name") for s in aud.get("segments", [])]

        avatars = block_data.get("11_avatars", {})
        if avatars:
            av_list = avatars.get("avatars", [])
            memory["avatars"] = [{"avatar_id": a.get("avatar_id"), "name": a.get("name"), "occupation": a.get("occupation"), "fears": a.get("fears", [])[:2]} for a in av_list[:5]]
            memory["avatar_ids"] = [a["avatar_id"] for a in av_list[:5] if a.get("avatar_id")]

        pains = block_data.get("13_pains", {})
        if pains:
            pain_list = pains.get("pains", [])
            memory["pains_count"] = len(pain_list)
            memory["top_pain_ids"] = [p.get("pain_id") for p in pain_list[:10]]
            memory["pain_avatar_map"] = {p.get("pain_id"): p.get("avatar_id") for p in pain_list if p.get("pain_id")}

        triggers = block_data.get("14_triggers", {})
        if triggers:
            memory["triggers_count"] = len(triggers.get("triggers", []))

        offers = block_data.get("15_offers", {})
        if offers:
            off_list = offers.get("offers", [])
            memory["offers_count"] = len(off_list)
            memory["top_offer_ids"] = [o.get("offer_id") for o in off_list[:10]]
            memory["offer_pain_map"] = {o.get("offer_id"): o.get("pain_id") for o in off_list if o.get("offer_id")}

        funnels = block_data.get("16_funnels", {})
        if funnels:
            memory["funnel_stages"] = [s.get("stage") for s in funnels.get("steps", [])[:5]]

        ads = block_data.get("17_advertising", {})
        if ads:
            memory["ad_campaigns"] = len(ads.get("campaigns", []))
            memory["ad_budget_total"] = "500-1000 ₽"

        cp = block_data.get("18_content_plan", {})
        if cp:
            memory["content_plan_days"] = len(cp.get("days", []))

        # Truncate to max memory size
        import json
        json_str = json.dumps(memory, ensure_ascii=False)
        if len(json_str) > self.MAX_MEMORY_CHARS:
            # Drop largest fields first
            for key in ["top_pain_ids", "top_offer_ids", "pain_avatar_map", "offer_pain_map"]:
                if key in memory:
                    del memory[key]
                    json_str = json.dumps(memory, ensure_ascii=False)
                    if len(json_str) <= self.MAX_MEMORY_CHARS:
                        break

        return memory