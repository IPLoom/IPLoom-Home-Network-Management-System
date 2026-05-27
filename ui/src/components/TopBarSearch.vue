<template>
  <div class="search-wrapper" v-click-outside="closeResults">
    <div class="search-bar">
      <SearchIcon style="height: 16px; width: 16px; color: rgb(var(--color-text-tertiary)); margin-right: 8px; flex-shrink: 0;" />
      <input
        v-model="searchStore.searchQuery"
        type="text"
        placeholder="Search devices or activity..."
        class="search-input"
        @input="handleInput"
        @focus="showResults = true"
        @keyup.enter="goToDevices"
      />
      <div class="controls-wrapper">
        <kbd class="kbd-shortcut">
          <span style="font-size: 8px; margin-right: 2px;">⌘</span>K
        </kbd>
        <button v-if="searchStore.searchQuery" @click="clearSearch" class="clear-btn">
          <XIcon style="height: 16px; width: 16px;" />
        </button>
      </div>
    </div>

    <!-- Search Results Dropdown -->
    <v-expand-transition>
      <div
        v-if="showResults && (searchStore.results.length > 0 || searchStore.isLoading || (searchStore.searchQuery.length >= 2 && !searchStore.isLoading))"
        class="results-dropdown"
      >
        <div v-if="searchStore.isLoading" class="loading-container">
          <v-progress-circular indeterminate color="primary" size="24" width="2"></v-progress-circular>
        </div>
        <div v-else-if="searchStore.results.length > 0" class="results-list">
          <div v-for="device in searchStore.results" :key="device.id">
            <button
              @click="goToDevice(device)"
              class="result-item"
            >
              <div class="icon-container">
                <div class="icon-box">
                  <component :is="getIcon(device.icon || 'help-circle')" style="height: 16px; width: 16px;" />
                </div>
                <span class="status-dot" :style="{ backgroundColor: device.status === 'online' ? '#10b981' : '#94a3b8' }"></span>
              </div>
              <div style="flex: 1; min-width: 0;">
                <div style="font-size: 12px; font-weight: bold; color: rgb(var(--color-text-primary)); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ device.display_name || 'Unnamed Device' }}</div>
                <div style="font-size: 10px; color: rgb(var(--color-text-secondary)); font-family: monospace; letter-spacing: -0.025em;">{{ device.ip }}</div>
              </div>
            </button>
          </div>
          <div style="padding: 8px; border-top: 1px solid rgba(var(--color-border), 0.5); margin-top: 4px;">
            <button @click="goToDevices" class="show-all-btn">
              <span>Show all results</span>
              <ArrowRightIcon style="height: 12px; width: 12px;" />
            </button>
          </div>
        </div>
      </div>
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

<style scoped>
.search-wrapper {
  position: relative;
  width: 100%;
}

.search-bar {
  position: relative;
  display: flex;
  align-items: center;
  background-color: rgba(var(--color-surface), 0.5);
  border: 1px solid rgb(var(--color-border));
  border-radius: 8px;
  transition: all 0.2s;
  padding: 8px 12px;
}

.search-bar:focus-within {
  border-color: rgba(var(--color-text-secondary), 0.5);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.search-input {
  width: 100%;
  background: transparent;
  border: none;
  outline: none;
  font-size: 14px;
  color: rgb(var(--color-text-primary));
}
.search-input::placeholder {
  color: rgb(var(--color-text-tertiary));
}

.controls-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: 8px;
  flex-shrink: 0;
}

.kbd-shortcut {
  display: none;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  font-family: sans-serif;
  font-size: 10px;
  font-weight: bold;
  color: rgb(var(--color-text-tertiary));
  background-color: rgb(var(--color-surface-elevated));
  border: 1px solid rgb(var(--color-border));
  border-radius: 4px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  user-select: none;
}
@media (min-width: 640px) {
  .kbd-shortcut {
    display: inline-flex;
  }
}

.clear-btn {
  background: transparent;
  border: none;
  color: rgb(var(--color-text-tertiary));
  padding: 2px;
  cursor: pointer;
  display: flex;
  align-items: center;
}
.clear-btn:hover {
  color: rgb(var(--color-text-primary));
}

.results-dropdown {
  position: absolute;
  margin-top: 8px;
  width: 100%;
  background-color: rgb(var(--color-surface-elevated));
  border: 1px solid rgb(var(--color-border));
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  z-index: 50;
}

.loading-container {
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.results-list {
  padding: 8px 0 0 0;
}

.result-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: transparent;
  border: none;
  text-align: left;
  cursor: pointer;
}
.result-item:hover {
  background-color: rgba(59, 130, 246, 0.05);
}

.icon-container {
  position: relative;
}

.icon-box {
  padding: 8px;
  background-color: rgba(var(--color-surface), 0.5);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgb(var(--color-text-secondary));
  transition: all 0.2s;
}
.result-item:hover .icon-box {
  background-color: rgba(59, 130, 246, 0.1);
  color: #2563eb;
}

.status-dot {
  position: absolute;
  bottom: -2px;
  right: -2px;
  height: 10px;
  width: 10px;
  border-radius: 50%;
  border: 2px solid rgb(var(--color-surface-elevated));
}

.show-all-btn {
  width: 100%;
  padding: 8px 16px;
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #2563eb;
  background: transparent;
  border: none;
  border-radius: 8px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}
.show-all-btn:hover {
  background-color: rgba(59, 130, 246, 0.05);
}
</style>
