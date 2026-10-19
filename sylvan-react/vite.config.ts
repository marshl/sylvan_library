import { reactRouter } from '@react-router/dev/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';
import tsconfigPaths from 'vite-tsconfig-paths';
import path from 'path';

const DJANGO_BACKEND = process.env.DJANGO_BACKEND || 'http://localhost:8000';

// React Router requires Vite's `base` to be a prefix of `basename`.
// - In dev, the app is served at http://localhost:5173/, so base == basename.
// - In prod, Django's built HTML lives under /static/react/, but the app is served at /;
//   at build time we set base to /static/react/ so hashed asset URLs resolve through
//   Django's staticfiles handler.  The dev-only prefix check doesn't run at build time.
//   `npm run build` copies build/client into the Django frontend app's static dir.
export default defineConfig(({ command }) => ({
  plugins: [reactRouter(), tailwindcss(), tsconfigPaths()],
  root: path.resolve(__dirname),
  base: command === 'serve' ? '/' : '/static/react/',
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': { target: DJANGO_BACKEND, changeOrigin: true },
      '/static': { target: DJANGO_BACKEND, changeOrigin: true },
      '/api-auth': { target: DJANGO_BACKEND, changeOrigin: true },
      '/admin': { target: DJANGO_BACKEND, changeOrigin: true },
    },
  },
}));
