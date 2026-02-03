# Generate Refresh Token on Your Local Machine

Since the OAuth flow requires browser access, you need to run this on your local computer.

## Quick Setup (5 minutes)

### Step 1: Install Python Package
```bash
pip install google-auth-oauthlib
```

### Step 2: Create and Run This Script

Save this as `get_token.py`:

```python
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_ID = "YOUR_CLIENT_ID.apps.googleusercontent.com"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
SCOPES = ["https://www.googleapis.com/auth/adwords"]

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

credentials = flow.run_local_server(port=8080, prompt='consent')
print("\n=== YOUR REFRESH TOKEN ===")
print(credentials.refresh_token)
print("=========================\n")
```

### Step 3: Run It
```bash
python get_token.py
```

Your browser will open. Sign in and authorize the app.

### Step 4: Copy the Refresh Token

The script will print your refresh token. **Copy it** and send it to me, and I'll configure everything for you!

---

## Important Notes

- Make sure you added your email as a **test user** in the OAuth consent screen
- If you get an error about "redirect_uri_mismatch", make sure the redirect URI in your OAuth client settings includes: `http://localhost:8080/`
- Keep your refresh token secure - treat it like a password!

---

Once you have the refresh token, just paste it here and I'll complete the setup!
