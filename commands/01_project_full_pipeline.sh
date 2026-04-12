#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  AI Sales OS — أوامر تشغيل المشروع الكامل (Full Pipeline)
#  الخط الرئيسي: Apollo → Notion → Score → Action → Track
# ═══════════════════════════════════════════════════════════════

# الانتقال لمجلد السكربتات
cd "$(dirname "$0")/../scripts" || exit 1

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  AI Sales OS — Full Pipeline Commands"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─────────────────────────────────────────────────────
# 1. المزامنة (Sync) — Apollo → Notion
# ─────────────────────────────────────────────────────

# المزامنة اليومية (آخر 24 ساعة) — الوضع الافتراضي
python core/daily_sync.py

# المزامنة اليومية مع هامش تداخل (يستخدمه GitHub Actions)
python core/daily_sync.py --mode incremental --hours 26

# مزامنة آخر 7 أيام
python core/daily_sync.py --mode incremental --days 7

# مزامنة آخر 30 يوم
python core/daily_sync.py --mode incremental --days 30

# استرجاع الفجوات (backfill) — سنة كاملة مع نقطة استئناف
python core/daily_sync.py --mode backfill --days 365

# المزامنة الكاملة (كل السجلات — 2-4 ساعات)
python core/daily_sync.py --mode full

# المزامنة مع بوابة الحوكمة (صارم)
python core/daily_sync.py --mode incremental --days 7 --gate strict

# المزامنة مع بوابة الحوكمة (مراجعة)
python core/daily_sync.py --mode incremental --days 7 --gate review

# المزامنة مع بوابة الحوكمة (تدقيق فقط — لا يمنع)
python core/daily_sync.py --mode incremental --days 7 --gate audit

# ─────────────────────────────────────────────────────
# 2. الإثراء (Enrichment) — إشارات النية والتحليل
# ─────────────────────────────────────────────────────

# إثراء الشركات بإشارات التوظيف (أعلى 50)
python enrichment/job_postings_enricher.py --limit 50

# إثراء بدون كتابة (معاينة)
python enrichment/job_postings_enricher.py --dry-run

# إثراء الشركات HOT فقط
python enrichment/job_postings_enricher.py --tier HOT

# إثراء بدون كاش (تجاهل كاش 7 أيام)
python enrichment/job_postings_enricher.py --no-cache

# إثراء جميع الشركات HOT/WARM بدون حد
python enrichment/job_postings_enricher.py

# تحليل MUHIDE الاستراتيجي (يحتاج ANTHROPIC_API_KEY)
python enrichment/muhide_strategic_analysis.py --limit 50

# تحليل MUHIDE — معاينة
python enrichment/muhide_strategic_analysis.py --dry-run

# تحليل MUHIDE — استئناف من نقطة توقف
python enrichment/muhide_strategic_analysis.py --resume

# تحليل MUHIDE — كل الشركات
python enrichment/muhide_strategic_analysis.py

# مزامنة التفاعل من Apollo Analytics (آخر 7 أيام)
python enrichment/analytics_tracker.py --days 7

# تقرير التفاعل بدون كتابة
python enrichment/analytics_tracker.py --dry-run

# تقرير فقط بدون مزامنة Notion
python enrichment/analytics_tracker.py --skip-sync

# تصدير التقرير لملف
python enrichment/analytics_tracker.py --export

# تحليل الردود بالذكاء الاصطناعي (Reply Intelligence)
python enrichment/reply_intelligence.py --dry-run

# تحليل الردود — تنفيذ
python enrichment/reply_intelligence.py

# تحليل الردود — تحديد العدد
python enrichment/reply_intelligence.py --limit 20

# تحليل الردود — إعادة معالجة الكل
python enrichment/reply_intelligence.py --force

# تحليل الردود — تصدير لملف JSON
python enrichment/reply_intelligence.py --export

# إثراء حقول AI Sales Actions من Apollo
python enrichment/ai_sales_actions_enricher.py --dry-run

# إثراء AI Sales Actions — تنفيذ
python enrichment/ai_sales_actions_enricher.py

# ─────────────────────────────────────────────────────
# 3. التسجيل (Scoring) — حساب النقاط والتصنيف
# ─────────────────────────────────────────────────────

# تسجيل جهات الاتصال غير المسجلة فقط
python scoring/lead_score.py

# إعادة حساب جميع النقاط (force)
python scoring/lead_score.py --force

