"use strict";

// ── Constants ─────────────────────────────────────────────────────────────────

const MONTH_NAMES = ["January","February","March","April","May","June",
                     "July","August","September","October","November","December"];

const SPLIT_TEMPLATES = [
  {
    id: "ppl",
    name: "Push / Pull / Legs",
    description: "3 days — the most popular split for intermediate lifters",
    days: [
      { name: "Push Day", exercises: ["Bench Press","Overhead Press","Incline Bench Press","Tricep Pushdown","Lateral Raises"] },
      { name: "Pull Day", exercises: ["Deadlift","Pull-ups","Barbell Row","Barbell Curl","Face Pulls"] },
      { name: "Legs Day", exercises: ["Squat","Romanian Deadlift","Leg Press","Leg Curl","Calf Raises"] },
    ],
  },
  {
    id: "upper_lower",
    name: "Upper / Lower",
    description: "2 days — ideal for beginners or 4-day programs",
    days: [
      { name: "Upper Body", exercises: ["Bench Press","Barbell Row","Overhead Press","Barbell Curl","Tricep Pushdown"] },
      { name: "Lower Body", exercises: ["Squat","Romanian Deadlift","Leg Press","Leg Curl","Calf Raises"] },
    ],
  },
  {
    id: "full_body",
    name: "Full Body",
    description: "1 day — great for 3x/week training",
    days: [
      { name: "Full Body", exercises: ["Squat","Bench Press","Barbell Row","Overhead Press","Romanian Deadlift"] },
    ],
  },
  {
    id: "bro_split",
    name: "Bro Split",
    description: "5 days — one muscle group per session",
    days: [
      { name: "Chest Day",     exercises: ["Bench Press","Incline Bench Press","Dips"] },
      { name: "Back Day",      exercises: ["Deadlift","Pull-ups","Barbell Row","Cable Row"] },
      { name: "Shoulders Day", exercises: ["Overhead Press","Lateral Raises","Face Pulls","Dumbbell Shoulder Press"] },
      { name: "Arms Day",      exercises: ["Barbell Curl","Dumbbell Curl","Hammer Curl","Tricep Pushdown","Skull Crushers"] },
      { name: "Legs Day",      exercises: ["Squat","Romanian Deadlift","Leg Press","Leg Curl","Calf Raises"] },
    ],
  },
];

// ── State ────────────────────────────────────────────────────────────────────

let calYear  = new Date().getFullYear();
let calMonth = new Date().getMonth();
let loggedDates = new Set();

let currentSessionDate  = null;
let currentSessionDayId = null;

let currentDayId = null;
let currentDay   = null;

let currentExerciseId = null;
let backDestination   = "calendar"; // "calendar" | "session" | "day"

let trendChart = null;
let allPresets = [];
let setupGoal  = null;

// ── DOM refs ─────────────────────────────────────────────────────────────────

const viewCalendar        = document.getElementById("view-calendar");
const calGrid             = document.getElementById("cal-grid");
const calMonthLabel       = document.getElementById("cal-month-label");

const viewSession         = document.getElementById("view-session");
const sessionDateTitle    = document.getElementById("session-date-title");
const sessionPicker       = document.getElementById("session-picker");
const sessionDayOptions   = document.getElementById("session-day-options");
const sessionNoSplit      = document.getElementById("session-no-split");
const sessionLog          = document.getElementById("session-log");
const sessionDayLabel     = document.getElementById("session-day-label");
const sessionExercises    = document.getElementById("session-exercises");

const viewSplit           = document.getElementById("view-split");
const dayGrid             = document.getElementById("day-grid");
const splitEmpty          = document.getElementById("split-empty");

const viewDay             = document.getElementById("view-day");
const dayTitle            = document.getElementById("day-title");
const dayExercisesList    = document.getElementById("day-exercises-list");

const viewDetail          = document.getElementById("view-detail");
const detailTitle         = document.getElementById("detail-title");
const detailRange         = document.getElementById("detail-range");
const recWeight           = document.getElementById("rec-weight");
const recReps             = document.getElementById("rec-reps");
const recNote             = document.getElementById("rec-note");
const historyContainer    = document.getElementById("history-container");
const chartEmpty          = document.getElementById("chart-empty");

