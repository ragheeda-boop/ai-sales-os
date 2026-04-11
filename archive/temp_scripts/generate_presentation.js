const PptxGenJS = require("pptxgenjs");

// Initialize presentation
const pres = new PptxGenJS();
pres.layout = 'LAYOUT_16x9';
pres.author = 'Ragheed';
pres.title = 'AI Sales OS - Version 3.1';
pres.subject = 'Unified Sales Intelligence Platform';

// Color Palette
const colors = {
  primary: "E8771A",      // Orange
  secondary: "1A1A1A",    // Near-black
  darkBg: "1A1A1A",       // Dark background
  lightBg: "F5F5F5",      // Light background
  textLight: "FFFFFF",    // Text on dark
  textDark: "1A1A1A",     // Text on light
  accent: "F0F0F0"        // Accent
};

// Helper function to add a title slide
function addTitleSlide(title, subtitle, details, notes) {
  const slide = pres.addSlide();
  slide.background = { color: colors.darkBg };

  // Main title
  slide.addText(title, {
    x: 0.5, y: 0.8, w: 9, h: 1.2,
    fontSize: 54, bold: true, color: colors.primary,
    align: "center", fontFace: "Arial"
  });

  // Subtitle
  slide.addText(subtitle, {
    x: 0.5, y: 2.0, w: 9, h: 0.6,
    fontSize: 24, color: colors.textLight,
    align: "center", fontFace: "Arial"
  });

  // Details (array of text lines)
  if (details && details.length > 0) {
    let yPos = 2.8;
    details.forEach((detail, idx) => {
      slide.addText(detail, {
        x: 0.5, y: yPos, w: 9, h: 0.4,
        fontSize: 14, color: colors.accent,
        align: "center", fontFace: "Arial"
      });
      yPos += 0.45;
    });
  }

  // Notes if provided
  if (notes) {
    slide.notes = notes;
  }
}

// Helper function to add a section break slide
function addSectionBreak(title, subtitle) {
  const slide = pres.addSlide();
  slide.background = { color: colors.darkBg };

  slide.addText(title, {
    x: 0.5, y: 1.8, w: 9, h: 1.2,
    fontSize: 48, bold: true, color: colors.primary,
    align: "center", fontFace: "Arial"
  });

  slide.addText(subtitle, {
    x: 0.5, y: 3.2, w: 9, h: 0.6,
    fontSize: 20, color: colors.textLight,
    align: "center", fontFace: "Arial"
  });
}

// Helper function for content slides
function addContentSlide(title, content) {
  const slide = pres.addSlide();
  slide.background = { color: colors.lightBg };

  // Title bar with orange accent
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.6,
    fill: { color: colors.primary }, line: { type: "none" }
  });

  slide.addText(title, {
    x: 0.5, y: 0.1, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.textLight,
    align: "left", fontFace: "Arial", margin: 0
  });

  // Content area
  return { slide, contentY: 0.8 };
}

// ============ SLIDE 1: TITLE ============
addTitleSlide(
  "AI SALES OS",
  "Unified Sales Intelligence Platform",
  [
    "Apollo.io → Python Engine → Notion CRM → GitHub Actions",
    "",
    "44,875 Contacts | 15,407 Companies | 4 Phases | 0 Middleware",
    "",
    "Version 3.1 | March 2026 | Owner: Ragheed"
  ]
);

// ============ SLIDE 2: SECTION BREAK ============
addSectionBreak("The Challenge.", "Why we built AI Sales OS");

// ============ SLIDE 3: BEFORE VS AFTER ============
const slide3 = pres.addSlide();
slide3.background = { color: colors.lightBg };

slide3.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.6,
  fill: { color: colors.primary }, line: { type: "none" }
});

slide3.addText("Before vs After", {
  x: 0.5, y: 0.1, w: 9, h: 0.5,
  fontSize: 28, bold: true, color: colors.textLight,
  align: "left", fontFace: "Arial", margin: 0
});

