// LeadForge Enterprise SaaS Frontend Architecture
// Apple/Linear-tier UX, deterministic client-side routing, and real-time backend orchestration.

// Global State
const state = {
  activeRoute: "dashboard",
  token: localStorage.getItem("leadforge_token") || "",
  user: null,
  org: null,
  theme: localStorage.getItem("leadforge_theme") || "light",
  leads: [],
  leadsTotal: 0,
  leadsLimit: 25,
  leadsOffset: 0,
  leadsFilters: {
    query: "",
    technology: "",
    country: "",
    status: "",
    has_email: null,
    min_score: null,
    sort_by: "score",
    preset: "all",
  },
  selectedLeadIds: new Set(),
  technologies: [],
  analytics: null,
  activeSSE: null,
  jobs: [],
  webhooks: [],
  apiKeys: [],
  members: [],
  auditLogs: [],
  projects: [],
  lists: [],
  cmdKIndex: 0,
  filteredCmdK: [],
};

// Initialize Theme
function applyTheme(theme) {
  state.theme = theme;
  localStorage.setItem("leadforge_theme", theme);
  if (theme === "dark") {
    document.documentElement.classList.add("dark");
  } else {
    document.documentElement.classList.remove("dark");
  }
}
function toggleTheme() {
  applyTheme(state.theme === "dark" ? "light" : "dark");
}

// Client-Side Router
const routes = [
  "dashboard", "discover", "leads", "projects", "lists",
  "technologies", "jobs", "imports", "exports", "webhooks",
  "api-keys", "settings", "audit-logs"
];

function getInitialRoute() {
  const path = window.location.pathname.replace(/^\//, "").split("/")[0];
  if (routes.includes(path)) return path;
  if (path === "api") return "api-keys";
  return "dashboard";
}

function navigateRoute(e, route) {
  if (e) e.preventDefault();
  if (!routes.includes(route)) route = "dashboard";
  state.activeRoute = route;
  window.history.pushState({ route }, "", `/${route}`);
  renderActiveRoute();
}

window.addEventListener("popstate", (e) => {
  const r = (e.state && e.state.route) ? e.state.route : getInitialRoute();
  state.activeRoute = r;
  renderActiveRoute();
});

function renderActiveRoute() {
  // Hide all views
  routes.forEach((r) => {
    const el = document.getElementById(`view-${r}`);
    if (el) el.classList.add("hidden");
    const nav = document.getElementById(`nav-${r}`);
    if (nav) {
      nav.classList.remove("bg-neutral-100", "dark:bg-neutral-800", "font-bold", "text-[#ef4d23]", "dark:text-[#ef4d23]");
    }
  });

  // Show active view
  const currentView = document.getElementById(`view-${state.activeRoute}`);
  if (currentView) currentView.classList.remove("hidden");

  // Highlight active nav
  const currentNav = document.getElementById(`nav-${state.activeRoute}`);
  if (currentNav) {
    currentNav.classList.add("bg-neutral-100", "dark:bg-neutral-800", "font-bold", "text-[#ef4d23]", "dark:text-[#ef4d23]");
  }

  // Update Breadcrumbs
  updateBreadcrumbs(state.activeRoute);

  // Trigger route-specific loads
  switch (state.activeRoute) {
    case "dashboard":
      loadDashboardAnalytics();
      break;
    case "leads":
      loadLeadsTable();
      break;
    case "technologies":
      loadTechCatalog();
      break;
    case "projects":
      loadProjects();
      break;
    case "lists":
      loadLeadLists();
      break;
    case "jobs":
      loadUnifiedJobs();
      break;
    case "webhooks":
      loadWebhooks();
      break;
    case "api-keys":
      loadApiKeys();
      break;
    case "settings":
      loadOrgSettings();
      break;
    case "audit-logs":
      loadAuditLogs();
      break;
    default:
      break;
  }

  if (window.lucide) lucide.createIcons();
}

function updateBreadcrumbs(route) {
  const sectionEl = document.getElementById("breadcrumb-section");
  const pageEl = document.getElementById("breadcrumb-page");
  if (!sectionEl || !pageEl) return;

  const titleMap = {
    dashboard: ["Overview", "Executive Intelligence"],
    discover: ["Discovery Engine", "Technology Fingerprinting"],
    leads: ["Leads Directory", "Verified Storefronts"],
    projects: ["Workspace", "Campaign Projects"],
    lists: ["Targeting", "Curated Lists"],
    technologies: ["Intelligence", "19 Tech Signatures"],
    jobs: ["Monitoring", "Background Workers"],
    imports: ["Ingestion", "Batch Domain Ingestion"],
    exports: ["Integrations", "Multi-Format Export Center"],
    webhooks: ["Integrations", "HMAC-SHA256 Webhooks"],
    "api-keys": ["Developers", "Production API & Keys"],
    settings: ["Governance", "Organization & Team"],
    "audit-logs": ["Compliance", "Operational Audit Logs"],
  };

  const [sec, pg] = titleMap[route] || ["LeadForge", route];
  sectionEl.innerText = sec;
  pageEl.innerText = pg;
}

// User Profile & Authentication
async function checkAuthMe() {
  try {
    const headers = {};
    if (state.token) headers["Authorization"] = `Bearer ${state.token}`;
    const res = await fetch("/api/v1/auth/me", { headers });
    if (res.ok) {
      const data = await res.json();
      state.user = data.user;
      state.org = data.organization;
      updateUserUI();
    }
  } catch (err) {
    console.warn("Auth check:", err);
  }
}

function updateUserUI() {
  if (state.user) {
    const emailEl = document.getElementById("user-display-email");
    const roleEl = document.getElementById("user-display-role");
    const initialsEl = document.getElementById("user-avatar-initials");
    const orgEl = document.getElementById("sidebar-org-name");

    if (emailEl) emailEl.innerText = state.user.email;
    if (roleEl) roleEl.innerText = state.user.role;
    if (initialsEl) initialsEl.innerText = state.user.email.substring(0, 2).toUpperCase();
    if (orgEl && state.org) orgEl.innerText = state.org.name;
  }
}

function openAuthModal() {
  document.getElementById("auth-modal")?.classList.remove("hidden");
}
function closeAuthModal() {
  document.getElementById("auth-modal")?.classList.add("hidden");
}
function fillDemoLogin() {
  const emailInput = document.getElementById("auth-email");
  const passInput = document.getElementById("auth-password");
  if (emailInput) emailInput.value = "admin@leadforge.io";
  if (passInput) passInput.value = "leadforge123";
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  const email = document.getElementById("auth-email").value.trim();
  const password = document.getElementById("auth-password").value;
  const btn = document.getElementById("auth-submit-btn");

  btn.disabled = true;
  btn.innerText = "Authenticating...";

  try {
    const res = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Authentication failed");
    }
    const data = await res.json();
    state.token = data.access_token;
    state.user = data.user;
    state.org = data.organization;
    localStorage.setItem("leadforge_token", data.access_token);
    updateUserUI();
    closeAuthModal();
    notifyUser("Success", `Logged in as ${data.user.email}`);
  } catch (err) {
    alert(err.message);
  } finally {
    btn.disabled = false;
    btn.innerText = "Sign In to Workspace";
  }
}

