# AI Sales OS — Operator Runbook

**ماذا تفعل ومتى. بدون تنظير.**

الإصدار: v2.0 — Operator-First (**Bootstrap Mode v0.1**)
آخر تحديث: 2026-04-10

---

## ⚠️ Bootstrap Mode — الواقع الحالي

النظام الخلفي (auto_tasks, opportunity_manager, meeting_tracker) **مبني لكن لم يُشغَّل فعليًا**. لا توجد Tasks حقيقية ولا Opportunities حقيقية في قواعد البيانات.

**الحقيقة الوحيدة اليوم:** 📥 Lead Inbox الذي تملؤه يدويًا.

هذا Runbook يصف التشغيل في Bootstrap Mode. عند اكتمال معايير الترقية (انظر أسفل)، ستعود إلى Runbook v1.0.

---

## 📅 Daily Runbook (Bootstrap — 8 ساعات)

### ما يعمل تلقائيًا في الخلفية
- **7:00 AM KSA** — GitHub Actions يبدأ (Apollo sync فقط — لا تعتمد على مخرجاته بعد)
- Backend يحدّث Contacts/Companies DB، لكن **أنت لا تستخدم هذه البيانات في Bootstrap Mode**

النتيجة: عندما تفتح Notion، كل ما يهم هو **Lead Inbox** الذي تملؤه أنت.

### جدولك اليومي (Bootstrap)

| الوقت | الفعل | المدة |
|---|---|---|
| **9:00** | افتح Notion → ⭐ اليوم | 1 دقيقة |
| **9:01** | راجع قسم "📥 Leads جديدة" | 3 دقائق |
| **9:05** | افرز كل lead جديد → Review / Qualified / Rejected / Duplicate | 20 دقيقة |
| **9:25** | املأ "🎯 تركيز اليوم" بـ 3-5 بنود | 5 دقائق |
| **9:30** | اعمل على "🔍 Leads تحت المراجعة" — قرار لكل واحد | 1.5 ساعة |
| **11:00** | انقل كل "✅ Qualified" إلى Contacts DB يدويًا → Status = Moved | 1 ساعة |
| **12:00** | غداء | 2 ساعة |
| **14:00** | نفّذ بنود "🎯 تركيز اليوم" (اتصالات/إيميلات يدوية، lead generation) | 2 ساعة |
| **16:00** | جولة ثانية على Lead Inbox — امسح ما تبقى | 30 دقيقة |
| **16:30** | اكتب leads جديدة من محادثاتك اليوم في Lead Inbox | 15 دقيقة |
| **16:45** | تأكد: 0 سجلات في Status=New | 5 دقائق |
| **16:55** | اكتب ملاحظة اليوم | 5 دقائق |
| **17:00** | أغلق Notion | — |

**المجموع اليومي المستهدف (Bootstrap):** 10+ leads مفروزة، 3+ leads مُنقَلة إلى Contacts DB، 3+ بنود تركيز منجزة.

### Check اليوم قبل الإغلاق (Bootstrap)
- [ ] 0 سجلات في Status=New في Lead Inbox؟
- [ ] كل ✅ Qualified نُقلت إلى Contacts DB وحُوِّلت إلى Moved؟
- [ ] قائمة "🎯 تركيز اليوم" منفّذة أو منقولة إلى الغد؟
- [ ] ملاحظة اليوم مكتوبة؟

إذا نعم في الأربعة → يوم ناجح.

---

## 🎯 معايير الترقية من v0.1 إلى v1.0

Bootstrap Mode ينتهي عندما **تتحقق كل** هذه الشروط:

1. ≥ 20 lead في Contacts DB (نُقلت من Lead Inbox)
2. `scripts/automation/auto_tasks.py` شُغِّل بنجاح 3+ مرات على contacts حقيقيين
3. ≥ 1 Opportunity حقيقي (غير اختباري)
4. ≥ 1 Meeting حقيقي مسجّل
5. ≥ 5 محادثات مبيعات حقيقية يمكن تتبعها في النظام

عند تحقق الخمسة، يُعاد تفعيل:
- قسم "📞 اتصل اليوم" (من Tasks DB)
- قسم "✉️ تابع اليوم" (من Tasks DB)
- قسم "💼 الصفقات" (من Opportunities DB)
- Morning Brief و Dashboard
- Header حالة النظام 🟢/🔴

---

## 📅 Weekly Runbook (الأحد، 30 دقيقة)

**الوقت:** الأحد 8:30-9:00 AM (قبل بدء الأسبوع)

### الخطوات

