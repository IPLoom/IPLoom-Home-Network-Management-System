<template>
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
      <thead class="bg-slate-50 dark:bg-slate-900/50">
        <tr>
          <!-- Expand Column for Mobile -->
          <th class="md:hidden px-4 py-3 w-8"></th>
          
          <th v-if="columns.includes('device')" 
              @click="toggleSort('display_name')"
              class="table-header-cell cursor-pointer hover:text-slate-900 dark:hover:text-white transition-colors md:w-1/4">
            <div class="flex items-center gap-1">
              Device
              <component :is="getSortIcon('display_name')" class="h-3 w-3" />
            </div>
          </th>
          
          <th v-if="columns.includes('network')"
              @click="toggleSort('mac')"
              class="hidden md:table-cell table-header-cell cursor-pointer hover:text-slate-900 dark:hover:text-white transition-colors w-1/5">
            <div class="flex items-center gap-1">
              Network Info
              <component :is="getSortIcon('mac')" class="h-3 w-3" />
            </div>
          </th>
          
          <!-- Slot for extra headers (e.g. Deco Node, OpenWrt Interface) -->
          <slot name="extra-headers"></slot>
          
          <th v-if="columns.includes('activity')"
              class="hidden md:table-cell table-header-cell w-1/6">
            Activity
          </th>
          
          <th v-if="columns.includes('ports')"
              class="hidden md:table-cell table-header-cell w-1/6">
            Open Ports
          </th>
          
          <th v-if="columns.includes('type')"
              @click="toggleSort('device_type')"
              class="hidden md:table-cell table-header-cell cursor-pointer hover:text-slate-900 dark:hover:text-white transition-colors w-1/12">
            <div class="flex items-center gap-1">
              Type
              <component :is="getSortIcon('device_type')" class="h-3 w-3" />
            </div>
          </th>
          
          <th v-if="columns.includes('last_seen')"
              @click="toggleSort('last_seen')"
              class="hidden md:table-cell table-header-cell cursor-pointer hover:text-slate-900 dark:hover:text-white transition-colors w-1/12">
            <div class="flex items-center gap-1">
              Last Seen
              <component :is="getSortIcon('last_seen')" class="h-3 w-3" />
            </div>
          </th>
          
          <th v-if="columns.includes('actions')"
              class="hidden md:table-cell table-header-cell text-right w-20">
            Actions
          </th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-200 dark:divide-slate-700">
        <template v-for="device in devices" :key="device.id">
          <!-- Main Row -->
          <tr @click="navigateToDetails(device.id)" 
              class="hover-row group cursor-pointer"
              :class="{ '!bg-red-50/30 dark:!bg-red-900/20': !device.is_trusted }">
            
            <!-- Mobile Toggle -->
            <td class="md:hidden table-data-cell" @click.stop>
              <button @click="toggleRow(device.id)" class="p-1 -ml-1 text-slate-400 hover:text-blue-500">
                <component :is="expandedRows.has(device.id) ? ChevronDown : ChevronRight" class="h-4 w-4" />
              </button>
            </td>
            
            <!-- Device Column -->
            <td v-if="columns.includes('device')" class="table-data-cell">
              <div class="flex items-center gap-3">
                <div class="relative flex-shrink-0">
                  <div class="p-2 bg-slate-100 dark:bg-slate-700 rounded-lg group-hover:bg-white dark:group-hover:bg-slate-600 transition-colors">
                    <img v-if="device.icon && device.icon.startsWith('/static/')" :src="device.icon" class="h-5 w-5 object-contain" />
                    <component v-else :is="getIcon(device.icon || 'help-circle')" class="h-5 w-5 text-slate-600 dark:text-slate-400" />
                  </div>
                  <span class="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-white dark:border-slate-800"
                        :class="getDeviceStatusColor(device)"></span>
                </div>
                <div class="min-w-0">
                  <div class="flex items-center gap-1.5 truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    <img v-if="device.brand_icon" :src="device.brand_icon" class="w-4 h-4 object-contain rounded-sm" />
                    <span class="text-sm font-medium text-slate-900 dark:text-white truncate">
                      {{ device.display_name || 'Unnamed Device' }}
                    </span>
                    <span v-if="isNewDevice(device.first_seen)"
                          class="px-1 py-0.5 rounded text-[8px] font-black uppercase tracking-wider bg-emerald-500 text-white shadow-sm shadow-emerald-500/20">
                      New
                    </span>
                  </div>
                  <div class="flex flex-wrap items-center gap-2 mt-0.5">
                    <div class="text-xs text-slate-500 font-mono">{{ device.ip }}</div>
                    
                    <span class="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border"
                          :class="device.ip_type === 'static'
                            ? 'bg-indigo-50 text-indigo-600 dark:bg-indigo-900/40 dark:text-indigo-400 border-indigo-100 dark:border-indigo-800'
                            : device.ip_type === 'dynamic'
                            ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/40 dark:text-amber-400 border-amber-100 dark:border-amber-800'
                            : 'bg-slate-50 text-slate-500 dark:bg-slate-800/40 dark:text-slate-400 border-slate-200 dark:border-slate-700'">
                      {{ device.ip_type || 'UNKNOWN' }}
                    </span>
                    
                    <span v-if="!device.is_trusted"
                          class="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30 border border-red-200 dark:border-red-800 flex items-center gap-1">
                      <component :is="ShieldAlert" class="h-3 w-3" /> Untrusted
                    </span>
                    <span v-else
                          class="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-800 flex items-center gap-1">
                      <component :is="ShieldCheck" class="h-3 w-3" /> Trusted
                    </span>
                    
                    <span v-if="device.is_blocked"
                          class="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30 border border-red-200 dark:border-red-800 flex items-center gap-1"
                          v-tooltip="'Internet Access Blocked via OpenWrt'">
                      <component :is="Ban" class="h-3 w-3" /> Blocked
                    </span>
                    
                    <span v-if="device.has_schedule"
                          class="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400 bg-rose-100 dark:bg-rose-900/30 border border-rose-200 dark:border-rose-800 flex items-center gap-1"
                          :class="{ 'animate-pulse ring-1 ring-rose-500/50': device.is_scheduled_block }"
                          v-tooltip="device.is_scheduled_block ? 'Currently blocked by schedule' : 'Has recurring schedules defined'">
                      <component :is="Clock" class="h-3 w-3" /> 
                      {{ device.is_scheduled_block ? 'Scheduled (Active)' : 'Scheduled' }}
                    </span>
                    
                    <div v-if="device.is_quota_exceeded"
                          class="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-800 flex items-center gap-1"
                          v-tooltip="'Internet Data Quota Exceeded'">
                      <component :is="Zap" class="h-3 w-3" /> Quota
                    </div>

                    <span v-if="device.attributes?.connection_type === 'wireless'"
                          class="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-blue-50 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400 border border-blue-100 dark:border-blue-800 flex items-center gap-1"
                          v-tooltip="device.attributes.wlan_ssid ? `Connected to ${device.attributes.wlan_ssid}` : 'Connected via Wi-Fi Wireless'">
                      <component :is="Wifi" class="h-3 w-3" /> {{ device.attributes.wlan_band || 'Wi-Fi' }} 
                      <span v-if="device.attributes.wlan_rssi" class="opacity-80 ml-0.5">({{ device.attributes.wlan_rssi }} dBm)</span>
                    </span>
                    <span v-if="device.attributes?.connection_type === 'wired'"
                          class="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-800 flex items-center gap-1"
                          v-tooltip="'Connected via Ethernet LAN'">
                      <component :is="Network" class="h-3 w-3" /> LAN
                    </span>
                  </div>

                  <!-- Quota Mini Progress Bar -->
                  <div class="min-h-[14px]">
                    <div v-if="device.quota" class="mt-1.5 flex items-center gap-2" v-tooltip="`${formatBytes(device.quota.current_usage)} / ${formatBytes(device.quota.limit_bytes)} used`">
                      <div class="w-16 h-1 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                        <div class="h-full transition-all duration-500" 
                             :class="device.is_quota_exceeded ? 'bg-red-500' : 'bg-blue-500'"
                             :style="{ width: Math.min((device.quota.current_usage / device.quota.limit_bytes) * 100, 100) + '%' }"></div>
                      </div>
                      <span class="text-[8px] font-black uppercase tracking-tighter" :class="device.is_quota_exceeded ? 'text-red-500' : 'text-slate-500'">
                        {{ Math.round((device.quota.current_usage / device.quota.limit_bytes) * 100) }}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </td>
            
            <!-- Network Info Column -->
            <td v-if="columns.includes('network')" class="px-2 py-2 hidden md:table-cell">
              <div class="text-xs text-slate-600 dark:text-slate-300 font-medium">{{ device.vendor || 'Unknown' }}</div>
              <div class="text-xs text-slate-500 font-mono truncate max-w-[200px]">{{ device.mac || 'N/A' }}</div>
            </td>
            
            <!-- Slot for extra integration cells -->
            <slot name="extra-cells" :device="device"></slot>
            
            <!-- Activity Sparkline Column -->
            <td v-if="columns.includes('activity')" class="px-2 py-2 hidden md:table-cell">
              <div class="h-8 w-24 relative" v-if="device.traffic_history && device.traffic_history.length > 1">
                <TrafficSparkline :data="device.traffic_history" :width="100" :height="32" />
              </div>
              <span v-else class="text-xs text-slate-400 italic">No Activity</span>
            </td>
            
            <!-- Open Ports Column -->
            <td v-if="columns.includes('ports')" class="px-2 py-2 hidden md:table-cell">
              <div v-if="device.open_ports && device.open_ports.length > 0" class="flex flex-wrap gap-1">
                <span v-for="port in device.open_ports.slice(0, 3)"
                      :key="typeof port === 'object' ? port.port : port"
                      class="px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-100 dark:border-blue-800 uppercase">
                  {{ typeof port === 'object' ? (port.service || port.port) : port }}
                </span>
                <span v-if="device.open_ports.length > 3" class="text-[10px] text-slate-500 self-center">
                  +{{ device.open_ports.length - 3 }}
                </span>
              </div>
              <span v-else class="text-xs text-slate-400 italic">No ports</span>
            </td>
            
            <!-- Type Column -->
            <td v-if="columns.includes('type')" class="px-2 py-2 hidden md:table-cell">
              <span class="inline-flex px-2 py-1 text-xs font-medium rounded bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
                {{ device.device_type || 'Unknown' }}
              </span>
            </td>
            
            <!-- Last Seen Column -->
            <td v-if="columns.includes('last_seen')" class="px-3 py-4 text-sm text-slate-600 dark:text-slate-400 hidden md:table-cell">
              {{ formatRelativeTime(device.last_seen) }}
            </td>
            
            <!-- Actions Column -->
            <td v-if="columns.includes('actions')" class="px-2 py-2 text-right hidden md:table-cell w-20" @click.stop>
              <div class="flex items-center justify-end gap-1">
                <Button @click="navigateToDetails(device.id)"
                        severity="secondary"
                        text
                        v-tooltip="'View Details'"
                        :pt="{ root: 'p-1.5 rounded-lg' }">
                  <template #icon>
                    <component :is="Eye" class="h-4 w-4" />
                  </template>
                </Button>
                
                <Button @click.stop="toggleMenu($event, device)"
                        severity="secondary"
                        text
                        v-tooltip="'More Actions'"
                        :pt="{ root: 'p-1.5 rounded-lg' }">
                  <template #icon>
                    <component :is="MoreVertical" class="h-4 w-4" />
                  </template>
                </Button>
              </div>
            </td>
          </tr>
          
          <!-- Mobile Expanded Details -->
          <tr v-if="expandedRows.has(device.id)" class="md:hidden bg-slate-50/50 dark:bg-slate-800/30">
            <td :colspan="columns.length + 1" class="px-4 py-3 border-t border-slate-100 dark:border-slate-700">
              <div class="space-y-4">
                <!-- Actions Row -->
                <div v-if="columns.includes('actions')" class="flex gap-2 mb-4">
                  <Button @click="navigateToDetails(device.id)"
                          severity="secondary" outlined size="small"
                          :pt="{ root: 'flex-1 justify-center text-xs font-medium gap-1.5 rounded-lg py-2' }">
                    <template #icon><component :is="Eye" class="h-3.5 w-3.5" /></template>
                    View
                  </Button>
                  <Button @click.stop="$emit('edit', device)"
                          severity="info" outlined size="small"
                          :pt="{ root: 'flex-1 justify-center text-xs font-medium gap-1.5 rounded-lg py-2' }">
                    <template #icon><component :is="Pencil" class="h-3.5 w-3.5" /></template>
                    Edit
                  </Button>
                  <Button @click.stop="$emit('delete', device)"
                          severity="danger" outlined size="small"
                          :pt="{ root: 'flex-1 justify-center text-xs font-medium gap-1.5 rounded-lg py-2' }">
                    <template #icon><component :is="Trash2" class="h-3.5 w-3.5" /></template>
                    Delete
                  </Button>
                </div>
                
                <!-- Network Info -->
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <p class="text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">Vendor</p>
                    <p class="text-sm text-slate-700 dark:text-slate-300">{{ device.vendor || 'Unknown' }}</p>
                  </div>
                  <div>
                    <p class="text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">MAC Address</p>
                    <p class="text-sm font-mono text-slate-600 dark:text-slate-400">{{ device.mac || 'N/A' }}</p>
                  </div>
                </div>
                
                <!-- Slot for extra mobile details (e.g. Deco Node, Interface) -->
                <slot name="extra-mobile-details" :device="device"></slot>
                
                <!-- Activity & Last Seen -->
                <div class="grid grid-cols-2 gap-4 items-end">
                  <div v-if="columns.includes('activity')">
                    <p class="text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">Activity</p>
                    <div class="h-8 w-32 relative" v-if="device.traffic_history && device.traffic_history.length > 1">
                      <TrafficSparkline :data="device.traffic_history" :width="128" :height="32" />
                    </div>
                    <span v-else class="text-xs text-slate-400 italic">No Activity</span>
                  </div>
                  <div v-if="columns.includes('last_seen')">
                    <p class="text-[10px] uppercase tracking-wider text-slate-400 font-bold mb-1">Last Seen</p>
                    <p class="text-sm text-slate-600 dark:text-slate-400">{{ formatRelativeTime(device.last_seen) }}</p>
                  </div>
                </div>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>

    <Menu ref="actionMenu" :model="menuItems" :popup="true"
      :pt="{
        root: 'min-w-[160px] rounded-xl shadow-xl border border-slate-200 dark:border-slate-700 bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl p-1',
        list: 'py-0.5 space-y-0.5'
      }"
    >
      <template #item="{ item }">
        <button
          v-if="!item.separator"
          @click="item.command"
          class="w-full flex items-center gap-2 px-2.5 py-1.5 text-xs rounded-lg transition-colors text-left font-medium"
          :class="item.class || 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700/50 hover:text-slate-900 dark:hover:text-white'"
        >
          <component :is="item.icon" class="h-3.5 w-3.5 shrink-0" />
          <span>{{ item.label }}</span>
        </button>
        <div v-else class="h-px bg-slate-100 dark:bg-slate-700/50 my-1"></div>
      </template>
    </Menu>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import TrafficSparkline from '@/components/TrafficSparkline.vue'
