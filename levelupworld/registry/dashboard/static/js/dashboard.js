(() => {
  const q = document.getElementById("filter-q");
  const tier = document.getElementById("filter-tier");
  const category = document.getElementById("filter-category");
  const cards = [...document.querySelectorAll("#connector-grid .card")];
  if (!cards.length) return;

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
})();
