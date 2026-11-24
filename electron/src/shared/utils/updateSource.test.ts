import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';
import { RELEASES_API, STABLE_FEED, UPDATE_REPOSITORY } from './updateSource';

const ELECTRON = join(__dirname, '..', '..', '..');

function sources(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return name === 'node_modules' ? [] : sources(path);
    return /\.(ts|tsx|mjs)$/.test(name) && !/\.test\.tsx?$/.test(name) ? [path] : [];
  });
}

describe('update source', () => {
  it("is the fork's own repository", () => {
    expect(UPDATE_REPOSITORY).toBe('alefe7z/VoiceStudio');
    expect(STABLE_FEED).toBe('https://github.com/alefe7z/VoiceStudio/releases/latest/download');
    expect(RELEASES_API).toBe('https://api.github.com/repos/alefe7z/VoiceStudio/releases');
  });

  it('is the repository the packaged feed is built for', () => {
    const config = readFileSync(join(ELECTRON, 'electron-builder.config.mjs'), 'utf8');
    expect(config).toContain(`export const UPDATE_REPOSITORY = '${UPDATE_REPOSITORY}';`);
  });

  it('is the only release source the app reads updates or installers from', () => {
    const stray = sources(join(ELECTRON, 'src'))
      .concat(join(ELECTRON, 'electron-builder.config.mjs'))
      .filter((path) =>
        /(?:github\.com|api\.github\.com\/repos)\/(?!alefe7z\/)[^/'"`\s]+\/VoiceStudio\/releases/.test(
          readFileSync(path, 'utf8'),
        ),
      )
      .map((path) => relative(ELECTRON, path));
    expect(stray).toEqual([]);
  });
});
