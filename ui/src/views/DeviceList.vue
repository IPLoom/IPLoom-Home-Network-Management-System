<template>
  <v-container fluid class="pa-4 space-y-4">
    <!-- Main Header with Tabs -->
    <div class="d-flex flex-column flex-md-row align-start align-md-center justify-space-between mb-4">
      <div class="mb-2 mb-md-0">
        <h1 class="text-h5 font-weight-bold">Devices</h1>
        <div class="text-body-2 text-medium-emphasis mt-1">{{ globalStats.total }} devices discovered</div>
      </div>
      
      <v-tabs v-model="activeTab" color="primary" bg-color="transparent" slider-color="primary" density="compact" class="border-b w-100 w-md-auto">
        <v-tab value="list" class="text-none font-weight-medium rounded-t-lg">
          <component :is="LucideIcons.List" class="w-4 h-4 mr-2" /> List
        </v-tab>
        <v-tab value="topology" class="text-none font-weight-medium rounded-t-lg">
          <component :is="LucideIcons.Network" class="w-4 h-4 mr-2" /> Topology
        </v-tab>
        <v-tab value="occupancy" class="text-none font-weight-medium rounded-t-lg">
          <component :is="LucideIcons.Grid" class="w-4 h-4 mr-2" /> Occupancy
        </v-tab>
      </v-tabs>
    </div>

    <v-window v-model="activeTab">
      <!-- List Tab -->
      <v-window-item value="list">
        
        <!-- List Toolbar -->
        <div class="d-flex justify-end align-center gap-2 mb-4">
          <v-btn-group variant="outlined" density="comfortable" class="bg-surface" style="border-radius: 8px;">
            <v-btn @click="exportDevices" v-tooltip="'Export Devices to JSON'" class="text-none">
              <template v-slot:prepend><component :is="LucideIcons.Download" class="w-4 h-4" /></template>
              <span class="d-none d-sm-inline">Export</span>
            </v-btn>
            <v-btn @click="$refs.importInput.click()" v-tooltip="'Import Devices from JSON'" class="text-none">
              <template v-slot:prepend><component :is="LucideIcons.Upload" class="w-4 h-4" /></template>
              <span class="d-none d-sm-inline">Import</span>
            </v-btn>
          </v-btn-group>
          <input type="file" ref="importInput" class="d-none" @change="handleImport" accept=".json" />
          
          <v-btn color="primary" @click="isDiscoveryOpen = true" v-tooltip="'Quick Scan for New Devices'" elevation="2" class="text-none font-weight-bold rounded-lg px-4">
            <template v-slot:prepend><component :is="LucideIcons.Radar" class="w-4 h-4" /></template>
            Find New
          </v-btn>

          <v-btn icon :loading="isScanning" @click="triggerScan" v-tooltip="isScanning ? 'Scanning Network...' : 'Scan Network'" variant="tonal" color="primary" class="rounded-lg">
            <component :is="LucideIcons.RefreshCw" class="w-5 h-5" />
          </v-btn>
        </div>

        <!-- Quick Stats -->
        <v-row class="mb-4 mx-0">
          <v-col cols="6" md="3" v-for="stat in deviceStats" :key="stat.label">
            <v-card class="h-100 position-relative overflow-hidden" elevation="2" rounded="lg">
              <Sparkline :data="stat.trend" :color="stat.color" class="opacity-20 position-absolute w-100 h-100" style="top:0; left:0; pointer-events:none;" />
              <v-card-text class="d-flex flex-column align-center text-center position-relative z-10 pt-4 pb-3">
                <div class="d-flex justify-space-between w-100 align-start mb-2">
                  <v-avatar :class="stat.bgClass" rounded size="32">
                    <component :is="stat.icon" class="h-4 w-4" />
                  </v-avatar>
                  <v-chip v-if="stat.change" size="x-small" :color="stat.changeType === 'down' ? 'error' : 'success'" variant="flat" class="font-weight-bold">
                    {{ stat.change }}
                  </v-chip>
                </div>
                <div class="text-h4 font-weight-black mt-2">{{ stat.value }}</div>
                <div :class="stat.textColor" class="text-caption font-weight-black text-uppercase mt-1" style="letter-spacing: 0.1em;">
                  {{ stat.label }}
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <v-card elevation="2" rounded="lg" class="border overflow-hidden">
          <v-card-text class="pa-0">
            <!-- Filters & Search -->
            <div class="pa-4 bg-surface-elevated border-b">
              <v-row align="center" class="mx-0">
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="search"
                    @input="debounceFetch"
                    placeholder="Search IP, Mac, Vendor or Name..."
                    variant="outlined"
                    density="compact"
                    hide-details
                    bg-color="surface"
                  >
                    <template v-slot:prepend-inner>
                      <component :is="LucideIcons.Search" class="h-4 w-4 text-medium-emphasis" />
                    </template>
                  </v-text-field>
                </v-col>
                <v-col cols="12" md="3">
                  <v-select
                    v-model="statusFilter"
                    :items="[{title: 'All Statuses', value: ''}, {title: 'Online', value: 'online'}, {title: 'Offline', value: 'offline'}]"
                    @update:modelValue="fetchDevices"
                    variant="outlined"
                    density="compact"
                    hide-details
                    bg-color="surface"
                  >
                    <template v-slot:selection="{ item }">
                      <div class="d-flex align-center">
                        <component :is="LucideIcons.Filter" class="h-4 w-4 mr-2" :class="statusFilter ? 'text-primary' : 'text-medium-emphasis'" />
                        {{ item.title }}
                      </div>
                    </template>
                  </v-select>
                </v-col>
                <v-col cols="12" md="3">
                  <v-select
                    v-model="typeFilter"
                    :items="[{title: 'All Types', value: ''}, ...deviceTypes.map(t => ({title: t, value: t}))]"
                    @update:modelValue="fetchDevices"
                    variant="outlined"
                    density="compact"
                    hide-details
                    bg-color="surface"
                  >
                    <template v-slot:selection="{ item }">
                      <div class="d-flex align-center">
                        <component :is="LucideIcons.Layers" class="h-4 w-4 mr-2" :class="typeFilter ? 'text-primary' : 'text-medium-emphasis'" />
                        <span class="text-truncate">{{ item.title }}</span>
                      </div>
                    </template>
                  </v-select>
                </v-col>
              </v-row>
              <!-- Display Info Line -->
              <div class="d-flex align-center justify-space-between text-caption text-medium-emphasis mt-3">
                <div class="d-flex align-center gap-2">
                  <component :is="LucideIcons.Activity" class="h-4 w-4 text-primary" />
                  <span>Showing <b class="text-high-emphasis">{{ devices.length }}</b> of <b class="text-high-emphasis">{{ totalDevices }}</b> devices matching current filters</span>
                </div>
                <div v-if="sortBy" class="d-none d-sm-block text-uppercase opacity-70" style="font-size: 10px;">
                  Sorted by {{ sortBy }} ({{ sortOrder }})
                </div>
              </div>
            </div>

            <!-- Loading State -->
            <v-skeleton-loader
              v-if="loading && devices.length === 0"
              type="table-heading, table-row-divider@5"
              class="ma-4"
            ></v-skeleton-loader>

            <!-- Empty State -->
            <v-empty-state
              v-else-if="!loading && devices.length === 0"
              icon="mdi-magnify"
              title="No devices found"
              text="Try adjusting your search or filters to find what you're looking for."
              class="my-8"
            >
              <template v-slot:media>
                <component :is="LucideIcons.SearchX" class="w-16 h-16 text-medium-emphasis mb-4 mx-auto" />
              </template>
            </v-empty-state>

            <!-- Devices Table -->
            <DeviceTable
              v-else
              :devices="devices"
              :columns="['identity', 'status', 'activity', 'actions']"
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

            <!-- Pagination -->
            <div v-if="totalPages > 1" class="d-flex justify-space-between align-center px-4 py-3 border-t bg-surface">
              <v-btn @click="fetchDevices" icon variant="text" size="small" :loading="loading" v-tooltip="'Refresh List'" class="rounded-lg">
                <component :is="LucideIcons.RefreshCw" class="h-4 w-4" />
              </v-btn>
              
              <v-pagination
                v-model="currentPage"
                :length="totalPages"
                :total-visible="5"
                density="comfortable"
                rounded="circle"
                @update:modelValue="fetchDevices"
              ></v-pagination>
              
              <div style="width: 40px;"></div> <!-- Spacer to center pagination -->
            </div>
          </v-card-text>
        </v-card>
      </v-window-item>

      <!-- Topology Tab -->
      <v-window-item value="topology">
        <v-card elevation="2" rounded="lg" class="border overflow-hidden">
          <v-card-text class="pa-0" style="min-height: 600px;">
            <Topology />
          </v-card-text>
        </v-card>
      </v-window-item>

      <!-- Occupancy Tab -->
      <v-window-item value="occupancy">
        <v-card elevation="2" rounded="lg" class="border overflow-hidden">
          <v-card-text class="pa-0" style="min-height: 600px;">
            <Occupancy />
          </v-card-text>
        </v-card>
      </v-window-item>
    </v-window>

    <!-- Modals -->
    <EditDeviceModal :isOpen="isEditModalOpen" :device="deviceToEdit" @close="isEditModalOpen = false" @save="handleDeviceSaved" />

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

    <DiscoveryModal :isOpen="isDiscoveryOpen" @close="isDiscoveryOpen = false" @onboarded="fetchDevices" />
  </v-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted, reactive, computed, watch } from 'vue'
import api from '@/utils/api'
import Sparkline from '@/components/Sparkline.vue'
import EditDeviceModal from '@/components/EditDeviceModal.vue'
import DiscoveryModal from '@/components/DiscoveryModal.vue'
import DeviceTable from '@/components/DeviceTable.vue'
import ConfirmationModal from '@/components/ConfirmationModal.vue'
import Topology from './Topology.vue'
import Occupancy from './Occupancy.vue'
import { getIcon } from '@/utils/icons'
import * as LucideIcons from 'lucide-vue-next'
const { Download, Upload, RefreshCw, Loader2, Search, SearchX, ChevronUp, ChevronDown, ChevronRight, ArrowUpDown, Activity, Wifi, Network, Database, ZapOff, Ticket, Filter, Layers, ShieldCheck, ShieldAlert, Radar, Ban, Zap, Clock } = LucideIcons
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
const activeTab = ref('list')

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
