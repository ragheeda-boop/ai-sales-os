"""
=============================================================
AI Sales OS — Company ↔ Contact Relation Linker
=============================================================
هذا السكريبت يربط كل جهة اتصال (Contact) بالشركة (Company)
المناسبة في Notion عبر حقل العلاقة (Relation)
باستخدام مفتاح المطابقة: Apollo Account Id

المتطلبات:
  pip install requests

الاستخدام:
  1. انسخ Integration Token من Notion:
     - اذهب إلى https://www.notion.so/profile/integrations
     - أنشئ Integration جديد أو استخدم الموجود
     - انسخ الـ Token (يبدأ بـ ntn_ أو secret_)
  2. تأكد أن الـ Integration مضاف للصفحتين:
     - افتح قاعدة Companies في Notion → ... → Connections → أضف الـ Integration
     - افتح قاعدة Contacts في Notion → ... → Connections → أضف الـ Integration
  3. شغّل السكريبت:
     python link_companies_contacts.py
=============================================================
"""

import os
import requests
import time
import json
import sys
from datetime import datetime

# ============================================================
# الإعدادات — عدّل هنا فقط
# ============================================================

NOTION_TOKEN = os.getenv("NOTION_TOKEN", "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")

COMPANIES_DB_ID = "331e04a62da74afe9ab6b0efead39200"
CONTACTS_DB_ID = "9ca842d20aa9460bbdd958d0aa940d9c"

# سرعة الطلبات (Notion يسمح ~3 طلبات/ثانية)
REQUEST_DELAY = 0.35  # ثانية بين كل طلب
REQUEST_RETRIES = 5
BACKOFF_FACTOR = 2

# ملف السجل
LOG_FILE = "linking_log.json"

# ============================================================
# ثوابت
# ============================================================

