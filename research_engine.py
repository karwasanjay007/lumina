"""
Research Engine Module
Handles all API calls and research execution
"""

import asyncio
import aiohttp
import json
import time
import os
from pathlib import Path
from dotenv import load_dotenv
from utils import console_log

load_dotenv()

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
# PROMPT LOADING
# ============================================================================

def load_domain_prompts():
    """Load domain-specific prompts from prompts/ directory"""
    prompts_dir = Path(__file__).parent / "prompts"
    domain_prompts = {}
    
    domains = {
        "Stock Market Analysis": "stocks",
        "Medical Research": "medical",
        "Technology Trends": "technology",
        "Academic Research": "academic",
        "General Research": "general"
    }
    
    for display_name, file_key in domains.items():
        prompt_file = prompts_dir / f"perplexity_prompt_{file_key}.txt"
        
        if prompt_file.exists():
            try:
                domain_prompts[display_name] = prompt_file.read_text(encoding='utf-8')
            except Exception as e:
                console_log(f"Error loading {prompt_file}: {e}", "WARNING")
                domain_prompts[display_name] = get_fallback_prompt(display_name)
        else:
            domain_prompts[display_name] = get_fallback_prompt(display_name)
    
    return domain_prompts

def get_fallback_prompt(domain: str) -> str:
    """Fallback prompts if files don't exist"""
    return """You are an expert research assistant conducting comprehensive analysis.

Research Focus: {domain_focus}
Topic: {query}

Provide structured analysis with:

## Executive Summary
[2-3 sentence overview]

## Key Findings
1. Finding 1: [Detailed finding with data]
2. Finding 2: [Detailed finding with data]
3. Finding 3: [Detailed finding with data]

## Strategic Insights
- Insight 1: [Strategic implication]
- Insight 2: [Strategic implication]

Include specific data, cite sources, and maintain professional analysis."""

# Load prompts at startup
DOMAIN_PROMPTS = load_domain_prompts()

# ============================================================================
# MOCK DATA LOADING
# ============================================================================

def load_mock_data():
    """Load mock data from JSON file"""
    mock_file = Path(__file__).parent / "prompts" / "mock_data.json"
    
    try:
        if mock_file.exists():
            with open(mock_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        console_log(f"Error loading mock data: {e}", "ERROR")
    
    return None

MOCK_DATA = load_mock_data()

# ============================================================================
# API IMPLEMENTATIONS
# ============================================================================

async def call_perplexity_api_real(query: str, domain: str, model_type: str, max_sources: int = 2):
    """Real Perplexity API call"""
    start_time = time.time()
    model_config = PERPLEXITY_MODELS[model_type]
    model_name = model_config["model"]
    max_tokens = model_config["max_tokens"]
    
    console_log(f"🌐 Market Intelligence: Starting {model_type} research")
    
    api_key = os.getenv("PERPLEXITY_API_KEY")
    
    if not api_key:
        console_log("❌ PERPLEXITY_API_KEY not found", "ERROR")
        return {
            "success": False,
            "error": "PERPLEXITY_API_KEY not found",
            "agent_name": "Market Intelligence",
            "execution_time": 0,
            "medium": "Perplexity API",
            "tokens": 0,
            "cost": 0.0,
            "status": "❌ Failed",
            "sources_retrieved": 0
        }
    
    # Load domain-specific prompt
    prompt_template = DOMAIN_PROMPTS.get(domain, DOMAIN_PROMPTS.get("General Research", ""))
    
    domain_focuses = {
        "Stock Market Analysis": "Stock market data, financial metrics, analyst opinions",
        "Medical Research": "Peer-reviewed medical studies, clinical trials",
        "Technology Trends": "Latest technology developments, innovations",
        "Academic Research": "Scholarly articles, research papers",
        "General Research": "Comprehensive analysis across sources"
    }
    
    domain_focus = domain_focuses.get(domain, "General research")
    
    system_prompt = prompt_template.format(
        domain=domain,
        domain_focus=domain_focus,
        query=query,
        topic=query
    )
    
    user_prompt = f"Research query: {query}\n\nProvide comprehensive analysis with executive summary, key findings, and strategic insights."
    
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
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "return_citations": True,
                    "search_recency_filter": "month"
                },
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    citations = data.get('citations', [])
                    usage = data.get('usage', {})
                    tokens = usage.get('total_tokens', 0)
                    
                    execution_time = time.time() - start_time
                    
                    # Parse response (simplified)
                    sections = content.split('##')
                    summary = sections[1] if len(sections) > 1 else content[:500]
                    findings = ["Finding from analysis"] * min(5, max_sources)
                    insights = ["Strategic insight"] * min(3, max_sources)
                    
                    # Process sources
                    sources = []
                    for idx, url in enumerate(citations[:max_sources], 1):
                        sources.append({
                            "title": f"Source {idx}",
                            "url": url,
                            "summary": "Referenced in analysis",
                            "agent": "Market Intelligence",
                            "source_type": "Web Search",
                            "medium": "Perplexity API"
                        })
                    
                    cost = (tokens / 1000) * 0.002
                    
                    return {
                        "success": True,
                        "agent_name": "Market Intelligence",
                        "model_used": model_name,
                        "model_type": model_type,
                        "summary": summary,
                        "findings": findings,
                        "insights": insights,
                        "sources": sources,
                        "source_count": len(sources),
                        "sources_retrieved": len(citations),
                        "tokens": tokens,
                        "prompt_tokens": usage.get('prompt_tokens', 0),
                        "completion_tokens": usage.get('completion_tokens', 0),
                        "cost": cost,
                        "execution_time": execution_time,
                        "status": "✅ Success",
                        "medium": "Perplexity API",
                        "data_type": "Web Search Results"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API returned {response.status}",
                        "agent_name": "Market Intelligence",
                        "execution_time": time.time() - start_time,
                        "status": "❌ Failed"
                    }
                    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "agent_name": "Market Intelligence",
            "execution_time": time.time() - start_time,
            "status": "❌ Error"
        }

