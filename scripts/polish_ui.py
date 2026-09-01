"""Polish and enhance Enterprise UI components, tech badges, and keyboard shortcuts."""

from pathlib import Path
import re

INDEX_PATH = Path("/home/krish/.gemini/antigravity/scratch/leadgen-outreach-agent/src/web/index.html")

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Tech badge CSS & Category pill styles
POLISH_CSS = """
    /* Tech Stack Badges */
    .tech-pill {
      display: inline-flex;
      align-items: center;
      padding: 3px 8px;
      font-size: 10px;
      font-weight: 700;
      border-radius: 3px;
      margin-right: 4px;
      margin-bottom: 2px;
      letter-spacing: 0.04em;
      white-space: nowrap;
      font-family: var(--font-mono);
    }
    .tech-react { background: rgba(56, 189, 248, 0.12); border: 1px solid #38BDF8; color: #0284C7; }
    .tech-nextjs { background: rgba(15, 23, 42, 0.08); border: 1px solid #0F172A; color: #0F172A; }
    .tech-aws { background: rgba(245, 158, 11, 0.12); border: 1px solid #F59E0B; color: #D97706; }
    .tech-stripe { background: rgba(139, 92, 246, 0.12); border: 1px solid #8B5CF6; color: #7C3AED; }
    .tech-shopify { background: rgba(16, 185, 129, 0.12); border: 1px solid #10B981; color: #059669; }
    .tech-cloudflare { background: rgba(249, 115, 22, 0.12); border: 1px solid #F97316; color: #EA580C; }
    .tech-default { background: rgba(100, 116, 139, 0.1); border: 1px solid #94A3B8; color: #475569; }

    /* Category Pill Quick Filters */
    .cat-pills-container {
      display: flex;
      align-items: center;
      gap: 8px;
      overflow-x: auto;
      padding-bottom: 12px;
      margin-bottom: 20px;
      scrollbar-width: thin;
    }
    .cat-pill-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 14px;
      font-size: 11px;
      font-weight: 700;
      background: var(--bg-surface);
      border: 1px solid var(--border-light);
      color: var(--text-nav);
      border-radius: 20px;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.2s ease;
      user-select: none;
    }
    .cat-pill-btn:hover {
      border-color: var(--accent-cyan-border);
      color: #000;
      transform: translateY(-1px);
    }
    .cat-pill-btn.active {
      background: #0F172A;
      border-color: #0F172A;
      color: #38BDF8;
      box-shadow: 0 4px 12px rgba(15, 23, 42, 0.2);
    }
    .cat-pill-count {
      padding: 1px 6px;
      background: rgba(0, 0, 0, 0.06);
      border-radius: 10px;
      font-size: 9px;
      font-family: var(--font-mono);
    }
    .cat-pill-btn.active .cat-pill-count {
      background: rgba(56, 189, 248, 0.2);
      color: #38BDF8;
    }
"""

if ".tech-react" not in content:
    content = content.replace("/* Toast */", POLISH_CSS + "\n    /* Toast */")
    print("✅ Injected Polish CSS.")

