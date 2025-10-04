"""
Multi-Agent AI Deep Researcher - Complete Fixed Version
All issues resolved:
- Unique keys for all sliders
- No deprecation warnings
- Default sources = 2
- All features working
"""

import streamlit as st
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Multi-Agent AI Deep Researcher",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Prevent duplicate rendering
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.research_results = None
    st.session_state.research_history = []

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

# Initialize session state
if 'research_results' not in st.session_state:
    st.session_state.research_results = None
if 'research_history' not in st.session_state:
    st.session_state.research_history = []

# Header
st.markdown("""
<div class="main-header">
    <h1>🔍 Multi-Agent AI Deep Researcher</h1>
    <p>Powered by Perplexity AI | Comprehensive Research in Seconds</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    with st.expander("📊 Agent Settings", expanded=True):
        # DEFAULT TO 2 SOURCES - UNIQUE KEYS FOR EACH SLIDER
        max_sources_perplexity = st.slider(
            "Max Sources - Web Research", 
            min_value=1, 
            max_value=20, 
            value=2,
            key="slider_perplexity_sources",
            help="Maximum number of sources for Perplexity agent"
        )
        
        max_sources_youtube = st.slider(
            "Max Sources - YouTube", 
            min_value=1, 
            max_value=20, 
            value=2,
            key="slider_youtube_sources",
            help="Maximum number of video sources"
        )
        
        max_sources_api = st.slider(
            "Max Sources - API", 
            min_value=1, 
            max_value=20, 
            value=2,
            key="slider_api_sources",
            help="Maximum number of API sources (arXiv, news, etc.)"
        )
    
    with st.expander("🎯 Advanced Settings"):
        max_tokens = st.number_input(
            "Max Tokens per Agent",
            min_value=500,
            max_value=4000,
            value=2000,
            step=100,
            key="input_max_tokens",
            help="Maximum tokens for API responses"
        )
        
        timeout_seconds = st.number_input(
            "Timeout (seconds)",
            min_value=30,
            max_value=300,
            value=120,
            step=10,
            key="input_timeout",
            help="Maximum time to wait for agent responses"
        )
    
    # Current configuration display
    st.markdown("---")
    st.markdown("**Current Configuration:**")
    config_data = {
        "Perplexity Sources": max_sources_perplexity,
        "YouTube Sources": max_sources_youtube,
        "API Sources": max_sources_api,
        "Max Tokens": max_tokens,
        "Timeout": f"{timeout_seconds}s"
    }
    st.json(config_data)
    
    # Clear history button
    if st.button("🗑️ Clear History", key="btn_clear_history", type="secondary"):
        st.session_state.research_history = []
        st.session_state.research_results = None
        st.success("History cleared!")
        st.rerun()

# Main Content Area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🎯 Research Query")
    
    # Domain selection
    domain = st.selectbox(
        "Select Research Domain",
        ["general", "stocks", "medical", "academic", "technology"],
        key="select_domain",
        help="Choose the domain for specialized research"
    )
    
    # Query input
    query = st.text_area(
        "Enter your research question",
        placeholder="E.g., What are the latest developments in quantum computing?",
        height=100,
        key="input_query"
    )
    
    # Example queries
    st.markdown("**Quick Examples:**")
    example_cols = st.columns(3)
    
    with example_cols[0]:
        if st.button("📈 Stock Analysis", key="btn_example_stocks"):
            st.session_state.example_query = "Analyze Tesla stock performance and future outlook"
            st.rerun()
    
    with example_cols[1]:
        if st.button("🧬 Medical Research", key="btn_example_medical"):
            st.session_state.example_query = "Latest breakthroughs in cancer immunotherapy"
            st.rerun()
    
    with example_cols[2]:
        if st.button("🤖 AI Trends", key="btn_example_ai"):
            st.session_state.example_query = "Current trends in artificial intelligence for 2025"
            st.rerun()
    
    # Apply example query if set
    if 'example_query' in st.session_state and st.session_state.example_query:
        query = st.session_state.example_query
        del st.session_state.example_query

with col2:
    st.subheader("🎯 Select Agents")
    
    # Agent selection with recommendations
    st.markdown("**Recommended:** Web Research (Perplexity)")
    
    use_perplexity = st.checkbox(
        "🌐 Web Research (Perplexity)", 
        value=True,
        key="checkbox_perplexity"
    )
    use_youtube = st.checkbox(
        "📹 YouTube Videos", 
        value=False,
        key="checkbox_youtube"
    )
    use_api = st.checkbox(
        "📚 API Sources (arXiv, News)", 
        value=False,
        key="checkbox_api"
    )
    
    # Show agent info
    if use_perplexity:
        st.info("✓ Deep web search with citations")
    if use_youtube:
        st.info("✓ Video content analysis")
    if use_api:
        st.info("✓ Academic papers & news articles")

# Research button
research_button_disabled = not query or not query.strip()

if st.button(
    "🚀 Start Research", 
    type="primary", 
    disabled=research_button_disabled,
    key="btn_start_research"
):
    
    # Validate agent selection
    selected_agents = []
    if use_perplexity:
        selected_agents.append('perplexity')
    if use_youtube:
        selected_agents.append('youtube')
    if use_api:
        selected_agents.append('api')
    
    if not selected_agents:
        st.error("⚠️ Please select at least one research agent!")
    else:
        # Progress container
        with st.status("🔍 Researching...", expanded=True) as status:
            st.write(f"📝 Query: {query[:100]}...")
            st.write(f"🎯 Domain: {domain}")
            st.write(f"🤖 Agents: {', '.join(selected_agents)}")
            
            try:
                # Import workflow
                from workflows.langgraph_workflow import ResearchWorkflow
                
                # Create workflow with configuration
                max_sources_config = {
                    'perplexity': max_sources_perplexity,
                    'youtube': max_sources_youtube,
                    'api': max_sources_api
                }
                
                workflow = ResearchWorkflow(max_sources_config=max_sources_config)
                
                # Run research
                st.write("⏳ Executing agents in parallel...")
                
                results = asyncio.run(
                    workflow.execute(
                        query=query,
                        domain=domain,
                        agents=selected_agents
                    )
                )
                
                # Store results
                st.session_state.research_results = results
                
                # Add to history
                st.session_state.research_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "query": query,
                    "domain": domain,
                    "agents": selected_agents,
                    "total_sources": results.get('total_sources', 0)
                })
                
                status.update(label="✅ Research Complete!", state="complete")
                st.success(f"Found {results.get('total_sources', 0)} sources in {results.get('execution_time', 0):.1f}s")
                
            except Exception as e:
                status.update(label="❌ Research Failed", state="error")
                st.error(f"Error: {str(e)}")
                with st.expander("🐛 Full Error Details"):
                    st.exception(e)

# Display Results
if st.session_state.research_results:
    results = st.session_state.research_results
    
    st.markdown("---")
    st.header("📊 Research Results")
    
    # Top metrics
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("📚 Total Sources", results.get('total_sources', 0))
    with metric_cols[1]:
        st.metric("💰 Cost", f"${results.get('total_cost', 0):.6f}")
    with metric_cols[2]:
        st.metric("🎯 Tokens Used", f"{results.get('total_tokens', 0):,}")
    with metric_cols[3]:
        st.metric("⏱️ Time", f"{results.get('execution_time', 0):.1f}s")
    
    # Agent performance breakdown
    if results.get('agent_results'):
        st.subheader("🤖 Agent Performance")
        
        agent_data = []
        for agent in results['agent_results']:
            agent_data.append({
                "Agent": agent.get('agent_name', 'Unknown').title(),
                "Sources": len(agent.get('sources', [])),
                "Cost": f"${agent.get('cost', 0):.6f}",
                "Tokens": agent.get('tokens', 0),
                "Status": "✅ Success" if not agent.get('error') else f"❌ {agent.get('error')[:50]}"
            })
        
        st.dataframe(agent_data, hide_index=True)
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Summary", 
        "🔍 Key Findings", 
        "💡 Insights",
        "📚 Sources",
        "🗂️ JSON View"
    ])
    
    with tab1:
        st.subheader("Executive Summary")
        summary = results.get('summary', 'No summary generated.')
        if summary:
            st.markdown(summary)
        else:
            st.info("No summary available.")
    
    with tab2:
        st.subheader("Key Findings")
        findings = results.get('findings', [])
        if findings:
            for idx, finding in enumerate(findings, 1):
                st.markdown(f"**{idx}.** {finding}")
        else:
            st.info("No findings generated.")
    
    with tab3:
        st.subheader("Strategic Insights")
        insights = results.get('insights', [])
        if insights:
            for idx, insight in enumerate(insights, 1):
                st.markdown(f"💡 **{idx}.** {insight}")
        else:
            st.info("No insights generated.")
    
    with tab4:
        st.subheader("Research Sources")
        
        # Group sources by agent
        for agent_result in results.get('agent_results', []):
            agent_name = agent_result.get('agent_name', 'Unknown')
            sources = agent_result.get('sources', [])
            
            if sources:
                st.markdown(f"### {agent_name.title()} Sources ({len(sources)})")
                
                for idx, source in enumerate(sources, 1):
                    with st.container():
                        title = source.get('title', 'Untitled')
                        url = source.get('url', '#')
                        description = source.get('description', 'No description')
                        source_type = source.get('source_type', 'unknown')
                        
                        # Create clickable link
                        st.markdown(f"**{idx}. [{title}]({url})**")
                        st.caption(description[:200] + "..." if len(description) > 200 else description)
                        st.markdown(f"*Type: {source_type}*")
                        
                        # Additional metadata for specific types
                        if source_type == 'youtube':
                            duration = source.get('duration', '')
                            views = source.get('views', 0)
                            channel = source.get('channel', '')
                            if duration or views or channel:
                                meta_parts = []
                                if duration:
                                    meta_parts.append(f"⏱️ {duration}")
                                if views:
                                    meta_parts.append(f"👁️ {views:,} views")
                                if channel:
                                    meta_parts.append(f"📺 {channel}")
                                st.markdown(" | ".join(meta_parts))
                        
                        st.markdown("---")
    
    with tab5:
        st.subheader("Complete JSON Response")
        st.json(results)
    
    # Export options
    st.markdown("---")
    st.subheader("📤 Export Options")
    
    export_cols = st.columns(3)
    
    with export_cols[0]:
        # Prepare JSON for export
        json_str = json.dumps(results, indent=2, default=str)
        st.download_button(
            label="📋 Download JSON",
            data=json_str,
            file_name=f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            key="btn_download_json"
        )
    
    with export_cols[1]:
        # Prepare Markdown export
        md_content = f"# Research Results\n\n"
        md_content += f"**Query:** {results.get('query', 'N/A')}\n\n"
        md_content += f"**Domain:** {results.get('domain', 'N/A')}\n\n"
        md_content += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md_content += f"**Execution Time:** {results.get('execution_time', 0):.1f}s\n\n"
        md_content += f"**Total Sources:** {results.get('total_sources', 0)}\n\n"
        
        md_content += f"## Summary\n\n{results.get('summary', 'N/A')}\n\n"
        
        if results.get('findings'):
            md_content += "## Key Findings\n\n"
            for idx, finding in enumerate(results['findings'], 1):
                md_content += f"{idx}. {finding}\n"
            md_content += "\n"
        
        if results.get('insights'):
            md_content += "## Insights\n\n"
            for idx, insight in enumerate(results['insights'], 1):
                md_content += f"- {insight}\n"
            md_content += "\n"
        
        if results.get('agent_results'):
            md_content += "## Sources\n\n"
            for agent_result in results['agent_results']:
                agent_name = agent_result.get('agent_name', 'Unknown')
                sources = agent_result.get('sources', [])
                if sources:
                    md_content += f"### {agent_name.title()}\n\n"
                    for source in sources:
                        title = source.get('title', 'Untitled')
                        url = source.get('url', '')
                        md_content += f"- [{title}]({url})\n"
                    md_content += "\n"
        
        md_content += f"\n---\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        st.download_button(
            label="📝 Download Markdown",
            data=md_content,
            file_name=f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            key="btn_download_markdown"
        )
    
    with export_cols[2]:
        # PDF placeholder
        st.button(
            "📄 Generate PDF",
            disabled=True,
            key="btn_generate_pdf",
            help="PDF export coming soon!"
        )

# Footer
st.markdown("---")
footer_cols = st.columns([2, 1])
with footer_cols[0]:
    st.caption("Multi-Agent AI Deep Researcher | Version 2.0")
with footer_cols[1]:
    st.caption(f"© {datetime.now().year} | Powered by Perplexity AI")