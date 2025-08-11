# Research Agent (CLI)

A headless research agent that scrapes, preprocesses, embeds, stores, validates market signals, and emails reports.

## 🚀 Features

- **Multi-source data collection**: Hacker News (Algolia), ArXiv RSS, RSS (TechCrunch, MIT Tech Review, Wired)
- **Content extraction**: Optional full-article crawl via crawl4ai
- **Storage**: SQLite (`data/research.db`) for metadata + content
- **Embeddings**: Local SentenceTransformers + Chroma (disk persistence)
- **Socials + Validation**: Lightweight Reddit search + heuristic market score
- **Reporting + Email**: Markdown report + SMTP email

## 📁 Project Structure

```
research_agent/
├── cli.py                      # CLI entrypoint
├── src/
│   ├── scrapers/
│   │   ├── api_scrapers.py     # HN + ArXiv
│   │   ├── rss_scrapers.py     # TechCrunch, MIT TR, Wired
│   │   ├── base_scraper.py     # Orchestrator
│   │   └── social_scrapers.py  # Reddit (lightweight)
│   ├── processors/
│   │   ├── content_processor.py
│   │   ├── preprocess.py
│   │   └── validator.py
│   ├── storage/
│   │   ├── file_manager.py
│   │   └── db.py
│   ├── utils/
│   │   └── emailer.py
│   └── vector_store/
│       └── vector_store.py
├── data/
│   ├── research.db             # SQLite DB (created at runtime)
│   └── reports/                # Generated reports
├── vector_store/               # Chroma persistence
├── requirements.txt
└── README.md
```

## 🛠️ Installation

1. **Clone or create the project directory**:
   ```bash
   cd research_agent
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment variables** (optional for email):

Create `.env` in `research_agent/`:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=recipient@example.com
```

## 🚀 Usage (CLI)

- Ingest scrape -> DB -> embeddings (optionally crawl content):

```
python cli.py ingest --topic "AI" --days 7 --include-content --save-json --save-md
```

- Validate market (social + DB metrics), write report, optionally email:

```
python cli.py validate --topic "AI" --days 7 --email
```

- Semantic search over embedded corpus:

```
python cli.py search --query "foundation models for robotics" -k 5
```

### Programmatic Usage

```python
import asyncio
from src.scrapers.base_scraper import ResearchAgent

# Initialize the agent
agent = ResearchAgent()

# Basic scraping (metadata only)
results = agent.scrape_all("AI", days=7)

# Enhanced scraping with content extraction
results = asyncio.run(agent.scrape_all_with_content("AI", days=7))

# Save results
agent.save_results(results)
agent.export_to_markdown(results)
```

## 📊 Data Sources

- **Hacker News**: Algolia API (no auth)
- **ArXiv**: RSS feeds for multiple CS categories
- **TechCrunch/MIT TR/Wired**: RSS feeds
- **Reddit (light)**: public JSON search (no auth)

## 🔧 Configuration

Works out of the box without email. Data is saved to `research_agent/data/` and vectors to `research_agent/vector_store/`.

## 📈 Future Enhancements

- PRAW-based Reddit + GitHub Trending APIs
- LLM summarization/idea generation pipeline
- Better dedup and source config
- Scheduling via cron/systemd timers

## 🤝 Contributing

This is a modular architecture designed for easy extension. To add new data sources:

1. Create a new scraper in `src/scrapers/`
2. Add the scraper to `base_scraper.py`
3. Update the UI to display the new source

## 📄 License

This project is for educational and research purposes.