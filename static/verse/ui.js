/* UI preferences only. Authentication and roles always come from Django. */
(() => {
  const root = document.documentElement;
  const toggle = document.getElementById('theme-toggle');
  function applyTheme(theme) {
    root.dataset.theme = theme;
    toggle?.setAttribute('aria-pressed', String(theme === 'dark'));
    toggle?.setAttribute('aria-label', theme === 'dark' ? '切换到浅色主题' : '切换到深色主题');
    window.dispatchEvent(new Event('themechange'));
  }
  try {
    const saved = localStorage.getItem('verse-theme');
    if (saved === 'light' || saved === 'dark') applyTheme(saved);
  } catch (_) { /* Preference storage can be disabled. */ }
  toggle?.addEventListener('click', () => {
    const dark = root.dataset.theme === 'dark' || (!root.dataset.theme && matchMedia('(prefers-color-scheme: dark)').matches);
    const theme = dark ? 'light' : 'dark';
    applyTheme(theme);
    try { localStorage.setItem('verse-theme', theme); } catch (_) {}
  });
  document.querySelectorAll('.magic').forEach(card => card.addEventListener('pointermove', event => {
    const rect = card.getBoundingClientRect();
    card.style.setProperty('--mx', `${event.clientX - rect.left}px`);
    card.style.setProperty('--my', `${event.clientY - rect.top}px`);
  }));
  const errors = document.querySelector('.verse-errors');
  if (errors) { errors.tabIndex = -1; errors.focus(); }
  // Legacy prototype links map to actual server pages; no client-side login state.
  const legacy = { '#home': '/', '#login': '/login/', '#register': '/register/', '#forgot': '/forgot-password/', '#profile': '/account/', '#settings': '/account/', '#settings.profile': '/account/', '#settings.password': '/account/password/' };
  if (location.pathname === '/' && legacy[location.hash]) location.replace(legacy[location.hash]);
})();
