# 🎯 AI SALES OS — RACI MATRIX & RESPONSIBILITIES

**المشروع:** نظام بيع موحد Apollo + Notion + Odoo
**التاريخ:** 24 مارس 2026
**الفترة:** 8 أسابيع

---

## 📊 RACI LEGEND

| الرمز | المعنى | الوصف |
|------|--------|-------|
| **R** | Responsible | الشخص الذي ينفذ العمل |
| **A** | Accountable | صاحب القرار النهائي |
| **C** | Consulted | يُسأل للرأي قبل الإجراء |
| **I** | Informed | يُطلع بعد الانتهاء |

---

## 🗓️ RACI MATRIX — PHASE 1B (استيراد وربط البيانات)

### المهام الأساسية

```
Task: اختبار 100 سجل
─────────────────────────────────────────────────────────
 Project Lead        │ A
 RevOps Lead         │ R
 Data Engineer       │ C
 QA Lead             │ C
─────────────────────────────────────────────────────────

Task: استيراد 3,606 شركات
─────────────────────────────────────────────────────────
 Project Lead        │ A
 RevOps Lead         │ R
 Data Engineer       │ C
 QA Lead             │ I
─────────────────────────────────────────────────────────

Task: استيراد 5,898 جهة اتصال
─────────────────────────────────────────────────────────
 Project Lead        │ A
 RevOps Lead         │ R
 Data Engineer       │ C
 QA Lead             │ I
─────────────────────────────────────────────────────────

Task: الربط التلقائي (link_companies_contacts.py)
─────────────────────────────────────────────────────────
 Project Lead        │ A
 Data Engineer       │ R
 RevOps Lead         │ C
 QA Lead             │ C
─────────────────────────────────────────────────────────

Task: التحقق من الجودة
─────────────────────────────────────────────────────────
 Project Lead        │ A
 QA Lead             │ R
 RevOps Lead         │ C
 Data Engineer       │ I
─────────────────────────────────────────────────────────
```

---

## 🗓️ RACI MATRIX — PHASE 2 (تكامل Apollo)

```
Task: تفعيل Apollo MCP
─────────────────────────────────────────────────────────
 Project Lead        │ A
 Data Engineer       │ R
 RevOps Lead         │ C
 IT Security         │ C
─────────────────────────────────────────────────────────

Task: سحب Intent Signals (مزامنة يومية)
─────────────────────────────────────────────────────────
 Project Lead        │ A
 Data Engineer       │ R
 Data Analyst        │ C
 RevOps Lead         │ I
─────────────────────────────────────────────────────────

Task: إثراء Lead Score (صيغة وتوزيع)
─────────────────────────────────────────────────────────
 Project Lead        │ A
 Data Analyst        │ R
 AI Specialist       │ R
 RevOps Lead         │ C
 QA Lead             │ C
─────────────────────────────────────────────────────────
```

---

## 🗓️ RACI MATRIX — PHASE 3 (الأتمتة التنفيذية)

```
Task: أتمتة إنشاء المهام
─────────────────────────────────────────────────────────
 Project Lead        │ A
 Process Engineer    │ R
 RevOps Lead         │ C
 Sales Manager       │ C
─────────────────────────────────────────────────────────

Task: أتمتة جدولة الاجتماعات
─────────────────────────────────────────────────────────
 Project Lead        │ A
 Process Engineer    │ R
 Calendar Admin      │ C
 Sales Manager       │ C
─────────────────────────────────────────────────────────

Task: أتمتة إنشاء الفرص
─────────────────────────────────────────────────────────
 Project Lead        │ A
 Process Engineer    │ R
 Sales Manager       │ C
 Data Analyst        │ C
─────────────────────────────────────────────────────────

Task: تتبع النشاطات والمقاييس
─────────────────────────────────────────────────────────
 Project Lead        │ A
 Data Analyst        │ R
 Sales Manager       │ C
 Executive           │ I
─────────────────────────────────────────────────────────
```

---

## 🗓️ RACI MATRIX — PHASE 4 (دمج Odoo)

