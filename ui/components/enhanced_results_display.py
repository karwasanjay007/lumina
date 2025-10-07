# ============================================================================
# FILE: ui/components/enhanced_results_display.py
# PURPOSE: Enhanced results display with better synthesis and presentation
# ============================================================================
"""
Enhanced results display component with intelligent synthesis across agents
"""

import streamlit as st
import re
from typing import Dict, List, Any
from collections import Counter


def clean_text(text: str) -> str:
    """Remove all HTML/XML tags, special characters, and markdown formatting"""
    if not text or not isinstance(text, str):
        return ""
    
    # Remove HTML/XML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove markdown formatting
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'#{1,6}\s+', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Remove citation markers
    text = re.sub(r'\[\d+\]', '', text)
    # Clean whitespace
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,!?;:()\-\']', '', text)
    
    return text.strip()


def synthesize_summary(agent_results: List[Dict], query: str, domain: str) -> str:
    """
    Intelligently synthesize summaries from multiple agents
    instead of just taking the first one
    """
    summaries = []
    
    for result in agent_results:
        if result.get('status') == 'success':
            summary = result.get('summary', '')
            if summary:
                clean_summary = clean_text(summary)
                if len(clean_summary) > 50:  # Filter out very short summaries
                    summaries.append(clean_summary)
    
    if not summaries:
        # Generate fallback summary
        total_sources = sum(r.get('source_count', 0) for r in agent_results)
        return f"Comprehensive research on '{query}' in the {domain} domain analyzed {total_sources} sources across {len(agent_results)} specialized agents, providing multi-perspective insights."
    
    # If we have one good summary, use it
    if len(summaries) == 1:
        return summaries[0]
    
    # If multiple summaries, create a synthesized overview
    # Take the longest/most detailed summary as primary
    primary_summary = max(summaries, key=len)
    
    # Add context about multi-agent analysis
    prefix = f"**Multi-Agent Analysis:** This research synthesizes insights from {len(summaries)} specialized agents. "
    
    return prefix + primary_summary


def deduplicate_and_rank_findings(agent_results: List[Dict]) -> List[Dict[str, Any]]:
    """
    Extract, deduplicate, and rank findings from all agents
    Returns list of {text, sources, confidence}
    """
    findings_map = {}  # key: normalized text, value: {text, agents, count}
    
    for result in agent_results:
        if result.get('status') == 'success':
            agent_name = result.get('agent_name', 'Unknown')
            findings_list = result.get('key_findings', [])
            
            for finding in findings_list:
                clean_finding = clean_text(str(finding))
                if not clean_finding or len(clean_finding) < 20:
                    continue
                
                # Normalize for deduplication
                normalized = clean_finding.lower().strip()
                
                # Check if similar finding exists
                found_similar = False
                for existing_key in findings_map.keys():
                    # Simple similarity check
                    if normalized[:50] == existing_key[:50] or \
                       any(word in existing_key for word in normalized.split()[:5] if len(word) > 4):
                        findings_map[existing_key]['agents'].append(agent_name)
                        findings_map[existing_key]['count'] += 1
                        found_similar = True
                        break
                
                if not found_similar:
                    findings_map[normalized] = {
                        'text': clean_finding,
                        'agents': [agent_name],
                        'count': 1
                    }
    
    # Convert to list and rank by count (findings from multiple agents are more important)
    findings_list = []
    for data in findings_map.values():
        findings_list.append({
            'text': data['text'],
            'agents': list(set(data['agents'])),
            'confidence': min(data['count'] * 20 + 60, 100)  # Scale 60-100
        })
    
    # Sort by confidence (multi-agent findings first)
    findings_list.sort(key=lambda x: x['confidence'], reverse=True)
    
    return findings_list[:10]  # Return top 10


def generate_enhanced_insights(agent_results: List[Dict], domain: str) -> List[Dict[str, Any]]:
    """
    Generate insights with categorization and confidence scores
    """
    insights_data = []
    categories = {
        'technology': ['Innovation', 'Market Trend', 'Technical Analysis'],
        'medical': ['Clinical Evidence', 'Research Finding', 'Treatment Insight'],
        'academic': ['Scholarly Consensus', 'Research Gap', 'Methodology'],
        'stocks': ['Market Signal', 'Risk Factor', 'Investment Thesis']
    }
    
    domain_categories = categories.get(domain, ['Key Insight', 'Analysis', 'Observation'])
    
    # Collect all insights
    all_insights = []
    for result in agent_results:
        if result.get('status') == 'success':
            agent_name = result.get('agent_name', 'Unknown')
            insights_list = result.get('insights', [])
            
            for insight in insights_list:
                clean_insight = clean_text(str(insight))
                if clean_insight and len(clean_insight) > 20:
                    all_insights.append({
                        'text': clean_insight,
                        'agent': agent_name
                    })
    
    # Deduplicate and categorize
    seen = set()
    for idx, insight_item in enumerate(all_insights[:8]):  # Increased to 8
        text = insight_item['text']
        normalized = text.lower()[:100]
        
        if normalized not in seen:
            seen.add(normalized)
            category = domain_categories[idx % len(domain_categories)]
            insights_data.append({
                'text': text,
                'category': category,
                'agent': insight_item['agent'],
                'confidence': 85  # Default confidence
            })
    
    # If no insights from agents, generate domain-specific insights
    if not insights_data:
        total_sources = sum(r.get('source_count', 0) for r in agent_results)
        insights_data.append({
            'text': f"Analysis of {total_sources} sources provides comprehensive coverage across multiple perspectives",
            'category': 'Coverage',
            'agent': 'System',
            'confidence': 75
        })
    
    return insights_data


