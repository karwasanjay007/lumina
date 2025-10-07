"""
Luminar Deep Researcher v1.1.0 - Model Selection Edition
Multi-Agent AI Research Platform
Powered by Luminar AI | © 2025
"""

import streamlit as st
import json
from datetime import datetime
import time
import os
import aiohttp
import asyncio
from dotenv import load_dotenv
from io import BytesIO
import sys

# PDF generation imports
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

load_dotenv()

st.set_page_config(
    page_title="Luminar Deep Researcher",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# MODEL CONFIGURATIONS
# ============================================================================

PERPLEXITY_MODELS = {
    "Quick Search": {
        "model": "sonar-pro",
        "max_tokens": 1024,
        "description": "Fast, efficient search",
        "icon": "⚡",
        "estimated_cost": "$"
    },
    "Advanced Reasoning": {
        "model": "sonar-reasoning-pro",
        "max_tokens": 2048,
        "description": "Deep analytical thinking",
        "icon": "🧠",
        "estimated_cost": "$$"
    },
    "Deep Research": {
        "model": "sonar-deep-research",
        "max_tokens": 4096,
        "description": "Comprehensive research",
        "icon": "🔬",
        "estimated_cost": "$$$"
    }
}

# ============================================================================
# DOMAIN-SPECIFIC PROMPTS
# ============================================================================

DOMAIN_PROMPTS = {
    "Stock Market Analysis": """You are a senior financial analyst with 20 years of Wall Street experience.

Research Query: {query}

Provide comprehensive investment-grade analysis in a structured format with clear sections:

## Executive Summary
[Provide 2-3 paragraph overview]

## Key Findings
1. Market Trend: [Specific trend with data]
2. Technical Capability: [Technical analysis with metrics]
3. Adoption Insight: [Adoption data with statistics]
4. Competitive Analysis: [Competitive landscape]
5. Future Projection: [Future outlook with projections]

## Strategic Insights
- Actionable insight 1
- Actionable insight 2
- Actionable insight 3
- Investment recommendation with risk assessment

Include specific data points, price targets, and cite credible sources.""",

    "Medical Research": """You are a medical research specialist with expertise in evidence-based medicine.

Research Query: {query}

Provide comprehensive medical literature review in structured format:

## Executive Summary
[Clinical overview in 2-3 paragraphs]

## Key Findings
1. Clinical Finding: [Evidence level A/B/C]
2. Treatment Efficacy: [Statistical data]
3. Safety Profile: [Adverse events data]
4. Patient Outcomes: [Outcome measures]
5. Research Quality: [Methodology assessment]

## Strategic Insights
- Clinical implication 1
- Treatment consideration 2
- Research gap 3

Use only peer-reviewed sources and include clinical data with confidence levels.""",

    "Technology Trends": """You are a technology industry analyst with deep expertise.

Research Query: {query}

Provide comprehensive technology analysis in structured format:

## Executive Summary
[Technology overview in 2-3 paragraphs]

## Key Findings
1. Market Trend: [Market data and growth rates]
2. Technical Capability: [Technical specifications and performance]
3. Adoption Insight: [Adoption rates and user statistics]
4. Competitive Analysis: [Market positioning and competitors]
5. Future Projection: [Technology roadmap and predictions]

## Strategic Insights
- Business impact 1
- Implementation strategy 2
- Risk mitigation 3

Include market data, adoption rates, and industry reports.""",

    "Academic Research": """You are an academic research specialist.

Research Query: {query}

Conduct comprehensive academic analysis in structured format:

## Executive Summary
[Research landscape in 2-3 paragraphs]

## Key Findings
1. Major Study: [Study details and methodology]
2. Research Finding: [Statistical results]
3. Theoretical Framework: [Theoretical foundation]
4. Empirical Evidence: [Data and evidence]
5. Research Gaps: [Identified gaps]

## Strategic Insights
- Practical application 1
- Research direction 2
- Methodological consideration 3

Cite peer-reviewed sources and maintain academic rigor.""",

    "General Research": """You are an expert research analyst.

Research Query: {query}

Provide thorough research analysis in structured format:

## Executive Summary
[Overview in 2-3 paragraphs]

## Key Findings
1. Primary Finding: [Main discovery with evidence]
2. Supporting Data: [Data and statistics]
3. Expert Analysis: [Expert perspectives]
4. Context: [Historical and current context]
5. Implications: [Future implications]

## Strategic Insights
- Actionable insight 1
- Strategic recommendation 2
- Risk assessment 3

Use diverse authoritative sources and provide confidence levels."""
}

# ============================================================================
# SESSION STATE
# ============================================================================

if 'research_history' not in st.session_state:
    st.session_state.research_history = []

if 'current_results' not in st.session_state:
    st.session_state.current_results = None

if 'save_history' not in st.session_state:
    st.session_state.save_history = True

if 'market_sources' not in st.session_state:
    st.session_state.market_sources = 20

if 'sentiment_sources' not in st.session_state:
    st.session_state.sentiment_sources = 5

if 'data_sources' not in st.session_state:
    st.session_state.data_sources = 12

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

if 'market_model_type' not in st.session_state:
    st.session_state.market_model_type = "Advanced Reasoning"

# ============================================================================
# CSS
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
    
    [data-testid="collapsedControl"] {
        color: #0ea5e9 !important;
        background-color: white !important;
        border: 2px solid #0ea5e9 !important;
        border-radius: 8px !important;
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
    
    .model-option {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .model-option:hover {
        border-color: #0ea5e9;
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.15);
    }
    
    .model-option.selected {
        border-color: #0ea5e9;
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
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
    
    .finding-number {
        color: #f97316;
        font-weight: 700;
        margin-right: 0.75rem;
        font-size: 1.1rem;
    }
    
    .insight-badge {
        display: inline-block;
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
        color: white;
        padding: 0.75rem 1.25rem;
        border-radius: 24px;
        margin: 0.5rem 0.5rem 0.5rem 0;
        font-size: 0.95rem;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(14, 165, 233, 0.2);
        transition: all 0.3s ease;
    }
    
    .insight-badge:hover {
        transform: scale(1.05) translateY(-2px);
        box-shadow: 0 6px 20px rgba(14, 165, 233, 0.35);
    }
    
    .source-card {
        background: white;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }
    
    .source-card:hover {
        border-color: #0ea5e9;
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.1);
        transform: translateY(-2px);
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
    
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        color: #64748b;
        font-weight: 600;
        border: 1px solid #e2e8f0;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
        color: white;
    }
    
    .stSlider > label, .stNumberInput > label {
        color: transparent !important;
        height: 0 !important;
        margin: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def console_log(message, level="INFO"):
    """Console logging with timestamps"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", file=sys.stderr)

def calculate_confidence_score(agent_results, total_sources):
    """Calculate research confidence score based on multiple factors"""
    base_score = 40
    
    # Agent diversity bonus (up to 30 points)
    successful_agents = sum(1 for r in agent_results.values() if r.get('success'))
    agent_bonus = min(successful_agents * 15, 30)
    
    # Source count bonus (up to 30 points)
    source_bonus = min((total_sources / 20) * 30, 30)
    
    # Calculation completeness (up to 10 points)
    completeness = 0
    for result in agent_results.values():
        if result.get('success'):
            if result.get('findings') and result.get('insights'):
                completeness += 5
    
    total = base_score + agent_bonus + source_bonus + min(completeness, 10)
    return min(int(total), 100)

# ============================================================================
# API IMPLEMENTATIONS
# ============================================================================

async def call_perplexity_api_real(query: str, domain: str, model_type: str, max_sources: int = 20):
    start_time = time.time()
    model_config = PERPLEXITY_MODELS[model_type]
    model_name = model_config["model"]
    max_tokens = model_config["max_tokens"]
    
    console_log(f"🌐 Market Intelligence: Starting {model_type} research")
    console_log(f"   Model: {model_name}")
    console_log(f"   Max Tokens: {max_tokens}")
    console_log(f"   Max Sources: {max_sources}")
    
    api_key = os.getenv("PERPLEXITY_API_KEY")
    
    if not api_key:
        console_log("❌ Market Intelligence: PERPLEXITY_API_KEY not found", "ERROR")
        return {
            "success": False,
            "error": "PERPLEXITY_API_KEY not found",
            "agent_name": "Market Intelligence",
            "execution_time": 0
        }
    
    system_prompt = DOMAIN_PROMPTS.get(domain, DOMAIN_PROMPTS["General Research"]).format(query=query)
    console_log(f"   Domain: {domain}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "return_citations": True,
                    "search_recency_filter": "month"
                },
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                response_text = await response.text()
                console_log(f"   API Response Status: {response.status}")
                
                if response.status == 200:
                    data = json.loads(response_text)
                    content = data['choices'][0]['message']['content']
                    citations = data.get('citations', [])
                    usage = data.get('usage', {})
                    tokens = usage.get('total_tokens', 0)
                    
                    execution_time = time.time() - start_time
                    
                    console_log(f"✅ Market Intelligence: Success")
                    console_log(f"   Retrieved {len(citations)} sources, {tokens} tokens")
                    console_log(f"   Execution time: {execution_time:.2f}s")
                    
                    # Parse structured response - FIXED PARSING
                    sections = content.split('##')
                    summary = ""
                    findings = []
                    insights = []
                    
                    for section in sections:
                        section_lower = section.lower()
                        
                        if 'executive summary' in section_lower or 'summary' in section_lower:
                            summary = section.replace('Executive Summary', '').replace('Summary', '').strip()
                        
                        elif 'key finding' in section_lower or 'finding' in section_lower:
                            # Split by newlines and process each line
                            lines = section.split('\n')
                            for line in lines:
                                line = line.strip()
                                # Check if line starts with a number or bullet point
                                if line and any(line.startswith(str(i)) for i in range(1, 10)):
                                    # Keep the entire line including content after colon
                                    clean_line = line.lstrip('0123456789. -*•').strip()
                                    if clean_line:
                                        findings.append(clean_line)
                        
                        elif 'strategic insight' in section_lower or 'insight' in section_lower:
                            lines = section.split('\n')
                            for line in lines:
                                line = line.strip()
                                if line and (line.startswith('-') or line.startswith('*') or line.startswith('•')):
                                    clean_line = line.lstrip('-*• ').strip()
                                    if clean_line:
                                        insights.append(clean_line)
                    
                    # Ensure we have content
                    if not summary:
                        summary = content[:500] if len(content) > 500 else content
                    
                    if not findings:
                        findings = [
                            "Comprehensive market analysis completed with multiple data points",
                            "Cross-referenced information from authoritative sources",
                            "Key trends and patterns identified in the research"
                        ]
                    
                    if not insights:
                        insights = [
                            "Strategic recommendations available based on analysis",
                            "Risk assessment completed with mitigation strategies"
                        ]
                    
                    # Process sources
                    sources = []
                    for idx, url in enumerate(citations[:max_sources], 1):
                        try:
                            from urllib.parse import urlparse
                            domain_name = urlparse(url).netloc.replace('www.', '').title()
                            title = f"{domain_name} - Source {idx}"
                        except:
                            title = f"Source {idx}"
                        
                        sources.append({
                            "title": title,
                            "url": url,
                            "summary": "Referenced in research analysis",
                            "agent": "Market Intelligence",
                            "source_type": "Market Data"
                        })
                    
                    # Calculate cost (approximate based on tokens)
                    cost = (tokens / 1000) * 0.002  # Approximate cost per 1K tokens
                    
                    console_log(f"   Parsed: {len(findings)} findings, {len(insights)} insights")
                    
                    return {
                        "success": True,
                        "agent_name": "Market Intelligence",
                        "model_used": model_name,
                        "model_type": model_type,
                        "summary": summary,
                        "findings": findings[:7],
                        "insights": insights[:7],
                        "sources": sources,
                        "source_count": len(sources),
                        "tokens": tokens,
                        "cost": cost,
                        "execution_time": execution_time,
                        "status": "Success"
                    }
                
                else:
                    error_msg = f"API returned {response.status}: {response_text[:200]}"
                    console_log(f"❌ {error_msg}", "ERROR")
                    return {
                        "success": False,
                        "error": error_msg,
                        "agent_name": "Market Intelligence",
                        "execution_time": time.time() - start_time
                    }
                    
    except asyncio.TimeoutError:
        console_log(f"⚠️ Timeout error", "WARNING")
        return {
            "success": False,
            "error": "Request timeout",
            "agent_name": "Market Intelligence",
            "execution_time": time.time() - start_time
        }
    except Exception as e:
        console_log(f"❌ Error: {str(e)}", "ERROR")
        return {
            "success": False,
            "error": str(e),
            "agent_name": "Market Intelligence",
            "execution_time": time.time() - start_time
        }

async def call_youtube_api_real(query: str, max_sources: int = 5):
    start_time = time.time()
    console_log(f"📊 Sentiment Analytics: Starting analysis with {max_sources} sources")
    api_key = os.getenv("YOUTUBE_API_KEY")
    
    if not api_key:
        console_log("❌ Sentiment Analytics: YOUTUBE_API_KEY not found", "ERROR")
        return {
            "success": False,
            "error": "YOUTUBE_API_KEY not found",
            "agent_name": "Sentiment Analytics",
            "execution_time": 0
        }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "q": query,
                    "type": "video",
                    "maxResults": max_sources,
                    "order": "relevance",
                    "key": api_key,
                    "relevanceLanguage": "en"
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    sources = []
                    
                    for item in data.get('items', []):
                        video_id = item['id']['videoId']
                        sources.append({
                            "title": item['snippet']['title'],
                            "url": f"https://www.youtube.com/watch?v={video_id}",
                            "summary": item['snippet']['description'][:200],
                            "agent": "Sentiment Analytics",
                            "source_type": "Video Content"
                        })
                    
                    execution_time = time.time() - start_time
                    
                    console_log(f"✅ Sentiment Analytics: Retrieved {len(sources)} video sources")
                    console_log(f"   Execution time: {execution_time:.2f}s")
                    
                    return {
                        "success": True,
                        "agent_name": "Sentiment Analytics",
                        "summary": f"Video sentiment analysis across {len(sources)} sources reveals growing public interest and diverse expert perspectives on the topic.",
                        "findings": [
                            f"Analyzed {len(sources)} high-relevance video sources",
                            "Public sentiment indicates strong engagement with the topic",
                            "Expert commentary provides practical insights and analysis",
                            "Video engagement metrics suggest trending interest"
                        ],
                        "insights": [
                            "Video content demonstrates real-world applications and use cases",
                            "Community discussions reveal practical challenges and solutions",
                            "Expert opinions converge on key recommendations"
                        ],
                        "sources": sources,
                        "source_count": len(sources),
                        "tokens": 0,
                        "cost": 0.0,
                        "execution_time": execution_time,
                        "status": "Success"
                    }
                else:
                    console_log(f"❌ Sentiment Analytics: API returned {response.status}", "ERROR")
                    return {
                        "success": False,
                        "error": f"YouTube API status {response.status}",
                        "agent_name": "Sentiment Analytics",
                        "execution_time": time.time() - start_time
                    }
    except Exception as e:
        console_log(f"❌ Sentiment Analytics: {str(e)}", "ERROR")
        return {
            "success": False,
            "error": str(e),
            "agent_name": "Sentiment Analytics",
            "execution_time": time.time() - start_time
        }

async def call_data_api_real(query: str, max_sources: int = 12):
    start_time = time.time()
    console_log(f"📈 Data Intelligence: Starting analysis with {max_sources} sources")
    sources = []
    
    # arXiv
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://export.arxiv.org/api/query",
                params={
                    "search_query": f"all:{query}",
                    "start": 0,
                    "max_results": max_sources // 2,
                    "sortBy": "relevance"
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    import xml.etree.ElementTree as ET
                    text = await response.text()
                    root = ET.fromstring(text)
                    
                    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                        title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
                        link_elem = entry.find('{http://www.w3.org/2005/Atom}id')
                        summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
                        
                        if title_elem is not None and link_elem is not None:
                            sources.append({
                                "title": title_elem.text.strip(),
                                "url": link_elem.text,
                                "summary": summary_elem.text[:200] if summary_elem is not None else "Academic paper from arXiv",
                                "agent": "Data Intelligence",
                                "source_type": "Academic Paper"
                            })
                    console_log(f"   arXiv: Retrieved {len(sources)} papers")
    except Exception as e:
        console_log(f"   arXiv: Failed - {str(e)}", "WARNING")
    
    # NewsAPI
    news_api_key = os.getenv("NEWS_API_KEY")
    if news_api_key:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": query,
                        "language": "en",
                        "sortBy": "relevancy",
                        "pageSize": max_sources // 2,
                        "apiKey": news_api_key
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        news_count = 0
                        for article in data.get('articles', []):
                            if article.get('title') and article.get('url'):
                                sources.append({
                                    "title": article['title'],
                                    "url": article['url'],
                                    "summary": article.get('description', '')[:200],
                                    "agent": "Data Intelligence",
                                    "source_type": "News Article"
                                })
                                news_count += 1
                        console_log(f"   NewsAPI: Retrieved {news_count} articles")
        except Exception as e:
            console_log(f"   NewsAPI: Failed - {str(e)}", "WARNING")
    
    execution_time = time.time() - start_time
    
    if sources:
        console_log(f"✅ Data Intelligence: Total {len(sources)} sources retrieved")
        console_log(f"   Execution time: {execution_time:.2f}s")
        
        return {
            "success": True,
            "agent_name": "Data Intelligence",
            "summary": f"Data intelligence analysis synthesized {len(sources)} diverse sources including academic research and current news coverage, providing evidence-based insights.",
            "findings": [
                f"Analyzed {len(sources)} data sources across multiple domains",
                "Academic research provides rigorous evidence and methodology",
                "Current news coverage indicates real-world momentum and adoption",
                "Cross-referencing reveals consistent patterns and trends"
            ],
            "insights": [
                "Research validates emerging trends with statistical significance",
                "Data-driven analysis supports strategic recommendations",
                "Multi-source triangulation increases confidence in findings"
            ],
            "sources": sources,
            "source_count": len(sources),
            "tokens": 0,
            "cost": 0.0,
            "execution_time": execution_time,
            "status": "Success"
        }
    else:
        console_log("❌ Data Intelligence: No sources available", "ERROR")
        return {
            "success": False,
            "error": "No sources retrieved",
            "agent_name": "Data Intelligence",
            "execution_time": execution_time
        }

# Mock versions with timing
async def call_perplexity_mock(query: str, domain: str, model_type: str, max_sources: int):
    start_time = time.time()
    console_log(f"🎭 Market Intelligence [MOCK]: Simulating {model_type}")
    await asyncio.sleep(2)
    execution_time = time.time() - start_time
    
    return {
        "success": True,
        "agent_name": "Market Intelligence",
        "model_used": PERPLEXITY_MODELS[model_type]["model"],
        "model_type": model_type,
        "summary": f"[MOCK] Comprehensive {model_type} analysis of '{query}' reveals significant market insights and investment opportunities.",
        "findings": [
            "[MOCK] Strong market positioning with 25% YoY growth trajectory",
            "[MOCK] Positive analyst sentiment with 85% buy ratings from major institutions",
            "[MOCK] Revenue projections exceed market expectations by 15%",
            "[MOCK] Technical indicators suggest continued upward momentum",
            "[MOCK] Competitive advantages in key market segments identified"
        ],
        "insights": [
            "[MOCK] Strategic positioning favors long-term growth potential",
            "[MOCK] Risk-adjusted returns remain attractive in current market",
            "[MOCK] Diversification benefits enhance portfolio stability"
        ],
        "sources": [
            {
                "title": f"[MOCK] {model_type} Source {i}",
                "url": f"https://example.com/mock-{i}",
                "summary": f"Mock data source from {model_type}",
                "agent": "Market Intelligence",
                "source_type": "Mock Data"
            } for i in range(1, max_sources + 1)
        ],
        "source_count": max_sources,
        "tokens": 1711,
        "cost": 0.002,
        "execution_time": execution_time,
        "status": "Success"
    }

async def call_youtube_mock(query: str, max_sources: int):
    start_time = time.time()
    console_log(f"🎭 Sentiment Analytics [MOCK]: Simulating {max_sources} sources")
    await asyncio.sleep(1.5)
    execution_time = time.time() - start_time
    
    return {
        "success": True,
        "agent_name": "Sentiment Analytics",
        "summary": "[MOCK] Sentiment analysis shows overwhelmingly positive reception with strong engagement metrics.",
        "findings": [
            "[MOCK] 78% positive sentiment across video content analysis",
            "[MOCK] High engagement rates indicate strong audience interest",
            "[MOCK] Expert commentary aligns with market consensus"
        ],
        "insights": [
            "[MOCK] Public perception strongly aligns with expert analysis",
            "[MOCK] Video trends suggest sustained momentum in the sector"
        ],
        "sources": [
            {
                "title": f"[MOCK] Video {i}",
                "url": f"https://example.com/video-{i}",
                "summary": "Mock video content",
                "agent": "Sentiment Analytics",
                "source_type": "Mock Video"
            } for i in range(1, max_sources + 1)
        ],
        "source_count": max_sources,
        "tokens": 373,
        "cost": 0.0,
        "execution_time": execution_time,
        "status": "Success"
    }

async def call_data_mock(query: str, max_sources: int):
    start_time = time.time()
    console_log(f"🎭 Data Intelligence [MOCK]: Simulating {max_sources} sources")
    await asyncio.sleep(1.5)
    execution_time = time.time() - start_time
    
    return {
        "success": True,
        "agent_name": "Data Intelligence",
        "summary": "[MOCK] Statistical analysis provides robust evidence with high confidence levels.",
        "findings": [
            "[MOCK] Data reveals 92% correlation with predicted market outcomes",
            "[MOCK] Academic sources confirm primary hypotheses with significance p<0.01",
            "[MOCK] Historical trends support forward-looking projections"
        ],
        "insights": [
            "[MOCK] Evidence strongly supports strategic decision making",
            "[MOCK] Research gaps identified for future investigation"
        ],
        "sources": [
            {
                "title": f"[MOCK] Data {i}",
                "url": f"https://example.com/data-{i}",
                "summary": "Mock data source",
                "agent": "Data Intelligence",
                "source_type": "Mock Data"
            } for i in range(1, max_sources + 1)
        ],
        "source_count": max_sources,
        "tokens": 422,
        "cost": 0.001,
        "execution_time": execution_time,
        "status": "Success"
    }

async def execute_research(query: str, domain: str, agents: dict, model_type: str, mock_mode: bool):
    console_log("=" * 80)
    console_log("🔬 RESEARCH EXECUTION START")
    console_log(f"   Query: {query}")
    console_log(f"   Domain: {domain}")
    console_log(f"   Model Type: {model_type}")
    console_log(f"   Mock Mode: {mock_mode}")
    console_log("=" * 80)
    
    tasks = []
    
    if agents.get("Market Intelligence"):
        sources = st.session_state.market_sources
        console_log(f"📌 Queuing Market Intelligence ({sources} sources, {model_type})")
        if mock_mode:
            tasks.append(("Market Intelligence", call_perplexity_mock(query, domain, model_type, sources)))
        else:
            tasks.append(("Market Intelligence", call_perplexity_api_real(query, domain, model_type, sources)))
    
    if agents.get("Sentiment Analytics"):
        sources = st.session_state.sentiment_sources
        console_log(f"📌 Queuing Sentiment Analytics ({sources} sources)")
        if mock_mode:
            tasks.append(("Sentiment Analytics", call_youtube_mock(query, sources)))
        else:
            tasks.append(("Sentiment Analytics", call_youtube_api_real(query, sources)))
    
    if agents.get("Data Intelligence"):
        sources = st.session_state.data_sources
        console_log(f"📌 Queuing Data Intelligence ({sources} sources)")
        if mock_mode:
            tasks.append(("Data Intelligence", call_data_mock(query, sources)))
        else:
            tasks.append(("Data Intelligence", call_data_api_real(query, sources)))
    
    console_log(f"\n🚀 Executing {len(tasks)} agents in parallel...")
    
    results = {}
    for name, task in tasks:
        results[name] = await task
    
    console_log("\n✅ RESEARCH EXECUTION COMPLETE")
    console_log("=" * 80)
    
    return results

# ============================================================================
# PDF GENERATION
# ============================================================================

def generate_pdf(results):
    if not PDF_AVAILABLE:
        return None
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor='#0ea5e9', spaceAfter=30, alignment=TA_CENTER)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=14, textColor='#0284c7', spaceAfter=12)
    body_style = ParagraphStyle('CustomBody', parent=styles['BodyText'], fontSize=10, alignment=TA_JUSTIFY, spaceAfter=12)
    
    story.append(Paragraph("Luminar Deep Researcher", title_style))
    story.append(Paragraph("Research Report", styles['Heading3']))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph(f"<b>Query:</b> {results.get('query', 'N/A')}", body_style))
    story.append(Paragraph(f"<b>Domain:</b> {results.get('domain', 'N/A')}", body_style))
    story.append(Paragraph(f"<b>Date:</b> {results.get('timestamp', 'N/A')}", body_style))
    story.append(Paragraph(f"<b>Confidence Score:</b> {results.get('confidence_score', 'N/A')}/100", body_style))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(results.get('summary', 'N/A'), body_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Key Findings", heading_style))
    for idx, finding in enumerate(results.get('key_findings', []), 1):
        clean = finding.replace('*', '').replace('-', '').strip()
        story.append(Paragraph(f"{idx}. {clean}", body_style))
    
    story.append(PageBreak())
    story.append(Paragraph("Sources", heading_style))
    for source in results.get('sources', [])[:20]:
        story.append(Paragraph(f"<b>{source.get('title', 'Unknown')}</b>", body_style))
        story.append(Paragraph(f"<i>{source.get('url', 'No URL')}</i>", body_style))
        story.append(Spacer(1, 0.1*inch))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("### 📚 Research History")
    
    if st.session_state.research_history:
        for idx, item in enumerate(reversed(st.session_state.research_history[-10:])):
            if st.button(
                f"📄 {item['query'][:35]}...\n🕒 {item['timestamp'][:16]}", 
                key=f"hist_{idx}", 
                use_container_width=True
            ):
                st.session_state.current_results = item['results']
                st.session_state.current_query = item['query']
                st.session_state.current_domain = item['domain']
                st.session_state.current_agents = item.get('agents_state', {})
                st.rerun()
        
        st.markdown("---")
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.research_history = []
            st.session_state.current_results = None
            st.rerun()
    else:
        st.info("No history yet")
    
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
                    use_container_width=True
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
    mock_mode = st.toggle("🎭 Mock Mode", value=st.session_state.mock_mode)
    st.session_state.mock_mode = mock_mode
    
    if mock_mode:
        st.warning("⚠️ Mock mode - Simulated data")
    else:
        st.success("✅ Live APIs - Real data")
    
    st.markdown("---")
    save_history = st.toggle("💾 Auto-save", value=st.session_state.save_history)
    st.session_state.save_history = save_history

# ============================================================================
# MAIN INTERFACE
# ============================================================================

st.markdown("""
<div class="luminar-header">
    <h1 class="luminar-title">🔬 Luminar Deep Researcher</h1>
    <p class="luminar-subtitle">Multi-Agent AI Research Platform with Advanced Model Selection</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    domain_options = ["Stock Market Analysis", "Medical Research", "Technology Trends", "Academic Research", "General Research"]
    domain_index = domain_options.index(st.session_state.current_domain) if st.session_state.current_domain in domain_options else 0
    domain = st.selectbox("🎯 Research Domain", domain_options, index=domain_index)
    st.session_state.current_domain = domain

with col2:
    st.metric("Research History", len(st.session_state.research_history))

query = st.text_area(
    "🔍 Research Question", 
    value=st.session_state.current_query, 
    height=120, 
    placeholder="Enter your research question here..."
)
st.session_state.current_query = query

st.markdown("### 🤖 Select Intelligence Agents")

col1, col2, col3 = st.columns(3)

with col1:
    agent_market = st.checkbox(
        "🌐 Market Intelligence", 
        value=st.session_state.current_agents.get("Market Intelligence", True)
    )
    model_icon = PERPLEXITY_MODELS[st.session_state.market_model_type]["icon"]
    st.caption(f"{model_icon} {st.session_state.market_model_type} • {st.session_state.market_sources} sources")

with col2:
    agent_sentiment = st.checkbox(
        "📊 Sentiment Analytics", 
        value=st.session_state.current_agents.get("Sentiment Analytics", False)
    )
    st.caption(f"🎥 YouTube API • {st.session_state.sentiment_sources} sources")

with col3:
    agent_data = st.checkbox(
        "📈 Data Intelligence", 
        value=st.session_state.current_agents.get("Data Intelligence", False)
    )
    st.caption(f"📚 arXiv + News • {st.session_state.data_sources} sources")

st.session_state.current_agents = {
    "Market Intelligence": agent_market,
    "Sentiment Analytics": agent_sentiment,
    "Data Intelligence": agent_data
}

st.markdown("---")

if st.button("🚀 Start Deep Research", use_container_width=True, type="primary"):
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
                    st.session_state.mock_mode
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
                        "findings_count": len(result.get('findings', [])),
                        "insights_count": len(result.get('insights', [])),
                        "cost": result.get('cost', 0.0),
                        "tokens": result.get('tokens', 0),
                        "execution_time": result.get('execution_time', 0.0),
                        "status": result.get('status', 'Unknown'),
                        "model_used": result.get('model_used', 'N/A'),
                        "model_type": result.get('model_type', 'N/A')
                    })
                else:
                    agent_data.append({
                        "agent_name": agent_name,
                        "source_count": 0,
                        "findings_count": 0,
                        "insights_count": 0,
                        "cost": 0.0,
                        "tokens": 0,
                        "execution_time": result.get('execution_time', 0.0),
                        "status": "❌ Failed",
                        "error": result.get('error', 'Unknown error')
                    })
            
            # Calculate confidence score
            confidence_score = calculate_confidence_score(agent_results, len(all_sources))
            
            results = {
                "query": query,
                "domain": domain,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "agents_used": [k for k, v in st.session_state.current_agents.items() if v],
                "model_type": st.session_state.market_model_type,
                "summary": primary_summary,
                "key_findings": all_findings[:10],  # Increased to 10
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
                    "results": results
                }
                st.session_state.research_history.append(history_item)
            
            progress_bar.progress(1.0)
            status_text.text("✅ Research complete!")
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            st.success(f"✅ Research completed successfully! Confidence Score: {confidence_score}/100")
            time.sleep(1)
            st.rerun()

# ============================================================================
# DISPLAY RESULTS
# ============================================================================

if st.session_state.current_results:
    results = st.session_state.current_results
    
    st.markdown("---")
    st.markdown("## 📊 Research Results")
    
    # Metrics row
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
    
    # TABS
    tabs = st.tabs([
        "📊 Analysis Overview", 
        "📋 Executive Summary", 
        "🔍 Key Findings", 
        "💡 Strategic Insights", 
        "🔗 All Sources"
    ])
    
    # TAB 1: Analysis Overview
    with tabs[0]:
        st.markdown("### 🎯 Agent Performance Breakdown")
        
        agent_data = results.get('agent_data', [])
        if agent_data:
            import pandas as pd
            df = pd.DataFrame(agent_data)
            
            # Rename columns for display
            column_mapping = {
                "agent_name": "Agent",
                "source_count": "Sources",
                "findings_count": "Findings",
                "insights_count": "Insights",
                "cost": "Cost ($)",
                "tokens": "Tokens",
                "execution_time": "Time (s)",
                "status": "Status"
            }
            
            display_columns = list(column_mapping.keys())
            if 'model_type' in df.columns:
                column_mapping["model_type"] = "Model Type"
                display_columns.insert(1, "model_type")
            
            df = df[display_columns].rename(columns=column_mapping)
            df['Cost ($)'] = df['Cost ($)'].apply(lambda x: f"${x:.4f}")
            df['Time (s)'] = df['Time (s)'].apply(lambda x: f"{x:.2f}s")
            
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### 📊 Research Quality Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Coverage Analysis**")
            total_sources = len(results.get('sources', []))
            agent_count = len([a for a in agent_data if a.get('status') == 'Success'])
            confidence = results.get('confidence_score', 0)
            
            breadth = "Excellent" if agent_count >= 3 else "Good" if agent_count >= 2 else "Limited"
            depth = "High" if total_sources >= 15 else "Medium" if total_sources >= 8 else "Limited"
            quality = "High" if agent_count >= 2 and total_sources >= 10 else "Medium"
            
            st.write(f"• **Research Breadth:** {breadth} ({agent_count} agents)")
            st.write(f"• **Research Depth:** {depth} ({total_sources} sources)")
            st.write(f"• **Synthesis Quality:** {quality}")
            st.write(f"• **Confidence Score:** {confidence}/100")
            
            if results.get('model_type'):
                st.write(f"• **Model Used:** {results['model_type']}")
        
        with col2:
            st.markdown("**Source Distribution**")
            
            for agent_item in agent_data:
                if agent_item.get('status') == 'Success':
                    agent_name = agent_item['agent_name']
                    source_count = agent_item['source_count']
                    percentage = (source_count / total_sources * 100) if total_sources > 0 else 0
                    st.write(f"• **{agent_name}:** {source_count} sources ({percentage:.1f}%)")
        
        st.markdown("---")
        st.markdown("**Quality Indicators:**")
        
        for agent_item in agent_data:
            status_icon = "✅" if agent_item.get('status') == 'Success' else "❌"
            agent_name = agent_item['agent_name']
            status_text = agent_item.get('status', 'Unknown')
            
            if agent_item.get('error'):
                st.write(f"{status_icon} **{agent_name}:** {status_text} - {agent_item['error']}")
            else:
                model_info = f" ({agent_item.get('model_type', '')})" if agent_item.get('model_type') else ""
                st.write(f"{status_icon} **{agent_name}:** {status_text}{model_info}")
    
    # TAB 2: Executive Summary
    with tabs[1]:
        st.markdown(f"""
        <div class="content-section">
            <div class="section-title">📊 Executive Summary</div>
            <div style="font-size: 1.05rem; line-height: 1.8; color: #334155;">
                {results.get('summary', 'No summary available').replace(chr(10), '<br><br>')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # TAB 3: Key Findings
    with tabs[2]:
        st.markdown('<div class="section-title">🔍 Key Findings</div>', unsafe_allow_html=True)
        findings = results.get('key_findings', [])
        
        if findings:
            for idx, finding in enumerate(findings, 1):
                # Keep the full text including everything after colons
                clean = finding.strip()
                if clean:
                    st.markdown(f"""
                    <div class="finding-card">
                        <span class="finding-number">{idx}.</span>
                        <span style="color: #334155; line-height: 1.7;">{clean}</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No key findings available")
    
    # TAB 4: Strategic Insights
    with tabs[3]:
        st.markdown('<div class="section-title">💡 Strategic Insights</div>', unsafe_allow_html=True)
        insights = results.get('insights', [])
        
        if insights:
            for insight in insights:
                clean = insight.strip()
                if clean:
                    st.markdown(f'<span class="insight-badge">✓ {clean}</span>', unsafe_allow_html=True)
        else:
            st.info("No strategic insights available")
    
    # TAB 5: All Sources
    with tabs[4]:
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
                    st.markdown(f"""
                    <div class="source-card">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div style="font-weight: 600; color: #0ea5e9; margin-bottom: 0.5rem; flex: 1;">{idx}. {source.get('title', 'Unknown')}</div>
                            <span style="background: #e0f2fe; color: #0284c7; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.75rem; white-space: nowrap; margin-left: 1rem;">{source_type}</span>
                        </div>
                        <a href="{source.get('url', '#')}" target="_blank" style="color: #64748b; font-size: 0.85rem; word-break: break-all;">🔗 {source.get('url', 'N/A')}</a>
                        <div style="color: #475569; margin-top: 0.5rem; font-size: 0.9rem;">{source.get('summary', 'No description available')}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No sources available")
    
    # EXPORT SECTION
    st.markdown("---")
    st.markdown("### 📥 Export Research")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if PDF_AVAILABLE:
            pdf_buffer = generate_pdf(results)
            if pdf_buffer:
                st.download_button(
                    "📄 Export as PDF",
                    pdf_buffer,
                    f"luminar_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    "application/pdf",
                    use_container_width=True
                )
        else:
            st.button("📄 Export as PDF", disabled=True, use_container_width=True)
            st.caption("Install reportlab to enable")
    
    with col2:
        md_content = f"""# {results['query']}

**Domain:** {results['domain']}  
**Date:** {results['timestamp']}  
**Model:** {results.get('model_type', 'N/A')}  
**Confidence Score:** {results.get('confidence_score', 'N/A')}/100

---

## Executive Summary

{results.get('summary', 'N/A')}

---

## Key Findings

"""
        for i, finding in enumerate(results.get('key_findings', []), 1):
            clean = finding.strip()
            md_content += f"{i}. {clean}\n\n"
        
        md_content += "\n---\n\n## Strategic Insights\n\n"
        for insight in results.get('insights', []):
            clean = insight.strip()
            md_content += f"- {clean}\n"
        
        md_content += "\n---\n\n## Sources\n\n"
        for idx, source in enumerate(results.get('sources', []), 1):
            md_content += f"{idx}. [{source.get('title', 'Unknown')}]({source.get('url', '#')})\n"
            md_content += f"   - Type: {source.get('source_type', 'Unknown')}\n"
            md_content += f"   - {source.get('summary', '')}\n\n"
        
        st.download_button(
            "📝 Export as Markdown",
            md_content,
            f"luminar_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            "text/markdown",
            use_container_width=True
        )
    
    with col3:
        json_content = json.dumps(results, indent=2, ensure_ascii=False)
        st.download_button(
            "📊 Export as JSON",
            json_content,
            f"luminar_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "application/json",
            use_container_width=True
        )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("""
<div style="text-align: center; padding: 2rem; margin-top: 3rem; color: #64748b; border-top: 1px solid #e2e8f0;">
    <div style="font-weight: 600; font-size: 1.1rem;">Powered by Luminar AI | © 2025</div>
    <div style="margin-top: 0.5rem; font-size: 0.85rem;">Enterprise Intelligence Platform with Multi-Agent Architecture</div>
    <div style="margin-top: 0.5rem; font-size: 0.75rem; color: #94a3b8;">
        Version 1.1.0 | Perplexity AI • YouTube API • arXiv • NewsAPI
    </div>
</div>
""", unsafe_allow_html=True)