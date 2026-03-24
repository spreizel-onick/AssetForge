/* AssetForge v3.3 — Frontend Logic */

const API = "";
let generators = {};
let presets = {};
let favorites = [];
let outputOpen = false;
let currentPreviewFile = null;

// ── Init ───────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
  // Load theme from localStorage
  if (localStorage.getItem("af-theme") === "light") {
    document.body.classList.add("light");
    document.getElementById("btn-theme").textContent = "Dark";
  }

  await Promise.all([loadGenerators(), loadPresets(), loadSettings(), loadFavorites(), loadStats(), loadRecent()]);
  updateFooter();

  document.getElementById("btn-output").addEventListener("click", toggleOutput);
  document.getElementById("btn-zip").addEventListener("click", downloadZip);
  document.getElementById("close-output").addEventListener("click", toggleOutput);
  document.getElementById("btn-clear-output").addEventListener("click", clearOutput);

  // Theme toggle
  document.getElementById("btn-theme").addEventListener("click", toggleTheme);

  // Settings modal
  document.getElementById("btn-settings").addEventListener("click", openSettings);
  document.getElementById("settings-cancel").addEventListener("click", closeSettings);
  document.getElementById("settings-save").addEventListener("click", saveSettings);
  document.getElementById("settings-reset").addEventListener("click", resetSettings);

  // Preview modal
  document.getElementById("preview-close").addEventListener("click", closePreview);
  document.getElementById("preview-copy").addEventListener("click", copyPreview);
  document.getElementById("preview-download").addEventListener("click", downloadPreview);
  document.getElementById("preview-modal").addEventListener("click", (e) => {
    if (e.target === e.currentTarget) closePreview();
  });

  // History modal
  document.getElementById("btn-history").addEventListener("click", openHistory);
  document.getElementById("history-close").addEventListener("click", closeHistory);
  document.getElementById("history-clear").addEventListener("click", clearHistory);
  document.getElementById("history-modal").addEventListener("click", (e) => {
    if (e.target === e.currentTarget) closeHistory();
  });

  // Bundle modal
  document.getElementById("btn-bundle").addEventListener("click", openBundle);
  document.getElementById("bundle-close").addEventListener("click", closeBundle);
  document.getElementById("bundle-run").addEventListener("click", runBundle);
  document.getElementById("bundle-modal").addEventListener("click", (e) => {
    if (e.target === e.currentTarget) closeBundle();
  });

  // Sidebar search
  document.getElementById("sidebar-search").addEventListener("input", filterSidebar);

  // Toggle all categories
  document.getElementById("btn-toggle-cats").addEventListener("click", toggleAllCategories);

  // Export/Import Favorites
  document.getElementById("btn-export-favs").addEventListener("click", exportFavorites);
  document.getElementById("btn-import-favs").addEventListener("click", () => document.getElementById("import-favs-file").click());
  document.getElementById("import-favs-file").addEventListener("change", importFavorites);

  // Quick Launcher
  document.getElementById("launcher-input").addEventListener("input", filterLauncher);
  document.getElementById("launcher-modal").addEventListener("click", (e) => {
    if (e.target === e.currentTarget) closeLauncher();
  });

  // Keyboard shortcuts
  document.addEventListener("keydown", handleShortcuts);

  // Mobile hamburger menu
  document.getElementById("hamburger").addEventListener("click", toggleMobileSidebar);
  document.getElementById("sidebar-overlay").addEventListener("click", closeMobileSidebar);
});

// ── Keyboard Shortcuts ────────────────────────────────
function handleShortcuts(e) {
  // Ignore if typing in an input
  if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.tagName === "SELECT") {
    if (e.key === "Escape") e.target.blur();
    return;
  }

  if (e.key === "Escape") {
    closePreview();
    closeHistory();
    closeBundle();
    closeSettings();
    closeLauncher();
    if (outputOpen) toggleOutput();
    return;
  }

  if (e.ctrlKey || e.metaKey) {
    if (e.key === "g" || e.key === "G") {
      e.preventDefault();
      const btn = document.getElementById("btn-generate");
      if (btn) btn.click();
    } else if (e.key === "h" || e.key === "H") {
      e.preventDefault();
      openHistory();
    } else if (e.key === "b" || e.key === "B") {
      e.preventDefault();
      openBundle();
    } else if (e.key === "k" || e.key === "K") {
      e.preventDefault();
      openLauncher();
    }
  }
}

// ── Theme ──────────────────────────────────────────────
function toggleTheme() {
  document.body.classList.toggle("light");
  const isLight = document.body.classList.contains("light");
  localStorage.setItem("af-theme", isLight ? "light" : "dark");
  document.getElementById("btn-theme").textContent = isLight ? "Dark" : "Light";
}

// ── Load Data ──────────────────────────────────────────
async function loadGenerators() {
  try {
    const res = await fetch(`${API}/api/generators`);
    generators = await res.json();
    renderSidebar();
  } catch (e) {
    console.error("Failed to load generators:", e);
  }
}

async function loadPresets() {
  try {
    const res = await fetch(`${API}/api/presets`);
    presets = await res.json();
    renderPresets();
  } catch (e) {
    console.error("Failed to load presets:", e);
  }
}

async function loadSettings() {
  try {
    const res = await fetch(`${API}/api/settings`);
    const data = await res.json();
    document.getElementById("settings-output-dir").value = data.output_dir;
  } catch (e) {
    console.error("Failed to load settings:", e);
  }
}

async function loadFavorites() {
  try {
    const res = await fetch(`${API}/api/favorites`);
    favorites = await res.json();
    renderFavorites();
  } catch (e) {
    console.error("Failed to load favorites:", e);
  }
}

async function loadStats() {
  try {
    const res = await fetch(`${API}/api/stats`);
    const stats = await res.json();
    const bar = document.getElementById("stats-bar");
    if (!bar) return;
    bar.innerHTML = `
      <div class="stat-item">
        <div class="stat-value" data-count="${stats.file_count}">0</div>
        <div class="stat-label">Dateien</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">${formatSize(stats.total_size)}</div>
        <div class="stat-label">Gesamt</div>
      </div>
      <div class="stat-item">
        <div class="stat-value" data-count="${stats.history_count}">0</div>
        <div class="stat-label">Generierungen</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">${stats.last_generation ? new Date(stats.last_generation).toLocaleDateString("de-DE") : "—"}</div>
        <div class="stat-label">Letzte</div>
      </div>
    `;
    // Animate counters
    bar.querySelectorAll("[data-count]").forEach(el => {
      const target = parseInt(el.dataset.count);
      if (target === 0) return;
      let current = 0;
      const step = Math.max(1, Math.ceil(target / 20));
      const interval = setInterval(() => {
        current = Math.min(current + step, target);
        el.textContent = current;
        if (current >= target) clearInterval(interval);
      }, 30);
    });
    renderWelcomeGrid();
  } catch (e) {
    console.error("Failed to load stats:", e);
  }
}