# 2. Add Category Pills Bar above the Filter Box in page-explorer
PILLS_HTML = """
        <!-- Category Quick-Filter Ribbon -->
        <div class="cat-pills-container" id="category-pills-bar">
          <button onclick="selectCategoryPill('')" class="cat-pill-btn active" id="cat-pill-all">
            <span>🌐</span> All Categories <span class="cat-pill-count" id="pill-cnt-all">49</span>
          </button>
          <button onclick="selectCategoryPill('B2B SaaS & Tech')" class="cat-pill-btn" id="cat-pill-saas">
            <span>⚡</span> B2B SaaS & Tech <span class="cat-pill-count">10</span>
          </button>
          <button onclick="selectCategoryPill('Retail & E-Commerce')" class="cat-pill-btn" id="cat-pill-retail">
            <span>🛍️</span> Retail & E-Commerce <span class="cat-pill-count">7</span>
          </button>
          <button onclick="selectCategoryPill('Healthcare & Medical')" class="cat-pill-btn" id="cat-pill-health">
            <span>🏥</span> Healthcare <span class="cat-pill-count">5</span>
          </button>
          <button onclick="selectCategoryPill('Financial Services & Banking')" class="cat-pill-btn" id="cat-pill-finance">
            <span>💳</span> FinTech & Banking <span class="cat-pill-count">5</span>
          </button>
          <button onclick="selectCategoryPill('Logistics & Supply Chain')" class="cat-pill-btn" id="cat-pill-logistics">
            <span>📦</span> Logistics <span class="cat-pill-count">4</span>
          </button>
          <button onclick="selectCategoryPill('Legal & Professional Services')" class="cat-pill-btn" id="cat-pill-legal">
            <span>⚖️</span> Legal & Advisory <span class="cat-pill-count">3</span>
          </button>
          <button onclick="selectCategoryPill('Manufacturing & Industrial')" class="cat-pill-btn" id="cat-pill-manufacturing">
            <span>🏭</span> Manufacturing <span class="cat-pill-count">3</span>
          </button>
          <button onclick="selectCategoryPill('Education & EdTech')" class="cat-pill-btn" id="cat-pill-education">
            <span>🎓</span> EdTech <span class="cat-pill-count">3</span>
          </button>
        </div>
"""

if 'id="category-pills-bar"' not in content and '<!-- Multi-Faceted Filter Control Bar -->' in content:
    content = content.replace('<!-- Multi-Faceted Filter Control Bar -->', PILLS_HTML + '\n        <!-- Multi-Faceted Filter Control Bar -->')
    print("✅ Injected Category Pills HTML.")

# 3. Update renderGlobalLeadsTable to use colored tech badges and pill sync
NEW_TECH_RENDER = """
    function getTechBadgeClass(tech) {
      const t = tech.toLowerCase();
      if (t.includes('react')) return 'tech-react';
      if (t.includes('next')) return 'tech-nextjs';
      if (t.includes('aws') || t.includes('cloud')) return 'tech-aws';
      if (t.includes('stripe')) return 'tech-stripe';
      if (t.includes('shopify')) return 'tech-shopify';
      if (t.includes('cloudflare')) return 'tech-cloudflare';
      return 'tech-default';
    }

    window.selectCategoryPill = function(cat) {
      const select = document.getElementById('global-filter-category');
      if (select) select.value = cat;

      document.querySelectorAll('.cat-pill-btn').forEach(btn => btn.classList.remove('active'));
      if (!cat) {
        document.getElementById('cat-pill-all')?.classList.add('active');
      } else {
        const found = Array.from(document.querySelectorAll('.cat-pill-btn')).find(b => b.innerText.includes(cat.split(' ')[0]));
        if (found) found.classList.add('active');
      }

      applyGlobalFilters();
    };

    // Global Keyboard Shortcut (Ctrl+K or / to search)
    window.addEventListener('keydown', (e) => {
      if ((e.key === '/' || (e.ctrlKey && e.key === 'k')) && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
        e.preventDefault();
        const input = document.getElementById('global-search-input');
        if (input) {
          input.focus();
          input.select();
          showToast('Search mode active');
        }
      }
    });
"""

if "function getTechBadgeClass" not in content:
    content = content.replace("window.goToGlobalPage = function", NEW_TECH_RENDER + "\n    window.goToGlobalPage = function")
    print("✅ Injected JS Enhancements.")

# 4. Update table tech rendering loop in renderGlobalLeadsTable
old_tech_map = "const techs = (l.tech_stack || []).slice(0, 3).map(t => `<span class=\"badge-opp\" style=\"font-size: 10px; margin-right: 4px;\">${escapeHtml(t)}</span>`).join('');"
new_tech_map = "const techs = (l.tech_stack || []).slice(0, 3).map(t => `<span class=\"tech-pill ${getTechBadgeClass(t)}\">${escapeHtml(t)}</span>`).join('');"

if old_tech_map in content:
    content = content.replace(old_tech_map, new_tech_map)
    print("✅ Updated Tech Badge markup.")

# Write modified file
with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Polish update complete.")
