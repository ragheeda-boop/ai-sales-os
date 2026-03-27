# Phase 3: Apollo Webhook Integration - دليل الإعداد الكامل

## 📋 نظرة عامة

هذا الدليل سيساعدك في:
1. ✅ إعداد Webhook في Apollo
2. ✅ تفعيل الـ Server الخاص بك (Python)
3. ✅ اختبار الربط
4. ✅ تفعيل المراقبة والتسجيل

---

## الجزء 1️⃣: إعداد Webhook في Apollo

### الخطوة 1: تسجيل الدخول لـ Apollo Admin
```
1. اذهب إلى: https://app.apollo.io/admin
2. استخدم بيانات حسابك الإداري
3. من القائمة اليسرى → Settings
```

### الخطوة 2: إنشاء Webhook Endpoint جديد
```
Navigation:
Settings → Integrations → Webhooks → Create New Webhook

اختر الخيارات التالية:
```

| الحقل | القيمة |
|------|--------|
| **Event Type** | Select All (أو اختر: Contact Created, Contact Updated, Company Updated) |
| **Webhook URL** | `http://YOUR_SERVER_IP:5000/webhook` |
| **Authentication** | Bearer Token |
| **Token Value** | `your_secret_token_here` (استخدم أي قيمة قوية) |
| **Active** | ✅ Enabled |

### الخطوة 3: حفظ الـ Details
احفظ هذه المعلومات:
```
Webhook ID: ___________________
API Key: ___________________
Webhook URL: ___________________
Secret Token: ___________________
```

---

## الجزء 2️⃣: إعداد Python Server

### المتطلبات الأساسية
```bash
# تأكد من تثبيت Python 3.8+
python --version

# المكتبات المطلوبة:
pip install flask requests python-dotenv notiondb
```

### إنشاء Configuration File

أنشئ ملف `.env` في المجلد الرئيسي:

```env
# Apollo
APOLLO_API_KEY=e0gTSdM3PbPWFUfgolUM5w
APOLLO_WEBHOOK_SECRET=your_secret_token_here

# Notion
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID_CONTACTS=your_contacts_db_id
NOTION_DATABASE_ID_COMPANIES=your_companies_db_id

# Server
SERVER_PORT=5000
SERVER_HOST=0.0.0.0
FLASK_ENV=development

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/webhook_events.log
```

---

## الجزء 3️⃣: اختبار الربط

### اختبار 1: التحقق من الـ Server
```bash
# من Terminal/Command Prompt
curl http://localhost:5000/health

# يجب أن ترى:
# {"status": "ok", "timestamp": "2026-03-24T..."}
```

### اختبار 2: إرسال Test Event من Apollo
```
في Apollo Admin → Webhooks → اختر الـ Webhook الجديد
→ Test Delivery

يجب أن ترى رسالة نجاح
```

### اختبار 3: التحقق من Notion
```
بعد Test Delivery:
1. اذهب لـ Notion Contacts Database
2. ابحث عن "Webhook Log" في أسفل الصفحة
3. يجب أن تشوف entry جديد
```

---

## الجزء 4️⃣: مراقبة الأحداث

### موقع ملفات السجل
```
logs/
├── webhook_events.log          # كل الأحداث
├── errors.log                  # الأخطاء فقط
└── sync_status.log            # حالة المزامعة
```

### قراءة السجل (Real-time)
```bash
# اتابع السجل مباشرة أثناء حدوث الأحداث
tail -f logs/webhook_events.log
```

---

## الجزء 5️⃣: الأحداث المدعومة

| الحدث | الوصف | البيانات المرسلة |
|-------|-------|-----------------|
| `contact.created` | جهة اتصال جديدة في Apollo | اسم، بريد، هاتف، الشركة |
| `contact.updated` | تحديث جهة اتصال | التغييرات فقط |
| `company.created` | شركة جديدة | الاسم، الموقع، الصناعة |
| `company.updated` | تحديث شركة | التغييرات فقط |

---

## الجزء 6️⃣: استكشاف الأخطاء

### المشكلة: "Connection Refused"
```
الحل: تأكد من أن Python Server يعمل
→ اشغل: python webhook_server.py
```

### المشكلة: "Invalid Token"
```
الحل: تحقق من Secret Token في .env
يجب أن يطابق القيمة في Apollo
```

### المشكلة: "Notion Database Not Found"
```
الحل: انسخ Database ID من Notion URL
مثال: https://notion.so/workspace/DATABASE_ID?v=view
استخرج: DATABASE_ID
```

---

## ✅ Checklist الإطلاق النهائي

- [ ] Webhook مُنشأ في Apollo
- [ ] `.env` file معبأ بالبيانات الصحيحة
- [ ] Python Server يعمل بدون أخطاء
- [ ] اختبار Delivery في Apollo نجح
- [ ] Notion Database استقبل البيانات
- [ ] السجلات تظهر الأحداث بشكل صحيح
- [ ] معالجة الأخطاء تعمل

---

## 📞 المشاكل والحلول السريعة

```
مشكلة                 → الحل
─────────────────────────────────────────
Webhook لا يستقبل      → تحقق من URL عام (public IP)
                       → Firewall قد يسد المنفذ

عدم مزامعة Notion      → تحقق من NOTION_API_KEY
                       → تحقق من DATABASE_IDs

Server يتوقف فجأة      → شغّل في Screen/Tmux
                       → استخدم PM2 للمراقبة المستمرة
```

---

## 🚀 الخطوات التالية

بعد نجاح Phase 3:
1. **Phase 4**: إنشاء Lead Scoring Rules
2. **Phase 5**: Odoo CRM Integration
