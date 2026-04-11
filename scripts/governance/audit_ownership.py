#!/usr/bin/env python3
"""Audit ownership gaps - uses direct requests with longer timeout."""
import os, json, sys, requests, time
from dotenv import load_dotenv
load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_VERSION = "2022-06-28"
BASE = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}

CONTACTS_DB = os.getenv("NOTION_DATABASE_ID_CONTACTS")
COMPANIES_DB = os.getenv("NOTION_DATABASE_ID_COMPANIES")
TASKS_DB = os.getenv("NOTION_DATABASE_ID_TASKS")
MEETINGS_DB = os.getenv("NOTION_DATABASE_ID_MEETINGS")
OPPS_DB = os.getenv("NOTION_DATABASE_ID_OPPORTUNITIES")

def query_db(db_id, label, max_pages=50):
    """Query database with pagination, max_pages to limit."""
    results = []
    cursor = None
    page_count = 0
    while page_count < max_pages:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        try:
            resp = requests.post(
                f"{BASE}/databases/{db_id}/query",
                headers=HEADERS, json=body, timeout=60
            )
            if resp.status_code == 429:
                time.sleep(2)
                continue
            data = resp.json()
        except Exception as e:
            print(f"  Error querying {label}: {e}")
            break
        
        results.extend(data.get("results", []))
        page_count += 1
        
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        time.sleep(0.4)  # rate limit
    
    return results

def get_rt(props, field):
    rt = props.get(field, {}).get("rich_text", [])
    return rt[0].get("plain_text", "").strip() if rt else ""

def get_sel(props, field):
    s = props.get(field, {}).get("select")
    return s.get("name", "") if s else ""

def get_status(props, field):
    s = props.get(field, {}).get("status")
    return s.get("name", "") if s else ""

def get_rel(props, field):
    return [r["id"] for r in props.get(field, {}).get("relation", [])]

print("=" * 70)
print("AI SALES OS — OWNERSHIP AUDIT (LIVE DATA)")
print("=" * 70)

# ── CONTACTS ──
print("\n📋 CONTACTS...")
contacts = query_db(CONTACTS_DB, "contacts", max_pages=100)
print(f"  Total: {len(contacts)}")

c_stats = {"no_owner": 0, "no_company": 0, "no_email": 0, "no_score": 0, "no_tier": 0, "owners": {}}
for p in contacts:
    props = p.get("properties", {})
    owner = get_rt(props, "Contact Owner")
    if not owner: c_stats["no_owner"] += 1
    else: c_stats["owners"][owner] = c_stats["owners"].get(owner, 0) + 1
    if not get_rel(props, "Company"): c_stats["no_company"] += 1
    if not props.get("Email", {}).get("email"): c_stats["no_email"] += 1
    if props.get("Lead Score", {}).get("number") is None: c_stats["no_score"] += 1
    if not get_sel(props, "Lead Tier"): c_stats["no_tier"] += 1

n = max(len(contacts), 1)
print(f"  No Owner:   {c_stats['no_owner']} ({c_stats['no_owner']*100/n:.1f}%)")
print(f"  No Company: {c_stats['no_company']} ({c_stats['no_company']*100/n:.1f}%)")
print(f"  No Email:   {c_stats['no_email']} ({c_stats['no_email']*100/n:.1f}%)")
print(f"  No Score:   {c_stats['no_score']} ({c_stats['no_score']*100/n:.1f}%)")
print(f"  No Tier:    {c_stats['no_tier']} ({c_stats['no_tier']*100/n:.1f}%)")
print(f"  Owners: {json.dumps(c_stats['owners'])}")

# ── COMPANIES ──
print("\n🏢 COMPANIES...")
companies = query_db(COMPANIES_DB, "companies", max_pages=200)
print(f"  Total: {len(companies)}")

co_stats = {"no_owner": 0, "no_stage": 0, "no_active": 0, "stages": {}, "owners": {}}
for p in companies:
    props = p.get("properties", {})
    owner = get_sel(props, "Primary Company Owner")
    if not owner: co_stats["no_owner"] += 1
    else: co_stats["owners"][owner] = co_stats["owners"].get(owner, 0) + 1
    stage = get_sel(props, "Company Stage")
    if not stage: co_stats["no_stage"] += 1
    else: co_stats["stages"][stage] = co_stats["stages"].get(stage, 0) + 1
    ac = props.get("Active Contacts", {}).get("number")
    if not ac: co_stats["no_active"] += 1

n = max(len(companies), 1)
print(f"  No Primary Owner: {co_stats['no_owner']} ({co_stats['no_owner']*100/n:.1f}%)")
print(f"  No Stage:         {co_stats['no_stage']} ({co_stats['no_stage']*100/n:.1f}%)")
print(f"  No Active Cntcts: {co_stats['no_active']} ({co_stats['no_active']*100/n:.1f}%)")
print(f"  Stages: {json.dumps(co_stats['stages'])}")
print(f"  Owners: {json.dumps(co_stats['owners'])}")

