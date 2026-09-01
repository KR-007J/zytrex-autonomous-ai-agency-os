"""Injects Enterprise Views and Logic into index.html."""

from pathlib import Path
import re

INDEX_PATH = Path("/home/krish/.gemini/antigravity/scratch/leadgen-outreach-agent/src/web/index.html")

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. New Views Markup
ENTERPRISE_VIEWS = """
    <!-- ==================================================================== -->
    <!-- PRIMARY ENTERPRISE VIEW 1: GLOBAL LEADS DIRECTORY EXPLORER          -->
    <!-- ==================================================================== -->
    <div id="page-explorer" class="zytrex-page-view active-view">
      <section style="padding: clamp(24px, 4vw, 48px) clamp(16px, 4vw, 48px); max-width: 1440px; margin: 0 auto; width: 100%;">
        
        <!-- Header Banner & Stats Strip -->
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 20px; margin-bottom: 32px;">
          <div>
            <div style="display: inline-flex; align-items: center; gap: 8px; padding: 4px 12px; background: rgba(21, 188, 223, 0.12); border: 1px solid var(--accent-cyan-border); color: #0284C7; font-size: 11px; font-weight: 700; margin-bottom: 12px; letter-spacing: 0.08em;">
              <span>🌐</span> GLOBAL BUSINESS INTELLIGENCE PLATFORM
            </div>
            <h1 style="font-size: clamp(26px, 4.5vw, 44px); font-weight: 700; letter-spacing: -0.5px; color: var(--text-heading); margin-bottom: 8px;">
              ENTERPRISE GLOBAL DIRECTORY
            </h1>
            <p style="color: var(--text-body); font-size: 14px; max-width: 680px; line-height: 1.5;">
              Searchable, filterable registry of verified commercial entities worldwide across 12 industry verticals and global regions. Powered by Crawlee and Common Crawl open-source pipelines.
            </p>
          </div>

          <div style="display: flex; gap: 12px; flex-wrap: wrap;">
            <button onclick="exportGlobalExcel()" class="zytrex-btn-primary">
              <span>📊</span> EXPORT EXCEL (.XLSX)
            </button>
            <button onclick="exportGlobalJson()" class="zytrex-btn-dark">
              <span>📄</span> EXPORT JSON
            </button>
          </div>
        </div>

        <!-- Global Metrics Strip -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 32px;">
          <div class="mission-stat-box chamfer-card">
            <div style="font-size: 11px; font-weight: 700; color: var(--text-body); letter-spacing: 0.06em; margin-bottom: 6px;">TOTAL VERIFIED LEADS</div>
            <div id="stat-global-total" style="font-size: 28px; font-weight: 700; color: var(--text-heading);">48</div>
            <div style="font-size: 11px; color: #10B981; font-weight: 700; margin-top: 4px;">● 100% Crawlee Verified</div>
          </div>
          <div class="mission-stat-box chamfer-card">
            <div style="font-size: 11px; font-weight: 700; color: var(--text-body); letter-spacing: 0.06em; margin-bottom: 6px;">INDUSTRY VERTICALS</div>
            <div style="font-size: 28px; font-weight: 700; color: #0284C7;">12 Core Sectors</div>
            <div style="font-size: 11px; color: var(--text-body); margin-top: 4px;">Retail, SaaS, Health, Legal, etc.</div>
          </div>
          <div class="mission-stat-box chamfer-card">
            <div style="font-size: 11px; font-weight: 700; color: var(--text-body); letter-spacing: 0.06em; margin-bottom: 6px;">GLOBAL REGIONS</div>
            <div style="font-size: 28px; font-weight: 700; color: var(--text-heading);">50+ Tech Hubs</div>
            <div style="font-size: 11px; color: var(--text-body); margin-top: 4px;">US, EU, UK, APAC, Middle East</div>
          </div>
          <div class="mission-stat-box chamfer-card">
            <div style="font-size: 11px; font-weight: 700; color: var(--text-body); letter-spacing: 0.06em; margin-bottom: 6px;">COMPLIANCE STANDARD</div>
            <div style="font-size: 28px; font-weight: 700; color: #059669;">GDPR Art 6(1)(f)</div>
            <div style="font-size: 11px; color: #059669; font-weight: 700; margin-top: 4px;">● Role-Based Generic Mailboxes</div>
          </div>
        </div>

        <!-- Multi-Faceted Filter Control Bar -->
        <div style="background: var(--bg-surface); border: 1px solid var(--border-light); padding: 20px; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.03);">
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; align-items: end;">
            
            <!-- Category Filter -->
            <div>
              <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-body); margin-bottom: 6px; letter-spacing: 0.05em;">CATEGORY / INDUSTRY</label>
              <select id="global-filter-category" onchange="applyGlobalFilters()" style="width: 100%; padding: 10px 12px; font-family: var(--font-display); font-size: 13px; font-weight: 600; border: 1px solid var(--border-light); background: #FFF; color: var(--text-heading); outline: none;">
                <option value="">All Categories (12 Verticals)</option>
                <option value="B2B SaaS & Tech">B2B SaaS & Tech</option>
                <option value="Retail & E-Commerce">Retail & E-Commerce</option>
                <option value="Healthcare & Medical">Healthcare & Medical</option>
                <option value="Financial Services & Banking">Financial Services & Banking</option>
                <option value="Logistics & Supply Chain">Logistics & Supply Chain</option>
                <option value="Legal & Professional Services">Legal & Professional Services</option>
                <option value="Real Estate & Property">Real Estate & Property</option>
                <option value="Manufacturing & Industrial">Manufacturing & Industrial</option>
                <option value="Hospitality & Food Service">Hospitality & Food Service</option>
                <option value="Education & EdTech">Education & EdTech</option>
                <option value="Media, Marketing & Agency">Media, Marketing & Agency</option>
                <option value="Construction & Engineering">Construction & Engineering</option>
              </select>
            </div>

            <!-- Region / Country Filter -->
            <div>
              <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-body); margin-bottom: 6px; letter-spacing: 0.05em;">REGION / COUNTRY</label>
              <select id="global-filter-region" onchange="applyGlobalFilters()" style="width: 100%; padding: 10px 12px; font-family: var(--font-display); font-size: 13px; font-weight: 600; border: 1px solid var(--border-light); background: #FFF; color: var(--text-heading); outline: none;">
                <option value="">All Regions Worldwide</option>
                <option value="North America">North America (US & Canada)</option>
                <option value="Europe (EU)">Europe (Germany, France, Netherlands)</option>
                <option value="Europe (UK)">Europe (United Kingdom)</option>
                <option value="Asia-Pacific (APAC)">Asia-Pacific (India, Singapore, Australia)</option>
                <option value="Middle East">Middle East (UAE)</option>
              </select>
            </div>

            <!-- Search Bar -->
            <div>
              <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-body); margin-bottom: 6px; letter-spacing: 0.05em;">KEYWORD SEARCH</label>
              <input
                type="text"
                id="global-search-input"
                oninput="debounceGlobalSearch()"
                placeholder="Company, domain, tech, email..."
                style="width: 100%; padding: 10px 12px; font-family: var(--font-display); font-size: 13px; font-weight: 600; border: 1px solid var(--border-light); background: #FFF; color: var(--text-heading); outline: none;"
              />
            </div>

            <!-- Action Controls -->
            <div style="display: flex; gap: 8px;">
              <button onclick="resetGlobalFilters()" class="zytrex-btn-dark" style="flex: 1; padding: 10px; font-size: 11px; justify-content: center;">
                <span>🔄</span> RESET
              </button>
            </div>

          </div>
        </div>

        <!-- Table Controls & Badge Strip -->
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 16px;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <span id="global-badge-count" style="display: inline-block; padding: 6px 14px; background: rgba(0, 0, 0, 0.04); border: 1px solid var(--border-light); font-size: 12px; font-weight: 700; color: var(--text-heading);">
              Showing 1-10 of 48 verified leads
            </span>
            <span id="global-page-info-top" style="font-size: 12px; color: var(--text-body); font-weight: 600;">
              Page 1 of 5
            </span>
          </div>

          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 11px; font-weight: 700; color: var(--text-body);">Rows:</span>
            <select id="global-page-size" onchange="changeGlobalPageSize(this.value)" style="padding: 4px 8px; font-family: var(--font-display); font-size: 11px; font-weight: 700; border: 1px solid var(--border-light); background: #FFF;">
              <option value="10">10 / page</option>
              <option value="25" selected>25 / page</option>
              <option value="50">50 / page</option>
              <option value="100">100 / page</option>
              <option value="1000">Show All</option>
            </select>
            <div id="global-top-pagination-nav" style="display: flex; gap: 4px;"></div>
          </div>
        </div>

        <!-- Global Enterprise Leads Data Table -->
        <div class="pipeline-table-container chamfer-card" style="box-shadow: 0 10px 30px rgba(0,0,0,0.04);">
          <table class="pipeline-table">
            <thead>
              <tr>
                <th>COMPANY / BUSINESS</th>
                <th>CATEGORY</th>
                <th>REGION / COUNTRY</th>
                <th>VERIFIED CONTACT</th>
                <th>DETECTED TECH STACK</th>
                <th>SCORE</th>
                <th>ACTIONS</th>
              </tr>
            </thead>
            <tbody id="global-leads-tbody">
              <!-- Rendered Dynamically -->
            </tbody>
          </table>
        </div>

        <!-- Bottom Pagination Bar -->
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; margin-top: 24px; padding: 16px 20px; background: var(--bg-surface); border: 1px solid var(--border-light);">
          <div style="display: flex; align-items: center; gap: 12px;">
            <span id="global-page-info-bottom" style="font-size: 12px; font-weight: 700; color: var(--text-heading);">
              Page 1 of 5 (48 leads)
            </span>
          </div>
          <div id="global-pagination-nav" style="display: flex; gap: 4px; flex-wrap: wrap;"></div>
        </div>

      </section>
    </div>

    <!-- ==================================================================== -->
    <!-- PRIMARY ENTERPRISE VIEW 2: INGESTION & PIPELINES                    -->
    <!-- ==================================================================== -->
    <div id="page-pipelines" class="zytrex-page-view">
      <section style="padding: clamp(24px, 4vw, 48px) clamp(16px, 4vw, 48px); max-width: 1440px; margin: 0 auto; width: 100%;">
        
        <div style="margin-bottom: 32px;">
          <div style="display: inline-flex; align-items: center; gap: 8px; padding: 4px 12px; background: rgba(21, 188, 223, 0.12); border: 1px solid var(--accent-cyan-border); color: #0284C7; font-size: 11px; font-weight: 700; margin-bottom: 12px; letter-spacing: 0.08em;">
            <span>⚡</span> HIGH-THROUGHPUT CRAWLER ENGINE
          </div>
          <h1 style="font-size: clamp(26px, 4.5vw, 44px); font-weight: 700; letter-spacing: -0.5px; color: var(--text-heading); margin-bottom: 8px;">
            INGESTION & CRAWLER PIPELINES
          </h1>
          <p style="color: var(--text-body); font-size: 14px; max-width: 680px; line-height: 1.5;">
            Production crawler pipeline orchestrating Crawlee (Apify), search API seed queries, and Common Crawl bulk domain index harvesting with automated rate limiting and retry backoff.
          </p>
        </div>

        <!-- Crawler Controls & Dispatcher Card -->
        <div style="background: var(--bg-surface); border: 1px solid var(--border-light); padding: 24px; margin-bottom: 32px; box-shadow: 0 4px 20px rgba(0,0,0,0.03);" class="chamfer-card">
          <h3 style="font-size: 16px; font-weight: 700; margin-bottom: 16px; color: var(--text-heading);">
            DISPATCH TARGETED INGESTION JOB
          </h3>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; align-items: end;">
            <div>
              <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-body); margin-bottom: 6px;">TARGET VERTICAL</label>
              <select id="dispatch-category" style="width: 100%; padding: 10px; font-family: var(--font-display); font-size: 13px; font-weight: 600; border: 1px solid var(--border-light); background: #FFF;">
                <option value="B2B SaaS & Tech">B2B SaaS & Tech</option>
                <option value="Retail & E-Commerce">Retail & E-Commerce</option>
                <option value="Healthcare & Medical">Healthcare & Medical</option>
                <option value="Financial Services & Banking">Financial Services & Banking</option>
                <option value="Logistics & Supply Chain">Logistics & Supply Chain</option>
                <option value="Legal & Professional Services">Legal & Professional Services</option>
              </select>
            </div>

            <div>
              <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-body); margin-bottom: 6px;">TARGET REGION / GEO</label>
              <select id="dispatch-region" style="width: 100%; padding: 10px; font-family: var(--font-display); font-size: 13px; font-weight: 600; border: 1px solid var(--border-light); background: #FFF;">
                <option value="Asia-Pacific (APAC)">Asia-Pacific (India, Singapore, Australia)</option>
                <option value="Europe (EU)">Europe (Germany, France, Netherlands)</option>
                <option value="Europe (UK)">Europe (United Kingdom)</option>
                <option value="North America">North America (US & Canada)</option>
                <option value="Middle East">Middle East (UAE)</option>
              </select>
            </div>

            <div>
              <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-body); margin-bottom: 6px;">DISCOVERY SEED DEPTH</label>
              <select id="dispatch-depth" style="width: 100%; padding: 10px; font-family: var(--font-display); font-size: 13px; font-weight: 600; border: 1px solid var(--border-light); background: #FFF;">
                <option value="20">20 Seed Domains</option>
                <option value="50">50 Seed Domains</option>
                <option value="100">100 Seed Domains</option>
              </select>
            </div>

            <div>
              <button onclick="dispatchPipelineRun()" id="btn-dispatch-pipeline" class="zytrex-btn-primary" style="width: 100%; justify-content: center; padding: 11px;">
                <span>⚡</span> RUN CRAWLEE PIPELINE
              </button>
            </div>
          </div>
        </div>

        <!-- Ingestion History Table -->
        <h3 style="font-size: 16px; font-weight: 700; margin-bottom: 16px; color: var(--text-heading);">
          LIVE INGESTION JOBS & CRAWL LOGS
        </h3>
        <div class="pipeline-table-container chamfer-card">
          <table class="pipeline-table">
            <thead>
              <tr>
                <th>JOB ID</th>
                <th>PIPELINE TYPE</th>
                <th>TARGET CATEGORY</th>
                <th>TARGET REGION</th>
                <th>SEEDS</th>
                <th>PAGES</th>
                <th>LEADS EXTRACTED</th>
                <th>STATUS</th>
              </tr>
            </thead>
            <tbody id="pipeline-jobs-tbody">
              <!-- Rendered Dynamically -->
            </tbody>
          </table>
        </div>

      </section>
    </div>

    <!-- ==================================================================== -->
    <!-- PRIMARY ENTERPRISE VIEW 3: COMPLIANCE & SUPPRESSION (DNC)          -->
    <!-- ==================================================================== -->
    <div id="page-compliance" class="zytrex-page-view">
      <section style="padding: clamp(24px, 4vw, 48px) clamp(16px, 4vw, 48px); max-width: 1440px; margin: 0 auto; width: 100%;">
        
        <div style="margin-bottom: 32px;">
          <div style="display: inline-flex; align-items: center; gap: 8px; padding: 4px 12px; background: rgba(16, 185, 129, 0.12); border: 1px solid #10B981; color: #047857; font-size: 11px; font-weight: 700; margin-bottom: 12px; letter-spacing: 0.08em;">
            <span>🛡️</span> REGULATORY GOVERNANCE & PRIVACY SAFEGUARDS
          </div>
          <h1 style="font-size: clamp(26px, 4.5vw, 44px); font-weight: 700; letter-spacing: -0.5px; color: var(--text-heading); margin-bottom: 8px;">
            COMPLIANCE & SUPPRESSION CENTER
          </h1>
          <p style="color: var(--text-body); font-size: 14px; max-width: 680px; line-height: 1.5;">
            Non-negotiable compliance controls enforcing GDPR Article 6(1)(f) legitimate interest rules, CAN-SPAM opt-out standards, and global Do-Not-Contact (DNC) suppression lists.
          </p>
        </div>

        <!-- Add Suppression Entry Form -->
        <div style="background: var(--bg-surface); border: 1px solid var(--border-light); padding: 24px; margin-bottom: 32px;" class="chamfer-card">
          <h3 style="font-size: 16px; font-weight: 700; margin-bottom: 16px; color: var(--text-heading);">
            ADD DOMAIN OR EMAIL TO GLOBAL SUPPRESSION LIST
          </h3>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; align-items: end;">
            <div>
              <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-body); margin-bottom: 6px;">DOMAIN OR EMAIL</label>
              <input
                type="text"
                id="suppress-input-target"
                placeholder="e.g. competitor.com or optout@domain.com"
                style="width: 100%; padding: 10px; font-family: var(--font-display); font-size: 13px; font-weight: 600; border: 1px solid var(--border-light); background: #FFF;"
              />
            </div>
            <div>
              <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-body); margin-bottom: 6px;">REASON / LEGAL BASIS</label>
              <select id="suppress-input-reason" style="width: 100%; padding: 10px; font-family: var(--font-display); font-size: 13px; font-weight: 600; border: 1px solid var(--border-light); background: #FFF;">
                <option value="GDPR Right to Erasure / Opt-Out">GDPR Right to Erasure / Opt-Out</option>
                <option value="CAN-SPAM DNC Request">CAN-SPAM DNC Request</option>
                <option value="Competitor Exclusion">Competitor Exclusion</option>
                <option value="Invalid / Dead Domain">Invalid / Dead Domain</option>
              </select>
            </div>
            <div>
              <label style="display: block; font-size: 11px; font-weight: 700; color: var(--text-body); margin-bottom: 6px;">SCOPE</label>
              <select id="suppress-input-scope" style="width: 100%; padding: 10px; font-family: var(--font-display); font-size: 13px; font-weight: 600; border: 1px solid var(--border-light); background: #FFF;">
                <option value="GLOBAL">GLOBAL (All Regions)</option>
                <option value="REGION_EU">EUROPE (EU/UK)</option>
                <option value="REGION_US">NORTH AMERICA (US/CA)</option>
              </select>
            </div>
            <div>
              <button onclick="submitSuppressionEntry()" class="zytrex-btn-primary" style="width: 100%; justify-content: center; padding: 11px; background: #EF4444; border-color: #DC2626; color: #FFF;">
                <span>🚫</span> ADD TO SUPPRESSION
              </button>
            </div>
          </div>
        </div>

        <!-- Active Suppression List Table -->
        <h3 style="font-size: 16px; font-weight: 700; margin-bottom: 16px; color: var(--text-heading);">
          ACTIVE SUPPRESSION RECORDS (BLOCKED FROM EXPORTS & DISPATCH)
        </h3>
        <div class="pipeline-table-container chamfer-card" style="margin-bottom: 40px;">
          <table class="pipeline-table">
            <thead>
              <tr>
                <th>SUPPRESSED TARGET</th>
                <th>REASON</th>
                <th>SCOPE</th>
                <th>DATE ADDED</th>
                <th>ACTION</th>
              </tr>
            </thead>
            <tbody id="suppression-tbody">
              <!-- Rendered Dynamically -->
            </tbody>
          </table>
        </div>

        <!-- Legal Position Paper Card -->
        <div style="background: var(--bg-surface); border: 1px solid var(--border-light); padding: 32px;" class="chamfer-card">
          <h3 style="font-size: 18px; font-weight: 700; margin-bottom: 16px; color: var(--text-heading);">
            📜 CLIENT COMPLIANCE & LEGAL POSITION NOTE
          </h3>
          <div style="font-size: 14px; line-height: 1.7; color: var(--text-body); max-width: 900px;">
            <p style="margin-bottom: 12px;">
              <strong>1. GDPR & UK-GDPR (EU/UK):</strong> All commercial business contact discovery is executed under <strong>Article 6(1)(f) Legitimate Interests</strong> for B2B commercial intelligence. The platform prioritizes corporate generic mailboxes (<code>contact@</code>, <code>info@</code>, <code>sales@</code>) and respects immediate right-to-erasure requests.
            </p>
            <p style="margin-bottom: 12px;">
              <strong>2. CAN-SPAM (US) & CASL (Canada):</strong> Automated compliance verification checks for clear sender transparency and maintains a real-time suppression index to prevent unsolicited contact to opted-out domains.
            </p>
            <p>
              <strong>3. Auditability:</strong> Every discovered record retains source provenance metadata, discovery timestamps, and crawler verification trails.
            </p>
          </div>
        </div>

      </section>
    </div>

    <!-- ==================================================================== -->
    <!-- PRIMARY ENTERPRISE VIEW 4: DEVELOPER REST API & EXPORTS            -->
    <!-- ==================================================================== -->
    <div id="page-api-docs" class="zytrex-page-view">
      <section style="padding: clamp(24px, 4vw, 48px) clamp(16px, 4vw, 48px); max-width: 1440px; margin: 0 auto; width: 100%;">
        
        <div style="margin-bottom: 32px;">
          <div style="display: inline-flex; align-items: center; gap: 8px; padding: 4px 12px; background: rgba(21, 188, 223, 0.12); border: 1px solid var(--accent-cyan-border); color: #0284C7; font-size: 11px; font-weight: 700; margin-bottom: 12px; letter-spacing: 0.08em;">
            <span>🔌</span> DEVELOPER REST API
          </div>
          <h1 style="font-size: clamp(26px, 4.5vw, 44px); font-weight: 700; letter-spacing: -0.5px; color: var(--text-heading); margin-bottom: 8px;">
            REST API & DATA EXPORT ENGINE
          </h1>
          <p style="color: var(--text-body); font-size: 14px; max-width: 680px; line-height: 1.5;">
            Enterprise REST endpoints for programmatic querying, filtering, and streaming global business leads directly into CRMs or custom analytics pipelines.
          </p>
        </div>

        <!-- Interactive Query Builder -->
        <div style="background: var(--bg-surface); border: 1px solid var(--border-light); padding: 24px; margin-bottom: 24px;" class="chamfer-card">
          <h3 style="font-size: 16px; font-weight: 700; margin-bottom: 16px; color: var(--text-heading);">
            INTERACTIVE QUERY EXPLORER (TRY IT LIVE)
          </h3>
          <div style="display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px;">
            <input
              type="text"
              id="api-query-endpoint"
              value="/api/leads?category=B2B SaaS & Tech&region=North America&limit=10"
              style="flex: 1; min-width: 280px; padding: 12px 16px; font-family: var(--font-mono); font-size: 13px; border: 1px solid var(--border-light); background: #F8FAFC;"
            />
            <button onclick="executeLiveApiTest()" class="zytrex-btn-primary" style="padding: 12px 20px;">
              <span>⚡</span> EXECUTE REQUEST
            </button>
          </div>

          <!-- JSON Result Box -->
          <pre id="api-response-viewer" style="background: #0F172A; color: #38BDF8; padding: 20px; font-family: var(--font-mono); font-size: 12px; border-radius: 4px; max-height: 360px; overflow: auto;">{
  "status": "Click EXECUTE REQUEST to inspect live API output..."
}</pre>
        </div>

        <!-- Code Snippets Carousel -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px;">
          <div style="background: var(--bg-surface); border: 1px solid var(--border-light); padding: 20px;" class="chamfer-card">
            <h4 style="font-size: 13px; font-weight: 700; margin-bottom: 10px; color: var(--text-heading);">cURL</h4>
            <pre style="background: #0F172A; color: #E2E8F0; padding: 14px; font-family: var(--font-mono); font-size: 11px; overflow-x: auto;">curl -X GET "http://localhost:8000/api/leads?category=Retail&limit=25" \\
  -H "Accept: application/json"</pre>
          </div>
          <div style="background: var(--bg-surface); border: 1px solid var(--border-light); padding: 20px;" class="chamfer-card">
            <h4 style="font-size: 13px; font-weight: 700; margin-bottom: 10px; color: var(--text-heading);">Python (httpx)</h4>
            <pre style="background: #0F172A; color: #E2E8F0; padding: 14px; font-family: var(--font-mono); font-size: 11px; overflow-x: auto;">import httpx
res = httpx.get("http://localhost:8000/api/leads", params={"category": "Retail", "limit": 25})
leads = res.json()["items"]</pre>
          </div>
        </div>

      </section>
    </div>
"""

