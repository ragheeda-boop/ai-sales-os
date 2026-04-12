# 📥 Lead Inbox — Templates

3 templates for fast lead entry. All templates default to `Status = New` and `Intake Date = Today`.

---

## Template 1 — ➕ Manual

**Use case:** You're adding a lead manually from memory, a note, or a conversation.

**Pre-filled:**
- Source = `Manual`
- Status = `New`
- Intake Owner = `Ragheed`

**Body:** empty

**Typical use:** 10–20 seconds per entry.

---

## Template 2 — 🤝 Referral

**Use case:** Someone in your network introduced you to a lead.

**Pre-filled:**
- Source = `Referral`
- Status = `New`
- Intake Owner = `Ragheed`

**Body:**
```markdown
### من أحاله
(اسم الشخص + علاقته بك)

### لماذا دافئ
(سبب الإحالة — ما الذي جعل المُحيل يظن أنه مناسب؟)
```

**Typical use:** 30 seconds (because you should capture the referral context immediately).

---

## Template 3 — 💳 Business Card

**Use case:** You met someone at an event/conference/meeting and got their business card.

**Pre-filled:**
- Source = `Manual`
- Status = `New`
- Intake Owner = `Ragheed`
- Notes = `من معرض/حدث: `

**Body:** empty

**Typical use:** 20 seconds. Fill the event name right after "من معرض/حدث:" before anything else.

---

## What about Muqawil and Import?

**Muqawil:** Until Day 14, add Muqawil leads using the `➕ Manual` template and change Source to `Muqawil` manually. After Day 14, a dedicated script `scripts/intake/from_muqawil.py` will auto-populate the inbox.

**Import:** Use `scripts/intake/import_list.py` (Day 4 build). Do NOT create records manually with Source=Import.

---

## What we deliberately did NOT create

- ❌ Apollo template — Apollo contacts don't pass through Lead Inbox (reserved source)
- ❌ Bulk import template — use the import script instead
- ❌ Other templates — keep it to 3 to avoid decision fatigue
