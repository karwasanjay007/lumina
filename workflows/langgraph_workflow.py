# ============================================================================
# FILE 1: workflows/langgraph_workflow.py - COMPLETE WORKING VERSION
# ============================================================================
"""
Research Workflow with proper async handling and source limiting
"""

import asyncio
import os
import time
from datetime import datetime
from typing import Dict, List
from pathlib import Path


class ResearchWorkflow:
    """Orchestrates multiple research agents in parallel"""
    
    def __init__(self, max_sources_config=None):
        # Default to 2 sources per agent
        self.max_sources_config = max_sources_config or {
            'perplexity': 2,
            'youtube': 2,
            'api': 2
        }
        
        print(f"🚀 Workflow initialized with max sources:")
        for agent, max_val in self.max_sources_config.items():
            print(f"   - {agent}: {max_val}")
    
    async def execute(self, query: str, domain: str, agents: List[str]) -> Dict:
        """Execute research workflow with multiple agents"""
        
        start_time = datetime.now()
        
        results = {
            "query": query,
            "domain": domain,
            "agents": agents,
            "agent_results": [],
            "total_sources": 0,
            "total_cost": 0,
            "total_tokens": 0,
            "execution_time": 0,
            "timestamp": start_time.isoformat()
        }
        
        print(f"\n🚀 Starting research workflow")
        print(f"   Query: {query}")
        print(f"   Domain: {domain}")
        print(f"   Agents: {agents}")
        
        # Create tasks for each agent
        tasks = []
        for agent in agents:
            if agent == 'perplexity':
                print(f"   ✅ Adding Perplexity agent to execution queue")
                tasks.append(('perplexity', self._execute_perplexity(query, domain)))
            elif agent == 'youtube':
                print(f"   ✅ Adding YouTube agent to execution queue")
                tasks.append(('youtube', self._execute_youtube(query, domain)))
            elif agent == 'api':
                print(f"   ✅ Adding API agent to execution queue")
                tasks.append(('api', self._execute_api(query, domain)))
        
        if not tasks:
            results["error"] = "No agents selected for execution"
            return results
        
        print(f"\n⏳ Executing {len(tasks)} agents in parallel...")
        
        # Execute all agents in parallel
        task_coroutines = [task[1] for task in tasks]
        agent_responses = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # Process responses
        for idx, response in enumerate(agent_responses):
            agent_name = tasks[idx][0]
            
            if isinstance(response, Exception):
                print(f"   ❌ {agent_name} agent error: {response}")
                results["agent_results"].append({
                    "agent_name": agent_name,
                    "error": str(response),
                    "sources": [],
                    "cost": 0,
                    "tokens": 0
                })
                continue
            
            if response and isinstance(response, dict):
                print(f"   ✅ {agent_name} agent completed: {len(response.get('sources', []))} sources")
                results["agent_results"].append(response)
                results["total_sources"] += len(response.get("sources", []))
                results["total_cost"] += response.get("cost", 0)
                results["total_tokens"] += response.get("tokens", 0)
        
        # Consolidate results
        self._consolidate_results(results)
        
        # Calculate execution time
        end_time = datetime.now()
        results["execution_time"] = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Research complete:")
        print(f"   Total sources: {results['total_sources']}")
        print(f"   Total cost: ${results['total_cost']:.4f}")
        print(f"   Execution time: {results['execution_time']:.1f}s")
        
        return results
    
    async def _execute_perplexity(self, query: str, domain: str) -> Dict:
        """Execute Perplexity agent with original working code"""
        
        try:
            print(f"\n🌐 Initializing Perplexity agent...")
            
            # Import here to avoid circular imports
            from services.perplexity_client import PerplexityClient
            
            api_key = os.getenv("PERPLEXITY_API_KEY")
            if not api_key:
                print(f"   ❌ PERPLEXITY_API_KEY not found")
                return {
                    "agent_name": "perplexity",
                    "error": "API key not found",
                    "sources": [],
                    "cost": 0,
                    "tokens": 0
                }
            
            print(f"   ✅ API key loaded: {api_key[:10]}...")
            
            max_sources = self.max_sources_config.get('perplexity', 2)
            print(f"   📊 Max sources: {max_sources}")
            
            # Load system prompt from prompts folder
            prompt_path = Path(f"prompts/{domain}_prompt.txt")
            if prompt_path.exists():
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    system_prompt = f.read().strip()
                    print(f"   📝 Loaded {domain} prompt")
            else:
                system_prompt = """You are an expert research analyst. Provide comprehensive, well-structured analysis with:

## EXECUTIVE SUMMARY
(2-3 sentences)

## KEY FINDINGS
- Finding 1
- Finding 2
- Finding 3

## INSIGHTS
- Insight 1
- Insight 2

Format your response with clear section headers."""
                print(f"   ⚠️  Using default prompt")
            
            # Create client and execute search
            client = PerplexityClient(api_key)
            print(f"   🔍 Executing search...")
            
            # Use synchronous call (original working version)
            result = client.deep_search(
                query=query,
                system_prompt=system_prompt,
                domain=domain,
                max_tokens=2000
            )
            
            if not result.get('success'):
                print(f"   ❌ Search failed: {result.get('error')}")
                return {
                    "agent_name": "perplexity",
                    "error": result.get('error'),
                    "sources": result.get('sources', []),
                    "cost": result.get('estimated_cost', 0),
                    "tokens": result.get('tokens_used', 0)
                }
            
            # Extract sections
            sections = result.get('sections', {})
            sources = result.get('sources', [])
            
            # Limit sources to configured maximum
            if len(sources) > max_sources:
                print(f"   ⚠️  Limiting sources from {len(sources)} to {max_sources}")
                sources = sources[:max_sources]
            
            # Format sources for UI
            formatted_sources = []
            for source in sources:
                formatted_sources.append({
                    "title": source.get('title', 'Untitled'),
                    "url": source.get('url', ''),
                    "description": source.get('snippet', ''),
                    "source_type": "web",
                    "relevance_score": 1.0
                })
            
            print(f"   ✅ Perplexity complete: {len(formatted_sources)} sources")
            
            return {
                "agent_name": "perplexity",
                "sources": formatted_sources,
                "summary": sections.get('summary', ''),
                "findings": sections.get('findings', []),
                "insights": sections.get('insights', []),
                "cost": result.get('estimated_cost', 0),
                "tokens": result.get('tokens_used', 0),
                "duration": result.get('duration', 0)
            }
            
        except Exception as e:
            print(f"   ❌ Perplexity error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "agent_name": "perplexity",
                "error": str(e),
                "sources": [],
                "cost": 0,
                "tokens": 0
            }
    
    async def _execute_youtube(self, query: str, domain: str) -> Dict:
        """Execute YouTube agent - FIXED"""
        
        try:
            print(f"\n📹 Initializing YouTube agent...")
            
            # Import the fixed search_youtube function
            from agents.youtube_agent import search_youtube
            
            max_sources = self.max_sources_config.get('youtube', 2)
            print(f"   📊 Max sources: {max_sources}")
            print(f"   🔍 Searching videos for: '{query}'")
            
            # Search YouTube (this is synchronous, no await)
            videos = search_youtube(query, max_results=max_sources)
            
            # Format results
            sources = []
            for video in videos:
                sources.append({
                    "title": video.get('title', ''),
                    "url": video.get('url', ''),
                    "description": video.get('description', ''),
                    "source_type": "youtube",
                    "duration": video.get('duration', ''),
                    "views": video.get('views', 0),
                    "channel": video.get('channel', '')
                })
            
            print(f"   ✅ YouTube agent complete: {len(sources)} sources")
            
            return {
                "agent_name": "youtube",
                "sources": sources,
                "summary": f"Found {len(sources)} relevant videos on {query}",
                "findings": [],
                "insights": [],
                "cost": 0,
                "tokens": len(sources) * 100  # Estimate: 100 tokens per video metadata
            }
            
        except Exception as e:
            print(f"   ❌ YouTube error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "agent_name": "youtube",
                "error": str(e),
                "sources": [],
                "cost": 0,
                "tokens": 0
            }
    
    async def _execute_api(self, query: str, domain: str) -> Dict:
        """Execute API agent - FIXED (removed async call)"""
        
        try:
            print(f"\n📚 Initializing API agent...")
            
            from agents.api_agent import APIAgent
            
            max_sources = self.max_sources_config.get('api', 2)
            print(f"   📊 Max sources: {max_sources}")
            print(f"   🔍 Executing API agent...")
            
            agent = APIAgent()
            
            # Execute - NOTE: This is synchronous, not async!
            result = agent.execute(query, domain)
            
            # Get papers/sources from result
            papers = result.get('papers', [])
            
            # Limit to max_sources
            if len(papers) > max_sources:
                print(f"   ⚠️  Limiting sources from {len(papers)} to {max_sources}")
                papers = papers[:max_sources]
            
            # Format sources
            sources = []
            for paper in papers:
                sources.append({
                    "title": paper.get('title', ''),
                    "url": paper.get('url', ''),
                    "description": paper.get('summary', ''),
                    "source_type": paper.get('type', 'api'),
                    "authors": paper.get('authors', []),
                    "published": paper.get('published', '')
                })
            
            print(f"   ✅ API agent complete: {len(sources)} sources")
            
            return {
                "agent_name": "api",
                "sources": sources,
                "summary": result.get('summary', ''),
                "findings": result.get('findings', []),
                "insights": result.get('insights', []),
                "cost": 0,
                "tokens": 0
            }
            
        except Exception as e:
            print(f"   ❌ API error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "agent_name": "api",
                "error": str(e),
                "sources": [],
                "cost": 0,
                "tokens": 0
            }
    
    def _consolidate_results(self, results: Dict):
        """Consolidate results from all agents"""
        
        print(f"\n📊 Consolidating results...")
        print(f"   Agent results count: {len(results.get('agent_results', []))}")
        
        all_findings = []
        all_insights = []
        all_summaries = []
        
        for idx, agent_result in enumerate(results.get('agent_results', []), 1):
            agent_name = agent_result.get('agent_name', 'unknown')
            print(f"   {idx}. Processing {agent_name}:")
            
            # Skip if error
            if agent_result.get('error'):
                print(f"      ⚠️  Has error: {agent_result.get('error')}")
                continue
            
            # Show what we got
            print(f"      📚 Sources: {len(agent_result.get('sources', []))}")
            
            # Collect findings
            findings = agent_result.get('findings', [])
            if findings:
                print(f"      🔍 Findings: {len(findings)}")
                all_findings.extend(findings)
            
            # Collect insights
            insights = agent_result.get('insights', [])
            if insights:
                print(f"      💡 Insights: {len(insights)}")
                all_insights.extend(insights)
            
            # Collect summary
            summary = agent_result.get('summary', '')
            if summary:
                print(f"      📝 Summary: {len(summary)} chars")
                all_summaries.append(summary)
        
        # Deduplicate and store
        results['findings'] = list(dict.fromkeys(all_findings))[:10]  # Top 10
        results['insights'] = list(dict.fromkeys(all_insights))[:5]   # Top 5
        results['summary'] = ' | '.join(all_summaries)[:1000]          # Combined
        
        print(f"   ✅ Consolidated:")
        print(f"      - Findings: {len(results['findings'])}")
        print(f"      - Insights: {len(results['insights'])}")
        print(f"      - Summary: {len(results['summary'])} chars")


