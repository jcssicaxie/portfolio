/* Jessica Xie — Portfolio, Edition 2026
   Small, dependency-free enhancements. Every page works without this file. */
(() => {
  const root = document.documentElement;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));

  /* Intro (home, once per visit): wait for the Ballet font, write the name, then turn the page */
  const intro = $("[data-intro]");
  if (intro && root.classList.contains("show-intro")) {
    let done = false, timer = 0;
    const finish = (quick) => {
      if (done) return; done = true; clearTimeout(timer);
      try { sessionStorage.setItem("jx-intro", "1"); } catch (e) {}
      intro.classList.add("out"); if (quick) intro.classList.add("quick");
      const end = () => { root.classList.remove("show-intro"); root.classList.add("intro-done"); intro.remove(); };
      intro.addEventListener("transitionend", end, { once: true });
      setTimeout(end, 1200);
    };
    const start = () => { intro.classList.add("go"); timer = setTimeout(() => finish(false), 3600); };
    const fontReady = document.fonts && document.fonts.load ? document.fonts.load('1em "Ballet"') : Promise.resolve();
    Promise.race([fontReady, new Promise((r) => setTimeout(r, 1500))]).then(start, start);
    ["pointerdown", "keydown", "wheel", "touchstart"].forEach((ev) => window.addEventListener(ev, () => finish(true), { once: true, passive: true }));
  } else if (intro) {
    intro.remove();
  }

  /* Theme: light (#F5F4F0) by default; dark only when the reader chooses it */
  const isDark = () => root.dataset.theme === "dark";
  const themeBtn = $("[data-theme-toggle]");
  const syncTheme = () => themeBtn && themeBtn.setAttribute("aria-pressed", String(isDark()));
  if (themeBtn) {
    syncTheme();
    themeBtn.addEventListener("click", () => {
      const next = isDark() ? "light" : "dark";
      root.dataset.theme = next;
      try { localStorage.setItem("jx-theme", next); } catch (e) {}
      syncTheme();
    });
  }

  /* Mobile menu: the cream tab that slides out from the left edge */
  const menuBtn = $("[data-menu-toggle]");
  const panel = $("#site-nav-panel");
  const mobile = window.matchMedia("(max-width: 63.99rem)");
  const setMenu = (open) => {
    if (!menuBtn || !panel) return;
    root.classList.toggle("menu-open", open);
    menuBtn.setAttribute("aria-expanded", String(open));
    panel.inert = mobile.matches && !open;
  };
  if (menuBtn && panel) {
    setMenu(false);
    menuBtn.addEventListener("click", () => {
      const open = !root.classList.contains("menu-open");
      setMenu(open);
      if (open) $("a", panel)?.focus();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && root.classList.contains("menu-open")) { setMenu(false); menuBtn.focus(); }
    });
    document.addEventListener("click", (e) => {
      if (root.classList.contains("menu-open") && !e.target.closest("#site-nav")) setMenu(false);
    });
    $$("a", panel).forEach((a) => a.addEventListener("click", () => setMenu(false)));
    mobile.addEventListener?.("change", () => setMenu(false));
  }

  /* Reveal on scroll — once, quietly */
  const reveals = $$(".reveal");
  if ("IntersectionObserver" in window && !reduceMotion.matches) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); } });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.04 });
    reveals.forEach((el) => io.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add("is-in"));
  }

  /* Videos: play only while visible; with reduced motion, show controls instead */
  const vids = $$("video[data-autoplay]");
  if (reduceMotion.matches || !("IntersectionObserver" in window)) {
    vids.forEach((v) => { v.controls = true; v.preload = "metadata"; });
  } else {
    const vo = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        const v = en.target;
        if (en.isIntersecting) { v.play().catch(() => { v.controls = true; }); } else { v.pause(); }
      });
    }, { threshold: 0.25 });
    vids.forEach((v) => vo.observe(v));
  }

  /* Hero background video: decorative, silent; stopped for reduced motion */
  $$("video[data-bg-video]").forEach((v) => {
    if (reduceMotion.matches) { v.pause(); v.removeAttribute("autoplay"); v.preload = "none"; return; }
    v.play().catch(() => {});
  });

  /* Index of work: filter by discipline (hash-linkable, e.g. work.html#ux) */
  const filterWrap = $(".filters");
  if (filterWrap) {
    const buttons = $$("button[data-filter]", filterWrap);
    const rows = $$(".ix-row");
    const groups = $$(".ix-group");
    const count = $("[data-count]");
    const apply = (key, push) => {
      if (!buttons.some((b) => b.dataset.filter === key)) key = "all";
      buttons.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.filter === key)));
      let n = 0;
      rows.forEach((r) => { const show = key === "all" || r.dataset.discipline === key; r.hidden = !show; if (show) n++; });
      groups.forEach((g) => { g.hidden = !$$(".ix-row", g).some((r) => !r.hidden); });
      if (count) count.textContent = `${n} ${n === 1 ? "entry" : "entries"}`;
      if (push) history.replaceState(null, "", key === "all" ? location.pathname : `#${key}`);
    };
    buttons.forEach((b) => b.addEventListener("click", () => apply(b.dataset.filter, true)));
    apply(location.hash.slice(1) || "all", false);
    window.addEventListener("hashchange", () => apply(location.hash.slice(1) || "all", false));
  }

  /* Floating image preview for index lists (pointer devices only) */
  const preview = $(".preview");
  const previewImg = preview && $("img", preview);
  const targets = $$("[data-preview]");
  if (preview && targets.length && finePointer.matches) {
    let x = 0, y = 0, raf = 0;
    const move = () => { preview.style.transform = `translate3d(${x + 24}px, ${y - preview.offsetHeight / 2}px, 0)`; raf = 0; };
    const onMove = (e) => { x = e.clientX; y = e.clientY; if (!raf) raf = requestAnimationFrame(move); };
    targets.forEach((t) => {
      t.addEventListener("mouseenter", (e) => {
        previewImg.src = t.dataset.preview; x = e.clientX; y = e.clientY;
        preview.classList.add("on"); move();
      });
      t.addEventListener("mousemove", onMove);
      t.addEventListener("mouseleave", () => preview.classList.remove("on"));
    });
    window.addEventListener("scroll", () => preview.classList.remove("on"), { passive: true });
  }

  /* Magazine page strip */
  $$("[data-pages]").forEach((wrap) => {
    const track = $(".pg-track", wrap);
    const pages = $$(".pg", track);
    const prev = $("[data-pg-prev]", wrap);
    const next = $("[data-pg-next]", wrap);
    const out = $("[data-pg-count]", wrap);
    const total = String(pages.length).padStart(2, "0");
    const current = () => {
      const left = track.scrollLeft + 2;
      let i = pages.findIndex((p) => p.offsetLeft - track.offsetLeft + p.offsetWidth / 2 > left + parseFloat(getComputedStyle(track).scrollPaddingLeft || 0));
      return Math.max(0, i);
    };
    const update = () => {
      const i = current();
      out.textContent = `${String(i + 1).padStart(2, "0")} / ${total}`;
      prev.disabled = track.scrollLeft < 4;
      next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 4;
    };
    const go = (dir) => {
      const i = Math.min(pages.length - 1, Math.max(0, current() + dir));
      track.scrollTo({ left: pages[i].offsetLeft - track.offsetLeft - parseFloat(getComputedStyle(track).paddingLeft), behavior: reduceMotion.matches ? "auto" : "smooth" });
    };
    prev.addEventListener("click", () => go(-1));
    next.addEventListener("click", () => go(1));
    track.addEventListener("scroll", () => requestAnimationFrame(update), { passive: true });
    track.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight") { e.preventDefault(); go(1); }
      if (e.key === "ArrowLeft") { e.preventDefault(); go(-1); }
    });
    update();
  });

  /* ASCII flow trail: characters follow the pointer and fade out.
     Dense glyphs at the head, sparse dots in the tail. Off for reduced motion. */
  $$("[data-ascii-trail]").forEach((el) => {
    if (reduceMotion.matches) return;
    const canvas = document.createElement("canvas");
    canvas.className = "ascii-trail";
    canvas.setAttribute("aria-hidden", "true");
    el.prepend(canvas);
    const ctx = canvas.getContext("2d");
    const RAMP = " .·:-+*=#%@";
    const CW = 9, CH = 12;            // cell size in CSS px
    const RADIUS = 3.8;                // brush radius in cells
    const DECAY = 0.965;               // per frame
    let cols = 0, rows = 0, field = null, dither = null, dpr = 1, w = 0, h = 0;
    let last = null, raf = 0, color = "#0B0B0A", visible = true;

    const resize = () => {
      const r = el.getBoundingClientRect();
      w = r.width; h = r.height; dpr = Math.min(2, window.devicePixelRatio || 1);
      canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
      cols = Math.ceil(w / CW); rows = Math.ceil(h / CH);
      field = new Float32Array(cols * rows);
      dither = new Float32Array(cols * rows).map(() => Math.random());
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.textBaseline = "top";
      ctx.font = `${CH}px ui-monospace, "SFMono-Regular", Menlo, monospace`;
    };
    const stamp = (x, y, strength) => {
      const cx = x / CW, cy = y / CH;
      const r = Math.ceil(RADIUS);
      for (let j = Math.floor(cy) - r; j <= Math.floor(cy) + r; j++) {
        if (j < 0 || j >= rows) continue;
        for (let i = Math.floor(cx) - r; i <= Math.floor(cx) + r; i++) {
          if (i < 0 || i >= cols) continue;
          const d = Math.hypot(i + 0.5 - cx, j + 0.5 - cy);
          const v = Math.max(0, 1 - d / RADIUS) * strength;
          const k = j * cols + i;
          if (v > field[k]) field[k] = Math.min(1, v);
        }
      }
    };
    const frame = () => {
      raf = 0;
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = color;
      let energy = 0;
      for (let k = 0; k < field.length; k++) {
        let v = field[k];
        if (v < 0.02) { field[k] = 0; continue; }
        energy += v;
        field[k] = v * DECAY;
        if (v < 0.45 && dither[k] > v * 2.6) continue;     // sparse, stippled tail
        const ch = RAMP[Math.min(RAMP.length - 1, Math.round(v * (RAMP.length - 1)))];
        ctx.globalAlpha = Math.min(1, 0.45 + v);
        ctx.fillText(ch, (k % cols) * CW, Math.floor(k / cols) * CH);
      }
      ctx.globalAlpha = 1;
      if (energy > 0 && visible) raf = requestAnimationFrame(frame);
    };
    const kick = () => { if (!raf) raf = requestAnimationFrame(frame); };
    el.addEventListener("pointerenter", (e) => {
      const cs = getComputedStyle(el);
      color = cs.getPropertyValue("--trail").trim() || cs.color;
      const r = el.getBoundingClientRect(); last = { x: e.clientX - r.left, y: e.clientY - r.top };
    });
    el.addEventListener("pointermove", (e) => {
      const r = el.getBoundingClientRect();
      const p = { x: e.clientX - r.left, y: e.clientY - r.top };
      if (last) {
        const dist = Math.hypot(p.x - last.x, p.y - last.y);
        const steps = Math.max(1, Math.ceil(dist / (CW * 0.6)));
        for (let s = 1; s <= steps; s++) stamp(last.x + (p.x - last.x) * s / steps, last.y + (p.y - last.y) * s / steps, 1);
      } else stamp(p.x, p.y, 1);
      last = p; kick();
    }, { passive: true });
    el.addEventListener("pointerleave", () => { last = null; });
    /* Touch: draw with a finger, also while the page scrolls (passive, never blocks scrolling) */
    const touchPoint = (e) => { const t = e.touches[0]; const r = el.getBoundingClientRect(); return { x: t.clientX - r.left, y: t.clientY - r.top }; };
    el.addEventListener("touchstart", (e) => {
      const cs = getComputedStyle(el);
      color = cs.getPropertyValue("--trail").trim() || cs.color;
      last = touchPoint(e); stamp(last.x, last.y, 1); kick();
    }, { passive: true });
    el.addEventListener("touchmove", (e) => {
      const p = touchPoint(e);
      if (last) {
        const dist = Math.hypot(p.x - last.x, p.y - last.y);
        const steps = Math.max(1, Math.ceil(dist / (CW * 0.6)));
        for (let s = 1; s <= steps; s++) stamp(last.x + (p.x - last.x) * s / steps, last.y + (p.y - last.y) * s / steps, 1);
      } else stamp(p.x, p.y, 1);
      last = p; kick();
    }, { passive: true });
    el.addEventListener("touchend", () => { last = null; }, { passive: true });
    if ("ResizeObserver" in window) new ResizeObserver(resize).observe(el); else window.addEventListener("resize", resize);
    if ("IntersectionObserver" in window) new IntersectionObserver((en) => { visible = en[0].isIntersecting; if (visible) kick(); }).observe(el);
    resize();
  });

  /* Back to top: smooth (instant with reduced motion), then focus the logo for keyboard users */
  $$('a[href="#top"]').forEach((a) => a.addEventListener("click", (e) => {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: reduceMotion.matches ? "auto" : "smooth" });
    $(".logo")?.focus({ preventScroll: true });
    history.replaceState(null, "", location.pathname + location.search);
  }));

  /* Copy e-mail address */
  $$("[data-copy]").forEach((btn) => {
    const status = $("[data-copy-status]");
    btn.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(btn.dataset.copy); if (status) status.textContent = "Copied."; }
      catch (e) { if (status) status.textContent = "Select the address above to copy it."; }
    });
  });
})();
