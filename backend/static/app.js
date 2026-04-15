const state = {
  token:             localStorage.getItem("career_token") || "",
  role:              localStorage.getItem("career_role")  || "",
  me:                null,
  selectedStudentId: null,
  status:            "",
  error:             "",
  // dashboard
  section:           "overview",   // overview | grades | cv | opportunities | history
  semester:          "S1",         // active semester tab
  dashboardData:     null,         // cached /api/dashboard response
  cvResult:          null,         // last CV analysis result
  oppResults:        null,         // last opportunity search snapshot
};

const app = document.getElementById("app");
const nav = document.getElementById("nav");

function saveAuth(token, role) {
  state.token = token;
  state.role = role;
  localStorage.setItem("career_token", token);
  localStorage.setItem("career_role", role);
}

function clearAuth() {
  state.token = "";
  state.role = "";
  state.me = null;
  localStorage.removeItem("career_token");
  localStorage.removeItem("career_role");
}

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || "Request failed");
  }
  const contentType = response.headers.get("content-type") || "";
  return contentType.includes("application/json") ? response.json() : response.text();
}

function setStatus(message = "", type = "") {
  state.status = message;
  state.error = type === "error" ? message : "";
}

function statusMarkup() {
  if (!state.status) return "";
  const klass = state.error ? "status error" : "status";
  return `<div class="${klass}">${state.status}</div>`;
}

function renderNav() {
  if (!state.token) {
    nav.innerHTML = `<button class="secondary" data-route="home">Overview</button><button data-route="login">Login</button>`;
    return;
  }
  const dashboardTarget = state.role === "admin" ? "admin" : "dashboard";
  nav.innerHTML = `
    <button class="secondary" data-route="${dashboardTarget}">Dashboard</button>
    <button class="secondary" id="logout-btn">Logout</button>
  `;
  document.getElementById("logout-btn").onclick = () => {
    clearAuth();
    render();
  };
}

function layout(content) {
  app.innerHTML = statusMarkup() + content;
  Array.from(document.querySelectorAll("[data-route]")).forEach((button) => {
    button.onclick = () => {
      location.hash = `#${button.dataset.route}`;
    };
  });
}

function renderHome() {
  layout(`
    <section class="hero">
      <div>
        <div class="eyebrow">IIR — Branch Prediction Platform</div>
        <h1>Find the specialization that fits your academic profile.</h1>
        <p>
          Enter your semester grades, upload your CV, and let the platform recommend
          the right branch for you — IADATA, DSI, or CIR — backed by a Machine Learning model
          trained on real student data.
        </p>
        <div class="chips">
          <span class="chip">IADATA — Intelligence Artificielle & Data</span>
          <span class="chip">DSI — Développement des Systèmes d'Information</span>
          <span class="chip">CIR — Cybersécurité, Infrastructure & Réseaux</span>
        </div>
        <div style="margin-top:22px;display:flex;gap:12px;flex-wrap:wrap;">
          <button data-route="login">Se connecter</button>
        </div>
      </div>
      <div class="hero-stack">
        <div class="highlight">
          <h3>Espace étudiant</h3>
          <p class="muted">Saisie des notes, analyse de CV, recommandations de stages et bourses, historique personnel.</p>
        </div>
        <div class="highlight">
          <h3>Espace administrateur</h3>
          <p class="muted">Gestion des comptes étudiants, consultation des prédictions, CVs et historique académique.</p>
        </div>
      </div>
    </section>
  `);
}

function renderLogin() {
  layout(`
    <section class="panel auth-card">
      <div class="eyebrow">Secure access</div>
      <h2>Login</h2>
      <form id="login-form">
        <label>Email</label>
        <input name="email" type="email" required />
        <label>Password</label>
        <input name="password" type="password" required />
        <button type="submit">Login</button>
      </form>
    </section>
  `);
  document.getElementById("login-form").onsubmit = async (event) => {
    event.preventDefault();
    const form = new FormData(event.target);
    try {
      const payload = await api("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: form.get("email"), password: form.get("password") }),
      });
      saveAuth(payload.access_token, payload.user.role);
      state.me = payload;
      setStatus("");
      location.hash = payload.user.role === "admin" ? "#admin" : "#dashboard";
      render();
    } catch (error) {
      setStatus(error.message, "error");
      renderLogin();
    }
  };
}

