"use strict";

// ── State ────────────────────────────────────────────────────────────────────
let currentExerciseId = null;
let currentDayId      = null;
let currentDay        = null;
let trendChart        = null;
let allPresets = [];
let setupGoal  = null;

const SPLIT_TEMPLATES = [
  {
    id: "ppl",
    name: "Push / Pull / Legs",
    description: "3 days — the most popular split for intermediate lifters",
    days: [
      { name: "Push Day", exercises: ["Bench Press", "Overhead Press", "Incline Bench Press", "Tricep Pushdown", "Lateral Raises"] },
      { name: "Pull Day", exercises: ["Deadlift", "Pull-ups", "Barbell Row", "Barbell Curl", "Face Pulls"] },
      { name: "Legs Day", exercises: ["Squat", "Romanian Deadlift", "Leg Press", "Leg Curl", "Calf Raises"] },
    ],
  },
  {
    id: "upper_lower",
    name: "Upper / Lower",
    description: "2 days — ideal for beginners or 4-day programs",
    days: [
      { name: "Upper Body", exercises: ["Bench Press", "Barbell Row", "Overhead Press", "Barbell Curl", "Tricep Pushdown"] },
      { name: "Lower Body", exercises: ["Squat", "Romanian Deadlift", "Leg Press", "Leg Curl", "Calf Raises"] },
    ],
  },
  {
    id: "full_body",
    name: "Full Body",
    description: "1 day — great for 3x/week training",
    days: [
      { name: "Full Body", exercises: ["Squat", "Bench Press", "Barbell Row", "Overhead Press", "Romanian Deadlift"] },
    ],
  },
  {
    id: "bro_split",
    name: "Bro Split",
    description: "5 days — one muscle group per session",
    days: [
      { name: "Chest Day",     exercises: ["Bench Press", "Incline Bench Press", "Dips"] },
      { name: "Back Day",      exercises: ["Deadlift", "Pull-ups", "Barbell Row", "Cable Row"] },
      { name: "Shoulders Day", exercises: ["Overhead Press", "Lateral Raises", "Face Pulls", "Dumbbell Shoulder Press"] },
      { name: "Arms Day",      exercises: ["Barbell Curl", "Dumbbell Curl", "Hammer Curl", "Tricep Pushdown", "Skull Crushers"] },
      { name: "Legs Day",      exercises: ["Squat", "Romanian Deadlift", "Leg Press", "Leg Curl", "Calf Raises"] },
    ],
  },
];

// ── DOM refs ─────────────────────────────────────────────────────────────────
const viewSplit  = document.getElementById("view-split");
const viewDay    = document.getElementById("view-day");
const viewDetail = document.getElementById("view-detail");

const dayGrid    = document.getElementById("day-grid");
const splitEmpty = document.getElementById("split-empty");
const dayTitle   = document.getElementById("day-title");
const dayExercisesList = document.getElementById("day-exercises-list");

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

const modalAddDay  = document.getElementById("modal-add-day");
const formAddDay   = document.getElementById("form-add-day");
const inputDayName = document.getElementById("input-day-name");
const addDayError  = document.getElementById("add-day-error");

const modalSetup       = document.getElementById("modal-setup");
const setupStep1       = document.getElementById("setup-step-1");
const setupStep2       = document.getElementById("setup-step-2");
const setupGoalLabel   = document.getElementById("setup-goal-label");
const templateGrid     = document.getElementById("template-grid");
const setupError       = document.getElementById("setup-error");

const modalPicker      = document.getElementById("modal-picker");
const pickerSearch     = document.getElementById("picker-search");
const pickerList       = document.getElementById("picker-preset-list");
const formCustomEx     = document.getElementById("form-custom-exercise");
const pickerCustomName = document.getElementById("picker-custom-name");
const pickerCustomLow  = document.getElementById("picker-custom-low");
const pickerCustomHigh = document.getElementById("picker-custom-high");
const pickerCustomInc  = document.getElementById("picker-custom-increment");
const pickerError      = document.getElementById("picker-error");

// ── API helpers ───────────────────────────────────────────────────────────────

