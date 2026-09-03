(() => {
  "use strict";

  const bookmarks = Array.isArray(window.BOOKMARKS) ? window.BOOKMARKS : [];
  const shuffledBookmarks = shuffle(bookmarks);
  const sourceOrder = ["x", "web", "bilibili", "youtube", "wechat"];
  const sourceLabels = {
    all: "All",
    x: "X",
    web: "Web",
    bilibili: "Bilibili",
    youtube: "YouTube",
    wechat: "WeChat",
    rss: "RSS",
    telegram: "Telegram",
    unknown: "Other",
  };
  const sourceSymbols = {
    all: "▦",
    x: "X",
    web: "◎",
    bilibili: "▻",
    youtube: "▶",
    wechat: "●",
    rss: "◔",
    telegram: "↗",
    unknown: "•",
  };

  const elements = {
    search: document.querySelector("#search-input"),
    filters: document.querySelector("#source-filters"),
    grid: document.querySelector("#bookmark-grid"),
    summary: document.querySelector("#results-summary"),
    total: document.querySelector("#total-count"),
    clear: document.querySelector("#clear-search"),
    sort: document.querySelector("#sort-toggle"),
    empty: document.querySelector("#empty-state"),
    reset: document.querySelector("#reset-filters"),
    views: [...document.querySelectorAll("[data-view]")],
  };

  const storedView = localStorage.getItem("link-vault-view");
  const state = {
    query: "",
    source: "all",
    sort: "random",
    view: storedView === "list" ? "list" : "grid",
  };

  function shuffle(items) {
    const shuffled = [...items];
    for (let index = shuffled.length - 1; index > 0; index -= 1) {
      const target = Math.floor(Math.random() * (index + 1));
      [shuffled[index], shuffled[target]] = [shuffled[target], shuffled[index]];
    }
    return shuffled;
  }

  function normalize(value) {
    return String(value || "").normalize("NFKC").toLocaleLowerCase();
  }

  function sourceCount(source) {
    return source === "all" ? bookmarks.length : bookmarks.filter((item) => item.source === source).length;
  }

  function activeSources() {
    const available = [...new Set(bookmarks.map((item) => item.source))];
    return ["all", ...sourceOrder.filter((source) => available.includes(source)), ...available.filter((source) => !sourceOrder.includes(source))];
  }

  function renderFilters() {
    elements.filters.replaceChildren();
    activeSources().forEach((source) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "filter-button" + (state.source === source ? " is-active" : "");
      button.dataset.source = source;
      button.setAttribute("aria-pressed", state.source === source ? "true" : "false");

      const symbol = document.createElement("span");
      symbol.className = "filter-symbol";
      symbol.setAttribute("aria-hidden", "true");
      symbol.textContent = sourceSymbols[source] || sourceSymbols.unknown;

      const label = document.createElement("span");
      label.textContent = sourceLabels[source] || source;

      const count = document.createElement("span");
      count.className = "filter-count";
      count.textContent = sourceCount(source);

      button.append(symbol, label, count);
      button.addEventListener("click", () => {
        state.source = source;
        renderFilters();
        renderBookmarks();
      });
      elements.filters.append(button);
    });
  }

  function matches(item) {
    if (state.source !== "all" && item.source !== state.source) return false;
    if (!state.query) return true;
    const haystack = normalize([item.title, item.author, item.domain, item.source, item.excerpt].join(" "));
    return state.query.split(/\s+/).every((term) => haystack.includes(term));
  }

  function text(tag, className, value) {
    const node = document.createElement(tag);
    node.className = className;
    node.textContent = value;
    return node;
  }

  function formatDate(value) {
    if (!value) return "Undated";
    const parsed = new Date(value + "T00:00:00Z");
    if (Number.isNaN(parsed.valueOf())) return value;
    return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" }).format(parsed);
  }

  function createCard(item, index) {
    const card = document.createElement("article");
    const useAccent = !item.image && item.excerpt && index % 9 === 4;
    card.className = "bookmark" + (useAccent ? " is-accent" : "");
    card.dataset.source = item.source;

    if (item.image) {
      const figure = document.createElement("figure");
      figure.className = "bookmark-media";
      const image = document.createElement("img");
      image.src = item.image;
      image.alt = "";
      image.loading = index < 8 ? "eager" : "lazy";
      image.decoding = "async";
      image.addEventListener("error", () => figure.remove(), { once: true });
      figure.append(image);
      card.append(figure);
    }

    const body = document.createElement("div");
    body.className = "bookmark-body";
    body.append(text("span", "bookmark-source", sourceLabels[item.source] || item.source));

    const heading = document.createElement("h2");
    heading.className = "bookmark-title";
    const link = document.createElement("a");
    link.href = item.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = item.title;
    link.setAttribute("aria-label", `${item.title} — open saved page`);
    heading.append(link);
    body.append(heading);

    if (item.excerpt && (!item.image || state.view === "list")) {
      body.append(text("p", "bookmark-excerpt", item.excerpt));
    }

    const meta = document.createElement("div");
    meta.className = "bookmark-meta";
    if (item.domain) meta.append(text("span", "bookmark-domain", item.domain));
    if (item.author) {
      if (item.domain) meta.append(text("span", "meta-dot", "·"));
      meta.append(text("span", "bookmark-author", item.author));
    }
    if (item.domain || item.author) meta.append(text("span", "meta-dot", "·"));
    meta.append(text("time", "bookmark-date", formatDate(item.date)));
    meta.append(text("span", "bookmark-open", "↗"));
    body.append(meta);
    card.append(body);
    return card;
  }

  function renderBookmarks() {
    const ordered = state.sort === "timeline" ? bookmarks : shuffledBookmarks;
    const filtered = ordered.filter(matches);
    elements.grid.replaceChildren(...filtered.map(createCard));
    elements.grid.classList.toggle("is-list", state.view === "list");
    elements.empty.hidden = filtered.length !== 0;
    elements.grid.hidden = filtered.length === 0;

    const scope = state.source === "all" ? "bookmarks" : `${sourceLabels[state.source] || state.source} bookmarks`;
    const resultLabel = state.query
      ? `${filtered.length} ${scope} matching “${elements.search.value.trim()}”`
      : `${filtered.length} ${scope}`;
    elements.summary.textContent = `${resultLabel}, ${state.sort === "timeline" ? "newest first" : "shuffled"}`;
    elements.total.textContent = `${bookmarks.length} bookmarks`;
    elements.clear.hidden = !state.query;
  }

  function toggleSort() {
    const timeline = state.sort !== "timeline";
    state.sort = timeline ? "timeline" : "random";
    elements.sort.textContent = timeline ? "Shuffle" : "Timeline";
    elements.sort.setAttribute("aria-pressed", timeline ? "true" : "false");
    renderBookmarks();
  }

  function setView(view) {
    state.view = view;
    localStorage.setItem("link-vault-view", view);
    elements.views.forEach((button) => {
      const active = button.dataset.view === view;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    });
    renderBookmarks();
  }

  function reset() {
    elements.search.value = "";
    state.query = "";
    state.source = "all";
    renderFilters();
    renderBookmarks();
    elements.search.focus();
  }

  elements.search.addEventListener("input", (event) => {
    state.query = normalize(event.target.value.trim());
    renderBookmarks();
  });
  elements.clear.addEventListener("click", reset);
  elements.sort.addEventListener("click", toggleSort);
  elements.reset.addEventListener("click", reset);
  elements.views.forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));
  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLocaleLowerCase() === "k") {
      event.preventDefault();
      elements.search.focus();
    }
    if (event.key === "Escape" && document.activeElement === elements.search && elements.search.value) {
      reset();
    }
  });

  if (!/Mac|iPhone|iPad/.test(navigator.platform)) {
    document.querySelector(".command-key").textContent = "Ctrl+";
  }
  renderFilters();
  setView(state.view);
})();
