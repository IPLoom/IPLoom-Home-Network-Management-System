<template>
  <div class="space-y-6">
    <!-- Header Summary Card -->
    <div class="bg-white/80 dark:bg-slate-800/80 backdrop-blur-md rounded-2xl p-6 border border-slate-200/50 dark:border-slate-700/50 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
          <span>TP-Link Deco Mesh System</span>
          <span :class="[
            'px-2 py-0.5 text-xs font-semibold rounded-full uppercase tracking-wider',
            isConfigured && isVerified
              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-400'
              : 'bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-400'
          ]">
            {{ isConfigured && isVerified ? 'Connected' : 'Not Configured' }}
          </span>
        </h2>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Last Sync: {{ lastSyncTime || 'Never' }}
        </p>
      </div>

      <div class="flex items-center gap-3">
        <button 
          @click="syncDeco" 
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

    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div v-for="i in 2" :key="i" class="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-slate-200 dark:border-slate-700 animate-pulse space-y-4">
        <div class="h-6 w-1/3 bg-slate-200 dark:bg-slate-700 rounded-md"></div>
        <div class="h-4 w-2/3 bg-slate-100 dark:bg-slate-700/50 rounded-md"></div>
        <div class="h-24 bg-slate-50 dark:bg-slate-900 rounded-xl"></div>
      </div>
    </div>

    <template v-else-if="isConfigured && isVerified">
      <!-- Mesh Nodes Grid -->
      <div class="space-y-4">
        <h3 class="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
          <svg class="h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <span>Mesh Nodes ({{ nodes.length }})</span>
        </h3>

        <!-- Only 1 Node Warning Notice -->
        <div v-if="nodes.length === 1" class="p-4 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/50 rounded-2xl flex items-start gap-3">
          <svg class="h-5 w-5 text-amber-600 dark:text-amber-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div class="text-sm text-amber-800 dark:text-amber-300 leading-normal">
            <strong class="font-semibold">Only 1 Deco Node showing?</strong>
            <p class="mt-1">Satellite (slave) Deco nodes only return their local state. To retrieve the entire mesh network structure and all connected clients, make sure to configure the <strong>Master/Main Deco Router's IP address</strong> in Settings.</p>
          </div>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div 
            v-for="node in nodes" 
            :key="node.id"
            class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200/60 dark:border-slate-700/60 p-5 shadow-sm hover:shadow-md transition-all group hover:-translate-y-0.5"
          >
            <div class="flex items-start justify-between">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-500/10 flex items-center justify-center text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform">
                  <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071a9 9 0 0114.14 0M2.006 8.502a13 13 0 0119.988 0" />
                  </svg>
                </div>
                <div>
                  <h4 class="font-bold text-slate-800 dark:text-slate-100">{{ node.attributes.deco_node_name || node.name }}</h4>
                  <p class="text-xs text-slate-400 dark:text-slate-500 uppercase font-semibold tracking-wider mt-0.5">{{ node.attributes.deco_role || 'Node' }}</p>
                </div>
              </div>
              <span :class="[
                'px-2 py-0.5 text-[10px] font-bold rounded-full uppercase tracking-wider',
                node.status === 'online' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-400' : 'bg-rose-100 text-rose-800 dark:bg-rose-500/10 dark:text-rose-400'
              ]">
                {{ node.status }}
              </span>
            </div>

            <div class="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700/50 space-y-2 text-xs">
              <div class="flex justify-between">
                <span class="text-slate-400">IP Address</span>
                <span class="font-medium text-slate-700 dark:text-slate-300 font-mono">{{ node.ip }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">MAC Address</span>
                <span class="font-medium text-slate-700 dark:text-slate-300 font-mono">{{ node.mac }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">Hardware Ver</span>
                <span class="font-medium text-slate-700 dark:text-slate-300">v{{ node.attributes.deco_hw_ver || 'N/A' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">Firmware Ver</span>
                <span class="font-medium text-slate-700 dark:text-slate-300 truncate max-w-[150px]" :title="node.attributes.deco_fw_ver">
                  {{ node.attributes.deco_fw_ver || 'N/A' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Connected Clients List -->
      <div class="space-y-4 pt-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <h3 class="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
            <svg class="h-5 w-5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <span>Connected Clients ({{ filteredClients.length }})</span>
          </h3>
          
          <div class="relative w-full sm:max-w-xs">
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="Search clients..." 
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
                  <th class="px-6 py-4">Client</th>
                  <th class="px-6 py-4">IP / MAC</th>
                  <th class="px-6 py-4">Connected Node</th>
                  <th class="px-6 py-4 text-center">Type / Band</th>
                  <th class="px-6 py-4 text-center">Signal Strength</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-700/40 text-sm">
                <tr 
                  v-for="client in filteredClients" 
                  :key="client.id"
                  class="hover:bg-slate-50/50 dark:hover:bg-slate-800/50 transition-colors"
                >
                  <!-- Client Details -->
                  <td class="px-6 py-4">
                    <div class="flex items-center gap-3">
                      <div class="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 flex items-center justify-center font-bold text-xs">
                        {{ getClientInitials(client.name) }}
                      </div>
                      <div>
                        <div class="font-semibold text-slate-800 dark:text-slate-200">{{ client.name }}</div>
                        <div class="text-[10px] text-slate-400 font-mono">{{ client.attributes.deco_mac || client.mac }}</div>
                      </div>
                    </div>
                  </td>

                  <!-- IP Address -->
                  <td class="px-6 py-4">
                    <span class="font-mono text-slate-600 dark:text-slate-400">{{ client.ip || 'N/A' }}</span>
                  </td>

                  <!-- Connected Node -->
                  <td class="px-6 py-4">
                    <div class="flex items-center gap-2">
                      <div class="w-1.5 h-1.5 rounded-full bg-blue-500"></div>
                      <span class="text-slate-700 dark:text-slate-300 font-medium">{{ client.attributes.deco_node_name || 'Deco Node' }}</span>
                    </div>
                  </td>

                  <!-- Connection Type & Band -->
                  <td class="px-6 py-4 text-center">
                    <div class="flex flex-col items-center gap-1">
                      <span :class="[
                        'px-2 py-0.5 text-[10px] font-bold rounded-md uppercase tracking-wider',
                        client.attributes.connection_type === 'wired' 
                          ? 'bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400' 
                          : 'bg-indigo-50 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-400'
                      ]">
                        {{ client.attributes.connection_type || 'wireless' }}
                      </span>
                      <span v-if="client.attributes.band" class="text-[10px] font-semibold text-slate-400 dark:text-slate-500">
                        {{ client.attributes.band }}
                      </span>
                    </div>
                  </td>

                  <!-- RSSI Signal Indicator -->
                  <td class="px-6 py-4">
                    <div class="flex items-center justify-center gap-2">
                      <div class="flex items-end gap-0.5 h-4 w-6">
                        <div 
                          v-for="bar in 4" 
                          :key="bar"
                          :class="[
                            'w-1 rounded-sm transition-all',
                            getSignalBars(client.attributes.rssi) >= bar 
                              ? getSignalColorClass(client.attributes.rssi) 
                              : 'bg-slate-200 dark:bg-slate-700'
                          ]"
                          :style="{ height: `${bar * 25}%` }"
                        ></div>
                      </div>
                      <span class="text-xs font-mono font-bold" :class="getSignalTextClass(client.attributes.rssi)">
                        {{ client.attributes.rssi ? `${client.attributes.rssi} dBm` : 'N/A' }}
                      </span>
                    </div>
                  </td>
                </tr>

                <tr v-if="filteredClients.length === 0">
                  <td colspan="5" class="px-6 py-8 text-center text-slate-400 dark:text-slate-500">
                    No clients found matching search query
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
          <h3 class="text-lg font-bold text-slate-800 dark:text-slate-100">TP-Link Deco integration is inactive</h3>
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

const { notifySuccess, notifyError } = useNotifications()

const loading = ref(true)
const syncing = ref(false)
const error = ref(null)

const isConfigured = ref(false)
const isVerified = ref(false)
const lastSyncTime = ref('')
const nodes = ref([])
const clients = ref([])
const searchQuery = ref('')

const fetchDecoData = async () => {
  loading.value = true
  error.value = null
  try {
    const res = await api.get('/integrations/deco/data')
    isConfigured.value = res.data.enabled
    isVerified.value = res.data.verified
    lastSyncTime.value = res.data.last_run ? new Date(res.data.last_run).toLocaleString() : ''
    nodes.value = res.data.nodes || []
    clients.value = res.data.clients || []
  } catch (err) {
    console.error('Error fetching deco data:', err)
    error.value = err.response?.data?.detail || 'Failed to load Deco integration details.'
  } finally {
    loading.value = false
  }
}

const syncDeco = async () => {
  syncing.value = true
  try {
    await api.post('/integrations/deco/sync')
    notifySuccess('Deco synchronization queued in background')
    // Wait briefly and poll data
    setTimeout(fetchDecoData, 2000)
  } catch (err) {
    console.error('Failed to trigger deco sync:', err)
    notifyError(err.response?.data?.detail || 'Failed to start Deco synchronization.')
  } finally {
    syncing.value = false
  }
}

const getClientInitials = (name) => {
  if (!name) return '??'
  const clean = name.replace(/[^a-zA-Z0-9 ]/g, '').trim()
  if (!clean) return '?'
  const parts = clean.split(' ')
  if (parts.length > 1) {
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  return clean.slice(0, 2).toUpperCase()
}

const getSignalBars = (rssi) => {
  if (!rssi) return 0
  const val = parseInt(rssi)
  if (val >= -55) return 4
  if (val >= -67) return 3
  if (val >= -78) return 2
  return 1
}

const getSignalColorClass = (rssi) => {
  if (!rssi) return 'bg-slate-200 dark:bg-slate-700'
  const val = parseInt(rssi)
  if (val >= -55) return 'bg-emerald-500'
  if (val >= -67) return 'bg-teal-500'
  if (val >= -78) return 'bg-amber-500'
  return 'bg-rose-500'
}

const getSignalTextClass = (rssi) => {
  if (!rssi) return 'text-slate-400'
  const val = parseInt(rssi)
  if (val >= -55) return 'text-emerald-600 dark:text-emerald-400'
  if (val >= -67) return 'text-teal-600 dark:text-teal-400'
  if (val >= -78) return 'text-amber-600 dark:text-amber-400'
  return 'text-rose-600 dark:text-rose-400'
}

const filteredClients = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  if (!query) return clients.value
  return clients.value.filter(c => 
    c.name.toLowerCase().includes(query) || 
    c.mac.toLowerCase().includes(query) || 
    (c.ip && c.ip.toLowerCase().includes(query)) ||
    (c.attributes?.deco_node_name && c.attributes.deco_node_name.toLowerCase().includes(query))
  )
})

onMounted(() => {
  fetchDecoData()
})
</script>
