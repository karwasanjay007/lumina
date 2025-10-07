"""
Luminar Deep Researcher v2.1.0 - Main Application
Multi-Agent AI Research Platform
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

if 'session_active' not in st.session_state:
    st.session_state.session_active = True

# ============================================================================
# CSS STYLING
# ============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .main {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #fff7ed 100%);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border-right: 1px solid #e2e8f0;
    }
    
    .luminar-header {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 70%, #f97316 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(14, 165, 233, 0.2);
        text-align: center;
    }
    
    .luminar-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: white;
        margin: 0;
    }
    
    .luminar-subtitle {
        font-size: 1.1rem;
        color: rgba(255,255,255,0.95);
        margin-top: 0.5rem;
    }
    
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(14, 165, 233, 0.15);
        border-color: #0ea5e9;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.5rem 0;
    }
    
    .history-item {
        background: white;
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        border: 1px solid #e2e8f0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .history-item:hover {
        border-color: #0ea5e9;
        transform: translateX(4px);
        box-shadow: 0 2px 8px rgba(14, 165, 233, 0.15);
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
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("### 📚 Research History")
    
    if st.session_state.research_history:
        # Show last 15 items
        for idx, item in enumerate(reversed(st.session_state.research_history[-15:])):
            history_key = f"hist_{item['timestamp']}_{idx}"
            
            button_label = f"""📄 {item['query'][:30]}...
🕒 {item['timestamp'][:16]}
🔬 {item.get('model_type', 'N/A')}
📊 {item.get('domain', 'N/A')[:20]}"""
            
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
        
    if st.button("🗑️ Clear History", width='stretch', key="clear_history_btn"):
            if st.session_state.research_history:
                save_history_to_json()
                st.session_state.research_history = []
                st.session_state.current_results = None
                st.success("✅ History cleared!")
                time.sleep(1)
                st.rerun()
    else:
        st.info("No history yet. Start a research query!")
    
    st.markdown("---")
    st.markdown("### ⚙️ Configuration")
    
    # MODEL SELECTION
    with st.expander("🤖 Market Intelligence Model", expanded=True):
        st.markdown("**Select Research Mode**")
        
        for model_name, config in PERPLEXITY_MODELS.items():
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button(
                    config["icon"],
                    key=f"model_{model_name}",
                    width='stretch'
                ):
                    st.session_state.market_model_type = model_name
            
            with col2:
                selected = " ✓" if st.session_state.market_model_type == model_name else ""
                st.markdown(f"**{model_name}{selected}**")
                st.caption(f"{config['description']} • {config['estimated_cost']}")
        
        st.markdown("---")
        st.markdown(f"**Selected:** {st.session_state.market_model_type}")
        st.markdown(f"**Model:** `{PERPLEXITY_MODELS[st.session_state.market_model_type]['model']}`")
    
    with st.expander("📊 Agent Settings", expanded=False):
        st.markdown("**Market Intelligence Sources**")
        market_sources = st.slider(
            "Market sources",
            1, 30, 
            st.session_state.market_sources, 
            key="market_slider",
            label_visibility="collapsed"
        )
        st.session_state.market_sources = market_sources
        
        st.markdown("**Sentiment Analytics Sources**")
        sentiment_sources = st.slider(
            "Sentiment sources",
            1, 20, 
            st.session_state.sentiment_sources, 
            key="sentiment_slider",
            label_visibility="collapsed"
        )
        st.session_state.sentiment_sources = sentiment_sources
        
        st.markdown("**Data Intelligence Sources**")
        data_sources = st.slider(
            "Data sources",
            1, 20, 
            st.session_state.data_sources, 
            key="data_slider",
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
    st.caption(f"{model_icon} {st.session_state.market_model_type} • {st.session_state.market_sources} sources")

with col2:
    agent_sentiment = st.checkbox(
        "📊 Sentiment Analytics", 
        value=st.session_state.current_agents.get("Sentiment Analytics", False),
        key="agent_sentiment_check"
    )
    st.caption(f"🎥 YouTube API • {st.session_state.sentiment_sources} sources")

with col3:
    agent_data = st.checkbox(
        "📈 Data Intelligence", 
        value=st.session_state.current_agents.get("Data Intelligence", False),
        key="agent_data_check"
    )
    st.caption(f"📚 arXiv + News • {st.session_state.data_sources} sources")

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
        st.error("⚠️ Please select at least one intelligence agent")
    else:
        with st.spinner("🔬 Conducting deep research analysis..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Initializing research agents...")
            progress_bar.progress(0.1)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            status_text.text("Executing parallel research...")
            progress_bar.progress(0.3)
            
            agent_results = loop.run_until_complete(
                execute_research(
                    query, 
                    domain, 
                    st.session_state.current_agents, 
                    st.session_state.market_model_type,
                    st.session_state.mock_mode,
                    st.session_state.market_sources,
                    st.session_state.sentiment_sources,
                    st.session_state.data_sources
                )
            )
            loop.close()
            
            status_text.text("Synthesizing results...")
            progress_bar.progress(0.8)
            
            # Consolidate results
            all_findings = []
            all_insights = []
            all_sources = []
            total_tokens = 0
            total_cost = 0.0
            total_execution_time = 0.0
            primary_summary = ""
            agent_data = []
            
            for agent_name, result in agent_results.items():
                if result.get('success'):
                    if not primary_summary:
                        primary_summary = result.get('summary', '')
                    
                    all_findings.extend(result.get('findings', []))
                    all_insights.extend(result.get('insights', []))
                    all_sources.extend(result.get('sources', []))
                    total_tokens += result.get('tokens', 0)
                    total_cost += result.get('cost', 0.0)
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