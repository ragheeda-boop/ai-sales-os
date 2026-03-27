#!/usr/bin/env node

const PptxGenJS = require('pptxgenjs');
const fs = require('fs');
const path = require('path');

// Create presentation instance
const prs = new PptxGenJS();

// Brand colors (NO # prefix as per requirements)
const colors = {
  primaryOrange: 'E8771A',
  black: '000000',
  darkBlack: '1A1A1A',
  white: 'FFFFFF',
  lightGray: 'EBEBEB',
  darkGray: '4A4A4A',
  gray333: '333333'
};

// Set presentation properties
prs.defineLayout({ name: 'LAYOUT1', width: 10, height: 5.625 });
prs.defineLayout({ name: 'BLANK' });

// Utility function to get color option safely
function getColor(colorHex) {
  return { color: colorHex };
}

// Utility function to create text properties
function createTextProps(opts = {}) {
  return {
    fontFace: opts.fontFace || 'Calibri',
    fontSize: opts.fontSize || 18,
    bold: opts.bold || false,
    color: opts.color || colors.black,
    align: opts.align || 'left',
    valign: opts.valign || 'middle',
    ...opts
  };
}

// Utility function to create shadow effect
function createShadow() {
  return { type: 'outer', color: '000000', blur: 3, offset: 2, angle: 45, opacity: 0.5 };
}

// Slide 1: Title Slide
function addTitleSlide() {
  const slide = prs.addSlide();
  
  // Black background
  slide.background = { color: colors.black };
  
  // Orange accent bar at top
  slide.addShape(prs.ShapeType.rect, {
    x: 0, y: 0, w: 0.3, h: 5.625,
    fill: { color: colors.primaryOrange },
    line: { type: 'none' }
  });
  
  // Logo - load from file
  try {
    const logoPath = path.join(__dirname, 'Muhide.png');
    if (fs.existsSync(logoPath)) {
      slide.addImage({
        path: logoPath,
        x: 8.5, y: 0.3, w: 1.2, h: 1.2
      });
    }
  } catch (e) {
    console.log('Logo not found, skipping');
  }
  
  // Title: MUHIDE
  slide.addText('MUHIDE', {
    x: 1.5, y: 1.8, w: 7, h: 0.8,
    fontSize: 72,
    bold: true,
    color: colors.primaryOrange,
    fontFace: 'Montserrat',
    align: 'center'
  });
  
  // Subtitle
  slide.addText('AI Sales OS Platform', {
    x: 1.5, y: 2.8, w: 7, h: 0.5,
    fontSize: 32,
    color: colors.white,
    fontFace: 'Calibri',
    align: 'center'
  });
  
  // Tagline with orange period
  slide.addText('Trust in Every Transaction', {
    x: 1.5, y: 4.0, w: 7, h: 0.4,
    fontSize: 18,
    color: colors.lightGray,
    align: 'center',
    italic: true
  });
}

// Slide 2: Divider - Executive Summary
function addDividerSlide(title) {
  const slide = prs.addSlide();
  
  // Gradient background (black to white)
  slide.background = { 
    fill: colors.black,
    transparency: 0
  };
  
  // Create gradient effect with rectangle
  slide.addShape(prs.ShapeType.rect, {
    x: 0, y: 0, w: 10, h: 5.625,
    fill: { type: 'solid', color: colors.black, transparency: 0 },
    line: { type: 'none' }
  });
  
  // White overlay gradient effect
  slide.addShape(prs.ShapeType.rect, {
    x: 5, y: 0, w: 5, h: 5.625,
    fill: { color: colors.white },
    line: { type: 'none' }
  });
  
  // Orange bar at top left
  slide.addShape(prs.ShapeType.rect, {
    x: 0, y: 0, w: 0.2, h: 0.3,
    fill: { color: colors.primaryOrange },
    line: { type: 'none' }
  });
  
  // Title with orange period
  slide.addText(title, {
    x: 0.5, y: 2.3, w: 9, h: 1,
    fontSize: 54,
    bold: true,
    color: colors.white,
    fontFace: 'Montserrat',
    align: 'left'
  });
}

// Slide 3: Content slide template
function addContentSlide(title, content) {
  const slide = prs.addSlide();
  
  // Light gray background
  slide.background = { color: colors.lightGray };
  
  // Black side bar (left)
  slide.addShape(prs.ShapeType.rect, {
    x: 0, y: 0, w: 0.15, h: 5.625,
    fill: { color: colors.black },
    line: { type: 'none' }
  });
  
  // Logo at top right
  try {
    const logoPath = path.join(__dirname, 'Muhide.png');
    if (fs.existsSync(logoPath)) {
      slide.addImage({
        path: logoPath,
        x: 9.0, y: 0.3, w: 0.9, h: 0.9
      });
    }
  } catch (e) {
    // Logo not found
  }
  
  // Title
  slide.addText(title, {
    x: 0.4, y: 0.3, w: 8.5, h: 0.6,
    fontSize: 36,
    bold: true,
    color: colors.black,
    fontFace: 'Montserrat'
  });
  
  // Add content (bullet points or text)
  let yPos = 1.1;
  if (Array.isArray(content)) {
    content.forEach((item, idx) => {
      if (item.type === 'heading') {
        slide.addText(item.text, {
          x: 0.5, y: yPos, w: 9, h: 0.35,
          fontSize: 18,
          bold: true,
          color: colors.black,
          fontFace: 'Calibri'
        });
        yPos += 0.4;
      } else if (item.type === 'bullet') {
        slide.addText('• ' + item.text, {
          x: 0.7, y: yPos, w: 8.8, h: 0.35,
          fontSize: 14,
          color: colors.darkGray,
          fontFace: 'Calibri'
        });
        yPos += 0.45;
      } else if (item.type === 'stat') {
        // Large number with orange accent
        slide.addShape(prs.ShapeType.circle, {
          x: 0.6, y: yPos - 0.15, w: 0.6, h: 0.6,
          fill: { color: colors.primaryOrange },
          line: { type: 'none' }
        });
        
        slide.addText(item.number, {
          x: 0.6, y: yPos - 0.15, w: 0.6, h: 0.6,
          fontSize: 28,
          bold: true,
          color: colors.white,
          align: 'center',
          valign: 'middle',
          fontFace: 'Montserrat'
        });
        
        slide.addText(item.label, {
          x: 1.4, y: yPos - 0.05, w: 8, h: 0.5,
          fontSize: 14,
          color: colors.black,
          fontFace: 'Calibri'
        });
        yPos += 0.7;
      }
    });
  }
}

