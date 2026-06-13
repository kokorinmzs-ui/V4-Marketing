"""Unit tests for BlockExecutor."""

import pytest

from ai_engine.pipeline.block_executor import BlockExecutor
from ai_engine.pipeline.block_registry import BlockRegistry, BlockDefinition
from ai_engine.pipeline.block_result import BlockResult
from ai_engine.validators.base import ValidationIssue, ValidationResult, ValidationSeverity
from ai_engine.validators.stop_words import validate_stop_words
from ai_engine.validators.kpi_validator import validate_kpis
from ai_engine.validators.content_quality import validate_content_quality
from ai_engine.validators.actionability import validate_actionability
from ai_engine.providers.base import LLMUsage


# ============================================================
# Mock helpers
# ============================================================

def make_mock_aiservice(return_data=None, return_error=False):
    """Create a mock generate function."""
    calls = []

    def mock_gen(system_prompt="", user_prompt="", json_schema=None):
        calls.append({"system": system_prompt, "user": user_prompt})
        if return_error:
            from ai_engine.services.ai_service import AIServiceResponse
            return AIServiceResponse(status="error", error="Mock generation error")
        from ai_engine.services.ai_service import AIServiceResponse
        data = return_data or {"status": "success", "data": {"title": "Generated"}}
        return AIServiceResponse(
            status="success",
            data=data,
            usage=LLMUsage(model="mock", input_tokens=100, output_tokens=50, cost=0.0001),
        )

    mock_gen.calls = calls
    return mock_gen


def make_passing_validator(name="test_validator"):
    """Create a validator that always passes."""
    def validate(data):
        return ValidationResult(
            validator_name=name,
            passed=True,
            score=100.0,
            issues=[],
        )
    return validate


def make_failing_validator(name="test_validator", error_path="title", error_code="test_error"):
    """Create a validator that always fails."""
    def validate(data):
        return ValidationResult(
            validator_name=name,
            passed=False,
            score=50.0,
            issues=[
                ValidationIssue(
                    code=error_code,
                    message="Test error",
                    path=error_path,
                    severity=ValidationSeverity.ERROR,
                )
            ],
        )
    return validate


def make_block_registry(block_id="01_test", validators=None):
    """Create a block registry with one test block."""
    reg = BlockRegistry()
    reg.register(BlockDefinition(
        block_id=block_id,
        block_name="Test Block",
        prompt="Test system prompt",
        validators=validators or [make_passing_validator()],
    ))
    return reg


# ============================================================
# Test Successful Block
# ============================================================

class TestBlockExecutorSuccess:
    def test_successful_block_passes(self):
        mock_gen = make_mock_aiservice(
            return_data={"title": "Снять Reels про выбор зала"}
        )
        reg = make_block_registry()
        executor = BlockExecutor(
            block_registry=reg,
            generate_func=mock_gen,
            repair_prompt="Fix only errors",
        )
        result = executor.execute("01_test")
        assert result.status == "passed"
        assert result.passed is True
        assert result.all_validators_passed is True
        assert result.data["title"] == "Снять Reels про выбор зала"

    def test_block_with_real_validators_passes(self):
        """Good data passes all real validators."""
        mock_gen = make_mock_aiservice(
            return_data={
                "title": "Снять Reels про выбор фотостудии",
                "ready_text": "Если вы впервые бронируете фотостудию, напишите нам",
                "cta": "Напишите слово ЗАЛ в директ",
            }
        )
        reg = BlockRegistry()
        reg.register(BlockDefinition(
            block_id="01_test",
            block_name="Test Block",
            prompt="Test prompt",
            validators=[validate_stop_words, validate_content_quality],
        ))
        executor = BlockExecutor(
            block_registry=reg,
            generate_func=mock_gen,
            repair_prompt="Fix only errors",
        )
        result = executor.execute("01_test")
        assert result.status == "passed"
        assert result.repair_attempts == 0


# ============================================================
# Test Failed Validation
# ============================================================

class TestBlockExecutorValidation:
    def test_block_not_found(self):
        mock_gen = make_mock_aiservice()
        reg = BlockRegistry()
        executor = BlockExecutor(
            block_registry=reg,
            generate_func=mock_gen,
            repair_prompt="Fix only errors",
        )
        result = executor.execute("99_nonexistent")
        assert result.status == "failed"
        assert "not found" in result.error

    def test_generation_error(self):
        mock_gen = make_mock_aiservice(return_error=True)
        reg = make_block_registry()
        executor = BlockExecutor(
            block_registry=reg,
            generate_func=mock_gen,
            repair_prompt="Fix only errors",
        )
        result = executor.execute("01_test")
        assert result.status == "failed"
        assert "Generation failed" in result.error

    def test_validation_fails_no_repair_success(self):
        """Data has placeholder stop words (ERROR severity) → fails validation."""
        mock_gen = make_mock_aiservice(
            return_data={"title": "нет информации о рынке"}
        )
        reg = make_block_registry(
            validators=[validate_stop_words],
        )
        executor = BlockExecutor(
            block_registry=reg,
            generate_func=mock_gen,
            repair_prompt="Fix only errors",
            max_repair_attempts=0,  # No repair allowed
        )
        result = executor.execute("01_test")
        assert result.status == "failed"
        assert result.repair_attempts == 0


# ============================================================
# Test Repair
# ============================================================