// ── Section nav markup ─────────────────────────────────────────────────────────
function sectionNavMarkup() {
  const sections = [
    { id: "overview",      label: "Overview"      },
    { id: "grades",        label: "Grades"        },
    { id: "cv",            label: "CV Analyzer"   },
    { id: "opportunities", label: "Opportunities" },
    { id: "history",       label: "History"       },
  ];
  return `<nav class="section-nav">
    ${sections.map(s => `
      <button class="${s.id === state.section ? "snav-active" : "snav-btn"}" data-section="${s.id}">
        ${s.label}
      </button>
    `).join("")}
  </nav>`;
}

// ── Header strip (always shown above section content) ─────────────────────────
function headerStrip(dashboard) {
  const name = dashboard.profile?.full_name || dashboard.user.email;
  return `
    <div class="dash-header">
      <div class="dash-name">
        <div class="eyebrow">Student workspace</div>
        <h2>${name}</h2>
      </div>
      <div class="dash-metrics">
        <div class="dash-metric">
          <strong>${dashboard.metrics.predictions}</strong>
          <span>Predictions</span>
        </div>
        <div class="dash-metric">
          <strong>${dashboard.metrics.cv_uploads}</strong>
          <span>CV Uploads</span>
        </div>
        <div class="dash-metric">
          <strong>${dashboard.metrics.opportunity_searches}</strong>
          <span>Searches</span>
        </div>
      </div>
    </div>
  `;
}

// ── SECTION: Overview ─────────────────────────────────────────────────────────
function sectionOverview(dashboard) {
  const pred = dashboard.latest_prediction;
  const cv   = dashboard.recent_cv_analysis;
  const predCard = pred ? `
    <div class="card">
      <p class="muted" style="margin-bottom:6px;font-size:0.8rem;text-transform:uppercase;letter-spacing:1px">Latest prediction</p>
      <h2 style="margin:0 0 6px">${pred.predicted_branch}</h2>
      <p style="margin:0 0 12px">${pred.gap_analysis?.message || ""}</p>
      <div class="chips">
        ${Object.entries(pred.probabilities).map(([b, v]) =>
          `<span class="chip">${b}: ${(v * 100).toFixed(1)}%</span>`).join("")}
      </div>
      ${(pred.recommended_courses || []).length ? `
        <p class="muted" style="margin:14px 0 8px;font-size:0.82rem;text-transform:uppercase;letter-spacing:1px">Courses to bridge the gap</p>
        <div class="list">
          ${pred.recommended_courses.slice(0,3).map(c => `
            <div class="list-item">
              <strong>${c.title}</strong>
              <p class="muted">${c.rating ? `⭐ ${Number(c.rating).toFixed(1)}` : ""} ${c.duration ? `· ${c.duration}` : ""}</p>
              ${c.url ? `<a href="${c.url}" target="_blank" style="font-size:0.82rem">Udemy →</a>` : ""}
            </div>`).join("")}
        </div>` : ""}
    </div>` : `<div class="empty">No predictions yet — go to <strong>Grades</strong> to get started.</div>`;

  const cvCard = cv ? `
    <div class="card">
      <p class="muted" style="margin-bottom:6px;font-size:0.8rem;text-transform:uppercase;letter-spacing:1px">Latest CV analysis</p>
      <h2 style="margin:0 0 4px">${cv.recommended_branch || "—"}</h2>
      <p class="muted">Confidence: ${cv.confidence || "—"}</p>
      <pre style="white-space:pre-wrap;font-size:0.8rem;color:#8aa0bb;margin-top:8px;max-height:180px;overflow:auto">${cv.full_analysis_output || ""}</pre>
    </div>` : `<div class="empty">No CV analyzed yet — go to <strong>CV Analyzer</strong>.</div>`;

  const shortcuts = [
    { label: "Predict my branch",       section: "grades"        },
    { label: "Analyze my CV",           section: "cv"            },
    { label: "Find internships",        section: "opportunities" },
    { label: "View history",            section: "history"       },
  ].map(s => `<button class="snav-btn" data-section="${s.section}">${s.label}</button>`).join("");

  return `
    <div class="grid">
      <div class="two-col">
        ${predCard}
        ${cvCard}
      </div>
      <div class="shortcuts">${shortcuts}</div>
    </div>`;
}

