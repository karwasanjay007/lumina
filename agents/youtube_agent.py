"""
YouTube Agent with proper token tracking
Industry-standard implementation
"""

import os
import aiohttp
from typing import Dict, List, Any
from datetime import datetime


class YouTubeAgent:
    """
    YouTube video research agent with token tracking
    """
    
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        self.api_url = "https://www.googleapis.com/youtube/v3/search"
        
        # Token estimation for YouTube metadata
        self.avg_tokens_per_video = 200  # Estimated tokens per video metadata
        
    async def research(
        self,
        query: str,
        domain: str = "general",
        max_sources: int = 10
    ) -> Dict[str, Any]:
        """
        Execute YouTube research
        
        Args:
            query: Research question
            domain: Research domain
            max_sources: Maximum videos to fetch
            
        Returns:
            Dictionary with research results and metrics
        """
        print(f"   📹 YouTube Agent: Searching videos for '{query}'")
        
        if not self.api_key:
            print(f"   ⚠️ YouTube API key not configured")
            return {
                "agent_name": "youtube",
                "agent_type": "youtube",
                "status": "skipped",
                "message": "YouTube API key not configured",
                "sources": [],
                "source_count": 0,
                "tokens": 0,
                "cost": 0.0
            }
        
        try:
            sources = await self._search_videos(query, max_sources)
            
            # Estimate tokens based on actual content
            total_tokens = self._estimate_tokens(sources)
            
            # YouTube API is free (quota-based)
            cost = 0.0
            
            result = {
                "agent_name": "youtube",
                "agent_type": "youtube",
                "status": "success",
                "query": query,
                "domain": domain,
                "sources": sources,
                "source_count": len(sources),
                "tokens": total_tokens,  # Properly tracked
                "cost": cost,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"   ✅ YouTube: {len(sources)} videos, {total_tokens} estimated tokens")
            
            return result
            
        except Exception as e:
            print(f"   ❌ YouTube error: {e}")
            return {
                "agent_name": "youtube",
                "agent_type": "youtube",
                "status": "error",
                "error": str(e),
                "sources": [],
                "source_count": 0,
                "tokens": 0,
                "cost": 0.0
            }
    
    async def _search_videos(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search YouTube videos
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of video sources
        """
        sources = []
        
        try:
            params = {
                "key": self.api_key,
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": min(max_results, 50),
                "order": "relevance",
                "relevanceLanguage": "en"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.api_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
            
            items = data.get('items', [])
            
            for item in items:
                video_id = item.get('id', {}).get('videoId', '')
                snippet = item.get('snippet', {})
                
                if video_id:
                    sources.append({
                        "title": snippet.get('title', 'No Title'),
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "description": snippet.get('description', 'No description')[:200] + "...",
                        "source_type": "youtube",
                        "channel": snippet.get('channelTitle', 'Unknown'),
                        "published_at": snippet.get('publishedAt', '')
                    })
            
        except Exception as e:
            print(f"   ⚠️ YouTube search error: {e}")
        
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
            channel = source.get('channel', '')
            
            # Rough estimation: 1 token ≈ 4 characters
            title_tokens = len(title) // 4
            desc_tokens = len(description) // 4
            channel_tokens = len(channel) // 4
            
            # Add metadata overhead (URL, type, published date) - approximately 25 tokens
            metadata_tokens = 25
            
            total_tokens += title_tokens + desc_tokens + channel_tokens + metadata_tokens
        
        return total_tokens