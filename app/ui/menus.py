from __future__ import annotations

import webbrowser
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from app.models.job import Job, SearchFilters
from app.services.export import ExportService
from app.services.search import SearchService
from app.storage.favorites import FavoritesStorage
from app.storage.history import HistoryStorage
from app.ui.components import console, job_card, jobs_table, pagination_bar, print_logo, print_rule
from app.ui.prompts import (
    ask_confirm,
    ask_export_format,
    ask_job_action,
    ask_job_number,
    ask_main_menu,
    ask_pagination_action,
    ask_search_filters,
)

_PER_PAGE = 10


class GuigoApp:
    def __init__(self) -> None:
        self._search_service = SearchService()
        self._favorites = FavoritesStorage()
        self._history = HistoryStorage()
        self._export_service = ExportService()
        self._current_jobs: list[Job] = []
        self._current_filters: Optional[SearchFilters] = None

    def run(self) -> None:
        print_logo()
        while True:
            choice = ask_main_menu()
            if not choice or choice == "Quit":
                console.print("\n[muted]Bye! Happy job hunting. 🚀[/muted]\n")
                break
            elif choice == "Search jobs":
                self._flow_search()
            elif choice == "View favorites":
                self._flow_favorites()
            elif choice == "Search history":
                self._flow_history()
            elif choice == "Export results":
                self._flow_export()
            elif choice == "Clear cache":
                self._flow_clear_cache()

    def _flow_search(self) -> None:
        print_rule("New Search")
        raw = ask_search_filters()
        filters = SearchFilters(**raw)

        provider_count = len(self._search_service._providers)
        progress = Progress(
            SpinnerColumn(style="primary"),
            TextColumn("[primary]{task.description}[/primary]"),
            BarColumn(bar_width=30, style="secondary", complete_style="primary"),
            MofNCompleteColumn(),
            transient=True,
        )

        with progress:
            task = progress.add_task("Fetching jobs...", total=provider_count)

            def on_done(provider_name: str, count: int) -> None:
                progress.advance(task)
                progress.update(task, description=f"[muted]{provider_name}[/muted] → {count} jobs")

            jobs = self._search_service.search_with_progress(filters, on_provider_done=on_done)

        self._current_jobs = jobs
        self._current_filters = filters
        self._history.add(filters, len(jobs))

        if not jobs:
            console.print("\n[danger]No jobs found.[/danger] Try broader keywords.\n")
            return

        console.print(f"\n[success]Found {len(jobs)} jobs[/success] [muted](ranked by relevance)[/muted]\n")
        self._flow_results(jobs)

    def _flow_results(self, jobs: list[Job]) -> None:
        page = 1
        total_pages = max(1, (len(jobs) + _PER_PAGE - 1) // _PER_PAGE)

        while True:
            console.print()
            console.print(jobs_table(jobs, page=page, per_page=_PER_PAGE))
            console.print(pagination_bar(page, total_pages, len(jobs)))
            console.print()

            action = ask_pagination_action(page, total_pages)
            if not action or action == "Back to menu":
                break
            elif action == "← Previous page" and page > 1:
                page -= 1
            elif action == "→ Next page" and page < total_pages:
                page += 1
            elif action == "Select a job":
                num = ask_job_number(min(len(jobs), page * _PER_PAGE))
                if num:
                    self._flow_job_detail(jobs[num - 1])

    def _flow_job_detail(self, job: Job) -> None:
        job.favorited = self._favorites.is_favorite(job.id)
        while True:
            console.print()
            console.print(job_card(job, index=0, show_description=True))
            console.print(f"\n[muted]URL:[/muted] {job.url}\n")

            action = ask_job_action(job.title)
            if not action or action == "Back":
                break
            elif action == "Open in browser":
                webbrowser.open(job.url)
                console.print("[success]Opened in browser.[/success]")
            elif action == "Toggle favorite":
                is_fav = self._favorites.toggle(job)
                job.favorited = is_fav
                status = "[accent]★ Added to favorites[/accent]" if is_fav else "[muted]Removed from favorites[/muted]"
                console.print(status)
            elif action == "View description":
                desc = job.description or "[muted]No description available.[/muted]"
                console.print(Panel(desc, title="Description", border_style="#374151", padding=(1, 2)))

    def _flow_favorites(self) -> None:
        print_rule("Favorites")
        jobs = self._favorites.all()
        if not jobs:
            console.print("[muted]No favorites yet. Search and star jobs to save them.[/muted]\n")
            return
        console.print(f"[success]{len(jobs)} saved jobs[/success]\n")
        self._flow_results(jobs)

    def _flow_history(self) -> None:
        print_rule("Search History")
        records = self._history.all()
        if not records:
            console.print("[muted]No searches yet.[/muted]\n")
            return

        table = Table(show_header=True, header_style="primary", border_style="#374151", expand=True)
        table.add_column("Date", style="muted", width=18)
        table.add_column("Keywords", style="highlight")
        table.add_column("Seniority", style="company", width=10)
        table.add_column("Results", style="success", width=9, justify="right")

        for record in records[:20]:
            kw = ", ".join(record.filters.keywords + record.filters.technologies) or "—"
            table.add_row(
                record.timestamp.strftime("%Y-%m-%d %H:%M"),
                kw[:40],
                record.filters.seniority.value,
                str(record.results_count),
            )

        console.print(table)
        console.print()

        if ask_confirm("Clear history?", default=False):
            self._history.clear()
            console.print("[success]History cleared.[/success]\n")

    def _flow_export(self) -> None:
        if not self._current_jobs:
            console.print("[muted]No results to export. Run a search first.[/muted]\n")
            return

        print_rule("Export")
        fmt = ask_export_format()
        if not fmt:
            return

        try:
            if fmt == "JSON":
                path = self._export_service.to_json(self._current_jobs)
            elif fmt == "CSV":
                path = self._export_service.to_csv(self._current_jobs)
            else:
                path = self._export_service.to_txt(self._current_jobs)

            console.print(f"\n[success]Exported {len(self._current_jobs)} jobs →[/success] [highlight]{path}[/highlight]\n")
        except Exception as e:
            console.print(f"[danger]Export failed: {e}[/danger]\n")

    def _flow_clear_cache(self) -> None:
        if ask_confirm("Clear all cached results?", default=False):
            from app.utils.cache import FileCache
            cache = FileCache()
            cache._dir = cache._dir.parent
            import shutil
            shutil.rmtree(str(cache._dir / "remoteok"), ignore_errors=True)
            shutil.rmtree(str(cache._dir / "remotive"), ignore_errors=True)
            shutil.rmtree(str(cache._dir / "arbeitnow"), ignore_errors=True)
            shutil.rmtree(str(cache._dir / "themuse"), ignore_errors=True)
            console.print("[success]Cache cleared.[/success]\n")
