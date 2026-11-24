/**
 * The one GitHub repository this build takes application updates from.
 *
 * This fork publishes its own builds, so it must never offer, download or
 * install another repository's installer: an update replaces the whole app.
 * `electron-builder.config.mjs` writes the same repository into the packaged
 * feed; `updateSource.test.ts` keeps the two equal.
 */
export const UPDATE_REPOSITORY = 'alefe7z/VoiceStudio';

export const RELEASES_PAGE = `https://github.com/${UPDATE_REPOSITORY}/releases`;
export const RELEASE_DOWNLOAD = `${RELEASES_PAGE}/download`;
export const STABLE_FEED = `${RELEASES_PAGE}/latest/download`;
export const RELEASES_API = `https://api.github.com/repos/${UPDATE_REPOSITORY}/releases`;
