import os
import re

TARGET_DIR = "/Users/shivaramakrishnan/Desktop/dashboard-1"

FOOTER_HTML = """            <footer class="app-footer"
                style="padding: 40px 0; border-top: 1px solid var(--border); margin-top: 30px;">
                <div style="display: grid; grid-template-columns: 1.5fr 1fr 1fr; gap: 40px;">
                    <div>
                        <h3 style="color: var(--navy); font-size: 14px; margin-bottom: 15px;">Rashtriya Raksha University</h3>
                        <p style="font-size: 12px; color: var(--text-muted); line-height: 1.8;">Puducherry Campus, Pondicherry
                            Institute of Hotel Management & Catering Technology [PIHMCT]<br>Opp To Mahalakshmi Nagar,
                            Murungapakkam, Puducherry – 605004</p>
                    </div>
                    <div>
                        <h3 style="color: var(--navy); font-size: 14px; margin-bottom: 15px;">Contact</h3>
                        <p style="font-size: 12px; color: var(--text-muted);">Email: pulse-r24@rru.ac.in</p>
                        <p style="font-size: 12px; color: var(--text-muted);">Phone: +91 79 XXXXXXXX</p>
                    </div>
                    <div>
                        <h3 style="color: var(--navy); font-size: 14px; margin-bottom: 15px;">Follow</h3>
                        <p style="font-size: 12px; color: var(--text-muted);"><a href="#"
                                style="color: inherit; text-decoration: none;">Instagram</a></p>
                        <p style="font-size: 12px; color: var(--text-muted);"><a href="#"
                                style="color: inherit; text-decoration: none;">LinkedIn</a></p>
                    </div>
                </div>
            </footer>"""

ALL_PAGES = [
    "students.html", "internships.html", "field-visits.html", 
    "industrial-visits.html", "placements.html", "external-jobs.html", 
    "reports.html", "settings.html", "dashboard.html"
]

def replace_footer(content):
    pattern = re.compile(r'<footer class="app-footer".*?</footer>', re.DOTALL)
    if pattern.search(content):
        return pattern.sub(FOOTER_HTML, content)
    return content

count = 0
for page in ALL_PAGES:
    filepath = os.path.join(TARGET_DIR, page)
    if not os.path.exists(filepath):
        print(f"Missing {page}")
        continue
    
    with open(filepath, 'r') as f:
        content = f.read()
        
    new_content = replace_footer(content)
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        count += 1
        print(f"Replaced footer in {page}")

print(f"Total replacements: {count}")
