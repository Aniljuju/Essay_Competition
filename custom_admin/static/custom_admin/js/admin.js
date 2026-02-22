/* ═══════════════════════════════════════════════════════
   custom_admin/static/custom_admin/js/admin.js
   Global JS: sidebar, dark mode, clock, toast, AJAX helpers
   ═══════════════════════════════════════════════════════ */
"use strict";

/* ── CSRF token ──────────────────────────────────────── */
function getCsrf() {
  return document.cookie
    .split('; ')
    .find(r => r.startsWith('csrftoken='))
    ?.split('=')[1] ?? '';
}

/* ── AJAX POST ───────────────────────────────────────── */
async function ajaxPost(url, data) {
  const fd = new FormData();
  fd.append('csrfmiddlewaretoken', getCsrf());
  Object.entries(data).forEach(([k, v]) => fd.append(k, v));
  const res = await fetch(url, { method: 'POST', body: fd });
  if (!res.ok) throw new Error('HTTP ' + res.status);
  return res.json();
}

/* ── Toast ───────────────────────────────────────────── */
function toast(msg, type) {
  type = type || 'success';
  const rack = document.getElementById('toast-rack');
  if (!rack) return;
  const el = document.createElement('div');
  el.className = 'ca-toast ' + type;
  const icons = { success: 'bi-check-circle-fill', error: 'bi-x-circle-fill', info: 'bi-info-circle-fill' };
  el.innerHTML = '<i class="bi ' + (icons[type] || icons.info) + '"></i><span>' + msg + '</span>';
  rack.appendChild(el);
  setTimeout(function() {
    el.style.animation = 'toastOut .3s ease forwards';
    setTimeout(function() { el.remove(); }, 300);
  }, 3500);
}

/* ── Sidebar ─────────────────────────────────────────── */
(function() {
  var sidebar   = document.getElementById('sidebar');
  var toggleBtn = document.getElementById('sidebarToggle');
  if (!sidebar || !toggleBtn) return;

  var isDesktop = function() { return window.innerWidth >= 993; };

  // Restore desktop collapse state
  if (isDesktop() && localStorage.getItem('ca_sidebar') === 'collapsed') {
    sidebar.style.transform = 'translateX(-100%)';
    document.getElementById('main-wrap').style.marginLeft = '0';
  }

  var collapsed = false;
  toggleBtn.addEventListener('click', function() {
    if (isDesktop()) {
      collapsed = !collapsed;
      sidebar.style.transform   = collapsed ? 'translateX(-100%)' : '';
      document.getElementById('main-wrap').style.marginLeft = collapsed ? '0' : '';
      localStorage.setItem('ca_sidebar', collapsed ? 'collapsed' : 'open');
    } else {
      sidebar.classList.toggle('open');
    }
  });

  // Close on outside tap (mobile)
  document.addEventListener('click', function(e) {
    if (!isDesktop() && sidebar.classList.contains('open')) {
      if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    }
  });
})();

/* ── Dark mode ───────────────────────────────────────── */
(function() {
  var btn  = document.getElementById('themeToggle');
  var icon = document.getElementById('themeIcon');
  var html = document.documentElement;

  function apply(theme) {
    html.setAttribute('data-theme', theme);
    if (icon) icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
    localStorage.setItem('ca_theme', theme);
  }

  apply(localStorage.getItem('ca_theme') || 'light');
  if (btn) btn.addEventListener('click', function() {
    apply(html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
  });
})();

/* ── Live clock ──────────────────────────────────────── */
(function() {
  var el = document.getElementById('liveClock');
  if (!el) return;
  function tick() {
    el.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  tick();
  setInterval(tick, 30000);
})();
