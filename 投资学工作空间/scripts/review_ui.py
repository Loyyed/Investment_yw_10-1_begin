"""Local, explicit human review of source candidates. Opening this UI is read-only."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
sys.dont_write_bytecode = True
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import traceback

WORKSPACE = Path(__file__).resolve().parents[1]
COMPARABILITY = (
    ("report_version", "报告版本与指定材料一致"),
    ("periods", "本期2024、比较期2023与比较基数正确"),
    ("unit_currency", "两期单位、币种一致"),
    ("reporting_entity", "两期报表主体一致"),
    ("consolidation_scope", "两期合并范围一致或可比"),
    ("metric_definition", "两期指标定义与口径一致"),
    ("no_restatement", "未发现影响比较的前期数据重述"),
)
GROUPS = {
    "第一次 · 营业收入与归母净利润": "first",
    "收入结构 · R / N 候选": "revenue",
    "口径 · C 候选": "scope",
    "全部候选": "all",
}


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


def reviewer_from_task(workspace: Path) -> str:
    """Read the entered executor, without supplying a signature or a date."""
    try:
        text = (workspace / "tasks/01-first-task.md").read_text(encoding="utf-8")
    except OSError:
        return ""
    matches = re.findall(r"执行人[：:]\s*([^；\n]+)", text)
    for match in reversed(matches):
        name = match.strip().strip("_ *")
        if name and "待" not in name:
            return name
    return ""


def text_value(value) -> str:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False)
    return "" if value is None else str(value)


def computation_python(executable=None) -> str:
    """Use console Python with captured pipes, even when the UI uses pythonw."""
    python = Path(executable or sys.executable)
    if os.name == "nt" and python.name.casefold() == "pythonw.exe":
        python = python.with_name("python.exe")
        if not python.is_file():
            raise FileNotFoundError(f"未找到复算所需的Python：{python}")
    return str(python)


class ReviewApp:
    def __init__(self, root: tk.Tk, workspace: Path = WORKSPACE, store=None):
        if store is None:
            from review_store import ReviewStore
            store = ReviewStore(workspace)
        self.root, self.workspace, self.store = root, Path(workspace).resolve(), store
        self.candidates = []
        self.by_id = {}
        self.compute_queue = queue.Queue()
        self.computing = False
        self.compare_sync_pending = False
        self.comparison_binding = None
        profile = self.store.get_profile() or {}
        self.actor_var = tk.StringVar(value=profile.get("reviewer") if "reviewer" in profile else reviewer_from_task(self.workspace))
        self.group_var = tk.StringVar(value=next(iter(GROUPS)))
        self.year_var = tk.StringVar(value="全部年份")
        self.state_var = tk.StringVar(value="全部状态")
        self.search_var = tk.StringVar()
        self.count_var = tk.StringVar()
        self.selection_var = tk.StringVar()
        self.status_var = tk.StringVar(value="已选择第一次的两条候选；请核对PDF后再确认。选择本身不会保存或变成Fact。")
        self.note_var = tk.StringVar()
        self.compare_note_var = tk.StringVar()
        self.compare_status_var = tk.StringVar()
        self.all_comparable_var = tk.BooleanVar(value=False)
        self.compare_vars = {key: tk.BooleanVar(value=False) for key, _ in COMPARABILITY}
        self._configure_window()
        self._build()
        self.refresh_candidates(initial=True)
        self._load_change_result()

    def _configure_window(self):
        self.root.title("贵州茅台年报 · 本人人工核验")
        self.root.geometry("1100x760")
        self.root.minsize(900, 650)
        self.root.option_add("*Font", ("Microsoft YaHei UI", 10))
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TFrame", background="#f5f7fb")
        style.configure("TLabel", background="#f5f7fb", foreground="#243247")
        style.configure("TNotebook", background="#f5f7fb", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(18, 9))
        style.configure("TButton", padding=(12, 7), font=("Microsoft YaHei UI", 10))
        style.configure("Primary.TButton", background="#2368c4", foreground="#ffffff", borderwidth=0)
        style.map("Primary.TButton", background=[("active", "#1753a5"), ("disabled", "#b3c6df")],
                  foreground=[("disabled", "#ffffff")])
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 18, "bold"))
        style.configure("Subtle.TLabel", foreground="#596a80")
        style.configure("Treeview", rowheight=29, font=("Microsoft YaHei UI", 10), background="#ffffff")
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"), padding=(5, 7))
        style.map("Treeview", background=[("selected", "#d9e9fc")], foreground=[("selected", "#17395f")])
        self.root.configure(background="#f5f7fb")

    def _build(self):
        shell = ttk.Frame(self.root, padding=(20, 14, 20, 12))
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(1, weight=1)
        header = ttk.Frame(shell)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="本人人工核验", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, textvariable=self.count_var, style="Subtle.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 0))
        actor = ttk.Frame(header)
        actor.grid(row=0, column=1, rowspan=2, sticky="e")
        ttk.Label(actor, text="核验人").pack(side="left", padx=(0, 8))
        self.actor_entry = ttk.Entry(actor, textvariable=self.actor_var, width=16)
        self.actor_entry.pack(side="left")
        ttk.Label(actor, text="姓名可补填，保存时记忆", style="Subtle.TLabel").pack(side="left", padx=(10, 0))
        self.notebook = ttk.Notebook(shell)
        self.notebook.grid(row=1, column=0, sticky="nsew")
        self.review_tab = ttk.Frame(self.notebook, padding=14)
        self.compare_tab = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(self.review_tab, text="候选核验")
        self.notebook.add(self.compare_tab, text="变化可比性")
        self._build_review_tab()
        self._build_compare_tab()
        ttk.Label(shell, text="人工日期自动记录。窗口关闭前的未保存选择与备注不会写入证据。", style="Subtle.TLabel").grid(row=2, column=0, sticky="w", pady=(10, 0))

    def _build_review_tab(self):
        tab = self.review_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)
        ttk.Label(tab, text="确认表示已回到原PDF核对版本、期间、单位、表名、口径、注释及支持边界。", wraplength=970).grid(row=0, column=0, sticky="w", pady=(0, 10))
        filters = ttk.Frame(tab)
        filters.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.group_combo = ttk.Combobox(filters, textvariable=self.group_var, values=list(GROUPS), state="readonly", width=32)
        self.group_combo.pack(side="left", padx=(0, 8))
        self.year_combo = ttk.Combobox(filters, textvariable=self.year_var, values=["全部年份", "2024", "2023", "2022", "2021", "2020"], state="readonly", width=10)
        self.year_combo.pack(side="left", padx=(0, 8))
        self.state_combo = ttk.Combobox(filters, textvariable=self.state_var, values=["全部状态", "Fact", "Unknown"], state="readonly", width=11)
        self.state_combo.pack(side="left", padx=(0, 8))
        ttk.Label(filters, text="搜索").pack(side="left", padx=(3, 6))
        ttk.Entry(filters, textvariable=self.search_var).pack(side="left", fill="x", expand=True)
        for variable in (self.group_var, self.year_var, self.state_var, self.search_var):
            variable.trace_add("write", lambda *_: self._fill_tree())
        panes = ttk.Panedwindow(tab, orient="vertical")
        panes.grid(row=2, column=0, sticky="nsew")
        list_frame = ttk.Frame(panes)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        columns = ("id", "state", "year", "claim", "value", "location")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="extended", height=7)
        for col, label, width in (("id", "编号", 92), ("state", "状态", 86), ("year", "报告期", 72), ("claim", "指标 / 主张", 295), ("value", "原值（元）", 224), ("location", "PDF / 报告页", 130)):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, minwidth=55, stretch=col in ("claim", "value"))
        self.tree.tag_configure("Fact", foreground="#16774b")
        self.tree.tag_configure("Unknown", foreground="#53667b")
        self.tree.grid(row=0, column=0, sticky="nsew")
        ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview).grid(row=0, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        horizontal.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=list_frame.grid_slaves(row=0, column=1)[0].set, xscrollcommand=horizontal.set)
        self.tree.bind("<<TreeviewSelect>>", self._selection_changed)
        panes.add(list_frame, weight=3)
        details = ttk.Frame(panes, padding=(0, 10, 0, 0))
        details.columnconfigure(0, weight=1)
        details.rowconfigure(1, weight=1)
        details_header = ttk.Frame(details)
        details_header.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        ttk.Label(details_header, text="当前条目的来源与口径", font=("Microsoft YaHei UI", 10, "bold")).pack(side="left")
        self.open_pdf_button = ttk.Button(details_header, text="打开当前原PDF", command=self.open_selected_pdf)
        self.open_pdf_button.pack(side="right")
        self.detail_text = self._scrolled_text(details, 1, height=8)
        panes.add(details, weight=3)
        controls = ttk.Frame(tab)
        controls.grid(row=3, column=0, sticky="ew", pady=(9, 0))
        controls.columnconfigure(1, weight=1)
        ttk.Label(controls, textvariable=self.selection_var).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        ttk.Label(controls, text="可选备注").grid(row=1, column=0, sticky="w", padx=(0, 10))
        self.note_entry = ttk.Entry(controls, textvariable=self.note_var)
        self.note_entry.grid(row=1, column=1, sticky="ew")
        buttons = ttk.Frame(controls)
        buttons.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(9, 0))
        self.fact_button = ttk.Button(buttons, text="确认所选为 Fact", style="Primary.TButton", command=lambda: self.submit_selected("Fact"))
        self.fact_button.pack(side="left", padx=(0, 10))
        self.unknown_button = ttk.Button(buttons, text="保留 Unknown / 撤回确认", command=lambda: self.submit_selected("Unknown"))
        self.unknown_button.pack(side="left", padx=(0, 10))
        self.select_all_button = ttk.Button(buttons, text="全选当前列表", command=self.select_all_visible)
        self.select_all_button.pack(side="left")
        self.sync_button = ttk.Button(buttons, text="刷新并同步", command=self.sync_and_refresh)
        self.sync_button.pack(side="right")
        ttk.Label(controls, textvariable=self.status_var, wraplength=960, style="Subtle.TLabel").grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _scrolled_text(self, parent, row, height=8):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        text = tk.Text(frame, height=height, wrap="word", font=("Microsoft YaHei UI", 10), relief="solid", borderwidth=1, background="#ffffff", foreground="#243247", padx=11, pady=8, cursor="arrow")
        text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=scroll.set, state="disabled")
        return text

    @staticmethod
    def _put_text(widget, content):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.configure(state="disabled")

    def refresh_candidates(self, initial=False):
        self.candidates = list(self.store.list_candidates(group="all"))
        self.by_id = {text_value(row["id"]): row for row in self.candidates}
        facts = sum(row.get("state") == "Fact" for row in self.candidates)
        self.count_var.set(f"贵州茅台 · {len(self.candidates)} 条候选    Fact {facts}    Unknown {len(self.candidates) - facts}")
        self._fill_tree(initial=initial)
        if hasattr(self, "comparison_tree"):
            self._refresh_comparison()

    def _fill_tree(self, initial=False):
        if not hasattr(self, "tree"):
            return
        selected = set(self.tree.selection())
        group = GROUPS.get(self.group_var.get(), "all")
        query = self.search_var.get().strip().casefold()
        rows = []
        for row in self.candidates:
            rid = text_value(row.get("id"))
            if group == "first" and rid not in {"C01", "C02"}:
                continue
            if group == "revenue" and not rid.startswith(("R", "N")):
                continue
            if group == "scope" and not rid.startswith("C"):
                continue
            if self.year_var.get() != "全部年份" and text_value(row.get("year")) != self.year_var.get():
                continue
            state = "Fact" if row.get("state") == "Fact" else "Unknown"
            if self.state_var.get() != "全部状态" and state != self.state_var.get():
                continue
            if query and query not in " ".join(text_value(row.get(k)) for k in ("id", "claim", "value", "year", "location", "scope", "table", "note")).casefold():
                continue
            rows.append(row)
        if group == "first":
            rows.sort(key=lambda row: row["id"])
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            rid = text_value(row["id"])
            state = "Fact" if row.get("state") == "Fact" else "Unknown"
            self.tree.insert("", "end", iid=rid, values=(rid, state, text_value(row.get("year")), text_value(row.get("claim")), text_value(row.get("value")), text_value(row.get("location"))), tags=(state,))
        visible = set(self.tree.get_children())
        restore = selected & visible
        if initial or (group == "first" and not restore):
            restore = {"C01", "C02"} & visible
        if restore:
            ordered = [rid for rid in self.tree.get_children() if rid in restore]
            self.tree.selection_set(ordered)
            self.tree.focus(ordered[0])
        self._selection_changed()

    def select_all_visible(self):
        self.tree.selection_set(self.tree.get_children())
        self._selection_changed()

    def _active_candidate(self):
        selected = self.tree.selection()
        focus = self.tree.focus()
        rid = focus if focus in selected else (selected[0] if selected else None)
        return self.by_id.get(rid)

    def _selection_changed(self, *_):
        selected = self.tree.selection()
        self.selection_var.set(f"当前显示 {len(self.tree.get_children())} 条，已选 {len(selected)} 条。Ctrl / Shift 可多选；确认仅作用于所选条目。")
        for button in (self.fact_button, self.unknown_button):
            button.configure(state="normal" if selected else "disabled")
        row = self._active_candidate()
        self.open_pdf_button.configure(state="normal" if row and row.get("pdf_path") else "disabled")
        if not row:
            self._put_text(self.detail_text, "选择一条候选，查看原值、PDF位置、表名与口径。")
            return
        pdf = text_value(row.get("pdf_path"))
        detail = [f"{row['id']}  ·  {text_value(row.get('claim'))}",
                  f"原值：{text_value(row.get('value'))}    报告期：{text_value(row.get('year'))}    单位：{text_value(row.get('unit') or '人民币元')}",
                  f"来源版本：{text_value(row.get('source_version') or str(row.get('year', '')) + '年度报告')}",
                  f"定位：{text_value(row.get('location'))}    表名：{text_value(row.get('table') or '请回到PDF核对表名')}",
                  f"口径：{text_value(row.get('scope'))}",
                  f"支持边界：{text_value(row.get('support_boundary') or '限定材料与口径内的披露值')}",
                  f"不能支持：{text_value(row.get('unsupported_boundary') or '变化机制、未来价值或买卖判断')}",
                  f"原PDF：{pdf}",
                  f"人工状态：{text_value(row.get('state') or 'Unknown')}    核验人：{text_value(row.get('actor') or '待补')}    日期：{text_value(row.get('confirmed_at') or '尚未确认')}"]
        if row.get("note"):
            detail.append(f"已保存备注：{text_value(row['note'])}")
        if row.get("stale_reason"):
            detail.append(f"待重新核验：{text_value(row['stale_reason'])}")
        self._put_text(self.detail_text, "\n".join(detail))

    def open_selected_pdf(self):
        row = self._active_candidate()
        if row:
            self._open_pdf(row.get("pdf_path"))

    def _open_pdf(self, value):
        if not value:
            self.status_var.set("此候选尚无可打开的原PDF路径。")
            return
        path = Path(str(value))
        if not path.is_absolute():
            path = self.workspace / path
        try:
            if not path.is_file():
                raise FileNotFoundError(f"原PDF未找到：{path.name}")
            os.startfile(str(path.resolve()))
        except (OSError, AttributeError) as exc:
            self.status_var.set(f"无法打开原PDF：{exc}")

    def submit_selected(self, state):
        ids = list(self.tree.selection())
        if not ids:
            self.status_var.set("请先选择要保存的候选。")
            return
        try:
            result = self.store.submit(ids, state=state, actor=self.actor_var.get().strip(), note=self.note_var.get().strip(),
                                       expected_bindings={rid: self.by_id[rid]["binding"] for rid in ids})
        except Exception as exc:
            self._reload_after_rejection()
            self.status_var.set(f"本次未确认：{exc}。已重新加载，请回到当前原PDF重新核验。")
            return
        self.refresh_candidates()
        profile = self.store.get_profile() or {}
        if "reviewer" in profile:
            self.actor_var.set(profile["reviewer"])
        label = "Fact" if state == "Fact" else "Unknown（已保留或撤回确认）"
        if result.get("sync_errors"):
            self.status_var.set(f"{len(ids)} 条记录已保存为 {label}，部分视图待刷新。")
        else:
            self.status_var.set(f"已保存所选 {len(ids)} 条为 {label}，证据记录与成果视图已同步。")
        self.note_var.set("")

    def _clear_comparability(self):
        for variable in self.compare_vars.values():
            variable.set(False)
        self.all_comparable_var.set(False)

    def _reload_after_rejection(self):
        try:
            self.refresh_candidates()
        except Exception:
            # Never continue with an old success state if a source cannot be reread.
            self.fact_button.configure(state="disabled")
            self.unknown_button.configure(state="disabled")
        self._clear_comparability()

    def sync_and_refresh(self):
        """Rebuild derived views only after the user explicitly asks for it."""
        try:
            result = self.store.sync()
        except Exception as exc:
            self.status_var.set(f"刷新同步未完成：{exc}。已保存的核验记录仍保留，请稍后重试。")
            return
        try:
            self.refresh_candidates()
            self._load_change_result()
        except Exception as exc:
            self.status_var.set(f"同步已执行，列表暂未刷新：{exc}。已保存的核验记录仍保留。")
            return
        if result.get("sync_errors") or result.get("errors"):
            self.status_var.set("记录已保留，部分视图待刷新；可再次点击“刷新并同步”。")
        else:
            self.status_var.set("列表与成果视图已刷新同步；人工核验状态保持为已保存的记录。")

    def _build_compare_tab(self):
        tab = self.compare_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(5, weight=1)
        ttk.Label(tab, text="确认两期原值与可比性后复算变化。第一次的Fact确认与以下七项确认相互独立。", wraplength=960).grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.comparison_tree = ttk.Treeview(tab, columns=("metric", "current", "previous", "location"), show="headings", height=2, selectmode="browse")
        for col, label, width in (("metric", "指标（人民币元，合并）", 280), ("current", "2024 本期原值", 230), ("previous", "2023 比较期原值", 230), ("location", "2024报告定位", 155)):
            self.comparison_tree.heading(col, text=label)
            self.comparison_tree.column(col, width=width, stretch=True)
        self.comparison_tree.grid(row=1, column=0, sticky="ew")
        self.comparison_pdf = ""
        source_row = ttk.Frame(tab)
        source_row.grid(row=2, column=0, sticky="ew", pady=(7, 10))
        ttk.Label(source_row, text="来源：2024年原PDF的2024本期列与2023比较列。以下数值与实际复算输入一致。", style="Subtle.TLabel").pack(side="left")
        ttk.Button(source_row, text="打开2024原PDF", command=lambda: self._open_pdf(self.comparison_pdf)).pack(side="right")
        checklist = ttk.Frame(tab)
        checklist.grid(row=3, column=0, sticky="ew")
        checklist.columnconfigure(0, weight=1)
        checklist.columnconfigure(1, weight=1)
        self.all_comparable_check = ttk.Checkbutton(checklist, text="上述七项均已核对且可比较", variable=self.all_comparable_var, command=self._toggle_all_comparable)
        self.all_comparable_check.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self.comparability_checks = {}
        for index, (key, label) in enumerate(COMPARABILITY):
            check = ttk.Checkbutton(checklist, text=label, variable=self.compare_vars[key], command=self._update_all_comparable)
            check.grid(row=index // 2 + 1, column=index % 2, sticky="w", padx=(0, 12), pady=4)
            self.comparability_checks[key] = check
        controls = ttk.Frame(tab)
        controls.grid(row=4, column=0, sticky="ew", pady=(12, 9))
        controls.columnconfigure(1, weight=1)
        ttk.Label(controls, text="可选备注").grid(row=0, column=0, padx=(0, 10))
        ttk.Entry(controls, textvariable=self.compare_note_var).grid(row=0, column=1, sticky="ew", padx=(0, 12))
        self.save_compare_button = ttk.Button(controls, text="保存并复算", style="Primary.TButton", command=self.save_and_compute)
        self.save_compare_button.grid(row=0, column=2)
        self.result_text = self._scrolled_text(tab, 5, height=7)
        ttk.Label(tab, textvariable=self.compare_status_var, style="Subtle.TLabel", wraplength=970).grid(row=6, column=0, sticky="w", pady=(8, 0))
        self._refresh_comparison(initial=True)

    def _refresh_comparison(self, initial=False):
        try:
            snapshot = self.store.comparison_snapshot()
        except Exception as exc:
            self.comparison_binding = None
            self.comparison_pdf = ""
            self.comparison_tree.delete(*self.comparison_tree.get_children())
            self._clear_comparability()
            self.save_compare_button.configure(state="disabled")
            self.compare_status_var.set(f"两期原值暂不能核验：{exc}。请核对原PDF并刷新后重新确认。")
            self._load_change_result()
            return
        changed = self.comparison_binding is not None and self.comparison_binding != snapshot["binding"]
        self.comparison_binding = snapshot["binding"]
        self.comparison_pdf = snapshot.get("pdf_path", "")
        self.comparison_tree.delete(*self.comparison_tree.get_children())
        for row in snapshot.get("rows", []):
            pages = ", ".join(map(str, row.get("pdf_pages", [])))
            self.comparison_tree.insert("", "end", values=(row["metric"], row["current"], row["previous"], row.get("location") or f"PDF / 报告 {pages} 页"))
        if initial:
            flags = snapshot.get("flags", {})
            for key, variable in self.compare_vars.items():
                variable.set(flags.get(key) is True)
            self._update_all_comparable()
        elif changed:
            self._clear_comparability()
            self.compare_status_var.set("原PDF、候选或两期输入已变化，已重新加载并清除本窗口的七项勾选，请重新核验。")
            self._load_change_result()
        self.save_compare_button.configure(state="disabled" if self.computing else "normal")

    def _toggle_all_comparable(self):
        chosen = self.all_comparable_var.get()
        for variable in self.compare_vars.values():
            variable.set(chosen)

    def _update_all_comparable(self):
        self.all_comparable_var.set(all(variable.get() for variable in self.compare_vars.values()))

    def save_and_compute(self):
        if self.computing:
            return
        if not self.comparison_binding:
            self._refresh_comparison()
            self._clear_comparability()
            self.compare_status_var.set("本次未保存：两期原值尚未取得有效来源，请刷新并重新核验。")
            return
        flags = {key: variable.get() for key, variable in self.compare_vars.items()}
        try:
            saved = self.store.save_comparability(flags, actor=self.actor_var.get().strip(), note=self.compare_note_var.get().strip(),
                                                  expected_binding=self.comparison_binding)
        except Exception as exc:
            self._reload_after_rejection()
            self.compare_status_var.set(f"本次可比性未保存：{exc}。已重新加载并清除七项勾选，请重新核验。")
            return
        self.compare_sync_pending = bool(saved.get("sync_errors"))
        if self.compare_sync_pending:
            self.compare_status_var.set("可比性记录已保存，部分视图待刷新；正在尝试复算。可在候选页点击“刷新并同步”。")
        else:
            self.compare_status_var.set("可比性记录已保存，正在复算；变化结果仍需本人核验。")
        self.computing = True
        self.save_compare_button.configure(state="disabled")
        threading.Thread(target=self._compute_worker, daemon=True).start()
        self.root.after(100, self._poll_compute)

    def _compute_worker(self):
        try:
            options = {"cwd": str(self.workspace), "capture_output": True, "text": True, "encoding": "utf-8", "errors": "replace", "timeout": 90}
            if os.name == "nt":
                options["creationflags"] = subprocess.CREATE_NO_WINDOW
            result = subprocess.run([computation_python(), str(self.workspace / "scripts/07_compute_changes.py")], **options)
            self.compute_queue.put((result.returncode, (result.stderr or result.stdout).strip()))
        except Exception as exc:
            self.compute_queue.put((-1, str(exc)))

    def _poll_compute(self):
        try:
            returncode, message = self.compute_queue.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_compute)
            return
        self.computing = False
        prior_binding = self.comparison_binding
        self._refresh_comparison()
        changed = self.comparison_binding is None or self.comparison_binding != prior_binding
        self._load_change_result()
        if changed:
            self.compare_status_var.set("复算结束；原PDF或两期输入现已变化，已重新加载并清除七项勾选，请重新核验。")
        elif returncode == 0:
            self.compare_status_var.set("已保存并完成复算。复算值保留Unknown，确认其变化事实需另行核验。")
        elif returncode == 2:
            self.compare_status_var.set("已保存；可比性条件未全部通过，已停止计算并保留Unknown。")
        else:
            self.compare_status_var.set(f"可比性记录已保存，复算未完成：{message[:350]}")
        if self.compare_sync_pending:
            self.compare_status_var.set(self.compare_status_var.get() + " 部分视图待刷新，可在候选页点击“刷新并同步”。")

    def _load_change_result(self):
        result = read_json(self.workspace / "work/change-recalculation.json", {})
        if not result:
            self._put_text(self.result_text, "尚无复算结果。核对上述七项后，点击“保存并复算”。")
            return
        if result.get("status") == "stopped":
            self._put_text(self.result_text, f"计算已停止 · Unknown\n{result.get('reason', '可比性未全部人工确认')}\n\n核对后可保存新的可比性记录并复算。")
            return
        rows = result.get("results", [])
        if (not self.comparison_binding or not rows
                or any(row.get("source_binding") != self.comparison_binding for row in rows)):
            self._put_text(self.result_text, "既有复算结果尚未对应当前来源，暂不展示为当前结果。\n请重新核验两期输入与七项可比性，再点击“保存并复算”。")
            return
        lines = ["已有复算结果 · 仍待本人核验（Unknown）", "公式：（本期数 − 比较期数）÷ 比较期数 × 100%；四舍五入保留2位。"]
        for row in result.get("results", []):
            lines.append(f"\n{row.get('metric', '')}：{row.get('percent', '')}%\n本期 {row.get('current', '')} 元；比较期 {row.get('previous', '')} 元。")
        lines.append("\n以上仅描述指标变化，不能直接支持变化机制、预测或投资判断。")
        self._put_text(self.result_text, "\n".join(lines))


def main(argv=None):
    parser = argparse.ArgumentParser(description="本地人工核验窗口")
    parser.add_argument("--workspace", type=Path, default=WORKSPACE)
    parser.add_argument("--smoke", action="store_true", help="隐藏窗口，仅建立控件并检查布局，不保存")
    args = parser.parse_args(argv)
    root = None
    try:
        root = tk.Tk()
        if args.smoke:
            root.withdraw()
        app = ReviewApp(root, args.workspace)
        if args.smoke:
            root.update_idletasks()
            assert {"C01", "C02"} <= set(app.tree.selection()), "第一次两条候选未默认选中"
            assert app.actor_var.get() == app.store.get_profile().get("reviewer", reviewer_from_task(args.workspace))
            if os.name == "nt" and Path(sys.executable).name.casefold() == "pythonw.exe":
                assert Path(computation_python()).name.casefold() == "python.exe"
            if sys.stdout is not None:
                print("UI smoke passed: widgets built; first candidates selected; console Python selected for computation; no save action invoked.")
            return 0
        root.mainloop()
        return 0
    except Exception as exc:
        if args.smoke:
            if sys.stderr is not None:
                traceback.print_exc(file=sys.stderr)
            return 1
        detail = traceback.format_exc()
        log_path = args.workspace.resolve() / "work/review-ui-errors.log"
        logged = False
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as stream:
                stream.write(f"\n[{datetime.now().isoformat(timespec='seconds')}]\n{detail}")
            logged = True
        except OSError:
            pass
        message = f"人工核验窗口无法启动。\n\n原因：{exc}\n\n请从完整工作空间中的入口重试；如仍失败，请查看错误日志或联系维护者。"
        if logged:
            message += f"\n\n错误日志：{log_path}"
        message += "\n\n已有核验记录不会被这次启动覆盖。"
        try:
            messagebox.showerror("人工核验窗口启动失败", message, parent=root)
        except tk.TclError:
            if os.name == "nt":
                import ctypes
                ctypes.windll.user32.MessageBoxW(None, message, "人工核验窗口启动失败", 0x10)
            elif sys.stderr is not None:
                print(message, file=sys.stderr)
        return 1
    finally:
        if root is not None:
            try:
                root.destroy()
            except tk.TclError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
