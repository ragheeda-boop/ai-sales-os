# 📊 NOTION DATABASES SETUP GUIDE
## قواعد البيانات اللي تحتاجها في Notion

**التاريخ:** 24 مارس 2026
**الموضوع:** إعداد قواعد بيانات Notion الكاملة
**الحالة:** Ready for Phase 1B

---

## 🎯 قواعد البيانات المطلوبة

```
عدد القواعس الأساسية: 5
├─ 1. Companies (الشركات) ⭐ أساسية
├─ 2. Contacts (جهات الاتصال) ⭐ أساسية
├─ 3. Opportunities (الفرص) ⭐ أساسية
├─ 4. Tasks (المهام) ⭐ أساسية
└─ 5. Meetings (الاجتماعات) ⭐ أساسية

اختيارية (يمكن إضافتها لاحقاً):
├─ Email Hub
├─ Activity Log
├─ Campaigns
└─ Analytics Dashboard
```

---

## 1️⃣ COMPANIES DATABASE (الشركات)

### الفائدة:
```
✅ مخزن كل الشركات (3,606)
✅ ربط مركزي للـ Contacts و Opportunities
✅ تتبع Intent Signals وـ Lead Scores
✅ حفظ معلومات الشركة الكاملة
```

### الحقول المطلوبة:

```
📌 IDENTIFICATION (معرّفات)
├─ Name (اسم الشركة) ⭐ Text, Required
├─ Domain (المجال) ⭐ Email/URL, Unique
├─ Apollo Account ID (معرّف Apollo) ⭐ Text, Unique
└─ Record Source (المصدر) = Select: Apollo, Manual, Import

📊 COMPANY INFO (معلومات الشركة)
├─ Industry (الصناعة) = Select: SaaS, Finance, Tech, ...
├─ Company Size (حجم الشركة) = Select: 1-10, 11-50, 51-200, 201-500, 501-1K, 1K+
├─ Employee Count (عدد الموظفين) = Number
├─ Revenue Range (نطاق الإيرادات) = Select: <$1M, $1-10M, $10-50M, $50M+
├─ HQ Location (المقر الرئيسي) = Text
├─ Website (الموقع) = URL
└─ Phone (الهاتف) = Phone

💰 FUNDING INFO (معلومات التمويل)
├─ Latest Funding Stage (آخر مرحلة تمويل) = Select: Seed, Series A-H, IPO, Acquired
├─ Latest Funding Amount (آخر مبلغ تمويلي) = Currency
├─ Latest Funding Date (تاريخ آخر تمويل) = Date
└─ Total Funding (إجمالي التمويل) = Currency

🔗 RELATIONSHIPS (العلاقات)
├─ Contacts (جهات الاتصال) = Relation → Contacts DB (One-to-Many)
├─ Opportunities (الفرص) = Relation → Opportunities DB (One-to-Many)
└─ Tasks (المهام) = Relation → Tasks DB (One-to-Many)

🧠 INTELLIGENCE (الذكاء الاصطناعي)
├─ Intent Score (درجة النية) = Number (0-100)
│  └─ Definition: كم الشركة مهتمة (من Apollo)
├─ Engagement Score (درجة التفاعل) = Number (0-100)
│  └─ Definition: كم تفاعلت مع outreach
├─ Growth Rate (معدل النمو) = Percentage (%)
│  └─ Definition: النمو السنوي للموظفين
└─ Technology Stack (تقنيات مستخدمة) = Multi-select: Salesforce, HubSpot, AWS, ...

📈 SIGNALS (الإشارات)
├─ Job Postings (وظائف مفتوحة) = Number
├─ Website Activity (نشاط الموقع) = Number
├─ Funding News (أخبار تمويلية) = Checkbox
├─ Technology Changes (تغييرات تقنية) = Text
└─ Executive Changes (تغييرات قيادية) = Checkbox

⏰ TRACKING (التتبع)
├─ Created At (تاريخ الإضافة) = Date
├─ Updated At (آخر تحديث) = Date
├─ Last Synced (آخر مزامنة) = Date
└─ Data Status (حالة البيانات) = Select: Raw, Cleaned, Enriched, Verified
```

### Views المطلوبة في Companies:
```
1. All Companies
   └─ جميع الشركات مع كل الحقول

2. High Intent (80+)
   └─ Filter: Intent Score ≥ 80
   └─ Sort: Intent Score DESC

3. By Industry
   └─ Group By: Industry
   └─ يسهل البحث حسب الصناعة

4. Recently Updated
   └─ Filter: Updated At > 7 days ago
   └─ Sort: Updated At DESC
```

