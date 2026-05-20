<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="text-2xl font-semibold text-slate-900 dark:text-white">Devices</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">{{ globalStats.total }} devices discovered</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="btn-group">
          <button @click="exportDevices"
            class="px-3 py-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-l-lg transition text-slate-600 dark:text-slate-400 flex items-center gap-2 text-xs font-medium"
            v-tooltip="'Export Devices to JSON'">
            <Download class="h-4 w-4" />
            <span class="hidden sm:inline">Export</span>
          </button>
          <div class="w-px bg-slate-200 dark:bg-slate-700"></div>
          <button @click="$refs.importInput.click()"
            class="px-3 py-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-r-lg transition text-slate-600 dark:text-slate-400 flex items-center gap-2 text-xs font-medium"
            v-tooltip="'Import Devices from JSON'">
            <Upload class="h-4 w-4" />
            <span class="hidden sm:inline">Import</span>
          </button>
        </div>
        <input type="file" ref="importInput" class="hidden" @change="handleImport" accept=".json" />
        
        <button @click="isDiscoveryOpen = true" 
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-[11px] font-black uppercase tracking-widest transition-all shadow-lg shadow-blue-500/20 flex items-center gap-2"
          v-tooltip="'Quick Scan for New Devices'">
          <Radar class="w-4 h-4" />
          Find New
        </button>

        <button @click="triggerScan" :disabled="isScanning" class="btn-action"
          v-tooltip="isScanning ? 'Scanning Network...' : 'Scan Network'">
          <component :is="isScanning ? Loader2 : RefreshCw" class="w-5 h-5" :class="{ 'animate-spin': isScanning }" />
        </button>
      </div>
    </div>



    <!-- Quick Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div v-for="stat in deviceStats" :key="stat.label" class="card-stat group">

        <!-- Sparkline Background -->
        <Sparkline :data="stat.trend" :color="stat.color" class="opacity-15" />

        <!-- Header Row -->
        <div class="relative z-10 flex items-center justify-between w-full">
          <div :class="[stat.bgClass, 'p-1.5 rounded-lg shadow-sm border border-white/10']">
            <component :is="stat.icon" class="h-4 w-4" />
          </div>
          <div v-if="stat.change"
            class="flex items-center gap-1 bg-white/50 dark:bg-slate-900/40 px-2 py-0.5 rounded-full backdrop-blur-sm border border-slate-200/50 dark:border-slate-700/50">
            <span :class="[stat.changeType === 'down' ? 'text-rose-500' : 'text-emerald-600', 'text-[10px] font-bold']">
              {{ stat.change }}
            </span>
          </div>
        </div>

        <!-- Center Content -->
        <div class="relative z-10 flex flex-col items-center text-center -mt-1">
          <p class="text-2xl font-black text-slate-900 dark:text-white tracking-tight leading-none">
            {{ stat.value }}
          </p>
          <p :class="stat.textColor" class="text-[9px] font-black uppercase tracking-[0.2em] opacity-80 mt-1">
            {{ stat.label }}
          </p>
        </div>
      </div>
    </div>

    <!-- Filters & Search -->
    <div class="glass-panel flex flex-col gap-4">
      <div class="flex flex-col md:flex-row gap-4 items-center">
        <div class="relative flex-1 w-full">
          <Search class="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input v-model="search" @input="debounceFetch" type="text" placeholder="Search IP, Mac, Vendor or Name..."
            class="input-base" />
        </div>
        <div class="flex flex-col sm:flex-row items-center gap-3 w-full md:w-auto">
          <!-- Status Filter -->
          <div class="relative flex-1 md:w-44 group" v-click-outside="() => isStatusOpen = false">
            <button @click="isStatusOpen = !isStatusOpen"
              class="w-full flex items-center justify-between pl-4 pr-3.5 py-2 bg-slate-100/50 dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-700/50 rounded-xl outline-none hover:ring-2 hover:ring-blue-500/10 transition-all text-sm font-medium text-slate-700 dark:text-slate-300">
              <div class="flex items-center gap-2.5">
                <Filter class="h-3.5 w-3.5" :class="statusFilter ? 'text-blue-500' : 'text-slate-400'" />
                <span>{{ statusFilter ? (statusFilter.charAt(0).toUpperCase() + statusFilter.slice(1)) : 'All Statuses'
                }}</span>
              </div>
              <ChevronDown class="h-4 w-4 text-slate-400 transition-transform duration-200"
                :class="{ 'rotate-180': isStatusOpen }" />
            </button>

            <transition enter-active-class="transition duration-100 ease-out"
              enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100"
              leave-active-class="transition duration-75 ease-in" leave-from-class="transform scale-100 opacity-100"
              leave-to-class="transform scale-95 opacity-0">
              <div v-if="isStatusOpen"
                class="absolute z-[60] mt-2 w-full bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl py-1.5 overflow-hidden">
                <button v-for="opt in ['', 'online', 'offline']" :key="opt"
                  @click="statusFilter = opt; isStatusOpen = false; fetchDevices()"
                  class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors"
                  :class="statusFilter === opt ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                  <div class="w-2 h-2 rounded-full"
                    :class="opt === 'online' ? 'bg-emerald-500' : opt === 'offline' ? 'bg-slate-400' : 'bg-transparent border border-slate-300'">
                  </div>
                  {{ opt === '' ? 'All Statuses' : opt.charAt(0).toUpperCase() + opt.slice(1) }}
                </button>
              </div>
            </transition>
          </div>

          <!-- Type Filter -->
          <div class="relative flex-1 md:w-44 group" v-click-outside="() => isTypeOpen = false">
            <button @click="isTypeOpen = !isTypeOpen"
              class="w-full flex items-center justify-between pl-4 pr-3.5 py-2 bg-slate-100/50 dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-700/50 rounded-xl outline-none hover:ring-2 hover:ring-blue-500/10 transition-all text-sm font-medium text-slate-700 dark:text-slate-300">
              <div class="flex items-center gap-2.5">
                <Layers class="h-3.5 w-3.5" :class="typeFilter ? 'text-blue-500' : 'text-slate-400'" />
                <span class="truncate">{{ typeFilter || 'All Types' }}</span>
              </div>
              <ChevronDown class="h-4 w-4 text-slate-400 transition-transform duration-200"
                :class="{ 'rotate-180': isTypeOpen }" />
            </button>

            <transition enter-active-class="transition duration-100 ease-out"
              enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100"
              leave-active-class="transition duration-75 ease-in" leave-from-class="transform scale-100 opacity-100"
              leave-to-class="transform scale-95 opacity-0">
              <div v-if="isTypeOpen"
                class="absolute z-[60] mt-2 w-full bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl py-1.5 overflow-y-auto max-h-60 scrollbar-hide">
                <button @click="typeFilter = ''; isTypeOpen = false; fetchDevices()"
                  class="w-full px-4 py-2 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors"
                  :class="typeFilter === '' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                  All Types
                </button>
                <button v-for="type in deviceTypes" :key="type"
                  @click="typeFilter = type; isTypeOpen = false; fetchDevices()"
                  class="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-left hover:bg-blue-600 hover:text-white transition-colors"
                  :class="typeFilter === type ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                  <component :is="getIcon(type.toLowerCase())" class="h-3.5 w-3.5 opacity-60" />
                  {{ type }}
                </button>
              </div>
            </transition>
          </div>
        </div>
      </div>
      <!-- Display Info Line -->
      <div class="px-2 flex items-center justify-between text-[11px] font-medium text-slate-500 dark:text-slate-400">
        <div class="flex items-center gap-2">
          <Activity class="h-3.5 w-3.5 text-blue-500" />
          <span>Showing <b>{{ devices.length }}</b> of <b>{{ totalDevices }}</b> devices matching current filters</span>
        </div>
        <div v-if="sortBy" class="hidden sm:block text-[10px] uppercase tracking-wider opacity-60">
          Sorted by {{ sortBy }} ({{ sortOrder }})
        </div>
      </div>
    </div>

    <!-- Devices Table -->
    <div class="content-panel">
      <DeviceTable
        :devices="devices"
        :columns="['device', 'network', 'activity', 'ports', 'type', 'last_seen', 'actions']"
        :approvingId="approvingId"
        :blockingId="blockingId"
        :sortBy="sortBy"
        :sortOrder="sortOrder"
        @sort="toggleSort"
        @approve="approveDevice"
        @block-toggle="toggleBlockList"
        @edit="openEditDialog"
        @delete="confirmDelete"
      />
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex justify-center items-center gap-2">
      <button @click="changePage(currentPage - 1)" :disabled="currentPage <= 1" class="pagination-btn">
        Previous
      </button>
      <button @click="fetchDevices" class="btn-action !p-2" v-tooltip="'Refresh List'">
        <RefreshCw class="h-5 w-5" :class="{ 'animate-spin': loading }" />
      </button>
      <div class="px-4 py-2 bg-slate-900 dark:bg-white rounded-lg text-sm font-medium text-white dark:text-slate-900">
        {{ currentPage }} / {{ totalPages }}
      </div>
      <button @click="changePage(currentPage + 1)" :disabled="currentPage >= totalPages" class="pagination-btn">
        Next
      </button>
    </div>

    <!-- Edit Modal -->
    <EditDeviceModal :isOpen="isEditModalOpen" :device="deviceToEdit" @close="isEditModalOpen = false"
      @save="handleDeviceSaved" />

    <!-- Delete Confirmation Modal -->
    <ConfirmationModal
      :isOpen="!!deviceToDelete"
      title="Delete Device?"
      :message="deviceToDelete ? `Are you sure you want to delete ${deviceToDelete.display_name || deviceToDelete.ip}? This action cannot be undone.` : ''"
      confirmText="Delete"
      type="danger"
      @close="cancelDelete"
      @confirm="deleteDevice"
    />

    <!-- Approve Confirmation Modal -->
    <ConfirmationModal
      :isOpen="!!deviceToApprove"
      title="Trust this Device?"
      :message="deviceToApprove ? `You are about to mark ${deviceToApprove.display_name || deviceToApprove.ip} as a trusted member of your network.` : ''"
      confirmText="Trust Device"
      :loading="!!approvingId"
      @close="deviceToApprove = null"
      @confirm="confirmApprove"
    />

    <!-- Discovery Modal -->
    <DiscoveryModal :isOpen="isDiscoveryOpen" @close="isDiscoveryOpen = false" @onboarded="fetchDevices" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, reactive, computed, watch } from 'vue'
