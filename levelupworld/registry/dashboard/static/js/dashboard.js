(() => {
  const q = document.getElementById("filter-q");
  const tier = document.getElementById("filter-tier");
  const category = document.getElementById("filter-category");
  const operation = document.getElementById("filter-operation");
  const environment = document.getElementById("filter-environment");
  const health = document.getElementById("filter-health");
  const transport = document.getElementById("filter-transport");
  const sort = document.getElementById("filter-sort");
  const rows = [...document.querySelectorAll("#connector-table .catalog-row")];
  const cards = [...document.querySelectorAll("#connector-grid .card")];
  const tableView = document.getElementById("catalog-table-view");
  const cardView = document.getElementById("connector-grid");
  const btnTable = document.getElementById("view-table");
  const btnCards = document.getElementById("view-cards");

  const TRUST_RANK = {
    unverified: 1,
    sandboxed: 2,
    reviewed: 3,
    certified: 4,
    production_critical: 5,
  };

  function parseTier(value) {
    if (!value) return null;
    if (value.includes(",")) {
      return value.split(",").map((x) => Number(x.trim())).filter(Boolean);
    }
    if (TRUST_RANK[value]) return [TRUST_RANK[value]];
    return null;
  }

  function rowVisible(el) {
    const query = (q?.value || "").trim().toLowerCase();
    const t = tier?.value || "";
    const c = category?.value || "";
    const op = operation?.value || "";
    const env = environment?.value || "";
    const h = health?.value || "";
    const tr = transport?.value || "";

    const okQ = !query || (el.dataset.text || "").includes(query);
    let okT = true;
    const ranks = parseTier(t);
    if (ranks) {
      okT = ranks.includes(TRUST_RANK[el.dataset.tier] || 0);
    } else if (t) {
      okT = el.dataset.tier === t;
    }
    const okC = !c || el.dataset.category === c;
    const okOp = !op || (el.dataset.ops || "").split(",").includes(op);
    const okEnv = !env || (el.dataset.envs || "").split(",").includes(env);
    const okH = !h || el.dataset.health === h;
    const okTr = !tr || el.dataset.transport === tr;
    return okQ && okT && okC && okOp && okEnv && okH && okTr;
  }

  function applySort() {
    const key = sort?.value || "rank";
    const tbody = document.querySelector("#connector-table tbody");
    if (!tbody) return;
    const list = [...rows];
    const desc = key.startsWith("-");
    const field = key.replace(/^-/, "");
    list.sort((a, b) => {
      let av;
      let bv;
      if (field === "name") {
        av = a.dataset.text;
        bv = b.dataset.text;
        return desc ? bv.localeCompare(av) : av.localeCompare(bv);
      }
      if (field === "activity_24h" || field === "success_rate_24h") {
        av = Number(a.dataset.success || 0);
        bv = Number(b.dataset.success || 0);
      } else if (field === "p95_latency_ms") {
        av = Number(a.dataset.p95 || 0);
        bv = Number(b.dataset.p95 || 0);
      } else {
        return 0;
      }
      return desc ? bv - av : av - bv;
    });
    for (const row of list) tbody.appendChild(row);
  }

  function apply() {
    for (const row of rows) {
      row.classList.toggle("is-hidden", !rowVisible(row));
    }
    for (const card of cards) {
      const query = (q?.value || "").trim().toLowerCase();
      const t = tier?.value || "";
      const c = category?.value || "";
      const okQ = !query || (card.dataset.text || "").includes(query);
      const ranks = parseTier(t);
      let okT = true;
      if (ranks) okT = ranks.includes(TRUST_RANK[card.dataset.tier] || 0);
      else if (t) okT = card.dataset.tier === t;
      const okC = !c || card.dataset.category === c;
      card.classList.toggle("is-hidden", !(okQ && okT && okC));
    }
    applySort();
    // Reflect filters into URL for shareable catalog state
    const params = new URLSearchParams();
    if (q?.value) params.set("q", q.value);
    if (category?.value) params.set("category", category.value);
    if (operation?.value) params.set("operation", operation.value);
    if (tier?.value) params.set("trustTier", tier.value);
    if (environment?.value) params.set("environment", environment.value);
    if (health?.value) params.set("health", health.value);
    if (sort?.value && sort.value !== "rank") params.set("sort", sort.value);
    const qs = params.toString();
    history.replaceState(null, "", qs ? `/?${qs}` : "/");
  }

  function setView(mode) {
    const table = mode !== "cards";
    tableView?.classList.toggle("is-hidden", !table);
    cardView?.classList.toggle("is-hidden", table);
    btnTable?.classList.toggle("active", table);
    btnCards?.classList.toggle("active", !table);
  }

  q?.addEventListener("input", apply);
  tier?.addEventListener("change", apply);
  category?.addEventListener("change", apply);
  operation?.addEventListener("change", apply);
  environment?.addEventListener("change", apply);
  health?.addEventListener("change", apply);
  transport?.addEventListener("change", apply);
  sort?.addEventListener("change", apply);
  btnTable?.addEventListener("click", () => setView("table"));
  btnCards?.addEventListener("click", () => setView("cards"));

  // Hydrate from URL
  const initial = new URLSearchParams(location.search);
  if (q && initial.get("q")) q.value = initial.get("q");
  if (category && initial.get("category")) category.value = initial.get("category").split(",")[0];
  if (operation && initial.get("operation")) operation.value = initial.get("operation");
  if (tier && (initial.get("trustTier") || initial.get("trust_tier"))) {
    tier.value = initial.get("trustTier") || initial.get("trust_tier");
  }
  if (environment && initial.get("environment")) environment.value = initial.get("environment");
  if (health && initial.get("health")) health.value = initial.get("health").split(",")[0];
  if (sort && initial.get("sort")) sort.value = initial.get("sort");
  apply();
  setView("table");

  window.runTests = async (slug, version) => {
    const out = document.getElementById("test-output");
    if (out) out.textContent = "Running…";
    const res = await fetch(`/api/v1/connectors/${slug}/versions/${version}/test-runs?suite=full`, {
      method: "POST",
    });
    const body = await res.json();
    if (out) out.textContent = JSON.stringify(body, null, 2);
  };

  window.requestActivation = async (slug, version) => {
    const out = document.getElementById("activation-output");
    const res = await fetch("/api/v1/activations", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        slug,
        version,
        project_id: "agent-platform",
        environment: "staging",
        actor: "user:dashboard",
      }),
    });
    const body = await res.json();
    if (out) out.textContent = JSON.stringify(body, null, 2);
  };

  window.quarantine = async (event) => {
    event.preventDefault();
    const form = event.target;
    const slug = form.action.split("/").slice(-2, -1)[0];
    const version = form.querySelector('[name="version"]').value;
    if (!confirm(`Quarantine ${slug}@${version} at the gateway?`)) return false;
    const res = await fetch(form.action, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ version, reason: "emergency quarantine from dashboard", actor: "user:dashboard" }),
    });
    const body = await res.json();
    alert(res.ok ? `Quarantined: ${body.id}` : JSON.stringify(body));
    if (res.ok) location.reload();
    return false;
  };
})();
