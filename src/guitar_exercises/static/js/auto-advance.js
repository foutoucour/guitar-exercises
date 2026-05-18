// Shared auto-advance helper used by every exercise.
//
// One place to change the delay; one place to change the navigation pattern.
// Exposed on window.GuitarExercises so feedback fragments and exercise
// scripts can call it without bundling.
(function () {
  "use strict";

  const ns = window.GuitarExercises || (window.GuitarExercises = {});

  // Wait time between a correct answer and the next exercise. Tune here to
  // change the cadence across the whole site.
  ns.autoAdvanceMs = 1200;

  // Schedule a navigation to `url` after the shared delay.
  ns.advanceTo = function (url) {
    if (typeof url !== "string" || url.length === 0) return;
    setTimeout(function () {
      window.location.assign(url);
    }, ns.autoAdvanceMs);
  };

  // Arm a one-shot Enter/Space key listener that navigates to `url`. Used on
  // failure feedback so keyboard players can move on without grabbing the mouse.
  // Calling this again replaces any previously-armed listener.
  ns.armKeyAdvance = function (url) {
    if (typeof url !== "string" || url.length === 0) return;
    if (ns._keyAdvanceHandler) {
      document.removeEventListener("keydown", ns._keyAdvanceHandler);
      ns._keyAdvanceHandler = null;
    }
    function isTypingTarget(el) {
      if (!el || !el.tagName) return false;
      const tag = el.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
      return el.isContentEditable === true;
    }
    ns._keyAdvanceHandler = function (event) {
      if (event.defaultPrevented) return;
      const isEnter = event.key === "Enter";
      const isSpace = event.key === " " || event.code === "Space";
      if (!isEnter && !isSpace) return;
      if (isTypingTarget(event.target)) return;
      event.preventDefault();
      document.removeEventListener("keydown", ns._keyAdvanceHandler);
      ns._keyAdvanceHandler = null;
      window.location.assign(url);
    };
    document.addEventListener("keydown", ns._keyAdvanceHandler);
  };

  // Pick up [data-key-advance="<url>"] from any element htmx swaps in and arm
  // the key listener. This is the failure-feedback path: an inline <script>
  // inside the swapped fragment is unreliable across htmx configs, so the
  // server marks the wrapper with a data attribute and we react to the swap.
  function scanAndArm(root) {
    if (!root || root.nodeType !== 1) return;
    let el = null;
    if (root.matches && root.matches("[data-key-advance]")) el = root;
    if (!el && root.querySelector) el = root.querySelector("[data-key-advance]");
    if (!el) return;
    const url = el.getAttribute("data-key-advance");
    if (url) ns.armKeyAdvance(url);
  }
  document.addEventListener("htmx:afterSwap", function (event) {
    scanAndArm(event.target);
  });
})();
