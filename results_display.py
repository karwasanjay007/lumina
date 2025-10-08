"""
Results Display Module - FIXED VERSION
Handles all results visualization with proper source structure handling
"""

import streamlit as st
import json
from datetime import datetime
import pandas as pd
import os

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from utils import generate_comprehensive_pdf, PDF_AVAILABLE

def flatten_sources(sources):
    """
    Flatten nested source structures from agents
    Handles both flat lists and nested structures
    """
    flattened = []
    
    for source in sources:
        # Check if source has 'items' (nested structure from build_structured_record)
        if isinstance(source, dict) and 'items' in source:
            # Extract items from nested structure
            for item in source.get('items', []):
                flattened.append({
                    'title': item.get('title', 'Unknown'),
                    'url': item.get('source', item.get('url', '#')),
                    'summary': item.get('summary', 'No description'),
                    'agent': source.get('agent_name', item.get('authors', ['Unknown'])[0] if item.get('authors') else 'Unknown'),
                    'source_type': source.get('source_name', 'Web Research'),
                    'medium': source.get('metadata', {}).get('medium', 'N/A') if 'metadata' in source else 'N/A'
                })
        else:
            # Already flat structure
            flattened.append({
                'title': source.get('title', 'Unknown'),
                'url': source.get('url', '#'),
                'summary': source.get('summary', 'No description'),
                'agent': source.get('agent', 'Unknown'),
                'source_type': source.get('source_type', 'Unknown'),
                'medium': source.get('medium', 'N/A')
            })
    
    return flattened