function renderWelcomeGrid() {
  const grid = document.getElementById("welcome-grid");
  if (!grid) return;

  const categoryIcons = {
    "Konfiguration": "&#9881;",
    "Dokumentation": "&#128196;",
    "Datenbank": "&#128451;",
    "Visuell": "&#127912;",
    "Sicherheit": "&#128274;",
    "Code": "&#128187;",
  };

  // Preset card
  const presetCount = Object.keys(presets).length;
  let html = `<div class="welcome-card" onclick="document.querySelector('.preset-btn')?.click()">
    <div class="welcome-icon">&#9889;</div>
    <h3>Presets <span class="welcome-count">${presetCount}</span></h3>
    <p>Komplettes Projekt-Setup mit einem Klick</p>
  </div>`;

  // Category cards
  for (const [cat, gens] of Object.entries(generators)) {
    const icon = categoryIcons[cat] || "&#128230;";
    const names = gens.slice(0, 4).map(g => g.name).join(", ");
    const more = gens.length > 4 ? ` +${gens.length - 4}` : "";
    html += `<div class="welcome-card" data-category="${escapeHtml(cat)}" onclick="scrollToCategory('${escapeHtml(cat)}')">
      <div class="welcome-icon">${icon}</div>
      <h3>${escapeHtml(cat)} <span class="welcome-count">${gens.length}</span></h3>
      <p>${escapeHtml(names)}${more}</p>
    </div>`;
  }

  grid.innerHTML = html;
}

function scrollToCategory(catName) {
  // Expand the category if collapsed
  document.querySelectorAll("#gen-nav .category").forEach(cat => {
    const label = cat.querySelector(".category-label");
    if (label && label.textContent.toUpperCase().includes(catName.toUpperCase())) {
      const items = cat.querySelector(".category-items");
      const arrow = cat.querySelector(".cat-arrow");
      if (items && items.classList.contains("hidden")) {
        items.classList.remove("hidden");
        if (arrow) arrow.classList.remove("collapsed");
      }
      // Click the first generator
      const firstBtn = cat.querySelector(".gen-btn");
      if (firstBtn) firstBtn.click();
    }
  });
}

// ── Sidebar Search ────────────────────────────────────
function highlightText(text, query) {
  if (!query) return escapeHtml(text);
  const escaped = escapeHtml(text);
  const idx = escaped.toLowerCase().indexOf(query.toLowerCase());
  if (idx === -1) return escaped;
  return escaped.slice(0, idx) + '<mark class="search-hl">' + escaped.slice(idx, idx + query.length) + '</mark>' + escaped.slice(idx + query.length);
}

function filterSidebar() {
  const q = document.getElementById("sidebar-search").value.toLowerCase().trim();
  document.querySelectorAll("#gen-nav .category").forEach(cat => {
    let anyVisible = false;
    const items = cat.querySelector(".category-items");
    if (q && items) items.classList.remove("hidden");
    cat.querySelectorAll(".gen-btn").forEach(btn => {
      const name = btn.dataset.genName || btn.textContent;
      const match = name.toLowerCase().includes(q) || btn.title.toLowerCase().includes(q);
      btn.style.display = match ? "" : "none";
      // Highlight matching text
      if (q && match) {
        btn.innerHTML = highlightText(name, q);
      } else {
        btn.textContent = name;
      }
      if (match) anyVisible = true;
    });
    cat.style.display = (anyVisible || !q) ? "" : "none";
    if (!q && items) {
      const collapsed = JSON.parse(localStorage.getItem("af-collapsed") || "{}");
      const catName = cat.querySelector(".category-label")?.textContent?.trim();
      for (const [key, val] of Object.entries(collapsed)) {
        if (val && catName && catName.includes(key)) items.classList.add("hidden");
      }
    }
  });
  document.querySelectorAll("#preset-nav .preset-btn").forEach(btn => {
    const name = btn.dataset.presetLabel || btn.textContent;
    const match = name.toLowerCase().includes(q) || btn.title.toLowerCase().includes(q);
    btn.style.display = match ? "" : "none";
    if (q && match) {
      btn.innerHTML = highlightText(name, q);
    } else {
      btn.textContent = name;
    }
  });
  document.querySelectorAll("#fav-nav .fav-btn").forEach(btn => {
    const match = btn.textContent.toLowerCase().includes(q);
    btn.style.display = match ? "" : "none";
  });
}

// ── Sidebar ────────────────────────────────────────────
function renderFavorites() {
  const nav = document.getElementById("fav-nav");
  nav.innerHTML = "";
  if (favorites.length === 0) {
    nav.innerHTML = '<div class="sidebar-empty">Keine Favoriten</div>';
    return;
  }
  favorites.forEach((fav, idx) => {
    const btn = document.createElement("button");
    btn.className = "fav-btn";
    btn.innerHTML = `<span class="fav-name">${escapeHtml(fav.name)}</span><span class="fav-remove" data-idx="${idx}" title="Entfernen">&times;</span>`;
    btn.addEventListener("click", (e) => {
      if (e.target.classList.contains("fav-remove")) {
        removeFavorite(idx);
        return;
      }
      clearActive();
      btn.classList.add("active");
      applyFavorite(fav);
    });
    nav.appendChild(btn);
  });
}

function renderPresets() {
  const nav = document.getElementById("preset-nav");
  nav.innerHTML = "";
  for (const [key, preset] of Object.entries(presets)) {
    const btn = document.createElement("button");
    btn.className = "preset-btn";
    btn.textContent = preset.label;
    btn.dataset.presetLabel = preset.label;
    btn.title = preset.description;
    btn.addEventListener("click", () => selectPreset(key, preset, btn));
    nav.appendChild(btn);
  }
}

