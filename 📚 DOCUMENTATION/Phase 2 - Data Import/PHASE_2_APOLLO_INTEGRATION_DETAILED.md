# 🔗 PHASE 2: APOLLO INTEGRATION — الخطة التفصيلية
## خطة ربط Apollo بـ Notion كاملة

**التاريخ:** 24 مارس 2026
**المرحلة:** Phase 2 (April 1-14, 2026)
**الهدف:** ربط Apollo مع Notion + سحب البيانات الحية يومياً
**الوقت المتوقع:** 17 ساعة

---

## 📊 نظرة عامة على الربط

### الوضع الحالي (بعد Phase 1B):
```
Notion Database:
├─ 3,606 شركة
├─ 5,898 جهة اتصال
└─ 100% مرتبطة ببعضها ✅

لكن: البيانات ثابتة (ما تتحرك)
```

### الوضع المطلوب (بعد Phase 2):
```
Notion Database:
├─ 3,606 شركة
├─ 5,898 جهة اتصال
├─ Data يتحدث يومياً من Apollo 🔄
├─ Lead Scores محسوبة تلقائياً 📊
└─ Alerts عند تغييرات مهمة 🔔
```

---

## 🔧 المتطلبات التقنية

### قبل ما نبدأ، تحتاج:

```
☐ Apollo.io Account (Pro/Enterprise)
☐ Apollo API Key (من Settings)
☐ Notion API Token (من Integration Settings)
☐ Access إلى Notion Workspace
☐ Python 3.8+ (لو بتستخدم automation script)
☐ Internet connection مستقر
```

### المعلومات اللي تحتاجها:
```
من Apollo:
├─ API Key: sk_test_XXXXXXXXXXXXX
└─ Workspace ID: xxxxxxxxxxxxx

من Notion:
├─ API Token: secret_XXXXXXXXXXXXX
└─ Database IDs:
   ├─ Companies DB: xxxxxxxxxxxxx
   ├─ Contacts DB: xxxxxxxxxxxxx
   └─ Scoring DB: xxxxxxxxxxxxx
```

---

## 📋 الخطوات التفصيلية

## ✅ الخطوة 1: تجهيز Apollo

### 1.1: انسخ Apollo API Key

**المسؤول:** RevOps Lead أو Engineer
**الوقت:** 10 دقايق

```
الخطوات:
1. اذهب إلى: https://app.apollo.io
2. اضغط على Icon الحساب (أعلى اليسار)
3. اختر: Settings
4. اذهب إلى: Integrations
5. ابحث عن: API Key
6. اضغط: Copy
7. احفظها في مكان آمن (Password Manager)

⚠️ تنبيه مهم:
- لا تشاركها مع أحد
- لا تحفظها في Slack أو Email
- استخدم: 1Password, Bitwarden, أو Notion Security Database
```

### 1.2: اختبر الاتصال من Apollo

**الخطوات:**
```
1. اذهب إلى: Apollo Settings → API
2. اضغط: Test Connection
3. يجب ترى: ✅ Connection Successful
4. إذا Error ❌ تحقق من:
   - Key صحيح (ما فيه مسافات)
   - API Tier عالي (Pro/Enterprise)
   - Internet connection شغال
```

---

## ✅ الخطوة 2: تجهيز Notion

### 2.1: إنشاء Integration في Notion

**الوقت:** 15 دقيقة

```
الخطوات:
1. اذهب إلى: https://www.notion.so/my-integrations
2. اضغط: New Integration
3. ملء البيانات:
   - Name: "Apollo Data Sync"
   - Logo: (اختياري)
   - Description: "Daily sync from Apollo to Notion"
4. اضغط: Create Integration
5. انسخ: Internal Integration Token
   - يبدأ بـ: secret_XXXXX...

⚠️ تنبيه:
- احفظ Token في مكان آمن
- لا تشاركها مع أحد
```

### 2.2: أعطِ الـ Integration صلاحيات

