#!/usr/bin/env python3
"""
group_Microsoft_html.py
Re-formats Microsoft_leetcode.html into grouped, collapsible sections.
"""

import re, html
from pathlib import Path
from bs4 import BeautifulSoup

SRC_FILE = Path("Microsoft_leetcode.html")           # original file
DST_FILE = Path("Microsoft_leetcode_grouped.html")   # output file

def parse_items(soup):
    """Extract problem info from every <li> in the source HTML."""
    items = []
    for li in soup.find_all("li"):
        a = li.find("a")
        if not a:
            continue

        href = a["href"]
        lines = [ln.strip() for ln in a.get_text("\n").splitlines() if ln.strip()]
        if not lines:
            continue                        # malformed row

        # line 0 -> "123. Two Sum"
        m = re.match(r"(\d+)\.\s*(.+)", lines[0])
        if not m:
            continue

        number = m.group(1)
        name   = m.group(2)

        # acceptance %
        acc_line = next((ln for ln in lines if ln.endswith("%")), "0%")
        acceptance = float(acc_line.rstrip("%"))

        # difficulty
        diff_line = next((ln for ln in lines
                          if ln.lower().startswith(("easy", "med", "hard"))),
                         "Unknown")
        if diff_line.lower().startswith("easy"):
            diff = "Easy"
        elif diff_line.lower().startswith("hard"):
            diff = "Hard"
        else:
            diff = "Medium"                 # default / “Med.” variations

        items.append(
            dict(href=href, name=name, number=number,
                 acceptance=acceptance, difficulty=diff)
        )
    return items

def build_html(groups):
    """Return the final HTML string."""
    total = sum(len(v) for v in groups.values())
    out = [
        "<!DOCTYPE html>",
        "<html>",
        "<head><meta charset='utf-8'><title>Microsoft LeetCode – Grouped</title>",
        "<style>",
        "body{font-family:system-ui,Arial;margin:1em}",
        "details{margin-bottom:1em;border:1px solid #ccc;border-radius:6px;padding:.5em}",
        "summary{font-size:1.25em;font-weight:bold;cursor:pointer}",
        "ol{margin-left:1.5em;line-height:1.6}",
        "a{text-decoration:none;color:#0366d6}",
        "a:hover{text-decoration:underline}",
        "</style></head><body>",
        f"<h1>Microsoft LeetCode – {total} problems</h1>",
    ]

    for diff in ("Easy", "Medium", "Hard"):
        lst = groups[diff]
        out.append(f"<details {'open' if diff=='Easy' else ''}>"
                   f"<summary>{diff} ({len(lst)})</summary><ol>")
        for idx, itm in enumerate(lst, 1):
            out.append(
                f"<li><a href='{html.escape(itm['href'])}' "
                f"target='_blank' rel='noopener'>"
                f"{html.escape(itm['name'])} : "
                f"{itm['number']} | {itm['acceptance']:.1f}%"
                "</a></li>"
            )
        out.extend(["</ol></details>"])

    out.extend(["</body></html>"])
    return "\n".join(out)

def main():
    if not SRC_FILE.exists():
        raise SystemExit(f"❌ {SRC_FILE} not found.")

    soup   = BeautifulSoup(SRC_FILE.read_text(encoding="utf-8"), "html.parser")
    items  = parse_items(soup)

    # group & sort
    groups = {"Easy": [], "Medium": [], "Hard": []}
    for itm in items:
        groups[itm["difficulty"]].append(itm)
    for diff in groups:
        groups[diff].sort(key=lambda x: -x["acceptance"])

    DST_FILE.write_text(build_html(groups), encoding="utf-8")
    print(f"✅ Created {DST_FILE.resolve()}")

if __name__ == "__main__":
    main()
