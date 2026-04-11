# AI Sales OS v2.0 — Safe Folder Reorganization Plan

**Version:** 1.1 (Corrected) | **Date:** 2026-04-10 | **Status:** Approved — 2-Wave Execution

## Corrections applied in v1.1
1. **Muqawil is NOT frozen** — reclassified as MANUAL ONLY / BACKGROUND INTAKE SOURCE. Remains at `pipelines/muqawil/`. Only `engineering_offices` is frozen.
2. **Operator files stay visible** — MANUAL/RUNBOOK/COMMAND_MAP/V2_BLUEPRINT/FOLDER_REORG remain in Root (not moved to `operator/`). An `operator/` folder is created only for auxiliary operator docs.
3. **Two-wave reorganization** — Wave 1 (safe, no path-breaking moves) + Wave 2 (deferred, gated). No pipeline or script file is moved in Wave 1.

> ⚠️ **مبدأ أساسي:** لا يُنقل ملف واحد إلى أن تكتمل خطة الهجرة الآمنة. كل نقل يتم بـ `git mv`، وكل مرجع imports يُفحص قبل النقل.

---

## 1. Project Folder Problems Today

المشاكل المرصودة في الجذر الحالي:

1. **Root مزدحم** — 10+ ملفات متنوعة في الجذر (docx, xlsx, log, json, md). لا يوجد فصل بين operator-facing و engineering.
2. **ملفات logs و checkpoint في الجذر** — `fix_seniority.log`, `ingestion_gate.log`, `muhide_analysis.log`, `muhide_analysis_checkpoint.json`, `muhide_analysis_stats.json` يجب أن تكون في `data/logs/` أو مُضافة إلى `.gitignore`.
3. **ملفات مؤقتة مكشوفة** — `~$_Sales_OS_دليل_التنفيذ_البرمجي.docx` (lock file من Word) في الجذر.
4. **تكرار documentation** — `AI_Sales_OS_Code_Execution_Guide.md` + `AI_Sales_OS_دليل_التنفيذ_البرمجي.docx` + `start_here/` + `docs/start_here/` — نفس المحتوى تقريبًا في 4 أماكن.
5. **dashboards/** يحتوي على 9 ملفات HTML، 8 منها مجمّدة الآن ولم تعد تُولّد يوميًا.
6. **لا يوجد مجلد `notion/`** — لا يوجد مكان واضح لتوثيق v2 Operator Layer (Today page, Lead Inbox schemas).
7. **`pipelines/` مخلوط** — يحتوي على `muqawil/` و `engineering_offices/` (كلاهما خارج المسار الرئيسي) إضافة إلى `file_sync/` (فعّال ومستقل).
8. **`muqawil_output/` و `muqawil_pipeline/` في الجذر** — تكرار لـ `pipelines/muqawil/` ويبدو أنهما بقايا قديمة.
9. **`commands/` vs `scripts/`** — shell scripts موزّعة بين `commands/` و `scripts/`. غير واضح أيهما الرسمي.
10. **لا يوجد `operator/`** — MANUAL/RUNBOOK/COMMAND_MAP/V2_BLUEPRINT منتشرة في الجذر بدون grouping.

---

## 2. Recommended Folder Structure v2.0

```
AI Sales OS/
│
├── README.md                       ← نقطة بداية واحدة
├── CLAUDE.md                       ← تعليمات الوكيل (يبقى)
│
├── operator/                       ← 🆕 طبقة التشغيل اليومية (Operator-First)
│   ├── MANUAL.md                   ← نُقل من root
│   ├── RUNBOOK.md                  ← نُقل من root
│   ├── COMMAND_MAP.md              ← نُقل من root
│   ├── V2_BLUEPRINT.md             ← نُقل من v2_operator/
│   ├── FOLDER_REORG.md             ← هذا الملف
│   └── today_checklist.md          ← اختياري — نسخة مطبوعة من Today page
│
├── notion/                         ← 🆕 كل ما يخص بنية Notion
│   ├── v2/
│   │   ├── today_page/
│   │   │   └── schema.md           ← تعريف الأقسام و linked views
│   │   ├── lead_inbox/
│   │   │   ├── schema.md           ← 12 حقل + حالات
│   │   │   ├── views.md            ← 4 views
│   │   │   └── templates.md        ← 3 templates
│   │   └── sidebar.md              ← بنية الـ sidebar النهائية
│   └── legacy/
│       └── v1_schemas.md           ← توثيق schemas القديمة (reference)
│
├── scripts/                        ← 🟢 يبقى كما هو (لا تلمسه)
│   ├── core/
│   ├── scoring/
│   ├── automation/
│   ├── governance/
│   ├── enrichment/
│   ├── meetings/
│   ├── monitoring/
│   ├── webhooks/
│   └── intake/                     ← 🆕 سيُضاف لاحقًا (import_list.py)
│
├── pipelines/
│   └── file_sync/                  ← 🟢 يبقى (فعّال)
│       └── ... (كما هو)
│
├── docs/
│   ├── architecture/               ← يبقى
│   ├── reports/                    ← يبقى
│   ├── setup/                      ← يبقى
│   ├── operator/                   ← 🆕 نسخ generated للـ MANUAL/RUNBOOK
│   └── legacy/                     ← 🆕 docs قديمة
│
├── dashboards/
│   ├── active/                     ← 🆕
│   │   └── Sales_Dashboard_Accounts.html   ← الوحيد الفعّال
│   └── archived/                   ← 🆕 (8 ملفات HTML أخرى)
│       ├── AI_Sales_OS_Live_Dashboard.html
│       ├── AI_Sales_OS_MindMap.html
│       ├── AI_Sales_OS_Test_Report.html
│       ├── Companies_DB_Revenue_Engine_Analysis.html
│       ├── Company_Centric_Enforcement_Plan.html
│       ├── Full_System_Revenue_Engine_Analysis.html
│       ├── Sales_Dashboard_Accounts_view.html
│       └── تقرير_الاكتتابات_السعودية_2026.html
│
├── data/
│   ├── imports/                    ← يبقى
│   ├── logs/                       ← كل .log files تُجمع هنا
│   ├── mapping/                    ← يبقى
│   ├── snapshots/                  ← يبقى
│   └── checkpoints/                ← 🆕 للـ *_checkpoint.json
│
├── archive/
│   ├── frozen_scripts/             ← 🆕 (muhide batch, engineering_offices)
│   ├── old_dashboards/             ← اختياري (أو نترك كل شيء في dashboards/archived/)
│   ├── legacy_docs/                ← 🆕 (docs مكررة/قديمة)
│   ├── legacy_outputs/             ← 🆕 (muqawil_output القديم، xlsx قديم)
│   └── presentations_old/          ← نُقل من presentations/
│
├── presentations/                  ← يبقى (النسخ الحديثة فقط)
│   ├── english/
│   ├── arabic/
│   └── ceo_pitch/
│
├── assets/                         ← يبقى
│
├── commands/                       ← يبقى (أو يُدمج في scripts/cli/)
│
└── .github/
    └── workflows/                  ← يبقى (لا يُلمس)
```

---

## 3. What Stays in Root (يبقى في الجذر)

ملفات Root بعد التنظيف — 2 فقط:

| ملف | سبب البقاء |
|---|---|
| `README.md` | نقطة دخول GitHub |
| `CLAUDE.md` | تعليمات الوكيل — يجب أن تكون في الجذر ليجدها Claude |

**كل ما عدا ذلك يُنقل.**

---

## 4. What Moves to `operator/`

| من | إلى |
|---|---|
| `MANUAL.md` | `operator/MANUAL.md` |
| `RUNBOOK.md` | `operator/RUNBOOK.md` |
| `COMMAND_MAP.md` | `operator/COMMAND_MAP.md` |
| `v2_operator/V2_BLUEPRINT.md` | `operator/V2_BLUEPRINT.md` |
| `FOLDER_REORG.md` | `operator/FOLDER_REORG.md` |

ثم يُحذف مجلد `v2_operator/` فارغًا.

---

## 5. What Moves to Background (يبقى فعّال لكن يُخفى)

| من | إلى | السبب |
|---|---|---|
| `AI_Sales_OS_Live_Dashboard.html` | `dashboards/archived/` | مجمّد (مش في daily pipeline) |
| `AI_Sales_OS_MindMap.html` | `dashboards/archived/` | reference فقط |
| `AI_Sales_OS_Test_Report.html` | `dashboards/archived/` | قديم |
| `Companies_DB_Revenue_Engine_Analysis.html` | `dashboards/archived/` | تحليل لمرة واحدة |
| `Company_Centric_Enforcement_Plan.html` | `dashboards/archived/` | خطة v5.0 — منفذة |
| `Full_System_Revenue_Engine_Analysis.html` | `dashboards/archived/` | تحليل لمرة واحدة |
| `Sales_Dashboard_Accounts_view.html` | `dashboards/archived/` | نسخة مكررة |
| `تقرير_الاكتتابات_السعودية_2026.html` | `dashboards/archived/` | تقرير قديم |
| `Sales_Dashboard_Accounts.html` | `dashboards/active/` | **الوحيد الفعّال** (لكنه مجمّد أيضًا حاليًا — يبقى في active للاستعادة السريعة) |

---

## 6. What Moves to Archive (للرجوع فقط)

| من | إلى | السبب |
|---|---|---|
| `AI_Sales_OS_Code_Execution_Guide.md` | `archive/legacy_docs/` | مكرر مع docs/ |
| `AI_Sales_OS_Restructuring_Report_v6.0.docx` | `archive/legacy_docs/` | تقرير v6.0 — منفّذ |
| `AI_Sales_OS_دليل_التنفيذ_البرمجي.docx` | `archive/legacy_docs/` | مكرر |
| `~$_Sales_OS_دليل_التنفيذ_البرمجي.docx` | **يُحذف** | Word lock file |
| `MUHIDE_Contractor_Sequences.docx` | `archive/legacy_docs/` | قديم |
| `Apollo_Contacts_MUHIDE_Score.xlsx` | `archive/legacy_outputs/` | output لمرة واحدة |
| `IPO_Saudi_2026_MUHIDE_Score.xlsx` | `archive/legacy_outputs/` | output لمرة واحدة |
| `muqawil_output/` | `archive/legacy_outputs/muqawil_output/` | output قديم |
| `muqawil_pipeline/` | `archive/frozen_scripts/muqawil_pipeline/` | مكرر مع `pipelines/muqawil/` |
| `pipelines/muqawil/` | `archive/frozen_scripts/muqawil/` | خارج الـ main workflow |
| `pipelines/engineering_offices/` | `archive/frozen_scripts/engineering_offices/` | inactive (all zeros) |
| `start_here/` | `archive/legacy_docs/start_here/` | مكرر مع `docs/start_here/` |

---

## 7. What Gets Renamed

| من | إلى | السبب |
|---|---|---|
| `v2_operator/` | (يُحذف بعد نقل المحتوى إلى `operator/`) | تسمية أوضح |
| `commands/` | `scripts/cli/` (اختياري) | توحيد — **لكن هذا يكسر references في docs، نؤجّله لـ Phase 2** |

**لا تغييرات تسمية أخرى.** لا نعيد تسمية أي script داخل `scripts/` (يكسر imports).

---

## 8. What Gets Frozen (يُنقل إلى `archive/frozen_scripts/`)

| مكون | حالة | السبب |
|---|---|---|
| `pipelines/muqawil/` | FROZEN | خارج main workflow + last_activity_stats.json كلها أصفار |
| `pipelines/engineering_offices/` | FROZEN | inactive |
| `muqawil_pipeline/` (root) | FROZEN | مكرر |
| `scripts/enrichment/muhide_strategic_analysis.py` batch runs | FROZEN (الملف يبقى في مكانه) | Script لا يُنقل، لكن batch mode معطّل في workflow |
| `scripts/monitoring/dashboard_generator.py` daily run | FROZEN (الملف يبقى) | الخطوة تُزال من workflow |
| `scripts/monitoring/morning_brief.py` daily run | FROZEN (الملف يبقى) | الخطوة تُزال من workflow |
| `scripts/governance/fix_seniority.py` | ONE-TIME — DONE | نُقل إلى `archive/one_time_migrations/` |
| `scripts/automation/cleanup_overdue_tasks.py` | ONE-TIME — DONE | نُقل إلى `archive/one_time_migrations/` |
| `scripts/automation/outcome_tracker_backup.py` | DEPRECATED | نُقل إلى `archive/deprecated_scripts/` |

> ⚠️ السكربتات التي تبقى في `scripts/` ولا تُنقل فعليًا — فقط تُعلَّم كـ FROZEN في `COMMAND_MAP.md` لتجنّب كسر imports داخلية.

---

## 9. Safe Folder Migration Plan

**المبدأ:** Archive-first. Git mv. Import check. Dry run. Commit.

### Pre-flight (قبل أي نقل)

```bash
# 1. نسخ احتياطي كامل
cd "/sessions/trusting-vigilant-pasteur/mnt/AI Sales OS"
git status                           # تأكد من clean working tree
git checkout -b reorg/v2-operator    # branch جديد

# 2. فحص الـ imports قبل النقل
grep -rn "from pipelines.muqawil" scripts/ .github/
grep -rn "from pipelines.engineering_offices" scripts/ .github/
grep -rn "v2_operator" scripts/ .github/ docs/
grep -rn "muqawil_output" scripts/ .github/
grep -rn "muqawil_pipeline" scripts/ .github/
```

لو ظهر أي import للمجلدات المراد نقلها → **أوقف العملية** وأصلح الـ import أولًا.

### Phase A — Zero-Risk (لا يكسر شيئًا) — Day 1

```bash
# إنشاء المجلدات الجديدة
mkdir -p operator
mkdir -p notion/v2/today_page notion/v2/lead_inbox notion/legacy
mkdir -p dashboards/active dashboards/archived
mkdir -p data/logs data/checkpoints
mkdir -p archive/legacy_docs archive/legacy_outputs archive/frozen_scripts archive/one_time_migrations archive/deprecated_scripts

# نقل ملفات operator (لا references في scripts)
git mv MANUAL.md operator/MANUAL.md
git mv RUNBOOK.md operator/RUNBOOK.md
git mv COMMAND_MAP.md operator/COMMAND_MAP.md
git mv FOLDER_REORG.md operator/FOLDER_REORG.md
git mv v2_operator/V2_BLUEPRINT.md operator/V2_BLUEPRINT.md
rmdir v2_operator

# نقل dashboards (لكن راجع dashboard_generator.py --output أولًا)
git mv dashboards/Sales_Dashboard_Accounts.html dashboards/active/
git mv dashboards/AI_Sales_OS_Live_Dashboard.html dashboards/archived/
git mv dashboards/AI_Sales_OS_MindMap.html dashboards/archived/
git mv dashboards/AI_Sales_OS_Test_Report.html dashboards/archived/
git mv dashboards/Companies_DB_Revenue_Engine_Analysis.html dashboards/archived/
git mv dashboards/Company_Centric_Enforcement_Plan.html dashboards/archived/
git mv dashboards/Full_System_Revenue_Engine_Analysis.html dashboards/archived/
git mv dashboards/Sales_Dashboard_Accounts_view.html dashboards/archived/
git mv "dashboards/تقرير_الاكتتابات_السعودية_2026.html" dashboards/archived/

# نقل logs و checkpoints (كلها gitignored عادة)
mv fix_seniority.log data/logs/ 2>/dev/null
mv ingestion_gate.log data/logs/ 2>/dev/null
mv muhide_analysis.log data/logs/ 2>/dev/null
mv muhide_analysis_checkpoint.json data/checkpoints/ 2>/dev/null
mv muhide_analysis_stats.json data/checkpoints/ 2>/dev/null

# حذف Word lock file
rm -f '~$_Sales_OS_دليل_التنفيذ_البرمجي.docx'

git commit -m "reorg: Phase A — operator layer + dashboards split (zero-risk moves)"
```

**Gate A:** شغّل `python scripts/core/doc_sync_checker.py` — لازم يمر.

### Phase B — Medium-Risk (يحتاج تحديث references) — Day 2

```bash
# 1. حدّث dashboard_generator.py output path
# من: ../dashboards/Sales_Dashboard_Accounts.html
# إلى: ../dashboards/active/Sales_Dashboard_Accounts.html
# (في .github/workflows/daily_sync.yml أيضًا)

# 2. نقل documents قديمة إلى archive
git mv AI_Sales_OS_Code_Execution_Guide.md archive/legacy_docs/
git mv AI_Sales_OS_Restructuring_Report_v6.0.docx archive/legacy_docs/
git mv "AI_Sales_OS_دليل_التنفيذ_البرمجي.docx" archive/legacy_docs/
git mv MUHIDE_Contractor_Sequences.docx archive/legacy_docs/
git mv Apollo_Contacts_MUHIDE_Score.xlsx archive/legacy_outputs/
git mv IPO_Saudi_2026_MUHIDE_Score.xlsx archive/legacy_outputs/

# 3. نقل start_here المكرر
git mv start_here archive/legacy_docs/start_here

git commit -m "reorg: Phase B — archive legacy docs + update dashboard paths"
```

**Gate B:** شغّل workflow يدويًا عبر GitHub Actions UI (manual trigger) — تأكد من نجاح Job 1 و Job 2.

### Phase C — High-Risk (يحتاج حذر) — Day 3 (اختياري — يمكن تأجيله)

```bash
# نقل pipelines المجمّدة
# ⚠️ فقط بعد التأكد من صفر references
git mv pipelines/muqawil archive/frozen_scripts/muqawil
git mv pipelines/engineering_offices archive/frozen_scripts/engineering_offices
git mv muqawil_pipeline archive/frozen_scripts/muqawil_pipeline_root
git mv muqawil_output archive/legacy_outputs/muqawil_output

# نقل one-time scripts
git mv scripts/governance/fix_seniority.py archive/one_time_migrations/
git mv scripts/automation/cleanup_overdue_tasks.py archive/one_time_migrations/
git mv scripts/automation/outcome_tracker_backup.py archive/deprecated_scripts/

git commit -m "reorg: Phase C — archive frozen pipelines + one-time scripts"
```

**Gate C:** شغّل كل الـ workflow مرة أخرى + `python scripts/core/doc_sync_checker.py --strict`. لو أي شيء كسر → `git revert`.

### Phase D — Notion layer (اختياري) — Day 4

إنشاء `notion/v2/` وكتابة `schema.md` لكل عنصر (Today page, Lead Inbox, Sidebar).

---

## 10. Path/Dependency Risks

| خطر | احتمال | الأثر | التخفيف |
|---|---|---|---|
| `dashboard_generator.py --output` يكتب إلى مسار قديم | عالي | Dashboard لا يُولّد | حدّث `.github/workflows/daily_sync.yml` و command في Phase B |
| Scripts في `pipelines/muqawil/` تستورد من بعضها بعضًا بـ relative paths | متوسط | ImportError | Phase C فقط بعد grep كامل |
| `CLAUDE.md` يذكر مسارات قديمة | عالي | توثيق مضلل | تحديث CLAUDE.md بعد كل Phase |
| `docs/` يحتوي روابط لـ `start_here/` | متوسط | روابط مكسورة | بحث و استبدال |
| GitHub Actions cache يحتفظ بمسارات قديمة | منخفض | أول run يفشل | clear cache manually |
| ملفات `.env` تشير إلى مسارات مطلقة | منخفض | crash | فحص `.env.example` أولًا |
| `commands/*.sh` تحتوي مسارات hardcoded | متوسط | shell scripts تفشل | فحص قبل Phase C |

---

## 11. Final Repository Mind Map

```
AI Sales OS/
│
├─ 🎯 OPERATOR LAYER (ما أفتحه أنا)
│   ├─ README.md
│   ├─ CLAUDE.md
│   └─ operator/
│       ├─ MANUAL.md          ← دليلي
│       ├─ RUNBOOK.md         ← ماذا أفعل
│       ├─ COMMAND_MAP.md     ← الأوامر
│       ├─ V2_BLUEPRINT.md    ← التصميم
│       └─ FOLDER_REORG.md    ← هذا الملف
│
├─ 🧠 NOTION LAYER (تصميم الواجهة)
│   └─ notion/v2/
│       ├─ today_page/
│       ├─ lead_inbox/
│       └─ sidebar.md
│
├─ ⚙️ BACKEND ENGINE (لا يُلمس)
│   ├─ scripts/
│   │   ├─ core/ scoring/ automation/
│   │   ├─ governance/ enrichment/
│   │   ├─ meetings/ monitoring/
│   │   ├─ webhooks/ intake/
│   ├─ pipelines/file_sync/
│   └─ .github/workflows/
│
├─ 📊 OUTPUTS
│   ├─ dashboards/active/     ← الوحيد الفعّال
│   ├─ dashboards/archived/   ← 8 ملفات
│   └─ data/
│       ├─ logs/
│       ├─ checkpoints/
│       ├─ imports/ mapping/ snapshots/
│
├─ 📚 DOCS
│   ├─ docs/architecture/
│   ├─ docs/reports/
│   ├─ docs/setup/
│   └─ docs/operator/  (نسخ generated)
│
├─ 🎨 ASSETS
│   ├─ assets/
│   └─ presentations/
│
└─ 🗄️ ARCHIVE (للرجوع فقط)
    ├─ frozen_scripts/
    │   ├─ muqawil/
    │   └─ engineering_offices/
    ├─ legacy_docs/
    ├─ legacy_outputs/
    ├─ one_time_migrations/
    └─ deprecated_scripts/
```

---

## 12. Execution Checklist

- [ ] Phase A (Day 1) — Zero-risk moves
- [ ] Gate A — doc_sync_checker passes
- [ ] Phase B (Day 2) — Archive legacy + update dashboard paths
- [ ] Gate B — Manual workflow run succeeds
- [ ] Phase C (Day 3) — Archive frozen pipelines (optional, can defer)
- [ ] Gate C — Full workflow + strict checker
- [ ] Phase D (Day 4) — Build notion/v2/ schema docs
- [ ] Update CLAUDE.md with new paths
- [ ] Merge `reorg/v2-operator` branch
- [ ] Update `operator/COMMAND_MAP.md` with new paths

**Rollback:** `git revert <commit>` لكل Phase. أو `git reset --hard main` على branch الـ reorg.
