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

  // Tab/Shift+Tab inside an active row's chip group cycles within the group.
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
    const dir = event.shiftKey ? -1 : 1;
    const next = chips[(idx + dir + chips.length) % chips.length];
    event.preventDefault();
    next.focus();
  });

  // After an htmx swap turns a row into its answered state, unlock the next
  // playable string (or the "New chord" link if there are no more).
  document.body.addEventListener("htmx:afterSwap", function (event) {
    const target = event.target;
    if (!target || !target.classList || !target.classList.contains("string-row")) return;
    const next = firstPlayableAfter(target);
    if (next) {
      activate(next, true);
      return;
    }
    const newChord = document.querySelector("a.new-chord");
    if (newChord) newChord.focus();
  });
})();
