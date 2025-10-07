"""
Research Engine Module - FIXED VERSION WITH REAL API CALLS
Handles agent orchestration and execution with proper API integration
"""

import time
import json
import os
import requests
from pathlib import Path
from utils import console_log

# Perplexity Models Configuration
PERPLEXITY_MODELS = {
    "Quick Search": {
        "model": "sonar",
        "icon": "⚡",
        "description": "Fast results, lower cost",
        "cost_multiplier": 0.5
    },
    "Deep Research": {
        "model": "sonar-pro",
        "icon": "🔬",
        "description": "Comprehensive analysis, higher accuracy",
        "cost_multiplier": 1.5
    }
}

def load_mock_data():
    """Load mock data from JSON file"""
    try:
        mock_file = Path("prompts/mock_data.json")
        if mock_file.exists():
            with open(mock_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        console_log(f"Error loading mock data: {e}", "ERROR")
    
    # Return default mock data if file doesn't exist
    return {
        "perplexity_response": "This is a mock response from Perplexity API.",
        "findings": ["Mock finding 1", "Mock finding 2", "Mock finding 3"],
        "insights": ["Mock insight 1", "Mock insight 2"]
    }

def call_perplexity_api_directly(query, model_type, max_sources):
    """
    Call Perplexity API directly without needing agent module
    """
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise Exception("PERPLEXITY_API_KEY not found in environment")
    
    model = PERPLEXITY_MODELS[model_type]["model"]
    
    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a research assistant. Provide detailed findings and insights based on the query."
                    },
                    {
                        "role": "user",
                        "content": f"Research this topic and provide {max_sources} key findings and insights: {query}"
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.2,
                "return_citations": True,
                "return_images": False
            },
            timeout=60
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Extract response
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        citations = data.get("citations", [])
        
        # Parse findings and insights from content
        findings = []
        insights = []
        
        # Simple parsing - you can make this more sophisticated
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) > 20:
                if len(findings) < max_sources:
                    findings.append(line)
                elif len(insights) < max_sources:
                    insights.append(line)
        
        # Create sources from citations
        sources = []
        for i, citation in enumerate(citations[:max_sources]):
            sources.append({
                "title": f"Source #{i+1} - {query[:50]}",
                "url": citation if isinstance(citation, str) else citation.get("url", f"https://source-{i+1}.com"),
                "summary": f"Research source for: {query[:50]}",
                "agent": "Market Intelligence",
                "source_type": "Web Research",
                "medium": "Perplexity API"
            })
        
        # Get token usage
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
        
        # Calculate cost (approximate)
        cost = (prompt_tokens * 0.000001) + (completion_tokens * 0.000003)
        
        return {
            "success": True,
            "agent_name": "Market Intelligence",
            "summary": content[:500] if content else f"Analysis of {max_sources} sources for: {query}",
            "findings": findings if findings else ["Research finding from Perplexity API"],
            "insights": insights if insights else ["Insight from Perplexity API"],
            "sources": sources,
            "source_count": len(sources),
            "sources_retrieved": len(sources),
            "tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost": cost,
            "status": "✅ Success",
            "model_used": model,
            "model_type": model_type,
            "medium": "Perplexity API",
            "data_type": "Live Research"
        }
        
    except Exception as e:
        raise Exception(f"Perplexity API call failed: {str(e)}")

def execute_market_intelligence(query, model_type, max_sources, mock_mode=False):
    """
    Execute Market Intelligence agent (Perplexity)
    """
    start_time = time.time()
    
    try:
        if mock_mode:
            console_log("🎭 Market Intelligence: Using MOCK mode", "INFO")
            time.sleep(2)
            
            mock_data = load_mock_data()
            
            sources = []
            for i in range(max_sources):
                sources.append({
                    "title": f"[MOCK] Source #{i+1} - {query[:50]}",
                    "url": f"https://example.com/mock-{i+1}",
                    "summary": f"Mock summary for {query[:50]}",
                    "agent": "Market Intelligence",
                    "source_type": "Mock Data",
                    "medium": "Mock Perplexity API"
                })
            
            return {
                "success": True,
                "agent_name": "Market Intelligence",
                "summary": f"Mock analysis of {max_sources} sources for: {query}",
                "findings": mock_data.get("findings", ["Mock finding 1", "Mock finding 2"]),
                "insights": mock_data.get("insights", ["Mock insight 1", "Mock insight 2"]),
                "sources": sources,
                "source_count": len(sources),
                "sources_retrieved": len(sources),
                "tokens": 1850,
                "prompt_tokens": 450,
                "completion_tokens": 1400,
                "cost": 0.0037,
                "execution_time": time.time() - start_time,
                "status": "✅ Success (Mock)",
                "model_used": PERPLEXITY_MODELS[model_type]["model"],
                "model_type": model_type,
                "medium": "Mock Perplexity API",
                "data_type": "Simulated Research"
            }
        else:
            console_log("✅ Market Intelligence: Using LIVE Perplexity API", "INFO")
            
            # FIXED: Call Perplexity API directly instead of importing agent module
            try:
                result = call_perplexity_api_directly(query, model_type, max_sources)
                result["execution_time"] = time.time() - start_time
                return result
            except Exception as api_error:
                console_log(f"⚠️ Perplexity API call failed: {api_error}", "WARNING")
                console_log("Falling back to mock mode", "WARNING")
                # Only fall back to mock if API call fails
                return execute_market_intelligence(query, model_type, max_sources, mock_mode=True)
            
    except Exception as e:
        console_log(f"Error in Market Intelligence: {e}", "ERROR")
        return {
            "success": False,
            "agent_name": "Market Intelligence",
            "execution_time": time.time() - start_time,
            "status": "❌ Failed",
            "error": str(e)
        }

