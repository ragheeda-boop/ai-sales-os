# 🧪 Phase 3 Testing Guide

**دليل الاختبار الشامل - Apollo API Pull Strategy**

---

## 📋 أنواع الاختبارات

1. [اختبارات الاتصال](#اختبارات-الاتصال)
2. [اختبارات الوظائف](#اختبارات-الوظائف)
3. [اختبارات الأداء](#اختبارات-الأداء)
4. [اختبارات الاستقرار](#اختبارات-الاستقرار)

---

## 🔌 اختبارات الاتصال

### 1. اختبر اتصال Apollo API

```bash
# 1. اسحب جهات الاتصال الخاصة بك من Apollo
curl -X GET "https://api.apollo.io/v1/contacts/search" \
  -H "X-Api-Key: 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" \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}'

# ستشاهد JSON response مثل:
# {
#   "breadcrumbs": [],
#   "contacts": [
#     {
#       "id": "5e66b6381e05b4008c8331b8",
#       "name": "John Smith",
#       "email": "john@example.com",
#       "title": "Sales Manager",
#       "organization_name": "Acme Inc",
#       ...
#     },
#     ...
#   ],
#   "pagination": {
#     "page": 1,
#     "per_page": 5,
#     "total_entries": 3606
#   }
# }
```

**معنى الاستجابة:**
- `contacts`: قائمة الجهات المسحوبة
- `pagination`: معلومات الترقيم
- `total_entries`: إجمالي الجهات (3,606 في قاعدتك)

**[] اختبار نجح:**

---

### 2. اختبر اتصال Notion API

```bash
# 1. احصل على معلومات المستخدم
curl -X GET "https://api.notion.com/v1/users/me" \
  -H "Authorization: Bearer secret_abc123..." \
  -H "Notion-Version: 2022-06-28"

# ستشاهد JSON response مثل:
# {
#   "object": "user",
#   "id": "987f-6543-2109-abcd",
#   "name": "Ragheed",
#   "email": "ragheedalmadani@gmail.com",
#   "type": "person",
#   "workspace_name": "Ragheed's Workspace"
# }
```

**[] اختبار نجح:**

---

### 3. اختبر وصول قاعدة البيانات

```bash
# احصل على معلومات قاعدة Contacts
curl -X GET "https://api.notion.com/v1/databases/9ca842d20aa9460bbdd958d0aa940d9c" \
  -H "Authorization: Bearer secret_abc123..." \
  -H "Notion-Version: 2022-06-28"

# ستشاهد structure قاعدة البيانات:
# {
#   "object": "database",
#   "id": "9ca842d2-0aa9-460b-bdd9-58d0aa940d9c",
#   "title": [{"text": {"content": "Contacts"}}],
#   "properties": {
#     "Name": {"type": "title", ...},
#     "Email": {"type": "email", ...},
#     "Phone": {"type": "phone_number", ...},
#     ...
#   }
# }
```

**[] اختبار نجح:**

---

## ✅ اختبارات الوظائف

### 1. اختبر إنشاء جهة اتصال جديدة

```bash
# أنشئ جهة اتصال تجريبية
curl -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer secret_abc123..." \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {
      "database_id": "9ca842d20aa9460bbdd958d0aa940d9c"
    },
    "properties": {
      "Name": {
        "title": [
          {
            "text": {
              "content": "Test Contact"
            }
          }
        ]
      },
      "Email": {
        "email": "test@example.com"
      },
      "Phone": {
        "phone_number": "+1234567890"
      },
      "Title": {
        "rich_text": [
          {
            "text": {
              "content": "Test Manager"
            }
          }
        ]
      }
    }
  }'

# النتيجة:
# {
#   "object": "page",
#   "id": "new-page-id",
#   "created_time": "2026-03-24T12:30:00Z",
#   "properties": {...}
# }
```

**[] جهة تجريبية منشأة:**

---

### 2. اختبر تحديث جهة اتصال

```bash
# حدّث الجهة التي أنشأتها للتو
curl -X PATCH "https://api.notion.com/v1/pages/new-page-id" \
  -H "Authorization: Bearer secret_abc123..." \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{
    "properties": {
      "Phone": {
        "phone_number": "+9876543210"
      },
      "Title": {
        "rich_text": [
          {
            "text": {
              "content": "Senior Manager"
            }
          }
        ]
      }
    }
  }'

# النتيجة: ✅ تم التحديث
```

**[] جهة محدثة:**

---

### 3. اختبر البحث عن جهة موجودة

```bash
# ابحث عن جهة بـ email معين
curl -X POST "https://api.notion.com/v1/databases/9ca842d20aa9460bbdd958d0aa940d9c/query" \
  -H "Authorization: Bearer secret_abc123..." \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "property": "Email",
      "email": {
        "equals": "test@example.com"
      }
    }
  }'

# النتيجة:
# {
#   "results": [
#     {
#       "object": "page",
#       "id": "...",
#       "properties": {...}
#     }
#   ]
# }
```

**[] البحث يعمل:**

---

## ⚡ اختبارات الأداء

### 1. اختبر سرعة المزامعة

```bash
# ابدأ scheduler وقس السرعة
$ time python apollo_sync_scheduler.py

# يجب أن يكمل في:
# - Pull من Apollo: < 2 ثانية
# - Sync مع Notion: < 5 ثواني
# - Total: < 10 ثواني
```

**الوقت المتوقع:**
- 1-100 جهة: < 5 ثواني
- 100-1000 جهة: < 15 ثانية
- 1000+ جهة: < 30 ثانية

**[] سرعة مقبولة:**

---

### 2. اختبر استهلاك الذاكرة

```bash
# في terminal جديد:
$ watch -n 1 'ps aux | grep apollo_sync'

# ابحث عن:
# apollo_sync_scheduler 123456  0.5  0.2   65432  54321 ...
#
# المعنى:
# - 0.5% CPU (عادي جداً)
# - 0.2% Memory (منخفض جداً)
# - 54321 KB RAM = ~53 MB (طبيعي)
```

**[] استهلاك منخفض:**

---

### 3. اختبر الاستجابة تحت الحمل

```bash
# اسحب عدد أكبر من الجهات
curl -X POST "https://api.apollo.io/v1/contacts/search" \
  -H "X-Api-Key: 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" \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 100,
    "filters": [{"field_name": "has_email", "predicate": "yes"}]
  }'

# يجب أن ينتهي في:
# - < 3 ثواني (Apollo API response)
# - ثم معالجة الـ 100 جهة في < 15 ثانية
```

**[] يتعامل مع الحمل:**

---

## 🔄 اختبارات الاستقرار

### 1. اختبر الدورات المتكررة

```
اتركه يعمل لمدة 1 ساعة:

✅ كل 5 دقائق:
   - Log جديد
   - Sync بدون أخطاء
   - لا توقف متوقع

بعد ساعة:
- 12 دورة sync
- 0 توقفات
- 0 أخطاء متراكمة
```

**[] مستقر لمدة ساعة:**

---

### 2. اختبر معالجة الأخطاء

```bash
# أيقف Internet مؤقتاً ثم أعده
# في الـ logs ستشاهد:
#
# [ERROR] ❌ Error pulling contacts from Apollo: ...
# [WARNING] ⚠️ Connection error, retrying next cycle...
# [INFO] ✅ Connected again, sync successful
#
# النتيجة: ✅ يتعافى تلقائياً
```

**[] معالجة أخطاء جيدة:**

---

### 3. اختبر الاستمرار بعد الخطأ

```bash
# غيّر API Key في .env إلى خطأ مقصود
# ستشاهد في الـ logs:
#
# [ERROR] ❌ Invalid API key
# [INFO] ⚠️ Scheduler will retry in 5 minutes
# [INFO] 🔄 Next sync attempt: 2026-03-24 12:35:00
#
# بعد 5 دقائق - أعد الـ Key الصحيح
# ستشاهد:
#
# [INFO] ✅ Connection restored
# [INFO] 🔄 Sync resumed successfully
```

**[] يستمر بالعمل:**

---

## 📊 مراقبة النتائج

### قراءة الـ Logs:

```bash
# اعرض آخر 50 سطر
$ tail -50 logs/apollo_sync.log

# اعرض آخر تحديثات حية
$ tail -f logs/apollo_sync.log

# ابحث عن أخطاء
$ grep ERROR logs/apollo_sync.log

# احصل على إحصائيات
$ grep "Created:" logs/apollo_sync.log | tail -5
```

---

### الإحصائيات المتوقعة:

```
في اليوم الأول:
✅ Created: 3,500-4,000 (جهات جديدة من Apollo)
✅ Updated: 0-100 (جهات موجودة تم تحديثها)
✅ Errors: 0

في اليوم الثاني:
✅ Created: 50-200 (جهات جديدة فقط)
✅ Updated: 100-300 (جهات حدثت بيانتها)
✅ Errors: 0

المستقبل:
✅ Created: 10-50 يومياً (جهات جديدة من Apollo)
✅ Updated: 50-200 يومياً (تحديثات)
✅ Errors: 0-2 (أخطاء نادرة)
```

---

## ✨ معايير النجاح

```
✅ النجاح يعني:
  - Logs بدون أخطاء
  - Sync كل 5 دقائق منتظم
  - Notion محدث دائماً
  - 0 توقفات غير متوقعة
  - استجابة < 15 ثانية للـ Sync

❌ الفشل يعني:
  - أخطاء متكررة في الـ Logs
  - Sync لم يحدث
  - Notion لم يتحدث
  - Scheduler توقف
  - استجابة > 30 ثانية
```

---

## 🎉 اختبار نهائي شامل

```
□ الاتصالات تعمل (Apollo + Notion)
□ الوظائف تعمل (Create + Update + Search)
□ الأداء مقبول (< 15 ثانية)
□ الاستقرار جيد (بدون توقفات)
□ المراقبة تعمل (Logs واضحة)
□ استعادة من الأخطاء تعمل
□ كل 5 دقائق تعمل بنتظام

إذا كل ✅ → Phase 3 مكتمل! 🎉
```

---

**تم الإنشاء:** 24 مارس، 2026
**الحالة:** ✅ دليل شامل
