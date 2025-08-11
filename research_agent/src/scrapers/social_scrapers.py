#!/usr/bin/env python3
"""
Social scraping (lightweight, API-first where possible). For MVP, use HN comment/meta (already captured),
and Reddit via the public pushshift-like endpoints fallback (if available) or omit and return empty.

This module provides a unified interface returning social signal items:
  { source, url, title, score, comments, created_at }
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta

import requests


class SocialScraper:
    def __init__(self):
        self.session = requests.Session()

    def fetch_social_signals(self, topic: str, days: int = 7) -> List[Dict[str, Any]]:
        # For MVP, we implement a simple Reddit search using the public Reddit JSON endpoints.
        # Note: This is limited and may be throttled; acceptable for MVP.
        items: List[Dict[str, Any]] = []
        try:
            q = topic.replace(' ', '+')
            url = f"https://www.reddit.com/search.json?q={q}&sort=top&t=week&limit=25"
            headers = {
                'User-Agent': 'ResearchAgent/0.1 (by u/example)'
            }
            resp = self.session.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for child in data.get('data', {}).get('children', []):
                    post = child.get('data', {})
                    created = datetime.utcfromtimestamp(post.get('created_utc', 0))
                    if created >= datetime.utcnow() - timedelta(days=days):
                        items.append({
                            'source': 'reddit',
                            'url': 'https://www.reddit.com' + post.get('permalink', ''),
                            'title': post.get('title', ''),
                            'score': int(post.get('score', 0)),
                            'comments': int(post.get('num_comments', 0)),
                            'created_at': created.isoformat(),
                            'subreddit': post.get('subreddit', '')
                        })
        except Exception:
            # Silent fail for MVP; return what we have
            pass
        return items



