# Research Agent MVP - Application Structure

## 🎯 **Basic App Flow**

### **Input:**
- Topic/Field selection (basically input keywords, text input)
- Date range (last 7 days, 30 days, etc.)
- Source selection (which APIs to use)

### **Output:**
- Latest news articles related to the topic
- Article summaries
- Key insights and trends
- Export to markdown file

### **User Journey:**
1. User opens Streamlit app
2. Selects topic (AI, Blockchain, Startups, etc.)
3. Chooses date range and sources
4. Clicks "Fetch Research"
5. Views results in organized dashboard
6. Exports findings to markdown

---

## 🚀 **MVP Phase 1 - Easy Implementations List**

### **Easiest Things to Build (No Authentication Required):**
1. **Hacker News API** - Algolia API (completely free, no auth)
2. **ArXiv RSS/API** - Public RSS feeds for research papers
3. **RSS Feed Parser** - TechCrunch, MIT Tech Review, Wired RSS
4. **Basic Streamlit UI** - Input forms + display results
5. **File Storage System** - Save results to JSON/Markdown
6. **Content Extraction** - Use newspaper3k for article content

### **Slightly Harder (Requires API Keys but Free):**
1. **Reddit API** - Requires Reddit account + API key
2. **GitHub API** - Requires GitHub token (free tier)

---

# 🤖 **CURSOR PROMPT**

```
I want you to build a Research Agent MVP using Python and Streamlit. This is a web scraping and research tool for academic/college research purposes.

## PROJECT REQUIREMENTS:

### Core Functionality:
- Input: Topic/field selection, date range
- Output: Latest news/research articles, summaries, markdown export
- Interface: Streamlit web app
- Storage: Local files (JSON + Markdown)

### Data Sources to Implement (Phase 1 - Easy ones first):
1. **Hacker News** - Use Algolia API (no auth required)
2. **ArXiv** - RSS feeds for research papers  
3. **RSS Feeds** - TechCrunch, MIT Tech Review, Wired
4. **Basic web scraping** - Using requests + BeautifulSoup

### Required Libraries:
```
streamlit
requests
feedparser
beautifulsoup4
newspaper3k
pandas
python-dotenv
datetime
json
pathlib
fake-useragent
httpx
plotly (for basic charts)
```

### Project Structure:
```
research_agent/
├── app.py                 # Main Streamlit app
├── src/
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── hackernews.py   # Hacker News API
│   │   ├── arxiv.py        # ArXiv RSS
│   │   ├── rss_parser.py   # General RSS parser
│   │   └── utils.py        # Common utilities
│   ├── storage/
│   │   ├── __init__.py
│   │   └── file_manager.py # Save/load data
│   └── processors/
│       ├── __init__.py
│       └── content_processor.py # Clean & process articles
├── data/
│   ├── raw/               # Raw scraped data
│   └── processed/         # Cleaned data
├── requirements.txt
├── .env.example
└── README.md
```

### Specific Implementation Details:

#### 1. Hacker News Integration:
- Use Algolia API: `https://hn.algolia.com/api/v1/search`
- Search by topic keywords
- Get stories from last 7/30 days
- Extract: title, url, points, comments_count, created_at

#### 2. ArXiv Integration:
- Use RSS feeds like: `http://export.arxiv.org/rss/cs.AI`
- Categories: cs.AI, cs.LG, cs.CL, etc.
- Extract: title, authors, abstract, pdf_url, published_date

#### 3. RSS Parser:
- Sources to include:
  - TechCrunch: `https://techcrunch.com/feed/`
  - MIT Tech Review: `https://www.technologyreview.com/feed/`
  - Wired: `https://www.wired.com/feed/`
- Extract: title, description, link, published_date

#### 4. Streamlit UI Components:
- **Sidebar:** Topic selection, date range, source selection
- **Main area:** Results display with tabs (All Articles, Summaries, Export)
- **Topic options:** AI/ML, Blockchain, Startups, Web3, Cybersecurity, Biotech
- **Display format:** Cards showing title, source, date, summary, link

#### 5. Data Processing:
- Remove duplicates based on title similarity
- Extract clean article content using newspaper3k
- Generate basic summaries (first 2 sentences)
- Sort by relevance and date

#### 6. Storage System:
- Save raw data as JSON with timestamp
- Generate markdown reports
- Create daily folders for organization

#### 7. Key Functions to Implement:
```python
# Core functions needed:
def fetch_hackernews(topic, days=7)
def fetch_arxiv_papers(category, days=7)  
def parse_rss_feeds(sources, topic, days=7)
def process_articles(raw_articles)
def save_to_markdown(articles, filename)
def display_streamlit_ui()
```

### Streamlit App Flow:
1. **Header:** App title and description
2. **Sidebar:** Input controls (topic, date range, sources)
3. **Main area:** 
   - Loading spinner during fetch
   - Results in expandable cards
   - Export button
   - Simple metrics (total articles, sources used)

### Error Handling:
- Try/except for all API calls
- Fallback to cached data if APIs fail
- User-friendly error messages in Streamlit
- Log errors to file for debugging

### Success Criteria:
- User can select "AI" topic and get 20+ relevant articles
- Results show within 30 seconds
- Can export to clean markdown file
- UI is intuitive and responsive
- No crashes on API failures

Build this as a complete, working application. Include:
1. All necessary imports
2. Complete functions with error handling
3. Working Streamlit interface
4. File structure as specified
5. Requirements.txt with all dependencies
6. Basic README with setup instructions

Make it production-ready but simple. Focus on functionality over fancy features. The goal is to have a working research tool that can fetch and display recent tech news/research based on user topics.

Start with the project structure and then implement each component. Make sure everything works together as a cohesive application.
```