// ── SECTION: Grades ───────────────────────────────────────────────────────────
function sectionGrades(dashboard) {
  const semesters = dashboard.semesters;
  const semKeys   = Object.keys(semesters);
  const sem       = semesters[state.semester];

  const semPills = semKeys.map(k => `
    <button class="${k === state.semester ? "sem-active" : "sem-btn"}" data-sem="${k}">${k}</button>
  `).join("");

  const moduleGrid = sem.modules.map(([key, label, coef]) => `
    <div class="grade-cell">
      <label>${label}<span class="coef">×${coef}</span></label>
      <input type="number" min="0" max="20" step="0.25" name="${key}" value="12" />
    </div>`).join("");

  return `
    <div class="panel">
      <div class="section-header">
        <h2>Grade Predictor</h2>
      </div>
      <form id="prediction-form">
        <div class="three-col" style="margin-bottom:18px">
          <div><label>Age</label><input name="age" type="number" min="17" max="60" value="21" /></div>
          <div><label>Gender</label><input name="gender" value="Male" /></div>
          <div>
            <label>Preferred Branch</label>
            <select name="preferred_branch">
              <option value="IADATA">IADATA</option>
              <option value="DSI">DSI</option>
              <option value="CIR">CIR</option>
            </select>
          </div>
        </div>
        <div class="sem-nav">${semPills}</div>
        <p class="muted" style="margin:0 0 14px;font-size:0.88rem">${sem.title}</p>
        <div class="grade-grid">${moduleGrid}</div>
        <button type="submit" style="margin-top:18px;width:100%">Run Prediction</button>
      </form>
    </div>`;
}

// ── SECTION: CV Analyzer ──────────────────────────────────────────────────────
function sectionCv() {
  const resultMarkup = state.cvResult ? `
    <div class="card" style="margin-top:20px;border-left:4px solid #38bdf8">
      <p class="muted" style="margin-bottom:6px;font-size:0.8rem;text-transform:uppercase;letter-spacing:1px">Analysis result</p>
      <h2 style="margin:0 0 4px">${state.cvResult.recommended_branch || "—"}</h2>
      <p class="muted">Confidence: <strong>${state.cvResult.confidence || "—"}</strong></p>
      <pre style="white-space:pre-wrap;font-size:0.82rem;color:#8aa0bb;margin-top:12px">${state.cvResult.analysis_output || ""}</pre>
    </div>` : "";

  return `
    <div class="panel" style="max-width:620px">
      <div class="section-header"><h2>CV Analyzer</h2></div>
      <p class="muted">Upload your CV as a PDF. The AI reads your projects and skills and recommends the best branch — runs locally via Ollama, no internet needed.</p>
      <form id="cv-form" style="margin-top:18px">
        <label>Ollama model</label>
        <select name="ollama_model">
          <option value="llama3.2">llama3.2</option>
          <option value="mistral">mistral</option>
          <option value="gemma2">gemma2</option>
        </select>
        <label>PDF CV</label>
        <input name="file" type="file" accept="application/pdf" required />
        <button type="submit" style="width:100%;margin-top:6px">Upload & Analyze</button>
      </form>
      ${resultMarkup}
    </div>`;
}

