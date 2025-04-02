import json
import logging
from typing import List, Dict, Any

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_groq import ChatGroq
from pymongo import MongoClient

from utils.prompts import SCHEMA_INFERENCE_PROMPT

logging.basicConfig(
    level=logging.INFO,  # You can change to DEBUG for verbose logs
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class CatalogSchemaDeriver:
    """
    Phase 3: Infers a common schema for a product category and restructures product data.
    """

    def __init__(self, mongo_uri: str = "mongodb://localhost:27017/", db_name: str = "catalog_db"):
        """
        Initializes the LangChain schema derivation chain and MongoDB connection.

        Args:
            mongo_uri (str): MongoDB URI.
            db_name (str): MongoDB database name.
        """
        self.llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0.2
        )

        self.prompt_template = PromptTemplate(
            input_variables=["category", "products"],
            template=SCHEMA_INFERENCE_PROMPT
        )

        self.chain: RunnableSequence = self.prompt_template | self.llm | JsonOutputParser()

        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[db_name]
        self.collection = self.db["catalogs"]

    def derive_and_store(self, category: str, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Derives the schema and stores the result in MongoDB.

        Args:
            category (str): The product category (e.g., "Aerial lifts").
            products (List[Dict[str, Any]]): Raw product dictionaries.

        Returns:
            Dict[str, Any]: Final structured data with schema + cleaned products.
        """
        try:
            truncated_products = products[:10]  # To avoid token limit
            input_data = {
                "category": category,
                "products": json.dumps(truncated_products)
            }

            result = self.chain.invoke(input_data)

            # Store in MongoDB
            self.collection.insert_one(result)
            logger.info(f"Saved '{category}' with {len(result['products'])} products to MongoDB.")
            return result

        except Exception as e:
            logger.error(f"Error processing category '{category}': {e}")
            return {}

if __name__ == "__main__":
    sample = [
        {
            "supplier": "Genie",
            "url": "https://www.genielift.com/",
            "products": [
                {
                    "name": "Genie Aerial Lifts",
                    "description": "Genie aerial lifts are designed to provide a safe and efficient way to perform tasks at height.",
                    "specs": {
                    "height": "up to 60 ft",
                    "weight": "up to 1000 lbs",
                    "platform": "6 ft x 9 ft"
                    },
                    "price": "Starting at $10,000"
                }
            ]
        },
        {
            "supplier": "JLG",
            "url": "https://www.jlg.com/",
            "products": [
                {
                    "name": "JLG Aerial Lifts",
                    "description": "JLG aerial lifts are designed to provide a safe and efficient way to perform tasks at height.",
                    "specs": {
                    "height": "up to 80 ft",
                    "weight": "up to 1500 lbs",
                    "platform": "8 ft x 12 ft"
                    },
                    "price": "Starting at $15,000"
                }
            ]
        }
    ]


    schema_agent = CatalogSchemaDeriver()

    result = schema_agent.derive_and_store("Aerial lifts", sample)
    logger.info(result)