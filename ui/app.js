(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const state = { items: [], activeId: null, tab: "signals", query: "" };
  let api = null;

  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  // ---------- Connection to Python ----------
  function ready(fn) {
    if (window.pywebview && window.pywebview.api) return fn(window.pywebview.api);
    window.addEventListener("pywebviewready", () => fn(window.pywebview.api));
    if (new URLSearchParams(location.search).has("demo")) {
      // Browser preview only
      import("./demo.js").then((m) => fn(m.createDemoApi()));
    }
  }

  // ---------- File list ----------
  function addResults(results) {
    let firstNew = null;
    for (const r of results) {
      const key = r.xmlPath;
      const existing = state.items.findIndex((i) => i.xmlPath === key);
      const item = { ...r, id: r.id || "err-" + Math.random().toString(36).slice(2), savedTo: null };
      if (existing >= 0) {
        if (state.items[existing].ok) api.remove(state.items[existing].id);
        state.items[existing] = item;
      } else {
        state.items.push(item);
      }
      firstNew = firstNew || item.id;
    }
    if (firstNew) select(firstNew);
    renderList();
  }

  function renderList() {
    const ul = $("filelist");
    if (!state.items.length) {
      ul.innerHTML = '<li class="placeholder">No files loaded yet.</li>';
    } else {
      ul.innerHTML = state.items.map((i) => {
        const cls = ["file", i.id === state.activeId ? "active" : "", i.ok ? "" : "err", i.savedTo ? "saved" : ""].join(" ");
        const meta = !i.ok ? "Failed to read file"
          : `${esc(i.dbName)} · ${i.signals.length} signals${i.savedTo ? " · saved" : ""}`;
        return `<li class="${cls}" data-id="${esc(i.id)}">
          <span class="dot"></span>
          <div><div class="file-name">${esc(i.fileName)}</div><div class="file-meta">${meta}</div></div>
          <button class="remove" data-remove="${esc(i.id)}" title="Remove from list">×</button>
        </li>`;
      }).join("");
    }
    const okCount = state.items.filter((i) => i.ok).length;
    $("sidebar-foot").hidden = okCount < 2;
    $("btn-save-all").textContent = `Save all (${okCount})…`;
  }

  function select(id) {
    state.activeId = id;
    state.query = "";
    $("search").value = "";
    setTab("signals", false);
    renderList();
    renderDetail();
  }

  function removeItem(id) {
    const idx = state.items.findIndex((i) => i.id === id);
    if (idx < 0) return;
    if (state.items[idx].ok) api.remove(id);
    state.items.splice(idx, 1);
    if (state.activeId === id) state.activeId = state.items[Math.min(idx, state.items.length - 1)]?.id ?? null;
    renderList();
    renderDetail();
  }

  // ---------- Detail view ----------
  function current() { return state.items.find((i) => i.id === state.activeId); }

  function renderDetail() {
    const item = current();
    $("empty").hidden = !!item;
    $("detail").hidden = !item || !item.ok;
    $("error-view").hidden = !item || item.ok;
    if (!item) return;
    if (!item.ok) {
      $("e-path").textContent = item.xmlPath;
      $("e-msg").textContent = item.error;
      return;
    }
    $("d-db").textContent = item.dbName;
    $("d-path").textContent = item.xmlPath;
    $("d-path").title = item.xmlPath;
    $("s-signals").textContent = item.signals.length;
    $("s-skipped").textContent = item.skipped.length;
    $("t-signals").textContent = item.signals.length;
    $("t-skipped").textContent = item.skipped.length;

    const types = {};
    for (const s of item.signals) types[s.Type] = (types[s.Type] || 0) + 1;
    $("s-types").innerHTML = Object.entries(types).sort((a, b) => b[1] - a[1])
      .map(([t, n]) => `<span class="chip">${esc(t)}<b>${n}</b></span>`).join("") || '<span class="stat-lbl">–</span>';

    $("skip-notice").hidden = item.skipped.length === 0;
    $("skip-notice-count").textContent = item.skipped.length;
    $("btn-save").disabled = false;
    renderTable();
  }

  function setTab(tab, render = true) {
    state.tab = tab;
    document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
    if (render) renderTable();
  }

  function renderTable() {
    const item = current();
    if (!item || !item.ok) return;
    const q = state.query.trim().toLowerCase();
    let head, rows;
    if (state.tab === "signals") {
      head = "<tr><th>#</th><th>Name</th><th>Address</th><th>S7 type</th><th>moneo type</th><th>Unit</th></tr>";
      rows = item.signals.map((s, i) => {
        const [addr, s7] = s.Address.split(";");
        return { text: `${s.MeasurementName} ${s.Address} ${s.Type}`.toLowerCase(), html:
          `<tr><td class="nowrap">${i + 1}</td><td>${esc(s.MeasurementName)}</td><td class="mono">${esc(addr)}</td>
           <td><span class="type s7">${esc(s7)}</span></td><td><span class="type">${esc(s.Type)}</span></td><td>${esc(s.Unit)}</td></tr>` };
      });
    } else {
      head = "<tr><th>Variable</th><th>TIA data type</th><th>Reason</th></tr>";
      rows = item.skipped.map((s) => ({ text: `${s.path} ${s.datatype} ${s.reason}`.toLowerCase(), html:
        `<tr><td class="mono">${esc(s.path)}</td><td class="mono">${esc(s.datatype)}</td><td class="reason">${esc(s.reason)}</td></tr>` }));
    }
    const visible = q ? rows.filter((r) => r.text.includes(q)) : rows;
    $("thead").innerHTML = head;
    $("tbody").innerHTML = visible.map((r) => r.html).join("");
    $("table-empty").hidden = visible.length > 0;
    $("table-empty").textContent = q ? "No matches for your search." :
      (state.tab === "signals" ? "No transferable signals found." : "No variables were skipped.");
  }

  // ---------- Actions ----------
  async function pickFiles() {
    const results = await api.pick_files();
    if (results && results.length) addResults(results);
  }

  async function saveCurrent() {
    const item = current();
    if (!item) return;
    $("btn-save").disabled = true;
    try {
      const res = await api.save_one(item.id);
      if (res.ok) {
        item.savedTo = res.path;
        renderList();
        toast("JSON file saved", res.path, res.path);
      } else if (!res.cancelled) {
        toast("Saving failed", res.error, null, true);
      }
    } finally {
      $("btn-save").disabled = false;
    }
  }

  async function saveAll() {
    const ids = state.items.filter((i) => i.ok).map((i) => i.id);
    if (!ids.length) return;
    const folder = await api.choose_folder();
    if (!folder) return;
    let res = await api.save_all(ids, folder, false);
    if (res.conflicts) {
      const ok = await confirmDialog("Overwrite files?",
        `The target folder already contains:\n${res.conflicts.join("\n")}`, "Overwrite");
      if (!ok) return;
      res = await api.save_all(ids, folder, true);
    }
    for (const p of res.saved || []) {
      const it = state.items.find((i) => i.ok && p.toLowerCase().endsWith("\\" + i.defaultFilename.toLowerCase()));
      if (it) it.savedTo = p;
    }
    renderList();
    if (res.errors && res.errors.length) toast("Some files could not be saved", res.errors.join("\n"), null, true);
    if (res.saved && res.saved.length) toast(`${res.saved.length} JSON files saved`, res.folder, res.folder);
  }

  function toast(title, text, openPath, isErr = false) {
    const el = document.createElement("div");
    el.className = "toast" + (isErr ? " err" : "");
    el.innerHTML = `<div class="toast-body"><b>${esc(title)}</b><div class="path">${esc(text)}</div>
      ${openPath ? '<button class="link" data-open>Show in Explorer</button>' : ""}</div>
      <button class="close" title="Close">×</button>`;
    el.querySelector(".close").onclick = () => el.remove();
    if (openPath) el.querySelector("[data-open]").onclick = () => api.open_in_explorer(openPath);
    $("toasts").appendChild(el);
    setTimeout(() => el.remove(), isErr ? 15000 : 8000);
  }

  function confirmDialog(title, msg, okLabel) {
    const dlg = $("confirm");
    $("confirm-title").textContent = title;
    $("confirm-msg").textContent = msg;
    $("confirm-ok").textContent = okLabel;
    dlg.returnValue = "";
    dlg.showModal();
    return new Promise((resolve) => dlg.addEventListener("close", () => resolve(dlg.returnValue === "ok"), { once: true }));
  }

  // ---------- Drag & drop (visuals only; Python provides the paths) ----------
  let dragDepth = 0;
  const hasFiles = (e) => Array.from(e.dataTransfer?.types || []).includes("Files");
  document.addEventListener("dragenter", (e) => {
    dragDepth++;
    document.body.classList.add("dragging");
    document.body.classList.toggle("has-files", hasFiles(e) && state.items.length > 0);
  });
  document.addEventListener("dragleave", () => {
    if (--dragDepth <= 0) { dragDepth = 0; document.body.classList.remove("dragging", "has-files"); }
  });
  document.addEventListener("dragover", (e) => e.preventDefault());
  document.addEventListener("drop", (e) => {
    e.preventDefault();
    dragDepth = 0;
    document.body.classList.remove("dragging", "has-files");
  });

  // ---------- Start ----------
  window.app = { addResults };
  renderList();

  ready(async (a) => {
    api = a;
    try {
      const info = await api.info();
      $("version").textContent = "v" + info.version;
    } catch (_) { /* ignore */ }
    $("btn-pick").onclick = pickFiles;
    $("btn-add").onclick = pickFiles;
    $("btn-save").onclick = saveCurrent;
    $("btn-save-all").onclick = saveAll;
    $("skip-notice-link").onclick = () => setTab("skipped");
    $("search").oninput = (e) => { state.query = e.target.value; renderTable(); };
    document.querySelectorAll(".tab").forEach((b) => (b.onclick = () => setTab(b.dataset.tab)));
    $("filelist").addEventListener("click", (e) => {
      const rm = e.target.closest("[data-remove]");
      if (rm) { e.stopPropagation(); removeItem(rm.dataset.remove); return; }
      const li = e.target.closest(".file");
      if (li) select(li.dataset.id);
    });
  });
})();
