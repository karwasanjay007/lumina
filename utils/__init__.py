"""
Utility Functions Module - Package Initialization
PDF generation, history management, helper functions
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
# HISTORY MANAGEMENT
# ============================================================================

def save_history_to_json():
    """Save history to JSON file"""
    try:
        import streamlit as st
        
        history_file = Path("data/history/research_history.json")
        history_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.research_history, f, indent=2, ensure_ascii=False)
        
        console_log(f"✅ History saved: {len(st.session_state.research_history)} items")
        return True
    except Exception as e:
        console_log(f"Error saving history: {e}", "ERROR")
        return False

def load_history_from_json():
    """Load history from JSON file"""
    try:
        import streamlit as st
        
        history_file = Path("data/history/research_history.json")
        
        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                st.session_state.research_history = json.load(f)
            console_log(f"✅ History loaded: {len(st.session_state.research_history)} items")
            return True
    except Exception as e:
        console_log(f"Error loading history: {e}", "ERROR")
    
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
                wedges, texts, autotexts = pie_result
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontsize(9)
                    autotext.set_fontweight('bold')
            else:
                wedges, texts = pie_result
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        
        # Save to bytes
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    except Exception as e:
        console_log(f"Error creating chart: {e}", "ERROR")
        plt.close()
        return None

# ============================================================================
# PDF GENERATION
# ============================================================================

def generate_comprehensive_pdf(results):
    """Generate comprehensive PDF with stats and charts"""
    if not PDF_AVAILABLE:
        return None
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#0ea5e9'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0284c7'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        leading=14
    )
    
    # Title Page
    story.append(Paragraph("Luminar Deep Researcher", title_style))
    story.append(Paragraph("Comprehensive Research Report v2.1", styles['Heading3']))
    story.append(Spacer(1, 0.3*inch))
    
    # Metadata
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
        
        # Source chart
        successful_agents = [a for a in agent_data if '✅' in a.get('status', '')]
        if successful_agents:
            agent_names = [a.get('agent_name', 'Unknown')[:15] for a in successful_agents]
            source_counts = [a.get('source_count', 0) for a in successful_agents]
            
            chart_img = create_chart_image(
                chart_type='bar',
                title='Source Distribution by Agent',
                labels=agent_names,
                values=source_counts
            )
            
            if chart_img:
                img = Image(chart_img, width=6*inch, height=3*inch)
                story.append(img)
    
    story.append(PageBreak())
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    summary_text = results.get('summary', 'No summary available')
    for para in summary_text.split('\n\n'):
        if para.strip():
            story.append(Paragraph(para.strip(), body_style))
    
    story.append(PageBreak())
    
    # Key Findings
    story.append(Paragraph("Key Findings", heading_style))
    findings = results.get('key_findings', [])
    
    if findings:
        findings_data = [["#", "Finding"]]
        for idx, finding in enumerate(findings, 1):
            findings_data.append([str(idx), finding.strip()])
        
        findings_table = Table(findings_data, colWidths=[0.5*inch, 5.5*inch])
        findings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f97316')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fffbfa')])
        ]))
        
        story.append(findings_table)
    
    # Build PDF
    try:
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        console_log(f"Error building PDF: {e}", "ERROR")
        return None

# Export all functions
__all__ = [
    'console_log',
    'calculate_confidence_score',
    'save_history_to_json',
    'load_history_from_json',
    'create_chart_image',
    'generate_comprehensive_pdf',
    'PDF_AVAILABLE'
]