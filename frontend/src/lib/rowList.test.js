// The row reducer the resource list uses, and the small field helpers.
import { describe, expect, it } from 'vitest'

import { blankToNull, integerOrNull, keyed, rowsReducer, splitAliases } from './rowList'

const rows = (...names) => names.map((name) => keyed({ name }))
const namesOf = (list) => list.map((row) => row.name)

describe('rowsReducer', () => {
  it('adds a row with a key', () => {
    const next = rowsReducer([], { type: 'add', row: { name: 'a' } })
    expect(namesOf(next)).toEqual(['a'])
    expect(next[0]._key).toBeTruthy()
  })

  it('updates one row and leaves the others the same objects', () => {
    const before = rows('a', 'b')
    const next = rowsReducer(before, { type: 'update', index: 1, patch: { name: 'B' } })
    expect(namesOf(next)).toEqual(['a', 'B'])
    expect(next[0]).toBe(before[0])
  })

  it('removes by index', () => {
    expect(namesOf(rowsReducer(rows('a', 'b', 'c'), { type: 'remove', index: 1 }))).toEqual(['a', 'c'])
  })

  it('moves a row up and down, carrying its key', () => {
    const before = rows('a', 'b', 'c')
    const up = rowsReducer(before, { type: 'move', from: 2, to: 1 })
    expect(namesOf(up)).toEqual(['a', 'c', 'b'])
    expect(up[1]._key).toBe(before[2]._key)
    expect(namesOf(rowsReducer(before, { type: 'move', from: 0, to: 1 }))).toEqual(['b', 'a', 'c'])
  })

  it('does not wrap a move off either end', () => {
    const before = rows('a', 'b')
    expect(rowsReducer(before, { type: 'move', from: 0, to: -1 })).toBe(before)
    expect(rowsReducer(before, { type: 'move', from: 1, to: 2 })).toBe(before)
  })
})

describe('splitAliases', () => {
  it('splits on every separator the box accepts, trimming', () => {
    expect(splitAliases('a, b，c、d\n e ')).toEqual(['a', 'b', 'c', 'd', 'e'])
  })

  it('drops empties and case-insensitive repeats, keeping the first spelling', () => {
    expect(splitAliases('Hand,, hand ,、HAND,foot')).toEqual(['Hand', 'foot'])
  })

  it('answers an empty list for nothing typed', () => {
    expect(splitAliases('')).toEqual([])
    expect(splitAliases(null)).toEqual([])
  })
})

describe('field helpers', () => {
  it('treats a blank as absent', () => {
    expect(blankToNull('  ')).toBeNull()
    expect(blankToNull(' x ')).toBe('x')
  })

  it('reads an integer or nothing', () => {
    expect(integerOrNull('')).toBeNull()
    expect(integerOrNull('3')).toBe(3)
    expect(integerOrNull('abc')).toBeNull()
  })
})