async function api(method, path, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") || "";
  if (!ct.includes("application/json")) {
    throw new Error(`Server error (${res.status}) — please restart the Flask server and refresh the page.`);
  }
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

const get  = (path)       => api("GET",    path);
const post = (path, body) => api("POST",   path, body);
const del  = (path)       => api("DELETE", path);

// ── Views ─────────────────────────────────────────────────────────────────────

function showSplit() {
  viewSplit.hidden  = false;
  viewDay.hidden    = true;
  viewDetail.hidden = true;
  currentDayId      = null;
  currentDay        = null;
  currentExerciseId = null;
  loadWorkoutDays();
}

function showDay(day) {
  currentDayId      = day.id;
  currentDay        = day;
  currentExerciseId = null;
  viewSplit.hidden  = true;
  viewDay.hidden    = false;
  viewDetail.hidden = true;
  dayTitle.textContent = day.name;
  loadDayExercises(day.id);
}

function showDetail(exercise) {
  currentExerciseId = exercise.id;
  viewSplit.hidden  = true;
  viewDay.hidden    = true;
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

// ── Split view ────────────────────────────────────────────────────────────────

async function loadWorkoutDays() {
  const days = await get("/api/workout-days");
  dayGrid.innerHTML = "";
  splitEmpty.hidden = days.length > 0;

  days.forEach(day => {
    const card = document.createElement("div");
    card.className = "exercise-card";
    card.innerHTML = `
      <h3>${esc(day.name)}</h3>
      <p class="card-meta">Tap to open &amp; log</p>
    `;
    card.addEventListener("click", () => showDay(day));
    dayGrid.appendChild(card);
  });
}

// ── Day view ──────────────────────────────────────────────────────────────────

async function loadDayExercises(dayId) {
  const exercises = await get(`/api/workout-days/${dayId}/exercises`);
  dayExercisesList.innerHTML = "";

  if (exercises.length === 0) {
    dayExercisesList.innerHTML = `<p class="empty-state">No exercises yet. Add some below!</p>`;
    return;
  }

  exercises.forEach(ex => {
    const card = document.createElement("div");
    card.className = "day-exercise-card";
    card.innerHTML = `
      <div class="day-exercise-header">
        <span class="day-exercise-name" role="button" tabindex="0">${esc(ex.name)}</span>
        <button class="btn-remove" title="Remove from day">×</button>
      </div>
      <div class="day-rec-row">
        <span class="day-rec-badge" id="rec-badge-${ex.id}">Loading…</span>
      </div>
      <div class="day-log-row">
        <input type="number" class="input-day-weight" placeholder="Weight (lbs)" min="0" step="0.5" />
        <input type="number" class="input-day-reps"   placeholder="Reps" min="1" step="1" />
        <button class="btn-primary btn-log-inline">Log</button>
        <span class="inline-feedback" hidden></span>
      </div>
    `;

    card.querySelector(".day-exercise-name").addEventListener("click",  () => showDetail(ex));
    card.querySelector(".day-exercise-name").addEventListener("keydown", e => { if (e.key === "Enter") showDetail(ex); });

    card.querySelector(".btn-remove").addEventListener("click", () => removeExerciseFromDay(dayId, ex.id, card));

    card.querySelector(".btn-log-inline").addEventListener("click", () => {
      const wInput = card.querySelector(".input-day-weight");
      const rInput = card.querySelector(".input-day-reps");
      const fb     = card.querySelector(".inline-feedback");
      logSetInline(ex.id, wInput, rInput, fb);
    });

    dayExercisesList.appendChild(card);
    loadRecBadge(ex.id);
  });
}

async function loadRecBadge(exerciseId) {
  const badge = document.getElementById(`rec-badge-${exerciseId}`);
  if (!badge) return;
  try {
    const rec = await get(`/api/exercises/${exerciseId}/recommendation`);
    badge.textContent = rec.weight === 0
      ? "No history yet"
      : `Next: ${rec.weight} lbs × ${rec.target_reps} reps`;
    if (rec.note) badge.title = rec.note;
  } catch {
    badge.textContent = "—";
  }
}

async function logSetInline(exerciseId, wInput, rInput, fb) {
  hideMsg(fb);
  const weight = parseFloat(wInput.value);
  const reps   = parseInt(rInput.value, 10);

  if (!wInput.value || !rInput.value || isNaN(weight) || isNaN(reps)) {
    showMsg(fb, "Enter weight and reps", true);
    return;
  }

  try {
    await post(`/api/exercises/${exerciseId}/sets`, { date: today(), weight, reps });
    showMsg(fb, "Logged!", false);
    wInput.value = "";
    rInput.value = "";
    loadRecBadge(exerciseId);
  } catch (err) {
    showMsg(fb, err.message, true);
  }
}

async function removeExerciseFromDay(dayId, exerciseId, cardEl) {
  try {
    await del(`/api/workout-days/${dayId}/exercises/${exerciseId}`);
    cardEl.remove();
    if (dayExercisesList.querySelectorAll(".day-exercise-card").length === 0) {
      dayExercisesList.innerHTML = `<p class="empty-state">No exercises yet. Add some below!</p>`;
    }
  } catch (err) {
    alert(err.message);
  }
}

// ── Quick Setup Modal ─────────────────────────────────────────────────────────

function openSetupModal() {
  setupGoal = null;
  setupStep1.hidden = false;
  setupStep2.hidden = true;
  hideMsg(setupError);
  modalSetup.hidden = false;
}

document.getElementById("btn-quick-setup").addEventListener("click", openSetupModal);
document.getElementById("btn-cancel-setup").addEventListener("click", () => { modalSetup.hidden = true; });
modalSetup.addEventListener("click", e => { if (e.target === modalSetup) modalSetup.hidden = true; });

document.getElementById("btn-setup-back").addEventListener("click", () => {
  setupStep1.hidden = false;
  setupStep2.hidden = true;
  hideMsg(setupError);
});

document.querySelectorAll(".goal-card").forEach(btn => {
  btn.addEventListener("click", () => {
    setupGoal = btn.dataset.goal;
    setupGoalLabel.textContent = setupGoal === "strength"
      ? "Strength — 3–6 reps, +5 lb jumps"
      : "Hypertrophy — 8–12 reps, +2.5 lb jumps";
    setupStep1.hidden = true;
    setupStep2.hidden = false;
    renderTemplates(SPLIT_TEMPLATES);
  });
});

function renderTemplates(templates) {
  templateGrid.innerHTML = "";
  templates.forEach(t => {
    const card = document.createElement("div");
    card.className = "template-card";

    const daysList = t.days.map(d =>
      `<li><b>${esc(d.name)}:</b> ${d.exercises.slice(0, 3).map(esc).join(", ")}${d.exercises.length > 3 ? "…" : ""}</li>`
    ).join("");

    card.innerHTML = `
      <strong class="template-name">${esc(t.name)}</strong>
      <p class="template-desc">${esc(t.description)}</p>
      <ul class="template-days">${daysList}</ul>
      <button class="btn-primary template-select-btn">Use This Split</button>
    `;

    card.querySelector(".template-select-btn").addEventListener("click", () => applySetup(t.id));
    templateGrid.appendChild(card);
  });
}

async function applySetup(templateId) {
  hideMsg(setupError);
  try {
    await post("/api/setup", { goal: setupGoal, template: templateId });
    modalSetup.hidden = true;
    loadWorkoutDays();
  } catch (err) {
    showMsg(setupError, err.message, true);
  }
}

// ── Add Day Modal ─────────────────────────────────────────────────────────────

document.getElementById("btn-add-day").addEventListener("click", () => {
  formAddDay.reset();
  hideMsg(addDayError);
  modalAddDay.hidden = false;
  inputDayName.focus();
});

document.getElementById("btn-cancel-add-day").addEventListener("click", () => { modalAddDay.hidden = true; });

modalAddDay.addEventListener("click", e => { if (e.target === modalAddDay) modalAddDay.hidden = true; });

formAddDay.addEventListener("submit", async e => {
  e.preventDefault();
  hideMsg(addDayError);
  try {
    await post("/api/workout-days", { name: inputDayName.value.trim() });
    modalAddDay.hidden = true;
    loadWorkoutDays();
  } catch (err) {
    showMsg(addDayError, err.message, true);
  }
});

// ── Delete Day ────────────────────────────────────────────────────────────────

document.getElementById("btn-delete-day").addEventListener("click", async () => {
  if (!confirm(`Delete "${currentDay.name}"? This cannot be undone.`)) return;
  try {
    await del(`/api/workout-days/${currentDayId}`);
    showSplit();
  } catch (err) {
    alert(err.message);
  }
});

// ── Exercise Picker Modal ─────────────────────────────────────────────────────

document.getElementById("btn-add-exercise-to-day").addEventListener("click", async () => {
  formCustomEx.reset();
  hideMsg(pickerError);
  pickerSearch.value = "";
  modalPicker.hidden = false;

  if (allPresets.length === 0) {
    allPresets = await get("/api/presets");
  }
  renderPickerList(allPresets);
  pickerSearch.focus();
});

document.getElementById("btn-cancel-picker").addEventListener("click", () => { modalPicker.hidden = true; });

modalPicker.addEventListener("click", e => { if (e.target === modalPicker) modalPicker.hidden = true; });

pickerSearch.addEventListener("input", () => {
  const q = pickerSearch.value.toLowerCase();
  renderPickerList(allPresets.filter(p => p.name.toLowerCase().includes(q)));
});

function renderPickerList(exercises) {
  const grouped = {};
  exercises.forEach(ex => {
    if (!grouped[ex.category]) grouped[ex.category] = [];
    grouped[ex.category].push(ex);
  });

  pickerList.innerHTML = "";
  Object.entries(grouped).forEach(([cat, items]) => {
    const header = document.createElement("p");
    header.className  = "picker-category";
    header.textContent = cat;
    pickerList.appendChild(header);

    items.forEach(ex => {
      const row = document.createElement("div");
      row.className  = "picker-row";
      row.textContent = ex.name;
      row.addEventListener("click", () => addPresetToDay(ex.name));
      pickerList.appendChild(row);
    });
  });

  if (exercises.length === 0) {
    pickerList.innerHTML = `<p class="empty-state" style="padding:.75rem">No matches.</p>`;
  }
}

async function addPresetToDay(name) {
  hideMsg(pickerError);
  try {
    await post(`/api/workout-days/${currentDayId}/exercises`, { name });
    modalPicker.hidden = true;
    loadDayExercises(currentDayId);
  } catch (err) {
    showMsg(pickerError, err.message, true);
  }
}

formCustomEx.addEventListener("submit", async e => {
  e.preventDefault();
  hideMsg(pickerError);
  const name = pickerCustomName.value.trim();
  if (!name) { showMsg(pickerError, "Name is required", true); return; }
  try {
    await post(`/api/workout-days/${currentDayId}/exercises`, {
      name,
      rep_range_low:    parseInt(pickerCustomLow.value,  10),
      rep_range_high:   parseInt(pickerCustomHigh.value, 10),
      weight_increment: parseFloat(pickerCustomInc.value),
    });
    modalPicker.hidden = true;
    loadDayExercises(currentDayId);
  } catch (err) {
    showMsg(pickerError, err.message, true);
  }
});

// ── Detail view loaders ───────────────────────────────────────────────────────

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

// ── Log Set form (detail view) ────────────────────────────────────────────────

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

// ── Navigation ────────────────────────────────────────────────────────────────

document.getElementById("btn-back").addEventListener("click", () => {
  if (currentDay) showDay(currentDay);
  else showSplit();
});

document.getElementById("btn-back-to-split").addEventListener("click", showSplit);

const headerTitle = document.getElementById("header-title");
headerTitle.addEventListener("click",   showSplit);
headerTitle.addEventListener("keydown", e => { if (e.key === "Enter") showSplit(); });

document.addEventListener("keydown", e => {
  if (e.key === "Escape") {
    if (!modalSetup.hidden)   modalSetup.hidden   = true;
    else if (!modalAddDay.hidden)  modalAddDay.hidden  = true;
    else if (!modalPicker.hidden)  modalPicker.hidden  = true;
  }
});

// ── Utilities ─────────────────────────────────────────────────────────────────

function today() {
  return new Date().toLocaleDateString("en-CA");
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

showSplit();
