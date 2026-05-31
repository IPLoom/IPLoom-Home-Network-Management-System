<template>
  <v-table hover density="comfortable" class="bg-surface fixed-table">
        <thead>
      <tr>
        <!-- Expand Column for Mobile -->
        <th class="d-md-none pa-3 w-8"></th>
        
        <th v-if="columns.includes('identity')" 
            @click="toggleSort('display_name')"
            class="cursor-pointer text-left font-weight-bold" style="width: 40%;">
          <div class="d-flex align-center gap-1">
            Device & Network
            <component :is="getSortIcon('display_name')" class="h-3 w-3" />
          </div>
        </th>
        
        <th v-if="columns.includes('status')"
            class="d-none d-md-table-cell text-left font-weight-bold" style="width: 20%;">
          Status & Tags
        </th>
        
        <slot name="extra-headers"></slot>
        
        <th v-if="columns.includes('activity')"
            class="d-none d-md-table-cell text-left font-weight-bold" style="width: 25%;">
          Activity & Usage
        </th>
        
        <th v-if="columns.includes('actions')"
            class="d-none d-md-table-cell text-right font-weight-bold" style="width: 15%;">
          Actions
        </th>
      </tr>
    </thead>
    <tbody>
      <template v-for="device in devices" :key="device.id">
        <!-- Main Row -->
        <tr @click="navigateToDetails(device.id)" 
            class="cursor-pointer transition"
            :class="{ 'bg-error-lighten-5': !device.is_trusted }">
          
          <!-- Mobile Toggle -->
          <td class="d-md-none" @click.stop>
            <v-btn icon variant="text" size="small" @click="toggleRow(device.id)" color="medium-emphasis">
              <component :is="expandedRows.has(device.id) ? ChevronDown : ChevronRight" class="h-4 w-4" />
            </v-btn>
          </td>
          
          <!-- Identity & Network Column -->
          <td v-if="columns.includes('identity')" class="py-3 text-wrap">
            <div class="d-flex align-start gap-3">
              <v-badge
                dot
                location="bottom right"
                offset-x="2"
                offset-y="2"
                :color="device.status === 'online' ? 'success' : (device.status === 'offline' ? 'grey' : 'grey-lighten-2')"
                bordered
              >
                <v-avatar color="surface-variant" rounded="lg" size="44">
                  <img v-if="device.icon && device.icon.startsWith('/static/')" :src="device.icon" style="width: 24px; height: 24px; object-fit: contain;" />
                  <component v-else :is="getIcon(device.icon || 'help-circle')" class="text-medium-emphasis" style="width: 24px; height: 24px;" />
                </v-avatar>
              </v-badge>
              
              <div class="flex-1 min-w-0 d-flex flex-column justify-center pt-1">
                <div class="d-flex align-center gap-2 min-w-0">
                  <span class="text-body-1 font-weight-bold text-truncate text-high-emphasis flex-1 min-w-0">
                    {{ device.display_name || 'Unnamed Device' }}
                  </span>
                  <v-chip v-if="isNewDevice(device.first_seen)" size="x-small" color="success" class="font-weight-black text-uppercase flex-shrink-0">
                    New
                  </v-chip>
                </div>
                <div class="text-caption font-weight-medium font-family-mono text-primary mt-1">{{ device.ip }}</div>
                <div class="d-flex align-center gap-2 mt-1 min-w-0">
                  <span class="text-[10px] text-medium-emphasis font-family-mono flex-shrink-0">{{ device.mac || 'N/A' }}</span>
                  <span class="text-[10px] text-disabled text-truncate min-w-0 flex-1" v-if="device.vendor">&bull; {{ device.vendor }}</span>
                </div>
              </div>
            </div>
          </td>
          
          <!-- Status & Tags Column -->
          <td v-if="columns.includes('status')" class="d-none d-md-table-cell py-3">
            <div class="d-flex flex-wrap align-center gap-2">
              <v-chip size="x-small" variant="flat" color="surface-variant" class="font-weight-medium px-2">
                {{ device.device_type || 'Unknown' }}
              </v-chip>
              
              <v-chip size="x-small" variant="outlined" class="font-weight-bold text-uppercase px-2 d-flex align-center"
                    :color="device.ip_type === 'static' ? 'indigo' : (device.ip_type === 'dynamic' ? 'amber-darken-2' : 'grey')">
                IP: {{ device.ip_type || 'UNKNOWN' }}
              </v-chip>
              
              <v-chip v-if="!device.is_trusted" size="x-small" color="error" variant="flat" class="font-weight-bold text-uppercase px-2 d-flex align-center">
                <component :is="ShieldAlert" style="width: 10px; height: 10px;" class="mr-1" /> Untrusted
              </v-chip>
              <v-chip v-else size="x-small" color="success" variant="tonal" class="font-weight-bold text-uppercase px-2 d-flex align-center">
                <component :is="ShieldCheck" style="width: 10px; height: 10px;" class="mr-1" /> Trusted
              </v-chip>
              
              <v-chip v-if="device.is_blocked" size="x-small" color="error" variant="flat" class="font-weight-bold text-uppercase px-2 d-flex align-center" v-tooltip="'Internet Access Blocked'">
                <component :is="Ban" style="width: 10px; height: 10px;" class="mr-1" /> Blocked
              </v-chip>
              
              <v-chip v-if="device.has_schedule" size="x-small" color="warning" variant="tonal" class="font-weight-bold text-uppercase px-2 d-flex align-center" v-tooltip="'Has active schedules'">
                <component :is="Clock" style="width: 10px; height: 10px;" class="mr-1" /> 
                {{ device.is_scheduled_block ? 'Scheduled (Blocked)' : 'Scheduled' }}
              </v-chip>
              
              <v-chip v-if="device.attributes?.connection_type === 'wireless'" size="x-small" color="blue" variant="tonal" class="font-weight-bold text-uppercase px-2 d-flex align-center" v-tooltip="device.attributes.wlan_ssid ? `Wi-Fi: ${device.attributes.wlan_ssid}` : 'Connected via Wi-Fi'">
                <component :is="Wifi" style="width: 10px; height: 10px;" class="mr-1" /> {{ device.attributes.wlan_band || 'Wi-Fi' }} 
                <span v-if="device.attributes.wlan_rssi" class="opacity-80 ml-1">({{ device.attributes.wlan_rssi }} dBm)</span>
              </v-chip>
              
              <v-chip v-if="device.attributes?.connection_type === 'wired'" size="x-small" color="teal" variant="tonal" class="font-weight-bold text-uppercase px-2 d-flex align-center" v-tooltip="'Connected via Ethernet LAN'">
                <component :is="Network" style="width: 10px; height: 10px;" class="mr-1" /> LAN (Wired)
              </v-chip>
            </div>
          </td>
          
          <!-- Slot for extra integration cells -->
          <slot name="extra-cells" :device="device"></slot>
          
          <!-- Activity & Usage Column -->
          <td v-if="columns.includes('activity')" class="d-none d-md-table-cell py-3">
            <div class="d-flex flex-column gap-2">
              <div class="d-flex align-center justify-space-between">
                <div style="height: 24px; width: 100px; position: relative;" v-if="device.traffic_history && device.traffic_history.length > 1">
                  <TrafficSparkline :data="device.traffic_history" :width="100" :height="24" />
                </div>
                <span v-else class="text-caption font-italic text-disabled">No Activity</span>
                
                <span class="text-[10px] text-medium-emphasis">Seen {{ formatRelativeTime(device.last_seen) }}</span>
              </div>
              
              <!-- Quota Mini Progress Bar -->
              <div v-if="device.quota" class="w-100">
                <div class="d-flex align-center gap-2" v-tooltip="`${formatBytes(device.quota.current_usage)} / ${formatBytes(device.quota.limit_bytes)} used`">
                  <v-progress-linear :model-value="(device.quota.current_usage / device.quota.limit_bytes) * 100" :color="device.is_quota_exceeded ? 'error' : 'primary'" height="4" rounded class="flex-grow-1"></v-progress-linear>
                  <span class="text-[9px] font-weight-black text-uppercase" :class="device.is_quota_exceeded ? 'text-error' : 'text-medium-emphasis'">
                    <component v-if="device.is_quota_exceeded" :is="Zap" style="width: 8px; height: 8px; display: inline-block;" class="mr-n1" />
                    {{ Math.round((device.quota.current_usage / device.quota.limit_bytes) * 100) }}% Quota
                  </span>
                </div>
              </div>
              
              <!-- Open Ports -->
              <div v-if="device.open_ports && device.open_ports.length > 0" class="d-flex flex-wrap gap-1 mt-1">
                <v-chip v-for="port in device.open_ports.slice(0, 3)" :key="typeof port === 'object' ? port.port : port" size="x-small" color="info" variant="outlined" class="text-uppercase font-weight-bold px-1" style="font-size: 8px; height: 16px;">
                  {{ typeof port === 'object' ? (port.service || port.port) : port }}
                </v-chip>
                <span v-if="device.open_ports.length > 3" class="text-[9px] text-medium-emphasis align-self-center ml-1">
                  +{{ device.open_ports.length - 3 }}
                </span>
              </div>
            </div>
          </td>
          
          <!-- Actions Column -->
          <td v-if="columns.includes('actions')" class="d-none d-md-table-cell py-3 text-right" @click.stop>
            <div class="d-flex align-center justify-end gap-1">
              <v-btn v-if="!device.is_trusted" 
                      icon variant="text" size="24"
                      @click.stop="$emit('approve', device)"
                      :loading="approvingId === device.id"
                      color="error"
                      v-tooltip="'Trust this Device'">
                <component :is="ShieldCheck" style="width: 14px; height: 14px;" />
              </v-btn>
              
              <v-btn icon variant="text" size="24"
                      @click.stop="$emit('block-toggle', device)"
                      :loading="blockingId === device.id"
                      :color="device.is_blocked ? 'error' : 'medium-emphasis'"
                      v-tooltip="device.is_blocked ? 'Unblock Device Access' : 'Block Device Access'">
                <component :is="Ban" style="width: 14px; height: 14px;" />
              </v-btn>
              
              <v-btn icon variant="text" size="24" color="primary" @click="navigateToDetails(device.id)" v-tooltip="'View Details'">
                <component :is="Eye" style="width: 14px; height: 14px;" />
              </v-btn>
              
              <v-btn icon variant="text" size="24" color="info" @click.stop="$emit('edit', device)" v-tooltip="'Edit Device Name & Type'">
                <component :is="Pencil" style="width: 14px; height: 14px;" />
              </v-btn>
              
              <v-btn icon variant="text" size="24" color="error" @click.stop="$emit('delete', device)" v-tooltip="'Delete Device'">
                <component :is="Trash2" style="width: 14px; height: 14px;" />
              </v-btn>
            </div>
          </td>
        </tr>
        
        <!-- Mobile Expanded Details -->
        <tr v-if="expandedRows.has(device.id)" class="d-md-none bg-surface-variant">
          <td :colspan="columns.length + 1" class="pa-4">
            <div class="d-flex flex-column gap-4">
              <!-- Actions Row -->
              <div v-if="columns.includes('actions')" class="d-flex gap-2">
                <v-btn flex-grow-1 variant="tonal" size="small" color="primary" @click="navigateToDetails(device.id)">
                  <component :is="Eye" class="h-4 w-4 mr-1" /> View
                </v-btn>
                <v-btn flex-grow-1 variant="tonal" size="small" color="info" @click.stop="$emit('edit', device)">
                  <component :is="Pencil" class="h-4 w-4 mr-1" /> Edit
                </v-btn>
                <v-btn flex-grow-1 variant="tonal" size="small" color="error" @click.stop="$emit('delete', device)">
                  <component :is="Trash2" class="h-4 w-4 mr-1" /> Delete
                </v-btn>
              </div>
              
              <!-- Status & Tags Mobile -->
              <v-row class="mx-0" v-if="columns.includes('status')">
                <v-col cols="12" class="pa-0">
                  <div class="d-flex flex-wrap align-center gap-2">
                    <v-chip size="x-small" variant="flat" color="surface-variant" class="font-weight-medium px-2">
                      {{ device.device_type || 'Unknown' }}
                    </v-chip>
                    
                    <v-chip size="x-small" variant="outlined" class="font-weight-bold text-uppercase px-2 d-flex align-center"
                          :color="device.ip_type === 'static' ? 'indigo' : (device.ip_type === 'dynamic' ? 'amber-darken-2' : 'grey')">
                      IP: {{ device.ip_type || 'UNKNOWN' }}
                    </v-chip>
                    
                    <v-chip v-if="!device.is_trusted" size="x-small" color="error" variant="flat" class="font-weight-bold text-uppercase px-2 d-flex align-center">
                      <component :is="ShieldAlert" style="width: 10px; height: 10px;" class="mr-1" /> Untrusted
                    </v-chip>
                    <v-chip v-else size="x-small" color="success" variant="tonal" class="font-weight-bold text-uppercase px-2 d-flex align-center">
                      <component :is="ShieldCheck" style="width: 10px; height: 10px;" class="mr-1" /> Trusted
                    </v-chip>
                    
                    <v-chip v-if="device.is_blocked" size="x-small" color="error" variant="flat" class="font-weight-bold text-uppercase px-2 d-flex align-center" v-tooltip="'Internet Access Blocked'">
                      <component :is="Ban" style="width: 10px; height: 10px;" class="mr-1" /> Blocked
                    </v-chip>
                    
                    <v-chip v-if="device.attributes?.connection_type === 'wireless'" size="x-small" color="blue" variant="tonal" class="font-weight-bold text-uppercase px-2 d-flex align-center" v-tooltip="device.attributes.wlan_ssid ? `Wi-Fi: ${device.attributes.wlan_ssid}` : 'Connected via Wi-Fi'">
                      <component :is="Wifi" style="width: 10px; height: 10px;" class="mr-1" /> {{ device.attributes.wlan_band || 'Wi-Fi' }} 
                      <span v-if="device.attributes.wlan_rssi" class="opacity-80 ml-1">({{ device.attributes.wlan_rssi }} dBm)</span>
                    </v-chip>
                    
                    <v-chip v-if="device.attributes?.connection_type === 'wired'" size="x-small" color="teal" variant="tonal" class="font-weight-bold text-uppercase px-2 d-flex align-center" v-tooltip="'Connected via Ethernet LAN'">
                      <component :is="Network" style="width: 10px; height: 10px;" class="mr-1" /> LAN (Wired)
                    </v-chip>
                  </div>
                </v-col>
              </v-row>
              
              <!-- Slot for extra mobile details -->
              <slot name="extra-mobile-details" :device="device"></slot>
              
              <!-- Activity & Last Seen -->
              <v-row align="end" class="mx-0 mt-2">
                <v-col cols="6" v-if="columns.includes('activity')">
                  <div class="text-[10px] font-weight-bold text-uppercase text-medium-emphasis mb-1">Activity</div>
                  <div style="height: 32px; width: 128px; position: relative;" v-if="device.traffic_history && device.traffic_history.length > 1">
                    <TrafficSparkline :data="device.traffic_history" :width="128" :height="32" />
                  </div>
                  <span v-else class="text-caption font-italic text-disabled">No Activity</span>
                </v-col>
                <v-col cols="6" v-if="columns.includes('activity')">
                  <div class="text-[10px] font-weight-bold text-uppercase text-medium-emphasis mb-1">Last Seen</div>
                  <div class="text-body-2 text-medium-emphasis">{{ formatRelativeTime(device.last_seen) }}</div>
                </v-col>
              </v-row>
            </div>
          </td>
        </tr>
      </template>
    </tbody>
  </v-table>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import TrafficSparkline from '@/components/TrafficSparkline.vue'
import { getIcon } from '@/utils/icons'
import { formatRelativeTime } from '@/utils/date'
import { DateTime } from 'luxon'
import * as LucideIcons from 'lucide-vue-next'

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
  ChevronUp 
} = LucideIcons

const props = defineProps({
  devices: {
    type: Array,
    required: true
  },
  columns: {
    type: Array,
    default: () => ['identity', 'status', 'activity', 'actions']
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
</script>

<style scoped>
.fixed-table :deep(.v-table__wrapper > table) {
  table-layout: fixed;
  width: 100%;
}
</style>