**الخطوات:**
```
1. في Notion، افتح workspace
2. اضغط: Share (أعلى اليمين)
3. اختر: Connections (في الأسفل)
4. ابحث عن: "Apollo Data Sync"
5. اختر: ✅ Allow
6. حدد الصلاحيات:
   ☑️ Read database contents
   ☑️ Update database items
   ☑️ Create database items
```

### 2.3: احصل على Database IDs

**الخطوات:**
```
للشركات (Companies DB):
1. افتح: Companies database
2. انظر إلى URL:
   https://www.notion.so/[WORKSPACE_ID]?v=[DATABASE_ID]
3. انسخ DATABASE_ID

افعل نفس الشي لـ:
- Contacts database
- Opportunities database (لو موجود)
- Activities database
```

---

## ✅ الخطوة 3: ربط Apollo مع Notion

### 3.1: طريقة أولى - استخدام Zapier (الأسهل)

**الوقت:** 30 دقيقة
**Difficulty:** ⭐⭐ Easy

```
الخطوات:

1. اذهب إلى: https://zapier.com
2. اضغط: Sign Up (إذا ما عندك حساب)
3. أنشئ Zap جديد:
   - Trigger: Apollo → Contact Updated
   - Action: Notion → Update Database Item

4. ربط Apollo:
   - اختر: Apollo.io
   - اختر: New Contact
   - أدخل: Apollo API Key
   - اختبر: Connection ✅

5. ربط Notion:
   - اختر: Notion
   - اختر: Update Database Item
   - أدخل: Notion API Token
   - اختر: Contacts Database
   - Map الحقول:
     ├─ Apollo Contact ID → Notion Contact ID
     ├─ Name → Name
     ├─ Email → Email
     ├─ Title → Title
     ├─ Seniority → Seniority
     └─ Company → Company (link)

6. اختبر الـ Zap:
   - أضف contact جديد في Apollo
   - انتظر 1-2 دقيقة
   - تحقق من Notion ✅

7. فعّل الـ Zap: ON
```

### 3.2: طريقة ثانية - استخدام Python Script (الأفضل)

**الوقت:** 2-3 ساعات
**Difficulty:** ⭐⭐⭐ Advanced

```python
# apollo_notion_sync.py

import requests
import json
from datetime import datetime

# Config
APOLLO_API_KEY = "sk_test_XXXXX"
NOTION_API_KEY = "secret_XXXXX"
NOTION_DB_ID = "xxxxxxxxxxxxx"

# Headers
APOLLO_HEADERS = {
    "Authorization": f"Bearer {APOLLO_API_KEY}",
    "Content-Type": "application/json"
}

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# Step 1: سحب البيانات من Apollo
def get_contacts_from_apollo():
    url = "https://api.apollo.io/v1/contacts"
    params = {
        "api_key": APOLLO_API_KEY,
        "limit": 500,
        "page": 1
    }

    response = requests.get(url, params=params, headers=APOLLO_HEADERS)

    if response.status_code == 200:
        return response.json()["contacts"]
    else:
        print(f"❌ Error: {response.status_code}")
        return []

# Step 2: تحديث Notion بالبيانات
def update_notion_contact(contact_data):
    url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"

    # البحث عن Contact في Notion
    search_payload = {
        "filter": {
            "property": "Apollo_ID",
            "rich_text": {
                "equals": contact_data["id"]
            }
        }
    }

    search_response = requests.post(url, json=search_payload, headers=NOTION_HEADERS)

    if search_response.status_code == 200:
        results = search_response.json()["results"]

        if results:
            # Update existing
            page_id = results[0]["id"]
            update_url = f"https://api.notion.com/v1/pages/{page_id}"

            update_payload = {
                "properties": {
                    "Name": {
                        "title": [{"text": {"content": contact_data["name"]}}]
                    },
                    "Email": {
                        "email": contact_data["email"]
                    },
                    "Title": {
                        "rich_text": [{"text": {"content": contact_data["title"]}}]
                    },
                    "Last_Updated": {
                        "date": {"start": datetime.now().isoformat()}
                    }
                }
            }

            update_response = requests.patch(update_url, json=update_payload, headers=NOTION_HEADERS)
            return update_response.status_code == 200

    return False

# Step 3: شغّل الـ Sync
def sync_all():
    contacts = get_contacts_from_apollo()

    success_count = 0
    error_count = 0

    for contact in contacts:
        if update_notion_contact(contact):
            success_count += 1
        else:
            error_count += 1

    print(f"✅ Synced: {success_count}")
    print(f"❌ Errors: {error_count}")

    return {
        "timestamp": datetime.now().isoformat(),
        "synced": success_count,
        "errors": error_count
    }

if __name__ == "__main__":
    result = sync_all()
    print(json.dumps(result, indent=2))
```

