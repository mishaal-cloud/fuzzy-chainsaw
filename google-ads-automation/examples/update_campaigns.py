#!/usr/bin/env python3
"""
Example: Automated Campaign Updates
Demonstrates how to make automated changes to Google Ads campaigns
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.google_ads_client import GoogleAdsAPIClient
from src.data_analyzer import GoogleAdsAnalyzer
from src.campaign_updater import GoogleAdsUpdater
from datetime import datetime, timedelta


def main():
    print("=" * 60)
    print("Google Ads Automated Updates")
    print("=" * 60)

    # Initialize client, analyzer, and updater
    client = GoogleAdsAPIClient(config_path="config/google-ads.yaml")
    analyzer = GoogleAdsAnalyzer(client)
    updater = GoogleAdsUpdater(client)

    # Set date range (last 30 days)
    date_to = datetime.now().strftime("%Y-%m-%d")
    date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    print(f"\nAnalyzing data from {date_from} to {date_to}")
    print("-" * 60)

    # WARNING: Set DRY_RUN to False to actually make changes
    DRY_RUN = True

    if DRY_RUN:
        print("\n⚠️  DRY RUN MODE - No changes will be made")
    else:
        print("\n🚨 LIVE MODE - Changes will be applied to your account!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return

    print("-" * 60)

    # 1. Pause underperforming keywords
    print("\n1. Identifying and Pausing Underperforming Keywords")
    print("-" * 60)

    keywords_df = analyzer.get_keyword_performance(
        date_from=date_from,
        date_to=date_to,
        min_impressions=500  # Higher threshold for taking action
    )

    if not keywords_df.empty:
        # Define aggressive thresholds
        underperforming = analyzer.identify_underperforming_keywords(
            keywords_df,
            max_cpc=10.0,  # CPC over $10
            min_ctr=0.5,   # CTR under 0.5%
            max_cost_per_conv=100.0  # Cost per conversion over $100
        )

        if not underperforming.empty:
            print(f"\nFound {len(underperforming)} keywords to pause")

            # Show top 5
            print("\nTop 5 keywords by wasted spend:")
            print(underperforming[["keyword", "ctr", "avg_cpc", "cost", "conversions"]]
                  .head()
                  .to_string(index=False))

            if not DRY_RUN:
                # Prepare keyword criteria for pausing
                # Note: You need criterion_id which requires additional query
                print("\n⚠️  Actual pausing requires criterion IDs from your account")
                print("This is a demonstration. In production, you'd query for criterion IDs.")
            else:
                print(f"\n[DRY RUN] Would pause {len(underperforming)} keywords")
        else:
            print("\nNo underperforming keywords found")
    else:
        print("No keyword data available")

    # 2. Add negative keywords
    print("\n\n2. Adding Negative Keywords")
    print("-" * 60)

    # Example: Add common negative keywords to a campaign
    campaign_id = "YOUR_CAMPAIGN_ID"  # Replace with actual campaign ID
    negative_keywords = [
        "free",
        "cheap",
        "download"
    ]

    print(f"\nNegative keywords to add: {', '.join(negative_keywords)}")

    if not DRY_RUN and campaign_id != "YOUR_CAMPAIGN_ID":
        for keyword in negative_keywords:
            updater.add_negative_keyword(
                campaign_id=campaign_id,
                keyword_text=keyword,
                match_type="BROAD"
            )
    else:
        print(f"[DRY RUN] Would add {len(negative_keywords)} negative keywords to campaign {campaign_id}")

    # 3. Update campaign budgets based on performance
    print("\n\n3. Adjusting Campaign Budgets")
    print("-" * 60)

    campaigns_df = analyzer.get_campaign_performance(
        date_from=date_from,
        date_to=date_to
    )

    if not campaigns_df.empty:
        # Calculate ROAS (Return on Ad Spend) if conversion value is available
        campaigns_df["roas"] = campaigns_df["conversion_value"] / campaigns_df["cost"]
        campaigns_df["roas"] = campaigns_df["roas"].fillna(0)

        # Identify high-performing campaigns (ROAS > 3.0)
        high_performers = campaigns_df[campaigns_df["roas"] > 3.0]

        # Identify low-performing campaigns (ROAS < 1.0)
        low_performers = campaigns_df[(campaigns_df["roas"] < 1.0) & (campaigns_df["roas"] > 0)]

        if not high_performers.empty:
            print(f"\nHigh-performing campaigns (ROAS > 3.0): {len(high_performers)}")
            print("\nThese campaigns could benefit from increased budget:")
            print(high_performers[["campaign_name", "cost", "conversion_value", "roas"]]
                  .to_string(index=False))

            if not DRY_RUN:
                print("\n⚠️  Budget updates require current budget + new budget calculation")
                print("This is a demonstration. In production, you'd calculate and apply new budgets.")
            else:
                print("\n[DRY RUN] Would increase budgets by 20% for high performers")

        if not low_performers.empty:
            print(f"\nLow-performing campaigns (ROAS < 1.0): {len(low_performers)}")
            print("\nThese campaigns should have reduced budgets or be paused:")
            print(low_performers[["campaign_name", "cost", "conversion_value", "roas"]]
                  .to_string(index=False))

            if not DRY_RUN:
                for _, campaign in low_performers.iterrows():
                    if campaign["roas"] < 0.5:
                        # Pause very poor performers
                        updater.pause_campaign(
                            campaign_id=str(campaign["campaign_id"]),
                            reason=f"Poor ROAS: {campaign['roas']:.2f}"
                        )
            else:
                print("\n[DRY RUN] Would pause campaigns with ROAS < 0.5")

    # 4. Summary
    print("\n\n" + "=" * 60)
    print("Update Summary")
    print("=" * 60)

    if DRY_RUN:
        print("\n✓ Analysis complete (DRY RUN)")
        print("\nTo apply these changes:")
        print("1. Review the analysis above")
        print("2. Adjust thresholds as needed")
        print("3. Set DRY_RUN = False in the script")
        print("4. Run again to apply changes")
    else:
        print("\n✓ Updates applied successfully")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
