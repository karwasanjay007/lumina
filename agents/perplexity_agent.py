"""
Perplexity Agent with fixed citation handling
Handles various Perplexity API response formats
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import aiohttp
except ImportError as e:
    print(f"ERROR: aiohttp not found. Please install: pip install aiohttp==3.9.1")
    raise ImportError(
        "aiohttp is required for Perplexity agent. "
        "Install with: pip install aiohttp==3.9.1"
    ) from e


class PerplexityAgent:
    """
    Perplexity research agent with domain-specific prompt loading
    """
    
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not found in environment")
        
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.model = "sonar-pro"
        
        # Prompts directory
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        
        # Cost per token (approximate for sonar-pro)
        self.cost_per_1k_input_tokens = 0.001
        self.cost_per_1k_output_tokens = 0.001
        
    async def research(
        self,
        query: str,
        domain: str = "general",
        max_sources: int = 10,
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """
        Execute Perplexity research with domain-specific prompts
        
        Args:
            query: Research question
            domain: Research domain (stocks, medical, academic, technology)
            max_sources: Maximum sources to return
            max_tokens: Maximum tokens for response
            
        Returns:
            Dictionary with research results, sources, and metrics
        """
        print(f"   🌐 Perplexity Agent: Researching '{query}' in domain '{domain}'")
        
        # Load domain-specific prompt
        system_prompt = self._load_domain_prompt(domain, query)
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2,
            "return_citations": True,
            "return_images": False
        }
        
        # Execute API call
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
            
            # Extract response with error handling
            try:
                content = data['choices'][0]['message']['content']
            except (KeyError, IndexError, TypeError) as e:
                print(f"   ❌ Perplexity: Invalid response structure: {e}")
                print(f"   Response data: {data}")
                return self._error_result(f"Invalid API response: {e}")
            
            # Extract citations - handle different formats
            citations = self._extract_citations(data)
            
            # Extract token usage
            usage = data.get('usage', {})
            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)
            total_tokens = input_tokens + output_tokens
            
            # Calculate cost
            cost = (
                (input_tokens / 1000) * self.cost_per_1k_input_tokens +
                (output_tokens / 1000) * self.cost_per_1k_output_tokens
            )
            
            # Format sources from citations
            sources = self._format_sources(citations, max_sources)
            
            # Parse structured content
            parsed_content = self._parse_response(content)
            
            result = {
                "agent_name": "perplexity",
                "agent_type": "perplexity",
                "status": "success",
                "query": query,
                "domain": domain,
                "content": content,
                "summary": parsed_content.get('summary', content[:500]),
                "key_findings": parsed_content.get('findings', []),
                "insights": parsed_content.get('insights', []),
                "sources": sources,
                "source_count": len(sources),
                "tokens": total_tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": cost,
                "model": self.model,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"   ✅ Perplexity: {len(sources)} sources, {total_tokens} tokens, ${cost:.6f}")
            
            return result
            
        except aiohttp.ClientError as e:
            print(f"   ❌ Perplexity API error: {e}")
            return self._error_result(str(e))
        except Exception as e:
            print(f"   ❌ Perplexity error: {e}")
            import traceback
            traceback.print_exc()
            return self._error_result(str(e))
    
    def _extract_citations(self, data: Dict[str, Any]) -> List[Any]:
        """
        Extract citations from API response with robust error handling
        
        Args:
            data: API response data
            
        Returns:
            List of citation objects (can be dicts, strings, or URLs)
        """
        # Try different possible locations for citations
        
        # Method 1: Top-level citations field
        if 'citations' in data and data['citations']:
            citations = data['citations']
            if isinstance(citations, list):
                return citations
            elif isinstance(citations, str):
                # Single URL string
                return [citations]
        
        # Method 2: Inside message
        try:
            message = data['choices'][0]['message']
            if 'citations' in message and message['citations']:
                citations = message['citations']
                if isinstance(citations, list):
                    return citations
                elif isinstance(citations, str):
                    return [citations]
        except (KeyError, IndexError, TypeError):
            pass
        
        # Method 3: Check for URLs in content
        try:
            content = data['choices'][0]['message']['content']
            if isinstance(content, str):
                import re
                urls = re.findall(r'https?://[^\s\)]+', content)
                if urls:
                    return urls
        except (KeyError, IndexError, TypeError):
            pass
        
        # No citations found
        return []
    
    def _format_sources(
        self,
        citations: List[Any],
        max_sources: int
    ) -> List[Dict[str, str]]:
        """
        Format citations into source dictionaries
        
        Args:
            citations: Raw citation data from API
            max_sources: Maximum number of sources to return
            
        Returns:
            List of formatted source dictionaries
        """
        sources = []
        
        for idx, citation in enumerate(citations[:max_sources], 1):
            try:
                # Handle different citation formats
                if isinstance(citation, dict):
                    # Citation is already a dictionary
                    sources.append({
                        "title": citation.get('title', f'Source {idx}'),
                        "url": citation.get('url', citation.get('link', '#')),
                        "description": citation.get('snippet', citation.get('description', '')),
                        "source_type": "web"
                    })
                elif isinstance(citation, str):
                    # Citation is a URL string
                    # Try to extract domain as title
                    import re
                    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', citation)
                    domain = domain_match.group(1) if domain_match else 'Source'
                    
                    sources.append({
                        "title": f"{domain} - Source {idx}",
                        "url": citation,
                        "description": f"Reference from {domain}",
                        "source_type": "web"
                    })
                else:
                    # Unknown format - skip
                    print(f"   ⚠️ Unknown citation format: {type(citation)}")
                    continue
                    
            except Exception as e:
                print(f"   ⚠️ Error formatting citation {idx}: {e}")
                continue
        
        # If no sources were extracted, create a generic one
        if not sources:
            sources.append({
                "title": "Perplexity AI Research",
                "url": "https://www.perplexity.ai",
                "description": "Research conducted via Perplexity AI",
                "source_type": "web"
            })
        
        return sources
    
    def _error_result(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error result"""
        return {
            "agent_name": "perplexity",
            "agent_type": "perplexity",
            "status": "error",
            "error": error_message,
            "sources": [],
            "source_count": 0,
            "tokens": 0,
            "cost": 0.0
        }
    
    def _load_domain_prompt(self, domain: str, query: str) -> str:
        """Load domain-specific prompt from prompts directory"""
        domain_file = self.prompts_dir / f"perplexity_prompt_{domain}.txt"
        
        if not domain_file.exists():
            domain_file = self.prompts_dir / "perplexity_prompt.txt"
        
        if not domain_file.exists():
            return self._get_builtin_prompt(domain)
        
        try:
            template = domain_file.read_text(encoding='utf-8')
            domain_focus = self._get_domain_focus(domain)
            
            prompt = template.format(
                domain=domain,
                domain_focus=domain_focus,
                topic=query,
                query=query
            )
            
            return prompt
            
        except Exception as e:
            print(f"   ⚠️ Error loading prompt from {domain_file}: {e}")
            return self._get_builtin_prompt(domain)
    
    def _get_domain_focus(self, domain: str) -> str:
        """Get domain-specific focus description"""
        focuses = {
            "stocks": "Stock market data, financial metrics, earnings reports, analyst opinions, and market trends.",
            "medical": "Peer-reviewed medical studies, clinical trials, treatment protocols, and regulatory updates.",
            "academic": "Scholarly articles, research papers, academic publications, and peer-reviewed journals.",
            "technology": "Technology developments, product launches, innovations, technical specifications, and industry trends.",
            "general": "Comprehensive research across all relevant and credible sources."
        }
        return focuses.get(domain, focuses["general"])
    
    def _get_builtin_prompt(self, domain: str) -> str:
        """Built-in fallback prompt if files not available"""
        domain_focus = self._get_domain_focus(domain)
        
        return f"""You are an expert research assistant conducting deep research in the {domain} domain.

Focus: {domain_focus}

Provide a comprehensive, well-structured response with:

1. **Executive Summary** (2-3 sentences)
2. **Key Findings** (3-5 bullet points with evidence)
3. **Detailed Analysis** (comprehensive paragraphs with data)
4. **Insights & Implications** (trends, opportunities, risks)
5. **Recommendations** (actionable suggestions)

Use clear language, cite sources, and focus on credible information.
"""
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Parse Perplexity response into structured sections"""
        import re
        
        result = {
            "summary": "",
            "findings": [],
            "insights": []
        }
        
        # Extract summary
        summary_match = re.search(
            r'\*\*Executive Summary\*\*\s*\n\s*(.+?)(?:\n\n|\n\*\*)',
            content,
            re.DOTALL
        )
        if summary_match:
            result["summary"] = summary_match.group(1).strip()
        else:
            paragraphs = content.split('\n\n')
            if paragraphs:
                result["summary"] = paragraphs[0][:500]
        
        # Extract findings
        findings_match = re.search(
            r'\*\*Key Findings?\*\*\s*\n\s*(.+?)(?:\n\n\*\*|\Z)',
            content,
            re.DOTALL
        )
        if findings_match:
            findings_text = findings_match.group(1)
            findings = re.split(r'\n\s*[\-\*\d]+\.?\s+', findings_text)
            result["findings"] = [f.strip() for f in findings if f.strip()][:5]
        
        # Extract insights
        insights_match = re.search(
            r'\*\*Insights?(?:\s+&\s+Implications?)?\*\*\s*\n\s*(.+?)(?:\n\n\*\*|\Z)',
            content,
            re.DOTALL
        )
        if insights_match:
            insights_text = insights_match.group(1)
            insights = [s.strip() for s in insights_text.split('\n') if s.strip()]
            result["insights"] = insights[:3]
        
        return result