/* WaveAssure appearance preferences: display only, never modify research samples. */
(() => {
  'use strict';
  const root = document.documentElement;
  const KEY_THEME = 'waveassure.theme.v1';
  const KEY_MOTION = 'waveassure.motion.v1';
  const query = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)');
  const reducedQuery = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');
  function read(key, fallback) {
    try { return window.localStorage.getItem(key) || fallback; } catch (_) { return fallback; }
  }
  function save(key, value) {
    try { window.localStorage.setItem(key, value); } catch (_) { /* Browser storage may be disabled. */ }
  }
  const initialTheme = read(KEY_THEME, 'system');
  const initialMotion = read(KEY_MOTION, 'off');
  let preference = ['system', 'light', 'dark'].includes(initialTheme) ? initialTheme : 'system';
  let motionPreference = ['on', 'off'].includes(initialMotion) ? initialMotion : 'on';
  function apply() {
    const actual = preference === 'system' ? (query && query.matches ? 'dark' : 'light') : preference;
    const reduced = Boolean(reducedQuery && reducedQuery.matches);
    root.dataset.theme = actual;
    root.dataset.themePreference = preference;
    root.dataset.motion = motionPreference === 'off' || reduced ? 'off' : 'on';
    root.style.colorScheme = actual;
    const themeSelect = document.getElementById('themeSelect');
    if (themeSelect) themeSelect.value = preference;
    const motion = document.getElementById('motionToggle');
    if (motion) {
      const enabled = root.dataset.motion === 'on';
      motion.setAttribute('aria-pressed', String(enabled));
      motion.setAttribute('aria-label', enabled ? 'Turn interface effects off (recording replay unaffected)' : 'Turn interface effects on (recording replay unaffected)');
      motion.setAttribute('title', reduced ? 'Interface effects disabled by accessibility preference; waveform replay still works' : (enabled ? 'Disable decorative UI transitions; waveform replay unaffected' : 'Enable decorative UI transitions; waveform replay unaffected'));
      const label = motion.querySelector('[data-motion-label]');
      if (label) label.textContent = enabled ? 'UI effects on' : 'UI effects off';
      motion.disabled = reduced;
    }
    window.dispatchEvent(new CustomEvent('waveassure:appearance', { detail: { theme: actual, motion: root.dataset.motion } }));
  }
  function ready() {
    const select = document.getElementById('themeSelect');
    if (select) select.addEventListener('change', event => {
      if (!['system', 'light', 'dark'].includes(event.target.value)) return;
      preference = event.target.value;
      save(KEY_THEME, preference);
      apply();
    });
    const motion = document.getElementById('motionToggle');
    if (motion) motion.addEventListener('click', () => {
      if (reducedQuery && reducedQuery.matches) return;
      motionPreference = motionPreference === 'on' ? 'off' : 'on';
      save(KEY_MOTION, motionPreference);
      apply();
    });
    apply();
  }
  // Apply before first paint to avoid a flash of the wrong theme.
  apply();
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready, { once: true });
  else ready();
  if (query) query.addEventListener('change', () => { if (preference === 'system') apply(); });
  if (reducedQuery) reducedQuery.addEventListener('change', apply);
})();
