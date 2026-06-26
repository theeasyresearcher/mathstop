"""
build_site.py — MathStatDS Hub
Reads data/items.json, writes index.html
"""

import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("data")


def main():
    items = []
    p = DATA_DIR / "items.json"
    if p.exists():
        items = json.loads(p.read_text())

    updated = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
    total = len(items)
    india = sum(1 for i in items if i.get("location") == "India")
    world = sum(1 for i in items if i.get("location") == "World")

    # Counts by category
    cats = {
        "Exam Notification": 0,
        "Conference": 0,
        "Workshop / School": 0,
        "Webinar / Lecture": 0,
        "Fellowship / Award": 0,
    }
    for i in items:
        c = i.get("category", "Conference")
        if c in cats:
            cats[c] += 1

    items_json = json.dumps(items, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="MathStatDS Hub — Daily-updated listings of Math, Statistics & Data Science exams, conferences, workshops, fellowships, and webinars. India and World.">
<title>MathStatDS Hub — Maths · Statistics · Data Science</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {{
  --primary:#2563EB; --primary-light:#EFF6FF;
  --danger:#DC2626; --danger-light:#FEF2F2;
  --success:#16A34A; --success-light:#F0FDF4;
  --purple:#7C3AED; --purple-light:#F5F3FF;
  --amber:#D97706; --amber-light:#FFFBEB;
  --gray-50:#F9FAFB; --gray-100:#F3F4F6; --gray-200:#E5E7EB;
  --gray-400:#9CA3AF; --gray-500:#6B7280; --gray-700:#374151; --gray-900:#111827;
  --bg:#fff; --surface:#fff; --border:var(--gray-200);
  --text:var(--gray-900); --text-muted:var(--gray-500);
  --sidebar-w:240px; --radius:12px;
}}
@media (prefers-color-scheme:dark) {{
  :root {{
    --bg:#0f172a; --surface:#1e293b; --border:#334155;
    --text:#f1f5f9; --text-muted:#94a3b8;
    --gray-50:#1e293b; --gray-100:#334155; --gray-200:#475569;
  }}
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text);font-size:14px;line-height:1.5}}
a{{color:inherit;text-decoration:none}}
button{{cursor:pointer;border:none;background:none;font-family:inherit}}

/* Header */
.header{{position:sticky;top:0;z-index:100;background:var(--bg);border-bottom:1px solid var(--border);padding:0 1rem}}
.header-inner{{max-width:1200px;margin:0 auto;display:flex;align-items:center;gap:1rem;height:56px}}
.logo{{display:flex;align-items:center;gap:.5rem;font-weight:600;font-size:1rem;white-space:nowrap}}
.logo-symbol{{font-size:1.5rem;color:var(--primary)}}
.tagline{{color:var(--text-muted);font-size:.8rem;flex:1;text-align:center}}
.header-right{{display:flex;align-items:center;gap:.75rem;white-space:nowrap}}
.last-updated{{font-size:.75rem;color:var(--text-muted)}}
.dark-toggle{{width:36px;height:36px;border-radius:50%;border:1px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:1rem;background:var(--surface);color:var(--text)}}
.dark-toggle:hover{{background:var(--gray-100)}}

/* Layout */
.layout{{max-width:1200px;margin:0 auto;display:flex;gap:0}}

