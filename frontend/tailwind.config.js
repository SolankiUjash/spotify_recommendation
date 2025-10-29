/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'spotify-green': '#1ed760',
        'spotify-black': '#121212',
        'spotify-gray': '#535353',
      },
      backgroundImage: {
        'spotify-gradient': 'linear-gradient(135deg, #1ed760 0%, #1db954 100%)',
      },
      boxShadow: {
        'glow-green': '0 0 20px rgba(30, 215, 96, 0.5)',
        'glow-green-lg': '0 0 40px rgba(30, 215, 96, 0.6)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
