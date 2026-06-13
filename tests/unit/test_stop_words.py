"""Unit tests for Stop Words registry."""

import json
from pathlib import Path

from shared.constants import STOP_WORDS, load_stop_words


class TestStopWordsStructure:
    """Test the structure of stop_words.json."""

    def test_stop_words_loaded(self):
        """Stop words should be loaded as a dict."""
        assert isinstance(STOP_WORDS, dict)
        assert "categories" in STOP_WORDS

    def test_all_required_categories_present(self):
        """All 7 required categories must be present."""
        required = [
            "marketing_fluff",
            "empty_advice",
            "placeholders",
            "hallucination_risk",
            "dangerous_promises",
            "ads_risk",
            "medical_risk",
        ]
        for category in required:
            assert category in STOP_WORDS["categories"], f"Missing category: {category}"

    def test_each_category_has_words(self):
        """Each category must have at least one word."""
        for name, category in STOP_WORDS["categories"].items():
            assert "words" in category, f"Category {name} missing 'words'"
            assert len(category["words"]) > 0, f"Category {name} has no words"

    def test_each_category_has_description(self):
        """Each category must have a description."""
        for name, category in STOP_WORDS["categories"].items():
            assert "description" in category, f"Category {name} missing 'description'"
            assert len(category["description"]) > 0

    def test_each_category_has_rule(self):
        """Each category must have a rule."""
        for name, category in STOP_WORDS["categories"].items():
            assert "rule" in category, f"Category {name} missing 'rule'"
            assert len(category["rule"]) > 0

    def test_version_present(self):
        """Stop words file must have a version."""
        assert "version" in STOP_WORDS
        assert STOP_WORDS["version"] == "1.0.0"

    def test_universal_rule_present(self):
        """Universal rule must be present."""
        assert "universal_rule" in STOP_WORDS
        assert len(STOP_WORDS["universal_rule"]) > 0


class TestStopWordsContent:
    """Test the content of stop words categories."""

    def test_marketing_fluff_contains_key_words(self):
        """Marketing fluff must include key water words."""
        words = STOP_WORDS["categories"]["marketing_fluff"]["words"]
        assert "уникальный" in words
        assert "инновационный" in words
        assert "синергия" in words
        assert "лидер рынка" in words

    def test_empty_advice_contains_key_words(self):
        """Empty advice must include key meaningless advice phrases."""
        words = STOP_WORDS["categories"]["empty_advice"]["words"]
        assert "развивать соцсети" in words
        assert "повышать узнаваемость" in words
        assert "работать над брендом" in words
        assert "улучшать маркетинг" in words

    def test_placeholders_contains_key_words(self):
        """Placeholders must include key data-absence phrases."""
        words = STOP_WORDS["categories"]["placeholders"]["words"]
        assert "нет информации" in words
        assert "не найдено" in words
        assert "ручная проверка" in words
        assert "данные отсутствуют" in words

    def test_hallucination_risk_contains_key_words(self):
        """Hallucination risk must include unverifiable guarantees."""
        words = STOP_WORDS["categories"]["hallucination_risk"]["words"]
        assert "гарантированно" in words
        assert "100%" in words
        assert "точно получите" in words

    def test_dangerous_promises_contains_key_words(self):
        """Dangerous promises must include legally risky phrases."""
        words = STOP_WORDS["categories"]["dangerous_promises"]["words"]
        assert "идеально" in words
        assert "самый лучший" in words
        assert "полная гарантия" in words

    def test_ads_risk_contains_key_words(self):
        """Ads risk must include prohibited ad claims."""
        words = STOP_WORDS["categories"]["ads_risk"]["words"]
        assert "доход гарантирован" in words
        assert "лёгкие деньги" in words
        assert "миллион за месяц" in words

    def test_medical_risk_contains_key_words(self):
        """Medical risk must include prohibited medical claims."""
        words = STOP_WORDS["categories"]["medical_risk"]["words"]
        assert "лечит" in words
        assert "медицинский препарат" in words
        assert "замена врачу" in words


class TestStopWordsDetection:
    """Test detection of stop words in text."""

    def _contains_stop_word(self, text: str, category: str) -> bool:
        """Check if text contains any stop word from a category."""
        words = STOP_WORDS["categories"][category]["words"]
        text_lower = text.lower()
        return any(word in text_lower for word in words)

    def test_detect_marketing_fluff(self):
        """Should detect marketing fluff in text."""
        assert self._contains_stop_word(
            "Наш уникальный подход гарантирует синергию",
            "marketing_fluff",
        )

    def test_no_false_positive_marketing_fluff(self):
        """Clean text should not trigger marketing fluff."""
        assert not self._contains_stop_word(
            "Опубликуйте Reels с темой 'Как выбрать зал'",
            "marketing_fluff",
        )

    def test_detect_empty_advice(self):
        """Should detect empty advice."""
        assert self._contains_stop_word(
            "Нужно развивать соцсети и повышать узнаваемость",
            "empty_advice",
        )

    def test_detect_placeholders(self):
        """Should detect placeholders."""
        assert self._contains_stop_word(
            "Требуется ручная проверка, нет информации о конкурентах",
            "placeholders",
        )

    def test_detect_hallucination_risk(self):
        """Should detect hallucination risk."""
        assert self._contains_stop_word(
            "Вы гарантированно получите 100% результат",
            "hallucination_risk",
        )

    def test_detect_dangerous_promises(self):
        """Should detect dangerous promises."""
        assert self._contains_stop_word(
            "Это самый лучший сервис с полной гарантией",
            "dangerous_promises",
        )

    def test_detect_ads_risk(self):
        """Should detect ad risks."""
        assert self._contains_stop_word(
            "Доход гарантирован, миллион за месяц без вложений",
            "ads_risk",
        )

    def test_detect_medical_risk(self):
        """Should detect medical risks."""
        assert self._contains_stop_word(
            "Наш препарат лечит и заменяет врачу",
            "medical_risk",
        )

    def test_clean_content_passes_all(self):
        """Good content should not match any stop word category."""
        clean_text = (
            "Опубликуйте пост с темой '3 ошибки при выборе фотостудии'. "
            "Используйте готовый текст. CTA: напишите ЗАЛ."
        )
        for category in STOP_WORDS["categories"]:
            assert not self._contains_stop_word(clean_text, category), (
                f"False positive in category: {category}"
            )


class TestStopWordsReload:
    """Test stop words loading."""

    def test_load_stop_words_from_file(self):
        """Should load stop words from JSON file."""
        loaded = load_stop_words()
        assert isinstance(loaded, dict)
        assert "categories" in loaded
        assert len(loaded["categories"]) == 7

    def test_json_file_exists(self):
        """The stop_words.json file must exist."""
        path = Path(__file__).parent.parent.parent / "shared" / "constants" / "stop_words.json"
        assert path.exists(), f"Stop words file not found at {path}"

    def test_json_file_is_valid(self):
        """The stop_words.json must be valid JSON."""
        path = Path(__file__).parent.parent.parent / "shared" / "constants" / "stop_words.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)