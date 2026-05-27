<template>
  <div class="flex-1 max-w-lg relative w-full md:w-auto" v-click-outside="closeResults">
    <div class="relative flex items-center bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-slate-300 dark:focus-within:border-slate-600 transition-all px-3 py-2">
      <SearchIcon class="h-4 w-4 text-slate-400 mr-2 flex-shrink-0" />
      <input
        v-model="searchStore.searchQuery"
        type="text"
        placeholder="Search devices or activity..."
        class="w-full bg-transparent border-none outline-none text-sm placeholder-slate-500 dark:text-slate-200"
        @input="handleInput"
        @focus="showResults = true"
        @keyup.enter="goToDevices"
      />
      <div class="flex items-center gap-1.5 ml-2 flex-shrink-0">
        <kbd class="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 font-sans text-[10px] font-bold text-slate-400 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md shadow-sm select-none">
          <span class="text-[8px]">⌘</span>K
        </kbd>
        <button v-if="searchStore.searchQuery" @click="clearSearch" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-0.5">
          <XIcon class="h-4 w-4" />
        </button>
      </div>
    </div>

    <!-- Search Results Dropdown -->
    <v-expand-transition>
      <v-card
        v-if="showResults && (searchStore.results.length > 0 || searchStore.isLoading || (searchStore.searchQuery.length >= 2 && !searchStore.isLoading))"
        class="absolute mt-2 w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl overflow-hidden z-50"
      >
        <div v-if="searchStore.isLoading" class="p-6 flex items-center justify-center">
          <v-progress-circular indeterminate color="primary" size="24" width="2"></v-progress-circular>
        </div>
        <div v-else-if="searchStore.results.length > 0" class="py-2">
          <div v-for="device in searchStore.results" :key="device.id">
            <button
              @click="goToDevice(device)"
              class="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors text-left group/item"
            >
              <div class="relative">
                <div class="p-2 bg-slate-100 dark:bg-slate-700 rounded-lg group-hover/item:bg-blue-100 dark:group-hover/item:bg-blue-900/40 transition-colors">
                  <component :is="getIcon(device.icon || 'help-circle')" class="h-4 w-4 text-slate-600 dark:text-slate-400 group-hover/item:text-blue-600 dark:group-hover/item:text-blue-400" />
                </div>
                <span class="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-white dark:border-slate-800" :class="device.status === 'online' ? 'bg-emerald-500' : 'bg-slate-400'"></span>
              </div>
              <div class="min-w-0 flex-1">
                <div class="text-xs font-bold text-slate-900 dark:text-white truncate">{{ device.display_name || 'Unnamed Device' }}</div>
                <div class="text-[10px] text-slate-500 font-mono tracking-tight">{{ device.ip }}</div>
              </div>
            </button>
          </div>
          <div class="px-2 pt-2 mt-1 border-t border-slate-100 dark:border-slate-700/50">
            <button @click="goToDevices" class="w-full py-2 px-4 text-[10px] font-black uppercase tracking-widest text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-500/10 rounded-xl transition-all flex items-center justify-between">
              <span>Show all results</span>
              <ArrowRightIcon class="h-3 w-3" />
            </button>
          </div>
        </div>
      </v-card>
    </v-expand-transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSearchStore } from '@/stores/search'
import {
  Search as SearchIcon,
  X as XIcon,
  ArrowRight as ArrowRightIcon,
  HelpCircle,
  Smartphone,
  Tablet,
  Laptop,
  Monitor,
  Server,
  Router,
  Network,
  Tv,
  Printer
} from 'lucide-vue-next'

const searchStore = useSearchStore()
const router = useRouter()
const showResults = ref(false)

const handleInput = (event) => {
  searchStore.setSearchQuery(event.target.value)
  showResults.value = true
}

const closeResults = () => {
  showResults.value = false
}

const clearSearch = () => {
  searchStore.searchQuery = ''
  searchStore.results = []
}

const goToDevice = (device) => {
  showResults.value = false
  router.push({ name: 'DeviceDetails', params: { id: device.id } })
}

const goToDevices = () => {
  showResults.value = false
  router.push('/devices')
}

const getIcon = (name) => {
  const iconMap = {
    'smartphone': Smartphone,
    'tablet': Tablet,
    'laptop': Laptop,
    'monitor': Monitor,
    'server': Server,
    'router': Router,
    'network': Network,
    'tv': Tv,
    'printer': Printer,
    'help-circle': HelpCircle
  }
  const key = name.toLowerCase().replace('device-', '')
  return iconMap[key] || HelpCircle
}

const vClickOutside = {
  mounted(el, binding) {
    el._clickOutside = (event) => {
      if (!(el === event.target || el.contains(event.target))) {
        binding.value(event)
      }
    }
    document.addEventListener('click', el._clickOutside)
  },
  unmounted(el) {
    document.removeEventListener('click', el._clickOutside)
  }
}
</script>
