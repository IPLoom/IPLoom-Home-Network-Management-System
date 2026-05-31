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
          class="btn-primary !px-4 !py-2.5 rounded-xl text-sm font-semibold transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shadow-sm flex items-center gap-2 border-none"
        >
          <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': syncing }" />
          <span>{{ syncing ? 'Syncing...' : 'Sync Now' }}</span>
        </button>
      </div>
    </div>

    <!-- Error State -->
    <div v-if="error" class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-2xl p-4 text-red-700 dark:text-red-400 text-sm flex items-start gap-3">
      <AlertTriangle class="h-5 w-5 mt-0.5 shrink-0 text-red-650 dark:text-red-450" />
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
            <Cpu class="h-5 w-5 text-teal-500" />
            <span>Active DHCP / Wireless Leases ({{ filteredDevices.length }})</span>
          </h3>

          <IconField class="w-full sm:max-w-xs">
            <InputIcon>
              <Search class="w-4 h-4 text-slate-400" />
            </InputIcon>
            <InputText 
              v-model="searchQuery" 
              placeholder="Search OpenWrt devices..." 
              class="w-full"
              :pt="{ root: 'input-base' }"
            />
          </IconField>
        </div>

        <div class="content-panel">
          <DeviceTable
            :devices="filteredDevices"
            :columns="['device', 'network', 'interface', 'last_seen', 'actions']"
            :approvingId="approvingId"
            :blockingId="blockingId"
            @approve="approveDevice"
            @block-toggle="toggleBlockList"
            @edit="openEditDialog"
            @delete="confirmDelete"
          >
            <!-- Interface / Network slot headers -->
            <template #extra-headers>
              <th class="hidden md:table-cell table-header-cell w-1/5 font-bold">Interface / Network</th>
            </template>
            
            <!-- Interface / Network slot cells -->
            <template #extra-cells="{ device }">
              <td class="hidden md:table-cell table-data-cell">
                <span class="text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-900 px-2.5 py-1 rounded-md border border-slate-200/40 dark:border-slate-800/40 font-semibold">
                  {{ device.attributes?.interface || 'lan' }}
                </span>
              </td>
            </template>

            <!-- Mobile details slot -->
            <template #extra-mobile-details="{ device }">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <p class="text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">Interface / Network</p>
                  <span class="text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-900 px-2.5 py-1 rounded-md border border-slate-200/40 dark:border-slate-800/40 font-semibold">
                    {{ device.attributes?.interface || 'lan' }}
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
          <AlertTriangle class="h-8 w-8 text-amber-600 dark:text-amber-450" />
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
  Search
} from 'lucide-vue-next'

const { notifySuccess, notifyError } = useNotifications()

const loading = ref(true)
const syncing = ref(false)
const error = ref(null)

const isConfigured = ref(false)
const isVerified = ref(false)
const url = ref('')
const devices = ref([])
const searchQuery = ref('')

// Action states
const deviceToEdit = ref(null)
const isEditModalOpen = ref(false)
const deviceToDelete = ref(null)
const deviceToApprove = ref(null)
const approvingId = ref(null)
const blockingId = ref(null)

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

// Action handlers implementation
const approveDevice = (device) => {
  deviceToApprove.value = device
}

const confirmApprove = async () => {
  if (!deviceToApprove.value) return
  const device = deviceToApprove.value
  approvingId.value = device.id
  try {
    await api.patch(`/devices/${device.id}`, { is_trusted: true })
    await fetchOpenWrtData()
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
    await fetchOpenWrtData()
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
  await fetchOpenWrtData()
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
