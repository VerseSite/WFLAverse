module.exports = {
  content: ['./templates/**/*.html', './static/verse/ui.js', './static/verse/campus.js'],
  theme: {
    extend: {
      colors: { ink: 'var(--ink)', muted: 'var(--muted)', line: 'var(--line)', lav: 'var(--lav)', sky: 'var(--sky)', accent: 'var(--accent)', surface: 'var(--surface)' },
      borderRadius: { '4xl': '2rem', '5xl': '2.5rem' },
    },
  },
};