import { getIcon } from '@/utils/icons'
import { formatRelativeTime } from '@/utils/date'
import { DateTime } from 'luxon'
import * as LucideIcons from 'lucide-vue-next'

// PrimeVue components
import Button from 'primevue/button'
import Menu from 'primevue/menu'

const { 
  ChevronDown, 
  ChevronRight, 
  ShieldAlert, 
  ShieldCheck, 
  Wifi, 
  Network, 
  Ban, 
  Clock, 
  Zap, 
  Eye, 
  Pencil, 
  Trash2, 
  Loader2, 
  ArrowUpDown, 
  ChevronUp,
  MoreVertical
} = LucideIcons

const props = defineProps({
  devices: {
    type: Array,
    required: true
  },
  columns: {
    type: Array,
    default: () => ['device', 'network', 'activity', 'ports', 'type', 'last_seen', 'actions']
  },
  approvingId: {
    type: String,
    default: null
  },
  blockingId: {
    type: String,
    default: null
  },
  sortBy: {
    type: String,
    default: 'ip'
  },
  sortOrder: {
    type: String,
    default: 'asc'
  }
})

const emit = defineEmits(['approve', 'block-toggle', 'edit', 'delete', 'sort'])

const router = useRouter()
const expandedRows = ref(new Set())

const toggleRow = (id) => {
  if (expandedRows.value.has(id)) {
    expandedRows.value.delete(id)
  } else {
    expandedRows.value.add(id)
  }
}

