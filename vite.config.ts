import path from 'path';
import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv } from 'vite';
import { cardmarketMiddleware } from './server/cardmarket';

export default defineConfig(({ mode }) => {
  const key = process.env.PTCG_API_KEY || loadEnv(mode, process.cwd(), '').PTCG_API_KEY || '';
  const middleware = cardmarketMiddleware(key);
  return {
  plugins: [react(), { name: 'cardmarket-prices', configureServer(server) { server.middlewares.use(middleware); }, configurePreviewServer(server) { server.middlewares.use(middleware); } }],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
}; });
