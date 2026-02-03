#!/usr/bin/env python3
"""
Quick Test Script - Verify Google Ads API is working
Run this after setup.py to test your connection
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.google_ads_client import GoogleAdsAPIClient

def main():
    print("=" * 70)
    print("Google Ads API - Quick Connection Test")
    print("=" * 70)
    print()

    try:
        # Initialize client
        print("Initializing Google Ads API client...")
        client = GoogleAdsAPIClient()
        print(f"✓ Client created successfully")
        print(f"  Customer ID: {client.customer_id}")
        print()

        # Try a simple query
        print("Running test query to list campaigns...")
        query = """
            SELECT
                campaign.id,
                campaign.name,
                campaign.status
            FROM campaign
            ORDER BY campaign.name
            LIMIT 5
        """

        results = client.execute_query(query)

        print("✓ Query executed successfully!")
        print()
        print("Your campaigns:")

        count = 0
        for row in results:
            count += 1
            print(f"  {count}. {row.campaign.name}")
            print(f"     ID: {row.campaign.id}")
            print(f"     Status: {row.campaign.status.name}")
            print()

        if count == 0:
            print("  No campaigns found (this is OK if you haven't created any yet)")
            print()

        print("=" * 70)
        print("✓ SUCCESS! Your Google Ads API is working perfectly!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Run: python examples/analyze_performance.py")
        print("  2. Check the reports/ folder for CSV exports")
        print("  3. Customize the examples for your needs")
        print()

    except Exception as e:
        print(f"✗ Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Run setup.py first: python setup.py")
        print("  2. Check your credentials in config/google-ads.yaml")
        print("  3. Verify your customer ID in .env")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
