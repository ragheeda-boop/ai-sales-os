#!/usr/bin/env python3
"""
AI Sales OS — Meeting Analyzer v1.0

AI-powered meeting analysis engine. Reads meetings with notes but no Outcome,
analyzes them via Claude API, and writes structured intelligence back to Notion.

Two modes:
  1. Auto mode (default): Scans Notion Meetings DB for unanalyzed meetings,
     sends notes to Claude API, writes structured output back.
  2. Interactive mode (--text): Analyze text directly from CLI input.

Data Flow:
  Notion Meeting (with notes) → Claude API analysis → Structured JSON output
  → Update Meeting (Outcome, Key Takeaways, Next Steps, Decision Made)
  → Update Contact (Stage, Last Contacted, Contact Responded)
  → Create Task (if follow-up needed)
  → Flag Opportunity (if buying signals detected)

Usage:
    python meeting_analyzer.py                # analyze all unprocessed meetings
    python meeting_analyzer.py --dry-run      # preview without writing
    python meeting_analyzer.py --limit 5      # max meetings to process
    python meeting_analyzer.py --days 7       # scan last N days (default: 7)

Requires: ANTHROPIC_API_KEY in .env (Claude API)
"""
import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import os
import sys
import json
import logging
import time
import argparse
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from core.notion_helpers import (
    NOTION_DATABASE_ID_CONTACTS,
    rate_limiter,
    notion_request,
    create_page,
    update_page,
    NOTION_BASE_URL,
)
from core.constants import (
    FIELD_FULL_NAME, FIELD_EMAIL, FIELD_STAGE, FIELD_LAST_CONTACTED,
    FIELD_CONTACT_RESPONDED, FIELD_MEETING_BOOKED,
    FIELD_MEETING_TITLE, FIELD_MEETING_TYPE, FIELD_MEETING_SCHEDULED_DATE,
    FIELD_MEETING_OUTCOME, FIELD_MEETING_NOTES, FIELD_MEETING_KEY_TAKEAWAYS,
    FIELD_MEETING_DECISION, FIELD_MEETING_NEXT_STEPS,
    FIELD_MEETING_CONTACT, FIELD_MEETING_COMPANY, FIELD_MEETING_AGENDA,
    MEETING_OUTCOME_POSITIVE, MEETING_OUTCOME_NEUTRAL,
    MEETING_OUTCOME_NEGATIVE, MEETING_OUTCOME_NO_SHOW,
    FIELD_TASK_TITLE, FIELD_TASK_PRIORITY, FIELD_TASK_STATUS,
    FIELD_TASK_DUE_DATE, FIELD_TASK_TYPE, FIELD_TASK_CONTEXT,
    FIELD_TASK_EXPECTED_OUTCOME, FIELD_TASK_CONTACT, FIELD_TASK_COMPANY,
    FIELD_TASK_AUTO_CREATED,
)

# ─── Config ──────────────────────────────────────────────────────────────────

