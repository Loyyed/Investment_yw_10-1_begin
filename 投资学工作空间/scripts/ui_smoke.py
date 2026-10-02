"""Hidden Tk smoke checks; all button-driven saves use a temporary workspace."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
sys.dont_write_bytecode = True
import tempfile
import time
import tkinter as tk
from unittest.mock import patch

from review_ui import COMPARABILITY, GROUPS, ReviewApp, WORKSPACE, read_json
from review_store import ReviewStore


def fingerprints(workspace):
    result = {}
    for folder in ("config", "evidence", "outputs", "tasks", "work", "docs", "sources/annual_reports"):
        for path in (workspace / folder).rglob("*"):
            if path.is_file() and "pdf-text" not in path.parts:
                result[str(path.relative_to(workspace))] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name in ("README.md", "工作流程与文件说明.md", "工作台.html", "sources/manifest.json"):
        path = workspace / name
        if path.is_file():
            result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def build_hidden(workspace, store=None):
    root = tk.Tk()
    root.withdraw()
    app = ReviewApp(root, workspace, store)
    root.update_idletasks()
    return root, app


def main():
    before = fingerprints(WORKSPACE)
    root, app = build_hidden(WORKSPACE)
    try:
        assert set(app.tree.selection()) == {"C01", "C02"}
        assert app.actor_var.get() == "Leo", app.actor_var.get()
        saved_flags = app.store.comparison_snapshot().get("flags", {})
        assert {key: variable.get() for key, variable in app.compare_vars.items()} == {key: saved_flags.get(key) is True for key, _ in COMPARABILITY}, "Opening UI changed comparability flags"
        assert len(app.notebook.tabs()) == 2
        assert app.fact_button.winfo_exists()
        assert not app.computing
    finally:
        root.destroy()
    assert fingerprints(WORKSPACE) == before, "Opening UI wrote real workspace data"

    with tempfile.TemporaryDirectory(prefix="review-ui-smoke-") as tmp:
        test_workspace = Path(tmp)
        for folder in ("config", "evidence", "outputs", "tasks", "docs"):
            shutil.copytree(WORKSPACE / folder, test_workspace / folder)
        (test_workspace / "sources").mkdir()
        shutil.copy2(WORKSPACE / "sources/manifest.json", test_workspace / "sources/manifest.json")
        shutil.copytree(WORKSPACE / "sources/annual_reports", test_workspace / "sources/annual_reports")
        for name in ("README.md", "工作流程与文件说明.md", "工作台.html"):
            shutil.copy2(WORKSPACE / name, test_workspace / name)
        (test_workspace / "work").mkdir()
        for path in (WORKSPACE / "work").iterdir():
            if path.is_file() and path.suffix in (".json", ".md", ".jsonl"):
                shutil.copy2(path, test_workspace / "work" / path.name)
        (test_workspace / "scripts").mkdir()
        for name in ("07_compute_changes.py", "common.py", "review_store.py"):
            shutil.copy2(WORKSPACE / "scripts" / name, test_workspace / "scripts" / name)
        root, app = build_hidden(test_workspace, ReviewStore(test_workspace))
        try:
            with patch("os.startfile", create=True) as opener:
                original_flags = {key: variable.get() for key, variable in app.compare_vars.items()}
                app.fact_button.invoke()
                root.update()
                assert all(app.by_id[rid]["state"] == "Fact" for rid in ("C01", "C02"))
                assert "部分视图" not in app.status_var.get(), app.status_var.get()
                app.sync_button.invoke()
                root.update()
                assert "已刷新同步" in app.status_var.get(), app.status_var.get()
                assert {key: variable.get() for key, variable in app.compare_vars.items()} == original_flags, "First-task Fact changed comparability"
                app.unknown_button.invoke()
                root.update()
                assert all(app.by_id[rid]["state"] == "Unknown" for rid in ("C01", "C02"))
                app.fact_button.invoke()
                root.update()
                assert all(app.by_id[rid]["state"] == "Fact" for rid in ("C01", "C02"))
                app.group_var.set(next(label for label, group in GROUPS.items() if group == "all"))
                app.select_all_button.invoke()
                assert len(app.tree.selection()) == len(app.candidates)
                for variable in app.compare_vars.values():
                    variable.set(False)
                app._update_all_comparable()
                app.all_comparable_check.invoke()
                assert all(v.get() for v in app.compare_vars.values())
                key = COMPARABILITY[0][0]
                app.comparability_checks[key].invoke()
                assert not app.all_comparable_var.get() and not app.compare_vars[key].get()
                app.comparability_checks[key].invoke()
                assert app.all_comparable_var.get()
                app.save_compare_button.invoke()
                deadline = time.monotonic() + 30
                while app.computing and time.monotonic() < deadline:
                    root.update()
                    time.sleep(0.02)
                assert not app.computing, "Recalculation timed out"
                result = read_json(test_workspace / "work/change-recalculation.json", {})
                assert result.get("status") == "calculated-awaiting-human-verification", app.compare_status_var.get()
                assert len(result.get("results", [])) == 2
                assert "已有复算结果" in app.result_text.get("1.0", "end")

                # Saving must confirm what this window displayed, not a changed source.
                app.group_var.set(next(label for label, group in GROUPS.items() if group == "first"))
                root.update()
                ledger = test_workspace / "evidence/review-state.json"
                event_count = len(read_json(ledger, {}).get("events", []))
                candidate_path = test_workspace / "work/evidence-candidates.md"
                candidate_text = candidate_path.read_text(encoding="utf-8")
                candidate_changed = candidate_text.replace("170,899,152,276.34", "170,899,152,276.35", 1)
                assert candidate_changed != candidate_text
                candidate_path.write_text(candidate_changed, encoding="utf-8")
                app.fact_button.invoke()
                root.update()
                assert len(read_json(ledger, {}).get("events", [])) == event_count, "Changed candidate was confirmed using old display"
                assert app.by_id["C01"]["state"] != "Fact"
                assert "本次未确认" in app.status_var.get(), app.status_var.get()
                assert all(not v.get() for v in app.compare_vars.values())
                candidate_path.write_text(candidate_text, encoding="utf-8")
                app.sync_button.invoke()
                root.update()

                pdf = test_workspace / app.by_id["C01"]["pdf_path"]
                pdf_bytes = pdf.read_bytes()
                event_count = len(read_json(ledger, {}).get("events", []))
                pdf.write_bytes(pdf_bytes + b"\n% changed during UI smoke\n")
                app.fact_button.invoke()
                root.update()
                assert len(read_json(ledger, {}).get("events", [])) == event_count, "Changed PDF was confirmed using old display"
                assert app.by_id["C01"]["state"] != "Fact"
                assert "本次未确认" in app.status_var.get()
                assert all(not v.get() for v in app.compare_vars.values())

                app.all_comparable_check.invoke()
                assert all(v.get() for v in app.compare_vars.values())
                pdf.write_bytes(pdf_bytes + b"\n% changed again after comparison display\n")
                app.save_compare_button.invoke()
                root.update()
                assert len(read_json(ledger, {}).get("events", [])) == event_count, "Changed comparison was confirmed using old display"
                assert not app.computing
                assert "本次可比性未保存" in app.compare_status_var.get(), app.compare_status_var.get()
                assert all(not v.get() for v in app.compare_vars.values())
                assert not app.all_comparable_var.get()
                pdf.write_bytes(pdf_bytes)
                app.sync_button.invoke()
                root.update()

                # Raw display and normalized computation may never silently diverge.
                data_path = test_workspace / "work/structured-data.json"
                source_data = data_path.read_text(encoding="utf-8")
                data = json.loads(source_data)
                current = next(row for row in data["summary"] if row["year"] == 2024 and row["metric"] == "营业收入")
                current["current"] = "170899152276.35"
                data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                event_count = len(read_json(ledger, {}).get("events", []))
                app.sync_button.invoke()
                root.update()
                assert app.comparison_binding is None
                assert "不一致" in app.compare_status_var.get(), app.compare_status_var.get()
                assert str(app.save_compare_button.cget("state")) == "disabled"
                app.all_comparable_check.invoke()
                app.save_compare_button.invoke()
                assert len(read_json(ledger, {}).get("events", [])) == event_count
                assert not app.computing
                data_path.write_text(source_data, encoding="utf-8")
                opener.assert_not_called()
        finally:
            root.destroy()
    assert fingerprints(WORKSPACE) == before, "Temporary button tests modified real workspace"
    print("UI smoke passed: readonly startup; default selection/reviewer; temporary button saves; checkbox linkage; recalculation; stale candidate/PDF/comparison rejection; normalized/raw mismatch blocked; no PDF launch.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
