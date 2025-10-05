"""
LangGraph Workflow with proper import handling
Industry-standard implementation with clean formatting
"""

import asyncio
import re
from typing import Dict, List, Any
from datetime import datetime


class ResearchWorkflow:
    """
    Orchestrates multi-agent research workflow
    """
    
    def __init__(self):
        """Initialize workflow - imports are deferred until execute()"""
        self.agents = {}
        self._agents_initialized = False
    
    def _initialize_agents(self):
        """
        Initialize agents with proper error handling
        Called on first execute() to avoid import errors at startup
        """
        if self._agents_initialized:
            return
        
        print("   🔧 Initializing agents...")
        
        try:
            # Import agents here to avoid circular imports and startup errors
            from agents.perplexity_agent import PerplexityAgent
            self.agents["perplexity"] = PerplexityAgent()
            print("   ✓ Perplexity agent loaded")
        except ImportError as e:
            print(f"   ⚠️ Perplexity agent not available: {e}")
            self.agents["perplexity"] = None
        except Exception as e:
            print(f"   ⚠️ Perplexity agent error: {e}")
            self.agents["perplexity"] = None
        
        try:
            from agents.youtube_agent import YouTubeAgent
            self.agents["youtube"] = YouTubeAgent()
            print("   ✓ YouTube agent loaded")
        except ImportError as e:
            print(f"   ⚠️ YouTube agent not available: {e}")
            self.agents["youtube"] = None
        except Exception as e:
            print(f"   ⚠️ YouTube agent error: {e}")
            self.agents["youtube"] = None
        
        try:
            from agents.api_agent import APIAgent
            self.agents["api"] = APIAgent()
            print("   ✓ API agent loaded")
        except ImportError as e:
            print(f"   ⚠️ API agent not available: {e}")
            self.agents["api"] = None
        except Exception as e:
            print(f"   ⚠️ API agent error: {e}")
            self.agents["api"] = None
        
        self._agents_initialized = True
        print(f"   ✅ {len([a for a in self.agents.values() if a is not None])} agents initialized")
    
    async def execute(
        self,
        query: str,
        domain: str,
        selected_agents: List[str],
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute research workflow with selected agents
        
        Args:
            query: Research question
            domain: Research domain
            selected_agents: List of agent names to use
            config: Configuration parameters
            
        Returns:
            Consolidated research results
        """
        # Initialize agents on first run
        self._initialize_agents()
        
        if config is None:
            config = {}
        
        print(f"\n🚀 Starting research workflow")
        print(f"   Query: {query}")
        print(f"   Domain: {domain}")
        print(f"   Agents: {', '.join(selected_agents)}")
        
        start_time = datetime.now()
        
        # Execute agents in parallel
        tasks = []
        for agent_name in selected_agents:
            agent = self.agents.get(agent_name)
            
            if agent is None:
                print(f"   ⚠️ Agent '{agent_name}' not available, skipping")
                continue
            
            # Get max sources for this agent from config
            max_sources = config.get(f"max_{agent_name}_sources", 10)
            
            # Create task
            task = agent.research(query=query, domain=domain, max_sources=max_sources)
            tasks.append(task)
        
        if not tasks:
            # No agents available
            return {
                "query": query,
                "domain": domain,
                "summary": "No agents available to execute research",
                "key_findings": [],
                "insights": [],
                "agent_results": [],
                "total_sources": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "execution_time": 0.0,
                "timestamp": datetime.now().isoformat(),
                "error": "No agents available"
            }
        
        # Wait for all agents to complete
        agent_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(agent_results):
            if isinstance(result, Exception):
                print(f"   ⚠️ Agent task failed: {result}")
            else:
                valid_results.append(result)
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Consolidate results
        consolidated = self._consolidate_results(
            query=query,
            domain=domain,
            agent_results=valid_results,
            execution_time=execution_time
        )
        
        print(f"✅ Research completed in {execution_time:.1f}s")
        print(f"   Total sources: {consolidated['total_sources']}")
        print(f"   Total tokens: {consolidated['total_tokens']:,}")
        print(f"   Total cost: ${consolidated['total_cost']:.6f}\n")
        
        return consolidated
    
    def _consolidate_results(
        self,
        query: str,
        domain: str,
        agent_results: List[Dict[str, Any]],
        execution_time: float
    ) -> Dict[str, Any]:
        """
        Consolidate results from multiple agents
        
        Args:
            query: Original query
            domain: Research domain
            agent_results: List of agent result dictionaries
            execution_time: Total execution time in seconds
            
        Returns:
            Consolidated results dictionary
        """
        # Aggregate sources
        all_sources = []
        total_tokens = 0
        total_cost = 0.0
        
        for result in agent_results:
            if result.get('status') == 'success':
                sources = result.get('sources', [])
                all_sources.extend(sources)
                total_tokens += result.get('tokens', 0)
                total_cost += result.get('cost', 0.0)
        
        # Generate consolidated summary
        summary = self._generate_summary(agent_results, query, domain)
        
        # Extract key findings
        key_findings = self._extract_key_findings(agent_results)
        
        # Generate insights
        insights = self._generate_insights(agent_results, domain)
        
        consolidated = {
            "query": query,
            "domain": domain,
            "summary": summary,
            "key_findings": key_findings,
            "insights": insights,
            "agent_results": agent_results,
            "total_sources": len(all_sources),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
        return consolidated
    
    def _generate_summary(
        self,
        agent_results: List[Dict[str, Any]],
        query: str,
        domain: str
    ) -> str:
        """Generate executive summary from agent results"""
        summaries = []
        
        for result in agent_results:
            if result.get('status') == 'success':
                summary = result.get('summary', '')
                if summary:
                    clean_summary = self._clean_markdown(summary)
                    summaries.append(clean_summary)
        
        if summaries:
            return summaries[0] if summaries else f"Research completed on {query} in the {domain} domain. {len(agent_results)} agents provided insights from multiple sources."
        else:
            return f"Research completed on {query} in the {domain} domain with {sum(r.get('source_count', 0) for r in agent_results)} sources analyzed."
    
    def _extract_key_findings(self, agent_results: List[Dict[str, Any]]) -> List[str]:
        """Extract and consolidate key findings from all agents"""
        findings = []
        
        for result in agent_results:
            if result.get('status') == 'success':
                agent_findings = result.get('key_findings', [])
                
                for finding in agent_findings:
                    clean_finding = self._clean_markdown(finding)
                    
                    if clean_finding and clean_finding not in findings:
                        findings.append(clean_finding)
        
        return findings[:5]
    
    def _generate_insights(
        self,
        agent_results: List[Dict[str, Any]],
        domain: str
    ) -> List[str]:
        """Generate strategic insights from research"""
        insights = []
        
        for result in agent_results:
            if result.get('status') == 'success':
                agent_insights = result.get('insights', [])
                
                for insight in agent_insights:
                    clean_insight = self._clean_markdown(insight)
                    
                    if clean_insight and clean_insight not in insights:
                        insights.append(clean_insight)
        
        if not insights:
            total_sources = sum(r.get('source_count', 0) for r in agent_results)
            insights.append(
                f"Analysis based on {total_sources} sources across multiple platforms provides comprehensive coverage of the topic."
            )
            
            if domain == "stocks":
                insights.append(
                    "Market data and analyst opinions provide multiple perspectives on investment opportunities and risks."
                )
            elif domain == "medical":
                insights.append(
                    "Clinical evidence and research studies offer insights into current treatment approaches and ongoing developments."
                )
            elif domain == "academic":
                insights.append(
                    "Scholarly sources and peer-reviewed research provide authoritative information on current state of knowledge."
                )
            elif domain == "technology":
                insights.append(
                    "Technology trends and expert analysis reveal emerging patterns and potential future developments."
                )
        
        return insights[:3]
    
    def _clean_markdown(self, text: str) -> str:
        """Remove markdown formatting for clean display"""
        if not text:
            return ""
        
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'#{1,6}\s+(.+)', r'\1', text)
        text = re.sub(r'`(.+?)`', r'\1', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\[\d+\]', '', text)
        
        return text.strip()