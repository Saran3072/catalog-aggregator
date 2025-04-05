import os
import json
import argparse
import logging
import asyncio
import time

from dotenv import load_dotenv
from modules.leaf_extractor import UNSPSCLeafExtractor
from modules.catalog_search import CatalogPipeline
from modules.catalog_search_agentic import CatalogSearchAgent
from modules.schema_inference import CatalogSchemaDeriver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

class CatalogAggregator:
    def __init__(self, use_agentic: bool = False):
        self.use_agentic = use_agentic
        self.schema_deriver = CatalogSchemaDeriver()
        if self.use_agentic:
            logger.info("Using AGENTIC catalog search.")
            self.catalog_search = CatalogSearchAgent()
        else:
            logger.info("Using catalog search.")
            self.catalog_search = CatalogPipeline()

    def process_category_agentic(self, category: str):
        logger.info(f"Processing category: {category}")
        try:
            results = self.catalog_search.search_and_extract_products(category)

            if results:
                self.schema_deriver.derive_and_store(category, results)
        except Exception as e:
            logger.error(f"Failed to process '{category}': {e}")
    
    async def process_category(self, category: str):
        logger.info(f"Processing category: {category}")
        try:
            results = await self.catalog_search.run_pipeline(category)

            if results:
                self.schema_deriver.derive_and_store(category, results)
        except Exception as e:
            logger.error(f"Failed to process '{category}': {e}")

    async def run(self, root_unspsc_code: str):
        logger.info(f"Extracting leaf nodes from UNSPSC code {root_unspsc_code}")
        extractor = UNSPSCLeafExtractor()
        leaf_nodes = extractor.get_leaf_nodes(root_unspsc_code)

        logger.info(f"Found {len(leaf_nodes)} leaf categories.")

        for node in leaf_nodes:
            await self.process_category(node["category"])
            time.sleep(5)

    def run_agentic(self, root_unspsc_code: str):
        logger.info(f"Extracting leaf nodes from UNSPSC code {root_unspsc_code}")
        extractor = UNSPSCLeafExtractor()
        leaf_nodes = extractor.get_leaf_nodes(root_unspsc_code)

        logger.info(f"Found {len(leaf_nodes)} leaf categories.")

        for node in leaf_nodes:
            self.process_category_agentic(node["category"])
            time.sleep(5)

def main():
    parser = argparse.ArgumentParser(description="UNSPSC Catalog Aggregator")
    parser.add_argument("--agentic", action="store_true", help="Use LangChain Agent-based search", default=False)
    parser.add_argument("--code", help="Root UNSPSC code (e.g., 22000000)", default="22000000")
    args = parser.parse_args()

    aggregator = CatalogAggregator(use_agentic=args.agentic)
    if not args.agentic:
        asyncio.run(aggregator.run(args.code))
    else:
        aggregator.run_agentic(args.code)

if __name__ == "__main__":
    main()