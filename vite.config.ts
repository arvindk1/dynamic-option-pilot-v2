/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'http://localhost:8000',
        ws: true,
        changeOrigin: true,
      }
    },
    // Performance optimizations for dev server
    hmr: {
      overlay: false // Reduce overlay render overhead
    },
    fs: {
      strict: false // Allow serving files outside of workspace
    }
  },
  // Development-specific optimizations
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      '@tanstack/react-query',
      'lucide-react',
      'recharts',
      'lodash',
      'date-fns',
      'clsx',
      'class-variance-authority'
    ],
    exclude: ['@radix-ui/react-*'] // Exclude large UI libraries from pre-bundling
  },
  esbuild: {
    target: 'es2020', // Use modern JS for faster builds
    logOverride: { 'this-is-undefined-in-esm': 'silent' },
    minifyIdentifiers: mode === 'production',
    minifySyntax: mode === 'production'
  },
  plugins: [
    react(),
    mode === 'development' &&
    componentTagger(),
  ].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    target: 'es2020', // Modern JS for smaller builds
    chunkSizeWarningLimit: 800,
    minify: 'esbuild', // Faster than Terser
    sourcemap: mode === 'development',
    cssCodeSplit: true, // Enable CSS code splitting
    // Optimize assets
    assetsDir: 'assets',
    reportCompressedSize: false, // Skip compressed size reporting for faster builds
    rollupOptions: {
      // Optimize imports
      external: mode === 'production' ? [] : undefined,
      output: {
        // Optimize chunk splitting for better caching
        manualChunks: (id) => {
          // Core React ecosystem (highest priority - cache longest)
          if (id.includes('react') || id.includes('react-dom')) {
            return 'react-core';
          }
          
          // React ecosystem extensions
          if (id.includes('@tanstack/react-query') || id.includes('react-router')) {
            return 'react-ecosystem';
          }
          
          // UI Framework - split by usage frequency
          if (id.includes('@radix-ui')) {
            return 'radix-ui';
          }
          
          // Large visualization libraries
          if (id.includes('recharts') || id.includes('d3-')) {
            return 'charts';
          }
          
          // Icons (used everywhere)
          if (id.includes('lucide-react')) {
            return 'icons';
          }
          
          // Utility libraries
          if (id.includes('lodash') || id.includes('date-fns') || id.includes('clsx')) {
            return 'utils';
          }
          
          // Trading-specific components (business logic)
          if (id.includes('components/Trading') || 
              id.includes('components/OptimizedTrading') ||
              id.includes('components/TradeCard') ||
              id.includes('components/Strategies')) {
            return 'trading-core';
          }
          
          // Lazy-loaded components
          if (id.includes('components/Lazy') || 
              id.includes('LazyTab')) {
            return 'lazy-components';
          }
          
          // Services and utilities
          if (id.includes('services/') || id.includes('utils/')) {
            return 'services';
          }
          
          // Contexts and hooks
          if (id.includes('contexts/') || id.includes('hooks/')) {
            return 'app-state';
          }
          
          // Remaining node_modules
          if (id.includes('node_modules')) {
            const chunks = id.split('/');
            const packageName = chunks[chunks.indexOf('node_modules') + 1];
            // Group by package family
            if (packageName.startsWith('@radix-ui')) return 'radix-ui';
            if (packageName.includes('react')) return 'react-ecosystem';
            return 'vendor';
          }
        },
        // Optimize file names for caching
        entryFileNames: 'assets/[name].[hash].js',
        chunkFileNames: 'assets/[name].[hash].js',
        assetFileNames: 'assets/[name].[hash].[ext]'
      }
    }
  },
  // Test configuration
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/test/**',
        'src/**/*.test.{ts,tsx}',
        'src/**/*.d.ts',
        'src/main.tsx'
      ]
    }
  }
}));
