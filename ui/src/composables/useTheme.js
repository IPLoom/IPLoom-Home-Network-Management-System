import { ref, watchEffect } from 'vue'

const theme = ref(localStorage.getItem('theme') || 'dark') // Default to dark-first design as specified in UI_UX

// Apply the theme to documentElement
const applyTheme = (val) => {
  if (val === 'dark') {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

// Watch theme changes to automatically update class and localStorage
watchEffect(() => {
  applyTheme(theme.value)
  localStorage.setItem('theme', theme.value)
})

export function useTheme() {
  const isDark = ref(theme.value === 'dark')

  const toggleTheme = () => {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    isDark.value = theme.value === 'dark'
  }

  const setTheme = (newTheme) => {
    if (newTheme === 'dark' || newTheme === 'light') {
      theme.value = newTheme
      isDark.value = newTheme === 'dark'
    }
  }

  // Initialize theme class
  applyTheme(theme.value)

  return {
    theme,
    isDark,
    toggleTheme,
    setTheme
  }
}
