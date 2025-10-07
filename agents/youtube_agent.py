"""
YouTube Research Agent - Using YouTube Data API v3 Only
NO FFmpeg, NO yt_dlp, NO whisper dependencies
FIXED VERSION - Corrected build_structured_record calls
"""
from __future__ import annotations

import json
import logging
import time
from functools import lru_cache
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import requests
from requests import Session

from graph.state import ResearchState
from utils.config_loader import get_youtube_api_key
from utils.llm_registry import invoke_llm, zero_metrics
from utils.structured_data import build_structured_record

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "youtube"
DATA_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

# Configuration
_PUBLISHED_AFTER_DAYS = 365
_MAX_RESULTS_SIMPLE = 3
_MAX_RESULTS_EXTENDED = 5
_SUMMARY_MAX_CHARS = 2000

_SUMMARY_PROMPT_PATH = Path(__file__).resolve().parents[1] / 'prompts' / 'youtube_summary_prompt.txt'
_DEFAULT_SUMMARY_PROMPT = (
    'You are summarising insights from a YouTube video.\n'
    'Title: {title}\n'
    'Channel: {channel}\n'
    'URL: {url}\n'
    'Description: {description}\n\n'
    'Provide a concise summary based on the title, description, and available metadata. '
    'Focus on key insights, main topics covered, and potential value for research.'
)

_session: Optional[Session] = None


@lru_cache(maxsize=1)
def _load_summary_prompt() -> str:
    """Load the YouTube summary prompt template, cached across runs."""
    if _SUMMARY_PROMPT_PATH.exists():
        return _SUMMARY_PROMPT_PATH.read_text(encoding="utf-8")
    return _DEFAULT_SUMMARY_PROMPT


def _get_session() -> Session:
    """Return a singleton HTTP session for YouTube API calls."""
    global _session
    if _session is None:
        _session = Session()
        _session.headers.update({"Accept": "application/json"})
    return _session


def _search_videos(
    api_key: str, 
    query: str, 
    max_results: int,
    extra_factor: int = 3
) -> List[Dict[str, Any]]:
    """Search YouTube videos using Data API v3."""
    session = _get_session()
    published_after = (datetime.utcnow() - timedelta(days=_PUBLISHED_AFTER_DAYS)).isoformat("T") + "Z"
    
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "publishedAfter": published_after,
        "maxResults": max_results * extra_factor,
        "order": "relevance",
        "key": api_key,
    }
    
    response = session.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    
    results = []
    for item in data.get("items", []):
        snippet = item.get("snippet", {})
        results.append({
            "video_id": item["id"]["videoId"],
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "channel_id": snippet.get("channelId", ""),
            "description": snippet.get("description", ""),
            "published_at": snippet.get("publishedAt", ""),
            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        })
    
    return results


