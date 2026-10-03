"""Human-confirmed changes, kept separate from original disclosure Facts."""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from pathlib import Path
from zoneinfo import ZoneInfo

FORMULA = "(current-previous)/previous*100"
ROUNDING = "ROUND_HALF_UP 2 decimal places"
FIELDS = ("metric", "current", "previous", "source_binding", "formula", "percent", "rounding")
PAIRS = (("CH01", "C01"), ("CH02", "C02"))
SUPPORT = "仅支持对应口径下2024年较2023年的变化方向与幅度"
UNSUPPORTED = "不支持原因、机制、持续性、未来价值、股价或投资建议"


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def number(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError("变化证据包含无效数字") from error
    if not result.is_finite():
        raise ValueError("变化证据包含非有限数字")
    return result


class ChangeReviewStore:
    def __init__(self, root, review=None):
        self.workspace = Path(root).resolve()
        if review is None:
            from review_store import ReviewStore
            review = ReviewStore(self.workspace)
        self.review = review
        self.state_path = self.workspace / "evidence/change-review-state.json"
        self.calc_path = self.workspace / "work/change-recalculation.json"

    def _read(self):
        if not self.state_path.exists():
            return {"schema": 1, "records": {}, "events": []}
        ledger = json.loads(self.state_path.read_text(encoding="utf-8-sig"))
        if ledger.get("schema") != 1 or not isinstance(ledger.get("records"), dict) \
                or not isinstance(ledger.get("events"), list):
            raise ValueError("变化核验账本结构无效")
        return ledger

    def _validated(self, payload=None):
        snapshot = self.review.comparison_snapshot()
        if not self.review.validate_comparability(snapshot["binding"]):
            raise ValueError("两期可比性尚未有效确认")
        facts = {r["id"]: r for r in self.review.facts()}
        raw = {}
        for _, identifier in PAIRS:
            fact = facts.get(identifier)
            if not fact or fact.get("state") != "Fact":
                raise ValueError(identifier + "原始Fact已失效或撤回")
            raw[identifier] = {k: fact.get(k) for k in
                              ("id", "binding", "candidate_fingerprint", "confirmed_at",
                               "pdf_path", "pdf_sha256", "value")}
        if payload is None:
            payload = json.loads(self.calc_path.read_text(encoding="utf-8-sig"))
        results = payload.get("results")
        if not isinstance(results, list) or len(results) != 2:
            raise ValueError("变化计算必须包含两项唯一结果")
        rows = {r["id"]: r for r in snapshot["rows"]}
        if len(rows) != 2 or set(rows) != {"C01", "C02"}:
            raise ValueError("比较数来源缺少唯一C01/C02记录")
        normalized, sources = {}, {}
        for change_id, raw_id in PAIRS:
            row = rows[raw_id]
            if any(row.get(k) != facts[raw_id].get(k) for k in ("pdf_path", "pdf_sha256")) \
                    or row.get("fact_state") != "Fact":
                raise ValueError(raw_id + "比较来源与有效原始Fact不一致")
            matches = [r for r in results if r.get("metric") == row["metric"]]
            if len(matches) != 1:
                raise ValueError(raw_id + "计算结果缺失或重复")
            result = matches[0]
            current, previous = number(row["current"]), number(row["previous"])
            if previous == 0:
                raise ValueError(raw_id + "比较基数为零")
            if number(result.get("current")) != current or number(result.get("previous")) != previous:
                raise ValueError(raw_id + "计算输入与来源快照不一致")
            if number(str(facts[raw_id]["value"]).replace(",", "")) != current:
                raise ValueError(raw_id + "本期输入与有效原始Fact不一致")
            if result.get("source_binding") != snapshot["binding"]:
                raise ValueError(raw_id + "计算来源绑定已变化")
            if result.get("formula") != FORMULA or result.get("rounding") != ROUNDING:
                raise ValueError(raw_id + "公式或舍入规则不一致")
            with localcontext() as ctx:
                ctx.prec = 50
                percent = format(((current - previous) / previous * 100)
                                 .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f")
            if result.get("percent") != percent:
                raise ValueError(raw_id + "变化率与Decimal复算不一致")
            normalized[change_id] = {k: result.get(k) for k in FIELDS}
            normalized[change_id].update(current=format(current, "f"), previous=format(previous, "f"))
            sources[change_id] = copy.deepcopy(row)
        if digest(snapshot) != digest(self.review.comparison_snapshot()):
            raise ValueError("核验期间来源发生变化，请重新核验")
        if raw != {i: {k: f.get(k) for k in raw[i]} for f in self.review.facts()
                   if (i := f["id"]) in raw}:
            raise ValueError("核验期间原始Fact发生变化")
        return snapshot, raw, normalized, sources

    def _effective(self, ledger, payload=None):
        try:
            snapshot, raw, normalized, sources = self._validated(payload)
            error = ""
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as failure:
            error = str(failure)
        records = []
        for identifier, record in ledger["records"].items():
            result = copy.deepcopy(record)
            reason = error
            if not reason:
                expected = normalized.get(identifier)
                if not any(digest(record) == digest(previous) for event in ledger["events"]
                           for previous in event.get("records", []) if previous.get("id") == identifier):
                    reason = "记录缺少匹配的本人聊天确认事件"
                elif expected is None or record.get("calc_digest") != digest(expected) \
                        or any(record.get(k) != expected[k] for k in FIELDS):
                    reason = "计算输入、结果、公式或舍入规则已变化"
                elif record.get("raw_fact_bindings") != raw:
                    reason = "原始Fact确认绑定已变化"
                elif record.get("source_snapshot") != {"binding": snapshot["binding"],
                        "source_binding": snapshot["source_binding"], "row": sources[identifier]}:
                    reason = "来源PDF、输入或定位绑定已变化"
            result.update(state="Unknown" if reason else "Fact", stale_reason=reason)
            records.append(result)
        return records

    def list_records(self):
        """Never promote from cached states; retain confirmed history when stale."""
        return self._effective(self._read())

    def facts(self):
        return [r for r in self.list_records() if r["state"] == "Fact"]

    def export(self):
        ledger = self._read()
        records = self._effective(ledger)
        return {"authority": "evidence/change-review-state.json",
                "counts": {"Fact": sum(r["state"] == "Fact" for r in records),
                           "Unknown": sum(r["state"] == "Unknown" for r in records)},
                "records": records, "events": copy.deepcopy(ledger["events"])}

    def confirm(self, statement, context, actor="", client_date="2026-10-03"):
        """Register an explicit chat confirmation; never create PDF-window events."""
        if not isinstance(statement, str) or not statement.strip() \
                or not isinstance(context, str) or not context.strip():
            raise ValueError("必须保留本人原话及明确的确认上下文")
        with self.review._locked():
            snapshot, raw, normalized, sources = self._validated()
            ledger = self._read()
            key = digest({"statement": statement, "context": context, "calc": normalized,
                          "source": snapshot, "raw": raw})
            current = self._effective(ledger)
            if {r["id"] for r in current if r["state"] == "Fact"} == {"CH01", "CH02"} \
                    and all(r.get("confirmation_key") == key for r in current):
                return current
            now = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")
            records = {}
            for identifier, _ in PAIRS:
                source = sources[identifier]
                record = dict(normalized[identifier], id=identifier, state="Fact",
                    submitted_state="Fact", stale_reason="", calc_digest=digest(normalized[identifier]),
                    source_snapshot={"binding": snapshot["binding"],
                                     "source_binding": snapshot["source_binding"], "row": source},
                    raw_fact_bindings=copy.deepcopy(raw), confirmed_at=now, actor=actor,
                    client_date=client_date, statement_original=statement,
                    confirmation_context=context, confirmation_key=key,
                    support_boundary=SUPPORT, unsupported_boundary=UNSUPPORTED)
                record.update({k: source.get(k) for k in
                    ("pdf_path", "pdf_sha256", "location", "unit", "scope", "year", "previous_year")})
                records[identifier] = record
            ledger["records"].update(records)
            ledger["updated_at"] = now
            ledger["events"].append({"type": "chat-confirmation", "sequence": len(ledger["events"]) + 1,
                "confirmed_at": now,
                "actor": actor, "client_date": client_date, "confirmation_key": key,
                "statement_original": statement, "confirmation_context": context,
                "records": copy.deepcopy(list(records.values()))})
            self.review._atomic_text(self.state_path, json.dumps(ledger, ensure_ascii=False,
                                                                indent=2) + "\n")
            return list(records.values())

    def annotate_calculation(self, payload):
        """Decorate a recomputation only when the existing confirmation still binds."""
        result = copy.deepcopy(payload)
        effective = {r["metric"]: r for r in self._effective(self._read(), result)
                     if r["state"] == "Fact"}
        for row in result.get("results", []):
            confirmation = effective.get(row.get("metric"))
            row["state"] = "Fact" if confirmation else "Unknown"
            row["note"] = ("本人聊天确认；仅支持变化方向与幅度" if confirmation else
                           "未有当前有效的本人变化结果核验，保留Unknown")
            if confirmation:
                row.update(change_evidence_id=confirmation["id"],
                           confirmed_at=confirmation["confirmed_at"])
            else:
                row.pop("change_evidence_id", None)
                row.pop("confirmed_at", None)
        if result.get("results"):
            result["status"] = ("human-confirmed" if len(effective) == 2 else
                                "calculated-awaiting-human-verification")
        return result
