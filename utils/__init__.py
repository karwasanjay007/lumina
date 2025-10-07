"""
Utility Functions Module - FIXED VERSION
PDF generation, history management with limits, helper functions
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from io import BytesIO

# PDF generation imports
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
    from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
    from reportlab.lib import colors
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# ============================================================================
# CONSOLE LOGGING
# ============================================================================

def console_log(message, level="INFO"):
    """Console logging with timestamps"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", file=sys.stderr)

# ============================================================================
# CONFIDENCE SCORE CALCULATION
# ============================================================================

def calculate_confidence_score(agent_results, total_sources):
    """Calculate research confidence score"""
    base_score = 40
    
    # Agent diversity bonus
    successful_agents = sum(1 for r in agent_results.values() if r.get('success'))
    agent_bonus = min(successful_agents * 15, 30)
    
    # Source count bonus
    source_bonus = min((total_sources / 20) * 30, 30)
    
    total = base_score + agent_bonus + source_bonus
    return min(int(total), 100)

# ============================================================================
# HISTORY MANAGEMENT WITH LIMIT SUPPORT
# ============================================================================

def save_history_to_json():
    """
    Save history to JSON file with limit enforcement
    FIXED: Now respects max_history_items from session state
    """
    try:
        import streamlit as st
        
        history_file = Path("data/history/research_history.json")
        history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # FIXED: Enforce history limit before saving
        max_items = st.session_state.get('max_history_items', 5)
        if len(st.session_state.research_history) > max_items:
            # Keep only the most recent items
            st.session_state.research_history = st.session_state.research_history[-max_items:]
            console_log(f"History trimmed to {max_items} items before saving")
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.research_history, f, indent=2, ensure_ascii=False)
        
        console_log(f"✅ History saved: {len(st.session_state.research_history)} items")
        return True
    except Exception as e:
        console_log(f"Error saving history: {e}", "ERROR")
        return False

def load_history_from_json():
    """
    Load history from JSON file
    FIXED: Automatically trims to max_history_items on load
    """
    try:
        import streamlit as st
        
        history_file = Path("data/history/research_history.json")
        
        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                loaded_history = json.load(f)
            
            # FIXED: Respect max_history_items when loading
            max_items = st.session_state.get('max_history_items', 5)
            if len(loaded_history) > max_items:
                # Keep only the most recent items
                loaded_history = loaded_history[-max_items:]
                console_log(f"History trimmed to {max_items} items on load")
            
            st.session_state.research_history = loaded_history
            console_log(f"✅ History loaded: {len(st.session_state.research_history)} items")
            return True
    except Exception as e:
        console_log(f"Error loading history: {e}", "ERROR")
    
    return False

def get_history_count():
    """Get current history count"""
    try:
        import streamlit as st
        return len(st.session_state.get('research_history', []))
    except:
        return 0

def clear_old_history():
    """
    Clear old history items if exceeding limit
    FIXED: Can be called manually to enforce limits
    """
    try:
        import streamlit as st
        
        max_items = st.session_state.get('max_history_items', 5)
        current_count = len(st.session_state.research_history)
        
        if current_count > max_items:
            removed_count = current_count - max_items
            st.session_state.research_history = st.session_state.research_history[-max_items:]
            console_log(f"Removed {removed_count} old history items (limit: {max_items})")
            save_history_to_json()
            return True
        
        return False
    except Exception as e:
        console_log(f"Error clearing old history: {e}", "ERROR")
        return False

# ============================================================================
# CHART GENERATION
# ============================================================================

def create_chart_image(chart_type='bar', title='', labels=None, values=None, colors_list=None):
    """Create matplotlib chart and return as image"""
    if not PDF_AVAILABLE or labels is None or values is None:
        return None
    
    try:
        fig, ax = plt.subplots(figsize=(8, 4))
        
        if colors_list is None:
            colors_list = ['#0ea5e9', '#f97316', '#10b981', '#8b5cf6', '#f59e0b']
        
        if chart_type == 'bar':
            bars = ax.bar(labels, values, color=colors_list[:len(labels)])
            ax.set_ylabel('Count', fontsize=10)
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}', ha='center', va='bottom', fontsize=9)
                       
        elif chart_type == 'pie':
            pie_result = ax.pie(values, labels=labels, autopct='%1.1f%%', 
                               colors=colors_list[:len(labels)], startangle=90)
            if len(pie_result) == 3:
                _, texts, autotexts = pie_result
            else:
                _, texts = pie_result
                autotexts = []
                
            for text in texts:
                text.set_fontsize(9)
            for autotext in autotexts:
                autotext.set_fontsize(8)
                autotext.set_color('white')
                autotext.set_fontweight('bold')
        
        ax.set_title(title, fontsize=12, fontweight='bold')
        plt.tight_layout()
        
        # Save to bytes
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf
    except Exception as e:
        console_log(f"Error creating chart: {e}", "ERROR")
        return None

# ============================================================================
# PDF GENERATION
# ============================================================================

