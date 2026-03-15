/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "var(--surface)",
        "surface-2": "var(--surface-2)",
        border: "var(--border)",
        accent: "var(--accent)",
      },
      fontFamily: {
        sans: ['"DM Sans"', "system-ui", "-apple-system", "sans-serif"],
        mono: ['"JetBrains Mono"', '"Fira Code"', "monospace"],
      },
      boxShadow: {
        glow: "0 0 20px -4px rgba(99, 102, 241, 0.15)",
        "glow-lg": "0 0 40px -8px rgba(99, 102, 241, 0.2)",
      },
    },
  },
  plugins: [],
};