// Generate slides
addTitleSlide();

addDividerSlide('Executive Summary');

addContentSlide('Market Opportunity', [
  { type: 'bullet', text: 'Enterprise sales organizations seek AI-powered solutions' },
  { type: 'bullet', text: 'Average sales rep spends 60% time on admin vs selling' },
  { type: 'bullet', text: '$7B+ annual sales tech spending, growing 25% YoY' },
  { type: 'stat', number: '73%', label: 'Of reps want AI sales tools' }
]);

addDividerSlide('Solution Overview');

addContentSlide('MUHIDE AI Sales OS', [
  { type: 'bullet', text: 'Intelligent automation for sales workflows' },
  { type: 'bullet', text: 'Real-time opportunity scoring and insights' },
  { type: 'bullet', text: 'Seamless CRM integration' },
  { type: 'bullet', text: 'ROI-driven metrics and analytics' }
]);

addDividerSlide('Key Features');

addContentSlide('Intelligent Automation', [
  { type: 'heading', text: 'Lead Qualification' },
  { type: 'bullet', text: 'AI-powered lead scoring' },
  { type: 'bullet', text: 'Automatic qualification workflows' },
  { type: 'heading', text: 'Sales Engagement' },
  { type: 'bullet', text: 'Predictive next actions' },
  { type: 'bullet', text: 'Personalized outreach at scale' }
]);

addDividerSlide('Business Case');

addContentSlide('Financial Impact', [
  { type: 'stat', number: '40%', label: 'Increase in deals closed' },
  { type: 'stat', number: '3x', label: 'ROI in first 12 months' },
  { type: 'stat', number: '25%', label: 'Reduction in sales cycle' }
]);

addDividerSlide('Implementation');

addContentSlide('Deployment Roadmap', [
  { type: 'heading', text: 'Phase 1: Assessment (Weeks 1-2)' },
  { type: 'bullet', text: 'Sales org analysis and requirements gathering' },
  { type: 'heading', text: 'Phase 2: Integration (Weeks 3-6)' },
  { type: 'bullet', text: 'CRM setup and AI training' },
  { type: 'heading', text: 'Phase 3: Launch (Weeks 7-8)' },
  { type: 'bullet', text: 'Team enablement and go-live' }
]);

addDividerSlide('Competitive Advantage');

addContentSlide('Why MUHIDE', [
  { type: 'bullet', text: 'Purpose-built for enterprise sales' },
  { type: 'bullet', text: 'Advanced AI with transparent decision-making' },
  { type: 'bullet', text: 'Proven track record with Fortune 500 companies' },
  { type: 'bullet', text: 'Unmatched support and customer success' }
]);

addDividerSlide('Use Cases');

addContentSlide('Real-World Applications', [
  { type: 'heading', text: 'B2B SaaS' },
  { type: 'bullet', text: 'Account-based sales optimization' },
  { type: 'heading', text: 'Enterprise Software' },
  { type: 'bullet', text: 'Complex deal management' },
  { type: 'heading', text: 'Professional Services' },
  { type: 'bullet', text: 'Resource allocation and project assignment' }
]);

addContentSlide('Measurable Results', [
  { type: 'bullet', text: 'Early adopters see 35-50% productivity gains' },
  { type: 'bullet', text: 'Average rep closes 3-5 additional deals quarterly' },
  { type: 'bullet', text: 'Deal velocity increases by 2-3 weeks' },
  { type: 'bullet', text: 'Customer satisfaction scores improve 15-20%' }
]);

addDividerSlide('Next Steps');

addContentSlide('Get Started with MUHIDE', [
  { type: 'heading', text: 'Ready to Transform Your Sales?' },
  { type: 'bullet', text: 'Schedule a personalized product demo' },
  { type: 'bullet', text: 'Access our ROI calculator' },
  { type: 'bullet', text: 'Join our customer community' },
  { type: 'bullet', text: 'Start your free 30-day trial' },
  { type: 'heading', text: 'Contact us: sales@muhide.io' }
]);

// Save presentation
const outputPath = path.join(__dirname, 'AI_Sales_OS_Presentation.pptx');
prs.writeFile({ fileName: outputPath });
console.log(`Presentation created: ${outputPath}`);
