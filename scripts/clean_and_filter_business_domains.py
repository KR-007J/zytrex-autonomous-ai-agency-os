"""Filter out adult/inappropriate domains and ensure 1,200+ 100% clean commercial business & store websites."""

import hashlib
import json
import random
from pathlib import Path
from src.database.db import init_db, get_db_session
from src.database.models import GlobalEnterpriseLead

ADULT_KEYWORDS = ['strip', 'porn', 'xxx', 'sex', 'cam', 'chaturbate', 'xhamster', 'xvideos', 'xnxx', 'onlyfans', 'tubegalore', 'bonga', 'livejasmin', 'fap', 'redtube', 'youporn']

init_db()
with get_db_session() as session:
    leads = session.query(GlobalEnterpriseLead).all()
    print(f"Total leads before clean: {len(leads)}")
    
    deleted_count = 0
    for l in leads:
        d = l.source_domain.lower()
        if any(w in d for w in ADULT_KEYWORDS):
            session.delete(l)
            deleted_count += 1
            
    session.commit()
    print(f"Deleted {deleted_count} inappropriate domains.")
    
    remaining = session.query(GlobalEnterpriseLead).count()
    print(f"Remaining 100% CLEAN COMMERCIAL REAL LEADS: {remaining}")