# معاينة بدون كتابة
python scoring/lead_score.py --dry-run

# تحديث Action Ready (5 شروط)
python scoring/action_ready_updater.py

# Action Ready — معاينة
python scoring/action_ready_updater.py --dry-run

# معايرة الأوزان (مراجعة فقط — آمن)
python scoring/score_calibrator.py

# معايرة آخر 90 يوم
python scoring/score_calibrator.py --days 90

# تطبيق الأوزان الموصى بها (⚠️ يعدل lead_score.py مباشرة)
python scoring/score_calibrator.py --apply

# تصدير تحليل المعايرة
python scoring/score_calibrator.py --export

# ─────────────────────────────────────────────────────
# 4. الأتمتة (Automation) — المهام والتسلسلات
# ─────────────────────────────────────────────────────

# إنشاء مهام للشركات (Action Ready)
python automation/auto_tasks.py

# معاينة المهام بدون إنشاء
python automation/auto_tasks.py --dry-run

# تحديد عدد الشركات
python automation/auto_tasks.py --limit 20

# فحص المهام المتأخرة فقط
python automation/auto_tasks.py --mark-overdue

# تسجيل جهات الاتصال في تسلسلات Apollo
python automation/auto_sequence.py

# تسلسلات — معاينة
python automation/auto_sequence.py --dry-run

# تسلسلات — أعلى 50 فقط (حد الخط اليومي)
python automation/auto_sequence.py --limit 50

# تسلسلات — HOT فقط
python automation/auto_sequence.py --tier HOT

# تسلسلات — مرسل محدد
python automation/auto_sequence.py --sender ragheed

# تتبع النتائج (Task → Contact) — معاينة آمنة
python automation/outcome_tracker.py

# تتبع النتائج — تنفيذ
python automation/outcome_tracker.py --execute

# تتبع النتائج — إعادة معالجة
python automation/outcome_tracker.py --execute --force

# تتبع النتائج — تحديد العدد
python automation/outcome_tracker.py --execute --limit 20

# تتبع النتائج — شامل المغلقة تلقائياً
python automation/outcome_tracker.py --execute --include-auto-closed

# ─────────────────────────────────────────────────────
# 5. الاجتماعات والفرص (Meetings & Opportunities)
# ─────────────────────────────────────────────────────

# مزامنة الاجتماعات (آخر 7 أيام)
python meetings/meeting_tracker.py --days 7

# مزامنة الاجتماعات — معاينة
python meetings/meeting_tracker.py --dry-run

# مزامنة مع Google Calendar
python meetings/meeting_tracker.py --days 7 --calendar

# تحليل الاجتماعات بالذكاء الاصطناعي (أعلى 10)
python meetings/meeting_analyzer.py --limit 10

# تحليل الاجتماعات — معاينة
python meetings/meeting_analyzer.py --dry-run

# إدارة الفرص (اجتماع → فرصة)
python meetings/opportunity_manager.py

# الفرص — معاينة
python meetings/opportunity_manager.py --dry-run

# فحص الصفقات الراكدة فقط
python meetings/opportunity_manager.py --stale-only

# ─────────────────────────────────────────────────────
# 6. المراقبة (Monitoring) — الصحة والتقارير
# ─────────────────────────────────────────────────────

# فحص صحة الخط (بعد كل تشغيل)
python monitoring/health_check.py

# فحص صارم (يخرج بكود 1 عند أي تحذير)
python monitoring/health_check.py --strict

# التقرير الصباحي اليومي
python monitoring/morning_brief.py

# التقرير الصباحي — حفظ لملف
python monitoring/morning_brief.py --output file

# التقرير الصباحي — آخر 3 أيام
python monitoring/morning_brief.py --days 3

# تحديث لوحة المعلومات
python monitoring/dashboard_generator.py

# لوحة المعلومات — مسار مخصص
python monitoring/dashboard_generator.py --output ../dashboards/Sales_Dashboard_Accounts.html

# لوحة المعلومات — معاينة
python monitoring/dashboard_generator.py --dry-run

# فحص تطابق التوثيق
python core/doc_sync_checker.py --strict --fix-hints

# ─────────────────────────────────────────────────────
# 7. Webhooks
# ─────────────────────────────────────────────────────

# تشغيل سيرفر الويب هوك
python webhooks/webhook_server.py

# التحقق من روابط جهات الاتصال والشركات
python webhooks/verify_links.py
