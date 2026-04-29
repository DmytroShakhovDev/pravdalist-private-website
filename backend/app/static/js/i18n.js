/**
 * i18n.js — client-side fetch of localization strings from /api/v1/i18n
 */
window.i18n = {
  _cache: {},

  async load(page, lang) {
    const key = `${page}:${lang}`;
    if (this._cache[key]) return this._cache[key];
    const resp = await fetch(`/api/v1/i18n/${page}/${lang}`);
    if (!resp.ok) return {};
    const data = await resp.json();
    this._cache[key] = data;
    return data;
  },

  t(strings, key) {
    const parts = key.split('.');
    let node = strings;
    for (const part of parts) {
      if (node && typeof node === 'object' && part in node) {
        node = node[part];
      } else {
        return key;
      }
    }
    return String(node);
  },
};
