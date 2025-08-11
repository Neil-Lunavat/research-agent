#!/usr/bin/env python3
"""
CLI entrypoint for the Research Agent (headless pipeline)

Workflow:
  - ingest: scrape -> (optional) content crawl -> preprocess -> store in SQLite -> embed into Chroma
  - validate: scrape socials (optional) -> compute market validation -> write report -> (optional) email
"""

import argparse
import asyncio
import os
import shutil
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

# Local imports
from src.scrapers.base_scraper import ResearchAgent
from src.storage.db import DatabaseManager
from src.processors.preprocess import build_document_for_embedding
from src.vector_store.vector_store import VectorStore
from src.scrapers.social_scrapers import SocialScraper
from src.processors.validator import MarketValidator
from src.utils.emailer import EmailClient


def ensure_directories(base_dir: Path) -> None:
    (base_dir / "data").mkdir(exist_ok=True)
    (base_dir / "data" / "reports").mkdir(parents=True, exist_ok=True)
    (base_dir / "vector_store").mkdir(exist_ok=True)


def cmd_ingest(args: argparse.Namespace) -> None:
    base_dir = Path(__file__).parent
    ensure_directories(base_dir)

    db_path = base_dir / "data" / "research.db"
    db = DatabaseManager(db_path=str(db_path))
    agent = ResearchAgent(data_dir=str(base_dir / "data"))

    print(f"\n=== INGEST: topic='{args.topic}' days={args.days} include_content={args.include_content} ===")
    if args.include_content:
        results = asyncio.run(agent.scrape_all_with_content(args.topic, args.days))
    else:
        results = agent.scrape_all(args.topic, args.days)

    # Persist metadata first
    article_id_map = {}  # url -> article_id
    for article in results.get('hackernews', []):
        article_id_map[article['url']] = db.upsert_article(article, topic=args.topic)
    for article in results.get('arxiv', []):
        # Use arxiv_url as canonical link if available
        canonical = article.get('arxiv_url') or article.get('url')
        article['url'] = canonical
        article_id_map[article['url']] = db.upsert_article(article, topic=args.topic)
    for article in results.get('rss', []):
        article_id_map[article['url']] = db.upsert_article(article, topic=args.topic)

    # Persist crawled content if available
    crawled = results.get('crawled_content', {})
    for url, content in crawled.items():
        if not content.get('success'):
            continue
        article_id = article_id_map.get(url)
        if article_id:
            db.upsert_crawled_content(article_id=article_id, url=url, markdown=content.get('markdown_content', ''),
                                      word_count=int(content.get('word_count', 0)),
                                      crawled_at=content.get('crawled_at'))

    # Build embeddings and index into Chroma
    vs = VectorStore(persist_directory=str(base_dir / "vector_store"))
    docs_to_index = []
    metas_to_index = []
    ids_to_index = []

    rows = db.fetch_articles_for_embedding()
    for row in rows:
        doc_text = build_document_for_embedding(
            title=row['title'] or '',
            summary=row['description'] or row['abstract'] or '',
            full_content=row['markdown_content'] or ''
        )
        if not doc_text.strip():
            continue
        docs_to_index.append(doc_text)
        metas_to_index.append({
            'url': row['url'],
            'title': row['title'] or '',
            'source': row['source'] or ''
        })
        ids_to_index.append(row['url'])

    if docs_to_index:
        vs.add_documents(ids=ids_to_index, documents=docs_to_index, metadatas=metas_to_index)
        print(f"🔎 Indexed {len(docs_to_index)} documents into vector store")
    else:
        print("ℹ️ No new documents to index")

    # Optional export of raw results
    if args.save_json or args.save_md:
        files = {}
        if args.include_content:
            files = agent.save_results_with_content(results)
        else:
            json_path = agent.save_results(results)
            files['json'] = json_path
            md_path = agent.export_to_markdown(results)
            files['md'] = md_path
        print(f"Artifacts saved: {files}")


def cmd_validate(args: argparse.Namespace) -> None:
    base_dir = Path(__file__).parent
    ensure_directories(base_dir)

    load_dotenv(base_dir / ".env")

    db_path = base_dir / "data" / "research.db"
    db = DatabaseManager(db_path=str(db_path))

    print("\n=== VALIDATE: social signals + market scores ===")
    social = SocialScraper()
    social_items = social.fetch_social_signals(topic=args.topic, days=args.days)

    validator = MarketValidator()
    report_md, summary = validator.generate_report(db=db, social_items=social_items, topic=args.topic, days=args.days)

    report_name = f"market_report_{args.topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path = base_dir / "data" / "reports" / report_name
    report_path.write_text(report_md, encoding='utf-8')
    print(f"📝 Report written to {report_path}")

    # Email if requested
    if args.email:
        email_to = os.getenv('EMAIL_TO')
        if not email_to:
            print("⚠️ EMAIL_TO not set; skipping email")
        else:
            client = EmailClient()
            subject = f"Research Agent Market Report - {args.topic}"
            client.send_email(subject=subject, body=report_md, attachments=[str(report_path)])
            print(f"✉️  Report emailed to {email_to}")