// ── SECTION: Opportunities ────────────────────────────────────────────────────
function sectionOpportunities() {
  let resultsMarkup = "";
  if (state.oppResults) {
    const { stages = [], scholarships = [] } = state.oppResults;
    const stagesHtml = stages.length
      ? stages.map(s => `
          <div class="list-item">
            <strong>${s.title}</strong>
            <p class="muted">${s.company} · ${s.location} · ${s.source}</p>
            <a href="${s.url}" target="_blank" style="font-size:0.82rem">View offer →</a>
          </div>`).join("")
      : `<div class="empty">No internships found. Try directly on <a href="https://www.rekrute.com" target="_blank">Rekrute.ma</a>.</div>`;

    const scholHtml = scholarships.length
      ? scholarships.map(s => `
          <div class="list-item">
            <strong>${s.title}</strong>
            <p class="muted">${s.company} · ${s.location}</p>
            <p class="muted" style="font-size:0.82rem">Deadline: ${s.deadline}</p>
            <p style="font-size:0.88rem">${s.description}</p>
            <a href="${s.url}" target="_blank" style="font-size:0.82rem">Apply →</a>
          </div>`).join("")
      : `<div class="empty">No scholarships match your GPA for this branch.</div>`;

    resultsMarkup = `
      <div style="margin-top:24px">
        <h3>Internships</h3>
        <div class="list" style="margin-bottom:20px">${stagesHtml}</div>
        <h3>Scholarships</h3>
        <div class="list">${scholHtml}</div>
      </div>`;
  }

  return `
    <div class="panel" style="max-width:680px">
      <div class="section-header"><h2>Stages & Scholarships</h2></div>
      <p class="muted">Select a branch and enter your GPA to find matching internships and scholarships.</p>
      <form id="opportunity-form" style="margin-top:18px">
        <div class="two-col">
          <div>
            <label>Branch</label>
            <select name="branch">
              <option value="IADATA">IADATA</option>
              <option value="DSI">DSI</option>
              <option value="CIR">CIR</option>
            </select>
          </div>
          <div>
            <label>GPA (/ 20)</label>
            <input name="gpa" type="number" min="0" max="20" step="0.25" value="13" />
          </div>
        </div>
        <button type="submit" style="width:100%">Search</button>
      </form>
      ${resultsMarkup}
    </div>`;
}

// ── SECTION: History ──────────────────────────────────────────────────────────
async function sectionHistory() {
  try {
    const [predictions, cvUploads, searches] = await Promise.all([
      api("/api/predictions"),
      api("/api/cv"),
      api("/api/opportunities/history"),
    ]);

    const predsHtml = predictions.length
      ? predictions.map(p => `
          <div class="list-item">
            <strong>${p.predicted_branch}</strong>
            <p class="muted">${new Date(p.created_at).toLocaleString()}</p>
            <p>${p.gap_analysis?.message || ""}</p>
            <div class="chips" style="margin-top:6px">
              ${Object.entries(p.probabilities).map(([b, v]) =>
                `<span class="chip">${b}: ${(v * 100).toFixed(1)}%</span>`).join("")}
            </div>
          </div>`).join("")
      : `<div class="empty">No predictions yet.</div>`;

    const cvsHtml = cvUploads.length
      ? cvUploads.map(u => `
          <div class="list-item">
            <strong>${u.original_filename}</strong>
            <p class="muted">${new Date(u.uploaded_at).toLocaleString()}</p>
            <p>${u.analyses?.[0]?.recommended_branch
                ? `Recommended: <strong>${u.analyses[0].recommended_branch}</strong> · Confidence: ${u.analyses[0].confidence}`
                : "Stored — no analysis available."}</p>
          </div>`).join("")
      : `<div class="empty">No CVs uploaded yet.</div>`;

    const srchHtml = searches.length
      ? searches.map(s => `
          <div class="list-item">
            <strong>${s.branch}</strong>
            <p class="muted">GPA ${s.gpa} · ${new Date(s.created_at).toLocaleString()}</p>
            <p>${(s.result_snapshot.stages || []).length} stages · ${(s.result_snapshot.scholarships || []).length} scholarships found</p>
          </div>`).join("")
      : `<div class="empty">No opportunity searches yet.</div>`;

    return `
      <div class="grid">
        <div class="two-col">
          <section class="panel">
            <h3>Prediction History</h3>
            <div class="list">${predsHtml}</div>
          </section>
          <section class="panel">
            <h3>CV History</h3>
            <div class="list">${cvsHtml}</div>
          </section>
        </div>
        <section class="panel">
          <h3>Opportunity Searches</h3>
          <div class="list" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px">${srchHtml}</div>
        </section>
      </div>`;
  } catch {
    return `<div class="empty">Failed to load history.</div>`;
  }
}