// Command Palette (⌘K)
const cmdKItems = [
  { title: "Jump to Dashboard", category: "Navigation", icon: "layout-dashboard", action: () => navigateRoute(null, "dashboard") },
  { title: "Launch Discovery Probe", category: "Discovery", icon: "sparkles", action: () => navigateRoute(null, "discover") },
  { title: "View Verified Leads Directory", category: "Navigation", icon: "database", action: () => navigateRoute(null, "leads") },
  { title: "Browse 19 Tech Signatures", category: "Intelligence", icon: "cpu", action: () => navigateRoute(null, "technologies") },
  { title: "Batch Import Domains", category: "Ingestion", icon: "upload-cloud", action: () => navigateRoute(null, "imports") },
  { title: "Export to Excel (.xlsx)", category: "Exports", icon: "file-spreadsheet", action: () => quickExportLeads("xlsx") },
  { title: "Export to CSV Spreadsheet", category: "Exports", icon: "file-text", action: () => quickExportLeads("csv") },
  { title: "Export to PDF Dossier", category: "Exports", icon: "file-check-2", action: () => quickExportLeads("pdf") },
  { title: "Manage Outbound Webhooks", category: "Integrations", icon: "webhook", action: () => navigateRoute(null, "webhooks") },
  { title: "Developer API & Keys", category: "Integrations", icon: "key-round", action: () => navigateRoute(null, "api-keys") },
  { title: "Organization & Team Settings", category: "Governance", icon: "users", action: () => navigateRoute(null, "settings") },
  { title: "Security Audit Trail", category: "Governance", icon: "shield-alert", action: () => navigateRoute(null, "audit-logs") },
  { title: "Toggle Light / Dark Theme", category: "System", icon: "sun-moon", action: () => toggleTheme() },
];

function openCmdK() {
  const modal = document.getElementById("cmd-k-modal");
  const input = document.getElementById("cmd-k-input");
  if (modal && input) {
    modal.classList.remove("hidden");
    input.value = "";
    input.focus();
    handleCmdKFilter("");
  }
}

function closeCmdK() {
  document.getElementById("cmd-k-modal")?.classList.add("hidden");
}

function handleCmdKFilter(query) {
  const q = query.toLowerCase().trim();
  state.filteredCmdK = cmdKItems.filter((it) =>
    it.title.toLowerCase().includes(q) || it.category.toLowerCase().includes(q)
  );
  state.cmdKIndex = 0;
  renderCmdKResults();
}

function renderCmdKResults() {
  const container = document.getElementById("cmd-k-results");
  if (!container) return;

  if (state.filteredCmdK.length === 0) {
    container.innerHTML = `<div class="py-6 text-center text-neutral-400 text-xs">No matching commands found</div>`;
    return;
  }

  container.innerHTML = state.filteredCmdK.map((item, idx) => `
    <div
      onclick="executeCmdKItem(${idx})"
      class="flex items-center justify-between px-3 py-2 rounded-xl cursor-pointer transition ${idx === state.cmdKIndex ? 'bg-[#ef4d23] text-white' : 'hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-800 dark:text-neutral-200'}"
    >
      <div class="flex items-center gap-2.5">
        <i data-lucide="${item.icon}" class="w-4 h-4 ${idx === state.cmdKIndex ? 'text-white' : 'text-neutral-400'}"></i>
        <span class="font-medium">${escapeHtml(item.title)}</span>
      </div>
      <span class="text-[10px] font-mono px-2 py-0.5 rounded ${idx === state.cmdKIndex ? 'bg-black/20 text-white' : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-400'}">${escapeHtml(item.category)}</span>
    </div>
  `).join("");

  if (window.lucide) lucide.createIcons();
}

function executeCmdKItem(idx) {
  const item = state.filteredCmdK[idx];
  if (item && item.action) {
    closeCmdK();
    item.action();
  }
}

function handleCmdKKeydown(e) {
  if (e.key === "Escape") {
    closeCmdK();
  } else if (e.key === "ArrowDown") {
    e.preventDefault();
    state.cmdKIndex = (state.cmdKIndex + 1) % state.filteredCmdK.length;
    renderCmdKResults();
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    state.cmdKIndex = (state.cmdKIndex - 1 + state.filteredCmdK.length) % state.filteredCmdK.length;
    renderCmdKResults();
  } else if (e.key === "Enter") {
    e.preventDefault();
    executeCmdKItem(state.cmdKIndex);
  }
}

document.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
    e.preventDefault();
    const modal = document.getElementById("cmd-k-modal");
    if (modal && modal.classList.contains("hidden")) {
      openCmdK();
    } else {
      closeCmdK();
    }
  }
});

// Notifications
function toggleNotifications() {
  document.getElementById("notifications-drawer")?.classList.toggle("hidden");
}

function notifyUser(title, message) {
  const drawer = document.getElementById("notifications-list");
  if (!drawer) return;
  const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const itemHtml = `
    <div class="p-2.5 rounded-xl bg-neutral-50 dark:bg-neutral-800/80 border border-neutral-200 dark:border-neutral-700 text-xs">
      <div class="flex items-center justify-between font-bold text-neutral-900 dark:text-white">
        <span>${escapeHtml(title)}</span>
        <span class="text-[10px] text-neutral-400 font-mono">${time}</span>
      </div>
      <p class="text-[11px] text-neutral-500 dark:text-neutral-400 mt-0.5">${escapeHtml(message)}</p>
    </div>
  `;
  if (drawer.innerText.includes("No recent notifications")) {
    drawer.innerHTML = itemHtml;
  } else {
    drawer.insertAdjacentHTML("afterbegin", itemHtml);
  }
}

