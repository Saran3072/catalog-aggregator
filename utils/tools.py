from playwright.sync_api import sync_playwright
from langchain.tools import tool

@tool
def get_website_html(url: str) -> str:
    """Use Playwright to fetch the fully rendered HTML of a web page for the agent to analyze."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)

            # Give JS time to load (fallback wait)
            page.wait_for_timeout(3000)

            html = page.content()
            browser.close()
            return html[:5000]  # Limit for token budget
    except Exception as e:
        return f"Error fetching {url}: {e}"