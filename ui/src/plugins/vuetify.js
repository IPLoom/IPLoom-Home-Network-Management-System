import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import '@mdi/font/css/materialdesignicons.css'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        dark: false,
        colors: {
          background: '#f8fafc',      // slate-50
          surface: '#ffffff',         // pure white
          'surface-variant': '#f1f5f9', // slate-100
          primary: '#3b82f6',         // blue-500
          secondary: '#64748b',       // slate-500
          success: '#10b981',         // emerald-500
          warning: '#f59e0b',         // amber-500
          error: '#ef4444',           // red-500
          info: '#06b6d4',            // cyan-500
          border: '#e2e8f0',          // slate-200
        }
      },
      dark: {
        dark: true,
        colors: {
          background: '#0f172a',      // slate-900
          surface: '#1e293b',         // slate-800
          'surface-variant': '#334155', // slate-700
          primary: '#3b82f6',         // blue-500
          secondary: '#94a3b8',       // slate-400
          success: '#10b981',         // emerald-500
          warning: '#f59e0b',         // amber-500
          error: '#ef4444',           // red-500
          info: '#06b6d4',            // cyan-500
          border: '#334155',          // slate-700
        }
      }
    }
  }
})
