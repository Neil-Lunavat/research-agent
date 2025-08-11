#!/usr/bin/env python3
"""
SQLite persistence for articles and crawled content.
"""

import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE,
                    title TEXT,
                    source TEXT,
                    author TEXT,
                    created_at TEXT,
                    published_date TEXT,
                    points INTEGER,
                    comments_count INTEGER,
                    description TEXT,
                    abstract TEXT,
                    category TEXT,
                    arxiv_id TEXT,
                    hn_url TEXT,
                    topic TEXT,
                    inserted_at TEXT,
                    updated_at TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS crawled_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER,
                    url TEXT,
                    markdown_content TEXT,
                    word_count INTEGER,
                    crawled_at TEXT,
                    updated_at TEXT,
                    UNIQUE(article_id),
                    FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE CASCADE
                )
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_articles_topic ON articles(topic)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_date)")
            conn.commit()

    def upsert_article(self, article: Dict[str, Any], topic: Optional[str] = None) -> int:
        now = datetime.utcnow().isoformat()
        url = article.get('url') or article.get('arxiv_url') or article.get('hn_url')
        if not url:
            raise ValueError("Article missing canonical URL")
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM articles WHERE url = ?", (url,))
            row = cur.fetchone()
            if row:
                article_id = row['id']
                cur.execute(
                    """
                    UPDATE articles SET
                        title = COALESCE(?, title),
                        source = COALESCE(?, source),
                        author = COALESCE(?, author),
                        created_at = COALESCE(?, created_at),
                        published_date = COALESCE(?, published_date),
                        points = COALESCE(?, points),
                        comments_count = COALESCE(?, comments_count),
                        description = COALESCE(?, description),
                        abstract = COALESCE(?, abstract),
                        category = COALESCE(?, category),
                        arxiv_id = COALESCE(?, arxiv_id),
                        hn_url = COALESCE(?, hn_url),
                        topic = COALESCE(?, topic),
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        article.get('title'),
                        article.get('source'),
                        article.get('author'),
                        article.get('created_at'),
                        article.get('published_date'),
                        article.get('points'),
                        article.get('comments_count'),
                        article.get('description'),
                        article.get('abstract'),
                        article.get('category'),
                        article.get('arxiv_id'),
                        article.get('hn_url'),
                        topic,
                        now,
                        article_id,
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO articles (
                        url, title, source, author, created_at, published_date,
                        points, comments_count, description, abstract, category,
                        arxiv_id, hn_url, topic, inserted_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        url,
                        article.get('title'),
                        article.get('source'),
                        article.get('author'),
                        article.get('created_at'),
                        article.get('published_date'),
                        int(article.get('points') or 0),
                        int(article.get('comments_count') or 0),
                        article.get('description'),
                        article.get('abstract'),
                        article.get('category'),
                        article.get('arxiv_id'),
                        article.get('hn_url'),
                        topic,
                        now,
                        now,
                    ),
                )
                article_id = cur.lastrowid
            conn.commit()
            return int(article_id)

    def upsert_crawled_content(self, article_id: int, url: str, markdown: str, word_count: int, crawled_at: str) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM crawled_content WHERE article_id = ?", (article_id,))
            row = cur.fetchone()
            if row:
                cur.execute(
                    """
                    UPDATE crawled_content SET
                        url = ?,
                        markdown_content = ?,
                        word_count = ?,
                        crawled_at = COALESCE(?, crawled_at),
                        updated_at = ?
                    WHERE article_id = ?
                    """,
                    (url, markdown, int(word_count or 0), crawled_at, now, article_id),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO crawled_content (
                        article_id, url, markdown_content, word_count, crawled_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (article_id, url, markdown, int(word_count or 0), crawled_at or now, now),
                )
            conn.commit()

    def fetch_articles_for_embedding(self) -> List[sqlite3.Row]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT a.url, a.title, a.source, a.description, a.abstract,
                       COALESCE(cc.markdown_content, '') AS markdown_content
                FROM articles a
                LEFT JOIN crawled_content cc ON cc.article_id = a.id
                ORDER BY a.published_date DESC
                """
            )
            return cur.fetchall()

    def aggregate_signals(self, topic: Optional[str] = None, days: Optional[int] = None) -> Dict[str, Any]:
        where_clauses = []
        params: List[Any] = []
        if topic:
            where_clauses.append("topic = ?")
            params.append(topic)
        if days is not None:
            where_clauses.append("COALESCE(published_date, created_at) >= ?")
            cutoff = datetime.utcnow().timestamp() - days * 86400
            # Using created_at/published_date ISO strings; conservative filter
            iso_cutoff = datetime.utcfromtimestamp(cutoff).isoformat()
            params.append(iso_cutoff)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM articles {where_sql}", params)
            total = cur.fetchone()[0]

            cur.execute(f"SELECT SUM(points), SUM(comments_count) FROM articles {where_sql}", params)
            row = cur.fetchone()
            total_points = row[0] or 0
            total_comments = row[1] or 0

            cur.execute(f"SELECT COUNT(*) FROM crawled_content", [])
            crawled = cur.fetchone()[0]

        return {
            'articles': int(total),
            'hn_points': int(total_points),
            'hn_comments': int(total_comments),
            'crawled_count': int(crawled),
        }


