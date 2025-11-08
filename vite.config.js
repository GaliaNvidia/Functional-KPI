import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 👇 חשוב: החליפי Functional-KPI בשם הריפו שלך ב-GitHub אם שונה
export default defineConfig({
  base: '/Functional-KPI/',
  plugins: [react()],
})
