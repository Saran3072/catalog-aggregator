from playwright.sync_api import sync_playwright
from langchain.tools import tool
from bs4 import BeautifulSoup, Comment

from utils.token_count import count_tokens

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
            soup = BeautifulSoup(html, 'html.parser')

            # Remove script and style elements
            for tag in soup(["script", "style"]):
                tag.decompose()

            # Remove comments
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()

            # Optionally remove head, meta, nav, footer etc.
            for tag in soup(["head", "meta", "nav", "footer", "noscript", "iframe"]):
                tag.decompose()

            content = soup.get_text(separator=" ", strip=True)
            browser.close()
            if count_tokens(content) > 6000:
                content = content[:5000]
            return content
    except Exception as e:
        return f"Error fetching {url}: {e}"