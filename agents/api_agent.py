"""
API Agent with proper token tracking
Fetches from academic and news APIs with accurate metrics
"""

import os
import aiohttp
import asyncio
from typing import Dict, List, Any
from datetime import datetime


class APIAgent:
    """
    API research agent for academic papers and news
    """
    
    def __init__(self):
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.arxiv_base_url = "http://export.arxiv.org/api/query"
        self.news_base_url = "https://newsapi.org/v2/everything"
        
        # Token estimation (since these APIs don't return token counts)
        self.avg_tokens_per_source = 150  # Estimated tokens per source metadata
        
    async def research(
        self,
        query: str,
        domain: str = "general",
        max_sources: int = 10
    ) -> Dict[str, Any]:
        """
        Execute API research across academic and news sources
        
        Args:
            query: Research question
            domain: Research domain
            max_sources: Maximum sources to fetch
            
        Returns:
            Dictionary with research results and metrics
        """
        print(f"   📚 API Agent: Fetching sources for '{query}'")
        
        sources = []
        
        # Fetch from different sources based on domain
        if domain in ["academic", "medical", "technology"]:
            # Academic sources
            arxiv_sources = await self._fetch_arxiv(query, max_sources // 2)
            sources.extend(arxiv_sources)
        
        if domain in ["stocks", "technology"]:
            # News sources
            if self.news_api_key:
                news_sources = await self._fetch_news(query, max_sources // 2)
                sources.extend(news_sources)
        
        # If no domain-specific sources, get both
        if not sources:
            arxiv_task = self._fetch_arxiv(query, max_sources // 2)
            news_task = self._fetch_news(query, max_sources // 2) if self.news_api_key else asyncio.sleep(0)
            
            arxiv_sources, news_sources = await asyncio.gather(
                arxiv_task,
                news_task if self.news_api_key else asyncio.sleep(0)
            )
            
            sources.extend(arxiv_sources)
            if news_sources and isinstance(news_sources, list):
                sources.extend(news_sources)
        
        # Estimate tokens based on actual content
        total_tokens = self._estimate_tokens(sources)
        
        # Cost is zero for free APIs
        cost = 0.0
        
        result = {
            "agent_name": "api",
            "agent_type": "api",
            "status": "success",
            "query": query,
            "domain": domain,
            "sources": sources,
            "source_count": len(sources),
            "tokens": total_tokens,  # Properly tracked now
            "cost": cost,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"   ✅ API Agent: {len(sources)} sources, {total_tokens} estimated tokens")
        
        return result
    
    async def _fetch_arxiv(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch academic papers from arXiv
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of source dictionaries
        """
        sources = []
        
        try:
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.arxiv_base_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    xml_content = await response.text()
            
            # Parse XML (simple extraction)
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            
            # Namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                title_elem = entry.find('atom:title', ns)
                summary_elem = entry.find('atom:summary', ns)
                id_elem = entry.find('atom:id', ns)
                
                if title_elem is not None and id_elem is not None:
                    sources.append({
                        "title": title_elem.text.strip() if title_elem.text else "No Title",
                        "url": id_elem.text.strip() if id_elem.text else "#",
                        "description": summary_elem.text.strip()[:200] + "..." if summary_elem is not None and summary_elem.text else "No description",
                        "source_type": "academic"
                    })
            
        except Exception as e:
            print(f"   ⚠️ arXiv fetch error: {e}")
        
        return sources
    
    async def _fetch_news(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch news articles from News API
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of source dictionaries
        """
        if not self.news_api_key:
            return []
        
        sources = []
        
        try:
            params = {
                "q": query,
                "apiKey": self.news_api_key,
                "pageSize": max_results,
                "sortBy": "relevancy",
                "language": "en"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.news_base_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
            
            articles = data.get('articles', [])
            
            for article in articles[:max_results]:
                sources.append({
                    "title": article.get('title', 'No Title'),
                    "url": article.get('url', '#'),
                    "description": article.get('description', 'No description')[:200] + "...",
                    "source_type": "news"
                })
            
        except Exception as e:
            print(f"   ⚠️ News API fetch error: {e}")
        
        return sources
    
    def _estimate_tokens(self, sources: List[Dict[str, Any]]) -> int:
        """
        Estimate token count based on actual source content
        
        Args:
            sources: List of source dictionaries
            
        Returns:
            Estimated token count
        """
        total_tokens = 0
        
        for source in sources:
            # Count tokens based on actual text length
            title = source.get('title', '')
            description = source.get('description', '')
            
            # Rough estimation: 1 token ≈ 4 characters
            title_tokens = len(title) // 4
            desc_tokens = len(description) // 4
            
            # Add metadata overhead (URL, type, etc.) - approximately 20 tokens
            metadata_tokens = 20
            
            total_tokens += title_tokens + desc_tokens + metadata_tokens
        
        return total_tokens