// BEFORE column
slide3.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 0.9, w: 4.2, h: 0.4,
  fill: { color: colors.secondary }, line: { type: "none" }
});

slide3.addText("BEFORE", {
  x: 0.5, y: 0.95, w: 4.2, h: 0.3,
  fontSize: 16, bold: true, color: colors.textLight,
  align: "center", fontFace: "Arial"
});

slide3.addText([
  { text: "Scattered data across platforms", options: { bullet: true, breakLine: true } },
  { text: "No automated sync between systems", options: { bullet: true, breakLine: true } },
  { text: "Manual lead prioritization", options: { bullet: true, breakLine: true } },
  { text: "Inconsistent scoring criteria", options: { bullet: true, breakLine: true } },
  { text: "5+ expensive middleware tools", options: { bullet: true } }
], {
  x: 0.6, y: 1.5, w: 4.0, h: 3.0,
  fontSize: 11, color: colors.textDark,
  fontFace: "Arial"
});

// AFTER column
slide3.addShape(pres.shapes.RECTANGLE, {
  x: 5.3, y: 0.9, w: 4.2, h: 0.4,
  fill: { color: colors.primary }, line: { type: "none" }
});

slide3.addText("AI SALES OS", {
  x: 5.3, y: 0.95, w: 4.2, h: 0.3,
  fontSize: 16, bold: true, color: colors.textLight,
  align: "center", fontFace: "Arial"
});

slide3.addText([
  { text: "Unified data pipeline (Apollo → Notion)", options: { bullet: true, breakLine: true } },
  { text: "Automatic daily sync (daily_sync.py)", options: { bullet: true, breakLine: true } },
  { text: "AI lead scoring (0-100 scale)", options: { bullet: true, breakLine: true } },
  { text: "HOT/WARM/COLD classification", options: { bullet: true, breakLine: true } },
  { text: "Zero middleware — pure Python + GitHub", options: { bullet: true } }
], {
  x: 5.4, y: 1.5, w: 4.0, h: 3.0,
  fontSize: 11, color: colors.textDark,
  fontFace: "Arial"
});

// ============ SLIDE 4: SYSTEM ARCHITECTURE ============
const slide4 = pres.addSlide();
slide4.background = { color: colors.lightBg };

slide4.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.6,
  fill: { color: colors.primary }, line: { type: "none" }
});

slide4.addText("System Architecture", {
  x: 0.5, y: 0.1, w: 9, h: 0.5,
  fontSize: 28, bold: true, color: colors.textLight,
  align: "left", fontFace: "Arial", margin: 0
});

// Architecture boxes
const boxWidth = 2.0;
const boxHeight = 1.8;
const boxY = 1.2;
const boxSpacing = 2.2;

const boxes = [
  { x: 0.5, label: "Apollo.io", details: "44,875 Contacts\n15,407 Companies" },
  { x: 0.5 + boxSpacing, label: "Python Engine", details: "daily_sync.py v2.1\nlead_score.py\nauto_tasks.py\n3 Sync Modes" },
  { x: 0.5 + boxSpacing * 2, label: "Notion CRM", details: "7 Databases\nHOT/WARM/COLD\nDashboards" },
  { x: 0.5 + boxSpacing * 3, label: "GitHub Actions", details: "Daily Cron\n7:00 AM KSA\n10-Step Pipeline" }
];

boxes.forEach((box) => {
  slide4.addShape(pres.shapes.RECTANGLE, {
    x: box.x, y: boxY, w: boxWidth, h: boxHeight,
    fill: { color: colors.secondary }, line: { color: colors.primary, width: 2 }
  });

  slide4.addText(box.label, {
    x: box.x, y: boxY + 0.2, w: boxWidth, h: 0.35,
    fontSize: 14, bold: true, color: colors.primary,
    align: "center", fontFace: "Arial"
  });

  slide4.addText(box.details, {
    x: box.x + 0.1, y: boxY + 0.6, w: boxWidth - 0.2, h: 1.0,
    fontSize: 10, color: colors.accent,
    align: "center", valign: "middle", fontFace: "Arial"
  });
});

