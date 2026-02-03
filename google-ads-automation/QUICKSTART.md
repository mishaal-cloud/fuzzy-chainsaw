# Google Ads Automation - Quick Start

## The Simplest Way to Run This (No Directory Issues!)

### 1. One-Time Setup

```bash
# From ANYWHERE on your Mac, run this:
python3 ~/fuzzy-chainsaw/google-ads-automation/setup.py
```

Enter your credentials when prompted. That's it!

### 2. Run Scripts from ANYWHERE

```bash
# Test the connection
python3 ~/fuzzy-chainsaw/google-ads-automation/run.py quick_test

# List campaigns
python3 ~/fuzzy-chainsaw/google-ads-automation/run.py simple_query

# Full analysis
python3 ~/fuzzy-chainsaw/google-ads-automation/run.py analyze_performance
```

You can run these commands **from any directory** - they automatically find the project!

---

## Available Commands

| Command | What it does |
|---------|--------------|
| `python3 ~/fuzzy-chainsaw/google-ads-automation/run.py quick_test` | Test API connection |
| `python3 ~/fuzzy-chainsaw/google-ads-automation/run.py simple_query` | List campaigns & today's stats |
| `python3 ~/fuzzy-chainsaw/google-ads-automation/run.py analyze_performance` | Full 30-day analysis |
| `python3 ~/fuzzy-chainsaw/google-ads-automation/run.py update_campaigns` | Automated updates (dry-run) |

---

## For Cursor Users

Even easier! Just:

1. Open Cursor
2. Drag `/Users/mishaalmurawala/fuzzy-chainsaw` folder onto Cursor
3. Open terminal (`` Cmd+` ``)
4. Run: `python3 google-ads-automation/run.py simple_query`

Done!

---

## Troubleshooting

### "Permission Denied" Error?
Your developer token needs Standard Access approval. Check your email or visit:
https://ads.google.com/aw/apicenter

### "Configuration file not found"?
Run setup first:
```bash
python3 ~/fuzzy-chainsaw/google-ads-automation/setup.py
```

### Shell `cd` command broken?
Use the `run.py` script - it doesn't need `cd`!

---

## Why This Works

- ✅ **No `cd` commands needed** - Scripts find their own location
- ✅ **Run from anywhere** - Full path to run.py works from any directory
- ✅ **Auto-detects config files** - No more "file not found" errors
- ✅ **Works in Cursor** - Just use the built-in terminal

---

## Next Steps

Once your developer token is approved:

1. Run `python3 ~/fuzzy-chainsaw/google-ads-automation/run.py simple_query`
2. Ask Claude to analyze your data
3. Build custom automations with Claude's help

The framework handles all the directory navigation automatically!
