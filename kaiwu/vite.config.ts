import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  css: {
    postcss: {},
  },
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
      '/project-files': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
      '/project-images': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
      '/project-image-previews': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
    },
  },
});