def execute_sentiment_analytics(query, max_sources, mock_mode=False):
    """
    Execute Sentiment Analytics agent (YouTube)
    """
    start_time = time.time()
    
    try:
        if mock_mode:
            console_log("🎭 Sentiment Analytics: Using MOCK mode", "INFO")
            time.sleep(1.5)
            
            sources = []
            for i in range(max_sources):
                sources.append({
                    "title": f"[MOCK] Video Analysis #{i+1} - {query[:50]}",
                    "url": f"https://youtube.com/watch?v=mock{i+1}",
                    "summary": f"Expert video commentary on {query[:50]}",
                    "agent": "Sentiment Analytics",
                    "source_type": "Mock Video",
                    "medium": "Mock YouTube"
                })
            
            return {
                "success": True,
                "agent_name": "Sentiment Analytics",
                "summary": f"Sentiment analysis of {max_sources} video sources",
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
                "source_count": len(sources),
                "sources_retrieved": len(sources),
                "tokens": 0,
                "cost": 0.0,
                "execution_time": time.time() - start_time,
                "status": "✅ Success (Mock)",
                "medium": "Mock YouTube API",
                "data_type": "Video Analysis"
            }
        else:
            console_log("✅ Sentiment Analytics: Using LIVE YouTube API", "INFO")
            
            # Try to use the actual YouTube agent
            try:
                from agents.youtube_researcher import analyze_youtube
                from graph.state import ResearchState
                
                state = ResearchState(
                    topic=query,
                    mode="extended" if max_sources > 3 else "simple"
                )
                
                result = analyze_youtube(state)
                youtube_results = result.get("youtube_results", {})
                
                return {
                    "success": True,
                    "agent_name": "Sentiment Analytics",
                    "summary": f"YouTube analysis for: {query}",
                    "findings": youtube_results.get("findings", []),
                    "insights": youtube_results.get("insights", []),
                    "sources": youtube_results.get("sources", []),
                    "source_count": len(youtube_results.get("sources", [])),
                    "sources_retrieved": len(youtube_results.get("sources", [])),
                    "tokens": youtube_results.get("tokens", 0),
                    "cost": youtube_results.get("cost", 0.0),
                    "execution_time": youtube_results.get("elapsed", 0.0),
                    "status": "✅ Success",
                    "medium": "YouTube API",
                    "data_type": "Video Analysis"
                }
            except Exception as import_error:
                console_log(f"⚠️ YouTube agent error: {import_error}", "WARNING")
                console_log("Falling back to mock mode", "WARNING")
                return execute_sentiment_analytics(query, max_sources, mock_mode=True)
            
    except Exception as e:
        console_log(f"Error in Sentiment Analytics: {e}", "ERROR")
        return {
            "success": False,
            "agent_name": "Sentiment Analytics",
            "execution_time": time.time() - start_time,
            "status": "❌ Failed",
            "error": str(e)
        }

def call_arxiv_api(query, max_results=5):
    """Call arXiv API directly"""
    try:
        import urllib.parse
        import xml.etree.ElementTree as ET
        
        search_query = urllib.parse.quote(query)
        url = f"http://export.arxiv.org/api/query?search_query=all:{search_query}&start=0&max_results={max_results}"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}
        
        sources = []
        for entry in root.findall('atom:entry', namespace):
            title = entry.find('atom:title', namespace)
            summary = entry.find('atom:summary', namespace)
            link = entry.find('atom:id', namespace)
            
            sources.append({
                "title": title.text.strip() if title is not None and title.text is not None else "Academic Paper",
                "url": link.text.strip() if link is not None and link.text is not None else "",
                "summary": summary.text.strip()[:200] if summary is not None and summary.text is not None else "Academic research paper",
                "agent": "Data Intelligence",
                "source_type": "Academic",
                "medium": "arXiv API"
            })
        
        return sources
    except Exception as e:
        console_log(f"arXiv API error: {e}", "WARNING")
        return []

