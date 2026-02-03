#!/usr/bin/env python3
"""
Helper Script: Generate Google Ads API Refresh Token

This script helps you generate a refresh token for the Google Ads API.
Run this once during initial setup.
"""

import sys

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Error: google-auth-oauthlib not installed")
    print("\nInstall it with:")
    print("  pip install google-auth-oauthlib")
    sys.exit(1)


def main():
    print("=" * 60)
    print("Google Ads API - Refresh Token Generator")
    print("=" * 60)
    print("\nThis script will help you generate a refresh token.")
    print("You'll need:")
    print("  1. Client ID")
    print("  2. Client Secret")
    print("\nGet these from: https://console.cloud.google.com/")
    print("-" * 60)

    # Get credentials from user
    client_id = input("\nEnter your Client ID: ").strip()
    client_secret = input("Enter your Client Secret: ").strip()

    if not client_id or not client_secret:
        print("\nError: Both Client ID and Client Secret are required")
        sys.exit(1)

    # Scopes for Google Ads API
    SCOPES = ["https://www.googleapis.com/auth/adwords"]

    print("\n" + "-" * 60)
    print("Starting OAuth flow...")
    print("Your browser will open for authentication.")
    print("-" * 60)

    try:
        # Create the flow
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://accounts.google.com/o/oauth2/token",
                    "redirect_uris": ["http://localhost:8080/"],
                }
            },
            scopes=SCOPES
        )

        # Run the flow
        credentials = flow.run_local_server(port=8080, prompt='consent')

        print("\n" + "=" * 60)
        print("SUCCESS! Here is your refresh token:")
        print("=" * 60)
        print(f"\n{credentials.refresh_token}\n")
        print("=" * 60)
        print("\nAdd this to your config/google-ads.yaml file")
        print("under the 'refresh_token' field.")
        print("\n⚠️  Keep this token secure and never share it!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during authentication: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(0)
