"""
Environment checker - Verify Python environment and dependencies
Run: python check_environment.py
"""

import sys
import os
from pathlib import Path

def print_header(text):
    print("\n" + "=" * 70)
    print(text.center(70))
    print("=" * 70 + "\n")

def print_success(text):
    print(f"✓ {text}")

def print_error(text):
    print(f"✗ {text}")

def print_warning(text):
    print(f"⚠ {text}")

print_header("Environment Diagnostic Tool")

# 1. Python version and path
print("Python Environment:")
print("-" * 70)
print_success(f"Python version: {sys.version}")
print_success(f"Python executable: {sys.executable}")
print_success(f"Python prefix: {sys.prefix}")

# Check if in virtual environment
in_venv = hasattr(sys, 'real_prefix') or (
    hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
)

if in_venv:
    print_success("Running in virtual environment")
else:
    print_error("NOT running in virtual environment!")
    print_warning("Please activate .venv first:")
    print("  Windows: .venv\\Scripts\\activate")
    print("  Mac/Linux: source .venv/bin/activate")

# 2. Check sys.path
print("\nPython Path (sys.path):")
print("-" * 70)
for i, path in enumerate(sys.path[:5], 1):
    print(f"  {i}. {path}")
if len(sys.path) > 5:
    print(f"  ... and {len(sys.path) - 5} more paths")

# 3. Try importing critical dependencies
print("\nDependency Check:")
print("-" * 70)

dependencies = [
    ("streamlit", "Streamlit UI framework"),
    ("aiohttp", "Async HTTP client (CRITICAL)"),
    ("dotenv", "Environment variable loader"),
    ("langchain", "LangChain framework"),
    ("langgraph", "LangGraph orchestration"),
]

all_ok = True
for module_name, description in dependencies:
    try:
        module = __import__(module_name)
        version = getattr(module, '__version__', 'unknown')
        print_success(f"{module_name} ({description}) - version {version}")
    except ImportError as e:
        print_error(f"{module_name} NOT FOUND - {description}")
        print(f"        Error: {e}")
        all_ok = False

# 4. Check project structure
print("\nProject Structure:")
print("-" * 70)

project_root = Path.cwd()
required_dirs = [
    "agents",
    "workflows",
    "utils",
    "prompts",
    "services",
]

for dir_name in required_dirs:
    dir_path = project_root / dir_name
    if dir_path.exists():
        print_success(f"{dir_name}/ exists")
    else:
        print_error(f"{dir_name}/ NOT FOUND")
        all_ok = False

# 5. Check environment file
print("\nConfiguration:")
print("-" * 70)

env_file = project_root / ".env"
if env_file.exists():
    print_success(".env file exists")
    
    # Try to load and check for API key
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if api_key:
            print_success(f"PERPLEXITY_API_KEY configured ({api_key[:10]}...)")
        else:
            print_warning("PERPLEXITY_API_KEY not set in .env")
    except Exception as e:
        print_warning(f"Could not read .env: {e}")
else:
    print_error(".env file NOT FOUND")
    print_warning("Create .env from .env.example")

# 6. Try importing project modules
print("\nProject Modules:")
print("-" * 70)

try:
    # Add current directory to path if not already there
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Try importing agents
    try:
        from agents.perplexity_agent import PerplexityAgent
        print_success("agents.perplexity_agent imports successfully")
    except ImportError as e:
        print_error(f"agents.perplexity_agent FAILED: {e}")
        all_ok = False
    
    try:
        from agents.api_agent import APIAgent
        print_success("agents.api_agent imports successfully")
    except ImportError as e:
        print_error(f"agents.api_agent FAILED: {e}")
        all_ok = False
    
    try:
        from agents.youtube_agent import YouTubeAgent
        print_success("agents.youtube_agent imports successfully")
    except ImportError as e:
        print_error(f"agents.youtube_agent FAILED: {e}")
        all_ok = False
    
    try:
        from workflows.langgraph_workflow import ResearchWorkflow
        print_success("workflows.langgraph_workflow imports successfully")
    except ImportError as e:
        print_error(f"workflows.langgraph_workflow FAILED: {e}")
        all_ok = False

except Exception as e:
    print_error(f"Project import test failed: {e}")
    all_ok = False

# 7. Summary
print_header("Summary")

if all_ok and in_venv:
    print("✅ Environment is correctly configured!")
    print("\nYou can now run:")
    print("  python run_streamlit.py")
elif not in_venv:
    print("⚠️  Virtual environment is NOT activated")
    print("\nPlease activate it first:")
    print("  Windows: .venv\\Scripts\\activate")
    print("  Mac/Linux: source .venv/bin/activate")
    print("\nThen run this check again:")
    print("  python check_environment.py")
else:
    print("❌ Some issues were found")
    print("\nPlease fix the errors above, then run:")
    print("  python check_environment.py")

print()