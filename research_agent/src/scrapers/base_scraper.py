#!/usr/bin/env python3
"""
Base scraper orchestrator for research agent
Coordinates all scraping activities and provides main interface
"""

from datetime import datetime
from typing import Dict, Any, List

from .api_scrapers import APIScrapers
from .rss_scrapers import RSSScrapers
from ..processors.content_processor import ContentProcessor
from ..storage.file_manager import FileManager


class ResearchAgent:
    """
    Main orchestrator for the research agent
    Coordinates scraping, processing, and storage
    """
    
    def __init__(self, data_dir: str = "data"):
        self.api_scrapers = APIScrapers()
        self.rss_scrapers = RSSScrapers()
        self.content_processor = ContentProcessor()
        self.file_manager = FileManager(data_dir)
    
    def scrape_all(self, topic: str, days: int = 7) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape all Phase 1 sources (without content extraction)
        """
        print(f"\n🚀 Starting Phase 1 scraping for topic: '{topic}' (last {days} days)")
        print("=" * 60)
        
        results = {
            'hackernews': [],
            'arxiv': [],
            'rss': [],
            'metadata': {
                'topic': topic,
                'days': days,
                'scraped_at': datetime.now().isoformat(),
                'total_articles': 0
            }
        }
        
        # Fetch from all sources
        results['hackernews'] = self.api_scrapers.fetch_hackernews(topic, days)
        results['arxiv'] = self.api_scrapers.fetch_arxiv_papers(topic, days)
        results['rss'] = self.rss_scrapers.parse_rss_feeds(topic, days)
        
        # Update metadata
        total = len(results['hackernews']) + len(results['arxiv']) + len(results['rss'])
        results['metadata']['total_articles'] = total
        
        print("\n" + "=" * 60)
        print(f"🎉 Scraping complete! Total articles found: {total}")
        print(f"   📊 Hacker News: {len(results['hackernews'])}")
        print(f"   📚 ArXiv: {len(results['arxiv'])}")
        print(f"   📰 RSS Feeds: {len(results['rss'])}")
        
        return results
    
    async def scrape_all_with_content(self, topic: str, days: int = 7) -> Dict[str, Any]:
        """
        Enhanced scraping that includes content extraction
        """
        print(f"\n🚀 Starting Enhanced Phase 1 scraping for topic: '{topic}' (last {days} days)")
        print("=" * 80)
        
        # First, get the metadata (URLs, titles, etc.)
        results = self.scrape_all(topic, days)
        
        # Then crawl the actual content
        crawled_content = await self.content_processor.crawl_content_from_urls(results)
        
        # Create compilation
        compilation = self.content_processor.create_content_compilation(crawled_content)
        
        # Add crawled content to results
        results['crawled_content'] = crawled_content
        results['content_compilation'] = compilation
        results['metadata']['content_crawling'] = {
            'total_urls_attempted': len(crawled_content),
            'successful_crawls': sum(1 for c in crawled_content.values() if c.get('success')),
            'total_words_extracted': sum(c.get('word_count', 0) for c in crawled_content.values() if c.get('success')),
            'crawled_at': datetime.now().isoformat()
        }
        
        return results
    
    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """
        Save results to JSON file
        """
        return self.file_manager.save_results(results, filename)
    
    def export_to_markdown(self, results: Dict[str, Any], filename: str = None) -> str:
        """
        Export results to markdown format
        """
        return self.file_manager.export_to_markdown(results, filename)
    
    def save_results_with_content(self, results: Dict[str, Any], filename: str = None) -> Dict[str, str]:
        """
        Save enhanced results including content compilation
        """
        return self.file_manager.save_results_with_content(results, filename)
    
    def load_results(self, filepath: str) -> Dict[str, Any]:
        """
        Load results from JSON file
        """
        return self.file_manager.load_results(filepath)