// Dashboard Analytics Loader
async function loadDashboardAnalytics() {
  const icon = document.getElementById("dash-refresh-icon");
  if (icon) icon.classList.add("animate-spin");

  try {
    const res = await fetch("/api/v1/dashboard/analytics");
    if (!res.ok) throw new Error("Failed to load analytics");
    const data = await res.json();
    state.analytics = data;

    // Summary numbers
    const s = data.summary;
    const totalEl = document.getElementById("dash-stat-total");
    if (totalEl) totalEl.innerText = s.total_leads.toLocaleString();
    const liveEl = document.getElementById("dash-stat-live");
    if (liveEl) liveEl.innerText = s.live_leads.toLocaleString();
    const emailEl = document.getElementById("dash-stat-email");
    if (emailEl) emailEl.innerText = s.leads_with_email.toLocaleString();

    const sideLeadsCount = document.getElementById("sidebar-leads-count");
    if (sideLeadsCount) sideLeadsCount.innerText = s.total_leads.toLocaleString();

    // Render Recent Genuine Verified Leads Table
    const recentTable = document.getElementById("dash-recent-leads-tbody");
    if (recentTable) {
      if (data.recent_leads && data.recent_leads.length > 0) {
        recentTable.innerHTML = data.recent_leads.map(l => {
          const techName = l.primary_technology || "Standard Web";
          const sslBadge = l.has_ssl
            ? `<span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400">SSL Valid</span>`
            : `<span class="px-1.5 py-0.5 rounded text-[10px] font-medium bg-neutral-200 dark:bg-neutral-800 text-neutral-500">No SSL</span>`;
          const httpBadge = (l.http_status === 200 || l.status === "LIVE")
            ? `<span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400">HTTP 200</span>`
            : `<span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400">${l.http_status || 'Live'}</span>`;
          const emailDisplay = l.primary_email
            ? `<a href="mailto:${escapeHtml(l.primary_email)}" class="text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 font-mono text-[11px]"><i data-lucide="mail" class="w-3 h-3"></i>${escapeHtml(l.primary_email)}</a>`
            : `<span class="text-neutral-400 text-[11px]">—</span>`;

          return `
            <tr class="hover:bg-neutral-50 dark:hover:bg-neutral-800/40 transition">
              <td class="py-3 px-4">
                <div class="font-bold text-neutral-900 dark:text-white">${escapeHtml(l.business_name || l.domain)}</div>
                <a href="${escapeHtml(l.canonical_url || 'https://' + l.domain)}" target="_blank" class="text-neutral-400 hover:text-[#ef4d23] text-[11px] font-mono flex items-center gap-1">
                  <span>${escapeHtml(l.domain)}</span>
                  <i data-lucide="external-link" class="w-3 h-3"></i>
                </a>
              </td>
              <td class="py-3 px-3">
                <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-semibold text-[11px] bg-orange-100 dark:bg-orange-950/80 text-[#ef4d23] border border-orange-200/80 dark:border-orange-800/40">
                  <i data-lucide="tag" class="w-3 h-3"></i>
                  <span>${escapeHtml(techName)}</span>
                </span>
              </td>
              <td class="py-3 px-3">
                <div class="flex items-center gap-1.5 flex-wrap">
                  ${httpBadge}
                  <span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-400">DNS OK</span>
                  ${sslBadge}
                </div>
              </td>
              <td class="py-3 px-3">${emailDisplay}</td>
              <td class="py-3 px-3 text-neutral-500 dark:text-neutral-400 font-medium">${escapeHtml(l.country || 'United Kingdom')}</td>
              <td class="py-3 px-4 text-right">
                <div class="flex items-center justify-end gap-1.5">
                  <button onclick="openLeadDossier(${l.id})" class="bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-800 dark:text-neutral-200 text-[11px] font-bold px-2.5 py-1 rounded-lg transition inline-flex items-center gap-1 cursor-pointer">
                    <i data-lucide="file-text" class="w-3 h-3 text-[#ef4d23]"></i>
                    <span>Dossier</span>
                  </button>
                  <button onclick="reverifyLeadInline(${l.id}, this)" class="bg-white dark:bg-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-700 border border-neutral-200 dark:border-neutral-700 text-neutral-700 dark:text-neutral-300 text-[11px] font-semibold px-2 py-1 rounded-lg transition inline-flex items-center gap-1 cursor-pointer" title="Re-verify HTTP & DNS">
                    <i data-lucide="refresh-cw" class="w-3 h-3 text-neutral-400"></i>
                  </button>
                </div>
              </td>
            </tr>
          `;
        }).join("");
      } else {
        recentTable.innerHTML = `
          <tr>
            <td colspan="6" class="text-center py-12 text-neutral-400">
              <div class="max-w-sm mx-auto space-y-2">
                <i data-lucide="search" class="w-8 h-8 text-neutral-300 dark:text-neutral-600 mx-auto"></i>
                <div class="font-medium text-neutral-700 dark:text-neutral-300 text-sm">No verified leads yet</div>
                <p class="text-xs text-neutral-400">Use the search box above to discover and verify your first technology leads.</p>
              </div>
            </td>
          </tr>
        `;
      }
    }

    if (window.lucide) lucide.createIcons();

  } catch (err) {
    console.error("Dashboard error:", err);
  } finally {
    if (icon) icon.classList.remove("animate-spin");
  }
}

// Hero Search Controls
function setHeroSearch(tech, country) {
  const techSelect = document.getElementById("hero-tech-select");
  const geoInput = document.getElementById("hero-geo-input");
  if (techSelect) techSelect.value = tech;
  if (geoInput) geoInput.value = country;
  executeHeroSearch();
}

async function executeHeroSearch() {
  const techSelect = document.getElementById("hero-tech-select");
  const geoInput = document.getElementById("hero-geo-input");
  const tech = techSelect ? techSelect.value : "OpenCart";
  const geo = geoInput ? geoInput.value.trim() : "United Kingdom";

  // Switch to discover view
  navigateRoute(null, "discover");

  // Populate discovery form inputs
  const discTech = document.getElementById("disc-tech-select");
  const discCountry = document.getElementById("disc-country-input");
  if (discTech) discTech.value = tech;
  if (discCountry) discCountry.value = geo;

  // Execute discovery automatically
  executeDiscovery(new Event("submit"));
}

// Inline Re-verify Lead
async function reverifyLeadInline(leadId, btn) {
  if (!btn) return;
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader-2" class="w-3 h-3 animate-spin text-[#ef4d23]"></i>`;
  if (window.lucide) lucide.createIcons();

  try {
    const res = await fetch(`/api/v1/leads/${leadId}/refresh`, { method: "POST" });
    if (!res.ok) throw new Error("Re-verification failed");
    btn.innerHTML = `<i data-lucide="check" class="w-3 h-3 text-emerald-500"></i>`;
    if (window.lucide) lucide.createIcons();
    setTimeout(() => {
      loadDashboardAnalytics();
      loadLeadsTable();
    }, 500);
  } catch (err) {
    btn.innerHTML = `<i data-lucide="alert-circle" class="w-3 h-3 text-red-500"></i>`;
    if (window.lucide) lucide.createIcons();
    setTimeout(() => {
      btn.disabled = false;
      btn.innerHTML = originalHtml;
      if (window.lucide) lucide.createIcons();
    }, 2000);
  }
}


function refreshDashboardAnalytics() {
  loadDashboardAnalytics();
}

// Leads Directory Engine
async function loadLeadsTable() {
  const tbody = document.getElementById("leads-table-tbody");
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="8" class="text-center py-12 text-neutral-400">Querying database...</td></tr>`;

  let url = `/api/v1/leads?limit=${state.leadsLimit}&offset=${state.leadsOffset}&sort_by=${state.leadsFilters.sort_by}`;
  if (state.leadsFilters.query) url += `&query=${encodeURIComponent(state.leadsFilters.query)}`;
  if (state.leadsFilters.technology) url += `&technology=${encodeURIComponent(state.leadsFilters.technology)}`;
  if (state.leadsFilters.country) url += `&country=${encodeURIComponent(state.leadsFilters.country)}`;
  if (state.leadsFilters.status) url += `&status=${encodeURIComponent(state.leadsFilters.status)}`;
  if (state.leadsFilters.has_email !== null) url += `&has_email=${state.leadsFilters.has_email}`;
  if (state.leadsFilters.min_score !== null) url += `&min_score=${state.leadsFilters.min_score}`;

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch leads");
    const data = await res.json();
    state.leads = data.leads || [];
    state.leadsTotal = data.total || 0;

    renderLeadsRows();
    updatePaginationUI();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-8 text-red-500">Error loading leads: ${escapeHtml(err.message)}</td></tr>`;
  }
}

