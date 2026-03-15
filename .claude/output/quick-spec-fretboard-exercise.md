# Quick Spec: Guitar Fretboard Note Identification Exercise

**Date**: 2026-03-15
**Scope**: 5 files, 1 feature module (pure frontend, no backend)

## Tasks

### 1. Scaffold the Vite + Vue 3 + TypeScript project

- **Files**: `package.json`, `vite.config.ts`, `tsconfig.json`, `index.html`, `src/main.ts` (create)
- **What**: Init a Vite project with `vue-ts` template. Add Vitest for unit tests.
- **Acceptance**:
  - Given a fresh clone, when `npm install && npm run dev` is run, then a blank Vue app loads at `localhost:5173`
  - Given `npm test` is run, then Vitest finds and runs test files

---

### 2. Fretboard logic module

- **Files**: `src/features/fretboard/fretboard.ts` (create), `src/features/fretboard/fretboard.spec.ts` (create)
- **What**: Pure functions — no state, no UI.
  - `getNoteAtPosition(string: 1–6, fret: 0–11): string` — returns the note name (e.g. `"A"`, `"C#"`)
  - `isCorrectAnswer(input: string, string: number, fret: number): boolean` — case-insensitive, trims whitespace, accepts both `C#` and `Db` as equivalent (enharmonic)
  - Standard tuning open notes: `[E, A, D, G, B, E]` (strings 6→1)
  - Chromatic scale: `C C# D D# E F F# G G# A A# B`
- **Acceptance**:
  - Given string=6, fret=0, then `getNoteAtPosition` returns `"E"`
  - Given string=5, fret=2, then returns `"B"`
  - Given string=1, fret=5, then returns `"A"`
  - Given input `"c#"` for a C# position, then `isCorrectAnswer` returns `true`

---

### 3. Exercise composable

- **Files**: `src/features/fretboard/useFretboardExercise.ts` (create)
- **What**: Reactive state + logic using Vue `ref`/`computed`.
  - State: `currentString`, `currentFret`, `streak`, `lastResult` (`'correct' | 'wrong' | null`)
  - `submitAnswer(input: string): void` — validates answer, increments or resets streak, generates next question
  - `nextQuestion(): void` — picks random string (1–6) and fret (0–11)
- **Acceptance**:
  - Given a correct answer, when `submitAnswer` is called, then `streak` increments and `lastResult` is `'correct'`
  - Given a wrong answer, when `submitAnswer` is called, then `streak` resets to 0 and `lastResult` is `'wrong'`
  - Given `nextQuestion`, then `currentString` and `currentFret` are updated to new random values

---

### 4. FretboardExercise component

- **Files**: `src/features/fretboard/FretboardExercise.vue` (create)
- **What**: Single Vue SFC. Uses `useFretboardExercise`. Displays:
  - The question: "String **3**, Fret **5**"
  - A text input for the note answer + submit button (also on Enter key)
  - Current streak count
  - Feedback: "Correct!" in green or "Wrong — it was X" in red, auto-clears after 1.5s
- **Acceptance**:
  - Given the component mounts, then a string and fret are shown
  - Given the user types a note and presses Enter or clicks Submit, then feedback appears
  - Given feedback appears, then after 1.5s it disappears and the input clears
  - Given streak ≥ 1, then the streak counter is visible

---

### 5. App shell

- **Files**: `src/App.vue` (create/modify)
- **What**: Minimal shell — page title "Guitar Exercises", renders `<FretboardExercise />`.
- **Acceptance**:
  - Given `npm run dev`, then the exercise is visible and functional in the browser

---

## Testing Strategy

- **Unit tests**: `fretboard.spec.ts` — cover `getNoteAtPosition` for all 6 open strings, a selection of fretted notes, and `isCorrectAnswer` for correct/wrong/case/enharmonic inputs
- **Component tests**: not required for this first iteration — the logic is fully covered by unit tests on the composable and pure functions
- **Manual verification**: open the app, answer a few notes correctly to verify streak increments, answer one wrong to verify streak resets to 0

## Dependencies

- `vue@^3.4.0`
- `vite@^5.0.0`
- `@vitejs/plugin-vue@^5.0.0`
- `vitest@^1.0.0`
- `typescript@^5.3.0`
- `@vue/test-utils@^2.4.0` (optional, for future component tests)

## Notes

- Frets 0–11 only (one octave) keeps the question set manageable; fret 12 is the same as fret 0 and can be added later
- Enharmonic equivalents (C#/Db, D#/Eb, etc.) should be accepted as correct — the `isCorrectAnswer` function handles this with a lookup map
- No routing needed — single page for now; a route layer can be added when a second exercise is introduced
- String numbering: String 1 = high E, String 6 = low E (standard guitar convention)
