#!/usr/bin/env python3
"""
Example: Simple Google Ads Query
Demonstrates basic usage of the Google Ads API
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.google_ads_client import GoogleAdsAPIClient


def main():
    print("=" * 60)
    print("Simple Google Ads API Query")
    print("=" * 60)

    # Initialize client
    client = GoogleAdsAPIClient(config_path="config/google-ads.yaml")

    # Example 1: List all campaigns
    print("\n1. Listing All Campaigns")
    print("-" * 60)

    query = """
        SELECT
            campaign.id,
            campaign.name,
            campaign.status
        FROM campaign
        ORDER BY campaign.name
    """

    results = client.execute_query(query)

    print("\nCampaigns in your account:")
    for row in results:
        print(f"  - {row.campaign.name} (ID: {row.campaign.id}, Status: {row.campaign.status.name})")

    # Example 2: Get today's performance
    print("\n\n2. Today's Performance Summary")
    print("-" * 60)

    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")

    query = f"""
        SELECT
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros
        FROM campaign
        WHERE segments.date = '{today}'
    """

    results = client.execute_query_to_list(query)

    total_impressions = sum(row.metrics.impressions for row in results)
    total_clicks = sum(row.metrics.clicks for row in results)
    total_cost = sum(row.metrics.cost_micros for row in results) / 1_000_000

    print(f"\nToday's totals:")
    print(f"  Impressions: {total_impressions:,}")
    print(f"  Clicks: {total_clicks:,}")
    print(f"  Cost: ${total_cost:,.2f}")

    if total_impressions > 0:
        ctr = (total_clicks / total_impressions) * 100
        print(f"  CTR: {ctr:.2f}%")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
