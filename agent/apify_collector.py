"""Apify web scraping integration for collecting travel data."""

import os
import logging
from datetime import datetime
from apify_client import ApifyClient
from models.schemas import TravelPreferences

logger = logging.getLogger(__name__)


class ApifyCollector:
    """Collects travel data from the web using Apify's Google Search Scraper."""

    def __init__(self):
        """Initialize the Apify client with token from environment."""
        self.api_token = os.getenv("APIFY_API_TOKEN")
        if not self.api_token:
            logger.warning("APIFY_API_TOKEN not set - data collection will fail")
        self.client = ApifyClient(self.api_token) if self.api_token else None

    def collect_travel_data(
        self,
        destination: str,
        preferences: TravelPreferences | None = None,
    ) -> list[dict]:
        """
        Collect travel data by running Google Search Scraper on Apify.

        Args:
            destination: The travel destination to research.
            preferences: Optional travel preferences to tailor search queries.

        Returns:
            A list of result dicts with keys: title, url, description.
            Returns empty list on failure.
        """
        if not self.client:
            logger.error("Apify client not initialized - missing API token")
            return []

        queries = self._build_queries(destination, preferences)
        # Limit to max 3 queries to keep it fast
        queries = queries[:3]

        logger.info(f"Running Apify search with {len(queries)} queries for '{destination}'")

        try:
            run_input = {
                "queries": "\n".join(queries),
                "maxPagesPerQuery": 1,
                "resultsPerPage": 5,
                "mobileResults": False,
                "languageCode": "",
                "maxConcurrency": 5,
                "saveHtml": False,
                "saveHtmlToKeyValueStore": False,
                "includeUnfilteredResults": False,
                "customDataFunction": "async ({ input, $, request, response, html }) => { return { title: $('title').text() }; }",
            }

            # Run the Google Search Scraper actor
            run = self.client.actor("apify/google-search-scraper").call(run_input=run_input)

            if not run:
                logger.warning("Apify actor run returned None")
                return []

            # In apify-client v3, run is a Run object, not a dict
            default_dataset_id = getattr(run, "default_dataset_id", None) or run.get("defaultDatasetId") if isinstance(run, dict) else run.default_dataset_id

            # Fetch results from the dataset
            dataset_items = list(
                self.client.dataset(default_dataset_id).iterate_items()
            )

            logger.info(f"Collected {len(dataset_items)} raw results from Apify")

            # Parse and normalize results
            results = self._parse_results(dataset_items)
            logger.info(f"Parsed {len(results)} usable results")

            return results

        except Exception as e:
            logger.error(f"Apify data collection failed: {str(e)}")
            return []

    def _build_queries(
        self,
        destination: str,
        preferences: TravelPreferences | None,
    ) -> list[str]:
        """Build search queries based on destination and preferences."""
        current_year = datetime.now().year

        queries = [
            f"best things to do in {destination}",
            f"best restaurants in {destination}",
            f"neighborhoods to explore in {destination}",
            f"{destination} travel tips {current_year}",
        ]

        # Add preference-based queries
        if preferences:
            if preferences.trip_length:
                queries.append(f"{destination} {preferences.trip_length} itinerary")
            if preferences.budget_level:
                queries.append(
                    f"{destination} {preferences.budget_level.value} travel guide"
                )
            if preferences.travel_style:
                style = preferences.travel_style[0]
                queries.append(f"{destination} {style} travel")

        return queries

    def _parse_results(self, dataset_items: list[dict]) -> list[dict]:
        """Parse Apify dataset items into normalized result dicts."""
        results = []

        for item in dataset_items:
            # Google Search Scraper returns organic results
            organic_results = item.get("organicResults", [])

            for result in organic_results:
                parsed = {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "description": result.get("description", result.get("snippet", "")),
                }

                # Only include results with meaningful content
                if parsed["title"] and parsed["description"]:
                    results.append(parsed)

        # Limit total results to avoid overwhelming the prompt
        return results[:15]
