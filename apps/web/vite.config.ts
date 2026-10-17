import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@shared": path.resolve(__dirname, "../../packages/shared/src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        ws: true,
      },
      "/ws": {
        target: "ws://127.0.0.1:8000",
        changeOrigin: true,
        ws: true,
      },
    },
  },
  build: {
    target: "esnext",
    minify: "esbuild",
    rollupOptions: {
      output: {
        manualChunks: {
          three: ["three"],
          charts: ["lightweight-charts", "recharts"],
          motion: ["framer-motion"],
          react: ["react", "react-dom", "react-router-dom"],
        },
      },
    },
  },
});
