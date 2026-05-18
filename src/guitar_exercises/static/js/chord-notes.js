// Keyboard navigation for the "Name the notes" exercise.
//
// Goal: Tab cycles inside the active string's note chips. The next string
// becomes reachable only after the user picks an answer for the current one
// (which submits the form and swaps the row into its answered state).
(function () {
  "use strict";

  const stringList = document.querySelector(".string-list");
  if (!stringList) return;

  function chipsOf(row) {
    return row ? row.querySelector(".note-chips") : null;
  }

  function isPlayable(row) {
    if (!row || !row.classList.contains("string-row")) return false;
    if (row.classList.contains("string-row-answered")) return false;
    return chipsOf(row) !== null;
  }

  function setRowTabbability(row, enabled) {
    const chips = chipsOf(row);
    if (!chips) return;
    chips.querySelectorAll(".note-chip").forEach(function (chip) {
      chip.tabIndex = enabled ? 0 : -1;
    });
  }

  function activate(row, focus) {
    if (!isPlayable(row)) return;
    stringList.querySelectorAll(".string-row").forEach(function (r) {
      if (r !== row) setRowTabbability(r, false);
    });
    setRowTabbability(row, true);
    if (focus) {
      const first = chipsOf(row).querySelector(".note-chip");
      if (first) first.focus();
    }
  }

  function firstPlayableAfter(row) {
    let cur = row.nextElementSibling;
    while (cur) {
      if (isPlayable(cur)) return cur;
      cur = cur.nextElementSibling;
    }
    return null;
  }

  // Initial state is set server-side via tabindex; just make sure exactly one
  // row is active in case the markup ever drifts.
  const playable = Array.from(stringList.querySelectorAll(".string-row")).filter(isPlayable);
  if (playable.length > 0) activate(playable[0], false);

  // Tab/Shift+Tab inside an active row's chip group advances within the group.
  // At the first chip (Shift+Tab) or last chip (Tab) normal browser Tab behaviour
  // is restored so the user can reach other page controls without answering.
  document.addEventListener("keydown", function (event) {
    if (event.key !== "Tab") return;
    const focused = document.activeElement;
    if (!focused || !focused.classList || !focused.classList.contains("note-chip")) return;
    const group = focused.closest(".note-chips");
    if (!group) return;
    const chips = Array.from(group.querySelectorAll(".note-chip"));
    if (chips.length === 0) return;
    const idx = chips.indexOf(focused);
    if (idx === -1) return;
    if (event.shiftKey) {
      if (idx === 0) return; // allow Shift+Tab out at first chip
      event.preventDefault();
      chips[idx - 1].focus();
    } else {
      if (idx === chips.length - 1) return; // allow Tab out at last chip
      event.preventDefault();
      chips[idx + 1].focus();
    }
  });

  function anyIncorrect() {
    return stringList.querySelector(".string-row-incorrect") !== null;
  }

  // After an htmx swap turns a row into its answered state, unlock the next
  // playable string. When every playable string has been answered: if they
  // were all correct, auto-advance to the next chord using the shared
  // delay; otherwise let the user click "New chord" so they can review the
  // mistakes.
  document.body.addEventListener("htmx:afterSwap", function (event) {
    const target = event.target;
    if (!target || !target.classList || !target.classList.contains("string-row")) return;
    const next = firstPlayableAfter(target);
    if (next) {
      activate(next, true);
      return;
    }
    if (!anyIncorrect() && window.GuitarExercises && window.GuitarExercises.advanceTo) {
      window.GuitarExercises.advanceTo("/exercises/chord-notes");
      return;
    }
    const newChord = document.querySelector("a.new-chord");
    if (newChord) newChord.focus();
  });
})();