function renderLeadsRows() {
  const tbody = document.getElementById("leads-table-tbody");
  if (!tbody) return;

  if (state.leads.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-12 text-neutral-400">No leads match the specified filter criteria.</td></tr>`;
    return;
  }

  tbody.innerHTML = state.leads.map((l) => {
    const isSelected = state.selectedLeadIds.has(l.id);
    const scoreColor = l.lead_score >= 80 ? "bg-orange-100 text-[#ef4d23] dark:bg-orange-950 dark:text-orange-300" :
                       l.lead_score >= 60 ? "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300" :
                       "bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400";
    const statusColor = l.status === "LIVE" ? "text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950" : "text-neutral-500 bg-neutral-100 dark:bg-neutral-800";

    return `
      <tr class="hover:bg-neutral-50 dark:hover:bg-neutral-800/50 transition">
        <td class="py-3 px-4">
          <input type="checkbox" ${isSelected ? "checked" : ""} onchange="toggleLeadSelection(${l.id}, this.checked)" class="rounded text-[#ef4d23] focus:ring-[#ef4d23] w-3.5 h-3.5" />
        </td>
        <td class="py-3 px-4 font-medium text-neutral-900 dark:text-white">
          <div class="flex items-center gap-2">
            <span class="font-bold truncate max-w-[180px]">${escapeHtml(l.business_name || l.domain)}</span>
            <a href="${escapeHtml(l.canonical_url || 'http://' + l.domain)}" target="_blank" class="text-neutral-400 hover:text-[#ef4d23]" title="Open target website">
              <i data-lucide="external-link" class="w-3 h-3"></i>
            </a>
          </div>
          <span class="text-[10px] font-mono text-neutral-400 block">${escapeHtml(l.domain)}</span>
        </td>
        <td class="py-3 px-3">
          <span class="inline-flex items-center gap-1 font-semibold px-2 py-0.5 rounded-full text-[11px] bg-neutral-100 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200">
            <span>${escapeHtml(l.primary_technology || 'Web Standard')}</span>
            <span class="text-[10px] text-neutral-400 font-mono">${Math.round((l.technology_confidence || 1) * 100)}%</span>
          </span>
        </td>
        <td class="py-3 px-3">
          <span class="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${statusColor}">
            ● ${escapeHtml(l.status)}
          </span>
        </td>
        <td class="py-3 px-3 font-medium">
          ${escapeHtml(l.country || 'Global')}
        </td>
        <td class="py-3 px-3">
          ${l.primary_email ? `<a href="mailto:${escapeHtml(l.primary_email)}" class="text-emerald-600 dark:text-emerald-400 hover:underline font-mono text-[11px] block">✉ ${escapeHtml(l.primary_email)}</a>` : '<span class="text-neutral-400 text-[11px]">—</span>'}
          ${l.primary_phone ? `<span class="text-[10px] font-mono text-neutral-400 block">📞 ${escapeHtml(l.primary_phone)}</span>` : ''}
        </td>
        <td class="py-3 px-3 text-center">
          <span class="inline-block font-mono font-bold px-2 py-0.5 rounded-md text-xs ${scoreColor}">
            ${l.lead_score}
          </span>
        </td>
        <td class="py-3 px-4 text-right">
          <button onclick="openLeadDossier(${l.id})" class="bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 dark:hover:bg-neutral-700 text-neutral-800 dark:text-neutral-200 text-[11px] font-bold px-2.5 py-1 rounded-lg transition inline-flex items-center gap-1">
            <i data-lucide="eye" class="w-3 h-3"></i> Dossier
          </button>
        </td>
      </tr>
    `;
  }).join("");

  if (window.lucide) lucide.createIcons();
}

function updatePaginationUI() {
  const info = document.getElementById("leads-pagination-info");
  const pageNum = document.getElementById("leads-page-number");
  const btnPrev = document.getElementById("btn-prev-page");
  const btnNext = document.getElementById("btn-next-page");

  const currentPage = Math.floor(state.leadsOffset / state.leadsLimit) + 1;
  const totalPages = Math.ceil(state.leadsTotal / state.leadsLimit) || 1;

  if (info) info.innerText = `Showing ${Math.min(state.leadsOffset + 1, state.leadsTotal)} to ${Math.min(state.leadsOffset + state.leadsLimit, state.leadsTotal)} of ${state.leadsTotal} leads`;
  if (pageNum) pageNum.innerText = `Page ${currentPage} of ${totalPages}`;

  if (btnPrev) btnPrev.disabled = state.leadsOffset === 0;
  if (btnNext) btnNext.disabled = state.leadsOffset + state.leadsLimit >= state.leadsTotal;
}

function changeLeadsPage(delta) {
  state.leadsOffset = Math.max(0, state.leadsOffset + delta * state.leadsLimit);
  loadLeadsTable();
}

let searchDebounceTimeout = null;
function handleLeadsSearch(val) {
  clearTimeout(searchDebounceTimeout);
  searchDebounceTimeout = setTimeout(() => {
    state.leadsFilters.query = val.trim();
    state.leadsOffset = 0;
    loadLeadsTable();
  }, 300);
}

function triggerLeadsFilterUpdate() {
  state.leadsFilters.technology = document.getElementById("leads-filter-tech").value;
  state.leadsFilters.country = document.getElementById("leads-filter-country").value;
  state.leadsFilters.sort_by = document.getElementById("leads-filter-sort").value;
  state.leadsOffset = 0;
  loadLeadsTable();
}

function filterLeadsByPreset(preset) {
  state.leadsFilters.preset = preset;
  ["all", "hot", "email", "live"].forEach((p) => {
    const b = document.getElementById(`preset-${p}`);
    if (b) {
      if (p === preset) {
        b.className = "px-3 py-1 rounded-full text-xs font-bold transition bg-[#0b0f1a] text-white dark:bg-white dark:text-black";
      } else {
        b.className = "px-3 py-1 rounded-full text-xs font-bold transition text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800";
      }
    }
  });

  state.leadsFilters.min_score = null;
  state.leadsFilters.has_email = null;
  state.leadsFilters.status = "";

  if (preset === "hot") state.leadsFilters.min_score = 80;
  if (preset === "email") state.leadsFilters.has_email = true;
  if (preset === "live") state.leadsFilters.status = "LIVE";

  state.leadsOffset = 0;
  loadLeadsTable();
}

function toggleLeadSelection(id, checked) {
  if (checked) state.selectedLeadIds.add(id);
  else state.selectedLeadIds.delete(id);
}

function toggleSelectAllLeads(checked) {
  state.leads.forEach(l => {
    if (checked) state.selectedLeadIds.add(l.id);
    else state.selectedLeadIds.delete(l.id);
  });
  renderLeadsRows();
}

