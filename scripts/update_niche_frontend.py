"""Upgrade index.html with Platform/CMS filters, OpenCart/Supplements/WordPress quick pills and phone display."""

from pathlib import Path
import re

INDEX_PATH = Path("/home/krish/.gemini/antigravity/scratch/leadgen-outreach-agent/src/web/index.html")

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Platform CSS badges
PLATFORM_CSS = """
    .platform-badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 8px;
      font-size: 10px;
      font-weight: 700;
      border-radius: 4px;
      font-family: var(--font-mono);
      white-space: nowrap;
    }
    .platform-opencart {
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid #10B981;
      color: #047857;
    }
    .platform-wordpress {
      background: rgba(59, 130, 246, 0.12);
      border: 1px solid #3B82F6;
      color: #1D4ED8;
    }
    .platform-shopify {
      background: rgba(139, 92, 246, 0.12);
      border: 1px solid #8B5CF6;
      color: #7C3AED;
    }
    .platform-custom {
      background: rgba(100, 116, 139, 0.12);
      border: 1px solid #94A3B8;
      color: #334155;
    }
"""

if ".platform-opencart" not in content:
    content = content.replace("/* Tech Stack Badges */", PLATFORM_CSS + "\n    /* Tech Stack Badges */")
    print("✅ Injected Platform Badge CSS.")

# 2. Replace Category Pills with Client-Targeted Ribbon
NEW_PILLS_HTML = """
        <!-- Targeted Quick-Filter Ribbon (Client Specific: OpenCart, Steroids/Supplements & WordPress) -->
        <div class="cat-pills-container" id="category-pills-bar">
          <button onclick="selectQuickFilter('', '')" class="cat-pill-btn active" id="pill-all">
            <span>🌐</span> All Leads <span class="cat-pill-count" id="pill-cnt-all">78</span>
          </button>
          <button onclick="selectQuickFilter('OpenCart', '')" class="cat-pill-btn" id="pill-opencart" style="border: 1.5px solid #10B981;">
            <span>🛒</span> OpenCart Stores <span class="cat-pill-count" style="background: rgba(16,185,129,0.2); color: #047857;">12</span>
          </button>
          <button onclick="selectQuickFilter('', 'Steroids & Fitness Supplements')" class="cat-pill-btn" id="pill-supplements" style="border: 1.5px solid #EC4899;">
            <span>💊</span> Steroids & Supplements <span class="cat-pill-count" style="background: rgba(236,72,153,0.2); color: #BE185D;">15</span>
          </button>
          <button onclick="selectQuickFilter('WordPress', '')" class="cat-pill-btn" id="pill-wordpress" style="border: 1.5px solid #3B82F6;">
            <span>🌐</span> WordPress / WooCommerce <span class="cat-pill-count" style="background: rgba(59,130,246,0.2); color: #1D4ED8;">13</span>
          </button>
          <button onclick="selectQuickFilter('', 'B2B SaaS & Tech')" class="cat-pill-btn" id="pill-saas">
            <span>⚡</span> B2B SaaS & Tech <span class="cat-pill-count">18</span>
          </button>
          <button onclick="selectQuickFilter('', 'Retail & E-Commerce')" class="cat-pill-btn" id="pill-retail">
            <span>🛍️</span> Retail & E-Commerce <span class="cat-pill-count">13</span>
          </button>
          <button onclick="selectQuickFilter('Shopify', '')" class="cat-pill-btn" id="pill-shopify">
            <span>🛍️</span> Shopify Stores <span class="cat-pill-count">3</span>
          </button>
        </div>
"""

# Replace old pills container
content = re.sub(r'<div class="cat-pills-container" id="category-pills-bar">[\s\S]*?</div>', NEW_PILLS_HTML.strip(), content)
print("✅ Replaced Quick Pills Ribbon.")

# 3. Add Platform dropdown to Filter Bar
OLD_FILTER_ROW = """            <!-- Category Filter -->
            <div>
              <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-body); margin-bottom: 6px; letter-spacing: 0.05em;">CATEGORY / INDUSTRY</label>
              <select id="global-filter-category" onchange="applyGlobalFilters()" style="width: 100%; padding: 10px 12px; font-family: var(--font-display); font-size: 13px; font-weight: 600; border: 1px solid var(--border-light); background: #FFF; color: var(--text-heading); outline: none;">
                <option value="">All Categories (12 Verticals)</option>
                <option value="B2B SaaS & Tech">B2B SaaS & Tech</option>
                <option value="Retail & E-Commerce">Retail & E-Commerce</option>
                <option value="Healthcare & Medical">Healthcare & Medical</option>
                <option value="Financial Services & Banking">Financial Services & Banking</option>
                <option value="Logistics & Supply Chain">Logistics & Supply Chain</option>
                <option value="Legal & Professional Services">Legal & Professional Services</option>
                <option value="Real Estate & Property">Real Estate & Property</option>
                <option value="Manufacturing & Industrial">Manufacturing & Industrial</option>
                <option value="Hospitality & Food Service">Hospitality & Food Service</option>
                <option value="Education & EdTech">Education & EdTech</option>
                <option value="Media, Marketing & Agency">Media, Marketing & Agency</option>
                <option value="Construction & Engineering">Construction & Engineering</option>
              </select>
            </div>"""

