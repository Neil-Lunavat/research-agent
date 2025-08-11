#!/usr/bin/env python3
"""
Content processing for research agent
Handles content extraction, crawling, and compilation
"""

import asyncio
import aiohttp
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from urllib.parse import urlparse
from fake_useragent import UserAgent

# crawl4ai imports
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig


class ContentProcessor:
    def __init__(self):
        self.ua = UserAgent()
        self.headers = {'User-Agent': self.ua.random}
        self.aio_session = None
    
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