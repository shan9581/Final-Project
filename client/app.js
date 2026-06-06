"use strict";

// ── State ────────────────────────────────────────────────────────────────────
let currentExerciseId = null;
let trendChart = null;

// ── DOM refs ─────────────────────────────────────────────────────────────────
const viewList   = document.getElementById("view-list");
const viewDetail = document.getElementById("view-detail");
const exerciseGrid  = document.getElementById("exercise-grid");
const emptyState    = document.getElementById("empty-state");

const detailTitle   = document.getElementById("detail-title");
const detailRange   = document.getElementById("detail-range");
const formLogSet    = document.getElementById("form-log-set");
const inputDate     = document.getElementById("input-date");
const inputWeight   = document.getElementById("input-weight");
const inputReps     = document.getElementById("input-reps");
const logFeedback   = document.getElementById("log-feedback");

const recWeight     = document.getElementById("rec-weight");
const recReps       = document.getElementById("rec-reps");
const recNote       = document.getElementById("rec-note");

const historyContainer = document.getElementById("history-container");
const chartEmpty       = document.getElementById("chart-empty");

const modalOverlay     = document.getElementById("modal-overlay");
const formAddExercise  = document.getElementById("form-add-exercise");
const inputName        = document.getElementById("input-name");
const inputLow         = document.getElementById("input-low");
const inputHigh        = document.getElementById("input-high");
const inputIncrement   = document.getElementById("input-increment");
const modalError       = document.getElementById("modal-error");

// ── API helpers ───────────────────────────────────────────────────────────────

async function api(method, path, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

const get  = (path)        => api("GET", path);
const post = (path, body)  => api("POST", path, body);

// ── Views ─────────────────────────────────────────────────────────────────────

function showList() {
  viewList.hidden   = false;
  viewDetail.hidden = true;
  currentExerciseId = null;
  loadExercises();
}

function showDetail(exercise) {
  currentExerciseId = exercise.id;
  viewList.hidden   = true;
  viewDetail.hidden = false;

  detailTitle.textContent = exercise.name;
  detailRange.textContent =
    `Rep range: ${exercise.rep_range_low}–${exercise.rep_range_high}  ·  +${exercise.weight_increment} lbs per progression`;

  inputDate.value   = today();
  inputWeight.value = "";
  inputReps.value   = "";
  hideMsg(logFeedback);

  loadRecommendation(exercise.id);
  loadHistory(exercise.id);
  loadTrend(exercise.id);
}

// ── Data loaders ──────────────────────────────────────────────────────────────

async function loadExercises() {
  const exercises = await get("/api/exercises");
  exerciseGrid.innerHTML = "";
  emptyState.hidden = exercises.length > 0;

  exercises.forEach(ex => {
    const card = document.createElement("div");
    card.className = "exercise-card";
    card.innerHTML = `
      <h3>${esc(ex.name)}</h3>
      <p class="card-meta">${ex.rep_range_low}–${ex.rep_range_high} reps &nbsp;·&nbsp; +${ex.weight_increment} lbs</p>
    `;
    card.addEventListener("click", () => showDetail(ex));
    exerciseGrid.appendChild(card);
  });
}

async function loadRecommendation(exerciseId) {
  const rec = await get(`/api/exercises/${exerciseId}/recommendation`);
  recWeight.textContent = rec.weight === 0 ? "—" : rec.weight;
  recReps.textContent   = rec.target_reps;
  recNote.textContent   = rec.note;
}

async function loadHistory(exerciseId) {
  const history = await get(`/api/exercises/${exerciseId}/history`);

  if (history.length === 0) {
    historyContainer.innerHTML = `<p class="empty-state">No sets logged yet.</p>`;
    return;
  }

  // Group by date descending for display
  const byDate = {};
  [...history].reverse().forEach(s => {
    if (!byDate[s.date]) byDate[s.date] = [];
    byDate[s.date].push(s);
  });

  let html = `<table><thead><tr><th>Date</th><th>Weight (lbs)</th><th>Reps</th><th>Est. 1RM</th></tr></thead><tbody>`;
  Object.entries(byDate).forEach(([date, sets]) => {
    sets.forEach((s, i) => {
      const orm = (s.weight * (1 + s.reps / 30)).toFixed(1);
      html += `<tr>
        <td>${i === 0 ? esc(date) : ""}</td>
        <td>${s.weight}</td>
        <td>${s.reps}</td>
        <td>${orm}</td>
      </tr>`;
    });
  });
  html += `</tbody></table>`;
  historyContainer.innerHTML = html;
}

async function loadTrend(exerciseId) {
  const trend = await get(`/api/exercises/${exerciseId}/trend`);

  if (trendChart) { trendChart.destroy(); trendChart = null; }

  if (trend.length === 0) {
    chartEmpty.hidden = false;
    return;
  }
  chartEmpty.hidden = true;

  const ctx = document.getElementById("trend-chart").getContext("2d");
  trendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: trend.map(t => t.date),
      datasets: [{
        label: "Estimated 1RM (lbs)",
        data: trend.map(t => t.estimated_1rm),
        borderColor: "#2563eb",
        backgroundColor: "rgba(37,99,235,.08)",
        pointBackgroundColor: "#2563eb",
        fill: true,
        tension: 0.3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: false },
      },
    },
  });
}

