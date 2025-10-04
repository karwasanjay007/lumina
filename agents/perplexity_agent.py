"""
Perplexity Agent - Based on Original Working Project Code
agents/perplexity_agent.py
"""

from agents.base_agent import BaseAgent
from services.perplexity_client import PerplexityClient
from typing import Dict, Optional
from pathlib import Path
import os


class PerplexityAgent(BaseAgent):
    """Agent for deep research using Perplexity API with domain-specific prompts"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("Perplexity API key not found")
        
        self.client = PerplexityClient(self.api_key)
        self.name = "Perplexity Deep Research Agent"
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
    
    async def execute(
        self, 
        query: str, 
        domain: str = "general",
        max_tokens: int = 2000
    ) -> Dict:
        """
        Execute deep research query
        
        Args:
            query: Research question
            domain: Research domain (stocks, medical, academic, technology, general)
            max_tokens: Maximum tokens for response
            
        Returns:
            Structured research results with success, sources, findings, etc.
        """
        
        # Load domain-specific prompt from prompts folder
        system_prompt = self._load_domain_prompt(domain, query)
        
        # Call the client's deep_search method
        result = await self.client.deep_search(
            query=query,
            system_prompt=system_prompt,
            domain=domain,
            max_tokens=max_tokens
        )
        
        # Add agent metadata
        result["agent_name"] = "perplexity"
        result["agent_type"] = "perplexity"
        
        return result
    
    def _load_domain_prompt(self, domain: str, query: str) -> str:
        """Load domain-specific prompt from prompts folder"""
        
        # Try to load custom prompt first
        prompt_file = self.prompts_dir / f"perplexity_prompt_{domain}.txt"
        
        if not prompt_file.exists():
            # Fall back to default prompt
            prompt_file = self.prompts_dir / "perplexity_prompt.txt"
        
        if not prompt_file.exists():
            # Use built-in default if no files found
            return self._get_builtin_prompt(domain)
        
        try:
            template = prompt_file.read_text(encoding='utf-8')
            
            # Replace placeholders
            prompt = template.format(
                domain=domain,
                domain_focus=self._get_domain_focus(domain),
                topic=query,
                query=query
            )
            
            return prompt
        except Exception as e:
            print(f"   ⚠️ Error loading prompt: {e}, using built-in")
            return self._get_builtin_prompt(domain)
    
    def _get_domain_focus(self, domain: str) -> str:
        """Get domain-specific focus description"""
        
        focuses = {
            "stocks": "Stock market data, earnings, analyst opinions, and market trends.",
            "medical": "Peer-reviewed studies, clinical trials, and regulatory updates.",
            "academic": "Scholarly articles, research papers, and academic publications.",
            "technology": "Technology developments, product launches, and innovations.",
            "general": "Comprehensive research across all relevant sources."
        }
        
        return focuses.get(domain, focuses["general"])
    
    def _get_builtin_prompt(self, domain: str) -> str:
        """Built-in prompt template as fallback"""
        
        return f"""You are an expert research assistant performing deep research. Focus on {self._get_domain_focus(domain)}

Structure your response EXACTLY as follows:

1. **Executive Summary** (2-3 sentences)
2. **Key Findings** (3-6 bullet points with citations)
3. **Detailed Analysis** (comprehensive paragraphs with evidence)
4. **Insights & Implications** (trends, opportunities, risks)
5. **Source List** (markdown list with citations)

Guidelines:
- Aggregate information from multiple high-quality sources
- Prefer recent publications and authoritative outlets
- Preserve factual accuracy; do not speculate
- Use inline citations like [^1], [^2]
- Be professional, neutral, and analytical
- Do not fabricate sources

Focus on providing actionable intelligence with proper citations."""
    
    def get_status(self) -> Dict:
        """Get agent status"""
        return {
            "name": self.name,
            "type": "perplexity",
            "available": bool(self.api_key),
            "model": "sonar-pro",
            "prompts_dir": str(self.prompts_dir)
        }


# Base agent class if not exists
class BaseAgent:
    """Base class for all agents"""
    
    async def execute(self, **kwargs) -> Dict:
        raise NotImplementedError
    
    def get_status(self) -> Dict:
        raise NotImplementedError