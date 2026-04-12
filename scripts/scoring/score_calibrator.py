#!/usr/bin/env python3
"""
AI Sales OS — Score Calibrator (Self-Learning Weights)

Analyzes actual engagement outcomes (from Apollo Analytics + Notion) and
recommends weight adjustments for lead_score.py.

The feedback loop:
  Score → Action → Outcome → Calibrate → Better Score

Safety rails:
  - MAX_WEIGHT_CHANGE = 0.10 per cycle (no sudden jumps)
  - MIN_WEIGHT = 0.05 (no component goes to zero)
  - MIN_EMAILS_FOR_CALIBRATION = 100 (need enough data)
  - Saves full history in calibration_history.json
  - Never auto-applies unless --apply flag is used

Usage:
    python score_calibrator.py                  # analyze + recommend (no changes)
    python score_calibrator.py --apply          # apply recommended weights
    python score_calibrator.py --days 90        # analyze last 90 days
    python score_calibrator.py --export         # save analysis to file
"""
import os
import sys
import json
import logging
import time
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

# ─── Config ──────────────────────────────────────────────────────────────────

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
APOLLO_BASE_URL = "https://api.apollo.io/api/v1"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Safety rails
MAX_WEIGHT_CHANGE = 0.10     # Max shift per calibration cycle
MIN_WEIGHT = 0.05            # No component goes below 5%
MIN_EMAILS_FOR_CALIBRATION = 100  # Minimum emails sent for valid analysis

# Current weights (from lead_score.py)
CURRENT_WEIGHTS = {
    "intent": 0.10,
    "engagement": 0.10,
    "size": 0.45,
    "seniority": 0.35,
}

CALIBRATION_HISTORY_FILE = os.path.join(SCRIPT_DIR, "calibration_history.json")

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), "score_calibrator.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ─── Apollo Analytics ────────────────────────────────────────────────────────

def apollo_request(method: str, url: str, max_retries: int = 5, **kwargs):
    """Apollo API request with retry."""
    import requests
    kwargs.setdefault("timeout", 60)

    for attempt in range(max_retries):
        try:
            resp = requests.request(method, url, **kwargs)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                time.sleep(min(2 ** attempt, 30))
                continue
            raise

        if resp.status_code == 429:
            time.sleep(float(resp.headers.get("Retry-After", min(2 ** attempt, 30))))
            continue
        if resp.status_code >= 500:
            time.sleep(min(2 ** attempt, 30))
            continue

        resp.raise_for_status()
        return resp

    raise Exception(f"Failed after {max_retries} retries")


def fetch_analytics(metrics: List[str], group_by: Optional[List[str]] = None, days: int = 30) -> Dict:
    """Fetch analytics report from Apollo."""
    if days <= 30:
        date_range = {"modality": "last_30_days"}
    elif days <= 90:
        date_range = {"modality": "last_3_months"}
    else:
        date_range = {"modality": "last_6_months"}

    payload = {
        "api_key": APOLLO_API_KEY,
        "metrics": metrics,
        "date_range": date_range,
    }
    if group_by:
        payload["group_by"] = group_by

    try:
        resp = apollo_request("POST", f"{APOLLO_BASE_URL}/analytics/sync_report", json=payload)
        return resp.json()
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return {}


# ─── Data Collection ─────────────────────────────────────────────────────────

def collect_seniority_performance(days: int = 30) -> Dict[str, Dict]:
    """Get reply rates by seniority level."""
    data = fetch_analytics(
        metrics=["num_emails_sent", "num_emails_replied", "percent_emails_replied"],
        group_by=["person_seniority"],
        days=days,
    )

    results = {}
    for row in data.get("rows", []):
        seniority = row.get("person_seniority", "Unknown")
        results[seniority] = {
            "sent": row.get("num_emails_sent", 0),
            "replied": row.get("num_emails_replied", 0),
            "reply_rate": row.get("percent_emails_replied", 0),
        }

    return results


def collect_company_size_performance(days: int = 30) -> Dict[str, Dict]:
    """Get reply rates by company size."""
    data = fetch_analytics(
        metrics=["num_emails_sent", "num_emails_replied", "percent_emails_replied"],
        group_by=["organization_num_current_employees"],
        days=days,
    )

    results = {}
    for row in data.get("rows", []):
        size = row.get("organization_num_current_employees", "Unknown")
        results[str(size)] = {
            "sent": row.get("num_emails_sent", 0),
            "replied": row.get("num_emails_replied", 0),
            "reply_rate": row.get("percent_emails_replied", 0),
        }

    return results


