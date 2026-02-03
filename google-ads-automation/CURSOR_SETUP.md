# Setup with Cursor (The Easy Way)

## 1. Open in Cursor

```bash
cd ~/fuzzy-chainsaw
cursor .
```

Or just drag the `fuzzy-chainsaw` folder onto Cursor.

## 2. Run Automated Setup

Open Cursor's terminal (`` Ctrl+` `` or `` Cmd+` ``) and run:

```bash
cd google-ads-automation
python3 setup.py
```

This automatically:
- ✓ Creates your config files
- ✓ Sets up credentials
- ✓ Validates everything
- ✓ Tests the connection

## 3. Test It

```bash
python3 quick_test.py
```

This will:
- Connect to Google Ads API
- List your campaigns
- Confirm everything works

## 4. Start Using It

**Option A: Run the examples**
```bash
python3 examples/simple_query.py
python3 examples/analyze_performance.py
```

**Option B: Use in your own code**

Create a new Python file in Cursor and add:

```python
from src.google_ads_client import GoogleAdsAPIClient
from src.data_analyzer import GoogleAdsAnalyzer

# Connect
client = GoogleAdsAPIClient()
analyzer = GoogleAdsAnalyzer(client)

# Get campaign performance
campaigns = analyzer.get_campaign_performance(
    date_from="2025-01-01",
    date_to="2025-01-31"
)

print(campaigns)
```

Then click the **▶ Run** button in Cursor!

## That's It!

No more terminal gymnastics. Cursor handles everything.

---

## Troubleshooting in Cursor

If you get import errors, install dependencies in Cursor's terminal:

```bash
pip3 install google-ads pandas python-dotenv pyyaml
```

If you want a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
pip install google-ads pandas python-dotenv pyyaml
```
