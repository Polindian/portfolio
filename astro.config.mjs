import { defineConfig } from 'astro/config';

// GitHub Pages project site lives at /portfolio.
// When a custom domain is added: set site to the domain and base to '/'.
export default defineConfig({
  site: 'https://polindian.github.io',
  base: '/portfolio',
  markdown: {
    shikiConfig: { theme: 'github-dark' },
  },
});
