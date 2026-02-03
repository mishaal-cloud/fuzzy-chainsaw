"""
Google Ads API Client Wrapper
Handles authentication and provides easy access to Google Ads API
"""

import os
from pathlib import Path
from typing import Optional
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from dotenv import load_dotenv


class GoogleAdsAPIClient:
    """Wrapper for Google Ads API client with helper methods"""

    def __init__(self, config_path: str = None):
        """
        Initialize the Google Ads API client

        Args:
            config_path: Path to the google-ads.yaml configuration file
                        If not provided, auto-detects the project root
        """
        # Auto-detect project root
        if config_path is None:
            # Find the google-ads-automation directory
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent  # google-ads-automation/src/file.py -> google-ads-automation/
            config_path = project_root / "config" / "google-ads.yaml"
            env_path = project_root / ".env"

            # Load .env from project root
            load_dotenv(dotenv_path=env_path)
        else:
            load_dotenv()
            config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Expected location: {config_path.parent.parent}/config/google-ads.yaml\n"
                "Run setup.py to create configuration files."
            )

        self.client = GoogleAdsClient.load_from_storage(str(config_path))
        self.customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID")

        if not self.customer_id:
            raise ValueError(
                "GOOGLE_ADS_CUSTOMER_ID not found in environment variables.\n"
                "Please set it in your .env file."
            )

    def get_service(self, service_name: str, version: str = None):
        """
        Get a Google Ads API service

        Args:
            service_name: Name of the service (e.g., 'GoogleAdsService')
            version: API version (default: None, uses latest)

        Returns:
            Service object
        """
        if version:
            return self.client.get_service(service_name, version=version)
        else:
            return self.client.get_service(service_name)

    def execute_query(self, query: str, customer_id: Optional[str] = None):
        """
        Execute a Google Ads Query Language (GAQL) query

        Args:
            query: GAQL query string
            customer_id: Customer ID (uses default if not provided)

        Returns:
            Iterator of result rows
        """
        ga_service = self.get_service("GoogleAdsService")
        customer_id = customer_id or self.customer_id

        try:
            response = ga_service.search(customer_id=customer_id, query=query)
            return response
        except GoogleAdsException as ex:
            print(f"Request failed with status {ex.error.code().name}")
            for error in ex.failure.errors:
                print(f"\tError: {error.message}")
                if error.location:
                    for field_path_element in error.location.field_path_elements:
                        print(f"\t\tOn field: {field_path_element.field_name}")
            raise

    def execute_query_to_list(self, query: str, customer_id: Optional[str] = None):
        """
        Execute query and return results as a list of dictionaries

        Args:
            query: GAQL query string
            customer_id: Customer ID (uses default if not provided)

        Returns:
            List of dictionaries containing query results
        """
        results = []
        response = self.execute_query(query, customer_id)

        for row in response:
            results.append(row)

        return results
