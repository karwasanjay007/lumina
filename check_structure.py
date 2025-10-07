"""
File Structure Validator for Luminar Deep Researcher
Run this to check if all files are in the correct locations
"""

import os
from pathlib import Path
import sys

def check_structure():
    print("=" * 80)
    print("Luminar Deep Researcher - File Structure Check")
    print("=" * 80)
    print()
    
    # Current directory
    current_dir = Path.cwd()
    print(f"📁 Current Directory: {current_dir}")
    print()
    
    # Check for utils structure
    print("🔍 Checking utils structure...")
    
    utils_file = Path("utils.py")
    utils_dir = Path("utils")
    utils_init = Path("utils/__init__.py")
    
    if utils_dir.exists():
        print("   ✅ Found utils/ directory")
        if utils_init.exists():
            print("   ✅ Found utils/__init__.py")
            print("   ℹ️  Using package structure (utils/)")
        else:
            print("   ❌ Missing utils/__init__.py")
            print("   🔧 Creating utils/__init__.py...")
            # Copy content from the artifact
            print("   ⚠️  Please copy the content from 'utils/__init__.py' artifact")
    elif utils_file.exists():
        print("   ✅ Found utils.py file")
        print("   ℹ️  Using single file structure")
    else:
        print("   ❌ Neither utils.py nor utils/ directory found")
        print("   🔧 Please create one of these")
    
    print()
    
    # Check main files
    print("🔍 Checking main application files...")
    main_files = {
        "app.py": "Main Streamlit application",
        "research_engine.py": "Research execution engine",
        "results_display.py": "Results display module"
    }
    
    all_present = True
    for filename, description in main_files.items():
        filepath = Path(filename)
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"   ✅ {filename:25} ({size:,} bytes) - {description}")
        else:
            print(f"   ❌ {filename:25} - MISSING - {description}")
            all_present = False
    
    print()
    
    # Check prompts directory
    print("🔍 Checking prompts directory...")
    prompts_dir = Path("prompts")
    if prompts_dir.exists():
        print("   ✅ prompts/ directory exists")
        
        # Check for mock_data.json
        mock_data = prompts_dir / "mock_data.json"
        if mock_data.exists():
            size = mock_data.stat().st_size
            print(f"   ✅ mock_data.json ({size:,} bytes)")
        else:
            print("   ⚠️  mock_data.json missing (mock mode may not work)")
    else:
        print("   ⚠️  prompts/ directory missing")
        print("   🔧 Creating prompts/ directory...")
        prompts_dir.mkdir(parents=True, exist_ok=True)
        print("   ✅ Created prompts/")
    
    print()
    
    # Check data directory
    print("🔍 Checking data directory...")
    data_dir = Path("data/history")
    if data_dir.exists():
        print("   ✅ data/history/ directory exists")
        
        # Check for history file
        history_file = data_dir / "research_history.json"
        if history_file.exists():
            size = history_file.stat().st_size
            print(f"   ✅ research_history.json ({size:,} bytes)")
        else:
            print("   ℹ️  research_history.json not yet created (will be created on first save)")
    else:
        print("   ⚠️  data/history/ directory missing")
        print("   🔧 Creating data/history/ directory...")
        data_dir.mkdir(parents=True, exist_ok=True)
        print("   ✅ Created data/history/")
    
    print()
    
    # Check .env file
    print("🔍 Checking configuration...")
    env_file = Path(".env")
    if env_file.exists():
        print("   ✅ .env file exists")
        # Check for API keys
        with open(env_file, 'r') as f:
            content = f.read()
            if 'PERPLEXITY_API_KEY' in content:
                print("   ✅ PERPLEXITY_API_KEY configured")
            else:
                print("   ⚠️  PERPLEXITY_API_KEY not found in .env")
    else:
        print("   ⚠️  .env file missing")
    
    print()
    
    # Check Python packages
    print("🔍 Checking Python packages...")
    required_packages = {
        'streamlit': 'Streamlit framework',
        'aiohttp': 'Async HTTP client',
        'dotenv': 'Environment variables (python-dotenv)',
        'reportlab': 'PDF generation',
        'matplotlib': 'Charts and graphs',
        'pandas': 'Data analysis'
    }
    
    all_installed = True
    for package, description in required_packages.items():
        try:
            if package == 'dotenv':
                __import__('python_dotenv')
            else:
                __import__(package)
            print(f"   ✅ {package:15} - {description}")
        except ImportError:
            print(f"   ❌ {package:15} - NOT INSTALLED - {description}")
            all_installed = False
    
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if all_present and all_installed:
        print("✅ All checks passed! Ready to run.")
        print()
        print("Next steps:")
        print("  1. Configure API keys in .env (if not already done)")
        print("  2. Run: streamlit run app.py")
        print("  or")
        print("  2. Run: python start_app.py")
    else:
        print("⚠️  Some issues found. Please fix them before running.")
        if not all_present:
            print()
            print("Missing files:")
            print("  - Download all required Python files")
            print("  - Ensure they are in the same directory")
        
        if not all_installed:
            print()
            print("Missing packages:")
            print("  - Run: pip install -r requirements.txt")
    
    print()
    print("For more help, see:")
    print("  - README.md")
    print("  - QUICK_SETUP.md")
    print("  - TROUBLESHOOTING.md")
    print()

def show_directory_tree():
    """Show directory tree"""
    print("=" * 80)
    print("Directory Structure")
    print("=" * 80)
    print()
    
    current = Path.cwd()
    print(f"{current.name}/")
    
    # Show relevant files and directories
    items = [
        "app.py",
        "research_engine.py",
        "utils.py",
        "utils/",
        "results_display.py",
        "start_app.py",
        "requirements.txt",
        ".env",
        "prompts/",
        "data/"
    ]
    
    for item in items:
        path = Path(item)
        if path.exists():
            if path.is_dir():
                print(f"├── {item}")
                # Show some contents
                for subitem in sorted(path.glob("*"))[:5]:
                    if subitem.name != "__pycache__":
                        print(f"│   ├── {subitem.name}")
            else:
                size = path.stat().st_size
                print(f"├── {item:30} ({size:,} bytes)")
        else:
            print(f"├── {item:30} (missing)")
    
    print()

if __name__ == "__main__":
    try:
        check_structure()
        print()
        response = input("Show directory tree? (y/n): ")
        if response.lower() == 'y':
            print()
            show_directory_tree()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPress Enter to exit...")