**1. فحص صحة الأسبوع الماضي (5 دقائق)**
- افتح GitHub → Actions → آخر 7 أيام
- كلها 🟢؟ ✅
- أي 🔴؟ افتحها، اقرأ الـ log، صحّح إذا لزم

**2. قياس إنتاجية الأسبوع (10 دقائق)**
- Notion → Background → Tasks → view "مكتمل هذا الأسبوع"
- سجّل في ملاحظات الأسبوع:
  - عدد Urgent Calls المنجزة
  - عدد Follow-ups المنجزة
  - معدل Meeting Scheduled

**3. مراجعة Pipeline (10 دقائق)**
- Background → Opportunities → view "تغيّرت هذا الأسبوع"
- كم Opportunity جديدة؟
- كم تقدمت في Stage؟
- أي Opportunity stale (> 14 يوم)؟ → تعامل معها هذا الأسبوع

**4. مراجعة Lead Inbox (5 دقائق)**
- Lead Inbox → view "مؤرشف" → فلتر آخر 7 أيام
- كم قبلنا؟ كم رفضنا؟
- أكبر سبب رفض → تعلّم منه

**5. اكتب ملخص الأسبوع**
- صفحة "اليوم" → toggle "ملاحظات الأسبوع"
- 3 أسطر فقط: أفضل إنجاز، أكبر عائق، قرار للأسبوع القادم

### ما يعمل تلقائيًا يوم الأحد
- **Sunday 8:00 AM** — Score Calibrator يعمل في وضع المراجعة (review-only)
- النتيجة: تقرير في GitHub Actions artifacts
- **ليس مطلوبًا منك قراءته** إلا إذا قررت ضبط الأوزان (نادر)

---

## 📅 Monthly Runbook (أول سبت، 60 دقيقة)

### الخطوات

**1. فحص جودة البيانات (15 دقيقة)**
```bash
python scripts/governance/data_governor.py --dry-run
```
- اقرأ التقرير
- إذا فيه > 1000 سجل يحتاج أرشفة:
  ```bash
  python scripts/governance/data_governor.py --enforce
  ```
- إذا < 1000 → لا حاجة لإجراء

**2. فحص ملكية البيانات (10 دقائق)**
```bash
python scripts/governance/audit_ownership.py
```
- إذا فيه سجلات بلا owner، راجع يدويًا
- كل سجل بلا owner = فرصة ضائعة

**3. تقرير Lead Inbox الشهري (10 دقائق)**
- Lead Inbox → view "مؤرشف" → فلتر آخر 30 يوم
- احسب:
  - إجمالي leads المقبولة
  - إجمالي leads المرفوضة
  - أعلى 3 مصادر قبولًا
  - أعلى 3 مصادر رفضًا
- قرار:
  - أي مصدر تستثمر فيه أكثر؟
  - أي مصدر توقفه؟

**4. مراجعة Apollo credits (5 دقائق)**
- افتح Apollo dashboard
- كم استخدمت هذا الشهر؟
- هل في اتجاه مقلق؟
- هل تحتاج ترقية؟

**5. مراجعة Score Calibration (10 دقائق)**
- افتح آخر تقرير calibration (من Sunday runs الأربعة الأخيرة)
- هل الأوزان مستقرة؟
- هل تحتاج تعديل يدوي؟
- قرار: apply / ignore / wait

**6. تحديث MANUAL.md و RUNBOOK.md (10 دقائق)**
- هل هناك شيء تعلّمته هذا الشهر يستحق التوثيق؟
- هل هناك خطوة في Runbook أصبحت غير دقيقة؟
- عدّل إذا لزم

### ما يعمل تلقائيًا شهريًا
- لا شيء مجدول شهريًا تلقائيًا
- كل المهام الشهرية يدوية (لأنها تحتاج قرارًا بشريًا)

---

## 🚨 Failure Recovery Runbook

### إذا رأيت 🔴 في صفحة "اليوم"

**الخطوة 1 — حدّد المشكلة**
افتح GitHub → Actions → آخر run → أي job فشل؟

### إذا Job 1 (Sync/Score) فشل

**الأسباب الشائعة:**

| السبب | الحل |
|---|---|
| Apollo API rate limit | انتظر ساعة، أعد التشغيل يدويًا من GitHub UI |
| Notion API timeout | أعد التشغيل، إذا فشل مرتين: تحقق من Notion status |
| Python dependency error | نادر — اتصل بـ Cowork |

**Fallback محلي:**
```bash
python scripts/core/daily_sync.py --mode incremental --hours 48
```

### إذا Job 2 (Action/Track) فشل

Job 2 فيه `continue-on-error`. فشل خطوة واحدة لا يوقف كل شيء.

**الأسباب الشائعة:**