---

## 2️⃣ CONTACTS DATABASE (جهات الاتصال)

### الفائدة:
```
✅ مخزن جميع جهات الاتصال (5,898)
✅ تتبع Lead Scores والـ Engagement
✅ إدارة الـ Outreach والـ Sequences
✅ جدولة الـ Follow-ups والـ Meetings
```

### الحقول المطلوبة:

```
👤 PERSONAL INFO (معلومات شخصية)
├─ Full Name (الاسم الكامل) ⭐ Text, Required
├─ First Name (الاسم الأول) = Text
├─ Last Name (الاسم الأخير) = Text
├─ Apollo Contact ID (معرّف Apollo) ⭐ Text, Unique
└─ Email (البريد الإلكتروني) ⭐ Email, Unique

📞 CONTACT INFO (معلومات التواصل)
├─ Direct Phone (هاتف مباشر) = Phone
├─ Mobile Phone (هاتف جوال) = Phone
├─ Corporate Phone (هاتف العمل) = Phone
└─ LinkedIn URL (ملف LinkedIn) = URL

💼 JOB INFO (معلومات الوظيفة)
├─ Title (المسمى الوظيفي) = Text
├─ Seniority (المستوى الوظيفي) = Select: C-Suite, VP, Director, Manager, IC, Other
├─ Department (القسم) = Select: Sales, Marketing, Engineering, Finance, ...
└─ Reports To (يرفع التقارير إلى) = Text

🏢 COMPANY LINK (ربط الشركة)
├─ Company (الشركة) ⭐ Relation → Companies DB (Many-to-One)
├─ Company Domain (مجال الشركة) = Text (for matching)
├─ Company Name (اسم الشركة) = Text (for context)
└─ Company Industry (صناعة الشركة) = Text (for intelligence)

🎯 OUTREACH STATUS (حالة الـ Outreach)
├─ Outreach Status (حالة المراسلة) = Select:
│  ├─ Not Started (لم تبدأ)
│  ├─ In Sequence (في sequence)
│  ├─ Awaiting Reply (في انتظار رد)
│  ├─ Replied (ردّ)
│  └─ Closed (مغلقة)
├─ Qualification Status (حالة التأهيل) = Select:
│  ├─ Unqualified (غير مؤهلة)
│  ├─ Qualified (مؤهلة)
│  └─ Highly Qualified (مؤهلة جداً)
├─ Sequence Status (حالة الـ Sequence) = Select:
│  ├─ Not in Sequence
│  ├─ Active
│  ├─ Paused
│  └─ Completed
└─ Do Not Contact (عدم التواصل) = Checkbox

📊 ENGAGEMENT (التفاعل)
├─ Email Sent (بريد مرسل) = Number
├─ Email Opened (بريد مفتوح) = Number
├─ Email Clicked (بريد تم الضغط عليه) = Number
├─ Email Replied (رد على البريد) = Number
├─ Open Rate (نسبة الفتح) = Percentage (%)
├─ Click Rate (نسبة الضغط) = Percentage (%)
└─ Reply Rate (نسبة الرد) = Percentage (%)

💯 LEAD SCORE (درجة القيادة)
├─ Lead Score (درجة القيادة) ⭐ Number (0-100)
│  └─ Formula: (Intent × 40%) + (Engagement × 35%) + (Size × 15%) + (Industry × 10%)
├─ Last Score Update (آخر تحديث) = Date
└─ Score Trend (اتجاه الدرجة) = Select: ↑ Up, → Stable, ↓ Down

🔗 RELATIONSHIPS (العلاقات)
├─ Company (الشركة) = Relation → Companies DB
├─ Opportunities (الفرص) = Relation → Opportunities DB
├─ Tasks (المهام) = Relation → Tasks DB
└─ Meetings (الاجتماعات) = Relation → Meetings DB

⏰ TRACKING (التتبع)
├─ First Contacted (أول تواصل) = Date
├─ Last Contacted (آخر تواصل) = Date
├─ Last Activity (آخر نشاط) = Date
├─ Next Follow-up (المتابعة التالية) = Date
├─ Days Since Contact (أيام منذ التواصل) = Number (formula)
└─ Created At (تاريخ الإضافة) = Date
```

