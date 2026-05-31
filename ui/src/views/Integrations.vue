<template>
  <div class="space-y-6">
    <!-- Navigation Tabs using PrimeVue Tabs -->
    <Tabs v-model:value="activeTab" class="w-full">
      <!-- Page Title, Description & Tabs Header row -->
      <div class="page-header items-start sm:items-center">
        <div>
          <h1 class="text-2xl font-semibold text-slate-900 dark:text-white">Integrations</h1>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Monitor status, synced clients, and performance metrics for connected systems
          </p>
        </div>

        <TabList :pt="{
          root: { class: 'flex items-center gap-1 bg-white/80 dark:bg-slate-800/80 backdrop-blur-md p-1 rounded-xl border border-slate-200/50 dark:border-slate-700/50 shadow-sm overflow-x-auto whitespace-nowrap' },
          content: { class: '!border-none !border-b-0 !shadow-none bg-transparent', style: 'border: none !important; box-shadow: none !important;' },
          tabList: { class: '!border-none !border-b-0 bg-transparent', style: 'border: none !important; border-bottom: none !important;' },
          activeBar: { class: 'hidden', style: 'display: none !important;' }
        }">
          <Tab v-for="tab in tabs" :key="tab.id" :value="tab.id"
            :pt="{
              root: ({ context }) => [
                'flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-205 border-none outline-none cursor-pointer',
                context.active
                  ? 'bg-blue-600 text-white shadow-sm' 
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-750 bg-transparent'
              ]
            }"
          >
            <component :is="tab.icon" class="w-4 h-4" />
            <span>{{ tab.name }}</span>
          </Tab>
        </TabList>
      </div>

    </Tabs>

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
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'

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
/* Remove PrimeVue's default tab list border and active bar */
:deep(.p-tablist-tab-list) {
  border: none !important;
  border-bottom: none !important;
  border-style: none !important;
}
:deep(.p-tablist-active-bar) {
  display: none !important;
}
:deep(.p-tablist-content) {
  border: none !important;
}
:deep(.p-tablist) {
  border: none !important;
  overflow: visible;
}
</style>
