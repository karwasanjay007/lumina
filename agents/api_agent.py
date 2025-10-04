# ============================================================================
# FIX 3: API Agent - Better News Sources
# Replace your api_agent.py with this improved version
# FILE: agents/api_agent.py
# ============================================================================

"""
API Agent - Improved with better news sources
"""
import os
from typing import Dict, List
from datetime import datetime
import requests
import json


class APIAgent:
    """Agent for fetching data from various APIs"""
    
    def __init__(self):
        self.name = "API Agent"
    
    def execute(self, query: str, domain: str) -> Dict:
        """
        Execute API agent with improved news sources
        
        Args:
            query: Research query
            domain: Research domain
            
        Returns:
            Dict with papers, summary, findings, insights
        """
        try:
            print(f"   📚 API Agent starting for domain: {domain}")
            print(f"   🔍 Query: {query}")
            
            papers = []
            findings = []
            insights = []
            summary = ""
            
            # Route based on domain
            if domain in ["academic", "medical"]:
                print(f"   🎓 Using arXiv for {domain} domain")
                papers = self._fetch_arxiv(query)
                
                if papers:
                    print(f"   ✅ arXiv: {len(papers)} papers")
                    findings.append(f"Found {len(papers)} academic papers on {query}")
                    insights.append(f"Research is active in this area")
                    summary = f"Retrieved {len(papers)} academic papers from arXiv"
            
            elif domain in ["stocks", "technology", "general"]:
                print(f"   🌐 Using news sources for {domain} domain")
                
                # Try multiple news sources
                papers = []
                
                # Try NewsAPI (if you have key)
                newsapi_results = self._fetch_newsapi(query)
                if newsapi_results:
                    papers.extend(newsapi_results)
                    print(f"   ✅ NewsAPI: {len(newsapi_results)} articles")
                
                # Try Bing News Search (no key needed)
                if len(papers) < 5:
                    bing_results = self._fetch_bing_news(query)
                    if bing_results:
                        papers.extend(bing_results)
                        print(f"   ✅ Bing News: {len(bing_results)} articles")
                
                # Fallback: Web scraping from Google News
                if len(papers) < 2:
                    google_results = self._fetch_google_news(query)
                    if google_results:
                        papers.extend(google_results)
                        print(f"   ✅ Google News: {len(google_results)} articles")
                
                if papers:
                    findings.append(f"Found {len(papers)} news articles on {query}")
                    insights.append(f"Topic is covered in recent news")
                    summary = f"Retrieved {len(papers)} news articles"
                else:
                    print(f"   ⚠️  No news articles found")
                    summary = "No news articles found - try arXiv or web search"
            
            print(f"   ✅ API Agent complete: {len(papers)} sources retrieved")
            
            return {
                "papers": papers,
                "summary": summary,
                "findings": findings,
                "insights": insights
            }
            
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "papers": [],
                "summary": f"Error: {str(e)}",
                "findings": [],
                "insights": []
            }
    
    def _fetch_arxiv(self, query: str, max_results: int = 10) -> List[Dict]:
        """Fetch papers from arXiv API"""
        try:
            import urllib.parse
            import xml.etree.ElementTree as ET
            
            base_url = "http://export.arxiv.org/api/query"
            search_query = urllib.parse.quote(query)
            url = f"{base_url}?search_query=all:{search_query}&start=0&max_results={max_results}"
            
            response = requests.get(url, timeout=20)
            if response.status_code != 200:
                return []
            
            root = ET.fromstring(response.content)
            papers = []
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                title_elem = entry.find('atom:title', ns)
                summary_elem = entry.find('atom:summary', ns)
                link_elem = entry.find('atom:id', ns)
                published_elem = entry.find('atom:published', ns)
                
                authors = []
                for author in entry.findall('atom:author', ns):
                    name_elem = author.find('atom:name', ns)
                    if name_elem is not None:
                        authors.append(name_elem.text)
                
                papers.append({
                    "title": title_elem.text.strip() if title_elem is not None else "",
                    "url": link_elem.text if link_elem is not None else "",
                    "summary": summary_elem.text.strip()[:200] if summary_elem is not None else "",
                    "authors": authors,
                    "published": published_elem.text[:10] if published_elem is not None else "",
                    "type": "academic"
                })
            
            return papers
            
        except Exception as e:
            print(f"      ⚠️  arXiv error: {e}")
            return []
    
    def _fetch_newsapi(self, query: str, max_results: int = 5) -> List[Dict]:
        """Fetch from NewsAPI (requires free API key)"""
        try:
            api_key = os.getenv("NEWSAPI_KEY")
            if not api_key:
                return []
            
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "apiKey": api_key,
                "pageSize": max_results,
                "language": "en",
                "sortBy": "relevancy"
            }
            
            response = requests.get(url, params=params, timeout=20)
            if response.status_code != 200:
                return []
            
            data = response.json()
            articles = data.get("articles", [])
            
            papers = []
            for article in articles[:max_results]:
                papers.append({
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "summary": article.get("description", "")[:200],
                    "published": article.get("publishedAt", "")[:10],
                    "type": "news"
                })
            
            return papers
            
        except Exception as e:
            print(f"      ⚠️  NewsAPI error: {e}")
            return []
    
    def _fetch_bing_news(self, query: str, max_results: int = 5) -> List[Dict]:
        """Fetch from Bing News (requires free API key)"""
        try:
            api_key = os.getenv("BING_SEARCH_KEY")
            if not api_key:
                return []
            
            url = "https://api.bing.microsoft.com/v7.0/news/search"
            headers = {"Ocp-Apim-Subscription-Key": api_key}
            params = {
                "q": query,
                "count": max_results,
                "mkt": "en-US",
                "freshness": "Month"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=20)
            if response.status_code != 200:
                return []
            
            data = response.json()
            articles = data.get("value", [])
            
            papers = []
            for article in articles[:max_results]:
                papers.append({
                    "title": article.get("name", ""),
                    "url": article.get("url", ""),
                    "summary": article.get("description", "")[:200],
                    "published": article.get("datePublished", "")[:10],
                    "type": "news"
                })
            
            return papers
            
        except Exception as e:
            print(f"      ⚠️  Bing News error: {e}")
            return []
    
    def _fetch_google_news(self, query: str, max_results: int = 5) -> List[Dict]:
        """Fetch from Google News RSS (no API key needed)"""
        try:
            import urllib.parse
            import xml.etree.ElementTree as ET
            
            # Google News RSS feed
            search_query = urllib.parse.quote(query)
            url = f"https://news.google.com/rss/search?q={search_query}&hl=en-US&gl=US&ceid=US:en"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code != 200:
                return []
            
            root = ET.fromstring(response.content)
            papers = []
            
            for item in root.findall('.//item')[:max_results]:
                title = item.find('title')
                link = item.find('link')
                description = item.find('description')
                pub_date = item.find('pubDate')
                
                papers.append({
                    "title": title.text if title is not None else "",
                    "url": link.text if link is not None else "",
                    "summary": (description.text if description is not None else "")[:200],
                    "published": (pub_date.text if pub_date is not None else "")[:10],
                    "type": "news"
                })
            
            return papers
            
        except Exception as e:
            print(f"      ⚠️  Google News error: {e}")
            return []
    
    def get_status(self) -> Dict:
        """Get agent status"""
        return {
            "name": self.name,
            "type": "api",
            "available": True
        }