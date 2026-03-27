# 📊 NOTION SETUP - MANUAL GUIDE
## خطوة خطوة: إنشاء قواعد البيانات الـ 5

**التاريخ:** 24 مارس 2026
**الحالة:** Ready for Execution
**الوقت المتوقع:** 30-45 دقيقة لكل database

---

## 🚀 STEP 0: التحضير الأولي

### تسجيل الدخول إلى Notion
```
1. اذهب إلى: https://www.notion.so
2. سجّل الدخول بـ account الخاص بك
3. اختر workspace: "AI Sales OS"
```

### إنشاء مجلد للـ Databases
```
1. في Workspace الرئيسية
2. اضغط: + Add a page
3. اختر: Database
4. سمّيها: "DATABASES" (هذا يكون الـ parent folder)
5. قيمة لكل database تحتها
```

---

## 📌 DATABASE #1: COMPANIES

### Step 1.1: إنشاء Database
```
1. داخل "DATABASES" folder
2. اضغط: + Add a page
3. اختر: Database → Table
4. سمّيها: "Companies"
5. Emoji: 🏢
6. Press: Enter
```

### Step 1.2: إضافة الحقول (28 field)

**اضغط على: +** في آخر الأعمدة لإضافة حقل جديد

#### ✏️ الحقول الأساسية (IDENTIFICATION)

| # | Field Name | Type | Options/Settings | Required |
|---|-----------|------|------------------|----------|
| 1 | **Name** | Title | - | ✅ YES |
| 2 | **Domain** | Email | Unique | ✅ YES |
| 3 | **Apollo Account ID** | Text | Unique | ✅ YES |
| 4 | **Record Source** | Select | Apollo, Manual, Import | ❌ NO |

**كيفية إضافة Select Field:**
```
1. اضغط: + (لإضافة field جديد)
2. اختر: Select
3. اضغط: Add option
4. أضف: Apollo
5. اضغط: Add option
6. أضف: Manual
7. اضغط: Add option
8. أضف: Import
9. Done
```

---

#### 📊 معلومات الشركة (COMPANY INFO)

| # | Field Name | Type | Options | Required |
|---|-----------|------|---------|----------|
| 5 | **Industry** | Select | SaaS, Finance, Tech, Healthcare, Retail, Manufacturing, Other | ❌ |
| 6 | **Company Size** | Select | 1-10, 11-50, 51-200, 201-500, 501-1K, 1K+ | ❌ |
| 7 | **Employee Count** | Number | - | ❌ |
| 8 | **Revenue Range** | Select | <$1M, $1-10M, $10-50M, $50M+ | ❌ |
| 9 | **HQ Location** | Text | - | ❌ |
| 10 | **Website** | URL | - | ❌ |
| 11 | **Phone** | Phone Number | - | ❌ |

---

#### 💰 معلومات التمويل (FUNDING INFO)

| # | Field Name | Type | Options | Required |
|---|-----------|------|---------|----------|
| 12 | **Latest Funding Stage** | Select | Seed, Series A, Series B, Series C, Series D, Series E+, IPO, Acquired | ❌ |
| 13 | **Latest Funding Amount** | Number | Currency | ❌ |
| 14 | **Latest Funding Date** | Date | - | ❌ |
| 15 | **Total Funding** | Number | Currency | ❌ |

---

#### 🧠 الذكاء الاصطناعي (INTELLIGENCE)

| # | Field Name | Type | Options | Required |
|---|-----------|------|---------|----------|
| 16 | **Intent Score** | Number | Range: 0-100 | ❌ |
| 17 | **Engagement Score** | Number | Range: 0-100 | ❌ |
| 18 | **Growth Rate** | Number | Percentage (%) | ❌ |
| 19 | **Technology Stack** | Multi-select | Salesforce, HubSpot, AWS, Azure, Google Cloud, Slack, Teams, Other | ❌ |

---

#### 📈 الإشارات (SIGNALS)

| # | Field Name | Type | Options | Required |
|---|-----------|------|---------|----------|
| 20 | **Job Postings** | Number | - | ❌ |
| 21 | **Website Activity** | Number | - | ❌ |
| 22 | **Funding News** | Checkbox | - | ❌ |
| 23 | **Technology Changes** | Text | - | ❌ |
| 24 | **Executive Changes** | Checkbox | - | ❌ |

