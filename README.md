# ProductionLens AI

ProductionLens AI is a Streamlit dashboard for reviewing AI project ideas against production-readiness criteria. It uses a local Ollama model to generate structured audit outputs across architecture, data, RAG, security, observability, evaluation, adoption, and executive lenses.

## Features

- Multi-lens AI readiness review
- Executive, RAG, architecture, and full production review modes
- Readiness scoring, risk summaries, gap mapping, and 90-day pilot plans
- Local SQLite review history for portfolio and comparison views
- PDF export for audit reports

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com/) running locally
- The `llama3.2` model pulled in Ollama

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
ollama pull llama3.2
```

## Run

```bash
streamlit run app.py
```

The app stores local review history in `reviews.db`. That file is intentionally ignored by git because it may contain private project descriptions and generated assessments.

## Public Repo Notes

This repository intentionally excludes private documents, generated local databases, virtual environments, caches, and scratch scripts.