import api from '@/utils/api'
import Sparkline from '@/components/Sparkline.vue'
import EditDeviceModal from '@/components/EditDeviceModal.vue'
import DiscoveryModal from '@/components/DiscoveryModal.vue'
import DeviceTable from '@/components/DeviceTable.vue'
import ConfirmationModal from '@/components/ConfirmationModal.vue'
import { getIcon } from '@/utils/icons'
import * as LucideIcons from 'lucide-vue-next'
const { Download, Upload, RefreshCw, Loader2, Search, ChevronUp, ChevronDown, ChevronRight, ArrowUpDown, Activity, Wifi, Network, Database, ZapOff, Ticket, Filter, Layers, ShieldCheck, ShieldAlert, Radar, Ban, Zap, Clock } = LucideIcons
import { DateTime } from 'luxon'
import { formatRelativeTime, parseUTC } from '@/utils/date'
import { useNotifications } from '@/composables/useNotifications'
import { useWebSockets } from '@/composables/useWebSockets'

const { lastNotification } = useWebSockets()
const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const isNewDevice = (firstSeen) => {
  if (!firstSeen) return false
  try {
    const firstSeenDate = DateTime.fromISO(firstSeen)
    return DateTime.now().diff(firstSeenDate, 'hours').hours < 24
  } catch (e) {
    return false
  }
}