**الخطوات:**
```
1. احفظ الـ Script: 03_SETUP/apollo_notion_sync.py
2. ركب المكتبات:
   pip install requests

3. ضع الـ API Keys:
   APOLLO_API_KEY = "sk_test_XXXXX"
   NOTION_API_KEY = "secret_XXXXX"

4. شغّل:
   python apollo_notion_sync.py

5. تحقق من النتائج:
   ✅ Synced: 5,898
   ❌ Errors: 0
```

---

## ✅ الخطوة 4: سحب Intent Signals

### 4.1: الحقول المراد سحبها

```
من Apollo، سحب هالحقول:

📊 Company Intelligence:
├─ Employee Count (عدد الموظفين)
├─ Latest Funding Amount (أكثر تمويل)
├─ Latest Funding Date (تاريخ التمويل)
├─ Technologies Using (التقنيات المستخدمة)
└─ Website Contacts (عدد الجهات من الموقع)

🎯 Intent Signals:
├─ Job Postings Count (عدد الوظائف المفتوحة)
├─ Recent Website Activity (نشاط الموقع)
├─ Technology Changes (تقنيات جديدة)
├─ Funding News (أخبار تمويل)
└─ Executive Changes (تغييرات قيادية)

📈 Engagement Metrics:
├─ Last Contact Date (آخر تواصل)
├─ Open Rate (نسبة الفتح)
├─ Click Rate (نسبة الضغط)
└─ Reply Rate (نسبة الرد)
```

### 4.2: إنشاء حقول جديدة في Notion

**الخطوات:**
```
1. افتح: Companies database
2. اضغط: + Add a property
3. أضف الحقول التالية:

Company Intelligence:
├─ Employee Count (Number)
├─ Latest Funding Amount (Currency)
├─ Latest Funding Date (Date)
├─ Technologies (Multi-select)
└─ Website Contacts (Number)

Intent Signals:
├─ Job Postings (Number)
├─ Website Activity Score (Number)
├─ Technology Changes (Rich Text)
├─ Funding News (Checkbox)
└─ Executive Changes (Text)

Engagement:
├─ Last Contact (Date)
├─ Open Rate % (Number)
├─ Click Rate % (Number)
└─ Reply Rate % (Number)

System Fields:
├─ Last Synced (Date)
├─ Sync Status (Select: Synced, Pending, Error)
└─ Intent Score (Number, calculated)
```

### 4.3: ربط الحقول من Apollo

**باستخدام Zapier:**
```
1. أنشئ Zap جديد:
   Trigger: Apollo → Workspace Daily Digest
   Action: Notion → Update Database Item

2. Map الحقول:
   Apollo: employee_count → Notion: Employee Count
   Apollo: latest_funding_amount → Notion: Latest Funding Amount
   Apollo: job_postings_count → Notion: Job Postings
   ...إلخ
```

---

## ✅ الخطوة 5: حساب Lead Scores

### 5.1: الصيغة