// Lead Dossier Modal
async function openLeadDossier(leadId) {
  const modal = document.getElementById("lead-dossier-modal");
  if (!modal) return;
  modal.classList.remove("hidden");

  try {
    const res = await fetch(`/api/v1/leads/${leadId}`);
    if (!res.ok) throw new Error("Lead details not found");
    const lead = await res.json();

    document.getElementById("dossier-title").innerText = lead.business_name || lead.domain;
    const urlEl = document.getElementById("dossier-url");
    urlEl.innerText = lead.canonical_url || `https://${lead.domain}`;
    urlEl.href = lead.canonical_url || `https://${lead.domain}`;

    document.getElementById("dossier-score").innerText = `${lead.lead_score}/100 (${lead.score_label})`;
    document.getElementById("dossier-tech").innerText = `${lead.primary_technology} (${Math.round(lead.technology_confidence * 100)}%)`;
    document.getElementById("dossier-latency").innerText = `${Math.round(lead.response_time_ms)}ms`;
    document.getElementById("dossier-location").innerText = `${lead.country || 'Global'} (${lead.industry || 'E-commerce'})`;

    const sslEl = document.getElementById("dossier-ssl-badge");
    if (lead.has_ssl) {
      sslEl.innerText = "HTTPS Valid";
      sslEl.className = "px-1.5 py-0.2 rounded text-[10px] font-bold bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-400";
    } else {
      sslEl.innerText = "HTTP Insecure";
      sslEl.className = "px-1.5 py-0.2 rounded text-[10px] font-bold bg-neutral-200 text-neutral-600";
    }

    // Evidence
    const evList = document.getElementById("dossier-evidence-list");
    if (lead.evidence && lead.evidence.length) {
      evList.innerHTML = lead.evidence.map(e => `<li>✓ ${escapeHtml(e)}</li>`).join("");
    } else {
      evList.innerHTML = `<li>• No explicit technology evidence records found.</li>`;
    }

    // Contacts
    const conList = document.getElementById("dossier-contacts-list");
    let conHtml = "";
    if (lead.emails && lead.emails.length) {
      conHtml += lead.emails.map(em => `<div class="font-mono text-emerald-600 dark:text-emerald-400">✉ ${escapeHtml(em.value)} <span class="text-neutral-400 text-[10px]">(${em.role_type})</span></div>`).join("");
    }
    if (lead.phones && lead.phones.length) {
      conHtml += lead.phones.map(p => `<div class="font-mono text-neutral-700 dark:text-neutral-300">📞 ${escapeHtml(p.value)}</div>`).join("");
    }
    conList.innerHTML = conHtml || `<span class="text-neutral-400">No public contacts detected on crawl.</span>`;

    // Wire reverify
    const reverifyBtn = document.getElementById("dossier-btn-reverify");
    reverifyBtn.onclick = async () => {
      reverifyBtn.innerText = "Probing...";
      await fetch(`/api/v1/leads/${leadId}/refresh`, { method: "POST" });
      openLeadDossier(leadId);
      loadLeadsTable();
      reverifyBtn.innerHTML = `<i data-lucide="check" class="w-3.5 h-3.5"></i> Re-verified!`;
      if (window.lucide) lucide.createIcons();
    };

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    alert(err.message);
  }
}

function closeDossierModal() {
  document.getElementById("lead-dossier-modal")?.classList.add("hidden");
}

// Discovery Engine Execution
async function executeDiscovery(e) {
  e.preventDefault();
  const tech = document.getElementById("disc-tech-select").value;
  const country = document.getElementById("disc-country-input").value.trim();
  const industry = document.getElementById("disc-industry-input").value.trim();
  const limit = parseInt(document.getElementById("disc-limit-select").value, 10) || 20;
  const requireEmail = document.getElementById("disc-email-toggle").checked;

  const card = document.getElementById("probe-execution-card");
  card.classList.remove("hidden");

  const btn = document.getElementById("btn-start-probe");
  btn.disabled = true;
  btn.innerText = "Dispatching Discovery Workers...";

  try {
    const res = await fetch("/api/v1/discover", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        technology: tech,
        country: country || null,
        industry: industry || null,
        limit: limit,
        require_email: requireEmail,
      }),
    });
    if (!res.ok) throw new Error("Failed to initialize discovery job");
    const data = await res.json();
    const jobId = data.job_id;

    document.getElementById("probe-job-id").innerText = `Job: ${jobId.substring(0, 8)}...`;
    listenToSSEStream(jobId);
    notifyUser("Discovery Job Started", `Probing for ${tech} storefronts in ${country || 'Global'}`);
  } catch (err) {
    alert(`Discovery error: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="zap" class="w-4 h-4"></i> Launch Live Verification Probe`;
    if (window.lucide) lucide.createIcons();
  }
}

function listenToSSEStream(jobId) {
  if (state.activeSSE) state.activeSSE.close();

  const logBox = document.getElementById("probe-stream-logs");
  const pBar = document.getElementById("probe-progress-bar");
  const pStep = document.getElementById("probe-step-label");
  const pPct = document.getElementById("probe-pct-label");
  const candEl = document.getElementById("probe-candidates-count");
  const verEl = document.getElementById("probe-verified-count");
  const qualEl = document.getElementById("probe-qualified-count");

  logBox.innerHTML = "";
  const es = new EventSource(`/api/v1/discover/${jobId}/stream`);
  state.activeSSE = es;

  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      const logLine = document.createElement("div");
      logLine.innerText = `[${data.stage || 'PROGRESS'}] ${data.message || ''}`;
      logBox.appendChild(logLine);
      logBox.scrollTop = logBox.scrollHeight;

      if (data.progress !== undefined) {
        pBar.style.width = `${data.progress}%`;
        pPct.innerText = `${data.progress}%`;
      }
      if (data.message) pStep.innerText = data.message;
      if (data.candidates_count) candEl.innerText = data.candidates_count;
      if (data.verified_count) verEl.innerText = data.verified_count;
      if (data.qualified_count) qualEl.innerText = data.qualified_count;

      if (data.status === "COMPLETED" || data.status === "FAILED") {
        es.close();
        document.getElementById("probe-status-badge").innerText = data.status;
        document.getElementById("probe-status-badge").className = data.status === "COMPLETED" ?
          "px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 font-bold" :
          "px-2 py-0.5 rounded bg-red-950 text-red-400 font-bold";
        loadDashboardAnalytics();
      }
    } catch (err) {
      console.warn("SSE parse error:", err);
    }
  };

  es.onerror = () => {
    es.close();
  };
}

// Natural Language Search Parser
let nlDebounce = null;
function handleNLInput(val) {
  clearTimeout(nlDebounce);
  if (!val.trim()) {
    document.getElementById("nl-parsed-tags")?.classList.add("hidden");
    return;
  }
  nlDebounce = setTimeout(() => {
    parseNLQueryApi(val);
  }, 400);
}

