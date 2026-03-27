# GitHub Setup Guide — AI Sales OS

## الخطوة 1: إصلاح Git repo (شغّل من VS Code Terminal)

```bash
cd "AI Sales OS"

# احذف الـ .git القديم وابدأ من جديد
rm -rf .git
git init -b main

# إعداد Git
git config user.name "Ragheed"
git config user.email "ragheedalmadani@gmail.com"

# ربط بالريبو
git remote add origin https://github.com/ragheeda-boop/ai-sales-os.git
```

## الخطوة 2: أول Commit

```bash
# إضافة الملفات المهمة (بدون .env)
git add .gitignore CLAUDE.md README.md
git add ".github/"
git add "💻 CODE/Phase 3 - Sync/daily_sync.py"
git add "💻 CODE/Phase 3 - Sync/lead_score.py"
git add "💻 CODE/Phase 3 - Sync/constants.py"
git add "💻 CODE/Phase 3 - Sync/notion_helpers.py"
git add "💻 CODE/Phase 3 - Sync/auto_tasks.py"
git add "💻 CODE/Phase 3 - Sync/action_ready_updater.py"
git add "💻 CODE/Phase 3 - Sync/health_check.py"
git add "💻 CODE/Phase 3 - Sync/webhook_server.py"
git add "💻 CODE/Phase 3 - Sync/verify_links.py"
git add "💻 CODE/Phase 3 - Sync/requirements.txt"
git add "💻 CODE/Phase 3 - Sync/.env.example"
git add "🚀 START HERE/"
git add "📚 DOCUMENTATION/"
git add AI_Sales_OS_MindMap.html

# Commit
git commit -m "Initial commit: AI Sales OS v3.2 — Full pipeline ready

- Sync Engine v2.1 (daily_sync.py) with 3 modes
- Lead Score v1.1 (lead_score.py) with calibrated weights
- Action Engine (auto_tasks.py) with SLA-based tasks
- Action Ready evaluator (action_ready_updater.py) — 5 conditions
- Health Check validator (health_check.py)
- GitHub Actions 10-step pipeline (daily_sync.yml)
- Constants unified in constants.py (single source of truth)
- Bug fixes: field name consistency across all scripts
- Skills framework integration for operations
- .gitignore updated for v3.2 builds"
```

## الخطوة 3: رفع على GitHub

```bash
git push -u origin main
```

> إذا الريبو فيه ملفات (README مثلاً)، استخدم:
> `git pull origin main --rebase` ثم `git push -u origin main`

## الخطوة 4: إضافة GitHub Secrets

روح لـ: https://github.com/ragheeda-boop/ai-sales-os/settings/secrets/actions

أضف هالـ Secrets (5 مطلوبة):

| Secret Name | القيمة |
|---|---|
| `APOLLO_API_KEY` | مفتاح Apollo الخاص فيك |
| `NOTION_API_KEY` | توكن Notion Integration |
| `NOTION_DATABASE_ID_CONTACTS` | `9ca842d20aa9460bbdd958d0aa940d9c` |
| `NOTION_DATABASE_ID_COMPANIES` | `331e04a62da74afe9ab6b0efead39200` |
| `NOTION_DATABASE_ID_TASKS` | `5644e28ae9c9422b90e210df500ad607` |

## الخطوة 5: تشغيل السكربتات (Calibration + أول تشغيل)

```bash
cd "💻 CODE/Phase 3 - Sync"

# 1. Calibration — حساب Lead Tier لكل الكونتاكتس
python lead_score.py --force

# 2. تحديث Action Ready
python action_ready_updater.py

# 3. تجربة Action Engine (dry run أول)
python auto_tasks.py --dry-run

# 4. إذا النتايج سليمة، شغّل فعلي
python auto_tasks.py

# 5. Health Check
python health_check.py
```

## الخطوة 6: تفعيل GitHub Actions

روح لـ: https://github.com/ragheeda-boop/ai-sales-os/actions

1. اضغط "I understand my workflows, go ahead and enable them"
2. اختر "🔄 Apollo → Notion Daily Pipeline"
3. اضغط "Run workflow" → اختر `incremental` → Run

الـ Pipeline يشتغل تلقائياً كل يوم الساعة 7:00 صباحاً بتوقيت السعودية.
