import { expect, it } from 'vitest';
import { MAX_VARIATIONS, planVariations, variationCount } from './generate-variations';

it('keeps a single take on the default path with no explicit seed', () => {
  expect(planVariations(1, null)).toEqual([undefined]);
  expect(planVariations(0, null)).toEqual([undefined]);
  expect(planVariations(Number.NaN, null)).toEqual([undefined]);
});

it('gives each variation a distinct seed and caps the count', () => {
  let n = 0;
  const repeating = () => [0.1, 0.1, 0.2, 0.3, 0.4, 0.5][n++ % 6];
  const seeds = planVariations(3, { kind: 'clone' } as never, repeating);
  expect(seeds).toHaveLength(3);
  expect(new Set(seeds).size).toBe(3);
  expect(planVariations(99, null)).toHaveLength(MAX_VARIATIONS);
  for (const seed of planVariations(2, null)) expect(Number.isInteger(seed)).toBe(true);
});

it('never varies a designed voice, whose seed is its identity', () => {
  expect(planVariations(4, { kind: 'design' } as never)).toEqual([undefined]);
});

it('counts takes without drawing seeds', () => {
  expect(variationCount(3, null)).toBe(3);
  expect(variationCount(3, { kind: 'design' } as never)).toBe(1);
  expect(variationCount(-2, { kind: 'clone' } as never)).toBe(1);
});

it('still returns distinct seeds from a constant random source', () => {
  const seeds = planVariations(4, null, () => 0.25);
  expect(new Set(seeds).size).toBe(4);
});