// Arrows between boxes
for (let i = 0; i < 3; i++) {
  const arrowX = 0.5 + (i + 1) * boxSpacing - 0.3;
  slide4.addShape(pres.shapes.RIGHT_ARROW, {
    x: arrowX, y: boxY + 0.8, w: 0.3, h: 0.2,
    fill: { color: colors.primary }, line: { type: "none" }
  });
}

// Bottom note
slide4.addText("No middleware — pure Python + GitHub Actions", {
  x: 0.5, y: 4.5, w: 9, h: 0.3,
  fontSize: 12, bold: true, color: colors.primary,
  align: "center", fontFace: "Arial"
});

// ============ SLIDE 5: DATA AT SCALE ============
const slide5 = pres.addSlide();
slide5.background = { color: colors.lightBg };

slide5.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.6,
  fill: { color: colors.primary }, line: { type: "none" }
});

slide5.addText("Data at Scale", {
  x: 0.5, y: 0.1, w: 9, h: 0.5,
  fontSize: 28, bold: true, color: colors.textLight,
  align: "left", fontFace: "Arial", margin: 0
});

// Big stats
const stats = [
  { num: "44,875", label: "Contacts" },
  { num: "15,407", label: "Companies" },
  { num: "7", label: "Databases" },
  { num: "3", label: "Sync Modes" }
];

stats.forEach((stat, idx) => {
  const statX = 0.5 + (idx % 4) * 2.3;
  slide5.addShape(pres.shapes.RECTANGLE, {
    x: statX, y: 1.0, w: 2.0, h: 0.9,
    fill: { color: colors.secondary }, line: { color: colors.primary, width: 2 }
  });

  slide5.addText(stat.num, {
    x: statX, y: 1.15, w: 2.0, h: 0.35,
    fontSize: 28, bold: true, color: colors.primary,
    align: "center", fontFace: "Arial"
  });

  slide5.addText(stat.label, {
    x: statX, y: 1.5, w: 2.0, h: 0.25,
    fontSize: 11, color: colors.accent,
    align: "center", fontFace: "Arial"
  });
});

// Databases list
const dbTitle = "7 Notion Databases";
slide5.addText(dbTitle, {
  x: 0.5, y: 2.1, w: 9, h: 0.3,
  fontSize: 14, bold: true, color: colors.secondary,
  align: "left", fontFace: "Arial"
});

slide5.addText([
  { text: "Companies", options: { bullet: true, breakLine: true } },
  { text: "Contacts", options: { bullet: true, breakLine: true } },
  { text: "Tasks (auto-created by Action Engine)", options: { bullet: true, breakLine: true } },
  { text: "Opportunities", options: { bullet: true, breakLine: true } },
  { text: "Meetings", options: { bullet: true, breakLine: true } },
  { text: "Activities", options: { bullet: true, breakLine: true } },
  { text: "Email Hub", options: { bullet: true } }
], {
  x: 0.7, y: 2.5, w: 8.6, h: 2.7,
  fontSize: 11, color: colors.textDark,
  fontFace: "Arial"
});

// ============ SLIDE 6: SYNC ENGINE ============
const slide6 = pres.addSlide();
slide6.background = { color: colors.lightBg };

slide6.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.6,
  fill: { color: colors.primary }, line: { type: "none" }
});

slide6.addText("daily_sync.py v2.1 — Three operational modes", {
  x: 0.5, y: 0.1, w: 9, h: 0.5,
  fontSize: 28, bold: true, color: colors.textLight,
  align: "left", fontFace: "Arial", margin: 0
});

