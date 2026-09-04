/**
 * RecoverAI — Frontend Application Controller
 * AI-Powered Revenue Recovery & Payment Intelligence Platform
 */

// Configuration: API Base URL defined in one single location
const API_BASE_URL = window.location.origin.includes(":8000")
  ? `${window.location.origin}/api`
  : "http://127.0.0.1:8000/api";

// App State
const state = {
  currentView: "dashboard",
  payments: { page: 1, limit: 15, search: "", status: "ALL", riskLevel: "ALL", sort: "created_at", order: "desc" },
  recovery: { page: 1, limit: 15, status: "ALL", strategy: "ALL", search: "" },
  audit: { page: 1, limit: 20, search: "", action: "ALL" },
  selectedPayment: null,
  charts: {},
};

// ==========================================================================
// API Utility Wrapper
// ==========================================================================
async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultHeaders = {
    "Content-Type": "application/json",
    "Accept": "application/json",
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers: { ...defaultHeaders, ...(options.headers || {}) },
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const errorMsg = data.detail || data.message || `Request failed with status ${response.status}`;
      throw new Error(errorMsg);
    }

    updateSystemHealth(true);
    return data;
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
      updateSystemHealth(false);
      showToast("Unable to connect to RecoverAI API. Ensure backend is running at " + API_BASE_URL, "error");
    } else {
      showToast(err.message, "error");
    }
    throw err;
  }
}

// System Health Monitor
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (res.ok) {
      updateSystemHealth(true);
    } else {
      updateSystemHealth(false);
    }
  } catch {
    updateSystemHealth(false);
  }
}

function updateSystemHealth(isHealthy) {
  const dot = document.getElementById("system-status-dot");
  const text = document.getElementById("system-status-text");
  if (dot && text) {
    if (isHealthy) {
      dot.className = "status-dot";
      text.innerText = "API Connected";
    } else {
      dot.className = "status-dot offline";
      text.innerText = "API Offline";
    }
  }
}

// ==========================================================================
// UI Helpers: Toast Notifications & Modals
// ==========================================================================
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;

  const iconMap = {
    success: "✓",
    error: "✕",
    warning: "⚠️",
    info: "ℹ",
  };

  toast.innerHTML = `
    <span style="font-weight:700;">${iconMap[type] || "•"}</span>
    <span style="flex:1;">${escapeHTML(message)}</span>
    <button style="background:none; border:none; color:var(--text-muted); cursor:pointer; font-size:1.1rem;" onclick="this.parentElement.remove()">&times;</button>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add("open");
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove("open");
  }
}

function openDrawer(drawerId) {
  const drawer = document.getElementById(drawerId);
  if (drawer) {
    drawer.classList.add("open");
  }
}

function closeDrawer(drawerId) {
  const drawer = document.getElementById(drawerId);
  if (drawer) {
    drawer.classList.remove("open");
  }
}

// Helper formatting
function formatCurrency(amount, currency = "INR") {
  if (amount === null || amount === undefined || isNaN(amount)) return "—";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: currency || "INR",
    minimumFractionDigits: 2,
  }).format(amount);
}

function formatDate(dateStr) {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function escapeHTML(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function getStatusBadge(status) {
  const s = (status || "UNKNOWN").toUpperCase();
  let badgeClass = "badge-neutral";
  if (s === "CAPTURED" || s === "SUCCEEDED" || s === "HEALTHY") badgeClass = "badge-captured";
  else if (s === "FAILED" || s === "CRITICAL" || s === "AT_RISK") badgeClass = "badge-failed";
  else if (s === "PENDING" || s === "MEDIUM") badgeClass = "badge-pending";
  else if (s === "ESCALATED" || s === "HIGH") badgeClass = "badge-escalated";
  else if (s === "LOW" || s === "RECOVERED") badgeClass = "badge-low";

  return `<span class="badge ${badgeClass}"><span class="badge-dot"></span>${escapeHTML(s)}</span>`;
}

// ==========================================================================
// Navigation & Router
// ==========================================================================
function navigate(viewName) {
  state.currentView = viewName;

  // Update Sidebar Active state
  document.querySelectorAll(".nav-item").forEach(item => {
    if (item.getAttribute("data-view") === viewName) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });

  // Update Views Visibility
  document.querySelectorAll(".app-view").forEach(v => {
    v.style.display = "none";
  });

  const targetView = document.getElementById(`view-${viewName}`);
  if (targetView) {
    targetView.style.display = "block";
  }

  // Update Breadcrumbs
  const breadcrumbs = document.getElementById("breadcrumbs");
  const group = (viewName === "dashboard" || viewName === "analytics") ? "Overview" :
    (viewName === "events" || viewName === "audit" || viewName === "settings") ? "System" : "Operations";
  const title = viewName.charAt(0).toUpperCase() + viewName.slice(1);
  breadcrumbs.innerHTML = `<span>${group}</span><span class="crumb-sep">/</span><span class="crumb-active">${title}</span>`;

  // Close mobile sidebar if open
  document.getElementById("sidebar").classList.remove("open");

  // Load View Data
  loadViewData(viewName);
}

function loadViewData(viewName) {
  switch (viewName) {
    case "dashboard":
      loadDashboard();
      break;
    case "analytics":
      loadAnalytics();
      break;
    case "payments":
      loadPayments();
      break;
    case "recovery":
      loadRecoveryAttempts();
      break;
    case "risk":
      // Clean or keep last analysis
      break;
    case "customers":
      loadCustomers();
      break;
    case "events":
      generateWebhookEventId();
      break;
    case "audit":
      loadAuditLogs();
      break;
    case "settings":
      checkHealth();
      break;
  }
}

// ==========================================================================
// Dashboard Logic
// ==========================================================================
async function loadDashboard() {
  try {
    const data = await fetchAPI("/dashboard/summary");

    // KPI Cards (Strict Real Database Values)
    document.getElementById("kpi-revenue-at-risk").innerText = data.revenue_at_risk > 0 ? formatCurrency(data.revenue_at_risk, data.currency) : "—";
    document.getElementById("kpi-recovered-revenue").innerText = data.recovered_revenue > 0 ? formatCurrency(data.recovered_revenue, data.currency) : "—";
    document.getElementById("kpi-recovery-rate").innerText = (data.total_payments > 0) ? `${data.recovery_rate}%` : "—";
    document.getElementById("kpi-active-attempts").innerText = data.active_attempts > 0 ? data.active_attempts : "—";

    document.getElementById("kpi-total-payments").innerText = data.total_payments > 0 ? data.total_payments : "—";
    document.getElementById("kpi-failed-payments").innerText = data.failed_payments > 0 ? data.failed_payments : "—";
    document.getElementById("kpi-successful-recoveries").innerText = data.successful_payments > 0 ? data.successful_payments : "—";
    document.getElementById("kpi-human-escalations").innerText = data.human_escalations > 0 ? data.human_escalations : "—";

    document.getElementById("dashboard-last-updated").innerText = `Updated ${new Date().toLocaleTimeString()}`;

    // Render Charts
    renderInterventionsChart(data.intervention_distribution);
    renderRiskDistChart(data.risk_distribution);

    // Render Recent Payments Table
    const payTbody = document.querySelector("#table-dashboard-payments tbody");
    if (data.recent_payments && data.recent_payments.length > 0) {
      payTbody.innerHTML = data.recent_payments.map(p => `
        <tr style="cursor:pointer;" onclick="app.inspectPayment('${p.payment_id}')">
          <td><span class="code-pill">${escapeHTML(p.payment_id)}</span></td>
          <td class="currency-amount">${formatCurrency(p.amount, p.currency)}</td>
          <td>${getStatusBadge(p.status)}</td>
          <td>${getStatusBadge(p.risk_level || 'LOW')}</td>
        </tr>
      `).join("");
    } else {
      payTbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted); padding:16px;">No payments recorded yet</td></tr>`;
    }

    // Render Recent Recovery Attempts Table
    const recTbody = document.querySelector("#table-dashboard-recoveries tbody");
    if (data.recent_recovery_attempts && data.recent_recovery_attempts.length > 0) {
      recTbody.innerHTML = data.recent_recovery_attempts.map(a => `
        <tr style="cursor:pointer;" onclick="app.inspectPayment('${a.payment_id}')">
          <td><span class="code-pill">${escapeHTML(a.attempt_id)}</span></td>
          <td><span class="badge badge-neutral">${escapeHTML(a.intervention)}</span></td>
          <td class="currency-amount">${formatCurrency(a.amount, a.currency)}</td>
          <td>${getStatusBadge(a.status)}</td>
        </tr>
      `).join("");
    } else {
      recTbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted); padding:16px;">No recovery attempts yet</td></tr>`;
    }

  } catch (err) {
    console.error("Error loading dashboard:", err);
  }
}

