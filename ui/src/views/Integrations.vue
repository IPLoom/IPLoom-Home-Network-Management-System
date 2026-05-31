<template>
  <div class="space-y-6">
    <!-- Page Title and Description -->
    <div class="page-header shrink-0 !mb-0">
      <div>
        <h1 class="text-2xl font-semibold text-slate-900 dark:text-white">Integrations</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Monitor status, synced clients, and performance metrics for connected systems
        </p>
      </div>
    </div>

    <!-- Navigation Tabs using PrimeVue Tabs -->
    <Tabs v-model:value="activeTab" class="w-full">
      <TabList :pt="{
        root: 'flex items-center gap-2 mb-6 bg-white/50 dark:bg-slate-900/50 p-1.5 rounded-2xl border border-slate-200 dark:border-slate-800 w-fit'
      }">
        <Tab v-for="tab in tabs" :key="tab.id" :value="tab.id"
          :pt="{
            root: ({ context }) => [
              'flex items-center gap-2 px-6 py-2.5 rounded-xl text-[11px] font-black uppercase tracking-widest transition-all border-none outline-none cursor-pointer',
              context.active
                ? 'bg-blue-600 text-white shadow-xl shadow-blue-600/20' 
                : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 bg-transparent'
            ]
          }"
        >
          <component :is="tab.icon" class="w-3.5 h-3.5" />
          <span>{{ tab.name }}</span>
        </Tab>
      </TabList>

      <TabPanels :pt="{ root: 'p-0 bg-transparent' }">
        <TabPanel value="deco" :pt="{ root: 'p-0' }">
          <DecoTab />
        </TabPanel>
        <TabPanel value="adguard" :pt="{ root: 'p-0' }">
          <AdguardTab />
        </TabPanel>
        <TabPanel value="openwrt" :pt="{ root: 'p-0' }">
          <OpenWrtTab />
        </TabPanel>
        <TabPanel value="tailscale" :pt="{ root: 'p-0' }">
          <TailscaleTab />
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import DecoTab from '@/components/integrations/DecoTab.vue'
import AdguardTab from '@/components/integrations/AdguardTab.vue'
import OpenWrtTab from '@/components/integrations/OpenWrtTab.vue'
import TailscaleTab from '@/components/integrations/TailscaleTab.vue'

// PrimeVue components
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'

import {
  Wifi,
  ShieldCheck,
  Cpu,
  Cloud
} from 'lucide-vue-next'

const activeTab = ref('deco')

const tabs = [
  { id: 'deco', name: 'TP-Link Deco', icon: Wifi },
  { id: 'adguard', name: 'AdGuard Home', icon: ShieldCheck },
  { id: 'openwrt', name: 'OpenWrt Router', icon: Cpu },
  { id: 'tailscale', name: 'Tailscale VPN', icon: Cloud }
]
</script>
