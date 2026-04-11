#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  AI Sales OS — أوامر التنظيف والصيانة (Cleanup)
#  تنظيف المهام القديمة + أرشفة + إصلاح البيانات
# ═══════════════════════════════════════════════════════════════

cd "$(dirname "$0")/../scripts" || exit 1

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  AI Sales OS — Cleanup & Maintenance"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─────────────────────────────────────────────────────
# 1. تنظيف المهام المتأخرة (Cleanup Overdue Tasks)
#    يكمل المهام القديمة من نموذج v4 (قبل Company-Centric)
#    التي لم تُنفذ وحلّ محلها نموذج v5.0
# ─────────────────────────────────────────────────────

# معاينة — ماذا سيُنظف؟ (⚠️ شغّل أولاً دائماً)
python automation/cleanup_overdue_tasks.py --dry-run

# تنفيذ التنظيف
python automation/cleanup_overdue_tasks.py

# تنظيف أول 100 مهمة فقط
python automation/cleanup_overdue_tasks.py --limit 100

# ─────────────────────────────────────────────────────
# 2. أرشفة جهات الاتصال غير المؤهلة
#    بدون مالك أو بدون بريد مرسل → Stage = Archived
# ─────────────────────────────────────────────────────

# معاينة (⚠️ شغّل أولاً)
python governance/archive_unqualified.py --dry-run

# تنفيذ
python governance/archive_unqualified.py

# أرشفة محدودة
python governance/archive_unqualified.py --limit 50

# ─────────────────────────────────────────────────────
# 3. حاكم البيانات — تنظيف شامل
#    يدقق كل السجلات + يؤرشف غير المؤهلة
#    + يربط جهات الاتصال بالشركات + يعيّن المالكين
# ─────────────────────────────────────────────────────

# تدقيق فقط (آمن)
python governance/data_governor.py --dry-run

# تنفيذ كامل
python governance/data_governor.py --enforce

# تقرير جودة
python governance/data_governor.py --report

# تنفيذ محدود
python governance/data_governor.py --enforce --limit 100

# ─────────────────────────────────────────────────────
# 4. إصلاح المسمى الوظيفي
#    مرة واحدة: "C suite" → "C-Suite"
# ─────────────────────────────────────────────────────

# معاينة
python governance/fix_seniority.py

# تنفيذ
python governance/fix_seniority.py --execute

# ─────────────────────────────────────────────────────
# 5. تدقيق الملكية
#    يفحص كل قواعد البيانات الـ 5 عن سجلات بدون مالك
# ─────────────────────────────────────────────────────

# تدقيق
python governance/audit_ownership.py

# تدقيق + إصلاح
python governance/audit_ownership.py --fix

# ─────────────────────────────────────────────────────
# 6. فحص صحة الخط بعد التنظيف
# ─────────────────────────────────────────────────────

# فحص عادي
python monitoring/health_check.py

# فحص صارم
python monitoring/health_check.py --strict

# ─────────────────────────────────────────────────────
# 7. التسلسل المُوصى به للتنظيف الشامل
# ─────────────────────────────────────────────────────

# الخطوة 1: فحص الحالة
# python governance/audit_ownership.py
#
# الخطوة 2: تنظيف المهام القديمة
# python automation/cleanup_overdue_tasks.py --dry-run
# python automation/cleanup_overdue_tasks.py
#
# الخطوة 3: أرشفة غير المؤهلين
# python governance/archive_unqualified.py --dry-run
# python governance/archive_unqualified.py
#
# الخطوة 4: حوكمة شاملة
# python governance/data_governor.py --dry-run
# python governance/data_governor.py --enforce --report
#
# الخطوة 5: تأكيد
# python monitoring/health_check.py --strict