function renderSidebar() {
  const nav = document.getElementById("gen-nav");
  nav.innerHTML = "";
  const collapsed = JSON.parse(localStorage.getItem("af-collapsed") || "{}");
  for (const [category, gens] of Object.entries(generators)) {
    const cat = document.createElement("div");
    cat.className = "category";
    const isCollapsed = collapsed[category] === true;
    const label = document.createElement("div");
    label.className = "category-label category-toggle";
    label.innerHTML = `<span class="cat-arrow ${isCollapsed ? "collapsed" : ""}">\u25BE</span> ${escapeHtml(category)} <span class="cat-badge">${gens.length}</span>`;
    label.addEventListener("click", () => {
      const items = cat.querySelector(".category-items");
      const arrow = label.querySelector(".cat-arrow");
      items.classList.toggle("hidden");
      arrow.classList.toggle("collapsed");
      const c = JSON.parse(localStorage.getItem("af-collapsed") || "{}");
      c[category] = items.classList.contains("hidden");
      localStorage.setItem("af-collapsed", JSON.stringify(c));
    });
    cat.appendChild(label);
    const items = document.createElement("div");
    items.className = "category-items" + (isCollapsed ? " hidden" : "");
    for (const gen of gens) {
      const btn = document.createElement("button");
      btn.className = "gen-btn";
      btn.textContent = gen.name;
      btn.dataset.genName = gen.name;
      btn.title = gen.description;
      btn.addEventListener("click", () => selectGenerator(gen, btn));
      items.appendChild(btn);
    }
    cat.appendChild(items);
    nav.appendChild(cat);
  }
  // Update total count
  const total = Object.values(generators).reduce((s, g) => s + g.length, 0);
  const genTotal = document.getElementById("gen-total");
  if (genTotal) genTotal.textContent = `(${total})`;
}

// ── Mobile Sidebar ────────────────────────────────────
function toggleMobileSidebar() {
  document.getElementById("sidebar").classList.toggle("mobile-open");
  document.getElementById("sidebar-overlay").classList.toggle("active");
}

function closeMobileSidebar() {
  document.getElementById("sidebar").classList.remove("mobile-open");
  document.getElementById("sidebar-overlay").classList.remove("active");
}

function toggleAllCategories() {
  const allItems = document.querySelectorAll("#gen-nav .category-items");
  const allArrows = document.querySelectorAll("#gen-nav .cat-arrow");
  const anyVisible = [...allItems].some(el => !el.classList.contains("hidden"));
  const collapsed = {};

  allItems.forEach(el => {
    if (anyVisible) el.classList.add("hidden");
    else el.classList.remove("hidden");
  });
  allArrows.forEach(a => {
    if (anyVisible) a.classList.add("collapsed");
    else a.classList.remove("collapsed");
  });

  // Save state
  document.querySelectorAll("#gen-nav .category-label").forEach(label => {
    const catText = label.textContent.replace(/[▾\d]/g, "").trim();
    for (const [cat] of Object.entries(generators)) {
      if (catText.toUpperCase().includes(cat.toUpperCase())) {
        collapsed[cat] = anyVisible;
      }
    }
  });
  localStorage.setItem("af-collapsed", JSON.stringify(collapsed));

  const btn = document.getElementById("btn-toggle-cats");
  btn.textContent = anyVisible ? "Alle ▸" : "Alle ▾";
}

function clearActive() {
  document.querySelectorAll(".gen-btn, .preset-btn, .fav-btn").forEach(b => b.classList.remove("active"));
}

function selectGenerator(gen, btn) {
  clearActive();
  btn.classList.add("active");
  btn.scrollIntoView({ behavior: "smooth", block: "nearest" });
  renderForm(gen);
  closeMobileSidebar();
}

function selectPreset(key, preset, btn) {
  clearActive();
  btn.classList.add("active");
  renderPresetForm(key, preset);
  closeMobileSidebar();
}

// ── Generator Form ─────────────────────────────────────
function renderForm(gen) {
  const main = document.getElementById("main-content");
  main.innerHTML = "";

  const panel = document.createElement("div");
  panel.className = "form-panel";
  // Find category for breadcrumb
  let genCategory = "";
  for (const [cat, gens] of Object.entries(generators)) {
    if (gens.find(g => g.name === gen.name)) { genCategory = cat; break; }
  }
  panel.innerHTML = `
    <div class="breadcrumb">
      <a onclick="showWelcome()">Home</a>
      <span class="sep">/</span>
      <span>${escapeHtml(genCategory)}</span>
      <span class="sep">/</span>
      <span class="current">${escapeHtml(gen.name)}</span>
    </div>
    <h2>${escapeHtml(gen.name)}</h2>
    <p class="desc">${escapeHtml(gen.description)}</p>
    <form id="gen-form"></form>
    <div class="form-actions">
      <button type="button" class="btn btn-primary" id="btn-generate">Generieren</button>
      <button type="button" class="btn" id="btn-reset-form" title="Formular zurücksetzen">Reset</button>
      <button type="button" class="btn" id="btn-save-fav" title="Als Favorit speichern">Favorit speichern</button>
    </div>
    <div id="result-area"></div>
  `;
  main.appendChild(panel);

  const form = document.getElementById("gen-form");
  for (const param of gen.parameters) {
    form.appendChild(createField(param));
  }

  // Restore last used params from localStorage
  restoreFormParams(gen.name, form);

  document.getElementById("btn-generate").addEventListener("click", async () => {
    if (!validateForm(gen.parameters)) return;
    // Save params for next time
    saveFormParams(gen.name, form);
    // Check for existing files
    const proceed = await checkOverwrite(gen.name);
    if (proceed) runGenerator(gen.name);
  });

  document.getElementById("btn-save-fav").addEventListener("click", () => {
    const params = collectFormData(form);
    saveFavorite(gen.name, "generator", params);
  });

  document.getElementById("btn-reset-form").addEventListener("click", () => {
    form.querySelectorAll("input, select, textarea").forEach(el => {
      if (el.type === "checkbox") el.checked = false;
      else if (el.type === "color") el.value = el.defaultValue || "#e94560";
      else el.value = el.defaultValue || "";
    });
    form.querySelectorAll(".field.invalid").forEach(f => {
      f.classList.remove("invalid");
      const err = f.querySelector(".error-msg");
      if (err) err.remove();
    });
    document.getElementById("result-area").innerHTML = "";
  });
}

