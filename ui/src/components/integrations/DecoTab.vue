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
          class="btn-primary !px-4 !py-2.5 rounded-xl text-sm font-semibold transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shadow-sm flex items-center gap-2 border-none"
        >
          <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': syncing }" />
          <span>{{ syncing ? 'Syncing...' : 'Sync Now' }}</span>
        </button>
      </div>
    </div>

    <!-- Error State -->
    <div v-if="error" class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-2xl p-4 text-red-700 dark:text-red-400 text-sm flex items-start gap-3">
      <AlertTriangle class="h-5 w-5 mt-0.5 shrink-0 text-red-600 dark:text-red-450" />
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
          <Cpu class="h-5 w-5 text-blue-500" />
          <span>Mesh Nodes ({{ nodes.length }})</span>
        </h3>

        <!-- Only 1 Node Warning Notice -->
        <div v-if="nodes.length === 1" class="p-4 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/50 rounded-2xl flex items-start gap-3">
          <AlertTriangle class="h-5 w-5 text-amber-600 dark:text-amber-500 shrink-0 mt-0.5" />
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
                <div class="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-500/10 flex items-center justify-center text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform overflow-hidden">
                  <img v-if="node.icon && node.icon.startsWith('/static/')" :src="node.icon" class="h-6 w-6 object-contain" />
                  <component :is="getIcon(node.icon)" v-else-if="node.icon" class="h-6 w-6" />
                  <Wifi v-else class="w-6 h-6" />
                </div>
                <div>
                  <h4 class="font-bold text-slate-800 dark:text-slate-100">{{ node.display_name || node.attributes.deco_node_name || node.name }}</h4>
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
            <Users class="h-5 w-5 text-indigo-500" />
            <span>Connected Clients ({{ filteredClients.length }})</span>
          </h3>
          
          <IconField class="w-full sm:max-w-xs">
            <InputIcon>
              <Search class="h-4 w-4 text-slate-400" />
            </InputIcon>
            <InputText 
              v-model="searchQuery"
              placeholder="Search clients..."
              class="w-full"
              :pt="{ root: 'input-base' }"
            />
          </IconField>
        </div>

        <div class="content-panel">
          <DeviceTable
            :devices="filteredClients"
            :columns="['device', 'network', 'deco_node', 'last_seen', 'actions']"
            :approvingId="approvingId"
            :blockingId="blockingId"
            @approve="approveDevice"
            @block-toggle="toggleBlockList"
            @edit="openEditDialog"
            @delete="confirmDelete"
          >
            <!-- Deco Node / RSSI Header slot -->
            <template #extra-headers>
              <th class="hidden md:table-cell table-header-cell w-1/5">Connected Node</th>
              <th class="hidden md:table-cell table-header-cell w-1/5 text-center">Signal Strength</th>
            </template>
            
            <!-- Deco Node / RSSI Row slot -->
            <template #extra-cells="{ device: client }">
              <!-- Connected Node -->
              <td class="hidden md:table-cell table-data-cell">
                <div class="flex items-center gap-2">
                  <div class="w-1.5 h-1.5 rounded-full bg-blue-500"></div>
                  <span class="text-slate-700 dark:text-slate-300 font-medium">
                    {{ client.attributes.deco_node || 'Deco Node' }}
                  </span>
                </div>
              </td>
              
              <!-- RSSI Signal Indicator -->
              <td class="hidden md:table-cell table-data-cell">
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
            </template>

            <!-- Mobile details slot -->
            <template #extra-mobile-details="{ device: client }">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <p class="text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">Connected Node</p>
                  <p class="text-sm text-slate-700 dark:text-slate-300">
                    {{ client.attributes.deco_node || 'Deco Node' }}
                  </p>
                </div>
                <div>
                  <p class="text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">Signal Strength</p>
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-mono font-bold" :class="getSignalTextClass(client.attributes.rssi)">
                      {{ client.attributes.rssi ? `${client.attributes.rssi} dBm` : 'N/A' }}
                    </span>
                  </div>
                </div>
              </div>
            </template>
          </DeviceTable>
        </div>
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
    </template>

    <div v-else class="bg-white dark:bg-slate-800 rounded-2xl p-8 border border-slate-200/60 dark:border-slate-700/60 text-center shadow-sm">
      <div class="max-w-md mx-auto space-y-4">
        <div class="w-16 h-16 bg-amber-50 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400 rounded-full flex items-center justify-center mx-auto">
          <AlertTriangle class="h-8 w-8 text-amber-600 dark:text-amber-450" />
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
import { ref, computed, onMounted } from 'vue'
import api from '@/utils/api'
import { useNotifications } from '@/composables/useNotifications'
import { getIcon } from '@/utils/icons'
import DeviceTable from '@/components/DeviceTable.vue'
import ConfirmationModal from '@/components/ConfirmationModal.vue'
import EditDeviceModal from '@/components/EditDeviceModal.vue'

// PrimeVue components
import Button from 'primevue/button'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'

import {
  RefreshCw,
  AlertTriangle,
  Cpu,
  Wifi,
  Users,
  Search
} from 'lucide-vue-next'

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

// Action states
const deviceToEdit = ref(null)
const isEditModalOpen = ref(false)
const deviceToDelete = ref(null)
const deviceToApprove = ref(null)
const approvingId = ref(null)
const blockingId = ref(null)

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

// Actions implementation
const approveDevice = (device) => {
  deviceToApprove.value = device
}

const confirmApprove = async () => {
  if (!deviceToApprove.value) return
  const device = deviceToApprove.value
  approvingId.value = device.id
  try {
    await api.patch(`/devices/${device.id}`, { is_trusted: true })
    await fetchDecoData()
    notifySuccess(`"${device.display_name || device.ip}" is now trusted`)
    deviceToApprove.value = null
  } catch (e) {
    notifyError('Failed to approve device')
  } finally {
    approvingId.value = null
  }
}

const toggleBlockList = async (device) => {
  if (!device.mac || device.mac === 'unknown' || device.mac === 'N/A') {
    notifyError('Cannot block device without a valid MAC address')
    return
  }
  blockingId.value = device.id
  const action = device.is_blocked ? 'unblock' : 'block'
  try {
    const res = await api.post(`/integrations/openwrt/devices/${device.mac}/${action}`)
    if (res.data.status === 'success') {
      device.is_blocked = !device.is_blocked
      notifySuccess(`Device ${device.is_blocked ? 'blocked' : 'unblocked'} successfully`)
    }
  } catch (err) {
    notifyError(err.response?.data?.detail || `Failed to ${action} device`)
  } finally {
    blockingId.value = null
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
    await api.delete(`/devices/${deviceToDelete.value.id}`)
    await fetchDecoData()
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
  await fetchDecoData()
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
    (c.attributes?.deco_node && c.attributes.deco_node.toLowerCase().includes(query))
  )
})

onMounted(() => {
  fetchDecoData()
})
</script>
