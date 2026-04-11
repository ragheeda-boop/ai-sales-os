# AI Sales OS v2.0 — Operator-First Blueprint

**مواصفات Notion v2.0 + Lead Inbox + Today Page + خطة 14 يوم.**
**مرجع التصميم الفني للتنفيذ.**

الإصدار: v2.0 (**Today Page: v0.1 Bootstrap Mode**)
آخر تحديث: 2026-04-10

---

## ⚠️ تحديث 2026-04-10 — Bootstrap Mode Pivot

صفحة "اليوم" التي وُصفت في القسم 3 بنسخة v1.0 **لم تعد النسخة الحية**. بعد بناء Lead Inbox (Day 2) تبيّن أن النظام الخلفي (auto_tasks, opportunity_manager) **لم يُشغَّل فعليًا**، ولا توجد Tasks أو Opportunities حقيقية في قواعد البيانات.

**القرار:** تم ترقية صفحة "اليوم" إلى **v0.1 Bootstrap Mode** — 6 أقسام تعتمد فقط على Lead Inbox. المواصفات الكاملة في `notion/v2/today_page/schema.md` (v0.1). القسم 3 أدناه محفوظ كمرجع تاريخي لـ v1.0 الذي سيُعاد تفعيله عند استيفاء معايير الترقية (انظر RUNBOOK.md → "معايير الترقية من v0.1 إلى v1.0").

**الأقسام الحية في Bootstrap Mode:**
1. 📥 Leads جديدة (Lead Inbox, Status=New)
2. 🔍 Leads تحت المراجعة (Status=Review)
3. ✅ Leads مؤهلة وجاهزة للنقل (Status=Qualified)
4. 🚚 Leads نُقلت إلى CRM (Status=Moved)
5. 🎯 تركيز اليوم (قائمة يدوية)
6. 📝 ملاحظات اليوم (toggle)

**ما لم يتغيّر:** Lead Inbox (القسم 2) + Sidebar (القسم 1) + Background DBs + خطة 14 يوم (مع تعديل Day 3 لإنتاج Bootstrap Mode بدل v1.0).

---

## 1. Notion v2.0 — هيكل Sidebar النهائي

```
📌 AI Sales OS
│
├── ⭐ اليوم              ← (PRIMARY — افتح هنا كل صباح)
├── 📥 Lead Inbox          ← (قاعدة بيانات)
├── 📖 Manual              ← (صفحة — محتوى MANUAL.md)
├── 🛠️ Runbook            ← (صفحة — محتوى RUNBOOK.md)
│
├── ─────────────────────
│
├── 📁 Background          ← (folder — مخفي في طي الاستخدام اليومي)
│   ├── 🏢 Companies
│   ├── 👥 Contacts
│   ├── ✅ Tasks
│   ├── 🤝 Meetings
│   ├── 💼 Opportunities
│   ├── 📝 Activities
│   └── 📧 Email Hub
│
└── 📦 Archive             ← (folder — للمرجعية فقط)
    ├── Old Dashboards (9 HTML)
    ├── Old Command Center
    ├── Old Loop Dashboard
    ├── Old Morning Brief pages
    └── Old Reports
```

### القواعد الصارمة

- **أعلى sidebar:** 4 عناصر فقط (⭐ 📥 📖 🛠️). لا خامس.
- **Background folder:** مطوي افتراضيًا. لا يُفتح يوميًا.
- **Archive folder:** مطوي. لا يُفتح إلا نادرًا.
- **الألوان في sidebar:**
  - ⭐ اليوم: أزرق فاتح
  - 📥 Lead Inbox: أخضر
  - 📖 Manual + 🛠️ Runbook: رمادي
  - Background + Archive: رمادي داكن

---

## 2. Lead Inbox — MVP Schema

**نوع:** Notion Database جديدة
**الاسم:** `Lead Inbox`
**الهدف:** نقطة دخول موحدة لكل lead جديد، لكل المسارات غير-Apollo.

### الحقول (12 حقل، لا أكثر)

