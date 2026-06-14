"""Sprint 23 — Prompt Contract Hardening Tests (12 tests)."""
import pathlib, pytest

ROOT = pathlib.Path(__file__).parent.parent.parent

CANONICAL_KEYS = {
    "01_market_analysis": ["market_overview", "market_size", "seasonality", "buying_triggers",
        "buying_barriers", "growth_opportunities", "channels", "risks", "confidence"],
    "04_platform": ["positioning", "usp", "big_idea", "tone_of_voice", "proof_points", "confidence"],
    "11_avatars": ["avatars", "similarity_score", "confidence"],
    "14_triggers": ["triggers", "confidence"],
    "15_offers": ["offers", "confidence"],
}

class TestMasterPromptContract:
    def test_master_prompt_has_json_only_instruction(self):
        path = ROOT / "ai_engine" / "prompts" / "system" / "master_system_prompt.py"
        content = path.read_text(encoding="utf-8")
        assert "JSON ONLY" in content, "Master prompt must explicitly require JSON only output"
        assert "schema" in content.lower(), "Master prompt must reference schema"

    def test_master_prompt_forbids_alternative_keys(self):
        path = ROOT / "ai_engine" / "prompts" / "system" / "master_system_prompt.py"
        content = path.read_text(encoding="utf-8")
        assert "alternative" in content.lower() or "DO NOT" in content, "Master prompt must forbid aliases"

    def test_schema_normalizer_aliases_match_prompts(self):
        from ai_engine.pipeline.schema_normalizer import SCHEMA_ALIASES
        for block_id, expected_keys in CANONICAL_KEYS.items():
            aliases = SCHEMA_ALIASES.get(block_id, {})
            for alias_val in set(aliases.values()):
                assert alias_val in expected_keys, f"{block_id}: alias '{alias_val}' not canonical"

class TestDriftIntegration:
    def test_all_5_blocks_in_registry(self):
        from ai_engine.prompts.registry import registry as pr
        for block_id in CANONICAL_KEYS:
            assert block_id in pr, f"{block_id} not registered"

    def test_all_5_blocks_have_prompt_files(self):
        file_map = {
            "01_market_analysis": "block_01_market_analysis_prompt.py",
            "04_platform": "block_04_platform_prompt.py",
            "11_avatars": "block_11_avatars_prompt.py",
            "14_triggers": "block_14_triggers_prompt.py",
            "15_offers": "block_15_offers_prompt.py",
        }
        for block_id, fname in file_map.items():
            path = ROOT / "ai_engine" / "prompts" / "blocks" / fname
            assert path.exists(), f"Missing: {fname}"

    def test_block_prompts_mention_canonical_keys(self):
        file_map = {
            "01_market_analysis": "block_01_market_analysis_prompt.py",
            "04_platform": "block_04_platform_prompt.py",
            "11_avatars": "block_11_avatars_prompt.py",
            "14_triggers": "block_14_triggers_prompt.py",
            "15_offers": "block_15_offers_prompt.py",
        }
        for block_id, fname in file_map.items():
            path = ROOT / "ai_engine" / "prompts" / "blocks" / fname
            if not path.exists():
                pytest.skip(f"{fname} not found (generated)")
            content = path.read_text(encoding="utf-8")
            keys = CANONICAL_KEYS[block_id]
            found = [k for k in keys if k in content]
            assert len(found) >= len(keys) * 0.5, f"{block_id}: only {len(found)}/{len(keys)} keys in prompt"

    def test_drift_tracker_counts_5_known_blocks(self):
        from ai_engine.pipeline.drift_tracker import DriftTracker
        dt = DriftTracker()
        for block_id in CANONICAL_KEYS:
            dt.record(block_id, {"raw": 1}, {"mapped": 1}, 1, 1)
        assert dt.total_drift_count() == 5

    def test_generation_service_uses_strict_assembly(self):
        path = ROOT / "backend" / "services" / "generation_service.py"
        content = path.read_text(encoding="utf-8")
        assert "PIPELINE_STRICT_ASSEMBLY" in content or "strict" in content

    def test_deepseek_provider_sends_json_schema(self):
        path = ROOT / "ai_engine" / "providers" / "deepseek.py"
        content = path.read_text(encoding="utf-8")
        assert "json_schema" in content or "json_object" in content

    def test_live_smoke_uses_normalizer(self):
        paths = [
            ROOT / "scripts" / "live_chain_5_blocks.py",
            ROOT / "scripts" / "live_chain_10_blocks.py",
        ]
        found = False
        for path in paths:
            if path.exists():
                content = path.read_text(encoding="utf-8")
                if "normalize(" in content:
                    found = True
                    break
        assert found, "Live chain scripts must use SchemaNormalizer"

    def test_drift_tracker_api_surface(self):
        from ai_engine.pipeline.drift_tracker import DriftTracker
        dt = DriftTracker()
        dt.record("test", {"k": "v"}, {"k": "v"})
        assert dt.raw_pass_rate() == 1.0
        assert dt.total_drift_count() == 0
        summary = dt.drift_summary()
        assert "raw_pass_rate" in summary
        assert "drift_blocks" in summary