#!/usr/bin/env python3
# Update README block with a generated SVG card and markdown fallback list
import os, sys, requests, json, math, re, subprocess
from datetime import datetime

# === CONFIG ===
USERNAME = "Sahilk-027"
# map: year -> goal
YEARS_GOALS = {
    2022: 250,
    2023: 500,
    2024: 1000,
    2025: 1000,
    2026: 2000,
}
README_PATH = "README.md"
SVG_PATH = "assets/commit-goals.svg"
START_MARKER = "<!-- COMMITS_LIST_START -->"
END_MARKER   = "<!-- COMMITS_LIST_END -->"
# visual options
SVG_WIDTH = 900
ROW_HEIGHT = 72
PADDING = 20
BAR_WIDTH = 520
BAR_HEIGHT = 18
# =================

token = os.environ.get("GITHUB_TOKEN")
if not token:
    print("GITHUB_TOKEN is required.")
    sys.exit(1)

def query_commits_for_year(login, year):
    from_iso = f"{year}-01-01T00:00:00Z"
    to_iso   = f"{year}-12-31T23:59:59Z"
    query = """
    query ($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
        }
      }
    }
    """
    resp = requests.post(
        "https://api.github.com/graphql",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"query": query, "variables": {"login": login, "from": from_iso, "to": to_iso}},
        timeout=20
    )
    if resp.status_code != 200:
        raise RuntimeError(f"GraphQL failed {resp.status_code}: {resp.text}")
    data = resp.json()
    try:
        n = data["data"]["user"]["contributionsCollection"]["totalCommitContributions"]
        return int(n or 0)
    except Exception:
        print("Unexpected GraphQL response:", json.dumps(data, indent=2))
        raise

# collect data
rows = []
for year, goal in sorted(YEARS_GOALS.items()):
    commits = query_commits_for_year(USERNAME, year)
    pct = (commits / goal) * 100 if goal else 0.0
    # emoji thresholds
    if pct >= 100:
        emoji = "☑️"
    elif pct >= 50:
        emoji = "🔨"
    else:
        emoji = "🚧"
    # textual progress bar (20 blocks) for fallback md
    blocks = 20
    filled = int(min(blocks, math.floor((commits / goal) * blocks))) if goal else 0
    bar = "█" * filled + "░" * (blocks - filled)
    rows.append({
        "year": year,
        "goal": goal,
        "commits": commits,
        "pct": pct,
        "emoji": emoji,
        "bar": bar
    })

# build markdown fallback
md_lines = []
for r in rows:
    md_lines.append(f"- **{r['year']}:** {r['commits']:,} / {r['goal']:,}  {r['bar']}  {r['pct']:.1f}% {r['emoji']}")

md_block = "\n".join(md_lines)

# build SVG
num_rows = len(rows)
svg_height = PADDING*2 + num_rows * ROW_HEIGHT
now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

svg_parts = []
svg_parts.append(f'<svg width="{SVG_WIDTH}" height="{svg_height}" viewBox="0 0 {SVG_WIDTH} {svg_height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Yearly commit goals">')
svg_parts.append('<style>')
svg_parts.append('  .title { font: 600 20px/1 "Segoe UI", Roboto, "Helvetica Neue", Arial; fill:#0f172a; }')
svg_parts.append('  .subtitle { font: 400 12px/1 "Segoe UI", Roboto, Arial; fill:#475569; }')
svg_parts.append('  .year { font: 700 16px/1 "Segoe UI", Roboto, Arial; fill:#0f172a; }')
svg_parts.append('  .meta { font: 400 13px/1 "Segoe UI", Roboto, Arial; fill:#0f172a; }')
svg_parts.append('</style>')

# background
svg_parts.append(f'<rect width="100%" height="100%" rx="12" fill="#f8fafc" />')
# header
svg_parts.append(f'<text x="{PADDING}" y="{PADDING+18}" class="title">Yearly Commit Goals</text>')
svg_parts.append(f'<text x="{SVG_WIDTH - PADDING}" y="{PADDING+18}" class="subtitle" text-anchor="end">Updated: {esc(now)}</text>')

# rows
start_y = PADDING + 42
for i, r in enumerate(rows):
    y = start_y + i*ROW_HEIGHT
    year_x = PADDING
    text_x = year_x + 80
    bar_x = text_x + 200
    # row background (alternating)
    if i % 2 == 0:
        svg_parts.append(f'<rect x="{PADDING}" y="{y-12}" rx="8" width="{SVG_WIDTH - PADDING*2}" height="{ROW_HEIGHT-12}" fill="#ffffff" />')
    # year
    svg_parts.append(f'<text x="{year_x}" y="{y+6}" class="year">{r["year"]}</text>')
    # commits meta
    svg_parts.append(f'<text x="{text_x}" y="{y+6}" class="meta">{r["commits"]:,} / {r["goal"]:,} • {r["pct"]:.1f}% {r["emoji"]}</text>')
    # bar bg
    svg_parts.append(f'<rect x="{bar_x}" y="{y-4}" rx="6" width="{BAR_WIDTH}" height="{BAR_HEIGHT}" fill="#e6eef7" />')
    # filled part
    fill_w = int(max(0, min(BAR_WIDTH, (r["commits"]/r["goal"]) * BAR_WIDTH))) if r["goal"] else 0
    # color by pct
    if r["pct"] >= 100:
        fill_color = "#16a34a"   # green
    elif r["pct"] >= 50:
        fill_color = "#f59e0b"   # amber
    else:
        fill_color = "#ef4444"   # red
    svg_parts.append(f'<rect x="{bar_x}" y="{y-4}" rx="6" width="{fill_w}" height="{BAR_HEIGHT}" fill="{fill_color}" />')

svg_parts.append('</svg>')
svg_content = "\n".join(svg_parts)

# ensure assets dir
os.makedirs(os.path.dirname(SVG_PATH), exist_ok=True)
with open(SVG_PATH, "w", encoding="utf-8") as f:
    f.write(svg_content)

# Update README: replace block between markers
if not os.path.exists(README_PATH):
    print(f"{README_PATH} not found.")
    sys.exit(1)

with open(README_PATH, "r", encoding="utf-8") as f:
    readme = f.read()

pattern = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL)
replacement_content = (
    START_MARKER + "\n\n"
    f"![Yearly Commit Goals]({SVG_PATH})\n\n"
    "### Quick (text) summary\n\n"
    + md_block + "\n\n"
    + END_MARKER
)

if not pattern.search(readme):
    print("Markers not found. Please add these lines to your README.md:\n")
    print(START_MARKER + "\\n...\\n" + END_MARKER)
    sys.exit(1)

new_readme = pattern.sub(replacement_content, readme)

if new_readme == readme:
    print("No README changes needed.")
else:
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_readme)
    # commit & push
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], check=True)
    subprocess.run(["git", "add", README_PATH, SVG_PATH], check=True)
    try:
        subprocess.run(["git", "commit", "-m", "chore: update commit goals card"], check=True)
        subprocess.run(["git", "push", "origin", "HEAD"], check=True)
        print("README and SVG updated and pushed.")
    except subprocess.CalledProcessError:
        print("Nothing to commit or push may have failed.")
