import { describe, it, expect } from 'vitest'
import { useFretboardExercise } from './useFretboardExercise'
import { getNoteAtPosition } from './fretboard'

function correctAnswer(ex: ReturnType<typeof useFretboardExercise>): string {
  return getNoteAtPosition(ex.currentString.value, ex.currentFret.value)
}

describe('useFretboardExercise', () => {
  describe('submitAnswer — correct input', () => {
    it('sets lastResult to correct', () => {
      const ex = useFretboardExercise()
      ex.submitAnswer(correctAnswer(ex))
      expect(ex.lastResult.value).toBe('correct')
    })

    it('increments streak', () => {
      const ex = useFretboardExercise()
      ex.submitAnswer(correctAnswer(ex))
      expect(ex.streak.value).toBe(1)
    })

    it('accumulates streak across multiple correct answers', () => {
      const ex = useFretboardExercise()
      ex.submitAnswer(correctAnswer(ex))
      ex.nextQuestion()
      ex.submitAnswer(correctAnswer(ex))
      ex.nextQuestion()
      ex.submitAnswer(correctAnswer(ex))
      expect(ex.streak.value).toBe(3)
    })

    it('clears correctNote', () => {
      const ex = useFretboardExercise()
      ex.submitAnswer(correctAnswer(ex))
      expect(ex.correctNote.value).toBe('')
    })
  })

  describe('submitAnswer — wrong input', () => {
    it('sets lastResult to wrong', () => {
      const ex = useFretboardExercise()
      ex.submitAnswer('X')
      expect(ex.lastResult.value).toBe('wrong')
    })

    it('resets streak to 0', () => {
      const ex = useFretboardExercise()
      ex.submitAnswer(correctAnswer(ex))
      ex.nextQuestion()
      ex.submitAnswer('X')
      expect(ex.streak.value).toBe(0)
    })

    it('sets correctNote to the right answer', () => {
      const ex = useFretboardExercise()
      const expected = correctAnswer(ex)
      ex.submitAnswer('X')
      expect(ex.correctNote.value).toBe(expected)
    })
  })

  describe('nextQuestion', () => {
    it('resets lastResult to null', () => {
      const ex = useFretboardExercise()
      ex.submitAnswer(correctAnswer(ex))
      ex.nextQuestion()
      expect(ex.lastResult.value).toBeNull()
    })

    it('resets correctNote', () => {
      const ex = useFretboardExercise()
      ex.submitAnswer('X')
      ex.nextQuestion()
      expect(ex.correctNote.value).toBe('')
    })

    it('updates currentString and currentFret', () => {
      const ex = useFretboardExercise()
      // Run nextQuestion many times — string and fret must always stay in valid range
      for (let i = 0; i < 20; i++) {
        ex.nextQuestion()
        expect(ex.currentString.value).toBeGreaterThanOrEqual(1)
        expect(ex.currentString.value).toBeLessThanOrEqual(6)
        expect(ex.currentFret.value).toBeGreaterThanOrEqual(0)
        expect(ex.currentFret.value).toBeLessThanOrEqual(11)
      }
    })
  })
})
