import os
import json
import asyncio
import logging
import aiohttp
from typing import List, Dict, Any

from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup, Comment

from utils.token_count import count_tokens
from utils.prompts import CATALOG_PROMPT

logging.basicConfig(
    level=logging.INFO,  # You can change to DEBUG for verbose logs
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CatalogPipeline:
    def __init__(self):
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0.2
        )
        self.prompt_template = PromptTemplate(
            input_variables=["category", "html_blocks"],
            template=CATALOG_PROMPT
        )
        self.chain = self.prompt_template | self.llm | JsonOutputParser()

    async def search_tavily(self, query: str, max_results: int = 3) -> List[str]:
        """
        Performs an async Tavily search and returns top URLs.
        """
        url = "https://api.tavily.com/search"
        headers = {
            "Authorization": f"Bearer {self.tavily_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, json=payload, timeout=15) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    return [r["url"] for r in data.get("results", []) if r.get("url")]
            except Exception as e:
                logger.error(f"[ERROR] Tavily search failed: {e}")
                return []

    async def fetch_html(self, url: str) -> str:
        """
        Uses async Playwright to fetch fully rendered HTML from a given URL.
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, timeout=15000)
                await page.wait_for_timeout(3000)
                content = await page.content()
                await browser.close()
                soup = BeautifulSoup(content, "html.parser")

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
                return content
        except Exception as e:
            logger.error(f"[ERROR] Failed to scrape {url}: {e}")
            return ""

    async def run_pipeline(self, category: str) -> Dict[str, Any]:
        """
        Full pipeline.
        """
        logger.info(f"Searching Tavily for: {category}")
        urls = await self.search_tavily(f"Buy {category} online")

        logger.info(f"Scraping the top urls")
        html_blocks = await asyncio.gather(*(self.fetch_html(url) for url in urls))
        if count_tokens(json.dumps(html_blocks)) > 6000:
            html_blocks = json.dumps(html_blocks)[:15000]

        logger.info("Sending content to LLM for product extraction")
        try:
            result = await self.chain.ainvoke({"category": category, "combined_html": html_blocks})
            return result
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            return {"category": category, "error": str(e)}


# === Run Script ===
if __name__ == "__main__":
    pipeline = CatalogPipeline()

    async def main():
        category = "Compactors"
        result = await pipeline.run_pipeline(category)
        with open(f"{category.lower().replace(' ', '_')}_catalog.json", "w") as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Execution completed for {category}")
        logger.info(f"Result: {result}")

    asyncio.run(main())