def collect_overall_stats(days: int = 30) -> Dict:
    """Get overall email stats."""
    data = fetch_analytics(
        metrics=["num_emails_sent", "num_emails_replied", "percent_emails_replied"],
        days=days,
    )

    rows = data.get("rows", [])
    if rows:
        return {
            "total_sent": rows[0].get("num_emails_sent", 0),
            "total_replied": rows[0].get("num_emails_replied", 0),
            "avg_reply_rate": rows[0].get("percent_emails_replied", 0),
        }
    return {"total_sent": 0, "total_replied": 0, "avg_reply_rate": 0}


# ─── Analysis Engine ─────────────────────────────────────────────────────────

def analyze_mismatches(
    seniority_perf: Dict[str, Dict],
    size_perf: Dict[str, Dict],
    overall: Dict,
) -> Dict:
    """
    Analyze where scoring weights don't match actual performance.

    Key question: Are high-scored segments actually performing better?
    If not, weights need adjustment.
    """
    analysis = {
        "seniority_findings": [],
        "size_findings": [],
        "weight_recommendations": {},
        "data_quality": {},
    }

    total_sent = overall.get("total_sent", 0)
    analysis["data_quality"]["total_emails"] = total_sent
    analysis["data_quality"]["sufficient_data"] = total_sent >= MIN_EMAILS_FOR_CALIBRATION

    if total_sent < MIN_EMAILS_FOR_CALIBRATION:
        logger.warning(f"Insufficient data: {total_sent} emails sent (need {MIN_EMAILS_FOR_CALIBRATION})")
        analysis["weight_recommendations"] = CURRENT_WEIGHTS.copy()
        return analysis

    avg_reply = overall.get("avg_reply_rate", 0)

    # Seniority scoring map (matches lead_score.py)
    seniority_score_map = {
        "c_suite": 100, "founder": 95, "owner": 95, "partner": 90,
        "vp": 85, "head": 80, "director": 75, "senior": 65,
        "manager": 60, "entry": 25, "intern": 15,
    }

    # Check if high-scored seniorities actually perform better
    seniority_mismatch = 0
    for seniority, perf in seniority_perf.items():
        if perf["sent"] < 10:
            continue  # Not enough data

        seniority_key = seniority.lower().replace("-", "_").replace(" ", "_")
        assigned_score = seniority_score_map.get(seniority_key, 30)
        actual_reply = perf["reply_rate"]

        # If high-scored seniority has below-average reply rate = mismatch
        if assigned_score >= 75 and actual_reply < avg_reply:
            seniority_mismatch += 1
            analysis["seniority_findings"].append({
                "seniority": seniority,
                "assigned_score": assigned_score,
                "reply_rate": actual_reply,
                "avg_reply_rate": avg_reply,
                "verdict": "OVERSCORED",
                "detail": f"{seniority} scores {assigned_score}/100 but only {actual_reply:.1f}% reply rate (avg: {avg_reply:.1f}%)",
            })

        # If low-scored seniority has above-average reply rate = mismatch
        elif assigned_score <= 60 and actual_reply > avg_reply * 1.5:
            seniority_mismatch += 1
            analysis["seniority_findings"].append({
                "seniority": seniority,
                "assigned_score": assigned_score,
                "reply_rate": actual_reply,
                "avg_reply_rate": avg_reply,
                "verdict": "UNDERSCORED",
                "detail": f"{seniority} only scores {assigned_score}/100 but has {actual_reply:.1f}% reply rate (avg: {avg_reply:.1f}%)",
            })

    # Calculate recommended weights
    new_weights = CURRENT_WEIGHTS.copy()

    # If seniority has mismatches, slightly reduce its weight
    if seniority_mismatch >= 2:
        shift = min(MAX_WEIGHT_CHANGE, seniority_mismatch * 0.03)
        new_weights["seniority"] = max(new_weights["seniority"] - shift, MIN_WEIGHT)
        # Redistribute to engagement (since we have actual engagement data now)
        new_weights["engagement"] = min(new_weights["engagement"] + shift, 0.40)
        logger.info(f"Seniority has {seniority_mismatch} mismatches → shifting {shift:.2f} to engagement")

    # If engagement data is now available, boost its weight
    if total_sent >= 500:
        if new_weights["engagement"] < 0.20:
            shift = min(MAX_WEIGHT_CHANGE, 0.05)
            new_weights["engagement"] += shift
            # Take from the largest weight
            largest = max(new_weights, key=new_weights.get)
            new_weights[largest] -= shift

    # Normalize to sum to 1.0
    total = sum(new_weights.values())
    if total > 0:
        new_weights = {k: round(v / total, 3) for k, v in new_weights.items()}

    analysis["weight_recommendations"] = new_weights

    return analysis


# ─── Apply Weights ───────────────────────────────────────────────────────────

