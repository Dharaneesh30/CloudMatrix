/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'Outfit'", "sans-serif"],
      },
      colors: {
        ink: "#1f2022",
        ember: "#ef5b36",
        dawn: "#f5e8d4",
        mint: "#35a57e",
      },
      boxShadow: {
        glass: "0 18px 45px rgba(31, 32, 34, 0.16)",
      },
    },
  },
  plugins: [],
};
