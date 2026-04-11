#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  خط أنابيب المقاولين (Muqawil Pipeline)
#  14,089 مقاول سعودي — Scrape → Clean → Notion → Apollo → Gmail → Rules
#  آخر سحب: 6 أبريل 2026
#  Notion DB: https://notion.so/25384c7f9128462b8737773004e7d1bd
# ═══════════════════════════════════════════════════════════════

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Muqawil Contractors Pipeline — 14,089 Records"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# =============================================================
# المتطلبات (Requirements)
# =============================================================
# cd pipelines/muqawil && pip install -r requirements.txt
# المكتبات: aiohttp, beautifulsoup4, lxml, openpyxl, pandas
# متغيرات البيئة المطلوبة:
#   NOTION_API_KEY
#   NOTION_DATABASE_ID (لقاعدة المقاولين)
#   APOLLO_API_KEY
#   GMAIL credentials (لفحص البريد)

# =============================================================
# ─── 0. السكريبينج (Scraping) — جمع البيانات من موقع مقاول ───
# =============================================================
cd pipelines/muqawil/ || exit 1

# جمع كل الصفحات من موقع مقاول
python muqawil_scraper.py

# اختبار — أول 5 صفحات فقط (للتأكد قبل التشغيل الكامل)
python muqawil_scraper.py --test 5

# اختبار — أول 10 صفحات
python muqawil_scraper.py --test 10

# استئناف من آخر نقطة توقف (يقرأ checkpoint.json)
python muqawil_scraper.py --resume

# البدء من صفحة محددة (مثلاً: الصفحة 100)
python muqawil_scraper.py --start-page 100

# استئناف + بداية محددة
python muqawil_scraper.py --resume --start-page 200

# ── المخرجات ──
# output/data_raw.json          ← البيانات الخام
# output/muqawil_contractors.csv  ← CSV للمراجعة
# output/muqawil_contractors.xlsx ← Excel
# output/checkpoint.json         ← نقطة الاستئناف
# output/errors.log              ← سجل الأخطاء

# =============================================================
# ─── 0.5 فحص جودة البيانات (Audit) ──────────────────────────
# =============================================================

# تشغيل فحص الجودة على البيانات المسحوبة
python output/__audit__.py

# أو فحص سريع بسكربت _peek
python pipeline/_peek.py

# =============================================================
# ─── 1. تشغيل الخط الكامل (Full Pipeline — 6 خطوات) ─────────
# =============================================================
cd pipeline/ || exit 1

# ── تشغيل كل المراحل بالترتيب ──
python run_muqawil_pipeline.py

# ── معاينة بدون كتابة ──
python run_muqawil_pipeline.py --dry-run

# ── تشغيل مرحلة واحدة محددة ──
python run_muqawil_pipeline.py --step 1    # الخطوة 1: تنظيف وإزالة التكرار
python run_muqawil_pipeline.py --step 2    # الخطوة 2: مزامنة Notion
python run_muqawil_pipeline.py --step 3    # الخطوة 3: مطابقة Apollo
python run_muqawil_pipeline.py --step 4    # الخطوة 4: فحص Gmail
python run_muqawil_pipeline.py --step 5    # الخطوة 5: محرك القواعد

# ── البدء من مرحلة معينة (يكمل الباقي) ──
python run_muqawil_pipeline.py --from-step 3    # يبدأ من Apollo ويكمل 4 و 5

# ── Notion sync فقط ──
python run_muqawil_pipeline.py --notion-only

# ── تخطي مراحل محددة ──
python run_muqawil_pipeline.py --skip-apollo     # تخطي مطابقة Apollo
python run_muqawil_pipeline.py --skip-gmail      # تخطي فحص Gmail
python run_muqawil_pipeline.py --skip-apollo --skip-gmail   # تخطي الاثنين

# ── أو استخدم ملف .bat على Windows ──
# RUN_AI_SALES_OS_muqawil_pipeline.bat

# =============================================================
# ─── 2. المراحل الفردية (Individual Steps) ───────────────────
# =============================================================

# ──────────────────────────────────────────────────
# المرحلة 1: التنظيف وإزالة التكرار
# المدخل: output/data_raw.json
# المخرج: cleaned_contractors.json + dedup_report.json
# ──────────────────────────────────────────────────

python 01_clean_deduplicate.py

# ──────────────────────────────────────────────────
# المرحلة 2: مزامنة Notion
# يدفع البيانات النظيفة إلى قاعدة Notion
# يدعم الاستئناف (02_notion_sync_checkpoint.json)
# ──────────────────────────────────────────────────

