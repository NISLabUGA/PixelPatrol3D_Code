export function getHrTimestamp() {
  return new Date()
    .toISOString()
    .replace(/[:.]/g, '-')
    .replace('T', '_')
    .replace('Z', '');
}

export function detectWebGL() {
  try {
    // OffscreenCanvas is available in workers
    const offscreen = new OffscreenCanvas(1, 1);
    const gl =
      offscreen.getContext('webgl2') ||
      offscreen.getContext('webgl') ||
      offscreen.getContext('experimental-webgl');
    return !!gl;
  } catch (e) {
    return false;
  }
}
