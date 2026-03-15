const CHROMATIC_SCALE = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'] as const

// Open string note indices (string 1 = high E, string 6 = low E)
const OPEN_STRING_NOTE_INDEX: Record<number, number> = {
  1: 4, // E
  2: 11, // B
  3: 7, // G
  4: 2, // D
  5: 9, // A
  6: 4, // E
}

// Maps flat notation to its sharp equivalent for enharmonic acceptance
const ENHARMONIC_TO_SHARP: Record<string, string> = {
  Db: 'C#',
  Eb: 'D#',
  Fb: 'E',
  Gb: 'F#',
  Ab: 'G#',
  Bb: 'A#',
  Cb: 'B',
}

export function getNoteAtPosition(string: number, fret: number): string {
  const openIndex = OPEN_STRING_NOTE_INDEX[string]
  return CHROMATIC_SCALE[(openIndex + fret) % 12]
}

function normalizeInput(input: string): string {
  const trimmed = input.trim()
  if (trimmed.length === 0) return ''
  // Capitalize first letter, lowercase the rest (handles "c#" → "C#", "db" → "Db")
  const normalized = trimmed[0].toUpperCase() + trimmed.slice(1).toLowerCase()
  return ENHARMONIC_TO_SHARP[normalized] ?? normalized
}

export function isCorrectAnswer(input: string, string: number, fret: number): boolean {
  const correct = getNoteAtPosition(string, fret)
  return normalizeInput(input) === correct
}