def apply_weights(new_weights: Dict[str, float]) -> bool:
    """
    Apply new weights to lead_score.py.
    Modifies the WEIGHT_* constants in the file.
    """
    lead_score_path = os.path.join(SCRIPT_DIR, "lead_score.py")

    try:
        with open(lead_score_path, "r", encoding="utf-8") as f:
            content = f.read()

        import re

        # Replace weight values
        weight_map = {
            "WEIGHT_INTENT": new_weights.get("intent", 0.10),
            "WEIGHT_ENGAGEMENT": new_weights.get("engagement", 0.10),
            "WEIGHT_SIZE": new_weights.get("size", 0.45),
            "WEIGHT_SENIORITY": new_weights.get("seniority", 0.35),
        }

        for var_name, new_val in weight_map.items():
            pattern = rf"({var_name}\s*=\s*)\d+\.\d+"
            replacement = rf"\g<1>{new_val:.3f}"
            content = re.sub(pattern, replacement, content)

        with open(lead_score_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Weights applied to {lead_score_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to apply weights: {e}")
        return False


# ─── History ─────────────────────────────────────────────────────────────────

def load_history() -> List[Dict]:
    """Load calibration history."""
    if os.path.exists(CALIBRATION_HISTORY_FILE):
        try:
            with open(CALIBRATION_HISTORY_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_to_history(analysis: Dict, applied: bool):
    """Save this calibration run to history."""
    history = load_history()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "previous_weights": CURRENT_WEIGHTS,
        "recommended_weights": analysis.get("weight_recommendations", {}),
        "applied": applied,
        "findings_count": len(analysis.get("seniority_findings", [])) + len(analysis.get("size_findings", [])),
        "data_quality": analysis.get("data_quality", {}),
    }
    history.append(entry)

    try:
        with open(CALIBRATION_HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save history: {e}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AI Sales OS — Score Calibrator")
    parser.add_argument("--apply", action="store_true", help="Apply recommended weights to lead_score.py")
    parser.add_argument("--days", type=int, default=30, help="Analysis period in days")
    parser.add_argument("--export", action="store_true", help="Save analysis to file")
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info(f"SCORE CALIBRATOR | Days: {args.days} | Apply: {args.apply}")
    logger.info("=" * 70)

    start_time = time.time()

    # Step 1: Collect data
    logger.info("Step 1: Collecting performance data from Apollo Analytics...")
    logger.info("  Current weights: " + json.dumps(CURRENT_WEIGHTS))

    seniority_perf = collect_seniority_performance(days=args.days)
    logger.info(f"  Seniority data: {len(seniority_perf)} segments")

    size_perf = collect_company_size_performance(days=args.days)
    logger.info(f"  Company size data: {len(size_perf)} segments")

    overall = collect_overall_stats(days=args.days)
    logger.info(f"  Overall: {overall['total_sent']} emails sent, {overall['avg_reply_rate']:.1f}% reply rate")

    # Step 2: Analyze mismatches
    logger.info("Step 2: Analyzing scoring mismatches...")
    analysis = analyze_mismatches(seniority_perf, size_perf, overall)

    # Report findings
    for finding in analysis.get("seniority_findings", []):
        logger.info(f"  [{finding['verdict']}] {finding['detail']}")

    for finding in analysis.get("size_findings", []):
        logger.info(f"  [{finding['verdict']}] {finding['detail']}")

    recommended = analysis.get("weight_recommendations", {})
    logger.info(f"  Recommended weights: {json.dumps(recommended)}")

    # Check if weights changed
    weights_changed = any(
        abs(recommended.get(k, v) - v) > 0.001
        for k, v in CURRENT_WEIGHTS.items()
    )

    if not weights_changed:
        logger.info("  No weight changes recommended — current weights are performing well")

    # Step 3: Apply if requested
    applied = False
    if args.apply and weights_changed:
        logger.info("Step 3: Applying new weights...")
        applied = apply_weights(recommended)
        if applied:
            logger.info("  Weights updated successfully!")
            logger.info("  IMPORTANT: Run 'python lead_score.py --force' to recalculate all scores")
    elif args.apply and not weights_changed:
        logger.info("Step 3: No changes to apply")
    else:
        logger.info("Step 3: Review mode — use --apply to apply changes")

    # Save history
    save_to_history(analysis, applied)

    # Export
    if args.export:
        export_file = os.path.join(SCRIPT_DIR, f"calibration_analysis_{datetime.now().strftime('%Y%m%d')}.json")
        with open(export_file, "w") as f:
            json.dump({
                "current_weights": CURRENT_WEIGHTS,
                "recommended_weights": recommended,
                "seniority_performance": seniority_perf,
                "size_performance": size_perf,
                "overall_stats": overall,
                "findings": analysis.get("seniority_findings", []) + analysis.get("size_findings", []),
            }, f, indent=2)
        logger.info(f"  Analysis exported to {export_file}")

    elapsed = time.time() - start_time

    logger.info("=" * 70)
    logger.info(f"SCORE CALIBRATOR COMPLETE | Time: {elapsed:.1f}s")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