function createField(param) {
  const field = document.createElement("div");
  field.className = "field";
  field.dataset.name = param.name;

  const reqMark = param.required ? ' <span class="req">*</span>' : "";
  const label = `<label>${escapeHtml(param.description || param.name)}${reqMark}</label>`;

  if (param.type === "text") {
    field.innerHTML = `${label}<input type="text" name="${param.name}" value="${param.default || ""}" placeholder="${escapeHtml(param.description || "")}">`;
  } else if (param.type === "number") {
    field.innerHTML = `${label}<input type="number" name="${param.name}" value="${param.default || ""}">`;
  } else if (param.type === "color") {
    field.innerHTML = `${label}<div class="field-row"><input type="color" name="${param.name}" value="${param.default || "#e94560"}"><input type="text" name="${param.name}_hex" value="${param.default || "#e94560"}" style="width:120px"></div>`;
    setTimeout(() => {
      const colorInput = field.querySelector('input[type="color"]');
      const textInput = field.querySelector('input[type="text"]');
      if (colorInput && textInput) {
        colorInput.addEventListener("input", () => { textInput.value = colorInput.value; });
        textInput.addEventListener("input", () => { colorInput.value = textInput.value; });
      }
    }, 0);
  } else if (param.type === "select") {
    const opts = (param.options || []).map(o => `<option value="${o}">${o}</option>`).join("");
    field.innerHTML = `${label}<select name="${param.name}">${opts}</select>`;
  } else if (param.type === "multi-select") {
    const checks = (param.options || []).map(o =>
      `<label><input type="checkbox" name="${param.name}" value="${o}"> ${o}</label>`
    ).join("");
    field.innerHTML = `${label}<div class="multi-select">${checks}</div>`;
  } else if (param.type === "boolean") {
    field.innerHTML = `<div class="checkbox-row"><input type="checkbox" name="${param.name}" id="cb-${param.name}"><label for="cb-${param.name}">${escapeHtml(param.description || param.name)}</label></div>`;
  } else if (param.type === "json") {
    field.innerHTML = `${label}<textarea name="${param.name}" placeholder='${escapeHtml(param.description || "JSON eingeben")}'>${param.default || ""}</textarea>`;
  } else {
    field.innerHTML = `${label}<input type="text" name="${param.name}" value="${param.default || ""}">`;
  }

  // Real-time validation on required fields
  if (param.required) {
    setTimeout(() => {
      const input = field.querySelector(`[name="${param.name}"]`);
      if (input && input.type !== "checkbox") {
        input.addEventListener("input", () => {
          if (input.value.trim()) {
            field.classList.remove("invalid");
            const err = field.querySelector(".error-msg");
            if (err) err.remove();
          }
        });
      }
    }, 0);
  }

  return field;
}

// ── Validation ─────────────────────────────────────────
function validateForm(parameters) {
  let valid = true;
  document.querySelectorAll(".field.invalid").forEach(f => {
    f.classList.remove("invalid");
    const err = f.querySelector(".error-msg");
    if (err) err.remove();
  });

  for (const param of parameters) {
    if (!param.required) continue;
    const field = document.querySelector(`.field[data-name="${param.name}"]`);
    if (!field) continue;

    let value;
    if (param.type === "multi-select") {
      const checked = field.querySelectorAll('input[type="checkbox"]:checked');
      value = checked.length > 0;
    } else {
      const input = field.querySelector(`[name="${param.name}"]`);
      value = input && input.value && input.value.trim();
    }

    if (!value) {
      field.classList.add("invalid");
      const msg = document.createElement("div");
      msg.className = "error-msg";
      msg.textContent = "Pflichtfeld";
      field.appendChild(msg);
      valid = false;
    }
  }

  if (!valid) {
    const firstInvalid = document.querySelector(".field.invalid");
    if (firstInvalid) firstInvalid.scrollIntoView({ behavior: "smooth", block: "center" });
  }
  return valid;
}

// ── Preset Form ────────────────────────────────────────
function renderPresetForm(key, preset) {
  const main = document.getElementById("main-content");
  main.innerHTML = `
    <div class="form-panel">
      <div class="breadcrumb">
        <a onclick="showWelcome()">Home</a>
        <span class="sep">/</span>
        <span>Presets</span>
        <span class="sep">/</span>
        <span class="current">${escapeHtml(preset.label)}</span>
      </div>
      <h2>${escapeHtml(preset.label)}</h2>
      <p class="desc">${escapeHtml(preset.description)}</p>
      <form id="gen-form">
        <div class="field" data-name="project_name">
          <label>Projektname <span class="req">*</span></label>
          <input type="text" name="project_name" placeholder="Mein Projekt">
        </div>
        <div class="field" data-name="author">
          <label>Autor</label>
          <input type="text" name="author" placeholder="Dein Name">
        </div>
        <div class="field" data-name="description">
          <label>Beschreibung</label>
          <input type="text" name="description" placeholder="Kurzbeschreibung des Projekts">
        </div>
      </form>
      <div class="form-actions">
        <button type="button" class="btn btn-primary" id="btn-generate">Preset ausführen</button>
      </div>
      <div id="result-area"></div>
    </div>
  `;

  const nameInput = document.querySelector('input[name="project_name"]');
  nameInput.addEventListener("input", () => {
    const field = document.querySelector('.field[data-name="project_name"]');
    if (nameInput.value.trim()) {
      field.classList.remove("invalid");
      const err = field.querySelector(".error-msg");
      if (err) err.remove();
    }
  });

  document.getElementById("btn-generate").addEventListener("click", () => {
    if (!nameInput.value.trim()) {
      const field = document.querySelector('.field[data-name="project_name"]');
      field.classList.add("invalid");
      let err = field.querySelector(".error-msg");
      if (!err) { err = document.createElement("div"); err.className = "error-msg"; field.appendChild(err); }
      err.textContent = "Pflichtfeld";
      return;
    }
    runPreset(key);
  });
}