NOTION_API = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def log(msg):
    """طباعة مع الوقت"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")


def notion_request(method, endpoint, payload=None, retries=3):
    """طلب Notion API مع إعادة المحاولة عند rate limit"""
    url = f"{NOTION_API}/{endpoint}"
    for attempt in range(retries):
        try:
            if method == "POST":
                resp = requests.post(url, headers=HEADERS, json=payload or {})
            elif method == "PATCH":
                resp = requests.patch(url, headers=HEADERS, json=payload or {})
            elif method == "GET":
                resp = requests.get(url, headers=HEADERS)
            else:
                raise ValueError(f"Unknown method: {method}")

            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                # Rate limit — انتظر وأعد المحاولة
                retry_after = float(resp.headers.get("Retry-After", 2))
                log(f"⏳ Rate limit — انتظار {retry_after} ثانية...")
                time.sleep(retry_after)
                continue
            elif resp.status_code in (500, 502, 503, 504):
                backoff = min(30, REQUEST_DELAY * (BACKOFF_FACTOR ** attempt))
                log(f"⚠️ خادم Notion {resp.status_code} — إعادة محاولة بعد {backoff:.1f} ثانية...")
                time.sleep(backoff)
                continue
            else:
                log(f"❌ خطأ {resp.status_code}: {resp.text[:200]}")
                if attempt < retries - 1:
                    time.sleep(1)
                    continue
                return None
        except requests.exceptions.RequestException as e:
            log(f"❌ خطأ اتصال: {e}")
            if attempt < retries - 1:
                time.sleep(2)
                continue
            return None
    return None


def get_text_property(page, prop_name):
    """استخراج قيمة حقل نصي من صفحة Notion"""
    prop = page.get("properties", {}).get(prop_name, {})
    prop_type = prop.get("type", "")

    if prop_type == "rich_text":
        texts = prop.get("rich_text", [])
        return texts[0]["plain_text"].strip() if texts else ""
    elif prop_type == "title":
        texts = prop.get("title", [])
        return texts[0]["plain_text"].strip() if texts else ""
    return ""


def get_relation_property(page, prop_name):
    """استخراج قائمة العلاقات من حقل relation"""
    prop = page.get("properties", {}).get(prop_name, {})
    return prop.get("relation", [])


# ============================================================
# الخطوة 1: بناء خريطة الشركات
# ============================================================

def build_company_map():
    """
    استعلام كل الشركات من Notion وبناء:
    company_map = {Apollo Account Id: page_id}
    """
    log("=" * 60)
    log("📊 الخطوة 1: بناء خريطة الشركات (Company Map)")
    log("=" * 60)

    company_map = {}
    cursor = None
    page_num = 0

    while True:
        page_num += 1
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor

        result = notion_request("POST", f"databases/{COMPANIES_DB_ID}/query", payload)
        if not result:
            log("❌ فشل استعلام الشركات!")
            break

        batch = result.get("results", [])
        for page in batch:
            apollo_id = get_text_property(page, "Apollo Account Id")
            page_id = page["id"]
            if apollo_id:
                company_map[apollo_id] = page_id

        log(f"  📦 الصفحة {page_num}: {len(batch)} شركة — الإجمالي: {len(company_map)}")

        if not result.get("has_more", False):
            break
        cursor = result.get("next_cursor")
        time.sleep(REQUEST_DELAY)

    log(f"✅ تم بناء خريطة الشركات: {len(company_map)} شركة")
    return company_map


# ============================================================
# الخطوة 2: ربط جهات الاتصال
# ============================================================

def link_contacts(company_map):
    """
    استعلام كل جهات الاتصال التي ليس لديها Company relation
    ثم ربط كل واحدة بالشركة المناسبة
    """
    log("")
    log("=" * 60)
    log("🔗 الخطوة 2: ربط جهات الاتصال بالشركات")
    log("=" * 60)

    stats = {
        "linked": 0,
        "already_linked": 0,
        "no_account_id": 0,
        "no_matching_company": 0,
        "errors": 0,
        "total_processed": 0,
    }

    # قائمة غير المتطابقين للمراجعة
    unmatched_contacts = []

    cursor = None
    page_num = 0

    while True:
        page_num += 1

        # استعلام جهات الاتصال بدون Company relation
        payload = {
            "page_size": 100,
            "filter": {
                "property": "Company",
                "relation": {
                    "is_empty": True
                }
            }
        }
        if cursor:
            payload["start_cursor"] = cursor

        result = notion_request("POST", f"databases/{CONTACTS_DB_ID}/query", payload)
        if not result:
            log("❌ فشل استعلام جهات الاتصال!")
            break

        batch = result.get("results", [])
        if not batch:
            log("  ✅ لا يوجد المزيد من جهات الاتصال غير المربوطة")
            break

        log(f"  📦 الدفعة {page_num}: {len(batch)} جهة اتصال غير مربوطة")

        for page in batch:
            stats["total_processed"] += 1
            contact_id = page["id"]
            full_name = get_text_property(page, "Full Name")
            apollo_account_id = get_text_property(page, "Apollo Account Id")

            # التحقق من وجود Apollo Account Id
            if not apollo_account_id:
                stats["no_account_id"] += 1
                continue

            # البحث عن الشركة في الخريطة
            if apollo_account_id not in company_map:
                stats["no_matching_company"] += 1
                unmatched_contacts.append({
                    "name": full_name,
                    "contact_id": contact_id,
                    "apollo_account_id": apollo_account_id,
                })
                continue

            # تنفيذ الربط
            company_page_id = company_map[apollo_account_id]

            update_payload = {
                "properties": {
                    "Company": {
                        "relation": [{"id": company_page_id}]
                    }
                }
            }

            update_result = notion_request("PATCH", f"pages/{contact_id}", update_payload)
            if update_result:
                stats["linked"] += 1
                if stats["linked"] % 50 == 0:
                    log(f"    ✅ تم ربط {stats['linked']} جهة اتصال...")
            else:
                stats["errors"] += 1
                log(f"    ❌ خطأ في ربط: {full_name} ({contact_id})")

            time.sleep(REQUEST_DELAY)

        if not result.get("has_more", False):
            break
        cursor = result.get("next_cursor")
        time.sleep(REQUEST_DELAY)

    return stats, unmatched_contacts


# ============================================================
# الخطوة 3: عد المربوطين مسبقاً
# ============================================================

def count_already_linked():
    """عد جهات الاتصال المربوطة مسبقاً"""
    log("")
    log("📊 عد جهات الاتصال المربوطة مسبقاً...")

    count = 0
    cursor = None

    while True:
        payload = {
            "page_size": 100,
            "filter": {
                "property": "Company",
                "relation": {
                    "is_not_empty": True
                }
            }
        }
        if cursor:
            payload["start_cursor"] = cursor

        result = notion_request("POST", f"databases/{CONTACTS_DB_ID}/query", payload)
        if not result:
            break

        count += len(result.get("results", []))

        if not result.get("has_more", False):
            break
        cursor = result.get("next_cursor")
        time.sleep(REQUEST_DELAY)

    return count


# ============================================================
# التنفيذ الرئيسي
# ============================================================

def main():
    start_time = datetime.now()

    log("🚀 AI Sales OS — بدء عملية ربط الشركات وجهات الاتصال")
    log(f"📅 التاريخ: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log("")

    # التحقق من التوكن
    if NOTION_TOKEN == "YOUR_NOTION_TOKEN_HERE":
        log("❌ خطأ: لم يتم تعيين NOTION_TOKEN!")
        log("   افتح الملف وضع التوكن في السطر:")
        log('   NOTION_TOKEN = "ntn_xxxxxxxxxxxxx"')
        sys.exit(1)

    # اختبار الاتصال
    log("🔌 اختبار الاتصال بـ Notion...")
    test = notion_request("GET", "users/me")
    if not test:
        log("❌ فشل الاتصال! تأكد من:")
        log("   1. التوكن صحيح")
        log("   2. الـ Integration مضاف لقواعد البيانات")
        sys.exit(1)
    log(f"✅ متصل كـ: {test.get('name', 'Unknown')}")
    log("")

    # عد المربوطين مسبقاً
    already_linked_before = count_already_linked()
    log(f"📌 جهات اتصال مربوطة مسبقاً: {already_linked_before}")

    # الخطوة 1: بناء خريطة الشركات
    company_map = build_company_map()
    if not company_map:
        log("❌ فشل بناء خريطة الشركات!")
        sys.exit(1)

    # الخطوة 2: ربط جهات الاتصال
    stats, unmatched = link_contacts(company_map)

    # عد المربوطين بعد العملية
    already_linked_after = count_already_linked()

    # التقرير النهائي
    elapsed = (datetime.now() - start_time).total_seconds()
    log("")
    log("=" * 60)
    log("📊 التقرير النهائي")
    log("=" * 60)
    log(f"  🏢 شركات في الخريطة:          {len(company_map):,}")
    log(f"  👤 جهات اتصال تمت معالجتها:    {stats['total_processed']:,}")
    log(f"  ✅ تم ربطها في هذه الجلسة:     {stats['linked']:,}")
    log(f"  🔗 مربوطة مسبقاً (قبل):        {already_linked_before:,}")
    log(f"  🔗 إجمالي المربوطة (بعد):       {already_linked_after:,}")
    log(f"  ⚠️  بدون Apollo Account Id:     {stats['no_account_id']:,}")
    log(f"  ❓ بدون شركة مطابقة:           {stats['no_matching_company']:,}")
    log(f"  ❌ أخطاء:                       {stats['errors']:,}")
    log(f"  ⏱️  الوقت الكلي:                {elapsed:.0f} ثانية ({elapsed/60:.1f} دقيقة)")
    log("=" * 60)

    # حفظ السجل
    log_data = {
        "date": start_time.isoformat(),
        "company_map_size": len(company_map),
        "stats": stats,
        "already_linked_before": already_linked_before,
        "already_linked_after": already_linked_after,
        "unmatched_contacts": unmatched,
        "elapsed_seconds": elapsed,
    }
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    log(f"📁 تم حفظ السجل في: {LOG_FILE}")

    if unmatched:
        log(f"\n⚠️  {len(unmatched)} جهة اتصال بدون شركة مطابقة:")
        for u in unmatched[:20]:
            log(f"    - {u['name']} (Apollo Account Id: {u['apollo_account_id']})")
        if len(unmatched) > 20:
            log(f"    ... و {len(unmatched) - 20} آخرين (راجع {LOG_FILE})")


if __name__ == "__main__":
    main()
