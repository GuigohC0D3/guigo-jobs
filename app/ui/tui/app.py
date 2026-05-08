from __future__ import annotations

import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    RadioButton,
    RadioSet,
    Rule,
    Static,
    Switch,
    TabbedContent,
    TabPane,
)

from app.models.job import Job, SearchFilters, SeniorityLevel
from app.core.config import settings
from app.services.export import ExportService
from app.services.resume import ResumeData, ResumeService
from app.services.search import SearchService
from app.storage.favorites import FavoritesStorage
from app.storage.history import HistoryStorage

_CSS = """
Screen {
    background: #060d18;
    color: #c9d1d9;
}

Header {
    background: #0d1117;
    color: #58a6ff;
    text-style: bold;
}

Footer {
    background: #0d1117;
    color: #484f58;
}

/* ── Layout ────────────────────────────────────── */

#main-layout {
    height: 1fr;
}

/* ── Sidebar ───────────────────────────────────── */

#sidebar {
    width: 32;
    background: #0d1117;
    border-right: solid #21262d;
    padding: 1 2;
    overflow-y: auto;
}

#logo {
    color: #58a6ff;
    text-style: bold;
    text-align: center;
    height: 3;
    content-align: center middle;
    border-bottom: solid #21262d;
    margin-bottom: 1;
}

.s-label {
    color: #484f58;
    height: 1;
    margin-top: 1;
}

Input {
    background: #161b22;
    border: tall #30363d;
    color: #e6edf3;
    height: 3;
}

Input:focus {
    border: tall #58a6ff;
}

RadioSet {
    border: none;
    background: transparent;
    height: auto;
    padding: 0;
    margin-bottom: 1;
}

RadioSet > RadioButton {
    background: transparent;
    color: #8b949e;
    border: none;
    padding: 0 1 0 0;
}

RadioSet > RadioButton.-on {
    color: #58a6ff;
    text-style: bold;
    background: transparent;
}

RadioSet:focus-within > RadioButton.-on {
    color: #58a6ff;
}

Switch {
    margin: 1 0;
    border: none;
}

#btn-search {
    width: 100%;
    margin-top: 2;
    background: #238636;
    color: #ffffff;
    text-style: bold;
    border: none;
}

#btn-search:hover {
    background: #2ea043;
}

#btn-search:focus {
    background: #2ea043;
    border: none;
}

/* ── Content area ──────────────────────────────── */

#content {
    width: 1fr;
    background: #060d18;
}

#status {
    height: 1;
    background: #0d1117;
    border-bottom: solid #21262d;
    padding: 0 2;
    color: #484f58;
}

TabbedContent {
    height: 1fr;
}

TabPane {
    padding: 0;
}

Tab {
    background: #0d1117;
    color: #8b949e;
}

Tab.-active {
    color: #58a6ff;
    text-style: bold;
}

Tabs {
    background: #0d1117;
    border-bottom: solid #21262d;
}

Tabs:focus {
    border-bottom: solid #21262d;
}

/* ── Job list ──────────────────────────────────── */

#job-list, #fav-list {
    padding: 1;
    background: #060d18;
}

JobItem {
    height: auto;
    background: #0d1117;
    border: solid #21262d;
    padding: 1 2;
    margin-bottom: 1;
}

JobItem.--highlight {
    border: solid #58a6ff;
    background: #0d1f36;
}

JobItem:focus {
    border: solid #58a6ff;
}

/* ── History table ─────────────────────────────── */

DataTable {
    margin: 1;
    background: #060d18;
}

DataTable > .datatable--header {
    background: #0d1117;
    color: #58a6ff;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: #0d1f36;
    color: #e6edf3;
}

DataTable > .datatable--even-row {
    background: #060d18;
}

DataTable > .datatable--odd-row {
    background: #0d1117;
}

/* ── Country quick-pick ────────────────────────── */

#country-row {
    layout: horizontal;
    height: auto;
    margin-top: 1;
}

.region-btn {
    width: 1fr;
    border: solid #30363d;
    background: #161b22;
    color: #8b949e;
    margin-right: 1;
    height: 3;
}

.region-btn:last-of-type {
    margin-right: 0;
}

.region-btn.-active-region {
    background: #0d1f36;
    color: #58a6ff;
    border: solid #58a6ff;
    text-style: bold;
}

#sources-label {
    color: #484f58;
    height: 1;
    margin-top: 2;
}

#sources-info {
    color: #30363d;
    height: auto;
}

/* ── Resume section ──────────────────────────────── */
#resume-row {
    height: auto;
    margin-bottom: 1;
}

#resume-status {
    width: 1fr;
    height: 1;
    content-align: left middle;
}

.resume-btn {
    width: 3;
    height: 1;
    border: none;
    min-width: 3;
    background: #21262d;
    color: #8b949e;
}

.resume-btn:hover {
    background: #30363d;
    color: #e6edf3;
}

/* ── Job Detail Modal ──────────────────────────── */

JobDetailModal {
    align: center middle;
}

#modal-box {
    width: 80%;
    max-height: 88%;
    background: #161b22;
    border: solid #30363d;
    padding: 2 3;
}

#m-title {
    text-style: bold;
    color: #58a6ff;
    height: auto;
    margin-bottom: 1;
}

#m-company {
    color: #d2a8ff;
    height: auto;
}

#m-location {
    color: #8b949e;
    height: auto;
}

#m-salary {
    color: #3fb950;
    height: auto;
    margin-bottom: 1;
}

#m-source {
    color: #79c0ff;
    height: auto;
}

#m-tags {
    color: #e3b341;
    height: auto;
    margin-bottom: 1;
}

#m-desc {
    color: #c9d1d9;
    height: auto;
    margin-bottom: 1;
}

#m-url {
    color: #484f58;
    height: auto;
    margin-bottom: 2;
}

#m-actions {
    height: auto;
    layout: horizontal;
}

.m-btn {
    margin-right: 1;
    border: none;
}

#btn-browser { background: #6e40c9; color: #ffffff; }
#btn-browser:hover { background: #8957e5; }

#btn-fav { background: #9e6a03; color: #ffffff; }
#btn-fav:hover { background: #bb8009; }

#btn-fav.--favorited { background: #9e6a03; }

#btn-mclose { background: #21262d; color: #8b949e; }
#btn-mclose:hover { background: #30363d; }

/* ── Export Modal ──────────────────────────────── */

ExportModal {
    align: center middle;
}

#export-box {
    width: 38;
    height: auto;
    background: #161b22;
    border: solid #30363d;
    padding: 2 3;
}

#export-title {
    text-align: center;
    color: #58a6ff;
    text-style: bold;
    height: 2;
    margin-bottom: 1;
}

.ex-btn {
    width: 100%;
    margin-bottom: 1;
    border: none;
}

#ex-json { background: #1f6feb; color: #ffffff; }
#ex-json:hover { background: #388bfd; }

#ex-csv { background: #238636; color: #ffffff; }
#ex-csv:hover { background: #2ea043; }

#ex-txt { background: #6e40c9; color: #ffffff; }
#ex-txt:hover { background: #8957e5; }

#ex-cancel { background: #21262d; color: #8b949e; }
#ex-cancel:hover { background: #30363d; }

/* ── Resume Modal ──────────────────────────────────── */

ResumeModal {
    align: center middle;
}

#resume-box {
    width: 56;
    height: auto;
    background: #161b22;
    border: solid #30363d;
    padding: 2 3;
}

#resume-modal-title {
    text-align: center;
    color: #58a6ff;
    text-style: bold;
    height: 2;
    margin-bottom: 1;
}

#resume-preview {
    height: auto;
    min-height: 4;
    background: #0d1117;
    border: solid #21262d;
    padding: 1;
    margin-top: 1;
    color: #8b949e;
}

#resume-top-actions {
    height: auto;
    margin-top: 1;
}

#resume-bot-actions {
    height: auto;
    margin-top: 1;
}

.rm-btn {
    margin-right: 1;
    border: none;
}

#btn-rmbrowse { background: #21262d; color: #8b949e; }
#btn-rmbrowse:hover { background: #30363d; }

#btn-rmparse { background: #1f6feb; color: #ffffff; }
#btn-rmparse:hover { background: #388bfd; }

#btn-rmuse { background: #238636; color: #ffffff; }
#btn-rmuse:hover { background: #2ea043; }

#btn-rmcancel { background: #21262d; color: #8b949e; }
#btn-rmcancel:hover { background: #30363d; }
"""