| # | اسم الحقل | النوع | إلزامي | القيم/الملاحظات |
|---|---|---|---|---|
| 1 | Name | title | ✅ | اسم الشخص |
| 2 | Source | select | ✅ | Apollo / Manual / Referral / Import / Muqawil / Other |
| 3 | Company Name | rich_text | ✅ | اسم الشركة (نص حر حتى التأهيل) |
| 4 | Email | email | ❌ | |
| 5 | Phone | phone | ❌ | |
| 6 | Title | rich_text | ❌ | |
| 7 | Status | status | ✅ | New / Review / Qualified / Duplicate / Rejected / Moved |
| 8 | Warm Signal | checkbox | ❌ | للـ referral/inbound |
| 9 | Intake Owner | select | ✅ | Ragheed / Ibrahim / Soha |
| 10 | Intake Date | date | auto | تلقائي عند الإضافة |
| 11 | Notes | rich_text | ❌ | ملاحظة سريعة |
| 12 | Rejection Reason | select | ❌ | Not ICP / No Contact Method / Low Quality / Out of Scope / Duplicate |

**ملاحظة:** Matched Company (relation → Companies DB) تُضاف في Phase 2 عندما يكون Lead Inbox مستقرًا. الآن، Company Name كنص حر يكفي.

### Status State Machine

```
         ┌─────┐
         │ New │  ← كل lead جديد يبدأ هنا
         └──┬──┘
            │
            ▼
      ┌──────────┐
      │  Review  │  ← اختياري، للحالات غير الواضحة
      └─────┬────┘
            │
   ┌────────┼────────┬──────────┐
   │        │        │          │
   ▼        ▼        ▼          ▼
┌──────┐ ┌───────┐ ┌─────────┐ ┌────────┐
│Qualified│Rejected│Duplicate │ │ Review │
└───┬──┘ └───────┘ └─────────┘ └────────┘
    │
    ▼
┌───────┐
│ Moved │  ← انتقل إلى Contacts DB
└───────┘
```

### Views داخل Lead Inbox (4 فقط)

| View | فلتر | Sort |
|---|---|---|
| **🆕 جديد** | Status = New | Intake Date DESC |
| **🔍 قيد المراجعة** | Status = Review | Intake Date ASC (الأقدم أولًا) |
| **✅ جاهز للنقل** | Status = Qualified | Warm Signal DESC, Intake Date ASC |
| **📦 مؤرشف** | Status ∈ {Rejected, Moved, Duplicate} | Intake Date DESC |

### Templates السريعة (في أعلى Lead Inbox)

**Template 1: ➕ Lead يدوي**
- Source: Manual
- Status: New
- Intake Owner: (يُختار)

**Template 2: 🤝 Lead من علاقة شخصية**
- Source: Referral
- Status: Review (مراجعة فورية)
- Warm Signal: ✅
- Intake Owner: (يُختار)
- Notes: prompt "السياق؟"

**Template 3: 💳 بطاقة عمل**
- Source: Other
- Status: New
- Intake Owner: (يُختار)

### Review Flow (كيف يتحرك lead)

1. **New** → رغيد يراجع (يوميًا 10 دقائق)
2. راجع الاسم + الشركة + طريقة التواصل
3. قرار:
   - ✅ مناسب → Status = Qualified → املأ أي معلومات ناقصة → Status = Moved
   - ❌ غير مناسب → Status = Rejected + Rejection Reason
   - 👯 مكرر → Status = Duplicate
   - 🤔 غير واضح → Status = Review → عد غدًا
4. عند **Moved**: يتم إنشاء سجل في Contacts DB يدويًا (أو عبر button/automation في Phase 2)

### Dedup Logic (يدوي في MVP)

عند مراجعة lead جديد، افتح view "📦 مؤرشف" وابحث:
- هل نفس الإيميل موجود؟ → Duplicate
- هل نفس الهاتف؟ → Duplicate
- هل نفس الاسم + نفس الشركة؟ → Duplicate

في Phase 2: سكربت تلقائي يفحص ضد Contacts DB.

---

## 3. صفحة "اليوم" — التصميم التفصيلي

> ⚠️ **ملاحظة 2026-04-10:** هذا القسم يصف نسخة v1.0 الأصلية (Tasks + Opportunities + Apollo). النسخة الحية حاليًا هي **v0.1 Bootstrap Mode** — مواصفاتها في `notion/v2/today_page/schema.md`. ما تحت هذا السطر محفوظ كمرجع لـ v1.0 المستقبلي.


**النوع:** صفحة Notion (ليست DB)
**الاسم:** `⭐ اليوم`
**الهدف:** نقطة البداية الوحيدة كل صباح.

### الترتيب من أعلى إلى أسفل

