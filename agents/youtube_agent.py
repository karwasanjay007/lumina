"""
YouTube Research Agent - FIXED VERSION
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
    if _SUMMARY_PROMPT_PATH.exists():
        return _SUMMARY_PROMPT_PATH.read_text(encoding="utf-8")
    return _DEFAULT_SUMMARY_PROMPT


def _get_session() -> Session:
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
    session = _get_session()
    url = "https://www.googleapis.com/youtube/v3/search"
    
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "key": api_key,
        "maxResults": max_results * extra_factor,
        "relevanceLanguage": "en",
        "order": "relevance",
        "safeSearch": "none",
        "videoEmbeddable": "true",
        "publishedAfter": (
            datetime.utcnow() - timedelta(days=_PUBLISHED_AFTER_DAYS)
        ).isoformat() + "Z",
    }
    
    response = session.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    results = []
    for item in data.get("items", []):
        video_id = item["id"].get("videoId")
        snippet = item.get("snippet", {})
        
        results.append({
            "video_id": video_id,
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "channel": snippet.get("channelTitle", ""),
            "channel_id": snippet.get("channelId", ""),
            "published_at": snippet.get("publishedAt", ""),
            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        })
    
    return results


def _fetch_video_details(api_key: str, video_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    if not video_ids:
        return {}
    
    session = _get_session()
    url = "https://www.googleapis.com/youtube/v3/videos"
    
    params = {
        "part": "snippet,contentDetails,statistics",
        "id": ",".join(video_ids),
        "key": api_key,
    }
    
    response = session.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    details_map = {}
    for item in data.get("items", []):
        video_id = item.get("id")
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        content = item.get("contentDetails", {})
        
        details_map[video_id] = {
            "description": snippet.get("description", ""),
            "tags": snippet.get("tags", []),
            "category_id": snippet.get("categoryId", ""),
            "default_language": snippet.get("defaultLanguage", ""),
            "duration": content.get("duration", ""),
            "views": stats.get("viewCount", "0"),
            "likes": stats.get("likeCount", "0"),
            "comments": stats.get("commentCount", "0"),
        }
    
    return details_map


def _parse_duration(iso_duration: str) -> str:
    import re
    match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_duration)
    if not match:
        return "Unknown"
    
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def _summarize_video(
    title: str,
    channel: str,
    description: str,
    url: str,
    tags: List[str],
    views: str,
    duration: str,
) -> Tuple[str, Dict[str, Any]]:
    prompt_template = _load_summary_prompt()
    truncated_desc = description[:_SUMMARY_MAX_CHARS]
    if len(description) > _SUMMARY_MAX_CHARS:
        truncated_desc += "..."
    
    tags_str = ", ".join(tags[:10]) if tags else "None"
    
    prompt = prompt_template.format(
        title=title,
        channel=channel,
        url=url,
        description=truncated_desc,
        tags=tags_str,
        views=views,
        duration=duration
    )
    
    try:
        result = invoke_llm(prompt, model="youtube_summarizer")
        summary_text = result.get("response", "")
        metrics = result.get("metrics", zero_metrics())
        return summary_text, metrics
    except Exception as exc:
        logger.warning(f"Failed to summarize video: {exc}")
        return f"Video: {title}\nChannel: {channel}\nViews: {views}\nDuration: {duration}", zero_metrics()


def research_youtube_videos(state: ResearchState, mode: str = "simple") -> dict:
    start = time.time()
    topic = state["research_topic"]
    logger.info(f"Analyzing YouTube videos for topic: {topic} (mode={mode})")
    
    api_key = get_youtube_api_key()
    
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
    
    video_ids = [item["video_id"] for item in search_results]
    try:
        video_details = _fetch_video_details(api_key, video_ids)
    except Exception as exc:
        logger.warning("Failed to fetch video details: %s", exc)
        video_details = {}
    
    run_id = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    run_dir = DATA_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    summaries: List[Dict[str, Any]] = []
    metadata_records: List[Dict[str, Any]] = []
    total_tokens = 0
    total_cost = 0.0
    
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
        
        item = build_structured_record(
            published_date=video.get("published_at", ""),
            title=video.get("title", ""),
            authors=[video.get("channel", "")] if video.get("channel") else None,
            summary=summary_text,
            content=None,
            source=url,
            pdf_url=None,
        )
        summaries.append(item)
        
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
    
    elapsed = time.time() - start
    
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
    
    return {
        "youtube_results": {
            "sources": summaries,
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