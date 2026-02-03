"""
Google Ads Data Analyzer
Extracts and analyzes performance data from Google Ads
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from .google_ads_client import GoogleAdsAPIClient


class GoogleAdsAnalyzer:
    """Analyzes Google Ads performance data"""

    def __init__(self, client: GoogleAdsAPIClient):
        """
        Initialize the analyzer

        Args:
            client: GoogleAdsAPIClient instance
        """
        self.client = client

    def get_campaign_performance(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        campaign_ids: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get campaign performance metrics

        Args:
            date_from: Start date (YYYY-MM-DD format, defaults to 30 days ago)
            date_to: End date (YYYY-MM-DD format, defaults to today)
            campaign_ids: List of specific campaign IDs to analyze (optional)

        Returns:
            DataFrame with campaign performance metrics
        """
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")

        campaign_filter = ""
        if campaign_ids:
            ids_str = ", ".join(campaign_ids)
            campaign_filter = f"AND campaign.id IN ({ids_str})"

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.cost_per_conversion
            FROM campaign
            WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
            {campaign_filter}
            ORDER BY metrics.cost_micros DESC
        """

        results = self.client.execute_query_to_list(query)
        data = []

        for row in results:
            data.append({
                "campaign_id": row.campaign.id,
                "campaign_name": row.campaign.name,
                "status": row.campaign.status.name,
                "channel_type": row.campaign.advertising_channel_type.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "ctr": row.metrics.ctr,
                "avg_cpc": row.metrics.average_cpc / 1_000_000,  # Convert micros to currency
                "cost": row.metrics.cost_micros / 1_000_000,
                "conversions": row.metrics.conversions,
                "conversion_value": row.metrics.conversions_value,
                "cost_per_conversion": row.metrics.cost_per_conversion / 1_000_000 if row.metrics.cost_per_conversion else 0
            })

        df = pd.DataFrame(data)

        # Aggregate by campaign
        if not df.empty:
            df = df.groupby(["campaign_id", "campaign_name", "status", "channel_type"], as_index=False).sum()
            df["ctr"] = (df["clicks"] / df["impressions"] * 100).round(2) if len(df) > 0 else 0
            df["avg_cpc"] = (df["cost"] / df["clicks"]).round(2) if len(df) > 0 else 0

        return df

    def get_keyword_performance(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_impressions: int = 100
    ) -> pd.DataFrame:
        """
        Get keyword performance metrics

        Args:
            date_from: Start date (YYYY-MM-DD format, defaults to 30 days ago)
            date_to: End date (YYYY-MM-DD format, defaults to today)
            min_impressions: Minimum impressions threshold

        Returns:
            DataFrame with keyword performance metrics
        """
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                ad_group.id,
                ad_group.name,
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                ad_group_criterion.quality_info.quality_score,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_micros,
                metrics.conversions,
                metrics.cost_per_conversion
            FROM keyword_view
            WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
                AND ad_group_criterion.status = 'ENABLED'
                AND metrics.impressions > {min_impressions}
            ORDER BY metrics.cost_micros DESC
        """

        results = self.client.execute_query_to_list(query)
        data = []

        for row in results:
            data.append({
                "campaign_id": row.campaign.id,
                "campaign_name": row.campaign.name,
                "ad_group_id": row.ad_group.id,
                "ad_group_name": row.ad_group.name,
                "keyword": row.ad_group_criterion.keyword.text,
                "match_type": row.ad_group_criterion.keyword.match_type.name,
                "quality_score": row.ad_group_criterion.quality_info.quality_score,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "ctr": row.metrics.ctr,
                "avg_cpc": row.metrics.average_cpc / 1_000_000,
                "cost": row.metrics.cost_micros / 1_000_000,
                "conversions": row.metrics.conversions,
                "cost_per_conversion": row.metrics.cost_per_conversion / 1_000_000 if row.metrics.cost_per_conversion else 0
            })

        df = pd.DataFrame(data)

        # Aggregate by keyword
        if not df.empty:
            df = df.groupby([
                "campaign_id", "campaign_name", "ad_group_id",
                "ad_group_name", "keyword", "match_type"
            ], as_index=False).agg({
                "quality_score": "first",
                "impressions": "sum",
                "clicks": "sum",
                "cost": "sum",
                "conversions": "sum"
            })
            df["ctr"] = (df["clicks"] / df["impressions"] * 100).round(2)
            df["avg_cpc"] = (df["cost"] / df["clicks"]).round(2)
            df["cost_per_conversion"] = (df["cost"] / df["conversions"]).round(2)
            df["cost_per_conversion"] = df["cost_per_conversion"].fillna(0)

        return df

    def identify_underperforming_keywords(
        self,
        df: pd.DataFrame,
        max_cpc: float = None,
        min_ctr: float = 1.0,
        max_cost_per_conv: float = None
    ) -> pd.DataFrame:
        """
        Identify underperforming keywords based on thresholds

        Args:
            df: DataFrame from get_keyword_performance
            max_cpc: Maximum acceptable CPC
            min_ctr: Minimum acceptable CTR (%)
            max_cost_per_conv: Maximum acceptable cost per conversion

        Returns:
            DataFrame with underperforming keywords
        """
        underperforming = df.copy()

        if max_cpc:
            underperforming = underperforming[underperforming["avg_cpc"] > max_cpc]

        if min_ctr:
            underperforming = underperforming[underperforming["ctr"] < min_ctr]

        if max_cost_per_conv:
            underperforming = underperforming[
                (underperforming["cost_per_conversion"] > max_cost_per_conv) &
                (underperforming["conversions"] > 0)
            ]

        return underperforming.sort_values("cost", ascending=False)

    def get_ad_performance(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get ad performance metrics

        Args:
            date_from: Start date (YYYY-MM-DD format, defaults to 30 days ago)
            date_to: End date (YYYY-MM-DD format, defaults to today)

        Returns:
            DataFrame with ad performance metrics
        """
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                ad_group.id,
                ad_group.name,
                ad_group_ad.ad.id,
                ad_group_ad.ad.type,
                ad_group_ad.status,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.cost_micros,
                metrics.conversions
            FROM ad_group_ad
            WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
                AND ad_group_ad.status != 'REMOVED'
            ORDER BY metrics.cost_micros DESC
        """

        results = self.client.execute_query_to_list(query)
        data = []

        for row in results:
            data.append({
                "campaign_id": row.campaign.id,
                "campaign_name": row.campaign.name,
                "ad_group_id": row.ad_group.id,
                "ad_group_name": row.ad_group.name,
                "ad_id": row.ad_group_ad.ad.id,
                "ad_type": row.ad_group_ad.ad.type_.name,
                "ad_status": row.ad_group_ad.status.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "ctr": row.metrics.ctr,
                "cost": row.metrics.cost_micros / 1_000_000,
                "conversions": row.metrics.conversions
            })

        return pd.DataFrame(data)

    def export_to_csv(self, df: pd.DataFrame, filename: str):
        """
        Export DataFrame to CSV

        Args:
            df: DataFrame to export
            filename: Output filename (will be saved to reports/ directory)
        """
        output_path = f"reports/{filename}"
        df.to_csv(output_path, index=False)
        print(f"Report exported to: {output_path}")
        return output_path
