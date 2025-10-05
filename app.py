"""
Multi-Agent AI Deep Researcher - Fixed Session State
Resolves StreamlitAPIException for query_input modification
"""

import streamlit as st
import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Multi-Agent AI Deep Researcher",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state FIRST before any widgets
if 'app_initialized' not in st.session_state:
    st.session_state.app_initialized = True
    st.session_state.research_results = None
    st.session_state.research_history = []
    st.session_state.example_query = None  # NEW: Store example query separately

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    .source-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 3px solid #10b981;
    }
    
    .agent-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    
    .perplexity-badge { background: #667eea; color: white; }
    .youtube-badge { background: #ff0000; color: white; }
    .api-badge { background: #10b981; color: white; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🔍 Multi-Agent AI Deep Researcher</h1>
    <p>Powered by Perplexity AI | Comprehensive Research in Seconds</p>
</div>
""", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    with st.expander("📊 Agent Settings", expanded=True):
        max_perplexity = st.slider("Perplexity Sources", 1, 20, 2, key="slider_perp")
        max_youtube = st.slider("YouTube Sources", 1, 20, 2, key="slider_yt")
        max_api = st.slider("API Sources", 1, 20, 2, key="slider_api")
    
    with st.expander("💰 Cost Settings"):
        max_cost = st.number_input("Max Cost per Query ($)", 0.1, 10.0, 2.0, 0.1, key="cost_max")
    
    st.markdown("---")
    st.caption("v2.0 | © 2025 Powered by Perplexity AI")

# Main content area
col1, col2 = st.columns([2, 1])

# Example queries
example_queries = {
    "stocks": "Latest quarterly earnings for Tesla and market outlook",
    "medical": "Recent clinical trials for alzheimer's treatment",
    "academic": "Latest research on quantum computing applications",
    "technology": "AI trends and innovations in 2025"
}

with col1:
    st.subheader("🎯 Research Query")
    
    # Domain selection
    domain = st.selectbox(
        "Select Research Domain",
        ["stocks", "medical", "academic", "technology"],
        format_func=lambda x: {
            "stocks": "📈 Stock Market Analysis",
            "medical": "🏥 Medical Research",
            "academic": "📚 Academic Research",
            "technology": "💻 Technology Trends"
        }[x],
        key="domain_select"
    )
    
    # CRITICAL FIX: Handle example query BEFORE creating text_area widget
    # Check if example button was clicked in previous run
    if st.session_state.example_query is not None:
        default_query = st.session_state.example_query
        st.session_state.example_query = None  # Reset after using
    else:
        default_query = ""
    
    # Query input with dynamic default value
    query = st.text_area(
        "Enter your research question",
        value=default_query,
        placeholder="e.g., What are the latest trends in AI technology?",
        height=100,
        key="query_input"
    )
    
    # Quick examples - uses callback to set example_query
    st.caption("Quick examples:")
    if st.button(f"💡 Try: {example_queries[domain]}", key="example_btn"):
        # Set example query in session state for next rerun
        st.session_state.example_query = example_queries[domain]
        st.rerun()

with col2:
    st.subheader("🤖 Select Agents")
    
    # Agent selection based on domain
    recommended_agents = {
        "stocks": ["perplexity", "api"],
        "medical": ["perplexity", "api"],
        "academic": ["perplexity", "api"],
        "technology": ["perplexity", "youtube"]
    }
    
    selected_agents = []
    
    enable_perp = st.checkbox(
        "🌐 Web Research (Perplexity)",
        value=True,
        help="Deep web search with citations",
        key="agent_perp"
    )
    if enable_perp:
        selected_agents.append("perplexity")
    
    enable_yt = st.checkbox(
        "📹 Video Analysis (YouTube)",
        value="youtube" in recommended_agents[domain],
        help="Analyze relevant YouTube videos",
        key="agent_yt"
    )
    if enable_yt:
        selected_agents.append("youtube")
    
    enable_api = st.checkbox(
        "📚 API Sources (Academic/News)",
        value="api" in recommended_agents[domain],
        help="Fetch from arXiv, PubMed, News APIs",
        key="agent_api"
    )
    if enable_api:
        selected_agents.append("api")
    
    st.info(f"✓ {len(selected_agents)} agent(s) selected")

# Start research button
if st.button("🚀 Start Research", type="primary", disabled=not query, use_container_width=True, key="start_btn"):
    if not selected_agents:
        st.error("Please select at least one agent")
    else:
        with st.spinner("🔍 Conducting research..."):
            # Import workflow
            try:
                from workflows.langgraph_workflow import ResearchWorkflow
                
                # Create workflow
                workflow = ResearchWorkflow()
                
                # Execute research
                results = asyncio.run(workflow.execute(
                    query=query,
                    domain=domain,
                    selected_agents=selected_agents,
                    config={
                        "max_perplexity_sources": max_perplexity,
                        "max_youtube_sources": max_youtube,
                        "max_api_sources": max_api
                    }
                ))
                
                st.session_state.research_results = results
                st.success("✅ Research completed!")
                
            except Exception as e:
                st.error(f"❌ Research failed: {str(e)}")
                st.exception(e)

# Helper function to clean markdown formatting
def clean_markdown(text):
    """Remove markdown formatting characters for clean display"""
    if not text:
        return ""
    # Remove ** for bold
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    # Remove * for italic
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    # Remove ### headers but keep text
    text = re.sub(r'#{1,6}\s+(.+)', r'\1', text)
    # Remove code backticks
    text = re.sub(r'`(.+?)`', r'\1', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove citation markers
    text = re.sub(r'\[\d+\]', '', text)
    return text.strip()

# Display results
if st.session_state.research_results:
    results = st.session_state.research_results
    
    st.markdown("---")
    st.header("📊 Research Results")
    
    # Metrics row
    metric_cols = st.columns(4)
    
    with metric_cols[0]:
        st.metric(
            "📚 Total Sources",
            results.get('total_sources', 0)
        )
    
    with metric_cols[1]:
        cost = results.get('total_cost', 0)
        st.metric(
            "💰 Cost",
            f"${cost:.6f}"
        )
    
    with metric_cols[2]:
        tokens = results.get('total_tokens', 0)
        st.metric(
            "🎯 Tokens Used",
            f"{tokens:,}"
        )
    
    with metric_cols[3]:
        exec_time = results.get('execution_time', 0)
        st.metric(
            "⏱️ Time",
            f"{exec_time:.1f}s"
        )
    
    # Agent Performance
    st.subheader("😊 Agent Performance")
    
    agent_results = results.get('agent_results', [])
    
    if agent_results:
        # Create DataFrame for agent performance
        import pandas as pd
        
        perf_data = []
        for agent in agent_results:
            perf_data.append({
                "Agent": agent.get('agent_name', 'Unknown').title(),
                "Sources": agent.get('source_count', 0),
                "Cost": f"${agent.get('cost', 0):.6f}",
                "Tokens": agent.get('tokens', 0),
                "Status": "✅ Success" if agent.get('status') == 'success' else "❌ Failed"
            })
        
        df = pd.DataFrame(perf_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Results tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Summary",
        "🔍 Key Findings",
        "💡 Insights",
        "🔗 Sources",
        "📋 JSON View"
    ])
    
    with tab1:
        st.subheader("Executive Summary")
        summary = results.get('summary', 'No summary available.')
        clean_summary = clean_markdown(summary)
        st.write(clean_summary)
    
    with tab2:
        st.subheader("Key Findings")
        findings = results.get('key_findings', [])
        
        if findings:
            for idx, finding in enumerate(findings, 1):
                clean_finding = clean_markdown(finding)
                st.markdown(f"**{idx}.** {clean_finding}")
        else:
            st.info("No findings generated.")
    
    with tab3:
        st.subheader("Strategic Insights")
        insights = results.get('insights', [])
        
        if insights:
            for idx, insight in enumerate(insights, 1):
                clean_insight = clean_markdown(insight)
                st.markdown(f"💡 **{idx}.** {clean_insight}")
        else:
            st.info("No insights generated.")
    
    with tab4:
        st.subheader("All Sources")
        
        for agent_result in agent_results:
            agent_name = agent_result.get('agent_name', 'Unknown').title()
            sources = agent_result.get('sources', [])
            
            if sources:
                st.markdown(f"### {agent_name} ({len(sources)} sources)")
                
                for source in sources:
                    with st.container():
                        title = source.get('title', 'Untitled')
                        url = source.get('url', '#')
                        description = source.get('description', 'No description')
                        source_type = source.get('source_type', 'unknown')
                        
                        clean_desc = clean_markdown(description)
                        
                        st.markdown(f"**[{title}]({url})**")
                        st.caption(clean_desc[:200] + "..." if len(clean_desc) > 200 else clean_desc)
                        st.markdown(f"*Type: {source_type}*")
                        st.markdown("---")
    
    with tab5:
        st.subheader("Complete JSON Response")
        st.json(results)
    
    # Export options
    st.markdown("---")
    st.subheader("📤 Export Options")
    
    export_cols = st.columns(3)
    
    with export_cols[0]:
        json_str = json.dumps(results, indent=2, default=str)
        st.download_button(
            label="📋 Download JSON",
            data=json_str,
            file_name=f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            key="download_json"
        )
    
    with export_cols[1]:
        md_content = f"# Research Results\n\n"
        md_content += f"**Query:** {results.get('query', 'N/A')}\n\n"
        md_content += f"**Domain:** {results.get('domain', 'N/A')}\n\n"
        md_content += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md_content += f"**Execution Time:** {results.get('execution_time', 0):.1f}s\n\n"
        md_content += f"**Total Sources:** {results.get('total_sources', 0)}\n\n"
        
        md_content += f"## Summary\n\n{clean_markdown(results.get('summary', 'N/A'))}\n\n"
        
        if results.get('key_findings'):
            md_content += "## Key Findings\n\n"
            for idx, finding in enumerate(results['key_findings'], 1):
                md_content += f"{idx}. {clean_markdown(finding)}\n"
            md_content += "\n"
        
        if results.get('insights'):
            md_content += "## Insights\n\n"
            for idx, insight in enumerate(results['insights'], 1):
                md_content += f"{idx}. {clean_markdown(insight)}\n"
            md_content += "\n"
        
        if agent_results:
            md_content += "## Sources\n\n"
            for agent_result in agent_results:
                agent_name = agent_result.get('agent_name', 'Unknown').title()
                sources = agent_result.get('sources', [])
                if sources:
                    md_content += f"### {agent_name}\n\n"
                    for source in sources:
                        title = source.get('title', 'Untitled')
                        url = source.get('url', '#')
                        md_content += f"- [{title}]({url})\n"
                    md_content += "\n"
        
        st.download_button(
            label="📝 Download Markdown",
            data=md_content,
            file_name=f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            key="download_md"
        )
    
    with export_cols[2]:
        try:
            from utils.export import export_to_pdf
            
            pdf_bytes = export_to_pdf(results)
            
            st.download_button(
                label="📄 Generate PDF",
                data=pdf_bytes,
                file_name=f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                key="download_pdf"
            )
        except Exception as e:
            st.button("📄 PDF (Error)", disabled=True, help=f"PDF export error: {str(e)}")

# Footer
st.markdown("---")
st.caption(f"Multi-Agent AI Deep Researcher | Version 2.0 | © {datetime.now().year} | Powered by Perplexity AI")