```
┌─────────────────────────────────────────────┐
│ 📅 [التاريخ تلقائي]                          │
│ ☀️ صباح الخير رغيد                            │
│                                             │
│ ┌─────────────── حالة النظام ─────────────┐ │
│ │ 🟢 Apollo Sync: آخر تشغيل [timestamp]   │ │
│ │ 🟢 Scoring: جرى [timestamp]              │ │
│ │ 🟢 المهام: [X] مُنشأة                    │ │
│ │ 📥 Lead Inbox الجديد: [X] يحتاج مراجعة   │ │
│ └──────────────────────────────────────────┘ │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│ 📞 اتصل اليوم                                │
│ [linked view of Tasks DB — max 15 rows]     │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│ ✉️ تابع اليوم                                │
│ [linked view of Tasks DB — max 30 rows]     │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│ 💼 الصفقات                                   │
│ [linked view of Opportunities DB]           │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│ 📥 البريد الوارد                             │
│ [linked view of Lead Inbox — Status=New]    │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│ ▸ 📝 ملاحظات اليوم                           │
│   (toggle — اكتب ملاحظة سطر واحد)            │
│                                             │
│ ▸ 📝 ملاحظات الأسبوع                         │
│   (toggle — تُراجع يوم الأحد)                │
│                                             │
└─────────────────────────────────────────────┘
```

### Section 1: حالة النظام (Callout Blocks)

نصوص ثابتة في 4 callouts. تُحدَّث يدويًا أسبوعيًا، أو عبر سكربت صغير يكتب في Notion (Phase 2).

**في MVP:** نصوص ثابتة، رغيد يتحقق يدويًا من GitHub Actions مرة في الأسبوع.

**في Phase 2:** سكربت `monitoring/today_page_updater.py` يقرأ `last_sync_stats.json` ويحدّث الـ callouts.

### Section 2: 📞 اتصل اليوم

**Type:** Linked Database View من Tasks DB

**Filters:**
```
Task Type = "Urgent Call"
AND Status ≠ "Completed"
AND Due Date ≤ Today
AND Task Owner = Current User (أو filter يدوي = Ragheed)
```

**Sort:**
```
Priority DESC
Due Date ASC
```

**Columns المعروضة (5 فقط):**
1. Company (relation)
2. Primary Contact (rich_text أو عبر Task Title)
3. Phone (pulled from Contact relation)
4. Last Contacted (pulled from Contact)
5. Priority

**Limit:** 15 rows max (عبر pagination في Notion)

### Section 3: ✉️ تابع اليوم

**Type:** Linked Database View من Tasks DB

**Filters:**
```
Task Type = "Follow-up"
AND Status ≠ "Completed"
AND Due Date ≤ Today + 2 days
AND Task Owner = Current User
```

**Sort:**
```
Last Contacted ASC (الأقدم أولًا)
```

**Columns:**
1. Company
2. Primary Contact
3. Email
4. Last Contacted
5. Sequence Status (pulled from Contact)

**Limit:** 30 rows

### Section 4: 💼 الصفقات

**Type:** Linked Database View من Opportunities DB

**Filters:**
```
Stage ∉ {Closed Won, Closed Lost}
AND Opportunity Owner = Current User
```

**Sort:**
```
Stage (custom order: Discovery → Proposal → Negotiation)
Expected Close Date ASC
```

**Columns:**
1. Opportunity Name
2. Company
3. Stage
4. Deal Value
5. Next Action
6. Deal Health (🟢/🟡/🔴)

### Section 5: 📥 البريد الوارد

**Type:** Linked Database View من Lead Inbox

**Filters:**
```
Status = "New"
AND Intake Owner = Current User
```

**Sort:**
```
Warm Signal DESC (leads حارة أولًا)
Intake Date DESC
```

**Columns:**
1. Name
2. Company Name
3. Source
4. Warm Signal
5. Intake Date

**هدف هذا القسم:** تذكير بصري يومي أن هناك leads تحتاج مراجعة. يُستخدم في 16:45.

### Section 6: 📝 Toggles

- **Toggle 1: ملاحظات اليوم** — نص حر، يُمسح أو يُضاف كل يوم
- **Toggle 2: ملاحظات الأسبوع** — نص حر، يُراجَع يوم الأحد

---

## 4. ما يُنقل إلى Background

