#!/usr/bin/env python3
# Update README block with ASCII-style commit goals summary
import os, sys, requests, json, math, re, subprocess

# === CONFIG ===
USERNAME = "SahilK-027"
# map: year -> goal
YEARS_GOALS = {
    2022: 250,
    2023: 500,
    2024: 1000,
    2025: 1000,
    2026: 2000,
}
README_PATH = "README.md"
START_MARKER = "<!-- COMMITS_LIST_START -->"
END_MARKER   = "<!-- COMMITS_LIST_END -->"
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

# build ASCII-style markdown summary
md_lines = []
for r in rows:
    md_lines.append(f"- **{r['year']}:** {r['commits']:,} / {r['goal']:,}  {r['bar']}  {r['pct']:.1f}% {r['emoji']}")

md_block = "\n".join(md_lines)

# Update README: replace block between markers
if not os.path.exists(README_PATH):
    print(f"{README_PATH} not found.")
    sys.exit(1)

with open(README_PATH, "r", encoding="utf-8") as f:
    readme = f.read()

pattern = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL)
replacement_content = (
    START_MARKER + "\n\n"
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
    subprocess.run(["git", "add", README_PATH], check=True)
    try:
        subprocess.run(["git", "commit", "-m", "chore: update commit goals"], check=True)
        subprocess.run(["git", "push", "origin", "HEAD"], check=True)
        print("README updated and pushed.")
    except subprocess.CalledProcessError:
        print("Nothing to commit or push may have failed.")