function renderInterventionsChart(dist) {
  const canvas = document.getElementById("chart-interventions");
  const emptyEl = document.getElementById("chart-interventions-empty");
  if (!canvas) return;

  const labels = Object.keys(dist || {});
  const values = Object.values(dist || {});

  if (labels.length === 0 || values.every(v => v === 0)) {
    canvas.style.display = "none";
    if (emptyEl) emptyEl.style.display = "flex";
    return;
  }

  canvas.style.display = "block";
  if (emptyEl) emptyEl.style.display = "none";

  if (state.charts.interventions) {
    state.charts.interventions.destroy();
  }

  state.charts.interventions = new Chart(canvas, {
    type: "bar",
    data: {
      labels: labels.map(l => l.replace(/_/g, " ")),
      datasets: [{
        label: "Attempts",
        data: values,
        backgroundColor: "rgba(6, 182, 212, 0.75)",
        borderColor: "#06B6D4",
        borderWidth: 1,
        borderRadius: 4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: { ticks: { color: "#94A3B8", font: { size: 10 } }, grid: { display: false } },
        y: { ticks: { color: "#94A3B8", stepSize: 1 }, grid: { color: "rgba(255,255,255,0.05)" } },
      },
    },
  });
}

function renderRiskDistChart(dist) {
  const canvas = document.getElementById("chart-risk-dist");
  const emptyEl = document.getElementById("chart-risk-empty");
  if (!canvas) return;

  const tiers = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
  const values = tiers.map(t => dist ? (dist[t] || 0) : 0);

  if (values.every(v => v === 0)) {
    canvas.style.display = "none";
    if (emptyEl) emptyEl.style.display = "flex";
    return;
  }

  canvas.style.display = "block";
  if (emptyEl) emptyEl.style.display = "none";

  if (state.charts.riskDist) {
    state.charts.riskDist.destroy();
  }

  state.charts.riskDist = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: tiers,
      datasets: [{
        data: values,
        backgroundColor: [
          "rgba(6, 182, 212, 0.8)",   // LOW
          "rgba(245, 158, 11, 0.8)",  // MEDIUM
          "rgba(139, 92, 246, 0.8)",  // HIGH
          "rgba(244, 63, 94, 0.8)",   // CRITICAL
        ],
        borderWidth: 0,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "right", labels: { color: "#94A3B8", boxWidth: 12 } },
      },
      cutout: "68%",
    },
  });
}