async def call_perplexity_mock(query: str, domain: str, model_type: str, max_sources: int):
    """Mock Perplexity API call using data from JSON file"""
    start_time = time.time()
    console_log(f"🎭 Market Intelligence [MOCK]: Simulating {model_type}")
    await asyncio.sleep(2)
    execution_time = time.time() - start_time
    
    # Load mock data from JSON file
    if MOCK_DATA and domain in MOCK_DATA.get('domains', {}):
        domain_data = MOCK_DATA['domains'][domain]
        summary = domain_data.get('summary', '').format(query=query)
        findings = domain_data.get('findings', [])
        insights = domain_data.get('insights', [])
    else:
        summary = f"Mock analysis of '{query}' in {domain} domain"
        findings = [f"Finding {i}" for i in range(1, 6)]
        insights = [f"Insight {i}" for i in range(1, 4)]
    
    # Generate mock sources
    sources = []
    source_domains = ["Bloomberg", "Reuters", "WSJ", "Nature", "Science"]
    
    for i in range(1, max_sources + 1):
        source_domain = source_domains[i % len(source_domains)]
        sources.append({
            "title": f"[MOCK] {source_domain} - {domain} Report #{i}",
            "url": f"https://example.com/mock-{i}",
            "summary": f"Comprehensive {domain.lower()} analysis with data",
            "agent": "Market Intelligence",
            "source_type": "Mock Data",
            "medium": "Mock API"
        })
    
    return {
        "success": True,
        "agent_name": "Market Intelligence",
        "model_used": PERPLEXITY_MODELS[model_type]["model"],
        "model_type": model_type,
        "summary": summary,
        "findings": findings[:7],
        "insights": insights[:7],
        "sources": sources,
        "source_count": max_sources,
        "sources_retrieved": max_sources,
        "tokens": 1850,
        "prompt_tokens": 450,
        "completion_tokens": 1400,
        "cost": 0.0037,
        "execution_time": execution_time,
        "status": "✅ Success (Mock)",
        "medium": "Mock Perplexity API",
        "data_type": "Simulated Research"
    }

async def call_youtube_mock(query: str, max_sources: int):
    """Mock YouTube API call"""
    start_time = time.time()
    await asyncio.sleep(1.5)
    
    sources = []
    for i in range(1, max_sources + 1):
        sources.append({
            "title": f"[MOCK] Video Analysis #{i} - {query}",
            "url": f"https://youtube.com/watch?v=mock{i}",
            "summary": f"Expert video commentary on {query}",
            "agent": "Sentiment Analytics",
            "source_type": "Mock Video",
            "medium": "Mock YouTube"
        })
    
    return {
        "success": True,
        "agent_name": "Sentiment Analytics",
        "summary": f"Sentiment analysis of {max_sources} video sources reveals positive trends",
        "findings": [
            f"Analyzed {max_sources} videos with high engagement",
            "Positive sentiment dominates community discussions",
            "Expert opinions converge on key recommendations"
        ],
        "insights": [
            "Video content demonstrates practical applications",
            "Community identifies implementation challenges",
            "Expert predictions align on adoption timeline"
        ],
        "sources": sources,
        "source_count": max_sources,
        "sources_retrieved": max_sources,
        "tokens": 0,
        "cost": 0.0,
        "execution_time": time.time() - start_time,
        "status": "✅ Success (Mock)",
        "medium": "Mock YouTube API",
        "data_type": "Video Analysis"
    }