### Views المطلوبة في Contacts:
```
1. All Contacts
   └─ جميع جهات الاتصال

2. 🔴 HOT LEADS (80+)
   └─ Filter: Lead Score ≥ 80
   └─ Sort: Lead Score DESC
   └─ Priority: HIGH (ركز عليهم)

3. 🟡 WARM LEADS (50-79)
   └─ Filter: Lead Score 50-79
   └─ Sort: Lead Score DESC
   └─ Priority: MEDIUM (Nurture)

4. 🟢 COLD LEADS (<50)
   └─ Filter: Lead Score < 50
   └─ Sort: Lead Score DESC
   └─ Priority: LOW (Monitor)

5. Recently Updated
   └─ Filter: Last Activity > 7 days ago
   └─ Sort: Last Activity DESC

6. By Company
   └─ Group By: Company
   └─ عرض جميع الجهات لكل شركة

7. By Seniority
   └─ Group By: Seniority
   └─ تقسيم حسب المستوى الوظيفي

8. Awaiting Reply
   └─ Filter: Outreach Status = "Awaiting Reply"
   └─ Sort: Last Contacted ASC
   └─ Action: Follow-up needed
```

---

## 3️⃣ OPPORTUNITIES DATABASE (الفرص)

### الفائدة:
```
✅ تتبع الصفقات والمبيعات
✅ إدارة مراحل البيع (Discovery → Closed)
✅ تقدير الإيرادات والـ Probability
✅ ربط كل صفقة بـ Company و Contact
```

### الحقول المطلوبة:

```
📌 IDENTIFICATION (معرّفات)
├─ Opportunity Name (اسم الفرصة) ⭐ Text, Required
├─ Opportunity ID (معرّف الفرصة) ⭐ Text, Unique
└─ Record Source (المصدر) = Select: Apollo, Odoo, Manual, Import

🏢 RELATIONSHIPS (العلاقات)
├─ Company (الشركة) ⭐ Relation → Companies DB
├─ Primary Contact (جهة الاتصال الأساسية) = Relation → Contacts DB
└─ Secondary Contacts (جهات اتصال ثانوية) = Relation → Contacts DB (multi)

💰 DEAL INFO (معلومات الصفقة)
├─ Deal Value (قيمة الصفقة) ⭐ Currency
├─ Currency (العملة) = Select: USD, EUR, AED, ...
├─ Annual Recurring Revenue (الإيرادات السنوية) = Currency
└─ Contract Term (مدة العقد) = Select: 1 Year, 2 Years, 3 Years, Custom

📈 STAGE & TIMELINE (المرحلة والجدول الزمني)
├─ Stage (مرحلة الصفقة) ⭐ Select:
│  ├─ Discovery (اكتشاف)
│  ├─ Proposal (عرض)
│  ├─ Negotiation (تفاوض)
│  ├─ Closed Won (مغلقة - فاز)
│  └─ Closed Lost (مغلقة - خسر)
├─ Probability (احتمالية الفوز) = Select: 10%, 25%, 50%, 75%, 90%, 100%
├─ Created Date (تاريخ الإنشاء) = Date
├─ Expected Close Date (تاريخ الإغلاق المتوقع) = Date
├─ Actual Close Date (تاريخ الإغلاق الفعلي) = Date
└─ Days in Stage (أيام في هذه المرحلة) = Number (formula)

👤 OWNERSHIP (الملكية)
├─ Opportunity Owner (المسؤول عن الفرصة) = People
├─ Account Owner (مسؤول الحساب) = People
└─ Team (الفريق) = Select: Sales A, Sales B, Enterprise, ...

🎯 HEALTH & NEXT STEPS (الصحة والخطوات التالية)
├─ Deal Health (صحة الصفقة) = Select: 🟢 Green, 🟡 Yellow, 🔴 Red
├─ Health Reason (سبب الحالة) = Text
├─ Next Action (الخطوة التالية) = Text
├─ Blockers (العوائق) = Multi-select: Budget, Timeline, Stakeholder Approval, ...
├─ Competitor (المنافس) = Text (إن وجد)
└─ Risk Level (مستوى الخطر) = Select: Low, Medium, High

📊 TRACKING (التتبع)
├─ Notes (ملاحظات) = Text
├─ Last Updated (آخر تحديث) = Date
└─ Update Frequency (تكرار التحديث) = Select: Daily, Weekly, Monthly
```

