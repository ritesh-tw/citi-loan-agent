/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        citi: {
          blue: "#003B70",
          light: "#0066A1",
          accent: "#00BCD4",
          gray: "#F5F5F5",
        },
      },
    },
  },
  plugins: [],
};
