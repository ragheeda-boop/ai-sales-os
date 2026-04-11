# meetings/ — Revenue Intelligence Layer

Scripts that track meetings and convert them to opportunities.

## Scripts (currently in Phase 3 - Sync/)

| Script | Role |
|--------|------|
| `meeting_tracker.py` (v2.0) | Syncs meetings, auto-links Company from Contact, updates Company Stage |
| `meeting_analyzer.py` (v4.1) | Claude AI analysis: takeaways, sentiment, next steps |
| `opportunity_manager.py` (v2.0) | Meeting → Opportunity pipeline, ONE per company, stale detection 14d |

## Key Rule
meeting_analyzer.py requires ANTHROPIC_API_KEY in GitHub Secrets.
The workflow guards with: if: ${{ env.ANTHROPIC_API_KEY != '' }}
