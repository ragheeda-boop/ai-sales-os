"""
01_clean_deduplicate.py  — Muqawil Data Cleaner v1.0
Input : muqawil_output/data_raw.json
Output: muqawil_pipeline/cleaned_contractors.json
"""
import json, re, os
from collections import Counter
from datetime import datetime

BASE   = r"C:\Users\PC\Documents\AI Sales OS"
INPUT  = BASE + r"\muqawil_output\data_raw.json"
OUTDIR = BASE + r"\muqawil_pipeline"
OUTPUT = OUTDIR + r"\cleaned_contractors.json"
REPORT = OUTDIR + r"\dedup_report.json"
os.makedirs(OUTDIR, exist_ok=True)

REGION_MAP = {
    "الرياض":"الرياض","رياض":"الرياض",
    "مكة":"مكة المكرمة","مكه":"مكة المكرمة","مكة المكرمة":"مكة المكرمة",
    "جدة":"مكة المكرمة","جده":"مكة المكرمة",
    "الشرقية":"المنطقة الشرقية","الشرقيه":"المنطقة الشرقية",
    "المنطقة الشرقية":"المنطقة الشرقية",
    "القصيم":"القصيم","المدينة المنورة":"المدينة المنورة",
    "المدينه المنوره":"المدينة المنورة",
    "عسير":"عسير","نجران":"نجران","حائل":"حائل",
    "جازان":"جازان","تبوك":"تبوك","الجوف":"الجوف",
    "الباحة":"الباحة","الحدود الشمالية":"الحدود الشمالية",
}
SHARED_DOMAINS = {"gmail.com","hotmail.com","yahoo.com","outlook.com","live.com","icloud.com"}

def nt(t):
    if not t: return ""
    t = re.sub(r"\s+"," ",str(t).strip())
    t = re.sub(r"[\u0610-\u061A\u064B-\u065F\u0670]","",t)
    return t.strip()

def norm_name(n):
    n = nt(n).strip(".,،؛؟!-\u2013\u2014")
    n = re.sub(r"^شركه\b","شركة",n)
    n = re.sub(r"^مؤسسه\b","مؤسسة",n)
    return n.strip()

def norm_phone(p):
    if not p: return ""
    p = re.sub(r"[\s\-\.\(\)]","",str(p))
    if p.startswith("+966"): p = "0"+p[4:]
    elif p.startswith("00966"): p = "0"+p[5:]
    elif p.startswith("966") and len(p)>9: p = "0"+p[3:]
    p = re.sub(r"[^\d]","",p)
    return p if len(p)>=9 else ""

def norm_email(e):
    if not e: return ""
    e = str(e).lower().strip()
    return e if "@" in e and "[" not in e else ""

def norm_region(r):
    r = nt(r)
    return REGION_MAP.get(r,r)

def domain_of(email):
    return email.split("@")[-1].lower().strip() if email and "@" in email else ""

def completeness(r):
    w = {"email":25,"company_name":20,"region":10,"city":10,"phone":15,"membership_number":10,"address":5,"classification_grade":5}
    return sum(w[f] for f in w if str(r.get(f,"")).strip())

def clean_record(r):
    name  = norm_name(r.get("company_name",""))
    email = norm_email(r.get("email",""))
    phone = norm_phone(r.get("phone",""))
    region= norm_region(r.get("region",""))
    city  = nt(r.get("city",""))
    mem   = str(r.get("membership_number","")).strip()
    dom   = domain_of(email)
    score = completeness({"email":email,"company_name":name,"region":region,"city":city,"phone":phone,"membership_number":mem,"address":nt(r.get("address","")),"classification_grade":r.get("classification_grade","")})
    stage = "Ready for Initial Outreach" if email else "No Valid Email"
    action= "Enroll in Sequence" if email else "Find Contact / Enrich"
    return {
        "contractor_id":r.get("contractor_id",""),
        "membership_number":mem,
        "company_name":name,
        "normalized_name":re.sub(r"\s","",name.upper()),
        "contractor_type":nt(r.get("contractor_type","")),
        "member_since":r.get("member_since",""),
        "status":nt(r.get("status","")),
        "classification_grade":nt(r.get("classification_grade","")),
        "establishment_size":nt(r.get("establishment_size","")),
        "membership_badge":nt(r.get("membership_badge","")),
        "training_hours":nt(r.get("training_hours","")),
        "rating_stars":r.get("rating_stars",""),
        "city":city,"region":region,
        "address":nt(r.get("address","")),
        "email":email,"phone":phone,"domain":dom,
        "primary_contractor_count":r.get("primary_contractor_count",""),
        "subcontractor_count":r.get("subcontractor_count",""),
        "source_url":r.get("detail_url",r.get("company_url","")),
        "listing_page":r.get("listing_page",""),
        "scraped_at":r.get("scraped_at",""),
        "has_email":bool(email),"has_phone":bool(phone),"has_address":bool(nt(r.get("address",""))),
        "data_completeness_score":score,
        "ready_for_outreach":bool(email),
        "previous_outreach_detected":False,"previous_outreach_source":"",
        "duplicate_suspected":False,"needs_manual_review":False,
        "apollo_matched":False,"apollo_account_id":"","apollo_contact_id":"",
        "in_apollo_list":False,"in_sequence":False,"sequence_status":"",
        "follow_up_stage":stage,"next_action":action,
        "import_batch":datetime.now().strftime("%Y-%m-%d"),
    }