```
Task: ربط Notion بـ Odoo
─────────────────────────────────────────────────────────
 Project Lead        │ A
 Data Engineer       │ R
 Odoo Admin          │ R
 IT Security         │ C
─────────────────────────────────────────────────────────

Task: مزامنة الفرص (Real-time)
─────────────────────────────────────────────────────────
 Project Lead        │ A
 Data Engineer       │ R
 Odoo Admin          │ C
 Finance Manager     │ I
─────────────────────────────────────────────────────────

Task: تتبع الإيرادات والتنبؤات
─────────────────────────────────────────────────────────
 CFO / Finance Lead  │ A
 Data Analyst        │ R
 Sales Manager       │ C
 Executive           │ I
─────────────────────────────────────────────────────────
```

---

## 👥 TEAM STRUCTURE & ROLES

### الفريق الأساسي (7 أشخاص)

```
┌─────────────────────────────────────────────────────────┐
│                 PROJECT LEAD (1)                        │
│  ↓                                                      │
│  Responsible for:                                       │
│  ├─ Overall timeline and budget                         │
│  ├─ Risk management                                     │
│  ├─ Stakeholder communication                           │
│  └─ Go/No-Go decisions                                  │
│                                                         │
│  Time: 40% (16 hours/week)                              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              REVOPS LEAD / OPERATIONS (1)               │
│  ↓                                                      │
│  Responsible for:                                       │
│  ├─ Data import coordination                            │
│  ├─ Process design and documentation                    │
│  ├─ Team training                                       │
│  └─ Daily operations post-launch                        │
│                                                         │
│  Time: 100% (40 hours/week)                             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              DATA ENGINEER / TECHNICAL (1)              │
│  ↓                                                      │
│  Responsible for:                                       │
│  ├─ API integrations                                    │
│  ├─ Data pipeline setup                                 │
│  ├─ Automation development                              │
│  ├─ System monitoring                                   │
│  └─ Troubleshooting                                     │
│                                                         │
│  Time: 100% (40 hours/week)                             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              DATA ANALYST / INTELLIGENCE (1)            │
│  ↓                                                      │
│  Responsible for:                                       │
│  ├─ Lead Score calculations                             │
│  ├─ Data quality reporting                              │
│  ├─ Analytics and insights                              │
│  └─ KPI tracking                                        │
│                                                         │
│  Time: 80% (32 hours/week)                              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              QA / VALIDATION LEAD (1)                   │
│  ↓                                                      │
│  Responsible for:                                       │
│  ├─ Data validation                                     │
│  ├─ Testing automation rules                            │
│  ├─ Quality assurance sign-off                          │
│  └─ Issue tracking                                      │
│                                                         │
│  Time: 60% (24 hours/week)                              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              SALES MANAGER / STAKEHOLDER (1)            │
│  ↓                                                      │
│  Responsible for:                                       │
│  ├─ Sales team input and requirements                   │
│  ├─ Training and adoption                               │
│  ├─ Performance tracking                                │
│  └─ Feedback to operations                              │
│                                                         │
│  Time: 50% (20 hours/week)                              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              SUPPORT / DOCUMENTATION (1)                │
│  ↓                                                      │
│  Responsible for:                                       │
│  ├─ Documentation and guides                            │
│  ├─ Training materials                                  │
│  ├─ User support                                        │
│  └─ Knowledge base management                           │
│                                                         │
│  Time: 40% (16 hours/week)                              │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 ROLE DESCRIPTIONS & RESPONSIBILITIES

### 1. PROJECT LEAD

**متطلبات:**
- 5+ سنة إدارة مشاريع
- خبرة مع أنظمة CRM
- مهارات قيادة قوية

**المسؤوليات:**
```
Strategic:
├─ تعريف الرؤية والأهداف
├─ تخطيط الموارد
├─ إدارة المخاطر
└─ التواصل مع الإدارة

Tactical:
├─ المراقبة الأسبوعية
├─ حل المشاكل العالقة
├─ قرارات التوقيت
└─ الموافقة على التغييرات
```

**رابط التقرير:** أسبوعي إلى التنفيذي

---

### 2. REVOPS LEAD

**متطلبات:**
- 3+ سنة في العمليات
- خبرة مع Notion/CRM
- مهارات تصميم العمليات

**المسؤوليات:**
```
Operational:
├─ إجراء الاستيراد الفعلي
├─ التحقق من البيانات اليومي
├─ مراقبة الأداء
└─ استكشاف الأخطاء