---

#### ⏰ التتبع (TRACKING)

| # | Field Name | Type | Options | Required |
|---|-----------|------|---------|----------|
| 25 | **Created At** | Date | - | ❌ |
| 26 | **Updated At** | Date | - | ❌ |
| 27 | **Last Synced** | Date | - | ❌ |
| 28 | **Data Status** | Select | Raw, Cleaned, Enriched, Verified | ❌ |

---

### Step 1.3: إنشاء Views

**اضغط على:** View menu (أعلى الـ database)

#### View 1: All Companies
```
1. اضغط: + Add a view
2. اختر: Table
3. اسمها: "All Companies"
4. Settings: None (عرض كل البيانات)
```

#### View 2: High Intent (80+)
```
1. اضغط: + Add a view
2. اختر: Table
3. اسمها: "High Intent"
4. اضغط: Filter
5. Add filter:
   - Property: Intent Score
   - Condition: Greater than or equal to
   - Value: 80
6. اضغط: Sort
7. Add sort:
   - Property: Intent Score
   - Direction: Descending (Z→A)
```

#### View 3: By Industry
```
1. اضغط: + Add a view
2. اختر: Table
3. اسمها: "By Industry"
4. اضغط: Group
5. Group by: Industry
```

#### View 4: Recently Updated
```
1. اضغط: + Add a view
2. اختر: Table
3. اسمها: "Recently Updated"
4. اضغط: Filter
5. Add filter:
   - Property: Updated At
   - Condition: Is within
   - Value: Last 7 days
6. اضغط: Sort
7. Add sort:
   - Property: Updated At
   - Direction: Descending
```

✅ **Companies Database تم!** 🎉

---

## 👤 DATABASE #2: CONTACTS

### Step 2.1: إنشاء Database
```
1. داخل "DATABASES" folder
2. اضغط: + Add a page
3. اختر: Database → Table
4. اسمها: "Contacts"
5. Emoji: 👤
6. Press: Enter
```

### Step 2.2: إضافة الحقول (38 field)

#### ✏️ المعلومات الشخصية (PERSONAL INFO)

| # | Field Name | Type | Required |
|---|-----------|------|----------|
| 1 | **Full Name** | Title | ✅ YES |
| 2 | **First Name** | Text | ❌ |
| 3 | **Last Name** | Text | ❌ |
| 4 | **Apollo Contact ID** | Text | ✅ YES |
| 5 | **Email** | Email | ✅ YES |

---

#### 📞 معلومات التواصل (CONTACT INFO)

| # | Field Name | Type | Required |
|---|-----------|------|----------|
| 6 | **Direct Phone** | Phone Number | ❌ |
| 7 | **Mobile Phone** | Phone Number | ❌ |
| 8 | **Corporate Phone** | Phone Number | ❌ |
| 9 | **LinkedIn URL** | URL | ❌ |

---

#### 💼 معلومات الوظيفة (JOB INFO)

| # | Field Name | Type | Options | Required |
|---|-----------|------|---------|----------|
| 10 | **Title** | Text | - | ❌ |
| 11 | **Seniority** | Select | C-Suite, VP, Director, Manager, IC, Other | ❌ |
| 12 | **Department** | Select | Sales, Marketing, Engineering, Finance, Operations, HR, Other | ❌ |

---

#### 🏢 ربط الشركة (COMPANY LINK)

| # | Field Name | Type | Relation | Required |
|---|-----------|------|----------|----------|
| 13 | **Company** | Relation | → Companies | ✅ YES |
| 14 | **Company Domain** | Text | - | ❌ |
| 15 | **Company Name** | Text | - | ❌ |

**كيفية إضافة Relation Field:**
```
1. اضغط: + لإضافة field جديد
2. اختر: Relation
3. اختر: Companies (database)
4. Type: Many-to-One (عدة contacts → شركة واحدة)
5. Done
```

---

#### 🎯 حالة الـ Outreach (OUTREACH STATUS)