### Views المطلوبة في Opportunities:
```
1. All Opportunities
   └─ جميع الفرص

2. Pipeline (خط أنابيب)
   └─ Group By: Stage
   └─ Show: Deal Value, Probability
   └─ Color code each stage

3. By Stage + Value
   └─ Group By: Stage
   └─ Sort By: Deal Value DESC

4. Red Flag Deals
   └─ Filter: Deal Health = Red
   └─ Priority: HIGH (تحتاج اهتمام)

5. Closing Soon
   └─ Filter: Expected Close Date ≤ 30 days
   └─ Sort: Expected Close Date ASC

6. By Owner
   └─ Group By: Opportunity Owner
   └─ عرض الفرص لكل شخص
```

---

## 4️⃣ TASKS DATABASE (المهام)

### الفائدة:
```
✅ تتبع المهام اليومية
✅ تلقائياً من Rule (مثل: Lead Score ≥ 80)
✅ إدارة Follow-ups والـ Next Actions
✅ ربط المهام بـ Contacts و Opportunities
```

### الحقول المطلوبة:

```
📌 IDENTIFICATION (معرّفات)
├─ Task Title (عنوان المهمة) ⭐ Text, Required
├─ Task ID (معرّف المهمة) ⭐ Text, Unique
└─ Task Type (نوع المهمة) = Select: Follow-up, Demo, Proposal, Review, Other

📝 DESCRIPTION (الوصف)
├─ Description (الوصف) = Text/Rich Text
├─ Context (السياق) = Text
└─ Expected Outcome (النتيجة المتوقعة) = Text

🔗 RELATIONSHIPS (العلاقات)
├─ Company (الشركة) = Relation → Companies DB
├─ Contact (جهة الاتصال) = Relation → Contacts DB
├─ Opportunity (الفرصة) = Relation → Opportunities DB
└─ Related Tasks (مهام مرتبطة) = Relation → Tasks DB (multi)

👤 ASSIGNMENT (التعيين)
├─ Assigned To (معيّن إلى) ⭐ People
├─ Created By (أنشأه) = People
└─ Team (الفريق) = Select: Sales A, Sales B, ...

📊 STATUS & PRIORITY (الحالة والأولوية)
├─ Status (الحالة) ⭐ Select:
│  ├─ Not Started (لم تبدأ)
│  ├─ In Progress (جارية)
│  └─ Completed (مكتملة)
├─ Priority (الأولوية) ⭐ Select:
│  ├─ Low (منخفضة)
│  ├─ Medium (متوسطة)
│  ├─ High (عالية)
│  └─ Critical (حرجة)
└─ Status Reason (سبب الحالة) = Text

⏰ TIMELINE (الجدول الزمني)
├─ Due Date (تاريخ الاستحقاق) ⭐ Date
├─ Start Date (تاريخ البداية) = Date
├─ Completed At (تاريخ الإنجاز) = Date
├─ Overdue? (متأخرة؟) = Checkbox (formula)
└─ Days Remaining (الأيام المتبقية) = Number (formula)

🤖 AUTOMATION (الأتمتة)
├─ Auto Created (أنشئت تلقائياً) = Checkbox
├─ Trigger Rule (قاعدة التفعيل) = Text
│  └─ مثال: "Lead Score ≥ 80", "Email Replied = True"
└─ Automation Type (نوع الأتمتة) = Select: Lead Scoring, Engagement, Approval, Other
```

### Views المطلوبة في Tasks:
```
1. My Tasks
   └─ Filter: Assigned To = [Current User]
   └─ Sort: Priority DESC, Due Date ASC

2. Overdue
   └─ Filter: Overdue? = True AND Status ≠ Completed
   └─ Priority: CRITICAL (تحتاج عملاً فوراً)

3. By Priority
   └─ Group By: Priority
   └─ Shows: Critical, High, Medium, Low

4. By Status
   └─ Group By: Status
   └─ Track: Not Started, In Progress, Completed

5. Due Soon
   └─ Filter: Due Date ≤ 7 days AND Status ≠ Completed
   └─ Sort: Due Date ASC

6. By Type
   └─ Group By: Task Type
   └─ Categorize: Follow-up, Demo, Proposal, ...
```

---

## 5️⃣ MEETINGS DATABASE (الاجتماعات)

### الفائدة:
```
✅ تتبع جميع الاجتماعات
✅ تسجيل Attendees والـ Notes
✅ ربط الاجتماعات بـ Opportunities
✅ تتبع Action Items بعد الاجتماع
```

### الحقول المطلوبة:

