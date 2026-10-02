"""Durable, local human-review ledger; standard library only.

Only an explicit ``submit`` creates a review event. Candidate source files and
PDFs are never edited. All views can be rebuilt by ``sync`` after an interrupted
write; review-state.json is the sole authority. Monetary values remain strings.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import html
import json
import os
from pathlib import Path
import re
import tempfile
import threading
import time
from typing import Any, Literal, TypedDict


FLAGS = ("report_version", "periods", "unit_currency", "reporting_entity",
         "consolidation_scope", "metric_definition", "no_restatement")
FLAG_LABELS = ("报告版本", "报告期间", "单位与币种", "报表主体", "合并范围", "指标定义", "无重述")
SHANGHAI = timezone(timedelta(hours=8), "Asia/Shanghai")
_THREAD_LOCKS: dict[str, threading.Lock] = {}
_THREAD_LOCKS_GUARD = threading.Lock()
_ID = re.compile(r"^(?:C\d{2}|[RN]\d{4}-\d{2})$")
_OLD_INTRO = "> Agent定位、PDF原值对照和结构检查已完成；人工核验为待核验，候选披露仍为Unknown。本人核验并签认后才能升级Fact。人名及签署日期按用户要求留空。"
_NEW_INTRO = "> Agent定位、PDF原值对照和结构检查已完成。人工核验状态由统一核验记录更新；未确认条目保留Unknown，合同签署按实际情况另行完成。"


class EvidenceRecord(TypedDict, total=False):
    id: str
    claim: str
    value: str
    year: int
    period: str
    location: str
    scope: str
    pdf_path: str
    state: Literal["Fact", "Unknown", "Withdrawn"]
    actor: str
    confirmed_at: str
    note: str
    source_version: str
    unit: str
    table: str
    support_boundary: str
    unsupported_boundary: str
    candidate_fingerprint: str
    pdf_sha256: str
    stale_reason: str
    submitted_state: str
    numbers: list[str]
    pending_issue: str
    binding: str


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _digest(value: Any) -> str:
    return sha256(_json(value).encode("utf-8")).hexdigest()


def _file_hash(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    return "\n".join("| " + " | ".join(_cell(c) for c in row) + " |"
                     for row in [headers, ["---"] * len(headers), *rows])


class ReviewStore:
    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace).resolve()
        self.state_path = self.workspace / "evidence/review-state.json"
        self.candidates_path = self.workspace / "work/evidence-candidates.md"
        if not self.candidates_path.is_file():
            raise FileNotFoundError(f"候选账本不存在：{self.candidates_path}")

    def _path(self, relative: str) -> Path:
        path = (self.workspace / relative).resolve()
        if not path.is_relative_to(self.workspace):
            raise ValueError("文件路径超出工作空间")
        return path

    @contextmanager
    def _locked(self):
        key = str(self.workspace)
        with _THREAD_LOCKS_GUARD:
            mutex = _THREAD_LOCKS.setdefault(key, threading.Lock())
        with mutex:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path = self.state_path.parent / ".review-state.lock"
            with lock_path.open("a+b") as stream:
                stream.seek(0, os.SEEK_END)
                if stream.tell() == 0:
                    stream.write(b"0")
                    stream.flush()
                deadline = time.monotonic() + 10
                while True:
                    try:
                        stream.seek(0)
                        if os.name == "nt":
                            import msvcrt
                            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                        else:
                            import fcntl
                            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except OSError:
                        if time.monotonic() >= deadline:
                            raise TimeoutError("核验记录正由另一操作保存，请稍后重试")
                        time.sleep(0.05)
                try:
                    yield
                finally:
                    stream.seek(0)
                    if os.name == "nt":
                        import msvcrt
                        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def _read_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {"schema_version": 1, "records": {}, "events": [], "comparability": None}
        state = json.loads(self.state_path.read_text(encoding="utf-8-sig"))
        if (not isinstance(state, dict) or state.get("schema_version") != 1
                or not isinstance(state.get("records"), dict)
                or not isinstance(state.get("events"), list)):
            raise ValueError("核验账本格式损坏；已停止保存，避免覆盖历史")
        return state

    def _atomic_text(self, path: Path, content: str) -> bool:
        if path.exists() and path.read_text(encoding="utf-8-sig") == content:
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, path)
        finally:
            if os.path.exists(name):
                os.unlink(name)
        return True

    def _candidates(self) -> list[EvidenceRecord]:
        rows: list[EvidenceRecord] = []
        ids: set[str] = set()
        pdf_dir = self._path("sources/annual_reports/pdf")
        pdfs = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
        hashes: dict[Path, str] = {}
        for line in self.candidates_path.read_text(encoding="utf-8-sig").splitlines():
            if not line.startswith("|"):
                continue
            cells = [s.strip() for s in re.split(r"(?<!\\)\|", line)[1:-1]]
            if not cells or not _ID.fullmatch(cells[0]):
                continue
            if len(cells) != 12 or cells[0] in ids:
                raise ValueError(f"候选行字段或编号不合法：{cells[0]}")
            ids.add(cells[0])
            match = re.search(r"(?:19|20)\d{2}", cells[3] + cells[4])
            if not match:
                raise ValueError(f"候选缺少来源年度：{cells[0]}")
            year = int(match.group())
            def report_year(path: Path) -> int | None:
                # Publication dates are often in the following year; prefer the
                # explicit stock-code/report-year filename field over any date.
                found = re.match(r"^\d+_((?:19|20)\d{2})_", path.name)
                found = found or re.search(r"((?:19|20)\d{2})年", path.name)
                found = found or re.search(r"(?<!\d)((?:19|20)\d{2})(?!\d)", path.name)
                return int(found.group(1)) if found else None
            matches = [p for p in pdfs if report_year(p) == year]
            pdf = matches[0] if len(matches) == 1 else None
            source_problem = "" if pdf else "来源PDF缺失或存在多个相同年度版本，需重新核验"
            if pdf:
                if not pdf.resolve().is_relative_to(self.workspace):
                    raise ValueError("来源PDF超出工作空间")
                if pdf not in hashes:
                    hashes[pdf] = _file_hash(pdf)
            row: EvidenceRecord = {
                "id": cells[0], "claim": cells[1], "source_version": cells[3],
                "year": year, "period": cells[4], "location": cells[5],
                "value": cells[6], "scope": cells[7], "unit": cells[7].split("；")[0],
                "table": "合并利润表" if cells[0] in {"C01", "C02", "C03", "C04", "C08", "C09", "C10"}
                         else ("母公司利润表" if cells[0] in {"C05", "C11"} else "来源定位见原PDF与口径"),
                "support_boundary": cells[8], "unsupported_boundary": cells[9],
                "pdf_path": pdf.relative_to(self.workspace).as_posix() if pdf else "",
                "pdf_sha256": hashes.get(pdf, ""), "state": "Unknown", "actor": "",
                "confirmed_at": "", "note": cells[11], "pending_issue": cells[11], "stale_reason": source_problem,
                "numbers": re.findall(r"(?<!\d)\d[\d,]*\.\d+", cells[6]),
            }
            # This source ledger is never edited by sync; bind the complete row,
            # including newly added limitations or unresolved source questions.
            row["candidate_fingerprint"] = _digest(cells)
            row["binding"] = _digest({key: row[key] for key in ("candidate_fingerprint", "pdf_sha256", "pdf_path")})
            rows.append(row)
        if not rows:
            raise ValueError("候选账本没有可核验记录")
        return rows

    def _effective(self, state: dict[str, Any], candidates: list[EvidenceRecord]) -> list[EvidenceRecord]:
        result = []
        for candidate in candidates:
            row = dict(candidate)
            record = state["records"].get(row["id"])
            if record:
                row.update({key: record.get(key, "") for key in ("actor", "confirmed_at", "note")})
                row["submitted_state"] = record["state"]
                same = all(record.get(k) == row.get(k) for k in ("candidate_fingerprint", "pdf_sha256", "pdf_path"))
                if not same or not row.get("pdf_sha256"):
                    row["stale_reason"] = "候选内容或原PDF已变化／缺失，原核验失效，需重新核验"
                    row["state"] = "Unknown"
                else:
                    row["state"] = record["state"]
            result.append(row)
        return result

    def list_candidates(self, group: str = "all") -> list[EvidenceRecord]:
        if group not in {"all", "first", "revenue", "scope"}:
            raise ValueError(f"未知分组：{group}")
        rows = self._effective(self._read_state(), self._candidates())
        return [r for r in rows if group == "all"
                or (group == "first" and r["id"] in {"C01", "C02"})
                or (group == "scope" and r["id"].startswith("C"))
                or (group == "revenue" and r["id"].startswith(("R", "N")))]

    def get_profile(self) -> dict[str, str]:
        ledger = self._read_state()
        for event in reversed(ledger["events"]):
            if isinstance(event.get("actor"), str):
                return {"reviewer": event["actor"].strip(), "timezone": "Asia/Shanghai"}
        path = self._path("tasks/01-first-task.md")
        text = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        appendix = text.split("## 本工作空间执行说明", 1)[-1]
        match = re.search(r"执行人[：:]\s*([^；\n]+)", appendix)
        reviewer = match.group(1).strip(" _*").strip() if match else ""
        return {"reviewer": reviewer, "timezone": "Asia/Shanghai"}

    @staticmethod
    def _normal_state(value: str) -> str:
        aliases = {"Fact": "Fact", "Unknown": "Unknown", "Withdrawn": "Withdrawn", "withdrawn": "Withdrawn",
                   "撤回": "Withdrawn", "通过": "Fact", "保留Unknown": "Unknown"}
        if value not in aliases:
            raise ValueError("核验状态只能为Fact、Unknown或Withdrawn（撤回）")
        return aliases[value]

    def submit(self, ids: list[str], state: str = "Fact", actor: str = "", note: str = "",
               expected_bindings: dict[str, str] | None = None) -> dict[str, Any]:
        status = self._normal_state(state)
        if isinstance(ids, str) or not isinstance(ids, (list, tuple)) or not ids:
            raise ValueError("请选择至少一条候选编号")
        if not all(isinstance(i, str) for i in ids):
            raise ValueError("候选编号须为字符串")
        selected = list(dict.fromkeys(ids))
        reviewer = actor.strip()
        with self._locked():
            ledger = self._read_state()
            candidates = self._candidates()
            lookup = {r["id"]: r for r in candidates}
            unknown = set(selected) - lookup.keys()
            if unknown:
                raise ValueError("未知候选编号：" + "、".join(sorted(unknown)))
            if expected_bindings is not None:
                if not isinstance(expected_bindings, dict) or any(
                    not isinstance(expected_bindings.get(i), str) for i in selected
                ):
                    raise ValueError("缺少所选候选的展示来源绑定，请重新加载")
                if any(expected_bindings[i] != lookup[i]["binding"] for i in selected):
                    raise ValueError("候选或原PDF自展示后已变化，请重新加载并重新核验；整批未保存")
            if status == "Fact" and any(not lookup[i]["pdf_sha256"] for i in selected):
                raise ValueError("来源PDF缺失或版本不唯一，不能升级Fact")
            now = datetime.now(SHANGHAI).isoformat(timespec="seconds")
            changed = []
            for identifier in selected:
                row = lookup[identifier]
                record = {k: row[k] for k in ("candidate_fingerprint", "pdf_sha256", "pdf_path")}
                record.update(state=status, actor=reviewer, note=note.strip())
                previous = ledger["records"].get(identifier)
                if previous and all(previous.get(k) == v for k, v in record.items()):
                    continue
                record["confirmed_at"] = now
                record["snapshot"] = row
                ledger["records"][identifier] = record
                ledger["events"].append({"sequence": len(ledger["events"]) + 1, "operation": "review",
                    "id": identifier, "previous_state": previous.get("state", "Unknown") if previous else "Unknown",
                    **record})
                changed.append(identifier)
            if changed:
                ledger["updated_at"] = now
                self._atomic_text(self.state_path, _json(ledger))
            synced = self._sync_locked(ledger, candidates)
            return {"changed": len(changed), "changed_ids": changed, "counts": synced["counts"],
                    "results": [r for r in self._effective(ledger, candidates) if r["id"] in selected],
                    "sync_errors": synced["errors"], "committed": bool(changed)}

    def facts(self) -> list[EvidenceRecord]:
        return [r for r in self.list_candidates() if r["state"] == "Fact"]

    def _comparability_binding(self, candidates: list[EvidenceRecord]) -> dict[str, Any]:
        inputs = {}
        for relative in ("work/structured-data.json", "work/scope-data.json"):
            path = self._path(relative)
            if path.exists():
                inputs[relative] = _file_hash(path)
        return {"candidates": {r["id"]: r["candidate_fingerprint"] for r in candidates},
                "pdfs": {r["pdf_path"]: r["pdf_sha256"] for r in candidates if r["pdf_path"]}, "inputs": inputs}

    @staticmethod
    def _decimal(value: Any, label: str, raw: bool = False) -> Decimal:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label}缺少精确数值字符串：停止确认")
        text = value.replace(",", "") if raw else value
        try:
            result = Decimal(text.strip())
        except InvalidOperation as error:
            raise ValueError(f"{label}不是有效数值：停止确认") from error
        if not result.is_finite():
            raise ValueError(f"{label}不是有限数值：停止确认")
        return result

    def _comparison_rows(self, ledger: dict[str, Any], candidates: list[EvidenceRecord],
                         require_facts: bool = False) -> list[dict[str, Any]]:
        source = json.loads(self._path("work/structured-data.json").read_text(encoding="utf-8-sig"))
        if not isinstance(source, dict) or not isinstance(source.get("summary"), list):
            raise ValueError("结构化比较数缺少summary：停止确认")
        effective = {r["id"]: r for r in self._effective(ledger, candidates)}
        result = []
        for identifier, metric in (("C01", "营业收入"), ("C02", "归属于上市公司股东的净利润")):
            matches = [r for r in source["summary"] if isinstance(r, dict)
                       and r.get("year") == 2024 and r.get("metric") == metric]
            if len(matches) != 1:
                raise ValueError(f"2024年{metric}比较记录缺失或重复：停止确认")
            source_row = matches[0]
            current = self._decimal(source_row.get("current"), f"{metric} normalized current")
            previous = self._decimal(source_row.get("previous"), f"{metric} normalized previous")
            raw_current = self._decimal(source_row.get("raw_current"), f"{metric} raw_current", True)
            raw_previous = self._decimal(source_row.get("raw_previous"), f"{metric} raw_previous", True)
            if current != raw_current or previous != raw_previous:
                raise ValueError(f"{metric}原文raw与实际计算normalized数值不一致：停止确认")
            fact = effective.get(identifier)
            if not fact:
                raise ValueError(f"缺少{identifier}候选：停止确认")
            if source_row.get("pdf") != fact["pdf_path"]:
                raise ValueError(f"{metric}比较记录来源PDF与{identifier}候选来源不一致：停止确认")
            if fact["state"] == "Fact":
                snapshot = ledger["records"][identifier].get("snapshot", {})
                fact_current = self._decimal(snapshot.get("value"), f"{identifier}有效Fact快照", True)
                if fact_current != current:
                    raise ValueError(f"{metric}normalized current与{identifier}有效Fact快照数值不一致：停止确认")
            elif require_facts:
                raise ValueError("C01、C02尚未有效确认为Fact：停止计算，保留Unknown")
            pages = source_row.get("pdf_pages", [])
            if not isinstance(pages, list) or not pages or any(type(page) is not int or page < 1 for page in pages):
                raise ValueError(f"{metric}比较记录缺少有效PDF定位：停止确认")
            if require_facts and previous == 0:
                raise ValueError(f"{metric}比较基数为零：停止计算，保留Unknown")
            result.append({"id": identifier, "metric": metric, "year": 2024, "previous_year": 2023,
                "current": format(current, "f"), "previous": format(previous, "f"),
                "raw_current": source_row["raw_current"], "raw_previous": source_row["raw_previous"],
                "pdf_path": fact["pdf_path"], "pdf_sha256": fact["pdf_sha256"], "pdf_pages": list(pages),
                "location": "PDF／报告" + ",".join(str(page) for page in pages) + "页（2024报告本期与比较列）",
                "fact_location": fact["location"], "fact_state": fact["state"],
                "unit": source_row.get("unit", ""), "scope": source_row.get("scope", ""),
                "table": source_row.get("table", "年报主要会计数据及本期／比较期披露")})
        return result

    def _comparison_snapshot(self, ledger: dict[str, Any] | None = None,
                             require_facts: bool = False) -> dict[str, Any]:
        before_ledger = self._read_state() if ledger is None else ledger
        before_candidates = self._candidates()
        before = self._comparability_binding(before_candidates)
        rows = self._comparison_rows(before_ledger, before_candidates, require_facts)
        after_candidates = self._candidates()
        after = self._comparability_binding(after_candidates)
        if before != after or _digest(before_ledger) != _digest(self._read_state()):
            raise ValueError("可比性来源或核验状态在读取期间已变化，请重新加载并重新核验")
        confirmation = before_ledger.get("comparability")
        flags = {key: False for key in FLAGS}
        if confirmation and confirmation.get("binding") == after:
            flags.update({key: confirmation.get("flags", {}).get(key) is True for key in FLAGS})
        return {"binding": _digest(after), "source_binding": after, "rows": rows,
                "pdf_path": rows[0]["pdf_path"], "flags": flags}

    def comparison_snapshot(self) -> dict[str, Any]:
        """Read a stable snapshot of the exact normalized calculation inputs.

        Missing human Facts allow display. Contradictory numeric fields or a
        concurrent source change always fail closed, including for display.
        """
        try:
            return self._comparison_snapshot()
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"比较数来源无法读取：停止确认（{error}）") from error

    def save_comparability(self, flags: dict[str, bool], actor: str = "", note: str = "",
                           expected_binding: str | None = None) -> dict[str, Any]:
        if not isinstance(flags, dict) or set(flags) != set(FLAGS) or any(type(v) is not bool for v in flags.values()):
            raise ValueError("可比性须明确提供七项布尔确认，不能用字符串或数字替代")
        reviewer = actor.strip()
        with self._locked():
            ledger = self._read_state()
            candidates = self._candidates()
            snapshot = self._comparison_snapshot(ledger, require_facts=True)
            if expected_binding is not None and expected_binding != snapshot["binding"]:
                raise ValueError("可比性来源自展示后已变化，请重新加载并重新核验七项；未保存")
            value = {"flags": dict(flags), "actor": reviewer, "note": note.strip(),
                     "binding": snapshot["source_binding"], "snapshot_binding": snapshot["binding"],
                     "rows": snapshot["rows"]}
            old = ledger.get("comparability")
            changed = not old or any(old.get(k) != v for k, v in value.items())
            if changed:
                value["confirmed_at"] = datetime.now(SHANGHAI).isoformat(timespec="seconds")
                ledger["comparability"] = value
                ledger["events"].append({"sequence": len(ledger["events"]) + 1,
                    "operation": "comparability", **value})
                ledger["updated_at"] = value["confirmed_at"]
                self._atomic_text(self.state_path, _json(ledger))
            synced = self._sync_locked(ledger, candidates)
            try:
                self._validate_comparability(ledger, candidates)
                valid, reason = True, ""
            except ValueError as error:
                valid, reason = False, str(error)
            return {"changed": int(changed), "flags": dict(flags), "valid": valid, "reason": reason,
                    "counts": synced["counts"], "sync_errors": synced["errors"]}

    def _validate_comparability(self, ledger: dict[str, Any], candidates: list[EvidenceRecord],
                               expected_binding: str | None = None) -> bool:
        confirmation = ledger.get("comparability")
        if not confirmation or not all(confirmation.get("flags", {}).get(k) is True for k in FLAGS):
            raise ValueError("人工可比性未全部确认：停止计算，保留Unknown")
        snapshot = self._comparison_snapshot(ledger, require_facts=True)
        if confirmation.get("binding") != snapshot["source_binding"]:
            raise ValueError("可比性确认的候选、原PDF或计算输入已变化：须重新核验七项可比性")
        if expected_binding is not None and expected_binding != snapshot["binding"]:
            raise ValueError("展示比较数与当前来源或已保存可比性确认不一致：停止计算，请重新核验")
        if confirmation.get("snapshot_binding", _digest(confirmation["binding"])) != snapshot["binding"]:
            raise ValueError("已保存可比性快照与当前来源不一致：停止计算，请重新核验")
        return True

    def validate_comparability(self, expected_binding: str | None = None) -> bool:
        try:
            return self._validate_comparability(self._read_state(), self._candidates(), expected_binding)
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"可比性来源或账本无法读取：停止计算，保留Unknown（{error}）") from error

    @staticmethod
    def _counts(rows: list[EvidenceRecord]) -> dict[str, int]:
        return {"total": len(rows), "Fact": sum(r["state"] == "Fact" for r in rows),
                "Unknown": sum(r["state"] == "Unknown" for r in rows),
                "Withdrawn": sum(r["state"] == "Withdrawn" for r in rows),
                "stale": sum(bool(r.get("stale_reason")) for r in rows)}

    def sync(self) -> dict[str, Any]:
        with self._locked():
            return self._sync_locked(self._read_state(), self._candidates())

    def _block(self, text: str, name: str, content: str, is_html: bool = False) -> str:
        start, end = f"<!-- review-store:{name}:start -->", f"<!-- review-store:{name}:end -->"
        block = f"{start}\n{content}\n{end}"
        expression = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
        if expression.search(text):
            return expression.sub(lambda _: block, text)
        if is_html and "</main>" in text:
            return text.replace("</main>", block + "\n</main>", 1)
        return text.rstrip() + "\n\n" + block + "\n"

    def _row_states(self, text: str, lookup: dict[str, EvidenceRecord]) -> str:
        lines = []
        for line in text.splitlines(keepends=True):
            match = re.match(r"^\|\s*((?:C\d{2}|[RN]\d{4}-\d{2}))\s*\|", line)
            if not match or match.group(1) not in lookup:
                lines.append(line)
                continue
            row = lookup[match.group(1)]
            # Change the generated status cell only, preserving custom prose in it.
            cells = re.split(r"(?<!\\)\|", line.rstrip("\r\n"))
            current = cells[-2].strip()
            current = re.sub(r"\s*<!-- review-store:status:.*? -->", "", current)
            generated = re.compile(r"^(?:待核验／Unknown|本人核验／Fact(?:（.*?）)?|保留／Unknown(?:（.*?）)?|撤回／Unknown(?:（.*?）)?|来源变化／Unknown(?:（.*?）)?)$")
            if row.get("stale_reason"):
                status = "来源变化／Unknown"
            elif row["state"] == "Fact":
                status = f"本人核验／Fact（{_cell(row['actor'] or '姓名待补')}，{row['confirmed_at']}）"
            elif row["state"] == "Withdrawn":
                status = "撤回／Unknown"
            else:
                status = "保留／Unknown" if row.get("confirmed_at") else "待核验／Unknown"
            if generated.fullmatch(current):
                cells[-2] = f" {status} <!-- review-store:status:{row['id']} --> "
            else:
                # A handwritten cell remains byte-for-byte, with the current state in its managed block.
                lines.append(line)
                continue
            lines.append("|".join(cells) + ("\n" if line.endswith("\n") else ""))
        return "".join(lines)

    def _sync_locked(self, ledger: dict[str, Any], candidates: list[EvidenceRecord]) -> dict[str, Any]:
        rows = self._effective(ledger, candidates)
        lookup = {r["id"]: r for r in rows}
        counts = self._counts(rows)
        facts = [r for r in rows if r["state"] == "Fact"]
        summary = f"当前有效Fact为{counts['Fact']}条；Unknown为{counts['Unknown']}条；已撤回{counts['Withdrawn']}条；需重新核验{counts['stale']}条。共{counts['total']}条候选。"
        summary += " 日期自动按Asia/Shanghai记录。合同验收、复核人与正式签署另行完成。"
        status_rows = [[r["id"], r["state"], r["actor"] or ("姓名待补" if r["confirmed_at"] else ""),
                        r["confirmed_at"], r.get("stale_reason") or r["note"]] for r in rows]
        status_table = _table(["编号", "有效状态", "核验人", "核验时间", "备注／失效原因"], status_rows)
        errors, updated = [], []

        def save(relative: str, content: str):
            try:
                if self._atomic_text(self._path(relative), content):
                    updated.append(relative)
            except Exception as error:
                errors.append({"path": relative, "error": f"{type(error).__name__}: {error}"})

        try:
            save("evidence/confirmed-facts.json", _json({"schema_version": 1, "authority": "evidence/review-state.json",
                 "updated_at": ledger.get("updated_at", ""), "counts": counts, "facts": facts,
                 "source_binding": self._comparability_binding(candidates)}))
        except Exception as error:
            errors.append({"path": "evidence/confirmed-facts.json", "error": str(error)})
        fact_rows = [[r["id"], r["claim"], "Fact", r["source_version"] + "；PDF SHA-256=" + r["pdf_sha256"],
                      r["period"], r["location"], r["value"], r["scope"], r["support_boundary"],
                      r["unsupported_boundary"], f"{r['actor'] or '姓名待补'}；{r['confirmed_at']}", r["note"]] for r in facts]
        fact_table = _table(["编号", "主张", "类型", "来源版本", "报告期／比较基数", "精确定位", "原文或数值摘要",
                             "单位与口径", "支持边界", "不能支持什么", "人工核验", "待解决问题"], fact_rows)
        event_rows = []
        for event in ledger["events"]:
            event_rows.append([event["sequence"], event.get("id", "七项可比性"), event.get("state", "独立可比性确认"),
                               event.get("actor") or "姓名待补", event.get("confirmed_at", ""), event.get("note", "")])
        audit = _table(["事件", "编号／范围", "提交状态", "核验人", "时间", "备注"], event_rows)
        primary = {"evidence/evidence-log.md": "## 统一核验的有效证据\n\n" + summary + "\n\n" + fact_table + "\n\n## 提交历史\n\n" + audit,
                   "evidence/human-review-forms.md": "## 统一核验记录\n\n" + summary + "\n\n" + status_table,
                   "work/pending-checks.md": "## 已核验范围与仍待处理的候选\n\n" + summary + "\n\n" + status_table,
                   "docs/task-status.md": "## 统一核验进度\n\n" + summary + "\n\n" + self._group_table(rows),
                   "tasks/01-first-task.md": "## 第一次任务核验登记\n\n" + _table(["编号", "有效状态", "核验人", "时间"],
                       [[r["id"], r["state"], r["actor"] or ("姓名待补" if r["confirmed_at"] else ""), r["confirmed_at"]]
                        for r in rows if r["id"] in {"C01", "C02"}]) + "\n\n仅登记实际核验结果；合同正文验收勾选、复核与签署不由程序代填。合同尚未正式关闭。",
                   "README.md": "## 人工核验进度\n\n" + summary,
                   "工作流程与文件说明.md": "## 当前人工核验进度\n\n" + summary}
        for relative, body in primary.items():
            path = self._path(relative)
            if not path.exists():
                continue
            try:
                text = path.read_text(encoding="utf-8-sig")
                if relative == "evidence/evidence-log.md":
                    text = re.sub(r"当前已人工签认Fact为\d+条。", "人工核验进度见下方统一核验记录。", text)
                    text = text.replace("核验通过后复制候选行，保留编号，标Fact，记录核验人和日期；", "通过统一入口核验后自动登记候选编号、Fact、核验人和日期；")
                elif relative == "README.md":
                    text = text.replace("资料与自动化研究准备已完成；学生本人PDF核验、口径裁决、证据Fact升级与合同签署尚待完成。人名和签署日期留空，按用户要求以后统一填写。",
                        "资料与自动化研究准备已完成。学生本人PDF核验进度由统一核验记录更新，口径裁决与合同签署按实际情况完成。")
                    text = text.replace("本人核验后的证据日志及人工表；当前未假造Fact", "本人核验后的证据日志、统一核验账本及人工表")
                elif relative == "tasks/01-first-task.md":
                    text = re.sub(r"状态：自动化定位、整理和检查已完成；(?:人工核验未完成|C01、C02有效Fact为\d+/2条)，合同尚未正式关闭。",
                        f"状态：自动化定位、整理和检查已完成；C01、C02有效Fact为{sum(lookup[i]['state'] == 'Fact' for i in ('C01', 'C02') if i in lookup)}/2条，合同尚未正式关闭。", text)
                elif relative == "work/pending-checks.md":
                    text = text.replace("全部机器候选未本人签认", "候选人工核验范围见下方记录")
                elif relative == "docs/task-status.md":
                    text = text.replace("执行人、复核人和签署日期按用户要求留空；仅填姓名不等于已经核验。",
                        "核验人来自实际提交；合同复核人与签署按实际情况填写。仅填姓名不等于已经核验。")
                    text = self._task_status(text, rows, ledger, candidates)
                elif relative == "工作流程与文件说明.md":
                    text = text.replace("人员、签署与学生本人核验由你以后统一完成；",
                        "人工核验进度通过统一入口记录，人员与合同正式签署按实际情况完成；")
                if relative == "evidence/human-review-forms.md":
                    text = self._human_form(text, lookup)
                save(relative, self._block(text, "progress", body))
            except Exception as error:
                errors.append({"path": relative, "error": str(error)})

        for relative, group in (("outputs/first-analysis.md", "first"), ("outputs/revenue-structure-table.md", "revenue"),
                                ("outputs/metric-scope-decision.md", "scope"),
                                ("work/metric-scope-candidates.md", "scope")):
            path = self._path(relative)
            if not path.exists():
                continue
            try:
                text = path.read_text(encoding="utf-8-sig").replace(_OLD_INTRO, _NEW_INTRO)
                text = self._row_states(text, lookup)
                if group == "first":
                    text = text.replace("Unknown：本人核验、口径确认与签署未完成。", "核验状态见统一核验记录；口径取舍与合同签署按实际情况完成。")
                elif group == "scope":
                    text = text.replace("Unknown：本人核验、取舍裁决和证据编号尚未完成；", "待处理：未确认条目见统一核验记录，取舍裁决按实际情况记录；")
                group_rows = [r for r in rows if (group == "first" and r["id"] in {"C01", "C02"})
                    or (group == "scope" and r["id"].startswith("C")) or (group == "revenue" and r["id"].startswith(("R", "N")))]
                body = summary + "\n\n" + _table(["编号", "有效状态", "核验人", "核验时间", "备注／失效原因"],
                    [[r["id"], r["state"], r["actor"], r["confirmed_at"], r.get("stale_reason") or r["note"]] for r in group_rows])
                save(relative, self._block(text, "progress", body))
            except Exception as error:
                errors.append({"path": relative, "error": str(error)})

        html_path = self._path("工作台.html")
        if html_path.exists():
            try:
                text = html_path.read_text(encoding="utf-8-sig")
                text = re.sub(r"已人工签认Fact为\d+条。", f"当前有效Fact为{counts['Fact']}条。", text)
                text = text.replace("人员、签署及学生本人核验留待填写；", "人工核验进度由统一入口记录，合同签署另行完成；")
                save("工作台.html", self._block(text, "progress", '<section class="notice"><h2>人工核验进度</h2><p>'
                    + html.escape(summary) + "</p></section>", True))
            except Exception as error:
                errors.append({"path": "工作台.html", "error": str(error)})

        confirmation = ledger.get("comparability")
        if confirmation:
            try:
                config_path = self._path("config/human-review.json")
                config = json.loads(config_path.read_text(encoding="utf-8-sig")) if config_path.exists() else {}
                if not isinstance(config, dict) or not isinstance(config.get("human_confirmation", {}), dict):
                    raise ValueError("human-review.json格式错误；保留原文件")
                flags = dict(confirmation["flags"])
                if confirmation["binding"] != self._comparability_binding(candidates):
                    flags = {key: False for key in FLAGS}
                config.setdefault("human_confirmation", {}).update(flags)
                save("config/human-review.json", _json(config))
            except Exception as error:
                errors.append({"path": "config/human-review.json", "error": str(error)})
        return {"counts": counts, "updated_files": updated, "errors": errors, "sync_errors": errors,
                "event_count": len(ledger["events"])}

    @staticmethod
    def _group_table(rows: list[EvidenceRecord]) -> str:
        groups = [("第一次", [r for r in rows if r["id"] in {"C01", "C02"}]),
                  ("第二次", [r for r in rows if r["id"].startswith(("R", "N"))]),
                  ("第三次", [r for r in rows if r["id"].startswith("C")])]
        return _table(["任务", "有效Fact", "候选", "后续验收"],
            [[name, sum(r["state"] == "Fact" for r in subset), len(subset), "逐项验收、口径裁决与合同正式签署另行完成"]
             for name, subset in groups])

    @staticmethod
    def _human_form(text: str, lookup: dict[str, EvidenceRecord]) -> str:
        if "C01" not in lookup:
            return text
        row = lookup["C01"]
        lines = []
        for line in text.splitlines(keepends=True):
            if line.startswith("| H01数字 |"):
                cells = line.rstrip("\r\n").split("|")
                if cells[3].strip() in {"Unknown／待核验", "Fact／已核验", "Unknown／已撤回", "Unknown／来源变化"}:
                    cells[3] = " " + ("Fact／已核验" if row["state"] == "Fact" else
                        "Unknown／来源变化" if row.get("stale_reason") else
                        "Unknown／已撤回" if row["state"] == "Withdrawn" else "Unknown／待核验") + " "
                    line = "|".join(cells) + ("\n" if line.endswith("\n") else "")
            lines.append(line)
        return "".join(lines)

    def _task_status(self, text: str, rows: list[EvidenceRecord], ledger: dict[str, Any], candidates: list[EvidenceRecord]) -> str:
        totals = {"第一次": (sum(r["state"] == "Fact" for r in rows if r["id"] in {"C01", "C02"}), 2),
                  "第二次": (sum(r["state"] == "Fact" for r in rows if r["id"].startswith(("R", "N"))), 51),
                  "第三次": (sum(r["state"] == "Fact" for r in rows if r["id"].startswith("C")), 12)}
        known = {"第一次": "两条原文核验及Fact登记", "第二次": "至少一条本人核验；最终逐行确认范围",
                 "第三次": "本人采用/排除裁决及实际修正记录", "第四次": "本人确认可比性后执行复算并核验"}
        lines = []
        for line in text.splitlines(keepends=True):
            match = re.match(r"^\|\s*(第一次|第二次|第三次|第四次)\s*\|", line)
            if match:
                name = match.group(1)
                cells = re.split(r"(?<!\\)\|", line.rstrip("\r\n"))
                if len(cells) == 6 and (cells[-2].strip() == known[name] or "<!-- review-store:task:" in cells[-2]):
                    if name in totals:
                        confirmed, total = totals[name]
                        content = f"有效Fact {confirmed}/{total}条；"
                        content += "逐项验收与正式签署另行完成" if name == "第一次" else (
                            "逐行确认范围与正式验收仍须完成" if name == "第二次" else "本人采用/排除裁决及实际修正按真实过程记录")
                    else:
                        confirmation = ledger.get("comparability")
                        count = 0
                        if confirmation and confirmation.get("binding") == self._comparability_binding(candidates):
                            count = sum(confirmation["flags"].get(k) is True for k in FLAGS)
                        content = f"七项可比性独立确认{count}/7项；变化复算与正式核验仍须完成"
                    cells[-2] = f" {content} <!-- review-store:task:{name} --> "
                    line = "|".join(cells) + ("\n" if line.endswith("\n") else "")
            lines.append(line)
        return "".join(lines)
