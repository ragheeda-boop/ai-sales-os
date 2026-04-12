# AI Sales OS — Command Map

**كل سكربت، تصنيفه، ومتى يعمل. مرجع واحد فقط.**

الإصدار: v2.0 — Operator-First
آخر تحديث: 2026-04-10

---

## دليل التصنيفات

| التصنيف | المعنى |
|---|---|
| **ACTIVE** | يعمل تلقائيًا كل يوم عبر GitHub Actions. لا تلمسه. |
| **BACKGROUND** | موجود ويعمل، لكن لا يُستدعى من المستخدم مباشرة. |
| **MANUAL ONLY** | يُشغَّل يدويًا عند الحاجة. ليس في pipeline التلقائي. |
| **FROZEN** | موجود في الكود لكن متوقف رسميًا. لا تُشغّله. |
| **ONE-TIME** | مهمة هجرة انتهت. لا تُعد تشغيله. |
| **DEPRECATED** | نسخة قديمة، تُؤرشف. |

---

## الجدول الكامل

### Core (المحرك)

| السكربت | التصنيف | متى يعمل | ماذا يفعل | الأمر |
|---|---|---|---|---|
| `core/daily_sync.py` | **ACTIVE** | يوميًا 7:00 AM KSA | Apollo → Notion sync | تلقائي في Job 1 |
| `core/notion_helpers.py` | **BACKGROUND** | يُستدعى من سكربتات أخرى | Notion API utilities | — |
| `core/constants.py` | **BACKGROUND** | يُستورد من كل السكربتات | Field names + thresholds | — |
| `core/doc_sync_checker.py` | **MANUAL ONLY** | عند إنهاء جلسة تطوير | يكشف drift بين docs والكود | `python scripts/core/doc_sync_checker.py --strict` |

### Scoring

| السكربت | التصنيف | متى يعمل | ماذا يفعل | الأمر |
|---|---|---|---|---|
| `scoring/lead_score.py` | **ACTIVE** | يوميًا بعد sync | يُسجّل كل جهات الاتصال | تلقائي في Job 1 |
| `scoring/action_ready_updater.py` | **ACTIVE** | يوميًا بعد scoring | يضبط Action Ready checkbox | تلقائي في Job 1 |
| `scoring/score_calibrator.py` | **ACTIVE** (weekly) | الأحد 8:00 AM | يحلل أوزان scoring، review-only | تلقائي |

### Automation

| السكربت | التصنيف | متى يعمل | ماذا يفعل | الأمر |
|---|---|---|---|---|
| `automation/auto_tasks.py` | **ACTIVE** | يوميًا Job 2 | ينشئ مهام company-level | تلقائي |
| `automation/auto_sequence.py` | **ACTIVE** | يوميًا Job 2 | يُدخل contacts في Apollo sequences | تلقائي |
| `automation/outcome_tracker.py` | **ACTIVE** | يوميًا Job 2 | يغلق loop Task → Contact | تلقائي (`--execute`) |
| `automation/cleanup_overdue_tasks.py` | **ONE-TIME** | انتهى | تنظيف legacy tasks قبل v5.0 | لا تُشغّل |
| `automation/outcome_tracker_backup.py` | **DEPRECATED** | — | نسخة قديمة | archive/ |

### Governance

| السكربت | التصنيف | متى يعمل | ماذا يفعل | الأمر |
|---|---|---|---|---|
| `governance/ingestion_gate.py` | **BACKGROUND** | مدمج في daily_sync | يفلتر بيانات Apollo الواردة | — |
| `governance/data_governor.py` | **MANUAL ONLY** | شهريًا | يدقق ويؤرشف غير المؤهل | `python scripts/governance/data_governor.py --dry-run` |
| `governance/audit_ownership.py` | **MANUAL ONLY** | شهريًا | يدقق فجوات الملكية | `python scripts/governance/audit_ownership.py` |
| `governance/archive_unqualified.py` | **MANUAL ONLY** | عند الحاجة | يؤرشف contacts بلا owner/email | `python scripts/governance/archive_unqualified.py --dry-run` |
| `governance/fix_seniority.py` | **ONE-TIME** | انتهى | Migration "C suite" → "C-Suite" | لا تُشغّل |

### Enrichment

| السكربت | التصنيف | متى يعمل | ماذا يفعل | الأمر |
|---|---|---|---|---|
| `enrichment/job_postings_enricher.py` | **ACTIVE** | يوميًا Job 1 (`--limit 50`) | Intent proxy من Apollo jobs | تلقائي |
| `enrichment/analytics_tracker.py` | **ACTIVE** | يوميًا Job 2 (`--days 7`) | sync engagement من Apollo | تلقائي |
| `enrichment/muhide_strategic_analysis.py` | **FROZEN** (batch) / **MANUAL ONLY** (--limit) | لا batch run | AI scoring شركات ضد ICP | فقط يدويًا مع `--limit ≤ 20` |

