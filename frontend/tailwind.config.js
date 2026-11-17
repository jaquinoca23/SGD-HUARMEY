/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Paleta institucional neutra y configurable (no es un logotipo ni identidad oficial).
        brand: {
          50: "#eef6f6",
          100: "#d5e8ea",
          200: "#aed2d6",
          300: "#80b6bd",
          400: "#4f949e",
          500: "#357882",
          600: "#2b616b",
          700: "#274f58",
          800: "#254349",
          900: "#223a3f",
        },
      },
    },
  },
  plugins: [],
};