/* Sidebar */
.sidebar{{width:var(--sidebar-w);flex-shrink:0;border-right:1px solid var(--border);padding:1rem;position:sticky;top:56px;height:calc(100vh - 56px);overflow-y:auto}}
.sidebar-section{{margin-bottom:1.25rem}}
.sidebar-label{{font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:var(--text-muted);margin-bottom:.5rem}}
.sidebar-logo{{display:flex;align-items:center;gap:.5rem;font-weight:600;margin-bottom:1.25rem}}
.sidebar-logo .logo-symbol{{font-size:1.25rem;color:var(--primary)}}
.nav-btn{{display:flex;align-items:center;justify-content:space-between;width:100%;padding:.4rem .6rem;border-radius:6px;font-size:.85rem;color:var(--text);transition:background .1s}}
.nav-btn:hover,.nav-btn.active{{background:var(--primary-light);color:var(--primary)}}
.nav-btn .badge{{font-size:.7rem;background:var(--gray-100);color:var(--text-muted);border-radius:999px;padding:.1rem .4rem;min-width:1.5rem;text-align:center}}
.nav-btn.active .badge{{background:var(--primary);color:#fff}}
.stat-row{{display:flex;justify-content:space-between;font-size:.8rem;padding:.2rem 0;color:var(--text-muted)}}
.stat-row span:last-child{{font-weight:500;color:var(--text)}}
.about-text{{font-size:.78rem;color:var(--text-muted);line-height:1.5}}

/* Main */
.main{{flex:1;min-width:0;padding:1rem 1.25rem}}

/* Search */
.search-wrap{{position:relative;margin-bottom:.75rem}}
.search-input{{width:100%;height:44px;border:1.5px solid var(--border);border-radius:8px;padding:0 2.5rem 0 .875rem;font-size:.9rem;background:var(--surface);color:var(--text);outline:none;transition:border-color .15s}}
.search-input:focus{{border-color:var(--primary)}}
.search-clear{{position:absolute;right:.75rem;top:50%;transform:translateY(-50%);color:var(--text-muted);font-size:1rem;display:none}}
.search-clear.show{{display:block}}

/* Sort */
.sort-bar{{display:flex;align-items:center;justify-content:flex-end;gap:.5rem;margin-bottom:.75rem;font-size:.82rem;color:var(--text-muted)}}
.sort-select{{border:1px solid var(--border);border-radius:6px;padding:.25rem .5rem;background:var(--surface);color:var(--text);font-size:.82rem}}

/* Stats row */
.stats-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:.75rem;margin-bottom:1rem}}
.stat-card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:.75rem 1rem}}
.stat-card .stat-num{{font-size:1.5rem;font-weight:600;line-height:1}}
.stat-card .stat-label{{font-size:.72rem;color:var(--text-muted);margin-top:.2rem}}
.stat-card.exam .stat-num{{color:var(--danger)}}
.stat-card.conf .stat-num{{color:var(--primary)}}
.stat-card.ws .stat-num{{color:var(--success)}}
.stat-card.fellow .stat-num{{color:var(--amber)}}

/* Cards grid */
.cards-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}}

