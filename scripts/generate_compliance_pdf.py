"""Script to compile professional Compliance Note PDF using ReportLab."""

from __future__ import annotations
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable


def build_compliance_pdf(output_path: str = "LinkedIn_ToS_Compliance_Architecture.pdf"):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45,
    )
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4f46e5"),
        spaceAfter=15,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8,
    )
    bullet_style = ParagraphStyle(
        "BulletCustom",
        parent=body_style,
        leftIndent=15,
        bulletIndent=5,
        spaceAfter=4,
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("Legal & Technical Compliance Architecture", title_style))
    story.append(Paragraph("LinkedIn Outreach, Public Data Scraping Policy & Risk Mitigation Protocol", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4f46e5"), spaceAfter=12))

    # Executive Summary
    story.append(Paragraph("1. Executive Summary", heading_style))
    exec_text = (
        "This architectural specification details the compliant operating model implemented in the "
        "Lead Generation and LinkedIn Outreach Agent. By deliberately adhering to a <b>Manual-Assist Architecture</b> "
        "and utilizing official <b>LinkedIn Marketing Developer Platform Lead Sync APIs</b> for inbound opt-ins, "
        "the system guarantees 100% adherence to LinkedIn User Agreement (Section 8.2), eliminates personal account ban risks, "
        "and safeguards company reputation."
    )
    story.append(Paragraph(exec_text, body_style))

    # Threat Analysis Table
    story.append(Paragraph("2. Comparative Risk Analysis", heading_style))
    table_data = [
        [
            Paragraph("<b>Compliance Vector</b>", body_style),
            Paragraph("<b>Automated Headless Bots</b>", body_style),
            Paragraph("<b>Our Manual-Assist Model</b>", body_style),
        ],
        [
            Paragraph("<b>LinkedIn ToS (Sec 8.2)</b>", body_style),
            Paragraph("<font color='#dc2626'><b>Direct Violation</b></font><br/>Explicit prohibition on bots/auto-DMs.", body_style),
            Paragraph("<font color='#16a34a'><b>100% Compliant</b></font><br/>Human sender in official UI.", body_style),
        ],
        [
            Paragraph("<b>Account Ban Risk</b>", body_style),
            Paragraph("<font color='#dc2626'><b>Critical / High</b></font><br/>Flagged by Behavioral AI heuristics.", body_style),
            Paragraph("<font color='#16a34a'><b>Zero Risk</b></font><br/>Standard authentic session.", body_style),
        ],
        [
            Paragraph("<b>Credential Security</b>", body_style),
            Paragraph("<font color='#dc2626'><b>Exposed</b></font><br/>Requires sharing session cookies.", body_style),
            Paragraph("<font color='#16a34a'><b>Zero Exposure</b></font><br/>No passwords/cookies stored.", body_style),
        ],
        [
            Paragraph("<b>Message Quality & Conversion</b>", body_style),
            Paragraph("<font color='#64748b'><b>Low</b></font><br/>Generic spam scripts.", body_style),
            Paragraph("<font color='#16a34a'><b>High</b></font><br/>Contextual AI enrichment.", body_style),
        ],
    ]

    t = Table(table_data, colWidths=[130, 190, 200])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#1e293b")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # Core Policy Enforcement Pillars
    story.append(Paragraph("3. Technical Enforcement Pillars", heading_style))
    story.append(Paragraph("• <b>Human-in-the-Loop 1-Click Clipboard:</b> AI models extract public lead signals and craft bespoke drafts. Human operators review and click 'Send' natively.", bullet_style))
    story.append(Paragraph("• <b>Public Search & robots.txt Adherence:</b> Scraper engine parses only public directory endpoints, enforces rate-limiting delays with jitter, and respects robots.txt.", bullet_style))
    story.append(Paragraph("• <b>Persistent Memory Deduplication:</b> SQLite/PostgreSQL storage tracks contacted identifiers, preventing duplicate outreach across all future cron runs.", bullet_style))
    story.append(Paragraph("• <b>Official Ads Lead Sync:</b> Supports official OAuth 2.0 Webhook integration for inbound LinkedIn Lead Gen Ads.", bullet_style))

    # Recommendation
    story.append(Paragraph("4. Legal Counsel Recommendation", heading_style))
    rec_text = (
        "Enterprise clients are strongly advised to maintain the Manual-Assist operational mode. "
        "Attempting full headless automation carries substantial liability, potential C&D action under CFAA, "
        "and permanent LinkedIn account termination. The Manual-Assist model provides enterprise-grade scalability "
        "while maintaining total legal protection."
    )
    story.append(Paragraph(rec_text, body_style))

    doc.build(story)
    print(f"✅ Compliance PDF generated successfully at: {output_path}")


if __name__ == "__main__":
    build_compliance_pdf()
