"""Embed SQLite leads database directly into static frontend bundle for Firebase Hosting."""

import json
from pathlib import Path
import re
from src.database.db import get_db_session, GlobalLeadRepository

with get_db_session() as session:
    leads, total = GlobalLeadRepository.get_leads(session, limit=2000)
    print(f"Loaded {total} leads from database.")

    raw_list = [l.to_dict() for l in leads]
    embedded_code = f"const GLOBAL_MASTER_LEADS_DATASET = {json.dumps(raw_list, indent=2)};"

for filepath in [
    Path("/home/krish/.gemini/antigravity/scratch/leadgen-outreach-agent/src/web/index.html"),
    Path("/home/krish/.gemini/antigravity/scratch/leadgen-outreach-agent/public/index.html")
]:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Safely replace GLOBAL_MASTER_LEADS_DATASET without regex escape errors
    start_marker = "const GLOBAL_MASTER_LEADS_DATASET ="
    start_pos = content.find(start_marker)
    if start_pos != -1:
        end_pos = content.find("];", start_pos)
        if end_pos != -1:
            end_pos += 2
            content = content[:start_pos] + embedded_code + content[end_pos:]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print(f"✅ Successfully bundled & updated index.html files with {total} leads.")
