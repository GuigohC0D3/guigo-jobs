# Guigo — Remote Job Hunter

Terminal-based job search tool for remote junior positions. Searches multiple job boards simultaneously, ranks results by relevance, and lets you manage favorites and export results.

## Features

- Multi-provider search (RemoteOK, Remotive, Arbeitnow, The Muse)
- Relevance scoring with configurable weights
- Favorites management (persistent)
- Search history
- Export to JSON, CSV, or TXT
- File-based cache (configurable TTL)
- Pagination and job detail view
- Open jobs directly in browser

## Requirements

- Python 3.12+

## Setup

```bash
git clone <repo>
cd guigo-jobs

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
```

## Running

```bash
python main.py
```

## Project Structure

```
guigo/
├── app/
│   ├── core/           # Config, logger
│   ├── models/         # Pydantic models (Job, SearchFilters, SearchRecord)
│   ├── providers/      # Job source adapters (RemoteOK, Remotive, Arbeitnow, The Muse)
│   ├── services/       # Search orchestration, export
│   ├── storage/        # Favorites, history (JSON persistence)
│   ├── ui/             # Terminal UI (Rich, Questionary)
│   └── utils/          # HTTP client, cache, scoring
├── exports/            # Exported files land here
├── logs/               # Log files
├── tests/
├── .env.example
├── requirements.txt
└── main.py
```

## Adding a New Provider

1. Create `app/providers/yourprovider.py` extending `BaseProvider`
2. Implement `fetch(filters: SearchFilters) -> list[Job]`
3. Register it in `app/providers/registry.py`
4. Add a toggle in `.env.example` and `app/core/config.py`

## Configuration

All configuration lives in `.env`. See `.env.example` for available options. Key settings:

| Variable | Default | Description |
|---|---|---|
| `CACHE_ENABLED` | `true` | Enable/disable file cache |
| `CACHE_TTL_MINUTES` | `30` | Cache lifetime |
| `MAX_RETRIES` | `3` | HTTP retry attempts |
| `SCORE_TECH_MATCH` | `3.0` | Points per matched technology tag |

## Storage

Favorites and history are stored in `.guigo/` at the project root (gitignored).
