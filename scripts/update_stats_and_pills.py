"""Update stat counters and quick-pills for 1,051 rich B2B active leads."""

from pathlib import Path
import re

for filepath in [
    Path("/home/krish/.gemini/antigravity/scratch/leadgen-outreach-agent/src/web/index.html"),
    Path("/home/krish/.gemini/antigravity/scratch/leadgen-outreach-agent/public/index.html")
]:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update stat counter
    content = re.sub(
        r'<div id="stat-global-total"[^>]*>[\d,\+]+</div>',
        '<div id="stat-global-total" style="font-size: 28px; font-weight: 700; color: var(--text-heading);">1,051+</div>',
        content
    )

    # 2. Update quick pills ribbon
    NEW_PILLS = """        <!-- Targeted Quick-Filter Ribbon (1,051 Rich B2B Leads with Decision Makers) -->
        <div class="cat-pills-container" id="category-pills-bar">
          <button onclick="selectQuickFilter('', '')" class="cat-pill-btn active" id="pill-all">
            <span>🌐</span> All Real Stores <span class="cat-pill-count" id="pill-cnt-all">1,051+</span>
          </button>
          <button onclick="selectQuickFilter('OpenCart', '')" class="cat-pill-btn" id="pill-opencart" style="border: 1.5px solid #10B981;">
            <span>🛒</span> OpenCart Stores <span class="cat-pill-count" style="background: rgba(16,185,129,0.2); color: #047857;">19</span>
          </button>
          <button onclick="selectQuickFilter('', 'Steroids & Fitness Supplements')" class="cat-pill-btn" id="pill-supplements" style="border: 1.5px solid #EC4899;">
            <span>💊</span> Steroids & Supplements <span class="cat-pill-count" style="background: rgba(236,72,153,0.2); color: #BE185D;">47</span>
          </button>
          <button onclick="selectQuickFilter('WordPress', '')" class="cat-pill-btn" id="pill-wordpress" style="border: 1.5px solid #3B82F6;">
            <span>🌐</span> WordPress / WooCommerce <span class="cat-pill-count" style="background: rgba(59,130,246,0.2); color: #1D4ED8;">24</span>
          </button>
          <button onclick="selectQuickFilter('Shopify', '')" class="cat-pill-btn" id="pill-shopify" style="border: 1.5px solid #8B5CF6;">
            <span>🛍️</span> Shopify Stores <span class="cat-pill-count" style="background: rgba(139,92,246,0.2); color: #7C3AED;">14</span>
          </button>
          <button onclick="selectQuickFilter('', 'Retail & E-Commerce')" class="cat-pill-btn" id="pill-retail">
            <span>🛍️</span> Retail & E-Commerce <span class="cat-pill-count">745</span>
          </button>
          <button onclick="selectQuickFilter('', 'B2B SaaS & Tech')" class="cat-pill-btn" id="pill-saas">
            <span>⚡</span> B2B SaaS & Tech <span class="cat-pill-count">258</span>
          </button>
        </div>"""

    content = re.sub(r'<div class="cat-pills-container" id="category-pills-bar">[\s\S]*?</div>', NEW_PILLS.strip(), content)

    # 3. Update rows per page selector
    NEW_PAGE_SELECT = """<select id="global-page-size" onchange="changeGlobalPageSize(this.value)" style="padding: 4px 8px; font-family: var(--font-display); font-size: 11px; font-weight: 700; border: 1px solid var(--border-light); background: #FFF;">
              <option value="10">10 / page</option>
              <option value="25" selected>25 / page</option>
              <option value="50">50 / page</option>
              <option value="100">100 / page</option>
              <option value="250">250 / page</option>
              <option value="500">500 / page</option>
              <option value="1051">All (1,051) / page</option>
            </select>"""

    content = re.sub(r'<select id="global-page-size"[\s\S]*?</select>', NEW_PAGE_SELECT.strip(), content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Updated {filepath}")

print("All updates applied.")
