"""
Configuration constants for PagerDuty Jira Extension Automation.
All fixed/default values extracted from existing extension rules (existing_rules_dump.json).
"""

# ──────────────────────────────────────────────────────────────────────────────
#  PagerDuty API Settings
# ──────────────────────────────────────────────────────────────────────────────
PAGERDUTY_API_BASE = "https://api.pagerduty.com"
PAGERDUTY_JIRA_INTEGRATION_BASE = "https://api.pagerduty.com/integration-jira-cloud"

# Jira Cloud Account Mapping ID (your extensions are created under this account)
JIRA_ACCOUNT_MAPPING_ID = "PJV19ZB"

# ──────────────────────────────────────────────────────────────────────────────
#  Jira Project (Fixed)
# ──────────────────────────────────────────────────────────────────────────────
JIRA_PROJECT = {
    "id": "10006",
    "key": "CLDOPS",
    "name": "Cloud Operations",
}

# ──────────────────────────────────────────────────────────────────────────────
#  Jira Issue Type (Fixed)
# ──────────────────────────────────────────────────────────────────────────────
JIRA_ISSUE_TYPE = {
    "id": "10009",
    "name": "Incident Management",
}

# ──────────────────────────────────────────────────────────────────────────────
#  Jira Field Mapping - Fixed fields
#  These are identical across all your extensions.
#  Format matches EXACTLY what the PagerDuty API returns/expects.
# ──────────────────────────────────────────────────────────────────────────────
FIXED_CUSTOM_FIELDS = [
    {
        "source_incident_field": "incident_title",
        "target_issue_field": "summary",
        "target_issue_field_name": "Summary",
        "type": "attribute",
        "value": None,
    },
    {
        "source_incident_field": "incident_description",
        "target_issue_field": "description",
        "target_issue_field_name": "Description",
        "type": "attribute",
        "value": None,
    },
    {
        "source_incident_field": None,
        "target_issue_field": "customfield_10078",
        "target_issue_field_name": "Assigned Team",
        "type": "jira_value",
        "value": {"displayName": "AppOps L1", "id": "10196"},
    },
    {
        "source_incident_field": None,
        "target_issue_field": "customfield_10072",
        "target_issue_field_name": "Environment",
        "type": "jira_value",
        "value": {"displayName": "Production", "id": "10126"},
    },
    {
        "source_incident_field": "incident_html_url",
        "target_issue_field": "customfield_10074",
        "target_issue_field_name": "PagerDuty URL",
        "type": "attribute",
        "value": None,
    },
    {
        "source_incident_field": None,
        "target_issue_field": "labels",
        "target_issue_field_name": "Labels",
        "type": "const",
        "value": "AppOps_SLA",
    },
    {
        "source_incident_field": None,
        "target_issue_field": "customfield_10050",
        "target_issue_field_name": "Source",
        "type": "jira_value",
        "value": {"displayName": "Monitoring", "id": "10034"},
    },
]

# Variable fields (filled at runtime):
# - customfield_10064 = Requesters Division  (type: jira_value, value: {displayName, id})
# - customfield_10189 = Impacted Service     (type: jira_value, value: {displayName, id})

# ──────────────────────────────────────────────────────────────────────────────
#  Sync Notes User (Fixed)
# ──────────────────────────────────────────────────────────────────────────────
SYNC_NOTES_USER = {
    "id": "PZRC6HE",
    "type": "user_reference",
}

# ──────────────────────────────────────────────────────────────────────────────
#  Status Mapping (Fixed)
# ──────────────────────────────────────────────────────────────────────────────
STATUS_MAPPING = {
    "acknowledged": {"id": "3", "name": "In Progress"},
    "resolved": {"id": "5", "name": "Resolved"},
    "triggered": {"id": "10023", "name": "New"},
}

# ──────────────────────────────────────────────────────────────────────────────
#  Priority Mapping (Fixed - uses actual PagerDuty priority IDs and Jira IDs)
# ──────────────────────────────────────────────────────────────────────────────
PRIORITY_MAPPING = [
    {"jira_id": "1", "pagerduty_id": "P3X9UL0"},   # P1
    {"jira_id": "2", "pagerduty_id": "PMTVV87"},   # P2
    {"jira_id": "3", "pagerduty_id": "PIH7UVH"},   # P3
    {"jira_id": "4", "pagerduty_id": "PF7JTGU"},   # P4
]
