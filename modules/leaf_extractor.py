import requests
from typing import List, Dict, Optional
import logging

logging.basicConfig(
    level=logging.INFO,  # You can change to DEBUG for verbose logs
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UNSPSCLeafExtractor:
    """
    Class to fetch and extract UNSPSC leaf nodes related to building material categories.
    """

    UNSPSC_API_URL = "https://www.ungm.org/API/UNSPSCs"

    def __init__(self):
        self._all_data = []

    def fetch_unspsc_data(self) -> None:
        """
        Fetches the full UNSPSC code hierarchy from the UNGM API.
        Raises:
            requests.HTTPError: If the API call fails.
        """
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(self.UNSPSC_API_URL, headers=headers)
        response.raise_for_status()
        self._all_data = response.json().get("value", [])

    def _find_id_by_code(self, code: str) -> Optional[str]:
        """
        Finds the internal ID of a given UNSPSC code.
        Args:
            code (str): The UNSPSC code to look for.
        Returns:
            Optional[str]: The internal ID if found, else None.
        """
        for item in self._all_data:
            if item["UNSPSCode"] == code:
                return item["Id"]
        return None

    def _build_children_lookup(self) -> Dict[str, List[Dict]]:
        """
        Builds a mapping of ParentId → list of children.
        Returns:
            Dict[str, List[Dict]]: The parent-to-children map.
        """
        lookup = {}
        for item in self._all_data:
            pid = item["ParentId"]
            lookup.setdefault(pid, []).append(item)
        return lookup

    def get_leaf_nodes(self, root_unspsc_code: str) -> List[Dict[str, str]]:
        """
        Extracts all leaf node UNSPSC codes under a given parent code.
        Args:
            root_unspsc_code (str): The UNSPSC code for the root category.
        Returns:
            List[Dict[str, str]]: List of leaf nodes with `unspsc_code` and `category`.
        """
        if not self._all_data:
            self.fetch_unspsc_data()

        target_id = self._find_id_by_code(root_unspsc_code)
        if target_id is None:
            raise ValueError(f"UNSPSC code '{root_unspsc_code}' not found in the data.")

        children_lookup = self._build_children_lookup()
        leaf_nodes = []

        def _collect_leaf_nodes(parent_id: str):
            children = children_lookup.get(parent_id, [])
            if not children:
                item = next((x for x in self._all_data if x["Id"] == parent_id), None)
                if item:
                    leaf_nodes.append({
                        "unspsc_code": item["UNSPSCode"],
                        "category": item["Title"]
                    })
            else:
                for child in children:
                    _collect_leaf_nodes(child["Id"])

        _collect_leaf_nodes(target_id)
        return leaf_nodes

if __name__ == "__main__":
    extractor = UNSPSCLeafExtractor()
    leaf_nodes = extractor.get_leaf_nodes("22000000")
    for node in leaf_nodes:
        logger.info(node)