// ── Run Generator ──────────────────────────────────────
async function runGenerator(name) {
  const form = document.getElementById("gen-form");
  const resultArea = document.getElementById("result-area");
  const btn = document.getElementById("btn-generate");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Generiere...';
  resultArea.innerHTML = "";

  const params = collectFormData(form);

  try {
    const res = await fetch(`${API}/api/generate/${name}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    const data = await res.json();

    if (res.ok) {
      const fileItems = (data.files || []).map(f => {
        const fname = f.replace(/\\/g, "/").split("/").pop();
        return `<li>
          <a onclick="openPreview('${encodeURIComponent(fname)}')">${escapeHtml(fname)}</a>
          <span class="file-actions">
            <button class="btn btn-sm" onclick="copyFile('${encodeURIComponent(fname)}')" title="Kopieren">Kopieren</button>
          </span>
        </li>`;
      }).join("");

      resultArea.innerHTML = `
        <div class="result result-animate">
          <h4><span class="success-check">&#10003;</span> ${escapeHtml(data.message || "Erfolgreich generiert!")}</h4>
          <ul class="files">${fileItems}</ul>
        </div>`;
      resultArea.scrollIntoView({ behavior: "smooth", block: "nearest" });
      loadStats(); loadRecent();
    } else {
      resultArea.innerHTML = `<div class="result error"><h4>Fehler</h4><p>${escapeHtml(data.detail || "Unbekannter Fehler")}</p></div>`;
    }
  } catch (e) {
    resultArea.innerHTML = `<div class="result error"><h4>Fehler</h4><p>${escapeHtml(e.message)}</p></div>`;
  }

  btn.disabled = false;
  btn.textContent = "Generieren";
}

// ── Run Preset ─────────────────────────────────────────
async function runPreset(key) {
  const form = document.getElementById("gen-form");
  const resultArea = document.getElementById("result-area");
  const btn = document.getElementById("btn-generate");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Generiere...';
  resultArea.innerHTML = "";

  const params = collectFormData(form);

  try {
    const res = await fetch(`${API}/api/presets/${key}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    const data = await res.json();

    if (res.ok) {
      const items = (data.results || []).map(r => {
        const cls = r.status === "ok" ? "ok" : "err";
        const msg = r.message || r.status;
        return `<div class="preset-result-item ${cls}"><span><span class="status-dot"></span>${escapeHtml(r.name)}</span><span>${escapeHtml(msg)}</span></div>`;
      }).join("");

      resultArea.innerHTML = `
        <div class="result">
          <h4>${escapeHtml(data.label)} — ${data.total_files} Dateien generiert</h4>
          <div class="preset-results">${items}</div>
        </div>`;
      loadStats(); loadRecent();
    } else {
      resultArea.innerHTML = `<div class="result error"><h4>Fehler</h4><p>${escapeHtml(data.detail || "Unbekannter Fehler")}</p></div>`;
    }
  } catch (e) {
    resultArea.innerHTML = `<div class="result error"><h4>Fehler</h4><p>${escapeHtml(e.message)}</p></div>`;
  }

  btn.disabled = false;
  btn.textContent = "Preset ausführen";
}

// ── Parameter Persistence ─────────────────────────────
function saveFormParams(genName, form) {
  try {
    const data = collectFormData(form);
    const saved = JSON.parse(localStorage.getItem("af-params") || "{}");
    saved[genName] = data;
    localStorage.setItem("af-params", JSON.stringify(saved));
  } catch (e) { /* ignore */ }
}

function restoreFormParams(genName, form) {
  try {
    const saved = JSON.parse(localStorage.getItem("af-params") || "{}");
    const data = saved[genName];
    if (!data) return;

    for (const [key, val] of Object.entries(data)) {
      if (Array.isArray(val)) {
        // Multi-select checkboxes
        form.querySelectorAll(`input[name="${key}"]`).forEach(cb => {
          if (cb.type === "checkbox") cb.checked = val.includes(cb.value);
        });
      } else if (typeof val === "boolean") {
        const cb = form.querySelector(`input[name="${key}"][type="checkbox"]`);
        if (cb) cb.checked = val;
      } else {
        const el = form.querySelector(`[name="${key}"]`);
        if (el) {
          el.value = val;
          // Sync color hex input
          if (el.type === "color") {
            const hex = form.querySelector(`[name="${key}_hex"]`);
            if (hex) hex.value = val;
          }
        }
      }
    }
  } catch (e) { /* ignore */ }
}

function collectFormData(form) {
  const data = {};
  const inputs = form.querySelectorAll("input, select, textarea");

  for (const input of inputs) {
    const name = input.name;
    if (!name || name.endsWith("_hex")) continue;

    if (input.type === "checkbox" && input.closest(".multi-select")) {
      if (!data[name]) data[name] = [];
      if (input.checked) data[name].push(input.value);
    } else if (input.type === "checkbox") {
      data[name] = input.checked;
    } else if (input.type === "number") {
      data[name] = input.value ? Number(input.value) : undefined;
    } else if (input.tagName === "TEXTAREA") {
      try { data[name] = JSON.parse(input.value); }
      catch { data[name] = input.value; }
    } else {
      if (input.value) data[name] = input.value;
    }
  }
  return data;
}

// ── Preview ────────────────────────────────────────────
async function openPreview(encodedName) {
  const name = decodeURIComponent(encodedName);
  currentPreviewFile = name;

  try {
    const res = await fetch(`${API}/api/preview/${encodeURIComponent(name)}`);
    const data = await res.json();

    document.getElementById("preview-title").textContent = data.name;
    const content = document.getElementById("preview-content");
    const copyBtn = document.getElementById("preview-copy");

    if (data.type === "text") {
      content.innerHTML = `<pre>${addLineNumbers(escapeHtml(data.content))}</pre>`;
      copyBtn.style.display = "";
    } else if (data.type === "image") {
      content.innerHTML = `<img src="data:${data.mime};base64,${data.data}" alt="${escapeHtml(data.name)}">`;
      copyBtn.style.display = "none";
    } else {
      content.innerHTML = `<p>Binärdatei (${formatSize(data.size)})</p>`;
      copyBtn.style.display = "none";
    }

    document.getElementById("preview-modal").classList.add("open");
  } catch (e) {
    showToast("Vorschau konnte nicht geladen werden", "error");
  }
}

function addLineNumbers(html) {
  const lines = html.split("\n");
  const digits = String(lines.length).length;
  return lines.map((line, i) => {
    const num = String(i + 1).padStart(digits, " ");
    return `<span class="line-num">${num}</span>${line}`;
  }).join("\n");
}

function closePreview() {
  document.getElementById("preview-modal").classList.remove("open");
  currentPreviewFile = null;
}

async function copyPreview() {
  const pre = document.querySelector("#preview-content pre");
  if (pre) {
    const text = pre.textContent.replace(/^\s*\d+\s*/gm, "");
    await navigator.clipboard.writeText(text);
    showToast("In Zwischenablage kopiert!");
  }
}

function downloadPreview() {
  if (currentPreviewFile) {
    window.open(`${API}/api/output/${encodeURIComponent(currentPreviewFile)}`, "_blank");
  }
}

async function copyFile(encodedName) {
  const name = decodeURIComponent(encodedName);
  try {
    const res = await fetch(`${API}/api/preview/${encodeURIComponent(name)}`);
    const data = await res.json();
    if (data.type === "text") {
      await navigator.clipboard.writeText(data.content);
      showToast("Kopiert!");
    } else {
      showToast("Nur Textdateien können kopiert werden");
    }
  } catch (e) {
    showToast("Fehler beim Kopieren", "error");
  }
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function showWelcome() {
  clearActive();
  location.reload();
}

async function checkOverwrite(generatorName) {
  try {
    const res = await fetch(`${API}/api/output`);
    const data = await res.json();
    if (data.files.length === 0) return true;
    // Simple heuristic: check known output filenames for common generators
    const existingNames = data.files.map(f => f.name);
    const knownOutputs = {
      "gitignore": [".gitignore"], "dockerfile": ["Dockerfile"], "compose": ["docker-compose.yml"],
      "env": [".env"], "readme": ["README.md"], "license": ["LICENSE"], "changelog": ["CHANGELOG.md"],
      "robots-txt": ["robots.txt"], "htaccess": [".htaccess"], "nginx-conf": ["nginx.conf"],
      "prettierrc": [".prettierrc", ".prettierignore"], "editorconfig": [".editorconfig"],
      "eslintrc": ["eslint.config.js"], "tsconfig": ["tsconfig.json"], "makefile": ["Makefile"],
      "logo": ["logo.png"], "og-image": ["og-image.png"], "dockerignore": [".dockerignore"],
      "tailwind-config": ["tailwind.config.js"], "vite-config": ["vite.config.ts"],
      "jest-config": ["jest.config.js"], "vitest-config": ["vitest.config.ts"],
      "pwa-manifest": ["manifest.json"], "openapi-spec": ["openapi.yaml"],
      "security-txt": ["security.txt"], "env-validator": [".env.example"],
      "stylelint-config": [".stylelintrc.json", ".stylelintignore"],
      "babel-config": ["babel.config.json"], "webpack-config": ["webpack.config.js"],
      "gitattributes": [".gitattributes"],
    };
    const outputs = knownOutputs[generatorName] || [];
    const conflicts = outputs.filter(f => existingNames.includes(f));
    if (conflicts.length > 0) {
      return confirm(`Folgende Dateien werden überschrieben:\n${conflicts.join(", ")}\n\nFortfahren?`);
    }
  } catch (e) { /* ignore */ }
  return true;
}

function updateFooter() {
  const footer = document.getElementById("app-footer");
  if (!footer) return;
  const genCount = Object.values(generators).reduce((sum, g) => sum + g.length, 0);
  const presetCount = Object.keys(presets).length;
  const catCount = Object.keys(generators).length;
  footer.innerHTML = `<span>AssetForge</span> v3.3 by Onick — ${genCount} Generatoren · ${presetCount} Presets · ${catCount} Kategorien`;
}

// ── History ────────────────────────────────────────────
async function openHistory() {
  const content = document.getElementById("history-content");
  content.innerHTML = '<div style="text-align:center;padding:2rem"><span class="spinner"></span></div>';
  document.getElementById("history-modal").classList.add("open");

  try {
    const res = await fetch(`${API}/api/history`);
    const history = await res.json();

    if (history.length === 0) {
      content.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:2rem">Noch keine Generierungen</p>';
      return;
    }

    content.innerHTML = history.map((entry, idx) => {
      const time = new Date(entry.timestamp).toLocaleString("de-DE");
      const typeLabel = entry.type === "preset" ? "Preset" : "Generator";
      const fileCount = (entry.files || []).length;
      return `
        <div class="history-item">
          <div class="history-info">
            <span class="history-badge ${entry.type}">${typeLabel}</span>
            <strong>${escapeHtml(entry.generator)}</strong>
            <span class="history-meta">${fileCount} Dateien &middot; ${time}</span>
          </div>
          <div class="history-actions">
            <button class="btn btn-sm" onclick="rerunHistory(${idx})" title="Nochmal ausführen">Wiederholen</button>
            <button class="btn btn-sm" onclick="undoHistory(${idx})" title="Dateien löschen" style="color:var(--accent)">Rückgängig</button>
          </div>
        </div>`;
    }).join("");
  } catch (e) {
    content.innerHTML = `<p style="color:var(--accent);padding:1rem">Fehler: ${escapeHtml(e.message)}</p>`;
  }
}

function closeHistory() {
  document.getElementById("history-modal").classList.remove("open");
}

async function clearHistory() {
  if (!confirm("Gesamte History wirklich löschen?")) return;
  try {
    await fetch(`${API}/api/history`, { method: "DELETE" });
    showToast("History gelöscht");
    loadRecent();
    openHistory();
  } catch (e) {
    showToast("Fehler beim Löschen", "error");
  }
}

async function undoHistory(index) {
  if (!confirm("Generierte Dateien wirklich löschen?")) return;
  try {
    const res = await fetch(`${API}/api/history/${index}/undo`, { method: "POST" });
    const data = await res.json();
    showToast(`${data.count} Dateien gelöscht`);
    loadStats();
    openHistory();
  } catch (e) {
    showToast("Fehler beim Rückgängigmachen", "error");
  }
}

async function rerunHistory(index) {
  try {
    const res = await fetch(`${API}/api/history`);
    const history = await res.json();
    const entry = history[index];
    if (!entry) return;
    closeHistory();

    if (entry.type === "preset") {
      const presetBtn = [...document.querySelectorAll(".preset-btn")].find(b => {
        const key = Object.keys(presets).find(k => presets[k].label === b.textContent);
        return key === entry.generator;
      });
      if (presetBtn) presetBtn.click();
    } else {
      for (const [, gens] of Object.entries(generators)) {
        const gen = gens.find(g => g.name === entry.generator);
        if (gen) {
          const btn = [...document.querySelectorAll(".gen-btn")].find(b => b.textContent === gen.name);
          if (btn) {
            selectGenerator(gen, btn);
            setTimeout(() => fillFormData(entry.params), 50);
          }
          break;
        }
      }
    }
  } catch (e) {
    showToast("Fehler beim Laden", "error");
  }
}

function fillFormData(params) {
  const form = document.getElementById("gen-form");
  if (!form) return;
  for (const [key, val] of Object.entries(params)) {
    const inputs = form.querySelectorAll(`[name="${key}"]`);
    for (const input of inputs) {
      if (input.type === "checkbox" && input.closest(".multi-select")) {
        input.checked = Array.isArray(val) && val.includes(input.value);
      } else if (input.type === "checkbox") {
        input.checked = !!val;
      } else if (input.tagName === "TEXTAREA") {
        input.value = typeof val === "object" ? JSON.stringify(val, null, 2) : val;
      } else {
        input.value = val;
      }
    }
  }
}

// ── Favorites ──────────────────────────────────────────
async function saveFavorite(generator, type, params) {
  const name = prompt("Name für den Favoriten:", generator);
  if (!name) return;

  try {
    await fetch(`${API}/api/favorites`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, generator, type, params }),
    });
    await loadFavorites();
    showToast("Favorit gespeichert!");
  } catch (e) {
    showToast("Fehler beim Speichern", "error");
  }
}

