"""
Original Working Perplexity Client - Based on tools/perplexity_client.py
This is the version that was working before!
services/perplexity_client.py
"""
from __future__ import annotations

import re
import time
from typing import Any, Dict, Iterable, List, Optional

import requests

_DEFAULT_BASE_URL = "https://api.perplexity.ai"
_DEFAULT_MODEL = "sonar-pro"
_DEFAULT_TIMEOUT = 120  # Original working timeout
_BULLET_MARKERS = ("-", "*", "\u2022", "\u2023", "\u00b7")


def _safe_text(response: requests.Response) -> str:
    try:
        return response.text[:500]
    except Exception:
        return ""


def _strip_bullet_prefix(value: str) -> str:
    stripped = value.lstrip("-*\t \u2022\u2023\u00b7")
    return stripped.lstrip("0123456789. )-\u2022\u2023\u00b7")


class PerplexityClient:
    """Lightweight client wrapping the Perplexity chat completions endpoint."""

    SUPPORTED_DOMAINS = {
        "general": "Comprehensive research across all relevant sources.",
        "stocks": "Stock market data, earnings, analyst opinions, and market trends.",
        "medical": "Peer-reviewed studies, clinical trials, and regulatory updates.",
        "academic": "Scholarly articles, research papers, and academic publications.",
        "technology": "Technology developments, product launches, and innovations.",
    }

    def __init__(self, api_key: str, *, model: str = _DEFAULT_MODEL, base_url: str = _DEFAULT_BASE_URL) -> None:
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.base_url = base_url.rstrip("/")
        self.model = model

    def deep_search(
        self,
        query: str,
        system_prompt: str,
        *,
        domain: str = "general",
        max_tokens: int = 2000,
        temperature: float = 0.2,
        top_p: float = 0.9,
    ) -> Dict[str, Any]:
        """Execute a Perplexity deep-search styled chat completion."""
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "return_citations": True,
            "return_images": False,
        }

        url = f"{self.base_url}/chat/completions"
        start = time.perf_counter()
        try:
            response = requests.post(url, headers=self._headers, json=payload, timeout=_DEFAULT_TIMEOUT)
        except requests.RequestException as exc:
            duration = time.perf_counter() - start
            return {
                "success": False,
                "error": f"Connection error: {exc}",
                "tokens_used": 0,
                "duration": duration,
            }

        duration = time.perf_counter() - start
        if not response.ok:
            return {
                "success": False,
                "error": f"API error {response.status_code}: {_safe_text(response)}",
                "tokens_used": 0,
                "status_code": response.status_code,
                "duration": duration,
            }

        try:
            result = response.json()
        except ValueError:
            return {
                "success": False,
                "error": "Invalid JSON response from Perplexity",
                "tokens_used": 0,
                "duration": duration,
            }

        parsed = self._parse_response(result, query=query, domain=domain)
        parsed.setdefault("tokens_used", 0)
        parsed["duration"] = duration
        return parsed

    def _parse_response(self, result: Dict[str, Any], *, query: str, domain: str) -> Dict[str, Any]:
        choices = result.get("choices") or []
        if not choices:
            return {
                "success": False,
                "error": "No response choices returned",
                "tokens_used": 0,
            }

        message = choices[0].get("message", {})
        content = self._to_text(message.get("content"))
        citations = result.get("citations") or message.get("citations") or []
        usage = result.get("usage") or {}

        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or usage.get("generation_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or (prompt_tokens + completion_tokens))

        sections = self._extract_sections(content)

        return {
            "success": True,
            "query": query,
            "domain": domain,
            "content": content,
            "sections": sections,
            "sources": self._format_citations(citations),
            "citation_count": len(citations),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "tokens_used": total_tokens,
            "estimated_cost": self._estimate_cost(prompt_tokens, completion_tokens),
            "model": self.model,
            "raw": result,
        }

    @staticmethod
    def _to_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: List[str] = []
            for chunk in content:
                if isinstance(chunk, dict):
                    value = chunk.get("text") or chunk.get("content")
                    if value:
                        parts.append(str(value))
                elif chunk:
                    parts.append(str(chunk))
            return "\n".join(parts)
        if isinstance(content, dict):
            value = content.get("text") or content.get("content")
            return str(value) if value else ""
        return str(content) if content else ""

    def _extract_sections(self, content: str) -> Dict[str, Any]:
        """Extract structured sections like summary, findings, insights."""
        sections = {
            "summary": "",
            "findings": [],
            "insights": [],
            "next_steps": [],
            "analysis": content
        }

        lines = content.split("\n")
        current_section = None
        buffer: List[str] = []

        for line in lines:
            line_lower = line.lower().strip()
            
            # Detect section headers
            if any(marker in line_lower for marker in ["executive summary", "summary:", "## summary"]):
                if current_section and buffer:
                    sections[current_section] = "\n".join(buffer).strip()
                current_section = "summary"
                buffer = []
                continue
            elif any(marker in line_lower for marker in ["key finding", "findings:", "## findings"]):
                if current_section and buffer:
                    if current_section == "summary":
                        sections["summary"] = "\n".join(buffer).strip()
                    buffer = []
                current_section = "findings"
                continue
            elif any(marker in line_lower for marker in ["insight", "key insight", "## insights"]):
                if current_section and buffer:
                    if current_section == "findings":
                        sections["findings"] = [_strip_bullet_prefix(b) for b in buffer if b.strip()]
                    buffer = []
                current_section = "insights"
                continue
            elif any(marker in line_lower for marker in ["next step", "recommendations:", "## next steps"]):
                if current_section and buffer:
                    if current_section == "insights":
                        sections["insights"] = [_strip_bullet_prefix(b) for b in buffer if b.strip()]
                    buffer = []
                current_section = "next_steps"
                continue

            # Add content to buffer
            if current_section and line.strip():
                buffer.append(line.strip())

        # Handle remaining buffer
        if current_section and buffer:
            if current_section == "summary":
                sections["summary"] = "\n".join(buffer).strip()
            elif current_section in ["findings", "insights", "next_steps"]:
                sections[current_section] = [_strip_bullet_prefix(b) for b in buffer if b.strip()]

        # Fallback if no structured sections found
        if not sections["summary"]:
            # Take first few sentences as summary
            sentences = content.split(". ")[:3]
            sections["summary"] = ". ".join(sentences).strip() + "." if sentences else ""

        if not sections["findings"]:
            # Extract bullet points as findings
            for line in lines:
                stripped = line.strip()
                if any(stripped.startswith(marker) for marker in _BULLET_MARKERS):
                    finding = _strip_bullet_prefix(stripped)
                    if len(finding) > 20:  # Only substantial findings
                        sections["findings"].append(finding)
                        if len(sections["findings"]) >= 5:
                            break

        return sections

    def _format_citations(self, citations: List[Any]) -> List[Dict[str, Any]]:
        """Format citations into structured source objects."""
        sources = []
        for idx, citation in enumerate(citations, 1):
            if isinstance(citation, str):
                sources.append({
                    "id": idx,
                    "url": citation,
                    "title": f"Source {idx}",
                    "snippet": "",
                    "type": "web"
                })
            elif isinstance(citation, dict):
                sources.append({
                    "id": idx,
                    "url": citation.get("url", ""),
                    "title": citation.get("title", f"Source {idx}"),
                    "snippet": citation.get("snippet", ""),
                    "type": citation.get("type", "web")
                })
        return sources

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost for sonar-pro model."""
        # Sonar Pro pricing: ~$5 per 1M tokens (both input and output)
        total_tokens = prompt_tokens + completion_tokens
        return (total_tokens / 1_000_000) * 5.0