// Three modes
const modes = [
  { title: "INCREMENTAL", subtitle: "Daily use", detail: "Last 26 hours\nOverlap handling\nNo gaps" },
  { title: "BACKFILL", subtitle: "Gap recovery", detail: "Historical range\nCheckpoint resume\nInterruptible" },
  { title: "FULL", subtitle: "First-time / rebuild", detail: "All records\nA-Z partitioning\n2-4 hours" }
];

modes.forEach((mode, idx) => {
  const modeX = 0.5 + idx * 3.1;
  slide6.addShape(pres.shapes.RECTANGLE, {
    x: modeX, y: 1.1, w: 2.9, h: 0.4,
    fill: { color: colors.primary }, line: { type: "none" }
  });

  slide6.addText(mode.title, {
    x: modeX, y: 1.15, w: 2.9, h: 0.3,
    fontSize: 13, bold: true, color: colors.textLight,
    align: "center", fontFace: "Arial"
  });

  slide6.addText(mode.subtitle, {
    x: modeX, y: 1.6, w: 2.9, h: 0.25,
    fontSize: 10, color: colors.secondary,
    align: "center", fontFace: "Arial"
  });

  slide6.addText(mode.detail, {
    x: modeX + 0.1, y: 1.95, w: 2.7, h: 1.3,
    fontSize: 9, color: colors.textDark,
    align: "center", valign: "middle", fontFace: "Arial"
  });
});

// Features
slide6.addText([
  { text: "Triple Dedup", options: { bullet: true, breakLine: true } },
  { text: "Seniority Normalization", options: { bullet: true, breakLine: true } },
  { text: "Safe Boolean Writing", options: { bullet: true, breakLine: true } },
  { text: "Pre-loads Notion records", options: { bullet: true } }
], {
  x: 0.7, y: 3.7, w: 8.6, h: 1.5,
  fontSize: 11, color: colors.textDark,
  fontFace: "Arial"
});

// ============ SLIDE 7: LEAD SCORING ============
const slide7 = pres.addSlide();
slide7.background = { color: colors.lightBg };

slide7.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.6,
  fill: { color: colors.primary }, line: { type: "none" }
});

slide7.addText("lead_score.py — Writes Score + Lead Tier", {
  x: 0.5, y: 0.1, w: 9, h: 0.5,
  fontSize: 28, bold: true, color: colors.textLight,
  align: "left", fontFace: "Arial", margin: 0
});

// Formula
slide7.addText("Scoring Formula (v1.1 — Current Calibrated Weights)", {
  x: 0.5, y: 0.8, w: 9, h: 0.25,
  fontSize: 12, bold: true, color: colors.secondary,
  align: "left", fontFace: "Arial"
});

slide7.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.15, w: 9, h: 0.55,
  fill: { color: colors.secondary }, line: { color: colors.primary, width: 1 }
});

slide7.addText("Score = (Intent × 10%) + (Engagement × 10%) + (Company Size × 45%) + (Seniority × 35%)", {
  x: 0.7, y: 1.25, w: 8.6, h: 0.35,
  fontSize: 12, color: colors.accent,
  align: "center", valign: "middle", fontFace: "Arial"
});

// Classification table
slide7.addText("Lead Classification", {
  x: 0.5, y: 1.85, w: 9, h: 0.25,
  fontSize: 12, bold: true, color: colors.secondary,
  align: "left", fontFace: "Arial"
});

const tableData = [
  [
    { text: "Tier", options: { bold: true, fill: { color: colors.primary }, color: colors.textLight } },
    { text: "Score", options: { bold: true, fill: { color: colors.primary }, color: colors.textLight } },
    { text: "Action", options: { bold: true, fill: { color: colors.primary }, color: colors.textLight } }
  ],
  ["HOT", "≥ 80", "Call today — high-value decision makers"],
  ["WARM", "50–79", "Follow up within 48 hours"],
  ["COLD", "< 50", "Monitor only — no action"]
];

