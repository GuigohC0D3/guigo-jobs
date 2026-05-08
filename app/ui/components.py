from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from app.models.job import Job
from app.ui.theme import GUIGO_THEME, LOGO, LOGO_COMPACT


console = Console(theme=GUIGO_THEME)


def print_logo(compact: bool = False) -> None:
    if compact:
        console.print(LOGO_COMPACT)
    else:
        console.print(LOGO)


def print_rule(title: str = "") -> None:
    console.print(Rule(f"[primary]{title}[/primary]" if title else "", style="#1F2937"))


def job_card(job: Job, index: int, show_description: bool = False) -> Panel:
    title_line = Text()
    title_line.append(f"[{index}] ", style="muted")
    title_line.append(job.title, style="highlight bold")

    if job.favorited:
        title_line.append("  ★", style="accent")

    meta = Text()
    meta.append(f"  {job.company}", style="company")
    meta.append("  ·  ", style="muted")
    meta.append(job.location, style="muted")

    if job.salary:
        meta.append("  ·  ", style="muted")
        meta.append(job.salary, style="salary")

    if job.published_at:
        pub = job.published_at
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        days = (datetime.now(timezone.utc) - pub).days
        age = f"{days}d ago" if days > 0 else "today"
        meta.append(f"  ·  {age}", style="muted")

    source_text = Text(f"  [{job.source}]", style="source")

    content = Text.assemble(title_line, "\n", meta, "\n", source_text)

    if job.tags:
        tag_line = Text("\n  ")
        for tag in job.tags[:6]:
            tag_line.append(f" {tag} ", style="tag on #1F2937")
            tag_line.append(" ", style="")
        content = Text.assemble(content, tag_line)

    if show_description and job.description:
        desc = job.description[:300].strip()
        content = Text.assemble(content, f"\n\n  {desc}", style="muted")

    score_color = "success" if job.relevance_score >= 5 else "accent" if job.relevance_score >= 2 else "muted"
    border_style = "success" if job.relevance_score >= 5 else "#374151"

    return Panel(
        content,
        border_style=border_style,
        subtitle=f"[{score_color}]score: {job.relevance_score:.1f}[/{score_color}]",
        subtitle_align="right",
        padding=(0, 1),
    )


def jobs_table(jobs: list[Job], page: int = 1, per_page: int = 10) -> Table:
    table = Table(
        show_header=True,
        header_style="primary",
        border_style="#374151",
        row_styles=["", "on #111827"],
        expand=True,
    )
    table.add_column("#", style="muted", width=4, justify="right")
    table.add_column("Title", style="highlight", min_width=25)
    table.add_column("Company", style="company", min_width=15)
    table.add_column("Location", style="muted", min_width=12)
    table.add_column("Salary", style="salary", min_width=12)
    table.add_column("Posted", style="muted", width=10)
    table.add_column("Score", style="accent", width=7, justify="right")
    table.add_column("Source", style="source", width=10)

    start = (page - 1) * per_page
    for i, job in enumerate(jobs[start : start + per_page], start + 1):
        posted = ""
        if job.published_at:
            pub = job.published_at
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            days = (datetime.now(timezone.utc) - pub).days
            posted = f"{days}d" if days > 0 else "today"

        table.add_row(
            str(i),
            job.title[:45],
            job.company[:20],
            job.location[:15],
            job.salary or "—",
            posted,
            f"{job.relevance_score:.1f}",
            job.source,
        )

    return table


def pagination_bar(current: int, total_pages: int, total_jobs: int) -> str:
    parts = []
    if current > 1:
        parts.append("[muted]← prev[/muted]")
    parts.append(f"[primary]Page {current}/{total_pages}[/primary]")
    if current < total_pages:
        parts.append("[muted]next →[/muted]")
    parts.append(f"[muted]({total_jobs} jobs)[/muted]")
    return "  ".join(parts)


def status_bar(message: str, style: str = "muted") -> None:
    console.print(f"[{style}]{message}[/{style}]")
