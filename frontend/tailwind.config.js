/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // dark surfaces from spec
        ink: {
          950: '#0D111A',
          900: '#0F1115',
          850: '#10141D',
          800: '#12161F',
          700: '#151923',
          600: '#1B2030',
          500: '#252b3d',
        },
        brand: {
          purple: '#673AB7',
          amber: '#FA9042',
          periwinkle: '#8885FF',
        },
      },
      fontFamily: {
        sans: ['"Manrope"', '"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        display: ['"Plus Jakarta Sans"', '"Manrope"', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        '3xl': '1.75rem',
      },
      backdropBlur: {
        glass: '14px',
      },
      keyframes: {
        'pulse-soft': {
          '0%,100%': { opacity: '0.6' },
          '50%': { opacity: '1' },
        },
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      animation: {
        'pulse-soft': 'pulse-soft 1.8s ease-in-out infinite',
        'fade-up': 'fade-up 0.4s ease-out both',
        'shimmer': 'shimmer 2.4s linear infinite',
      },
    },
  },
  plugins: [],
};