slide7.addTable(tableData, {
  x: 0.5, y: 2.2, w: 9, h: 1.6,
  border: { pt: 1, color: "CCCCCC" },
  colW: [1.2, 1.0, 6.8],
  fontSize: 10,
  color: colors.textDark
});

// Note
slide7.addText("Note: v1.1 weights — Size+Seniority weighted high because Intent+Engagement data is sparse. This is expected and correct.", {
  x: 0.5, y: 4.0, w: 9, h: 0.5,
  fontSize: 9, italic: true, color: colors.secondary,
  align: "left", fontFace: "Arial"
});

// ============ SLIDE 8: AUTOMATED PIPELINE ============
const slide8 = pres.addSlide();
slide8.background = { color: colors.lightBg };

slide8.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.6,
  fill: { color: colors.primary }, line: { type: "none" }
});

slide8.addText("GitHub Actions — 10-Step Daily Pipeline", {
  x: 0.5, y: 0.1, w: 9, h: 0.5,
  fontSize: 28, bold: true, color: colors.textLight,
  align: "left", fontFace: "Arial", margin: 0
});

// 10 steps in 2 columns
const steps = [
  "1. Checkout repository",
  "2. Setup Python 3.11 with pip cache",
  "3. Install dependencies",
  "4. daily_sync.py (sync last 26 hours)",
  "5. lead_score.py (recalculate + write tier)",
  "6. action_ready_updater.py (5-condition gating)",
  "7. auto_tasks.py (create SLA-based tasks)",
  "8. health_check.py (validate pipeline)",
  "9. Upload logs as artifacts",
  "10. Notify on failure"
];

slide8.addText(steps.slice(0, 5).join("\n"), {
  x: 0.5, y: 1.0, w: 4.5, h: 2.8,
  fontSize: 10, color: colors.textDark,
  align: "left", fontFace: "Arial"
});

slide8.addText(steps.slice(5).join("\n"), {
  x: 5.0, y: 1.0, w: 4.5, h: 2.8,
  fontSize: 10, color: colors.textDark,
  align: "left", fontFace: "Arial"
});

// Cost/timing
slide8.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 4.0, w: 9, h: 0.5,
  fill: { color: colors.secondary }, line: { color: colors.primary, width: 1 }
});

slide8.addText("Schedule: Daily at 7:00 AM KSA (04:00 UTC) | Cost: FREE — 450 min/month of 2,000 free tier", {
  x: 0.7, y: 4.1, w: 8.6, h: 0.3,
  fontSize: 11, bold: true, color: colors.accent,
  align: "center", fontFace: "Arial"
});

// ============ SLIDE 9: CODE BASE ============
const slide9 = pres.addSlide();
slide9.background = { color: colors.lightBg };

slide9.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.6,
  fill: { color: colors.primary }, line: { type: "none" }
});

slide9.addText("Code Base — 10 Active Scripts", {
  x: 0.5, y: 0.1, w: 9, h: 0.5,
  fontSize: 28, bold: true, color: colors.textLight,
  align: "left", fontFace: "Arial", margin: 0
});

const codeTable = [
  [
    { text: "Script", options: { bold: true, fill: { color: colors.primary }, color: colors.textLight } },
    { text: "Purpose", options: { bold: true, fill: { color: colors.primary }, color: colors.textLight } },
    { text: "Status", options: { bold: true, fill: { color: colors.primary }, color: colors.textLight } }
  ],
  ["daily_sync.py", "Sync Engine v2.1", "ACTIVE"],
  ["lead_score.py", "Score + Tier Writer", "ACTIVE"],
  ["constants.py", "Unified Field Names", "ACTIVE"],
  ["notion_helpers.py", "Notion API Utils", "ACTIVE"],
  ["auto_tasks.py", "Action Engine (SLA)", "ACTIVE"],
  ["action_ready_updater.py", "5-Condition Gating", "ACTIVE"],
  ["health_check.py", "Pipeline Validator", "ACTIVE"],
  ["webhook_server.py", "Apollo Webhooks", "ACTIVE"],
  ["verify_links.py", "Link Verifier", "ACTIVE"],
  ["job_postings_sync.py", "Job Signals", "PLANNED"]
];

