# automation/ — Action & Execution Layer

Scripts that convert scores into actions and track outcomes.

## Scripts (currently in Phase 3 - Sync/)

| Script | Role |
|--------|------|
| `auto_tasks.py` (v2.0) | Creates company-level tasks: HOT→"Urgent Call", WARM→"Follow-up" |
| `auto_sequence.py` | Enrolls Action Ready contacts in Apollo Sequences |
| `outcome_tracker.py` (v1.0) | Closes Task→Contact loop: Contact Responded, Last Contacted, Meeting Booked |
| `cleanup_overdue_tasks.py` | One-time: bulk-closes legacy pre-v5.0 contact-level tasks |

## Critical Rule: Task Type Separation
HOT → task_type = "Urgent Call"
WARM → task_type = "Follow-up"
These MUST differ for company-level dedup to work correctly.
