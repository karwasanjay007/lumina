"""
Luminar Deep Researcher v2.1.0 - Main Application
Multi-Agent AI Research Platform - FIXED VERSION
"""

import streamlit as st
import json
from datetime import datetime
import time
import asyncio
from pathlib import Path
import sys

# Import modular components
from research_engine import execute_research, PERPLEXITY_MODELS
from utils import (
    console_log,
    calculate_confidence_score,
    save_history_to_json,
    load_history_from_json,
    generate_comprehensive_pdf,
    PDF_AVAILABLE
)

# Page configuration
st.set_page_config(
    page_title="Luminar Deep Researcher",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

# History Configuration
if 'max_history_items' not in st.session_state:
    st.session_state.max_history_items = 5  # Default limit, configurable

# History Management
if 'research_history' not in st.session_state:
    st.session_state.research_history = []

if 'current_results' not in st.session_state:
    st.session_state.current_results = None

if 'save_history' not in st.session_state:
    st.session_state.save_history = True

# DEFAULT VALUES - ALL SET TO 2
if 'market_sources' not in st.session_state:
    st.session_state.market_sources = 2

if 'sentiment_sources' not in st.session_state:
    st.session_state.sentiment_sources = 2

if 'data_sources' not in st.session_state:
    st.session_state.data_sources = 2

if 'max_cost' not in st.session_state:
    st.session_state.max_cost = 2.0

if 'mock_mode' not in st.session_state:
    st.session_state.mock_mode = False

if 'current_query' not in st.session_state:
    st.session_state.current_query = ""

if 'current_domain' not in st.session_state:
    st.session_state.current_domain = "Stock Market Analysis"

if 'current_agents' not in st.session_state:
    st.session_state.current_agents = {
        "Market Intelligence": True,
        "Sentiment Analytics": False,
        "Data Intelligence": False
    }

if 'total_queries' not in st.session_state:
    st.session_state.total_queries = 0

if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0.0

# DEFAULT MODEL TYPE - QUICK SEARCH
if 'market_model_type' not in st.session_state:
    st.session_state.market_model_type = "Quick Search"

# ============================================================================
# CUSTOM CSS WITH TEXT OVERFLOW FIXES
# ============================================================================

st.markdown("""
<style>
    .luminar-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .luminar-title {
        color: white;
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .luminar-subtitle {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
    }
    
    /* FIXED: History item text overflow */
    .history-item {
        background: white;
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        border: 1px solid #e2e8f0;
        cursor: pointer;
        transition: all 0.3s ease;
        word-wrap: break-word;
        overflow: hidden;
    }
    
    .history-item:hover {
        border-color: #0ea5e9;
        transform: translateX(4px);
        box-shadow: 0 2px 8px rgba(14, 165, 233, 0.15);
    }
    
    /* FIXED: Text wrapping for long content */
    .history-item button {
        white-space: normal !important;
        text-align: left !important;
        line-height: 1.4 !important;
    }
    
    /* FIXED: Ensure values don't overflow */
    .stMetric label, .stMetric > div {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    /* FIXED: Agent card text overflow */
    .agent-card {
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    
    /* FIXED: Caption text wrapping */
    .stCaption {
        white-space: normal !important;
        word-wrap: break-word !important;
    }
    
    .content-section {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 1.5rem;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 0.75rem;
    }
    
    .finding-card {
        background: white;
        border-radius: 8px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #f97316;
        transition: all 0.3s ease;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        word-wrap: break-word;
    }
    
    .finding-card:hover {
        background: #fffbfa;
        transform: translateX(6px);
        box-shadow: 0 4px 12px rgba(249, 115, 22, 0.15);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        white-space: normal;
        word-wrap: break-word;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# LOAD HISTORY ON STARTUP
# ============================================================================

if not st.session_state.research_history:
    load_history_from_json()

# ============================================================================
# SIDEBAR WITH FIXED HISTORY DISPLAY
# ============================================================================

with st.sidebar:
    st.markdown("### 📚 Research History")
    
    # FIXED: Show history only if it exists
    if st.session_state.research_history and len(st.session_state.research_history) > 0:
        # Show last items based on max_history_items
        display_count = min(len(st.session_state.research_history), 15)
        for idx, item in enumerate(reversed(st.session_state.research_history[-display_count:])):
            history_key = f"hist_{item['timestamp']}_{idx}"
            
            # FIXED: Truncate query text properly
            query_display = item['query'][:40] + "..." if len(item['query']) > 40 else item['query']
            domain_display = item.get('domain', 'N/A')[:25]
            
            # FIXED: Create multiline button label with proper formatting
            button_label = f"📄 {query_display}\n🕒 {item['timestamp'][:16]}\n🔬 {item.get('model_type', 'N/A')[:20]}\n📊 {domain_display}"
            
            if st.button(button_label, key=history_key, width='stretch'):
                # Restore complete state from history
                st.session_state.current_results = item['results']
                st.session_state.current_query = item['query']
                st.session_state.current_domain = item['domain']
                st.session_state.current_agents = item.get('agents_state', {})
                st.session_state.market_model_type = item.get('model_type', 'Quick Search')
                st.session_state.market_sources = item.get('market_sources', 2)
                st.session_state.sentiment_sources = item.get('sentiment_sources', 2)
                st.session_state.data_sources = item.get('data_sources', 2)
                console_log(f"📂 Restored history item: {item['query'][:40]}")
                st.rerun()
        
        st.markdown("---")
        
        # Download Complete History JSON
        history_json = json.dumps(st.session_state.research_history, indent=2, ensure_ascii=False)
        st.download_button(
            "📥 Download Complete History",
            history_json,
            f"luminar_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "application/json",
            width='stretch',
            key="download_history_json"
        )
    else:
        # FIXED: This should only show when there's actually no history
        st.info("No history yet. Start a research query!")
    
    # ========================================================================
    # CLEAR HISTORY BUTTON - FIXED VERSION (ONLY ONE!)
    # ========================================================================
    if st.button("🗑️ Clear History", width='stretch', key="clear_history_btn"):
        if st.session_state.research_history and len(st.session_state.research_history) > 0:
            # FIXED: Clear directly without saving first
            st.session_state.research_history = []
            st.session_state.current_results = None
            st.session_state.current_query = ""
            
            # Clear the JSON file
            try:
                history_file = Path("data/history/research_history.json")
                if history_file.exists():
                    history_file.write_text("[]", encoding='utf-8')
            except Exception as e:
                console_log(f"Error clearing history file: {e}", "ERROR")
            
            st.success("✅ History cleared successfully!")
            st.rerun()
        else:
            st.info("No history to clear")
    
    st.markdown("---")
    
    # History Configuration
    st.markdown("### ⚙️ History Settings")
    max_history = st.number_input(
        "Max history items to store",
        min_value=1,
        max_value=50,
        value=st.session_state.max_history_items,
        step=1,
        help="Number of research queries to keep in history before overriding old ones"
    )
    
    if max_history != st.session_state.max_history_items:
        st.session_state.max_history_items = max_history
        st.success(f"✅ History limit set to {max_history} items")
    
    st.markdown("---")
    
    # Agent Configuration
    with st.expander("🤖 Agent Settings", expanded=False):
        st.markdown("**Market Intelligence**")
        model_type = st.selectbox(
            "Model type",
            list(PERPLEXITY_MODELS.keys()),
            index=list(PERPLEXITY_MODELS.keys()).index(st.session_state.market_model_type),
            label_visibility="collapsed",
            key="model_type_select"
        )
        st.session_state.market_model_type = model_type
        
        market_sources = st.number_input(
            "Market sources",
            value=st.session_state.market_sources,
            min_value=1,
            max_value=20,
            step=1,
            label_visibility="collapsed"
        )
        st.session_state.market_sources = market_sources
        
        st.markdown("**Sentiment Analytics**")
        sentiment_sources = st.number_input(
            "Sentiment sources",
            value=st.session_state.sentiment_sources,
            min_value=1,
            max_value=10,
            step=1,
            label_visibility="collapsed"
        )
        st.session_state.sentiment_sources = sentiment_sources
        
        st.markdown("**Data Intelligence**")
        data_sources = st.number_input(
            "Data sources",
            value=st.session_state.data_sources,
            min_value=1,
            max_value=20,
            step=1,
            label_visibility="collapsed"
        )
        st.session_state.data_sources = data_sources
    
    with st.expander("💰 Cost Settings", expanded=False):
        st.markdown("**Max Cost per Query ($)**")
        max_cost = st.number_input(
            "Max cost",
            value=st.session_state.max_cost,
            min_value=0.1,
            max_value=10.0,
            step=0.1,
            label_visibility="collapsed"
        )
        st.session_state.max_cost = max_cost
    
    st.markdown("---")
    st.markdown("### 📊 Session Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Queries", st.session_state.total_queries)
    with col2:
        st.metric("Cost", f"${st.session_state.total_cost:.4f}")
    
    st.markdown("---")
    # FIXED: Mock mode toggle with proper state management
    mock_mode = st.toggle("🎭 Mock Mode", value=st.session_state.mock_mode, key="mock_toggle")
    st.session_state.mock_mode = mock_mode
    
    if mock_mode:
        st.warning("⚠️ Mock mode - Enhanced simulated data")
    else:
        st.success("✅ Live APIs - Real data sources")
    
    st.markdown("---")
    save_history = st.toggle("💾 Auto-save History", value=st.session_state.save_history, key="save_toggle")
    st.session_state.save_history = save_history

# ============================================================================
# MAIN INTERFACE
# ============================================================================

st.markdown("""
<div class="luminar-header">
    <h1 class="luminar-title">🔬 Luminar Deep Researcher</h1>
    <p class="luminar-subtitle">Multi-Agent AI Research Platform v2.1 - Modular Edition</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    domain_options = ["Stock Market Analysis", "Medical Research", "Technology Trends", "Academic Research", "General Research"]
    domain_index = domain_options.index(st.session_state.current_domain) if st.session_state.current_domain in domain_options else 0
    domain = st.selectbox("🎯 Research Domain", domain_options, index=domain_index, key="domain_select")
    st.session_state.current_domain = domain

with col2:
    st.metric("Research History", len(st.session_state.research_history))

query = st.text_area(
    "🔍 Research Question",
    value=st.session_state.current_query,
    height=120,
    placeholder="Enter your research question here...",
    key="query_input"
)
st.session_state.current_query = query

st.markdown("### 🤖 Select Intelligence Agents")

col1, col2, col3 = st.columns(3)

with col1:
    agent_market = st.checkbox(
        "🌐 Market Intelligence",
        value=st.session_state.current_agents.get("Market Intelligence", True),
        key="agent_market_check"
    )
    model_icon = PERPLEXITY_MODELS[st.session_state.market_model_type]["icon"]
    # FIXED: Proper text wrapping for captions
    st.caption(f"{model_icon} {st.session_state.market_model_type}")
    st.caption(f"Sources: {st.session_state.market_sources}")

with col2:
    agent_sentiment = st.checkbox(
        "📊 Sentiment Analytics",
        value=st.session_state.current_agents.get("Sentiment Analytics", False),
        key="agent_sentiment_check"
    )
    st.caption("🎥 YouTube API")
    st.caption(f"Sources: {st.session_state.sentiment_sources}")

with col3:
    agent_data = st.checkbox(
        "📈 Data Intelligence",
        value=st.session_state.current_agents.get("Data Intelligence", False),
        key="agent_data_check"
    )
    st.caption("📚 arXiv + News")
    st.caption(f"Sources: {st.session_state.data_sources}")

st.session_state.current_agents = {
    "Market Intelligence": agent_market,
    "Sentiment Analytics": agent_sentiment,
    "Data Intelligence": agent_data
}

st.markdown("---")

# ============================================================================
# RESEARCH EXECUTION
# ============================================================================

if st.button("🚀 Start Deep Research", width='stretch', type="primary", key="start_research_btn"):
    if not query:
        st.error("⚠️ Please enter a research question")
    elif not any(st.session_state.current_agents.values()):
        st.error("⚠️ Please select at least one agent")
    else:
        with st.spinner("🔬 Research in progress..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # CRITICAL FIX: Pass mock_mode to execute_research
            agent_results = execute_research(
                query=query,
                domain=domain,
                agents=st.session_state.current_agents,
                model_type=st.session_state.market_model_type,
                market_sources=st.session_state.market_sources,
                sentiment_sources=st.session_state.sentiment_sources,
                data_sources=st.session_state.data_sources,
                progress_callback=lambda p, msg: (progress_bar.progress(p), status_text.text(msg)),
                mock_mode=st.session_state.mock_mode  # FIXED: Pass the actual mock_mode state
            )
            
            # Process results
            all_findings = []
            all_insights = []
            all_sources = []
            total_cost = 0.0
            total_tokens = 0
            total_execution_time = 0.0
            agent_data = []
            
            primary_summary = "Comprehensive research analysis completed."
            
            for agent_name, result in agent_results.items():
                if result.get('success'):
                    if 'summary' in result and result['summary']:
                        primary_summary = result['summary']
                    
                    all_findings.extend(result.get('findings', []))
                    all_insights.extend(result.get('insights', []))
                    all_sources.extend(result.get('sources', []))
                    total_cost += result.get('cost', 0.0)
                    total_tokens += result.get('tokens', 0)
                    total_execution_time += result.get('execution_time', 0.0)
                    
                    agent_data.append({
                        "agent_name": agent_name,
                        "source_count": result.get('source_count', 0),
                        "sources_retrieved": result.get('sources_retrieved', 0),
                        "findings_count": len(result.get('findings', [])),
                        "insights_count": len(result.get('insights', [])),
                        "cost": result.get('cost', 0.0),
                        "tokens": result.get('tokens', 0),
                        "prompt_tokens": result.get('prompt_tokens', 0),
                        "completion_tokens": result.get('completion_tokens', 0),
                        "execution_time": result.get('execution_time', 0.0),
                        "status": result.get('status', 'Unknown'),
                        "model_used": result.get('model_used', 'N/A'),
                        "model_type": result.get('model_type', 'N/A'),
                        "medium": result.get('medium', 'N/A'),
                        "data_type": result.get('data_type', 'N/A')
                    })
                else:
                    agent_data.append({
                        "agent_name": agent_name,
                        "source_count": 0,
                        "sources_retrieved": 0,
                        "findings_count": 0,
                        "insights_count": 0,
                        "cost": 0.0,
                        "tokens": 0,
                        "execution_time": result.get('execution_time', 0.0),
                        "status": result.get('status', "❌ Failed"),
                        "error": result.get('error', 'Unknown error'),
                        "medium": result.get('medium', 'N/A')
                    })
            
            # Calculate confidence score
            confidence_score = calculate_confidence_score(agent_results, len(all_sources))
            
            # Create complete results object
            results = {
                "query": query,
                "domain": domain,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "agents_used": [k for k, v in st.session_state.current_agents.items() if v],
                "model_type": st.session_state.market_model_type,
                "summary": primary_summary,
                "key_findings": all_findings[:10],
                "insights": all_insights[:7],
                "sources": all_sources,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "execution_time": total_execution_time,
                "confidence_score": confidence_score,
                "mock_mode": st.session_state.mock_mode,
                "agent_data": agent_data,
                "agent_results": agent_results
            }
            
            status_text.text("Finalizing results...")
            progress_bar.progress(0.95)
            
            st.session_state.current_results = results
            st.session_state.total_queries += 1
            st.session_state.total_cost += total_cost
            
            # FIXED: Implement history limit with override
            if st.session_state.save_history:
                history_item = {
                    "query": query,
                    "domain": domain,
                    "timestamp": results["timestamp"],
                    "agents_state": st.session_state.current_agents.copy(),
                    "model_type": st.session_state.market_model_type,
                    "market_sources": st.session_state.market_sources,
                    "sentiment_sources": st.session_state.sentiment_sources,
                    "data_sources": st.session_state.data_sources,
                    "results": results
                }
                
                st.session_state.research_history.append(history_item)
                
                # FIXED: Implement history limit - remove oldest items if exceeded
                if len(st.session_state.research_history) > st.session_state.max_history_items:
                    # Keep only the most recent items
                    st.session_state.research_history = st.session_state.research_history[-st.session_state.max_history_items:]
                    console_log(f"History limited to {st.session_state.max_history_items} items (oldest removed)")
                
                save_history_to_json()
            
            progress_bar.progress(1.0)
            status_text.text("✅ Research complete!")
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            st.success(f"✅ Research completed! Confidence Score: {confidence_score}/100")
            time.sleep(1)
            st.rerun()

# ============================================================================
# DISPLAY RESULTS - Import from results_display.py
# ============================================================================

if st.session_state.current_results:
    from results_display import display_results
    display_results(st.session_state.current_results)

st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #64748b;">
    <p style="font-size: 0.875rem;">Luminar Deep Researcher v2.1.0 - Modular Edition</p>
    <p style="font-size: 0.75rem;">Powered by Luminar AI | © 2025</p>
</div>
""", unsafe_allow_html=True)