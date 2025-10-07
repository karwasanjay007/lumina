"""
YouTube Research Agent - FIXED VERSION (Metrics Error Resolved)
Using YouTube Data API v3 Only - NO FFmpeg dependencies
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
    """Load the YouTube summary prompt template"""
    if _SUMMARY_PROMPT_PATH.exists():
        return _SUMMARY_PROMPT_PATH.read_text(encoding="utf-8")
    return _DEFAULT_SUMMARY_PROMPT


def _get_session() -> Session:
    """Return a singleton HTTP session for YouTube API calls"""
    global _session
    if _session is None:
        _session = Session()
        _session.headers.update({"Accept": "application/json"})
    return _session


def _search_videos(
    api_key: str,
    query: str,
    max_results: int = 5,
    extra_factor: int = 2,
) -> List[Dict[str, Any]]:
    """Search YouTube videos using YouTube Data API v3"""
    session = _get_session()
    published_after = (datetime.utcnow() - timedelta(days=_PUBLISHED_AFTER_DAYS)).isoformat("T") + "Z"
    
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": min(max_results * extra_factor, 50),
        "order": "relevance",
        "publishedAfter": published_after,
        "key": api_key,
        "relevanceLanguage": "en",
        "videoCaption": "any",
    }
    
    url = "https://www.googleapis.com/youtube/v3/search"
    
    try:
        resp = session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.exception("YouTube search failed for query '%s'", query)
        raise RuntimeError(f"YouTube search API error: {exc}") from exc
    
    results = []
    for item in data.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        if not video_id:
            continue
        
        snippet = item.get("snippet", {})
        results.append({
            "video_id": video_id,
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "channel_id": snippet.get("channelId", ""),
            "description": snippet.get("description", ""),
            "published_at": snippet.get("publishedAt", ""),
            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        })
    
    logger.info("Found %d videos for query '%s'", len(results), query)
    return results


def _fetch_video_details(api_key: str, video_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Fetch detailed metadata for videos using YouTube Data API v3"""
    if not video_ids:
        return {}
    
    session = _get_session()
    params = {
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(video_ids[:50]),
        "key": api_key,
    }
    
    url = "https://www.googleapis.com/youtube/v3/videos"
    
    try:
        resp = session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("Video details fetch failed: %s", exc)
        return {}
    
    details = {}
    for item in data.get("items", []):
        video_id = item.get("id")
        if not video_id:
            continue
        
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})
        
        details[video_id] = {
            "duration": content_details.get("duration", ""),
            "views": statistics.get("viewCount", "0"),
            "likes": statistics.get("likeCount", "0"),
            "comments": statistics.get("commentCount", "0"),
            "description": snippet.get("description", ""),
            "tags": snippet.get("tags", []),
            "category_id": snippet.get("categoryId", ""),
            "default_language": snippet.get("defaultLanguage", ""),
        }
    
    logger.info("Fetched details for %d videos", len(details))
    return details


def _parse_duration(duration_str: str) -> str:
    """Convert ISO 8601 duration to readable format"""
    if not duration_str or not duration_str.startswith("PT"):
        return "N/A"
    
    try:
        duration_str = duration_str[2:]
        hours = 0
        minutes = 0
        seconds = 0
        
        if "H" in duration_str:
            hours, duration_str = duration_str.split("H")
            hours = int(hours)
        
        if "M" in duration_str:
            minutes, duration_str = duration_str.split("M")
            minutes = int(minutes)
        
        if "S" in duration_str:
            seconds = int(duration_str.replace("S", ""))
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    except Exception as exc:
        logger.warning("Failed to parse duration '%s': %s", duration_str, exc)
        return "N/A"


def _summarize_video(
    title: str,
    channel: str,
    description: str,
    url: str,
    tags: List[str],
    views: str,
    duration: str
) -> Tuple[str, Dict[str, Any]]:
    """
    Summarize video based on metadata (no transcript needed)
    
    Returns:
        Tuple of (summary_text, metrics_dict)
    """
    if not description:
        return "No description available for analysis.", {
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
    
    # FIXED: Convert metrics object to dictionary
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
        
        full_description = metadata.get("description", video.get("description", ""))
        tags = metadata.get("tags", [])
        views = metadata.get("views", "0")
        duration = _parse_duration(metadata.get("duration", ""))
        
        # Summarize based on metadata only (no transcript)
        summary_text, metrics_dict = _summarize_video(
            video.get("title", ""),
            video.get("channel", ""),
            full_description,
            url,
            tags,
            views,
            duration
        )
        
        # FIXED: Use dictionary access instead of .get() on object
        total_tokens += metrics_dict["total_tokens"]
        total_cost += metrics_dict["cost"]
        
        # Build summary item
        item = {
            "published_date": video.get("published_at", ""),
            "title": video.get("title", ""),
            "authors": [video.get("channel", "")],
            "summary": summary_text,
            "content": None,
            "source": url,
            "pdf_url": None,
        }
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
    
    # Save metadata to JSON
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
    
    # Build structured output
    structured_sources = []
    for idx, (item, meta_rec) in enumerate(zip(summaries, metadata_records), start=1):
        structured_sources.append(
            build_structured_record(
                agent_name="YouTube",
                source_name=f"video_{idx}",
                items=[item],
                metadata=meta_rec
            )
        )
    
    return {
        "youtube_results": {
            "sources": structured_sources,
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
            },
        }
    }