class TestBlockExecutorRepair:
    def test_repair_success(self):
        """First call returns bad data, repair call returns good data."""
        call_count = [0]

        def mock_gen(system_prompt="", user_prompt="", json_schema=None):
            call_count[0] += 1
            from ai_engine.services.ai_service import AIServiceResponse
            if call_count[0] == 1:
                # First call — bad data with stop words
                return AIServiceResponse(
                    status="success",
                    data={"title": "нет информации о рынке"},
                    usage=LLMUsage(model="mock", input_tokens=100, output_tokens=50, cost=0.0001),
                )
            else:
                # Repair call — good data
                return AIServiceResponse(
                    status="success",
                    data={"title": "Анализ рынка фотостудий в Москве"},
                    usage=LLMUsage(model="mock", input_tokens=80, output_tokens=40, cost=0.0001),
                )

        reg = make_block_registry(
            validators=[validate_stop_words],
        )
        executor = BlockExecutor(
            block_registry=reg,
            generate_func=mock_gen,
            repair_prompt="Fix only errors",
            max_repair_attempts=1,
        )
        result = executor.execute("01_test")
        assert result.status == "passed"
        assert result.repaired is True
        assert result.repair_attempts > 0

    def test_repair_exhausted(self):
        """Repair keeps failing → exhausted → status=failed."""
        call_count = [0]

        def mock_gen(system_prompt="", user_prompt="", json_schema=None):
            call_count[0] += 1
            from ai_engine.services.ai_service import AIServiceResponse
            return AIServiceResponse(
                status="success",
                data={"title": "нет информации"},  # Always bad
                usage=LLMUsage(model="mock", input_tokens=100, output_tokens=50, cost=0.0001),
            )

        reg = make_block_registry(
            validators=[validate_stop_words],
        )
        executor = BlockExecutor(
            block_registry=reg,
            generate_func=mock_gen,
            repair_prompt="Fix only errors",
            max_repair_attempts=2,
        )
        result = executor.execute("01_test")
        assert result.status == "failed"
        assert "Validation failed" in result.error


# ============================================================
# Test Multiple Validators
# ============================================================

class TestBlockExecutorMultipleValidators:
    def test_chain_schema_stopwords_content(self):
        """Full validator chain: schema → stop_words → content_quality."""
        mock_gen = make_mock_aiservice(
            return_data={
                "title": "Снять Reels про выбор фотостудии",
                "ready_text": "Готовый текст длиннее 15 символов для проверки",
            }
        )
        reg = BlockRegistry()
        reg.register(BlockDefinition(
            block_id="01_test",
            block_name="Test Block",
            prompt="Test prompt",
            validators=[validate_stop_words, validate_content_quality],
        ))
        executor = BlockExecutor(
            block_registry=reg,
            generate_func=mock_gen,
            repair_prompt="Fix only errors",
        )
        result = executor.execute("01_test")
        assert result.status == "passed"
        assert len(result.validation_results) == 2  # Both validators ran

    def test_one_validator_fails_others_pass(self):
        """Stop words pass but KPI fails."""
        mock_gen = make_mock_aiservice(
            return_data={
                "title": "Clean title",
                "metric": "хороший результат",  # Vague KPI
            }
        )
        reg = BlockRegistry()
        reg.register(BlockDefinition(
            block_id="01_test",
            block_name="Test Block",
            prompt="Test prompt",
            validators=[validate_stop_words, validate_kpis],
        ))
        executor = BlockExecutor(
            block_registry=reg,
            generate_func=mock_gen,
            repair_prompt="Fix only errors",
            max_repair_attempts=0,
        )
        result = executor.execute("01_test")
        assert result.status == "failed"


# ============================================================
# Test Context Passing
# ============================================================

class TestBlockExecutorContext:
    def test_context_passed_to_generate(self):
        mock_gen = make_mock_aiservice()
        reg = make_block_registry()
        executor = BlockExecutor(
            block_registry=reg,
            generate_func=mock_gen,
            repair_prompt="Fix only errors",
        )
        context = {"brief": {"project_name": "Test", "industry": "photography"}}
        result = executor.execute("01_test", context=context)
        assert result.status == "passed"
        # Check that context was included in user prompt
        user_prompts = " ".join(c["user"] for c in mock_gen.calls)
        assert "Test" in user_prompts or "photography" in user_prompts


# ============================================================
# Test Usage Tracking
# ============================================================

class TestBlockExecutorUsage:
    def test_usage_tracked(self):
        mock_gen = make_mock_aiservice()
        reg = make_block_registry()
        executor = BlockExecutor(
            block_registry=reg,
            generate_func=mock_gen,
            repair_prompt="Fix only errors",
        )
        result = executor.execute("01_test")
        assert result.usage.input_tokens > 0
        assert result.total_usage.total_tokens() > 0


# ============================================================
# Test Block Registry
# ============================================================

class TestBlockRegistry:
    def test_register_and_get(self):
        reg = BlockRegistry()
        reg.register(BlockDefinition(block_id="01_test", block_name="Test"))
        assert "01_test" in reg
        assert reg.get("01_test").block_name == "Test"

    def test_get_none_for_missing(self):
        reg = BlockRegistry()
        assert reg.get("missing") is None

    def test_check_complete(self):
        reg = BlockRegistry()
        reg.register(BlockDefinition(block_id="01_test"))
        ok, missing = reg.check_complete(["01_test"])
        assert ok is True
        ok, missing = reg.check_complete(["01_test", "02_missing"])
        assert ok is False
        assert "02_missing" in missing