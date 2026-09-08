/**
 * LeadForge — Core Application Client (Terranova Refractive Glass Architecture)
 * Complete live lead generation SPA: Router, SSE Discovery, Leads Directory, Dossier & Exports.
 */

// Application State
const state = {
  activeRoute: 'dashboard',
  theme: localStorage.getItem('leadforge_theme') || 'dark',
  activeLeadId: null,
  leads: [],
  pagination: {
    page: 1,
    limit: 15,
    total: 0,
    totalPages: 1
  },
  activeJobId: null,
  eventSource: null,
  searchTimer: null
};

// =========================================================================
// 1. Theme Management
// =========================================================================
function applyTheme(theme) {
  state.theme = theme;
  localStorage.setItem('leadforge_theme', theme);
  if (theme === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
}

function toggleTheme() {
  applyTheme(state.theme === 'dark' ? 'light' : 'dark');
}

// =========================================================================
// 2. Terranova Menu Drawer Management
// =========================================================================
const menuEl = document.getElementById('menu');
const menuOpenBtn = document.getElementById('menu-open');
const menuCloseBtn = document.getElementById('menu-close');
const menuBackdrop = document.getElementById('menu-backdrop');

function setMenu(open) {
  if (!menuEl) return;
  menuEl.classList.toggle('is-open', open);
  menuEl.setAttribute('aria-hidden', (!open).toString());
  if (menuOpenBtn) menuOpenBtn.setAttribute('aria-expanded', open.toString());
  document.body.style.overflow = open ? 'hidden' : '';
}

if (menuOpenBtn) menuOpenBtn.addEventListener('click', () => setMenu(true));
if (menuCloseBtn) menuCloseBtn.addEventListener('click', () => setMenu(false));
if (menuBackdrop) menuBackdrop.addEventListener('click', () => setMenu(false));

// Procedural Web Audio Micro-Interactions
const audioCtx = (typeof window !== 'undefined' && (window.AudioContext || window.webkitAudioContext))
  ? new (window.AudioContext || window.webkitAudioContext)()
  : null;

function playHapticSound(type = 'click') {
  if (!audioCtx || localStorage.getItem('leadforge_muted') === 'true') return;
  try {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    const now = audioCtx.currentTime;
    if (type === 'click') {
      osc.frequency.setValueAtTime(800, now);
      osc.frequency.exponentialRampToValueAtTime(300, now + 0.04);
      gain.gain.setValueAtTime(0.04, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);
      osc.start(now);
      osc.stop(now + 0.04);
    } else if (type === 'success') {
      osc.frequency.setValueAtTime(520, now);
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.12);
      gain.gain.setValueAtTime(0.06, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
      osc.start(now);
      osc.stop(now + 0.12);
    } else if (type === 'modal') {
      osc.frequency.setValueAtTime(320, now);
      osc.frequency.exponentialRampToValueAtTime(440, now + 0.08);
      gain.gain.setValueAtTime(0.05, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
      osc.start(now);
      osc.stop(now + 0.08);
    }
  } catch (err) {
    // Suppress ungestured audio error
  }
}

window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    setMenu(false);
    closeLeadDossier();
    return;
  }

  // Do not intercept keystrokes if focused in an input, textarea, or select
  const tag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
  if (tag === 'input' || tag === 'textarea' || tag === 'select') return;

  if (e.key === '/' || (e.ctrlKey && e.key.toLowerCase() === 'k')) {
    e.preventDefault();
    const searchInput = document.getElementById('filter-search');
    if (searchInput) {
      if (state.activeRoute !== 'leads') navigateRoute(null, 'leads');
      setTimeout(() => searchInput.focus(), 60);
    }
  } else if (e.key.toLowerCase() === 'r' && !e.ctrlKey && !e.metaKey) {
    e.preventDefault();
    playHapticSound('click');
    triggerAutoRefreshBatch(100);
  } else if (e.key.toLowerCase() === 'd' && !e.ctrlKey && !e.metaKey) {
    navigateRoute(null, 'dashboard');
  } else if (e.key.toLowerCase() === 'l' && !e.ctrlKey && !e.metaKey) {
    navigateRoute(null, 'leads');
  }
});

function navigateAndCloseMenu(route) {
  setMenu(false);
  navigateRoute(null, route);
}

// =========================================================================
// 3. Client-Side Router
// =========================================================================
const validRoutes = ['dashboard', 'discover', 'leads', 'exports'];

