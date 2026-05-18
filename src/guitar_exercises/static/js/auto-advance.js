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
})();
