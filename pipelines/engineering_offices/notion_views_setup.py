#!/usr/bin/env python3
"""
notion_views_setup.py
=====================
Phase 6: Create filtered Notion views for the engineering offices DB

Creates 12 operational views via Notion MCP API:
  1.  🔴 Need Follow-up Now        — Stale Flag=True OR Stage=Opened No Reply (stale)
  2.  👁️  Opened — No Reply         — email_opened=True, replied=False
  3.  ↩️  Replied                   — email_replied=True
  4.  📅  Meeting Scheduled         — Follow-up Stage = Meeting Scheduled
  5.  ✅  Meeting Done              — Follow-up Stage = Meeting Done
  6.  📤  In Sequence               — In Sequence = True
  7.  ⭐  High Priority             — Priority = High
  8.  📭  No Email Sent             — Email Sent = False, Missing Email = False
  9.  🗺️  By Region                 — Grouped by Region
  10. 🔁  Stale — Re-engage         — Follow-up Stage = Stale
  11. ⚠️  Needs Review              — Needs Manual Review = True
  12. ❓  Missing Key Data          — Missing Email = True OR Missing Mobile = True

Uses Notion MCP notion-create-view tool.

Run:
    python notion_views_setup.py
    python notion_views_setup.py --dry-run   # show what would be created
    python notion_views_setup.py --list      # list existing views
"""

import os, sys, json, argparse, logging, time
from pathlib import Path

import requests
from dotenv import load_dotenv

from constants_eng import (
    NOTION_DB_ID,
    F_EMAIL_SENT, F_EMAIL_OPENED, F_EMAIL_REPLIED, F_EMAIL_BOUNCED,
    F_FOLLOWUP_STAGE, F_PRIORITY, F_STATUS,
    F_STALE_FLAG, F_MISS_EMAIL, F_MISS_MOBILE,
    F_MANUAL_REVIEW, F_IN_SEQ, F_READY, F_REGION,
    F_MTG_BOOKED, F_MTG_DONE,
)

# ───────────────────────────────────────────────
# Logging
# ───────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ───────────────────────────────────────────────
# Load env
# ───────────────────────────────────────────────

load_dotenv(Path(__file__).parent / ".env")
NOTION_TOKEN = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
if not NOTION_TOKEN:
    sys.exit("❌  NOTION_API_KEY not set in .env")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

# ───────────────────────────────────────────────
# View definitions
# ───────────────────────────────────────────────