async function parseNLQueryApi(q) {
  try {
    const res = await fetch(`/api/v1/search/parse?q=${encodeURIComponent(q)}`);
    if (!res.ok) return;
    const data = await res.json();
    const tagsContainer = document.getElementById("nl-tags-container");
    const parentBox = document.getElementById("nl-parsed-tags");
    if (!tagsContainer || !parentBox) return;

    let html = "";
    if (data.technology) html += `<span class="bg-orange-100 dark:bg-orange-950 text-[#ef4d23] px-2 py-0.5 rounded font-bold">Tech: ${escapeHtml(data.technology)}</span>`;
    if (data.country) html += `<span class="bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded font-bold">Region: ${escapeHtml(data.country)}</span>`;
    if (data.has_email) html += `<span class="bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 px-2 py-0.5 rounded font-bold">Require Email</span>`;
    if (data.min_score) html += `<span class="bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded font-bold">Min Score: ${data.min_score}</span>`;

    tagsContainer.innerHTML = html || `<span class="text-neutral-400">Standard discovery query</span>`;
    parentBox.classList.remove("hidden");

    // Pre-populate fields
    if (data.technology) document.getElementById("disc-tech-select").value = data.technology;
    if (data.country) document.getElementById("disc-country-input").value = data.country;
    if (data.has_email) document.getElementById("disc-email-toggle").checked = true;
  } catch (err) {
    console.warn(err);
  }
}

function applyNLQuery() {
  const input = document.getElementById("nl-query-input");
  if (input) parseNLQueryApi(input.value);
}

// Technologies Catalog
async function loadTechCatalog() {
  const grid = document.getElementById("tech-cards-grid");
  if (!grid) return;

  try {
    const res = await fetch("/api/v1/technologies");
    if (!res.ok) throw new Error("Failed to load technologies");
    state.technologies = await res.json();
    renderTechCards(state.technologies);
  } catch (err) {
    grid.innerHTML = `<div class="col-span-3 text-center text-red-500 py-8">${escapeHtml(err.message)}</div>`;
  }
}

function renderTechCards(list) {
  const grid = document.getElementById("tech-cards-grid");
  if (!grid) return;

  grid.innerHTML = list.map(t => `
    <div class="bg-white dark:bg-neutral-900 rounded-2xl p-5 border border-neutral-200/80 dark:border-neutral-800/80 shadow-xs flex flex-col justify-between">
      <div>
        <div class="flex items-center justify-between mb-2">
          <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400">${escapeHtml(t.category)}</span>
          <span class="text-xs font-bold text-[#ef4d23] font-mono">${t.verified_leads_count} Leads</span>
        </div>
        <h3 class="font-bold text-base text-neutral-900 dark:text-white">${escapeHtml(t.name)}</h3>
        <p class="text-xs text-neutral-500 mt-1 line-clamp-2">${escapeHtml(t.description || 'Deterministic fingerprint rules.')}</p>
      </div>

      <div class="mt-4 pt-3 border-t border-neutral-100 dark:border-neutral-800 flex items-center justify-between text-xs">
        <span class="font-mono text-[11px] text-neutral-400">${t.patterns_count} heuristics</span>
        <button onclick="selectTechForProbe('${escapeHtml(t.name)}')" class="font-bold text-[#ef4d23] hover:underline flex items-center gap-1">
          <span>Find Leads</span> &rarr;
        </button>
      </div>
    </div>
  `).join("");

  if (window.lucide) lucide.createIcons();
}

function filterTechCategory(cat) {
  if (cat === "all") {
    renderTechCards(state.technologies);
  } else {
    const filtered = state.technologies.filter(t => t.category.toLowerCase().includes(cat.toLowerCase()));
    renderTechCards(filtered);
  }
}

function selectTechForProbe(name) {
  document.getElementById("disc-tech-select").value = name;
  navigateRoute(null, "discover");
}

// Unified Background Jobs
async function loadUnifiedJobs() {
  const tbody = document.getElementById("jobs-table-tbody");
  if (!tbody) return;

  try {
    const res = await fetch("/api/v1/jobs");
    if (!res.ok) throw new Error("Failed to load jobs");
    const jobs = await res.json();
    state.jobs = jobs;

    if (!jobs.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-12 text-neutral-400">No background jobs executed yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = jobs.map(j => {
      const statusColor = j.status === "COMPLETED" ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300" :
                          j.status === "RUNNING" ? "bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300 animate-pulse" :
                          j.status === "FAILED" ? "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300" :
                          "bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-400";

      const time = j.created_at ? new Date(j.created_at).toLocaleString([], { dateStyle: "short", timeStyle: "short" }) : "--";

      return `
        <tr class="hover:bg-neutral-50 dark:hover:bg-neutral-800/50">
          <td class="py-3 px-4 font-mono text-[11px] text-neutral-800 dark:text-neutral-200">${escapeHtml(j.id ? j.id.substring(0, 10) + '...' : '--')}</td>
          <td class="py-3 px-3 uppercase text-[10px] font-bold text-neutral-400">${escapeHtml(j.job_type || 'job')}</td>
          <td class="py-3 px-3 font-medium text-neutral-800 dark:text-neutral-200">${escapeHtml(j.description || '--')}</td>
          <td class="py-3 px-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${statusColor}">${escapeHtml(j.status)}</span></td>
          <td class="py-3 px-3 font-mono text-[11px]">${j.progress_percent !== undefined ? j.progress_percent + '%' : (j.row_count !== undefined ? j.row_count + ' rows' : '--')}</td>
          <td class="py-3 px-4 text-right text-neutral-400 font-mono text-[11px]">${time}</td>
        </tr>
      `;
    }).join("");

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-8 text-red-500">${escapeHtml(err.message)}</td></tr>`;
  }
}

