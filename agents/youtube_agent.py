# ============================================================================
# ISSUE 2: Fix YouTube Agent - Simplified Version WITHOUT transcript API
# FILE: agents/youtube_agent.py
# ============================================================================
"""
YouTube Agent - Simplified without transcript dependency
"""
import os
from typing import Dict, List
import requests

def search_youtube(query: str, max_results: int = 2) -> List[Dict]:
    """
    Search YouTube videos - NO TRANSCRIPT NEEDED
    
    Args:
        query: Search query
        max_results: Maximum number of videos to return
        
    Returns:
        List of video dictionaries
    """
    try:
        api_key = os.getenv("YOUTUBE_API_KEY")
        
        if not api_key:
            print(f"   ⚠️  YOUTUBE_API_KEY not found")
            return []
        
        from datetime import datetime, timedelta
        
        # Calculate date 30 days ago
        published_after = (datetime.utcnow() - timedelta(days=30)).isoformat("T") + "Z"
        
        # Search YouTube API directly
        search_url = "https://www.googleapis.com/youtube/v3/search"
        search_params = {
            "key": api_key,
            "q": query,
            "type": "video",
            "part": "id,snippet",
            "maxResults": max_results * 3,  # Get extra to filter
            "relevanceLanguage": "en",
            "order": "relevance",
            "publishedAfter": published_after,
            "safeSearch": "moderate",
        }
        
        print(f"   📡 Calling YouTube API...")
        response = requests.get(search_url, params=search_params, timeout=20)
        
        if response.status_code != 200:
            print(f"   ❌ YouTube API error: {response.status_code}")
            return []
        
        data = response.json()
        items = data.get("items", [])
        
        if not items:
            print(f"   ⚠️  No videos found")
            return []
        
        # Get video IDs
        video_ids = [item.get("id", {}).get("videoId") for item in items if item.get("id", {}).get("videoId")]
        
        if not video_ids:
            print(f"   ⚠️  No valid video IDs")
            return []
        
        # Fetch video details (duration, views, etc.)
        videos_url = "https://www.googleapis.com/youtube/v3/videos"
        videos_params = {
            "key": api_key,
            "id": ",".join(video_ids[:max_results]),
            "part": "contentDetails,statistics,snippet",
        }
        
        details_response = requests.get(videos_url, params=videos_params, timeout=20)
        
        if details_response.status_code != 200:
            print(f"   ⚠️  Could not fetch video details")
            # Return basic info without details
            results = []
            for item in items[:max_results]:
                snippet = item.get("snippet", {})
                video_id = item.get("id", {}).get("videoId")
                results.append({
                    "title": snippet.get("title", ""),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "description": snippet.get("description", ""),
                    "channel": snippet.get("channelTitle", ""),
                    "duration": "Unknown",
                    "views": 0,
                    "published_at": snippet.get("publishedAt", "")
                })
            return results
        
        details_data = details_response.json()
        details_items = details_data.get("items", [])
        
        # Format results with details
        results = []
        for detail_item in details_items[:max_results]:
            video_id = detail_item.get("id")
            snippet = detail_item.get("snippet", {})
            content_details = detail_item.get("contentDetails", {})
            statistics = detail_item.get("statistics", {})
            
            # Parse duration (ISO 8601 format like PT15M30S)
            duration_iso = content_details.get("duration", "")
            duration = _parse_duration(duration_iso)
            
            results.append({
                "title": snippet.get("title", ""),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "description": snippet.get("description", "")[:200],  # Limit description
                "channel": snippet.get("channelTitle", ""),
                "duration": duration,
                "views": int(statistics.get("viewCount", 0)),
                "published_at": snippet.get("publishedAt", "")
            })
        
        print(f"   ✅ Found {len(results)} videos")
        return results
        
    except Exception as e:
        print(f"   ❌ YouTube error: {e}")
        import traceback
        traceback.print_exc()
        return []


def _parse_duration(iso_duration: str) -> str:
    """Convert YouTube ISO 8601 duration to readable format"""
    if not iso_duration:
        return "Unknown"
    
    hours = minutes = seconds = 0
    current = ""
    
    # Skip PT prefix
    for ch in iso_duration[2:]:
        if ch.isdigit():
            current += ch
        elif ch == "H":
            hours = int(current or 0)
            current = ""
        elif ch == "M":
            minutes = int(current or 0)
            current = ""
        elif ch == "S":
            seconds = int(current or 0)
            current = ""
    
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"