const modalAddDay         = document.getElementById("modal-add-day");
const formAddDay          = document.getElementById("form-add-day");
const inputDayName        = document.getElementById("input-day-name");
const addDayError         = document.getElementById("add-day-error");

const modalPicker         = document.getElementById("modal-picker");
const pickerSearch        = document.getElementById("picker-search");
const pickerList          = document.getElementById("picker-preset-list");
const formCustomEx        = document.getElementById("form-custom-exercise");
const pickerCustomName    = document.getElementById("picker-custom-name");
const pickerCustomLow     = document.getElementById("picker-custom-low");
const pickerCustomHigh    = document.getElementById("picker-custom-high");
const pickerCustomInc     = document.getElementById("picker-custom-increment");
const pickerError         = document.getElementById("picker-error");

const modalSetup          = document.getElementById("modal-setup");
const setupStep1          = document.getElementById("setup-step-1");
const setupStep2          = document.getElementById("setup-step-2");
const setupGoalLabel      = document.getElementById("setup-goal-label");
const templateGrid        = document.getElementById("template-grid");
const setupError          = document.getElementById("setup-error");

// ── API helpers ───────────────────────────────────────────────────────────────

async function api(method, path, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") || "";
  if (!ct.includes("application/json")) {
    throw new Error(`Server error (${res.status}) — please restart the Flask server and refresh.`);
  }
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

const get  = (path)       => api("GET",    path);
const post = (path, body) => api("POST",   path, body);
const del  = (path)       => api("DELETE", path);

// ── View helpers ──────────────────────────────────────────────────────────────

function hideAllViews() {
  viewCalendar.hidden = true;
  viewSession.hidden  = true;
  viewSplit.hidden    = true;
  viewDay.hidden      = true;
  viewDetail.hidden   = true;
}

// ── Calendar ──────────────────────────────────────────────────────────────────

async function showCalendar() {
  hideAllViews();
  viewCalendar.hidden = false;
  renderCalendarGrid();           // draw grid immediately — no waiting
  try {
    const dates = await get(`/api/calendar/${calYear}/${calMonth + 1}`);
    loggedDates = new Set(dates);
    renderCalendarGrid();         // re-draw with workout dots
  } catch { /* dots won't show, but calendar is still usable */ }
}

function renderCalendarGrid() {
  calMonthLabel.textContent = `${MONTH_NAMES[calMonth]} ${calYear}`;

  const firstDayOfWeek = new Date(calYear, calMonth, 1).getDay();
  const daysInMonth    = new Date(calYear, calMonth + 1, 0).getDate();
  const todayStr       = today();

  calGrid.innerHTML = "";

  // Day-of-week headers
  ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"].forEach(d => {
    const h = document.createElement("div");
    h.className   = "cal-header-cell";
    h.textContent = d;
    calGrid.appendChild(h);
  });

  // Empty leading cells
  for (let i = 0; i < firstDayOfWeek; i++) {
    const e = document.createElement("div");
    e.className = "cal-cell cal-empty";
    calGrid.appendChild(e);
  }

  // Day cells
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${calYear}-${String(calMonth + 1).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
    const cell = document.createElement("div");
    cell.className = "cal-cell";
    if (dateStr === todayStr) cell.classList.add("cal-today");

    const num = document.createElement("span");
    num.className   = "cal-day-num";
    num.textContent = d;
    cell.appendChild(num);

    if (loggedDates.has(dateStr)) {
      const dot = document.createElement("span");
      dot.className = "cal-dot";
      cell.appendChild(dot);
    }

    cell.addEventListener("click", () => showSession(dateStr));
    calGrid.appendChild(cell);
  }
}

document.getElementById("btn-cal-prev").addEventListener("click", () => {
  calMonth--;
  if (calMonth < 0) { calMonth = 11; calYear--; }
  showCalendar();
});

document.getElementById("btn-cal-next").addEventListener("click", () => {
  calMonth++;
  if (calMonth > 11) { calMonth = 0; calYear++; }
  showCalendar();
});

// ── Session view ──────────────────────────────────────────────────────────────

