# Design: Resume Import, LinkedIn Provider & TUI Redesign

**Date:** 2026-05-08  
**Status:** Approved

---

## Overview

Three interconnected features for the Guigo remote job hunter TUI:

1. **Resume import (PDF)** — parses the user's CV, pre-fills search filters, and adds a CV match score to every job card.
2. **LinkedIn provider** — fetches jobs from LinkedIn's public guest API endpoint (no auth).
3. **TUI redesign** — fixes the Gupy/Select navigation bug at its root, improves keyboard UX, adds resume status to sidebar, and enriches job cards visually.

---

## Architecture

### New files

| File | Responsibility |
|---|---|
| `app/services/resume.py` | PDF parsing, skill extraction, CV match scoring |
| `app/providers/linkedin.py` | LinkedIn Jobs public API provider |

### Modified files

| File | Change |
|---|---|
| `app/models/job.py` | Add `cv_match_score: float = 0.0` field |
| `app/core/config.py` | Add `enable_linkedin: bool = True` toggle |
| `app/ui/tui/app.py` | Full TUI redesign (see below) |
| `requirements.txt` | Add `pypdf>=4.0` |

### Data flow

```
[PDF path] ──→ ResumeService.parse() ──→ ResumeData
                                              │
                                    pre-fills sidebar filters
                                              │
                              SearchService.search() ──→ [Job, ...]
                                              │
                    ResumeService.score_job(job, resume) ──→ cv_match_score
                                              │
                                   JobItem renders CV badge
```

---

## ResumeService (`app/services/resume.py`)

### ResumeData dataclass

```python
@dataclass
class ResumeData:
    path: Path
    technologies: list[str]   # e.g. ["python", "fastapi", "postgres"]
    keywords: list[str]        # e.g. ["backend", "api", "microservices"]
    seniority: SeniorityLevel
    raw_text: str
```

### parse(path: Path) -> ResumeData

1. Open PDF with `pypdf.PdfReader`, concatenate text from all pages.
2. **Technology extraction:** regex `\b<term>\b` (case-insensitive) against a curated dict of ~120 terms grouped by category (languages, frameworks, cloud, databases, tools). Returns matched terms.
3. **Seniority extraction:** scan for terms (`senior`, `sr.`, `lead`, `júnior`, `jr`, `estágio`, `trainee`, `entry`). Maps to `SeniorityLevel`. Defaults to `ANY` if ambiguous.
4. **Keyword extraction:** tokenize text, remove stopwords (pt + en), take top-10 by frequency.

### score_job(job: Job, resume: ResumeData) -> float

```
score = (len(common_techs) / max(len(resume.technologies), 1)) * 70
      + (len(common_keywords) / max(len(resume.keywords), 1)) * 30
```

Returns 0.0–100.0, rounded to 1 decimal. Stored in `job.cv_match_score`.

---

## LinkedInProvider (`app/providers/linkedin.py`)

### Endpoint

```
GET https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search
Params: keywords, location="Remote", start=0|25, f_WT=2
```

No authentication required. Returns HTML.

### HTML parsing

Uses stdlib `html.parser` — no BeautifulSoup dependency.

| Element | CSS selector | Field |
|---|---|---|
| `h3.base-search-card__title` | text | `title` |
| `h4.base-search-card__subtitle` | text | `company` |
| `span.job-search-card__location` | text | `location` |
| `a.base-card__full-link` | `href` | `url` |

### Limits

- Max 2 pages (50 jobs) per search to avoid 429 throttling.
- Respects existing `FileCache` (30-min TTL).
- Appears in sidebar sources only when region is `Global` or `Both`.

---

## TUI Redesign (`app/ui/tui/app.py`)

### Bug fix: Select navigation

**Root cause:** Textual's `Select` opens a dropdown overlay that captures all keyboard events. When dismissed, focus returns to the Select — making the region buttons below it unreachable via keyboard.

**Fix:** Replace `Select` for Seniority with `RadioSet` (horizontal). Navigation via `←/→` arrows, no dropdown. Focus moves naturally to the next widget on `Tab`.

### Sidebar changes

```
┌─────────────────────────────┐
│  ⬡  G U I G O              │
├─────────────────────────────┤
│ Resume                       │
│ [✗ No resume loaded]  [R]   │  ← status + keybinding hint
├─────────────────────────────┤
│ Keywords                     │
│ [python, backend        ]   │
│ Technologies                 │
│ [react, fastapi         ]   │
│ Seniority                    │
│ ◉ Junior ○ Mid ○ Senior ○ Any│  ← RadioSet (fix)
│ Remote only    [●]           │
│ Max days old                 │
│ [30                     ]   │
│ Region                       │
│ [🌐 Global] [🇧🇷 Brasil] [⊕ Both]│
│ Sources                      │
│ remoteok  remotive  linkedin │
│                              │
│ [⌕  SEARCH]                 │
└─────────────────────────────┘
```

### Job card changes

Before:
```
#1  Senior Python Dev  ↑4.5  ★
Acme Corp  ·  Remote
python  fastapi  [linkedin]
```

After (with CV loaded):
```
#1  Senior Python Dev  ↑4.5  [CV 87%]  ★
Acme Corp  ·  Remote  ·  3d ago
python  fastapi  [linkedin]
```

CV badge color:
- ≥ 70%: `#3fb950` (green)
- ≥ 40%: `#e3b341` (yellow)
- < 40%: `#484f58` (gray)

Source badge color per provider:
- `gupy`: `#3fb950`
- `linkedin`: `#0a66c2`
- others: `#79c0ff`

### ResumeModal

Triggered by keybinding `r` (global). Contains:
1. `Input` for file path (manual type or paste).
2. `Button` "Browse" — opens OS file dialog via `tkinter.filedialog` (stdlib, no extra dep). Falls back to manual input if tkinter unavailable.
3. After parse: shows extracted skills preview (`Technologies: python, fastapi... | Seniority: Junior`).
4. `Button` "Use this resume" — applies to app state and pre-fills filters.
5. `Button` "Cancel" — dismisses without changes.

### Keybindings (updated)

| Key | Action |
|---|---|
| `Ctrl+S` | Search |
| `R` | Import Resume |
| `E` | Export |
| `F2` | Results tab |
| `F3` | Favorites tab |
| `F4` | History tab |
| `Q` | Quit |

---

## Error handling

| Scenario | Behavior |
|---|---|
| PDF parse fails | `notify("Could not read PDF", severity="error")`, no state change |
| PDF has no extractable text (scanned image) | `notify("PDF appears to be image-only", severity="warning")` |
| LinkedIn returns 429 | Provider returns empty list, logs warning, cache not written |
| LinkedIn HTML structure changes | `try/except` per card, skip unparseable cards |
| No skills extracted from CV | Filters not pre-filled, notify user, but CV match score still 0% |

---

## Dependencies

```
pypdf>=4.0      # PDF text extraction (lightweight, no system deps)
```

`html.parser` and `tkinter` are stdlib — no additional installs.

---

## Out of scope

- NLP-based skill extraction (spacy/nltk)
- LinkedIn authentication / cookie-based scraping
- CV storage between sessions (path is re-entered each run)
- Automatic re-scoring when filters change manually after CV import
