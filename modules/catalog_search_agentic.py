import json
import logging
from typing import List, Dict, Any, Optional

from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate

from utils.tools import get_website_html
from utils.prompts import CATALOG_AGENT_PROMPT

logging.basicConfig(
    level=logging.INFO,  # You can change to DEBUG for verbose logs
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CatalogSearchAgent:
    """
    Agent that performs Tavily-powered search and uses Playwright to scrape supplier websites.
    Returns structured product listings from the search results for a given material category.
    """

    def __init__(self):
        """
        Initializes the LLM agent with Tavily and Playwright tools.
        """

        self.llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            streaming=False,
            temperature=0.2
        )

        self.tools = [
            TavilySearchResults(max_results=2),
            get_website_html
        ]

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", CATALOG_AGENT_PROMPT),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

        self.agent = create_tool_calling_agent(llm=self.llm, tools=self.tools, prompt=self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    def search_and_extract_products(self, material_category: str) -> Optional[List[Dict[str, Any]]]:
        """
        Executes the agent for a given material category and returns structured supplier + product data.
        Args:
            material_category (str): Category of material to search for.
        Returns:
            Optional[List[Dict[str, Any]]]: List of suppliers and their products.
        """
        try:
            response = self.agent_executor.invoke({
                "input": f"Find product details and specifications for: {material_category}"
            })

            # Attempt to parse from the LLM output
            if isinstance(response, str):
                return json.loads(response)
            elif isinstance(response, dict):
                return json.loads(response.get("output", "{}"))
            else:
                return None
        except Exception as e:
            logger.error(f"[ERROR] Agent failed for '{material_category}': {e}")
            return None


if __name__ == "__main__":
    agent = CatalogSearchAgent()
    category = "Aerial lifts"

    results = agent.search_and_extract_products(category)

    if results:
        logger.info(json.dumps(results, indent=2))
    else:
        logger.info("No results found.")