NOTION_DATABASE_ID_MEETINGS = os.getenv("NOTION_DATABASE_ID_MEETINGS")
NOTION_DATABASE_ID_TASKS = os.getenv("NOTION_DATABASE_ID_TASKS")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Claude API settings
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS = 2000

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("meeting_analyzer.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ─── Claude API ──────────────────────────────────────────────────────────────

ANALYSIS_PROMPT = """You are a sales intelligence analyst for AI Sales OS. Analyze this meeting and return ONLY valid JSON (no markdown, no explanation).

Meeting Title: {title}
Meeting Type: {meeting_type}
Date: {date}
Agenda: {agenda}
Notes: {notes}

Return this exact JSON structure:
{{
  "outcome": "Positive" | "Neutral" | "Negative" | "No Show",
  "key_takeaways": "2-3 sentence summary of what matters most",
  "decision_made": "What was decided, or 'No decision made'",
  "next_steps": "Specific follow-up actions with who and when",
  "buying_signals": ["signal1", "signal2"],
  "objections": ["objection1", "objection2"],
  "opportunity_signal": true | false,
  "estimated_deal_value": null | number,
  "contact_stage": "Lead" | "Prospect" | "Engaged" | "Customer" | null,
  "follow_up_task": {{
    "needed": true | false,
    "title": "Task title",
    "priority": "Critical" | "High" | "Medium",
    "due_days": 3,
    "type": "Follow-up" | "Demo" | "Proposal" | "Review",
    "context": "Why this task is needed",
    "expected_outcome": "What success looks like"
  }}
}}

Rules:
- Be specific, not generic. Use details from the notes.
- If notes are thin, say so in key_takeaways and set outcome to "Neutral".
- buying_signals and objections can be empty arrays.
- opportunity_signal = true ONLY if there are real buying signals.
- contact_stage = null if no change is warranted.
- due_days = number of days from today for the follow-up task.
"""


def analyze_meeting_with_claude(meeting: Dict) -> Optional[Dict]:
    """Send meeting data to Claude API and get structured analysis."""
    import requests

    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set — cannot analyze meetings")
        return None

    prompt = ANALYSIS_PROMPT.format(
        title=meeting.get("title", ""),
        meeting_type=meeting.get("type", ""),
        date=meeting.get("scheduled", ""),
        agenda=meeting.get("agenda", ""),
        notes=meeting.get("notes", ""),
    )

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": CLAUDE_MAX_TOKENS,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )

        if resp.status_code != 200:
            logger.error(f"Claude API error {resp.status_code}: {resp.text[:200]}")
            return None

        data = resp.json()
        content = data.get("content", [{}])[0].get("text", "")

        # Parse JSON from response (handle potential markdown wrapping)
        json_str = content.strip()
        if json_str.startswith("```"):
            json_str = json_str.split("\n", 1)[1].rsplit("```", 1)[0]

        analysis = json.loads(json_str)
        logger.info(f"  Claude analysis: outcome={analysis.get('outcome')}, "
                     f"opportunity={analysis.get('opportunity_signal')}")
        return analysis

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}")
        logger.debug(f"Raw response: {content[:500]}")
        return None
    except Exception as e:
        logger.error(f"Claude API request failed: {e}")
        return None


# ─── Notion Data Fetching ────────────────────────────────────────────────────