async function removeFavorite(index) {
  try {
    await fetch(`${API}/api/favorites/${index}`, { method: "DELETE" });
    await loadFavorites();
    showToast("Favorit entfernt");
  } catch (e) {
    showToast("Fehler", "error");
  }
}

function applyFavorite(fav) {
  if (fav.type === "preset") {
    const preset = presets[fav.generator];
    if (preset) {
      renderPresetForm(fav.generator, preset);
      setTimeout(() => fillFormData(fav.params), 50);
    }
  } else {
    for (const [, gens] of Object.entries(generators)) {
      const gen = gens.find(g => g.name === fav.generator);
      if (gen) {
        renderForm(gen);
        setTimeout(() => fillFormData(fav.params), 50);
        break;
      }
    }
  }
}

// ── Export/Import Favorites ────────────────────────────
async function exportFavorites() {
  try {
    const res = await fetch(`${API}/api/favorites`);
    const favs = await res.json();
    if (favs.length === 0) { showToast("Keine Favoriten vorhanden", "error"); return; }
    const blob = new Blob([JSON.stringify(favs, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "assetforge-favorites.json";
    a.click();
    URL.revokeObjectURL(url);
    showToast(`${favs.length} Favoriten exportiert`);
  } catch (e) {
    showToast("Export fehlgeschlagen", "error");
  }
}

async function importFavorites(e) {
  const file = e.target.files[0];
  if (!file) return;
  try {
    const text = await file.text();
    const imported = JSON.parse(text);
    if (!Array.isArray(imported)) throw new Error("Ungültiges Format");
    const res = await fetch(`${API}/api/favorites/import`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ favorites: imported }),
    });
    const result = await res.json();
    await loadFavorites();
    showToast(`${result.added} Favoriten importiert` + (result.skipped ? `, ${result.skipped} Duplikate übersprungen` : ""));
  } catch (err) {
    showToast("Import fehlgeschlagen: " + err.message, "error");
  }
  e.target.value = "";
}