// ── Main dashboard renderer ───────────────────────────────────────────────────
async function renderDashboard() {
  try {
    if (!state.dashboardData) {
      state.dashboardData = await api("/api/dashboard");
    }
    const dashboard = state.dashboardData;

    let sectionContent = "";
    if      (state.section === "overview")      sectionContent = sectionOverview(dashboard);
    else if (state.section === "grades")        sectionContent = sectionGrades(dashboard);
    else if (state.section === "cv")            sectionContent = sectionCv();
    else if (state.section === "opportunities") sectionContent = sectionOpportunities();
    else if (state.section === "history")       sectionContent = await sectionHistory();

    layout(`
      ${headerStrip(dashboard)}
      ${sectionNavMarkup()}
      <div class="section-content">
        ${statusMarkup()}
        ${sectionContent}
      </div>
    `);

    // Wire section nav
    document.querySelectorAll("[data-section]").forEach(btn => {
      btn.onclick = () => {
        state.section = btn.dataset.section;
        state.status  = "";
        renderDashboard();
      };
    });

    // Wire semester pills
    document.querySelectorAll("[data-sem]").forEach(btn => {
      btn.onclick = () => {
        state.semester = btn.dataset.sem;
        renderDashboard();
      };
    });

    // Wire forms
    document.getElementById("prediction-form")?.addEventListener("submit", submitPrediction);
    document.getElementById("cv-form")?.addEventListener("submit", submitCv);
    document.getElementById("opportunity-form")?.addEventListener("submit", submitOpportunity);

  } catch (error) {
    setStatus(error.message, "error");
    renderHome();
  }
}



async function submitPrediction(event) {
  event.preventDefault();
  const form = new FormData(event.target);
  const module_grades = {};
  for (const [key, value] of form.entries()) {
    if (["age", "gender", "preferred_branch"].includes(key)) continue;
    module_grades[key] = Number(value);
  }
  const btn = event.target.querySelector("button[type=submit]");
  if (btn) { btn.disabled = true; btn.textContent = "Running…"; }
  try {
    const response = await api("/api/predictions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        age: Number(form.get("age")),
        gender: form.get("gender"),
        preferred_branch: form.get("preferred_branch"),
        module_grades,
      }),
    });
    state.dashboardData = null;   // invalidate cache so overview refreshes
    state.section = "overview";
    setStatus(`Prediction saved — recommended branch: ${response.predicted_branch}`);
    renderDashboard();
  } catch (error) {
    setStatus(error.message, "error");
    if (btn) { btn.disabled = false; btn.textContent = "Run Prediction"; }
  }
}

async function submitCv(event) {
  event.preventDefault();
  const form = new FormData(event.target);
  const btn = event.target.querySelector("button[type=submit]");
  if (btn) { btn.disabled = true; btn.textContent = "Analyzing…"; }
  try {
    const response = await api("/api/cv/upload", { method: "POST", body: form });
    if (response.warning) {
      setStatus(response.warning, "error");
      state.cvResult = null;
    } else {
      state.dashboardData = null;
      state.cvResult = response;
      setStatus("");
    }
    renderDashboard();
  } catch (error) {
    setStatus(error.message, "error");
    state.cvResult = null;
    if (btn) { btn.disabled = false; btn.textContent = "Upload & Analyze"; }
  }
}

async function submitOpportunity(event) {
  event.preventDefault();
  const form = new FormData(event.target);
  const btn = event.target.querySelector("button[type=submit]");
  if (btn) { btn.disabled = true; btn.textContent = "Searching…"; }
  try {
    const response = await api("/api/opportunities/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ branch: form.get("branch"), gpa: Number(form.get("gpa")) }),
    });
    state.oppResults = response.result_snapshot;
    setStatus(`Found ${(state.oppResults.stages || []).length} internships and ${(state.oppResults.scholarships || []).length} scholarships.`);
    renderDashboard();
  } catch (error) {
    setStatus(error.message, "error");
    if (btn) { btn.disabled = false; btn.textContent = "Search"; }
  }
}

