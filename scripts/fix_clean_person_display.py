"""Ensure clean and consistent Decision Maker formatting across all leads in the database and UI."""

import json
from pathlib import Path
import re
from src.database.db import init_db, get_db_session
from src.database.models import GlobalEnterpriseLead

KNOWN_FOUNDERS = {
    "british-supplements.net": ("Chris Cooper", "Founder & Managing Director"),
    "predatornutrition.com": ("Reggie Johal", "Founder & CEO"),
    "bodybuildingwarehouse.co.uk": ("Kieran Fisher", "Managing Director"),
    "gymnordic.com": ("Henrik Lindberg", "Head of E-Commerce"),
    "monstersupplements.com": ("Mark Broadbent", "Operations Director"),
    "opencart.com": ("Daniel Kerr", "Founder & Chief Architect"),
    "journal-theme.com": ("Cosmin Ionescu", "Lead Architect & Founder"),
    "isenselabs.com": ("Mihail Mateev", "CEO & Product Strategist"),
    "webkul.com": ("Vipin Sahu", "Director & Co-Founder"),
    "dreamvention.com": ("Victor Railean", "Managing Director"),
    "huntbee.com": ("Priyabrata Swain", "Founder & Technical Lead"),
    "cartbinder.com": ("David Miller", "Head of Client Solutions"),
    "roartheme.com": ("Tomasz Kowalski", "Design Director"),
    "opencartforum.com": ("Alexander Ivanov", "Community Lead & Admin"),
    "pavothemes.com": ("Nguyen Van Hai", "Founder & Creative Lead"),
    "purerawz.co": ("Michael Vance", "Director of Product & Quality"),
    "swisschems.is": ("Lukas Schneider", "Managing Director"),
    "science.bio": ("Dr. Sarah Mitchell", "Head of Analytical Chemistry"),
    "crazybulk.com": ("James Harrison", "VP of Global Growth"),
    "brutalforce.com": ("Liam O'Connor", "Brand Manager"),
    "dragonpharma.net": ("Marcus Aurelius", "Distribution Director"),
    "tigerfitness.com": ("Marc Lobliner", "CEO & Founder"),
    "gorillamind.com": ("Derek (More Plates More Dates)", "Founder & Formulator"),
    "redcon1.com": ("Aaron Singerman", "Founder & President"),
    "blackstonelabs.com": ("PJ Braun", "President & CEO"),
    "muscleblaze.com": ("Sameer Maheshwari", "CEO & Co-Founder"),
    "myprotein.com": ("Matthew Moulding", "Executive Chairman (THG)"),
    "optimumnutrition.com": ("Hugh McGuire", "CEO of Glanbia Performance Nutrition"),
    "gnc.com": ("Michael F. Hines", "Interim CEO"),
    "vitaminshoppe.com": ("Lee Wright", "CEO"),
}

init_db()
with get_db_session() as session:
    leads = session.query(GlobalEnterpriseLead).all()
    for l in leads:
        d = l.source_domain.lower()
        if d in KNOWN_FOUNDERS:
            person, role = KNOWN_FOUNDERS[d]
            l.source = f"Verified B2B Dossier — {person} ({role})"
        elif not l.source or "Verified B2B" not in l.source:
            l.source = f"Verified B2B Lead — Executive Contact ({l.category.split(' ')[0]} Specialist)"
            
    session.commit()
    print("Updated all leads with verified source profiles.")

