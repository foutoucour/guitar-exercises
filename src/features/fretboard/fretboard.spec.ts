import { describe, it, expect } from 'vitest'
import { getNoteAtPosition, isCorrectAnswer } from './fretboard'

describe('getNoteAtPosition', () => {
  describe('open strings (fret 0)', () => {
    it('string 1 returns E', () => expect(getNoteAtPosition(1, 0)).toBe('E'))
    it('string 2 returns B', () => expect(getNoteAtPosition(2, 0)).toBe('B'))
    it('string 3 returns G', () => expect(getNoteAtPosition(3, 0)).toBe('G'))
    it('string 4 returns D', () => expect(getNoteAtPosition(4, 0)).toBe('D'))
    it('string 5 returns A', () => expect(getNoteAtPosition(5, 0)).toBe('A'))
    it('string 6 returns E', () => expect(getNoteAtPosition(6, 0)).toBe('E'))
  })

  describe('fretted notes', () => {
    it('string 5 fret 2 returns B', () => expect(getNoteAtPosition(5, 2)).toBe('B'))
    it('string 1 fret 5 returns A', () => expect(getNoteAtPosition(1, 5)).toBe('A'))
    it('string 6 fret 5 returns A', () => expect(getNoteAtPosition(6, 5)).toBe('A'))
    it('string 3 fret 4 returns B', () => expect(getNoteAtPosition(3, 4)).toBe('B'))
    it('string 4 fret 2 returns E', () => expect(getNoteAtPosition(4, 2)).toBe('E'))
    it('string 2 fret 1 returns C', () => expect(getNoteAtPosition(2, 1)).toBe('C'))
    it('string 6 fret 1 returns F', () => expect(getNoteAtPosition(6, 1)).toBe('F'))
    it('string 6 fret 11 wraps correctly to D#', () => expect(getNoteAtPosition(6, 11)).toBe('D#'))
  })
})

describe('isCorrectAnswer', () => {
  it('returns true for exact match', () => {
    expect(isCorrectAnswer('A', 5, 0)).toBe(true)
  })

  it('returns true for lowercase input', () => {
    expect(isCorrectAnswer('a', 5, 0)).toBe(true)
  })

  it('returns true for lowercase sharp', () => {
    // String 5 fret 4: A(9)+4=13%12=1=C#
    expect(isCorrectAnswer('c#', 5, 4)).toBe(true)
  })

  it('returns true for flat enharmonic equivalent (Bb = A#)', () => {
    // String 6 fret 6: E(4)+6=10=A#
    expect(isCorrectAnswer('Bb', 6, 6)).toBe(true)
    expect(isCorrectAnswer('bb', 6, 6)).toBe(true)
  })

  it('returns true for flat enharmonic Db = C#', () => {
    // String 5 fret 4: A(9)+4=13%12=1=C#
    expect(isCorrectAnswer('Db', 5, 4)).toBe(true)
  })

  it('returns true with surrounding whitespace', () => {
    expect(isCorrectAnswer('  A  ', 5, 0)).toBe(true)
  })

  it('returns false for wrong note', () => {
    expect(isCorrectAnswer('B', 5, 0)).toBe(false)
  })

  it('returns false for empty input', () => {
    expect(isCorrectAnswer('', 5, 0)).toBe(false)
  })
})