| # | Field Name | Type | Options | Required |
|---|-----------|------|---------|----------|
| 16 | **Outreach Status** | Select | Not Started, In Sequence, Awaiting Reply, Replied, Closed | ❌ |
| 17 | **Qualification Status** | Select | Unqualified, Qualified, Highly Qualified | ❌ |
| 18 | **Sequence Status** | Select | Not in Sequence, Active, Paused, Completed | ❌ |
| 19 | **Do Not Contact** | Checkbox | - | ❌ |

---

#### 📊 التفاعل (ENGAGEMENT)

| # | Field Name | Type | Required |
|---|-----------|------|----------|
| 20 | **Emails Sent** | Number | ❌ |
| 21 | **Emails Opened** | Number | ❌ |
| 22 | **Emails Clicked** | Number | ❌ |
| 23 | **Emails Replied** | Number | ❌ |
| 24 | **Open Rate** | Number | ❌ |
| 25 | **Click Rate** | Number | ❌ |
| 26 | **Reply Rate** | Number | ❌ |

---

#### 💯 درجة القيادة (LEAD SCORE)

| # | Field Name | Type | Required |
|---|-----------|------|----------|
| 27 | **Lead Score** | Number | ❌ |
| 28 | **Last Score Update** | Date | ❌ |
| 29 | **Score Trend** | Select: ↑ Up, → Stable, ↓ Down | ❌ |

---

#### ⏰ التتبع (TRACKING)

| # | Field Name | Type | Required |
|---|-----------|------|----------|
| 30 | **First Contacted** | Date | ❌ |
| 31 | **Last Contacted** | Date | ❌ |
| 32 | **Last Activity** | Date | ❌ |
| 33 | **Next Follow-up** | Date | ❌ |
| 34 | **Created At** | Date | ❌ |

---

### Step 2.3: إنشاء Views (8 Views!)

#### View 1: All Contacts
```
Table view - بدون filters
```

#### View 2: 🔴 HOT LEADS (80+)
```
1. Filter: Lead Score ≥ 80
2. Sort: Lead Score DESC
3. لون مميز: Red (للأهمية)
```

#### View 3: 🟡 WARM LEADS (50-79)
```
1. Filter: Lead Score 50-79
2. Sort: Lead Score DESC
3. لون مميز: Orange
```

#### View 4: 🟢 COLD LEADS (<50)
```
1. Filter: Lead Score < 50
2. Sort: Lead Score DESC
3. لون مميز: Green
```

#### View 5: Recently Updated
```
1. Filter: Last Activity > 7 days
2. Sort: Last Activity DESC
```

#### View 6: By Company
```
1. Group By: Company
```

#### View 7: By Seniority
```
1. Group By: Seniority
```

#### View 8: Awaiting Reply
```
1. Filter: Outreach Status = "Awaiting Reply"
2. Sort: Last Contacted ASC
```

✅ **Contacts Database تم!** 🎉

---

## 🎯 DATABASE #3: OPPORTUNITIES

### Step 3.1: إنشاء Database
```
1. اضغط: + Add a page
2. Database → Table
3. اسمها: "Opportunities"
4. Emoji: 🎯
```

### Step 3.2: الحقول (26 field)

#### الحقول الأساسية:
| # | Field Name | Type | Required |
|---|-----------|------|----------|
| 1 | **Opportunity Name** | Title | ✅ |
| 2 | **Opportunity ID** | Text | ✅ |
| 3 | **Record Source** | Select | Apollo, Odoo, Manual, Import |
| 4 | **Company** | Relation → Companies | ✅ |
| 5 | **Primary Contact** | Relation → Contacts | ❌ |
| 6 | **Secondary Contacts** | Relation → Contacts | ❌ |
| 7 | **Deal Value** | Number | ✅ |
| 8 | **Currency** | Select | USD, EUR, GBP, AED, SAR, Other |
| 9 | **Annual Recurring Revenue** | Number | ❌ |
| 10 | **Contract Term** | Select | 1 Year, 2 Years, 3 Years, Custom |
| 11 | **Stage** | Select | Discovery, Proposal, Negotiation, Closed Won, Closed Lost | ✅ |
| 12 | **Probability** | Select | 10%, 25%, 50%, 75%, 90%, 100% |
| 13 | **Created Date** | Date | ❌ |
| 14 | **Expected Close Date** | Date | ❌ |
| 15 | **Actual Close Date** | Date | ❌ |
| 16 | **Opportunity Owner** | People | ❌ |
| 17 | **Account Owner** | People | ❌ |
| 18 | **Team** | Select | Sales A, Sales B, Enterprise, Other |
| 19 | **Deal Health** | Select | 🟢 Green, 🟡 Yellow, 🔴 Red |
| 20 | **Health Reason** | Text | ❌ |
| 21 | **Next Action** | Text | ❌ |
| 22 | **Blockers** | Multi-select | Budget, Timeline, Stakeholder Approval, Competition, Other |
| 23 | **Competitor** | Text | ❌ |
| 24 | **Risk Level** | Select | Low, Medium, High |
| 25 | **Notes** | Text | ❌ |
| 26 | **Last Updated** | Date | ❌ |