// ==========================================================================
// Analytics Logic
// ==========================================================================
async function loadAnalytics() {
  const days = document.getElementById("analytics-timeframe-select")?.value || 14;
  try {
    const data = await fetchAPI(`/analytics/summary?days=${days}`);

    renderTimelineChart("chart-recovered-timeline", "chart-recovered-timeline-empty", data.recovered_revenue_over_time, "Recovered (₹)", "#10B981", "rgba(16, 185, 129, 0.15)");
    renderTimelineChart("chart-risk-timeline", "chart-risk-timeline-empty", data.revenue_at_risk_over_time, "Revenue at Risk (₹)", "#F43F5E", "rgba(244, 63, 94, 0.15)");
    renderFailureReasonsChart(data.failure_reasons);
    renderInterventionRates(data.intervention_success_rates);

  } catch (err) {
    console.error("Error loading analytics:", err);
  }
}

function renderTimelineChart(canvasId, emptyId, series, label, color, fillColor) {
  const canvas = document.getElementById(canvasId);
  const emptyEl = document.getElementById(emptyId);
  if (!canvas) return;

  if (!series || series.length === 0 || series.every(pt => pt.amount === 0)) {
    canvas.style.display = "none";
    if (emptyEl) emptyEl.style.display = "flex";
    return;
  }

  canvas.style.display = "block";
  if (emptyEl) emptyEl.style.display = "none";

  const chartKey = canvasId;
  if (state.charts[chartKey]) {
    state.charts[chartKey].destroy();
  }

  state.charts[chartKey] = new Chart(canvas, {
    type: "line",
    data: {
      labels: series.map(pt => pt.date.slice(5)),
      datasets: [{
        label: label,
        data: series.map(pt => pt.amount),
        borderColor: color,
        backgroundColor: fillColor,
        fill: true,
        tension: 0.35,
        borderWidth: 2,
        pointRadius: 3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#94A3B8", font: { size: 10 } }, grid: { display: false } },
        y: { ticks: { color: "#94A3B8" }, grid: { color: "rgba(255,255,255,0.05)" } },
      },
    },
  });
}

function renderFailureReasonsChart(reasons) {
  const canvas = document.getElementById("chart-failure-reasons");
  const emptyEl = document.getElementById("chart-failure-reasons-empty");
  if (!canvas) return;

  const labels = Object.keys(reasons || {});
  const values = Object.values(reasons || {});

  if (labels.length === 0 || values.every(v => v === 0)) {
    canvas.style.display = "none";
    if (emptyEl) emptyEl.style.display = "flex";
    return;
  }

  canvas.style.display = "block";
  if (emptyEl) emptyEl.style.display = "none";

  if (state.charts.failureReasons) {
    state.charts.failureReasons.destroy();
  }

  state.charts.failureReasons = new Chart(canvas, {
    type: "bar",
    data: {
      labels: labels.map(l => l.replace(/_/g, " ")),
      datasets: [{
        label: "Occurrences",
        data: values,
        backgroundColor: "rgba(244, 63, 94, 0.7)",
        borderColor: "#F43F5E",
        borderWidth: 1,
        borderRadius: 4,
      }],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#94A3B8", stepSize: 1 }, grid: { color: "rgba(255,255,255,0.05)" } },
        y: { ticks: { color: "#94A3B8", font: { size: 10 } }, grid: { display: false } },
      },
    },
  });
}

function renderInterventionRates(rates) {
  const container = document.getElementById("intervention-success-rates-container");
  if (!container) return;

  const keys = Object.keys(rates || {});
  if (keys.length === 0) {
    container.innerHTML = `<div class="empty-state-text" style="text-align:center; padding:20px;">No historical intervention recovery data yet.</div>`;
    return;
  }

  container.innerHTML = keys.map(k => {
    const rate = rates[k];
    return `
      <div style="margin-bottom:14px;">
        <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:4px;">
          <span style="font-weight:600; color:var(--text-primary);">${escapeHTML(k.replace(/_/g, ' '))}</span>
          <span style="color:var(--accent-emerald); font-weight:700;">${rate}% Success</span>
        </div>
        <div style="background:var(--bg-input); height:8px; border-radius:4px; overflow:hidden;">
          <div style="background:linear-gradient(90deg, #06B6D4, #10B981); height:100%; width:${Math.min(100, Math.max(5, rate))}%; border-radius:4px;"></div>
        </div>
      </div>
    `;
  }).join("");
}

