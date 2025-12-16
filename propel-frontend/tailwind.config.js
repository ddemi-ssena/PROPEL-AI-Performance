/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#e6f1ff',
          100: '#b3d7ff',
          500: '#2196F3',
          600: '#1976D2',
          700: '#1565C0',
        },
        secondary: {
          500: '#64748B',
          600: '#475569',
        },
      },
    },
  },
  plugins: [],
}
