(() => {
  "use strict";

  const WIN_ID = "decky-tb-window";
  const ACCENT = "#1a9fff";

  if (window.__deckyToolbox) {
    window.__deckyToolbox.toggle();
    return "decky-toolbox: already loaded, toggling window";
  }

  function styleBtn(b) {
    b.style.cssText = [
      "padding:10px 14px", "background:#2a3441", "color:#fff",
      "border:1px solid #3a4a52", "border-radius:6px",
      "cursor:pointer", "font-size:14px", "text-align:left",
      "transition:background .15s",
    ].join(";");
    b.addEventListener("mouseenter", () => { b.style.background = "#34414f"; });
    b.addEventListener("mouseleave", () => { b.style.background = "#2a3441"; });
  }

  function buildWindow() {
    const win = document.createElement("div");
    win.id = WIN_ID;
    win.style.cssText = [
      "position:fixed", "top:46px", "right:10px",
      "width:340px", "height:300px",
      "background:#15181e", "border:1px solid #2c3340",
      "border-radius:12px", "box-shadow:0 10px 50px rgba(0,0,0,.75)",
      "z-index:99999", "display:flex", "flex-direction:column",
      "padding:16px", "box-sizing:border-box",
      "font-family:'Motiva Sans',Arial,sans-serif", "color:#fff",
    ].join(";");

    const head = document.createElement("div");
    head.style.cssText = "display:flex;align-items:center;justify-content:space-between;margin-bottom:14px";
    const title = document.createElement("div");
    title.textContent = "decky-toolbox";
    title.style.cssText = "font-weight:700;font-size:16px;letter-spacing:.3px";
    const dot = document.createElement("span");
    dot.textContent = " ●";
    dot.style.cssText = `color:${ACCENT};font-size:12px`;
    title.appendChild(dot);
    const close = document.createElement("div");
    close.textContent = "✕";
    close.style.cssText = "cursor:pointer;font-size:16px;opacity:.7;padding:4px 8px";
    close.addEventListener("click", () => win.remove());
    head.appendChild(title);
    head.appendChild(close);
    win.appendChild(head);

    const status = document.createElement("div");
    status.id = "decky-tb-status";
    status.textContent = "Ready.";
    status.style.cssText = [
      "background:#0d0f13", "border:1px solid #232a35", "border-radius:6px",
      "padding:8px 10px", "font-size:12px", "color:#9fb3c8",
      "margin-bottom:14px", "min-height:16px",
    ].join(";");
    win.appendChild(status);

    const col = document.createElement("div");
    col.style.cssText = "display:flex;flex-direction:column;gap:8px;flex:1";

    let counter = 0;
    const bA = document.createElement("button");
    bA.textContent = "Button A — counter";
    styleBtn(bA);
    bA.addEventListener("click", () => {
      counter++;
      status.textContent = `Button A clicked ${counter} times.`;
      status.style.color = ACCENT;
    });

    const colors = ["#15181e", "#1e1530", "#15301e", "#301520"];
    let ci = 0;
    const bB = document.createElement("button");
    bB.textContent = "Button B — background";
    styleBtn(bB);
    bB.addEventListener("click", () => {
      ci = (ci + 1) % colors.length;
      win.style.background = colors[ci];
      status.textContent = `Background: ${colors[ci]}`;
      status.style.color = "#9fb3c8";
    });

    const bC = document.createElement("button");
    bC.textContent = "Button C — system info";
    styleBtn(bC);
    bC.addEventListener("click", () => {
      const w = window.innerWidth, h = window.innerHeight;
      status.textContent = `Viewport ${w}x${h} — ${new Date().toLocaleTimeString()}`;
      status.style.color = "#9fb3c8";
    });

    col.appendChild(bA);
    col.appendChild(bB);
    col.appendChild(bC);
    win.appendChild(col);

    const foot = document.createElement("div");
    foot.textContent = "hehe";
    foot.style.cssText = "font-size:10px;color:#55606e;margin-top:10px;text-align:center";
    win.appendChild(foot);

    return win;
  }

  function toggleWindow() {
    const existing = document.getElementById(WIN_ID);
    if (existing) { existing.remove(); return; }
    document.body.appendChild(buildWindow());
  }

  window.__deckyToolbox = {
    toggle: toggleWindow,
    stop: () => {
      const w = document.getElementById(WIN_ID);
      if (w) w.remove();
      delete window.__deckyToolbox;
    },
  };

  toggleWindow();
  return "decky-toolbox: window opened";
})();