def generate_comprehensive_pdf(results):
    """Generate comprehensive PDF report from research results"""
    if not PDF_AVAILABLE:
        console_log("PDF generation not available - missing dependencies", "WARNING")
        return None
    
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#0ea5e9'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            leading=14,
            alignment=TA_JUSTIFY
        )
        
        # Title
        story.append(Paragraph("🔬 Luminar Deep Research Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Query
        story.append(Paragraph(f"<b>Research Query:</b> {results.get('query', 'N/A')}", body_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Metadata Table
        story.append(Paragraph("Research Metadata", heading_style))
        
        metadata = [
            ["Parameter", "Value"],
            ["Query", results.get('query', 'N/A')],
            ["Domain", results.get('domain', 'N/A')],
            ["Model Type", results.get('model_type', 'N/A')],
            ["Timestamp", results.get('timestamp', 'N/A')],
            ["Confidence", f"{results.get('confidence_score', 'N/A')}/100"]
        ]
        
        metadata_table = Table(metadata, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0ea5e9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9ff')])
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Agent Performance
        agent_data = results.get('agent_data', [])
        if agent_data:
            story.append(Paragraph("Agent Performance", heading_style))
            
            metrics_data = [["Agent", "Sources", "Findings", "Cost", "Time", "Status"]]
            for agent in agent_data:
                metrics_data.append([
                    agent.get('agent_name', 'N/A')[:20],
                    str(agent.get('source_count', 0)),
                    str(agent.get('findings_count', 0)),
                    f"${agent.get('cost', 0):.4f}",
                    f"{agent.get('execution_time', 0):.2f}s",
                    agent.get('status', 'Unknown')[:15]
                ])
            
            metrics_table = Table(metrics_data, colWidths=[1.5*inch, 0.7*inch, 0.7*inch, 0.8*inch, 0.7*inch, 1.2*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0ea5e9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9ff')])
            ]))
            
            story.append(metrics_table)
            story.append(Spacer(1, 0.2*inch))
        
        # Summary
        summary = results.get('summary', 'No summary available.')
        story.append(Paragraph("Executive Summary", heading_style))
        story.append(Paragraph(summary, body_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Key Findings
        findings = results.get('key_findings', [])
        if findings:
            story.append(Paragraph("Key Findings", heading_style))
            for idx, finding in enumerate(findings, 1):
                story.append(Paragraph(f"{idx}. {finding}", body_style))
                story.append(Spacer(1, 0.05*inch))
            story.append(Spacer(1, 0.1*inch))
        
        # Insights
        insights = results.get('insights', [])
        if insights:
            story.append(Paragraph("Strategic Insights", heading_style))
            for idx, insight in enumerate(insights, 1):
                story.append(Paragraph(f"• {insight}", body_style))
                story.append(Spacer(1, 0.05*inch))
            story.append(Spacer(1, 0.1*inch))
        
        # Sources
        sources = results.get('sources', [])
        if sources:
            story.append(PageBreak())
            story.append(Paragraph("Research Sources", heading_style))
            
            for idx, source in enumerate(sources[:20], 1):
                story.append(Paragraph(f"<b>[{idx}] {source.get('title', 'Unknown')}</b>", body_style))
                story.append(Paragraph(f"URL: {source.get('url', 'N/A')}", body_style))
                story.append(Paragraph(f"Summary: {source.get('summary', 'No summary')[:200]}...", body_style))
                story.append(Spacer(1, 0.1*inch))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        console_log(f"Error generating PDF: {e}", "ERROR")
        return None

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def export_to_markdown(results):
    """Export results to Markdown format"""
    try:
        md = f"""# Research Results

## Query
{results.get('query', 'N/A')}

## Domain
{results.get('domain', 'N/A')}

## Timestamp
{results.get('timestamp', 'N/A')}

## Confidence Score
{results.get('confidence_score', 'N/A')}/100

## Executive Summary
{results.get('summary', 'No summary available')}

## Key Findings
"""
        
        findings = results.get('key_findings', [])
        for idx, finding in enumerate(findings, 1):
            md += f"{idx}. {finding}\n"
        
        md += "\n## Strategic Insights\n"
        insights = results.get('insights', [])
        for insight in insights:
            md += f"- {insight}\n"
        
        md += "\n## Agent Performance\n"
        agent_data = results.get('agent_data', [])
        for agent in agent_data:
            md += f"\n### {agent.get('agent_name', 'Unknown')}\n"
            md += f"- Sources: {agent.get('source_count', 0)}\n"
            md += f"- Findings: {agent.get('findings_count', 0)}\n"
            md += f"- Cost: ${agent.get('cost', 0):.4f}\n"
            md += f"- Status: {agent.get('status', 'Unknown')}\n"
        
        md += "\n## Sources\n"
        sources = results.get('sources', [])
        for idx, source in enumerate(sources, 1):
            md += f"\n**[{idx}] {source.get('title', 'Unknown')}**\n"
            md += f"- URL: {source.get('url', 'N/A')}\n"
            md += f"- Summary: {source.get('summary', 'No summary')}\n"
        
        return md
        
    except Exception as e:
        console_log(f"Error exporting to Markdown: {e}", "ERROR")
        return None

def export_to_json(results):
    """Export results to JSON format"""
    try:
        return json.dumps(results, indent=2, ensure_ascii=False)
    except Exception as e:
        console_log(f"Error exporting to JSON: {e}", "ERROR")
        return None