#!/usr/bin/env python3
"""
API-based scrapers for research agent
Handles Hacker News, ArXiv, and other API-based data sources
"""

import requests
import feedparser
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fake_useragent import UserAgent


class APIScrapers:
    def __init__(self):
        self.ua = UserAgent()
        self.headers = {'User-Agent': self.ua.random}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # ArXiv categories mapping
        self.arxiv_categories = {
            'ai': 'cs.AI',
            'ml': 'cs.LG', 
            'cl': 'cs.CL',
            'cv': 'cs.CV',
            'crypto': 'cs.CR',
            'robotics': 'cs.RO'
        }
    
    def fetch_hackernews(self, topic: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch Hacker News stories using Algolia API
        """
        print(f"🔍 Fetching Hacker News stories for '{topic}' (last {days} days)...")
        
        # Calculate timestamp for date filtering
        since_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
        
        url = "https://hn.algolia.com/api/v1/search"
        params = {
            'query': topic,
            'tags': 'story',
            'numericFilters': f'created_at_i>{since_timestamp}',
            'hitsPerPage': 50
        }
        
        articles = []
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for hit in data.get('hits', []):
                article = {
                    'title': hit.get('title', ''),
                    'url': hit.get('url', ''),
                    'points': hit.get('points', 0),
                    'comments_count': hit.get('num_comments', 0),
                    'created_at': datetime.fromtimestamp(hit.get('created_at_i', 0)).isoformat(),
                    'author': hit.get('author', ''),
                    'source': 'hackernews',
                    'story_id': hit.get('objectID', ''),
                    'hn_url': f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
                }
                
                if article['title'] and article['url']:
                    articles.append(article)
            
            print(f"✅ Found {len(articles)} Hacker News articles")
            
        except Exception as e:
            print(f"❌ Error fetching Hacker News: {str(e)}")
        
        return articles
    
    def fetch_arxiv_papers(self, topic: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch ArXiv papers from RSS feeds
        """
        print(f"📚 Fetching ArXiv papers for '{topic}' (last {days} days)...")
        
        articles = []
        
        # Map topic to ArXiv categories
        categories_to_search = []
        topic_lower = topic.lower()
        
        if any(keyword in topic_lower for keyword in ['ai', 'artificial intelligence']):
            categories_to_search.append('cs.AI')
        if any(keyword in topic_lower for keyword in ['ml', 'machine learning', 'learning']):
            categories_to_search.append('cs.LG')
        if any(keyword in topic_lower for keyword in ['nlp', 'language', 'text']):
            categories_to_search.append('cs.CL')
        if any(keyword in topic_lower for keyword in ['vision', 'image', 'computer vision']):
            categories_to_search.append('cs.CV')
        if any(keyword in topic_lower for keyword in ['crypto', 'security', 'blockchain']):
            categories_to_search.append('cs.CR')
        if any(keyword in topic_lower for keyword in ['robot', 'robotics']):
            categories_to_search.append('cs.RO')
        
        # Default to AI and ML if no specific match
        if not categories_to_search:
            categories_to_search = ['cs.AI', 'cs.LG']
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for category in categories_to_search:
            try:
                rss_url = f"http://export.arxiv.org/rss/{category}"
                print(f"  📡 Fetching from {rss_url}")
                
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries:
                    # Parse publication date
                    pub_date = datetime(*entry.published_parsed[:6])
                    
                    if pub_date >= cutoff_date:
                        # Extract ArXiv ID from link
                        arxiv_id = entry.id.split('/')[-1]
                        
                        article = {
                            'title': entry.title,
                            'authors': entry.author if hasattr(entry, 'author') else 'Unknown',
                            'abstract': entry.summary,
                            'pdf_url': f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                            'arxiv_url': f"https://arxiv.org/abs/{arxiv_id}",
                            'published_date': pub_date.isoformat(),
                            'category': category,
                            'source': 'arxiv',
                            'arxiv_id': arxiv_id
                        }
                        
                        # Filter by topic in title or abstract
                        if self._matches_topic(topic, article['title'] + ' ' + article['abstract']):
                            articles.append(article)
                
                time.sleep(1)  # Be respectful to ArXiv
                
            except Exception as e:
                print(f"❌ Error fetching ArXiv category {category}: {str(e)}")
        
        print(f"✅ Found {len(articles)} ArXiv papers")
        return articles
    
    def _matches_topic(self, topic: str, text: str) -> bool:
        """
        Simple topic matching using keywords
        """
        topic_keywords = topic.lower().split()
        text_lower = text.lower()
        
        # Must match at least one keyword
        return any(keyword in text_lower for keyword in topic_keywords)