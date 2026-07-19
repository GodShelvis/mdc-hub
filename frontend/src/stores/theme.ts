import { ref } from 'vue'

const isDark = ref(true)

export function useTheme() {
  function toggle() { isDark.value = !isDark.value }
  return { isDark, toggle }
}