// ── Log Set form ──────────────────────────────────────────────────────────────

formLogSet.addEventListener("submit", async e => {
  e.preventDefault();
  hideMsg(logFeedback);

  try {
    await post(`/api/exercises/${currentExerciseId}/sets`, {
      date:   inputDate.value,
      weight: parseFloat(inputWeight.value),
      reps:   parseInt(inputReps.value, 10),
    });

    showMsg(logFeedback, "Set logged!", false);
    inputWeight.value = "";
    inputReps.value   = "";
    loadRecommendation(currentExerciseId);
    loadHistory(currentExerciseId);
    loadTrend(currentExerciseId);
  } catch (err) {
    showMsg(logFeedback, err.message, true);
  }
});

// ── Modal ─────────────────────────────────────────────────────────────────────

document.getElementById("btn-add-exercise").addEventListener("click", () => {
  formAddExercise.reset();
  hideMsg(modalError);
  modalOverlay.hidden = false;
  inputName.focus();
});

document.getElementById("btn-cancel-modal").addEventListener("click", closeModal);

modalOverlay.addEventListener("click", e => {
  if (e.target === modalOverlay) closeModal();
});

document.addEventListener("keydown", e => {
  if (e.key === "Escape" && !modalOverlay.hidden) closeModal();
});

formAddExercise.addEventListener("submit", async e => {
  e.preventDefault();
  hideMsg(modalError);

  try {
    await post("/api/exercises", {
      name:             inputName.value.trim(),
      rep_range_low:    parseInt(inputLow.value, 10),
      rep_range_high:   parseInt(inputHigh.value, 10),
      weight_increment: parseFloat(inputIncrement.value),
    });
    closeModal();
    loadExercises();
  } catch (err) {
    showMsg(modalError, err.message, true);
  }
});

function closeModal() { modalOverlay.hidden = true; }

// ── Nav ───────────────────────────────────────────────────────────────────────

document.getElementById("btn-back").addEventListener("click", showList);

const headerTitle = document.getElementById("header-title");
headerTitle.addEventListener("click", showList);
headerTitle.addEventListener("keydown", e => { if (e.key === "Enter") showList(); });

// ── Utilities ─────────────────────────────────────────────────────────────────

function today() {
  return new Date().toLocaleDateString("en-CA"); // YYYY-MM-DD in local time
}

function esc(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function showMsg(el, msg, isError) {
  el.textContent = msg;
  el.className   = isError ? "error" : "feedback";
  el.hidden      = false;
}

function hideMsg(el) { el.hidden = true; }

// ── Boot ──────────────────────────────────────────────────────────────────────

showList();
