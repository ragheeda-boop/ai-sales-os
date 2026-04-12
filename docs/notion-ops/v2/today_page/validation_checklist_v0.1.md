# ⭐ اليوم — Validation Checklist v0.1 Bootstrap

**الصفحة:** https://www.notion.so/33e69eddf30181548db3cbe78bfc7a71
**التاريخ:** 2026-04-10
**النسخة:** v0.1 Bootstrap Mode

---

## 8 اختبارات قصيرة

افتح ⭐ اليوم في Notion ونفّذ الاختبارات بالترتيب. كل اختبار ≤ 60 ثانية.

### T1 — Page opens and title is correct
- [ ] الصفحة تفتح بدون خطأ
- [ ] العنوان يعرض "⭐ اليوم" (بدون تكرار الأيقونة)
- [ ] المحتوى باللغة العربية ويظهر بشكل صحيح

### T2 — 6 sections visible in order
- [ ] قسم 1: 📥 Leads جديدة
- [ ] قسم 2: 🔍 Leads تحت المراجعة
- [ ] قسم 3: ✅ Leads مؤهلة وجاهزة للنقل
- [ ] قسم 4: 🚚 Leads نُقلت إلى CRM
- [ ] قسم 5: 🎯 تركيز اليوم
- [ ] قسم 6: 📝 ملاحظات اليوم

### T3 — 4 Linked Lead Inbox views inserted
في Notion UI، تحت كل قسم من الأقسام 1–4، يجب إدراج linked database view يدويًا (API لا يستطيع إنشاؤه).
- [ ] قسم 1 يحتوي linked view من Lead Inbox مع filter `Status = New`
- [ ] قسم 2 يحتوي linked view مع filter `Status = Review`
- [ ] قسم 3 يحتوي linked view مع filter `Status = Qualified`
- [ ] قسم 4 يحتوي linked view مع filter `Status = Moved`

### T4 — Filters actually work
- أضف lead اختباري في Lead Inbox بـ Status = New
- [ ] يظهر في قسم "📥 Leads جديدة" خلال 5 ثوانٍ
- غيّر Status → Review
- [ ] يختفي من قسم 1 ويظهر في قسم 2

### T5 — State transition through all statuses
- على نفس السجل الاختباري: Review → Qualified → Moved
- [ ] يظهر في قسم 3 عند Qualified
- [ ] يظهر في قسم 4 عند Moved
- [ ] لا يظهر في أي قسم آخر في كل مرحلة

### T6 — Focus list is editable
- [ ] قسم 🎯 تركيز اليوم يحتوي 5 checkboxes على الأقل
- [ ] يمكن الكتابة فيها وتعديلها
- [ ] يمكن وضع علامة ✓ على عنصر

### T7 — Notes toggle works
- [ ] قسم 📝 ملاحظات اليوم هو toggle heading
- [ ] يفتح ويغلق بالضغط
- [ ] يمكن إضافة نص حر بداخله

### T8 — No frozen sections remain
الأقسام التالية **يجب ألا تظهر** في Bootstrap Mode v0.1:
- [ ] ❌ لا يوجد "📞 اتصل اليوم"
- [ ] ❌ لا يوجد "✉️ تابع اليوم"
- [ ] ❌ لا يوجد "💼 الصفقات"
- [ ] ❌ لا يوجد header 🟢/🔴 للنظام
- [ ] ❌ لا يوجد Morning Brief أو Dashboard links

---

## نتيجة الاختبار

- [ ] كل الاختبارات T1–T8 نجحت
- [ ] تم حذف السجل الاختباري من Lead Inbox بعد T5

**إذا نجحت جميعها → Day 3 مُكتمل. Bootstrap Mode v0.1 LIVE.**

**إذا فشل أي اختبار:**
- T1–T2 → أعد تحميل الصفحة، تحقق من محتوى الصفحة في Notion
- T3 → أدرج linked view يدويًا من Notion UI (اكتب `/linked` → اختر Lead Inbox → أضف filter)
- T4–T5 → تحقق من إعدادات filter في كل view
- T6–T7 → حرّر الصفحة وأضف المكونات المفقودة
- T8 → احذف الأقسام القديمة من محتوى الصفحة