watch(lastNotification, (notif) => {
  if (notif && (notif.event_type === 'new_device' || notif.event_type === 'status_changed' || notif.event_type === 'completed')) {
    fetchDevices()
  }
})

const devices = ref([])
const totalDevices = ref(0)
const globalStats = ref({ total: 0, online: 0, offline: 0, top_vendor: 'None', top_vendor_count: 0 })
const currentPage = ref(1)
const totalPages = ref(1)
const limit = ref(20)

const isStatusOpen = ref(false)
const isTypeOpen = ref(false)
const expandedRows = ref(new Set())

const toggleRow = (id) => {
  if (expandedRows.value.has(id)) {
    expandedRows.value.delete(id)
  } else {
    expandedRows.value.add(id)
  }
}

const search = ref('')
const statusFilter = ref('')
const typeFilter = ref('')
const sortBy = ref('ip')
const sortOrder = ref('asc')

const isScanning = ref(false)
const isDiscoveryOpen = ref(false)
const loading = ref(false)
const approvingId = ref(null)
const deviceToApprove = ref(null)
const isEditModalOpen = ref(false)
const deviceToEdit = ref(null)

const { notifySuccess, notifyError } = useNotifications()

const tableHeaders = [
  { key: 'display_name', label: 'Device', class: 'md:w-1/4' },
  { key: 'mac', label: 'Network Info', class: 'hidden md:table-cell w-1/5' },
  { key: 'activity', label: 'Activity', class: 'hidden md:table-cell w-1/6' },
  { key: 'open_ports', label: 'Open Ports', class: 'hidden md:table-cell w-1/6' },
  { key: 'device_type', label: 'Type', class: 'hidden md:table-cell w-1/12' },
  { key: 'last_seen', label: 'Last Seen', class: 'hidden md:table-cell w-1/12' },
]