function getInitialRoute() {
  const path = window.location.pathname.replace(/^\//, '').split('/')[0];
  return validRoutes.includes(path) ? path : 'dashboard';
}

function navigateRoute(e, route) {
  if (e && e.preventDefault) e.preventDefault();
  if (!validRoutes.includes(route)) route = 'dashboard';
  state.activeRoute = route;
  window.history.pushState({ route }, '', `/${route === 'dashboard' ? '' : route}`);
  renderActiveRoute();
}

window.addEventListener('popstate', (e) => {
  const r = (e.state && e.state.route) ? e.state.route : getInitialRoute();
  state.activeRoute = r;
  renderActiveRoute();
});

function renderActiveRoute() {
  validRoutes.forEach((r) => {
    const section = document.getElementById(`view-${r}`);
    if (section) section.classList.add('hidden');
    const navBtn = document.getElementById(`nav-${r}`);
    if (navBtn) navBtn.classList.remove('active');
  });

  const activeSection = document.getElementById(`view-${state.activeRoute}`);
  if (activeSection) activeSection.classList.remove('hidden');

  const activeNavBtn = document.getElementById(`nav-${state.activeRoute}`);
  if (activeNavBtn) activeNavBtn.classList.add('active');

  // Trigger route-specific loaders
  switch (state.activeRoute) {
    case 'dashboard':
      loadDashboardAnalytics();
      break;
    case 'leads':
      loadLeadsTable();
      break;
    case 'discover':
      break;
    case 'exports':
      break;
  }

  if (window.lucide) {
    lucide.createIcons();
  }
}

// =========================================================================
// 4. Dashboard & Optical Findings Loader
// =========================================================================
async function loadDashboardAnalytics() {
  try {
    const res = await fetch('/api/v1/dashboard/analytics');
    if (!res.ok) throw new Error('Analytics failed');
    const data = await res.json();

    const summary = data.summary || {};
    const totalLeads = summary.total_leads ?? (data.total_leads || 0);
    const liveLeads = summary.live_leads ?? (data.live_count || 0);
    const hotLeads = summary.hot_leads ?? (data.hot_count || 0);
    const liveRate = totalLeads > 0 ? Math.round((liveLeads / totalLeads) * 100) : 100;

    // Populate Counters
    const totalEl = document.getElementById('stat-total-leads');
    const liveEl = document.getElementById('stat-live-rate');
    const hotEl = document.getElementById('stat-hot-leads');

    if (totalEl) totalEl.textContent = totalLeads;
    if (liveEl) liveEl.textContent = `${liveRate}%`;
    if (hotEl) hotEl.textContent = hotLeads;

    // Populate the Refractive Liquid Glass Card Findings
    const findingsContainer = document.getElementById('glass-card-findings');
    if (findingsContainer && data.recent_leads && data.recent_leads.length > 0) {
      const topRecent = data.recent_leads.slice(0, 2);
      findingsContainer.innerHTML = topRecent.map((lead, idx) => `
        <div class="finding cursor-pointer hover:bg-white/20 transition" onclick="openLeadDossier(${lead.id})">
          <div class="finding__title">
            <span class="truncate max-w-[200px] font-mono text-xs">${escapeHtml(lead.domain)}</span>
            <span class="badge-status ${lead.status === 'LIVE' ? 'badge-live' : 'badge-offline'} text-[9px]">${escapeHtml(lead.status)}</span>
          </div>
          <p class="finding__text">
            <strong>${escapeHtml(lead.primary_technology || 'Web Platform')}</strong> 
            (${Math.round((lead.technology_confidence || 0.8) * 100)}% confidence). 
            ${lead.primary_email ? `Contact: ${escapeHtml(lead.primary_email)}` : 'Verified storefront.'}
          </p>
        </div>
      `).join('');
    }

    // Populate Recent Leads Table
    const tbody = document.getElementById('dashboard-recent-leads-body');
    if (tbody && data.recent_leads) {
      if (data.recent_leads.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="7" class="text-center py-8 text-neutral-400 font-mono text-xs">
              No verified leads yet. Launch a discovery job above!
            </td>
          </tr>
        `;
      } else {
        tbody.innerHTML = data.recent_leads.slice(0, 6).map(renderLeadTableRow).join('');
      }
    }

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error('Error loading analytics:', err);
  }
}

// =========================================================================
// 5. Hero Quick Search Handlers
// =========================================================================
function setHeroPreset(tech, country) {
  const techSelect = document.getElementById('hero-tech-select');
  const countryInput = document.getElementById('hero-country-input');
  if (techSelect) techSelect.value = tech;
  if (countryInput) countryInput.value = country;
}

function handleHeroSearch(e) {
  e.preventDefault();
  const tech = document.getElementById('hero-tech-select').value;
  const country = document.getElementById('hero-country-input').value;
  const reqEmail = document.getElementById('hero-require-email').checked;

  // Sync to discover form
  const discTech = document.getElementById('disc-tech-select');
  const discCountry = document.getElementById('disc-country-input');
  const discEmail = document.getElementById('disc-require-email');

  if (discTech) discTech.value = tech;
  if (discCountry) discCountry.value = country;
  if (discEmail) discEmail.checked = reqEmail;

  navigateRoute(null, 'discover');
  startDiscoveryJob(tech, country, 'E-commerce', 20, reqEmail);
}

// Trigger auto refresh batch of 100 new leads and purge old ones
async function triggerAutoRefreshBatch(limit = 100) {
  const tech = document.getElementById('leads-tech-filter')?.value || 'opencart';
  const country = document.getElementById('leads-country-filter')?.value || 'United Kingdom';

  showToast(`Auto-refreshing: Purging previous batch and live-verifying ${limit} fresh leads...`, 'info');

  navigateRoute(null, 'discover');

  const discTech = document.getElementById('disc-tech-select');
  const discCountry = document.getElementById('disc-country-input');
  const discLimit = document.getElementById('disc-limit-select');
  const discReplace = document.getElementById('disc-replace-existing');

  if (discTech) discTech.value = tech;
  if (discCountry) discCountry.value = country;
  if (discLimit) discLimit.value = limit.toString();
  if (discReplace) discReplace.checked = true;

  startDiscoveryJob(tech, country, 'E-commerce', limit, false, true);
}

// =========================================================================
// 6. Discovery Engine & SSE Stream Handler
// =========================================================================
function handleDiscoverySubmit(e) {
  e.preventDefault();
  const tech = document.getElementById('disc-tech-select').value;
  const country = document.getElementById('disc-country-input').value;
  const industry = document.getElementById('disc-industry-input').value;
  const limit = parseInt(document.getElementById('disc-limit-select').value, 10) || 20;
  const requireEmail = document.getElementById('disc-require-email')?.checked || false;
  const replaceExisting = document.getElementById('disc-replace-existing')?.checked || false;

  startDiscoveryJob(tech, country, industry, limit, requireEmail, replaceExisting);
}

async function startDiscoveryJob(tech, country, industry, limit, requireEmail, replaceExisting = false) {
  const statusCard = document.getElementById('discovery-status-card');
  const leadsContainer = document.getElementById('discovery-leads-container');
  const streamGrid = document.getElementById('discovery-stream-grid');
  const logsContainer = document.getElementById('discovery-event-logs');
  const btnStart = document.getElementById('btn-start-discovery');

  if (statusCard) statusCard.classList.remove('hidden');
  if (leadsContainer) leadsContainer.classList.remove('hidden');
  if (streamGrid) streamGrid.innerHTML = '';
  if (logsContainer) logsContainer.innerHTML = '<div class="text-neutral-500">// Initiating live discovery job...</div>';

  const titleEl = document.getElementById('discovery-job-title');
  const metaEl = document.getElementById('discovery-job-meta');
  const statusBadge = document.getElementById('discovery-status-badge');
  const progressBar = document.getElementById('discovery-progress-bar');
  const progressPct = document.getElementById('discovery-progress-pct');
  const progressText = document.getElementById('discovery-progress-text');

  if (titleEl) titleEl.textContent = `Discovering ${tech.toUpperCase()} (${country || 'Global'})`;
  if (statusBadge) {
    statusBadge.className = 'badge-status badge-live';
    statusBadge.textContent = 'RUNNING';
  }
  if (progressBar) progressBar.style.width = '5%';
  if (progressPct) progressPct.textContent = '5%';
  if (progressText) progressText.textContent = replaceExisting ? 'Purging old leads & probing unseen domains...' : 'Contacting discovery providers...';

  // Reset counters
  document.getElementById('disc-count-candidates').textContent = '0';
  document.getElementById('disc-count-verified').textContent = '0';
  document.getElementById('disc-count-qualified').textContent = '0';

  if (btnStart) {
    btnStart.disabled = true;
    btnStart.classList.add('opacity-50', 'cursor-not-allowed');
  }

  // Close any existing SSE connection
  if (state.eventSource) {
    state.eventSource.close();
    state.eventSource = null;
  }

  try {
    const res = await fetch('/api/v1/discover', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        technology: tech,
        country: country || null,
        industry: industry || null,
        require_email: requireEmail,
        limit: limit,
        replace_existing: replaceExisting
      })
    });

    if (!res.ok) throw new Error(`Discovery start failed: ${res.statusText}`);
    const data = await res.json();
    state.activeJobId = data.job_id;

    if (metaEl) metaEl.textContent = `Job ID: ${data.job_id}`;
    appendDiscoveryLog(`Job started: ${data.job_id}. Listening to live SSE events...`);

    // Connect to SSE Stream
    const streamUrl = `/api/v1/discover/${data.job_id}/stream`;
    state.eventSource = new EventSource(streamUrl);

    state.eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        handleDiscoverySSEEvent(payload);
      } catch (err) {
        console.error('Failed to parse SSE payload:', err);
      }
    };

    state.eventSource.onerror = (err) => {
      console.warn('SSE stream closed or interrupted.');
      if (state.eventSource) {
        state.eventSource.close();
        state.eventSource = null;
      }
      if (btnStart) {
        btnStart.disabled = false;
        btnStart.classList.remove('opacity-50', 'cursor-not-allowed');
      }
    };

  } catch (err) {
    console.error('Discovery submission error:', err);
    showToast(`Error: ${err.message}`, 'error');
    if (btnStart) {
      btnStart.disabled = false;
      btnStart.classList.remove('opacity-50', 'cursor-not-allowed');
    }
  }
}

function handleDiscoverySSEEvent(data) {
  const event = data.event;
  const progressBar = document.getElementById('discovery-progress-bar');
  const progressPct = document.getElementById('discovery-progress-pct');
  const progressText = document.getElementById('discovery-progress-text');
  const countCand = document.getElementById('disc-count-candidates');
  const countVer = document.getElementById('disc-count-verified');
  const countQual = document.getElementById('disc-count-qualified');

  if (event === 'CANDIDATE_DISCOVERED') {
    if (countCand) countCand.textContent = data.count || (parseInt(countCand.textContent, 10) + 1);
    appendDiscoveryLog(`[DISCOVERY] Candidate found: ${data.domain} (Source: ${data.source})`);
  } else if (event === 'LEAD_PROCESSED') {
    const pct = data.progress || 50;
    if (progressBar) progressBar.style.width = `${pct}%`;
    if (progressPct) progressPct.textContent = `${pct}%`;
    if (progressText) progressText.textContent = `Probing ${data.lead.domain}...`;

    if (countVer && data.verified_count !== undefined) countVer.textContent = data.verified_count;
    if (countQual && data.qualified_count !== undefined) countQual.textContent = data.qualified_count;

    appendDiscoveryLog(`[VERIFY] ${data.lead.domain} — Status: ${data.lead.status} (${data.lead.http_status}), Score: ${data.lead.lead_score} (${data.lead.score_label})`);

    // Render streaming lead card
    renderStreamingLeadCard(data.lead);
  } else if (event === 'JOB_COMPLETED' || data.status === 'COMPLETED') {
    if (progressBar) progressBar.style.width = '100%';
    if (progressPct) progressPct.textContent = '100%';
    if (progressText) progressText.textContent = 'Discovery pipeline completed.';

    const statusBadge = document.getElementById('discovery-status-badge');
    if (statusBadge) {
      statusBadge.className = 'badge-status badge-live bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
      statusBadge.textContent = 'COMPLETED';
    }

    const spinner = document.getElementById('discovery-spinner');
    if (spinner) spinner.classList.remove('animate-ping');

    appendDiscoveryLog(`[SUCCESS] ${data.message || 'Discovery complete.'}`);
    showToast('Discovery job completed successfully!', 'success');

    if (state.eventSource) {
      state.eventSource.close();
      state.eventSource = null;
    }

    const btnStart = document.getElementById('btn-start-discovery');
    if (btnStart) {
      btnStart.disabled = false;
      btnStart.classList.remove('opacity-50', 'cursor-not-allowed');
    }

    // Refresh dashboard stats in background
    loadDashboardAnalytics();
  }

  if (window.lucide) lucide.createIcons();
}

function appendDiscoveryLog(msg) {
  const logsContainer = document.getElementById('discovery-event-logs');
  if (!logsContainer) return;
  const row = document.createElement('div');
  const now = new Date().toLocaleTimeString();
  row.innerHTML = `<span class="text-neutral-500 font-mono">[${now}]</span> ${escapeHtml(msg)}`;
  logsContainer.appendChild(row);
  logsContainer.scrollTop = logsContainer.scrollHeight;
}

function renderStreamingLeadCard(lead) {
  const grid = document.getElementById('discovery-stream-grid');
  if (!grid) return;

  const card = document.createElement('div');
  card.className = 'glass-surface p-4 rounded-2xl space-y-3 animate-[toastSlideIn_250ms_ease-out] hover:border-[#ef4d23]/50 transition cursor-pointer';
  card.onclick = () => openLeadDossier(lead.id);

  const scoreBadgeClass = getScoreBadgeClass(lead.score_label);
  const statusBadgeClass = lead.status === 'LIVE' ? 'badge-live' : 'badge-offline';

  card.innerHTML = `
    <div class="flex items-start justify-between gap-2">
      <div>
        <h4 class="font-medium text-sm text-white">${escapeHtml(lead.business_name || lead.domain)}</h4>
        <div class="text-xs font-mono text-[#ef4d23]">${escapeHtml(lead.domain)}</div>
      </div>
      <span class="badge-status ${statusBadgeClass} text-[9px]">${escapeHtml(lead.status)}</span>
    </div>

    <div class="flex flex-wrap items-center gap-1.5 text-xs">
      <span class="px-2 py-0.5 rounded-md bg-white/10 text-neutral-300 font-mono text-[10px]">
        ${escapeHtml(lead.primary_technology || 'Web')} ${Math.round((lead.technology_confidence || 0.8) * 100)}%
      </span>
      <span class="badge-status ${scoreBadgeClass} text-[10px]">
        ${escapeHtml(lead.score_label || 'HOT')} ${lead.lead_score || 85}
      </span>
    </div>

    <div class="text-xs text-neutral-400 truncate">
      ${lead.primary_email ? `<i data-lucide="mail" class="w-3.5 h-3.5 inline text-emerald-400 mr-1"></i>${escapeHtml(lead.primary_email)}` : '<span class="text-neutral-500 italic">No public email</span>'}
    </div>
  `;

  grid.prepend(card);
  if (window.lucide) lucide.createIcons();
}

// =========================================================================
// 7. Leads Directory Table & Pagination
// =========================================================================
function debounceLeadsSearch() {
  clearTimeout(state.searchTimer);
  state.searchTimer = setTimeout(() => {
    state.pagination.page = 1;
    loadLeadsTable();
  }, 300);
}

function setLeadsPreset(preset) {
  const techSelect = document.getElementById('leads-tech-filter');
  const scoreSelect = document.getElementById('leads-score-filter');
  const searchInput = document.getElementById('leads-search-input');

  if (preset === 'all') {
    if (techSelect) techSelect.value = '';
    if (scoreSelect) scoreSelect.value = '';
    if (searchInput) searchInput.value = '';
  } else if (preset === 'hot') {
    if (scoreSelect) scoreSelect.value = 'HOT';
  } else if (preset === 'email') {
    if (searchInput) searchInput.value = '@';
  } else if (preset === 'live') {
    if (scoreSelect) scoreSelect.value = '';
  }

  state.pagination.page = 1;
  loadLeadsTable();
}

async function loadLeadsTable() {
  const tbody = document.getElementById('leads-table-body');
  const pageLabel = document.getElementById('leads-page-label');
  const btnPrev = document.getElementById('btn-prev-page');
  const btnNext = document.getElementById('btn-next-page');
  const paginationInfo = document.getElementById('leads-pagination-info');

  if (tbody) {
    tbody.innerHTML = Array(5).fill(0).map(() => `
      <tr class="skeleton-row border-b border-white/5">
        <td class="py-4"><div class="h-4 bg-white/10 rounded w-32 mb-1"></div><div class="h-3 bg-white/5 rounded w-20"></div></td>
        <td><div class="h-5 bg-white/10 rounded w-24"></div></td>
        <td><div class="h-5 bg-white/10 rounded w-14"></div></td>
        <td><div class="h-4 bg-white/10 rounded w-16"></div></td>
        <td><div class="h-4 bg-white/10 rounded w-36"></div></td>
        <td><div class="h-5 bg-white/10 rounded w-16"></div></td>
        <td><div class="h-6 bg-white/10 rounded w-16"></div></td>
      </tr>
    `).join('');
  }

  const query = document.getElementById('leads-search-input')?.value.trim() || '';
  const tech = document.getElementById('leads-tech-filter')?.value || '';
  const country = document.getElementById('leads-country-filter')?.value || '';
  const scoreLabel = document.getElementById('leads-score-filter')?.value || '';

  const params = new URLSearchParams({
    page: state.pagination.page,
    limit: state.pagination.limit
  });

  if (query) params.append('query', query);
  if (tech) params.append('technology', tech);
  if (country) params.append('country', country);
  if (scoreLabel) params.append('score_label', scoreLabel);

  try {
    const res = await fetch(`/api/v1/leads?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to load leads');
    const data = await res.json();

    state.leads = data.leads || [];
    state.pagination.total = data.total || 0;
    state.pagination.totalPages = Math.ceil((data.total || 0) / state.pagination.limit) || 1;

    if (pageLabel) pageLabel.textContent = `Page ${state.pagination.page} of ${state.pagination.totalPages}`;
    if (paginationInfo) paginationInfo.textContent = `Showing ${state.leads.length} of ${data.total} leads`;
    if (btnPrev) btnPrev.disabled = state.pagination.page <= 1;
    if (btnNext) btnNext.disabled = state.pagination.page >= state.pagination.totalPages;

    if (tbody) {
      if (state.leads.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="7" class="text-center py-12 text-neutral-400 font-mono text-xs">
              <div class="space-y-3">
                <i data-lucide="search-x" class="w-8 h-8 mx-auto text-neutral-500"></i>
                <p>No matching verified leads found for current criteria.</p>
                <button onclick="resetLeadsFilters()" class="btn-chamfer text-xs py-1 px-3">
                  Clear Filters
                </button>
              </div>
            </td>
          </tr>
        `;
      } else {
        tbody.innerHTML = state.leads.map(renderLeadTableRow).join('');
      }
    }

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error('Leads directory error:', err);
    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="text-center py-8 text-rose-400 font-mono text-xs">
            Error loading directory: ${escapeHtml(err.message)}
          </td>
        </tr>
      `;
    }
  }
}

function changeLeadsPage(delta) {
  const newPage = state.pagination.page + delta;
  if (newPage >= 1 && newPage <= state.pagination.totalPages) {
    state.pagination.page = newPage;
    loadLeadsTable();
  }
}

function resetLeadsFilters() {
  playHapticSound('click');
  const searchInput = document.getElementById('filter-search') || document.getElementById('leads-search-input');
  const techSelect = document.getElementById('leads-tech-filter');
  const countrySelect = document.getElementById('leads-country-filter');
  const scoreSelect = document.getElementById('leads-score-filter');
  if (searchInput) searchInput.value = '';
  if (techSelect) techSelect.value = '';
  if (countrySelect) countrySelect.value = '';
  if (scoreSelect) scoreSelect.value = '';
  state.pagination.page = 1;
  loadLeadsTable();
}

function renderLeadTableRow(lead) {
  const scoreBadgeClass = getScoreBadgeClass(lead.score_label);
  const statusBadgeClass = lead.status === 'LIVE' ? 'badge-live' : 'badge-offline';
  const confidencePct = Math.round((lead.technology_confidence || 0.8) * 100);

  return `
    <tr class="group hover:bg-white/5 transition">
      <td class="font-medium">
        <div class="text-white text-sm">${escapeHtml(lead.business_name || lead.domain)}</div>
        <a href="${escapeHtml(lead.canonical_url || 'https://' + lead.domain)}" target="_blank" rel="noopener noreferrer" class="text-xs font-mono text-neutral-400 hover:text-[#ef4d23] flex items-center gap-1 transition">
          ${escapeHtml(lead.domain)} <i data-lucide="external-link" class="w-3 h-3 opacity-0 group-hover:opacity-100 transition"></i>
        </a>
      </td>

      <td>
        <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/10 text-xs font-mono">
          <span>${escapeHtml(lead.primary_technology || 'Web Platform')}</span>
          <span class="text-[#ef4d23] text-[10px] font-bold">${confidencePct}%</span>
        </div>
      </td>

      <td>
        <span class="badge-status ${statusBadgeClass}">
          ${escapeHtml(lead.status || 'UNKNOWN')}
        </span>
      </td>

      <td class="text-xs text-neutral-300 font-mono">
        ${escapeHtml(lead.country || 'Global')}
      </td>

      <td>
        <div class="flex flex-col gap-0.5 text-xs">
          ${lead.primary_email ? `
            <a href="mailto:${escapeHtml(lead.primary_email)}" class="text-emerald-400 hover:underline flex items-center gap-1">
              <i data-lucide="mail" class="w-3 h-3"></i> ${escapeHtml(lead.primary_email)}
            </a>
          ` : '<span class="text-neutral-500 italic text-[11px]">No email</span>'}
          
          ${lead.primary_phone ? `
            <a href="tel:${escapeHtml(lead.primary_phone)}" class="text-neutral-400 hover:text-white flex items-center gap-1 text-[11px]">
              <i data-lucide="phone" class="w-2.5 h-2.5"></i> ${escapeHtml(lead.primary_phone)}
            </a>
          ` : ''}
        </div>
      </td>

      <td>
        <span class="badge-status ${scoreBadgeClass}">
          ${escapeHtml(lead.score_label || 'WARM')} ${lead.lead_score || 60}
        </span>
      </td>

      <td class="text-right whitespace-nowrap">
        <div class="inline-flex items-center gap-2">
          <button onclick="openLeadDossier(${lead.id})" class="px-2.5 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs font-medium text-white transition flex items-center gap-1">
            <i data-lucide="file-text" class="w-3.5 h-3.5"></i> Dossier
          </button>
          <button onclick="reverifyLeadInline(${lead.id})" title="Live Re-Verify" class="p-1.5 rounded-lg hover:bg-white/10 text-neutral-400 hover:text-white transition">
            <i data-lucide="refresh-cw" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </td>
    </tr>
  `;
}

function getScoreBadgeClass(label) {
  const l = (label || '').toUpperCase();
  if (l === 'HOT') return 'badge-score-hot';
  if (l === 'HIGH') return 'badge-score-high';
  if (l === 'MEDIUM') return 'badge-score-medium';
  return 'badge-score-low';
}

// =========================================================================
// 8. Lead Dossier Modal Management
// =========================================================================
async function openLeadDossier(leadId) {
  state.activeLeadId = leadId;
  const modal = document.getElementById('lead-dossier-modal');
  const content = document.getElementById('dossier-content');
  if (!modal || !content) return;

  modal.classList.remove('hidden');
  content.innerHTML = '<div class="py-12 text-center text-neutral-400 font-mono text-xs">Loading forensic dossier...</div>';

  try {
    const res = await fetch(`/api/v1/leads/${leadId}`);
    if (!res.ok) throw new Error('Failed to load lead dossier');
    const data = await res.json();
    const lead = data.lead || data;

    // Header updates
    document.getElementById('dossier-business-name').textContent = lead.business_name || lead.domain;
    const domainLink = document.getElementById('dossier-domain-link');
    domainLink.href = lead.canonical_url || `https://${lead.domain}`;
    domainLink.innerHTML = `${escapeHtml(lead.domain)} <i data-lucide="external-link" class="w-3 h-3"></i>`;

    const statusBadge = document.getElementById('dossier-status-badge');
    statusBadge.className = `badge-status ${lead.status === 'LIVE' ? 'badge-live' : 'badge-offline'}`;
    statusBadge.textContent = lead.status;

    const scoreBadge = document.getElementById('dossier-score-badge');
    scoreBadge.className = `badge-status ${getScoreBadgeClass(lead.score_label)}`;
    scoreBadge.textContent = `${lead.score_label} ${lead.lead_score}/100`;

    // Parse JSON fields safely
    const evidence = Array.isArray(lead.evidence) ? lead.evidence : [];
    const emails = Array.isArray(lead.emails) ? lead.emails : [];
    const phones = Array.isArray(lead.phones) ? lead.phones : [];
    const socials = lead.socials || {};
    const reasons = Array.isArray(lead.score_reasons) ? lead.score_reasons : [];

    content.innerHTML = `
      <!-- Live Network Probes -->
      <div class="glass-surface p-4 rounded-2xl space-y-3">
        <h4 class="text-xs font-mono uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
          <i data-lucide="network" class="w-3.5 h-3.5"></i> Live Network Probe Results
        </h4>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
          <div class="p-2.5 rounded-xl bg-white/5">
            <span class="text-neutral-400 block text-[10px]">HTTP Status</span>
            <span class="font-bold ${lead.http_status === 200 ? 'text-emerald-400' : 'text-neutral-200'}">${lead.http_status || 'N/A'}</span>
          </div>
          <div class="p-2.5 rounded-xl bg-white/5">
            <span class="text-neutral-400 block text-[10px]">SSL Certificate</span>
            <span class="font-bold ${lead.has_ssl ? 'text-emerald-400' : 'text-rose-400'}">${lead.has_ssl ? 'Active (HTTPS)' : 'Missing'}</span>
          </div>
          <div class="p-2.5 rounded-xl bg-white/5">
            <span class="text-neutral-400 block text-[10px]">Latency</span>
            <span class="font-bold text-neutral-200">${Math.round(lead.response_time_ms || 0)}ms</span>
          </div>
          <div class="p-2.5 rounded-xl bg-white/5">
            <span class="text-neutral-400 block text-[10px]">Geography</span>
            <span class="font-bold text-neutral-200">${escapeHtml(lead.country || 'Global')}</span>
          </div>
        </div>
      </div>

      <!-- Detected Technology & Forensic Evidence -->
      <div class="glass-surface p-4 rounded-2xl space-y-3">
        <h4 class="text-xs font-mono uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
          <i data-lucide="cpu" class="w-3.5 h-3.5"></i> Technology Fingerprint
        </h4>
        <div class="flex items-center justify-between">
          <div class="font-medium text-base text-white">${escapeHtml(lead.primary_technology || 'Web Platform')}</div>
          <span class="text-xs font-mono text-[#ef4d23] font-bold">${Math.round((lead.technology_confidence || 0.8) * 100)}% Confidence Match</span>
        </div>

        ${evidence.length > 0 ? `
          <div class="space-y-1.5 pt-2 border-t border-white/10">
            <span class="text-[11px] font-mono text-neutral-400 block">Forensic Proof Signals:</span>
            <div class="flex flex-wrap gap-1.5">
              ${evidence.map(e => `<span class="px-2 py-0.5 rounded-md bg-white/10 text-[11px] font-mono text-neutral-300">${escapeHtml(e)}</span>`).join('')}
            </div>
          </div>
        ` : ''}
      </div>

      <!-- Contact Information -->
      <div class="glass-surface p-4 rounded-2xl space-y-3">
        <h4 class="text-xs font-mono uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
          <i data-lucide="contact" class="w-3.5 h-3.5"></i> Discovered Public Contacts
        </h4>
        
        <div class="space-y-2 text-xs">
          <div>
            <span class="text-neutral-400 block text-[10px] font-mono uppercase">Emails:</span>
            ${emails.length > 0 ? `
              <div class="flex flex-wrap gap-2 mt-1">
                ${emails.map(m => {
                  const val = typeof m === 'string' ? m : m.value;
                  const role = typeof m === 'object' && m.role_type ? `(${m.role_type})` : '';
                  return `<a href="mailto:${escapeHtml(val)}" class="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono hover:underline">${escapeHtml(val)} <span class="text-[9px] text-neutral-400">${role}</span></a>`;
                }).join('')}
              </div>
            ` : '<span class="text-neutral-500 italic">No public emails discovered on homepage.</span>'}
          </div>

          <div class="pt-2 border-t border-white/10">
            <span class="text-neutral-400 block text-[10px] font-mono uppercase">Phones:</span>
            ${phones.length > 0 ? `
              <div class="flex flex-wrap gap-2 mt-1">
                ${phones.map(p => {
                  const val = typeof p === 'string' ? p : p.value;
                  return `<a href="tel:${escapeHtml(val)}" class="px-2.5 py-1 rounded-lg bg-white/10 text-neutral-300 font-mono hover:underline">${escapeHtml(val)}</a>`;
                }).join('')}
              </div>
            ` : '<span class="text-neutral-500 italic">No direct phone number listed.</span>'}
          </div>

          ${Object.keys(socials).length > 0 ? `
            <div class="pt-2 border-t border-white/10">
              <span class="text-neutral-400 block text-[10px] font-mono uppercase">Social Profiles:</span>
              <div class="flex flex-wrap gap-2 mt-1">
                ${Object.entries(socials).map(([net, url]) => `
                  <a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="px-2.5 py-1 rounded-lg bg-white/10 text-neutral-300 hover:text-white capitalize font-mono text-[11px]">${escapeHtml(net)} &rarr;</a>
                `).join('')}
              </div>
            </div>
          ` : ''}
        </div>
      </div>

      <!-- Scoring Drivers -->
      ${reasons.length > 0 ? `
        <div class="glass-surface p-4 rounded-2xl space-y-2">
          <h4 class="text-xs font-mono uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
            <i data-lucide="award" class="w-3.5 h-3.5"></i> Opportunity Score Drivers
          </h4>
          <ul class="list-disc list-inside space-y-1 text-xs text-neutral-300 font-mono">
            ${reasons.map(r => `<li>${escapeHtml(r)}</li>`).join('')}
          </ul>
        </div>
      ` : ''}
    `;

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    content.innerHTML = `<div class="py-8 text-center text-rose-400 font-mono text-xs">Error: ${escapeHtml(err.message)}</div>`;
  }
}

function closeLeadDossier() {
  const modal = document.getElementById('lead-dossier-modal');
  if (modal) modal.classList.add('hidden');
  state.activeLeadId = null;
}

async function reverifyCurrentLead() {
  if (!state.activeLeadId) return;
  const btn = document.getElementById('btn-dossier-reverify');
  if (btn) btn.classList.add('opacity-50', 'pointer-events-none');

  try {
    showToast('Probing website live over network...', 'info');
    const res = await fetch(`/api/v1/leads/${state.activeLeadId}/refresh`, { method: 'POST' });
    if (!res.ok) throw new Error('Re-verify failed');
    showToast('Lead re-verified successfully!', 'success');
    await openLeadDossier(state.activeLeadId);
    loadLeadsTable();
  } catch (err) {
    showToast(`Re-verify error: ${err.message}`, 'error');
  } finally {
    if (btn) btn.classList.remove('opacity-50', 'pointer-events-none');
  }
}

async function reverifyLeadInline(leadId) {
  try {
    showToast('Probing website live over network...', 'info');
    const res = await fetch(`/api/v1/leads/${leadId}/refresh`, { method: 'POST' });
    if (!res.ok) throw new Error('Re-verify failed');
    showToast('Lead re-verified successfully!', 'success');
    loadLeadsTable();
  } catch (err) {
    showToast(`Re-verify error: ${err.message}`, 'error');
  }
}

// =========================================================================
// 9. Toast Notification System
// =========================================================================
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'toast';

  let icon = 'info';
  if (type === 'success') icon = 'check-circle';
  if (type === 'error') icon = 'alert-circle';

  toast.innerHTML = `
    <i data-lucide="${icon}" class="w-4 h-4 ${type === 'success' ? 'text-emerald-400' : type === 'error' ? 'text-rose-400' : 'text-blue-400'}"></i>
    <span class="text-xs font-mono font-medium">${escapeHtml(message)}</span>
  `;

  container.appendChild(toast);
  if (window.lucide) lucide.createIcons();

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 200ms ease';
    setTimeout(() => toast.remove(), 200);
  }, 3500);
}

// =========================================================================
// 10. Utility Functions
// =========================================================================
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// =========================================================================
// 11. App Initialization
// =========================================================================
document.addEventListener('DOMContentLoaded', () => {
  applyTheme(state.theme);
  state.activeRoute = getInitialRoute();
  renderActiveRoute();
});