// ── Bundle Builder ─────────────────────────────────────
function openBundle() {
  const list = document.getElementById("bundle-list");
  list.innerHTML = "";

  for (const [category, gens] of Object.entries(generators)) {
    const catDiv = document.createElement("div");
    catDiv.className = "bundle-category";
    catDiv.innerHTML = `<div class="bundle-category-label">${escapeHtml(category)}</div>`;

    for (const gen of gens) {
      const item = document.createElement("label");
      item.className = "bundle-item";
      item.innerHTML = `<input type="checkbox" value="${gen.name}"> <strong>${escapeHtml(gen.name)}</strong> <span class="bundle-desc">${escapeHtml(gen.description)}</span>`;
      item.querySelector("input").addEventListener("change", updateBundleCount);
      catDiv.appendChild(item);
    }
    list.appendChild(catDiv);
  }

  updateBundleCount();
  document.getElementById("bundle-result").innerHTML = "";
  document.getElementById("bundle-modal").classList.add("open");
}

function closeBundle() {
  document.getElementById("bundle-modal").classList.remove("open");
}

function updateBundleCount() {
  const count = document.querySelectorAll("#bundle-list input:checked").length;
  document.getElementById("bundle-count").textContent = `${count} ausgewählt`;
  document.getElementById("bundle-run").disabled = count === 0;

  // Toggle selected class
  document.querySelectorAll(".bundle-item").forEach(item => {
    item.classList.toggle("selected", item.querySelector("input").checked);
  });
}

async function runBundle() {
  const checked = document.querySelectorAll("#bundle-list input:checked");
  const names = [...checked].map(c => c.value);
  if (names.length === 0) return;

  const btn = document.getElementById("bundle-run");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Generiere...';

  const bundleGenerators = names.map(name => ({ name, params: {} }));

  try {
    const res = await fetch(`${API}/api/generate-bundle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ generators: bundleGenerators }),
    });
    const data = await res.json();

    const items = (data.results || []).map(r => {
      const cls = r.status === "ok" ? "ok" : "err";
      const msg = r.message || r.status;
      return `<div class="preset-result-item ${cls}"><span><span class="status-dot"></span>${escapeHtml(r.name)}</span><span>${escapeHtml(msg)}</span></div>`;
    }).join("");

    document.getElementById("bundle-result").innerHTML = `
      <div class="result" style="margin-top:1rem">
        <h4>${data.total_files} Dateien generiert</h4>
        <div class="preset-results">${items}</div>
      </div>`;
    loadStats();
  } catch (e) {
    document.getElementById("bundle-result").innerHTML = `<div class="result error" style="margin-top:1rem"><h4>Fehler</h4><p>${escapeHtml(e.message)}</p></div>`;
  }

  btn.disabled = false;
  btn.textContent = "Bundle generieren";
}

// ── Toast ──────────────────────────────────────────────
function showToast(msg, type = "success") {
  let toast = document.querySelector(".toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.remove("toast-error", "toast-success");
  toast.classList.add(type === "error" ? "toast-error" : "toast-success");
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2000);
}

// ── Output Panel ───────────────────────────────────────
async function toggleOutput() {
  const panel = document.getElementById("output-panel");
  outputOpen = !outputOpen;
  panel.classList.toggle("open", outputOpen);
  if (outputOpen) await loadOutput();
}

async function loadOutput() {
  try {
    const res = await fetch(`${API}/api/output`);
    const data = await res.json();
    const list = document.getElementById("output-list");
    const dirDisplay = document.getElementById("output-dir-display");

    dirDisplay.textContent = data.output_dir || "./output";

    if (data.files.length === 0) {
      list.innerHTML = '<li style="color:var(--text-muted);padding:1rem 0">Noch keine Dateien generiert</li>';
      return;
    }
    list.innerHTML = data.files.map(f => `
      <li>
        <a class="fname" onclick="openPreview('${encodeURIComponent(f.name)}')">${escapeHtml(f.name)}</a>
        <span class="fsize">${formatSize(f.size)}</span>
        <span class="file-delete" onclick="deleteOutputFile('${encodeURIComponent(f.name)}')" title="Löschen">&times;</span>
      </li>
    `).join("");
  } catch (e) {
    console.error("Failed to load output:", e);
  }
}

async function deleteOutputFile(encodedName) {
  const name = decodeURIComponent(encodedName);
  try {
    await fetch(`${API}/api/output/${encodeURIComponent(name)}`, { method: "DELETE" });
    showToast("Gelöscht");
    loadOutput();
    loadStats();
  } catch (e) {
    showToast("Fehler beim Löschen", "error");
  }
}

async function clearOutput() {
  if (!confirm("Alle generierten Dateien löschen?")) return;
  try {
    const res = await fetch(`${API}/api/output`, { method: "DELETE" });
    const data = await res.json();
    showToast(`${data.deleted} Dateien gelöscht`);
    loadOutput();
    loadStats();
  } catch (e) {
    showToast("Fehler beim Leeren", "error");
  }
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

async function downloadZip() {
  window.open(`${API}/api/download-zip`, "_blank");
}

// ── Settings Modal ─────────────────────────────────────
function openSettings() {
  document.getElementById("settings-modal").classList.add("open");
}

function closeSettings() {
  document.getElementById("settings-modal").classList.remove("open");
}

async function saveSettings() {
  const dir = document.getElementById("settings-output-dir").value.trim();
  try {
    const res = await fetch(`${API}/api/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ output_dir: dir || null }),
    });
    const data = await res.json();
    if (res.ok) {
      document.getElementById("settings-output-dir").value = data.output_dir;
      closeSettings();
      showToast("Einstellungen gespeichert");
    } else {
      showToast(data.detail || "Fehler beim Speichern");
    }
  } catch (e) {
    showToast("Fehler: " + e.message);
  }
}

