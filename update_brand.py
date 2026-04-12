import os
import re

TARGET_DIR = "/Users/shivaramakrishnan/Desktop/dashboard-1"
ALL_PAGES = [
    "dashboard.html", "students.html", "internships.html", 
    "field-visits.html", "industrial-visits.html", "placements.html", 
    "external-jobs.html", "reports.html", "settings.html"
]

NEW_BRAND_HTML = """            <a href="https://rru.ac.in" target="_blank" class="topbar-brand">
                <img src="https://upload.wikimedia.org/wikipedia/en/b/bc/Rashtriya_Raksha_University_logo.png" alt="RRU Logo" class="topbar-logo">
                <div class="topbar-brand-text">
                    <span class="topbar-brand-name">Rashtriya Raksha University</span>
                    <span class="topbar-brand-sub">Pondicherry Campus</span>
                </div>
            </a>"""

count = 0
for page in ALL_PAGES:
    filepath = os.path.join(TARGET_DIR, page)
    if not os.path.exists(filepath):
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We want to match precisely the topbar-brand block
    pattern = re.compile(r'<a href="dashboard\.html" class="topbar-brand">.*?</a>', re.DOTALL)
    
    new_content = pattern.sub(NEW_BRAND_HTML, content)
    
    # Try another pattern just in case they added href="dashboard.html" elsewhere or class ordered differently
    if new_content == content:
       alt_pattern = re.compile(r'<a\s+href="[^"]*"\s+class="topbar-brand">.*?</a>', re.DOTALL | re.IGNORECASE)
       new_content = alt_pattern.sub(NEW_BRAND_HTML, content)
       
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        count += 1
        print(f"Updated brand in {page}")

print(f"\nTotal pages updated: {count}")