// Batch Ingestion
async function executeBatchImport() {
  const text = document.getElementById("import-domains-textarea").value.trim();
  const autoVerify = document.getElementById("import-auto-verify").checked;
  const btn = document.getElementById("btn-batch-import");

  if (!text) {
    alert("Please provide at least one domain or URL to ingest.");
    return;
  }

  btn.disabled = true;
  btn.innerText = "Ingesting & Filtering...";

  try {
    const res = await fetch("/api/v1/import/text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: text,
        enqueue_verification: autoVerify,
      }),
    });
    if (!res.ok) throw new Error("Failed to ingest domain list");
    const data = await res.json();

    document.getElementById("import-new-count").innerText = data.unique_new_count || 0;
    document.getElementById("import-dup-count").innerText = data.duplicate_count || 0;
    document.getElementById("import-inv-count").innerText = data.invalid_count || 0;
    document.getElementById("import-result-summary").classList.remove("hidden");

    notifyUser("Ingestion Finished", `Ingested ${data.unique_new_count} new domains, skipped ${data.duplicate_count} duplicates.`);
    loadDashboardAnalytics();
  } catch (err) {
    alert(err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="upload" class="w-3.5 h-3.5"></i> Ingest &amp; Deduplicate`;
    if (window.lucide) lucide.createIcons();
  }
}

// Direct & Async Exports
function quickExportLeads(format) {
  triggerDirectExport(format);
}

function triggerDirectExport(format) {
  let q = "";
  if (state.leadsFilters.technology) q += `&technology=${encodeURIComponent(state.leadsFilters.technology)}`;
  if (state.leadsFilters.country) q += `&country=${encodeURIComponent(state.leadsFilters.country)}`;
  if (state.leadsFilters.min_score) q += `&min_score=${state.leadsFilters.min_score}`;
  window.location.href = `/api/v1/exports/${format}?${q}`;
}

async function startAsyncExportJob() {
  const format = document.getElementById("async-export-format").value;
  try {
    const res = await fetch("/api/v1/exports/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        format: format,
        technology: state.leadsFilters.technology || null,
        country: state.leadsFilters.country || null,
        min_score: state.leadsFilters.min_score || null,
        limit: 50000,
      }),
    });
    if (!res.ok) throw new Error("Failed to create export worker");
    const data = await res.json();
    notifyUser("Export Worker Dispatched", `Building ${format.toUpperCase()} export (Job ID: ${data.id.substring(0, 8)})`);
    navigateRoute(null, "jobs");
  } catch (err) {
    alert(err.message);
  }
}

// Webhooks
async function loadWebhooks() {
  const container = document.getElementById("webhooks-list");
  if (!container) return;

  try {
    const res = await fetch("/api/v1/webhooks");
    if (!res.ok) throw new Error("Failed to fetch webhooks");
    const hooks = await res.json();
    state.webhooks = hooks;

    if (!hooks.length) {
      container.innerHTML = `<div class="py-6 text-center text-neutral-400 text-xs">No webhooks registered yet.</div>`;
      return;
    }

    container.innerHTML = hooks.map(h => `
      <div class="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/60 border border-neutral-200 dark:border-neutral-700/80 flex items-center justify-between gap-4 text-xs">
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <strong class="font-mono text-neutral-900 dark:text-white truncate">${escapeHtml(h.url)}</strong>
            <span class="px-1.5 py-0.2 rounded text-[10px] font-bold ${h.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-neutral-200 text-neutral-600'}">${h.is_active ? 'ACTIVE' : 'INACTIVE'}</span>
          </div>
          <span class="text-[11px] text-neutral-500 block mt-0.5">Events: ${(h.events || []).join(", ")}</span>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <button onclick="pingWebhook(${h.id})" class="bg-white dark:bg-neutral-700 border border-neutral-300 dark:border-neutral-600 px-2.5 py-1 rounded-lg text-xs font-bold transition flex items-center gap-1">
            <i data-lucide="send" class="w-3 h-3 text-blue-500"></i> Ping
          </button>
          <button onclick="deleteWebhook(${h.id})" class="text-red-500 hover:text-red-700 p-1">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    `).join("");

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    container.innerHTML = `<div class="text-red-500 py-4 text-xs">${escapeHtml(err.message)}</div>`;
  }
}

async function registerNewWebhook() {
  const url = document.getElementById("hook-url-input").value.trim();
  const secret = document.getElementById("hook-secret-input").value.trim();
  if (!url) {
    alert("Please provide a valid payload URL.");
    return;
  }

  const events = [];
  if (document.getElementById("hook-evt-created").checked) events.push("lead.created");
  if (document.getElementById("hook-evt-verified").checked) events.push("lead.verified");
  if (document.getElementById("hook-evt-tech").checked) events.push("technology.changed");
  if (document.getElementById("hook-evt-export").checked) events.push("export.completed");

  try {
    const res = await fetch("/api/v1/webhooks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, secret: secret || undefined, events }),
    });
    if (!res.ok) throw new Error("Webhook registration failed");
    document.getElementById("hook-url-input").value = "";
    document.getElementById("hook-secret-input").value = "";
    loadWebhooks();
    notifyUser("Webhook Registered", url);
  } catch (err) {
    alert(err.message);
  }
}

async function pingWebhook(id) {
  try {
    const res = await fetch(`/api/v1/webhooks/${id}/ping`, { method: "POST" });
    const data = await res.json();
    alert(`Webhook ping response:\nHTTP ${data.status_code || 200}\nSignature: ${data.signature ? 'Verified HMAC-SHA256' : 'Sent'}`);
  } catch (err) {
    alert(`Ping failed: ${err.message}`);
  }
}

async function deleteWebhook(id) {
  if (!confirm("Are you sure you want to remove this webhook?")) return;
  try {
    await fetch(`/api/v1/webhooks/${id}`, { method: "DELETE" });
    loadWebhooks();
  } catch (err) {
    alert(err.message);
  }
}

// API Keys
async function loadApiKeys() {
  const tbody = document.getElementById("api-keys-table-tbody");
  if (!tbody) return;

  try {
    const res = await fetch("/api/v1/api-keys");
    if (!res.ok) throw new Error("Failed to load API keys");
    const keys = await res.json();
    state.apiKeys = keys;

    if (!keys.length) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center py-6 text-neutral-400">No active API keys found.</td></tr>`;
      return;
    }

    tbody.innerHTML = keys.map(k => `
      <tr class="hover:bg-neutral-50 dark:hover:bg-neutral-800/50">
        <td class="py-2.5 px-3 font-semibold text-neutral-900 dark:text-white">${escapeHtml(k.name)}</td>
        <td class="py-2.5 px-3 font-mono text-[11px] text-neutral-500">${escapeHtml(k.prefix)}...</td>
        <td class="py-2.5 px-3 text-neutral-400 font-mono text-[11px]">${k.created_at ? new Date(k.created_at).toLocaleDateString() : '--'}</td>
        <td class="py-2.5 px-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${k.is_active ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' : 'bg-neutral-200 text-neutral-600'}">${k.is_active ? 'ACTIVE' : 'REVOKED'}</span></td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4 text-red-500">${escapeHtml(err.message)}</td></tr>`;
  }
}