// ==========================================================================
// Payments Ledger Logic
// ==========================================================================
async function loadPayments() {
  const { page, limit, search, status, riskLevel, sort, order } = state.payments;
  const tbody = document.getElementById("payments-tbody");
  const emptyState = document.getElementById("payments-empty-state");

  try {
    let url = `/payments?page=${page}&limit=${limit}&sort_by=${sort}&sort_order=${order}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (status !== "ALL") url += `&status=${encodeURIComponent(status)}`;
    if (riskLevel !== "ALL") url += `&risk_level=${encodeURIComponent(riskLevel)}`;

    const data = await fetchAPI(url);

    if (!data.items || data.items.length === 0) {
      tbody.innerHTML = "";
      emptyState.style.display = "flex";
      document.getElementById("payments-pagination-info").innerText = "Showing 0 payments";
      document.getElementById("payments-prev-page").disabled = true;
      document.getElementById("payments-next-page").disabled = true;
      return;
    }

    emptyState.style.display = "none";
    tbody.innerHTML = data.items.map(p => `
      <tr>
        <td><span class="code-pill">${escapeHTML(p.payment_id)}</span></td>
        <td><span style="font-family:var(--font-mono); font-size:0.8rem; color:var(--text-primary);">${escapeHTML(p.customer_id)}</span></td>
        <td class="currency-amount">${formatCurrency(p.amount, p.currency)}</td>
        <td><span class="code-pill">${escapeHTML(p.currency)}</span></td>
        <td>${getStatusBadge(p.status)}</td>
        <td>${getStatusBadge(p.risk_level || 'LOW')}</td>
        <td style="max-width:200px; overflow:hidden; text-overflow:ellipsis; font-size:0.8rem;">${escapeHTML(p.failure_reason || p.failure_code || '—')}</td>
        <td style="font-size:0.8rem;">${formatDate(p.created_at)}</td>
        <td>
          <button class="btn-secondary btn-sm" onclick="app.inspectPayment('${p.payment_id}')">
            Inspect
          </button>
        </td>
      </tr>
    `).join("");

    document.getElementById("payments-pagination-info").innerText = `Showing ${(page - 1) * limit + 1} - ${Math.min(page * limit, data.total)} of ${data.total} payments`;
    document.getElementById("payments-page-num").innerText = `Page ${page} of ${data.total_pages}`;
    document.getElementById("payments-prev-page").disabled = page <= 1;
    document.getElementById("payments-next-page").disabled = page >= data.total_pages;

  } catch (err) {
    console.error("Error loading payments:", err);
  }
}

// Payment Detail Drawer Inspector
async function inspectPayment(paymentId) {
  try {
    const payment = await fetchAPI(`/payments/${paymentId}`);
    state.selectedPayment = payment;

    document.getElementById("drawer-pay-id").innerText = payment.payment_id;
    document.getElementById("drawer-pay-customer").innerText = `Customer: ${payment.customer_id} • Merchant: ${payment.merchant_id}`;

    const body = document.getElementById("drawer-pay-body");
    body.innerHTML = `
      <!-- Financial Overview -->
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:20px;">
        <div style="background:var(--bg-card); padding:14px; border-radius:var(--radius-sm); border:1px solid var(--border-card);">
          <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Amount & Status</div>
          <div style="font-size:1.4rem; font-weight:700; color:var(--text-primary); margin:4px 0;">${formatCurrency(payment.amount, payment.currency)}</div>
          <div>${getStatusBadge(payment.status)}</div>
        </div>

        <div style="background:var(--bg-card); padding:14px; border-radius:var(--radius-sm); border:1px solid var(--border-card);">
          <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Explainable Risk Score</div>
          <div style="font-size:1.4rem; font-weight:700; color:var(--accent-cyan); margin:4px 0;">${payment.risk_score !== null ? `${payment.risk_score}/100` : '—'}</div>
          <div>${getStatusBadge(payment.risk_level || 'LOW')}</div>
        </div>
      </div>

      <!-- Failure Mechanics -->
      <div style="background:var(--bg-card); padding:14px; border-radius:var(--radius-sm); border:1px solid var(--border-card); margin-bottom:20px;">
        <h4 style="font-size:0.85rem; font-weight:600; margin-bottom:8px;">Decline Breakdown</h4>
        <div style="font-size:0.82rem; color:var(--text-secondary); line-height:1.5;">
          <div><strong>Decline Code:</strong> <span class="code-pill">${escapeHTML(payment.failure_code || 'none')}</span></div>
          <div style="margin-top:4px;"><strong>Decline Reason:</strong> ${escapeHTML(payment.failure_reason || 'N/A')}</div>
          <div style="margin-top:4px;"><strong>Attempt Count:</strong> ${payment.attempt_count} / 3 bounded limit</div>
          <div style="margin-top:4px;"><strong>Cause Category:</strong> <span class="badge badge-neutral">${escapeHTML(payment.cause_category || 'UNCLASSIFIED')}</span></div>
        </div>
      </div>

      <!-- Action Trigger -->
      ${payment.status === "FAILED" ? `
        <div style="margin-bottom:24px;">
          <button class="btn-primary" style="width:100%; justify-content:center;" onclick="app.openRecoveryModal('${payment.payment_id}', ${payment.amount}, '${payment.currency}', '${payment.risk_level || 'MEDIUM'}', '${payment.cause_category || 'TEMPORARY_ISSUER_DECLINE'}')">
            <span>Calculate & Execute Recovery</span>
          </button>
        </div>
      ` : ''}

      <!-- Recovery Attempts History -->
      <h4 style="font-size:0.9rem; font-weight:600; margin-bottom:12px;">Recovery Attempt History</h4>
      ${payment.recovery_attempts && payment.recovery_attempts.length > 0 ? `
        <div class="table-responsive" style="margin-bottom:24px;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Attempt ID</th>
                <th>Strategy</th>
                <th>Status</th>
                <th>Recovered</th>
              </tr>
            </thead>
            <tbody>
              ${payment.recovery_attempts.map(a => `
                <tr>
                  <td><span class="code-pill">${escapeHTML(a.attempt_id)}</span></td>
                  <td><span class="badge badge-neutral">${escapeHTML(a.intervention)}</span></td>
                  <td>${getStatusBadge(a.status)}</td>
                  <td>${formatCurrency(a.recovered_amount, a.currency)}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      ` : `<p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:20px;">No recovery attempts launched for this payment yet.</p>`}

      <!-- Interactive Event Timeline -->
      <h4 style="font-size:0.9rem; font-weight:600; margin-bottom:12px;">Lifecycle Audit Timeline</h4>
      <div class="timeline">
        ${payment.audit_logs && payment.audit_logs.length > 0 ? payment.audit_logs.map(log => `
          <div class="timeline-step">
            <div class="timeline-node ${log.action.includes('SUCCEEDED') || log.action.includes('CAPTURED') ? 'success' : log.action.includes('FAILED') ? 'danger' : 'pending'}"></div>
            <div class="timeline-title">${escapeHTML(log.action.replace(/_/g, ' '))}</div>
            <div class="timeline-time">${formatDate(log.timestamp)} • Actor: ${escapeHTML(log.actor)}</div>
            <div class="timeline-desc">${escapeHTML(log.details || '')}</div>
          </div>
        `).join("") : '<p style="font-size:0.8rem; color:var(--text-muted);">No timeline logs recorded.</p>'}
      </div>
    `;

    openDrawer("drawer-payment-detail");
  } catch (err) {
    console.error("Error inspecting payment:", err);
  }
}

// ==========================================================================
// Recovery Operations Logic
// ==========================================================================
async function loadRecoveryAttempts() {
  const { page, limit, status, strategy, search } = state.recovery;
  const tbody = document.getElementById("recovery-tbody");
  const emptyState = document.getElementById("recovery-empty-state");

  try {
    let url = `/recovery/attempts?page=${page}&limit=${limit}`;
    if (status !== "ALL") url += `&status=${encodeURIComponent(status)}`;
    if (strategy !== "ALL") url += `&intervention=${encodeURIComponent(strategy)}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;

    const data = await fetchAPI(url);

    if (!data.items || data.items.length === 0) {
      tbody.innerHTML = "";
      emptyState.style.display = "flex";
      document.getElementById("recovery-pagination-info").innerText = "Showing 0 attempts";
      document.getElementById("recovery-prev-page").disabled = true;
      document.getElementById("recovery-next-page").disabled = true;
      return;
    }

    emptyState.style.display = "none";
    tbody.innerHTML = data.items.map(a => `
      <tr>
        <td><span class="code-pill">${escapeHTML(a.attempt_id)}</span></td>
        <td><span class="code-pill" style="cursor:pointer;" onclick="app.inspectPayment('${a.payment_id}')">${escapeHTML(a.payment_id)}</span></td>
        <td><span class="badge badge-neutral">${escapeHTML(a.intervention)}</span></td>
        <td class="currency-amount">${formatCurrency(a.amount, a.currency)}</td>
        <td>${getStatusBadge(a.status)}</td>
        <td class="currency-amount">${a.recovered_amount > 0 ? formatCurrency(a.recovered_amount, a.currency) : '—'}</td>
        <td style="font-weight:600; color:var(--accent-cyan);">${Math.round((a.recovery_probability || 0.5) * 100)}%</td>
        <td style="font-size:0.8rem;">${formatDate(a.created_at)}</td>
        <td>
          ${a.status === "ESCALATED" ? `
            <button class="btn-primary btn-sm" onclick="app.approveEscalation('${a.attempt_id}')">
              Approve
            </button>
          ` : a.status === "PENDING" ? `
            <button class="btn-secondary btn-sm" onclick="app.simulateWebhookCapture('${a.payment_id}', ${a.amount})">
              Simulate Webhook
            </button>
          ` : `
            <span style="font-size:0.75rem; color:var(--text-muted);">Completed</span>
          `}
        </td>
      </tr>
    `).join("");

    document.getElementById("recovery-pagination-info").innerText = `Showing ${(page - 1) * limit + 1} - ${Math.min(page * limit, data.total)} of ${data.total} attempts`;
    document.getElementById("recovery-page-num").innerText = `Page ${page} of ${data.total_pages}`;
    document.getElementById("recovery-prev-page").disabled = page <= 1;
    document.getElementById("recovery-next-page").disabled = page >= data.total_pages;

  } catch (err) {
    console.error("Error loading recovery attempts:", err);
  }
}

// Open Recovery Execution Modal with Decision Calculation
async function openRecoveryModal(paymentId, amount, currency, riskLevel, causeCategory) {
  try {
    // Call Recovery Decision API
    const decision = await fetchAPI("/recovery/decide", {
      method: "POST",
      body: JSON.stringify({
        payment_id: paymentId,
        risk_level: riskLevel,
        cause_category: causeCategory,
        amount: amount,
      }),
    });

    document.getElementById("m-rec-payment-id").innerText = paymentId;
    document.getElementById("m-rec-amount").innerText = formatCurrency(amount, currency);
    document.getElementById("m-rec-strategy").innerText = decision.intervention;
    document.getElementById("m-rec-probability").innerText = `${Math.round(decision.recovery_probability * 100)}%`;

    const guardrailsEl = document.getElementById("m-rec-guardrails-container");
    guardrailsEl.innerHTML = `
      <div style="margin-bottom:6px;"><strong>Rationale:</strong> ${escapeHTML(decision.reason)}</div>
      <div><strong>Enforced Safety Guardrails:</strong></div>
      <ul style="padding-left:18px; margin-top:4px;">
        ${decision.safety_guardrails_applied.map(g => `<li>${escapeHTML(g)}</li>`).join("")}
      </ul>
    `;

    const confirmBtn = document.getElementById("btn-confirm-recovery-execute");
    confirmBtn.onclick = async () => {
      confirmBtn.disabled = true;
      try {
        await fetchAPI("/recovery/execute", {
          method: "POST",
          body: JSON.stringify({
            payment_id: paymentId,
            intervention: decision.intervention,
            amount: amount,
            currency: currency,
            is_human_approved: decision.requires_human_approval,
          }),
        });

        showToast("Recovery attempt launched in PENDING status. Awaiting payment provider webhook.", "success");
        closeModal("modal-recovery-confirm");
        closeDrawer("drawer-payment-detail");
        loadRecoveryAttempts();
        loadDashboard();
      } finally {
        confirmBtn.disabled = false;
      }
    };

    openModal("modal-recovery-confirm");

  } catch (err) {
    console.error("Error calculating recovery decision:", err);
  }
}

async function approveEscalation(attemptId) {
  try {
    await fetchAPI(`/recovery/attempts/${attemptId}/approve`, {
      method: "POST",
      body: JSON.stringify({
        attempt_id: attemptId,
        approved_by: "OPERATOR",
        notes: "Approved by fintech operations supervisor.",
      }),
    });
    showToast(`Attempt ${attemptId} approved. Transitioned to active recovery queue.`, "success");
    loadRecoveryAttempts();
    loadDashboard();
  } catch (err) {
    console.error("Error approving escalation:", err);
  }
}

// ==========================================================================
// Risk Intelligence Logic
// ==========================================================================
async function handleRiskAnalyzeForm() {
  const paymentId = document.getElementById("risk-input-payment-id").value.trim();
  if (!paymentId) return;

  const btn = document.getElementById("btn-run-risk-analysis");
  btn.disabled = true;

  try {
    const analysis = await fetchAPI("/risk/analyze", {
      method: "POST",
      body: JSON.stringify({ payment_id: paymentId }),
    });

    const body = document.getElementById("risk-result-body");
    const tierBadge = document.getElementById("risk-badge-tier");
    tierBadge.outerHTML = getStatusBadge(analysis.risk_level);

    body.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; background:var(--bg-app); padding:16px; border-radius:var(--radius-sm); border:1px solid var(--border-card);">
        <div>
          <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Composite Risk Score</div>
          <div style="font-size:2rem; font-weight:800; color:var(--accent-cyan); line-height:1.2;">
            ${analysis.risk_score} <span style="font-size:0.9rem; color:var(--text-muted);">/ 100</span>
          </div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Recovery Priority</div>
          <div style="font-size:1.1rem; font-weight:700; color:var(--text-primary);">${analysis.recovery_priority}</div>
        </div>
      </div>

      <div style="margin-bottom:16px; font-size:0.85rem;">
        <div><strong>Root Cause Category:</strong> <span class="badge badge-neutral">${escapeHTML(analysis.cause_category)}</span> (${Math.round(analysis.cause_confidence * 100)}% confidence)</div>
        <div style="margin-top:6px;"><strong>Recommended Next Action:</strong> ${escapeHTML(analysis.recommended_immediate_action)}</div>
      </div>

      <h4 style="font-size:0.85rem; font-weight:600; margin-bottom:8px;">Explainability Factor Breakdown</h4>
      <ul style="font-size:0.8rem; color:var(--text-secondary); line-height:1.6; padding-left:18px; margin-bottom:20px;">
        ${analysis.reasons.map(r => `<li>${escapeHTML(r)}</li>`).join("")}
      </ul>

      <button class="btn-primary" style="width:100%; justify-content:center;" onclick="app.inspectPayment('${analysis.payment_id}')">
        <span>Open Payment Recovery Console</span>
      </button>
    `;

    showToast(`Risk score computed: ${analysis.risk_score}/100 (${analysis.risk_level})`, "info");

  } catch (err) {
    console.error("Error analyzing risk:", err);
  } finally {
    btn.disabled = false;
  }
}

// ==========================================================================
// Customers Logic
// ==========================================================================
async function loadCustomers() {
  const tbody = document.getElementById("customers-tbody");
  const emptyState = document.getElementById("customers-empty-state");

  try {
    const data = await fetchAPI("/customers");

    if (!data.items || data.items.length === 0) {
      tbody.innerHTML = "";
      emptyState.style.display = "flex";
      return;
    }

    emptyState.style.display = "none";
    tbody.innerHTML = data.items.map(c => `
      <tr>
        <td><span class="code-pill">${escapeHTML(c.customer_id)}</span></td>
        <td>${c.payment_count}</td>
        <td><span style="color:${c.failed_payments > 0 ? 'var(--accent-rose)' : 'inherit'}; font-weight:${c.failed_payments > 0 ? '600' : 'normal'}">${c.failed_payments}</span></td>
        <td class="currency-amount" style="color:var(--accent-emerald);">${formatCurrency(c.recovered_revenue, c.currency)}</td>
        <td class="currency-amount" style="color:${c.revenue_at_risk > 0 ? 'var(--accent-rose)' : 'inherit'};">${formatCurrency(c.revenue_at_risk, c.currency)}</td>
        <td style="font-size:0.8rem;">${formatDate(c.last_payment_date)}</td>
        <td>${getStatusBadge(c.recovery_status)}</td>
        <td>
          <button class="btn-secondary btn-sm" onclick="app.filterPaymentsByCustomer('${c.customer_id}')">
            View Ledger
          </button>
        </td>
      </tr>
    `).join("");

  } catch (err) {
    console.error("Error loading customers:", err);
  }
}

function filterPaymentsByCustomer(customerId) {
  state.payments.search = customerId;
  const input = document.getElementById("payments-search-input");
  if (input) input.value = customerId;
  navigate("payments");
}

// ==========================================================================
// Events & Webhook Simulator Logic
// ==========================================================================
function generateWebhookEventId() {
  const id = `evt_wh_${Math.random().toString(36).substring(2, 10)}`;
  const input = document.getElementById("wh-event-id");
  if (input) input.value = id;
}

function generatePaymentId() {
  const id = `pay_usr_${Math.random().toString(36).substring(2, 10)}`;
  const input = document.getElementById("new-pay-id");
  if (input) input.value = id;
}

function simulateWebhookCapture(paymentId, amount) {
  navigate("events");
  document.getElementById("wh-payment-id").value = paymentId;
  document.getElementById("wh-amount").value = amount;
  document.getElementById("wh-status").value = "captured";
  generateWebhookEventId();
}

async function handleWebhookSubmit() {
  const eventId = document.getElementById("wh-event-id").value.trim();
  const paymentId = document.getElementById("wh-payment-id").value.trim();
  const status = document.getElementById("wh-status").value;
  const amount = parseFloat(document.getElementById("wh-amount").value);
  const reason = document.getElementById("wh-reason").value.trim();

  const inspector = document.getElementById("wh-inspector-output");
  inspector.innerText = `// Sending POST /api/webhooks/payment ...\n`;

  try {
    const payload = {
      event_id: eventId,
      payment_id: paymentId,
      status: status,
      amount: amount,
      currency: "INR",
      failure_reason: reason || undefined,
    };

    const res = await fetchAPI("/webhooks/payment", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    inspector.innerText = `// Webhook Ingestion Response [200 OK]:\n` + JSON.stringify(res, null, 2);

    if (res.duplicate) {
      showToast("Duplicate webhook received: Idempotency enforced (no repeated processing).", "info");
    } else {
      showToast(`Webhook processed: Payment ${paymentId} marked as ${status.toUpperCase()}.`, "success");
    }

  } catch (err) {
    inspector.innerText = `// Error:\n` + err.message;
  }
}

// Payment Event Ingest Modal Handler
async function handlePaymentCreateSubmit() {
  const paymentId = document.getElementById("new-pay-id").value.trim();
  const customerId = document.getElementById("new-pay-customer").value.trim();
  const amount = parseFloat(document.getElementById("new-pay-amount").value);
  const status = document.getElementById("new-pay-status").value;
  const failureCode = document.getElementById("new-pay-failure-code").value;
  const failureReason = document.getElementById("new-pay-reason").value.trim();

  try {
    await fetchAPI("/payments/events", {
      method: "POST",
      body: JSON.stringify({
        payment_id: paymentId,
        customer_id: customerId,
        amount: amount,
        currency: "INR",
        status: status,
        failure_code: status === "FAILED" ? failureCode : undefined,
        failure_reason: status === "FAILED" ? failureReason : undefined,
      }),
    });

    showToast(`Payment ${paymentId} created successfully.`, "success");
    closeModal("modal-payment-create");
    loadPayments();
    loadDashboard();
  } catch (err) {
    console.error("Error creating payment:", err);
  }
}

// ==========================================================================
// Audit Trail Logic
// ==========================================================================
async function loadAuditLogs() {
  const { page, limit, search, action } = state.audit;
  const tbody = document.getElementById("audit-tbody");
  const emptyState = document.getElementById("audit-empty-state");

  try {
    let url = `/audit?page=${page}&limit=${limit}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (action !== "ALL") url += `&action=${encodeURIComponent(action)}`;

    const data = await fetchAPI(url);

    if (!data.items || data.items.length === 0) {
      tbody.innerHTML = "";
      emptyState.style.display = "flex";
      document.getElementById("audit-pagination-info").innerText = "Showing 0 log entries";
      document.getElementById("audit-prev-page").disabled = true;
      document.getElementById("audit-next-page").disabled = true;
      return;
    }

    emptyState.style.display = "none";
    tbody.innerHTML = data.items.map(log => `
      <tr>
        <td style="font-size:0.8rem;">${formatDate(log.timestamp)}</td>
        <td><span class="badge badge-neutral">${escapeHTML(log.action)}</span></td>
        <td>${log.payment_id ? `<span class="code-pill">${escapeHTML(log.payment_id)}</span>` : '—'}</td>
        <td>${log.attempt_id ? `<span class="code-pill">${escapeHTML(log.attempt_id)}</span>` : '—'}</td>
        <td><span class="code-pill">${escapeHTML(log.actor)}</span></td>
        <td>${log.status ? getStatusBadge(log.status) : '—'}</td>
        <td style="font-size:0.8rem; color:var(--text-secondary); max-width:320px; overflow:hidden; text-overflow:ellipsis;">${escapeHTML(log.details || '')}</td>
      </tr>
    `).join("");

    document.getElementById("audit-pagination-info").innerText = `Showing ${(page - 1) * limit + 1} - ${Math.min(page * limit, data.total)} of ${data.total} logs`;
    document.getElementById("audit-page-num").innerText = `Page ${page} of ${data.total_pages}`;
    document.getElementById("audit-prev-page").disabled = page <= 1;
    document.getElementById("audit-next-page").disabled = page >= data.total_pages;

  } catch (err) {
    console.error("Error loading audit logs:", err);
  }
}

// ==========================================================================
// Demo Data Seeder Controls
// ==========================================================================
async function seedData() {
  const btn = document.getElementById("btn-quick-seed");
  if (btn) btn.disabled = true;

  try {
    const res = await fetchAPI("/seed", { method: "POST" });
    showToast(res.message || "Seeded realistic multi-scenario demo records.", "success");
    loadViewData(state.currentView);
  } catch (err) {
    console.error("Error seeding data:", err);
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function clearData() {
  if (!confirm("Are you sure you want to wipe all records? This will return the database to a 100% clean empty state.")) {
    return;
  }

  try {
    const res = await fetchAPI("/seed/clear", { method: "POST" });
    showToast(res.message || "All database tables wiped successfully.", "info");
    loadViewData(state.currentView);
  } catch (err) {
    console.error("Error clearing data:", err);
  }
}

// ==========================================================================
// Initialization & Event Listeners
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
  // Navigation Clicks
  document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const view = item.getAttribute("data-view");
      if (view) navigate(view);
    });
  });

  // Mobile Toggle
  const mobileToggle = document.getElementById("mobile-toggle");
  if (mobileToggle) {
    mobileToggle.addEventListener("click", () => {
      document.getElementById("sidebar").classList.toggle("open");
    });
  }

  // Refresh Button
  const refreshBtn = document.getElementById("btn-refresh");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      loadViewData(state.currentView);
      showToast("Data refreshed", "info");
    });
  }

  // Quick Action Buttons
  document.getElementById("btn-quick-seed")?.addEventListener("click", seedData);
  document.getElementById("btn-quick-ingest")?.addEventListener("click", () => {
    generatePaymentId();
    openModal("modal-payment-create");
  });
  document.getElementById("btn-payments-ingest")?.addEventListener("click", () => {
    generatePaymentId();
    openModal("modal-payment-create");
  });
  document.getElementById("btn-new-recovery-modal")?.addEventListener("click", () => {
    navigate("payments");
    showToast("Select a failed payment to launch a recovery action.", "info");
  });

  // Timeframe selector
  document.getElementById("analytics-timeframe-select")?.addEventListener("change", loadAnalytics);

  // Search Debouncing for Payments
  let searchTimeout;
  document.getElementById("payments-search-input")?.addEventListener("input", (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      state.payments.search = e.target.value;
      state.payments.page = 1;
      loadPayments();
    }, 300);
  });

  // Filters for Payments
  document.getElementById("payments-status-filter")?.addEventListener("change", (e) => {
    state.payments.status = e.target.value;
    state.payments.page = 1;
    loadPayments();
  });
  document.getElementById("payments-risk-filter")?.addEventListener("change", (e) => {
    state.payments.riskLevel = e.target.value;
    state.payments.page = 1;
    loadPayments();
  });
  document.getElementById("payments-sort-select")?.addEventListener("change", (e) => {
    const val = e.target.value;
    if (val === "created_at_desc") { state.payments.sort = "created_at"; state.payments.order = "desc"; }
    else if (val === "created_at_asc") { state.payments.sort = "created_at"; state.payments.order = "asc"; }
    else if (val === "amount_desc") { state.payments.sort = "amount"; state.payments.order = "desc"; }
    else if (val === "amount_asc") { state.payments.sort = "amount"; state.payments.order = "asc"; }
    state.payments.page = 1;
    loadPayments();
  });

  // Pagination for Payments
  document.getElementById("payments-prev-page")?.addEventListener("click", () => {
    if (state.payments.page > 1) {
      state.payments.page--;
      loadPayments();
    }
  });
  document.getElementById("payments-next-page")?.addEventListener("click", () => {
    state.payments.page++;
    loadPayments();
  });

  // Filters for Recovery Center
  document.getElementById("recovery-status-filter")?.addEventListener("change", (e) => {
    state.recovery.status = e.target.value;
    state.recovery.page = 1;
    loadRecoveryAttempts();
  });
  document.getElementById("recovery-strategy-filter")?.addEventListener("change", (e) => {
    state.recovery.strategy = e.target.value;
    state.recovery.page = 1;
    loadRecoveryAttempts();
  });
  document.getElementById("recovery-prev-page")?.addEventListener("click", () => {
    if (state.recovery.page > 1) {
      state.recovery.page--;
      loadRecoveryAttempts();
    }
  });
  document.getElementById("recovery-next-page")?.addEventListener("click", () => {
    state.recovery.page++;
    loadRecoveryAttempts();
  });

  // Keyboard accessibility: Escape key closes modals and drawers
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.querySelectorAll(".modal-backdrop.open").forEach(m => m.classList.remove("open"));
      document.querySelectorAll(".drawer-backdrop.open").forEach(d => d.classList.remove("open"));
    }
  });

  // Initial Load
  checkHealth();
  navigate("dashboard");
});

// Expose public methods to window for inline HTML onclick handlers
window.app = {
  navigate,
  seedData,
  clearData,
  inspectPayment,
  openRecoveryModal,
  approveEscalation,
  simulateWebhookCapture,
  filterPaymentsByCustomer,
  handleRiskAnalyzeForm,
  handleWebhookSubmit,
  handlePaymentCreateSubmit,
  generateWebhookEventId,
  generatePaymentId,
  openModal,
  closeModal,
  openDrawer,
  closeDrawer,
};