slide9.addTable(codeTable, {
  x: 0.3, y: 0.8, w: 9.4, h: 3.5,
  border: { pt: 1, color: "CCCCCC" },
  colW: [2.2, 5.0, 2.2],
  fontSize: 9,
  color: colors.textDark,
  rowH: 0.32
});

// Tech stack
slide9.addText("Tech Stack: Python 3.11 | Notion API | Apollo API | GitHub Actions", {
  x: 0.5, y: 4.45, w: 9, h: 0.3,
  fontSize: 11, bold: true, color: colors.secondary,
  align: "center", fontFace: "Arial"
});

// ============ SLIDE 10: EXECUTION ROADMAP ============
const slide10 = pres.addSlide();
slide10.background = { color: colors.lightBg };

slide10.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.6,
  fill: { color: colors.primary }, line: { type: "none" }
});

slide10.addText("Execution Roadmap — 4 Phases", {
  x: 0.5, y: 0.1, w: 9, h: 0.5,
  fontSize: 28, bold: true, color: colors.textLight,
  align: "left", fontFace: "Arial", margin: 0
});

// 4 phase boxes
const phases = [
  { title: "Phase 1\nACTIVATE", status: "COMPLETE", color: "2D9C7B", items: ["Full Sync running", "Lead Scoring built", "Seniority normalization", "Safe boolean writing"] },
  { title: "Phase 2\nACTION", status: "CODE COMPLETE", color: colors.primary, items: ["auto_tasks.py built", "action_ready_updater.py", "health_check.py", "Pending first run"] },
  { title: "Phase 3\nENRICH", status: "NEXT", color: "4A90E2", items: ["Job Postings signal", "Job Change detection", "Intent Trend tracking", "Lead Score v2.0"] },
  { title: "Phase 4\nOPTIMIZE", status: "FUTURE", color: "999999", items: ["Odoo integration", "Revenue tracking", "Analytics", "Full automation"] }
];

phases.forEach((phase, idx) => {
  const phaseX = 0.4 + idx * 2.35;
  slide10.addShape(pres.shapes.RECTANGLE, {
    x: phaseX, y: 1.2, w: 2.15, h: 3.0,
    fill: { color: phase.color }, line: { type: "none" }
  });

  slide10.addText(phase.title, {
    x: phaseX + 0.1, y: 1.35, w: 1.95, h: 0.4,
    fontSize: 12, bold: true, color: colors.textLight,
    align: "center", fontFace: "Arial"
  });

  slide10.addText(phase.status, {
    x: phaseX + 0.1, y: 1.8, w: 1.95, h: 0.3,
    fontSize: 9, color: colors.accent,
    align: "center", fontFace: "Arial"
  });

  const itemText = phase.items.join("\n");
  slide10.addText(itemText, {
    x: phaseX + 0.1, y: 2.2, w: 1.95, h: 1.7,
    fontSize: 8, color: colors.accent,
    align: "center", valign: "middle", fontFace: "Arial"
  });
});

slide10.addText("Overall Progress: Phase 2 code complete — pending first run", {
  x: 0.5, y: 4.5, w: 9, h: 0.3,
  fontSize: 11, bold: true, color: colors.secondary,
  align: "center", fontFace: "Arial"
});

// ============ SLIDE 11: ACTION ENGINE ============
const slide11 = pres.addSlide();
slide11.background = { color: colors.lightBg };

slide11.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.6,
  fill: { color: colors.primary }, line: { type: "none" }
});

