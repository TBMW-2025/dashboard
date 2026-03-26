"""
dashboard_utils.py — Combined utility script (archived reference only)
----------------------------------------------------------------------
This script is NOT meant to be run again. It is kept here as a reference
for what was previously used to batch-update sidebars and convert light theme.

The dashboard has since been fully updated manually. The sidebar now uses:
  - RRU logo image
  - Updated nav items (Dashboard, Students, Companies, Placements, Reports, Settings)
  - Bootstrap Icons
  - User profile (avatar + name + role) instead of initials

To re-run any batch updates in the future, update the sidebar_html below
to match the current sidebar markup before running.
"""

import os
import re

# ─────────────────────────────────────────────────────────────────────
# PART 1 (from update_sidebar.py): Batch sidebar replacement
# ─────────────────────────────────────────────────────────────────────

CURRENT_SIDEBAR_TEMPLATE = """
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="sidebar-top">
                <img src="https://upload.wikimedia.org/wikipedia/en/b/bc/Rashtriya_Raksha_University_logo.png"
                    alt="Logo" class="sidebar-img-logo">
                <nav class="sidebar-nav">
                    <a href="dashboard.html" class="nav-item {active_index}">
                        <i class="bi bi-speedometer2"></i>
                        <span>Dashboard</span>
                    </a>
                    <a href="students.html" class="nav-item {active_students}">
                        <i class="bi bi-people-fill"></i>
                        <span>Students</span>
                    </a>
                    <a href="companies.html" class="nav-item {active_companies}">
                        <i class="bi bi-building"></i>
                        <span>Companies</span>
                    </a>
                    <a href="placements.html" class="nav-item {active_placements}">
                        <i class="bi bi-briefcase-fill"></i>
                        <span>Placements</span>
                    </a>
                    <a href="reports.html" class="nav-item {active_reports}">
                        <i class="bi bi-bar-chart-fill"></i>
                        <span>Reports</span>
                    </a>
                    <a href="settings.html" class="nav-item {active_settings}">
                        <i class="bi bi-gear"></i>
                        <span>Settings</span>
                    </a>
                </nav>
            </div>

            <div class="sidebar-bottom">
                <div class="bottom-icons">
                    <a href="mailto:pulse-r24@rru.ac.in" class="icon-btn" title="Contact Us"><i
                            class="bi bi-chat-left-text"></i></a>
                </div>
                <div class="user-profile" onclick="safeRedirect('dashboard.html')">
                    <div class="avatar">A</div>
                    <div>
                        <div class="user-name">Arsh.G</div>
                        <div class="user-role">Admin</div>
                    </div>
                </div>
            </div>
        </div>
"""

def update_sidebars():
    """Replaces sidebars in all HTML files (except dashboard.html) with current template."""
    for file in os.listdir('.'):
        if not file.endswith('.html') or file == 'dashboard.html':
            continue
        with open(file, 'r') as f:
            content = f.read()

        active = {
            'active_index': 'active' if file == 'dashboard.html' else '',
            'active_students': 'active' if file == 'students.html' else '',
            'active_companies': 'active' if file == 'companies.html' else '',
            'active_placements': 'active' if file == 'placements.html' else '',
            'active_reports': 'active' if file == 'reports.html' else '',
            'active_settings': 'active' if file == 'settings.html' else '',
        }

        new_sidebar = CURRENT_SIDEBAR_TEMPLATE.format(**active).strip()
        pattern = re.compile(r'<!-- Sidebar -->[\s\S]*?<!-- Main Content -->')
        if pattern.search(content):
            content = pattern.sub(f'{new_sidebar}\n\n        <!-- Main Content -->', content)
            with open(file, 'w') as f:
                f.write(content)
            print(f'Updated sidebar in {file}')


# ─────────────────────────────────────────────────────────────────────
# PART 2 (from update_all.py): CSS light theme conversion
# NOTE: already applied — only re-run if reverting to dark theme
# ─────────────────────────────────────────────────────────────────────

def convert_css_to_light_theme(css_file='styles.css'):
    """Converts dark theme CSS variables to light theme equivalents."""
    with open(css_file, 'r') as f:
        css = f.read()

    replacements = [
        ("background-color: #0a0e27;", "background-color: #f4f5f7;"),
        ("background-color: #1a1f3a;", "background-color: #ffffff;"),
        ("background: linear-gradient(135deg, #1a1f3a 0%, #252b4a 100%);", "background: #ffffff;"),
        ("background-color: #252b4a;", "background-color: #f8f9fa;"),
        ("border: 1px solid #2a2f4a;", "border: 1px solid #e1e4e8;"),
        ("border-right: 1px solid #1a1f3a;", "border-right: 1px solid #e1e4e8;"),
        ("border-bottom: 1px solid #2a2f4a;", "border-bottom: 1px solid #e1e4e8;"),
        ("border: 1px solid #3a3f5a;", "border: 1px solid #e1e4e8;"),
        ("color: #fff;", "color: #202124;"),
        ("color: #888;", "color: #5f6368;"),
        ("color: #aaa;", "color: #5f6368;"),
    ]

    for old, new in replacements:
        css = css.replace(old, new)

    with open(css_file, 'w') as f:
        f.write(css)
    print("CSS light theme conversion complete.")


# ─────────────────────────────────────────────────────────────────────
# PART 3: Inject security.js into all HTML pages
# ─────────────────────────────────────────────────────────────────────

CSP_META = '<meta http-equiv="Content-Security-Policy" content="default-src \'self\' https:; script-src \'self\' https://d3js.org https://cdn.jsdelivr.net; style-src \'self\' \'unsafe-inline\' https://fonts.googleapis.com https://cdn.jsdelivr.net; img-src \'self\' https: data:; font-src \'self\' https://fonts.gstatic.com https://cdn.jsdelivr.net; frame-ancestors \'none\';">'

def inject_security():
    """Injects CSP meta tag and security.js script tag into all HTML files."""
    for file in os.listdir('.'):
        if not file.endswith('.html'):
            continue
        with open(file, 'r') as f:
            content = f.read()

        modified = False

        # Add CSP meta tag
        if 'Content-Security-Policy' not in content:
            content = content.replace('<meta charset="UTF-8">', f'<meta charset="UTF-8">\n    {CSP_META}')
            modified = True

        # Add security.js script before closing </body>
        if 'security.js' not in content:
            content = content.replace('</body>', '    <script src="security.js"></script>\n</body>')
            modified = True

        if modified:
            with open(file, 'w') as f:
                f.write(content)
            print(f'Injected security into {file}')


if __name__ == '__main__':
    print("Running security injection...")
    inject_security()
    print("Done.")