async function showSession(dateStr) {
  currentSessionDate = dateStr;
  hideAllViews();
  viewSession.hidden = false;

  const [y, m, d] = dateStr.split("-").map(Number);
  sessionDateTitle.textContent = new Date(y, m - 1, d).toLocaleDateString("en-US", {
    weekday: "long", year: "numeric", month: "long", day: "numeric",
  });

  sessionPicker.hidden = false;
  sessionLog.hidden    = true;
  sessionDayOptions.innerHTML = '<p class="empty-state">Loading…</p>';
  sessionExercises.innerHTML  = "";
  sessionNoSplit.hidden = true;

  try {
    // Check if a workout was already started for this date
    let existingSession = null;
    try {
      existingSession = await get(`/api/sessions/${dateStr}`);
    } catch { /* no session or endpoint missing — continue to picker */ }

    if (existingSession) {
      currentSessionDayId = existingSession.session.workout_day_id;
      showSessionLog(existingSession.session.workout_day_name, existingSession.exercises, dateStr);
    } else {
      const days = await get("/api/workout-days");
      sessionDayOptions.innerHTML = "";
      renderSessionPicker(days);
    }
  } catch (err) {
    sessionDayOptions.innerHTML =
      `<p class="error" style="padding:.5rem">Failed to load: ${esc(err.message)}</p>`;
  }
}

function renderSessionPicker(days) {
  sessionDayOptions.innerHTML = "";
  if (days.length === 0) {
    sessionNoSplit.hidden = false;
    return;
  }
  days.forEach(day => {
    const card = document.createElement("div");
    card.className = "exercise-card";
    card.innerHTML = `<h3>${esc(day.name)}</h3>`;
    card.addEventListener("click", () => selectWorkoutDay(day));
    sessionDayOptions.appendChild(card);
  });
}

async function selectWorkoutDay(day) {
  currentSessionDayId = day.id;
  try {
    const result = await post("/api/sessions", {
      date: currentSessionDate,
      workout_day_id: day.id,
    });
    showSessionLog(day.name, result.exercises, currentSessionDate);
  } catch (err) {
    alert(err.message);
  }
}

async function showSessionLog(dayName, exercises, date) {
  sessionPicker.hidden = true;
  sessionLog.hidden    = false;
  sessionDayLabel.textContent = dayName;
  sessionExercises.innerHTML  = "";

  // Pre-load any sets already logged on this date
  const todaySets = await get(`/api/sessions/${date}/sets`);
  const setsByEx  = {};
  todaySets.forEach(s => { setsByEx[s.exercise_id] = s; });

  if (exercises.length === 0) {
    sessionExercises.innerHTML = `<p class="empty-state">No exercises in this day yet. Add some in My Split.</p>`;
    return;
  }

  exercises.forEach(ex => {
    const card = document.createElement("div");
    card.className = "day-exercise-card";

    const existing = setsByEx[ex.id];

    card.innerHTML = `
      <div class="day-exercise-header">
        <span class="day-exercise-name" role="button" tabindex="0">${esc(ex.name)}</span>
      </div>
      <div class="day-rec-row">
        <span class="day-rec-badge" id="rec-badge-${ex.id}">Loading…</span>
      </div>
      <div class="day-log-row">
        <input type="number" class="input-day-weight" placeholder="Weight (lbs)" min="0" step="0.5"
               value="${existing ? existing.weight : ''}" />
        <input type="number" class="input-day-reps" placeholder="Reps" min="1" step="1"
               value="${existing ? existing.reps : ''}" />
        <span class="save-status" hidden></span>
      </div>
    `;

    card.querySelector(".day-exercise-name").addEventListener("click", () => {
      backDestination = "session";
      showDetail(ex);
    });
    card.querySelector(".day-exercise-name").addEventListener("keydown", e => {
      if (e.key === "Enter") { backDestination = "session"; showDetail(ex); }
    });

    const wInput = card.querySelector(".input-day-weight");
    const rInput = card.querySelector(".input-day-reps");
    const status = card.querySelector(".save-status");
    let saveTimer = null;

    function scheduleAutoSave() {
      clearTimeout(saveTimer);
      const weight = parseFloat(wInput.value);
      const reps   = parseInt(rInput.value, 10);
      if (!wInput.value || !rInput.value || isNaN(weight) || isNaN(reps)) return;
      saveTimer = setTimeout(async () => {
        try {
          await api("PUT", `/api/exercises/${ex.id}/sets/${date}`, { weight, reps });
          status.textContent = "Saved";
          status.className   = "save-status saved";
          status.hidden      = false;
          setTimeout(() => { status.hidden = true; }, 2000);
          loadRecBadge(ex.id);
          if (!loggedDates.has(date)) loggedDates.add(date);
        } catch (err) {
          status.textContent = err.message;
          status.className   = "save-status error";
          status.hidden      = false;
        }
      }, 600);
    }

    wInput.addEventListener("input", scheduleAutoSave);
    rInput.addEventListener("input", scheduleAutoSave);

    sessionExercises.appendChild(card);
    loadRecBadge(ex.id);
  });
}