class JobItem(ListItem):
    def __init__(self, job: Job, index: int, is_fav: bool = False) -> None:
        super().__init__()
        self._job = job
        self._index = index
        self._is_fav = is_fav

    def compose(self) -> ComposeResult:
        j = self._job
        fav = "  [bold yellow]★[/bold yellow]" if self._is_fav else ""
        score = j.relevance_score
        sc = "#3fb950" if score >= 5 else "#e3b341" if score >= 2 else "#484f58"

        cv_badge = ""
        if j.cv_match_score > 0:
            pct = int(j.cv_match_score)
            cc = "#3fb950" if pct >= 70 else "#e3b341" if pct >= 40 else "#484f58"
            cv_badge = f"  [{cc}][CV {pct}%][/{cc}]"

        _SRC_COLORS = {"gupy": "#3fb950", "linkedin": "#0a66c2"}
        src_color = _SRC_COLORS.get(j.source, "#79c0ff")

        line1 = (
            f"[bold #8b949e]#{self._index}[/bold #8b949e]  "
            f"[bold #e6edf3]{j.title}[/bold #e6edf3]"
            f"  [{sc}]↑{score:.1f}[/{sc}]{cv_badge}{fav}"
        )

        meta = f"[#d2a8ff]{j.company}[/#d2a8ff]  [#484f58]·[/#484f58]  [#8b949e]{j.location}[/#8b949e]"
        if j.salary:
            meta += f"  [#484f58]·[/#484f58]  [#3fb950]{j.salary}[/#3fb950]"
        if j.published_at:
            pub = j.published_at
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            days = (datetime.now(timezone.utc) - pub).days
            age = f"  [#484f58]· {days}d ago[/#484f58]" if days > 0 else "  [#484f58]· today[/#484f58]"
            meta += age

        tags = "  ".join(f"[#e3b341]{t}[/#e3b341]" for t in j.tags[:5])
        src_badge = f"[{src_color}][{j.source}][/{src_color}]"
        line3 = f"{tags}  {src_badge}" if tags else src_badge

        yield Static(f"{line1}\n{meta}\n{line3}")

    @property
    def job(self) -> Job:
        return self._job


