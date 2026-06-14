const API = window.location.origin;

/* ── Auth guard ── */
function requireAuth() {
  if (!localStorage.getItem("token")) {
    window.location.href = "index.html";
  }
}

/* ── Sidebar ──────────────────────────────────────────────── */
function getSidebar(activePage) {
  const pages = [
    { id: "dashboard", label: "Dashboard",             icon: "📊", href: "dashboard.html" },
    { id: "upload",    label: "Upload Dataset",         icon: "📤", href: "upload.html"    },
    { id: "predict",   label: "Demand Forecast",        icon: "🤖", href: "predict.html"   },
    { id: "top",       label: "Top Products",           icon: "🏆", href: "top_product.html" }, // FIX: was top_products.html
    { id: "inventory", label: "Inventory Intelligence", icon: "📦", href: "inventory.html" },
    { id: "reports",   label: "Reports & Analytics",    icon: "📈", href: "reports.html"   },
  ];

  const links = pages.map(page => `
    <a href="${page.href}" class="
      flex items-center gap-3 px-4 py-3 rounded-xl
      transition-all duration-300
      ${page.id === activePage
        ? "bg-white text-blue-900 font-semibold shadow-lg"
        : "text-blue-100 hover:bg-blue-800 hover:translate-x-1"}">
      <span class="text-lg">${page.icon}</span>
      <span class="text-sm">${page.label}</span>
    </a>`).join("");

  return `
    <aside id="sidebarMenu" class="
      fixed md:relative z-50 w-64 min-h-screen
      bg-gradient-to-b from-slate-950 via-blue-950 to-blue-900
      text-white shadow-2xl transition-all duration-300
      -translate-x-full md:translate-x-0 flex flex-col">

      <!-- Logo -->
      <div class="p-5 border-b border-blue-800/60 flex-shrink-0">
        <div class="flex items-center gap-3">
          <div class="w-11 h-11 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500
                      flex items-center justify-center text-xl shadow-lg">🚚</div>
          <div>
            <h2 class="font-bold text-base leading-tight">ChainSight AI</h2>
            <p class="text-[10px] text-blue-300 uppercase tracking-widest">Supply Intelligence</p>
          </div>
        </div>
      </div>

      <!-- AI Status Badge -->
      <div class="px-4 pt-4">
        <div class="bg-blue-800/40 rounded-xl px-3 py-2 flex items-center gap-2 mb-3">
          <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse flex-shrink-0"></span>
          <span class="text-xs text-blue-200">AI Engine Online</span>
        </div>
      </div>

      <!-- Nav -->
      <nav class="px-3 pb-4 space-y-1 flex-1 overflow-y-auto">${links}</nav>

      <!-- Logout -->
      <div class="p-3 border-t border-blue-800/60 flex-shrink-0">
        <button onclick="logout()" class="
          w-full flex items-center gap-3 px-4 py-3 rounded-xl
          text-blue-200 hover:bg-red-600/80 hover:text-white transition-all duration-200 text-sm">
          🚪 <span>Logout</span>
        </button>
      </div>
    </aside>`;
}

/* ── Topbar ── */
function getTopbar(title) {
  return `
    <header class="bg-white shadow-sm border-b border-gray-200 px-5 py-3.5
                   flex items-center justify-between sticky top-0 z-30">
      <div class="flex items-center gap-3">
        <button onclick="toggleSidebar()"
          class="text-xl text-gray-500 hover:text-gray-800 transition md:hidden w-9 h-9
                 flex items-center justify-center rounded-lg hover:bg-gray-100">☰</button>
        <div>
          <h1 class="text-lg font-bold text-gray-800 leading-tight">${title}</h1>
          <p class="text-[10px] text-gray-400 uppercase tracking-widest">
            AI Smart Supply Chain Intelligence
          </p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <button class="w-9 h-9 rounded-full bg-gray-100 hover:bg-gray-200 transition
                       flex items-center justify-center text-base" title="Notifications">🔔</button>
        <div class="w-9 h-9 rounded-full bg-gradient-to-r from-blue-700 to-cyan-500
                    text-white flex items-center justify-center font-bold text-sm shadow">A</div>
      </div>
    </header>`;
}

