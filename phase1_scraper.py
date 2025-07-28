#!/usr/bin/env python3
"""
Research Agent Phase 1 Scraper
Standalone script for scraping easy, no-auth data sources
Enhanced with crawl4ai for content extraction
"""

import requests
import feedparser
import json
import time
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import re
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent
import aiohttp
import base64

# crawl4ai imports
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

class Phase1Scraper:
    def __init__(self):
        self.ua = UserAgent()
        self.headers = {'User-Agent': self.ua.random}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.aio_session = None
        
        # RSS Feed URLs
        self.rss_sources = {
            'techcrunch': 'https://techcrunch.com/feed/',
            'mit_tech_review': 'https://www.technologyreview.com/feed/',
            'wired': 'https://www.wired.com/feed/'
        }
        
        # ArXiv categories
        self.arxiv_categories = {
            'ai': 'cs.AI',
            'ml': 'cs.LG', 
            'cl': 'cs.CL',
            'cv': 'cs.CV',
            'crypto': 'cs.CR',
            'robotics': 'cs.RO'
        }
    
    async def _get_aio_session(self):
        if self.aio_session is None or self.aio_session.closed:
            self.aio_session = aiohttp.ClientSession(headers=self.headers)
        return self.aio_session

    async def _close_aio_session(self):
        if self.aio_session:
            await self.aio_session.close()

    async def fetch_github_readme(self, url: str) -> Dict[str, Any]:
        """
        Fetches the README content of a GitHub repository using the GitHub API.
        """
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            return {'success': False, 'error': 'Invalid GitHub repo URL'}
            
        owner, repo = path_parts[0], path_parts[1]
        api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        
        session = await self._get_aio_session()

        try:
            async with session.get(api_url) as response:
                response.raise_for_status()
                data = await response.json()
                
                content = base64.b64decode(data['content']).decode('utf-8')
                word_count = len(content.split())
                
                return {
                    'success': True,
                    'markdown_content': content,
                    'word_count': word_count,
                    'crawled_at': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"    ❌ GitHub API Error: {e}")
            return {'success': False, 'error': str(e)}

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
    
    def scrape_all(self, topic: str, days: int = 7) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape all Phase 1 sources
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
        results['hackernews'] = self.fetch_hackernews(topic, days)
        results['arxiv'] = self.fetch_arxiv_papers(topic, days)
        results['rss'] = self.parse_rss_feeds(topic, days)
        
        # Update metadata
        total = len(results['hackernews']) + len(results['arxiv']) + len(results['rss'])
        results['metadata']['total_articles'] = total
        
        print("\n" + "=" * 60)
        print(f"🎉 Scraping complete! Total articles found: {total}")
        print(f"   📊 Hacker News: {len(results['hackernews'])}")
        print(f"   📚 ArXiv: {len(results['arxiv'])}")
        print(f"   📰 RSS Feeds: {len(results['rss'])}")
        
        return results
    
    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """
        Save results to JSON file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            topic_clean = re.sub(r'[^\w\s-]', '', results['metadata']['topic']).strip()
            topic_clean = re.sub(r'[-\s]+', '_', topic_clean)
            filename = f"research_{topic_clean}_{timestamp}.json"
        
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        filepath = data_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {filepath}")
        return str(filepath)
    
    def export_to_markdown(self, results: Dict[str, Any], filename: str = None) -> str:
        """
        Export results to markdown format
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            topic_clean = re.sub(r'[^\w\s-]', '', results['metadata']['topic']).strip()
            topic_clean = re.sub(r'[-\s]+', '_', topic_clean)
            filename = f"research_report_{topic_clean}_{timestamp}.md"
        
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        filepath = data_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# Research Report: {results['metadata']['topic']}\n\n")
            f.write(f"**Generated:** {results['metadata']['scraped_at']}\n")
            f.write(f"**Time Range:** Last {results['metadata']['days']} days\n")
            f.write(f"**Total Articles:** {results['metadata']['total_articles']}\n\n")
            
            # Hacker News section
            if results['hackernews']:
                f.write("## 🔥 Hacker News\n\n")
                for article in results['hackernews']:
                    f.write(f"### [{article['title']}]({article['url']})\n")
                    f.write(f"- **Points:** {article['points']} | **Comments:** {article['comments_count']}\n")
                    f.write(f"- **Author:** {article['author']} | **Date:** {article['created_at'][:10]}\n")
                    f.write(f"- **HN Discussion:** [View]({article['hn_url']})\n\n")
            
            # ArXiv section
            if results['arxiv']:
                f.write("## 📚 ArXiv Papers\n\n")
                for article in results['arxiv']:
                    f.write(f"### [{article['title']}]({article['arxiv_url']})\n")
                    f.write(f"- **Authors:** {article['authors']}\n")
                    f.write(f"- **Category:** {article['category']} | **Date:** {article['published_date'][:10]}\n")
                    f.write(f"- **PDF:** [Download]({article['pdf_url']})\n")
                    f.write(f"- **Abstract:** {article['abstract'][:200]}...\n\n")
            
            # RSS section
            if results['rss']:
                f.write("## 📰 News Articles\n\n")
                for article in results['rss']:
                    f.write(f"### [{article['title']}]({article['url']})\n")
                    f.write(f"- **Source:** {article['source'].title()} | **Author:** {article['author']}\n")
                    f.write(f"- **Date:** {article['published_date'][:10]}\n")
                    if article['description']:
                        f.write(f"- **Summary:** {article['description'][:200]}...\n")
                    f.write("\n")
        
        print(f"📝 Markdown report saved to: {filepath}")
        return str(filepath)

    async def crawl_content_from_urls(self, results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, str]:
        """
        Crawl actual content from collected URLs using crawl4ai
        """
        print(f"\n🕷️  Starting content crawling with crawl4ai...")
        print("=" * 60)
        
        # Collect all URLs from different sources
        all_urls = []
        url_source_map = {}
        
        # Add Hacker News URLs
        for article in results['hackernews']:
            if article.get('url') and self._is_valid_url(article['url']):
                all_urls.append(article['url'])
                url_source_map[article['url']] = {
                    'source': 'hackernews',
                    'title': article['title'],
                    'points': article.get('points', 0)
                }
        
        # Add RSS URLs
        for article in results['rss']:
            if article.get('url') and self._is_valid_url(article['url']):
                all_urls.append(article['url'])
                url_source_map[article['url']] = {
                    'source': article['source'],
                    'title': article['title'],
                    'author': article.get('author', 'Unknown')
                }
        
        # Note: ArXiv papers are PDFs, so we skip them for content crawling
        
        # Remove duplicates while preserving order
        unique_urls = list(dict.fromkeys(all_urls))
        
        print(f"📊 Found {len(unique_urls)} unique URLs to crawl")
        
        if not unique_urls:
            print("❌ No valid URLs found for crawling")
            return {}
        
        # Configure crawl4ai
        browser_config = BrowserConfig(
            headless=True,
            verbose=False
        )
        
        crawler_config = CrawlerRunConfig(
            word_count_threshold=100, # Increased threshold
            wait_for_timeout=5000,    # Increased wait time
            cache_mode="enabled"      # Use caching to avoid re-crawling
        )
        
        crawled_content = {}
        
        crawler = AsyncWebCrawler(config=browser_config)

        for i, url in enumerate(unique_urls, 1):
            source_info = url_source_map.get(url, {})
            result_data = {
                'url': url,
                'title': source_info.get('title', 'Unknown Title'),
                'source': source_info.get('source', 'unknown'),
                'success': False
            }
            try:
                print(f"  [{i:2d}/{len(unique_urls)}] Crawling: {url[:80]}...")

                if 'github.com' in url:
                    content_result = await self.fetch_github_readme(url)
                else:
                    result = await crawler.arun(url=url, config=crawler_config)
                    if result.success and result.markdown:
                        markdown_text = str(result.markdown)
                        content_result = {
                            'success': True,
                            'markdown_content': markdown_text,
                            'word_count': len(markdown_text.split()),
                            'crawled_at': datetime.now().isoformat()
                        }
                    else:
                        content_result = {'success': False, 'error': result.error_message if result else 'Unknown error'}

                if content_result['success']:
                    result_data.update(content_result)
                    print(f"    ✅ Success - {result_data.get('word_count', 0)} words extracted")
                else:
                    result_data['error'] = content_result.get('error', 'Unknown error')
                    print(f"    ❌ Failed - {result_data['error']}")

            except Exception as e:
                print(f"    ❌ Exception - {str(e)}")
                result_data['error'] = str(e)
            
            crawled_content[url] = result_data
            
            # Be polite - small delay between requests
            await asyncio.sleep(1)

        await crawler.close()
        await self._close_aio_session()
        
        successful_crawls = sum(1 for content in crawled_content.values() if content.get('success'))
        print(f"\n✅ Content crawling completed!")
        print(f"   📊 Successfully crawled: {successful_crawls}/{len(unique_urls)} URLs")
        
        return crawled_content
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Check if URL is valid and worth crawling
        """
        if not url or not isinstance(url, str):
            return False
        
        # Skip non-HTTP URLs
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Skip PDFs and other document formats
        skip_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
        
        # Skip social media direct posts (often require login)
        skip_domains = ['twitter.com', 'facebook.com', 'linkedin.com', 'instagram.com']
        if any(domain in url.lower() for domain in skip_domains):
            return False
        
        return True
    
    def create_content_compilation(self, crawled_content: Dict[str, Dict]) -> str:
        """
        Create a compiled document from all crawled content
        """
        print(f"\n📚 Creating content compilation...")
        
        compilation_parts = []
        
        # Add header
        compilation_parts.append("# Research Content Compilation")
        compilation_parts.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        compilation_parts.append("")
        
        # Add summary
        successful_content = [content for content in crawled_content.values() if content.get('success')]
        total_words = sum(content.get('word_count', 0) for content in successful_content)
        
        compilation_parts.append("## Summary")
        compilation_parts.append(f"- **Total Articles:** {len(successful_content)}")
        compilation_parts.append(f"- **Total Word Count:** {total_words:,}")
        
        # Group by source
        sources = {}
        for content in successful_content:
            source = content.get('source', 'unknown')
            if source not in sources:
                sources[source] = []
            sources[source].append(content)
        
        for source, count in [(s, len(articles)) for s, articles in sources.items()]:
            compilation_parts.append(f"- **{source.title()}:** {count} articles")
        
        compilation_parts.append("")
        compilation_parts.append("---")
        compilation_parts.append("")
        
        # Add content by source
        for source_name, articles in sources.items():
            compilation_parts.append(f"# {source_name.title()} Articles")
            compilation_parts.append("")
            
            for i, content in enumerate(articles, 1):
                compilation_parts.append(f"## Article {i}: {content['title']}")
                compilation_parts.append(f"**URL:** {content['url']}")
                compilation_parts.append(f"**Words:** {content.get('word_count', 0):,}")
                compilation_parts.append(f"**Crawled:** {content.get('crawled_at', '')[:19]}")
                compilation_parts.append("")
                compilation_parts.append("### Content")
                compilation_parts.append("")
                # Add a simple cleaning step here
                cleaned_markdown = self._clean_markdown_content(content['markdown_content'])
                compilation_parts.append(cleaned_markdown)
                compilation_parts.append("")
                compilation_parts.append("---")
                compilation_parts.append("")
        
        compilation_text = "\n".join(compilation_parts)
        print(f"✅ Compilation created - {len(compilation_text):,} characters total")
        
        return compilation_text
    
    def _clean_markdown_content(self, text: str) -> str:
        """A simple cleaner for leftover markdown noise."""
        lines = text.split('\n')
        
        # Remove lines that look like navigation, footers, or junk
        # This is a heuristic: we remove short lines with links
        clean_lines = []
        for line in lines:
            line_lower = line.lower()
            if '©' in line_lower and 'github, inc.' in line_lower:
                continue
            if 'manage cookies' in line_lower or 'do not share my personal information' in line_lower:
                continue
            
            # Remove short, link-heavy lines common in nav/footers
            if len(line.split()) < 5 and ']' in line and '[' in line:
                continue

            clean_lines.append(line)
            
        return "\n".join(clean_lines)

    async def scrape_all_with_content(self, topic: str, days: int = 7) -> Dict[str, Any]:
        """
        Enhanced scraping that includes content extraction
        """
        print(f"\n🚀 Starting Enhanced Phase 1 scraping for topic: '{topic}' (last {days} days)")
        print("=" * 80)
        
        # First, get the metadata (URLs, titles, etc.)
        results = self.scrape_all(topic, days)
        
        # Then crawl the actual content
        crawled_content = await self.crawl_content_from_urls(results)
        
        # Create compilation
        compilation = self.create_content_compilation(crawled_content)
        
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

    def save_results_with_content(self, results: Dict[str, Any], filename: str = None) -> Dict[str, str]:
        """
        Save enhanced results including content compilation
        """
        files_created = {}
        
        # Save JSON results
        json_file = self.save_results(results, filename)
        files_created['json'] = json_file
        
        # Save content compilation
        if 'content_compilation' in results:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                topic_clean = re.sub(r'[^\w\s-]', '', results['metadata']['topic']).strip()
                topic_clean = re.sub(r'[-\s]+', '_', topic_clean)
                compilation_filename = f"content_compilation_{topic_clean}_{timestamp}.md"
            else:
                base_name = Path(filename).stem
                compilation_filename = f"{base_name}_content.md"
            
            # Create data directory if it doesn't exist
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            compilation_filepath = data_dir / compilation_filename
            
            with open(compilation_filepath, 'w', encoding='utf-8') as f:
                f.write(results['content_compilation'])
            
            files_created['compilation'] = str(compilation_filepath)
            print(f"📚 Content compilation saved to: {compilation_filepath}")
        
        return files_created


async def main():
    """
    Enhanced main function with content crawling
    """
    print("🤖 Enhanced Research Agent Phase 1 Scraper with Content Extraction")
    print("=" * 70)
    
    # Get user input
    topic = input("Enter research topic (e.g., 'AI', 'blockchain', 'startups'): ").strip()
    if not topic:
        topic = "AI"
        print(f"Using default topic: {topic}")
    
    days_input = input("Enter number of days to search (default: 7): ").strip()
    try:
        days = int(days_input) if days_input else 7
    except ValueError:
        days = 7
        print(f"Using default days: {days}")
    
    # Initialize scraper and run enhanced scraping
    scraper = Phase1Scraper()
    results = await scraper.scrape_all_with_content(topic, days)
    
    # Save results
    files_created = scraper.save_results_with_content(results)
    
    print(f"\n✅ Enhanced scraping completed successfully!")
    print(f"📁 Files created:")
    for file_type, filepath in files_created.items():
        print(f"   📊 {file_type.title()}: {filepath}")
    
    # Print summary
    metadata = results['metadata']
    content_meta = metadata.get('content_crawling', {})
    print(f"\n📈 Final Summary:")
    print(f"   🔍 Total articles found: {metadata['total_articles']}")
    print(f"   🕷️  URLs crawled: {content_meta.get('successful_crawls', 0)}/{content_meta.get('total_urls_attempted', 0)}")
    print(f"   📝 Words extracted: {content_meta.get('total_words_extracted', 0):,}")


if __name__ == "__main__":
    asyncio.run(main()) 