### Step 3.3: Views (5 Views)

```
1. All Opportunities
2. Pipeline (Group By: Stage)
3. By Stage + Value (Group By: Stage, Sort By: Deal Value DESC)
4. Red Flag Deals (Filter: Deal Health = Red)
5. Closing Soon (Filter: Expected Close Date ≤ 30 days)
```

✅ **Opportunities Database تم!** 🎉

---

## ✅ DATABASE #4: TASKS

### Step 4.1: إنشاء Database
```
اسمها: "Tasks"
Emoji: ✅
```

### Step 4.2: الحقول (23 field)

| # | Field Name | Type | Required |
|---|-----------|------|----------|
| 1 | **Task Title** | Title | ✅ |
| 2 | **Task ID** | Text | ✅ |
| 3 | **Task Type** | Select | Follow-up, Demo, Proposal, Review, Other |
| 4 | **Description** | Text | ❌ |
| 5 | **Context** | Text | ❌ |
| 6 | **Expected Outcome** | Text | ❌ |
| 7 | **Company** | Relation → Companies | ❌ |
| 8 | **Contact** | Relation → Contacts | ❌ |
| 9 | **Opportunity** | Relation → Opportunities | ❌ |
| 10 | **Related Tasks** | Relation → Tasks | ❌ |
| 11 | **Assigned To** | People | ✅ |
| 12 | **Created By** | People | ❌ |
| 13 | **Team** | Select | Sales A, Sales B, Operations, Other |
| 14 | **Status** | Select | Not Started, In Progress, Completed | ✅ |
| 15 | **Priority** | Select | Low, Medium, High, Critical | ✅ |
| 16 | **Status Reason** | Text | ❌ |
| 17 | **Due Date** | Date | ✅ |
| 18 | **Start Date** | Date | ❌ |
| 19 | **Completed At** | Date | ❌ |
| 20 | **Overdue** | Checkbox | ❌ |
| 21 | **Days Remaining** | Number | ❌ |
| 22 | **Auto Created** | Checkbox | ❌ |
| 23 | **Trigger Rule** | Text | ❌ |

### Step 4.3: Views (6 Views)

```
1. My Tasks
2. Overdue
3. By Priority (Group By: Priority)
4. By Status (Group By: Status)
5. Due Soon (Filter: Due Date ≤ 7 days)
6. By Type (Group By: Task Type)
```

✅ **Tasks Database تم!** 🎉

---

## 📞 DATABASE #5: MEETINGS

### Step 5.1: إنشاء Database
```
اسمها: "Meetings"
Emoji: 📞
```

### Step 5.2: الحقول (18 field)