# ── TASKS ──
print("\n✅ TASKS...")
tasks = query_db(TASKS_DB, "tasks", max_pages=20)
print(f"  Total: {len(tasks)}")

t_stats = {"no_owner": 0, "no_company": 0, "no_contact": 0, "auto": 0, "statuses": {}, "owners": {}}
for p in tasks:
    props = p.get("properties", {})
    owner = get_sel(props, "Task Owner")
    if not owner: t_stats["no_owner"] += 1
    else: t_stats["owners"][owner] = t_stats["owners"].get(owner, 0) + 1
    if not get_rel(props, "Company"): t_stats["no_company"] += 1
    if not get_rel(props, "Contact"): t_stats["no_contact"] += 1
    if props.get("Auto Created", {}).get("checkbox"): t_stats["auto"] += 1
    status = get_status(props, "Status")
    t_stats["statuses"][status or "empty"] = t_stats["statuses"].get(status or "empty", 0) + 1

n = max(len(tasks), 1)
print(f"  No Task Owner:  {t_stats['no_owner']} ({t_stats['no_owner']*100/n:.1f}%)")
print(f"  No Company:     {t_stats['no_company']} ({t_stats['no_company']*100/n:.1f}%)")
print(f"  No Contact:     {t_stats['no_contact']} ({t_stats['no_contact']*100/n:.1f}%)")
print(f"  Auto Created:   {t_stats['auto']} ({t_stats['auto']*100/n:.1f}%)")
print(f"  Statuses: {json.dumps(t_stats['statuses'])}")
print(f"  Owners:   {json.dumps(t_stats['owners'])}")

# ── MEETINGS ──
print("\n📅 MEETINGS...")
meetings = query_db(MEETINGS_DB, "meetings", max_pages=5)
print(f"  Total: {len(meetings)}")

m_stats = {"no_owner": 0, "no_company": 0, "no_contact": 0, "owners": {}}
for p in meetings:
    props = p.get("properties", {})
    owner = get_sel(props, "Meeting Owner")
    if not owner: m_stats["no_owner"] += 1
    else: m_stats["owners"][owner] = m_stats["owners"].get(owner, 0) + 1
    if not get_rel(props, "Company"): m_stats["no_company"] += 1
    if not get_rel(props, "Primary Contact"): m_stats["no_contact"] += 1

n = max(len(meetings), 1)
print(f"  No Owner:   {m_stats['no_owner']} ({m_stats['no_owner']*100/n:.1f}%)")
print(f"  No Company: {m_stats['no_company']} ({m_stats['no_company']*100/n:.1f}%)")
print(f"  No Contact: {m_stats['no_contact']} ({m_stats['no_contact']*100/n:.1f}%)")

# ── OPPORTUNITIES ──
print("\n💰 OPPORTUNITIES...")
opps = query_db(OPPS_DB, "opportunities", max_pages=5)
print(f"  Total: {len(opps)}")

o_stats = {"no_owner": 0, "no_company": 0, "no_contact": 0}
for p in opps:
    props = p.get("properties", {})
    if not get_rt(props, "Company Owner Snapshot"): o_stats["no_owner"] += 1
    if not get_rel(props, "Company"): o_stats["no_company"] += 1
    if not get_rel(props, "Primary Contact"): o_stats["no_contact"] += 1

print(f"  No Owner:   {o_stats['no_owner']}")
print(f"  No Company: {o_stats['no_company']}")
print(f"  No Contact: {o_stats['no_contact']}")

# ── SAVE ──
audit = {
    "contacts": {"total": len(contacts), **c_stats},
    "companies": {"total": len(companies), **co_stats},
    "tasks": {"total": len(tasks), **t_stats},
    "meetings": {"total": len(meetings), **m_stats},
    "opportunities": {"total": len(opps), **o_stats},
}
with open("/tmp/audit_data.json", "w") as f:
    json.dump(audit, f, indent=2)

print("\n" + "=" * 70)
total = len(contacts) + len(companies) + len(tasks) + len(meetings) + len(opps)
no_owner = c_stats["no_owner"] + co_stats["no_owner"] + t_stats["no_owner"] + m_stats["no_owner"] + o_stats["no_owner"]
no_company = c_stats["no_company"] + t_stats["no_company"] + m_stats["no_company"] + o_stats["no_company"]
print(f"TOTAL RECORDS: {total}")
print(f"TOTAL NO OWNER: {no_owner} ({no_owner*100/max(total,1):.1f}%)")
print(f"TOTAL NO COMPANY: {no_company} ({no_company*100/max(total,1):.1f}%)")
print("=" * 70)
