#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  خط أنابيب المكاتب الهندسية (Engineering Offices Pipeline)
#  مكاتب هندسية — وزارة الإسكان
#  Notion DB: https://notion.so/b85c24be6aa941a395dc33fd1c5f566a
#  Apollo Sequence: "مكاتب هندسية" (ID: 69541c78db24f5001d40dfd7)
#
#  ⚠️  الحالة: غير نشط — جميع الإحصائيات = صفر
#  ⚠️  آخر تشغيل: 6 أبريل 2026 (المراحل 3+4+5، النتيجة: 0 تحديثات)
#  ⚠️  STALE_DAYS = 14 يوم | OPENED_FOLLOWUP_DAYS = 3 أيام
# ═══════════════════════════════════════════════════════════════

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Engineering Offices Pipeline — مكاتب هندسية"
echo "  ⚠️  STATUS: INACTIVE (all stats = 0)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd pipelines/engineering_offices/ || exit 1

# =============================================================
# المتطلبات (Requirements)
# =============================================================
# pip install -r requirements.txt
# المكتبات: requests, python-dotenv
# متغيرات البيئة:
#   NOTION_API_KEY
#   APOLLO_API_KEY
# ملفات الإدخال:
#   مكاتب هندسية - Sheet1.csv
#   مكاتب هندسية 2 - Sheet1.csv
# الثوابت: constants_eng.py (Notion DB ID, Apollo Sequence, Field Names, Region Map)

# =============================================================
# ─── 1. تشغيل الخط الكامل (Full Pipeline — 5 مراحل) ─────────
# =============================================================

# ── تشغيل كل المراحل بالترتيب ──
python run_all.py

# ── معاينة بدون كتابة ──
python run_all.py --dry-run

# ── تشغيل مراحل محددة فقط (أرقام مفصولة بفاصلة) ──
python run_all.py --phases "1,2"       # التنظيف + Notion فقط
python run_all.py --phases "1,2,3"     # التنظيف + Notion + Apollo
python run_all.py --phases "3,4,5"     # Apollo + Activity + Rules فقط
python run_all.py --phases "5"         # محرك القواعد فقط

# ── تخطي مراحل محددة ──
python run_all.py --skip-clean         # تخطي المرحلة 1 (التنظيف)
python run_all.py --skip-sync          # تخطي المرحلة 2 (Notion)
python run_all.py --skip-match         # تخطي المرحلة 3 (Apollo Match)
python run_all.py --skip-activity      # تخطي المرحلة 4 (Activity Sync)
python run_all.py --skip-rules         # تخطي المرحلة 5 (Rules Engine)

# تخطي أكثر من مرحلة
python run_all.py --skip-clean --skip-sync    # مراحل 3+4+5 فقط
python run_all.py --skip-match --skip-activity  # مراحل 1+2+5

# ── الاستمرار عند فشل مرحلة ──
python run_all.py --continue-on-error

# ── معاينة + استمرار ──
python run_all.py --dry-run --continue-on-error

# =============================================================
# ─── 2. المراحل الفردية ──────────────────────────────────────
# =============================================================

# ──────────────────────────────────────────────────
# المرحلة 1: تنظيف البيانات
# يقرأ CSV من وزارة الإسكان → ينظف ويوحد
# المخرج: cleaned_offices.json
# ──────────────────────────────────────────────────

# معاينة — إحصائيات فقط بدون كتابة
python clean_engineering_offices.py --dry-run

# تنظيف + حفظ (المسار الافتراضي: cleaned_offices.json)
python clean_engineering_offices.py

# حفظ بمسار مخصص
python clean_engineering_offices.py --output my_cleaned_offices.json

# ──────────────────────────────────────────────────
# المرحلة 2: مزامنة Notion
# يدفع المكاتب النظيفة إلى قاعدة Notion
# ──────────────────────────────────────────────────

# معاينة — لا يكتب شيئاً
python notion_engineering_sync.py --dry-run

# مزامنة أول 50 (اختبار)
python notion_engineering_sync.py --limit 50

# مزامنة أول 200
python notion_engineering_sync.py --limit 200

# مزامنة الكل
python notion_engineering_sync.py

# إجبار التحديث — حتى السجلات الموجودة
python notion_engineering_sync.py --force-update

# إجبار + حد
python notion_engineering_sync.py --force-update --limit 100

# ملف إدخال مخصص (بدلاً من cleaned_offices.json الافتراضي)
python notion_engineering_sync.py --input my_cleaned_offices.json

# ملف مخصص + معاينة
python notion_engineering_sync.py --input my_cleaned_offices.json --dry-run

# ──────────────────────────────────────────────────
# المرحلة 3: مطابقة Apollo
# يبحث عن كل مكتب في Apollo ويربط الحسابات
# ──────────────────────────────────────────────────

# معاينة
python apollo_engineering_matcher.py --dry-run

# مطابقة أول 50
python apollo_engineering_matcher.py --limit 50

# مطابقة أول 200
python apollo_engineering_matcher.py --limit 200

