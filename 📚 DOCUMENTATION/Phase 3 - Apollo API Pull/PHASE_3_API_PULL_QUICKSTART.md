# 🚀 Phase 3: Apollo API Pull - Quick Start

**المرحلة الثالثة: Pull من Apollo API كل 5 دقائق → Sync مع Notion**

**الحالة:** ✅ جاهز للتشغيل الآن
**الوقت المتوقع:** 15 دقيقة فقط
**الموقع:** `04_PHASE3_APOLLO_API_PULL/`

---

## ⚡ الخطوات السريعة (5 خطوات بسيطة فقط)

### 1️⃣ الحصول على Notion Integration Token (1 دقيقة)

```bash
# اذهب إلى:
https://www.notion.so/my-integrations

# انقر: "Create new integration"
# اسم: "AI Sales OS"
# انقر: "Submit"
# انسخ: الـ Internal Integration Token
```

### 2️⃣ تحضير ملف التكوين (2 دقيقة)

```bash
# انسخ الملف النموذجي
$ cp .env.example .env

# افتح .env وأضف الـ Token
$ nano .env

# البحث عن السطر:
# NOTION_API_KEY=your_notion_integration_token_here

# استبدله بـ Token الذي نسخته للتو
NOTION_API_KEY=secret_abc123...

# احفظ الملف (Ctrl+X ثم Y ثم Enter)
```

### 3️⃣ تثبيت المتطلبات (3 دقائق)

```bash
# تثبيت جميع المكتبات المطلوبة
$ pip install -r requirements.txt

# سيتم تثبيت:
# ✅ requests (لـ Apollo API)
# ✅ APScheduler (للجدولة كل 5 دقائق)
# ✅ python-dotenv (لقراءة .env)
```

### 4️⃣ التحقق من الإعدادات (2 دقيقة)

```bash
# تشغيل script التحقق
$ python verify_setup.py

# ستشاهد:
# ✅ Python Version: OK
# ✅ Required Files: OK
# ✅ Dependencies: OK
# ✅ Environment: OK
#
# إذا رأيت ✅ على كل شيء → أنت جاهز! 🎉
```

### 5️⃣ تشغيل السيرفر (2 دقيقة)

```bash
# شغّل الـ scheduler الرئيسي
$ python apollo_sync_scheduler.py

# ستشاهد:
# ═══════════════════════════════════════════════════════════════════════════
# 🚀 APOLLO → NOTION SYNC ENGINE (API PULL)
# ═══════════════════════════════════════════════════════════════════════════
# Start Time: 2026-03-24T12:00:00.000000
# Sync Interval: 5 minutes
# ═══════════════════════════════════════════════════════════════════════════

# 🎉 الآن يعمل! سيقوم بـ:
# ✅ Pull من Apollo كل 5 دقائق
# ✅ Sync الجهات الجديدة إلى Notion
# ✅ تحديث الجهات الموجودة
# ✅ Deduplication تلقائي بـ email
# ✅ Logging شامل في logs/apollo_sync.log
```

---

## 📊 ما الذي يحدث الآن؟

### التدفق التلقائي (كل 5 دقائق):

```
⏰ كل 5 دقائق:
│
├─ 📥 Pull من Apollo API
│  ├─ احصل على جهات اتصال جديدة
│  └─ احصل على شركات جديدة
│
├─ 🔍 فحص التكرار
│  ├─ هل هذه الجهة موجودة بالفعل؟
│  └─ المقارنة عن طريق Email
│
├─ 💾 Sync مع Notion
│  ├─ إنشاء جهات جديدة
│  └─ تحديث جهات موجودة
│
└─ 📝 Log النتائج
   ├─ عدد المنشأة: N
   ├─ عدد المحدثة: M
   └─ الأخطاء: 0
```

---

## 🔍 مراقبة الـ Logs

### في تيرمينال آخر:

```bash
# اعرض السجلات الحية
$ tail -f logs/apollo_sync.log

# ستشاهد تقارير مثل:
# [INFO] 🔄 Starting contact sync...
# [INFO] 📥 Pulling contacts from Apollo (limit=100)
# [INFO] ✅ Pulled 15 contacts from Apollo
# [INFO] ✅ Created contact: John Doe (5f3c2a1b...)
# [INFO] ✅ Updated contact: Jane Smith (7a9d4e2c...)
# [INFO] 📊 Sync Results:
#        Created: 3, Updated: 2, Skipped: 0, Errors: 0
```

---

## ✅ التحقق من النجاح

### في Notion:

```
1. افتح: https://www.notion.so/...
2. اذهب إلى: جدول الجهات (Contacts)
3. ابحث عن الجهات من Apollo
4. تحقق من أنها تحتوي على:
   ✅ الاسم
   ✅ البريد الإلكتروني
   ✅ الهاتف
   ✅ المسمى الوظيفي
   ✅ اسم الشركة
```

---

## 🛠️ الأوامر المفيدة

```bash
# توقف السيرفر
Ctrl+C

# شاهد معلومات العملية
$ ps aux | grep apollo_sync_scheduler

# اقتل العملية إذا لزم الأمر
$ pkill -f apollo_sync_scheduler

# اختبر الاتصال بـ Notion
$ curl -H "Authorization: Bearer $NOTION_API_KEY" \
       https://api.notion.com/v1/users/me

# اختبر الاتصال بـ Apollo
$ curl -H "X-Api-Key: $APOLLO_API_KEY" \
       https://api.apollo.io/v1/contacts/search
```

---

## ❓ الأسئلة الشائعة

**س: كم مرة يحدث الـ Sync؟**
ج: كل 5 دقائق تلقائياً

**س: ماذا لو حدث خطأ؟**
ج: سيتم تسجيله في `logs/apollo_sync.log` والمحاولة مرة أخرى في الدورة التالية

**س: هل يمكنني تغيير فترة الـ Sync؟**
ج: نعم، عدّل `SYNC_INTERVAL_MINUTES` في ملف `.env`

**س: هل سيحذف الجهات القديمة؟**
ج: لا، فقط يضيف/يحدّث. لن يحذف أي شيء.

**س: كيف أتأكد من أن كل شيء يعمل؟**
ج: شاهد الـ logs وتحقق من Notion بعد 5 دقائق

---

## 🎉 اكتملت المرحلة الثالثة!

**الآن لديك:**
- ✅ API Pull من Apollo كل 5 دقائق
- ✅ Real-time sync مع Notion
- ✅ Deduplication تلقائي
- ✅ Logging شامل
- ✅ Error handling قوي

**الخطوات التالية:**
- الأسبوع القادم: Phase 4 (Lead Scoring)
- الأسبوع الثاني: Phase 5 (Odoo Integration)

---

**تم الإنشاء:** 24 مارس، 2026
**الحالة:** ✅ جاهز للعمل
**الدعم:** اقرأ `PHASE_3_IMPLEMENTATION_CHECKLIST.md` للمزيد من التفاصيل