def cmd_search(args: argparse.Namespace) -> None:
    base_dir = Path(__file__).parent
    vs = VectorStore(persist_directory=str(base_dir / "vector_store"))
    results = vs.query(query_texts=[args.query], n_results=args.k)
    for i, (doc, meta, score) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
        print(f"[{i+1}] {meta.get('title', '')} | {meta.get('source', '')} | {meta.get('url', '')}")
        print(f"     score: {score:.4f}")


def _remove_dir_contents(path: Path) -> int:
    if not path.exists():
        return 0
    removed = 0
    for child in path.iterdir():
        try:
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
            removed += 1
        except Exception:
            pass
    return removed


def cmd_clean(args: argparse.Namespace) -> None:
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data"
    reports_dir = data_dir / "reports"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    db_file = data_dir / "research.db"
    vectors_dir = base_dir / "vector_store"

    if args.all:
        args.db = args.reports = args.raw = args.processed = args.vectors = True

    if not any([args.db, args.reports, args.raw, args.processed, args.vectors]):
        print("Nothing to clean. Specify one or more of --db --reports --raw --processed --vectors, or use --all.")
        return

    print("\n=== CLEAN: removing generated artifacts ===")
    if args.db:
        try:
            if db_file.exists():
                db_file.unlink()
                print(f"🗑️  Deleted DB: {db_file}")
            else:
                print("ℹ️  DB not found; skipping")
        except Exception as e:
            print(f"⚠️  Failed to delete DB: {e}")

    if args.reports:
        removed = _remove_dir_contents(reports_dir)
        print(f"🗑️  Cleared reports ({removed} items): {reports_dir}")

    if args.raw:
        removed = _remove_dir_contents(raw_dir)
        print(f"🗑️  Cleared raw data ({removed} items): {raw_dir}")

    if args.processed:
        removed = _remove_dir_contents(processed_dir)
        print(f"🗑️  Cleared processed data ({removed} items): {processed_dir}")

    if args.vectors:
        try:
            if vectors_dir.exists():
                shutil.rmtree(vectors_dir, ignore_errors=True)
            vectors_dir.mkdir(parents=True, exist_ok=True)
            print(f"🗑️  Cleared vector store: {vectors_dir}")
        except Exception as e:
            print(f"⚠️  Failed to clear vector store: {e}")


def main():
    parser = argparse.ArgumentParser(description="Research Agent CLI")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # ingest
    p_ingest = subparsers.add_parser('ingest', help='Scrape + (optional) crawl content + store + embed')
    p_ingest.add_argument('--topic', required=True, help='Topic keywords, e.g. "AI"')
    p_ingest.add_argument('--days', type=int, default=7, help='Lookback window in days')
    p_ingest.add_argument('--include-content', action='store_true', help='Crawl full content with crawl4ai')
    p_ingest.add_argument('--save-json', action='store_true', help='Also save raw JSON results to data/')
    p_ingest.add_argument('--save-md', action='store_true', help='Also save markdown report to data/')
    p_ingest.set_defaults(func=cmd_ingest)

    # validate
    p_validate = subparsers.add_parser('validate', help='Scrape socials and compute market validation; write report; optional email')
    p_validate.add_argument('--topic', required=True, help='Topic keywords, e.g. "AI"')
    p_validate.add_argument('--days', type=int, default=7, help='Lookback window in days for validation')
    p_validate.add_argument('--email', action='store_true', help='Email the generated report')
    p_validate.set_defaults(func=cmd_validate)

    # search
    p_search = subparsers.add_parser('search', help='Semantic search over embedded corpus')
    p_search.add_argument('--query', required=True)
    p_search.add_argument('-k', type=int, default=5)
    p_search.set_defaults(func=cmd_search)

    # clean
    p_clean = subparsers.add_parser('clean', help='Remove generated artifacts (non-interactive)')
    p_clean.add_argument('--db', action='store_true', help='Delete data/research.db')
    p_clean.add_argument('--reports', action='store_true', help='Delete files in data/reports/')
    p_clean.add_argument('--raw', action='store_true', help='Delete files in data/raw/')
    p_clean.add_argument('--processed', action='store_true', help='Delete files in data/processed/')
    p_clean.add_argument('--vectors', action='store_true', help='Delete vector_store contents')
    p_clean.add_argument('--all', action='store_true', help='Delete all of the above')
    p_clean.set_defaults(func=cmd_clean)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()



