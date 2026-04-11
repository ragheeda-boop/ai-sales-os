#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  AI Sales OS — أوامر الحوكمة وجودة البيانات (Governance)
#  التحكم في جودة البيانات الداخلة والموجودة
# ═══════════════════════════════════════════════════════════════

cd "$(dirname "$0")/../scripts" || exit 1

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  AI Sales OS — Governance & Data Quality"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─────────────────────────────────────────────────────
# 1. بوابة الاستيعاب (Ingestion Gate) — منع الدخول
#    يمنع البيانات الرديئة قبل دخول النظام
#    الشركات: 2 من 5 معايير | جهات الاتصال: 4 من 4
# ─────────────────────────────────────────────────────

# وضع التدقيق — تقييم بدون كتابة (آمن)
python governance/ingestion_gate.py --dry-run

# وضع التدقيق (audit) — تسجيل فقط
python governance/ingestion_gate.py --mode audit

# وضع المراجعة (review) — يمرر الحالات المشكوك فيها للمراجعة
python governance/ingestion_gate.py --mode review

# وضع صارم (strict) — يمنع فعلياً
python governance/ingestion_gate.py --mode strict

# تطبيق صارم (اختصار)
python governance/ingestion_gate.py --enforce

# تقييم أول 50 شركة فقط
python governance/ingestion_gate.py --dry-run --limit 50

# حفظ تقرير مفصل
python governance/ingestion_gate.py --report

# تطبيق صارم + تقرير
python governance/ingestion_gate.py --enforce --report

# ─────────────────────────────────────────────────────
# 2. حاكم البيانات (Data Governor) — تنظيف الموجود
#    يدقق السجلات الموجودة ويؤرشف غير المؤهلة
# ─────────────────────────────────────────────────────

# تدقيق فقط — بدون تغييرات (الافتراضي)
python governance/data_governor.py --dry-run

# تطبيق الأرشفة والتنظيف
python governance/data_governor.py --enforce

# تقرير جودة مفصل
python governance/data_governor.py --report

# تنفيذ محدود (أول 100 سجل)
python governance/data_governor.py --enforce --limit 100

# تقرير + تنفيذ
python governance/data_governor.py --enforce --report

# ─────────────────────────────────────────────────────
# 3. أرشفة غير المؤهلين (Archive Unqualified)
#    يؤرشف جهات الاتصال بدون مالك أو بريد مرسل
# ─────────────────────────────────────────────────────

# معاينة — ماذا سيُؤرشف؟ (⚠️ شغّل هذا أولاً دائماً)
python governance/archive_unqualified.py --dry-run

# تنفيذ الأرشفة
python governance/archive_unqualified.py

# أرشفة أول 50 فقط (اختبار)
python governance/archive_unqualified.py --limit 50

# ─────────────────────────────────────────────────────
# 4. تدقيق الملكية (Audit Ownership)
#    يفحص فجوات الملكية في كل قواعد البيانات الـ 5
# ─────────────────────────────────────────────────────

# تدقيق كامل
python governance/audit_ownership.py

# تدقيق + إصلاح تلقائي
python governance/audit_ownership.py --fix

# ─────────────────────────────────────────────────────
# 5. إصلاح المسمى الوظيفي (Fix Seniority)
#    ⚠️ مرة واحدة فقط — تحويل "C suite" → "C-Suite"
# ─────────────────────────────────────────────────────

# معاينة (الافتراضي — آمن)
python governance/fix_seniority.py

# تنفيذ الترحيل
python governance/fix_seniority.py --execute

# تنفيذ مع حجم دفعة مخصص
python governance/fix_seniority.py --execute --batch-size 25
