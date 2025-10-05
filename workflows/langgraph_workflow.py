# ============================================================================
# FILE: workflows/langgraph_workflow.py
# DESCRIPTION: Complete workflow with built-in enhanced consolidation
# VERSION: 2.0.1 - Single File - No Warnings
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
        for agent_name in selected_agents:
            agent = self.agents.get(agent_name)
            
            if agent is None:
                print(f"   ⚠️ Agent '{agent_name}' not available, skipping")
                continue
            
            # Get max sources for this agent from config
            max_sources = config.get(f"max_{agent_name}_sources", 10)
            
            # Create async task for agent
            task = agent.research(query=query, domain=domain, max_sources=max_sources)
            tasks.append(task)
        
        if not tasks:
            # No agents available - return error state
            return self._create_empty_result(query, domain)
        
        # Wait for all agents to complete
        agent_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and collect valid results
        valid_results: List[Dict[str, Any]] = []
        for result in agent_results:
            if isinstance(result, Exception):
                print(f"   ⚠️ Agent task failed: {result}")
            elif isinstance(result, dict):
                valid_results.append(result)
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Consolidate results with enhanced synthesis
        consolidated = self._consolidate_results(
            query=query,
            domain=domain,
            agent_results=valid_results,
            execution_time=execution_time
        )
        
        print(f"✅ Research completed in {execution_time:.1f}s")
        print(f"   Total sources: {consolidated['total_sources']}")
        print(f"   Total tokens: {consolidated['total_tokens']:,}")
        print(f"   Total cost: ${consolidated['total_cost']:.6f}")
        print(f"   Confidence score: {consolidated['confidence_score']}/100\n")
        
        return consolidated
    
    def _create_empty_result(self, query: str, domain: str) -> Dict[str, Any]:
        """Create empty result structure when no agents available"""
        return {
            "query": query,
            "domain": domain,
            "summary": "No agents available to execute research",
            "key_findings": [],
            "insights": [],
            "contradictions": [],
            "agent_results": [],
            "successful_agents": [],
            "total_sources": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "execution_time": 0.0,
            "confidence_score": 0.0,
            "coverage_analysis": {
                "breadth": "none",
                "depth": "none",
                "source_types": [],
                "recommendations": ["Please select and configure agents"]
            },
            "timestamp": datetime.now().isoformat(),
            "synthesis_quality": "none",
            "error": "No agents available"
        }
    
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
        contradictions = self._detect_contradictions(agent_results)
        
        # Quality metrics
        confidence_score = self._calculate_confidence_score(agent_results)
        coverage_analysis = self._analyze_coverage(agent_results, domain)
        
        # Build consolidated result
        consolidated: Dict[str, Any] = {
            "query": query,
            "domain": domain,
            "summary": summary,
            "key_findings": key_findings,
            "insights": insights,
            "contradictions": contradictions,
            "confidence_score": confidence_score,
            "coverage_analysis": coverage_analysis,
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
        
        intro = f"**Multi-Agent Analysis** ({len(agent_names)} agents): "
        if len(agent_names) > 1:
            intro += f"Insights synthesized from {', '.join(agent_names)} sources. "
        
        return intro + primary_summary['text']
    
    def _synthesize_findings(self, agent_results: List[Dict[str, Any]]) -> List[str]:
        """Extract and deduplicate findings with semantic similarity"""
        findings_data: List[Dict[str, str]] = []
        
        for result in agent_results:
            if result.get('status') == 'success':
                findings_list = result.get('key_findings', [])
                for finding in findings_list:
                    clean_finding = self._clean_text(str(finding))
                    if clean_finding and len(clean_finding) > 20:
                        findings_data.append({
                            'text': clean_finding,
                            'normalized': self._normalize_text(clean_finding)
                        })
        
        if not findings_data:
            return []
        
        # Deduplicate using semantic similarity
        unique_findings: List[str] = []
        seen_normalized: Set[str] = set()
        
        for finding_item in findings_data:
            normalized = finding_item['normalized']
            
            is_duplicate = False
            for seen in seen_normalized:
                if self._texts_are_similar(normalized, seen):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_normalized.add(normalized)
                unique_findings.append(finding_item['text'])
        
        return unique_findings[:10]  # Return top 10
    
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
        unique_insights: List[str] = []
        for insight in insights_data:
            normalized = self._normalize_text(insight)
            
            is_duplicate = False
            for existing in unique_insights:
                if self._texts_are_similar(normalized, self._normalize_text(existing)):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_insights.append(insight)
        
        # Generate fallback if needed
        if not unique_insights:
            unique_insights = self._generate_domain_insights(agent_results, domain)
        
        return unique_insights[:8]  # Return top 8
    
    def _detect_contradictions(self, agent_results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Detect potential contradictions between agent findings"""
        contradictions: List[Dict[str, str]] = []
        
        all_statements: List[Dict[str, str]] = []
        for result in agent_results:
            if result.get('status') == 'success':
                agent_name = result.get('agent_name', 'unknown')
                
                for finding in result.get('key_findings', []):
                    clean_text = self._clean_text(str(finding))
                    if clean_text:
                        all_statements.append({
                            'text': clean_text,
                            'agent': agent_name,
                            'type': 'finding'
                        })
                
                for insight in result.get('insights', []):
                    clean_text = self._clean_text(str(insight))
                    if clean_text:
                        all_statements.append({
                            'text': clean_text,
                            'agent': agent_name,
                            'type': 'insight'
                        })
        
        # Simple contradiction detection
        contradiction_keywords = [
            ('increases', 'decreases'),
            ('positive', 'negative'),
            ('bullish', 'bearish'),
            ('effective', 'ineffective'),
            ('safe', 'unsafe'),
            ('recommended', 'not recommended'),
            ('growth', 'decline'),
            ('up', 'down')
        ]
        
        for i, stmt1 in enumerate(all_statements):
            for stmt2 in all_statements[i+1:]:
                if stmt1['agent'] != stmt2['agent']:
                    text1_lower = stmt1['text'].lower()
                    text2_lower = stmt2['text'].lower()
                    
                    for word1, word2 in contradiction_keywords:
                        if (word1 in text1_lower and word2 in text2_lower) or \
                           (word2 in text1_lower and word1 in text2_lower):
                            contradictions.append({
                                'agent1': stmt1['agent'],
                                'statement1': stmt1['text'][:100] + "...",
                                'agent2': stmt2['agent'],
                                'statement2': stmt2['text'][:100] + "...",
                                'type': 'potential_contradiction'
                            })
                            break
        
        return contradictions[:5]
    
    # ========================================================================
    # QUALITY METRICS
    # ========================================================================
    
    def _calculate_confidence_score(self, agent_results: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score (0-100)"""
        if not agent_results:
            return 0.0
        
        factors: Dict[str, float] = {
            'agent_success_rate': 0.0,
            'source_diversity': 0.0,
            'finding_consistency': 0.0,
            'insight_depth': 0.0
        }
        
        # Agent success rate (0-30 points)
        successful = len([r for r in agent_results if r.get('status') == 'success'])
        factors['agent_success_rate'] = (successful / len(agent_results)) * 30
        
        # Source diversity (0-30 points)
        total_sources = sum(r.get('source_count', 0) for r in agent_results)
        factors['source_diversity'] = min(total_sources / 10, 1.0) * 30
        
        # Finding consistency (0-20 points)
        total_findings = sum(len(r.get('key_findings', [])) for r in agent_results)
        if total_findings > 0:
            factors['finding_consistency'] = min(total_findings / 20, 1.0) * 20
        
        # Insight depth (0-20 points)
        total_insights = sum(len(r.get('insights', [])) for r in agent_results)
        if total_insights > 0:
            factors['insight_depth'] = min(total_insights / 10, 1.0) * 20
        
        total_score = sum(factors.values())
        return round(total_score, 1)
    
    def _analyze_coverage(
        self,
        agent_results: List[Dict[str, Any]],
        domain: str
    ) -> Dict[str, Any]:
        """Analyze research coverage quality"""
        total_sources = sum(r.get('source_count', 0) for r in agent_results)
        total_findings = sum(len(r.get('key_findings', [])) for r in agent_results)
        total_insights = sum(len(r.get('insights', [])) for r in agent_results)
        
        coverage: Dict[str, Any] = {
            'breadth': 'medium',
            'depth': 'medium',
            'source_types': [],
            'recommendations': []
        }
        
        # Breadth assessment
        if total_sources >= 30:
            coverage['breadth'] = 'excellent'
        elif total_sources >= 15:
            coverage['breadth'] = 'good'
        elif total_sources < 5:
            coverage['breadth'] = 'limited'
        
        # Depth assessment
        if total_findings >= 10 and total_insights >= 5:
            coverage['depth'] = 'excellent'
        elif total_findings >= 5 and total_insights >= 3:
            coverage['depth'] = 'good'
        elif total_findings < 3:
            coverage['depth'] = 'limited'
        
        # Source types
        agent_types: Set[str] = set()
        for result in agent_results:
            if result.get('status') == 'success':
                agent_types.add(result.get('agent_name', 'unknown'))
        coverage['source_types'] = list(agent_types)
        
        # Recommendations
        if len(agent_types) == 1:
            coverage['recommendations'].append("Consider using multiple agents for broader perspective")
        if total_sources < 10:
            coverage['recommendations'].append("Increase source count for more comprehensive analysis")
        if total_insights < 3:
            coverage['recommendations'].append("Refine query to generate more actionable insights")
        
        return coverage
    
    # ========================================================================
    # HELPER METHODS - TEXT PROCESSING
    # ========================================================================
    
    def _clean_text(self, text: str) -> str:
        """Remove HTML/XML/markdown formatting"""
        if not text or not isinstance(text, str):
            return ""
        
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'#{1,6}\s+', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'\[\d+\]', '', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for similarity comparison"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text
    
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
            f"Comprehensive research on '{query}' in the {domain} domain. "
            f"Analysis utilized {agent_count} specialized agent(s) to examine {total_sources} sources, "
            f"providing multi-dimensional insights across various information channels. "
            f"Detailed findings and sources are available in the respective tabs."
        )
    
    def _generate_domain_insights(
        self,
        agent_results: List[Dict[str, Any]],
        domain: str
    ) -> List[str]:
        """Generate domain-specific meta-insights when agents don't provide them"""
        total_sources = sum(r.get('source_count', 0) for r in agent_results)
        agent_names = [r.get('agent_name', 'unknown') for r in agent_results if r.get('status') == 'success']
        
        insights: List[str] = []
        
        insights.append(
            f"Research incorporates {total_sources} sources from {len(agent_names)} specialized agents, "
            f"providing comprehensive multi-perspective analysis"
        )
        
        domain_insights: Dict[str, List[str]] = {
            'technology': [
                "Technology landscape analysis reveals emerging trends and innovation patterns",
                "Cross-referencing technical sources provides validation of technological claims"
            ],
            'medical': [
                "Clinical evidence synthesis requires careful evaluation of source quality and methodology",
                "Multiple data sources help identify consensus and areas of ongoing research"
            ],
            'academic': [
                "Scholarly research benefits from diverse source types including peer-reviewed papers",
                "Academic consensus emerges from systematic evaluation of multiple authoritative sources"
            ],
            'stocks': [
                "Market analysis requires integration of quantitative data, analyst opinions, and sentiment",
                "Multiple information sources help identify investment opportunities while managing risk"
            ]
        }
        
        if domain in domain_insights:
            insights.extend(domain_insights[domain])
        else:
            insights.append("Multi-source analysis provides robust foundation for informed decision-making")
        
        return insights[:5]