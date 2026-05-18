// Live answer-timer for every exercise page.
//
// Responsibilities:
//   1. Tick the visible `0.0s` element so the player can see their time grow.
//   2. Inject `elapsed_ms` into every HTMX form submission on the page so the
//      server can echo it back in the feedback fragment and store it in the
//      per-exercise history cookie.
//   3. Keep ticking through the chord-notes multi-string flow (one timer per
//      chord — does NOT reset between strings) and stop only once the page is
//      about to navigate away.
//
// Exposed on window.GuitarExercises.timer so other scripts (e.g. chord-notes.js
// for the "final string" signal) can read the elapsed time.
(function () {
  "use strict";

  const ns = window.GuitarExercises || (window.GuitarExercises = {});

  const root = document.querySelector("[data-timer-root]");
  if (!root) return;

  const liveEl = root.querySelector("[data-timer-live]");
  const startedAt = (typeof performance !== "undefined" && performance.now)
    ? performance.now()
    : Date.now();

  function elapsedMs() {
    const now = (typeof performance !== "undefined" && performance.now)
      ? performance.now()
      : Date.now();
    return Math.max(0, Math.round(now - startedAt));
  }

  function render() {
    if (!liveEl) return;
    const seconds = elapsedMs() / 1000;
    liveEl.textContent = seconds.toFixed(1) + "s";
  }

  render();
  // ~10fps is enough for a single-decimal display and easy on the CPU.
  const intervalId = setInterval(render, 100);
  window.addEventListener("beforeunload", function () {
    clearInterval(intervalId);
  });

  ns.timer = {
    getElapsedMs: elapsedMs,
    rootEl: root,
  };

  // Inject `elapsed_ms` into every HTMX submission from this page. Using
  // configRequest (rather than a hidden form field) means we measure the
  // moment of submit, which is more accurate than the moment of page load
  // plus the user's click-to-submit lag — and it works for forms that are
  // swapped in by HTMX after the initial render.
  document.addEventListener("htmx:configRequest", function (event) {
    const params = event.detail && event.detail.parameters;
    if (!params) return;
    params.elapsed_ms = elapsedMs();
  });
})();
