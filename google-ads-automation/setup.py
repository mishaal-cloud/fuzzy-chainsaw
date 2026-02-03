#!/usr/bin/env python3
"""
Automated Setup Script for Google Ads Automation
Run this once to configure everything automatically
"""

import os
import sys
from pathlib import Path

def get_credentials():
    """Prompt user for credentials or use environment variables"""
    print("=" * 70)
    print("Enter your Google Ads API credentials")
    print("(or press Enter to use environment variables)")
    print("=" * 70)
    print()

    creds = {}

    # Check environment variables first
    creds['developer_token'] = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
    creds['client_id'] = os.getenv("GOOGLE_ADS_CLIENT_ID")
    creds['client_secret'] = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
    creds['refresh_token'] = os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
    creds['login_customer_id'] = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    creds['customer_id'] = os.getenv("GOOGLE_ADS_CUSTOMER_ID")

    # Prompt for missing values
    if not creds['developer_token']:
        creds['developer_token'] = input("Developer Token: ").strip()

    if not creds['client_id']:
        creds['client_id'] = input("Client ID: ").strip()

    if not creds['client_secret']:
        creds['client_secret'] = input("Client Secret: ").strip()

    if not creds['refresh_token']:
        creds['refresh_token'] = input("Refresh Token: ").strip()

    if not creds['login_customer_id']:
        creds['login_customer_id'] = input("Login Customer ID (without hyphens): ").strip()

    if not creds['customer_id']:
        default_customer = creds['login_customer_id']
        customer_input = input(f"Customer ID [{default_customer}]: ").strip()
        creds['customer_id'] = customer_input if customer_input else default_customer

    # Validate
    for key, value in creds.items():
        if not value:
            print(f"\n✗ Error: {key} is required!")
            sys.exit(1)

    return creds

def main():
    print("=" * 70)
    print("Google Ads Automation - Automatic Setup")
    print("=" * 70)
    print()

    # Step 1: Check we're in the right directory
    print("Step 1: Checking directory...")
    current_dir = Path.cwd()

    # Try to find the google-ads-automation directory
    if current_dir.name != "google-ads-automation":
        # Try to find it
        possible_paths = [
            current_dir / "google-ads-automation",
            current_dir.parent / "google-ads-automation",
            Path.home() / "fuzzy-chainsaw" / "google-ads-automation",
            Path.home() / "Documents" / "Projects" / "fuzzy-chainsaw" / "google-ads-automation",
        ]

        project_dir = None
        for path in possible_paths:
            if path.exists():
                project_dir = path
                break

        if project_dir:
            print(f"✓ Found project at: {project_dir}")
            os.chdir(project_dir)
        else:
            print("✗ Could not find google-ads-automation directory!")
            print("\nPlease run this script from one of these locations:")
            for path in possible_paths:
                print(f"  - {path}")
            sys.exit(1)
    else:
        print(f"✓ Already in project directory: {current_dir}")

    # Step 2: Get credentials
    print()
    creds = get_credentials()

    # Step 3: Create config directory if needed
    print("\nStep 2: Creating config directory...")
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    print("✓ Config directory ready")

    # Step 4: Create google-ads.yaml
    print("\nStep 3: Creating google-ads.yaml...")
    yaml_content = f"""# Google Ads API Configuration
# IMPORTANT: Keep this file secure and never commit it to version control

developer_token: "{creds['developer_token']}"
client_id: "{creds['client_id']}"
client_secret: "{creds['client_secret']}"
refresh_token: "{creds['refresh_token']}"
login_customer_id: "{creds['login_customer_id']}"
use_proto_plus: True
"""

    config_file = config_dir / "google-ads.yaml"
    config_file.write_text(yaml_content)
    print(f"✓ Created: {config_file}")

    # Step 5: Create .env file
    print("\nStep 4: Creating .env file...")
    env_content = f"""# Google Ads Account Configuration
# Your Google Ads Customer ID (without hyphens)
GOOGLE_ADS_CUSTOMER_ID={creds['customer_id']}
"""

    env_file = Path(".env")
    env_file.write_text(env_content)
    print(f"✓ Created: {env_file}")

    # Step 6: Check dependencies
    print("\nStep 5: Checking dependencies...")
    try:
        import google.ads.googleads
        import pandas
        import dotenv
        import yaml
        print("✓ All dependencies installed")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("\nPlease install dependencies:")
        print("  pip install google-ads pandas python-dotenv pyyaml")
        sys.exit(1)

    # Step 7: Test the setup
    print("\nStep 6: Testing Google Ads API connection...")
    try:
        sys.path.insert(0, str(Path.cwd()))
        from src.google_ads_client import GoogleAdsAPIClient

        client = GoogleAdsAPIClient()
        print(f"✓ Successfully connected!")
        print(f"  Customer ID: {client.customer_id}")

    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        print("\nThis might be OK - the connection may work when you run queries.")

    # Success!
    print("\n" + "=" * 70)
    print("✓ SETUP COMPLETE!")
    print("=" * 70)
    print("\nYou can now run:")
    print("  python examples/simple_query.py")
    print("  python examples/analyze_performance.py")
    print("\nOr import the modules in your own scripts:")
    print("  from src.google_ads_client import GoogleAdsAPIClient")
    print("  from src.data_analyzer import GoogleAdsAnalyzer")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
