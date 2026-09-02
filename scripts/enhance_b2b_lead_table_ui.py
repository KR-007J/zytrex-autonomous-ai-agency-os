"""Revamp the Lead Directory UI to display Decision Makers, Executive Roles, Direct Emails, Phone Lines, and Rich Dossiers."""

from pathlib import Path
import re

TABLE_ROW_LOGIC = """
            <tr>
              <td>
                <strong style="color: var(--text-heading); font-size: 13px; display: block;">${escapeHtml(l.company_name)}</strong>
                <div style="font-size: 11px; margin-top: 3px;">
                  <a href="${escapeHtml(l.live_url || 'https://' + l.source_domain)}" target="_blank" rel="noopener noreferrer" style="color: #0284C7; text-decoration: none; font-family: var(--font-mono); font-weight: 600;">🌐 ${escapeHtml(l.source_domain)} ↗</a>
                </div>
              </td>
              <td>
                ${getPlatformBadge(l.platform_cms)}
              </td>
              <td>
                <span style="font-size: 12px; font-weight: 600; color: var(--text-heading);">${escapeHtml(l.category)}</span>
              </td>
              <td>
                <span class="badge-loc">📍 ${escapeHtml(l.region)} [${escapeHtml(l.country_code)}]</span>
              </td>
              <td>
                <div style="margin-bottom: 3px;">
                  <span style="font-size: 12px; font-weight: 700; color: var(--text-heading);">👤 ${escapeHtml((l.source || '').replace('Verified B2B Lead — ', '').replace('Verified B2B Dossier — ', ''))}</span>
                </div>
                <div style="font-family: var(--font-mono); font-size: 12px; font-weight: 700; color: #047857;">
                  <a href="mailto:${escapeHtml(l.contact_email || '')}" style="color: #047857; text-decoration: none;">✉️ ${escapeHtml(l.contact_email || 'contact@' + l.source_domain)}</a>
                </div>
                ${l.contact_phone ? `<div style="font-size: 11px; color: var(--text-body); font-family: var(--font-mono); margin-top: 2px;"><a href="tel:${escapeHtml(l.contact_phone)}" style="color: var(--text-body); text-decoration: none;">📞 ${escapeHtml(l.contact_phone)}</a></div>` : ''}
              </td>
              <td>
                ${techs || '<span style="font-size: 11px; color: #94A3B8;">Web Standard</span>'}
              </td>
              <td>
                <span class="badge-score">${l.confidence_score}%</span>
              </td>
              <td>
                <button onclick="inspectGlobalLead(${l.id})" class="zytrex-btn-table">
                  <span>🔍</span> DOSSIER
                </button>
              </td>
            </tr>
"""

TABLE_HEADER_HTML = """
            <tr>
              <th style="width: 20%;">Store / Business</th>
              <th style="width: 12%;">Platform / CMS</th>
              <th style="width: 15%;">Category / Niche</th>
              <th style="width: 13%;">Region / Country</th>
              <th style="width: 20%;">Verified Contact & Decision Maker</th>
              <th style="width: 10%;">Tech Stack</th>
              <th style="width: 5%;">Score</th>
              <th style="width: 5%;">Actions</th>
            </tr>
"""

for filepath in [
    Path("/home/krish/.gemini/antigravity/scratch/leadgen-outreach-agent/src/web/index.html"),
    Path("/home/krish/.gemini/antigravity/scratch/leadgen-outreach-agent/public/index.html")
]:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Update table headers
    content = re.sub(
        r'<th[^>]*>Store / Business</th>[\s\S]*?<th>Actions</th>',
        '<th>Store / Business</th><th>Platform / CMS</th><th>Category / Niche</th><th>Region / Country</th><th>Verified Contact & Decision Maker</th><th>Tech Stack</th><th>Score</th><th>Actions</th>',
        content
    )

    # Update row template in renderGlobalLeadsTable
    content = re.sub(
        r'return `\s*<tr>\s*<td>\s*<strong style="color: var\(--text-heading\); font-size: 13px;">[\s\S]*?<\/tr>\s*`;',
        'return `' + TABLE_ROW_LOGIC.strip() + '`;',
        content
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Enhanced Lead Table in {filepath}")

print("Lead table UI enhancements completed.")
