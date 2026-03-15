"""
Utility: Dump Existing PagerDuty Jira Cloud Extension Rules
===========================================================

This script connects to PagerDuty and downloads the exact JSON configuration 
of all existing Jira Cloud Extension rules for a specific account mapping.

This is highly useful when moving from Sandbox to Production, as you can
manually create ONE extension in the PagerDuty UI, then run this script to
extract all the exact IDs (Priorities, Custom Fields, Users) to paste into your config.py.

Usage:
    export PAGERDUTY_TOKEN="your_key_here"
    python scripts/dump_existing_rules.py <jira_account_mapping_id>

Example:
    python scripts/dump_existing_rules.py PJV19ZB
"""

import os
import sys
import json
import requests

PAGERDUTY_JIRA_INTEGRATION_BASE = "https://api.pagerduty.com/integration-jira-cloud"

def main():
    if len(sys.argv) < 2:
        print("Error: Please provide the Jira Account Mapping ID as an argument.")
        print("Example: python dump_existing_rules.py PJV19ZB")
        sys.exit(1)

    mapping_id = sys.argv[1]
    api_key = os.environ.get("PAGERDUTY_TOKEN")

    if not api_key:
        print("Error: PAGERDUTY_TOKEN environment variable is not set.")
        sys.exit(1)

    print(f"Fetching rules for mapping ID: {mapping_id}...")

    headers = {
        "Authorization": f"Token token={api_key}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.pagerduty+json;version=2",
    }

    try:
        url = f"{PAGERDUTY_JIRA_INTEGRATION_BASE}/accounts_mappings/{mapping_id}/rules"
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        
        rules = resp.json().get("rules", [])
        
        if not rules:
            print("No rules found for this mapping ID.")
            sys.exit(0)

        filename = f"existing_rules_{mapping_id}.json"
        with open(filename, "w") as f:
            json.dump(rules, f, indent=2)

        print(f"\n✅ Success! Dumped {len(rules)} rules to: {filename}")
        print("Open this file to view the exact JSON payload, field IDs, and priority mappings.")

    except requests.exceptions.HTTPError as e:
        print(f"❌ API Error: {e.response.status_code}")
        print(e.response.text)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