const toggleSort = (key) => {
  emit('sort', key)
}

const getSortIcon = (key) => {
  if (props.sortBy !== key) return ArrowUpDown
  return props.sortOrder === 'asc' ? ChevronUp : ChevronDown
}

const getDeviceStatusColor = (device) => {
  if (device.status === 'online') return 'bg-emerald-500'
  if (device.status === 'offline') return 'bg-slate-400'
  return 'bg-slate-300'
}

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

const navigateToDetails = (id) => {
  router.push({ name: 'DeviceDetails', params: { id } })
}

// Overflow menu for secondary actions (Edit, Delete)
const actionMenu = ref(null)
const menuTargetDevice = ref(null)

const toggleMenu = (event, device) => {
  menuTargetDevice.value = device
  if (actionMenu.value) {
    actionMenu.value.toggle(event)
  }
}

const menuItems = computed(() => {
  if (!menuTargetDevice.value) return []
  
  const items = []
  
  // 1. Trust Action (only if not trusted)
  if (!menuTargetDevice.value.is_trusted) {
    items.push({
      label: 'Trust Device',
      icon: ShieldCheck,
      class: 'text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950/20',
      command: () => {
        emit('approve', menuTargetDevice.value)
      }
    })
    items.push({ separator: true })
  }
  
  // 2. Block/Unblock Action
  items.push({
    label: menuTargetDevice.value.is_blocked ? 'Unblock Device' : 'Block Device',
    icon: Ban,
    class: menuTargetDevice.value.is_blocked 
      ? 'text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950/20' 
      : 'text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/20',
    command: () => {
      emit('block-toggle', menuTargetDevice.value)
    }
  })
  
  items.push({ separator: true })
  
  // 3. Edit Action
  items.push({
    label: 'Edit Device',
    icon: Pencil,
    command: () => {
      emit('edit', menuTargetDevice.value)
    }
  })
  
  items.push({ separator: true })
  
  // 4. Delete Action
  items.push({
    label: 'Delete Device',
    icon: Trash2,
    class: 'text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/20',
    command: () => {
      emit('delete', menuTargetDevice.value)
    }
  })
  
  return items
})
</script>
