"""
PagerDuty Jira Cloud Extension Automation — CI/CD Version
==========================================================

Reads extension config from jira_extensions.yaml and creates
Jira Cloud extensions in PagerDuty automatically.

Designed for GitHub Actions — no interactive prompts.

Usage:
    Set env var PAGERDUTY_TOKEN, then:
    python scripts/create_jira_extensions.py

Exit codes:
    0 = All extensions created (or nothing to do)
    1 = One or more failures
"""

import os
import sys
import json
import time
import yaml
import requests

from config import (
    PAGERDUTY_API_BASE,
    PAGERDUTY_JIRA_INTEGRATION_BASE,
    JIRA_ACCOUNT_MAPPING_ID,
    JIRA_PROJECT,
    JIRA_ISSUE_TYPE,
    FIXED_CUSTOM_FIELDS,
    SYNC_NOTES_USER,
    STATUS_MAPPING,
    PRIORITY_MAPPING,
)

# Path to the YAML config (relative to repo root)
YAML_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jira_extensions.yaml")


# ──────────────────────────────────────────────────────────────────────────────
#  Logging Helpers (CI-friendly, no colorama)
# ──────────────────────────────────────────────────────────────────────────────

def log_info(msg):
    print(f"  ℹ️  {msg}")

def log_success(msg):
    print(f"  ✅ {msg}")

def log_error(msg):
    print(f"  ❌ {msg}")

def log_warning(msg):
    print(f"  ⚠️  {msg}")

def log_step(step, msg):
    print(f"\n{'─' * 60}")
    print(f"  Step {step}: {msg}")
    print(f"{'─' * 60}")


# ──────────────────────────────────────────────────────────────────────────────
#  PagerDuty API Helpers
# ──────────────────────────────────────────────────────────────────────────────

class PagerDutyAPI:
    """Wrapper around PagerDuty REST API calls."""

    def __init__(self, api_key):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token token={api_key}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.pagerduty+json;version=2",
        })

    def list_services(self):
        """List PagerDuty services (for API key validation)."""
        resp = self.session.get(f"{PAGERDUTY_API_BASE}/services", params={"limit": 1})
        resp.raise_for_status()
        return resp.json().get("services", [])

    def get_service_by_id(self, service_id):
        """Fetch a PagerDuty service by its unique ID."""
        resp = self.session.get(f"{PAGERDUTY_API_BASE}/services/{service_id}")
        resp.raise_for_status()
        return resp.json().get("service", None)

    def get_existing_rules(self, account_mapping_id):
        """Fetch all existing Jira extension rules."""
        resp = self.session.get(
            f"{PAGERDUTY_JIRA_INTEGRATION_BASE}/accounts_mappings/{account_mapping_id}/rules"
        )
        resp.raise_for_status()
        return resp.json().get("rules", [])

    def create_mapping_rule(self, account_mapping_id, rule_payload):
        """Create a new Jira Cloud account mapping rule."""
        resp = self.session.post(
            f"{PAGERDUTY_JIRA_INTEGRATION_BASE}/accounts_mappings/{account_mapping_id}/rules",
            json=rule_payload,
        )
        resp.raise_for_status()
        return resp.json()


# ──────────────────────────────────────────────────────────────────────────────
#  Rule Payload Builder (same logic as terminal version)
# ──────────────────────────────────────────────────────────────────────────────

def build_rule_payload(service_id, service_name, ext_config):
    """Build the JSON payload for creating a Jira extension rule."""
    custom_fields = list(FIXED_CUSTOM_FIELDS)

    # Requesters Division (variable)
    custom_fields.append({
        "source_incident_field": None,
        "target_issue_field": "customfield_10064",
        "target_issue_field_name": "Requesters Division",
        "type": "jira_value",
        "value": {
            "displayName": ext_config["requesters_division_name"],
            "id": ext_config["requesters_division_id"],
        },
    })

    # Impacted Service (variable)
    custom_fields.append({
        "source_incident_field": None,
        "target_issue_field": "customfield_10189",
        "target_issue_field_name": "Impacted Service",
        "type": "jira_value",
        "value": {
            "displayName": ext_config["impacted_service_name"],
            "id": ext_config["impacted_service_id"],
        },
    })

    return {
        "config": {
            "jira": {
                "autocreate_jql": None,
                "create_issue_on_incident_trigger": True,
                "custom_fields": custom_fields,
                "issue_type": JIRA_ISSUE_TYPE,
                "priorities": PRIORITY_MAPPING,
                "project": JIRA_PROJECT,
                "status_mapping": STATUS_MAPPING,
                "sync_notes_user": SYNC_NOTES_USER,
            },
            "service": {
                "id": service_id,
                "type": "service_reference",
            },
        },
        "name": service_name,
    }


# ──────────────────────────────────────────────────────────────────────────────
#  Duplicate Detection
# ──────────────────────────────────────────────────────────────────────────────

def get_existing_service_ids(pd, account_mapping_id):
    """Get set of service IDs that already have Jira extension rules."""
    existing_ids = set()
    try:
        rules = pd.get_existing_rules(account_mapping_id)
        for rule in rules:
            svc = rule.get("config", {}).get("service", {})
            if svc.get("id"):
                existing_ids.add(svc["id"])
    except Exception as e:
        log_warning(f"Could not fetch existing rules (will proceed anyway): {e}")
    return existing_ids