document.getElementById("btn-back-to-cal").addEventListener("click", showCalendar);

document.getElementById("btn-change-workout").addEventListener("click", async () => {
  sessionLog.hidden    = true;
  sessionPicker.hidden = false;
  sessionDayOptions.innerHTML = "";
  const days = await get("/api/workout-days");
  renderSessionPicker(days);
});

document.getElementById("btn-go-to-split").addEventListener("click", showSplitView);

// ── Split management ──────────────────────────────────────────────────────────

function showSplitView() {
  hideAllViews();
  viewSplit.hidden = false;
  loadWorkoutDays();
}

async function loadWorkoutDays() {
  const days = await get("/api/workout-days");
  dayGrid.innerHTML = "";
  splitEmpty.hidden = days.length > 0;
  days.forEach(day => {
    const card = document.createElement("div");
    card.className = "exercise-card";
    card.innerHTML = `<h3>${esc(day.name)}</h3><p class="card-meta">Tap to manage exercises</p>`;
    card.addEventListener("click", () => showDay(day));
    dayGrid.appendChild(card);
  });
}

function showDay(day) {
  currentDayId = day.id;
  currentDay   = day;
  hideAllViews();
  viewDay.hidden = false;
  dayTitle.textContent = day.name;
  loadDayExercises(day.id);
}

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
        <button class="btn-remove" title="Remove from day">&#215;</button>
      </div>
      <p class="card-meta">${ex.rep_range_low}–${ex.rep_range_high} reps &nbsp;·&nbsp; +${ex.weight_increment} lbs</p>
    `;

    card.querySelector(".day-exercise-name").addEventListener("click", () => {
      backDestination = "day";
      showDetail(ex);
    });
    card.querySelector(".btn-remove").addEventListener("click", () =>
      removeExerciseFromDay(dayId, ex.id, card)
    );

    dayExercisesList.appendChild(card);
  });
}

async function removeExerciseFromDay(dayId, exerciseId, cardEl) {
  try {
    await del(`/api/workout-days/${dayId}/exercises/${exerciseId}`);
    cardEl.remove();
    if (!dayExercisesList.querySelector(".day-exercise-card")) {
      dayExercisesList.innerHTML = `<p class="empty-state">No exercises yet. Add some below!</p>`;
    }
  } catch (err) {
    alert(err.message);
  }
}

document.getElementById("btn-my-split").addEventListener("click", showSplitView);
document.getElementById("btn-back-split-to-cal").addEventListener("click", showCalendar);
document.getElementById("btn-back-to-split").addEventListener("click", showSplitView);

document.getElementById("btn-delete-day").addEventListener("click", async () => {
  if (!confirm(`Delete "${currentDay.name}"? This cannot be undone.`)) return;
  try {
    await del(`/api/workout-days/${currentDayId}`);
    showSplitView();
  } catch (err) {
    alert(err.message);
  }
});

// ── Exercise Detail view ──────────────────────────────────────────────────────

function showDetail(exercise) {
  currentExerciseId = exercise.id;
  hideAllViews();
  viewDetail.hidden = false;

  detailTitle.textContent = exercise.name;
  detailRange.textContent =
    `Rep range: ${exercise.rep_range_low}–${exercise.rep_range_high}  ·  +${exercise.weight_increment} lbs per progression`;

  loadRecommendation(exercise.id);
  loadHistory(exercise.id);
  loadTrend(exercise.id);
}

document.getElementById("btn-back").addEventListener("click", () => {
  if (backDestination === "session") showSession(currentSessionDate);
  else if (backDestination === "day") showDay(currentDay);
  else showCalendar();
});

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
        <td>${s.weight}</td><td>${s.reps}</td><td>${orm}</td>
      </tr>`;
    });
  });
  html += `</tbody></table>`;
  historyContainer.innerHTML = html;
}

