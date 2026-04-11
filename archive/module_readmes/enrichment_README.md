# enrichment/ — Signal Intelligence Layer

Scripts that add intelligence signals to companies and contacts.

## Scripts (currently in Phase 3 - Sync/)

| Script | Role |
|--------|------|
| `job_postings_enricher.py` (v4.0) | Job Postings API → Intent Score for companies |
| `muhide_strategic_analysis.py` | Claude AI → Fit Score(1-100), Priority(P1-P3), Best Buyer, Outreach Angle |
| `analytics_tracker.py` (v4.0) | Apollo Analytics → engagement data back to Notion |

## MUHIDE Analysis Stats (verified from JSON)
- 15,372 companies analyzed
- P1: 2,517 | P2: 2,995 | P3: 9,860
- Write time: 7,500 seconds
- Requires ANTHROPIC_API_KEY
