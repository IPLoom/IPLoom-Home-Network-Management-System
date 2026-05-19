<template>
  <div class="space-y-6">
    <!-- Page Title and Description -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-3xl font-extrabold text-slate-900 dark:text-slate-50 tracking-tight">Integrations</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Monitor status, synced clients, and performance metrics for all connected system integrations.
        </p>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="bg-white/80 dark:bg-slate-800/80 backdrop-blur-md p-1.5 rounded-2xl border border-slate-200/50 dark:border-slate-700/50 shadow-sm inline-flex w-full overflow-x-auto whitespace-nowrap scrollbar-hide">
      <nav class="flex space-x-1 w-full" aria-label="Tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            activeTab === tab.id
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700/50',
            'flex-1 flex items-center justify-center gap-2.5 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200'
          ]"
        >
          <component :is="tab.icon" class="h-5 w-5" />
          <span>{{ tab.name }}</span>
        </button>
      </nav>
    </div>

    <!-- Tab View Panel -->
    <div class="transition-all duration-300">
      <Transition
        mode="out-in"
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="transform translate-y-2 opacity-0"
        enter-to-class="transform translate-y-0 opacity-100"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="transform translate-y-0 opacity-100"
        leave-to-class="transform translate-y-2 opacity-0"
      >
        <component :is="activeTabComponent" />
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import DecoTab from '@/components/integrations/DecoTab.vue'
import AdguardTab from '@/components/integrations/AdguardTab.vue'
import OpenWrtTab from '@/components/integrations/OpenWrtTab.vue'

import {
  WifiIcon,
  ShieldCheckIcon,
  CpuChipIcon
} from '@heroicons/vue/24/outline'

const activeTab = ref('deco')

const tabs = [
  { id: 'deco', name: 'TP-Link Deco', icon: WifiIcon },
  { id: 'adguard', name: 'AdGuard Home', icon: ShieldCheckIcon },
  { id: 'openwrt', name: 'OpenWrt Router', icon: CpuChipIcon }
]

const activeTabComponent = computed(() => {
  switch (activeTab.value) {
    case 'deco':
      return DecoTab
    case 'adguard':
      return AdguardTab
    case 'openwrt':
      return OpenWrtTab
    default:
      return DecoTab
  }
})
</script>

<style scoped>
/* Hide scrollbar for Chrome, Safari and Opera */
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
/* Hide scrollbar for IE, Edge and Firefox */
.scrollbar-hide {
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}
</style>