def fetch_unanalyzed_meetings(days: int = 7) -> List[Dict]:
    """
    Fetch meetings from Notion that have notes/agenda but no Outcome set.
    These are the meetings waiting for AI analysis.
    """
    if not NOTION_DATABASE_ID_MEETINGS:
        return []

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    results = []
    cursor = None

    while True:
        body = {
            "page_size": 100,
            "filter": {
                "and": [
                    {"property": FIELD_MEETING_SCHEDULED_DATE, "date": {"on_or_after": cutoff}},
                    {"property": FIELD_MEETING_OUTCOME, "select": {"is_empty": True}},
                    {
                        "or": [
                            {"property": FIELD_MEETING_NOTES, "rich_text": {"is_not_empty": True}},
                            {"property": FIELD_MEETING_AGENDA, "rich_text": {"is_not_empty": True}},
                            {"property": FIELD_MEETING_KEY_TAKEAWAYS, "rich_text": {"is_not_empty": True}},
                        ]
                    },
                ]
            },
            "sorts": [{"property": FIELD_MEETING_SCHEDULED_DATE, "direction": "descending"}],
        }
        if cursor:
            body["start_cursor"] = cursor

        rate_limiter.wait()
        try:
            resp = notion_request(
                "POST",
                f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID_MEETINGS}/query",
                json=body,
            )
            data = resp.json()
        except Exception as e:
            logger.error(f"Error fetching meetings: {e}")
            break

        for page in data.get("results", []):
            pid = page["id"]
            props = page.get("properties", {})

            title_items = props.get(FIELD_MEETING_TITLE, {}).get("title", [])
            title = title_items[0]["text"]["content"] if title_items else "Unknown"

            type_sel = props.get(FIELD_MEETING_TYPE, {}).get("select")
            meeting_type = type_sel.get("name", "") if type_sel else ""

            date_prop = props.get(FIELD_MEETING_SCHEDULED_DATE, {}).get("date")
            scheduled = date_prop.get("start", "") if date_prop else ""

            notes_rt = props.get(FIELD_MEETING_NOTES, {}).get("rich_text", [])
            notes = notes_rt[0]["text"]["content"] if notes_rt else ""

            agenda_rt = props.get(FIELD_MEETING_AGENDA, {}).get("rich_text", [])
            agenda = agenda_rt[0]["text"]["content"] if agenda_rt else ""

            takeaways_rt = props.get(FIELD_MEETING_KEY_TAKEAWAYS, {}).get("rich_text", [])
            takeaways = takeaways_rt[0]["text"]["content"] if takeaways_rt else ""

            # Get linked contact(s)
            contact_rel = props.get(FIELD_MEETING_CONTACT, {}).get("relation", [])
            contact_ids = [r["id"] for r in contact_rel] if contact_rel else []

            # Get linked company
            company_rel = props.get(FIELD_MEETING_COMPANY, {}).get("relation", [])
            company_ids = [r["id"] for r in company_rel] if company_rel else []

            results.append({
                "page_id": pid,
                "title": title,
                "type": meeting_type,
                "scheduled": scheduled,
                "notes": notes or takeaways,  # Use whatever text is available
                "agenda": agenda,
                "contact_ids": contact_ids,
                "company_ids": company_ids,
            })

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    logger.info(f"Found {len(results)} unanalyzed meetings (last {days} days)")
    return results


# ─── Notion Writing ──────────────────────────────────────────────────────────

def update_meeting_with_analysis(meeting_page_id: str, analysis: Dict, dry_run: bool = False) -> bool:
    """Write AI analysis results back to the Meeting record in Notion."""
    outcome = analysis.get("outcome", "Neutral")

    # Validate outcome is a valid option
    valid_outcomes = {MEETING_OUTCOME_POSITIVE, MEETING_OUTCOME_NEUTRAL,
                      MEETING_OUTCOME_NEGATIVE, MEETING_OUTCOME_NO_SHOW}
    if outcome not in valid_outcomes:
        outcome = MEETING_OUTCOME_NEUTRAL

    properties = {
        FIELD_MEETING_OUTCOME: {"select": {"name": outcome}},
    }

    # Key Takeaways
    takeaways = analysis.get("key_takeaways", "")
    if takeaways:
        properties[FIELD_MEETING_KEY_TAKEAWAYS] = {
            "rich_text": [{"text": {"content": takeaways[:2000]}}]
        }

    # Decision Made
    decision = analysis.get("decision_made", "")
    if decision:
        properties[FIELD_MEETING_DECISION] = {
            "rich_text": [{"text": {"content": decision[:2000]}}]
        }

    # Next Steps
    next_steps = analysis.get("next_steps", "")
    if next_steps:
        properties[FIELD_MEETING_NEXT_STEPS] = {
            "rich_text": [{"text": {"content": next_steps[:2000]}}]
        }

    if dry_run:
        logger.info(f"  [DRY RUN] Would update meeting with: outcome={outcome}")
        return True

    try:
        update_page(meeting_page_id, properties)
        logger.info(f"  Updated meeting: outcome={outcome}")
        return True
    except Exception as e:
        logger.error(f"  Failed to update meeting: {e}")
        return False