```
📌 IDENTIFICATION (معرّفات)
├─ Meeting Title (عنوان الاجتماع) ⭐ Text, Required
├─ Meeting ID (معرّف الاجتماع) ⭐ Text, Unique
└─ Meeting Type (نوع الاجتماع) = Select: Discovery, Demo, Proposal, Review, Other

🔗 RELATIONSHIPS (العلاقات)
├─ Company (الشركة) = Relation → Companies DB
├─ Primary Contact (جهة الاتصال الأساسية) = Relation → Contacts DB
├─ Other Attendees (الحاضرون الآخرون) = Relation → Contacts DB (multi)
└─ Opportunity (الفرصة) = Relation → Opportunities DB

⏰ SCHEDULE (الجدول الزمني)
├─ Scheduled Date (تاريخ الاجتماع) ⭐ Date
├─ Start Time (وقت البداية) = Time
├─ End Time (وقت الانتهاء) = Time
├─ Duration (المدة) = Number (minutes)
└─ Timezone (المنطقة الزمنية) = Select: UTC, EST, PST, GST, ...

📍 DETAILS (التفاصيل)
├─ Location/Meeting Link (الموقع/الرابط) = URL or Text
├─ Meeting Organizer (منظم الاجتماع) = People
├─ Number of Attendees (عدد الحاضرين) = Number
└─ Agenda (جدول الأعمال) = Text/Rich Text

📝 OUTCOMES (النتائج)
├─ Meeting Notes (ملاحظات الاجتماع) = Text/Rich Text
├─ Key Takeaways (النقاط الرئيسية) = Text (bullet points)
├─ Next Steps (الخطوات التالية) = Text
├─ Outcome (النتيجة) = Select: Positive, Neutral, Negative
└─ Decision Made (قرار تم اتخاذه) = Text
```

### Views المطلوبة في Meetings:
```
1. All Meetings
   └─ جميع الاجتماعات

2. Upcoming
   └─ Filter: Scheduled Date ≥ Today
   └─ Sort: Scheduled Date ASC

3. By Company
   └─ Group By: Company
   └─ Track meetings per company

4. By Outcome
   └─ Group By: Outcome
   └─ Shows: Positive, Neutral, Negative
```

---

## 📋 خطوات الـ Setup

### Step 1: Create Companies Database
```
1. في Notion، اضغط: + Add a page
2. اختر: Database
3. سمّيها: Companies
4. Type: Database
5. أضف الحقول من القائمة أعلى
6. Save
```

### Step 2: Create Contacts Database
```
1. نفس العملية مع Contacts
2. أضف حقل Relation:
   ├─ Property Name: Company
   ├─ Relation To: Companies DB
   └─ Type: Many-to-One
3. Save
```

### Step 3: Create Opportunities Database
```
1. نفس العملية مع Opportunities
2. أضف Relation fields:
   ├─ Company → Companies DB
   └─ Contact → Contacts DB
3. Save
```

### Step 4: Create Tasks Database
```
1. نفس العملية مع Tasks
2. أضف Relation fields:
   ├─ Company → Companies DB
   ├─ Contact → Contacts DB
   └─ Opportunity → Opportunities DB
3. Save
```

### Step 5: Create Meetings Database
```
1. نفس العملية مع Meetings
2. أضف Relation fields:
   ├─ Company → Companies DB
   ├─ Contact → Contacts DB
   └─ Opportunity → Opportunities DB
3. Save
```

---

## 🔄 العلاقات بين الـ Databases

```
Companies (3,606)
    │
    ├─→ Contacts (5,898) [One-to-Many]
    │    │
    │    ├─→ Tasks [Follow-up tasks]
    │    ├─→ Meetings [Sales calls]
    │    └─→ Opportunities [Deals]
    │
    ├─→ Opportunities [Company-level deals]
    │    │
    │    ├─→ Contacts [Stakeholders]
    │    └─→ Tasks [Deal management]
    │
    └─→ Tasks [Company-level actions]
        └─→ Meetings [Company meetings]
```

---

## ✅ Verification Checklist

بعد الـ Setup، تحقق:

```
☐ Companies Database: 5 views متاح
☐ Contacts Database: 8 views متاح
☐ Opportunities Database: 5 views متاح
☐ Tasks Database: 6 views متاح
☐ Meetings Database: 4 views متاح

☐ كل الـ Relation fields تعمل
☐ يمكنك الـ Click من Contact → Company
☐ يمكنك الـ Click من Opportunity → Contact
☐ Views تعرض البيانات صحيح
```

---

**Document Version:** 1.0
**Last Updated:** March 24, 2026
**Status:** Ready for Phase 1B Database Creation
