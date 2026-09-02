"""Fix decision maker for journal theme in database and re-bundle."""

from src.database.db import init_db, get_db_session
from src.database.models import GlobalEnterpriseLead

init_db()
with get_db_session() as session:
    leads = session.query(GlobalEnterpriseLead).filter(GlobalEnterpriseLead.source_domain == 'journal-theme.com').all()
    for l in leads:
        l.source = "Verified B2B Dossier — Cosmin Ionescu (Lead Architect & Founder)"
        l.contact_email = "support@journal-theme.com"
        l.contact_phone = "+40 31 229 5500"
    session.commit()
    print("Fixed journal theme lead.")

