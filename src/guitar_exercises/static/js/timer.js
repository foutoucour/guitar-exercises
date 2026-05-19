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
  let intervalId = setInterval(render, 100);
  let stopped = false;

  function stop() {
    if (stopped) return;
    stopped = true;
    clearInterval(intervalId);
    intervalId = null;
    render(); // freeze the display at the final value
    if (liveEl) liveEl.classList.add("exercise-timer-live--stopped");
  }

  window.addEventListener("beforeunload", stop);

  ns.timer = {
    getElapsedMs: elapsedMs,
    rootEl: root,
    stop: stop,
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

  // Stop ticking once there is no answerable form left on the page. Each
  // exercise's feedback fragment replaces the form, so when no
  // `form[hx-post]` remains we know the player has finished this question
  // (or, for chord-notes, this whole chord) and is awaiting the next page.
  document.addEventListener("htmx:afterSwap", function () {
    if (stopped) return;
    if (!document.querySelector("form[hx-post]")) stop();
  });

  // --- auto-advance toggle ----------------------------------------------
  //
  // The toggle is a checkbox rendered by _timer.html. State is mirrored to
  // a cookie so it survives navigation between questions. The actual
  // suppression of the 1.2s advance is done in auto-advance.js, which
  // consults `ns.isAutoAdvanceEnabled()` before scheduling.
  const AUTO_ADVANCE_COOKIE = "auto_advance";

  function readCookie(name) {
    const prefix = name + "=";
    const parts = (document.cookie || "").split(";");
    for (let i = 0; i < parts.length; i += 1) {
      const c = parts[i].trim();
      if (c.indexOf(prefix) === 0) return c.substring(prefix.length);
    }
    return null;
  }

  ns.isAutoAdvanceEnabled = function () {
    // Default is "on" when the cookie is missing.
    return readCookie(AUTO_ADVANCE_COOKIE) !== "0";
  };

  const toggle = root.querySelector("[data-auto-advance-toggle]");
  if (toggle) {
    // Reflect the persisted value into the checkbox (the server-rendered
    // state may be stale if the player toggled it in another tab).
    toggle.checked = ns.isAutoAdvanceEnabled();
    toggle.addEventListener("change", function () {
      const value = toggle.checked ? "1" : "0";
      // Path matches the cookie path the server uses for the other
      // per-exercise cookies, so a single toggle covers every exercise.
      document.cookie = AUTO_ADVANCE_COOKIE + "=" + value
        + "; path=/exercises; max-age=86400; samesite=lax";
    });
  }
})();