```
Lead Score = (Intent × 40%) + (Engagement × 35%) + (Size × 15%) + (Industry × 10%)

حيث:

Intent (40%):
├─ Job Postings: 0-30 نقطة
├─ Funding News: +20 نقطة
├─ Technology Changes: +20 نقطة
└─ Executive Changes: +20 نقطة
   → Max: 100

Engagement (35%):
├─ Website Activity: 0-40 نقطة
├─ Email Open Rate: 0-30 نقطة
└─ Email Click Rate: 0-30 نقطة
   → Max: 100

Company Size (15%):
├─ 1-10 employees: 20 نقطة
├─ 11-50: 40 نقطة
├─ 51-200: 60 نقطة
├─ 201-500: 80 نقطة
└─ 500+: 100 نقطة

Industry Fit (10%):
├─ Perfect Match: 100 نقطة
├─ Good Match: 70 نقطة
├─ Fair Match: 40 نقطة
└─ No Match: 0 نقطة
```

### 5.2: إضافة حقل Lead Score في Notion

**الخطوات:**
```
1. افتح: Contacts database
2. اضغط: + Add a property
3. ملء البيانات:
   - Name: "Lead Score"
   - Type: Formula
   - Formula:

(
  (prop("Company").prop("Intent_Score") * 0.4) +
  (prop("Engagement_Score") * 0.35) +
  (prop("Company").prop("Size_Score") * 0.15) +
  (prop("Company").prop("Industry_Score") * 0.10)
)

4. اضغط: Done
```

### 5.3: إنشاء Views للـ Lead Scores

**الخطوات:**
```
1. افتح: Contacts database
2. أنشئ View جديد: + Add a view

View 1: Hot Leads (80+)
├─ Type: Table
├─ Filter: Lead Score ≥ 80
├─ Sort: Lead Score DESC
└─ Name: 🔴 HOT LEADS (Prioritize)

View 2: Warm Leads (50-79)
├─ Type: Table
├─ Filter: Lead Score 50-79
├─ Sort: Lead Score DESC
└─ Name: 🟡 WARM LEADS (Nurture)

View 3: Cold Leads (<50)
├─ Type: Table
├─ Filter: Lead Score < 50
├─ Sort: Lead Score DESC
└─ Name: 🟢 COLD LEADS (Monitor)
```

---

## ✅ الخطوة 6: جدولة التحديثات اليومية

### 6.1: Automated Daily Sync

**الخطوات (استخدام Zapier):**
```
1. أنشئ Zap جديد:
   Trigger: Schedule → Every Day at 2:00 AM UTC
   Action: Run Python Script (أو Zapier Code)

2. Script اللي يشتغل:
   python 03_SETUP/apollo_notion_sync.py

3. بعد الـ Sync:
   - تحديث Lead Scores تلقائياً
   - إرسال Alert إذا Contact تغيّر (optional)

4. Logging:
   - احفظ النتائج في: 02_DOCUMENTATION/sync_logs/
   - فايل يومي: sync_2026-03-25.json
```

### 6.2: Alternative - استخدام Notion Automation

**الخطوات:**
```
1. في Notion، افتح: Companies database
2. اضغط: Automation (أعلى اليمين)
3. أنشئ جديد:
   Trigger: When database item changes
   Action: Update related Contacts with new scores

4. Configure:
   ├─ Trigger: When Company updated
   ├─ Filter: If Intent_Score changes
   └─ Action: Update all Contacts → Recalculate Lead Score
```

---

## 🧪 الاختبار والتحقق

### 7.1: اختبار الاتصال الأول

**الخطوات:**
```
الخطوة 1: إضافة Contact جديد في Apollo
├─ اسم: "Test Contact Phase 2"
├─ شركة: "Test Company"
└─ بريد: "test@example.com"

الخطوة 2: انتظر 2-5 دقايق
├─ Zapier يعالج الـ Request
└─ Notion يتحدث

الخطوة 3: تحقق من Notion
├─ افتح: Contacts database
├─ ابحث عن: "Test Contact Phase 2"
├─ تأكد: كل الحقول موجودة ✅
└─ تأكد: Lead Score محسوب ✅

النتيجة المتوقعة:
✅ Contact موجود في Notion
✅ جميع الحقول populated
✅ Lead Score = عدد معين
✅ Status: Synced
```

