#!/usr/bin/env python3
"""Archive stale contractors (in Notion but not in new muqawil scrape)."""
import os, json, time, requests, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

KEY = os.environ['NOTION_API_KEY']
DB = "25384c7f9128462b8737773004e7d1bd"
H = {"Authorization": f"Bearer {KEY}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}

# Load current cleaned mems
with open('pipelines/muqawil/pipeline/cleaned_contractors.json') as f:
    cleaned = {str(r.get('membership_number','')).strip() for r in json.load(f) if r.get('membership_number')}

# Page through Notion, collecting stale pages
print("Scanning Notion for stale contractors...")
stale_pages = []  # (page_id, mem)
cursor = None
pages_scanned = 0
while True:
    body = {"page_size": 100}
    if cursor: body["start_cursor"] = cursor
    r = requests.post(f"https://api.notion.com/v1/databases/{DB}/query", headers=H, json=body, timeout=60)
    if r.status_code != 200:
        print("ERR", r.status_code, r.text[:300]); sys.exit(1)
    d = r.json()
    for p in d["results"]:
        mn_prop = p["properties"].get("Membership Number", {}).get("rich_text", [])
        if not mn_prop: continue
        mem = mn_prop[0]["plain_text"].strip()
        if mem and mem not in cleaned:
            # Skip if already archived
            fs = p["properties"].get("Follow-up Stage", {}).get("select")
            if fs and fs.get("name") == "Stale / Removed from Source":
                continue
            stale_pages.append((p["id"], mem))
    pages_scanned += 1
    if pages_scanned % 20 == 0:
        print(f"  scanned {pages_scanned} pages, {len(stale_pages)} stale found")
    if not d.get("has_more"): break
    cursor = d.get("next_cursor")

print(f"\nTotal stale contractors to archive: {len(stale_pages)}")

# Archive each
def archive(page_id):
    body = {"properties": {
        "Follow-up Stage": {"select": {"name": "Stale / Removed from Source"}},
        "Ready for Outreach": {"checkbox": False},
        "Next Action": {"select": {"name": "No Action"}}
    }}
    for attempt in range(6):
        try:
            r = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=H, json=body, timeout=30)
        except Exception as e:
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 200: return True, None
        if r.status_code == 429:
            time.sleep(3 * (attempt + 1))
            continue
        if r.status_code >= 500:
            time.sleep(2 ** attempt)
            continue
        return False, f"{r.status_code}:{r.text[:150]}"
    return False, "max_retries"

done = 0
failed = 0
errors_sample = []
start = time.time()
with ThreadPoolExecutor(max_workers=2) as ex:
    futs = {ex.submit(archive, pid): mem for pid, mem in stale_pages}
    for f in as_completed(futs):
        ok, err = f.result()
        if ok: done += 1
        else:
            failed += 1
            if len(errors_sample) < 5 and err:
                errors_sample.append(err)
        if (done + failed) % 200 == 0:
            elapsed = time.time() - start
            rate = (done + failed) / elapsed
            eta = (len(stale_pages) - done - failed) / rate if rate > 0 else 0
            print(f"  {done + failed}/{len(stale_pages)}  ok={done} fail={failed}  ETA={eta/60:.1f}min", flush=True)
            if errors_sample:
                print(f"    sample error: {errors_sample[0]}", flush=True)

print(f"\nDone. Archived: {done}, Failed: {failed}")
if errors_sample:
    print("Errors sample:")
    for e in errors_sample: print(f"  {e}")
