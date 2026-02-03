#!/usr/bin/env python3
"""
Universal Launcher for Google Ads Automation
Run this from ANYWHERE - it will find the project automatically

Usage:
    python3 run.py simple_query
    python3 run.py analyze_performance
    python3 run.py update_campaigns
    python3 run.py quick_test
"""

import sys
import os
from pathlib import Path
import subprocess


def find_project_root():
    """Find the google-ads-automation directory"""
    # Start from this script's location
    script_path = Path(__file__).resolve()

    # If we're in the project, this script IS in google-ads-automation/
    if script_path.parent.name == "google-ads-automation":
        return script_path.parent

    # Otherwise search common locations
    possible_paths = [
        Path.home() / "fuzzy-chainsaw" / "google-ads-automation",
        Path.home() / "Documents" / "Projects" / "fuzzy-chainsaw" / "google-ads-automation",
        Path.home() / "Documents" / "GitHub" / "fuzzy-chainsaw" / "google-ads-automation",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    print("✗ Could not find google-ads-automation directory!")
    print("\nSearched:")
    for path in possible_paths:
        print(f"  - {path}")
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 run.py <script_name>")
        print("\nAvailable scripts:")
        print("  simple_query          - List campaigns and today's stats")
        print("  analyze_performance   - Full performance analysis")
        print("  update_campaigns      - Run automated updates (dry-run mode)")
        print("  quick_test            - Quick connection test")
        print("\nExample:")
        print("  python3 run.py simple_query")
        sys.exit(1)

    script_name = sys.argv[1]

    # Find project root
    project_root = find_project_root()
    print(f"✓ Found project at: {project_root}")

    # Map script names to paths
    scripts = {
        "simple_query": project_root / "examples" / "simple_query.py",
        "analyze_performance": project_root / "examples" / "analyze_performance.py",
        "update_campaigns": project_root / "examples" / "update_campaigns.py",
        "quick_test": project_root / "quick_test.py",
        "setup": project_root / "setup.py",
    }

    if script_name not in scripts:
        print(f"✗ Unknown script: {script_name}")
        print("\nAvailable scripts:")
        for name in scripts.keys():
            print(f"  - {name}")
        sys.exit(1)

    script_path = scripts[script_name]

    if not script_path.exists():
        print(f"✗ Script not found: {script_path}")
        sys.exit(1)

    print(f"✓ Running: {script_name}")
    print("=" * 60)
    print()

    # Run the script with Python
    result = subprocess.run([sys.executable, str(script_path)])
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