async function generateApiKey() {
  const name = document.getElementById("new-api-key-name").value.trim() || "Production Integration";
  try {
    const res = await fetch("/api/v1/api-keys", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    if (!res.ok) throw new Error("Failed to generate key");
    const data = await res.json();
    document.getElementById("new-key-secret-val").innerText = data.api_key;
    document.getElementById("new-key-secret-box").classList.remove("hidden");
    loadApiKeys();
  } catch (err) {
    alert(err.message);
  }
}

// Settings & Organization
async function loadOrgSettings() {
  try {
    const res = await fetch("/api/v1/organization");
    if (!res.ok) return;
    const org = await res.json();
    document.getElementById("settings-org-name-input").value = org.name;
    document.getElementById("settings-org-slug-input").value = org.slug;

    loadOrgMembers();
  } catch (err) {
    console.warn(err);
  }
}

async function saveOrgSettings() {
  const name = document.getElementById("settings-org-name-input").value.trim();
  try {
    const res = await fetch("/api/v1/organization", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    if (!res.ok) throw new Error("Failed to update organization name");
    alert("Organization settings updated successfully!");
    checkAuthMe();
  } catch (err) {
    alert(err.message);
  }
}

async function loadOrgMembers() {
  const tbody = document.getElementById("team-members-table-tbody");
  if (!tbody) return;

  try {
    const res = await fetch("/api/v1/organization/members");
    if (!res.ok) throw new Error("Failed to load members");
    const members = await res.json();
    state.members = members;

    tbody.innerHTML = members.map(m => `
      <tr class="hover:bg-neutral-50 dark:hover:bg-neutral-800/50">
        <td class="py-2.5 px-3 font-semibold text-neutral-900 dark:text-white">${escapeHtml(m.email)}</td>
        <td class="py-2.5 px-3 font-mono text-[11px] capitalize text-[#ef4d23] font-bold">${escapeHtml(m.role)}</td>
        <td class="py-2.5 px-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${m.is_active ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' : 'bg-neutral-200 text-neutral-600'}">${m.is_active ? 'ACTIVE' : 'DEACTIVATED'}</span></td>
        <td class="py-2.5 px-3 text-right">
          ${m.role !== 'owner' ? `<button onclick="removeOrgMember(${m.id})" class="text-red-500 hover:text-red-700 text-xs font-bold">Remove</button>` : '<span class="text-neutral-400">—</span>'}
        </td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4 text-red-500">${escapeHtml(err.message)}</td></tr>`;
  }
}

async function removeOrgMember(id) {
  if (!confirm("Are you sure you want to remove this member?")) return;
  try {
    await fetch(`/api/v1/organization/members/${id}`, { method: "DELETE" });
    loadOrgMembers();
  } catch (err) {
    alert(err.message);
  }
}

// Audit Logs
async function loadAuditLogs() {
  const tbody = document.getElementById("audit-logs-table-tbody");
  if (!tbody) return;

  try {
    const res = await fetch("/api/v1/audit-logs");
    if (!res.ok) throw new Error("Failed to load audit logs");
    const data = await res.json();
    const logs = data.audit_logs || [];
    state.auditLogs = logs;

    if (!logs.length) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center py-12 text-neutral-400">No audit events recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = logs.map(l => {
      const time = l.created_at ? new Date(l.created_at).toLocaleString([], { dateStyle: "short", timeStyle: "short" }) : "--";
      return `
        <tr class="hover:bg-neutral-50 dark:hover:bg-neutral-800/50">
          <td class="py-3 px-4 font-mono text-[11px] text-neutral-400">${time}</td>
          <td class="py-3 px-3 font-bold text-neutral-900 dark:text-white font-mono text-xs">${escapeHtml(l.action)}</td>
          <td class="py-3 px-3 text-neutral-600 dark:text-neutral-300 font-medium">${escapeHtml(l.resource_type)} ${l.resource_id ? '#' + escapeHtml(l.resource_id) : ''}</td>
          <td class="py-3 px-3 font-mono text-neutral-500">${l.user_id ? 'User #' + l.user_id : 'System'}</td>
          <td class="py-3 px-4 text-right font-mono text-[10px] text-neutral-400 truncate max-w-xs">${escapeHtml(JSON.stringify(l.details || {}))}</td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center py-8 text-red-500">${escapeHtml(err.message)}</td></tr>`;
  }
}

// Projects & Lists
async function loadProjects() {
  const grid = document.getElementById("projects-grid");
  if (!grid) return;
  try {
    const res = await fetch("/api/v1/projects");
    if (!res.ok) throw new Error("Failed to load projects");
    const list = await res.json();
    state.projects = list;

    if (!list.length) {
      grid.innerHTML = `<div class="col-span-3 text-center py-12 text-neutral-400 text-xs">No projects created yet. Press 'Create Project' above.</div>`;
      return;
    }

    grid.innerHTML = list.map(p => `
      <div class="bg-white dark:bg-neutral-900 rounded-2xl p-5 border border-neutral-200/80 dark:border-neutral-800/80 shadow-xs flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-orange-100 dark:bg-orange-950 text-[#ef4d23]">Active</span>
            <span class="text-xs font-mono text-neutral-400">${p.leads_count || 0} Leads</span>
          </div>
          <h3 class="font-bold text-base text-neutral-900 dark:text-white">${escapeHtml(p.name)}</h3>
          <p class="text-xs text-neutral-500 mt-1">${escapeHtml(p.description || 'Campaign workspace.')}</p>
        </div>
        <div class="mt-4 pt-3 border-t border-neutral-100 dark:border-neutral-800 flex items-center justify-between text-xs">
          <span class="text-neutral-400 font-mono text-[10px]">ID: #${p.id}</span>
          <button onclick="navigateRoute(null, 'leads')" class="font-bold text-[#ef4d23] hover:underline">View Leads &rarr;</button>
        </div>
      </div>
    `).join("");
  } catch (err) {
    grid.innerHTML = `<div class="col-span-3 text-center py-8 text-red-500">${escapeHtml(err.message)}</div>`;
  }
}

async function loadLeadLists() {
  const grid = document.getElementById("lists-grid");
  if (!grid) return;
  try {
    const res = await fetch("/api/v1/projects/lists");
    if (!res.ok) throw new Error("Failed to load lead lists");
    const list = await res.json();
    state.lists = list;

    if (!list.length) {
      grid.innerHTML = `<div class="col-span-3 text-center py-12 text-neutral-400 text-xs">No segmented lead lists created yet.</div>`;
      return;
    }

    grid.innerHTML = list.map(l => `
      <div class="bg-white dark:bg-neutral-900 rounded-2xl p-5 border border-neutral-200/80 dark:border-neutral-800/80 shadow-xs flex flex-col justify-between">
        <div>
          <h3 class="font-bold text-base text-neutral-900 dark:text-white">${escapeHtml(l.name)}</h3>
          <p class="text-xs text-neutral-500 mt-1">${escapeHtml(l.description || 'Targeted segment.')}</p>
        </div>
        <div class="mt-4 pt-3 border-t border-neutral-100 dark:border-neutral-800 flex items-center justify-between text-xs">
          <span class="font-mono text-neutral-400 text-[11px]">${l.members_count || 0} Members</span>
          <button onclick="navigateRoute(null, 'leads')" class="font-bold text-[#ef4d23] hover:underline">Open List &rarr;</button>
        </div>
      </div>
    `).join("");
  } catch (err) {
    grid.innerHTML = `<div class="col-span-3 text-center py-8 text-red-500">${escapeHtml(err.message)}</div>`;
  }
}

async function openNewProjectModal() {
  const name = prompt("Enter project name (e.g. UK E-Commerce Q4 Outreach):");
  if (!name) return;
  try {
    await fetch("/api/v1/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    loadProjects();
  } catch (err) {
    alert(err.message);
  }
}

async function openNewListModal() {
  const name = prompt("Enter lead list name (e.g. High Intent OpenCart Stores):");
  if (!name) return;
  try {
    await fetch("/api/v1/projects/lists", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    loadLeadLists();
  } catch (err) {
    alert(err.message);
  }
}

// Utility Helpers
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    alert("Copied to clipboard!");
  });
}

function toggleSidebarCollapse() {
  const sidebar = document.getElementById("app-sidebar");
  if (sidebar) sidebar.classList.toggle("hidden");
}

function toggleMobileSidebar() {
  toggleSidebarCollapse();
}

function toggleHeroView() {
  // Toggle showcase landing hero or modal
  alert("LeadForge Client-Ready Enterprise SaaS v2.0 - Active Workspace Loaded");
}

// Lifecycle Bootstrapping
window.addEventListener("DOMContentLoaded", () => {
  applyTheme(state.theme);
  state.activeRoute = getInitialRoute();
  renderActiveRoute();
  checkAuthMe();

  if (window.lucide) lucide.createIcons();
});
