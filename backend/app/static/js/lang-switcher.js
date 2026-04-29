/**
 * lang-switcher.js — Vue 3 island for the language switcher in the header.
 */
document.addEventListener('DOMContentLoaded', () => {
  const el = document.getElementById('lang-switcher-app');
  if (!el) return;

  const currentLang = el.dataset.currentLang || 'ua';
  const langs = JSON.parse(el.dataset.langs || '["ua","en","ru","de"]');

  const { createApp } = Vue;
  createApp({
    data() {
      return { currentLang, langs };
    },
    methods: {
      switchLang(lang) {
        const url = new URL(window.location.href);
        url.searchParams.set('lang', lang);
        window.location.href = url.toString();
      },
    },
    template: `
      <div class="lang-switcher d-flex gap-1">
        <button
          v-for="lang in langs"
          :key="lang"
          class="btn btn-sm"
          :class="lang === currentLang ? 'btn-light' : 'btn-outline-light'"
          @click="switchLang(lang)"
        >{{ lang.toUpperCase() }}</button>
      </div>
    `,
  }).mount(el);
});
