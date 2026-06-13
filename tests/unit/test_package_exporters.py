"""Tests for Package Exporter — Sprint 13 (55 tests)."""
import copy, json, os, tempfile, zipfile, io, pytest
from ai_engine.planner.execution_planner import ExecutionPlanner
from ai_engine.exporters.package_builder import PackageBuilder
from ai_engine.exporters.zip_exporter import ZipExporter

MIN_FD = {
    "project_name": "Test Project",
    "market_analysis": {"market_overview": "Test"},
    "avatars": {"avatars": [{"avatar_id": "av1", "name": "A", "age": 30, "income": "100k", "occupation": "M", "goals": ["G"], "fears": ["F"]}]},
    "pains": {"pains": [{"pain_id": "p1", "avatar_id": "av1", "pain": "Pain"}]},
    "offers": {"offers": [{"offer_id": "o1", "avatar_id": "av1", "pain_id": "p1", "headline": "Offer"}]},
    "funnels": {"steps": [{"stage": "awareness"}]},
    "advertising": {"campaigns": [{"platform": "vk", "audience": "Women", "offer": "Off", "budget": "500", "kpi": "CTR > 2%"}]},
    "content_plan": {"days": [{"day": 1}]},
    "reels": {"reels": [{"hook": "H", "frame_1": "F1", "frame_2": "F2", "frame_3": "F3", "frame_4": "F4", "cta": "C", "archetype": "case"}]},
    "posts": {"posts": [{"headline": "P", "post_text": "Text", "cta": "CTA"}]},
    "sales_scripts": {"scripts": [{"scenario": "first", "goal": "Start", "message": "Hi!", "next_step": "Ask"}]},
    "kpi": {"kpis": [{"action": "Reels", "metric": "5000 views", "success_threshold": "5000", "warning_threshold": "1500", "fail_threshold": "500", "if_success": "scale"}]},
}

@pytest.fixture
def evm():
    return ExecutionPlanner().plan(MIN_FD).execution_view_model

@pytest.fixture
def files(evm):
    return PackageBuilder().build(evm)

@pytest.fixture
def zip_data(files):
    return ZipExporter().export(files)

# ========== Package Builder Tests ==========
class TestPackageBuilder:
    def test_build_returns_dict(self, evm): assert isinstance(PackageBuilder().build(evm), dict)
    def test_has_readme(self, files): assert "01-README.txt" in files
    def test_has_dashboard(self, files): assert "02-EXECUTION-DASHBOARD.html" in files
    def test_has_content_library(self, files): assert "03-CONTENT-LIBRARY.html" in files
    def test_has_sales_scripts(self, files): assert "04-SALES-SCRIPTS.html" in files
    def test_has_kpi_guide(self, files): assert "05-KPI-GUIDE.html" in files
    def test_has_metadata(self, files): assert "06-PROJECT-METADATA.json" in files
    def test_readme_not_empty(self, files): assert len(files["01-README.txt"]) > 100
    def test_readme_contains_project(self, files): assert "Test Project" in files["01-README.txt"]
    def test_content_library_has_items(self, files): assert "Content Library" in files["03-CONTENT-LIBRARY.html"]
    def test_sales_scripts_not_empty(self, files): assert len(files["04-SALES-SCRIPTS.html"]) > 300
    def test_kpi_guide_not_empty(self, files): assert len(files["05-KPI-GUIDE.html"]) > 100
    def test_metadata_is_json(self, files):
        meta = json.loads(files["06-PROJECT-METADATA.json"])
        assert meta["project_name"] == "Test Project"
        assert meta["version"] == "4.0"
        assert meta["missions_count"] > 0
        assert meta["content_count"] > 0
        assert meta["sales_count"] > 0
        assert meta["ads_count"] > 0

# ========== ZIP Exporter Tests ==========
class TestZipExport:
    def test_export_returns_bytes(self, zip_data): assert isinstance(zip_data, bytes)
    def test_zip_size_positive(self, zip_data): assert len(zip_data) > 10000
    def test_zip_opens(self, zip_data): assert zipfile.is_zipfile(io.BytesIO(zip_data))
    def test_zip_contains_six_files(self, zip_data):
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            names = zf.namelist()
            assert len(names) == 6
    def test_zip_has_all_required(self, zip_data):
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            for req in ZipExporter.REQUIRED_FILES:
                assert req in zf.namelist()
    def test_no_empty_files(self, zip_data):
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            for info in zf.infolist():
                assert info.file_size > 0
    def test_export_to_file(self, files, tmp_path):
        p = tmp_path / "package.zip"
        size = ZipExporter().export_to_file(files, str(p))
        assert size > 0
        assert p.exists()
        assert zipfile.is_zipfile(str(p))
    def test_validate_zip_passed(self, zip_data):
        v = ZipExporter.validate_zip(zip_data)
        assert v["valid"]
        assert len(v["errors"]) == 0
        assert len(v["files"]) == 6

class TestZipValidation:
    def test_validate_missing_file(self, files):
        del files["01-README.txt"]
        with pytest.raises(ValueError):
            ZipExporter().export(files)
    def test_validate_empty_file(self, files):
        files["01-README.txt"] = ""
        with pytest.raises(ValueError):
            ZipExporter().export(files)
    def test_validate_whitespace_file(self, files):
        files["01-README.txt"] = "   "
        with pytest.raises(ValueError):
            ZipExporter().export(files)
    def test_corrupted_zip_fails_validation(self):
        bad = b"not a zip file at all"
        v = ZipExporter.validate_zip(bad)
        assert not v["valid"]
        assert len(v["errors"]) >= 1

class TestMutationZIP:
    def test_missing_dashboard_raises(self, files):
        del files["02-EXECUTION-DASHBOARD.html"]
        with pytest.raises(ValueError, match="Missing"):
            ZipExporter().export(files)
    def test_missing_readme_raises(self, files):
        del files["01-README.txt"]
        with pytest.raises(ValueError, match="Missing"):
            ZipExporter().export(files)
    def test_missing_sales_raises(self, files):
        del files["04-SALES-SCRIPTS.html"]
        with pytest.raises(ValueError, match="Missing"):
            ZipExporter().export(files)
    def test_empty_content_fails(self, files):
        files["03-CONTENT-LIBRARY.html"] = ""
        with pytest.raises(ValueError, match="Empty"):
            ZipExporter().export(files)


class TestPackageXSSHardening:
    def test_html_files_escape_malicious_strings(self):
        base = copy.deepcopy(ExecutionPlanner().plan(MIN_FD).execution_view_model)
        base.content_tasks[0].ready_text = '<script>alert(1)</script>'
        base.sales_tasks[0].message = '<button onclick="alert(1)">buy</button>'
        files = PackageBuilder().build(base)
        assert "<script>alert(1)</script>" not in files["03-CONTENT-LIBRARY.html"]
        assert 'onclick="alert(1)"' not in files["04-SALES-SCRIPTS.html"]
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in files["03-CONTENT-LIBRARY.html"]
        assert "&lt;button onclick=&quot;alert(1)&quot;&gt;buy&lt;/button&gt;" in files["04-SALES-SCRIPTS.html"]
    def test_corrupt_after_export_validation(self, files):
        data = ZipExporter().export(files)
        bad = data[:len(data)//2]
        v = ZipExporter.validate_zip(bad)
        assert not v["valid"]