async function loadTrend(exerciseId) {
  const trend = await get(`/api/exercises/${exerciseId}/trend`);
  if (trendChart) { trendChart.destroy(); trendChart = null; }
  if (trend.length === 0) { chartEmpty.hidden = false; return; }
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
        fill: true, tension: 0.3,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { grid: { display: false } }, y: { beginAtZero: false } },
    },
  });
}


// ── Shared day-exercise helpers ───────────────────────────────────────────────

async function loadRecBadge(exerciseId) {
  const badge = document.getElementById(`rec-badge-${exerciseId}`);
  if (!badge) return;
  try {
    const rec = await get(`/api/exercises/${exerciseId}/recommendation`);
    badge.textContent = rec.weight === 0
      ? "No history yet — enter your starting weight"
      : `Next: ${rec.weight} lbs × ${rec.target_reps} reps`;
    if (rec.note) badge.title = rec.note;
  } catch {
    badge.textContent = "—";
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

// ── Exercise Picker Modal ─────────────────────────────────────────────────────

document.getElementById("btn-add-exercise-to-day").addEventListener("click", async () => {
  formCustomEx.reset();
  hideMsg(pickerError);
  pickerSearch.value = "";
  modalPicker.hidden = false;
  if (allPresets.length === 0) allPresets = await get("/api/presets");
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
  if (exercises.length === 0) {
    pickerList.innerHTML = `<p class="empty-state" style="padding:.75rem">No matches.</p>`;
    return;
  }
  Object.entries(grouped).forEach(([cat, items]) => {
    const header = document.createElement("p");
    header.className = "picker-category";
    header.textContent = cat;
    pickerList.appendChild(header);
    items.forEach(ex => {
      const row = document.createElement("div");
      row.className = "picker-row";
      row.textContent = ex.name;
      row.addEventListener("click", () => addPresetToDay(ex.name));
      pickerList.appendChild(row);
    });
  });
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
      rep_range_low:    parseInt(pickerCustomLow.value, 10),
      rep_range_high:   parseInt(pickerCustomHigh.value, 10),
      weight_increment: parseFloat(pickerCustomInc.value),
    });
    modalPicker.hidden = true;
    loadDayExercises(currentDayId);
  } catch (err) {
    showMsg(pickerError, err.message, true);
  }
});

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
      `<li><b>${esc(d.name)}:</b> ${d.exercises.slice(0,3).map(esc).join(", ")}${d.exercises.length > 3 ? "…" : ""}</li>`
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

// ── Global keyboard handler ───────────────────────────────────────────────────

document.addEventListener("keydown", e => {
  if (e.key === "Escape") {
    if (!modalSetup.hidden)   modalSetup.hidden   = true;
    else if (!modalAddDay.hidden)  modalAddDay.hidden  = true;
    else if (!modalPicker.hidden)  modalPicker.hidden  = true;
  }
});

// ── Header title ──────────────────────────────────────────────────────────────

const headerTitle = document.getElementById("header-title");
headerTitle.addEventListener("click",   showCalendar);
headerTitle.addEventListener("keydown", e => { if (e.key === "Enter") showCalendar(); });

// ── Utilities ─────────────────────────────────────────────────────────────────

function today() {
  return new Date().toLocaleDateString("en-CA");
}

function esc(str) {
  return String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function showMsg(el, msg, isError) {
  el.textContent = msg;
  el.className   = isError ? "error" : "feedback";
  el.hidden      = false;
}

function hideMsg(el) { el.hidden = true; }

// ── Boot ──────────────────────────────────────────────────────────────────────

showCalendar();
