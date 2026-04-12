# 📋 AI Sales OS — دليل الأوامر

## الملفات

| # | الملف | المحتوى |
|---|-------|---------|
| 01 | `01_project_full_pipeline.sh` | **المشروع الكامل** — Sync → Enrich → Score → Automate → Meetings → Monitor |
| 02 | `02_governance.sh` | **الحوكمة** — Ingestion Gate + Data Governor + Archive + Audit |
| 03 | `03_scoring.sh` | **التسجيل** — Lead Score + Action Ready + Calibrator |
| 04 | `04_cleanup.sh` | **التنظيف** — مهام قديمة + أرشفة + إصلاح بيانات |
| 05 | `05_muqawil_pipeline.sh` | **المقاولين** — Scrape → Clean → Notion → Apollo → Gmail → Rules |
| 06 | `06_engineering_offices.sh` | **المكاتب الهندسية** — Clean → Notion → Apollo → Activity → Rules |

## طريقة الاستخدام

هذه الملفات **مرجعية** — افتح الملف المناسب وانسخ الأمر الذي تحتاجه.

```bash
# مثال: تشغيل المزامنة اليومية
cd scripts/
python core/daily_sync.py --mode incremental --hours 26
```

## القاعدة الذهبية

> **شغّل `--dry-run` دائماً قبل أي أمر يكتب بيانات**

## الترتيب اليومي الموصى به

```
1. Sync      → python core/daily_sync.py --mode incremental --hours 26
2. Enrich    → python enrichment/job_postings_enricher.py --limit 50
3. Score     → python scoring/lead_score.py
4. Ready     → python scoring/action_ready_updater.py
5. Tasks     → python automation/auto_tasks.py
6. Sequences → python automation/auto_sequence.py --limit 50
7. Meetings  → python meetings/meeting_tracker.py --days 7
8. Outcomes  → python automation/outcome_tracker.py --execute
9. Reply AI  → python enrichment/reply_intelligence.py --dry-run
10. Health   → python monitoring/health_check.py
11. Brief    → python monitoring/morning_brief.py --output file
```
