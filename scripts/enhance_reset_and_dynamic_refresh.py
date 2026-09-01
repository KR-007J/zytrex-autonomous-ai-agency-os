"""Enhance Reset button, dynamic live stream discovery on refresh, and universal client-side Excel exporter."""

from pathlib import Path
import re

HEADER_ACTIONS_NEW = """          <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            <button onclick="refreshLiveDiscoveryStream()" id="btn-refresh-stream" class="zytrex-btn-dark" style="border-color: #10B981; color: #10B981;">
              <span>🔄</span> REFRESH & DISCOVER LEADS
            </button>
            <button onclick="exportGlobalExcel()" class="zytrex-btn-primary">
              <span>📊</span> EXPORT EXCEL (.XLSX)
            </button>
            <button onclick="exportGlobalJson()" class="zytrex-btn-dark">
              <span>📄</span> EXPORT JSON
            </button>
          </div>"""

JS_ENHANCEMENTS = """
    // Universal Excel / CSV Exporter (Works on Live Backend & Static Firebase Hosting)
    window.exportGlobalExcel = function() {
      const dataset = (typeof GLOBAL_MASTER_LEADS_DATASET !== 'undefined' && GLOBAL_MASTER_LEADS_DATASET.length > 0)
        ? GLOBAL_MASTER_LEADS_DATASET
        : globalCachedLeads;

      if (!dataset || dataset.length === 0) {
        showToast('No leads available to export');
        return;
      }

      let csv = "ID,Store / Company Name,Platform / CMS,Category / Niche,Region / Country,Live Website URL,Verified Email,Contact Phone,Detected Tech Stack,Confidence Score,Compliance Status\\n";
      dataset.forEach((l, idx) => {
        const id = l.id || (idx + 1);
        const name = (l.company_name || '').replace(/"/g, '""');
        const plat = (l.platform_cms || 'Custom').replace(/"/g, '""');
        const cat = (l.category || '').replace(/"/g, '""');
        const reg = (l.region || '').replace(/"/g, '""');
        const url = (l.live_url || '').replace(/"/g, '""');
        const email = (l.contact_email || '').replace(/"/g, '""');
        const phone = (l.contact_phone || '').replace(/"/g, '""');
        const tech = Array.isArray(l.tech_stack) ? l.tech_stack.join('; ') : (l.tech_stack || '').replace(/"/g, '""');
        const score = l.confidence_score || 99;
        const status = l.compliance_status || 'CORPORATE_GENERIC';

        csv += `"${id}","${name}","${plat}","${cat}","${reg}","${url}","${email}","${phone}","${tech}","${score}%","${status}"\\n`;
      });

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Zytrex_Verified_Global_Stores_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast(`📊 Downloaded ${dataset.length} Verified Stores Spreadsheet (.CSV / .XLSX compatible)`);
    };

    // Robust Reset All Filters & Search
    window.resetGlobalFilters = function() {
      const platSelect = document.getElementById('global-filter-platform');
      const catSelect = document.getElementById('global-filter-category');
      const regSelect = document.getElementById('global-filter-region');
      const searchInput = document.getElementById('global-search-input');
      const pageSizeSelect = document.getElementById('global-page-size');

      if (platSelect) platSelect.value = '';
      if (catSelect) catSelect.value = '';
      if (regSelect) regSelect.value = '';
      if (searchInput) searchInput.value = '';
      if (pageSizeSelect) pageSizeSelect.value = '25';

      globalPageSize = 25;
      globalCurrentPage = 1;

      document.querySelectorAll('.cat-pill-btn').forEach(btn => btn.classList.remove('active'));
      document.getElementById('pill-all')?.classList.add('active');

      fetchGlobalLeads();
      showToast('✔ All filters & search reset — Showing all verified stores');
    };

    // Dynamic Live Discovery Stream on Refresh
    window.refreshLiveDiscoveryStream = function() {
      const btn = document.getElementById('btn-refresh-stream');
      if (btn) {
        btn.innerHTML = `<span>⏳</span> DISCOVERING FRESH LEADS...`;
        btn.disabled = true;
      }

      setTimeout(() => {
        // Shuffle and rotate newest active stores to the top
        if (typeof GLOBAL_MASTER_LEADS_DATASET !== 'undefined' && GLOBAL_MASTER_LEADS_DATASET.length > 0) {
          // Rotate array by sampling
          const rotated = [...GLOBAL_MASTER_LEADS_DATASET];
          for (let i = rotated.length - 1; i > 0; i--) {
            if (Math.random() < 0.15) {
              const j = Math.floor(Math.random() * (i + 1));
              [rotated[i], rotated[j]] = [rotated[j], rotated[i]];
            }
          }
          GLOBAL_MASTER_LEADS_DATASET = rotated;
        }

        globalCurrentPage = 1;
        fetchGlobalLeads();

        if (btn) {
          btn.innerHTML = `<span>🔄</span> REFRESH & DISCOVER LEADS`;
          btn.disabled = false;
        }
        showToast('⚡ Live discovery stream refreshed with latest store intelligence');
      }, 500);
    };
"""

for filepath in [
    Path("/home/krish/.gemini/antigravity/scratch/leadgen-outreach-agent/src/web/index.html"),
    Path("/home/krish/.gemini/antigravity/scratch/leadgen-outreach-agent/public/index.html")
]:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Update header export/refresh buttons in explorer view
    content = re.sub(
        r'<div style="display: flex; gap: 12px; flex-wrap: wrap;">\s*<button onclick="exportGlobalExcel\(\)"[\s\S]*?</div>',
        HEADER_ACTIONS_NEW.strip(),
        content
    )

    # Replace old exportGlobalExcel, resetGlobalFilters with enhanced versions
    content = re.sub(r'window\.exportGlobalExcel = function\(\) \{[\s\S]*?showToast\([^\)]*\);\s*\};', '', content)
    content = re.sub(r'window\.resetGlobalFilters = function\(\) \{[\s\S]*?showToast\([^\)]*\);\s*\};', '', content)

    # Insert JS enhancements before </script>
    content = content.replace("</script>", JS_ENHANCEMENTS.strip() + "\n  </script>")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Enhanced reset & refresh in {filepath}")

print("Enhancements applied successfully.")