### 7.2: اختبار على 100 Contact

**الخطوات:**
```
الخطوة 1: شغّل الـ Sync على 100 Contact
├─ python 03_SETUP/apollo_notion_sync.py --limit=100
└─ أو: Zapier Zap manually run

الخطوة 2: تحقق من النتائج
├─ عد السجلات المحدثة
├─ تحقق من 10 random contacts
├─ تأكد: Lead Scores منطقية

النتيجة المتوقعة:
✅ 100 / 100 synced
✅ 0 errors
✅ Lead Score distribution:
   - 10-15% High (80+)
   - 20-30% Medium (50-79)
   - 55-70% Low (<50)
```

### 7.3: اختبار على كل البيانات

**الخطوات:**
```
الخطوة 1: شغّل الـ Sync الكامل
├─ python 03_SETUP/apollo_notion_sync.py
└─ انتظر 30-45 دقيقة

الخطوة 2: تحقق من النتائج
├─ Total Contacts: 5,898 ✅
├─ Synced Successfully: 5,898 ✅
├─ Errors: 0 ✅
├─ Lead Scores Calculated: 5,898 ✅

الخطوة 3: حقق Views عاملة
├─ Hot Leads (80+): ~200 ✅
├─ Warm Leads (50-79): ~900 ✅
├─ Cold Leads (<50): ~4,800 ✅

Go/No-Go Decision:
✅ GO: كل المعايير محققة
❌ NO-GO: تحقق من الأخطاء
```

---

## 📊 النتائج المتوقعة

### بعد تمام Phase 2:

```
Notion Status:
├─ 3,606 Companies مع Intent Signals
├─ 5,898 Contacts مع Lead Scores
├─ Daily Sync شغال تلقائياً
└─ Dashboard عاملة بـ Real-time Data

Data Quality:
├─ Sync Success Rate: 99%+
├─ Lead Score Accuracy: 95%+
├─ Update Latency: <5 minutes
└─ Data Freshness: Updated daily

Team Impact:
├─ Sales focus على Hot Leads فقط (200)
├─ Productivity increase: +30%
├─ Win rate improvement: +20%
└─ Sales cycle reduction: -40%
```

---

## ⚠️ Troubleshooting

### المشكلة 1: Sync فيه Errors

```
الأعراض:
❌ API Connection Failed
❌ Some contacts not syncing
❌ Error in logs

الحل:
1. تحقق من API Keys:
   - استخدم Keys جديدة
   - تأكد من صحتها

2. تحقق من الاتصال:
   - ping api.apollo.io
   - ping api.notion.com

3. تحقق من الصلاحيات:
   - هل Notion Integration لديها صلاحيات كافية؟
   - هل Apollo API Key active؟

4. شغّل الـ Sync مجدداً
```

### المشكلة 2: Lead Scores غريبة

```
الأعراض:
❌ بعض الـ Scores 0 أو 100
❌ التوزيع غير منطقي

الحل:
1. تحقق من البيانات الأساسية:
   - هل Intent_Score موجود؟
   - هل Engagement_Score موجود؟

2. تحقق من الصيغة:
   - تأكد من الصيغة صحيحة
   - جرّب على contact واحد

3. عدّل الأوزان إذا لازم:
   - جرّب أوزان مختلفة
   - اختبر على 100 contact
```

---

## ✅ Success Criteria

```
Phase 2 Complete إذا:

☑️ Apollo ↔ Notion Sync شغال
☑️ 5,898 Contacts synchronized
☑️ Lead Scores محسوبة صحيح
☑️ Daily Sync مجدول
☑️ Team Views عاملة (Hot/Warm/Cold)
☑️ 0 Critical Errors
☑️ QA Sign-off obtained

🎯 Target Timeline: April 1-14, 2026
🎯 Estimated Time: 17 hours
🎯 Team: 2-3 people (Engineer + Analyst)
```

---

**Document Version:** 1.0
**Last Updated:** March 24, 2026
**Status:** Ready for Phase 2 Planning
