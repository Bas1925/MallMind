import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#07090d",
          900: "#0b0e14",
          850: "#10141c",
          800: "#151a23",
          700: "#1e2531",
          600: "#2a3240",
        },
        mist: {
          50: "#f6f4ef",
          200: "#d9d6cf",
          400: "#9aa0ab",
          500: "#7b818c",
        },
        gold: {
          200: "#f8e2b4",
          300: "#f2cf8a",
          400: "#e8b86a",
          500: "#d29a43",
        },
        jade: { 400: "#3ddc97" },
        rose: { 400: "#ff6b81" },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "ui-serif", "Georgia", "serif"],
      },
      boxShadow: {
        glass: "0 1px 0 0 rgba(255,255,255,0.06) inset, 0 20px 50px -12px rgba(0,0,0,0.6)",
        glow: "0 0 0 1px rgba(232,184,106,0.35), 0 8px 30px -6px rgba(232,184,106,0.45)",
      },
    },
  },
  plugins: [],
};

export default config;