slide11.addText("auto_tasks.py + action_ready_updater.py", {
  x: 0.5, y: 0.1, w: 9, h: 0.5,
  fontSize: 28, bold: true, color: colors.textLight,
  align: "left", fontFace: "Arial", margin: 0
});

// Action Ready conditions
slide11.addText("Action Ready — 5 Gating Conditions", {
  x: 0.5, y: 0.8, w: 9, h: 0.25,
  fontSize: 12, bold: true, color: colors.secondary,
  align: "left", fontFace: "Arial"
});

slide11.addText([
  { text: "Lead Score ≥ 50", options: { bullet: true, breakLine: true } },
  { text: "Do Not Call = False", options: { bullet: true, breakLine: true } },
  { text: "Outreach Status NOT in {Do Not Contact, Bounced, Bad Data}", options: { bullet: true, breakLine: true } },
  { text: "Stage is NOT 'Customer' or 'Churned'", options: { bullet: true, breakLine: true } },
  { text: "Has at least one contact method (email or phone)", options: { bullet: true } }
], {
  x: 0.7, y: 1.2, w: 8.6, h: 1.3,
  fontSize: 10, color: colors.textDark,
  fontFace: "Arial"
});

// Priority rules
slide11.addText("Priority Rules & SLA", {
  x: 0.5, y: 2.65, w: 9, h: 0.25,
  fontSize: 12, bold: true, color: colors.secondary,
  align: "left", fontFace: "Arial"
});

const prioTable = [
  [
    { text: "Tier", options: { bold: true, fill: { color: colors.primary }, color: colors.textLight } },
    { text: "Priority", options: { bold: true, fill: { color: colors.primary }, color: colors.textLight } },
    { text: "Action", options: { bold: true, fill: { color: colors.primary }, color: colors.textLight } },
    { text: "SLA", options: { bold: true, fill: { color: colors.primary }, color: colors.textLight } }
  ],
  ["HOT", "Critical", "CALL", "24 hours"],
  ["WARM", "High", "FOLLOW-UP", "48 hours"]
];

slide11.addTable(prioTable, {
  x: 0.5, y: 3.0, w: 9, h: 1.0,
  border: { pt: 1, color: "CCCCCC" },
  colW: [1.5, 1.8, 2.5, 3.2],
  fontSize: 10,
  color: colors.textDark
});

// Features
slide11.addText("Features:", {
  x: 0.5, y: 4.15, w: 9, h: 0.25,
  fontSize: 12, bold: true, color: colors.secondary,
  align: "left", fontFace: "Arial"
});

slide11.addText([
  { text: "Duplicate prevention: checks for existing open tasks before creating", options: { bullet: true, breakLine: true } },
  { text: "Automated task creation based on Lead Tier and SLA deadlines", options: { bullet: true } }
], {
  x: 0.7, y: 4.5, w: 8.6, h: 0.8,
  fontSize: 10, color: colors.textDark,
  fontFace: "Arial"
});

// ============ SLIDE 12: SIGNALS & ENRICHMENT ============
const slide12 = pres.addSlide();
slide12.background = { color: colors.lightBg };

slide12.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.6,
  fill: { color: colors.primary }, line: { type: "none" }
});

slide12.addText("Phase 3 — Signals & Enrichment", {
  x: 0.5, y: 0.1, w: 9, h: 0.5,
  fontSize: 28, bold: true, color: colors.textLight,
  align: "left", fontFace: "Arial", margin: 0
});

// Coming in Phase 3
slide12.addText("Coming in Phase 3", {
  x: 0.5, y: 0.8, w: 9, h: 0.25,
  fontSize: 12, bold: true, color: colors.secondary,
  align: "left", fontFace: "Arial"
});

slide12.addText([
  { text: "Job Postings Signal — detect hiring activity at target accounts", options: { bullet: true, breakLine: true } },
  { text: "Job Change Detection — identify when decision-makers change roles", options: { bullet: true, breakLine: true } },
  { text: "Intent Trend Tracking — compare intent scores between syncs", options: { bullet: true } }
], {
  x: 0.7, y: 1.2, w: 8.6, h: 1.2,
  fontSize: 11, color: colors.textDark,
  fontFace: "Arial"
});

