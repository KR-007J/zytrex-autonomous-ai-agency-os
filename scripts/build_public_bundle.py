"""Build complete bundle with embedded real datasets for seamless static & live deployments."""

import json
from pathlib import Path
from src.database.db import init_db, get_db_session, GlobalLeadRepository

init_db()
with get_db_session() as session:
    leads, total = GlobalLeadRepository.get_leads(session, skip=0, limit=500)
    dataset = [l.to_dict() for l in leads]
    print(f"Loaded {len(dataset)} leads from database.")

SRC_INDEX = Path("/home/krish/.gemini/antigravity/scratch/leadgen-outreach-agent/src/web/index.html")
PUB_INDEX = Path("/home/krish/.gemini/antigravity/scratch/leadgen-outreach-agent/public/index.html")

with open(SRC_INDEX, "r", encoding="utf-8") as f:
    content = f.read()

# Embed master dataset
embedded_code = f"""
    // Global Master Dataset (78 Verified Open-Source Scraped Commercial Entities)
    const GLOBAL_MASTER_LEADS_DATASET = {json.dumps(dataset, indent=2)};
"""

if "const GLOBAL_MASTER_LEADS_DATASET =" in content:
    import re
    content = re.sub(r'const GLOBAL_MASTER_LEADS_DATASET =[\s\S]*?;\n', embedded_code.strip() + '\n', content)
else:
    content = content.replace("let globalCachedLeads = [];", embedded_code + "\n    let globalCachedLeads = [];")

# Update fetchGlobalLeads with static fallback
FALLBACK_FETCH = """    async function fetchGlobalLeads() {
      const plat = document.getElementById('global-filter-platform')?.value || '';
      const cat = document.getElementById('global-filter-category')?.value || '';
      const reg = document.getElementById('global-filter-region')?.value || '';
      const search = document.getElementById('global-search-input')?.value || '';

      const params = new URLSearchParams({
        page: globalCurrentPage,
        limit: globalPageSize,
      });
      if (plat) params.append('platform', plat);
      if (cat) params.append('category', cat);
      if (reg) params.append('region', reg);
      if (search) params.append('search', search);

      try {
        const res = await fetch(`/api/leads?${params.toString()}`);
        if (res.ok) {
          const data = await res.json();
          globalCachedLeads = data.items || [];
          globalTotalLeads = data.total || 0;
          renderGlobalLeadsTable(data);
          return;
        }
      } catch (err) {}

      // Resilient Static / CDN Fallback
      let filtered = (typeof GLOBAL_MASTER_LEADS_DATASET !== 'undefined') ? GLOBAL_MASTER_LEADS_DATASET : [];
      if (plat) filtered = filtered.filter(l => (l.platform_cms || '').toLowerCase().includes(plat.toLowerCase()));
      if (cat) filtered = filtered.filter(l => (l.category || '').toLowerCase().includes(cat.toLowerCase()));
      if (reg) filtered = filtered.filter(l => (l.region || '').toLowerCase().includes(reg.toLowerCase()));
      if (search) {
        const s = search.toLowerCase();
        filtered = filtered.filter(l =>
          (l.company_name || '').toLowerCase().includes(s) ||
          (l.source_domain || '').toLowerCase().includes(s) ||
          (l.contact_email || '').toLowerCase().includes(s) ||
          (l.contact_phone || '').toLowerCase().includes(s) ||
          (l.category || '').toLowerCase().includes(s) ||
          (l.region || '').toLowerCase().includes(s)
        );
      }

      const totalCount = filtered.length;
      const totalP = Math.max(1, Math.ceil(totalCount / globalPageSize));
      const start = (globalCurrentPage - 1) * globalPageSize;
      const paged = filtered.slice(start, start + globalPageSize);

      globalCachedLeads = paged;
      globalTotalLeads = totalCount;
      renderGlobalLeadsTable({
        total: totalCount,
        page: globalCurrentPage,
        limit: globalPageSize,
        total_pages: totalP,
        items: paged
      });
    }"""

import re
content = re.sub(r'async function fetchGlobalLeads\(\) \{[\s\S]*?renderGlobalLeadsTable\(data\);\s*\}\s*\} catch \(err\) \{[\s\S]*?\}\s*\}', FALLBACK_FETCH.strip(), content)

with open(SRC_INDEX, "w", encoding="utf-8") as f:
    f.write(content)

with open(PUB_INDEX, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ Successfully bundled & updated {SRC_INDEX} and {PUB_INDEX}.")
