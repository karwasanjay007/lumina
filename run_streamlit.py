"""
Wrapper script to run Streamlit with environment variables loaded
Fixed to use the SAME Python that's executing this script
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment from .env file
env_file = Path(__file__).parent / '.env'
load_dotenv(env_file)

# Verify API key is loaded
api_key = os.getenv("PERPLEXITY_API_KEY")
if api_key:
    print(f"✅ API Key loaded: {api_key[:10]}...{api_key[-4:]}")
else:
    print("❌ WARNING: PERPLEXITY_API_KEY not found in .env!")
    sys.exit(1)

print("\n🚀 Starting Streamlit with environment loaded...\n")

# CRITICAL FIX: Use the SAME Python that's running this script
# Don't use subprocess - use execvp to replace this process with streamlit
# This ensures the same Python environment is used

# Method 1: Use sys.executable (the Python running this script)
os.execvp(
    sys.executable,
    [sys.executable, "-m", "streamlit", "run", "app.py"]
)

# Note: Code after execvp won't execute because the process is replaced