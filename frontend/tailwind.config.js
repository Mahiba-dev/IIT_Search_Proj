/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f4ff",
          100: "#dbe4ff",
          500: "#5b6ee8",
          600: "#4653d1",
          700: "#3740a8",
          900: "#1f2266",
        },
      },
    },
  },
  plugins: [],
}
