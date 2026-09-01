"""Fix renderGlobalLeadsTable call in 24/7 stream and ensure proper stats display."""

from pathlib import Path
import re

for filepath in [
    Path("/home/krish/.gemini/antigravity/scratch/leadgen-outreach-agent/src/web/index.html"),
    Path("/home/krish/.gemini/antigravity/scratch/leadgen-outreach-agent/public/index.html")
]:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Fix ingestSingleAutonomousLead to call fetchGlobalLeads()
    content = re.sub(
        r'if \(globalCurrentPage === 1 && !searchVal && !platVal\) \{[\s\S]*?renderGlobalLeadsTable\(GLOBAL_MASTER_LEADS_DATASET\.slice\(0, globalPageSize\), globalTotalLeads\);\s*\}',
        'if (globalCurrentPage === 1 && !searchVal && !platVal) { fetchGlobalLeads(); }',
        content
    )

    # 2. Fix stat-global-total update in renderGlobalLeadsTable
    content = re.sub(
        r"if \(document\.getElementById\('stat-global-total'\)\) document\.getElementById\('stat-global-total'\)\.innerText = total;",
        "if (document.getElementById('stat-global-total')) document.getElementById('stat-global-total').innerText = (typeof GLOBAL_MASTER_LEADS_DATASET !== 'undefined' ? GLOBAL_MASTER_LEADS_DATASET.length : total).toLocaleString() + '+';",
        content
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Fixed {filepath}")

print("All render fixes applied.")
