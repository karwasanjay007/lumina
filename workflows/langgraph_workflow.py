# ============================================================================
# FILE: workflows/langgraph_workflow.py
# DESCRIPTION: Complete workflow with built-in enhanced consolidation
# VERSION: 2.0.2 - Fixed text cleaning and synthesis
# ============================================================================
"""
Multi-Agent Research Workflow with Enhanced Consolidation
All consolidation logic built-in - no separate files needed
"""

import asyncio
import re
from typing import Dict, List, Any, Optional, Set
from datetime import datetime


class ResearchWorkflow:
    """
    Orchestrates multi-agent research workflow with enhanced consolidation
    All functionality in one class for simplicity
    """
    
    def __init__(self) -> None:
        """Initialize workflow - agents loaded lazily on first execute()"""
        self.agents: Dict[str, Any] = {}
        self._agents_initialized: bool = False
    
    def _initialize_agents(self) -> None:
        """
        Initialize agents with proper error handling
        Called on first execute() to avoid import errors at startup
        """
        if self._agents_initialized:
            return
        
        print("   🔧 Initializing agents...")
        
        # Initialize Perplexity Agent
        try:
            from agents.perplexity_agent import PerplexityAgent
            self.agents["perplexity"] = PerplexityAgent()
            print("   ✓ Perplexity agent loaded")
        except ImportError as e:
            print(f"   ⚠️ Perplexity agent not available: {e}")
            self.agents["perplexity"] = None
        except Exception as e:
            print(f"   ⚠️ Perplexity agent error: {e}")
            self.agents["perplexity"] = None
        
        # Initialize YouTube Agent
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
        
        # Initialize API Agent
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
        active_agents = len([a for a in self.agents.values() if a is not None])
        print(f"   ✅ {active_agents} agents initialized\n")
    
    async def execute(
        self,
        query: str,
        domain: str,
        selected_agents: List[str],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute research workflow with selected agents
        
        Args:
            query: Research question
            domain: Research domain (technology, medical, academic, stocks)
            selected_agents: List of agent names to use
            config: Optional configuration parameters
            
        Returns:
            Consolidated research results with enhanced synthesis
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
        agent_names_used = []
        
        for agent_name in selected_agents:
            agent = self.agents.get(agent_name)
            
            if agent is None:
                print(f"   ⚠️ Agent '{agent_name}' not available, skipping")
                continue
            
            agent_names_used.append(agent_name)
            max_sources = config.get(f"max_{agent_name}_sources", 10)
            
            # Create async task for agent
            task = agent.research(query=query, domain=domain, max_sources=max_sources)
            tasks.append(task)
        
        # Wait for all agents to complete
        print(f"\n   ⏳ Executing {len(tasks)} agents in parallel...")
        agent_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(agent_results):
            if isinstance(result, Exception):
                print(f"   ❌ Agent {agent_names_used[i]} failed: {result}")
                processed_results.append({
                    'agent_name': agent_names_used[i],
                    'status': 'failed',
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Consolidate results
        consolidated = self._consolidate_results(
            query=query,
            domain=domain,
            agent_results=processed_results,
            execution_time=execution_time
        )
        
        return consolidated
    
    # ========================================================================
    # CONSOLIDATION - MAIN METHOD
    # ========================================================================
    
    def _consolidate_results(
        self,
        query: str,
        domain: str,
        agent_results: List[Dict[str, Any]],
        execution_time: float
    ) -> Dict[str, Any]:
        """
        Enhanced consolidation with multi-agent synthesis
        
        This is the main consolidation method that orchestrates all synthesis
        """
        # Aggregate basic metrics
        all_sources: List[Dict[str, Any]] = []
        total_tokens = 0
        total_cost = 0.0
        successful_agents: List[str] = []
        
        for result in agent_results:
            if result.get('status') == 'success':
                sources = result.get('sources', [])
                all_sources.extend(sources)
                total_tokens += result.get('tokens', 0)
                total_cost += result.get('cost', 0.0)
                successful_agents.append(result.get('agent_name', 'unknown'))
        
        # Enhanced synthesis - call specialized methods
        summary = self._synthesize_summary(agent_results, query, domain)
        key_findings = self._synthesize_findings(agent_results)
        insights = self._synthesize_insights(agent_results, domain)
        
        # Quality metrics
        confidence_score = self._calculate_confidence_score(agent_results)
        
        # Build consolidated result
        consolidated: Dict[str, Any] = {
            "query": query,
            "domain": domain,
            "summary": summary,
            "key_findings": key_findings,
            "insights": insights,
            "confidence_score": confidence_score,
            "agent_results": agent_results,
            "successful_agents": successful_agents,
            "total_sources": len(all_sources),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
            "synthesis_quality": "high" if len(successful_agents) > 1 else "medium"
        }
        
        return consolidated
    
    # ========================================================================
    # SYNTHESIS METHODS
    # ========================================================================
    
    def _synthesize_summary(
        self,
        agent_results: List[Dict[str, Any]],
        query: str,
        domain: str
    ) -> str:
        """Intelligently synthesize summaries from multiple agents"""
        summaries: List[Dict[str, Any]] = []
        
        for result in agent_results:
            if result.get('status') == 'success':
                summary = result.get('summary', '')
                if summary:
                    clean_summary = self._clean_text(summary)
                    if len(clean_summary) > 50:
                        summaries.append({
                            'text': clean_summary,
                            'agent': result.get('agent_name', 'unknown'),
                            'length': len(clean_summary)
                        })
        
        if not summaries:
            total_sources = sum(r.get('source_count', 0) for r in agent_results)
            agent_count = len([r for r in agent_results if r.get('status') == 'success'])
            return self._generate_fallback_summary(query, domain, total_sources, agent_count)
        
        if len(summaries) == 1:
            return summaries[0]['text']
        
        # Multi-agent synthesis
        primary_summary = max(summaries, key=lambda x: x['length'])
        agent_names = list(set([s['agent'] for s in summaries]))
        
        intro = f"Multi-Agent Analysis ({len(agent_names)} agents): "
        if len(agent_names) > 1:
            intro += f"Insights synthesized from {', '.join(agent_names)} sources. "
        
        return intro + primary_summary['text']
    
    def _synthesize_findings(self, agent_results: List[Dict[str, Any]]) -> List[str]:
        """Extract and combine key findings from all agents"""
        all_findings: List[str] = []
        
        for result in agent_results:
            if result.get('status') == 'success':
                findings = result.get('findings', [])
                for finding in findings:
                    if isinstance(finding, str) and len(finding) > 20:
                        # CLEAN the finding text
                        clean_finding = self._clean_text(finding)
                        if clean_finding:
                            all_findings.append(clean_finding)
        
        if not all_findings:
            return ["No specific findings available"]
        
        # Deduplicate similar findings
        unique_findings = self._deduplicate_findings(all_findings)
        
        # Return top findings (cleaned)
        return unique_findings[:10]
    
    def _synthesize_insights(
        self,
        agent_results: List[Dict[str, Any]],
        domain: str
    ) -> List[str]:
        """Generate domain-specific insights"""
        insights_data: List[str] = []
        
        for result in agent_results:
            if result.get('status') == 'success':
                insights_list = result.get('insights', [])
                for insight in insights_list:
                    clean_insight = self._clean_text(str(insight))
                    if clean_insight and len(clean_insight) > 20:
                        insights_data.append(clean_insight)
        
        # Deduplicate
        unique_insights = self._deduplicate_findings(insights_data)
        
        return unique_insights[:8]
    
    def _calculate_confidence_score(self, agent_results: List[Dict[str, Any]]) -> int:
        """Calculate overall confidence score based on agent results"""
        base_score = 40
        
        # Agent diversity bonus
        successful_agents = sum(1 for r in agent_results if r.get('status') == 'success')
        agent_bonus = min(successful_agents * 15, 30)
        
        # Source count bonus
        total_sources = sum(r.get('source_count', 0) for r in agent_results)
        source_bonus = min((total_sources / 20) * 30, 30)
        
        total = base_score + agent_bonus + source_bonus
        return min(int(total), 100)
    
    # ========================================================================
    # HELPER METHODS - TEXT PROCESSING
    # ========================================================================
    
    def _clean_text(self, text: str) -> str:
        """
        Remove markdown and special formatting from text
        CRITICAL for fixing ** appearing in output
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Remove markdown bold
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        
        # Remove markdown italic
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        
        # Remove headers
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        
        # Remove code blocks
        text = re.sub(r'```[^`]*```', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Remove citations
        text = re.sub(r'\[\d+\]', '', text)
        
        # Remove HTML/XML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for similarity comparison"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _deduplicate_findings(self, findings: List[str]) -> List[str]:
        """Remove duplicate or very similar findings"""
        if not findings:
            return []
        
        unique_findings: List[str] = []
        seen_normalized: Set[str] = set()
        
        for finding in findings:
            normalized = self._normalize_text(finding)
            
            # Skip if too similar to existing finding
            is_duplicate = False
            for seen in seen_normalized:
                if self._texts_are_similar(normalized, seen):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_normalized.add(normalized)
                unique_findings.append(finding)
        
        return unique_findings
    
    def _texts_are_similar(self, text1: str, text2: str, threshold: float = 0.6) -> bool:
        """Simple similarity check using word overlap"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union)
        return similarity >= threshold
    
    # ========================================================================
    # FALLBACK CONTENT GENERATION
    # ========================================================================
    
    def _generate_fallback_summary(
        self,
        query: str,
        domain: str,
        total_sources: int,
        agent_count: int
    ) -> str:
        """Generate fallback summary when no agent summaries available"""
        return (
            f"Comprehensive research on {query} in the {domain} domain. "
            f"Analysis utilized {agent_count} specialized agent(s) to examine {total_sources} sources, "
            f"providing multi-dimensional insights across various information channels. "
            f"Detailed findings and sources are available in the respective tabs."
        )