| # | Field Name | Type | Required |
|---|-----------|------|----------|
| 1 | **Meeting Title** | Title | ✅ |
| 2 | **Meeting ID** | Text | ✅ |
| 3 | **Meeting Type** | Select | Discovery, Demo, Proposal, Review, Other |
| 4 | **Company** | Relation → Companies | ❌ |
| 5 | **Primary Contact** | Relation → Contacts | ❌ |
| 6 | **Other Attendees** | Relation → Contacts | ❌ |
| 7 | **Opportunity** | Relation → Opportunities | ❌ |
| 8 | **Scheduled Date** | Date | ✅ |
| 9 | **Start Time** | Time | ❌ |
| 10 | **End Time** | Time | ❌ |
| 11 | **Duration (minutes)** | Number | ❌ |
| 12 | **Timezone** | Select | UTC, EST, PST, CST, GST, IST, SGT, Other |
| 13 | **Location/Meeting Link** | URL | ❌ |
| 14 | **Meeting Organizer** | People | ❌ |
| 15 | **Number of Attendees** | Number | ❌ |
| 16 | **Agenda** | Text | ❌ |
| 17 | **Meeting Notes** | Text | ❌ |
| 18 | **Key Takeaways** | Text | ❌ |

### Step 5.3: Views (4 Views)

```
1. All Meetings
2. Upcoming (Filter: Scheduled Date ≥ Today)
3. By Company (Group By: Company)
4. By Outcome (إضافة field: Outcome أولاً)
```

✅ **Meetings Database تم!** 🎉

---

## 🔗 RELATIONSHIPS SETUP

الآن نربط كل الـ databases ببعضها!

### Relationship 1: Companies ↔ Contacts
```
✅ عملنا هذا بالفعل في Contacts
Companies (One) ←→ (Many) Contacts
```

### Relationship 2: Companies ↔ Opportunities
```
في Opportunities:
1. اضغط: + Add field
2. اختر: Relation
3. اختر: Companies
4. Type: Many-to-One
5. Done
```

### Relationship 3: Companies ↔ Tasks
```
في Tasks:
1. نفس الخطوات
2. اختر: Companies
```

### Relationship 4: Companies ↔ Meetings
```
في Meetings:
1. نفس الخطوات
2. اختر: Companies
```

### Relationship 5: Contacts ↔ Opportunities
```
في Opportunities:
Primary Contact و Secondary Contacts
✅ عملنا هذا بالفعل
```

### Relationship 6: Contacts ↔ Tasks
```
في Tasks:
1. اضغط: + Add field
2. اختر: Relation
3. اختر: Contacts
4. Type: Many-to-One
```

### Relationship 7: Contacts ↔ Meetings
```
في Meetings:
1. نفس الخطوات
2. اختر: Contacts
```

### Relationship 8: Opportunities ↔ Tasks
```
في Tasks:
✅ عملنا هذا بالفعل
```

### Relationship 9: Opportunities ↔ Meetings
```
في Meetings:
✅ عملنا هذا بالفعل
```

### Relationship 10: Tasks ↔ Tasks (Self-Relation)
```
في Tasks - Related Tasks:
✅ عملنا هذا بالفعل
```

---

## ✅ VERIFICATION CHECKLIST

بعد إنهاء كل الـ Databases، تحقق:

```
☐ Companies Database:
  ✅ 28 حقل موجود
  ✅ 4 views متاح
  ✅ Relations إلى Contacts, Opportunities, Tasks

☐ Contacts Database:
  ✅ 34+ حقل موجود
  ✅ 8 views متاح
  ✅ Relation إلى Companies

☐ Opportunities Database:
  ✅ 26 حقل موجود
  ✅ 5 views متاح
  ✅ Relations إلى Companies, Contacts, Tasks

☐ Tasks Database:
  ✅ 23 حقل موجود
  ✅ 6 views متاح
  ✅ Relations إلى Companies, Contacts, Opportunities

☐ Meetings Database:
  ✅ 18+ حقل موجود
  ✅ 4 views متاح
  ✅ Relations إلى Companies, Contacts, Opportunities

☐ جميع الـ Relationships تعمل:
  ✅ يمكنك الـ click من Contact إلى Company
  ✅ يمكنك الـ click من Opportunity إلى Contact
  ✅ Views تعرض البيانات صحيح
```

---

## 🎉 الخطوة التالية

بعد إنهاء كل الـ Databases:

1. **Import البيانات:**
   - Companies: 3,606 record
   - Contacts: 5,898 record

2. **Configure Automations:**
   - Lead Score Calculation
   - Auto Task Creation

3. **Set up Webhook:**
   - Real-time Apollo sync

---

**Document Version:** 1.0
**Last Updated:** March 24, 2026
**Status:** Ready for Manual Setup