/* ── renderLayout ────────────────────────────────────────── */
function renderLayout(activePage, title, contentHtml) {
  requireAuth();
  document.body.innerHTML = `
    <div class="flex min-h-screen bg-gray-50">
      ${getSidebar(activePage)}
      <!-- Mobile overlay -->
      <div id="sidebarOverlay"
           class="fixed inset-0 bg-black/40 z-40 hidden md:hidden"
           onclick="toggleSidebar()"></div>
      <div class="flex flex-col flex-1 min-w-0 overflow-hidden">
        ${getTopbar(title)}
        <main class="p-5 fade-in flex-1 overflow-y-auto">${contentHtml}</main>
      </div>
    </div>`;
}

/* ── Sidebar toggle ── */
function toggleSidebar() {
  const sidebar = document.getElementById("sidebarMenu");
  const overlay = document.getElementById("sidebarOverlay");
  if (!sidebar) return;
  const isOpen = !sidebar.classList.contains("-translate-x-full");
  sidebar.classList.toggle("-translate-x-full", isOpen);
  overlay.classList.toggle("hidden", isOpen);
}

/* ── Logout ── */
function logout() {
  localStorage.removeItem("token");
  window.location.href = "index.html";
}

/* ── KPI Stat Card ──────────────────────────────────────── */
function statCard(icon, label, value, color = "blue") {
  const palette = {
    blue:   { wrap: "from-blue-500 to-blue-700",     text: "text-blue-600",   bg: "bg-blue-50"   },
    green:  { wrap: "from-green-500 to-emerald-600", text: "text-green-600",  bg: "bg-green-50"  },
    purple: { wrap: "from-purple-500 to-violet-700", text: "text-purple-600", bg: "bg-purple-50" },
    orange: { wrap: "from-orange-400 to-orange-600", text: "text-orange-600", bg: "bg-orange-50" },
    red:    { wrap: "from-red-500 to-red-700",       text: "text-red-600",    bg: "bg-red-50"    },
  };
  const c = palette[color] || palette.blue;
  const numVal = Number(value);
  const display = (value !== null && value !== undefined && value !== "" && !isNaN(numVal))
    ? numVal.toLocaleString()
    : (value ?? "—");

  return `
    <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100
                hover:shadow-lg hover:-translate-y-1 transition-all duration-300 kpi-card group">
      <div class="flex items-start justify-between mb-3">
        <div class="w-12 h-12 rounded-xl bg-gradient-to-br ${c.wrap}
                    flex items-center justify-center text-xl shadow-md
                    group-hover:scale-110 transition-transform duration-300">
          ${icon}
        </div>
        <span class="text-[10px] font-semibold ${c.text} ${c.bg} px-2 py-1 rounded-full uppercase tracking-wider">
          Live
        </span>
      </div>
      <p class="text-xs text-gray-400 font-medium uppercase tracking-wider mb-1">${label}</p>
      <h3 class="text-2xl font-bold text-gray-800">${display}</h3>
      <div class="mt-2 text-[10px] text-green-600 font-semibold flex items-center gap-1">
        <span class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
        Updated via AI Analytics
      </div>
    </div>`;
}

/* ── Animated counter helper ─────────────────────────────── */
function animateCounters() {
  document.querySelectorAll("[data-count]").forEach(el => {
    const target = parseFloat(el.dataset.count);
    const duration = 1200;
    const start = performance.now();
    const isFloat = el.dataset.count.includes(".");
    function step(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = target * eased;
      el.textContent = isFloat ? current.toFixed(1) : Math.round(current).toLocaleString();
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  });
}