# ──────────────────────────────────────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  🚀 PagerDuty Jira Extension Automation — CI/CD")
    print("=" * 60)

    # ── Step 1: Read PD API key from environment ──────────────────────────
    log_step(1, "Read PagerDuty API Key")
    api_key = os.environ.get("PAGERDUTY_TOKEN")
    if not api_key:
        log_error("PAGERDUTY_TOKEN environment variable is not set.")
        log_error("Set it via: export PAGERDUTY_TOKEN='your_key_here'")
        sys.exit(1)

    pd = PagerDutyAPI(api_key)

    # Validate key
    log_info("Validating API key...")
    try:
        pd.list_services()
        log_success("API key is valid.")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            log_error("Invalid API key.")
        else:
            log_error(f"API error: {e.response.status_code}")
        sys.exit(1)

    # ── Step 2: Read YAML config ──────────────────────────────────────────
    log_step(2, "Read Extension Config")
    log_info(f"Reading: {YAML_CONFIG_PATH}")

    if not os.path.exists(YAML_CONFIG_PATH):
        log_error(f"Config file not found: {YAML_CONFIG_PATH}")
        sys.exit(1)

    with open(YAML_CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)

    extensions = config.get("extensions") or []
    if not extensions:
        log_info("No extensions defined in jira_extensions.yaml. Nothing to do.")
        print("\n✅ Done (0 extensions to process)\n")
        sys.exit(0)

    log_info(f"Found {len(extensions)} extension(s) in config.")

    # ── Step 3: Check for duplicates ──────────────────────────────────────
    log_step(3, "Check Existing Rules")
    existing_service_ids = get_existing_service_ids(pd, JIRA_ACCOUNT_MAPPING_ID)
    log_info(f"Found {len(existing_service_ids)} existing extension rule(s) in PagerDuty.")

    # Filter out extensions that already exist
    new_extensions = []
    skipped = []
    for ext in extensions:
        sid = ext.get("service_id", "").strip()
        if sid in existing_service_ids:
            skipped.append(ext)
            log_warning(f"Skipping {sid} — extension already exists.")
        else:
            new_extensions.append(ext)

    if not new_extensions:
        log_info("All extensions already exist. Nothing new to create.")
        if skipped:
            print(f"\n  ⏭️  Skipped {len(skipped)} existing extension(s)")
        print("\n✅ Done (0 new extensions)\n")
        sys.exit(0)

    log_success(f"{len(new_extensions)} new extension(s) to create.")

    # ── Step 4: Resolve services & create extensions ──────────────────────
    log_step(4, "Create Extensions")
    results = []

    for ext in new_extensions:
        sid = ext.get("service_id", "").strip()
        imp_id = str(ext.get("impacted_service_id", "")).strip()
        imp_name = ext.get("impacted_service_name", "").strip()
        req_id = str(ext.get("requesters_division_id", "")).strip()
        req_name = ext.get("requesters_division_name", "").strip()

        # Auto-lookup common names if missing
        if not imp_name:
            if imp_id == "11454": imp_name = "O&PS - E-Builder"
            elif imp_id == "11455": imp_name = "Cityworks"
            else: imp_name = f"ID: {imp_id}" # Fallback
            
        if not req_name:
            if req_id == "10257": req_name = "e-Builder"
            else: req_name = f"ID: {req_id}" # Fallback

        print(f"\n  ── Processing: {sid} ──")

        # Look up service
        try:
            svc = pd.get_service_by_id(sid)
            if not svc:
                log_error(f"Service {sid} returned no data.")
                results.append({"service_id": sid, "status": "FAILED", "error": "No data"})
                continue
            svc_name = svc["name"]
            log_info(f"Service: {svc_name}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                log_error(f"Service {sid} not found.")
            else:
                log_error(f"Error looking up {sid}: {e.response.status_code}")
            results.append({"service_id": sid, "status": "FAILED", "error": str(e)})
            continue

        # Build config
        ext_config = {
            "impacted_service_id": imp_id,
            "impacted_service_name": imp_name,
            "requesters_division_id": req_id,
            "requesters_division_name": req_name,
        }

        # Create
        try:
            payload = build_rule_payload(sid, svc_name, ext_config)
            pd.create_mapping_rule(JIRA_ACCOUNT_MAPPING_ID, payload)
            log_success(f"Extension created for '{svc_name}'!")
            results.append({
                "service_id": sid,
                "service_name": svc_name,
                "config_name": svc_name,
                "status": "SUCCESS",
            })
        except requests.exceptions.HTTPError as e:
            error_details = ""
            try:
                error_details = json.dumps(e.response.json(), indent=2)
            except Exception:
                error_details = e.response.text
            log_error(f"Failed for '{svc_name}': {e.response.status_code}")
            log_error(f"Details: {error_details}")
            results.append({
                "service_id": sid,
                "service_name": svc_name,
                "status": "FAILED",
                "error": error_details,
            })
        except Exception as e:
            log_error(f"Unexpected error for {sid}: {e}")
            results.append({"service_id": sid, "status": "FAILED", "error": str(e)})

        time.sleep(0.5)  # Rate limit protection

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\n\n{'=' * 60}")
    print(f"  📊 EXECUTION SUMMARY")
    print(f"{'=' * 60}")

    success_count = sum(1 for r in results if r["status"] == "SUCCESS")
    fail_count = sum(1 for r in results if r["status"] == "FAILED")

    for r in results:
        icon = "✅" if r["status"] == "SUCCESS" else "❌"
        name = r.get("service_name", r["service_id"])
        print(f"  {icon} {name} — {r['status']}")

    if skipped:
        for s in skipped:
            print(f"  ⏭️  {s['service_id']} — SKIPPED (already exists)")

    print(f"\n  Total: {success_count} created, {fail_count} failed, {len(skipped)} skipped")
    print(f"{'=' * 60}\n")

    # Exit with error code if any failures
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