| السبب | الحل |
|---|---|
| `auto_tasks.py` فشل | تحقق من NOTION_API_KEY في secrets |
| `meeting_analyzer.py` فشل | تحقق من ANTHROPIC_API_KEY في secrets |
| `outcome_tracker.py` فشل | تحقق من NOTION_DATABASE_ID_TASKS/CONTACTS |

### إذا Notion لا يعرض بيانات جديدة

1. تحقق من آخر sync في صفحة "اليوم" header
2. إذا قديم > 24 ساعة:
   ```bash
   python scripts/core/daily_sync.py --mode incremental --hours 48
   ```
3. إذا لا يزال فارغًا: تحقق من Apollo dashboard (هل API key ساري؟)

### إذا Lead Inbox لا يعمل

1. افتح Lead Inbox في Notion مباشرة — يُفتح؟
2. إذا لا: Notion API قد يكون معطلًا → status.notion.so
3. إذا نعم لكن لا يقبل سجلات جديدة: تحقق من schema (هل كل الحقول موجودة؟)

### إذا صفحة "اليوم" لا تعرض Leads

(Bootstrap Mode: Today page تعتمد فقط على Lead Inbox، لا على Tasks)

1. افتح view settings لقسم "📥 Leads جديدة"
2. تحقق من filters:
   - Source Database = 📥 Lead Inbox
   - Status = New
3. إذا الفلاتر صحيحة لكن لا توجد سجلات: ربما ليس لديك leads جديدة — أضف واحدًا من Lead Inbox مباشرة للتجربة

### إذا شيء آخر تعطّل ولا تعرف ما هو

**الخطة الذهبية:**
1. افتح Cowork
2. اكتب: "النظام معطل. استخدم `pipeline-health-monitor` skill"
3. اتبع التوجيهات

**لا تحاول إصلاح الكود بنفسك** قبل فهم المشكلة.

---

## 🔁 Rollback Runbook

### إذا v2.0 Operator Layer فشل وأردت العودة للوضع السابق

**الوقت المطلوب:** 30 دقيقة

**الخطوات:**
1. Notion → sidebar → اسحب dashboards القديمة من Archive إلى الأعلى
2. GitHub Actions workflow file: أعد تفعيل dashboard generation steps
3. GitHub Actions workflow file: أعد تفعيل `morning_brief.py`
4. Notion → اسحب ⭐ اليوم إلى Archive (لا تحذفها)
5. Notion → اسحب 📥 Lead Inbox إلى Archive (لا تحذفها)

**ما لا يحتاج rollback (لأنه لم يُلمس):**
- daily_sync.py
- scoring scripts
- auto_tasks.py
- كل الـ backend

**البيانات في Lead Inbox لن تضيع** — تبقى في Archive كمرجع.

---

## جدول الأتمتة اليومية المرجعي

| الوقت | ما يحدث | مصدر | حالة |
|---|---|---|---|
| 07:00 KSA | GitHub Actions يبدأ (Job 1) | Cron | تلقائي |
| 07:00-07:30 | Apollo sync (daily_sync.py --hours 26) | Backend | تلقائي |
| 07:30-08:00 | Lead scoring + Action Ready | Backend | تلقائي |
| 08:00-08:30 | Job Postings enrichment | Backend | تلقائي |
| 08:30 | Job 1 ينتهي، Job 2 يبدأ | Pipeline | تلقائي |
| 08:30-09:00 | Auto tasks + Auto sequence | Backend | تلقائي |
| 09:00 | **رغيد يفتح Notion** | Manual | **أنت** |
| 09:00-09:30 | Meeting tracker + analyzer + opportunity manager | Backend | تلقائي |
| 09:30-10:00 | Analytics + Outcome tracker + Health check | Backend | تلقائي |
| 10:00 | Pipeline ينتهي، صفحة "اليوم" محدّثة | — | — |

**الملاحظة المهمة:** Job 2 يعمل أثناء بدء يومك. هذا مقصود — لأن مهام اليوم جاهزة من Job 1 المبكر، و Job 2 يحدّث السياق بعد ذلك.

---

## الأوامر اليدوية الأربعة

```bash
# 1. استيراد leads من CSV
python scripts/intake/import_list.py <file.csv> --source Import

# 2. فحص جودة (شهريًا)
python scripts/governance/data_governor.py --dry-run

# 3. Backfill عند فقدان بيانات
python scripts/core/daily_sync.py --mode backfill --days 3

# 4. تقرير أسبوعي
python scripts/monitoring/morning_brief.py --days 7 --output weekly.md
```

**احفظ هذه الأربعة. كل ما عدا ذلك تلقائي أو من Notion.**