NEW_FILTER_ROW = """            <!-- Platform / CMS Filter -->
            <div>
              <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-body); margin-bottom: 6px; letter-spacing: 0.05em;">PLATFORM / CMS</label>
              <select id="global-filter-platform" onchange="applyGlobalFilters()" style="width: 100%; padding: 10px 12px; font-family: var(--font-display); font-size: 13px; font-weight: 600; border: 1px solid var(--border-light); background: #FFF; color: var(--text-heading); outline: none;">
                <option value="">All Platforms & CMS</option>
                <option value="OpenCart">🛒 OpenCart Stores</option>
                <option value="WordPress">🌐 WordPress / WooCommerce</option>
                <option value="Shopify">🛍️ Shopify Stores</option>
                <option value="Custom">⚡ Custom / Next.js</option>
              </select>
            </div>

            <!-- Category / Niche Filter -->
            <div>
              <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-body); margin-bottom: 6px; letter-spacing: 0.05em;">CATEGORY / NICHE</label>
              <select id="global-filter-category" onchange="applyGlobalFilters()" style="width: 100%; padding: 10px 12px; font-family: var(--font-display); font-size: 13px; font-weight: 600; border: 1px solid var(--border-light); background: #FFF; color: var(--text-heading); outline: none;">
                <option value="">All Categories & Niches</option>
                <option value="Steroids & Fitness Supplements">💊 Steroids & Fitness Supplements</option>
                <option value="Retail & E-Commerce">🛍️ Retail & E-Commerce</option>
                <option value="B2B SaaS & Tech">⚡ B2B SaaS & Tech</option>
                <option value="Healthcare & Medical">🏥 Healthcare & Medical</option>
                <option value="Financial Services & Banking">💳 Financial Services & Banking</option>
                <option value="Logistics & Supply Chain">📦 Logistics & Supply Chain</option>
                <option value="Legal & Professional Services">⚖️ Legal & Professional Services</option>
                <option value="Manufacturing & Industrial">🏭 Manufacturing & Industrial</option>
                <option value="Education & EdTech">🎓 Education & EdTech</option>
                <option value="Hospitality & Food Service">🍽️ Hospitality & Food</option>
                <option value="Media, Marketing & Agency">📢 Media & Marketing</option>
                <option value="Real Estate & Property">🏢 Real Estate & Property</option>
              </select>
            </div>"""

if OLD_FILTER_ROW in content:
    content = content.replace(OLD_FILTER_ROW, NEW_FILTER_ROW)
    print("✅ Injected Platform Filter Dropdown.")

# 4. Update Table Headers to include Platform
OLD_TH = """                <th style="padding: 12px 14px;">Company / Business</th>
                <th style="padding: 12px 14px;">Category</th>
                <th style="padding: 12px 14px;">Region / Country</th>
                <th style="padding: 12px 14px;">Verified Contact</th>
                <th style="padding: 12px 14px;">Detected Tech Stack</th>
                <th style="padding: 12px 14px;">Score</th>
                <th style="padding: 12px 14px;">Actions</th>"""

NEW_TH = """                <th style="padding: 12px 14px;">Store / Business</th>
                <th style="padding: 12px 14px;">Platform / CMS</th>
                <th style="padding: 12px 14px;">Category / Niche</th>
                <th style="padding: 12px 14px;">Region / Country</th>
                <th style="padding: 12px 14px;">Verified Contact</th>
                <th style="padding: 12px 14px;">Detected Tech Stack</th>
                <th style="padding: 12px 14px;">Score</th>
                <th style="padding: 12px 14px;">Actions</th>"""

if OLD_TH in content:
    content = content.replace(OLD_TH, NEW_TH)
    print("✅ Injected Platform Table Header.")

# 5. Update fetchGlobalLeads to pass platform parameter
OLD_FETCH = "const url = `/api/leads?page=${globalCurrentPage}&limit=${globalPageLimit}&category=${encodeURIComponent(cat)}&region=${encodeURIComponent(reg)}&search=${encodeURIComponent(search)}`;"
NEW_FETCH = """const plat = document.getElementById('global-filter-platform')?.value || '';
      const url = `/api/leads?page=${globalCurrentPage}&limit=${globalPageLimit}&category=${encodeURIComponent(cat)}&region=${encodeURIComponent(reg)}&platform=${encodeURIComponent(plat)}&search=${encodeURIComponent(search)}`;"""

if OLD_FETCH in content:
    content = content.replace(OLD_FETCH, NEW_FETCH)
    print("✅ Injected Platform URL Param in fetchGlobalLeads.")

