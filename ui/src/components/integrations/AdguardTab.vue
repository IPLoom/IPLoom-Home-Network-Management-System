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
        <button v-if="isConfigured && isVerified"
          @click="toggleProtection"
          :disabled="togglingProtection"
          :class="['!px-4 !py-2.5 rounded-xl text-sm font-semibold transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shadow-sm flex items-center gap-2 border-none', protectionEnabled ? 'bg-amber-500 hover:bg-amber-600 text-white' : 'bg-emerald-500 hover:bg-emerald-600 text-white']"
        >
          <ShieldAlert v-if="protectionEnabled" class="h-4 w-4" />
          <ShieldCheck v-else class="h-4 w-4" />
          <span>{{ togglingProtection ? 'Updating...' : (protectionEnabled ? 'Disable Protection' : 'Enable Protection') }}</span>
        </button>
        <button 
          @click="syncAdguard" 
          :disabled="syncing || !isConfigured"
          class="btn-primary !px-4 !py-2.5 rounded-xl text-sm font-semibold transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shadow-sm flex items-center gap-2 border-none"
        >
          <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': syncing }" />
          <span>{{ syncing ? 'Syncing...' : 'Sync Now' }}</span>
        </button>
      </div>
    </div>

    <!-- Protection Disabled Warning -->
    <div v-if="isConfigured && isVerified && !protectionEnabled && !loading" class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-2xl p-4 text-red-700 dark:text-red-400 text-sm flex items-start gap-3 shadow-sm">
      <ShieldAlert class="h-5 w-5 mt-0.5 shrink-0 text-red-600 dark:text-red-400" />
      <div>
        <h4 class="font-bold text-base">Protection Disabled</h4>
        <p class="mt-1 text-red-600/80 dark:text-red-400/80">
          AdGuard protection is currently turned off. Your network devices are not being shielded against ads, trackers, or malicious domains. It is highly recommended to keep protection enabled.
        </p>
      </div>
    </div>

    <!-- Error State -->
    <div v-if="error" class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-2xl p-4 text-red-700 dark:text-red-400 text-sm flex items-start gap-3">
      <ShieldAlert class="h-5 w-5 mt-0.5 shrink-0 text-red-650 dark:text-red-450" />
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
              <Search class="h-5 w-5" />
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
              <ShieldAlert class="h-5 w-5" />
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
              <Activity class="h-5 w-5" />
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
              <Clock class="h-5 w-5" />
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
          <Ban class="h-5 w-5 text-rose-500" />
          <span>Recently Blocked Queries</span>
        </h3>

        <div class="bg-white dark:bg-slate-800 border border-slate-200/60 dark:border-slate-700/60 rounded-2xl overflow-hidden shadow-sm">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-slate-100 dark:divide-slate-800/70">
              <thead class="bg-transparent">
                <tr class="border-b border-slate-100 dark:border-slate-800/70">
                  <th class="table-header-cell text-left px-6 py-4">Timestamp</th>
                  <th class="table-header-cell text-left px-6 py-4">Domain Name</th>
                  <th class="table-header-cell text-left px-6 py-4">Client IP</th>
                  <th class="table-header-cell text-center px-6 py-4">Type</th>
                  <th class="table-header-cell text-left px-6 py-4">Filter Reason</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-800/70">
                <tr 
                  v-for="(log, idx) in paginatedBlocked" 
                  :key="idx"
                  class="hover-row group"
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

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="flex justify-end items-center gap-2 p-4 border-t border-slate-100 dark:border-slate-700/50 bg-slate-50/50 dark:bg-slate-900/30 rounded-b-2xl">
          <button @click="changePage(currentPage - 1)" :disabled="currentPage <= 1" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 disabled:opacity-50 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">
            Previous
          </button>
          <div class="px-4 py-1.5 bg-slate-900 dark:bg-white rounded-lg text-sm font-medium text-white dark:text-slate-900">
            {{ currentPage }} / {{ totalPages }}
          </div>
          <button @click="changePage(currentPage + 1)" :disabled="currentPage >= totalPages" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 disabled:opacity-50 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">
            Next
          </button>
        </div>
      </div>
    </template>

    <div v-else class="bg-white dark:bg-slate-800 rounded-2xl p-8 border border-slate-200/60 dark:border-slate-700/60 text-center shadow-sm">
      <div class="max-w-md mx-auto space-y-4">
        <div class="w-16 h-16 bg-amber-50 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400 rounded-full flex items-center justify-center mx-auto">
          <ShieldAlert class="h-8 w-8 text-amber-600 dark:text-amber-450" />
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
            class="btn-primary !px-4 !py-2.5 rounded-xl text-sm font-semibold transition-all active:scale-95 shadow-sm inline-flex items-center justify-center cursor-pointer border-none"
          >
            Go to Settings
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/utils/api'
import { useNotifications } from '@/composables/useNotifications'

// PrimeVue components
import Button from 'primevue/button'

import {
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Search,
  Activity,
  Clock,
  Ban
} from 'lucide-vue-next'

const { notifySuccess, notifyError } = useNotifications()

const loading = ref(true)
const syncing = ref(false)
const error = ref(null)

const isConfigured = ref(false)
const isVerified = ref(false)
const url = ref('')
const stats = ref(null)
const recentBlocked = ref([])

const protectionEnabled = ref(false)
const togglingProtection = ref(false)

// Pagination
const currentPage = ref(1)
const itemsPerPage = 10
const totalPages = computed(() => Math.ceil(recentBlocked.value.length / itemsPerPage) || 1)
const paginatedBlocked = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  return recentBlocked.value.slice(start, start + itemsPerPage)
})
const changePage = (p) => {
  if (p >= 1 && p <= totalPages.value) {
    currentPage.value = p
  }
}

const fetchAdguardData = async () => {
  loading.value = true
  error.value = null
  try {
    const res = await api.get('/integrations/adguard/data')
    isConfigured.value = res.data.enabled
    isVerified.value = res.data.verified
    url.value = res.data.url || ''
    stats.value = res.data.stats
    protectionEnabled.value = res.data.protection_enabled || false
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

const toggleProtection = async () => {
  togglingProtection.value = true
  try {
    const newState = !protectionEnabled.value
    await api.post('/integrations/adguard/protection', { enabled: newState })
    protectionEnabled.value = newState
    notifySuccess(newState ? 'AdGuard protection enabled' : 'AdGuard protection disabled')
  } catch (err) {
    console.error('Failed to toggle Adguard protection:', err)
    notifyError(err.response?.data?.detail || 'Failed to toggle protection state.')
  } finally {
    togglingProtection.value = false
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