كل هذه موجودة اليوم في top-level sidebar أو قابلة للوصول مباشرة. تُنقل إلى folder واحد "Background":

- Companies DB
- Contacts DB
- Tasks DB
- Meetings DB
- Opportunities DB
- Activities DB
- Email Hub DB

**القاعدة:** هذه قواعد بيانات خلفية، تُغذّي صفحة "اليوم" عبر linked views. لا تُفتح يدويًا للعمل اليومي.

---

## 5. ما يُنقل إلى Archive

- 9 HTML dashboards الموجودة في `dashboards/` (تبقى كملفات لكن links لها تُنقل من top-level Notion)
- Old Command Center (إذا كان موجودًا كصفحة Notion)
- Old Loop Dashboard
- Old Morning Brief Notion pages (إن وجدت)
- MUHIDE strategic analysis reports القديمة
- أي صفحة Notion لم تُفتح في آخر 30 يوم

**لا تُحذف.** فقط تُنقل إلى Archive folder.

---

## 6. خطة تنفيذ 14 يوم

### الأسبوع 1 — بناء الواجهة (بدون لمس الخلفية)

#### 📅 اليوم 1 (Friday 2026-04-11)
**الهدف:** Scope Lock + المصادقة
**الفعل:**
- مراجعة ومصادقة رغيد على هذا الـ Blueprint
- قرار نعم/لا على البدء

**Gate:** موافقة صريحة من رغيد
**Rollback:** لا شيء يُنفَّذ بعد، rollback تلقائي

---

#### 📅 اليوم 2 (Saturday 2026-04-12)
**الهدف:** إنشاء Lead Inbox DB
**الفعل:**
- استخدام `notion-schema-manager` skill
- إنشاء قاعدة بـ 12 حقل محددة أعلاه
- إضافة 4 views (جديد، قيد المراجعة، جاهز للنقل، مؤرشف)
- اختبار: أضف 3 سجلات تجريبية

**Gate:** Lead Inbox تقبل سجلات
**Rollback:** حذف DB من Notion (30 ثانية)

---

#### 📅 اليوم 3 (Sunday 2026-04-13) — **Bootstrap Mode Pivot**
**الهدف:** إنشاء صفحة "اليوم" بنسخة v0.1 Bootstrap Mode (Lead Inbox فقط)
**السبب:** النظام الخلفي (Tasks, Opportunities) مبني لكن لم يُشغَّل فعليًا، لذا صفحة "اليوم" لا يمكن أن تعتمد عليه بعد.

**الفعل:**
- صفحة Notion جديدة ⭐ اليوم (✅ أُنجز في 2026-04-10)
- 4 linked database views من **📥 Lead Inbox** فقط:
  - 📥 Leads جديدة (Status = New)
  - 🔍 Leads تحت المراجعة (Status = Review)
  - ✅ Leads مؤهلة وجاهزة للنقل (Status = Qualified)
  - 🚚 Leads نُقلت إلى CRM (Status = Moved)
- 1 قائمة يدوية 🎯 تركيز اليوم (to-do blocks)
- 1 toggle 📝 ملاحظات اليوم
- **لا Tasks، لا Opportunities، لا Apollo، لا Dashboard، لا Header status**

**Gate:** الصفحة تعرض 4 views من Lead Inbox بشكل صحيح، وقائمة تركيز اليوم قابلة للاستخدام
**Rollback:** تعديل الصفحة — لا حذف (المحتوى القديم لا يعمل على أي حال)

**معايير الترقية إلى v1.0:** موثقة في RUNBOOK.md — باختصار: 20+ lead في Contacts DB، auto_tasks شُغِّل بنجاح 3+ مرات، 1+ Opportunity حقيقي، 1+ Meeting حقيقي، 5+ محادثات مبيعات.

---

#### 📅 اليوم 4 (Monday 2026-04-14)
**الهدف:** إعادة ترتيب Sidebar
**الفعل:**
- إنشاء folder "Background" في sidebar
- نقل Companies, Contacts, Tasks, Meetings, Opportunities, Activities, Email Hub إليه
- إنشاء folder "Archive"
- نقل dashboards/old pages القديمة إليه
- تثبيت ⭐ اليوم + 📥 Lead Inbox + 📖 Manual + 🛠️ Runbook في أعلى sidebar

**Gate:** Sidebar يحتوي على 4 عناصر فقط في الأعلى + folders
**Rollback:** إعادة سحب الصفحات إلى الأعلى (5 دقائق)

