# ============================================================================
# SEARCH AND REPLACE GUIDE FOR STREAMLIT DEPRECATION FIX
# ============================================================================
# 
# Replace all instances of use_container_width in these files:
# - app.py
# - results_display.py  
# - ui/components/export_buttons.py
# - Any other Streamlit UI files
#
# ============================================================================

"""
INSTRUCTIONS:
1. Use your IDE's Find & Replace feature
2. Search for: use_container_width=True
3. Replace with: width='stretch'
4. Then search for: use_container_width=False
5. Replace with: width='content'
"""

# ============================================================================
# EXAMPLE FIXES - Apply these patterns across all your Streamlit files
# ============================================================================

# ============================================================================
# FILE: app.py (PARTIAL - showing key changes)
# ============================================================================

# BEFORE (❌ DEPRECATED):
# st.button(button_label, key=history_key, use_container_width=True)

# AFTER (✅ FIXED):
# st.button(button_label, key=history_key, width='stretch')

# BEFORE (❌ DEPRECATED):
# st.download_button(
#     "📥 Download Complete History",
#     history_json,
#     f"luminar_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
#     "application/json",
#     use_container_width=True,
#     key="download_history_json"
# )

# AFTER (✅ FIXED):
# st.download_button(
#     "📥 Download Complete History",
#     history_json,
#     f"luminar_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
#     "application/json",
#     width='stretch',
#     key="download_history_json"
# )

# ============================================================================
# FILE: results_display.py (PARTIAL - showing key changes)
# ============================================================================

# BEFORE (❌ DEPRECATED):
# st.download_button(
#     "📄 Download PDF Report",
#     pdf_buffer,
#     pdf_filename,
#     "application/pdf",
#     use_container_width=True,
#     key="download_pdf_btn"
# )

# AFTER (✅ FIXED):
# st.download_button(
#     "📄 Download PDF Report",
#     pdf_buffer,
#     pdf_filename,
#     "application/pdf",
#     width='stretch',
#     key="download_pdf_btn"
# )

# BEFORE (❌ DEPRECATED):
# st.button("📄 PDF Export", disabled=True, use_container_width=True)

# AFTER (✅ FIXED):
# st.button("📄 PDF Export", disabled=True, width='stretch')

# ============================================================================
# FILE: ui/components/export_buttons.py (PARTIAL - showing key changes)
# ============================================================================

# BEFORE (❌ DEPRECATED):
# if st.button("📄 Export PDF", use_container_width=True):

# AFTER (✅ FIXED):
# if st.button("📄 Export PDF", width='stretch'):

# BEFORE (❌ DEPRECATED):
# if st.button("📝 Export Markdown", use_container_width=True):

# AFTER (✅ FIXED):
# if st.button("📝 Export Markdown", width='stretch'):

# BEFORE (❌ DEPRECATED):
# st.download_button(
#     label="📋 Export JSON",
#     data=json_content,
#     file_name=f"{filename_base}.json",
#     mime="application/json",
#     use_container_width=True
# )

# AFTER (✅ FIXED):
# st.download_button(
#     label="📋 Export JSON",
#     data=json_content,
#     file_name=f"{filename_base}.json",
#     mime="application/json",
#     width='stretch'
# )

# ============================================================================
# AUTOMATED FIX - Use this regex in your IDE
# ============================================================================
"""
Find:    use_container_width\s*=\s*True
Replace: width='stretch'

Find:    use_container_width\s*=\s*False
Replace: width='content'
"""

# ============================================================================
# VERIFICATION SCRIPT - Run this to check for remaining issues
# ============================================================================

import os
import re
from pathlib import Path

def check_deprecated_params(directory="."):
    """Check for deprecated use_container_width parameters"""
    deprecated_pattern = re.compile(r'use_container_width\s*=')
    issues = []
    
    for root, dirs, files in os.walk(directory):
        # Skip common directories
        if any(skip in root for skip in ['.git', '__pycache__', 'venv', 'env', 'node_modules']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = Path(root) / file
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines, 1):
                            if deprecated_pattern.search(line):
                                issues.append({
                                    'file': str(filepath),
                                    'line': i,
                                    'content': line.strip()
                                })
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    
    return issues

if __name__ == "__main__":
    print("🔍 Checking for deprecated Streamlit parameters...\n")
    issues = check_deprecated_params()
    
    if issues:
        print(f"❌ Found {len(issues)} deprecated use_container_width usages:\n")
        for issue in issues:
            print(f"📄 {issue['file']}:{issue['line']}")
            print(f"   {issue['content']}\n")
        print("\n💡 Replace use_container_width=True with width='stretch'")
        print("💡 Replace use_container_width=False with width='content'")
    else:
        print("✅ No deprecated use_container_width parameters found!")