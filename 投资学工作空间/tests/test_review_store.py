"""Review tests run only on temporary fixtures inside the development workspace."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from hashlib import sha256
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch


WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "scripts"))
from review_store import FLAGS, ReviewStore


class ReviewStoreTests(unittest.TestCase):
    def setUp(self):
        root = WORKSPACE / "work" / ".review-test-fixtures"
        root.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="review-", dir=root)
        self.addCleanup(self.temporary.cleanup)
        self.fixture = Path(self.temporary.name)
        self.assertTrue(self.fixture.is_relative_to(WORKSPACE))
        for relative in (
            "work/evidence-candidates.md", "work/metric-scope-candidates.md", "work/structured-data.json", "work/scope-data.json",
            "tasks/01-first-task.md", "evidence/evidence-log.md", "evidence/human-review-forms.md",
            "outputs/first-analysis.md", "outputs/revenue-structure-table.md", "outputs/metric-scope-decision.md",
            "docs/task-status.md", "work/pending-checks.md", "README.md", "config/human-review.json",
            "工作台.html", "工作流程与文件说明.md",
        ):
            source, destination = WORKSPACE / relative, self.fixture / relative
            if source.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
        # Small PDF byte fixtures are deliberate; the ledger binds actual bytes,
        # independent of PDF text extraction or the historical manifest.
        self.pdf_dir = self.fixture / "sources/annual_reports/pdf"
        self.pdf_dir.mkdir(parents=True)
        for year in range(2020, 2025):
            (self.pdf_dir / f"600519_{year}_fixture.pdf").write_bytes(f"%PDF-1.4\nfixture {year}\n%%EOF".encode())
        raw = self.fixture / "work/structured-data.json"
        data = json.loads(raw.read_text(encoding="utf-8"))
        for row in data["summary"]:
            row["pdf"] = f"sources/annual_reports/pdf/600519_{row['year']}_fixture.pdf"
        raw.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self.store = ReviewStore(self.fixture)

    def read(self, relative):
        return (self.fixture / relative).read_text(encoding="utf-8-sig")

    def state(self):
        return json.loads(self.read("evidence/review-state.json"))

    def view(self):
        return json.loads(self.read("evidence/confirmed-facts.json"))

    def test_initial_read_does_not_write_and_zero_events_do_not_promote(self):
        self.assertEqual(self.store.get_profile()["reviewer"], "Leo")
        rows = self.store.list_candidates()
        self.assertEqual(len(rows), 63)
        self.assertEqual(len(self.store.list_candidates("first")), 2)
        self.assertEqual(len(self.store.list_candidates("revenue")), 51)
        self.assertEqual(len(self.store.list_candidates("scope")), 12)
        self.assertFalse((self.fixture / "evidence/review-state.json").exists())
        self.assertFalse((self.fixture / "evidence/confirmed-facts.json").exists())
        result = self.store.sync()
        self.assertEqual(result["event_count"], 0)
        self.assertEqual(self.view()["facts"], [])
        self.assertTrue(all(r["state"] == "Unknown" for r in rows))
        self.assertFalse((self.fixture / "evidence/review-state.json").exists())

    def test_report_year_is_not_confused_with_following_publication_year(self):
        for year in range(2020, 2025):
            source = self.pdf_dir / f"600519_{year}_fixture.pdf"
            source.rename(self.pdf_dir / f"600519_{year}_贵州茅台{year}年年度报告_{year + 1}-04-03.pdf")
        rows = self.store.list_candidates()
        self.assertTrue(all(r["pdf_sha256"] for r in rows))
        self.assertTrue(all(f"600519_{r['year']}_" in r["pdf_path"] for r in rows))
        result = self.store.submit(["C01", "C02"])
        self.assertEqual(result["counts"]["Fact"], 2)

    def test_profile_remembers_last_explicit_reviewer_without_editing_contract(self):
        before = self.read("tasks/01-first-task.md")
        self.store.submit(["C01"], actor="核验者甲")
        self.assertEqual(self.store.get_profile()["reviewer"], "核验者甲")
        result = self.store.submit(["C02"], actor=self.store.get_profile()["reviewer"])
        self.assertEqual(result["results"][0]["actor"], "核验者甲")
        self.assertIn("执行人：__Leo__", self.read("tasks/01-first-task.md"))
        self.assertEqual(before.count("- [ ]"), self.read("tasks/01-first-task.md").count("- [ ]"))

    def test_confirm_two_updates_all_views_and_shanghai_date(self):
        sources_before = self.read("work/evidence-candidates.md")
        raw_before = self.read("work/structured-data.json")
        config_before = self.read("config/human-review.json")
        result = self.store.submit(["C01", "C02"], actor=self.store.get_profile()["reviewer"], note="逐页核对原表")
        self.assertEqual(result["changed"], 2)
        self.assertEqual(result["counts"]["Fact"], 2)
        self.assertEqual(result["sync_errors"], [])
        self.assertEqual({r["id"] for r in self.view()["facts"]}, {"C01", "C02"})
        self.assertEqual(self.view()["facts"], self.store.facts())
        self.assertTrue(all(r["actor"] == "Leo" and r["confirmed_at"].endswith("+08:00") for r in self.store.facts()))
        for relative in ("evidence/evidence-log.md", "outputs/first-analysis.md", "outputs/metric-scope-decision.md",
                         "docs/task-status.md", "work/pending-checks.md", "README.md", "工作流程与文件说明.md"):
            self.assertIn("Fact", self.read(relative))
        self.assertIn("C01、C02有效Fact为2/2条", self.read("tasks/01-first-task.md"))
        self.assertIn("Fact／已核验", self.read("evidence/human-review-forms.md"))
        self.assertIn("当前有效Fact为2条", self.read("工作台.html"))
        self.assertNotIn("已人工签认Fact为0条", self.read("evidence/evidence-log.md"))
        self.assertEqual(sources_before, self.read("work/evidence-candidates.md"))
        self.assertEqual(raw_before, self.read("work/structured-data.json"))
        self.assertEqual(config_before, self.read("config/human-review.json"))
        with self.assertRaises(ValueError):
            self.store.validate_comparability()

    def test_idempotence_unknown_and_withdraw_keep_history(self):
        self.store.submit(["C01", "C02", "C01"], actor="Leo", note="原文确认")
        before = self.read("evidence/review-state.json")
        self.assertEqual(self.store.submit(["C01", "C02"], actor="Leo", note="原文确认")["changed"], 0)
        self.assertEqual(before, self.read("evidence/review-state.json"))
        self.assertEqual(self.store.sync()["updated_files"], [])
        self.store.submit(["C01"], state="Unknown", note="口径需要继续查")
        self.store.submit(["C02"], state="撤回", note="撤回之前的确认")
        self.assertEqual(self.store.facts(), [])
        self.assertEqual(len(self.state()["events"]), 4)
        self.assertEqual(self.state()["records"]["C02"]["state"], "Withdrawn")
        self.assertEqual(self.store.submit(["C02"], state="Withdrawn", note="撤回之前的确认")["changed"], 0)
        self.assertEqual(self.view()["counts"]["Withdrawn"], 1)
        self.assertIn("撤回／Unknown", self.read("outputs/first-analysis.md"))

    def test_invalid_ids_reject_whole_transaction(self):
        with self.assertRaises(ValueError):
            self.store.submit(["C01", "C99"])
        self.assertFalse((self.fixture / "evidence/review-state.json").exists())
        self.assertEqual(self.store.facts(), [])
        for value in ([], "C01", [7]):
            with self.assertRaises(ValueError):
                self.store.submit(value)

    def test_source_or_candidate_change_invalidates_fact_and_reconfirm_is_required(self):
        self.store.submit(["C01", "C02"])
        candidate_path = self.fixture / "work/evidence-candidates.md"
        candidate_path.write_text(self.read("work/evidence-candidates.md").replace("170,899,152,276.34", "170,899,152,276.35"), encoding="utf-8")
        self.assertEqual({r["id"] for r in self.store.facts()}, {"C02"})
        c01 = next(r for r in self.store.list_candidates() if r["id"] == "C01")
        self.assertEqual(c01["state"], "Unknown")
        self.assertTrue(c01["stale_reason"])
        self.store.sync()
        self.assertEqual(len(self.view()["facts"]), 1)
        self.assertEqual(len(self.state()["events"]), 2)
        self.store.submit(["C01"])
        self.assertEqual(len(self.store.facts()), 2)
        self.assertEqual(len(self.state()["events"]), 3)
        (self.pdf_dir / "600519_2024_fixture.pdf").write_bytes(b"%PDF changed source bytes")
        self.assertEqual(self.store.facts(), [])
        self.store.sync()
        self.assertEqual(self.view()["facts"], [])
        self.assertIn("来源变化／Unknown", self.read("outputs/first-analysis.md"))

    def test_handwritten_text_contract_name_and_unchecked_acceptance_survive(self):
        handwritten = "\n人工notes：这里有真实修正，勿删除。\n"
        for relative in ("tasks/01-first-task.md", "evidence/evidence-log.md", "work/pending-checks.md", "outputs/first-analysis.md"):
            path = self.fixture / relative
            path.write_text(self.read(relative) + handwritten, encoding="utf-8")
        contract_before = self.read("tasks/01-first-task.md")
        count_unchecked = contract_before.count("- [ ]")
        self.store.submit(["C01", "C02"])
        self.store.sync()
        for relative in ("tasks/01-first-task.md", "evidence/evidence-log.md", "work/pending-checks.md", "outputs/first-analysis.md"):
            self.assertIn(handwritten.strip(), self.read(relative))
            self.assertEqual(self.read(relative).count("review-store:progress:start"), 1)
        contract = self.read("tasks/01-first-task.md")
        self.assertIn("执行人：__Leo__", contract)
        self.assertIn("签署日期：__________", contract)
        self.assertEqual(contract.count("- [ ]"), count_unchecked)
        self.assertIn("合同尚未正式关闭", contract)

    def test_blank_name_allowed_if_contract_name_pending(self):
        path = self.fixture / "tasks/01-first-task.md"
        path.write_text(self.read("tasks/01-first-task.md").replace("__Leo__", "__________"), encoding="utf-8")
        result = self.store.submit(["C01"])
        self.assertEqual(result["results"][0]["actor"], "")
        self.assertIn("姓名待补", self.read("evidence/evidence-log.md"))

    def test_explicit_blank_reviewer_is_kept_pending_even_when_contract_says_leo(self):
        self.assertEqual(self.store.get_profile()["reviewer"], "Leo")
        self.store.submit(["C01"], actor="另一测试昵称")
        self.assertEqual(self.store.get_profile()["reviewer"], "另一测试昵称")
        result = self.store.submit(["C02"], actor="")
        self.assertEqual(result["results"][0]["actor"], "")
        self.assertEqual(self.store.get_profile()["reviewer"], "")
        self.assertIn("执行人：__Leo__", self.read("tasks/01-first-task.md"))
        self.assertIn("姓名待补", self.read("evidence/evidence-log.md"))

    def test_comparability_is_independent_preserves_config_and_blocks_changed_inputs(self):
        flags = {key: True for key in FLAGS}
        config_before = json.loads(self.read("config/human-review.json"))
        config_before["custom"] = {"keep": "手写说明"}
        config_before["human_confirmation"]["custom_flag"] = "不改"
        config_path = self.fixture / "config/human-review.json"
        config_path.write_text(json.dumps(config_before, ensure_ascii=False), encoding="utf-8")
        self.store.submit(["C01", "C02"])
        with self.assertRaises(ValueError):
            self.store.validate_comparability()
        result = self.store.save_comparability(flags, note="单独逐项确认")
        self.assertTrue(result["valid"])
        self.assertIs(self.store.validate_comparability(), True)
        after = json.loads(self.read("config/human-review.json"))
        for key in set(config_before) - {"human_confirmation"}:
            self.assertEqual(after[key], config_before[key])
        self.assertEqual(after["human_confirmation"]["custom_flag"], "不改")
        self.assertEqual(self.store.save_comparability(flags, note="单独逐项确认")["changed"], 0)
        raw = self.fixture / "work/structured-data.json"
        raw.write_text(raw.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "已变化"):
            self.store.validate_comparability()
        self.store.sync()
        effective_flags = json.loads(self.read("config/human-review.json"))["human_confirmation"]
        self.assertTrue(all(effective_flags[key] is False for key in FLAGS))
        self.store.save_comparability(flags)
        self.assertTrue(self.store.validate_comparability())
        self.store.submit(["C02"], state="撤回")
        with self.assertRaisesRegex(ValueError, "尚未有效"):
            self.store.validate_comparability()

    def test_seven_flags_alone_cannot_promote_or_enable_calculation(self):
        snapshot = self.store.comparison_snapshot()
        self.assertEqual(len(snapshot["rows"]), 2)
        self.assertTrue(all(row["fact_state"] == "Unknown" for row in snapshot["rows"]))
        with self.assertRaisesRegex(ValueError, "尚未有效"):
            self.store.save_comparability({key: True for key in FLAGS}, expected_binding=snapshot["binding"])
        self.assertEqual(self.store.facts(), [])
        with self.assertRaises(ValueError):
            self.store.validate_comparability()
        invalid = {key: "true" for key in FLAGS}
        with self.assertRaises(ValueError):
            self.store.save_comparability(invalid)

    def test_display_binding_rejects_entire_batch_when_candidate_or_pdf_changes(self):
        bindings = {row["id"]: row["binding"] for row in self.store.list_candidates("first")}
        candidate_path = self.fixture / "work/evidence-candidates.md"
        candidate_path.write_text(self.read("work/evidence-candidates.md").replace("170,899,152,276.34", "170,899,152,276.35"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "自展示后已变化"):
            self.store.submit(["C01", "C02"], expected_bindings=bindings)
        self.assertFalse(self.store.state_path.exists())
        self.assertEqual(self.store.facts(), [])
        bindings = {row["id"]: row["binding"] for row in self.store.list_candidates("first")}
        (self.pdf_dir / "600519_2024_fixture.pdf").write_bytes(b"%PDF another version")
        with self.assertRaisesRegex(ValueError, "自展示后已变化"):
            self.store.submit(["C01", "C02"], expected_bindings=bindings)
        self.assertFalse(self.store.state_path.exists())
        bindings = {row["id"]: row["binding"] for row in self.store.list_candidates("first")}
        result = self.store.submit(["C01", "C02"], expected_bindings=bindings)
        self.assertEqual(result["changed"], 2)

    def test_comparison_display_binding_rejects_stale_save_and_stale_calculation(self):
        self.store.submit(["C01", "C02"])
        snapshot = self.store.comparison_snapshot()
        flags = {key: True for key in FLAGS}
        self.assertEqual(snapshot["rows"][0]["current"], "170899152276.34")
        self.assertEqual(snapshot["rows"][0]["previous"], "147693604994.14")
        self.assertEqual(snapshot["rows"][0]["raw_current"], "170,899,152,276.34")
        self.assertTrue(snapshot["rows"][0]["location"])
        raw = self.fixture / "work/structured-data.json"
        raw.write_text(raw.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        before = self.read("evidence/review-state.json")
        with self.assertRaisesRegex(ValueError, "自展示后已变化"):
            self.store.save_comparability(flags, expected_binding=snapshot["binding"])
        self.assertEqual(before, self.read("evidence/review-state.json"))
        new_snapshot = self.store.comparison_snapshot()
        self.store.save_comparability(flags, expected_binding=new_snapshot["binding"])
        self.assertTrue(self.store.validate_comparability(expected_binding=new_snapshot["binding"]))
        with self.assertRaisesRegex(ValueError, "不一致"):
            self.store.validate_comparability(expected_binding=snapshot["binding"])

    def test_normalized_and_raw_conflicts_block_display_save_and_validation(self):
        self.store.submit(["C01", "C02"])
        self.store.save_comparability({key: True for key in FLAGS})
        raw = self.fixture / "work/structured-data.json"
        original = json.loads(raw.read_text(encoding="utf-8"))
        for field in ("current", "previous"):
            data = json.loads(json.dumps(original))
            row = next(r for r in data["summary"] if r["year"] == 2024 and r["metric"] == "营业收入")
            row[field] = "1.00"
            raw.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            before = self.read("evidence/review-state.json")
            with self.assertRaisesRegex(ValueError, "不一致"):
                self.store.comparison_snapshot()
            with self.assertRaisesRegex(ValueError, "不一致"):
                self.store.save_comparability({key: True for key in FLAGS})
            with self.assertRaisesRegex(ValueError, "不一致"):
                self.store.validate_comparability()
            self.assertEqual(before, self.read("evidence/review-state.json"))

    def test_matching_raw_and_normalized_but_conflicting_fact_blocks_confirmation(self):
        self.store.submit(["C01", "C02"])
        self.store.save_comparability({key: True for key in FLAGS})
        raw = self.fixture / "work/structured-data.json"
        data = json.loads(raw.read_text(encoding="utf-8"))
        row = next(r for r in data["summary"] if r["year"] == 2024 and r["metric"] == "营业收入")
        row["current"], row["raw_current"] = "1.00", "1.00"
        raw.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        before = self.read("evidence/review-state.json")
        for action in (self.store.comparison_snapshot, self.store.validate_comparability,
                       lambda: self.store.save_comparability({key: True for key in FLAGS})):
            with self.assertRaisesRegex(ValueError, "有效Fact快照数值不一致"):
                action()
        self.assertEqual(before, self.read("evidence/review-state.json"))

    def test_comparison_snapshot_rejects_change_during_read(self):
        original = self.store._comparison_rows
        def changed_during_read(ledger, candidates, require_facts=False):
            rows = original(ledger, candidates, require_facts)
            raw = self.fixture / "work/structured-data.json"
            raw.write_text(raw.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            return rows
        with patch.object(self.store, "_comparison_rows", side_effect=changed_during_read):
            with self.assertRaisesRegex(ValueError, "读取期间已变化"):
                self.store.comparison_snapshot()

    def test_comparison_record_cannot_claim_another_pdf_than_reviewed_fact(self):
        self.store.submit(["C01", "C02"])
        raw = self.fixture / "work/structured-data.json"
        data = json.loads(raw.read_text(encoding="utf-8"))
        row = next(r for r in data["summary"] if r["year"] == 2024 and r["metric"] == "营业收入")
        row["pdf"] = "sources/annual_reports/pdf/600519_2023_fixture.pdf"
        raw.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "来源不一致"):
            self.store.comparison_snapshot()
        with self.assertRaisesRegex(ValueError, "来源不一致"):
            self.store.save_comparability({key: True for key in FLAGS})

    def test_failed_state_write_is_atomic_and_failed_view_can_recover(self):
        original = self.store._atomic_text
        def failed_state(path, content):
            if path == self.store.state_path:
                raise OSError("simulated state disk failure")
            return original(path, content)
        with patch.object(self.store, "_atomic_text", side_effect=failed_state):
            with self.assertRaises(OSError):
                self.store.submit(["C01", "C02"])
        self.assertFalse(self.store.state_path.exists())
        self.assertEqual(self.store.facts(), [])
        def failed_view(path, content):
            if path.name == "confirmed-facts.json":
                raise OSError("simulated view disk failure")
            return original(path, content)
        with patch.object(self.store, "_atomic_text", side_effect=failed_view):
            result = self.store.submit(["C01", "C02"])
        self.assertTrue(result["committed"])
        self.assertEqual(len(self.state()["events"]), 2)
        self.assertEqual(len(self.store.facts()), 2)
        self.assertTrue(result["sync_errors"])
        self.assertEqual(self.store.sync()["errors"], [])
        self.assertEqual(len(self.view()["facts"]), 2)

    def test_concurrent_submissions_are_serialized_and_no_events_are_lost(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda identifier: ReviewStore(self.fixture).submit([identifier]), ("C01", "C02")))
        self.assertTrue(all(r["changed"] == 1 for r in results))
        self.assertEqual(len(self.state()["events"]), 2)
        self.assertEqual(len(self.view()["facts"]), 2)

    def test_missing_pdf_and_corrupt_authority_fail_closed(self):
        (self.pdf_dir / "600519_2024_fixture.pdf").unlink()
        with self.assertRaisesRegex(ValueError, "来源PDF"):
            self.store.submit(["C01", "C02"])
        self.assertFalse(self.store.state_path.exists())
        damaged = '{"schema_version": 1, "records": []}'
        self.store.state_path.parent.mkdir(exist_ok=True)
        self.store.state_path.write_text(damaged, encoding="utf-8")
        with self.assertRaises(ValueError):
            self.store.submit(["C01"])
        self.assertEqual(self.store.state_path.read_text(encoding="utf-8"), damaged)


    def test_scope_candidate_view_sync_preserves_authority_sources_and_handwriting(self):
        view_path = self.fixture / "work/metric-scope-candidates.md"
        handwritten = "\n人工口径说明：已阅读合并与母公司边界，保留本段。\n"
        view_path.write_text(self.read("work/metric-scope-candidates.md") + handwritten, encoding="utf-8")
        untouched = [self.fixture / "work/evidence-candidates.md", self.fixture / "work/structured-data.json", *self.pdf_dir.glob("*.pdf")]
        hashes_before = {str(path): sha256(path.read_bytes()).hexdigest() for path in untouched}
        binding_before = {row["id"]: (row["candidate_fingerprint"], row["pdf_sha256"]) for row in self.store.list_candidates("scope")}
        ids = [row["id"] for row in self.store.list_candidates("scope")]
        result = self.store.submit(ids, actor="核验者甲", note="实际人工核验")
        self.assertEqual(result["changed"], 12)
        self.assertEqual(result["sync_errors"], [])
        state_before_sync = (self.fixture / "evidence/review-state.json").read_bytes()
        self.assertEqual(len(self.state()["events"]), 12)
        view = self.read("work/metric-scope-candidates.md")
        self.assertIn(handwritten.strip(), view)
        self.assertNotIn("人工核验为待核验，候选披露仍为Unknown", view)
        for identifier in ids:
            row = next(line for line in view.splitlines() if line.startswith("| " + identifier + " |"))
            self.assertIn("本人核验／Fact", row)
        self.assertEqual(view.count("review-store:progress:start"), 1)
        self.assertEqual(self.store.sync()["updated_files"], [])
        self.assertEqual(state_before_sync, (self.fixture / "evidence/review-state.json").read_bytes())
        self.assertEqual(hashes_before, {str(path): sha256(path.read_bytes()).hexdigest() for path in untouched})
        self.assertEqual(binding_before, {row["id"]: (row["candidate_fingerprint"], row["pdf_sha256"]) for row in self.store.list_candidates("scope")})

    def test_scope_candidate_sync_reflects_stale_fact_without_creating_events(self):
        self.store.submit(["C01", "C02"])
        (self.pdf_dir / "600519_2024_fixture.pdf").write_bytes(b"%PDF a changed annual report")
        authority_before = (self.fixture / "evidence/review-state.json").read_bytes()
        sources_before = (self.fixture / "work/evidence-candidates.md").read_bytes()
        result = self.store.sync()
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["event_count"], 2)
        self.assertEqual(authority_before, (self.fixture / "evidence/review-state.json").read_bytes())
        self.assertEqual(sources_before, (self.fixture / "work/evidence-candidates.md").read_bytes())
        view = self.read("work/metric-scope-candidates.md")
        for identifier in ("C01", "C02"):
            row = next(line for line in view.splitlines() if line.startswith("| " + identifier + " |"))
            self.assertIn("来源变化／Unknown", row)
        self.assertEqual(self.store.sync()["updated_files"], [])


if __name__ == "__main__":
    unittest.main()