# Insert Views before <div id="page-home"
if '<div id="page-home"' in content and '<div id="page-explorer"' not in content:
    content = content.replace('<div id="page-home"', ENTERPRISE_VIEWS + '\n    <div id="page-home"')
    print("✅ Injected Enterprise Views.")

# 2. Update validPages array
content = re.sub(
    r'const validPages = \[.*?\];',
    "const validPages = ['explorer', 'pipelines', 'compliance', 'api-docs', 'home', 'about', 'services', 'mission-control', 'pipeline', 'contact'];",
    content
)

# 3. Update getPageFromURL fallback to 'explorer'
content = re.sub(
    r"if \(validPages\.includes\(path\)\) return path;\s*return 'home';",
    "if (validPages.includes(path)) return path;\n      return 'explorer';",
    content
)

# 4. Global Enterprise JavaScript Suite
ENTERPRISE_JS = """
    // =========================================================================
    // ENTERPRISE GLOBAL LEADS & DIRECTORY JAVASCRIPT SUITE
    // =========================================================================
    let globalCurrentPage = 1;
    let globalPageSize = 25;
    let globalSearchDebounceTimer = null;
    let globalCachedLeads = [];
    let globalTotalLeads = 0;

    async function fetchGlobalLeads() {
      const cat = document.getElementById('global-filter-category')?.value || '';
      const reg = document.getElementById('global-filter-region')?.value || '';
      const search = document.getElementById('global-search-input')?.value || '';

      const params = new URLSearchParams({
        page: globalCurrentPage,
        limit: globalPageSize,
      });
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
        }
      } catch (err) {
        console.error('Error fetching global leads:', err);
      }
    }

    function renderGlobalLeadsTable(data) {
      const tbody = document.getElementById('global-leads-tbody');
      if (!tbody) return;

      const leads = data.items || [];
      const total = data.total || 0;
      const totalPages = data.total_pages || 1;

      if (leads.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="7" style="text-align: center; padding: 40px; color: var(--text-body);">
              No verified leads found matching your active filter criteria.
            </td>
          </tr>
        `;
      } else {
        tbody.innerHTML = leads.map(l => {
          const techs = (l.tech_stack || []).slice(0, 3).map(t => `<span class="badge-opp" style="font-size: 10px; margin-right: 4px;">${escapeHtml(t)}</span>`).join('');
          return `
            <tr>
              <td>
                <strong style="color: var(--text-heading); font-size: 14px;">${escapeHtml(l.company_name)}</strong>
                <div style="font-size: 11px; color: var(--text-body); margin-top: 2px;">
                  <a href="${escapeHtml(l.live_url)}" target="_blank" rel="noopener noreferrer" style="color: var(--accent-cyan-border);">${escapeHtml(l.source_domain)} ↗</a>
                </div>
              </td>
              <td>
                <span style="font-size: 12px; font-weight: 600; color: var(--text-heading);">${escapeHtml(l.category)}</span>
              </td>
              <td>
                <span class="badge-loc">📍 ${escapeHtml(l.region)} (${escapeHtml(l.country_code)})</span>
              </td>
              <td>
                <div style="font-size: 12px; font-weight: 700; color: #10B981;">${escapeHtml(l.contact_email || 'Verified Generic')}</div>
                <div style="font-size: 11px; color: var(--text-body); margin-top: 2px;">${escapeHtml(l.contact_phone || 'Public Available')}</div>
              </td>
              <td>
                ${techs || '<span style="font-size: 11px; color: #94A3B8;">Web & Cloud</span>'}
              </td>
              <td>
                <span class="badge-score">${l.confidence_score}%</span>
              </td>
              <td>
                <button onclick="inspectGlobalLead(${l.id})" class="zytrex-btn-dark" style="padding: 7px 12px; font-size: 11px;">
                  <span>🔍</span> INSPECT
                </button>
              </td>
            </tr>
          `;
        }).join('');
      }

      // Update Badges & Counters
      const startIdx = (globalCurrentPage - 1) * globalPageSize;
      const endIdx = Math.min(startIdx + globalPageSize, total);
      const countBadge = total === 0 ? "Showing 0 of 0 leads" : `Showing ${startIdx + 1}-${endIdx} of ${total} verified leads`;
      const pageInfo = `Page ${globalCurrentPage} of ${totalPages} (${total} leads)`;

      if (document.getElementById('global-badge-count')) document.getElementById('global-badge-count').innerText = countBadge;
      if (document.getElementById('global-page-info-top')) document.getElementById('global-page-info-top').innerText = pageInfo;
      if (document.getElementById('global-page-info-bottom')) document.getElementById('global-page-info-bottom').innerText = pageInfo;
      if (document.getElementById('stat-global-total')) document.getElementById('stat-global-total').innerText = total;

      // Populate Navigation Buttons
      const navHtml = buildGlobalPaginationNavHtml(globalCurrentPage, totalPages, false);
      const compactNavHtml = buildGlobalPaginationNavHtml(globalCurrentPage, totalPages, true);

      if (document.getElementById('global-pagination-nav')) document.getElementById('global-pagination-nav').innerHTML = navHtml;
      if (document.getElementById('global-top-pagination-nav')) document.getElementById('global-top-pagination-nav').innerHTML = compactNavHtml;
    }

    function buildGlobalPaginationNavHtml(cur, total, isCompact) {
      if (total <= 1) return '';
      let html = '';

      if (!isCompact) {
        html += `<button onclick="goToGlobalPage(1)" class="zytrex-page-btn" ${cur === 1 ? 'disabled' : ''} title="First Page">⏮</button>`;
      }
      html += `<button onclick="goToGlobalPage(${cur - 1})" class="zytrex-page-btn" ${cur === 1 ? 'disabled' : ''} title="Previous Page">◀</button>`;

      if (!isCompact) {
        let pagesToShow = [];
        if (total <= 7) {
          for (let i = 1; i <= total; i++) pagesToShow.push(i);
        } else {
          pagesToShow = [1];
          if (cur > 3) pagesToShow.push('...');
          for (let i = Math.max(2, cur - 1); i <= Math.min(total - 1, cur + 1); i++) {
            pagesToShow.push(i);
          }
          if (cur < total - 2) pagesToShow.push('...');
          pagesToShow.push(total);
        }

        pagesToShow.forEach(p => {
          if (p === '...') {
            html += `<span style="display:inline-flex; align-items:center; justify-content:center; width:28px; color:var(--text-body);">...</span>`;
          } else {
            html += `<button onclick="goToGlobalPage(${p})" class="zytrex-page-btn ${p === cur ? 'active' : ''}">${p}</button>`;
          }
        });
      }

      html += `<button onclick="goToGlobalPage(${cur + 1})" class="zytrex-page-btn" ${cur === total ? 'disabled' : ''} title="Next Page">▶</button>`;
      if (!isCompact) {
        html += `<button onclick="goToGlobalPage(${total})" class="zytrex-page-btn" ${cur === total ? 'disabled' : ''} title="Last Page">⏭</button>`;
      }
      return html;
    }

    window.goToGlobalPage = function(p) {
      globalCurrentPage = p;
      fetchGlobalLeads();
      window.scrollTo({ top: 200, behavior: 'smooth' });
    };

    window.applyGlobalFilters = function() {
      globalCurrentPage = 1;
      fetchGlobalLeads();
    };

    window.debounceGlobalSearch = function() {
      clearTimeout(globalSearchDebounceTimer);
      globalSearchDebounceTimer = setTimeout(() => {
        globalCurrentPage = 1;
        fetchGlobalLeads();
      }, 300);
    };

    window.resetGlobalFilters = function() {
      if (document.getElementById('global-filter-category')) document.getElementById('global-filter-category').value = '';
      if (document.getElementById('global-filter-region')) document.getElementById('global-filter-region').value = '';
      if (document.getElementById('global-search-input')) document.getElementById('global-search-input').value = '';
      globalCurrentPage = 1;
      fetchGlobalLeads();
      showToast('Filters reset to Global All');
    };

    window.changeGlobalPageSize = function(size) {
      globalPageSize = parseInt(size, 10);
      globalCurrentPage = 1;
      fetchGlobalLeads();
    };

    window.exportGlobalExcel = function() {
      window.location.href = '/api/export/excel';
    };

    window.exportGlobalJson = function() {
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(globalCachedLeads, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `zytrex_global_leads_export_${Date.now()}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      showToast('Exported JSON dataset');
    };

    window.inspectGlobalLead = function(leadId) {
      const lead = globalCachedLeads.find(l => l.id === leadId);
      if (!lead) return;

      document.getElementById('modal-company-title').innerText = lead.company_name;
      document.getElementById('modal-lead-details').innerText = `📍 ${lead.region} (${lead.country_code}) • Category: ${lead.category} • Confidence: ${lead.confidence_score}%`;
      document.getElementById('modal-opportunity-badge').innerText = (lead.tech_stack && lead.tech_stack.length) ? lead.tech_stack.join(' • ') : 'Web Modernization & Next.js Architecture';

      currentPitch = `Subject: Strategic Web & Tech Modernization for ${lead.company_name}\\n\\nHi Team,\\n\\nWe noticed ${lead.company_name} is scaling operations across ${lead.region}. We specialize in high-performance digital engineering and web platforms for leading ${lead.category} organizations.`;

      document.getElementById('modal-pitch-box').innerText = currentPitch;

      const mailtoBtn = document.getElementById('modal-mailto-btn');
      if (mailtoBtn) {
        const recipient = lead.contact_email || 'contact@' + lead.source_domain;
        mailtoBtn.href = `mailto:${encodeURIComponent(recipient)}?subject=${encodeURIComponent("Technical Modernization Roadmap")}&body=${encodeURIComponent(currentPitch)}`;
      }

      const siteBtn = document.getElementById('modal-site-btn');
      if (siteBtn) siteBtn.href = lead.live_url || `https://${lead.source_domain}`;

      document.getElementById('pitch-modal').classList.add('open');
    };

    // Pipeline Jobs Execution
    window.dispatchPipelineRun = async function() {
      const cat = document.getElementById('dispatch-category')?.value || 'B2B SaaS & Tech';
      const reg = document.getElementById('dispatch-region')?.value || 'Asia-Pacific (APAC)';
      const depth = parseInt(document.getElementById('dispatch-depth')?.value || '20', 10);
      const btn = document.getElementById('btn-dispatch-pipeline');

      btn.innerText = 'DISPATCHING CRAWLEE...';
      try {
        const res = await fetch('/api/pipeline/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ category: cat, region: reg, seed_limit: depth })
        });
        const data = await res.json();
        if (res.ok) {
          showToast(data.message || 'Pipeline dispatched successfully');
          fetchPipelineJobs();
        }
      } catch (err) {
        showToast('Error dispatching crawler');
      } finally {
        btn.innerHTML = `<span>⚡</span> RUN CRAWLEE PIPELINE`;
      }
    };

    async function fetchPipelineJobs() {
      try {
        const res = await fetch('/api/pipeline/jobs');
        if (res.ok) {
          const data = await res.json();
          const tbody = document.getElementById('pipeline-jobs-tbody');
          if (tbody) {
            const jobs = data.jobs || [];
            if (jobs.length === 0) {
              tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-body); padding: 20px;">No crawl jobs run yet.</td></tr>`;
            } else {
              tbody.innerHTML = jobs.map(j => `
                <tr>
                  <td><strong style="color: var(--text-heading);">#${j.id}</strong></td>
                  <td><span class="badge-opp">${escapeHtml(j.pipeline_type)}</span></td>
                  <td>${escapeHtml(j.category_filter)}</td>
                  <td>${escapeHtml(j.region_filter)}</td>
                  <td>${j.seeds_discovered}</td>
                  <td>${j.pages_crawled}</td>
                  <td><strong style="color: #10B981;">+${j.leads_extracted}</strong></td>
                  <td><span class="auth-badge">${escapeHtml(j.status)}</span></td>
                </tr>
              `).join('');
            }
          }
        }
      } catch (err) {}
    }

    // Suppression Center
    async function fetchSuppressionList() {
      try {
        const res = await fetch('/api/suppression/list');
        if (res.ok) {
          const data = await res.json();
          const tbody = document.getElementById('suppression-tbody');
          if (tbody) {
            const items = data.items || [];
            if (items.length === 0) {
              tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-body); padding: 20px;">No suppressed entities in active DNC list.</td></tr>`;
            } else {
              tbody.innerHTML = items.map(s => `
                <tr>
                  <td><strong style="color: #EF4444;">${escapeHtml(s.domain_or_email)}</strong></td>
                  <td>${escapeHtml(s.reason)}</td>
                  <td><span class="badge-loc">${escapeHtml(s.scope)}</span></td>
                  <td style="font-size: 11px; color: var(--text-body);">${escapeHtml(s.added_at ? s.added_at.slice(0, 10) : 'Active')}</td>
                  <td>
                    <button onclick="removeSuppressionRecord('${escapeHtml(s.domain_or_email)}')" class="zytrex-btn-dark" style="padding: 5px 10px; font-size: 10px; color: #EF4444;">
                      UNBLOCK
                    </button>
                  </td>
                </tr>
              `).join('');
            }
          }
        }
      } catch (err) {}
    }

    window.submitSuppressionEntry = async function() {
      const target = document.getElementById('suppress-input-target')?.value.trim();
      const reason = document.getElementById('suppress-input-reason')?.value;
      const scope = document.getElementById('suppress-input-scope')?.value;

      if (!target) {
        showToast('Please enter a target domain or email');
        return;
      }

      try {
        const res = await fetch('/api/suppression/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ domain_or_email: target, reason, scope })
        });
        if (res.ok) {
          showToast(`Suppressed ${target} globally`);
          document.getElementById('suppress-input-target').value = '';
          fetchSuppressionList();
          fetchGlobalLeads();
        }
      } catch (err) {
        showToast('Error adding suppression entry');
      }
    };

    window.removeSuppressionRecord = async function(domainOrEmail) {
      try {
        const res = await fetch(`/api/suppression/remove?domain_or_email=${encodeURIComponent(domainOrEmail)}`, {
          method: 'DELETE'
        });
        if (res.ok) {
          showToast(`Unblocked ${domainOrEmail}`);
          fetchSuppressionList();
          fetchGlobalLeads();
        }
      } catch (err) {
        showToast('Error removing suppression entry');
      }
    };

    // API Docs Live Tester
    window.executeLiveApiTest = async function() {
      const endpoint = document.getElementById('api-query-endpoint')?.value || '/api/leads';
      const viewer = document.getElementById('api-response-viewer');
      if (viewer) viewer.innerText = 'Executing query...';

      try {
        const res = await fetch(endpoint);
        const data = await res.json();
        if (viewer) viewer.innerText = JSON.stringify(data, null, 2);
      } catch (err) {
        if (viewer) viewer.innerText = `Error: ${err.message}`;
      }
    };
"""

# Append Enterprise JS inside the main script tag
if "fetchGlobalLeads();" not in content:
    content = content.replace("syncMissionControl();", "syncMissionControl();\n      fetchGlobalLeads();\n      fetchPipelineJobs();\n      fetchSuppressionList();")
    content = content.replace("</script>", ENTERPRISE_JS + "\n  </script>")
    print("✅ Injected Enterprise JS Suite.")

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Enterprise injection complete.")