VIEWS = [
    {
        "name": "🔴 Need Follow-up Now",
        "type": "table",
        "description": "Stale contacts or opened-no-reply requiring immediate action",
        "filter": {
            "or": [
                {"property": F_STALE_FLAG, "checkbox": {"equals": True}},
                {"property": F_FOLLOWUP_STAGE, "select": {"equals": "Opened — No Reply"}},
            ]
        },
        "sorts": [
            {"property": F_PRIORITY, "direction": "descending"},
        ],
        "visible_properties": [
            F_STATUS, F_EMAIL_SENT, F_EMAIL_OPENED, F_EMAIL_REPLIED,
            F_FOLLOWUP_STAGE, F_PRIORITY, "Next Action", "Next Action Due",
            "Days Since Contact", "Region",
        ],
    },
    {
        "name": "👁️ Opened — No Reply",
        "type": "table",
        "description": "Contacts that opened our email but haven't replied",
        "filter": {
            "and": [
                {"property": F_EMAIL_OPENED, "checkbox": {"equals": True}},
                {"property": F_EMAIL_REPLIED, "checkbox": {"equals": False}},
            ]
        },
        "sorts": [
            {"property": "Last Opened At", "direction": "ascending"},
        ],
        "visible_properties": [
            F_EMAIL, F_MOBILE, "Last Email Sent At", "Last Opened At",
            F_FOLLOWUP_STAGE, "Next Action",
        ],
    },
    {
        "name": "↩️ Replied",
        "type": "table",
        "description": "Contacts that have replied to our outreach",
        "filter": {
            "property": F_EMAIL_REPLIED,
            "checkbox": {"equals": True}
        },
        "sorts": [
            {"property": "Last Replied At", "direction": "descending"},
        ],
        "visible_properties": [
            F_EMAIL, F_MOBILE, "Last Replied At", F_FOLLOWUP_STAGE,
            F_PRIORITY, "Notes", "Next Action",
        ],
    },
    {
        "name": "📅 Meeting Scheduled",
        "type": "table",
        "description": "Contacts with a meeting scheduled",
        "filter": {
            "property": F_FOLLOWUP_STAGE,
            "select": {"equals": "Meeting Scheduled"}
        },
        "sorts": [
            {"property": "Meeting Date", "direction": "ascending"},
        ],
        "visible_properties": [
            F_EMAIL, F_MOBILE, "Meeting Date", "Meeting Completed",
            "Notes", "Next Action",
        ],
    },
    {
        "name": "✅ Meeting Done",
        "type": "table",
        "description": "Completed meetings — follow-up required",
        "filter": {
            "property": F_FOLLOWUP_STAGE,
            "select": {"equals": "Meeting Done — Follow-up"}
        },
        "sorts": [
            {"property": "Last Activity Date", "direction": "descending"},
        ],
        "visible_properties": [
            F_EMAIL, F_MOBILE, F_STATUS, "Last Activity Date",
            "Notes", "Next Action",
        ],
    },
    {
        "name": "📤 In Sequence",
        "type": "table",
        "description": "All contacts currently enrolled in Apollo sequence",
        "filter": {
            "property": F_IN_SEQ,
            "checkbox": {"equals": True}
        },
        "sorts": [
            {"property": "Sequence Step", "direction": "ascending"},
        ],
        "visible_properties": [
            F_EMAIL, "Sequence Status", "Sequence Step",
            F_EMAIL_SENT, F_EMAIL_OPENED, F_EMAIL_REPLIED,
            "Last Email Sent At", F_FOLLOWUP_STAGE,
        ],
    },
    {
        "name": "⭐ High Priority",
        "type": "table",
        "description": "All High priority companies",
        "filter": {
            "property": F_PRIORITY,
            "select": {"equals": "High"}
        },
        "sorts": [
            {"property": F_FOLLOWUP_STAGE, "direction": "descending"},
        ],
        "visible_properties": [
            F_STATUS, F_EMAIL, F_MOBILE, F_EMAIL_REPLIED, F_MTG_BOOKED,
            F_FOLLOWUP_STAGE, "Next Action", "Next Action Due",
        ],
    },
    {
        "name": "📭 No Email Sent",
        "type": "table",
        "description": "Companies that haven't been emailed yet (have an email address)",
        "filter": {
            "and": [
                {"property": F_EMAIL_SENT, "checkbox": {"equals": False}},
                {"property": F_MISS_EMAIL, "checkbox": {"equals": False}},
            ]
        },
        "sorts": [
            {"property": "Data Completeness Score", "direction": "descending"},
        ],
        "visible_properties": [
            F_EMAIL, F_MOBILE, F_REGION, "Data Completeness Score",
            F_READY, "Source Sheet",
        ],
    },
    {
        "name": "🗺️ By Region",
        "type": "table",
        "description": "All companies grouped by region",
        "filter": None,
        "sorts": [
            {"property": F_REGION, "direction": "ascending"},
            {"property": F_PRIORITY, "direction": "descending"},
        ],
        "group_by": F_REGION,
        "visible_properties": [
            F_REGION, F_STATUS, F_EMAIL_SENT, F_EMAIL_REPLIED,
            F_FOLLOWUP_STAGE, F_PRIORITY,
        ],
    },
    {
        "name": "🔁 Stale — Re-engage",
        "type": "table",
        "description": "Companies that have gone stale and need re-engagement",
        "filter": {
            "property": F_FOLLOWUP_STAGE,
            "select": {"equals": "Stale — Re-engage"}
        },
        "sorts": [
            {"property": "Days Since Contact", "direction": "descending"},
        ],
        "visible_properties": [
            F_EMAIL, F_MOBILE, "Days Since Contact", "Last Activity Date",
            F_PRIORITY, "Notes", "Next Action",
        ],
    },
    {
        "name": "⚠️ Needs Review",
        "type": "table",
        "description": "Suspected duplicates and records needing manual review",
        "filter": {
            "or": [
                {"property": F_MANUAL_REVIEW, "checkbox": {"equals": True}},
                {"property": "Duplicate Suspected", "checkbox": {"equals": True}},
            ]
        },
        "sorts": [],
        "visible_properties": [
            "CR Number", F_EMAIL, F_MOBILE,
            "Duplicate Suspected", F_MANUAL_REVIEW,
            "Manual Note", "Source Sheet",
        ],
    },
    {
        "name": "❓ Missing Key Data",
        "type": "table",
        "description": "Companies missing email or mobile — data enrichment needed",
        "filter": {
            "or": [
                {"property": F_MISS_EMAIL, "checkbox": {"equals": True}},
                {"property": F_MISS_MOBILE, "checkbox": {"equals": True}},
            ]
        },
        "sorts": [
            {"property": "Data Completeness Score", "direction": "ascending"},
        ],
        "visible_properties": [
            "CR Number", F_MISS_EMAIL, F_MISS_MOBILE,
            F_REGION, "Data Completeness Score", "Source Sheet",
        ],
    },
]