# 6. Update selectQuickFilter JS function
NEW_JS_HELPERS = """
    function getPlatformBadge(platform) {
      const p = (platform || 'Custom').toLowerCase();
      if (p.includes('opencart')) return `<span class="platform-badge platform-opencart">🛒 OpenCart</span>`;
      if (p.includes('wordpress')) return `<span class="platform-badge platform-wordpress">🌐 WordPress</span>`;
      if (p.includes('shopify')) return `<span class="platform-badge platform-shopify">🛍️ Shopify</span>`;
      return `<span class="platform-badge platform-custom">⚡ Custom</span>`;
    }

    window.selectQuickFilter = function(platform, category) {
      const platSelect = document.getElementById('global-filter-platform');
      const catSelect = document.getElementById('global-filter-category');
      if (platSelect) platSelect.value = platform;
      if (catSelect) catSelect.value = category;

      document.querySelectorAll('.cat-pill-btn').forEach(btn => btn.classList.remove('active'));
      if (!platform && !category) {
        document.getElementById('pill-all')?.classList.add('active');
      } else if (platform === 'OpenCart') {
        document.getElementById('pill-opencart')?.classList.add('active');
      } else if (category === 'Steroids & Fitness Supplements') {
        document.getElementById('pill-supplements')?.classList.add('active');
      } else if (platform === 'WordPress') {
        document.getElementById('pill-wordpress')?.classList.add('active');
      } else if (category === 'B2B SaaS & Tech') {
        document.getElementById('pill-saas')?.classList.add('active');
      } else if (category === 'Retail & E-Commerce') {
        document.getElementById('pill-retail')?.classList.add('active');
      } else if (platform === 'Shopify') {
        document.getElementById('pill-shopify')?.classList.add('active');
      }

      applyGlobalFilters();
    };
"""

if "function getPlatformBadge" not in content:
    content = content.replace("function getTechBadgeClass", NEW_JS_HELPERS + "\n    function getTechBadgeClass")
    print("✅ Injected Quick Filter & Platform Badge JS.")

# 7. Update renderGlobalLeadsTable row HTML
OLD_ROW_HTML = """              <td>
                <strong style="color: var(--text-heading); font-size: 13px;">${escapeHtml(l.company_name)}</strong>
                <div style="font-size: 11px; margin-top: 2px;">
                  <a href="${escapeHtml(l.live_url || 'https://' + l.source_domain)}" target="_blank" style="color: #0284C7; text-decoration: none; font-family: var(--font-mono);">${escapeHtml(l.source_domain)} ↗</a>
                </div>
              </td>
              <td>${escapeHtml(l.category)}</td>
              <td><span class="badge-loc">📍 ${escapeHtml(l.region)} [${escapeHtml(l.country_code)}]</span></td>
              <td>
                <div style="font-family: var(--font-mono); font-size: 12px; font-weight: 700; color: #047857;">${escapeHtml(l.contact_email || 'Verified In Public Index')}</div>
                ${l.contact_phone ? `<div style="font-size: 11px; color: var(--text-body); font-family: var(--font-mono); margin-top: 2px;">${escapeHtml(l.contact_phone)}</div>` : ''}
              </td>
              <td>${techs || '<span style="color: var(--text-body); font-size: 11px;">Standard Web</span>'}</td>
              <td><span class="badge-score">${l.confidence_score}%</span></td>
              <td>
                <button onclick="inspectGlobalLead(${l.id})" class="zytrex-btn-table">
                  <span>🔍</span> INSPECT
                </button>
              </td>"""

NEW_ROW_HTML = """              <td>
                <strong style="color: var(--text-heading); font-size: 13px;">${escapeHtml(l.company_name)}</strong>
                <div style="font-size: 11px; margin-top: 2px;">
                  <a href="${escapeHtml(l.live_url || 'https://' + l.source_domain)}" target="_blank" style="color: #0284C7; text-decoration: none; font-family: var(--font-mono);">${escapeHtml(l.source_domain)} ↗</a>
                </div>
              </td>
              <td>${getPlatformBadge(l.platform_cms)}</td>
              <td><span style="font-size: 12px; font-weight: 600;">${escapeHtml(l.category)}</span></td>
              <td><span class="badge-loc">📍 ${escapeHtml(l.region)} [${escapeHtml(l.country_code)}]</span></td>
              <td>
                <div style="font-family: var(--font-mono); font-size: 12px; font-weight: 700; color: #047857;">
                  <a href="mailto:${escapeHtml(l.contact_email || '')}" style="color: #047857; text-decoration: none;">✉️ ${escapeHtml(l.contact_email || 'contact@' + l.source_domain)}</a>
                </div>
                ${l.contact_phone ? `<div style="font-size: 11px; color: var(--text-body); font-family: var(--font-mono); margin-top: 2px;"><a href="tel:${escapeHtml(l.contact_phone)}" style="color: var(--text-body); text-decoration: none;">📞 ${escapeHtml(l.contact_phone)}</a></div>` : ''}
              </td>
              <td>${techs || '<span style="color: var(--text-body); font-size: 11px;">Standard Web</span>'}</td>
              <td><span class="badge-score">${l.confidence_score}%</span></td>
              <td>
                <button onclick="inspectGlobalLead(${l.id})" class="zytrex-btn-table">
                  <span>🔍</span> INSPECT
                </button>
              </td>"""

if OLD_ROW_HTML in content:
    content = content.replace(OLD_ROW_HTML, NEW_ROW_HTML)
    print("✅ Injected Platform Row HTML.")

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Target Niche UI Update Complete!")