/* Card */
.card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:1rem 1.25rem;transition:border-color .15s,box-shadow .15s;display:flex;flex-direction:column;gap:.5rem}}
.card:hover{{border-color:var(--primary);box-shadow:0 2px 8px rgba(37,99,235,.08)}}
.card-top{{display:flex;align-items:center;gap:.4rem;flex-wrap:wrap}}
.badge{{display:inline-flex;align-items:center;font-size:.7rem;font-weight:500;border-radius:999px;padding:.15rem .55rem;line-height:1.4}}
.badge-exam{{background:var(--danger-light);color:var(--danger)}}
.badge-conference{{background:var(--primary-light);color:var(--primary)}}
.badge-workshop{{background:var(--success-light);color:var(--success)}}
.badge-webinar{{background:var(--purple-light);color:var(--purple)}}
.badge-fellowship{{background:var(--amber-light);color:var(--amber)}}
.badge-new{{background:#DCFCE7;color:#15803D;font-size:.65rem}}
.flag{{font-size:.9rem}}
.card-title{{font-size:.875rem;font-weight:500;line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.card-title a:hover{{color:var(--primary)}}
.card-desc{{font-size:.78rem;color:var(--text-muted);display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}
.card-divider{{border:none;border-top:1px solid var(--gray-100);margin:.1rem 0}}
.card-footer{{display:flex;justify-content:space-between;align-items:center;font-size:.72rem;color:var(--text-muted)}}
.deadline-urgent{{color:var(--danger);font-weight:500}}
.deadline-soon{{color:var(--amber);font-weight:500}}
.source-name{{max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}

/* Empty state */
.empty{{text-align:center;padding:4rem 1rem;color:var(--text-muted)}}
.empty .empty-icon{{font-size:3rem;margin-bottom:.5rem}}
.empty h3{{font-size:1rem;font-weight:500;margin-bottom:.25rem;color:var(--text)}}

/* Loading skeleton */
.skeleton{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:1rem 1.25rem;display:flex;flex-direction:column;gap:.5rem}}
.skel-line{{border-radius:4px;animation:shimmer 1.2s ease-in-out infinite;background:linear-gradient(90deg,var(--gray-100) 25%,var(--gray-200) 50%,var(--gray-100) 75%);background-size:200% 100%}}
@keyframes shimmer{{0%{{background-position:200% 0}}100%{{background-position:-200% 0}}}}

/* Footer */
.footer{{text-align:center;padding:1.5rem 1rem;font-size:.78rem;color:var(--text-muted);border-top:1px solid var(--border);margin-top:1.5rem}}
.footer a{{color:var(--primary)}}

/* Mobile bottom nav */
.bottom-nav{{display:none;position:fixed;bottom:0;left:0;right:0;background:var(--bg);border-top:1px solid var(--border);z-index:200;height:56px}}
.bottom-nav-inner{{display:flex;height:100%}}
.bnav-btn{{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:.15rem;font-size:.65rem;font-weight:500;color:var(--text-muted);transition:color .15s}}
.bnav-btn.active,.bnav-btn:hover{{color:var(--primary)}}
.bnav-btn .bnav-icon{{font-size:1.1rem}}

/* Filter drawer */
.drawer-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:300}}
.drawer-overlay.open{{display:block}}
.drawer{{position:fixed;bottom:0;left:0;right:0;background:var(--bg);border-radius:1rem 1rem 0 0;padding:1.25rem 1rem 2rem;z-index:400;transform:translateY(100%);transition:transform .25s ease}}
.drawer.open{{transform:translateY(0)}}
.drawer-handle{{width:40px;height:4px;background:var(--gray-200);border-radius:2px;margin:0 auto .75rem}}
.drawer-title{{font-weight:600;margin-bottom:.75rem}}
.drawer-grid{{display:grid;grid-template-columns:1fr 1fr;gap:.5rem}}
.filter-btn{{padding:.5rem .75rem;border:1.5px solid var(--border);border-radius:8px;font-size:.82rem;font-weight:500;color:var(--text);background:var(--surface);text-align:left;transition:all .1s}}
.filter-btn.active{{border-color:var(--primary);background:var(--primary-light);color:var(--primary)}}

/* Responsive */
@media(max-width:1024px){{.cards-grid{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:768px){{
  .sidebar{{display:none}}
  .tagline{{display:none}}
  .bottom-nav{{display:flex}}
  .cards-grid{{grid-template-columns:1fr}}
  .stats-row{{grid-template-columns:repeat(2,1fr)}}
  .main{{padding:.75rem;padding-bottom:80px}}
  .header-inner{{gap:.5rem}}
  .last-updated{{display:none}}
}}
@media(max-width:480px){{.stats-row{{grid-template-columns:repeat(2,1fr)}}}}
</style>
</head>
<body>

<!-- Header -->
<header class="header">
  <div class="header-inner">
    <div class="logo"><span class="logo-symbol">∑</span> MathStatDS Hub</div>
    <div class="tagline">Maths · Statistics · Data Science</div>
    <div class="header-right">
      <span class="last-updated" id="lastUpdated">Updated: {updated}</span>
      <button class="dark-toggle" id="darkToggle" aria-label="Toggle dark mode">🌙</button>
    </div>
  </div>
</header>

<div class="layout">
  <!-- Sidebar -->
  <aside class="sidebar">
    <div class="sidebar-logo"><span class="logo-symbol">∑</span> MathStatDS Hub</div>

    <div class="sidebar-section">
      <div class="sidebar-label">Browse</div>
      <button class="nav-btn active" data-location="all">🌐 All <span class="badge" id="cnt-all">0</span></button>
      <button class="nav-btn" data-location="India">🇮🇳 India <span class="badge" id="cnt-india">0</span></button>
      <button class="nav-btn" data-location="World">🌍 World <span class="badge" id="cnt-world">0</span></button>
    </div>

    <div class="sidebar-section">
      <div class="sidebar-label">Category</div>
      <button class="nav-btn active" data-cat="all">All <span class="badge" id="cnt-cat-all">0</span></button>
      <button class="nav-btn" data-cat="Exam Notification">📋 Exam <span class="badge" id="cnt-exam">0</span></button>
      <button class="nav-btn" data-cat="Conference">🎓 Conference <span class="badge" id="cnt-conf">0</span></button>
      <button class="nav-btn" data-cat="Workshop / School">🛠 Workshop <span class="badge" id="cnt-ws">0</span></button>
      <button class="nav-btn" data-cat="Webinar / Lecture">📡 Webinar <span class="badge" id="cnt-web">0</span></button>
      <button class="nav-btn" data-cat="Fellowship / Award">🏆 Fellowship <span class="badge" id="cnt-fellow">0</span></button>
    </div>

    <div class="sidebar-section">
      <div class="sidebar-label">Stats</div>
      <div class="stat-row"><span>Total listings</span><span id="s-total">{total}</span></div>
      <div class="stat-row"><span>India</span><span id="s-india">{india}</span></div>
      <div class="stat-row"><span>World</span><span id="s-world">{world}</span></div>
      <div class="stat-row"><span>Sources</span><span>65+</span></div>
      <div class="stat-row"><span>Updated</span><span>{updated[:11]}</span></div>
    </div>

    <div class="sidebar-section">
      <div class="sidebar-label">About</div>
      <p class="about-text">Daily-updated hub for Maths, Statistics &amp; Data Science events in India and worldwide. Zero-cost, open-source.</p>
    </div>
  </aside>

  <!-- Main -->
  <main class="main">
    <!-- Search -->
    <div class="search-wrap">
      <input class="search-input" id="searchInput" type="search"
             placeholder="Search exams, conferences, workshops…" autocomplete="off">
      <button class="search-clear" id="searchClear" aria-label="Clear search">✕</button>
    </div>

    <!-- Sort -->
    <div class="sort-bar">
      Sort by:
      <select class="sort-select" id="sortSelect">
        <option value="deadline">Deadline (soonest)</option>
        <option value="added">Date added</option>
        <option value="az">A–Z</option>
      </select>
    </div>

    <!-- Stats row -->
    <div class="stats-row">
      <div class="stat-card exam"><div class="stat-num" id="m-exam">{cats["Exam Notification"]}</div><div class="stat-label">Exam Alerts</div></div>
      <div class="stat-card conf"><div class="stat-num" id="m-conf">{cats["Conference"]}</div><div class="stat-label">Conferences</div></div>
      <div class="stat-card ws"><div class="stat-num" id="m-ws">{cats["Workshop / School"]}</div><div class="stat-label">Workshops</div></div>
      <div class="stat-card fellow"><div class="stat-num" id="m-fellow">{cats["Fellowship / Award"]}</div><div class="stat-label">Fellowships</div></div>
    </div>

    <!-- Cards -->
    <div class="cards-grid" id="cardsGrid">
      <!-- skeleton -->
      {''.join(['<div class="skeleton"><div class="skel-line" style="height:14px;width:60%"></div><div class="skel-line" style="height:12px;width:90%;margin-top:4px"></div><div class="skel-line" style="height:12px;width:80%;margin-top:4px"></div><div class="skel-line" style="height:10px;width:40%;margin-top:8px"></div></div>' for _ in range(6)])}
    </div>

    <div class="empty" id="emptyState" style="display:none">
      <div class="empty-icon">📭</div>
      <h3>No listings found</h3>
      <p>Try adjusting your filters or search terms.</p>
    </div>

    <div class="empty" id="errorState" style="display:none">
      <div class="empty-icon">⚠️</div>
      <h3>Could not load data</h3>
      <p>Try refreshing the page.</p>
    </div>
  </main>
</div>

<!-- Footer -->
<footer class="footer">
  MathStatDS Hub · Auto-updated daily · Data from 65+ sources ·
  <a href="https://github.com/yourusername/mathstatds-hub" target="_blank">GitHub</a> ·
  Built with GitHub Pages + Actions
</footer>

<!-- Mobile bottom nav -->
<nav class="bottom-nav">
  <button class="bnav-btn active" data-location="all"><span class="bnav-icon">🌐</span>All</button>
  <button class="bnav-btn" data-location="India"><span class="bnav-icon">🇮🇳</span>India</button>
  <button class="bnav-btn" data-location="World"><span class="bnav-icon">🌍</span>World</button>
  <button class="bnav-btn" id="filterBtn"><span class="bnav-icon">🔽</span>Filter</button>
</nav>

<!-- Filter drawer (mobile) -->
<div class="drawer-overlay" id="drawerOverlay"></div>
<div class="drawer" id="filterDrawer">
  <div class="drawer-handle"></div>
  <div class="drawer-title">Filter by Category</div>
  <div class="drawer-grid">
    <button class="filter-btn active" data-cat="all">All</button>
    <button class="filter-btn" data-cat="Exam Notification">📋 Exam</button>
    <button class="filter-btn" data-cat="Conference">🎓 Conference</button>
    <button class="filter-btn" data-cat="Workshop / School">🛠 Workshop</button>
    <button class="filter-btn" data-cat="Webinar / Lecture">📡 Webinar</button>
    <button class="filter-btn" data-cat="Fellowship / Award">🏆 Fellowship</button>
  </div>
</div>

<script>
(function(){{
const ITEMS = {items_json};

// ── State ────────────────────────────────────────────────────────────────────
let state = {{
  items: [],
  location: 'all',
  category: 'all',
  search: '',
  sort: 'deadline',
}};

// ── Dark mode ────────────────────────────────────────────────────────────────
const prefersDark = window.matchMedia('(prefers-color-scheme:dark)').matches;
let darkMode = localStorage.getItem('theme') === 'dark' || (localStorage.getItem('theme') === null && prefersDark);
function applyTheme() {{
  document.documentElement.style.setProperty('--bg', darkMode ? '#0f172a' : '#fff');
  document.getElementById('darkToggle').textContent = darkMode ? '☀️' : '🌙';
}}
applyTheme();
document.getElementById('darkToggle').addEventListener('click', () => {{
  darkMode = !darkMode;
  localStorage.setItem('theme', darkMode ? 'dark' : 'light');
  applyTheme();
}});

// ── Utilities ────────────────────────────────────────────────────────────────
function esc(s) {{
  return String(s).replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
}}

function deadlineHtml(item) {{
  const d = item.deadline || item.event_date;
  if (!d) return '<span>📅 Date TBA</span>';
  const days = Math.ceil((new Date(d) - new Date()) / 86400000);
  if (days < 0) return `<span class="deadline-soon">📅 ${{d}}</span>`;
  if (days < 7) return `<span class="deadline-urgent">⚠ ${{days}}d left</span>`;
  if (days < 30) return `<span class="deadline-soon">⏳ ${{days}}d left</span>`;
  return `<span style="color:var(--text-muted)">📅 ${{d}}</span>`;
}}

function badgeClass(cat) {{
  return {{
    'Exam Notification':'badge-exam',
    'Conference':'badge-conference',
    'Workshop / School':'badge-workshop',
    'Webinar / Lecture':'badge-webinar',
    'Fellowship / Award':'badge-fellowship',
  }}[cat] || 'badge-conference';
}}

function renderCard(item) {{
  const flag = item.location === 'India' ? '🇮🇳' : '🌍';
  const newPill = item.is_new ? '<span class="badge badge-new">NEW</span>' : '';
  const cat = item.category || 'Conference';
  return `<div class="card">
    <div class="card-top">
      <span class="badge ${{badgeClass(cat)}}">${{esc(cat)}}</span>
      <span class="flag">${{flag}}</span>
      ${{newPill}}
    </div>
    <div class="card-title"><a href="${{esc(item.url)}}" target="_blank" rel="noopener">${{esc(item.title)}}</a></div>
    ${{item.description ? `<div class="card-desc">${{esc(item.description)}}</div>` : ''}}
    <hr class="card-divider">
    <div class="card-footer">
      ${{deadlineHtml(item)}}
      <span class="source-name" title="${{esc(item.source_name || '')}}">${{esc(item.source_name || '')}}</span>
    </div>
  </div>`;
}}

// ── Filter + sort ────────────────────────────────────────────────────────────
function filtered() {{
  let items = state.items;
  if (state.location !== 'all') items = items.filter(i => i.location === state.location);
  if (state.category !== 'all') items = items.filter(i => i.category === state.category);
  if (state.search) {{
    const q = state.search.toLowerCase();
    items = items.filter(i =>
      (i.title||'').toLowerCase().includes(q) ||
      (i.description||'').toLowerCase().includes(q)
    );
  }}
  if (state.sort === 'deadline') {{
    items = [...items].sort((a,b) => {{
      const da = a.deadline || a.event_date || '9999';
      const db = b.deadline || b.event_date || '9999';
      return da.localeCompare(db);
    }});
  }} else if (state.sort === 'az') {{
    items = [...items].sort((a,b) => (a.title||'').localeCompare(b.title||''));
  }} else {{
    items = [...items].sort((a,b) => (b.scraped_at||'').localeCompare(a.scraped_at||''));
  }}
  return items;
}}

function render() {{
  const items = filtered();
  const grid = document.getElementById('cardsGrid');
  const empty = document.getElementById('emptyState');
  if (items.length === 0) {{
    grid.innerHTML = '';
    empty.style.display = 'block';
  }} else {{
    empty.style.display = 'none';
    grid.innerHTML = items.map(renderCard).join('');
  }}
  updateCounts();
}}

// ── Count badges ─────────────────────────────────────────────────────────────
function count(loc, cat) {{
  return state.items.filter(i =>
    (loc === 'all' || i.location === loc) &&
    (cat === 'all' || i.category === cat)
  ).length;
}}
function updateCounts() {{
  document.getElementById('cnt-all').textContent = count('all','all');
  document.getElementById('cnt-india').textContent = count('India','all');
  document.getElementById('cnt-world').textContent = count('World','all');
  document.getElementById('cnt-cat-all').textContent = count('all','all');
  document.getElementById('cnt-exam').textContent = count('all','Exam Notification');
  document.getElementById('cnt-conf').textContent = count('all','Conference');
  document.getElementById('cnt-ws').textContent = count('all','Workshop / School');
  document.getElementById('cnt-web').textContent = count('all','Webinar / Lecture');
  document.getElementById('cnt-fellow').textContent = count('all','Fellowship / Award');
}}

// ── Event wiring ──────────────────────────────────────────────────────────────
// Location buttons (sidebar + bottom nav)
document.querySelectorAll('[data-location]').forEach(btn => {{
  btn.addEventListener('click', () => {{
    state.location = btn.dataset.location;
    document.querySelectorAll('[data-location]').forEach(b => b.classList.remove('active'));
    document.querySelectorAll(`[data-location="${{btn.dataset.location}}"]`).forEach(b => b.classList.add('active'));
    render();
  }});
}});

// Category buttons (sidebar)
document.querySelectorAll('.sidebar [data-cat]').forEach(btn => {{
  btn.addEventListener('click', () => {{
    state.category = btn.dataset.cat;
    document.querySelectorAll('.sidebar [data-cat]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    // sync drawer
    document.querySelectorAll('.filter-btn').forEach(b => {{
      b.classList.toggle('active', b.dataset.cat === state.category);
    }});
    render();
  }});
}});

// Drawer filter buttons
document.querySelectorAll('.filter-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    state.category = btn.dataset.cat;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.sidebar [data-cat]').forEach(b => {{
      b.classList.toggle('active', b.dataset.cat === state.category);
    }});
    closeDrawer();
    render();
  }});
}});

// Search
const searchInput = document.getElementById('searchInput');
const searchClear = document.getElementById('searchClear');
searchInput.addEventListener('input', () => {{
  state.search = searchInput.value;
  searchClear.classList.toggle('show', !!state.search);
  render();
}});
searchClear.addEventListener('click', () => {{
  searchInput.value = '';
  state.search = '';
  searchClear.classList.remove('show');
  render();
}});

// Sort
document.getElementById('sortSelect').addEventListener('change', e => {{
  state.sort = e.target.value;
  render();
}});

// Drawer
function openDrawer() {{
  document.getElementById('filterDrawer').classList.add('open');
  document.getElementById('drawerOverlay').classList.add('open');
}}
function closeDrawer() {{
  document.getElementById('filterDrawer').classList.remove('open');
  document.getElementById('drawerOverlay').classList.remove('open');
}}
document.getElementById('filterBtn').addEventListener('click', openDrawer);
document.getElementById('drawerOverlay').addEventListener('click', closeDrawer);

// ── Load data ─────────────────────────────────────────────────────────────────
function init() {{
  if (ITEMS && Array.isArray(ITEMS) && ITEMS.length > 0) {{
    state.items = ITEMS;
    render();
  }} else {{
    // Try fetch as fallback
    fetch('data/items.json')
      .then(r => {{ if (!r.ok) throw new Error('fetch failed'); return r.json(); }})
      .then(data => {{
        state.items = data;
        render();
      }})
      .catch(() => {{
        document.getElementById('cardsGrid').innerHTML = '';
        document.getElementById('errorState').style.display = 'block';
      }});
  }}
}}

init();
}})();
</script>
</body>
</html>"""

    Path("index.html").write_text(html, encoding="utf-8")
    print(f"[build_site] Done. index.html written ({len(html):,} chars, {total} items)")


if __name__ == "__main__":
    main()
