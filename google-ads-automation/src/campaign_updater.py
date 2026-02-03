"""
Google Ads Campaign Updater
Makes automated updates to campaigns, ad groups, keywords, and ads
"""

from typing import List, Dict, Optional
from google.ads.googleads.errors import GoogleAdsException
from .google_ads_client import GoogleAdsAPIClient


class GoogleAdsUpdater:
    """Handles updates to Google Ads campaigns"""

    def __init__(self, client: GoogleAdsAPIClient):
        """
        Initialize the updater

        Args:
            client: GoogleAdsAPIClient instance
        """
        self.client = client
        self.customer_id = client.customer_id

    def pause_keywords(self, keyword_criteria: List[Dict[str, str]], reason: str = ""):
        """
        Pause keywords based on criteria

        Args:
            keyword_criteria: List of dicts with 'ad_group_id' and 'criterion_id'
            reason: Reason for pausing (for logging)

        Returns:
            Number of keywords paused
        """
        ad_group_criterion_service = self.client.get_service("AdGroupCriterionService")
        operations = []

        for kw in keyword_criteria:
            ad_group_resource_name = self.client.client.get_service(
                "AdGroupService"
            ).ad_group_path(self.customer_id, kw["ad_group_id"])

            criterion_resource_name = ad_group_criterion_service.ad_group_criterion_path(
                self.customer_id, kw["ad_group_id"], kw["criterion_id"]
            )

            operation = self.client.client.get_type("AdGroupCriterionOperation")
            criterion = operation.update
            criterion.resource_name = criterion_resource_name
            criterion.status = self.client.client.enums.AdGroupCriterionStatusEnum.PAUSED

            operation.update_mask.paths.append("status")
            operations.append(operation)

        if operations:
            try:
                response = ad_group_criterion_service.mutate_ad_group_criteria(
                    customer_id=self.customer_id, operations=operations
                )
                print(f"Paused {len(response.results)} keywords. Reason: {reason}")
                return len(response.results)
            except GoogleAdsException as ex:
                print(f"Failed to pause keywords: {ex}")
                return 0
        return 0

    def update_keyword_bids(
        self,
        keyword_updates: List[Dict[str, any]],
        reason: str = ""
    ):
        """
        Update keyword bid amounts

        Args:
            keyword_updates: List of dicts with 'ad_group_id', 'criterion_id', and 'new_bid_micros'
            reason: Reason for updating (for logging)

        Returns:
            Number of keywords updated
        """
        ad_group_criterion_service = self.client.get_service("AdGroupCriterionService")
        operations = []

        for kw_update in keyword_updates:
            criterion_resource_name = ad_group_criterion_service.ad_group_criterion_path(
                self.customer_id, kw_update["ad_group_id"], kw_update["criterion_id"]
            )

            operation = self.client.client.get_type("AdGroupCriterionOperation")
            criterion = operation.update
            criterion.resource_name = criterion_resource_name
            criterion.cpc_bid_micros = kw_update["new_bid_micros"]

            operation.update_mask.paths.append("cpc_bid_micros")
            operations.append(operation)

        if operations:
            try:
                response = ad_group_criterion_service.mutate_ad_group_criteria(
                    customer_id=self.customer_id, operations=operations
                )
                print(f"Updated bids for {len(response.results)} keywords. Reason: {reason}")
                return len(response.results)
            except GoogleAdsException as ex:
                print(f"Failed to update keyword bids: {ex}")
                return 0
        return 0

    def pause_ads(self, ad_criteria: List[Dict[str, str]], reason: str = ""):
        """
        Pause ads based on criteria

        Args:
            ad_criteria: List of dicts with 'ad_group_id' and 'ad_id'
            reason: Reason for pausing (for logging)

        Returns:
            Number of ads paused
        """
        ad_group_ad_service = self.client.get_service("AdGroupAdService")
        operations = []

        for ad in ad_criteria:
            ad_resource_name = ad_group_ad_service.ad_group_ad_path(
                self.customer_id, ad["ad_group_id"], ad["ad_id"]
            )

            operation = self.client.client.get_type("AdGroupAdOperation")
            ad_group_ad = operation.update
            ad_group_ad.resource_name = ad_resource_name
            ad_group_ad.status = self.client.client.enums.AdGroupAdStatusEnum.PAUSED

            operation.update_mask.paths.append("status")
            operations.append(operation)

        if operations:
            try:
                response = ad_group_ad_service.mutate_ad_group_ads(
                    customer_id=self.customer_id, operations=operations
                )
                print(f"Paused {len(response.results)} ads. Reason: {reason}")
                return len(response.results)
            except GoogleAdsException as ex:
                print(f"Failed to pause ads: {ex}")
                return 0
        return 0

    def update_campaign_budget(
        self,
        campaign_id: str,
        new_budget_micros: int,
        reason: str = ""
    ):
        """
        Update campaign budget

        Args:
            campaign_id: Campaign ID
            new_budget_micros: New budget amount in micros (e.g., 50000000 = $50)
            reason: Reason for updating (for logging)

        Returns:
            True if successful
        """
        campaign_budget_service = self.client.get_service("CampaignBudgetService")

        # First, get the budget resource name for this campaign
        query = f"""
            SELECT campaign.campaign_budget
            FROM campaign
            WHERE campaign.id = {campaign_id}
        """

        results = self.client.execute_query_to_list(query)
        if not results:
            print(f"Campaign {campaign_id} not found")
            return False

        budget_resource_name = results[0].campaign.campaign_budget

        # Update the budget
        operation = self.client.client.get_type("CampaignBudgetOperation")
        budget = operation.update
        budget.resource_name = budget_resource_name
        budget.amount_micros = new_budget_micros

        operation.update_mask.paths.append("amount_micros")

        try:
            response = campaign_budget_service.mutate_campaign_budgets(
                customer_id=self.customer_id, operations=[operation]
            )
            print(f"Updated budget for campaign {campaign_id} to ${new_budget_micros/1_000_000}. Reason: {reason}")
            return True
        except GoogleAdsException as ex:
            print(f"Failed to update campaign budget: {ex}")
            return False

    def pause_campaign(self, campaign_id: str, reason: str = ""):
        """
        Pause a campaign

        Args:
            campaign_id: Campaign ID
            reason: Reason for pausing (for logging)

        Returns:
            True if successful
        """
        campaign_service = self.client.get_service("CampaignService")

        campaign_resource_name = campaign_service.campaign_path(
            self.customer_id, campaign_id
        )

        operation = self.client.client.get_type("CampaignOperation")
        campaign = operation.update
        campaign.resource_name = campaign_resource_name
        campaign.status = self.client.client.enums.CampaignStatusEnum.PAUSED

        operation.update_mask.paths.append("status")

        try:
            response = campaign_service.mutate_campaigns(
                customer_id=self.customer_id, operations=[operation]
            )
            print(f"Paused campaign {campaign_id}. Reason: {reason}")
            return True
        except GoogleAdsException as ex:
            print(f"Failed to pause campaign: {ex}")
            return False

    def enable_campaign(self, campaign_id: str, reason: str = ""):
        """
        Enable a campaign

        Args:
            campaign_id: Campaign ID
            reason: Reason for enabling (for logging)

        Returns:
            True if successful
        """
        campaign_service = self.client.get_service("CampaignService")

        campaign_resource_name = campaign_service.campaign_path(
            self.customer_id, campaign_id
        )

        operation = self.client.client.get_type("CampaignOperation")
        campaign = operation.update
        campaign.resource_name = campaign_resource_name
        campaign.status = self.client.client.enums.CampaignStatusEnum.ENABLED

        operation.update_mask.paths.append("status")

        try:
            response = campaign_service.mutate_campaigns(
                customer_id=self.customer_id, operations=[operation]
            )
            print(f"Enabled campaign {campaign_id}. Reason: {reason}")
            return True
        except GoogleAdsException as ex:
            print(f"Failed to enable campaign: {ex}")
            return False

    def add_negative_keyword(
        self,
        campaign_id: str,
        keyword_text: str,
        match_type: str = "BROAD"
    ):
        """
        Add a negative keyword to a campaign

        Args:
            campaign_id: Campaign ID
            keyword_text: Negative keyword text
            match_type: Match type (BROAD, PHRASE, or EXACT)

        Returns:
            True if successful
        """
        campaign_criterion_service = self.client.get_service("CampaignCriterionService")

        campaign_resource_name = self.client.client.get_service(
            "CampaignService"
        ).campaign_path(self.customer_id, campaign_id)

        operation = self.client.client.get_type("CampaignCriterionOperation")
        criterion = operation.create
        criterion.campaign = campaign_resource_name
        criterion.negative = True
        criterion.keyword.text = keyword_text
        criterion.keyword.match_type = getattr(
            self.client.client.enums.KeywordMatchTypeEnum, match_type
        )

        try:
            response = campaign_criterion_service.mutate_campaign_criteria(
                customer_id=self.customer_id, operations=[operation]
            )
            print(f"Added negative keyword '{keyword_text}' ({match_type}) to campaign {campaign_id}")
            return True
        except GoogleAdsException as ex:
            print(f"Failed to add negative keyword: {ex}")
            return False