import { useSystemStore } from '@/stores/system'
const systemStore = useSystemStore()

const deviceTypes = computed(() => {
  return systemStore.deviceTypes
})


const getSortIcon = (key) => {
  if (sortBy.value !== key) return ArrowUpDown
  return sortOrder.value === 'asc' ? ChevronUp : ChevronDown
}

const toggleSort = (key) => {
  if (sortBy.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = key
    sortOrder.value = 'asc'
  }
  fetchDevices()
}

const changePage = (page) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchDevices()
}

const getDeviceStatusColor = (device) => {
  if (device.status === 'online') return 'bg-emerald-500'
  if (device.status === 'offline') return 'bg-slate-400'
  return 'bg-slate-300'
}

const deviceStats = computed(() => {
  return [
    {
      label: 'Total Devices',
      value: globalStats.value.total,
      icon: LucideIcons.Database,
      color: '#3b82f6',
      textColor: 'text-blue-500',
      bgClass: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
      trend: [10, 12, 11, 13, 12, 14, 13, 15, 14, 16],
      change: '+2.4%',
      changeType: 'up'
    },
    {
      label: 'Online',
      value: globalStats.value.online,
      icon: LucideIcons.Wifi,
      color: '#10b981',
      textColor: 'text-emerald-500',
      bgClass: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400',
      trend: [8, 9, 7, 10, 9, 11, 10, 12, 11, 13],
      change: 'Active',
      changeType: 'up'
    },
    {
      label: 'Offline',
      value: globalStats.value.offline,
      icon: LucideIcons.ZapOff,
      color: '#f43f5e',
      textColor: 'text-rose-500',
      bgClass: 'bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400',
      trend: [2, 3, 4, 3, 3, 3, 3, 3, 3, 3],
      change: 'Standby',
      changeType: 'down'
    },
    {
      label: 'Top Vendor',
      value: (globalStats.value.top_vendor && typeof globalStats.value.top_vendor === 'string' && globalStats.value.top_vendor.length > 10) ? globalStats.value.top_vendor.substring(0, 8) + '..' : (globalStats.value.top_vendor || 'None'),
      icon: LucideIcons.Ticket,
      color: '#8b5cf6',
      textColor: 'text-violet-500',
      bgClass: 'bg-violet-100 text-violet-600 dark:bg-violet-900/30 dark:text-violet-400',
      trend: [5, 6, 5, 7, 6, 8, 7, 9, 8, 10],
      change: `count: ${globalStats.value.top_vendor_count}`,
      changeType: 'up'
    }
  ]
})