async function resetSettings() {
  document.getElementById("settings-output-dir").value = "";
  try {
    await fetch(`${API}/api/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ output_dir: null }),
    });
    closeSettings();
    showToast("Zurückgesetzt auf Standard");
  } catch (e) {
    console.error(e);
  }
}

// ── Recent Generators (Welcome Page) ──────────────────
async function loadRecent() {
  try {
    const res = await fetch(`${API}/api/history`);
    const history = await res.json();

    // Update history badge
    const badge = document.getElementById("history-badge");
    if (badge) {
      if (history.length > 0) {
        badge.textContent = history.length;
        badge.style.display = "";
      } else {
        badge.style.display = "none";
      }
    }

    // Recent section on welcome page
    const section = document.getElementById("recent-section");
    if (!section || history.length === 0) return;

    // Get unique recent generators (last 5)
    const seen = new Set();
    const recent = [];
    for (const entry of history) {
      if (!seen.has(entry.generator)) {
        seen.add(entry.generator);
        recent.push(entry);
      }
      if (recent.length >= 5) break;
    }

    section.innerHTML = `
      <h3>Zuletzt verwendet</h3>
      <div class="recent-chips">
        ${recent.map(entry => {
          const typeLabel = entry.type === "preset" ? "Preset" : "";
          return `<button class="recent-chip" onclick="quickLaunch('${escapeHtml(entry.generator)}', '${entry.type}')">
            ${escapeHtml(entry.generator)} ${typeLabel ? `<span class="chip-type">${typeLabel}</span>` : ""}
          </button>`;
        }).join("")}
      </div>
    `;
  } catch (e) {
    console.error("Failed to load recent:", e);
  }
}

function quickLaunch(name, type) {
  if (type === "preset") {
    const presetEntry = Object.entries(presets).find(([k]) => k === name);
    if (presetEntry) {
      const btn = [...document.querySelectorAll(".preset-btn")].find(b => b.textContent === presetEntry[1].label);
      if (btn) btn.click();
    }
  } else {
    for (const [, gens] of Object.entries(generators)) {
      const gen = gens.find(g => g.name === name);
      if (gen) {
        const btn = [...document.querySelectorAll(".gen-btn")].find(b => b.textContent === gen.name);
        if (btn) btn.click();
        return;
      }
    }
  }
}

// ── Quick Launcher (Ctrl+K) ───────────────────────────────
let launcherIndex = -1;

function openLauncher() {
  const modal = document.getElementById("launcher-modal");
  const input = document.getElementById("launcher-input");
  input.value = "";
  document.getElementById("launcher-results").innerHTML = "";
  launcherIndex = -1;
  modal.classList.add("open");
  setTimeout(() => input.focus(), 50);

  // Build initial list
  filterLauncher();

  // Arrow key navigation
  input.onkeydown = (e) => {
    const items = document.querySelectorAll(".launcher-item");
    if (e.key === "ArrowDown") {
      e.preventDefault();
      launcherIndex = Math.min(launcherIndex + 1, items.length - 1);
      updateLauncherActive(items);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      launcherIndex = Math.max(launcherIndex - 1, 0);
      updateLauncherActive(items);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (items[launcherIndex]) items[launcherIndex].click();
    }
  };
}

function closeLauncher() {
  document.getElementById("launcher-modal").classList.remove("open");
}

function updateLauncherActive(items) {
  items.forEach((item, i) => item.classList.toggle("active", i === launcherIndex));
  if (items[launcherIndex]) items[launcherIndex].scrollIntoView({ block: "nearest" });
}

function filterLauncher() {
  const q = document.getElementById("launcher-input").value.toLowerCase().trim();
  const results = document.getElementById("launcher-results");
  const items = [];

  // Presets
  for (const [key, preset] of Object.entries(presets)) {
    if (!q || preset.label.toLowerCase().includes(q) || key.toLowerCase().includes(q)) {
      items.push({ name: preset.label, key, type: "preset", cat: "Preset", desc: preset.description });
    }
  }

  // Generators
  for (const [category, gens] of Object.entries(generators)) {
    for (const gen of gens) {
      if (!q || gen.name.toLowerCase().includes(q) || gen.description.toLowerCase().includes(q) || category.toLowerCase().includes(q)) {
        items.push({ name: gen.name, type: "generator", cat: category, desc: gen.description, gen });
      }
    }
  }

  launcherIndex = items.length > 0 ? 0 : -1;
  results.innerHTML = items.slice(0, 12).map((item, i) => {
    const typeCls = item.type === "preset" ? "preset" : "gen";
    const typeLabel = item.type === "preset" ? "Preset" : "Gen";
    return `<li class="launcher-item ${i === 0 ? 'active' : ''}" data-type="${item.type}" data-key="${item.key || item.name}">
      <span class="launcher-type ${typeCls}">${typeLabel}</span>
      <span class="launcher-name">${escapeHtml(item.name)}</span>
      <span class="launcher-cat">${escapeHtml(item.cat)}</span>
    </li>`;
  }).join("");

  // Click handlers
  results.querySelectorAll(".launcher-item").forEach(li => {
    li.addEventListener("click", () => {
      closeLauncher();
      const type = li.dataset.type;
      const key = li.dataset.key;
      quickLaunch(key, type);
    });
  });
}
