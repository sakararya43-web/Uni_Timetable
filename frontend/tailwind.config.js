/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: "var(--color-paper)",
        "paper-2": "var(--color-paper-2)",
        "paper-3": "var(--color-paper-3)",
        ink: "var(--color-ink)",
        "ink-2": "var(--color-ink-2)",
        muted: "var(--color-muted)",
        rule: "var(--color-rule)",
        "rule-dark": "var(--color-rule-dark)",
        accent: {
          DEFAULT: "var(--color-accent)",
          deep: "var(--color-accent-deep)",
          soft: "var(--color-accent-soft)",
          ink: "var(--color-accent-ink)",
        },
        signal: {
          DEFAULT: "var(--color-signal)",
          soft: "var(--color-signal-soft)",
        },
        brand: {
          50: "oklch(96% 0.02 260)",
          100: "oklch(92% 0.035 260)",
          200: "oklch(82% 0.06 260)",
          300: "oklch(68% 0.10 260)",
          400: "oklch(52% 0.14 260)",
          500: "oklch(42% 0.15 260)",
          600: "oklch(36% 0.15 260)",
          700: "oklch(28% 0.14 260)",
          800: "oklch(22% 0.10 260)",
          900: "oklch(16% 0.06 260)",
        },
      },
      fontFamily: {
        display: ["var(--font-display)"],
        sans: ["var(--font-body)"],
        mono: ["var(--font-mono)"],
      },
    },
  },
  plugins: [],
}