# مطابقة الكل
python apollo_engineering_matcher.py

# غير المطابَقين فقط (يتخطى من لديهم Apollo ID)
python apollo_engineering_matcher.py --unmatched-only

# غير المطابقين + حد
python apollo_engineering_matcher.py --unmatched-only --limit 100

# ──────────────────────────────────────────────────
# المرحلة 4: مزامنة النشاط من Apollo
# يسحب بيانات التفاعل: Email Sent/Opened/Replied/Bounced
# + Meeting Booked + Sequence Status
# ──────────────────────────────────────────────────

# معاينة
python apollo_activity_sync.py --dry-run

# نشاط آخر 90 يوم (الافتراضي)
python apollo_activity_sync.py

# نشاط آخر 30 يوم
python apollo_activity_sync.py --days 30

# نشاط آخر 7 أيام (للتحقق السريع)
python apollo_activity_sync.py --days 7

# أول 50 سجل فقط
python apollo_activity_sync.py --limit 50

# جهات الاتصال في Sequence فقط
python apollo_activity_sync.py --sequence-only

# Sequence فقط + آخر 30 يوم
python apollo_activity_sync.py --sequence-only --days 30

# Sequence + حد
python apollo_activity_sync.py --sequence-only --limit 100

# ──────────────────────────────────────────────────
# المرحلة 5: محرك قواعد المتابعة
# يطبق قواعد: Follow-up Stage, Stale Flag, Next Action
# STALE_DAYS = 14 | OPENED_FOLLOWUP_DAYS = 3
# ──────────────────────────────────────────────────

# معاينة
python followup_rules_engine.py --dry-run

# تشغيل أول 50
python followup_rules_engine.py --limit 50

# تشغيل الكل
python followup_rules_engine.py

# إعادة حساب أعلام الركود فقط (Stale Flags)
python followup_rules_engine.py --reset-stale

# إعادة الركود + حد
python followup_rules_engine.py --reset-stale --limit 100

# =============================================================
# ─── 3. إعداد Notion Views ──────────────────────────────────
# =============================================================

# عرض الـ Views الموجودة في قاعدة البيانات
python notion_views_setup.py --list

# معاينة Views جديدة ستُنشأ
python notion_views_setup.py --dry-run

# إنشاء Views
python notion_views_setup.py

# =============================================================
# ─── 4. التسلسل المُوصى به (من الصفر) ───────────────────────
# =============================================================

# ── الخطوة 1: تنظيف CSV ──
# python clean_engineering_offices.py
#
# ── الخطوة 2: رفع إلى Notion ──
# python notion_engineering_sync.py --dry-run
# python notion_engineering_sync.py
#
# ── الخطوة 3: مطابقة Apollo ──
# python apollo_engineering_matcher.py --dry-run
# python apollo_engineering_matcher.py
#
# ── الخطوة 4: سحب النشاط ──
# python apollo_activity_sync.py --days 90
#
# ── الخطوة 5: تطبيق القواعد ──
# python followup_rules_engine.py --dry-run
# python followup_rules_engine.py
#
# ── الخطوة 6: إعداد الواجهات ──
# python notion_views_setup.py

# =============================================================
# ─── 5. ملفات البيانات والسجلات ──────────────────────────────
# =============================================================

# constants_eng.py                ← ثوابت: Notion DB ID, Apollo Sequence, حقول, خريطة المناطق
# cleaned_offices.json            ← البيانات النظيفة (مخرج المرحلة 1)
# last_activity_stats.json        ← إحصائيات آخر مزامنة نشاط
# last_pipeline_run.json          ← معلومات آخر تشغيل للخط
# run_all.log                     ← سجل الخط الكامل
# apollo_engineering_matcher.log  ← سجل مطابقة Apollo (246 KB)
# apollo_activity_sync.log        ← سجل مزامنة النشاط
# followup_rules_engine.log       ← سجل محرك القواعد (95 KB)

# =============================================================
# ─── 6. حقول Notion المستخدمة ────────────────────────────────
# =============================================================

# ── بيانات أساسية ──
# Company Name, Normalized Name, Region, City, CR Number
# Main Email, Mobile, WhatsApp, Source Sheet
# Data Completeness Score, Company Status, Account Tier
# Priority, Owner, Notes, Manual Note
#
# ── حقول Apollo ──
# Apollo Matched, Match Confidence, Apollo Account ID
# Apollo Contact ID, In Apollo List, In Sequence
# Sequence Status, Sequence Step
#
# ── حقول التفاعل ──
# Email Sent/Opened/Replied/Bounced
# Last Email Sent At, Last Opened At, Last Replied At
# Last Activity Date, Last Activity Type, Activity Count
# Positive Signal, Meeting Booked/Completed/Date
#
# ── حقول المتابعة ──
# Next Action, Next Action Due, Follow-up Stage
# Stale Flag, Days Since Contact
#
# ── حقول الجودة ──
# Missing Email, Missing Mobile, Duplicate Suspected
# Needs Manual Review, Ready for Outreach
