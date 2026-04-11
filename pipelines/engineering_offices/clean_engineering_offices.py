#!/usr/bin/env python3
"""
clean_engineering_offices.py
============================
Phase 1: Data Cleaning & Deduplication
مكاتب هندسية - وزارة الاسكان

Input:  Google Sheet CSV files (Sheet1 + Sheet2)
Output: cleaned_offices.json — ready for Notion sync

Run:
    python clean_engineering_offices.py
    python clean_engineering_offices.py --dry-run   # show stats only
    python clean_engineering_offices.py --output custom_output.json
"""

import csv, json, re, sys, argparse
from datetime import datetime
from pathlib import Path
from constants_eng import (
    SHEET1_PATH, SHEET2_PATH, REGION_MAP,
    F_NAME, F_REGION, F_CITY, F_CR, F_EMAIL, F_MOBILE, F_WA,
    F_COMPLETENESS, F_SOURCE, F_MANUAL_NOTE, F_MISS_EMAIL,
    F_MISS_MOBILE, F_DUP_SUSPECTED, F_MANUAL_REVIEW, F_READY
)

# ───────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────

REMOVE_SUFFIXES = [
    "شركة شخص واحد", "شخص واحد", "ل.ل.م", "للاستشارات الهندسية",
    "للهندسة المدنية", "للاستشارات المهنية", "للمساحة الأرضية",
    "للمساحة", "شركة", "مؤسسة",
]

def clean_company_name(name: str) -> str:
    """Remove trailing apostrophe and normalize Arabic text."""
    name = name.strip().rstrip("'").strip()
    return name

def normalize_company_name(name: str) -> str:
    """Create a simplified normalized name for dedup matching."""
    n = clean_company_name(name)
    for s in REMOVE_SUFFIXES:
        n = n.replace(s, "")
    n = re.sub(r"\s+", " ", n).strip()
    return n

def normalize_mobile(mobile: str) -> str:
    """Normalize mobile to 966XXXXXXXXX format."""
    m = re.sub(r"[^\d]", "", mobile.strip())
    if not m or m == "-":
        return ""
    if m.startswith("00966"):
        m = m[2:]
    if m.startswith("0") and len(m) == 10:
        m = "966" + m[1:]
    if not m.startswith("966") and len(m) == 9:
        m = "966" + m
    return m if len(m) >= 9 else ""

def normalize_whatsapp(wa: str) -> str:
    """Normalize WhatsApp — extract number or keep URL."""
    wa = wa.strip()
    if not wa or wa == "-":
        return ""
    if wa.startswith("https://wa.me/"):
        num = wa.replace("https://wa.me/", "").strip("/")
        return f"https://wa.me/{normalize_mobile(num)}" if normalize_mobile(num) else wa
    # Raw number
    num = normalize_mobile(wa)
    return f"https://wa.me/{num}" if num else ""

def normalize_email(email: str) -> str:
    """Lowercase and fix common typos."""
    e = email.strip().lower()
    if e == "-" or not e:
        return ""
    # Fix common typo: hotmail0com → hotmail.com
    e = re.sub(r"(hotmail|gmail|yahoo|outlook|live)(\d)com", r"\1.\2com", e)
    e = re.sub(r"@([a-z0-9]+)0com$", r"@\1.com", e)
    return e if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", e) else e

def extract_region_city(raw_location: str):
    """Extract region and city from 'جدة، منطقة مكة المكرمة' format."""
    raw_location = raw_location.strip()
    if not raw_location or raw_location == "-":
        return "", ""
    parts = raw_location.split("،")
    city = parts[0].strip()
    region_raw = ""
    if len(parts) > 1:
        region_raw = parts[1].replace("منطقة", "").strip()
    # Map to canonical region
    region = REGION_MAP.get(region_raw, REGION_MAP.get(city, "أخرى"))
    return region, city

def compute_completeness(rec: dict) -> int:
    """Score 0-100 based on key fields present."""
    score = 0
    if rec.get("email"): score += 30
    if rec.get("mobile"): score += 25
    if rec.get("cr") and rec.get("cr") != "-": score += 20
    if rec.get("region"): score += 10
    if rec.get("whatsapp"): score += 10
    if rec.get("name"): score += 5
    return score

# ───────────────────────────────────────────────
# Loader
# ───────────────────────────────────────────────

def load_csv(path: str, source_label: str) -> list[dict]:
    """Load and parse CSV file."""
    records = []
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            headers = next(reader)
            # Detect if 7th column (manual notes) exists
            has_notes_col = len(headers) > 6

            for i, row in enumerate(reader, start=2):
                if not row or not row[0].strip():
                    continue
                rec = {
                    "source_row": i,
                    "source": source_label,
                    "raw_name": row[0].strip() if len(row) > 0 else "",
                    "raw_region": row[1].strip() if len(row) > 1 else "",
                    "raw_cr": row[2].strip() if len(row) > 2 else "",
                    "raw_mobile": row[3].strip() if len(row) > 3 else "",
                    "raw_wa": row[4].strip() if len(row) > 4 else "",
                    "raw_email": row[5].strip() if len(row) > 5 else "",
                    "raw_manual_note": row[6].strip() if has_notes_col and len(row) > 6 else "",
                }
                records.append(rec)
    except FileNotFoundError:
        print(f"⚠️  File not found: {path}")
    return records

# ───────────────────────────────────────────────
# Main cleaning logic
# ───────────────────────────────────────────────

