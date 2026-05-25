<template>
  <div class="space-y-6">
    <!-- Header Card -->
    <div class="bg-white/80 dark:bg-slate-800/80 backdrop-blur-md rounded-2xl p-6 border border-slate-200/50 dark:border-slate-700/50 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
          <span>Tailscale VPN Integration</span>
          <span :class="[
            'px-2 py-0.5 text-xs font-semibold rounded-full uppercase tracking-wider',
            isConfigured
              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-400'
              : 'bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-400'
          ]">
            {{ isConfigured ? 'Connected' : 'Not Configured' }}
          </span>
        </h2>
        <p v-if="tailnet" class="text-xs font-mono text-slate-400 dark:text-slate-500 mt-1 truncate max-w-sm sm:max-w-md">
          Tailnet: {{ tailnet }}
        </p>
      </div>

      <div class="flex items-center gap-3">
        <button 
          @click="syncTailscale" 
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

    <template v-else-if="isConfigured">
      <!-- Synced Devices Table -->
      <div class="space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <h3 class="text-lg font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
            <svg class="h-5 w-5 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Active Tailnet Nodes ({{ filteredDevices.length }})</span>
          </h3>

          <div class="relative w-full sm:max-w-xs">
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="Search Tailscale devices..." 
              class="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
            <svg class="absolute left-3 top-2.5 h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        <div class="content-panel">
          <DeviceTable
            :devices="filteredDevices"
            :columns="['device', 'network', 'last_seen', 'actions']"
            :approvingId="approvingId"
            @approve="approveDevice"
            @edit="openEditDialog"
            @delete="confirmDelete"
          >
            <!-- Mobile details slot -->
            <template #extra-mobile-details="{ device }">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <p class="text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">Tailscale OS</p>
                  <span class="text-xs text-slate-600 dark:text-slate-400 font-semibold">
                    {{ device.os || 'Unknown' }}
                  </span>
                </div>
              </div>
            </template>
          </DeviceTable>
        </div>

        <!-- Modals -->
        <EditDeviceModal 
          :isOpen="isEditModalOpen" 
          :device="deviceToEdit" 
          @close="isEditModalOpen = false"
          @save="handleDeviceSaved" 
        />

        <ConfirmationModal
          :isOpen="!!deviceToDelete"
          title="Delete Device?"
          :message="deviceToDelete ? `Are you sure you want to delete ${deviceToDelete.display_name || deviceToDelete.ip}? This action cannot be undone.` : ''"
          confirmText="Delete"
          type="danger"
          @close="cancelDelete"
          @confirm="deleteDevice"
        />

        <ConfirmationModal
          :isOpen="!!deviceToApprove"
          title="Trust this Device?"
          :message="deviceToApprove ? `You are about to mark ${deviceToApprove.display_name || deviceToApprove.ip} as a trusted member of your network.` : ''"
          confirmText="Trust Device"
          :loading="!!approvingId"
          @close="deviceToApprove = null"
          @confirm="confirmApprove"
        />
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
          <h3 class="text-lg font-bold text-slate-800 dark:text-slate-100">Tailscale integration is inactive</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Please make sure that the integration is enabled and credentials are configured in Settings page.
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
import DeviceTable from '@/components/DeviceTable.vue'
import ConfirmationModal from '@/components/ConfirmationModal.vue'
import EditDeviceModal from '@/components/EditDeviceModal.vue'

const { notifySuccess, notifyError } = useNotifications()

const loading = ref(true)
const syncing = ref(false)
const error = ref(null)

const isConfigured = ref(false)
const tailnet = ref('-')
const devices = ref([])
const searchQuery = ref('')

// Action states
const deviceToEdit = ref(null)
const isEditModalOpen = ref(false)
const deviceToDelete = ref(null)
const deviceToApprove = ref(null)
const approvingId = ref(null)

const fetchTailscaleData = async () => {
  loading.value = true
  error.value = null
  try {
    const configRes = await api.get('/integrations/tailscale/config')
    isConfigured.value = configRes.data.enabled && !!configRes.data.api_key
    tailnet.value = configRes.data.tailnet || '-'
    
    if (isConfigured.value) {
      const devRes = await api.get('/integrations/tailscale/devices')
      devices.value = devRes.data || []
    }
  } catch (err) {
    console.error('Error fetching Tailscale data:', err)
    error.value = err.response?.data?.detail || 'Failed to load Tailscale integration details.'
  } finally {
    loading.value = false
  }
}

// Action handlers implementation
const approveDevice = (device) => {
  deviceToApprove.value = device
}

const confirmApprove = async () => {
  if (!deviceToApprove.value) return
  const device = deviceToApprove.value
  approvingId.value = device.id
  try {
    await api.patch(`/integrations/tailscale/devices/${device.id}`, { is_trusted: true })
    await fetchTailscaleData()
    notifySuccess(`"${device.display_name || device.ip}" is now trusted`)
    deviceToApprove.value = null
  } catch (e) {
    notifyError('Failed to approve device')
  } finally {
    approvingId.value = null
  }
}

const confirmDelete = (device) => {
  deviceToDelete.value = device
}

const cancelDelete = () => {
  deviceToDelete.value = null
}

const deleteDevice = async () => {
  if (!deviceToDelete.value) return
  try {
    await api.delete(`/integrations/tailscale/devices/${deviceToDelete.value.id}`)
    await fetchTailscaleData()
    notifySuccess('Device deleted successfully')
    deviceToDelete.value = null
  } catch (e) {
    notifyError('Failed to delete device')
  }
}

const openEditDialog = (device) => {
  deviceToEdit.value = { ...device }
  isEditModalOpen.value = true
}

const handleDeviceSaved = async () => {
  await fetchTailscaleData()
}

const syncTailscale = async () => {
  syncing.value = true
  try {
    await api.post('/integrations/tailscale/sync')
    notifySuccess('Tailscale synchronization queued in background')
    setTimeout(fetchTailscaleData, 2000)
  } catch (err) {
    console.error('Failed to trigger Tailscale sync:', err)
    notifyError(err.response?.data?.detail || 'Failed to start Tailscale synchronization.')
  } finally {
    syncing.value = false
  }
}

const filteredDevices = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  if (!query) return devices.value
  return devices.value.filter(d => 
    d.name?.toLowerCase().includes(query) || 
    (d.ip && d.ip.toLowerCase().includes(query))
  )
})

onMounted(() => {
  fetchTailscaleData()
})
</script>