Documentation:
├─ توثيق العمليات
├─ إنشاء أدلة المستخدم
├─ تدريب الفريق
└─ إدارة المعرفة

Process Design:
├─ تحسين سير العمل
├─ تحديد الاختناقات
└─ اقتراح التحسينات
```

**رابط التقرير:** يومي إلى Project Lead

---

### 3. DATA ENGINEER

**متطلبات:**
- 3+ سنة هندسة بيانات
- خبرة مع APIs و Python
- فهم الهندسة المعمارية

**المسؤوليات:**
```
Development:
├─ بناء APIs والعمليات
├─ كتابة سكريبتات الربط
├─ اختبار التكامل
└─ تحسين الأداء

Integration:
├─ ربط Notion ↔ Apollo
├─ ربط Notion ↔ Odoo
├─ معالجة الأخطاء
└─ مراقبة الصحة

Maintenance:
├─ الدعم الفني
├─ استكشاف الأخطاء
├─ التحديثات
└─ التوثيق التقني
```

**رابط التقرير:** يومي إلى Project Lead

---

### 4. DATA ANALYST

**متطلبات:**
- 2+ سنة تحليل بيانات
- خبرة مع Excel/SQL
- فهم القياس

**المسؤوليات:**
```
Analysis:
├─ تحليل جودة البيانات
├─ حساب المقاييس
├─ الإبلاغ عن الرؤى
└─ التنبؤات

Lead Scoring:
├─ تصميم الصيغة
├─ المعايرة والاختبار
├─ التوثيق
└─ التحديثات الدورية

Reporting:
├─ تقارير KPI
├─ لوحات التحكم
├─ تحليل الأداء
└─ توصيات التحسين
```

**رابط التقرير:** أسبوعي إلى Project Lead

---

### 5. QA LEAD

**متطلبات:**
- 2+ سنة ضمان الجودة
- فهم البيانات
- مهارات الاختبار

**المسؤوليات:**
```
Testing:
├─ اختبار الاستيراد
├─ التحقق من الربط
├─ اختبار الأتمتة
└─ اختبار الأداء

Validation:
├─ التحقق من البيانات
├─ حساب النسب المئوية
├─ توثيق المشاكل
└─ متابعة الإصلاحات

Sign-off:
├─ موافقة المرحلة
├─ توصيات الإصدار
├─ قائمة الأشياء المتبقية
└─ القبول النهائي
```

**رابط التقرير:** يومي إلى Project Lead

---

## 📅 DECISION RIGHTS MATRIX

### من يوافق على ماذا؟

```
قرار: متابعة الاستيراد بعد المرحلة الأولى
├─ صاحب القرار: Project Lead + RevOps Lead
└─ معايير: جودة ≥ A-, 0 أخطاء حرجة

قرار: تفعيل الأتمتة
├─ صاحب القرار: Project Lead + Sales Manager
└─ معايير: اختبار شامل، موافقة QA

قرار: إطلاق Odoo Integration
├─ صاحب القرار: CFO + Project Lead + Odoo Admin
└─ معايير: موافقة جميع الأطراف، اختبار شامل

قرار: توقف المشروع أو تأجيله
├─ صاحب القرار: Executive + Project Lead
└─ معايير: مشاكل جسيمة أو موارد غير كافية
```

---

## 🎓 TRAINING & ONBOARDING

### Phase 1B (الاستيراد والربط)

```
TRAINING SESSION 1: نظرة عامة على النظام
├─ المدة: 2 ساعة
├─ الجمهور: جميع الفريق (7 أشخاص)
├─ الموضوعات:
│  ├─ أهداف المشروع
│  ├─ البنية المعمارية
│  ├─ أدوارنا المسؤولة
│  └─ الخط الزمني
└─ الملفات: Blueprint + Execution Plan

TRAINING SESSION 2: فني Notion للاستيراء
├─ المدة: 3 ساعات
├─ الجمهور: RevOps, Engineer, QA (3 أشخاص)
├─ الموضوعات:
│  ├─ كيفية استيراد CSV
│  ├─ كيفية استيراد JSON
│  ├─ معالجة الأخطاء
│  └─ التحقق من البيانات
└─ الملفات: IMPORT_GUIDE_Phase1C.md