def clean_records(raw: list[dict]) -> list[dict]:
    cleaned = []
    for r in raw:
        name = clean_company_name(r["raw_name"])
        norm = normalize_company_name(r["raw_name"])
        region, city = extract_region_city(r["raw_region"])
        cr = r["raw_cr"].strip() if r["raw_cr"] and r["raw_cr"] != "-" else ""
        mobile = normalize_mobile(r["raw_mobile"])
        wa = normalize_whatsapp(r["raw_wa"])
        email = normalize_email(r["raw_email"])
        manual_note = r["raw_manual_note"].strip()

        rec = {
            "name": name,
            "normalized_name": norm,
            "region": region,
            "city": city,
            "cr": cr,
            "email": email,
            "mobile": mobile,
            "whatsapp": wa,
            "source": r["source"],
            "source_row": r["source_row"],
            "manual_note": manual_note,
            # Quality flags
            "missing_email": not bool(email),
            "missing_mobile": not bool(mobile),
            "duplicate_suspected": False,   # set in dedup step
            "needs_review": False,
        }
        rec["completeness"] = compute_completeness(rec)
        rec["ready_for_outreach"] = (
            bool(email)
            and not rec["missing_mobile"] is True
            and cr != ""
        )
        cleaned.append(rec)
    return cleaned

# ───────────────────────────────────────────────
# Deduplication
# ───────────────────────────────────────────────

def deduplicate(records: list[dict]) -> list[dict]:
    """
    Dedup priority:
    1. CR Number (exact match)
    2. Email (exact match)
    3. Mobile (exact match)
    4. Normalized name (fuzzy)
    Keep richest record (highest completeness score).
    """
    seen_cr: dict[str, dict] = {}
    seen_email: dict[str, dict] = {}
    seen_mobile: dict[str, dict] = {}
    seen_norm: dict[str, dict] = {}
    deduped = []

    for rec in records:
        dup_key = None

        if rec["cr"] and rec["cr"] in seen_cr:
            dup_key = "cr:" + rec["cr"]
            existing = seen_cr[rec["cr"]]
        elif rec["email"] and rec["email"] in seen_email:
            dup_key = "email:" + rec["email"]
            existing = seen_email[rec["email"]]
        elif rec["mobile"] and rec["mobile"] in seen_mobile:
            dup_key = "mobile:" + rec["mobile"]
            existing = seen_mobile[rec["mobile"]]
        elif rec["normalized_name"] and rec["normalized_name"] in seen_norm:
            dup_key = "name:" + rec["normalized_name"]
            existing = seen_norm[rec["normalized_name"]]

        if dup_key:
            # Mark both as suspected duplicates
            rec["duplicate_suspected"] = True
            existing["duplicate_suspected"] = True
            rec["needs_review"] = True
            existing["needs_review"] = True
            # Keep richer record
            if rec["completeness"] <= existing["completeness"]:
                continue  # skip current, keep existing

        # Register in lookup maps
        if rec["cr"]:
            seen_cr[rec["cr"]] = rec
        if rec["email"]:
            seen_email[rec["email"]] = rec
        if rec["mobile"]:
            seen_mobile[rec["mobile"]] = rec
        if rec["normalized_name"]:
            seen_norm[rec["normalized_name"]] = rec

        deduped.append(rec)

    return deduped

# ───────────────────────────────────────────────
# Stats
# ───────────────────────────────────────────────

def print_stats(original: list, cleaned: list):
    print("\n" + "═"*55)
    print("   DATA AUDIT — مكاتب هندسية - وزارة الاسكان")
    print("═"*55)
    print(f"  Total raw records:        {len(original)}")
    print(f"  After deduplication:      {len(cleaned)}")
    print(f"  Removed as duplicates:    {len(original) - len(cleaned)}")
    print()
    miss_email  = sum(1 for r in cleaned if r["missing_email"])
    miss_mobile = sum(1 for r in cleaned if r["missing_mobile"])
    dup_flag    = sum(1 for r in cleaned if r["duplicate_suspected"])
    review_flag = sum(1 for r in cleaned if r["needs_review"])
    ready       = sum(1 for r in cleaned if r["ready_for_outreach"])
    print(f"  Missing email:            {miss_email}")
    print(f"  Missing mobile:           {miss_mobile}")
    print(f"  Duplicate suspected:      {dup_flag}")
    print(f"  Needs manual review:      {review_flag}")
    print(f"  Ready for outreach:       {ready}")
    print()
    # Region breakdown
    from collections import Counter
    regions = Counter(r["region"] for r in cleaned)
    print("  Top regions:")
    for reg, cnt in regions.most_common(8):
        print(f"    {reg:<25} {cnt}")
    print("═"*55 + "\n")

# ───────────────────────────────────────────────
# Entry point
# ───────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Show stats only, no file write")
    parser.add_argument("--output", default="cleaned_offices.json", help="Output JSON file path")
    args = parser.parse_args()

    print("📂 Loading Sheet1...")
    raw1 = load_csv(SHEET1_PATH, "Sheet1")
    print(f"   → {len(raw1)} records")

    print("📂 Loading Sheet2 (updated)...")
    raw2 = load_csv(SHEET2_PATH, "Sheet2-Updated")
    print(f"   → {len(raw2)} records")

    # Merge: Sheet2 is newer/richer — give it priority
    # Combine them and let dedup keep the best
    all_raw = raw2 + raw1  # Sheet2 first so it wins ties in dedup
    print(f"\n🔀 Combined: {len(all_raw)} records — running dedup...")

    cleaned = clean_records(all_raw)
    deduped = deduplicate(cleaned)

    print_stats(all_raw, deduped)

    if args.dry_run:
        print("✅ Dry run — no file written.")
        return deduped

    out_path = Path(__file__).parent / args.output
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {len(deduped)} records → {out_path}")
    return deduped


if __name__ == "__main__":
    main()
