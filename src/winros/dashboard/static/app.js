const state = {
  data: null,
  group: "All",
  selectedRun: null,
  settings: {
    accent: "#2f9e8f",
    density: "comfortable",
    showResearch: true,
  },
};

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || response.statusText);
  }
  return data;
}

async function loadState() {
  state.data = await api("/api/state");
  mergeSettings();
  render();
}

function mergeSettings() {
  const local = JSON.parse(localStorage.getItem("winros-dashboard") || "{}");
  const theme = state.data.config?.theme || {};
  const preferences = state.data.config?.preferences || {};
  state.settings.accent = local.accent || theme.accent || state.settings.accent;
  state.settings.density = local.density || theme.density || state.settings.density;
  state.settings.showResearch = local.showResearch ?? preferences.show_research_runs ?? true;
  document.documentElement.style.setProperty("--accent", state.settings.accent);
  document.body.classList.toggle("compact", state.settings.density === "compact");
}

function render() {
  $("versionText").textContent = `v${state.data.project.version}`;
  renderNav();
  renderOverview();
  renderProfiles();
  renderRuns();
  renderSettings();
}

function visibleProfiles() {
  const profiles = state.data.profiles || [];
  return profiles.filter((profile) => {
    if (!state.settings.showResearch && profile.group === "Research Runs") return false;
    if (state.group === "All") return true;
    return profile.group === state.group;
  });
}

function profileGroups() {
  const groups = new Set(["All"]);
  for (const profile of state.data.profiles || []) {
    if (!state.settings.showResearch && profile.group === "Research Runs") continue;
    groups.add(profile.group);
  }
  return [...groups];
}

function renderNav() {
  const nav = $("groupNav");
  nav.innerHTML = "";
  for (const group of profileGroups()) {
    const groupProfiles = (state.data.profiles || []).filter((profile) => {
      if (!state.settings.showResearch && profile.group === "Research Runs") return false;
      return group === "All" || profile.group === group;
    });
    const count = groupProfiles.length;
    const button = document.createElement("button");
    button.className = `nav-button ${state.group === group ? "active" : ""}`;
    button.type = "button";
    button.innerHTML = `<span>${group}</span><strong>${count}</strong>`;
    button.addEventListener("click", () => {
      state.group = group;
      renderProfiles();
      renderNav();
    });
    nav.append(button);
  }
}

function renderOverview() {
  const envError = state.data.envs?.error;
  const metrics = [
    ["Tasks", state.data.tasks.length, "registered tracks"],
    ["Robots", state.data.robots.length, "built-in models"],
    ["Assets", state.data.assets.filter((asset) => asset.available).length, "available locally"],
    ["Envs", state.data.envs.items.length, envError ? "optional deps missing" : "training IDs"],
  ];
  $("overview").innerHTML = metrics
    .map(([label, value, note]) => `
      <article class="metric">
        <strong>${escapeHtml(String(value))}</strong>
        <span>${escapeHtml(label)} · ${escapeHtml(note)}</span>
      </article>
    `)
    .join("");
}

function renderProfiles() {
  const profiles = visibleProfiles();
  $("profileHeading").textContent = state.group === "All" ? "Profiles" : state.group;
  $("profileCount").textContent = `${profiles.length} available`;
  $("profiles").innerHTML = profiles.map(renderProfileCard).join("");
  for (const profile of profiles) {
    const card = document.querySelector(`[data-profile="${profile.id}"]`);
    card.querySelector("[data-preview]").addEventListener("click", () => previewProfile(profile));
    card.querySelector("[data-run]").addEventListener("click", () => runProfile(profile));
  }
}

function renderProfileCard(profile) {
  const tags = [profile.mode, ...(profile.tags || [])]
    .map((tag) => `<span class="pill">${escapeHtml(tag)}</span>`)
    .join("");
  const params = (profile.params || []).map((param) => renderParam(profile, param)).join("");
  return `
    <article class="profile-card" data-profile="${escapeAttr(profile.id)}">
      <div>
        <h3>${escapeHtml(profile.title)}</h3>
        <div class="profile-meta">${tags}</div>
      </div>
      <p class="profile-summary">${escapeHtml(profile.summary || "")}</p>
      <div class="param-grid">${params}</div>
      <div class="profile-actions">
        <button class="secondary-button" type="button" data-preview>Preview</button>
        <button class="primary-button" type="button" data-run>Run</button>
      </div>
    </article>
  `;
}