# معاينة (5 سجلات فقط — لا يكتب)
python 02_notion_sync.py --dry-run

# مزامنة أول 100 سجل (اختبار)
python 02_notion_sync.py --limit 100

# مزامنة أول 500
python 02_notion_sync.py --limit 500

# مزامنة الكل (14,089 سجل)
python 02_notion_sync.py

# إعادة من الصفر (مسح نقطة الاستئناف)
python 02_notion_sync.py --reset

# البدء من سجل محدد (تخطي أول 5000)
python 02_notion_sync.py --start-from 5000

# إعادة + حد
python 02_notion_sync.py --reset --limit 200

# ──────────────────────────────────────────────────
# المرحلة 3: مطابقة Apollo
# يبحث عن كل مقاول في Apollo ويربط الحسابات
# يستخدم: 03_apollo_checkpoint.json للاستئناف
# ──────────────────────────────────────────────────

# معاينة
python 03_apollo_matcher.py --dry-run

# مطابقة أول 50 (اختبار)
python 03_apollo_matcher.py --limit 50

# مطابقة أول 500 (الحد المُوصى من .bat)
python 03_apollo_matcher.py --limit 500

# مطابقة الكل
python 03_apollo_matcher.py

# إعادة فحص المطابَقين سابقاً (force)
python 03_apollo_matcher.py --force

# إعادة + حد
python 03_apollo_matcher.py --force --limit 100

# ──────────────────────────────────────────────────
# المرحلة 4: فحص Gmail
# يتحقق هل تم التواصل مع المقاول سابقاً بالبريد
# ──────────────────────────────────────────────────

# معاينة
python 04_gmail_outreach_check.py --dry-run

# فحص أول 50
python 04_gmail_outreach_check.py --limit 50

# فحص الكل
python 04_gmail_outreach_check.py

# إعادة فحص (حتى المفحوصين سابقاً)
python 04_gmail_outreach_check.py --force

# فحص البريد فقط — أسرع (بدون بحث بالاسم)
python 04_gmail_outreach_check.py --email-only

# إعادة + بريد فقط
python 04_gmail_outreach_check.py --force --email-only

# ──────────────────────────────────────────────────
# المرحلة 5: محرك القواعد
# يطبق قواعد التصنيف والأولوية والجاهزية
# ──────────────────────────────────────────────────

# معاينة
python 05_rules_engine.py --dry-run

# تشغيل أول 50
python 05_rules_engine.py --limit 50

# تشغيل الكل
python 05_rules_engine.py

# تشغيل + تحديث Notion مباشرة (أبطأ — يكتب للـ DB)
python 05_rules_engine.py --update-notion

# معاينة + Notion update
python 05_rules_engine.py --dry-run --update-notion

# =============================================================
# ─── 3. التسلسل المُوصى به (من الصفر) ───────────────────────
# =============================================================

# ── الخطوة 1: سحب البيانات ──
# python muqawil_scraper.py
#   أو
# python muqawil_scraper.py --resume
#
# ── الخطوة 2: فحص الجودة ──
# python output/__audit__.py
#
# ── الخطوة 3: تشغيل الخط الكامل ──
# cd pipeline/
# python run_muqawil_pipeline.py --dry-run     ← معاينة أولاً
# python run_muqawil_pipeline.py               ← تنفيذ
#
# ── أو مرحلة بمرحلة: ──
# python 01_clean_deduplicate.py
# python 02_notion_sync.py --dry-run
# python 02_notion_sync.py
# python 03_apollo_matcher.py --limit 500
# python 04_gmail_outreach_check.py
# python 05_rules_engine.py --update-notion

# =============================================================
# ─── 4. ملفات البيانات والنقاط المرجعية ──────────────────────
# =============================================================

# output/data_raw.json                ← البيانات الخام من الموقع
# output/muqawil_contractors.csv      ← CSV للمراجعة
# output/muqawil_contractors.xlsx     ← Excel
# output/checkpoint.json              ← نقطة استئناف السكريبينج
# output/errors.log                   ← أخطاء السحب
#
# pipeline/cleaned_contractors.json             ← بيانات نظيفة (بعد الخطوة 1)
# pipeline/cleaned_contractors_pre_apollo.json  ← نسخة قبل مطابقة Apollo
# pipeline/dedup_report.json                    ← تقرير إزالة التكرار
# pipeline/02_notion_sync_checkpoint.json       ← نقطة استئناف Notion
# pipeline/03_apollo_checkpoint.json            ← نقطة استئناف Apollo
# pipeline/pipeline_run.log                     ← سجل آخر تشغيل