async def call_data_mock(query: str, max_sources: int):
    """Mock Data Intelligence API call"""
    start_time = time.time()
    await asyncio.sleep(1.5)
    
    sources = []
    for i in range(1, max_sources + 1):
        sources.append({
            "title": f"[MOCK] Academic Paper #{i} - {query}",
            "url": f"https://example.com/paper-{i}",
            "summary": f"Peer-reviewed research on {query}",
            "agent": "Data Intelligence",
            "source_type": "Mock Academic",
            "medium": "Mock arXiv+News"
        })
    
    return {
        "success": True,
        "agent_name": "Data Intelligence",
        "summary": f"Data synthesis of {max_sources} academic sources with statistical validation",
        "findings": [
            f"Integrated {max_sources} diverse academic sources",
            "Cross-validation shows high inter-source agreement",
            "Longitudinal trends demonstrate consistent patterns",
            "Meta-analysis reveals robust effect sizes"
        ],
        "insights": [
            "Research validates trends with statistical confidence",
            "Multi-source triangulation increases reliability",
            "Predictive analytics suggest sustained growth"
        ],
        "sources": sources,
        "source_count": max_sources,
        "sources_retrieved": max_sources,
        "tokens": 0,
        "cost": 0.0,
        "execution_time": time.time() - start_time,
        "status": "✅ Success (Mock)",
        "medium": "Mock APIs",
        "data_type": "Academic Data"
    }

# Real API implementations (simplified stubs)
async def call_youtube_api_real(query: str, max_sources: int = 2):
    """Real YouTube API - stub for now"""
    return await call_youtube_mock(query, max_sources)

async def call_data_api_real(query: str, max_sources: int = 2):
    """Real Data Intelligence API - stub for now"""
    return await call_data_mock(query, max_sources)

# ============================================================================
# RESEARCH EXECUTION
# ============================================================================

async def execute_research(query: str, domain: str, agents: dict, model_type: str, 
                          mock_mode: bool, market_sources: int, sentiment_sources: int, 
                          data_sources: int):
    """Execute research across all selected agents"""
    console_log("=" * 80)
    console_log("🔬 RESEARCH EXECUTION START")
    console_log(f"   Query: {query}")
    console_log(f"   Domain: {domain}")
    console_log(f"   Model: {model_type}")
    console_log(f"   Mock: {mock_mode}")
    console_log("=" * 80)
    
    tasks = []
    
    if agents.get("Market Intelligence"):
        console_log(f"📌 Queuing Market Intelligence ({market_sources} sources)")
        if mock_mode:
            tasks.append(("Market Intelligence", call_perplexity_mock(query, domain, model_type, market_sources)))
        else:
            tasks.append(("Market Intelligence", call_perplexity_api_real(query, domain, model_type, market_sources)))
    
    if agents.get("Sentiment Analytics"):
        console_log(f"📌 Queuing Sentiment Analytics ({sentiment_sources} sources)")
        if mock_mode:
            tasks.append(("Sentiment Analytics", call_youtube_mock(query, sentiment_sources)))
        else:
            tasks.append(("Sentiment Analytics", call_youtube_api_real(query, sentiment_sources)))
    
    if agents.get("Data Intelligence"):
        console_log(f"📌 Queuing Data Intelligence ({data_sources} sources)")
        if mock_mode:
            tasks.append(("Data Intelligence", call_data_mock(query, data_sources)))
        else:
            tasks.append(("Data Intelligence", call_data_api_real(query, data_sources)))
    
    console_log(f"🚀 Executing {len(tasks)} agents in parallel...")
    
    results = {}
    for name, task in tasks:
        results[name] = await task
    
    console_log("✅ RESEARCH EXECUTION COMPLETE")
    console_log("=" * 80)
    
    return results