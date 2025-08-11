## Research Agent - Usage

Run all commands from the `research_agent` directory (or provide absolute paths as shown).

### Install

```bash
cd research_agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Ingest (scrape → store → embed)

```bash
python cli.py ingest --topic "AI" --days 7 --include-content --save-json --save-md
```

- `--include-content`: crawl full article content via crawl4ai
- `--save-json` / `--save-md`: write artifacts in `research_agent/data/`

### Validate (social + DB signals → report)

```bash
python cli.py validate --topic "AI" --days 7 --email
```

- Writes markdown report to `research_agent/data/reports/`
- Email requires `.env` with SMTP settings

### Search (semantic over embeddings)

```bash
python cli.py search --query "foundation models for robotics" -k 5
```

### Clean (remove generated artifacts)

```bash
python cli.py clean --all
# or granular:
python cli.py clean --db --reports --raw --processed --vectors
```

Artifacts locations:
- DB: `research_agent/data/research.db`
- Reports: `research_agent/data/reports/`
- Raw/Processed: `research_agent/data/raw/`, `research_agent/data/processed/`
- Vector store: `research_agent/vector_store/`

