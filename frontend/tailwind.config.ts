import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#f6f7f4",
          900: "#ffffff",
          850: "#f4f6f2",
          800: "#ffffff",
          700: "#e9efea",
          600: "#d6dfd8",
        },
        mist: {
          50: "#203a32",
          200: "#3f514b",
          300: "#50625b",
          400: "#66756e",
          500: "#6b7872",
        },
        gold: {
          200: "#245d49",
          300: "#226b51",
          400: "#176b52",
          500: "#12553f",
        },
        jade: { 400: "#176b52" },
        rose: { 400: "#b34850" },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glass: "0 8px 30px -12px rgba(29,55,43,0.15)",
        glow: "0 2px 4px rgba(29,55,43,0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