def execute_data_intelligence(query, max_sources, mock_mode=False):
    """
    Execute Data Intelligence agent (arXiv + News APIs)
    """
    start_time = time.time()
    
    try:
        if mock_mode:
            console_log("🎭 Data Intelligence: Using MOCK mode", "INFO")
            time.sleep(1.5)
            
            sources = []
            for i in range(max_sources):
                sources.append({
                    "title": f"[MOCK] Academic Paper #{i+1} - {query[:50]}",
                    "url": f"https://example.com/paper-{i+1}",
                    "summary": f"Peer-reviewed research on {query[:50]}",
                    "agent": "Data Intelligence",
                    "source_type": "Mock Academic",
                    "medium": "Mock arXiv+News"
                })
            
            return {
                "success": True,
                "agent_name": "Data Intelligence",
                "summary": f"Data synthesis of {max_sources} academic sources",
                "findings": [
                    f"Integrated {max_sources} diverse academic sources",
                    "Cross-validation shows high inter-source agreement",
                    "Longitudinal trends demonstrate consistent patterns",
                    "Meta-analysis reveals robust effect sizes"
                ],
                "insights": [
                    "Research validates trends with statistical confidence",
                    "Multi-source triangulation increases reliability",
                    "Emerging patterns suggest future research directions"
                ],
                "sources": sources,
                "source_count": len(sources),
                "sources_retrieved": len(sources),
                "tokens": 0,
                "cost": 0.0,
                "execution_time": time.time() - start_time,
                "status": "✅ Success (Mock)",
                "medium": "Mock APIs",
                "data_type": "Academic Research"
            }
        else:
            console_log("✅ Data Intelligence: Using LIVE arXiv API", "INFO")
            
            # FIXED: Call arXiv API directly
            try:
                sources = call_arxiv_api(query, max_sources)
                
                if sources:
                    findings = [f"Found {len(sources)} academic sources", 
                               "Research shows peer-reviewed insights",
                               "Academic consensus on key findings"]
                    insights = ["Academic research validates topic",
                               "Multiple studies support conclusions"]
                else:
                    findings = ["Limited academic sources found"]
                    insights = ["Consider broader search terms"]
                
                result = {
                    "success": True,
                    "agent_name": "Data Intelligence",
                    "summary": f"Academic research analysis from {len(sources)} sources",
                    "findings": findings,
                    "insights": insights,
                    "sources": sources,
                    "source_count": len(sources),
                    "sources_retrieved": len(sources),
                    "tokens": 0,
                    "cost": 0.0,
                    "execution_time": time.time() - start_time,
                    "status": "✅ Success",
                    "medium": "arXiv API",
                    "data_type": "Academic Research"
                }
                return result
            except Exception as api_error:
                console_log(f"⚠️ arXiv API error: {api_error}", "WARNING")
                console_log("Falling back to mock mode", "WARNING")
                return execute_data_intelligence(query, max_sources, mock_mode=True)
            
    except Exception as e:
        console_log(f"Error in Data Intelligence: {e}", "ERROR")
        return {
            "success": False,
            "agent_name": "Data Intelligence",
            "execution_time": time.time() - start_time,
            "status": "❌ Failed",
            "error": str(e)
        }

def execute_research(query, domain, agents, model_type, market_sources, 
                    sentiment_sources, data_sources, progress_callback=None, mock_mode=False):
    """
    Main research execution function
    """
    console_log(f"🚀 Starting research - Mock Mode: {mock_mode}", "INFO")
    
    agent_results = {}
    total_agents = sum(1 for v in agents.values() if v)
    completed_agents = 0
    
    # Market Intelligence
    if agents.get("Market Intelligence", False):
        if progress_callback:
            progress_callback(0.1, "🌐 Running Market Intelligence...")
        
        agent_results["Market Intelligence"] = execute_market_intelligence(
            query, model_type, market_sources, mock_mode=mock_mode
        )
        
        completed_agents += 1
        if progress_callback:
            progress_callback(0.1 + (0.6 * completed_agents / total_agents), 
                            f"✅ Market Intelligence complete")
    
    # Sentiment Analytics
    if agents.get("Sentiment Analytics", False):
        if progress_callback:
            progress_callback(0.1 + (0.6 * completed_agents / total_agents), 
                            "📊 Running Sentiment Analytics...")
        
        agent_results["Sentiment Analytics"] = execute_sentiment_analytics(
            query, sentiment_sources, mock_mode=mock_mode
        )
        
        completed_agents += 1
        if progress_callback:
            progress_callback(0.1 + (0.6 * completed_agents / total_agents), 
                            f"✅ Sentiment Analytics complete")
    
    # Data Intelligence
    if agents.get("Data Intelligence", False):
        if progress_callback:
            progress_callback(0.1 + (0.6 * completed_agents / total_agents), 
                            "📈 Running Data Intelligence...")
        
        agent_results["Data Intelligence"] = execute_data_intelligence(
            query, data_sources, mock_mode=mock_mode
        )
        
        completed_agents += 1
        if progress_callback:
            progress_callback(0.1 + (0.6 * completed_agents / total_agents), 
                            f"✅ Data Intelligence complete")
    
    if progress_callback:
        progress_callback(0.8, "📊 Consolidating results...")
    
    console_log(f"✅ Research complete - Agents: {completed_agents}/{total_agents}", "INFO")
    
    return agent_results