---
name: action-engine-builder
description: "Build, operate, and improve the Action Engine (auto_tasks.py) and Action Ready logic for AI Sales OS. Use this skill when the user talks about creating tasks automatically, task automation, SLA enforcement, Action Ready conditions, follow-up tasks, HOT lead actions, task creation rules, overdue tasks, or anything about converting lead scores into actionable sales tasks. Also trigger for 'why wasn't a task created for this contact?' or 'how does the Action Engine work?'"
---

# Action Engine Builder — AI Sales OS

You build and operate the system that converts intelligence (lead scores) into action (sales tasks). This is the bridge between knowing who matters and doing something about it.

## Architecture

```
lead_score.py → action_ready_updater.py → auto_tasks.py
     ↓                    ↓                      ↓
  Writes Score     Sets Action Ready      Creates Tasks
  + Lead Tier      (5 conditions)         in Tasks DB
```

The scripts run in this exact order. Running auto_tasks before action_ready_updater would use stale data.

## Action Ready Logic (`action_ready_updater.py`)

A contact becomes Action Ready = True only when ALL 5 conditions pass:

```python
1. Lead Score >= 50 (SCORE_WARM from constants.py)
2. Do Not Call = False
3. Outreach Status NOT in {"Do Not Contact", "Bounced", "Bad Data"}
4. Stage NOT in {"Customer", "Churned"} (case-insensitive)
5. Has email OR phone (Work Direct, Mobile, or Corporate)
```

The updater fetches all contacts with Lead Score >= 50, evaluates each one, and writes `Action Ready` checkbox. It only writes when the value actually changes (avoids unnecessary API calls).

**Commands:**
```bash
python action_ready_updater.py          # update all scored contacts
python action_ready_updater.py --dry-run  # show what would change
```

## Task Creation Logic (`auto_tasks.py`)

### Priority Rules

| Tier | Min Score | Priority | Action | Channel | SLA |
|------|-----------|----------|--------|---------|-----|
| HOT | >= 80 | Critical | CALL | Phone | 24 hours |
| WARM | >= 50 | High | FOLLOW-UP | Email | 48 hours |

### Task Creation Flow

1. Fetch all contacts where `Action Ready = True` AND `Lead Score >= 50`, sorted by score descending
2. Load all open tasks (Status != "Completed") and build set of Contact IDs with existing tasks
3. For each contact:
   - Skip if Do Not Call = True
   - Skip if Outreach Status in OUTREACH_BLOCKED
   - Skip if already has an open task (duplicate prevention)
   - Find matching priority rule
   - Create task with: Title, Priority, Status (Not Started), Due Date, Task Type, Context (why this lead), Description, Expected Outcome, Auto Created = True, Automation Type = "Lead Scoring", Trigger Rule, Contact relation, Company relation

### What Gets Written to Tasks DB

```python
{
    "Task Title": "CALL: {name} — {company}",  # or "FOLLOW-UP: ..."
    "Priority": "Critical" | "High",
    "Status": {"status": {"name": "Not Started"}},  # STATUS type, not select!
    "Due Date": today + SLA hours,
    "Task Type": "Follow-up",
    "Context": "Lead Score: 95/100 | Tier: HOT | Seniority: C-Suite | ...",
    "Description": "Auto-generated task for HOT lead. Action: CALL via Phone.",
    "Expected Outcome": "Schedule a meeting or demo within 24 hours",
    "Auto Created": True,
    "Automation Type": "Lead Scoring",
    "Trigger Rule": "Score >= 80 AND Action Ready = True",
    "Contact": [relation to contact],
    "Company": [relation to company if available]
}
```

### Duplicate Prevention

Before creating any task, checks if the contact already has an open task (Status != "Completed"). If yes, skips entirely. This prevents task spam.

### Overdue Detection

`mark_overdue_tasks()` runs at the start of every execution. It queries tasks where Due Date < today AND Status != "Completed" and logs them as overdue.

**Commands:**
```bash
python auto_tasks.py                  # create tasks for all Action Ready contacts
python auto_tasks.py --dry-run        # show what would be created
python auto_tasks.py --limit 20       # limit to first N (testing)
python auto_tasks.py --mark-overdue   # only check overdue tasks
```

## When Building or Modifying

- Always test with `--dry-run` first
- Start with `--limit 10` or `--limit 20` to verify task quality
- Check Tasks DB after creation — verify Context field explains the "why"
- Ensure no tasks were created for DNC or blocked contacts
- Verify Status uses `{"status": ...}` not `{"select": ...}`

## Stats Output

After each run, saves `last_action_stats.json`:
```json
{
  "created": 42,
  "skipped_open_task": 15,
  "skipped_blocked": 3,
  "skipped_no_rule": 0,
  "errors": 0
}
```

This file is read by `health_check.py` for pipeline validation.

Always follow the shared rules in `shared-sales-os-rules`.