TRAINING SESSION 3: البيانات والجودة
├─ المدة: 2 ساعة
├─ الجمهور: QA, Analyst (2 شخص)
├─ الموضوعات:
│  ├─ معايير الجودة
│  ├─ كيفية التحقق
│  ├─ الإبلاغ عن المشاكل
│  └─ الموافقة على الإصدار
└─ الملفات: DATA_COMPLETION_REPORT.md
```

---

## 📞 COMMUNICATION PLAN

### اجتماعات المشروع المنتظمة

```
DAILY STANDUP (15 دقيقة)
├─ الوقت: 9:30 صباحاً
├─ الحضور: جميع الفريق (7)
├─ الموضوعات:
│  ├─ ما تم إنجازه أمس
│  ├─ خطط اليوم
│  ├─ الحواجز والمشاكل
│  └─ نقاط العمل
└─ الملاحظات: Notion Doc (مشترك)

WEEKLY STEERING (1 ساعة)
├─ الوقت: يوم الخميس، 10 صباحاً
├─ الحضور: Project Lead + Leads (4 أشخاص)
├─ الجدول الزمني:
│  ├─ 15 دقيقة: حالة المشروع
│  ├─ 20 دقيقة: المخاطر والمشاكل
│  ├─ 15 دقيقة: القرارات
│  └─ 10 دقائق: الخطوات التالية
└─ الملاحظات: رسالة بريد إلى التنفيذي

BI-WEEKLY STAKEHOLDER (30 دقيقة)
├─ الوقت: يوم الثلاثاء، 2 مساءً
├─ الحضور: Project Lead + Sales Manager + Exec (3)
├─ الموضوعات:
│  ├─ تحديث التقدم
│  ├─ الآثار على الأعمال
│  ├─ الموارد المطلوبة
│  └─ الأسئلة والأجوبة
└─ الملاحظات: عرض شرائح تنفيذي

MONTHLY REVIEW (2 ساعة)
├─ الوقت: نهاية الأسبوع الأول من الشهر
├─ الحضور: جميع الفريق (7)
├─ الموضوعات:
│  ├─ المخرجات الشهرية
│  ├─ تحليل الأداء
│  ├─ دروس التعلم
│  ├─ التحسينات للشهر القادم
│  └─ الاحتفال بالإنجازات
└─ الملاحظات: محضر مفصل
```

---

## 📊 PERFORMANCE METRICS

### قياس فعالية الفريق

```
INDIVIDUAL METRICS:
├─ Utilization Rate (يجب أن تكون 80%+)
├─ Task Completion Rate (يجب أن تكون 95%+)
├─ Quality of Work (peer review)
└─ Communication Score (feedback)

TEAM METRICS:
├─ Schedule Adherence (يجب أن تكون 90%+)
├─ Budget Variance (يجب أن تكون ±5%)
├─ Risk Mitigation (0 مفاجآت)
└─ Stakeholder Satisfaction (يجب أن تكون 4+/5)

PROJECT METRICS:
├─ Data Quality (A+)
├─ System Uptime (99.5%+)
├─ User Adoption (80%+ في الشهر الأول)
└─ ROI (Break-even في Q3)
```

---

## ✅ SIGN-OFF TEMPLATE

```
PROJECT PHASE: _______________________
DATE: _______________________

PHASE LEAD SIGN-OFF:
Printed Name: _________________ Signature: _________ Date: _______
I confirm that this phase meets all defined acceptance criteria.

PROJECT LEAD APPROVAL:
Printed Name: _________________ Signature: _________ Date: _______
I approve moving forward to the next phase.

STAKEHOLDER ACKNOWLEDGMENT:
Printed Name: _________________ Signature: _________ Date: _______
I acknowledge receipt of this phase completion and next steps.

NOTES:
________________________________________________________________________
________________________________________________________________________
```

---

**آخر تحديث:** 24 مارس 2026
**الإصدار:** 2.0
**الحالة:** Ready for Implementation ✅
