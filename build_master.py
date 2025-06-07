# ---------------------------------------------------------------------------
# build_master.py   –   merge ALL <Company>_leetcode_grouped.html files
# ---------------------------------------------------------------------------
#  • Walks every  DSA/<company>/<Company>_leetcode_grouped.html
#  • Each file is organised as <details><summary>Easy/Medium/Hard …</summary>
#    containing many <li> rows.
#  • <li> anchor text now follows one of two formats:
#        1.  "idx. Title : 1234 | 88.8%"      (older grouped files)
#        2.  "Title : 1234 | 91.3%"           (newer grouped files – no idx.)
#    Both are handled.
#  • Produces  DSA/master_leetcode.html  with collapsible sections, sorted by
#    acceptance rate desc. & company badges.
# ---------------------------------------------------------------------------
#    Run:   python build_master.py   (from folder that contains DSA/)
# ---------------------------------------------------------------------------

import re, html, collections
from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path("DSA")
OUT_FILE = BASE_DIR / "master_leetcode.html"
DIFFS    = ("Easy", "Medium", "Hard")

# --- anchor‑text patterns ---------------------------------------------------
PAT_WITH_IDX = re.compile(r"(\d+)\.\s*(.+?)\s*:\s*(\d+)\s*\|\s*([\d.]+)%")
PAT_NO_IDX   = re.compile(r"(.+?)\s*:\s*(\d+)\s*\|\s*([\d.]+)%")
RAW_FALLBACK = re.compile(r"(\d+)\.\s*(.+)")            # very loose

# ---------------------------------------------------------------------------

def extract_li(li):
    a = li.find("a")
    if not a:
        return None
    href = a.get("href", "#")
    txt  = a.get_text(" ", strip=True)

    # 1️⃣  idx + title + number + %
    m = PAT_WITH_IDX.match(txt)
    if m:
        _idx, title, lc_num, acc = m.groups()
        acceptance = float(acc)
    else:
        # 2️⃣  title + number + %
        m2 = PAT_NO_IDX.match(txt)
        if m2:
            title, lc_num, acc = m2.groups()
            acceptance = float(acc)
        else:                                  # 3️⃣ very old raw pattern
            m3 = RAW_FALLBACK.match(txt)
            if not m3:
                return None
            lc_num, title = m3.groups()
            acc_search = re.search(r"([\d.]+)%", txt)
            acceptance = float(acc_search.group(1)) if acc_search else 0.0

    return dict(name=title, number=lc_num, acceptance=acceptance, href=href)


def parse_company_file(fp, company):
    soup = BeautifulSoup(fp.read_text(encoding="utf-8"), "html.parser")
    for det in soup.find_all("details"):
        diff = det.find("summary").get_text(" ", strip=True).split()[0].capitalize()
        diff = "Easy" if diff.startswith("Easy") else "Hard" if diff.startswith("Hard") else "Medium"
        for li in det.find_all("li"):
            info = extract_li(li)
            if not info:
                continue
            info.update(difficulty=diff, company=company)
            yield info


def collect_all():
    merged = collections.OrderedDict()
    for fp in BASE_DIR.glob("*/*_leetcode_grouped.html"):
        company = fp.parent.name.capitalize()
        for itm in parse_company_file(fp, company):
            key = itm["number"]
            if key not in merged:
                itm["companies"] = {company}
                merged[key] = itm
            else:
                merged[key]["companies"].add(company)
                merged[key]["acceptance"] = max(itm["acceptance"], merged[key]["acceptance"])
    return merged


def group_and_sort(merged):
    groups = {d: [] for d in DIFFS}
    for itm in merged.values():
        groups[itm["difficulty"]].append(itm)
    for d in groups:
        groups[d].sort(key=lambda x: -x["acceptance"])
    return groups


def badge_html(comps):
    return " ".join(
        f"<span style='display:inline-block;background:#eef;border:1px solid #ccd;border-radius:4px;padding:0 4px;margin-right:4px;font-size:.8em'>"
        f"{html.escape(c)}</span>" for c in sorted(comps))


def build_html(groups):
    total = sum(len(v) for v in groups.values())
    parts = [
        "<!DOCTYPE html>",
        "<html><head><meta charset='utf-8'><title>Master LeetCode List</title>",
        "<style>body{font-family:system-ui,Arial;margin:1em}details{margin-bottom:1em;border:1px solid #ccc;border-radius:6px;padding:.5em}summary{font-size:1.25em;font-weight:bold;cursor:pointer}ol{margin-left:1.5em;line-height:1.6}a{text-decoration:none;color:#0366d6}a:hover{text-decoration:underline}</style></head><body>",
        f"<h1>Master LeetCode List – {total} unique problems</h1>",
    ]
    for diff in DIFFS:
        lst = groups[diff]
        parts.append(f"<details {'open' if diff=='Easy' else ''}><summary>{diff} ({len(lst)})</summary><ol>")
        for idx, p in enumerate(lst, 1):
            parts.append(
                f"<li><a href='{html.escape(p['href'])}' target='_blank' rel='noopener'>"
                f"{idx}. {html.escape(p['name'])} : {p['number']} | {p['acceptance']:.1f}%"+ f"</a><br>"
                f"{badge_html(p['companies'])}</li>")
        parts.append("</ol></details>")
    parts.append("</body></html>")
    return "\n".join(parts)

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if not BASE_DIR.exists():
        raise SystemExit("❌ DSA/ directory not found.")

    merged  = collect_all()
    grouped = group_and_sort(merged)
    OUT_FILE.write_text(build_html(grouped), encoding="utf-8")
    print(f"✅  Created {OUT_FILE.resolve()}  ({len(merged)} unique problems)")
