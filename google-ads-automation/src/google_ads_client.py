"""
Google Ads API Client Wrapper
Handles authentication and provides easy access to Google Ads API
"""

import os
from typing import Optional
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from dotenv import load_dotenv


class GoogleAdsAPIClient:
    """Wrapper for Google Ads API client with helper methods"""

    def __init__(self, config_path: str = "config/google-ads.yaml"):
        """
        Initialize the Google Ads API client

        Args:
            config_path: Path to the google-ads.yaml configuration file
        """
        load_dotenv()

        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                "Please copy google-ads.yaml.template to google-ads.yaml "
                "and fill in your credentials."
            )

        self.client = GoogleAdsClient.load_from_storage(config_path)
        self.customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID")

        if not self.customer_id:
            raise ValueError(
                "GOOGLE_ADS_CUSTOMER_ID not found in environment variables.\n"
                "Please set it in your .env file."
            )

    def get_service(self, service_name: str, version: str = "v17"):
        """
        Get a Google Ads API service

        Args:
            service_name: Name of the service (e.g., 'GoogleAdsService')
            version: API version (default: v17)

        Returns:
            Service object
        """
        return self.client.get_service(service_name, version=version)

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
