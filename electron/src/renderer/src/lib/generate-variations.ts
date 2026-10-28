import type { Profile } from '@/lib/api/types';

export const MAX_VARIATIONS = 4;

/** How many takes one click renders: 1–4, and always 1 for a designed voice. */
export function variationCount(
  requested: number,
  profile: Pick<Profile, 'kind'> | null | undefined,
): number {
  const count = Math.min(MAX_VARIATIONS, Math.max(1, Math.round(requested) || 1));
  return profile?.kind === 'design' ? 1 : count;
}

/**
 * Seeds for one click's takes. Each variation gets its own random seed so the
 * engine samples a different delivery of the same voice. A designed voice is
 * defined by its seed, so it is never varied: one take, its own seed.
 */
export function planVariations(
  requested: number,
  profile: Pick<Profile, 'kind'> | null | undefined,
  random: () => number = Math.random,
): (number | undefined)[] {
  const count = variationCount(requested, profile);
  if (count === 1) return [undefined];
  const seeds = new Set<number>();
  for (let draws = 0; seeds.size < count && draws < count * 16; draws++)
    seeds.add(Math.floor(random() * 2 ** 31));
  // A degenerate random source still yields distinct seeds, never a hang.
  for (let next = 0; seeds.size < count; next++) seeds.add(next);
  return [...seeds];
}