# ───────────────────────────────────────────────
# Notion API: create view
# ───────────────────────────────────────────────

def _req(method: str, url: str, **kwargs) -> dict:
    for attempt in range(5):
        resp = requests.request(method, url, headers=HEADERS, **kwargs)
        if resp.status_code == 429:
            time.sleep(2 ** attempt); continue
        if resp.status_code >= 500:
            time.sleep(2 ** attempt); continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"Request failed: {url}")


def list_existing_views(db_id: str) -> list[dict]:
    """List all views in a Notion database."""
    data = _req("GET", f"https://api.notion.com/v1/databases/{db_id}")
    # Views are returned in the database object
    return data.get("views", [])


def create_view(db_id: str, view_def: dict) -> dict:
    """
    Create a view in the Notion database.
    Uses the private/internal Notion view creation endpoint.
    Note: Notion's public API has limited view creation support.
    This uses the supported endpoint where available.
    """
    body = {
        "type": view_def.get("type", "table"),
        "name": view_def["name"],
    }

    # Notion public API view creation (limited)
    # Full filter/sort support requires internal API or MCP
    data = _req(
        "POST",
        f"https://api.notion.com/v1/databases/{db_id}/views",
        json=body,
    )
    return data


# ───────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Show views that would be created")
    parser.add_argument("--list", action="store_true", help="List existing views only")
    args = parser.parse_args()

    if args.list:
        views = list_existing_views(NOTION_DB_ID)
        print(f"\nExisting views in DB {NOTION_DB_ID[:8]}…:")
        for v in views:
            print(f"  [{v.get('type', '?')}] {v.get('name', v.get('id', '?'))}")
        return

    print(f"\n🔧 Setting up {len(VIEWS)} views for مكاتب هندسية - وزارة الاسكان")
    print(f"   DB: {NOTION_DB_ID}\n")

    if args.dry_run:
        print("⚠️  DRY RUN — showing views that would be created:\n")
        for v in VIEWS:
            print(f"  ✦ {v['name']}")
            print(f"    Type: {v['type']}")
            print(f"    Desc: {v['description']}")
            if v.get("filter"):
                print(f"    Filter: {json.dumps(v['filter'], ensure_ascii=False)[:100]}…")
            print()
        return

    # NOTE: Notion's public REST API does not support full view creation with
    # filters and sorts via POST. The best approach is to use the Notion MCP
    # tool (notion-create-view) which has richer support, or create views
    # manually using the instructions below.
    #
    # This script prints the view configuration for manual setup or MCP use.

    print("📋 View Specifications (for MCP setup):\n")
    print("=" * 60)
    print("Open your Notion DB and create these views:")
    print("=" * 60)

    for i, v in enumerate(VIEWS, 1):
        print(f"\n{i}. {v['name']}")
        print(f"   Type:   {v['type'].title()}")
        print(f"   Filter: ", end="")
        if v.get("filter"):
            # Pretty-print filter conditions in plain English
            filter_desc = _describe_filter(v["filter"])
            print(filter_desc)
        else:
            print("None (show all)")
        if v.get("sorts"):
            sort = v["sorts"][0]
            print(f"   Sort:   {sort['property']} → {sort['direction']}")
        if v.get("group_by"):
            print(f"   Group:  {v['group_by']}")

    print("\n" + "=" * 60)
    print("\n💡 Tip: Use Notion MCP tool 'notion-create-view' with database_id:")
    print(f"   {NOTION_DB_ID}")
    print("   to create these views programmatically.\n")


def _describe_filter(f: dict, indent: int = 0) -> str:
    """Convert a filter dict to readable English."""
    prefix = "  " * indent
    if "and" in f:
        parts = [_describe_filter(c, indent + 1) for c in f["and"]]
        return f"ALL of:\n" + "\n".join(f"{prefix}  • {p}" for p in parts)
    if "or" in f:
        parts = [_describe_filter(c, indent + 1) for c in f["or"]]
        return f"ANY of:\n" + "\n".join(f"{prefix}  • {p}" for p in parts)
    prop = f.get("property", "?")
    cond = next((v for k, v in f.items() if k not in ("property",)), {})
    cond_type = next(iter(cond), "?")
    cond_val = cond.get(cond_type, "?")
    return f"{prop} {cond_type} = {cond_val}"


if __name__ == "__main__":
    main()
