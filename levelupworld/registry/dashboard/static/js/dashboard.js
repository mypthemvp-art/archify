(() => {
  const q = document.getElementById("filter-q");
  const tier = document.getElementById("filter-tier");
  const category = document.getElementById("filter-category");
  const cards = [...document.querySelectorAll("#connector-grid .card")];
  if (cards.length) {
    function apply() {
      const query = (q?.value || "").trim().toLowerCase();
      const t = tier?.value || "";
      const c = category?.value || "";
      for (const card of cards) {
        const okQ = !query || (card.dataset.text || "").includes(query);
        const okT = !t || card.dataset.tier === t;
        const okC = !c || card.dataset.category === c;
        card.classList.toggle("is-hidden", !(okQ && okT && okC));
      }
    }
    q?.addEventListener("input", apply);
    tier?.addEventListener("change", apply);
    category?.addEventListener("change", apply);
  }

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
