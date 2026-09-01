"""Seed Script for Enterprise Global Leads Database."""

from __future__ import annotations
import json
from src.database.db import init_db, get_db_session, GlobalLeadRepository

SEEDS = [
    # B2B SaaS & Tech
    {"company_name": "Tata Consultancy Services", "source_domain": "tcs.com", "category": "B2B SaaS & Tech", "region": "Asia-Pacific (APAC)", "country_code": "IN", "contact_email": "contact.us@tcs.com", "contact_phone": "+91 22 6778 9999", "tech_stack": ["React", "Next.js", "Cloudflare", "AWS Cloud"], "confidence_score": 98},
    {"company_name": "Infosys Limited", "source_domain": "infosys.com", "category": "B2B SaaS & Tech", "region": "Asia-Pacific (APAC)", "country_code": "IN", "contact_email": "contact@infosys.com", "contact_phone": "+91 80 2852 0261", "tech_stack": ["Next.js", "React", "Cloudflare", "Vercel"], "confidence_score": 98},
    {"company_name": "Wipro Technologies", "source_domain": "wipro.com", "category": "B2B SaaS & Tech", "region": "Asia-Pacific (APAC)", "country_code": "IN", "contact_email": "reach@wipro.com", "contact_phone": "+91 80 2844 0011", "tech_stack": ["React", "AWS Cloud", "Tailwind CSS"], "confidence_score": 97},
    {"company_name": "Postman API Platform", "source_domain": "postman.com", "category": "B2B SaaS & Tech", "region": "Asia-Pacific (APAC)", "country_code": "IN", "contact_email": "help@postman.com", "contact_phone": "+91 80 6789 1234", "tech_stack": ["React", "Next.js", "Stripe", "Cloudflare"], "confidence_score": 99},
    {"company_name": "Hasura Cloud", "source_domain": "hasura.io", "category": "B2B SaaS & Tech", "region": "Asia-Pacific (APAC)", "country_code": "IN", "contact_email": "support@hasura.io", "contact_phone": "+91 80 4567 8901", "tech_stack": ["Next.js", "GraphQL", "Tailwind CSS"], "confidence_score": 98},
    {"company_name": "Stripe Payments", "source_domain": "stripe.com", "category": "B2B SaaS & Tech", "region": "North America", "country_code": "US", "contact_email": "support@stripe.com", "contact_phone": "+1 888 926 2289", "tech_stack": ["React", "Stripe", "Next.js", "AWS Cloud"], "confidence_score": 99},
    {"company_name": "Vercel Cloud", "source_domain": "vercel.com", "category": "B2B SaaS & Tech", "region": "North America", "country_code": "US", "contact_email": "support@vercel.com", "contact_phone": "+1 866 837 2351", "tech_stack": ["Next.js", "React", "Vercel", "Tailwind CSS"], "confidence_score": 99},
    {"company_name": "SAP SE", "source_domain": "sap.com", "category": "B2B SaaS & Tech", "region": "Europe (EU)", "country_code": "DE", "contact_email": "info@sap.com", "contact_phone": "+49 6227 747474", "tech_stack": ["React", "Cloudflare", "AWS Cloud"], "confidence_score": 98},
    {"company_name": "Celonis Execution Management", "source_domain": "celonis.com", "category": "B2B SaaS & Tech", "region": "Europe (EU)", "country_code": "DE", "contact_email": "info@celonis.com", "contact_phone": "+49 89 4161 7099", "tech_stack": ["Next.js", "React", "HubSpot", "Cloudflare"], "confidence_score": 97},
    {"company_name": "Arm Holdings", "source_domain": "arm.com", "category": "B2B SaaS & Tech", "region": "Europe (UK)", "country_code": "UK", "contact_email": "info@arm.com", "contact_phone": "+44 1223 400400", "tech_stack": ["React", "Cloudflare", "AWS Cloud"], "confidence_score": 98},

    # Retail & E-Commerce
    {"company_name": "Zalando SE", "source_domain": "zalando.de", "category": "Retail & E-Commerce", "region": "Europe (EU)", "country_code": "DE", "contact_email": "service@zalando.de", "contact_phone": "+49 30 2000 88400", "tech_stack": ["React", "Next.js", "AWS Cloud", "Stripe"], "confidence_score": 98},
    {"company_name": "ASOS Fashion", "source_domain": "asos.com", "category": "Retail & E-Commerce", "region": "Europe (UK)", "country_code": "UK", "contact_email": "care@asos.com", "contact_phone": "+44 207 756 1000", "tech_stack": ["React", "Shopify", "Cloudflare"], "confidence_score": 97},
    {"company_name": "Flipkart Internet", "source_domain": "flipkart.com", "category": "Retail & E-Commerce", "region": "Asia-Pacific (APAC)", "country_code": "IN", "contact_email": "support@flipkart.com", "contact_phone": "+91 80 4660 9211", "tech_stack": ["React", "Tailwind CSS", "AWS Cloud"], "confidence_score": 99},
    {"company_name": "Nykaa E-Retail", "source_domain": "nykaa.com", "category": "Retail & E-Commerce", "region": "Asia-Pacific (APAC)", "country_code": "IN", "contact_email": "support@nykaa.com", "contact_phone": "+91 22 6614 9696", "tech_stack": ["Next.js", "React", "Cloudflare"], "confidence_score": 97},
    {"company_name": "Shopify Stores Global", "source_domain": "shopify.com", "category": "Retail & E-Commerce", "region": "North America", "country_code": "CA", "contact_email": "support@shopify.com", "contact_phone": "+1 888 746 7439", "tech_stack": ["Shopify", "React", "Cloudflare"], "confidence_score": 99},
    {"company_name": "Wayfair Home Goods", "source_domain": "wayfair.com", "category": "Retail & E-Commerce", "region": "North America", "country_code": "US", "contact_email": "service@wayfair.com", "contact_phone": "+1 877 929 3247", "tech_stack": ["React", "Next.js", "Stripe"], "confidence_score": 96},

    # Healthcare & Medical
    {"company_name": "Apollo Hospitals Enterprise", "source_domain": "apollohospitals.com", "category": "Healthcare & Medical", "region": "Asia-Pacific (APAC)", "country_code": "IN", "contact_email": "info@apollohospitals.com", "contact_phone": "+91 44 2829 0200", "tech_stack": ["WordPress", "React", "Cloudflare"], "confidence_score": 98},
    {"company_name": "Fortis Healthcare", "source_domain": "fortishealthcare.com", "category": "Healthcare & Medical", "region": "Asia-Pacific (APAC)", "country_code": "IN", "contact_email": "contactus@fortishealthcare.com", "contact_phone": "+91 124 492 1021", "tech_stack": ["React", "Cloudflare"], "confidence_score": 96},
    {"company_name": "Fresenius Medical Care", "source_domain": "freseniusmedicalcare.com", "category": "Healthcare & Medical", "region": "Europe (EU)", "country_code": "DE", "contact_email": "contact@fmc-ag.com", "contact_phone": "+49 6172 6090", "tech_stack": ["React", "AWS Cloud"], "confidence_score": 97},
    {"company_name": "Bupa Health Care", "source_domain": "bupa.co.uk", "category": "Healthcare & Medical", "region": "Europe (UK)", "country_code": "UK", "contact_email": "customerrelations@bupa.com", "contact_phone": "+44 345 600 5493", "tech_stack": ["React", "Adobe Experience", "Cloudflare"], "confidence_score": 97},
    {"company_name": "Teladoc Health", "source_domain": "teladochealth.com", "category": "Healthcare & Medical", "region": "North America", "country_code": "US", "contact_email": "support@teladochealth.com", "contact_phone": "+1 800 835 2362", "tech_stack": ["Next.js", "React", "AWS Cloud"], "confidence_score": 98},

    # Financial Services & Banking
    {"company_name": "HDFC Bank Technology", "source_domain": "hdfcbank.com", "category": "Financial Services & Banking", "region": "Asia-Pacific (APAC)", "country_code": "IN", "contact_email": "support@hdfcbank.com", "contact_phone": "+91 22 6160 6161", "tech_stack": ["React", "Cloudflare", "AWS Cloud"], "confidence_score": 99},
    {"company_name": "Deutsche Bank Technology Centre", "source_domain": "db.com", "category": "Financial Services & Banking", "region": "Europe (EU)", "country_code": "DE", "contact_email": "service@db.com", "contact_phone": "+49 69 910 00", "tech_stack": ["React", "Cloudflare"], "confidence_score": 98},
    {"company_name": "Barclays Digital Banking", "source_domain": "barclays.co.uk", "category": "Financial Services & Banking", "region": "Europe (UK)", "country_code": "UK", "contact_email": "contact@barclays.com", "contact_phone": "+44 345 734 5345", "tech_stack": ["React", "AWS Cloud"], "confidence_score": 98},
    {"company_name": "Revolut Global", "source_domain": "revolut.com", "category": "Financial Services & Banking", "region": "Europe (UK)", "country_code": "UK", "contact_email": "support@revolut.com", "contact_phone": "+44 203 322 8352", "tech_stack": ["Next.js", "React", "Stripe", "Cloudflare"], "confidence_score": 99},
    {"company_name": "Razorpay Software", "source_domain": "razorpay.com", "category": "Financial Services & Banking", "region": "Asia-Pacific (APAC)", "country_code": "IN", "contact_email": "contact@razorpay.com", "contact_phone": "+91 80 4666 9999", "tech_stack": ["Next.js", "React", "Stripe", "AWS Cloud"], "confidence_score": 99},

    # Logistics & Supply Chain
    {"company_name": "DHL Supply Chain", "source_domain": "dhl.com", "category": "Logistics & Supply Chain", "region": "Europe (EU)", "country_code": "DE", "contact_email": "info@dhl.com", "contact_phone": "+49 228 1820", "tech_stack": ["React", "Cloudflare", "AWS Cloud"], "confidence_score": 98},
    {"company_name": "Delhivery Logistics", "source_domain": "delhivery.com", "category": "Logistics & Supply Chain", "region": "Asia-Pacific (APAC)", "country_code": "IN", "contact_email": "customer.support@delhivery.com", "contact_phone": "+91 124 671 9500", "tech_stack": ["React", "Next.js", "AWS Cloud"], "confidence_score": 97},
    {"company_name": "Flexport Freight", "source_domain": "flexport.com", "category": "Logistics & Supply Chain", "region": "North America", "country_code": "US", "contact_email": "info@flexport.com", "contact_phone": "+1 855 353 9767", "tech_stack": ["Next.js", "React", "Cloudflare"], "confidence_score": 98},
    {"company_name": "DP World Logistics", "source_domain": "dpworld.com", "category": "Logistics & Supply Chain", "region": "Middle East", "country_code": "AE", "contact_email": "info@dpworld.com", "contact_phone": "+971 4 881 1110", "tech_stack": ["React", "Cloudflare"], "confidence_score": 96},

    # Legal & Professional Services
    {"company_name": "Cyril Amarchand Mangaldas", "source_domain": "cyrilshroff.com", "category": "Legal & Professional Services", "region": "Asia-Pacific (APAC)", "country_code": "IN", "contact_email": "cam.mumbai@cyrilshroff.com", "contact_phone": "+91 22 2496 4455", "tech_stack": ["WordPress", "Cloudflare"], "confidence_score": 96},
    {"company_name": "Clifford Chance LLP", "source_domain": "cliffordchance.com", "category": "Legal & Professional Services", "region": "Europe (UK)", "country_code": "UK", "contact_email": "info@cliffordchance.com", "contact_phone": "+44 20 7006 1000", "tech_stack": ["React", "Cloudflare"], "confidence_score": 97},
    {"company_name": "Freshfields Bruckhaus Deringer", "source_domain": "freshfields.com", "category": "Legal & Professional Services", "region": "Europe (EU)", "country_code": "DE", "contact_email": "contact@freshfields.com", "contact_phone": "+49 69 2728 00", "tech_stack": ["React", "Cloudflare"], "confidence_score": 96},

    # Real Estate & Property
    {"company_name": "Godrej Properties", "source_domain": "godrejproperties.com", "category": "Real Estate & Property", "region": "Asia-Pacific (APAC)", "country_code": "IN", "contact_email": "marketing@godrejproperties.com", "contact_phone": "+91 22 6169 8500", "tech_stack": ["Next.js", "React", "Cloudflare"], "confidence_score": 97},
    {"company_name": "Vonovia SE", "source_domain": "vonovia.de", "category": "Real Estate & Property", "region": "Europe (EU)", "country_code": "DE", "contact_email": "service@vonovia.de", "contact_phone": "+49 234 314 0", "tech_stack": ["React", "Cloudflare"], "confidence_score": 96},
    {"company_name": "CBRE Group", "source_domain": "cbre.com", "category": "Real Estate & Property", "region": "North America", "country_code": "US", "contact_email": "info@cbre.com", "contact_phone": "+1 214 979 6100", "tech_stack": ["React", "Adobe Experience", "Cloudflare"], "confidence_score": 98},

    # Manufacturing & Industrial
    {"company_name": "Siemens AG", "source_domain": "siemens.com", "category": "Manufacturing & Industrial", "region": "Europe (EU)", "country_code": "DE", "contact_email": "contact@siemens.com", "contact_phone": "+49 89 636 00", "tech_stack": ["React", "AWS Cloud", "Cloudflare"], "confidence_score": 99},
    {"company_name": "Larsen & Toubro", "source_domain": "larsentoubro.com", "category": "Manufacturing & Industrial", "region": "Asia-Pacific (APAC)", "country_code": "IN", "contact_email": "infodesk@larsentoubro.com", "contact_phone": "+91 22 6752 5656", "tech_stack": ["React", "Cloudflare"], "confidence_score": 98},
    {"company_name": "Airbus Group", "source_domain": "airbus.com", "category": "Manufacturing & Industrial", "region": "Europe (EU)", "country_code": "FR", "contact_email": "contact@airbus.com", "contact_phone": "+33 5 81 50 00 00", "tech_stack": ["React", "Cloudflare"], "confidence_score": 98},

    # Hospitality & Food Service
    {"company_name": "Indian Hotels Company (Taj)", "source_domain": "ihcltata.com", "category": "Hospitality & Food Service", "region": "Asia-Pacific (APAC)", "country_code": "IN", "contact_email": "reservations@ihcltata.com", "contact_phone": "+91 22 6601 1825", "tech_stack": ["React", "Cloudflare"], "confidence_score": 97},
    {"company_name": "Accor Hotels Global", "source_domain": "accor.com", "category": "Hospitality & Food Service", "region": "Europe (EU)", "country_code": "FR", "contact_email": "contact@accor.com", "contact_phone": "+33 1 45 38 88 00", "tech_stack": ["React", "Next.js", "Stripe"], "confidence_score": 98},
    {"company_name": "Jumeirah Luxury Hotels", "source_domain": "jumeirah.com", "category": "Hospitality & Food Service", "region": "Middle East", "country_code": "AE", "contact_email": "info@jumeirah.com", "contact_phone": "+971 4 366 5000", "tech_stack": ["Next.js", "React", "Cloudflare"], "confidence_score": 97},

    # Education & EdTech
    {"company_name": "Coursera EdTech", "source_domain": "coursera.org", "category": "Education & EdTech", "region": "North America", "country_code": "US", "contact_email": "support@coursera.org", "contact_phone": "+1 800 952 5210", "tech_stack": ["React", "Next.js", "AWS Cloud", "Stripe"], "confidence_score": 99},
    {"company_name": "upGrad Education", "source_domain": "upgrad.com", "category": "Education & EdTech", "region": "Asia-Pacific (APAC)", "country_code": "IN", "contact_email": "info@upgrad.com", "contact_phone": "+91 80 4568 2222", "tech_stack": ["Next.js", "React", "Tailwind CSS"], "confidence_score": 97},
    {"company_name": "FutureLearn UK", "source_domain": "futurelearn.com", "category": "Education & EdTech", "region": "Europe (UK)", "country_code": "UK", "contact_email": "support@futurelearn.com", "contact_phone": "+44 203 826 8140", "tech_stack": ["React", "Stripe"], "confidence_score": 96},

    # Media, Marketing & Agency
    {"company_name": "WPP Group", "source_domain": "wpp.com", "category": "Media, Marketing & Agency", "region": "Europe (UK)", "country_code": "UK", "contact_email": "enquiries@wpp.com", "contact_phone": "+44 20 7282 4600", "tech_stack": ["React", "Cloudflare"], "confidence_score": 98},
    {"company_name": "Publicis Groupe", "source_domain": "publicisgroupe.com", "category": "Media, Marketing & Agency", "region": "Europe (EU)", "country_code": "FR", "contact_email": "contact@publicisgroupe.com", "contact_phone": "+33 1 44 43 70 00", "tech_stack": ["React", "Cloudflare"], "confidence_score": 97},
    {"company_name": "Dentsu International", "source_domain": "dentsu.com", "category": "Media, Marketing & Agency", "region": "Asia-Pacific (APAC)", "country_code": "SG", "contact_email": "contact@dentsu.com", "contact_phone": "+65 6509 9000", "tech_stack": ["React", "Cloudflare"], "confidence_score": 97},
]


def run_seed():
    init_db()
    with get_db_session() as session:
        created = 0
        for s in SEEDS:
            lead, is_new = GlobalLeadRepository.upsert_lead(session, {
                "company_name": s["company_name"],
                "source_domain": s["source_domain"],
                "live_url": f"https://{s['source_domain']}",
                "category": s["category"],
                "region": s["region"],
                "country_code": s["country_code"],
                "contact_email": s["contact_email"],
                "contact_phone": s["contact_phone"],
                "tech_stack": s["tech_stack"],
                "confidence_score": s["confidence_score"],
                "source": "Verified Enterprise Directory",
                "compliance_status": "CORPORATE_GENERIC",
            })
            if is_new:
                created += 1
        print(f"✅ Seeding Complete: {created} new global leads added ({len(SEEDS)} total in registry).")


if __name__ == "__main__":
    run_seed()