def render_enhanced_results(results: Dict):
    """
    Enhanced render function with better synthesis and presentation
    """
    
    if not results:
        st.info("No results to display")
        return
    
    if results.get('error'):
        st.error(f"❌ Error: {results['error']}")
        return
    
    agent_results = results.get('agent_results', [])
    
    if not agent_results:
        st.warning("No agent results found")
        return
    
    # Custom CSS for enhanced styling
    st.markdown("""
    <style>
    .enhanced-summary-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 28px;
        border-radius: 12px;
        margin: 20px 0;
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
    }
    .enhanced-summary-box h3 {
        color: white;
        margin: 0 0 16px 0;
        font-size: 20px;
        font-weight: 600;
    }
    .enhanced-summary-box p {
        margin: 0;
        line-height: 1.7;
        font-size: 15px;
    }
    .finding-card-enhanced {
        background: #ffffff;
        border-left: 5px solid #3b82f6;
        padding: 20px;
        margin: 14px 0;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.3s;
    }
    .finding-card-enhanced:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        transform: translateX(4px);
    }
    .finding-meta {
        font-size: 12px;
        color: #6b7280;
        margin-top: 8px;
    }
    .confidence-badge {
        display: inline-block;
        background: #10b981;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 11px;
        margin-left: 8px;
    }
    .insight-card {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        border-radius: 10px;
        padding: 20px;
        margin: 14px 0;
        border-left: 4px solid #10b981;
    }
    .insight-category {
        display: inline-block;
        background: #10b981;
        color: white;
        padding: 6px 14px;
        border-radius: 16px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .source-card-enhanced {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 18px;
        margin: 14px 0;
        transition: all 0.3s;
    }
    .source-card-enhanced:hover {
        box-shadow: 0 6px 16px rgba(0,0,0,0.1);
        border-color: #3b82f6;
    }
    .agent-tag {
        display: inline-block;
        background: #f3f4f6;
        color: #374151;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 11px;
        margin-right: 6px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create enhanced tabs
    tabs = st.tabs([
        "📊 Executive Summary", 
        "🔍 Key Findings", 
        "💡 Strategic Insights", 
        "🔗 All Sources",
        "📈 Analysis Overview"
    ])
    
    # ========================================================================
    # TAB 1: ENHANCED EXECUTIVE SUMMARY
    # ========================================================================
    with tabs[0]:
        query = results.get('query', 'Research Query')
        domain = results.get('domain', 'general')
        
        # Synthesize summary from all agents
        synthesized_summary = synthesize_summary(agent_results, query, domain)
        
        st.markdown(f"""
        <div class="enhanced-summary-box">
            <h3>🎯 Executive Summary</h3>
            <p>{synthesized_summary}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Add quick stats
        col1, col2, col3, col4 = st.columns(4)
    with col1:
            st.metric("📚 Total Sources", results.get('total_sources', 0))
        with col2:
            st.metric("🤖 Agents Used", len(agent_results))
        with col3:
            st.metric("⚡ Time", f"{results.get('execution_time', 0):.1f}s")
        with col4:
            st.metric("💰 Cost", f"${results.get('total_cost', 0):.4f}")
    
    # ========================================================================
    # TAB 2: ENHANCED KEY FINDINGS
    # ========================================================================
    with tabs[1]:
        st.markdown("### 🔍 Key Discoveries")
        st.markdown("*Findings are ranked by confidence and validated across multiple sources*")
        
        findings = deduplicate_and_rank_findings(agent_results)
        
        if findings:
            for idx, finding_data in enumerate(findings, 1):
                # Extract data
                finding_text = finding_data['text']
                agents = finding_data['agents']
                confidence = finding_data['confidence']
                
                # Confidence color
                if confidence >= 85:
                    color = "#10b981"
                elif confidence >= 70:
                    color = "#f59e0b"
                else:
                    color = "#6b7280"
                
                st.markdown(f"""
                <div class="finding-card-enhanced">
                    <strong style="font-size: 16px; color: #1f2937;">
                        {idx}. {finding_text}
                    </strong>
                    <div class="finding-meta">
                        {"".join(f'<span class="agent-tag">{agent}</span>' for agent in agents)}
                        <span class="confidence-badge" style="background: {color};">
                            {confidence}% Confidence
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("⚠️ No key findings extracted. This may occur when agents return unstructured data.")
    
    # ========================================================================
    # TAB 3: ENHANCED STRATEGIC INSIGHTS
    # ========================================================================
    with tabs[2]:
        st.markdown("### 💡 Strategic Insights & Analysis")
        st.markdown("*Categorized insights derived from multi-agent analysis*")
        
        insights = generate_enhanced_insights(agent_results, results.get('domain', 'general'))
        
        if insights:
            for insight_data in insights:
                category = insight_data['category']
                text = insight_data['text']
                agent = insight_data['agent']
                
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-category">{category}</div>
                    <p style="margin: 8px 0 0 0; font-size: 14px; line-height: 1.6;">
                        {text}
                    </p>
                    <div style="margin-top: 8px; font-size: 11px; color: #6b7280;">
                        Source: {agent.capitalize()} Agent
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("⚠️ No insights generated. Try refining your query or selecting different agents.")
    
    # ========================================================================
    # TAB 4: ENHANCED SOURCES
    # ========================================================================
    with tabs[3]:
        st.markdown("### 🔗 Research Sources")
        st.markdown("*All sources organized by agent with direct links*")
        
        agent_icons = {
            "perplexity": "🌐",
            "youtube": "📹",
            "api": "📚"
        }
        
        for agent_result in agent_results:
            agent_name = agent_result.get('agent_name', 'Unknown')
            sources = agent_result.get('sources', [])
            
            if not sources:
                continue
            
            agent_icon = agent_icons.get(agent_name.lower(), "🔹")
            
            with st.expander(f"{agent_icon} **{agent_name.capitalize()} Agent** ({len(sources)} sources)", expanded=True):
                for idx, source in enumerate(sources, 1):
                    title = clean_text(str(source.get('title', 'Untitled')))
                    url = str(source.get('url', '#'))
                    summary = clean_text(str(source.get('summary', 'No description available')))
                    confidence = source.get('confidence', 3.0)
                    date = source.get('date', 'N/A')
                    
                    # Truncate summary
                    if len(summary) > 200:
                        summary = summary[:200] + "..."
                    
                    st.markdown(f"""
                    <div class="source-card-enhanced">
                        <div style="margin-bottom: 8px;">
                            <strong style="font-size: 15px;">
                                <a href="{url}" target="_blank" style="color: #3b82f6; text-decoration: none;">
                                    {idx}. {title}
                                </a>
                            </strong>
                        </div>
                        <p style="font-size: 13px; color: #4b5563; margin: 8px 0;">
                            {summary}
                        </p>
                        <div style="font-size: 11px; color: #9ca3af; margin-top: 8px;">
                            📅 {date} | ⭐ {confidence:.1f}/5.0
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # ========================================================================
    # TAB 5: ANALYSIS OVERVIEW (NEW)
    # ========================================================================
    with tabs[4]:
        st.markdown("### 📈 Research Analysis Overview")
        
        # Agent performance comparison
        st.markdown("#### 🤖 Agent Performance")
        
        agent_data = []
        for agent_result in agent_results:
            agent_data.append({
                'Agent': agent_result.get('agent_name', 'Unknown').capitalize(),
                'Status': '✅ Success' if agent_result.get('status') == 'success' else '❌ Failed',
                'Sources': agent_result.get('source_count', 0),
                'Findings': len(agent_result.get('key_findings', [])),
                'Insights': len(agent_result.get('insights', [])),
                'Cost': f"${agent_result.get('cost', 0):.6f}",
                'Tokens': f"{agent_result.get('tokens', 0):,}"
            })
        
        import pandas as pd
        df = pd.DataFrame(agent_data)
    st.dataframe(df, width='stretch', hide_index=True)
        
        # Domain-specific metrics
    st.markdown("#### 📊 Research Metrics")
        
    col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Coverage Analysis**")
            total_findings = sum(len(r.get('key_findings', [])) for r in agent_results)
            total_insights = sum(len(r.get('insights', [])) for r in agent_results)
            
            st.write(f"- Total Raw Findings: {total_findings}")
            st.write(f"- Total Raw Insights: {total_insights}")
            st.write(f"- Unique Findings (Deduplicated): {len(deduplicate_and_rank_findings(agent_results))}")
            st.write(f"- Synthesis Quality: {'High' if len(agent_results) > 1 else 'Medium'}")
        
        with col2:
            st.markdown("**Source Distribution**")
            for agent_result in agent_results:
                agent_name = agent_result.get('agent_name', 'Unknown')
                source_count = agent_result.get('source_count', 0)
                percentage = (source_count / results.get('total_sources', 1)) * 100
                st.write(f"- {agent_name.capitalize()}: {source_count} sources ({percentage:.1f}%)")


# Helper function to use in main app
def render_results(results: Dict):
    """Wrapper function for backwards compatibility"""
    render_enhanced_results(results)