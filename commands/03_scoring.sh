#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  AI Sales OS — أوامر التسجيل والتصنيف (Scoring)
#  حساب النقاط + التصنيف + Action Ready + المعايرة
# ═══════════════════════════════════════════════════════════════

cd "$(dirname "$0")/../scripts" || exit 1

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  AI Sales OS — Scoring & Classification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─────────────────────────────────────────────────────
# 1. تسجيل النقاط (Lead Score v1.5)
#    المعادلة: Size(35%) + Seniority(30%) + Industry(15%)
#              + Intent(10%) + Engagement(10%)
#    يكتب: Lead Score (0-100) + Lead Tier + Sort Score
# ─────────────────────────────────────────────────────

# تسجيل جهات الاتصال الجديدة فقط (غير المسجلة)
python scoring/lead_score.py

# إعادة حساب جميع النقاط (كل السجلات)
python scoring/lead_score.py --force

# معاينة — حساب بدون كتابة
python scoring/lead_score.py --dry-run

# ─────────────────────────────────────────────────────
# 2. Action Ready (جاهز للعمل)
#    5 شروط يجب تحققها كلها:
#    ✓ Lead Score ≥ 50
#    ✓ Do Not Call = False
#    ✓ Outreach Status ليس DNC/Bounced/Bad Data
#    ✓ Stage ليس Customer أو Churned
#    ✓ يملك بريد أو هاتف
# ─────────────────────────────────────────────────────

# تحديث Action Ready لكل جهات الاتصال المسجلة
python scoring/action_ready_updater.py

# معاينة التغييرات
python scoring/action_ready_updater.py --dry-run

# ─────────────────────────────────────────────────────
# 3. معايرة الأوزان (Score Calibrator)
#    يحلل نتائج التفاعل الفعلية ويقترح أوزاناً جديدة
#    ⚠️ تنبيه: score_calibrator يعرف 4 مكونات (v1.1)
#       بينما lead_score يستخدم 5 مكونات (v1.5)
#       --apply قد يحذف Industry Fit!
# ─────────────────────────────────────────────────────

# تحليل + توصيات (بدون تغيير — آمن)
python scoring/score_calibrator.py

# تحليل آخر 90 يوم
python scoring/score_calibrator.py --days 90

# تحليل آخر 7 أيام
python scoring/score_calibrator.py --days 7

# تصدير التحليل لملف
python scoring/score_calibrator.py --export

# ⚠️ تطبيق الأوزان الموصى بها (خطير — يعدل lead_score.py)
# ⚠️ تحذير: لا تستخدم هذا حتى يُصلح عدم التطابق v1.1/v1.5
# python scoring/score_calibrator.py --apply

# ─────────────────────────────────────────────────────
# 4. التسلسل المُوصى به (الترتيب الصحيح)
# ─────────────────────────────────────────────────────

# الخطوة 1: حساب النقاط
# python scoring/lead_score.py --force
#
# الخطوة 2: تحديث Action Ready
# python scoring/action_ready_updater.py
#
# الخطوة 3: معايرة (أسبوعي فقط — مراجعة)
# python scoring/score_calibrator.py --days 30 --export
