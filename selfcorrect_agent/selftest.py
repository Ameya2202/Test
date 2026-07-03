"""End-to-end self-test (offline, deterministic).

Run from the parent directory:  python -m selfcorrect_agent.selftest
Verifies: the loop runs, self-corrects a faulty test, reaches `ready`, the
website endpoints work, and apply writes the file + a backup.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

os.environ["SELFCORRECT_MOCK"] = "1"  # force the offline provider

from .config import Config
from .agent import SelfCorrectingAgent
from .server import create_app


def main():
    cfg = Config()
    assert cfg.use_mock or not cfg.has_api_key

    # 1. Headless loop -------------------------------------------------------
    here = Path(__file__).parent
    with tempfile.TemporaryDirectory() as d:
        target = Path(d) / "example_target.py"
        shutil.copy2(here / "example_target.py", target)

        s = SelfCorrectingAgent(cfg).run(str(target))
        names = [st.name for st in s.steps]
        print("cycle:", " -> ".join(names))
        assert s.status == "ready", f"expected ready, got {s.status}"
        assert s.changed, "expected a proposed change"
        # the planted faulty test must have triggered a Correct step
        assert "Correct" in names, "expected a self-correction iteration"
        assert "Verify" in names, "expected a verify step"
        assert "Score" in names, "expected before/after scoring"
        assert s.before_score < s.after_score, "expected the candidate to improve test pass rate"
        assert s.improvement_percent > 0, "expected positive improvement"
        assert "x  y" not in s.tests_code or 'normalize_spaces("x  y") == "x y"' in s.tests_code
        print(
            f"[ok] loop reached ready in {s.attempts_used} attempts "
            f"({s.before_score}% -> {s.after_score}%, {s.improvement_percent:+.1f}% lift)"
        )

    # 2. Website endpoints ---------------------------------------------------
    from fastapi.testclient import TestClient

    with tempfile.TemporaryDirectory() as d:
        target = Path(d) / "example_target.py"
        shutil.copy2(here / "example_target.py", target)
        original = target.read_text()

        app = create_app(str(target), cfg)
        client = TestClient(app)

        assert client.get("/").status_code == 200
        assert "Self-Correcting Agent" in client.get("/").text
        assert client.get("/api/target").json()["mock"] is True

        run = client.post("/api/run", json={}).json()
        assert run["status"] == "ready" and run["changed"]
        assert run["before_score"] < run["after_score"]
        assert run["improvement_percent"] > 0
        sid = run["id"]
        print(f"[ok] /api/run -> ready, {len(run['steps'])} steps, diff has "
              f"{run['diff'].count(chr(10))} lines")

        uploaded = client.post(
            "/api/upload",
            files={"file": ("uploaded_target.py", original.encode("utf-8"), "text/x-python")},
        )
        assert uploaded.status_code == 200, uploaded.text
        upload_path = uploaded.json()["path"]
        assert Path(upload_path).is_file(), "uploaded file was not stored"
        upload_run = client.post("/api/run", json={"path": upload_path}).json()
        assert upload_run["status"] == "ready"
        assert upload_run["after_score"] == 100.0
        print("[ok] /api/upload accepted a .py file and the cycle ran against it")

        applied = client.post("/api/apply",
                              json={"session_id": sid, "write_tests": True}).json()
        assert applied["applied"] is True
        assert Path(applied["backup_path"]).is_file(), "backup not created"
        assert Path(applied["test_path"]).is_file(), "test file not written"
        assert target.read_text() != original, "target file was not updated"
        assert "split()" in target.read_text(), "improved code not written"
        # backup must preserve the original
        assert Path(applied["backup_path"]).read_text() == original
        print(f"[ok] /api/apply wrote file + backup ({Path(applied['backup_path']).name})")

    print("\nALL SELF-TESTS PASSED")


if __name__ == "__main__":
    main()