class JobDetailModal(ModalScreen[bool]):
    BINDINGS = [("escape", "close_modal", "Close")]

    def __init__(self, job: Job, is_fav: bool) -> None:
        super().__init__()
        self._job = job
        self._is_fav = is_fav

    def compose(self) -> ComposeResult:
        j = self._job

        pub_str = ""
        if j.published_at:
            pub = j.published_at
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            days = (datetime.now(timezone.utc) - pub).days
            pub_str = f"  ·  {days}d ago" if days > 0 else "  ·  today"

        sal_str = j.salary or "Salary not disclosed"
        tags_str = "  ".join(j.tags) if j.tags else "—"
        desc_str = (j.description or "No description available.").strip()
        fav_label = "★ Unfavorite" if self._is_fav else "☆ Favorite"

        with VerticalScroll(id="modal-box"):
            yield Static(j.title, id="m-title")
            yield Static(j.company, id="m-company")
            yield Static(f"{j.location}{pub_str}", id="m-location")
            yield Static(sal_str, id="m-salary")
            yield Static(f"via {j.source}", id="m-source")
            yield Rule()
            yield Static(f"Tags: {tags_str}", id="m-tags")
            yield Rule()
            yield Static(desc_str, id="m-desc")
            yield Static(f"URL: {j.url}", id="m-url")
            with Horizontal(id="m-actions"):
                yield Button(fav_label, id="btn-fav", classes="m-btn")
                yield Button("Open in Browser", id="btn-browser", classes="m-btn")
                yield Button("Close  [Esc]", id="btn-mclose", classes="m-btn")

    def action_close_modal(self) -> None:
        self.dismiss(False)

    @on(Button.Pressed, "#btn-mclose")
    def on_close(self) -> None:
        self.dismiss(False)

    @on(Button.Pressed, "#btn-browser")
    def on_browser(self) -> None:
        webbrowser.open(self._job.url)
        self.app.notify("Opened in browser", severity="information")

    @on(Button.Pressed, "#btn-fav")
    def on_fav(self) -> None:
        self.dismiss(True)