def display_results(results):
    """Display comprehensive research results"""
    
    st.markdown("---")
    st.markdown("## 📊 Research Results")
    
    # Top metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Cost</div>
            <div class="metric-value">${results.get('total_cost', 0):.4f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Tokens</div>
            <div class="metric-value">{results.get('total_tokens', 0):,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Time</div>
            <div class="metric-value">{results.get('execution_time', 0):.1f}s</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # FIXED: Flatten sources before counting
        all_sources = flatten_sources(results.get('sources', []))
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Sources</div>
            <div class="metric-value">{len(all_sources)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        confidence = results.get('confidence_score', 0)
        color = "#10b981" if confidence >= 75 else "#f59e0b" if confidence >= 50 else "#ef4444"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Confidence</div>
            <div class="metric-value" style="background: linear-gradient(135deg, {color} 0%, {color} 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{confidence}/100</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Export buttons
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        results_json = json.dumps(results, indent=2, ensure_ascii=False)
        json_filename = f"luminar_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        st.download_button(
            "📥 Download Results JSON",
            results_json,
            json_filename,
            "application/json",
            width='stretch',
            key="download_results_json_btn"
        )
    
    with col2:
        pdf_filename = f"luminar_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        if PDF_AVAILABLE:
            try:
                pdf_buffer = generate_comprehensive_pdf(results)
                if pdf_buffer:
                    st.download_button(
                        "📄 Download PDF Report",
                        pdf_buffer,
                        pdf_filename,
                        "application/pdf",
                        width='stretch',
                        key="download_pdf_btn"
                    )
                else:
                    st.button("📄 PDF Export", disabled=True, width='stretch')
            except Exception as e:
                st.button(f"📄 PDF Error: {str(e)[:30]}", disabled=True, width='stretch')
        else:
            st.button("📄 PDF Unavailable", disabled=True, width='stretch')
    
    # TABS
    tabs = st.tabs([
        "📊 Overview", 
        "📋 Summary", 
        "🔍 Findings", 
        "💡 Insights", 
        "🔗 Sources",
        "📈 Statistics"
    ])
    
    with tabs[0]:
        display_overview_tab(results)
    
    with tabs[1]:
        display_summary_tab(results)
    
    with tabs[2]:
        display_findings_tab(results)
    
    with tabs[3]:
        display_insights_tab(results)
    
    with tabs[4]:
        display_sources_tab(results)
    
    with tabs[5]:
        display_statistics_tab(results)

def display_overview_tab(results):
    """Display analysis overview"""
    st.markdown("### 🎯 Agent Performance Breakdown")
    
    agent_data = results.get('agent_data', [])
    if agent_data:
        df_data = []
        for agent in agent_data:
            df_data.append({
                "Agent": agent.get('agent_name', 'Unknown'),
                "Status": agent.get('status', 'Unknown'),
                "Sources": agent.get('source_count', 0),
                "Findings": agent.get('findings_count', 0),
                "Insights": agent.get('insights_count', 0),
                "Tokens": agent.get('tokens', 0),
                "Cost": agent.get('cost', 0),
                "Time": f"{agent.get('execution_time', 0):.2f}s",
                "Medium": agent.get('medium', 'N/A')
            })
        
        # Create DataFrame
        df = pd.DataFrame(df_data)
        
        # Format cost column
        df['Cost'] = df['Cost'].apply(lambda x: f"${x:.4f}")
        
        # Display table
        st.dataframe(
            df,
            width='stretch',
            hide_index=True
        )
    else:
        st.warning("No agent performance data available")
    
    # Confidence Score
    st.markdown("---")
    st.markdown("### 🎯 Research Confidence")
    
    confidence = results.get('confidence_score', 0)
    
    if confidence > 0:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.progress(confidence / 100)
        
        with col2:
            level = "High" if confidence >= 75 else "Medium" if confidence >= 50 else "Low"
            st.info(f"**{level}** - {confidence}/100")
    else:
        st.info("Confidence score not available")

def display_summary_tab(results):
    """Display executive summary"""
    st.markdown(f"""
    <div class="content-section">
        <div class="section-title">📊 Executive Summary</div>
        <div style="font-size: 1.05rem; line-height: 1.8; color: #334155;">
            {results.get('summary', 'No summary available').replace(chr(10), '<br><br>')}
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_findings_tab(results):
    """Display key findings"""
    st.markdown('<div class="section-title">🔍 Key Findings</div>', unsafe_allow_html=True)
    findings = results.get('key_findings', [])
    
    if findings:
        for idx, finding in enumerate(findings, 1):
            clean = finding.strip() if isinstance(finding, str) else str(finding)
            if clean:
                st.markdown(f"""
                <div class="finding-card">
                    <span style="color: #f97316; font-weight: 700; margin-right: 0.75rem; font-size: 1.1rem;">{idx}.</span>
                    <span style="color: #334155; line-height: 1.7;">{clean}</span>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No key findings available")

def display_insights_tab(results):
    """Display strategic insights"""
    st.markdown('<div class="section-title">💡 Strategic Insights</div>', unsafe_allow_html=True)
    insights = results.get('insights', [])
    
    if insights:
        for insight in insights:
            clean = insight.strip() if isinstance(insight, str) else str(insight)
            if clean:
                st.markdown(f"""
                <div style="display: inline-block; background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); color: white; padding: 0.75rem 1.25rem; border-radius: 24px; margin: 0.5rem 0.5rem 0.5rem 0; font-size: 0.95rem; font-weight: 500; box-shadow: 0 2px 8px rgba(14, 165, 233, 0.2);">
                    ✓ {clean}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No strategic insights available")

def display_sources_tab(results):
    """
    Display all sources - FIXED to handle nested structures
    """
    st.markdown('<div class="section-title">🔗 Research Sources</div>', unsafe_allow_html=True)
    
    # FIXED: Flatten sources first
    all_sources = flatten_sources(results.get('sources', []))
    
    # Group by agent
    sources_by_agent = {}
    for source in all_sources:
        agent = source.get('agent', 'Unknown')
        if agent not in sources_by_agent:
            sources_by_agent[agent] = []
        sources_by_agent[agent].append(source)
    
    if sources_by_agent:
        for agent_name, sources in sources_by_agent.items():
            st.markdown(f"#### {agent_name} ({len(sources)} sources)")
            
            for idx, source in enumerate(sources, 1):
                title = source.get('title', 'Unknown')
                source_type = source.get('source_type', 'Unknown')
                medium = source.get('medium', 'N/A')
                url = source.get('url', '#')
                summary = source.get('summary', 'No description')
                
                # Clean up N/A values
                if not url or url == '#' or url == 'N/A':
                    url = '#'
                    url_display = 'URL not available'
                else:
                    url_display = url
                
                st.markdown(f"""
                <div style="background: white; border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                        <div style="font-weight: 600; color: #0ea5e9; flex: 1;">{idx}. {title}</div>
                        <span style="background: #e0f2fe; color: #0284c7; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.75rem; white-space: nowrap; margin-left: 1rem;">{source_type}</span>
                    </div>
                    <div style="color: #64748b; font-size: 0.85rem; margin-bottom: 0.5rem;">📡 Medium: {medium}</div>
                    <a href="{url}" target="_blank" style="color: #64748b; font-size: 0.85rem; word-break: break-all;">🔗 {url_display}</a>
                    <div style="color: #475569; margin-top: 0.5rem; font-size: 0.9rem;">{summary}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No sources available")

def display_statistics_tab(results):
    """Display comprehensive statistics"""
    st.markdown('<div class="section-title">📈 Comprehensive Statistics</div>', unsafe_allow_html=True)
    
    agent_data = results.get('agent_data', [])
    
    if agent_data:
        # Overall statistics
        st.markdown("### 📊 Overall Performance Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_sources = sum(a.get('source_count', 0) for a in agent_data)
            st.metric("Total Sources", total_sources)
        
        with col2:
            total_findings = sum(a.get('findings_count', 0) for a in agent_data)
            st.metric("Total Findings", total_findings)
        
        with col3:
            total_insights = sum(a.get('insights_count', 0) for a in agent_data)
            st.metric("Total Insights", total_insights)
        
        with col4:
            avg_time = sum(a.get('execution_time', 0) for a in agent_data) / len(agent_data)
            st.metric("Avg Time/Agent", f"{avg_time:.2f}s")
        
        st.markdown("---")
        
        # Token Usage Breakdown
        st.markdown("### 🎫 Token Usage Breakdown")
        
        for agent in agent_data:
            if agent.get('tokens', 0) > 0:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**{agent.get('agent_name')}**")
                
                with col2:
                    prompt_tokens = agent.get('prompt_tokens', 0)
                    completion_tokens = agent.get('completion_tokens', 0)
                    total_tokens = agent.get('tokens', prompt_tokens + completion_tokens)
                    st.write(f"Total: {total_tokens:,}")
                
                with col3:
                    cost = agent.get('cost', 0)
                    st.write(f"Cost: ${cost:.4f}")
        
        st.markdown("---")
        
        # Performance Summary
        st.markdown("### ⚡ Performance Summary")
        
        success_count = sum(1 for a in agent_data if 'Success' in a.get('status', ''))
        total_agents = len(agent_data)
        success_rate = (success_count / total_agents * 100) if total_agents > 0 else 0
        
        st.progress(success_rate / 100)
        st.write(f"**Success Rate:** {success_rate:.1f}% ({success_count}/{total_agents} agents)")
        
    else:
        st.info("No statistics available")