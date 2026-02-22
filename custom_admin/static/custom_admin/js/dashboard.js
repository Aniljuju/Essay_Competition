/* ═══════════════════════════════════════════════════════
   custom_admin/static/custom_admin/js/dashboard.js
   Chart.js rendering — data injected by dashboard.html
   ═══════════════════════════════════════════════════════ */
"use strict";

(function() {
  var isDark  = function() { return document.documentElement.getAttribute('data-theme') === 'dark'; };
  var gridCol = function() { return isDark() ? 'rgba(255,255,255,.06)' : 'rgba(0,0,0,.05)'; };
  var textCol = function() { return isDark() ? '#718096' : '#6b7280'; };

  Chart.defaults.font.family = "'Outfit', sans-serif";
  Chart.defaults.font.size   = 12;

  /* User Status Bar Chart */
  var userCtx = document.getElementById('userChart');
  if (userCtx && typeof USER_CHART_DATA !== 'undefined') {
    new Chart(userCtx, {
      type: 'bar',
      data: {
        labels: USER_CHART_DATA.labels,
        datasets: [{
          data: USER_CHART_DATA.values,
          backgroundColor: ['rgba(217,119,6,.14)', 'rgba(5,150,105,.14)', 'rgba(220,53,69,.14)'],
          borderColor:     ['#d97706',              '#059669',              '#dc3545'],
          borderWidth: 2,
          borderRadius: 8,
          borderSkipped: false,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: gridCol() }, ticks: { color: textCol() } },
          y: { grid: { color: gridCol() }, ticks: { color: textCol(), stepSize: 1 }, beginAtZero: true }
        }
      }
    });
  }

  /* Essay Status Doughnut */
  var essayCtx = document.getElementById('essayChart');
  if (essayCtx && typeof ESSAY_CHART_DATA !== 'undefined') {
    new Chart(essayCtx, {
      type: 'doughnut',
      data: {
        labels: ESSAY_CHART_DATA.labels,
        datasets: [{
          data: ESSAY_CHART_DATA.values,
          backgroundColor: ['rgba(30,64,175,.16)', 'rgba(5,150,105,.16)', 'rgba(55,65,81,.16)'],
          borderColor:     ['#1e40af',              '#059669',              '#374151'],
          borderWidth: 2,
          hoverOffset: 8,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '68%',
        plugins: {
          legend: { position: 'bottom', labels: { color: textCol(), padding: 14, font: { size: 11 } } }
        }
      }
    });
  }

  /* Competitions Line Chart */
  var compCtx = document.getElementById('compChart');
  if (compCtx && typeof COMP_CHART_DATA !== 'undefined') {
    new Chart(compCtx, {
      type: 'line',
      data: {
        labels: COMP_CHART_DATA.labels,
        datasets: [{
          label: 'Competitions',
          data: COMP_CHART_DATA.values,
          fill: true,
          tension: 0.42,
          borderColor: '#0f1f38',
          backgroundColor: 'rgba(15,31,56,.07)',
          pointBackgroundColor: '#c8973a',
          pointBorderColor: '#c8973a',
          pointRadius: 5,
          pointHoverRadius: 7,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: gridCol() }, ticks: { color: textCol(), maxRotation: 45 } },
          y: { grid: { color: gridCol() }, ticks: { color: textCol(), stepSize: 1 }, beginAtZero: true }
        }
      }
    });
  }

})();
