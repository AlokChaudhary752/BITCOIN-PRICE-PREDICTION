/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#07090e",
        surface: "#0c1017",
        "surface-card": "#111722",
        "surface-card-hover": "#172030",
        border: "#1c2638",
        "border-glow": "#2b3850",
        gold: {
          400: "#fbbf24",
          500: "#f59e0b",
          600: "#d97706",
          glow: "rgba(245, 158, 11, 0.2)",
        },
        bullish: {
          DEFAULT: "#10b981",
          light: "#34d399",
          glow: "rgba(16, 185, 129, 0.2)",
        },
        bearish: {
          DEFAULT: "#f43f5e",
          light: "#fb7185",
          glow: "rgba(244, 63, 94, 0.2)",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        mono: ["JetBrains Mono", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
      animation: {
        "pulse-subtle": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "float": "float 6s ease-in-out infinite",
        "shimmer": "shimmer 2s infinite linear",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      boxShadow: {
        gold: "0 0 25px rgba(245, 158, 11, 0.15)",
        emerald: "0 0 25px rgba(16, 185, 129, 0.15)",
        rose: "0 0 25px rgba(244, 63, 94, 0.15)",
        glass: "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
      },
    },
  },
  plugins: [],
};
