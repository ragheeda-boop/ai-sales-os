
import json, os, sys, re
from collections import Counter

PYPATH = r"C:\Users\PC\AppData\Local\Python\bin\python.exe"
path = r"C:\Users\PC\Documents\AI Sales OS\muqawil_output"

# ── File discovery ──
files = os.listdir(path)
print("=== FILE DISCOVERY ===")
for f in files:
    fp = os.path.join(path, f)
    size = os.path.getsize(fp)
    print(f"  {f}  ({size:,} bytes)")

# ── Read checkpoint ──
print("\n=== CHECKPOINT ===")
with open(os.path.join(path, "checkpoint.json"), encoding="utf-8") as f:
    cp = json.load(f)
print(json.dumps(cp, ensure_ascii=False, indent=2)[:800])

# ── Read raw JSON ──
print("\n=== RAW JSON DATA ===")
with open(os.path.join(path, "data_raw.json"), encoding="utf-8") as f:
    data = json.load(f)
print(f"Total records: {len(data)}")
print(f"Columns: {list(data[0].keys()) if data else []}")

print("\n=== SAMPLE RECORDS ===")
for i in range(min(3, len(data))):
    print(f"\n--- Record {i+1} ---")
    for k, v in data[i].items():
        if v:
            print(f"  {k}: {v}")

# ── Data quality audit ──
print("\n=== DATA QUALITY AUDIT ===")
total = len(data)

def pct(n): return f"{n}/{total} ({n/total*100:.1f}%)"

fields_to_check = [
    "membership_number","company_name","city","region","address",
    "phone","email","contractor_type","establishment_size",
    "training_hours","member_since","classification_grade",
    "rating_stars","detail_url"
]
for field in fields_to_check:
    filled = sum(1 for r in data if r.get(field, "").strip() if isinstance(r.get(field,""), str) else bool(r.get(field)))
    print(f"  {field}: {pct(filled)}")

# ── Duplicate analysis ──
print("\n=== DUPLICATE ANALYSIS ===")
mem_nums = [r.get("membership_number","") for r in data]
emails = [r.get("email","").lower().strip() for r in data]
phones = [r.get("phone","").strip() for r in data]
names = [r.get("company_name","").strip() for r in data]

dup_mem = sum(1 for v,c in Counter(mem_nums).items() if c>1 and v)
dup_email = sum(1 for v,c in Counter(emails).items() if c>1 and v)
dup_phone = sum(1 for v,c in Counter(phones).items() if c>1 and v)
dup_name = sum(1 for v,c in Counter(names).items() if c>1 and v)

print(f"  Duplicate membership numbers: {dup_mem}")
print(f"  Duplicate emails: {dup_email}")
print(f"  Duplicate phones: {dup_phone}")
print(f"  Duplicate company names: {dup_name}")

# ── Email quality ──
print("\n=== EMAIL QUALITY ===")
valid_email = sum(1 for r in data if "@" in r.get("email","") and "[" not in r.get("email",""))
cf_protected = sum(1 for r in data if "protected" in r.get("email","").lower() or "[" in r.get("email",""))
empty_email = sum(1 for r in data if not r.get("email","").strip())
print(f"  Valid emails: {pct(valid_email)}")
print(f"  CF protected (not decoded): {cf_protected}")
print(f"  Empty emails: {empty_email}")

# ── Phone quality ──
print("\n=== PHONE QUALITY ===")
has_phone = sum(1 for r in data if r.get("phone","").strip())
print(f"  Has phone: {pct(has_phone)}")

# ── Region breakdown ──
print("\n=== REGION BREAKDOWN (top 15) ===")
regions = Counter(r.get("region","(empty)").strip() for r in data)
for reg, cnt in regions.most_common(15):
    print(f"  {reg}: {cnt}")

# ── Establishment size breakdown ──
print("\n=== ESTABLISHMENT SIZE ===")
sizes = Counter(r.get("establishment_size","(empty)").strip() for r in data)
for s, cnt in sizes.most_common():
    print(f"  {s}: {cnt}")

# ── Contractor type ──
print("\n=== CONTRACTOR TYPE ===")
types = Counter(r.get("contractor_type","(empty)").strip() for r in data)
for t, cnt in types.most_common():
    print(f"  {t}: {cnt}")

# ── Ready for outreach ──
print("\n=== OUTREACH READINESS ===")
ready = sum(1 for r in data 
            if "@" in r.get("email","") and "[" not in r.get("email","")
            and r.get("company_name","").strip())
print(f"  Ready for outreach (has valid email + name): {pct(ready)}")
not_ready = total - ready
print(f"  Not ready: {not_ready}")

print("\n=== DONE ===")
