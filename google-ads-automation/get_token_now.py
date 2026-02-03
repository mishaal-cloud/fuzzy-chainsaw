#!/usr/bin/env python3
"""
Quick Refresh Token Generator
Uses the provided credentials to generate a refresh token
"""

from google_auth_oauthlib.flow import InstalledAppFlow

# Replace these with your actual credentials
CLIENT_ID = "YOUR_CLIENT_ID.apps.googleusercontent.com"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"

# Google Ads API scope
SCOPES = ["https://www.googleapis.com/auth/adwords"]

print("=" * 70)
print("Google Ads API - Refresh Token Generator")
print("=" * 70)
print("\nStarting OAuth flow...")
print("Your browser will open. Please:")
print("  1. Sign in with your Google Ads account")
print("  2. Click 'Allow' to authorize access")
print("  3. Wait for confirmation")
print("-" * 70)

try:
    # Create the OAuth flow
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://accounts.google.com/o/oauth2/token",
                "redirect_uris": ["http://localhost:8080/"],
            }
        },
        scopes=SCOPES
    )

    # Run the flow - this will open a browser
    credentials = flow.run_local_server(port=8080, prompt='consent')

    print("\n" + "=" * 70)
    print("✓ SUCCESS! Here is your refresh token:")
    print("=" * 70)
    print()
    print(credentials.refresh_token)
    print()
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Copy the token above")
    print("  2. We'll add it to config/google-ads.yaml")
    print("=" * 70)

except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nTroubleshooting:")
    print("  - Make sure you added your email as a test user in OAuth consent screen")
    print("  - Check that port 8080 is available")
    print("  - Try running in an environment with browser access")