function renderParam(profile, param) {
  const id = `${profile.id}-${param.name}`;
  if (param.type === "select") {
    const options = (param.choices || [])
      .map((choice) => `
        <option value="${escapeAttr(choice)}" ${choice === param.default ? "selected" : ""}>
          ${escapeHtml(choice)}
        </option>
      `)
      .join("");
    return `
      <label>
        <span>${escapeHtml(param.label || param.name)}</span>
        <select id="${escapeAttr(id)}" data-param="${escapeAttr(param.name)}">${options}</select>
      </label>
    `;
  }
  const type = param.type === "int" || param.type === "float" ? "number" : "text";
  const min = param.min !== undefined ? `min="${escapeAttr(String(param.min))}"` : "";
  const value = param.default ?? "";
  return `
    <label>
      <span>${escapeHtml(param.label || param.name)}</span>
      <input id="${escapeAttr(id)}" data-param="${escapeAttr(param.name)}"
        type="${type}" ${min} value="${escapeAttr(String(value))}" />
    </label>
  `;
}

function collectParams(profile) {
  const card = document.querySelector(`[data-profile="${cssEscape(profile.id)}"]`);
  const params = {};
  card.querySelectorAll("[data-param]").forEach((input) => {
    params[input.dataset.param] = input.value;
  });
  return params;
}

async function previewProfile(profile) {
  try {
    const data = await api("/api/preview", {
      method: "POST",
      body: JSON.stringify({ profileId: profile.id, params: collectParams(profile) }),
    });
    $("commandPreview").textContent = data.command;
  } catch (error) {
    $("commandPreview").textContent = error.message;
  }
}

async function runProfile(profile) {
  if (profile.mode === "training" || profile.group === "Research Runs") {
    const ok = confirm(`Start ${profile.title}?`);
    if (!ok) return;
  }
  try {
    const run = await api("/api/runs", {
      method: "POST",
      body: JSON.stringify({ profileId: profile.id, params: collectParams(profile) }),
    });
    state.selectedRun = run.id;
    $("commandPreview").textContent = run.command;
    await loadState();
    await loadRun(run.id);
  } catch (error) {
    $("commandPreview").textContent = error.message;
  }
}

function renderRuns() {
  const runs = state.data.runs || [];
  if (runs.length === 0) {
    $("runs").innerHTML = `<div class="run-row"><span>No runs yet</span></div>`;
    $("logTail").textContent = "";
    return;
  }
  $("runs").innerHTML = runs.map(renderRunRow).join("");
  for (const row of $("runs").querySelectorAll("[data-run-id]")) {
    row.addEventListener("click", () => loadRun(row.dataset.runId));
  }
}

function renderRunRow(run) {
  const badgeClass = run.status === "failed" ? "failed" : run.status === "running" ? "training" : "";
  return `
    <button class="run-row" type="button" data-run-id="${escapeAttr(run.id)}">
      <span class="run-main">
        <strong>${escapeHtml(run.title)}</strong>
        <span class="badge ${badgeClass}">${escapeHtml(run.status)}</span>
      </span>
      <span class="run-command">${escapeHtml(run.command)}</span>
    </button>
  `;
}

async function loadRun(runId) {
  const run = await api(`/api/runs/${runId}`);
  state.selectedRun = run.id;
  const stderr = run.stderrTail ? `\n\n[stderr]\n${run.stderrTail}` : "";
  $("logTail").textContent = `${run.stdoutTail || ""}${stderr}` || "No output yet";
}

function renderSettings() {
  $("accentInput").value = state.settings.accent;
  $("densityInput").value = state.settings.density;
  $("researchInput").checked = state.settings.showResearch;
}

async function saveSettings() {
  state.settings.accent = $("accentInput").value;
  state.settings.density = $("densityInput").value;
  state.settings.showResearch = $("researchInput").checked;
  localStorage.setItem("winros-dashboard", JSON.stringify(state.settings));
  await api("/api/config", {
    method: "POST",
    body: JSON.stringify({
      theme: { accent: state.settings.accent, density: state.settings.density },
      preferences: { show_research_runs: state.settings.showResearch },
    }),
  });
  mergeSettings();
  $("settingsDialog").close();
  render();
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}

function cssEscape(value) {
  if (window.CSS?.escape) return CSS.escape(value);
  return value.replaceAll('"', '\\"');
}

$("refreshBtn").addEventListener("click", loadState);
$("pollBtn").addEventListener("click", async () => {
  await loadState();
  if (state.selectedRun) await loadRun(state.selectedRun);
});
$("settingsBtn").addEventListener("click", () => $("settingsDialog").showModal());
$("saveSettingsBtn").addEventListener("click", saveSettings);

loadState().catch((error) => {
  $("commandPreview").textContent = error.message;
});
