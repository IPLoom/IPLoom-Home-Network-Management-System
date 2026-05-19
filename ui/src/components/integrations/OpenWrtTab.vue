<template>
  <div class="space-y-6">
    <!-- Header Card -->
    <div class="bg-white/80 dark:bg-slate-800/80 backdrop-blur-md rounded-2xl p-6 border border-slate-200/50 dark:border-slate-700/50 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
          <span>OpenWrt Router Interface</span>
          <span :class="[
            'px-2 py-0.5 text-xs font-semibold rounded-full uppercase tracking-wider',
            isConfigured && isVerified
              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-400'
              : 'bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-400'
          ]">
            {{ isConfigured && isVerified ? 'Connected' : 'Not Configured' }}
          </span>
        </h2>
        <p v-if="url" class="text-xs font-mono text-slate-400 dark:text-slate-500 mt-1 truncate max-w-sm sm:max-w-md">
          Router URL: {{ url }}
        </p>
      </div>

      <div class="flex items-center gap-3">
        <button 
          @click="syncOpenWrt" 
          :disabled="syncing || !isConfigured"
          class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white rounded-xl text-sm font-medium transition-all shadow-sm active:scale-95"
        >
          <svg v-if="syncing" class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89H18v3" />
          </svg>
          <span>{{ syncing ? 'Syncing...' : 'Sync Now' }}</span>
        </button>
      </div>
    </div>

    <!-- Error State -->
    <div v-if="error" class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-2xl p-4 text-red-700 dark:text-red-400 text-sm flex items-start gap-3">
      <svg class="h-5 w-5 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <div>
        <h4 class="font-semibold">Integration Error</h4>
        <p class="mt-0.5">{{ error }}</p>
      </div>
    </div>

    <div v-if="loading" class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 animate-pulse h-64"></div>

    <template v-else-if="isConfigured && isVerified">
      <!-- Synced Devices Table -->
      <div class="space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <h3 class="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
            <svg class="h-5 w-5 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 5h10a2 2 0 012 2v10a2 2 0 01-2 2H7a2 2 0 01-2-2V7a2 2 0 012-2z" />
            </svg>
            <span>Active DHCP / Wireless Leases ({{ filteredDevices.length }})</span>
          </h3>

          <div class="relative w-full sm:max-w-xs">
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="Search OpenWrt devices..." 
              class="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
            <svg class="absolute left-3 top-2.5 h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        <div class="bg-white dark:bg-slate-800 border border-slate-200/60 dark:border-slate-700/60 rounded-2xl overflow-hidden shadow-sm">
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-slate-50/75 dark:bg-slate-900/50 text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100 dark:border-slate-700/50">
                  <th class="px-6 py-4">Hostname / Device</th>
                  <th class="px-6 py-4">IP Address</th>
                  <th class="px-6 py-4">MAC Address</th>
                  <th class="px-6 py-4">Interface / Network</th>
                  <th class="px-6 py-4 text-center">Status</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-700/40 text-sm">
                <tr 
                  v-for="device in filteredDevices" 
                  :key="device.id"
                  class="hover:bg-slate-50/50 dark:hover:bg-slate-800/50 transition-colors"
                >
                  <td class="px-6 py-4">
                    <div class="flex items-center gap-3">
                      <div class="w-8 h-8 rounded-lg bg-teal-50 dark:bg-teal-500/10 text-teal-600 dark:text-teal-400 flex items-center justify-center flex-shrink-0">
                        <img v-if="device.icon && device.icon.startsWith('/static/')" :src="device.icon" class="h-5 w-5 object-contain" />
                        <component v-else :is="getIcon(device.icon || 'help-circle')" class="h-5 w-5" />
                      </div>
                      <div class="font-semibold text-slate-800 dark:text-slate-200">
                        {{ device.name }}
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-4 font-mono text-slate-600 dark:text-slate-400">
                    {{ device.ip || 'N/A' }}
                  </td>
                  <td class="px-6 py-4 font-mono text-slate-500">
                    {{ device.mac }}
                  </td>
                  <td class="px-6 py-4">
                    <span class="text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-900 px-2.5 py-1 rounded-md border border-slate-200/40 dark:border-slate-800/40">
                      {{ device.attributes.interface || 'lan' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-center">
                    <span :class="[
                      'px-2.5 py-0.5 text-[10px] font-bold rounded-full uppercase tracking-wider',
                      device.status === 'online' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-400' : 'bg-slate-100 text-slate-600 dark:bg-slate-700/50 dark:text-slate-400'
                    ]">
                      {{ device.status }}
                    </span>
                  </td>
                </tr>

                <tr v-if="filteredDevices.length === 0">
                  <td colspan="5" class="px-6 py-8 text-center text-slate-400 dark:text-slate-500">
                    No devices synced by OpenWrt found.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </template>

    <div v-else class="bg-white dark:bg-slate-800 rounded-2xl p-8 border border-slate-200/60 dark:border-slate-700/60 text-center shadow-sm">
      <div class="max-w-md mx-auto space-y-4">
        <div class="w-16 h-16 bg-amber-50 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400 rounded-full flex items-center justify-center mx-auto">
          <svg class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div>
          <h3 class="text-lg font-bold text-slate-800 dark:text-slate-100">OpenWrt integration is inactive</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Please make sure that the integration is enabled and credentials are verified in Settings page.
          </p>
        </div>
        <div>
          <router-link 
            to="/settings" 
            class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold transition-all active:scale-95 shadow-sm"
          >
            Go to Settings
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/utils/api'
import { useNotifications } from '@/composables/useNotifications'
import { getIcon } from '@/utils/icons'

const { notifySuccess, notifyError } = useNotifications()

const loading = ref(true)
const syncing = ref(false)
const error = ref(null)

const isConfigured = ref(false)
const isVerified = ref(false)
const url = ref('')
const devices = ref([])
const searchQuery = ref('')

const fetchOpenWrtData = async () => {
  loading.value = true
  error.value = null
  try {
    const res = await api.get('/integrations/openwrt/data')
    isConfigured.value = res.data.enabled
    isVerified.value = res.data.verified
    url.value = res.data.url || ''
    devices.value = res.data.devices || []
  } catch (err) {
    console.error('Error fetching OpenWrt data:', err)
    error.value = err.response?.data?.detail || 'Failed to load OpenWrt integration details.'
  } finally {
    loading.value = false
  }
}

const syncOpenWrt = async () => {
  syncing.value = true
  try {
    await api.post('/integrations/openwrt/sync')
    notifySuccess('OpenWrt synchronization queued in background')
    setTimeout(fetchOpenWrtData, 2000)
  } catch (err) {
    console.error('Failed to trigger OpenWrt sync:', err)
    notifyError(err.response?.data?.detail || 'Failed to start OpenWrt synchronization.')
  } finally {
    syncing.value = false
  }
}

const filteredDevices = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  if (!query) return devices.value
  return devices.value.filter(d => 
    d.name.toLowerCase().includes(query) || 
    d.mac.toLowerCase().includes(query) || 
    (d.ip && d.ip.toLowerCase().includes(query))
  )
})

onMounted(() => {
  fetchOpenWrtData()
})
</script>
