// Stage theme: Mermaid diagrams. Loaded as a module, only on pages with a ```mermaid block.
// The Mermaid build comes from params.stage.mermaid.url (a pinned version by default).
// Each diagram gets an "Enlarge" button that opens a native <dialog> (Esc closes it,
// focus goes back to the button).
const me = document.querySelector("script[data-mermaid-src]"); // module scripts have no document.currentScript
const cfg = me ? me.dataset : {};

const figures = [...document.querySelectorAll(".mermaid-figure")];
if (figures.length && cfg.mermaidSrc) {
  try {
    const { default: mermaid } = await import(cfg.mermaidSrc);
    // Diagrams always sit on white paper (see css/mermaid.css), so the default theme stays legible in dark mode.
    mermaid.initialize({ startOnLoad: false, theme: "default", securityLevel: "strict" });
    await mermaid.run({ querySelector: ".mermaid-figure .mermaid" });
  } catch (e) {
    console.warn("Stage: Mermaid could not be loaded", e);
  }

  let dialog = null;
  let opener = null;
  const getDialog = () => {
    if (dialog) return dialog;
    dialog = document.createElement("dialog");
    dialog.className = "mermaid-dialog";
    dialog.setAttribute("aria-label", cfg.enlarged || "Enlarged diagram");
    const close = document.createElement("button");
    close.type = "button";
    close.className = "btn mermaid-dialog__close";
    close.innerHTML = '<span><span class="mermaid-dialog__label"></span> <span aria-hidden="true">✕</span></span>';
    close.querySelector(".mermaid-dialog__label").textContent = cfg.close || "Close";
    close.addEventListener("click", () => dialog.close());
    const body = document.createElement("div");
    body.className = "mermaid-dialog__body";
    dialog.append(close, body);
    // a click on the backdrop (outside the body) closes too
    dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });
    dialog.addEventListener("close", () => { body.replaceChildren(); if (opener) opener.focus(); });
    document.body.appendChild(dialog);
    return dialog;
  };

  const enlarge = (svg, from) => {
    const d = getDialog();
    const body = d.querySelector(".mermaid-dialog__body");
    // Mermaid scopes each diagram's styles and markers to the SVG's id: the copy gets a new id,
    // and every reference to the old one is rewritten with it, so it keeps its look.
    const id = svg.id;
    const markup = id ? svg.outerHTML.replaceAll(id, `${id}-large`) : svg.outerHTML;
    body.innerHTML = markup;
    const copy = body.querySelector("svg");
    ["style", "width", "height"].forEach((a) => copy.removeAttribute(a));
    opener = from;
    d.showModal();
  };

  figures.forEach((fig) => {
    const svg = fig.querySelector(".mermaid svg");
    if (!svg) return;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn mermaid-enlarge";
    btn.innerHTML = '<span></span>';
    btn.firstChild.textContent = cfg.enlarge || "Enlarge diagram";
    btn.addEventListener("click", () => enlarge(fig.querySelector(".mermaid svg"), btn));
    fig.querySelector(".mermaid").addEventListener("click", () => enlarge(fig.querySelector(".mermaid svg"), btn));
    fig.appendChild(btn);
  });
}
