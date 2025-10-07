"""
Results Display Module
Handles all results visualization and export functionality
"""

import streamlit as st
import json
from datetime import datetime
import pandas as pd

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from utils import generate_comprehensive_pdf, PDF_AVAILABLE

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
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Sources</div>
            <div class="metric-value">{len(results.get('sources', []))}</div>
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
    
    import os
    with col1:
        results_json = json.dumps(results, indent=2, ensure_ascii=False)
        json_filename = f"luminar_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        # Check if file exists before offering download (for session/history restore)
        if not os.path.exists(json_filename):
            st.download_button(
                "📥 Download Results JSON",
                results_json,
                json_filename,
                "application/json",
                width='stretch',
                key="download_results_json_btn"
            )
        else:
            st.info(f"JSON file {json_filename} not found or already downloaded.")
    
    with col2:
        pdf_filename = f"luminar_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        if PDF_AVAILABLE:
            pdf_buffer = generate_comprehensive_pdf(results)
            # Check if file exists before offering download
            if pdf_buffer and not os.path.exists(pdf_filename):
                st.download_button(
                    "📄 Download Comprehensive PDF",
                    pdf_buffer,
                    pdf_filename,
                    "application/pdf",
                    width='stretch',
                    key="download_pdf_btn"
                )
            else:
                st.info(f"PDF file {pdf_filename} not found or already downloaded.")
        else:
            st.button("📄 PDF Export Unavailable", disabled=True, width='stretch')
    
    # TABS
    tabs = st.tabs([
        "📊 Overview", 
        "📋 Summary", 
        "🔍 Findings", 
        "💡 Insights", 
        "🔗 Sources",
        "📈 Statistics"
    ])
    
    # TAB 1: Overview
    with tabs[0]:
        display_overview_tab(results)
    
    # TAB 2: Executive Summary
    with tabs[1]:
        display_summary_tab(results)
    
    # TAB 3: Key Findings
    with tabs[2]:
        display_findings_tab(results)
    
    # TAB 4: Strategic Insights
    with tabs[3]:
        display_insights_tab(results)
    
    # TAB 5: All Sources
    with tabs[4]:
        display_sources_tab(results)
    
    # TAB 6: Statistics
    with tabs[5]:
        display_statistics_tab(results)