def deduplicate(records):
    seen_mem={};seen_email={};unique=[];removed=[];log=[]
    for r in records:
        mem=r.get("membership_number",""); email=r.get("email",""); dom=r.get("domain","")
        if mem and mem in seen_mem:
            r["duplicate_suspected"]=True;r["needs_manual_review"]=True
            removed.append({**r,"dup_reason":f"dup_membership:{mem}"});log.append({"reason":f"dup_membership","name":r["company_name"]});continue
        if email and email in seen_email and dom not in SHARED_DOMAINS:
            r["duplicate_suspected"]=True;r["needs_manual_review"]=True
            removed.append({**r,"dup_reason":f"dup_email:{email}"});log.append({"reason":"dup_email","name":r["company_name"]});continue
        if mem: seen_mem[mem]=len(unique)
        if email and dom not in SHARED_DOMAINS: seen_email[email]=len(unique)
        unique.append(r)
    return unique,removed,log

print("="*55)
print("Muqawil Data Cleaner v1.0 —",datetime.now().strftime("%Y-%m-%d %H:%M"))
print("="*55)
print(f"\n[1] Loading {INPUT}...")
with open(INPUT,encoding="utf-8") as f: raw=json.load(f)
print(f"    Raw records: {len(raw):,}")
print("\n[2] Cleaning...")
cleaned=[clean_record(r) for r in raw]
print(f"    Cleaned: {len(cleaned):,}")
print("\n[3] Deduplicating...")
unique,removed,log=deduplicate(cleaned)
total=len(unique)
print(f"    Unique : {total:,}")
print(f"    Removed: {len(removed):,}")
has_email=sum(1 for r in unique if r["has_email"])
has_phone=sum(1 for r in unique if r["has_phone"])
has_addr =sum(1 for r in unique if r["has_address"])
ready    =sum(1 for r in unique if r["ready_for_outreach"])
avg_score=sum(r["data_completeness_score"] for r in unique)/total if total else 0
print(f"\n=== FINAL STATS ===")
print(f"  Total unique     : {total:,}")
print(f"  Has valid email  : {has_email:,} ({has_email/total*100:.1f}%)")
print(f"  Has phone        : {has_phone:,} ({has_phone/total*100:.1f}%)")
print(f"  Has address      : {has_addr:,} ({has_addr/total*100:.1f}%)")
print(f"  Ready for outreach: {ready:,} ({ready/total*100:.1f}%)")
print(f"  Avg completeness : {avg_score:.1f}/100")
regs=Counter(r["region"] for r in unique)
print("\n=== TOP REGIONS ===")
[print(f"  {k}: {v:,}") for k,v in regs.most_common(12)]
print(f"\n[4] Saving cleaned data...")
with open(OUTPUT,"w",encoding="utf-8") as f: json.dump(unique,f,ensure_ascii=False,indent=2)
with open(REPORT,"w",encoding="utf-8") as f:
    json.dump({"run_at":datetime.now().isoformat(),"raw_count":len(raw),"unique_count":total,"removed_dupes":len(removed),"has_email":has_email,"has_phone":has_phone,"ready_for_outreach":ready,"avg_completeness":round(avg_score,1),"dedup_log":log[:200]},f,ensure_ascii=False,indent=2)
print(f"    -> {OUTPUT}")
print(f"    -> {REPORT}")
print("\n✅ DONE")
