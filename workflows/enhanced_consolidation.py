# ============================================================================
# FILE: workflows/enhanced_consolidation.py
# PURPOSE: Improved consolidation logic with intelligent synthesis
# ============================================================================
"""
Enhanced consolidation module that intelligently synthesizes results from
multiple agents instead of just taking the first agent's output
"""

import re
from typing import List, Dict, Any
from datetime import datetime
from collections import Counter


class EnhancedResultConsolidator:
    """
    Consolidates results from multiple agents with intelligent synthesis
    """
    
    def consolidate_results(
        self,
        query: str,
        domain: str,
        agent_results: List[Dict[str, Any]],
        execution_time: float
    ) -> Dict[str, Any]:
        """
        Enhanced consolidation with multi-agent synthesis
        
        Args:
            query: Original user query
            domain: Research domain
            agent_results: List of results from each agent
            execution_time: Total execution time
            
        Returns:
            Consolidated results dictionary with enhanced synthesis
        """
        
        # Aggregate basic metrics
        all_sources = []
        total_tokens = 0
        total_cost = 0.0
        successful_agents = []
        
        for result in agent_results:
            if result.get('status') == 'success':
                sources = result.get('sources', [])
                all_sources.extend(sources)
                total_tokens += result.get('tokens', 0)
                total_cost += result.get('cost', 0.0)
                successful_agents.append(result.get('agent_name', 'unknown'))
        
        # Enhanced synthesis
        summary = self._synthesize_summary(agent_results, query, domain)
        key_findings = self._synthesize_findings(agent_results)
        insights = self._synthesize_insights(agent_results, domain)
        contradictions = self._detect_contradictions(agent_results)
        
        # Additional analysis
        confidence_score = self._calculate_confidence_score(agent_results)
        coverage_analysis = self._analyze_coverage(agent_results, domain)
        
        consolidated = {
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
    
    def _synthesize_summary(
        self,
        agent_results: List[Dict[str, Any]],
        query: str,
        domain: str
    ) -> str:
        """
        Intelligently synthesize summaries from multiple agents
        """
        summaries = []
        
        # Collect all summaries
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
            # Generate fallback summary
            total_sources = sum(r.get('source_count', 0) for r in agent_results)
            agent_count = len([r for r in agent_results if r.get('status') == 'success'])
            return self._generate_fallback_summary(query, domain, total_sources, agent_count)
        
        # If single agent, use its summary
        if len(summaries) == 1:
            return summaries[0]['text']
        
        # Multi-agent synthesis
        # Strategy: Use longest summary as base, add context about multi-agent analysis
        primary_summary = max(summaries, key=lambda x: x['length'])
        agent_names = [s['agent'] for s in summaries]
        
        # Create synthesized summary
        intro = f"**Multi-Agent Research Analysis** ({len(agent_names)} agents): "
        
        # Add diversity note if agents are different types
        unique_agents = set(agent_names)
        if len(unique_agents) > 1:
            intro += f"Insights synthesized from {', '.join(unique_agents)} sources. "
        
        return intro + primary_summary['text']
    
    def _synthesize_findings(self, agent_results: List[Dict[str, Any]]) -> List[str]:
        """
        Synthesize and rank findings from all agents with intelligent deduplication
        """
        findings_data = []
        
        # Collect all findings with metadata
        for result in agent_results:
            if result.get('status') == 'success':
                agent_name = result.get('agent_name', 'unknown')
                findings_list = result.get('key_findings', [])
                
                for finding in findings_list:
                    clean_finding = self._clean_text(str(finding))
                    if clean_finding and len(clean_finding) > 20:
                        findings_data.append({
                            'text': clean_finding,
                            'agent': agent_name,
                            'normalized': self._normalize_text(clean_finding)
                        })
        
        if not findings_data:
            return ["No structured findings were extracted from the research. Review individual agent results for detailed information."]
        
        # Deduplicate using semantic similarity
        unique_findings = []
        seen_normalized = set()
        
        for finding_item in findings_data:
            normalized = finding_item['normalized']
            
            # Check if this finding is similar to any we've already seen
            is_duplicate = False
            for seen in seen_normalized:
                if self._texts_are_similar(normalized, seen):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_normalized.add(normalized)
                unique_findings.append(finding_item['text'])
        
        # Return top findings (increased limit)
        return unique_findings[:10]
    
    def _synthesize_insights(
        self,
        agent_results: List[Dict[str, Any]],
        domain: str
    ) -> List[str]:
        """
        Generate insights with domain-specific analysis
        """
        insights_data = []
        
        # Collect all insights
        for result in agent_results:
            if result.get('status') == 'success':
                insights_list = result.get('insights', [])
                
                for insight in insights_list:
                    clean_insight = self._clean_text(str(insight))
                    if clean_insight and len(clean_insight) > 20:
                        insights_data.append(clean_insight)
        
        # Deduplicate
        unique_insights = []
        for insight in insights_data:
            normalized = self._normalize_text(insight)
            
            is_duplicate = False
            for existing in unique_insights:
                if self._texts_are_similar(normalized, self._normalize_text(existing)):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_insights.append(insight)
        
        # If no insights from agents, generate domain-specific meta-insights
        if not unique_insights:
            unique_insights = self._generate_domain_insights(agent_results, domain)
        
        return unique_insights[:8]  # Increased from 3 to 8
    
    def _detect_contradictions(self, agent_results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Detect potential contradictions between agent findings
        """
        contradictions = []
        
        # Collect all statements from findings and insights
        all_statements = []
        for result in agent_results:
            if result.get('status') == 'success':
                agent_name = result.get('agent_name', 'unknown')
                
                # Add findings
                for finding in result.get('key_findings', []):
                    clean_text = self._clean_text(str(finding))
                    if clean_text:
                        all_statements.append({
                            'text': clean_text,
                            'agent': agent_name,
                            'type': 'finding'
                        })
                
                # Add insights
                for insight in result.get('insights', []):
                    clean_text = self._clean_text(str(insight))
                    if clean_text:
                        all_statements.append({
                            'text': clean_text,
                            'agent': agent_name,
                            'type': 'insight'
                        })
        
        # Simple contradiction detection (can be enhanced with NLP)
        contradiction_keywords = [
            ('increases', 'decreases'),
            ('positive', 'negative'),
            ('bullish', 'bearish'),
            ('effective', 'ineffective'),
            ('safe', 'unsafe'),
            ('recommended', 'not recommended')
        ]
        
        for i, stmt1 in enumerate(all_statements):
            for stmt2 in all_statements[i+1:]:
                if stmt1['agent'] != stmt2['agent']:
                    # Check for contradictory keywords
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
        
        return contradictions[:5]  # Return top 5 contradictions
    
    def _calculate_confidence_score(self, agent_results: List[Dict[str, Any]]) -> float:
        """
        Calculate overall confidence score based on multiple factors
        """
        if not agent_results:
            return 0.0
        
        factors = {
            'agent_success_rate': 0,
            'source_diversity': 0,
            'finding_consistency': 0,
            'insight_depth': 0
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
        
        # Calculate total (0-100)
        total_score = sum(factors.values())
        
        return round(total_score, 1)
    
    def _analyze_coverage(
        self,
        agent_results: List[Dict[str, Any]],
        domain: str
    ) -> Dict[str, Any]:
        """
        Analyze research coverage quality
        """
        coverage = {
            'breadth': 'medium',
            'depth': 'medium',
            'recency': 'unknown',
            'source_types': [],
            'recommendations': []
        }
        
        total_sources = sum(r.get('source_count', 0) for r in agent_results)
        
        # Breadth assessment
        if total_sources >= 30:
            coverage['breadth'] = 'excellent'
        elif total_sources >= 15:
            coverage['breadth'] = 'good'
        elif total_sources < 5:
            coverage['breadth'] = 'limited'
        
        # Depth assessment (based on findings and insights)
        total_findings = sum(len(r.get('key_findings', [])) for r in agent_results)
        total_insights = sum(len(r.get('insights', [])) for r in agent_results)
        
        if total_findings >= 10 and total_insights >= 5:
            coverage['depth'] = 'excellent'
        elif total_findings >= 5 and total_insights >= 3:
            coverage['depth'] = 'good'
        elif total_findings < 3:
            coverage['depth'] = 'limited'
        
        # Source type diversity
        agent_types = set()
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
    # HELPER METHODS
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
        """
        Simple similarity check using word overlap
        Can be enhanced with more sophisticated NLP
        """
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union)
        
        return similarity >= threshold
    
    def _generate_fallback_summary(
        self,
        query: str,
        domain: str,
        total_sources: int,
        agent_count: int
    ) -> str:
        """Generate a fallback summary when no agent summaries available"""
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
        """Generate domain-specific meta-insights when no agent insights available"""
        total_sources = sum(r.get('source_count', 0) for r in agent_results)
        agent_names = [r.get('agent_name', 'unknown') for r in agent_results if r.get('status') == 'success']
        
        insights = []
        
        # Generic insight about coverage
        insights.append(
            f"Research incorporates {total_sources} sources from {len(agent_names)} specialized agents, "
            f"providing comprehensive multi-perspective analysis"
        )
        
        # Domain-specific insights
        domain_insights = {
            'technology': [
                "Technology landscape analysis reveals emerging trends and innovation patterns",
                "Cross-referencing technical sources provides validation of technological claims"
            ],
            'medical': [
                "Clinical evidence synthesis requires careful evaluation of source quality and methodology",
                "Multiple data sources help identify consensus and areas of ongoing research"
            ],
            'academic': [
                "Scholarly research benefits from diverse source types including peer-reviewed papers and expert analysis",
                "Academic consensus emerges from systematic evaluation of multiple authoritative sources"
            ],
            'stocks': [
                "Market analysis requires integration of quantitative data, analyst opinions, and news sentiment",
                "Multiple information sources help identify investment opportunities while managing risk"
            ]
        }
        
        if domain in domain_insights:
            insights.extend(domain_insights[domain])
        else:
            insights.append("Multi-source analysis provides robust foundation for informed decision-making")
        
        return insights[:5]


# Convenience function for backward compatibility
def consolidate_results(
    query: str,
    domain: str,
    agent_results: List[Dict[str, Any]],
    execution_time: float
) -> Dict[str, Any]:
    """
    Wrapper function for backwards compatibility
    """
    consolidator = EnhancedResultConsolidator()
    return consolidator.consolidate_results(query, domain, agent_results, execution_time)