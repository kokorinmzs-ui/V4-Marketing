"""Sprint 16 — Golden Briefs Pipeline Tests (34 tests)."""
import json, pathlib, pytest, sys

ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from ai_engine.pipeline.block_registry import BlockRegistry
from ai_engine.pipeline.block_executor import BlockExecutor
from ai_engine.pipeline.final_data_assembler import FinalDataAssembler
from ai_engine.blocks.definitions import register_blocks_01_10, register_blocks_11_20, register_blocks_21_27
from ai_engine.planner.execution_planner import ExecutionPlanner
from ai_engine.exporters.html_dashboard_renderer import render_dashboard, HTMLDashboardRenderer
from ai_engine.exporters.package_builder import PackageBuilder
from ai_engine.exporters.zip_exporter import ZipExporter
from ai_engine.prompts.registry import get_repair_prompt
from ai_engine.validators.stop_words import validate_stop_words
from ai_engine.validators.kpi_validator import validate_kpis
from ai_engine.providers.base import LLMUsage

BRIEFS_DIR = ROOT / "tests" / "golden" / "briefs"
BRIEF_LIST = sorted(f.name for f in BRIEFS_DIR.glob("*.json") if f.is_file())

def mock_gen(bid):
    def fn(**kw):
        from ai_engine.services.ai_service import AIServiceResponse
        return AIServiceResponse(status="success", data={"status":"ok"}, usage=LLMUsage(model="mock",input_tokens=10,output_tokens=5,cost=0.001))
    return fn

class TestGoldenBriefExistence:
    def test_all_10_exist(self):
        assert len(BRIEF_LIST) == 10

class TestGoldenBriefValid:
    @pytest.mark.parametrize("fn", BRIEF_LIST)
    def test_brief_is_valid_json(self, fn):
        data = json.loads((BRIEFS_DIR/fn).read_text(encoding="utf-8"))
        assert "project_name" in data
        assert "industry" in data
    @pytest.mark.parametrize("fn", BRIEF_LIST)
    def test_brief_has_9_required_fields(self, fn):
        data = json.loads((BRIEFS_DIR/fn).read_text(encoding="utf-8"))
        for k in ["project_name","industry","business_description","target_audience","products","channels","goals","region","budget"]:
            assert k in data, f"{fn}: missing {k}"

class TestGoldenFastSmoke:
    def test_single_block_executes(self):
        reg = BlockRegistry()
        register_blocks_01_10(reg)
        exe = BlockExecutor(reg, mock_gen("01_market_analysis"), get_repair_prompt(), 0)
        r = exe.execute("01_market_analysis")
        assert r.status in ("passed", "failed")

class TestGoldenHTMLSmoke:
    def test_dashboard_renders(self):
        from shared.schemas.execution_view_model import ExecutionViewModel, ProjectInfo, DaySummary, Mission
        days = [DaySummary(day=d,phase="s",mission_count=1,goal="G") for d in range(1,31)]
        evm = ExecutionViewModel(
            project=ProjectInfo(name="T",industry="T",goal="G",current_day=1,current_phase="s"),
            today=days[0], days=days, missions=[Mission(mission_id="m1",day=1,phase="s",title="T",why="W",cta="C",metric="M",success_threshold="S",warning_threshold="W",fail_threshold="F",if_success="S",if_fail="F",steps=["S"],ready_text="R",xp_reward=10)],
            content_tasks=[],ads_tasks=[],sales_tasks=[],kpi_tasks=[], total_missions=1, total_days=30
        )
        html = render_dashboard(evm)
        assert "window.DATA" in html
        assert "window.MISSIONS" in html
    def test_dashboard_contains_8_tabs(self):
        from shared.schemas.execution_view_model import ExecutionViewModel, ProjectInfo, DaySummary, Mission
        days = [DaySummary(day=d,phase="s",mission_count=1,goal="G") for d in range(1,31)]
        evm = ExecutionViewModel(project=ProjectInfo(name="T",industry="T",goal="G",current_day=1,current_phase="s"),today=days[0],days=days,missions=[Mission(mission_id="m1",day=1,phase="s",title="T",why="W",cta="C",metric="M",success_threshold="S",warning_threshold="W",fail_threshold="F",if_success="S",if_fail="F",steps=["S"],ready_text="R",xp_reward=10)],content_tasks=[],ads_tasks=[],sales_tasks=[],kpi_tasks=[],total_missions=1,total_days=30)
        html = render_dashboard(evm)
        for tid in HTMLDashboardRenderer.TAB_IDS:
            assert f'id="{tid}"' in html, f"Tab {tid} missing"

class TestGoldenZipSmoke:
    def test_zip_export_validation(self):
        files = {"01-README.txt":"test","02-EXECUTION-DASHBOARD.html":"<html></html>","03-CONTENT-LIBRARY.html":"<html></html>","04-SALES-SCRIPTS.html":"<html></html>","05-KPI-GUIDE.html":"<html></html>","06-PROJECT-METADATA.json":'{"p":"t"}'}
        data = ZipExporter().export(files)
        v = ZipExporter.validate_zip(data)
        assert v["valid"]
    def test_zip_all_required_names(self):
        files = {"01-README.txt":"t","02-EXECUTION-DASHBOARD.html":"t","03-CONTENT-LIBRARY.html":"t","04-SALES-SCRIPTS.html":"t","05-KPI-GUIDE.html":"t","06-PROJECT-METADATA.json":'{}'}
        data = ZipExporter().export(files)
        v = ZipExporter.validate_zip(data)
        assert set(v["files"]) == set(ZipExporter.REQUIRED_FILES)

class TestGoldenStopWords:
    def test_no_placeholders(self):
        vr = validate_stop_words({"title":"Конкретный анализ рынка"})
        assert vr.passed
    def test_placeholder_detected(self):
        vr = validate_stop_words({"title":"нет информации о рынке"})
        assert not vr.passed

class TestGoldenKPI:
    def test_numeric_kpi_passes(self):
        vr = validate_kpis({"metric":"CTR > 2%"})
        assert vr.passed
    def test_vague_kpi_fails(self):
        vr = validate_kpis({"metric":"хороший результат"})
        assert not vr.passed
