#!/usr/bin/env python3
"""
File management for research agent
Handles saving, loading, and exporting data
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class FileManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """
        Save results to JSON file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            topic_clean = re.sub(r'[^\w\s-]', '', results['metadata']['topic']).strip()
            topic_clean = re.sub(r'[-\s]+', '_', topic_clean)
            filename = f"research_{topic_clean}_{timestamp}.json"
        
        filepath = self.data_dir / filename
        
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
        
        filepath = self.data_dir / filename
        
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
            
            compilation_filepath = self.data_dir / compilation_filename
            
            with open(compilation_filepath, 'w', encoding='utf-8') as f:
                f.write(results['content_compilation'])
            
            files_created['compilation'] = str(compilation_filepath)
            print(f"📚 Content compilation saved to: {compilation_filepath}")
        
        return files_created
    
    def load_results(self, filepath: str) -> Dict[str, Any]:
        """
        Load results from JSON file
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading results from {filepath}: {str(e)}")
            return {}