---

#### 📅 اليوم 5 (Tuesday 2026-04-15)
**الهدف:** إنشاء Notion pages لـ Manual و Runbook
**الفعل:**
- إنشاء صفحة "📖 Manual" في Notion
- نسخ محتوى `MANUAL.md` إليها (أو embed كمصدر خارجي)
- إنشاء صفحة "🛠️ Runbook" في Notion
- نسخ محتوى `RUNBOOK.md` إليها

**Gate:** الصفحتان قابلتان للقراءة في Notion
**Rollback:** حذف الصفحتين (30 ثانية)

---

#### 📅 اليوم 6 (Wednesday 2026-04-16)
**الهدف:** اختبار يوم كامل
**الفعل:**
- رغيد يستخدم صفحة "اليوم" فقط طوال اليوم (9 صباحًا - 5 مساءً)
- يحاول أن لا يفتح أي صفحة أخرى
- يسجّل في toggle "ملاحظات اليوم": كم مرة احتاج فتح صفحة خارج "اليوم"؟

**Gate:** ≤ 3 مرات احتياج لفتح صفحة خارجية. أكثر من 3 = نقطة ضعف
**Rollback:** العودة للاستخدام القديم (فوري)

---

#### 📅 اليوم 7 (Thursday 2026-04-17) — **Gate 1**
**الهدف:** مراجعة الأسبوع الأول
**الفعل:**
- مراجعة ملاحظات رغيد من اليوم 6
- تحديد العوائق
- قرار: هل نستمر إلى الأسبوع 2؟

**Gate 1 Criteria:**
- [ ] صفحة "اليوم" تعرض بيانات صحيحة
- [ ] Lead Inbox تستقبل سجلات
- [ ] رغيد قادر على العمل من الصفحة بدون تشتت
- [ ] عدد صفحات خارج "اليوم" اليوم ≤ 3

**إذا ✅:** استمر إلى الأسبوع 2
**إذا ❌:** أصلح الخلل ثم كرر اليوم 6

---

### الأسبوع 2 — التجميد والتنظيف

#### 📅 اليوم 8 (Friday 2026-04-18)
**الهدف:** تجميد daily dashboard generation
**الفعل:**
- تعديل `.github/workflows/daily_sync.yml`
- تعليق الخطوات 12-13 من Job 2 (dashboard_generator + commit dashboard)
- تشغيل تجريبي للـ workflow للتأكد أنه لا يزال يعمل

**Gate:** Workflow ينجح بدون dashboard generation
**Rollback:** uncomment الأسطر (2 دقائق)

---

#### 📅 اليوم 9 (Saturday 2026-04-19)
**الهدف:** تجميد `morning_brief.py` من Job 2
**الفعل:**
- تعليق `morning_brief.py --output file` في workflow
- تأكيد: الصفحة "اليوم" تحتوي على نفس المعلومات
- تحديث CLAUDE.md → إضافة قسم "Frozen Components"

**Gate:** Workflow ينجح، morning brief لم يعد يُولَّد
**Rollback:** uncomment (2 دقائق)

---

#### 📅 اليوم 10 (Sunday 2026-04-20)
**الهدف:** تحديث CLAUDE.md
**الفعل:**
- إضافة قسم جديد في CLAUDE.md:
  - "v2.0 Operator Layer"
  - قائمة Frozen Components
  - إشارة إلى MANUAL.md و RUNBOOK.md و COMMAND_MAP.md
- تشغيل `doc_sync_checker.py --strict` للتأكد من عدم وجود drift

**Gate:** `doc_sync_checker` يعطي 0 errors
**Rollback:** git revert (فوري)

---

#### 📅 اليوم 11 (Monday 2026-04-21)
**الهدف:** كتابة `intake/import_list.py`
**الفعل:**
- إنشاء مجلد `scripts/intake/`
- كتابة سكربت ~150 سطر:
  - قراءة CSV
  - validation
  - dedup ضد Lead Inbox
  - كتابة في Lead Inbox عبر Notion API
- اختبار على CSV بـ 10 سجلات

**Gate:** السكربت يستورد 10 سجلات بنجاح
**Rollback:** حذف الملف (فوري)

---

