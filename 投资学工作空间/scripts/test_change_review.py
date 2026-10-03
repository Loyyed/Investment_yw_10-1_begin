"""Boundary tests use an explicit in-memory review backend, never the real project."""
import copy
import json
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from change_review import ChangeReviewStore, FORMULA, ROUNDING

CONTEXT = ("上一条答复要求核对2024/2023本期和比较期原文、"
           "(current-previous)/previous*100公式及ROUND_HALF_UP保留两位；"
           "营业收入15.71%、归母净利润15.38%，用户答复确认本轮两项结果。")


class FixtureReview:
    def __init__(self):
        data = (("C01", "营业收入", "170899152276.34", "147693604994.14", "15.71"),
                ("C02", "归属于上市公司股东的净利润", "86228146421.62", "74734071550.75", "15.38"))
        self.snapshot = {"binding": "input-v1", "source_binding": {"pdf": "sha-v1"},
                         "rows": [], "flags": {"seven-reviewed": True}}
        self.records = []
        self.payload = {"status": "calculated-awaiting-human-verification", "results": []}
        self.comparable = True
        for identifier, metric, current, previous, percent in data:
            self.snapshot["rows"].append(dict(id=identifier, metric=metric, current=current,
                previous=previous, year=2024, previous_year=2023, pdf_path="annual.pdf",
                pdf_sha256="sha-v1", pdf_pages=[63, 64, 5], fact_state="Fact",
                location="PDF63、64页；5页交叉检查", unit="人民币元", scope="合并"))
            self.records.append(dict(id=identifier, state="Fact", value=current,
                binding=identifier+"-binding", candidate_fingerprint=identifier+"-fingerprint",
                confirmed_at="2026-10-02T10:00:00+08:00", pdf_path="annual.pdf", pdf_sha256="sha-v1"))
            self.payload["results"].append(dict(metric=metric, current=current,
                previous=previous, percent=percent, formula=FORMULA, rounding=ROUNDING,
                source_binding="input-v1", state="Unknown", note="尚待确认"))

    def comparison_snapshot(self):
        return copy.deepcopy(self.snapshot)

    def validate_comparability(self, expected_binding=None):
        return self.comparable and expected_binding == self.snapshot["binding"]

    def facts(self):
        return copy.deepcopy([r for r in self.records if r["state"] == "Fact"])

    @contextmanager
    def _locked(self):
        yield

    def _atomic_text(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


class ChangeReviewBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.review = FixtureReview()
        self.store = ChangeReviewStore(self.root, review=self.review)
        self.store.calc_path.parent.mkdir()
        (self.root/"evidence").mkdir()
        self.raw = self.root/"evidence/review-state.json"
        self.raw.write_bytes(b'{"events":[{"original":true}],"records":{"C01":"Fact"}}')
        self.write_calc()

    def write_calc(self):
        self.store.calc_path.write_text(json.dumps(self.review.payload), encoding="utf-8")

    def confirm(self):
        return self.store.confirm("核对完毕", CONTEXT)

    def test_confirm_keeps_original_ledger_and_blank_actor(self):
        original = self.raw.read_bytes()
        records = self.confirm()
        self.assertEqual({"CH01", "CH02"}, {r["id"] for r in records})
        self.assertEqual(["15.71", "15.38"], [r["percent"] for r in records])
        self.assertTrue(all(r["actor"] == "" and r["statement_original"] == "核对完毕" for r in records))
        self.assertTrue(all(r["confirmed_at"].endswith("+08:00") for r in records))
        self.assertEqual("2026-10-03", records[0]["client_date"])
        self.assertEqual(original, self.raw.read_bytes())
        self.assertEqual(2, len(self.store.facts()))
        self.assertEqual(1, len(self.store.export()["events"]))
        self.assertEqual("chat-confirmation", self.store.export()["events"][0]["type"])

    def test_retry_does_not_append_event_or_change_timestamp(self):
        first = self.confirm()
        second = self.confirm()
        self.assertEqual(first, second)
        self.assertEqual(1, len(self.store.export()["events"]))

    def test_automatic_recompute_cannot_create_confirmation(self):
        result = self.store.annotate_calculation(self.review.payload)
        self.assertTrue(all(r["state"] == "Unknown" for r in result["results"]))
        self.assertFalse(self.store.state_path.exists())

    def test_same_recompute_ignores_state_note_and_preserves_confirmation(self):
        self.confirm()
        self.review.payload["status"] = "recomputed"
        for result in self.review.payload["results"]:
            result.update(state="Unknown", note="重新计算，无新的人工核验")
        self.write_calc()
        annotated = self.store.annotate_calculation(self.review.payload)
        self.assertEqual("human-confirmed", annotated["status"])
        self.assertTrue(all(r["state"] == "Fact" for r in annotated["results"]))
        self.assertEqual(2, len(self.store.facts()))
        self.assertEqual(1, len(self.store.export()["events"]))

    def test_invalid_inputs_results_formula_rounding_and_source_cannot_be_fact(self):
        self.confirm()
        original = copy.deepcopy(self.review.payload)
        for field, bad in (("current", "170899152276.35"), ("previous", "1"),
                           ("percent", "15.72"), ("formula", "current/previous*100"),
                           ("rounding", "truncate"), ("source_binding", "unbound")):
            with self.subTest(field=field):
                self.review.payload = copy.deepcopy(original)
                self.review.payload["results"][0][field] = bad
                self.write_calc()
                self.assertEqual([], self.store.facts())
                self.assertTrue(all(r["state"] == "Unknown" for r in self.store.list_records()))
                with self.assertRaises(ValueError):
                    self.confirm()
        self.review.payload = original
        self.write_calc()
        self.assertEqual(2, len(self.store.facts()))

    def test_withdrawn_original_fact_invalidates_both_and_preserves_history(self):
        self.confirm()
        self.review.records[0]["state"] = "Withdrawn"
        self.assertEqual([], self.store.facts())
        self.assertEqual(1, len(self.store.export()["events"]))
        self.assertTrue(all("原始Fact" in r["stale_reason"] for r in self.store.list_records()))
        with self.assertRaises(ValueError):
            self.confirm()

    def test_changed_pdf_requires_new_explicit_confirmation(self):
        self.confirm()
        self.review.snapshot["binding"] = "input-v2"
        self.review.snapshot["source_binding"] = {"pdf": "sha-v2"}
        for row in self.review.snapshot["rows"]:
            row["pdf_sha256"] = "sha-v2"
        for row in self.review.records:
            row["pdf_sha256"] = "sha-v2"
        for row in self.review.payload["results"]:
            row["source_binding"] = "input-v2"
        self.write_calc()
        self.assertEqual([], self.store.facts())
        self.assertTrue(all(r["state"] == "Unknown" for r in
                            self.store.annotate_calculation(self.review.payload)["results"]))
        self.confirm()
        self.assertEqual(2, len(self.store.facts()))
        self.assertEqual(2, len(self.store.export()["events"]))

    def test_comparability_withdrawal_is_fail_closed(self):
        self.confirm()
        self.review.comparable = False
        self.assertEqual([], self.store.facts())
        with self.assertRaises(ValueError):
            self.confirm()

    def test_zero_base_blocks_confirmation_and_retains_previous_event(self):
        self.confirm()
        self.review.snapshot["rows"][0]["previous"] = "0"
        self.review.payload["results"][0]["previous"] = "0"
        self.write_calc()
        self.assertEqual([], self.store.facts())
        with self.assertRaisesRegex(ValueError, "基数为零"):
            self.confirm()
        self.assertEqual(1, len(self.store.export()["events"]))

    def test_empty_or_duplicate_calculation_cannot_be_confirmed(self):
        self.confirm()
        self.review.payload["results"] = []
        self.write_calc()
        self.assertEqual([], self.store.facts())
        with self.assertRaises(ValueError):
            self.confirm()

    def test_ledger_record_without_matching_chat_event_is_unknown(self):
        self.confirm()
        ledger = self.store._read()
        ledger["events"] = []
        self.review._atomic_text(self.store.state_path, json.dumps(ledger))
        self.assertEqual([], self.store.facts())


if __name__ == "__main__":
    unittest.main(verbosity=2)