const fetchDevices = async () => {
  loading.value = true
  try {
    const res = await api.get('/devices/', {
      params: {
        page: currentPage.value,
        limit: limit.value,
        search: search.value || undefined,
        status: statusFilter.value || undefined,
        device_type: typeFilter.value || undefined,
        sort_by: sortBy.value,
        sort_order: sortOrder.value
      }
    })
    devices.value = res.data.items
    totalDevices.value = res.data.total
    totalPages.value = res.data.total_pages
    if (res.data.global_stats) {
      globalStats.value = res.data.global_stats
    }
  } catch (e) {
    notifyError('Failed to load devices')
    console.error(e)
  } finally {
    loading.value = false
  }
}

let debounceTimer = null
const debounceFetch = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    currentPage.value = 1
    fetchDevices()
  }, 300)
}

const triggerScan = async () => {
  isScanning.value = true
  try {
    await api.post('/scans/discovery')
    await new Promise(resolve => setTimeout(resolve, 2000))
    await fetchDevices()
  } catch (e) {
    notifyError('Scan failed')
  } finally {
    isScanning.value = false
  }
}

const approveDevice = (device) => {
  deviceToApprove.value = device
}

const blockingId = ref(null)
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

const confirmApprove = async () => {
  if (!deviceToApprove.value) return
  
  const device = deviceToApprove.value
  approvingId.value = device.id
  try {
    await api.patch(`/devices/${device.id}`, { is_trusted: true })
    await fetchDevices()
    notifySuccess(`"${device.display_name || device.ip}" is now trusted`)
    deviceToApprove.value = null
  } catch (e) {
    notifyError('Failed to approve device')
  } finally {
    approvingId.value = null
  }
}

const deviceToDelete = ref(null)
const confirmDelete = (device) => { deviceToDelete.value = device }
const cancelDelete = () => { deviceToDelete.value = null }

const deleteDevice = async () => {
  if (!deviceToDelete.value) return
  try {
    await api.delete(`/devices/${deviceToDelete.value.id}`)
    await fetchDevices()
    notifySuccess('Device deleted successfully')
    deviceToDelete.value = null
  } catch (e) {
    notifyError('Failed to delete device')
  }
}

const openEditDialog = (device) => {
  deviceToEdit.value = { ...device } // Clone to avoid direct mutation
  isEditModalOpen.value = true
}

const handleDeviceSaved = async () => {
  await fetchDevices()
}

const exportDevices = async () => {
  try {
    const res = await api.get('/devices/export/json')
    const dataStr = JSON.stringify(res.data, null, 2)
    const blob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const dateStr = DateTime.now().toUTC().toFormat('yyyy-MM-dd')
    a.download = `devices-${dateStr}.json`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    notifyError('Export failed')
  }
}

const handleImport = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  try {
    const text = await file.text()
    const data = JSON.parse(text)
    await api.post('/devices/import/json', data)
    await fetchDevices()
    notifySuccess('Devices imported successfully')
  } catch (e) {
    notifyError('Import failed')
  }
}

let pollInterval = null

onMounted(() => {
  fetchDevices()
  pollInterval = setInterval(fetchDevices, 30000) // Increase interval for paginated view
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>
