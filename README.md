# Research Agent Phase 1 Scraper

A standalone Python scraper that collects the latest tech news, research papers, and discussions from multiple sources without requiring authentication.

## 🎯 What it does

Scrapes data from:
- **Hacker News** - Latest tech discussions via Algolia API
- **ArXiv** - Research papers from computer science categories
- **RSS Feeds** - TechCrunch, MIT Tech Review, Wired

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Run the Scraper

```bash
python phase1_scraper.py
```

You'll be prompted to enter:
- **Topic**: What to search for (e.g., "AI", "blockchain", "startups")
- **Days**: How many days back to search (default: 7)

### 3. View Results

The scraper creates two files in the `data/` directory:
- **JSON file**: Raw structured data for further processing
- **Markdown file**: Human-readable report

## 📊 Example Output

```
🤖 Research Agent Phase 1 Scraper
========================================
Enter research topic (e.g., 'AI', 'blockchain', 'startups'): AI
Enter number of days to search (default: 7): 7

🚀 Starting Phase 1 scraping for topic: 'AI' (last 7 days)
============================================================
🔍 Fetching Hacker News stories for 'AI' (last 7 days)...
✅ Found 15 Hacker News articles
📚 Fetching ArXiv papers for 'AI' (last 7 days)...
  📡 Fetching from http://export.arxiv.org/rss/cs.AI
  📡 Fetching from http://export.arxiv.org/rss/cs.LG
✅ Found 8 ArXiv papers
📰 Fetching RSS feeds for 'AI' (last 7 days)...
  📡 Fetching from techcrunch: https://techcrunch.com/feed/
  📡 Fetching from mit_tech_review: https://www.technologyreview.com/feed/
  📡 Fetching from wired: https://www.wired.com/feed/
✅ Found 12 RSS articles

============================================================
🎉 Scraping complete! Total articles found: 35
   📊 Hacker News: 15
   📚 ArXiv: 8
   📰 RSS Feeds: 12

💾 Results saved to: data/research_AI_20241210_143022.json
📝 Markdown report saved to: data/research_report_AI_20241210_143022.md
```

## 🔧 Features

- **No Authentication Required**: Uses public APIs and RSS feeds
- **Smart Topic Mapping**: Automatically maps topics to relevant ArXiv categories
- **Date Filtering**: Only fetches recent content within specified timeframe
- **Duplicate Handling**: Basic filtering to avoid duplicate content
- **Multiple Output Formats**: Both JSON (for processing) and Markdown (for reading)
- **Error Handling**: Gracefully handles API failures and network issues
- **Respectful Scraping**: Includes delays and proper headers

## 📁 Data Structure

### JSON Output
```json
{
  "hackernews": [...],
  "arxiv": [...],
  "rss": [...],
  "metadata": {
    "topic": "AI",
    "days": 7,
    "scraped_at": "2024-12-10T14:30:22",
    "total_articles": 35
  }
}
```

### Article Fields
- **Hacker News**: title, url, points, comments_count, author, created_at, hn_url
- **ArXiv**: title, authors, abstract, pdf_url, arxiv_url, published_date, category
- **RSS**: title, description, url, published_date, source, author

## 🎨 Customization

You can easily modify the scraper by editing `phase1_scraper.py`:

- **Add RSS sources**: Update the `rss_sources` dictionary
- **Add ArXiv categories**: Update the `arxiv_categories` dictionary  
- **Change topic matching**: Modify the `_matches_topic()` method
- **Adjust timeouts**: Change the timeout values in API calls

## 🚧 Limitations

- **Simple topic matching**: Uses basic keyword matching (could be improved with NLP)
- **No content extraction**: Doesn't fetch full article text (can be added with newspaper3k)
- **Rate limiting**: Basic delays only (could be enhanced)
- **No deduplication**: Doesn't remove similar articles across sources

## 🔮 Next Steps

This is Phase 1 of a larger research agent. Future phases will add:
- Reddit API integration
- GitHub trending repositories
- Advanced web scraping for protected sites
- LLM-powered content analysis and idea generation
- Streamlit web interface

## 📝 License

This project is for educational/research purposes. Please respect the terms of service of all data sources. 