### Meetings

| السكربت | التصنيف | متى يعمل | ماذا يفعل | الأمر |
|---|---|---|---|---|
| `meetings/meeting_tracker.py` | **ACTIVE** | يوميًا Job 2 (`--days 7`) | sync الاجتماعات | تلقائي |
| `meetings/meeting_analyzer.py` | **ACTIVE** | يوميًا Job 2 (`--limit 10`) | AI analysis لملاحظات الاجتماع | تلقائي (يتطلب ANTHROPIC_API_KEY) |
| `meetings/opportunity_manager.py` | **ACTIVE** | يوميًا Job 2 | Meetings → Opportunities | تلقائي |

### Monitoring

| السكربت | التصنيف | متى يعمل | ماذا يفعل | الأمر |
|---|---|---|---|---|
| `monitoring/health_check.py` | **ACTIVE** | يوميًا Job 2 | فحص صحة pipeline | تلقائي |
| `monitoring/morning_brief.py` | **FROZEN** (daily) / **MANUAL ONLY** (weekly) | لا daily run | تقرير markdown | `python scripts/monitoring/morning_brief.py --days 7 --output file` |
| `monitoring/dashboard_generator.py` | **FROZEN** (daily) / **MANUAL ONLY** (monthly) | لا daily run | يولّد HTML dashboard | يدويًا شهريًا فقط عند الحاجة |

### Webhooks

| السكربت | التصنيف | متى يعمل | ماذا يفعل | الأمر |
|---|---|---|---|---|
| `webhooks/webhook_server.py` | **BACKGROUND** | on demand | Apollo webhook receiver | server mode |
| `webhooks/verify_links.py` | **MANUAL ONLY** | عند الشك | فحص روابط Contact-Company | `python scripts/webhooks/verify_links.py` |

### Pipelines الإضافية

| Pipeline | التصنيف | السبب |
|---|---|---|
| `pipelines/muqawil/` | **MANUAL ONLY** | 14K مقاول، تشغيل شهري |
| `pipelines/engineering_offices/` | **FROZEN** | inactive، all zeros |
| `pipelines/file_sync/` | **MANUAL ONLY** | sync مع Drive/GitHub عند الحاجة |

### Intake (يُبنى في أسبوع 2)

| السكربت | التصنيف | متى يعمل | ماذا يفعل | الأمر |
|---|---|---|---|---|
| `intake/import_list.py` | **MANUAL ONLY** (جديد) | عند استيراد CSV | يكتب في Lead Inbox | `python scripts/intake/import_list.py <file>` |

---

## ما يعمل تلقائيًا يوميًا — الخلاصة

Pipeline واحد، 2 jobs، 13 خطوة:

**Job 1 (Sync/Score):**
1. `daily_sync.py --mode incremental --hours 26`
2. `job_postings_enricher.py --limit 50`
3. `lead_score.py`
4. `action_ready_updater.py`

**Job 2 (Action/Track):**
5. `auto_tasks.py`
6. `auto_sequence.py --limit 50`
7. `meeting_tracker.py --days 7`
8. `meeting_analyzer.py --limit 10`
9. `opportunity_manager.py`
10. `analytics_tracker.py --days 7`
11. `outcome_tracker.py --execute`
12. `health_check.py`
13. `dashboard_generator.py` (**سيُجمَّد** في v2.0)

**Weekly:**
- `score_calibrator.py --days 30 --export` (Sundays, review only)

---

## ما يعمل يدويًا — الخلاصة

فقط 4 أوامر تحتاج حفظها:

```bash
# استيراد قائمة
python scripts/intake/import_list.py <file.csv> --source Import

# فحص جودة شهري
python scripts/governance/data_governor.py --dry-run

# Backfill عند فقدان بيانات
python scripts/core/daily_sync.py --mode backfill --days 3

# تقرير أسبوعي
python scripts/monitoring/morning_brief.py --days 7 --output weekly.md
```

كل شيء آخر: يدوي على أساس "عند الحاجة"، يُراجَع في هذا الملف أولًا.

---

## ما لا يعمل بعد اليوم (Frozen List)

**لا تُشغّل هذه:**

1. `muhide_strategic_analysis.py` بدون `--limit` — يستهلك Claude credits ويلوث البيانات
2. `pipelines/engineering_offices/` — pipeline خامد
3. `dashboard_generator.py` في GitHub Actions اليومي — سيُعلَّق في `.github/workflows/daily_sync.yml`
4. `morning_brief.py` في GitHub Actions اليومي — سيُعلَّق
5. `cleanup_overdue_tasks.py` — one-time انتهى
6. `fix_seniority.py` — one-time انتهى
7. `outcome_tracker_backup.py` — deprecated

**سبب التجميد موثق في CLAUDE.md بعد تحديث v2.0.**