def _fetch_video_details(api_key: str, video_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Fetch detailed video information using Data API v3."""
    if not video_ids:
        return {}
    
    session = _get_session()
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "contentDetails,statistics,snippet",
        "id": ",".join(video_ids),
        "key": api_key,
    }
    
    response = session.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    
    details = {}
    for item in data.get("items", []):
        video_id = item["id"]
        content = item.get("contentDetails", {})
        stats = item.get("statistics", {})
        snippet = item.get("snippet", {})
        
        details[video_id] = {
            "duration": content.get("duration", ""),
            "views": stats.get("viewCount", "0"),
            "likes": stats.get("likeCount", "0"),
            "comments": stats.get("commentCount", "0"),
            "description": snippet.get("description", ""),
            "tags": snippet.get("tags", []),
            "category_id": snippet.get("categoryId", ""),
            "default_language": snippet.get("defaultLanguage", ""),
        }
    
    return details


def _parse_duration(iso_duration: str) -> str:
    """Convert ISO 8601 duration to human-readable format."""
    if not iso_duration or not iso_duration.startswith("PT"):
        return "N/A"
    
    import re
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, iso_duration)
    
    if not match:
        return "N/A"
    
    hours, minutes, seconds = match.groups()
    parts = []
    
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds:
        parts.append(f"{seconds}s")
    
    return " ".join(parts) if parts else "N/A"


def _summarize_video(
    title: str,
    channel: str,
    description: str,
    url: str,
    tags: List[str],
    views: str,
    duration: str
) -> Tuple[str, Dict[str, Any]]:
    """Generate AI summary from video metadata."""
    if not title and not description:
        return "No content available for summary.", {
            "total_tokens": 0,
            "cost": 0.0,
            "prompt_tokens": 0,
            "completion_tokens": 0
        }
    
    prompt_template = _load_summary_prompt()
    
    description_excerpt = description[:_SUMMARY_MAX_CHARS]
    if len(description) > _SUMMARY_MAX_CHARS:
        description_excerpt += "..."
    
    prompt = prompt_template.format(
        title=title or 'Unknown title',
        channel=channel or 'Unknown channel',
        url=url,
        description=description_excerpt,
    )
    
    context_parts = []
    if tags:
        context_parts.append(f"Tags: {', '.join(tags[:10])}")
    if views and views != "0":
        context_parts.append(f"Views: {views}")
    if duration and duration != "N/A":
        context_parts.append(f"Duration: {duration}")
    
    if context_parts:
        prompt += "\n\nAdditional Context:\n" + "\n".join(context_parts)
    
    response, metrics = invoke_llm("youtube_summarizer", prompt)
    
    metrics_dict = {
        "total_tokens": getattr(metrics, 'total_tokens', 0),
        "cost": getattr(metrics, 'cost', 0.0),
        "prompt_tokens": getattr(metrics, 'prompt_tokens', 0),
        "completion_tokens": getattr(metrics, 'completion_tokens', 0)
    }
    
    return response.content.strip(), metrics_dict


def analyze_youtube(state: ResearchState) -> Dict[str, Dict]:
    """
    Collect and summarize YouTube videos using only YouTube Data API v3
    
    NO transcripts, NO FFmpeg, NO whisper - pure API-based analysis
    """
    start = time.time()
    api_key = get_youtube_api_key()
    topic = state.get("topic", "")
    mode = state.get("mode", "extended")
    
    if not api_key:
        elapsed = time.time() - start
        logger.warning("YouTube API key not configured")
        return {
            "youtube_results": {
                "sources": [],
                "elapsed": elapsed,
                "tokens": 0,
                "cost": 0.0,
                "details": {"error": "YOUTUBE_API_KEY not configured"},
            }
        }
    
    max_results = _MAX_RESULTS_SIMPLE if mode == "simple" else _MAX_RESULTS_EXTENDED
    
    # Search for videos
    try:
        search_results = _search_videos(api_key, topic, max_results, extra_factor=3)
        search_results.sort(key=lambda item: item.get("published_at", ""), reverse=True)
    except Exception as exc:
        elapsed = time.time() - start
        logger.exception("YouTube search failed")
        return {
            "youtube_results": {
                "sources": [],
                "elapsed": elapsed,
                "tokens": 0,
                "cost": 0.0,
                "details": {"error": f"YouTube search failed: {exc}"},
            }
        }
    
    # Get detailed video information
    video_ids = [item["video_id"] for item in search_results]
    try:
        video_details = _fetch_video_details(api_key, video_ids)
    except Exception as exc:
        logger.warning("Failed to fetch video details: %s", exc)
        video_details = {}
    
    # Create output directory
    run_id = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    run_dir = DATA_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    summaries: List[Dict[str, Any]] = []
    metadata_records: List[Dict[str, Any]] = []
    
    total_tokens = 0
    total_cost = 0.0
    
    # Process each video
    for video in search_results:
        if len(summaries) >= max_results:
            break
        
        video_id = video["video_id"]
        url = f"https://www.youtube.com/watch?v={video_id}"
        metadata = video_details.get(video_id, {})
        
        # Get full description and tags from detailed metadata
        full_description = metadata.get("description", video.get("description", ""))
        tags = metadata.get("tags", [])
        views = metadata.get("views", "0")
        duration = _parse_duration(metadata.get("duration", ""))
        
        # Summarize based on metadata only (no transcript)
        summary_text, metrics = _summarize_video(
            video.get("title", ""),
            video.get("channel", ""),
            full_description,
            url,
            tags,
            views,
            duration
        )
        
        total_tokens += metrics.get("total_tokens", 0)
        total_cost += metrics.get("cost", 0.0)
        
        # Build summary item with correct parameters
        item = build_structured_record(
            published_date=video.get("published_at", ""),
            title=video.get("title", ""),
            authors=[video.get("channel", "")] if video.get("channel") else None,
            summary=summary_text,
            content=None,  # No transcript content
            source=url,
            pdf_url=None,
        )
        summaries.append(item)
        
        # Build metadata record
        meta_rec = {
            "video_id": video_id,
            "channel_id": video.get("channel_id", ""),
            "duration": duration,
            "views": views,
            "likes": metadata.get("likes", "0"),
            "comments": metadata.get("comments", "0"),
            "description": full_description[:500],
            "tags": tags[:10],
            "thumbnail": video.get("thumbnail", ""),
            "category_id": metadata.get("category_id", ""),
            "language": metadata.get("default_language", "unknown"),
        }
        metadata_records.append(meta_rec)
    
    # Save results
    elapsed = time.time() - start
    
    # Save metadata to JSON file
    metadata_file = run_dir / "metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata_records, f, indent=2, ensure_ascii=False)
    
    logger.info(
        "YouTube analysis complete: %d videos, %.2fs, %d tokens, $%.4f",
        len(summaries),
        elapsed,
        total_tokens,
        total_cost
    )
    
    # FIXED: Return structured sources directly without wrapping
    # The summaries list already contains properly structured records
    return {
        "youtube_results": {
            "sources": summaries,  # FIXED: Direct list of structured records
            "elapsed": elapsed,
            "tokens": total_tokens,
            "cost": total_cost,
            "details": {
                "search_count": len(search_results),
                "processed_count": len(summaries),
                "data_dir": str(run_dir),
                "mode": "api_only",
                "api_version": "v3",
                "no_transcripts": True,
                "metadata_file": str(metadata_file),
            },
        }
    }