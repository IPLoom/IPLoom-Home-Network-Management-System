<template>
  <div class="space-y-6">
    <!-- Page Title, Description & Tabs Header row -->
    <div class="page-header items-start sm:items-center">
      <div>
        <h1 class="text-2xl font-semibold text-slate-900 dark:text-white">Integrations</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Monitor status, synced clients, and performance metrics for connected systems
        </p>
      </div>

      <!-- Tab Switcher (Custom) -->
      <div class="flex items-center gap-1.5 p-1 bg-slate-50/80 dark:bg-slate-800/40 rounded-xl border border-slate-200/50 dark:border-slate-700/30 overflow-x-auto whitespace-nowrap shrink-0">
        <button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id"
            class="px-3 h-9 rounded-lg flex items-center gap-2 text-xs font-semibold transition-all border-none outline-none cursor-pointer"
            :class="activeTab === tab.id ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' : 'text-slate-600 dark:text-slate-400 hover:bg-white dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-white bg-transparent'">
            <component :is="tab.icon" class="w-3.5 h-3.5" />
            <span>{{ tab.name }}</span>
        </button>
      </div>
    </div>

    <!-- Tab View Panel -->
    <div class="transition-all duration-300">
      <component :is="activeTabComponent" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import DecoTab from '@/components/integrations/DecoTab.vue'
import AdguardTab from '@/components/integrations/AdguardTab.vue'
import OpenWrtTab from '@/components/integrations/OpenWrtTab.vue'
import TailscaleTab from '@/components/integrations/TailscaleTab.vue'

// PrimeVue components

import {
  Wifi,
  ShieldCheck,
  Cpu,
  Cloud
} from 'lucide-vue-next'

const activeTab = ref('deco')

const activeTabComponent = computed(() => {
  switch (activeTab.value) {
    case 'deco':
      return DecoTab
    case 'adguard':
      return AdguardTab
    case 'openwrt':
      return OpenWrtTab
    case 'tailscale':
      return TailscaleTab
    default:
      return DecoTab
  }
})

const tabs = [
  { id: 'deco', name: 'TP-Link Deco', icon: Wifi },
  { id: 'adguard', name: 'AdGuard Home', icon: ShieldCheck },
  { id: 'openwrt', name: 'OpenWrt Router', icon: Cpu },
  { id: 'tailscale', name: 'Tailscale VPN', icon: Cloud }
]
</script>

<style scoped>
</style>