def display_overview_tab(results):
    """Display analysis overview"""
    st.markdown("### 🎯 Agent Performance Breakdown")
    
    agent_data = results.get('agent_data', [])
    if agent_data:
        df_data = []
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
                    "Cost": f"${agent.get('cost', 0):.4f}",
                    "Time": f"{agent.get('execution_time', 0):.2f}s",
                    "Medium": agent.get('medium', 'N/A')
                })
            df = pd.DataFrame(df_data)
            # Clean currency columns for Arrow compatibility
            for col in ["Value", "Cost", "Per Source"]:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(r"[$,]", "", regex=True)
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            st.dataframe(df, width='stretch', hide_index=True)
            st.markdown("---")
            # Quality indicators
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Coverage**")
                total_sources = sum(a.get('source_count', 0) for a in agent_data)
                coverage = "Excellent" if total_sources >= 15 else "Good" if total_sources >= 8 else "Limited"
                st.info(f"**{coverage}**\n\n{total_sources} total sources")
            with col2:
                st.markdown("**Diversity**")
                successful = sum(1 for a in agent_data if '✅' in a.get('status', ''))
                diversity = "High" if successful >= 3 else "Medium" if successful >= 2 else "Low"
                st.info(f"**{diversity}**\n\n{successful}/{len(agent_data)} agents")
            with col3:
                st.markdown("**Confidence**")
                confidence = results.get('confidence_score', 0)
                level = "High" if confidence >= 75 else "Medium" if confidence >= 50 else "Low"
                st.info(f"**{level}**\n\n{confidence}/100 score")
            confidence = results.get('confidence_score', 0)
            level = "High" if confidence >= 75 else "Medium" if confidence >= 50 else "Low"
            st.info(f"**{level}**\n\n{confidence}/100 score")

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
            clean = finding.strip()
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
            clean = insight.strip()
            if clean:
                st.markdown(f"""
                <div style="display: inline-block; background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); color: white; padding: 0.75rem 1.25rem; border-radius: 24px; margin: 0.5rem 0.5rem 0.5rem 0; font-size: 0.95rem; font-weight: 500; box-shadow: 0 2px 8px rgba(14, 165, 233, 0.2);">
                    ✓ {clean}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No strategic insights available")

def display_sources_tab(results):
    """Display all sources"""
    st.markdown('<div class="section-title">🔗 Research Sources</div>', unsafe_allow_html=True)
    
    sources_by_agent = {}
    for source in results.get('sources', []):
        agent = source.get('agent', 'Unknown')
        if agent not in sources_by_agent:
            sources_by_agent[agent] = []
        sources_by_agent[agent].append(source)
    
    if sources_by_agent:
        for agent_name, sources in sources_by_agent.items():
            st.markdown(f"#### {agent_name} ({len(sources)} sources)")
            
            for idx, source in enumerate(sources, 1):
                source_type = source.get('source_type', 'Unknown')
                medium = source.get('medium', 'N/A')
                st.markdown(f"""
                <div style="background: white; border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                        <div style="font-weight: 600; color: #0ea5e9; flex: 1;">{idx}. {source.get('title', 'Unknown')}</div>
                        <span style="background: #e0f2fe; color: #0284c7; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.75rem; white-space: nowrap; margin-left: 1rem;">{source_type}</span>
                    </div>
                    <div style="color: #64748b; font-size: 0.85rem; margin-bottom: 0.5rem;">📡 Medium: {medium}</div>
                    <a href="{source.get('url', '#')}" target="_blank" style="color: #64748b; font-size: 0.85rem; word-break: break-all;">🔗 {source.get('url', 'N/A')}</a>
                    <div style="color: #475569; margin-top: 0.5rem; font-size: 0.9rem;">{source.get('summary', 'No description')}</div>
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
            successful_agents = sum(1 for a in agent_data if '✅' in a.get('status', ''))
            st.metric("Successful Agents", f"{successful_agents}/{len(agent_data)}")
        
        st.markdown("---")
        
        # Token Usage Statistics
        st.markdown("### 🔢 Token Usage Analysis")
        
        token_data = []
        for agent in agent_data:
            if agent.get('tokens', 0) > 0:
                token_data.append({
                    "Agent": agent.get('agent_name', 'Unknown'),
                    "Total Tokens": agent.get('tokens', 0),
                    "Prompt Tokens": agent.get('prompt_tokens', 0),
                    "Completion Tokens": agent.get('completion_tokens', 0),
                    "Efficiency %": f"{(agent.get('completion_tokens', 0) / max(agent.get('tokens', 1), 1) * 100):.1f}%"
                })
        
        if token_data:
            df_tokens = pd.DataFrame(token_data)
            # Clean currency columns for Arrow compatibility
            for col in ["Value", "Cost", "Per Source"]:
                if col in df_tokens.columns:
                    df_tokens[col] = df_tokens[col].astype(str).str.replace(r"[$,]", "", regex=True)
                    df_tokens[col] = pd.to_numeric(df_tokens[col], errors="coerce")
            st.dataframe(df_tokens, width='stretch', hide_index=True)
            
            # Token chart
            if MATPLOTLIB_AVAILABLE and len(token_data) > 0:
                fig, ax = plt.subplots(figsize=(10, 4))
                
                agents = [d['Agent'][:15] for d in token_data]
                totals = [d['Total Tokens'] for d in token_data]
                
                bars = ax.bar(agents, totals, color=['#0ea5e9', '#f97316', '#10b981'])
                ax.set_title('Total Tokens by Agent', fontsize=12, fontweight='bold')
                ax.set_ylabel('Tokens', fontsize=10)
                
                for i, v in enumerate(totals):
                    ax.text(i, v, str(v), ha='center', va='bottom', fontsize=9)
                
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
        
        st.markdown("---")
        
        # Cost Analysis
        st.markdown("### 💰 Cost Distribution")
        
        cost_data = []
        for agent in agent_data:
            if agent.get('cost', 0) > 0:
                cost_data.append({
                    "Agent": agent.get('agent_name', 'Unknown'),
                    "Cost": f"${agent.get('cost', 0):.4f}",
                    "Per Source": f"${(agent.get('cost', 0) / max(agent.get('source_count', 1), 1)):.4f}"
                })
        
        if cost_data:
            df_cost = pd.DataFrame(cost_data)
            # Clean currency columns for Arrow compatibility
            for col in ["Value", "Cost", "Per Source"]:
                if col in df_cost.columns:
                    df_cost[col] = df_cost[col].astype(str).str.replace(r"[$,]", "", regex=True)
                    df_cost[col] = pd.to_numeric(df_cost[col], errors="coerce")
            st.dataframe(df_cost, width='stretch', hide_index=True)
        
        st.markdown("---")
        
        # Summary Statistics
        st.markdown("### 📋 Summary Statistics")
        
        summary_stats = {
            "Total Agents": len(agent_data),
            "Successful Agents": successful_agents,
            "Total Sources": sum(a.get('source_count', 0) for a in agent_data),
            "Total Findings": sum(a.get('findings_count', 0) for a in agent_data),
            "Total Insights": sum(a.get('insights_count', 0) for a in agent_data),
            "Total Tokens": results.get('total_tokens', 0),
            "Total Cost": f"${results.get('total_cost', 0):.4f}",
            "Total Time": f"{results.get('execution_time', 0):.2f}s",
            "Confidence Score": f"{results.get('confidence_score', 0)}/100"
        }
        
        summary_df = pd.DataFrame([summary_stats]).T
        summary_df.columns = ['Value']
        # Clean currency columns for Arrow compatibility
        for col in ["Value", "Cost", "Per Source"]:
            if col in summary_df.columns:
                summary_df[col] = summary_df[col].astype(str).str.replace(r"[$,]", "", regex=True)
                summary_df[col] = pd.to_numeric(summary_df[col], errors="coerce")
        st.dataframe(summary_df, width='stretch')
        
    else:
        st.info("No statistics available")