// Lead Score v2.0
slide12.addText("Lead Score v2.0 Weights (activate with signals data)", {
  x: 0.5, y: 2.6, w: 9, h: 0.25,
  fontSize: 12, bold: true, color: colors.secondary,
  align: "left", fontFace: "Arial"
});

slide12.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 3.0, w: 9, h: 0.5,
  fill: { color: colors.secondary }, line: { color: colors.primary, width: 1 }
});

slide12.addText("Intent 30% + Engagement 25% + Signals 25% + Company Size 10% + Seniority 10%", {
  x: 0.7, y: 3.1, w: 8.6, h: 0.3,
  fontSize: 11, color: colors.accent,
  align: "center", valign: "middle", fontFace: "Arial"
});

// Note
slide12.addText("Note: DO NOT activate v2.0 until signals data is actually populated. Empty fields would weaken all scores.", {
  x: 0.5, y: 3.7, w: 9, h: 0.6,
  fontSize: 10, italic: true, color: colors.secondary,
  align: "left", fontFace: "Arial"
});

// ============ SLIDE 13: CURRENT STATUS ============
const slide13 = pres.addSlide();
slide13.background = { color: colors.lightBg };

slide13.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.6,
  fill: { color: colors.primary }, line: { type: "none" }
});

slide13.addText("Current Status", {
  x: 0.5, y: 0.1, w: 9, h: 0.5,
  fontSize: 28, bold: true, color: colors.textLight,
  align: "left", fontFace: "Arial", margin: 0
});

slide13.addText([
  { text: "Phase 1: ACTIVATE", options: { bold: true, breakLine: true } },
  { text: "✓ COMPLETE — Full sync, lead scoring, seniority normalization, safe booleans", options: { breakLine: true } },
  { text: "", options: { breakLine: true } },
  { text: "Phase 2: ACTION", options: { bold: true, breakLine: true } },
  { text: "✓ CODE COMPLETE — auto_tasks.py, action_ready_updater.py, health_check.py", options: { breakLine: true } },
  { text: "", options: { breakLine: true } },
  { text: "Remaining Tasks:", options: { bold: true, breakLine: true } },
  { text: "1. Run lead_score.py --force (write Lead Tier for all contacts)", options: { breakLine: true } },
  { text: "2. Run action_ready_updater.py (evaluate 5 conditions)", options: { breakLine: true } },
  { text: "3. Run auto_tasks.py --dry-run (validate task creation)", options: { breakLine: true } },
  { text: "4. Push code to GitHub, add NOTION_DATABASE_ID_TASKS secret", options: { breakLine: true } },
  { text: "5. Activate daily pipeline (GitHub Actions)", options: { breakLine: true } }
], {
  x: 0.7, y: 0.9, w: 8.6, h: 4.0,
  fontSize: 10, color: colors.textDark,
  fontFace: "Arial"
});

// ============ SLIDE 14: WHAT'S NEXT ============
addTitleSlide(
  "What's Next",
  "",
  [
    "1. Run lead_score.py --force (write Lead Tier for all contacts)",
    "2. Run action_ready_updater.py + auto_tasks.py --dry-run",
    "3. Push code to GitHub, add NOTION_DATABASE_ID_TASKS secret",
    "4. Activate daily pipeline (GitHub Actions)",
    "5. Phase 3: Job Postings + Intent Signals",
    "",
    "AI SALES OS — Built by Ragheed | Version 3.1 | March 2026"
  ]
);

// Save presentation
pres.writeFile({ fileName: "/sessions/wizardly-elegant-einstein/mnt/AI Sales OS/AI_Sales_OS_Presentation.pptx" });
console.log("✓ Presentation created successfully!");
