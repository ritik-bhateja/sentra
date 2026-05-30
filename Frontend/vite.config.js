import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],

  server: {
    host: true,                        
    strictPort: false,
    cors: true,
    allowedHosts: [
      'f4455f964b5e.ngrok-free.app',
      '*.ngrok-free.app'
    ]
  }
})

 