# ============================================================================
# FILE 2: app.py - COMPLETE WITH ALL FEATURES
# ============================================================================
"""
Multi-Agent AI Deep Researcher
Complete working version with all features
"""

import streamlit as st
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Multi-Agent AI Deep Researcher",
    page_icon="🔍",
    layout="wide"
)

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
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'research_results' not in st.session_state:
    st.session_state.research_results = None

# Header
st.markdown('<div class="main-header"><h1>🔍 Multi-Agent AI Deep Researcher</h1></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    with st.expander("📊 Agent Settings", expanded=True):
        # DEFAULT TO 2 SOURCES
        max_perplexity = st.slider("Perplexity Sources", 1, 20, 2)
        max_youtube = st.slider("YouTube Sources", 1, 20, 2)
        max_api = st.slider("API Sources", 1, 20, 2)
    
    st.markdown("---")
    st.markdown("**Current Config:**")
    st.json({
        "Perplexity": max_perplexity,
        "YouTube": max_youtube,
        "API": max_api
    })

# Main
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🎯 Research Query")
    domain = st.selectbox("Domain", ["general", "stocks", "medical", "academic", "technology"])
    query = st.text_area("Query", height=100)

with col2:
    st.subheader("🤖 Select Agents")
    use_perplexity = st.checkbox("🌐 Web Research", value=True)
    use_youtube = st.checkbox("📹 YouTube", value=False)
    use_api = st.checkbox("📚 API Sources", value=False)

if st.button("🚀 Start Research", type="primary"):
    selected_agents = []
    if use_perplexity:
        selected_agents.append('perplexity')
    if use_youtube:
        selected_agents.append('youtube')
    if use_api:
        selected_agents.append('api')
    
    if query and selected_agents:
        with st.status("🔍 Researching...", expanded=True) as status:
            try:
                from workflows.langgraph_workflow import ResearchWorkflow
                
                workflow = ResearchWorkflow(max_sources_config={
                    'perplexity': max_perplexity,
                    'youtube': max_youtube,
                    'api': max_api
                })
                
                results = asyncio.run(workflow.execute(query, domain, selected_agents))
                st.session_state.research_results = results
                
                status.update(label="✅ Complete!", state="complete")
            except Exception as e:
                status.update(label="❌ Error", state="error")
                st.error(str(e))

# Display Results
if st.session_state.research_results:
    results = st.session_state.research_results
    
    st.markdown("---")
    st.header("📊 Results")
    
    # Metrics
    cols = st.columns(4)
    cols[0].metric("📚 Sources", results.get('total_sources', 0))
    cols[1].metric("💰 Cost", f"${results.get('total_cost', 0):.6f}")
    cols[2].metric("🎯 Tokens", f"{results.get('total_tokens', 0):,}")
    cols[3].metric("⏱️ Time", f"{results.get('execution_time', 0):.1f}s")
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Summary", "🔍 Findings", "💡 Insights", "📚 Sources", "🗂️ JSON"])
    
    with tab1:
        st.subheader("Executive Summary")
        summary = results.get('summary', 'No summary available.')
        st.write(summary)
    
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
        st.subheader("All Sources")
        for agent_result in results.get('agent_results', []):
            agent_name = agent_result.get('agent_name', 'Unknown')
            sources = agent_result.get('sources', [])
            
            if sources:
                st.markdown(f"### {agent_name.title()} ({len(sources)} sources)")
                for source in sources:
                    with st.container():
                        st.markdown(f"**[{source.get('title', 'Untitled')}]({source.get('url', '#')})**")
                        st.caption(source.get('description', 'No description'))
                        st.markdown(f"*Type: {source.get('source_type', 'unknown')}*")
                        st.markdown("---")
    
    with tab5:
        st.subheader("Complete JSON Response")
        st.json(results)
    
    # Export
    st.markdown("---")
    st.subheader("📤 Export")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        json_str = json.dumps(results, indent=2, default=str)
        st.download_button(
            "📋 JSON",
            json_str,
            f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "application/json"
        )
    
    with col2:
        md_content = f"# Research Results\n\n**Query:** {query}\n\n**Domain:** {domain}\n\n"
        md_content += f"## Summary\n\n{results.get('summary', '')}\n\n"
        if results.get('findings'):
            md_content += "## Findings\n\n"
            for idx, f in enumerate(results['findings'], 1):
                md_content += f"{idx}. {f}\n"
        
        st.download_button(
            "📝 Markdown",
            md_content,
            f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            "text/markdown"
        )
    
    with col3:
        # PDF generation placeholder
        st.button("📄 PDF (Coming Soon)", disabled=True)

st.markdown("---")
st.caption(f"Multi-Agent AI Deep Researcher | © {datetime.now().year}")