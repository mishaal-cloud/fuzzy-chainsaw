# Google Ads Automation Framework

Automate Google Ads analysis and updates using the Google Ads API. This framework allows you to:

- Extract and analyze campaign, keyword, and ad performance data
- Identify underperforming keywords and ads
- Automatically pause/enable campaigns and keywords
- Update budgets and bids programmatically
- Add negative keywords
- Export reports to CSV

## Features

### Data Analysis
- **Campaign Performance**: Get comprehensive metrics for all campaigns
- **Keyword Analysis**: Identify high and low performers
- **Ad Performance**: Track ad effectiveness
- **Custom Thresholds**: Define your own performance criteria
- **Export to CSV**: Save reports for further analysis

### Automated Updates
- **Pause Underperformers**: Automatically pause keywords/ads based on criteria
- **Budget Management**: Increase/decrease budgets based on ROAS
- **Bid Adjustments**: Update keyword bids programmatically
- **Negative Keywords**: Add negative keywords to campaigns
- **Campaign Control**: Pause/enable campaigns based on performance

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- A Google Ads account with API access
- Google Ads Developer Token

### 2. Install Dependencies

```bash
cd google-ads-automation
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Get Google Ads API Credentials

Follow these steps to get your API credentials:

#### Step 1: Get a Developer Token
1. Go to [Google Ads API Center](https://ads.google.com/aw/apicenter)
2. Sign in with your Google Ads account
3. Request a developer token (approval may take 24-48 hours)

#### Step 2: Create OAuth 2.0 Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Ads API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Configure consent screen if needed
6. Select "Desktop app" as application type
7. Note down your `Client ID` and `Client Secret`

#### Step 3: Generate Refresh Token
1. Install the Google Ads API authentication helper:
   ```bash
   pip install google-auth-oauthlib
   ```

2. Run this Python script to generate a refresh token:
   ```python
   from google_auth_oauthlib.flow import InstalledAppFlow

   CLIENT_ID = "YOUR_CLIENT_ID"
   CLIENT_SECRET = "YOUR_CLIENT_SECRET"
   SCOPES = ["https://www.googleapis.com/auth/adwords"]

   flow = InstalledAppFlow.from_client_config(
       {
           "installed": {
               "client_id": CLIENT_ID,
               "client_secret": CLIENT_SECRET,
               "auth_uri": "https://accounts.google.com/o/oauth2/auth",
               "token_uri": "https://accounts.google.com/o/oauth2/token",
           }
       },
       scopes=SCOPES
   )

   credentials = flow.run_local_server(port=8080)
   print(f"Refresh Token: {credentials.refresh_token}")
   ```

3. Save the refresh token

### 4. Configure the Application

#### Create Configuration File
```bash
cd google-ads-automation
cp config/google-ads.yaml.template config/google-ads.yaml
```

Edit `config/google-ads.yaml` and fill in your credentials:

```yaml
developer_token: "YOUR_DEVELOPER_TOKEN"
client_id: "YOUR_CLIENT_ID.apps.googleusercontent.com"
client_secret: "YOUR_CLIENT_SECRET"
refresh_token: "YOUR_REFRESH_TOKEN"
login_customer_id: "1234567890"  # Your Manager Account ID (without hyphens)
use_proto_plus: True
```

#### Create Environment File
```bash
cp .env.example .env
```

Edit `.env` and set your customer ID:

```bash
GOOGLE_ADS_CUSTOMER_ID=1234567890  # Your Google Ads Account ID (without hyphens)
```

## Usage Examples

### 1. Simple Query (Test Your Setup)

```bash
python examples/simple_query.py
```

This will list all campaigns and today's performance. Perfect for testing your setup.

### 2. Comprehensive Performance Analysis

```bash
python examples/analyze_performance.py
```

This script will:
- Analyze campaign performance for the last 30 days
- Identify top-performing and underperforming keywords
- Export reports to CSV files in the `reports/` directory
- Show ad performance metrics

### 3. Automated Campaign Updates

```bash
python examples/update_campaigns.py
```

This script demonstrates automated updates:
- Pause underperforming keywords
- Add negative keywords
- Adjust campaign budgets based on ROAS
- Pause low-performing campaigns

**Note**: By default, this runs in DRY_RUN mode (no changes made). To apply changes, edit the script and set `DRY_RUN = False`.

## Custom Automation Scripts

### Example: Pause Low-CTR Keywords

```python
from src.google_ads_client import GoogleAdsAPIClient
from src.data_analyzer import GoogleAdsAnalyzer
from src.campaign_updater import GoogleAdsUpdater

# Initialize
client = GoogleAdsAPIClient()
analyzer = GoogleAdsAnalyzer(client)
updater = GoogleAdsUpdater(client)

# Get keyword data
keywords = analyzer.get_keyword_performance(
    date_from="2026-01-01",
    date_to="2026-01-31",
    min_impressions=1000
)

# Find low performers
low_ctr = keywords[keywords["ctr"] < 0.5]  # CTR < 0.5%

# Pause them (requires criterion_id)
for _, kw in low_ctr.iterrows():
    print(f"Would pause: {kw['keyword']} (CTR: {kw['ctr']}%)")
```

### Example: Increase Budget for High ROAS Campaigns

```python
from src.google_ads_client import GoogleAdsAPIClient
from src.data_analyzer import GoogleAdsAnalyzer
from src.campaign_updater import GoogleAdsUpdater

