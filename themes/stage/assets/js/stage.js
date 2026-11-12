// Stage theme: progressive enhancements only. Every page works without this file.
(() => {
  "use strict";
  // Reading progress: CSS scroll-driven animation where supported, this fallback elsewhere (e.g. Firefox).
  const bar = document.querySelector(".progress span");
  if (bar && !CSS.supports("animation-timeline: scroll()")) {
    let queued = false;
    const update = () => {
      queued = false;
      const max = document.documentElement.scrollHeight - innerHeight;
      bar.style.setProperty("--p", max > 0 ? Math.min(1, scrollY / max).toFixed(4) : 0);
    };
    addEventListener("scroll", () => { if (!queued) { queued = true; requestAnimationFrame(update); } }, { passive: true });
    addEventListener("resize", update);
    update();
  }

  // TOC: open beside the article on wide screens, and move the ▶ cursor to the section being read.
  const toc = document.querySelector("[data-toc]");
  if (toc) {
    const wide = matchMedia("(min-width: 1180px)");
    const sync = () => { if (wide.matches) toc.open = true; };
    sync();
    wide.addEventListener("change", sync);

    const links = new Map();
    toc.querySelectorAll("a[href^='#']").forEach((a) => {
      const el = document.getElementById(decodeURIComponent(a.hash.slice(1)));
      if (el) links.set(el, a);
    });
    if (links.size && "IntersectionObserver" in window) {
      const visible = new Set();
      const headings = [...links.keys()];
      const io = new IntersectionObserver((entries) => {
        entries.forEach((e) => (e.isIntersecting ? visible.add(e.target) : visible.delete(e.target)));
        let current = headings.find((h) => visible.has(h));
        if (!current) current = headings.filter((h) => h.getBoundingClientRect().top < 0).pop();
        links.forEach((a, h) => {
          const on = h === current;
          a.classList.toggle("is-current", on);
          if (on) a.setAttribute("aria-current", "location"); else a.removeAttribute("aria-current");
        });
      }, { rootMargin: "0px 0px -60% 0px" });
      headings.forEach((h) => io.observe(h));
    }
  }

  // Disqus: load the embed when the reader gets near the comments (or clicks the button).
  const thread = document.getElementById("disqus_thread");
  if (thread) {
    const host = location.hostname;
    const btn = document.querySelector("[data-disqus-load]");
    if (host === "localhost" || host === "127.0.0.1") {
      thread.textContent = "Comments are not loaded on localhost.";
    } else {
      let loaded = false;
      const load = () => {
        if (loaded) return;
        loaded = true;
        if (btn) btn.hidden = true;
        const s = document.createElement("script");
        s.src = `https://${thread.dataset.disqus}.disqus.com/embed.js`;
        s.setAttribute("data-timestamp", Date.now());
        s.async = true;
        document.body.appendChild(s);
      };
      if (btn) { btn.hidden = false; btn.addEventListener("click", load); }
      if ("IntersectionObserver" in window) {
        const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { io.disconnect(); load(); } }, { rootMargin: "600px 0px" });
        io.observe(thread);
      }
    }
  }

  // Search with Pagefind (the index is built after Hugo, see .github/workflows/hugo.yml).
  const form = document.querySelector("[data-search]");
  if (form) {
    const input = form.querySelector("input");
    const status = document.querySelector("[data-search-status]");
    const list = document.querySelector("[data-search-results]");
    let pf = null;
    const say = (msg) => { status.textContent = msg; };
    const load = async () => {
      if (pf) return pf;
      try {
        pf = await import(form.dataset.bundle + "pagefind.js");
        await pf.options({ excerptLength: 26 });
        pf.init();
      } catch (e) {
        pf = null;
        say("The search index isn't available here. It is built when the site is deployed.");
      }
      return pf;
    };
    const item = (data, i) => {
      const li = document.createElement("li");
      li.className = "mi";
      li.style.setProperty("--i", i % 4);
      const a = document.createElement("a");
      a.href = data.url;
      const label = document.createElement("span");
      label.className = "mi__label";
      label.textContent = data.meta.title || data.url;
      a.append(label);
      if (data.meta.date) {
        const d = document.createElement("span");
        d.className = "mi__meta";
        d.textContent = data.meta.date;
        a.append(d);
      }
      const ex = document.createElement("span");
      ex.className = "mi__excerpt";
      ex.innerHTML = data.excerpt; // Pagefind escapes entities; only <mark> tags are added
      a.append(ex);
      li.append(a);
      return li;
    };
    const run = async (q, debounced) => {
      q = q.trim();
      const url = new URL(location.href);
      if (q) url.searchParams.set("q", q); else url.searchParams.delete("q");
      history.replaceState(null, "", url);
      if (!q) { list.replaceChildren(); say(""); return; }
      const api = await load();
      if (!api) return;
      const search = debounced ? await api.debouncedSearch(q) : await api.search(q);
      if (search === null) return; // superseded by a newer keystroke
      const results = await Promise.all(search.results.slice(0, 20).map((r) => r.data()));
      list.replaceChildren(...results.map(item));
      const n = search.results.length;
      say(n ? `${n} result${n === 1 ? "" : "s"} for “${q}”${n > 20 ? ", showing the first 20" : ""}.` : `No results for “${q}”.`);
    };
    form.addEventListener("submit", (e) => { e.preventDefault(); run(input.value, false); });
    input.addEventListener("input", () => run(input.value, true));
    input.addEventListener("focus", load, { once: true });
    const q0 = new URLSearchParams(location.search).get("q");
    if (q0) { input.value = q0; run(q0, false); }
  }
})();
