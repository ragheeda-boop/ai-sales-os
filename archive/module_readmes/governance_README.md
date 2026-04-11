# governance/ — Data Quality & Compliance Layer

Scripts that enforce data standards and prevent junk from entering the system.

## Scripts (currently in Phase 3 - Sync/)

| Script | Role |
|--------|------|
| `ingestion_gate.py` (v6.0) | Gate: companies need 2/5 criteria, contacts need 4/4 |
| `data_governor.py` (v6.0) | Retroactive governance: audits existing Notion records |
| `archive_unqualified.py` (v4.4) | Archives contacts without owner/email → Stage = Archived |
| `audit_ownership.py` | Audits ownership gaps across all 5 Notion DBs |
| `fix_seniority.py` | ONE-TIME: normalized "C suite" → "C-Suite". Run once only. |

## ingestion_gate.py CLI (corrected)
```bash
python ingestion_gate.py --dry-run         # audit mode
python ingestion_gate.py --enforce         # alias for --mode strict
python ingestion_gate.py --mode strict     # strict enforcement
python ingestion_gate.py --mode review     # pass review-tier records
```
