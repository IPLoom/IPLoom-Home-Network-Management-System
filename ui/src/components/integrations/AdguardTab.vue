<template>
  <div class="space-y-6">
    <!-- Header Card -->
    <div class="bg-white/80 dark:bg-slate-800/80 backdrop-blur-md rounded-2xl p-6 border border-slate-200/50 dark:border-slate-700/50 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
          <span>AdGuard Home DNS Blocker</span>
          <span :class="[
            'px-2 py-0.5 text-xs font-semibold rounded-full uppercase tracking-wider',
            isConfigured && isVerified
              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-400'
              : 'bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-400'
          ]">
            {{ isConfigured && isVerified ? 'Active' : 'Not Configured' }}
          </span>
        </h2>
        <p v-if="url" class="text-xs font-mono text-slate-400 dark:text-slate-500 mt-1 truncate max-w-sm sm:max-w-md">
          Instance URL: {{ url }}
        </p>
      </div>

      <div class="flex items-center gap-3">
        <button 
          @click="syncAdguard" 
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

    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div v-for="i in 4" :key="i" class="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-slate-200 dark:border-slate-700 animate-pulse h-28"></div>
    </div>

    <template v-else-if="isConfigured && isVerified">
      <!-- 24h DNS Stats Overview -->
      <div v-if="stats" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Total Queries -->
        <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200/60 dark:border-slate-700/60 p-5 shadow-sm">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-slate-500 dark:text-slate-400">Total Queries (24h)</span>
            <div class="p-2 rounded-lg bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400">
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>
          <div class="mt-2">
            <div class="text-2xl font-bold text-slate-800 dark:text-slate-100">{{ stats.total_queries_24h.toLocaleString() }}</div>
            <p class="text-xs text-slate-400 mt-1">Processed DNS lookups</p>
          </div>
        </div>

        <!-- Blocked Queries -->
        <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200/60 dark:border-slate-700/60 p-5 shadow-sm">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-slate-500 dark:text-slate-400">Blocked Queries (24h)</span>
            <div class="p-2 rounded-lg bg-rose-50 dark:bg-rose-500/10 text-rose-600 dark:text-rose-400">
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
          </div>
          <div class="mt-2">
            <div class="text-2xl font-bold text-slate-800 dark:text-slate-100 text-rose-600 dark:text-rose-400">{{ stats.blocked_queries_24h.toLocaleString() }}</div>
            <p class="text-xs text-slate-400 mt-1">Threats & trackers filtered</p>
          </div>
        </div>

        <!-- Block Rate -->
        <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200/60 dark:border-slate-700/60 p-5 shadow-sm">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-slate-500 dark:text-slate-400">Blocking Ratio</span>
            <div class="p-2 rounded-lg bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
          <div class="mt-2">
            <div class="text-2xl font-bold text-slate-800 dark:text-slate-100">{{ stats.block_percentage_24h }}%</div>
            <p class="text-xs text-slate-400 mt-1">Percent of traffic blocked</p>
          </div>
        </div>

        <!-- Latency -->
        <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200/60 dark:border-slate-700/60 p-5 shadow-sm">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-slate-500 dark:text-slate-400">Avg Resolution Latency</span>
            <div class="p-2 rounded-lg bg-amber-50 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400">
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div class="mt-2">
            <div class="text-2xl font-bold text-slate-800 dark:text-slate-100">{{ stats.avg_response_time_ms }} ms</div>
            <p class="text-xs text-slate-400 mt-1">Response time speed</p>
          </div>
        </div>
      </div>

      <!-- Recent Blocked Log -->
      <div class="space-y-4">
        <h3 class="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
          <svg class="h-5 w-5 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
          </svg>
          <span>Recently Blocked Queries</span>
        </h3>

        <div class="bg-white dark:bg-slate-800 border border-slate-200/60 dark:border-slate-700/60 rounded-2xl overflow-hidden shadow-sm">
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-slate-50/75 dark:bg-slate-900/50 text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100 dark:border-slate-700/50">
                  <th class="px-6 py-4">Timestamp</th>
                  <th class="px-6 py-4">Domain Name</th>
                  <th class="px-6 py-4">Client IP</th>
                  <th class="px-6 py-4 text-center">Type</th>
                  <th class="px-6 py-4">Filter Reason</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-700/40 text-sm">
                <tr 
                  v-for="(log, idx) in recentBlocked" 
                  :key="idx"
                  class="hover:bg-slate-50/50 dark:hover:bg-slate-800/50 transition-colors"
                >
                  <td class="px-6 py-4 text-xs font-mono text-slate-400 truncate max-w-[150px]">
                    {{ formatDate(log.timestamp) }}
                  </td>
                  <td class="px-6 py-4 font-semibold text-slate-700 dark:text-slate-300 font-mono truncate max-w-sm" :title="log.domain">
                    {{ log.domain }}
                  </td>
                  <td class="px-6 py-4 font-mono text-slate-500">
                    {{ log.client_ip }}
                  </td>
                  <td class="px-6 py-4 text-center">
                    <span class="px-2 py-0.5 text-[10px] font-bold bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 rounded">
                      {{ log.query_type }}
                    </span>
                  </td>
                  <td class="px-6 py-4">
                    <span class="text-xs font-semibold text-slate-400 dark:text-slate-500">
                      {{ log.category || 'AdBlock Filter List' }}
                    </span>
                  </td>
                </tr>

                <tr v-if="recentBlocked.length === 0">
                  <td colspan="5" class="px-6 py-8 text-center text-slate-400 dark:text-slate-500">
                    No blocked queries found in local database.
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
          <h3 class="text-lg font-bold text-slate-800 dark:text-slate-100">AdGuard Home integration is inactive</h3>
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
import { ref, onMounted } from 'vue'
import api from '@/utils/api'
import { useNotifications } from '@/composables/useNotifications'

const { notifySuccess, notifyError } = useNotifications()

const loading = ref(true)
const syncing = ref(false)
const error = ref(null)

const isConfigured = ref(false)
const isVerified = ref(false)
const url = ref('')
const stats = ref(null)
const recentBlocked = ref([])

const fetchAdguardData = async () => {
  loading.value = true
  error.value = null
  try {
    const res = await api.get('/integrations/adguard/data')
    isConfigured.value = res.data.enabled
    isVerified.value = res.data.verified
    url.value = res.data.url || ''
    stats.value = res.data.stats
    recentBlocked.value = res.data.recent_blocked || []
  } catch (err) {
    console.error('Error fetching adguard data:', err)
    error.value = err.response?.data?.detail || 'Failed to load AdGuard integration details.'
  } finally {
    loading.value = false
  }
}

const syncAdguard = async () => {
  syncing.value = true
  try {
    await api.post('/integrations/adguard/sync')
    notifySuccess('AdGuard synchronization queued in background')
    setTimeout(fetchAdguardData, 2000)
  } catch (err) {
    console.error('Failed to trigger adguard sync:', err)
    notifyError(err.response?.data?.detail || 'Failed to start AdGuard synchronization.')
  } finally {
    syncing.value = false
  }
}

const formatDate = (val) => {
  if (!val) return ''
  return new Date(val).toLocaleTimeString()
}

onMounted(() => {
  fetchAdguardData()
})
</script>
