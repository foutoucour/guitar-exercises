import { ref } from 'vue'
import { getNoteAtPosition, isCorrectAnswer } from './fretboard'

export type AnswerResult = 'correct' | 'wrong' | null

function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

export function useFretboardExercise() {
  const currentString = ref(randomInt(1, 6))
  const currentFret = ref(randomInt(0, 11))
  const streak = ref(0)
  const lastResult = ref<AnswerResult>(null)
  const correctNote = ref('')

  function nextQuestion(): void {
    currentString.value = randomInt(1, 6)
    currentFret.value = randomInt(0, 11)
    lastResult.value = null
    correctNote.value = ''
  }

  function submitAnswer(input: string): void {
    if (isCorrectAnswer(input, currentString.value, currentFret.value)) {
      streak.value++
      lastResult.value = 'correct'
      correctNote.value = ''
    } else {
      correctNote.value = getNoteAtPosition(currentString.value, currentFret.value)
      streak.value = 0
      lastResult.value = 'wrong'
    }
  }

  return {
    currentString,
    currentFret,
    streak,
    lastResult,
    correctNote,
    submitAnswer,
    nextQuestion,
  }
}