#### 📅 اليوم 12 (Tuesday 2026-04-22)
**الهدف:** اختبار workflow كامل من Lead Inbox → Contacts
**الفعل:**
- أضف 5 leads يدويًا عبر templates
- راجعهم
- Qualified → أنشئ contacts يدويًا في Contacts DB
- تحقق من ظهورهم في "اتصل اليوم" بعد sync التالي

**Gate:** 5 leads انتقلت بنجاح إلى pipeline
**Rollback:** حذف test records

---

#### 📅 اليوم 13 (Wednesday 2026-04-23)
**الهدف:** تدريب ذاتي كامل
**الفعل:**
- رغيد يستخدم النظام يومًا كاملًا بدون مساعدة
- يتبع MANUAL.md و RUNBOOK.md حرفيًا
- يسجّل أي غموض أو عائق

**Gate:** اليوم يمر بدون الحاجة لمساعدة خارجية
**Rollback:** غير مطلوب

---

#### 📅 اليوم 14 (Thursday 2026-04-24) — **Gate 2**
**الهدف:** مراجعة الأسبوعين
**الفعل:**
- جلسة مراجعة 30 دقيقة
- مراجعة criteria

**Gate 2 Criteria:**
- [ ] رغيد استخدم صفحة "اليوم" كنقطة بداية كل يوم من الأيام السبعة الأخيرة
- [ ] Lead Inbox استقبل ≥ 10 leads
- [ ] ≥ 5 leads انتقلت إلى CRM
- [ ] 0 شكاوى "لا أعرف ماذا أفعل"
- [ ] `daily_sync.py` لم يُلمس
- [ ] Pipeline اليومي يعمل ✅

**إذا ✅ ✅ ✅:** v2.0 Operator Layer معتمد رسميًا. انتقل إلى Phase 2 (الأسبوع 3-4)
**إذا ❌:** توقف، قيّم، أصلح

---

### الأسبوع 3-4 — الاستقرار (بدون ميزات جديدة)

فقط استخدام يومي + إصلاح bugs صغيرة + قياس.

### الشهر 2 — Phase 2

بعد ثبات الأسبوعين:
- بناء Enrichment Agent (trigger-based)
- إضافة Source field إلى Contacts DB
- اختبار إعادة توجيه Apollo HOT leads إلى Lead Inbox (pilot)

---

## 7. Phase 2+ (مؤجَّل، للتخطيط فقط)

**الشهر 2 (30-60 يوم):**
- Enrichment Agent على Lead Inbox Qualified records
- Source field في Contacts + Source Boost في Scoring
- Muqawil pipeline → dual-write إلى Lead Inbox

**الشهر 3 (60-90 يوم):**
- Apollo HOT leads redirect إلى Lead Inbox (pilot)
- `today_page_updater.py` لتحديث حالة النظام تلقائيًا
- قياس conversion rate من Lead Inbox → Closed Won

**الشهر 4+ (لاحقًا):**
- Odoo integration
- Lead Score v2.0
- Job Change Detection
- Apollo full redirect (إذا نجح pilot)

**لا تفكر في هذه الآن.** ركّز على الأسبوعين.

---

## 8. المخاطر الرئيسية و Mitigations

| الخطر | الاحتمال | التأثير | الحل |
|---|---|---|---|
| صفحة "اليوم" filters خاطئة | متوسط | متوسط | اختبار اليوم 3، تصحيح يدوي |
| Lead Inbox تتراكم | متوسط | متوسط | تنبيه يومي 16:45 + حد أقصى 50/يوم |
| رغيد يرجع للعادة القديمة | عالٍ | عالٍ | Archive folder يمنع الوصول السريع |
| Notion API error | منخفض | عالٍ | Rollback خطة (30 دقيقة) |
| `daily_sync.py` يتوقف لسبب خارجي | منخفض | عالٍ | Backfill runbook جاهز |
| duplication بين Inbox و Contacts | متوسط | منخفض | dedup يدوي في MVP |

---

## 9. معيار النجاح النهائي

**معيار واحد فقط:**

> في يوم 14، رغيد يستطيع الإجابة على هذا السؤال بنعم:
> **"هل أفتح Notion كل صباح وأعرف ماذا أفعل خلال 30 ثانية؟"**

إذا الجواب نعم → v2.0 نجح.
إذا الجواب لا → توقف، حلل، أصلح.

لا شيء آخر يُقاس. ليس عدد السكربتات، ليس عدد الصفحات، ليس جودة الكود. فقط هذا السؤال.
