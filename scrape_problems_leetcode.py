# ---------------------------------------------------------------------------
# scrape_Microsoft_leetcode.py – Playwright script (fetch **all** Microsoft problems)
# ---------------------------------------------------------------------------
#  ✔  Persistent profile (folder: lc_profile) – log in once, scrape forever.
#  ✔  Scrolls the **inner results container** (not the window) until no new
#     rows are added. LeetCode auto‑paginates as you reach the bottom.
#  ✔  Detects the small Cloudflare/"spinner" `<img>` that appears while the
#     next page is loading and waits for it to vanish before continuing.
#  ✔  Generates Microsoft_leetcode.html – every problem title is a hyperlink.
# ---------------------------------------------------------------------------
#  Usage:
#      python scrape_Microsoft_leetcode.py                # (after first login)
#  First run (if cookies missing/expired):
#      – Script opens login page, you solve captcha/2FA, press <Enter>.
#      – Cookies are stored inside lc_profile.
# ---------------------------------------------------------------------------

from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError

OUTPUT_FILE  = Path("Microsoft_leetcode.html")
PROFILE_DIR  = Path("lc_profile")
LOGIN_URL    = "https://leetcode.com/accounts/login/"
LIST_URL     = "https://leetcode.com/company/microsoft/?favoriteSlug=microsoft-six-months"

# Main scrolling container that holds all cards (2025‑06 DOM)
CONTAINER_XPATH = "/html/body/div[1]/div[1]/div[4]/div/div[2]"
# Spinner `<img>` that shows while more rows are fetched
SPINNER_XPATH   = (
    "/html/body/div[1]/div[1]/div[4]/div/div[2]/div[2]/div[2]/div/div/div/div/div/img"
)
SCROLL_PAUSE_MS =5000

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def ensure_all_loaded(page):
    """Scrolls the results container until no new problem links appear."""
    page.wait_for_selector(f"xpath={CONTAINER_XPATH}")
    container = page.query_selector(f"xpath={CONTAINER_XPATH}")

    prev_cnt = -1
    while True:
        # Scroll the element itself to the bottom
        container.evaluate("el => { el.scrollTop = el.scrollHeight; }")
        page.wait_for_timeout(SCROLL_PAUSE_MS)

        # Wait while spinner is visible (LeetCode is loading the next slice)
        try:
            page.wait_for_selector(f"xpath={SPINNER_XPATH}", state="attached", timeout=5000)
            # If found, wait for it to disappear (load complete)
            page.wait_for_selector(f"xpath={SPINNER_XPATH}", state="detached", timeout=10_000)
        except TimeoutError:
            # spinner not present – fine
            print("Spinner not found")
            # pass

        links = container.query_selector_all('a[href*="/problems/"]')
        if len(links) == prev_cnt:
            break  # no new rows → reached end
        prev_cnt = len(links)

    return links


def collect_problems(page):
    links = ensure_all_loaded(page)
    problems = []
    for link in links:
        title = link.inner_text().strip()
        href  = link.get_attribute("href") or ""
        if href.startswith("/"):
            href = f"https://leetcode.com{href}"
        problems.append((title, href))
    return problems


def build_html(problems):
    html = [
        "<html>",
        "<head><meta charset='utf-8'><title>Microsoft LeetCode Problems</title>",
        "<style>body{font-family:system-ui,Arial}ol{line-height:1.6}</style></head>",
        "<body>",
        f"<h1>Microsoft LeetCode Problems ({len(problems)} total)</h1>",
        "<ol>"
    ]
    for title, url in problems:
        html.append(f"  <li><a href='{url}' target='_blank' rel='noopener'>{title}</a></li>")
    html += ["</ol>", "</body>", "</html>"]
    OUTPUT_FILE.write_text("\n".join(html), encoding="utf-8")
    print(f"\n✅  Saved → {OUTPUT_FILE.resolve()}  |  {len(problems)} problems captured")

# ---------------------------------------------------------------------------
# main driver
# ---------------------------------------------------------------------------

def main():
    PROFILE_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            PROFILE_DIR.as_posix(),
            headless=False,
            slow_mo=70,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.new_page()

        print("▶ Opening Microsoft six‑month list …")
        page.goto(LIST_URL, timeout=60_000)

        try:
            page.wait_for_selector(f"xpath={CONTAINER_XPATH}", timeout=8_000)
            print("✅ Already logged in – skipping login step.")
        except TimeoutError:
            print("🔒 Login required – redirecting to login page …")
            page.goto(LOGIN_URL, timeout=60_000)
            print("\n📌 Complete captcha / 2FA, then press <Enter> here …")
            input()
            page.goto(LIST_URL, timeout=60_000)
            page.wait_for_selector(f"xpath={CONTAINER_XPATH}")

        problems = collect_problems(page)
        build_html(problems)
        context.close()


if __name__ == "__main__":
    main()
