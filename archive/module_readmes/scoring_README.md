# scoring/ — Lead Intelligence Layer

All scripts related to scoring, ranking, and readiness evaluation.

## Scripts (currently in Phase 3 - Sync/)

| Script | Role |
|--------|------|
| `lead_score.py` (v1.5) | Computes Lead Score (0-100), Lead Tier (HOT/WARM/COLD), Sort Score |
| `score_calibrator.py` | Self-learning: analyzes outcomes and recommends weight adjustments |
| `action_ready_updater.py` | Evaluates 5 conditions to set Action Ready checkbox |

## Scoring Formula (v1.5)
Score = Size(35%) + Seniority(30%) + Industry(15%) + Intent(10%) + Engagement(10%)
HOT ≥ 80 | WARM ≥ 50 | COLD < 50

## Key Rule
WARM-HIGH is NOT a real tier. The code only outputs HOT/WARM/COLD.
