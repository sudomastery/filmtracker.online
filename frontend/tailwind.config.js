/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#fdf4ff',
          100: '#fae8ff',
          200: '#f3d0fe',
          300: '#e9a8fd',
          400: '#d975fa',
          500: '#c44af3',
          600: '#a928d8',
          700: '#8d1eb4',
          800: '#751d93',
          900: '#611a78',
          950: '#3f0455',
        },
        surface: {
          DEFAULT: '#0f0f0f',
          card:    '#161616',
          border:  '#2a2a2a',
          muted:   '#1e1e1e',
        },
      },
      fontFamily: {
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
