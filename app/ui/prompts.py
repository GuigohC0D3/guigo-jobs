from __future__ import annotations

from typing import Any, Optional

import questionary
from questionary import Style

GUIGO_STYLE = Style([
    ("qmark", "fg:#00D4FF bold"),
    ("question", "fg:#FFFFFF bold"),
    ("answer", "fg:#00D4FF bold"),
    ("pointer", "fg:#F59E0B bold"),
    ("highlighted", "fg:#F59E0B bold"),
    ("selected", "fg:#10B981"),
    ("separator", "fg:#6B7280"),
    ("instruction", "fg:#6B7280"),
    ("text", "fg:#D1D5DB"),
    ("disabled", "fg:#374151 italic"),
])


def ask_text(message: str, default: str = "") -> str:
    return questionary.text(message, default=default, style=GUIGO_STYLE).ask() or default


def ask_confirm(message: str, default: bool = True) -> bool:
    result = questionary.confirm(message, default=default, style=GUIGO_STYLE).ask()
    return result if result is not None else default


def ask_select(message: str, choices: list[str]) -> Optional[str]:
    return questionary.select(message, choices=choices, style=GUIGO_STYLE).ask()


def ask_checkbox(message: str, choices: list[str]) -> list[str]:
    result = questionary.checkbox(message, choices=choices, style=GUIGO_STYLE).ask()
    return result or []


def ask_search_filters() -> dict[str, Any]:
    from app.models.job import ContractType, SearchFilters, SeniorityLevel

    print()
    keywords_raw = ask_text("Keywords (comma-separated, e.g. python,backend):", "")
    keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]

    tech_raw = ask_text("Technologies (comma-separated, e.g. react,fastapi):", "")
    technologies = [t.strip() for t in tech_raw.split(",") if t.strip()]

    seniority_choice = ask_select(
        "Seniority level:",
        ["junior", "mid", "senior", "any"],
    ) or "junior"

    remote_only = ask_confirm("Remote only?", default=True)

    contract_choice = ask_select(
        "Contract type:",
        ["any", "full_time", "part_time", "contract", "freelance", "internship"],
    ) or "any"

    days_raw = ask_text("Max days old (leave blank = no limit):", "30")
    max_days = int(days_raw) if days_raw.strip().isdigit() else None

    limit_raw = ask_text("Max results per provider:", "50")
    limit = int(limit_raw) if limit_raw.strip().isdigit() else 50

    return {
        "keywords": keywords,
        "technologies": technologies,
        "seniority": SeniorityLevel(seniority_choice),
        "remote_only": remote_only,
        "contract_type": ContractType(contract_choice),
        "max_days_old": max_days,
        "limit": limit,
    }


def ask_job_action(job_title: str) -> Optional[str]:
    return ask_select(
        f"Action for: {job_title[:50]}",
        [
            "Open in browser",
            "Toggle favorite",
            "View description",
            "Back",
        ],
    )


def ask_main_menu() -> Optional[str]:
    return ask_select(
        "What do you want to do?",
        [
            "Search jobs",
            "View favorites",
            "Search history",
            "Export results",
            "Clear cache",
            "Quit",
        ],
    )


def ask_export_format() -> Optional[str]:
    return ask_select("Export format:", ["JSON", "CSV", "TXT"])


def ask_pagination_action(current_page: int, total_pages: int) -> Optional[str]:
    choices = []
    if current_page > 1:
        choices.append("← Previous page")
    if current_page < total_pages:
        choices.append("→ Next page")
    choices += ["Select a job", "Back to menu"]
    return ask_select(f"Page {current_page}/{total_pages}", choices)


def ask_job_number(max_num: int) -> Optional[int]:
    raw = ask_text(f"Job number (1-{max_num}):", "")
    if raw.strip().isdigit():
        val = int(raw.strip())
        if 1 <= val <= max_num:
            return val
    return None
