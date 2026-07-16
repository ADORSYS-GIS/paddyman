# Get Resources

## Overview

Downloads and processes all external source materials used by later pipeline stages.

**DownloadTrigger** runs three Airflow DAGs:
- `berlin_group_pdf_downloader` — downloads PDF documentation from the Berlin Group websites.
- `berlin_group_yaml_downloader` — clones NextGenPSD2 and OpenFinance YAML spec repositories.
- `adorsys_code_repo_downloader` — clones Adorsys XS2A source repositories.

**Docling** converts downloaded PDFs into cleaned Markdown files ready for parsing.
All PDFs are processed **concurrently** for maximum throughput. Worker count is
configurable via `config.yml` (defaults to 6 workers).

Cleaned markdown files are written **directly** to the final specification directory
without intermediate storage.

Both components use the central configuration system and run in sequence as one workflow.

---

## Project Setup

This module uses the **project-wide** environment, dependencies, and compose file.
All setup runs from `POC/` — not from inside this module directory.

```bash
# 1. Copy and populate the root environment template (once per developer)
cd POC
cp .env.example .env
# Edit .env — secrets only. Edit config.yml for paths, sources, schedules, and limits.

# 2. Create the root virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Install Docling ML dependencies (required for PDF processing)
pip install "docling>=2.0.0" "docling-core>=2.0.0" \
            "langchain-text-splitters>=0.3.0" "tiktoken>=0.6.0"
# Note: docling is commented out in requirements.txt because it pulls in heavy
# ML dependencies. Install it separately when you need to run batch_convert.py.

# 4. Install Playwright browser (required for PDF scraping)
playwright install chromium --with-deps
```

> See `POC/config.yml` for application configuration and `POC/.env.example` for secrets.
> See `POC/requirements.txt` for all project dependencies.

---

## Configuration

All configuration is read through `shared.config.settings`.

Application config: `POC/config.yml`
Secrets template: `POC/.env.example`
Runtime secrets: `POC/.env`

Key variables:

| Variable | Required | Purpose |
|---|---|---|
| `ADORSYS_GITLAB_TOKEN` | Yes | Adorsys GitLab access |
| `GITLAB_PERSONAL_ACCESS_TOKEN` | Optional | Avoids GitLab.com rate limits |
| `HF_TOKEN` | Optional | Avoids HuggingFace Hub rate limits |
| `PDF_SOURCES` | No | Prefer `sources.pdf` in `config.yml` |
| `YAML_REPOS` | No | Prefer `sources.yaml_repos` in `config.yml` |
| `CODE_REPOS` | No | Prefer `sources.code_repos` in `config.yml` |
| `DOCLING_MAX_WORKERS` | No | Concurrent PDF workers (default: CPU count - 1) |

Destinations, scheduling, network timeouts, and Docling processing options are configured in `POC/config.yml`.

> `.env` must not be committed to version control.

---

## Important Limitation

PDF downloading is coupled to the Berlin Group website DOM structure.

- Changing URLs or repositories: configuration change only.
- Supporting a different website with a different HTML structure: requires code changes in `DownloadTrigger/dags/berlin_group/scraper.py`.

---

## Execution

### Prerequisites
- Python 3.11+, Docker, Docker Compose, Git
- ~1–2 GB disk for PDFs, ~5–10 GB for repositories

### 1. Start Airflow

Run from `POC/` using the root compose file:

```bash
cd POC
docker compose up airflow-init          # first run only
docker compose up -d airflow-scheduler airflow-webserver
```

UI at `http://localhost:8080` — credentials: `admin` / `admin`.

### 2. Trigger the download DAGs

```bash
cd POC
docker compose exec airflow-scheduler airflow dags trigger berlin_group_pdf_downloader
docker compose exec airflow-scheduler airflow dags trigger berlin_group_yaml_downloader
docker compose exec airflow-scheduler airflow dags trigger adorsys_code_repo_downloader
```

### 3. Verify downloads

```bash
find 1_Get_Resources/DownloadTrigger/downloads/ -type f | wc -l   # non-zero confirms PDFs downloaded
ls DataSource/yaml_spec/                                           # nextgenpsd2  openfinance
ls DataSource/code_projects/                                       # aspsp-xs2a  ledgers  ...
```

### 4. Run Docling

```bash
cd POC
source .venv/bin/activate
python 1_Get_Resources/Docling/batch_convert.py
```

Options:
- `--picture-mode none` (default) | `local` | `api` — image description mode
- `--max-workers N` — number of concurrent workers (default: CPU count - 1, or from config.yml)

The batch converter processes all PDFs concurrently, showing real-time progress:
```
Found 12 PDF(s) under 1_Get_Resources/DownloadTrigger/downloads
Using 7 concurrent workersspecification_md_files/ -name "*.md" | wc -l
```

Each processed PDF produces:
- **One cleaned Markdown file** under `DataSource/berlin_group_specification_md_files/<slug>_clean.md`.
- Intermediate files (raw MD, metadata) under `Docling/output/<slug>/`.

The cleaned Markdown files are consumed by the Markdown parser in stage 2
======================================================================
Summary:
  Total PDFs:         12
  Successful:         10
  Skipped:            2
  Failed:             0
  Total time:         142.3s
  Avg time per PDF:   47.6s
======================================================================
```

Execution is **idempotent**: already-processed PDFs (those with cleaned Markdown files
in `DataSource/berlin_group_specification_md_files/`) are automatically skipped.

Each PDF produces exactly **one cleaned Markdown file** (`<slug>_clean.md`) directly in the
specification directory. No intermediate files are created.

For GPU-accelerated Docling processing, see `1_Get_Resources/Docling/EC2_GPU_SETUP.md`.

### 5. Verify Docling output

```bash
find POC/DataSource/berlin_group_specification_md_files/ -name "*.md" | wc -l
```

Each processed PDF produces one `<slug>_clean.md` file in the specification directory.

---

## Running Tests

```bash
cd POC
source .venv/bin/activate

# Shared model and config tests
pytest shared/tests/ -v

# 1_Get_Resources unit tests
cd 1_Get_Resources

# Docling batch converter tests
pytest tests/test_batch_convert.py -v
pytest --ignore=tests/test_scraper.py   # test_scraper requires: playwright install chromium
```

---

## Idempotency

Re-running any part of the workflow is safe.

- Destination directories are created automatically on first run.
- PDFs are skipped if the cleaned Markdown file already exists in the specification directory.
- Concurrent processing isolates failures: one failed PDF does not stop other PDFs.
- Repositories are skipped if `dest/.git` already exists.

---

## Troubleshooting

**`EnvironmentError` on DAG start** — `ADORSYS_GITLAB_TOKEN` is missing from `POC/.env`.

**Clone failures / rate limiting** — set `GITLAB_PERSONAL_ACCESS_TOKEN` for GitLab.com access.

**Git clone fails inside container** — check network:
```bash
cd POC
docker compose exec airflow-scheduler curl -I https://gitlab.com
```

**PDF scraper finds no documents** — the Berlin Group website DOM may have changed. Update the table-parsing selectors in `DownloadTrigger/dags/berlin_group/scraper.py`.

**Docling CUDA warning** — processing still runs on CPU. To silence:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