class ExportModal(ModalScreen[Optional[str]]):
    BINDINGS = [("escape", "close_modal", "Close")]

    def compose(self) -> ComposeResult:
        with Vertical(id="export-box"):
            yield Static("Export Results", id="export-title")
            yield Button("JSON", id="ex-json", classes="ex-btn")
            yield Button("CSV", id="ex-csv", classes="ex-btn")
            yield Button("TXT", id="ex-txt", classes="ex-btn")
            yield Button("Cancel", id="ex-cancel", classes="ex-btn")

    def action_close_modal(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed)
    def on_button(self, event: Button.Pressed) -> None:
        mapping = {"ex-json": "JSON", "ex-csv": "CSV", "ex-txt": "TXT"}
        self.dismiss(mapping.get(str(event.button.id)))


class ResumeModal(ModalScreen["Optional[ResumeData]"]):
    BINDINGS = [("escape", "close_modal", "Close")]

    def __init__(self) -> None:
        super().__init__()
        self._parsed: Optional[ResumeData] = None

    def compose(self) -> ComposeResult:
        with Vertical(id="resume-box"):
            yield Static("Import Resume (PDF)", id="resume-modal-title")
            yield Label("PDF file path", classes="s-label")
            yield Input(placeholder="/path/to/resume.pdf", id="resume-path")
            with Horizontal(id="resume-top-actions"):
                yield Button("Browse", id="btn-rmbrowse", classes="rm-btn")
                yield Button("Parse PDF", id="btn-rmparse", classes="rm-btn")
            yield Static("", id="resume-preview")
            with Horizontal(id="resume-bot-actions"):
                yield Button("✓ Use this resume", id="btn-rmuse", classes="rm-btn", disabled=True)
                yield Button("Cancel", id="btn-rmcancel", classes="rm-btn")

    def action_close_modal(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#btn-rmcancel")
    def on_cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#btn-rmbrowse")
    def on_browse(self) -> None:
        import os
        home = Path.home()
        try:
            os.startfile(str(home))
        except Exception:
            pass
        self.app.notify(
            f"Explorer aberto em {home}  —  copie o caminho do PDF e cole acima",
            severity="information",
        )

    def _set_path(self, path: str) -> None:
        self.query_one("#resume-path", Input).value = path

    @on(Button.Pressed, "#btn-rmparse")
    def on_parse(self) -> None:
        path_str = self.query_one("#resume-path", Input).value.strip()
        if not path_str:
            self.app.notify("Enter a file path first", severity="warning")
            return
        path = Path(path_str)
        if not path.exists():
            self.app.notify(f"File not found: {path_str}", severity="error")
            return
        self._parse_worker(path)

    @work(thread=True)
    def _parse_worker(self, path: Path) -> None:
        try:
            data = ResumeService().parse(path)
            self.app.call_from_thread(self._on_parsed, data)
        except FileNotFoundError:
            self.app.call_from_thread(
                self.app.notify, "Arquivo não encontrado. Verifique o caminho.", severity="error"
            )
        except ValueError as e:
            self.app.call_from_thread(self.app.notify, str(e), severity="warning")
        except Exception as e:
            self.app.call_from_thread(
                self.app.notify, f"Erro ao ler PDF: {e}", severity="error"
            )

    def _on_parsed(self, data: ResumeData) -> None:
        self._parsed = data
        techs = ", ".join(data.technologies[:8]) or "none detected"
        kws = ", ".join(data.keywords[:5]) or "—"
        preview = (
            f"[#3fb950]✓ Parsed successfully[/#3fb950]\n"
            f"[#8b949e]Tech:[/#8b949e] [#e3b341]{techs}[/#e3b341]\n"
            f"[#8b949e]Keywords:[/#8b949e] [#c9d1d9]{kws}[/#c9d1d9]\n"
            f"[#8b949e]Seniority:[/#8b949e] [#58a6ff]{data.seniority.value}[/#58a6ff]"
        )
        self.query_one("#resume-preview", Static).update(preview)
        self.query_one("#btn-rmuse", Button).disabled = False

    @on(Button.Pressed, "#btn-rmuse")
    def on_use(self) -> None:
        self.dismiss(self._parsed)


class GuigoTUI(App[None]):
    TITLE = "Guigo — Remote Job Hunter"
    CSS = _CSS

    BINDINGS = [
        Binding("ctrl+s", "do_search", "Search"),
        Binding("r", "do_resume", "Resume"),
        Binding("e", "do_export", "Export"),
        Binding("f2", "show_results", "Results"),
        Binding("f3", "show_favs", "Favorites"),
        Binding("f4", "show_hist", "History"),
        Binding("q", "quit", "Quit", priority=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._search_svc = SearchService()
        self._favorites = FavoritesStorage()
        self._history = HistoryStorage()
        self._export_svc = ExportService()
        self._jobs: list[Job] = []
        self._region: str = "global"  # "global" | "brazil" | "both"
        self._resume: Optional[ResumeData] = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-layout"):
            with Vertical(id="sidebar"):
                yield Static("⬡  G U I G O", id="logo")
                yield Label("Resume", classes="s-label")
                with Horizontal(id="resume-row"):
                    yield Static("[#484f58]✗ No resume[/#484f58]", id="resume-status")
                    yield Button("⊕", id="btn-resume", classes="resume-btn")
                yield Label("Keywords", classes="s-label")
                yield Input(placeholder="python, backend", id="in-kw")
                yield Label("Technologies", classes="s-label")
                yield Input(placeholder="react, fastapi", id="in-tech")
                yield Label("Seniority", classes="s-label")
                yield RadioSet(
                    RadioButton("Junior", value=True),
                    RadioButton("Mid"),
                    RadioButton("Senior"),
                    RadioButton("Any"),
                    id="in-sen",
                )
                yield Label("Remote only", classes="s-label")
                yield Switch(value=True, id="in-remote")
                yield Label("Max days old", classes="s-label")
                yield Input(placeholder="30", value="30", id="in-days")
                yield Label("Region", classes="s-label")
                with Horizontal(id="country-row"):
                    yield Button("🌐 Global", id="btn-region-global", classes="region-btn -active-region")
                    yield Button("🇧🇷 Brasil", id="btn-region-brazil", classes="region-btn")
                    yield Button("⊕ Both", id="btn-region-both", classes="region-btn")
                yield Label("Sources", classes="s-label", id="sources-label")
                yield Static(self._sources_text(), id="sources-info")
                yield Button("⌕  SEARCH", id="btn-search")
            with Vertical(id="content"):
                yield Static("[#484f58]Ready — set filters and search[/#484f58]", id="status")
                with TabbedContent(id="tabs"):
                    with TabPane("Results", id="tab-results"):
                        yield ListView(id="job-list")
                    with TabPane("Favorites", id="tab-favs"):
                        yield ListView(id="fav-list")
                    with TabPane("History", id="tab-hist"):
                        yield DataTable(id="hist-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#hist-table", DataTable)
        table.add_columns("Date", "Keywords", "Seniority", "Region", "Results")
        table.cursor_type = "row"
        self.query_one("#in-kw", Input).focus()

    # ── Region ─────────────────────────────────────────────────────────────

    def _sources_text(self) -> str:
        intl = []
        if settings.enable_remoteok:
            intl.append("remoteok")
        if settings.enable_remotive:
            intl.append("remotive")
        if settings.enable_arbeitnow:
            intl.append("arbeitnow")
        if settings.enable_themuse:
            intl.append("themuse")
        if settings.enable_linkedin:
            intl.append("linkedin")

        br = ["gupy"] if settings.enable_gupy else []

        if self._region == "brazil":
            active = br
        elif self._region == "global":
            active = intl
        else:
            active = intl + br

        return "  ".join(f"[#30363d]{s}[/#30363d]" for s in active) or "[#484f58]none[/#484f58]"

    def _set_region(self, region: str) -> None:
        self._region = region
        self.query_one("#sources-info", Static).update(self._sources_text())

        for btn_id, label, reg in [
            ("btn-region-global", "🌐 Global", "global"),
            ("btn-region-brazil", "🇧🇷 Brasil", "brazil"),
            ("btn-region-both", "⊕ Both", "both"),
        ]:
            btn = self.query_one(f"#{btn_id}", Button)
            btn.label = label
            if reg == region:
                btn.add_class("-active-region")
            else:
                btn.remove_class("-active-region")

    def _build_providers(self):
        from app.providers.arbeitnow import ArbeitnowProvider
        from app.providers.gupy import GupyProvider
        from app.providers.linkedin import LinkedInProvider
        from app.providers.remoteok import RemoteOKProvider
        from app.providers.remotive import RemotiveProvider
        from app.providers.themuse import TheMuseProvider

        intl = []
        if settings.enable_remoteok:
            intl.append(RemoteOKProvider())
        if settings.enable_remotive:
            intl.append(RemotiveProvider())
        if settings.enable_arbeitnow:
            intl.append(ArbeitnowProvider())
        if settings.enable_themuse:
            intl.append(TheMuseProvider())
        if settings.enable_linkedin:
            intl.append(LinkedInProvider())

        br = [GupyProvider()] if settings.enable_gupy else []

        if self._region == "brazil":
            return br
        elif self._region == "global":
            return intl
        return intl + br

    @on(Button.Pressed, "#btn-region-global")
    def on_region_global(self) -> None:
        self._set_region("global")

    @on(Button.Pressed, "#btn-region-brazil")
    def on_region_brazil(self) -> None:
        self._set_region("brazil")

    @on(Button.Pressed, "#btn-region-both")
    def on_region_both(self) -> None:
        self._set_region("both")

    # ── Helpers ────────────────────────────────────────────────────────────

    def _set_status(self, markup: str) -> None:
        self.query_one("#status", Static).update(markup)

    def _get_filters(self) -> SearchFilters:
        kw_raw = self.query_one("#in-kw", Input).value
        tech_raw = self.query_one("#in-tech", Input).value
        remote = self.query_one("#in-remote", Switch).value
        days_raw = self.query_one("#in-days", Input).value

        _SEN_OPTIONS = [SeniorityLevel.JUNIOR, SeniorityLevel.MID, SeniorityLevel.SENIOR, SeniorityLevel.ANY]
        pressed = self.query_one("#in-sen", RadioSet).pressed_index
        seniority = _SEN_OPTIONS[pressed] if pressed is not None else SeniorityLevel.JUNIOR

        return SearchFilters(
            keywords=[k.strip() for k in kw_raw.split(",") if k.strip()],
            technologies=[t.strip() for t in tech_raw.split(",") if t.strip()],
            seniority=seniority,
            remote_only=remote,
            max_days_old=int(days_raw) if days_raw.strip().isdigit() else None,
        )

    def _populate_job_list(self, selector: str, jobs: list[Job]) -> None:
        lv = self.query_one(selector, ListView)
        lv.clear()
        fav_ids = {j.id for j in self._favorites.all()}
        for i, job in enumerate(jobs, 1):
            lv.append(JobItem(job, i, is_fav=job.id in fav_ids))

    def _refresh_fav_list(self) -> None:
        lv = self.query_one("#fav-list", ListView)
        lv.clear()
        for i, job in enumerate(self._favorites.all(), 1):
            lv.append(JobItem(job, i, is_fav=True))

    def _refresh_hist_table(self) -> None:
        table = self.query_one("#hist-table", DataTable)
        table.clear()
        region_icons = {"global": "🌐", "brazil": "🇧🇷", "both": "⊕"}
        for rec in self._history.all()[:50]:
            kw = ", ".join(rec.filters.keywords + rec.filters.technologies) or "—"
            table.add_row(
                rec.timestamp.strftime("%m/%d %H:%M"),
                kw[:35],
                rec.filters.seniority.value,
                region_icons.get(getattr(rec.filters, "region", "global"), "🌐"),
                str(rec.results_count),
            )

    def _open_detail(self, job: Job) -> None:
        is_fav = self._favorites.is_favorite(job.id)
        self.push_screen(
            JobDetailModal(job, is_fav),
            callback=lambda changed: self._on_detail_close(job, changed),
        )

    def _on_detail_close(self, job: Job, fav_changed: bool) -> None:
        if fav_changed:
            is_now_fav = self._favorites.toggle(job)
            self.notify("Added to favorites ★" if is_now_fav else "Removed from favorites")
            self._populate_job_list("#job-list", self._jobs)
            self._refresh_fav_list()

    # ── Search ─────────────────────────────────────────────────────────────

    @on(Button.Pressed, "#btn-search")
    def on_search_btn(self) -> None:
        self._start_search()

    def action_do_search(self) -> None:
        self._start_search()

    def _start_search(self) -> None:
        filters = self._get_filters()
        providers = self._build_providers()
        if not providers:
            self.notify("No providers active for selected region.", severity="warning")
            return
        region_label = {"global": "🌐 Global", "brazil": "🇧🇷 Brasil", "both": "⊕ Both"}[self._region]
        self._set_status(f"[#58a6ff]⟳ Searching {region_label}...[/#58a6ff]")
        self._search_worker(filters, providers)

    @work(thread=True, exclusive=True)
    def _search_worker(self, filters: SearchFilters, providers: list) -> None:
        from app.services.search import SearchService
        svc = SearchService(providers=providers)
        jobs = svc.search(filters)

        if self._resume:
            resume_svc = ResumeService()
            for job in jobs:
                job.cv_match_score = resume_svc.score_job(job, self._resume)

        self._history.add(filters, len(jobs))
        self.call_from_thread(self._on_search_done, jobs)

    def _on_search_done(self, jobs: list[Job]) -> None:
        self._jobs = jobs
        self._populate_job_list("#job-list", jobs)
        self._refresh_hist_table()
        self.query_one("#tabs", TabbedContent).active = "tab-results"

        region_label = {"global": "🌐 Global", "brazil": "🇧🇷 Brasil", "both": "⊕ Both"}[self._region]
        cv_hint = "  [#6e40c9]· CV match active[/#6e40c9]" if self._resume else ""

        if jobs:
            self._set_status(
                f"[#3fb950]{len(jobs)} jobs found[/#3fb950]"
                f"  [#484f58]· {region_label} · ranked by relevance[/#484f58]"
                f"{cv_hint}"
            )
            self.notify(f"Found {len(jobs)} jobs", severity="information")
        else:
            self._set_status(
                f"[#f85149]No jobs found[/#f85149]"
                f"  [#484f58]· {region_label} · try broader filters[/#484f58]"
            )
            self.notify("No jobs found", severity="warning")

    # ── Job selection ──────────────────────────────────────────────────────

    @on(ListView.Selected, "#job-list")
    def on_job_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, JobItem):
            self._open_detail(event.item.job)

    @on(ListView.Selected, "#fav-list")
    def on_fav_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, JobItem):
            self._open_detail(event.item.job)

    # ── Tab navigation ─────────────────────────────────────────────────────

    def action_show_results(self) -> None:
        self.query_one("#tabs", TabbedContent).active = "tab-results"

    def action_show_favs(self) -> None:
        self._refresh_fav_list()
        self.query_one("#tabs", TabbedContent).active = "tab-favs"

    def action_show_hist(self) -> None:
        self._refresh_hist_table()
        self.query_one("#tabs", TabbedContent).active = "tab-hist"

    # ── Export ─────────────────────────────────────────────────────────────

    def action_do_export(self) -> None:
        if not self._jobs:
            self.notify("No results to export. Run a search first.", severity="warning")
            return
        self.push_screen(ExportModal(), callback=self._on_export_choice)

    def _on_export_choice(self, fmt: Optional[str]) -> None:
        if not fmt:
            return
        try:
            svc = self._export_svc
            path = (
                svc.to_json(self._jobs) if fmt == "JSON"
                else svc.to_csv(self._jobs) if fmt == "CSV"
                else svc.to_txt(self._jobs)
            )
            self.notify(f"Exported {len(self._jobs)} jobs → {path.name}", severity="information")
        except Exception as e:
            self.notify(f"Export failed: {e}", severity="error")

    # ── Resume ─────────────────────────────────────────────────────────────

    def action_do_resume(self) -> None:
        self.push_screen(ResumeModal(), callback=self._on_resume_imported)

    @on(Button.Pressed, "#btn-resume")
    def on_resume_btn(self) -> None:
        self.push_screen(ResumeModal(), callback=self._on_resume_imported)

    def _on_resume_imported(self, data: Optional[ResumeData]) -> None:
        if data is None:
            return
        self._resume = data

        if data.technologies:
            self.query_one("#in-tech", Input).value = ", ".join(data.technologies[:6])
        if data.keywords:
            self.query_one("#in-kw", Input).value = ", ".join(data.keywords[:3])

        _SEN_OPTIONS = [SeniorityLevel.JUNIOR, SeniorityLevel.MID, SeniorityLevel.SENIOR, SeniorityLevel.ANY]
        sen_idx = _SEN_OPTIONS.index(data.seniority) if data.seniority in _SEN_OPTIONS else 3
        buttons = list(self.query_one("#in-sen", RadioSet).query(RadioButton))
        if 0 <= sen_idx < len(buttons):
            buttons[sen_idx].value = True

        self.query_one("#resume-status", Static).update(
            f"[#3fb950]✓ {data.path.name}[/#3fb950]"
        )
        self.notify(
            f"Resume loaded — {len(data.technologies)} technologies, seniority: {data.seniority.value}",
            severity="information",
        )