async function renderAdmin() {
  try {
    const students = await api("/api/admin/students");
    let detailMarkup = `<div class="empty">Select a student to inspect the full history.</div>`;
    if (state.selectedStudentId) {
      const detail = await api(`/api/admin/students/${state.selectedStudentId}`);
      detailMarkup = `
        <div class="grid">
          <div class="card">
            <h3>${detail.profile.full_name}</h3>
            <p class="muted">${detail.user.email}</p>
            <div class="chips">
              <span class="chip">${detail.profile.preferred_branch || "No preferred branch"}</span>
              <span class="chip">${detail.grade_submissions.length} grade submissions</span>
              <span class="chip">${detail.cv_uploads.length} CV uploads</span>
            </div>
          </div>
          <div class="card">
            <h4>Predictions</h4>
            <div class="list">
              ${detail.prediction_results.map((item) => `<div class="list-item"><strong>${item.predicted_branch}</strong><p>${item.gap_analysis.message}</p></div>`).join("") || `<div class="empty">No predictions.</div>`}
            </div>
          </div>
          <div class="card">
            <h4>CV Analyses</h4>
            <div class="list">
              ${detail.cv_analyses.map((item) => `<div class="list-item"><strong>${item.recommended_branch || "No branch"}</strong><p class="muted">${item.confidence || "Unknown confidence"}</p><p>${item.full_analysis_output}</p></div>`).join("") || `<div class="empty">No CV analysis.</div>`}
            </div>
          </div>
        </div>
      `;
    }
    layout(`
      <section class="grid">
        <div class="hero">
          <div>
            <div class="eyebrow">Admin control room</div>
            <h1>See every student and every saved decision.</h1>
            <p>Audit grades, predictions, CV uploads, and search activity from one professional admin view.</p>
          </div>
          <section class="panel">
            <h2>Create User</h2>
            <form id="create-user-form">
              <input name="full_name" placeholder="Full name" required />
              <input name="email" type="email" placeholder="Email" required />
              <input name="password" type="password" placeholder="Temporary password" required />
              <button type="submit">Create Student Account</button>
            </form>
          </section>
        </div>
        <div class="split">
          <section class="table-wrap">
            <div class="section-header"><h2>Students</h2></div>
            <table>
              <thead><tr><th>Name</th><th>Email</th><th>Branch</th><th>Predictions</th><th>CVs</th><th></th></tr></thead>
              <tbody>
                ${students.map((student) => `
                  <tr>
                    <td>${student.full_name}</td>
                    <td>${student.email}</td>
                    <td>${student.preferred_branch || "-"}</td>
                    <td>${student.predictions_count}</td>
                    <td>${student.cv_count}</td>
                    <td><button class="secondary" data-student="${student.student_id}">Open</button></td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </section>
          <section class="panel">${detailMarkup}</section>
        </div>
      </section>
    `);
    document.getElementById("create-user-form").onsubmit = submitCreateUser;
    document.querySelectorAll("[data-student]").forEach((button) => {
      button.onclick = () => {
        state.selectedStudentId = button.dataset.student;
        renderAdmin();
      };
    });
  } catch (error) {
    setStatus(error.message, "error");
    renderHome();
  }
}

async function submitCreateUser(event) {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    await api("/api/admin/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        full_name: form.get("full_name"),
        email: form.get("email"),
        password: form.get("password"),
        role: "user",
      }),
    });
    setStatus("Student account created.");
    renderAdmin();
  } catch (error) {
    setStatus(error.message, "error");
    renderAdmin();
  }
}

async function bootAuth() {
  if (!state.token) return;
  try {
    state.me = await api("/api/me");
    saveAuth(state.me.access_token, state.me.user.role);
  } catch {
    clearAuth();
  }
}

async function render() {
  renderNav();
  const route = (location.hash || "#home").slice(1);
  if (route === "login") return renderLogin();
  if (route === "dashboard" && state.token) return renderDashboard();
  if (route === "admin" && state.token && state.role === "admin") return renderAdmin();
  return renderHome();
}

window.addEventListener("hashchange", render);
bootAuth().then(render);
