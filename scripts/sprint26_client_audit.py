"""Sprint 26 — Client Output Validation Script.

Generates 3 projects, approves them, and audits client deliverables:
dashboard.html, client-package.zip, final_data.json, etc.
"""
import json, pathlib, tempfile, sys, zipfile, io

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from backend.app import app
from backend.dependencies import get_project_service, get_artifact_service, get_generation_service
from backend.services.project_service import ProjectService
from backend.services.artifact_service import ArtifactService
from backend.services.generation_service import GenerationService

tmp = tempfile.mkdtemp(prefix="mo_s26_")
ps = ProjectService(str(tmp) + "/projects")
asvc = ArtifactService(ps)
gs = GenerationService(ps)

app.dependency_overrides[get_project_service] = lambda: ps
app.dependency_overrides[get_artifact_service] = lambda: asvc
app.dependency_overrides[get_generation_service] = lambda: gs

client = TestClient(app)

BRIEFS = {
    "dental": {
        "project_name": "Stomatologiya White Fang",
        "industry": "dentistry",
        "business_description": "Private dental clinic SPb. 5 rooms, microscope, implantation. Since 2015.",
        "products": ["Caries treatment", "Implantation", "Pediatric dentistry"],
        "goals": ["50 patients/month", "Loyalty program"],
        "region": "SPb",
    },
    "photo": {
        "project_name": "Photo Studio Air",
        "industry": "photography",
        "business_description": "Photo studio rental Moscow. 7 halls, Profoto, cyclorama. Since 2018.",
        "products": ["Hall rental", "Full day", "Equipment"],
        "goals": ["80% hall load", "30 leads/month"],
        "region": "Moscow",
    },
    "b2b": {
        "project_name": "B2B Marketing Service",
        "industry": "b2b_marketing",
        "business_description": "B2B marketing agency. Leadgen, email, content. 10 clients.",
        "products": ["Audit", "Leadgen monthly", "Content marketing"],
        "goals": ["5 contracts/quarter", "Own funnel"],
        "region": "Moscow/Russia",
    }
}

AUDIT_DIR = ROOT / "audit" / "sprint26"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

results = {}
for niche, brief_data in BRIEFS.items():
    name = brief_data["project_name"]
    print("\n" + "=" * 60)
    print("CLIENT AUDIT: " + name)
    print("=" * 60)

    resp = client.post("/projects", json={"name": name, "brief": brief_data})
    pid = resp.json()["project_id"]
    print("  Project: " + pid)

    gen = client.post("/projects/" + pid + "/generate")
    status = gen.json()["status"]
    print("  Generated: " + status)
    assert status == "review_required", "Expected review_required, got " + status
    print("  Review gate: OK (review_required)")

    appr = client.post("/projects/" + pid + "/review/approve")
    appr_status = appr.json()["status"]
    print("  Approved: " + appr_status)
    assert appr_status == "client_ready"

    artifacts = client.get("/projects/" + pid + "/artifacts").json()
    print("  Artifacts: " + str(len(artifacts)) + " files")
    artifact_names = [a["name"] for a in artifacts]
    for a in artifacts:
        print("    " + a["name"] + ": " + str(a["size"]) + " bytes")

    required = ["brief.json", "final_data.json", "execution_view_model.json",
                "dashboard.html", "generation_report.json", "client-package.zip"]
    for req in required:
        assert req in artifact_names, "Missing: " + req
    print("  All 6 artifacts: OK")

    db = client.get("/projects/" + pid + "/download/dashboard.html")
    db_text = db.text
    print("  Dashboard: " + str(len(db_text)) + " chars")
    assert len(db_text) > 1000, "Dashboard too small"
    assert "<script>" in db_text, "Dashboard has no JS"
    print("  Dashboard JS: OK")

    zip_resp = client.get("/projects/" + pid + "/download/client-package.zip")
    zip_data = zip_resp.content
    print("  ZIP: " + str(len(zip_data)) + " bytes")
    assert len(zip_data) > 100, "ZIP too small"

    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        zip_files = zf.namelist()
        print("  ZIP contents: " + str(len(zip_files)) + " files")
        for zfn in zip_files:
            info = zf.getinfo(zfn)
            print("    " + zfn + ": " + str(info.file_size) + " bytes")

    fd = client.get("/projects/" + pid + "/download/final_data.json")
    fd_data = json.loads(fd.text)
    print("  FinalData keys: " + str(len(fd_data.keys())))

    evm = client.get("/projects/" + pid + "/download/execution_view_model.json")
    evm_data = json.loads(evm.text)
    missions = evm_data.get("missions", [])
    print("  Missions: " + str(len(missions)))

    results[niche] = {
        "project_id": pid,
        "artifacts": len(artifacts),
        "dashboard_chars": len(db_text),
        "zip_bytes": len(zip_data),
        "zip_files": len(zip_files),
        "fd_keys": len(fd_data.keys()),
        "missions": len(missions),
    }

report = {
    "mode": "mock",
    "projects": results,
    "artifact_existence": True,
    "dashboard_opens": True,
    "zip_valid": True,
    "review_gate": True,
    "verdict": "PARTIAL - mock only, needs live AI for full PASS"
}
(AUDIT_DIR / "client_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

print("\n" + "=" * 60)
print("SPRINT 26 AUDIT COMPLETE")
print("Results in: " + str(AUDIT_DIR / "client_audit.json"))
for niche, r in results.items():
    print("  " + niche + ": " + str(r["artifacts"]) + " artifacts, " + str(r["missions"]) + " missions, dashboard=" + str(r["dashboard_chars"]) + "chars, zip=" + str(r["zip_bytes"]) + "b")