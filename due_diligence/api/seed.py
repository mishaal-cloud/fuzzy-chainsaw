"""One-time seed script to create the first API key on a fresh deployment.

Usage:
    # Locally
    python -m due_diligence.api.seed --name "Admin" --tier enterprise

    # On Cloud Run (via gcloud)
    gcloud run jobs execute seed-key --args="--name,Admin,--tier,enterprise"

    # Via the /admin/seed endpoint (protected by ADMIN_SECRET)
    curl -X POST https://your-service.run.app/admin/seed \
      -H "X-Admin-Secret: your-admin-secret" \
      -H "Content-Type: application/json" \
      -d '{"name": "Admin", "tier": "enterprise"}'
"""

import argparse
from due_diligence.api.database import init_db, create_api_key


def main():
    parser = argparse.ArgumentParser(description="Create initial API key")
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", default="")
    parser.add_argument("--tier", choices=["free", "pro", "enterprise"], default="pro")
    args = parser.parse_args()

    init_db()
    result = create_api_key(args.name, args.email, args.tier)

    print(f"\nAPI Key created successfully!")
    print(f"  Name:    {result['name']}")
    print(f"  Tier:    {result['tier']}")
    print(f"  Credits: {result['credits_remaining']}")
    print(f"\n  API Key (save this):")
    print(f"  {result['api_key']}\n")


if __name__ == "__main__":
    main()
