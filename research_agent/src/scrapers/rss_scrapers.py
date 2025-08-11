#!/usr/bin/env python3
"""
RSS-based scrapers for research agent
Handles TechCrunch, MIT Tech Review, Wired, and other RSS feeds
"""

import feedparser
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any


class RSSScrapers:
    def __init__(self):
        # RSS Feed URLs
        self.rss_sources = {
            'techcrunch': 'https://techcrunch.com/feed/',
            'mit_tech_review': 'https://www.technologyreview.com/feed/',
            'wired': 'https://www.wired.com/feed/'
        }
    
    def parse_rss_feeds(self, topic: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        Parse RSS feeds from TechCrunch, MIT Tech Review, and Wired
        """
        print(f"📰 Fetching RSS feeds for '{topic}' (last {days} days)...")
        
        articles = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for source_name, rss_url in self.rss_sources.items():
            try:
                print(f"  📡 Fetching from {source_name}: {rss_url}")
                
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries:
                    # Parse publication date
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6])
                    else:
                        pub_date = datetime.now()
                    
                    if pub_date >= cutoff_date:
                        article = {
                            'title': entry.title,
                            'description': entry.summary if hasattr(entry, 'summary') else '',
                            'url': entry.link,
                            'published_date': pub_date.isoformat(),
                            'source': source_name,
                            'author': entry.author if hasattr(entry, 'author') else 'Unknown'
                        }
                        
                        # Filter by topic
                        search_text = article['title'] + ' ' + article['description']
                        if self._matches_topic(topic, search_text):
                            articles.append(article)
                
                time.sleep(1)  # Be respectful
                
            except Exception as e:
                print(f"❌ Error fetching RSS from {source_name}: {str(e)}")
        
        print(f"✅ Found {len(articles)} RSS articles")
        return articles
    
    def _matches_topic(self, topic: str, text: str) -> bool:
        """
        Simple topic matching using keywords
        """
        topic_keywords = topic.lower().split()
        text_lower = text.lower()
        
        # Must match at least one keyword
        return any(keyword in text_lower for keyword in topic_keywords)