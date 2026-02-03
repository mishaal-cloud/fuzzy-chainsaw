#!/usr/bin/env python3
"""
Example: Analyze Google Ads Performance
Demonstrates how to extract and analyze campaign and keyword data
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.google_ads_client import GoogleAdsAPIClient
from src.data_analyzer import GoogleAdsAnalyzer
from datetime import datetime, timedelta


def main():
    print("=" * 60)
    print("Google Ads Performance Analysis")
    print("=" * 60)

    # Initialize client and analyzer
    client = GoogleAdsAPIClient(config_path="config/google-ads.yaml")
    analyzer = GoogleAdsAnalyzer(client)

    # Set date range (last 30 days)
    date_to = datetime.now().strftime("%Y-%m-%d")
    date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    print(f"\nAnalyzing data from {date_from} to {date_to}")
    print("-" * 60)

    # 1. Get campaign performance
    print("\n1. Campaign Performance Analysis")
    print("-" * 60)
    campaigns_df = analyzer.get_campaign_performance(
        date_from=date_from,
        date_to=date_to
    )

    if not campaigns_df.empty:
        print(f"\nFound {len(campaigns_df)} campaigns")
        print("\nTop 5 campaigns by spend:")
        print(campaigns_df[["campaign_name", "impressions", "clicks", "ctr", "cost", "conversions"]]
              .head()
              .to_string(index=False))

        # Calculate totals
        total_cost = campaigns_df["cost"].sum()
        total_conversions = campaigns_df["conversions"].sum()
        print(f"\nTotal Spend: ${total_cost:,.2f}")
        print(f"Total Conversions: {total_conversions:,.0f}")

        # Export to CSV
        analyzer.export_to_csv(campaigns_df, "campaign_performance.csv")
    else:
        print("No campaign data found")

    # 2. Get keyword performance
    print("\n\n2. Keyword Performance Analysis")
    print("-" * 60)
    keywords_df = analyzer.get_keyword_performance(
        date_from=date_from,
        date_to=date_to,
        min_impressions=100
    )

    if not keywords_df.empty:
        print(f"\nFound {len(keywords_df)} keywords with 100+ impressions")
        print("\nTop 10 keywords by cost:")
        print(keywords_df[["keyword", "match_type", "impressions", "clicks", "ctr", "cost", "conversions"]]
              .head(10)
              .to_string(index=False))

        # Export to CSV
        analyzer.export_to_csv(keywords_df, "keyword_performance.csv")
    else:
        print("No keyword data found")

    # 3. Identify underperforming keywords
    if not keywords_df.empty:
        print("\n\n3. Underperforming Keywords Analysis")
        print("-" * 60)

        # Define thresholds
        max_cpc = 5.0  # Maximum $5 CPC
        min_ctr = 1.0  # Minimum 1% CTR
        max_cost_per_conv = 50.0  # Maximum $50 cost per conversion

        underperforming = analyzer.identify_underperforming_keywords(
            keywords_df,
            max_cpc=max_cpc,
            min_ctr=min_ctr,
            max_cost_per_conv=max_cost_per_conv
        )

        if not underperforming.empty:
            print(f"\nFound {len(underperforming)} underperforming keywords")
            print("\nCriteria:")
            print(f"  - CTR < {min_ctr}%")
            print(f"  - CPC > ${max_cpc}")
            print(f"  - Cost/Conv > ${max_cost_per_conv}")

            print("\nTop 10 underperforming keywords:")
            print(underperforming[["keyword", "ctr", "avg_cpc", "cost", "conversions"]]
                  .head(10)
                  .to_string(index=False))

            # Export to CSV
            analyzer.export_to_csv(underperforming, "underperforming_keywords.csv")

            # Calculate potential savings
            total_waste = underperforming["cost"].sum()
            print(f"\nTotal spent on underperforming keywords: ${total_waste:,.2f}")
        else:
            print("\nNo underperforming keywords found based on criteria")

    # 4. Get ad performance
    print("\n\n4. Ad Performance Analysis")
    print("-" * 60)
    ads_df = analyzer.get_ad_performance(
        date_from=date_from,
        date_to=date_to
    )

    if not ads_df.empty:
        print(f"\nFound {len(ads_df)} ads")

        # Aggregate by ad
        ads_summary = ads_df.groupby(["campaign_name", "ad_id", "ad_type", "ad_status"]).agg({
            "impressions": "sum",
            "clicks": "sum",
            "cost": "sum",
            "conversions": "sum"
        }).reset_index()

        ads_summary["ctr"] = (ads_summary["clicks"] / ads_summary["impressions"] * 100).round(2)

        print("\nTop 10 ads by impressions:")
        print(ads_summary[["campaign_name", "ad_type", "impressions", "clicks", "ctr"]]
              .sort_values("impressions", ascending=False)
              .head(10)
              .to_string(index=False))

        # Export to CSV
        analyzer.export_to_csv(ads_summary, "ad_performance.csv")
    else:
        print("No ad data found")

    print("\n\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