def update_contact_from_analysis(contact_id: str, analysis: Dict, dry_run: bool = False) -> bool:
    """Update contact fields based on meeting analysis."""
    properties = {
        FIELD_CONTACT_RESPONDED: {"checkbox": True},
        FIELD_MEETING_BOOKED: {"checkbox": True},
        FIELD_LAST_CONTACTED: {
            "date": {"start": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
        },
    }

    # Update stage if analysis suggests it
    new_stage = analysis.get("contact_stage")
    if new_stage and new_stage in {"Lead", "Prospect", "Engaged", "Customer"}:
        properties[FIELD_STAGE] = {"select": {"name": new_stage}}

    if dry_run:
        logger.info(f"  [DRY RUN] Would update contact {contact_id}: "
                     f"stage={new_stage or 'no change'}")
        return True

    try:
        update_page(contact_id, properties)
        logger.info(f"  Updated contact {contact_id}")
        return True
    except Exception as e:
        logger.error(f"  Failed to update contact {contact_id}: {e}")
        return False


def create_follow_up_task(
    analysis: Dict,
    meeting_title: str,
    contact_ids: List[str],
    company_ids: List[str],
    dry_run: bool = False,
) -> bool:
    """Create a follow-up task if the analysis recommends one."""
    task_info = analysis.get("follow_up_task", {})
    if not task_info or not task_info.get("needed"):
        return False

    if not NOTION_DATABASE_ID_TASKS:
        logger.warning("NOTION_DATABASE_ID_TASKS not set — cannot create task")
        return False

    due_days = task_info.get("due_days", 3)
    due_date = (datetime.now(timezone.utc) + timedelta(days=due_days)).strftime("%Y-%m-%d")

    properties = {
        FIELD_TASK_TITLE: {
            "title": [{"text": {"content": task_info.get("title", f"Follow-up: {meeting_title}")[:100]}}]
        },
        FIELD_TASK_PRIORITY: {"select": {"name": task_info.get("priority", "High")}},
        FIELD_TASK_STATUS: {"status": {"name": "Not Started"}},
        FIELD_TASK_DUE_DATE: {"date": {"start": due_date}},
        FIELD_TASK_AUTO_CREATED: {"checkbox": True},
    }

    # Task Type
    task_type = task_info.get("type", "Follow-up")
    if task_type:
        properties[FIELD_TASK_TYPE] = {"select": {"name": task_type}}

    # Context
    context = task_info.get("context", "")
    if context:
        properties[FIELD_TASK_CONTEXT] = {
            "rich_text": [{"text": {"content": context[:2000]}}]
        }

    # Expected Outcome
    expected = task_info.get("expected_outcome", "")
    if expected:
        properties[FIELD_TASK_EXPECTED_OUTCOME] = {
            "rich_text": [{"text": {"content": expected[:2000]}}]
        }

    # Link to contact
    if contact_ids:
        properties[FIELD_TASK_CONTACT] = {
            "relation": [{"id": contact_ids[0]}]
        }

    # Link to company
    if company_ids:
        properties[FIELD_TASK_COMPANY] = {
            "relation": [{"id": company_ids[0]}]
        }

    if dry_run:
        logger.info(f"  [DRY RUN] Would create task: {task_info.get('title', 'follow-up')} "
                     f"| Priority: {task_info.get('priority')} | Due: {due_date}")
        return True

    try:
        page_id = create_page(NOTION_DATABASE_ID_TASKS, properties)
        logger.info(f"  Created follow-up task → {page_id}")
        return True
    except Exception as e:
        logger.error(f"  Failed to create task: {e}")
        return False


# ─── Main Pipeline ───────────────────────────────────────────────────────────

def process_meeting(meeting: Dict, dry_run: bool = False) -> Dict:
    """Full pipeline for one meeting: analyze → update meeting → update contact → create task."""
    result = {
        "analyzed": False,
        "meeting_updated": False,
        "contacts_updated": 0,
        "task_created": False,
        "opportunity_flagged": False,
    }

    logger.info(f"Analyzing: '{meeting['title']}' ({meeting['scheduled']})")

    # Step 1: AI Analysis
    analysis = analyze_meeting_with_claude(meeting)
    if not analysis:
        logger.warning(f"  Could not analyze meeting '{meeting['title']}'")
        return result

    result["analyzed"] = True

    # Step 2: Update Meeting record
    success = update_meeting_with_analysis(meeting["page_id"], analysis, dry_run)
    result["meeting_updated"] = success

    # Step 3: Update linked contacts
    for contact_id in meeting.get("contact_ids", []):
        if update_contact_from_analysis(contact_id, analysis, dry_run):
            result["contacts_updated"] += 1

    # Step 4: Create follow-up task
    result["task_created"] = create_follow_up_task(
        analysis, meeting["title"],
        meeting.get("contact_ids", []),
        meeting.get("company_ids", []),
        dry_run,
    )

    # Step 5: Flag opportunity signal
    if analysis.get("opportunity_signal"):
        result["opportunity_flagged"] = True
        deal_value = analysis.get("estimated_deal_value")
        logger.info(f"  💰 OPPORTUNITY SIGNAL detected"
                     f"{f' — est. ${deal_value:,.0f}' if deal_value else ''}")

    return result


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Sales OS — Meeting Analyzer v1.0")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--days", type=int, default=7, help="Scan last N days (default: 7)")
    parser.add_argument("--limit", type=int, default=10, help="Max meetings to analyze")
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info(f"MEETING ANALYZER v1.0 | Days: {args.days} | Dry Run: {args.dry_run}")
    logger.info("=" * 70)

    start_time = time.time()

    if not NOTION_DATABASE_ID_MEETINGS:
        logger.error("NOTION_DATABASE_ID_MEETINGS not set. Add to .env.")
        sys.exit(1)

    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set. Add to .env for AI analysis.")
        sys.exit(1)

    # Fetch unanalyzed meetings
    meetings = fetch_unanalyzed_meetings(days=args.days)

    if not meetings:
        logger.info("No unanalyzed meetings found.")
        stats = {
            "meetings_found": 0, "analyzed": 0, "meetings_updated": 0,
            "contacts_updated": 0, "tasks_created": 0, "opportunities_flagged": 0,
            "errors": 0, "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    else:
        # Process each meeting
        stats = {
            "meetings_found": len(meetings),
            "analyzed": 0,
            "meetings_updated": 0,
            "contacts_updated": 0,
            "tasks_created": 0,
            "opportunities_flagged": 0,
            "errors": 0,
        }

        for i, meeting in enumerate(meetings[:args.limit]):
            logger.info(f"\n--- Meeting {i+1}/{min(len(meetings), args.limit)} ---")
            result = process_meeting(meeting, dry_run=args.dry_run)

            if result["analyzed"]:
                stats["analyzed"] += 1
            else:
                stats["errors"] += 1

            if result["meeting_updated"]:
                stats["meetings_updated"] += 1
            stats["contacts_updated"] += result["contacts_updated"]
            if result["task_created"]:
                stats["tasks_created"] += 1
            if result["opportunity_flagged"]:
                stats["opportunities_flagged"] += 1

            # Rate limit between API calls
            time.sleep(1)

        stats["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Save stats
    elapsed = time.time() - start_time
    stats["runtime_seconds"] = round(elapsed, 1)

    stats_file = os.path.join(SCRIPT_DIR, "last_analyzer_stats.json")
    try:
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save stats: {e}")

    # Summary
    logger.info("")
    logger.info("=" * 50)
    logger.info("MEETING ANALYZER SUMMARY")
    logger.info(f"  Meetings found:       {stats['meetings_found']}")
    logger.info(f"  Successfully analyzed: {stats['analyzed']}")
    logger.info(f"  Meetings updated:      {stats['meetings_updated']}")
    logger.info(f"  Contacts updated:      {stats['contacts_updated']}")
    logger.info(f"  Tasks created:         {stats['tasks_created']}")
    logger.info(f"  Opportunities flagged: {stats['opportunities_flagged']}")
    logger.info(f"  Errors:                {stats['errors']}")
    logger.info(f"  Runtime:               {elapsed:.1f}s")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