# Initialize
client = GoogleAdsAPIClient()
analyzer = GoogleAdsAnalyzer(client)
updater = GoogleAdsUpdater(client)

# Get campaign performance
campaigns = analyzer.get_campaign_performance(
    date_from="2026-01-01",
    date_to="2026-01-31"
)

# Calculate ROAS
campaigns["roas"] = campaigns["conversion_value"] / campaigns["cost"]

# Increase budget for high ROAS campaigns
high_performers = campaigns[campaigns["roas"] > 5.0]

for _, campaign in high_performers.iterrows():
    new_budget = int(campaign["cost"] * 1.5 * 1_000_000)  # Increase by 50%
    updater.update_campaign_budget(
        campaign_id=str(campaign["campaign_id"]),
        new_budget_micros=new_budget,
        reason=f"High ROAS: {campaign['roas']:.2f}"
    )
```

## Project Structure

```
google-ads-automation/
├── config/
│   ├── google-ads.yaml.template   # Configuration template
│   └── google-ads.yaml            # Your credentials (gitignored)
├── src/
│   ├── __init__.py
│   ├── google_ads_client.py       # API client wrapper
│   ├── data_analyzer.py           # Data extraction and analysis
│   └── campaign_updater.py        # Update operations
├── examples/
│   ├── simple_query.py            # Basic API usage
│   ├── analyze_performance.py    # Comprehensive analysis
│   └── update_campaigns.py       # Automated updates
├── reports/                       # Generated CSV reports
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

## API Reference

### GoogleAdsAPIClient

Main client for interacting with Google Ads API.

```python
client = GoogleAdsAPIClient(config_path="config/google-ads.yaml")
service = client.get_service("GoogleAdsService")
results = client.execute_query(gaql_query)
```

### GoogleAdsAnalyzer

Extracts and analyzes performance data.

**Methods:**
- `get_campaign_performance()` - Get campaign metrics
- `get_keyword_performance()` - Get keyword metrics
- `get_ad_performance()` - Get ad metrics
- `identify_underperforming_keywords()` - Find keywords below thresholds
- `export_to_csv()` - Export DataFrame to CSV

### GoogleAdsUpdater

Makes updates to campaigns, keywords, and ads.

**Methods:**
- `pause_keywords()` - Pause keywords
- `update_keyword_bids()` - Update bids
- `pause_ads()` - Pause ads
- `update_campaign_budget()` - Update budget
- `pause_campaign()` - Pause campaign
- `enable_campaign()` - Enable campaign
- `add_negative_keyword()` - Add negative keyword

## Best Practices

1. **Always Test First**: Use DRY_RUN mode before making changes
2. **Set Conservative Thresholds**: Start with conservative performance thresholds
3. **Monitor Results**: Review changes after automation runs
4. **Use Negative Keywords**: Regularly add negative keywords to reduce wasted spend
5. **Schedule Wisely**: Run analysis during off-peak hours
6. **Backup Data**: Export reports before making bulk changes
7. **Gradual Rollout**: Test on small campaigns first

## Scheduling Automation

### Using Cron (Linux/Mac)

Edit your crontab:
```bash
crontab -e
```

Add a line to run daily at 2 AM:
```cron
0 2 * * * cd /path/to/google-ads-automation && source venv/bin/activate && python examples/update_campaigns.py >> logs/automation.log 2>&1
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily, weekly, etc.)
4. Action: Start a program
5. Program: `C:\path\to\venv\Scripts\python.exe`
6. Arguments: `examples\update_campaigns.py`
7. Start in: `C:\path\to\google-ads-automation`

## Troubleshooting

### "Configuration file not found"
- Make sure you copied `google-ads.yaml.template` to `google-ads.yaml`
- Check that the file is in the `config/` directory

### "GOOGLE_ADS_CUSTOMER_ID not found"
- Create a `.env` file from `.env.example`
- Add your customer ID without hyphens

### "Authentication failed"
- Verify your credentials in `google-ads.yaml`
- Make sure your refresh token is valid
- Check that your developer token is approved

### "No data returned"
- Verify your customer ID is correct
- Check that your account has campaigns with data
- Try a wider date range

### Rate Limiting
- The API has rate limits (queries per second)
- Use batch operations when possible
- Add delays between operations if hitting limits

## Security Notes

- **Never commit** `google-ads.yaml` or `.env` files to version control
- Keep your developer token and credentials secure
- Use environment variables for sensitive data in production
- Review the `.gitignore` file to ensure credentials are excluded

## Resources

- [Google Ads API Documentation](https://developers.google.com/google-ads/api/docs/start)
- [Google Ads Query Language (GAQL)](https://developers.google.com/google-ads/api/docs/query/overview)
- [Python Client Library](https://github.com/googleads/google-ads-python)
- [API Forum](https://groups.google.com/g/adwords-api)

## Support

For issues with:
- **This framework**: Check the examples and documentation
- **Google Ads API**: Visit the [official forum](https://groups.google.com/g/adwords-api)
- **API credentials**: Contact Google Ads support

## License

This is a demonstration framework. Customize and use according to your needs.

## Contributing

Feel free to extend this framework with:
- Additional analysis methods
- More sophisticated update logic
- Integration with other tools (Slack, email notifications, etc.)
- Performance optimizations
