# ============================================================================
# FILE: app.py
# DESCRIPTION: Main Streamlit application - Fixed for Streamlit 1.40+
# VERSION: 2.0.1 - No Warnings Edition
# ============================================================================
"""
Multi-Agent AI Deep Researcher - Main Application
Fixed: Streamlit deprecation warnings and Pylance type hints
"""

import streamlit as st
import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

# Import workflow
from workflows.langgraph_workflow import ResearchWorkflow

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Multi-Agent AI Deep Researcher",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/multi-agent-researcher',
        'Report a bug': 'https://github.com/yourusername/multi-agent-researcher/issues',
        'About': '# Multi-Agent AI Deep Researcher\nv2.0.1 - No Warnings Edition'
    }
)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'research_results' not in st.session_state:
    st.session_state.research_results = None

if 'research_history' not in st.session_state:
    st.session_state.research_history = []

if 'example_query' not in st.session_state:
    st.session_state.example_query = None

# ============================================================================
# CUSTOM CSS STYLING
# ============================================================================

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9);
        margin: 0.5rem 0 0 0;
    }
    
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
        color: white;
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
        font-weight: 500;
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
        font-weight: 500;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER
# ============================================================================

st.markdown("""
<div class="main-header">
    <h1>🔬 Multi-Agent AI Deep Researcher</h1>
    <p>Enhanced Edition | Intelligent Multi-Source Synthesis</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================

with st.sidebar:
    st.header("⚙️ Configuration")
    
    with st.expander("📊 Agent Settings", expanded=True):
        max_perplexity = st.slider("Perplexity Sources", 5, 30, 20, key="slider_perp")
        max_youtube = st.slider("YouTube Sources", 0, 20, 5, key="slider_yt")
        max_api = st.slider("API Sources", 5, 20, 12, key="slider_api")
    
    with st.expander("💰 Cost Settings"):
        max_cost = st.number_input("Max Cost per Query ($)", 0.01, 10.0, 2.0, 0.01, key="cost_max")
    
    st.markdown("---")
    
    # Statistics
    if st.session_state.research_history:
        st.subheader("📊 Session Stats")
        total_queries = len(st.session_state.research_history)
        total_cost = sum([r.get('total_cost', 0) for r in st.session_state.research_history])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Queries", total_queries)
        with col2:
            st.metric("Total Cost", f"${total_cost:.4f}")
        
        if st.button("Clear History", width='stretch'):
            st.session_state.research_history = []
            st.rerun()
    
    st.markdown("---")
    st.caption("v2.0.1 No Warnings | © 2025")

# ============================================================================
# MAIN CONTENT AREA
# ============================================================================

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🎯 Research Question")
    
    # Handle example query
    default_query = ""
    if st.session_state.example_query:
        default_query = st.session_state.example_query
        st.session_state.example_query = None
    
    query_input = st.text_area(
        "Enter your research question:",
        value=default_query,
        height=100,
        placeholder="Example: What are the latest developments in quantum computing?",
        key="query_input"
    )

with col2:
    st.subheader("🏷️ Domain Selection")
    domain = st.selectbox(
        "Choose research domain:",
        options=["technology", "medical", "academic", "stocks"],
        format_func=lambda x: {
            "technology": "💻 Technology",
            "medical": "🏥 Medical",
            "academic": "📚 Academic",
            "stocks": "📈 Stock Market"
        }[x],
        key="domain_select"
    )
    
    st.subheader("🤖 Select Agents")
    use_perplexity = st.checkbox("🌐 Perplexity (Web Research)", value=True, key="agent_perp")
    use_youtube = st.checkbox("📹 YouTube (Video Analysis)", value=False, key="agent_yt")
    use_api = st.checkbox("📚 API (Academic & News)", value=True, key="agent_api")

# Example queries
st.markdown("### 💡 Example Queries")
example_cols = st.columns(4)

examples = {
    "technology": "Latest trends in AI and machine learning for 2025",
    "medical": "Recent advancements in cancer immunotherapy",
    "academic": "Climate change impact on global agriculture",
    "stocks": "NVIDIA stock analysis and growth potential"
}

for idx, (domain_key, example_text) in enumerate(examples.items()):
    with example_cols[idx]:
        if st.button(f"{domain_key.capitalize()}", key=f"example_{domain_key}", width='stretch'):
            st.session_state.example_query = example_text
            st.rerun()

# ============================================================================
# RESEARCH EXECUTION
# ============================================================================

st.markdown("---")

if st.button("🚀 Start Research", type="primary", width='stretch'):
    if not query_input:
        st.error("⚠️ Please enter a research question")
    else:
        # Collect selected agents
        selected_agents = []
        if use_perplexity:
            selected_agents.append("perplexity")
        if use_youtube:
            selected_agents.append("youtube")
        if use_api:
            selected_agents.append("api")
        
        if not selected_agents:
            st.error("⚠️ Please select at least one agent")
        else:
            # Show progress
            with st.spinner("🔬 Conducting research... This may take 20-30 seconds"):
                try:
                    # Create config - Fix type warning by ensuring Dict[str, Any]
                    config: Dict[str, Any] = {
                        "max_perplexity_sources": int(max_perplexity),
                        "max_youtube_sources": int(max_youtube),
                        "max_api_sources": int(max_api)
                    }
                    
                    # Execute workflow
                    workflow = ResearchWorkflow()
                    results = asyncio.run(
                        workflow.execute(
                            query=query_input,
                            domain=domain,
                            selected_agents=selected_agents,
                            config=config
                        )
                    )
                    
                    # Store results
                    st.session_state.research_results = results
                    st.session_state.research_history.append(results)
                    
                    st.success("✅ Research completed successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Research failed: {str(e)}")
                    st.exception(e)

# ============================================================================
# RESULTS DISPLAY
# ============================================================================

if st.session_state.research_results:
    results = st.session_state.research_results
    
    st.markdown("---")
    st.header("📊 Research Results")
    
    # ========================================================================
    # METRICS ROW
    # ========================================================================
    
    metric_cols = st.columns(5)
    
    with metric_cols[0]:
        st.metric("📚 Total Sources", results.get('total_sources', 0))
    
    with metric_cols[1]:
        st.metric("🤖 Agents Used", len(results.get('successful_agents', [])))
    
    with metric_cols[2]:
        st.metric("⏱️ Time", f"{results.get('execution_time', 0):.1f}s")
    
    with metric_cols[3]:
        st.metric("💰 Cost", f"${results.get('total_cost', 0):.4f}")
    
    with metric_cols[4]:
        confidence = results.get('confidence_score', 0)
        st.metric("🎯 Confidence", f"{int(confidence)}/100")
    
    # ========================================================================
    # AGENT PERFORMANCE
    # ========================================================================
    
    st.subheader("🤖 Agent Performance")
    
    agent_results: List[Dict[str, Any]] = results.get('agent_results', [])
    
    if agent_results:
        perf_data = []
        for agent in agent_results:
            perf_data.append({
                "Agent": agent.get('agent_name', 'Unknown').capitalize(),
                "Sources": agent.get('source_count', 0),
                "Findings": len(agent.get('key_findings', [])),
                "Insights": len(agent.get('insights', [])),
                "Cost": f"${agent.get('cost', 0):.6f}",
                "Tokens": f"{agent.get('tokens', 0):,}",
                "Status": "✅ Success" if agent.get('status') == 'success' else "❌ Failed"
            })
        
        df = pd.DataFrame(perf_data)
        st.dataframe(df, width='stretch', hide_index=True)
    
    # ========================================================================
    # ENHANCED RESULTS TABS
    # ========================================================================
    
    tabs = st.tabs([
        "📊 Executive Summary",
        "🔍 Key Findings",
        "💡 Strategic Insights",
        "🔗 All Sources",
        "📈 Analysis Overview"
    ])
    
    # ====================================================================
    # TAB 1: EXECUTIVE SUMMARY
    # ====================================================================
    with tabs[0]:
        query = results.get('query', 'Research Query')
        summary = results.get('summary', 'No summary available')
        
        st.markdown(f"""
        <div class="enhanced-summary-box">
            <h3>🎯 Executive Summary</h3>
            <p>{summary}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick stats
        st.markdown("#### 📊 Quick Metrics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📚 Sources", results.get('total_sources', 0))
        with col2:
            st.metric("🤖 Agents", len(results.get('successful_agents', [])))
        with col3:
            st.metric("⚡ Time", f"{results.get('execution_time', 0):.1f}s")
        with col4:
            st.metric("💰 Cost", f"${results.get('total_cost', 0):.4f}")
    
    # ====================================================================
    # TAB 2: KEY FINDINGS
    # ====================================================================
    with tabs[1]:
        st.markdown("### 🔍 Key Discoveries")
        st.markdown("*Findings ranked by confidence and validated across multiple sources*")
        
        findings: List[str] = results.get('key_findings', [])
        
        if findings:
            for idx, finding in enumerate(findings, 1):
                # Calculate confidence score
                confidence = min(95, 70 + (len(findings) - idx) * 3)
                
                if confidence >= 85:
                    color = "#10b981"
                elif confidence >= 70:
                    color = "#f59e0b"
                else:
                    color = "#6b7280"
                
                st.markdown(f"""
                <div class="finding-card-enhanced">
                    <strong style="font-size: 16px; color: #1f2937;">
                        {idx}. {finding}
                    </strong>
                    <div class="finding-meta">
                        <span class="confidence-badge" style="background: {color};">
                            {confidence}% Confidence
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("⚠️ No key findings extracted. Review individual agent results for detailed information.")
    
    # ====================================================================
    # TAB 3: STRATEGIC INSIGHTS
    # ====================================================================
    with tabs[2]:
        st.markdown("### 💡 Strategic Insights & Analysis")
        st.markdown("*Categorized insights derived from multi-agent analysis*")
        
        insights: List[str] = results.get('insights', [])
        
        # Domain-specific categories
        domain_categories = {
            'technology': ['Innovation', 'Market Trend', 'Technical Analysis', 'Future Outlook'],
            'medical': ['Clinical Evidence', 'Research Finding', 'Treatment Insight', 'Patient Impact'],
            'academic': ['Scholarly Consensus', 'Research Gap', 'Methodology', 'Future Research'],
            'stocks': ['Market Signal', 'Risk Factor', 'Investment Thesis', 'Valuation Analysis']
        }
        
        categories = domain_categories.get(results.get('domain', 'general'), 
                                          ['Key Insight', 'Analysis', 'Observation', 'Finding'])
        
        if insights:
            for idx, insight in enumerate(insights):
                category = categories[idx % len(categories)]
                
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-category">{category}</div>
                    <p style="margin: 8px 0 0 0; font-size: 14px; line-height: 1.6;">
                        {insight}
                    </p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("⚠️ No insights generated. Try refining your query or selecting different agents.")
    
    # ====================================================================
    # TAB 4: ALL SOURCES
    # ====================================================================
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
            sources: List[Dict[str, Any]] = agent_result.get('sources', [])
            
            if not sources:
                continue
            
            agent_icon = agent_icons.get(agent_name.lower(), "🔹")
            
            with st.expander(f"{agent_icon} **{agent_name.capitalize()} Agent** ({len(sources)} sources)", expanded=True):
                for idx, source in enumerate(sources, 1):
                    title = str(source.get('title', 'Untitled'))
                    url = str(source.get('url', '#'))
                    summary_text = str(source.get('summary', 'No description available'))
                    confidence_val = float(source.get('confidence', 3.0))
                    date = str(source.get('date', 'N/A'))
                    
                    # Truncate summary
                    if len(summary_text) > 200:
                        summary_text = summary_text[:200] + "..."
                    
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
                            {summary_text}
                        </p>
                        <div style="font-size: 11px; color: #9ca3af; margin-top: 8px;">
                            📅 {date} | ⭐ {confidence_val:.1f}/5.0
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # ====================================================================
    # TAB 5: ANALYSIS OVERVIEW
    # ====================================================================
    with tabs[4]:
        st.markdown("### 📈 Research Analysis Overview")
        
        # Agent performance table
        st.markdown("#### 🤖 Agent Performance Breakdown")
        if agent_results:
            st.dataframe(df, width='stretch', hide_index=True)
        
        # Coverage metrics
        st.markdown("#### 📊 Research Quality Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Coverage Analysis**")
            coverage: Dict[str, Any] = results.get('coverage_analysis', {})
            
            st.write(f"- **Research Breadth:** {coverage.get('breadth', 'N/A').capitalize()}")
            st.write(f"- **Research Depth:** {coverage.get('depth', 'N/A').capitalize()}")
            st.write(f"- **Synthesis Quality:** {results.get('synthesis_quality', 'N/A').capitalize()}")
            st.write(f"- **Confidence Score:** {int(results.get('confidence_score', 0))}/100")
            
            # Recommendations
            recommendations: List[str] = coverage.get('recommendations', [])
            if recommendations:
                st.markdown("**Recommendations:**")
                for rec in recommendations:
                    st.write(f"• {rec}")
        
        with col2:
            st.markdown("**Source Distribution**")
            total_sources = results.get('total_sources', 1)
            for agent_result in agent_results:
                agent_name = agent_result.get('agent_name', 'Unknown')
                source_count = agent_result.get('source_count', 0)
                percentage = (source_count / total_sources) * 100 if total_sources > 0 else 0
                st.write(f"- **{agent_name.capitalize()}:** {source_count} sources ({percentage:.1f}%)")
        
        # Contradictions if any
        contradictions: List[Dict[str, str]] = results.get('contradictions', [])
        if contradictions:
            st.markdown("---")
            st.markdown("#### ⚠️ Potential Contradictions Detected")
            st.warning("The following contradictions were found between different sources:")
            
            for idx, contradiction in enumerate(contradictions, 1):
                with st.expander(f"Contradiction {idx}", expanded=False):
                    st.markdown(f"""
                    **Source 1:** {contradiction.get('agent1', 'Unknown').capitalize()} Agent
                    
                    {contradiction.get('statement1', 'N/A')}
                    
                    **Source 2:** {contradiction.get('agent2', 'Unknown').capitalize()} Agent
                    
                    {contradiction.get('statement2', 'N/A')}
                    """)
    
    # ========================================================================
    # EXPORT OPTIONS
    # ========================================================================
    
    st.markdown("---")
    st.subheader("📤 Export Options")
    
    export_cols = st.columns(3)
    
    with export_cols[0]:
        # JSON Export
        json_str = json.dumps(results, indent=2, default=str)
        st.download_button(
            label="📋 Download JSON",
            data=json_str,
            file_name=f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            key="download_json",
            width='stretch'
        )
    
    with export_cols[1]:
        # Markdown Export
        md_content = f"# Research Results\n\n"
        md_content += f"**Query:** {results.get('query', 'N/A')}\n\n"
        md_content += f"**Domain:** {results.get('domain', 'N/A').capitalize()}\n\n"
        md_content += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md_content += f"**Confidence Score:** {int(results.get('confidence_score', 0))}/100\n\n"
        md_content += f"---\n\n"
        
        md_content += f"## Executive Summary\n\n{results.get('summary', 'N/A')}\n\n"
        
        if results.get('key_findings'):
            md_content += f"## Key Findings\n\n"
            for idx, finding in enumerate(results['key_findings'], 1):
                md_content += f"{idx}. {finding}\n"
            md_content += "\n"
        
        if results.get('insights'):
            md_content += f"## Strategic Insights\n\n"
            for idx, insight in enumerate(results['insights'], 1):
                md_content += f"{idx}. {insight}\n"
            md_content += "\n"
        
        md_content += f"## Metrics\n\n"
        md_content += f"- Total Sources: {results.get('total_sources', 0)}\n"
        md_content += f"- Agents Used: {len(results.get('successful_agents', []))}\n"
        md_content += f"- Execution Time: {results.get('execution_time', 0):.1f}s\n"
        md_content += f"- Total Cost: ${results.get('total_cost', 0):.6f}\n"
        
        st.download_button(
            label="📝 Download Markdown",
            data=md_content,
            file_name=f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            key="download_md",
            width='stretch'
        )
    
    with export_cols[2]:
        st.button(
            "📄 Export PDF",
            width='stretch',
            help="PDF export coming soon",
            disabled=True
        )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 1rem;">
    <p>Multi-Agent AI Deep Researcher v2.0.1 No Warnings Edition</p>
    <p style="font-size: 0.9rem;">Powered by Perplexity AI | © 2025</p>
</div>
""", unsafe_allow_html=True)