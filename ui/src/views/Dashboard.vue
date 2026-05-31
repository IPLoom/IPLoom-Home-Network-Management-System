<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="text-2xl font-bold text-slate-900 dark:text-white leading-tight">Dashboard</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">Network overview and real-time monitoring</p>
      </div>
      <div class="flex items-center gap-3">
        <div
          class="hidden md:inline-flex items-center h-9 px-3 rounded-lg border border-emerald-200 dark:border-emerald-800/50 bg-emerald-50 dark:bg-emerald-900/20 shadow-sm"
        >
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span class="text-[10px] font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider">Scanner Active</span>
          </div>
        </div>
        <Button
          @click="fetchAllData"
          :loading="loading"
          severity="secondary"
          text
          v-tooltip="'Refresh All Data'"
          :pt="{ root: 'h-9 w-9 p-0 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm flex items-center justify-center bg-white/60 dark:bg-slate-800/60 hover:bg-slate-100 dark:hover:bg-slate-700/50' }"
        >
          <template #icon>
            <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
          </template>
        </Button>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <template v-if="loading && !statsLoaded">
        <div v-for="i in 4" :key="'skel-stat-' + i" class="card-stat">
          <div class="flex items-start justify-between">
            <Skeleton width="2.5rem" height="2.5rem" borderRadius="12px" />
            <Skeleton width="4rem" height="1.25rem" borderRadius="9999px" />
          </div>
          <div class="mt-4">
            <Skeleton width="3rem" height="2rem" class="mb-1" />
            <Skeleton width="5rem" height="0.75rem" />
          </div>
        </div>
      </template>
      <template v-else>
        <div v-for="stat in mainStats" :key="stat.label" class="card-stat group">
          <!-- Decoration -->
          <div
            class="absolute -right-4 -top-4 w-24 h-24 opacity-[0.03] group-hover:opacity-[0.05] transition-opacity text-slate-900 dark:text-white">
            <component :is="stat.icon" class="w-full h-full" />
          </div>

          <div class="flex items-start justify-between relative z-10">
            <div :class="[stat.bgClass, 'p-2.5 rounded-xl shadow-sm border border-white/10']">
              <component :is="stat.icon" class="h-5 w-5" />
            </div>
            <Tag v-if="stat.trend"
              :pt="{
                root: 'bg-white/50 dark:bg-slate-900/40 px-2 py-0.5 rounded-full border border-slate-200/50 dark:border-slate-700/50'
              }"
            >
              <template #default>
                <span class="text-[10px] font-bold" :class="stat.trendColor">{{ stat.trend }}</span>
              </template>
            </Tag>
          </div>

          <div class="mt-4 relative z-10">
            <p class="heading-xl">
              {{ stat.value }}
            </p>
            <p class="subtext-caps">
              {{ stat.label }}
            </p>
          </div>
        </div>
      </template>
    </div>

    <!-- Insights Row -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <template v-if="loading && !statsLoaded">
        <div v-for="i in 4" :key="'skel-insight-' + i" class="insight-card bg-slate-200 dark:bg-slate-700">
          <Skeleton width="3rem" height="3rem" borderRadius="12px" />
          <div class="flex-1 space-y-2">
            <Skeleton width="4rem" height="0.625rem" />
            <Skeleton width="6rem" height="1.25rem" />
          </div>
        </div>
      </template>
      <template v-else>
        <div class="insight-card-blue group">
          <div class="p-3 bg-white/20 rounded-xl">
            <Layers class="w-6 h-6" />
          </div>
          <div class="relative z-10">
            <p class="text-[10px] font-black uppercase tracking-widest opacity-70">Inventory</p>
            <p class="text-lg font-bold">{{ globalStats.unique_vendors || 0 }} Brands</p>
          </div>
          <div class="absolute -right-2 -bottom-2 opacity-10 group-hover:scale-110 transition-transform">
            <Layers class="w-16 h-16" />
          </div>
        </div>

        <div class="insight-card-indigo group">
          <div class="p-3 bg-white/20 rounded-xl">
            <Globe class="w-6 h-6" />
          </div>
          <div class="relative z-10">
            <p class="text-[10px] font-black uppercase tracking-widest opacity-70">DNS Queries</p>
            <p class="text-lg font-bold">{{ summary.dns?.total?.toLocaleString() || 0 }} <span
                class="text-xs font-normal opacity-60 ml-0.5">24h</span></p>
          </div>
          <div class="absolute -right-2 -bottom-2 opacity-10 group-hover:scale-110 transition-transform">
            <Globe class="w-16 h-16" />
          </div>
        </div>

        <div class="insight-card-rose group">
          <div class="p-3 bg-white/20 rounded-xl">
            <ShieldAlert class="w-6 h-6" />
          </div>
          <div class="relative z-10">
            <p class="text-[10px] font-black uppercase tracking-widest opacity-70">Block Rate</p>
            <p class="text-lg font-bold">{{ summary.dns?.block_rate || 0 }}% <span
                class="text-xs font-normal opacity-60 ml-0.5">Threats</span></p>
          </div>
          <div class="absolute -right-2 -bottom-2 opacity-10 group-hover:scale-110 transition-transform">
            <ShieldAlert class="w-16 h-16" />
          </div>
        </div>

        <div class="insight-card-slate group">
          <div class="p-3 bg-white/10 rounded-xl">
            <Zap class="w-6 h-6" />
          </div>
          <div class="relative z-10">
            <p class="text-[10px] font-black uppercase tracking-widest opacity-70">Top DNS Client</p>
            <p class="text-xs font-bold truncate max-w-[120px]">{{ summary.dns?.top_client || 'None' }}</p>
          </div>
          <div class="absolute -right-2 -bottom-2 opacity-10 group-hover:scale-110 transition-transform">
            <Activity class="w-16 h-16" />
          </div>
        </div>
      </template>
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Aggregate Traffic Chart -->
      <Card
        class="lg:col-span-2"
        :pt="{
          root: 'dashboard-card overflow-hidden',
          body: 'p-4',
          content: 'p-0'
        }"
      >
        <template #content>
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center gap-3">
              <div class="p-2 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-lg">
                <Activity class="w-5 h-5" />
              </div>
              <div>
                <h2 class="text-lg font-bold text-slate-900 dark:text-white">Network Throughput</h2>
                <p class="text-xs text-slate-500">Aggregate traffic across all devices (24h)</p>
              </div>
            </div>
            <div class="hidden sm:flex items-center gap-4">
              <Tag :pt="{ root: 'bg-transparent border-0 px-0 py-0' }">
                <template #default>
                  <div class="flex items-center gap-2">
                    <div class="w-2.5 h-2.5 rounded-full bg-emerald-500"></div>
                    <span class="text-[10px] font-black uppercase tracking-widest text-slate-600 dark:text-slate-300">Download</span>
                  </div>
                </template>
              </Tag>
              <Tag :pt="{ root: 'bg-transparent border-0 px-0 py-0' }">
                <template #default>
                  <div class="flex items-center gap-2">
                    <div class="w-2.5 h-2.5 rounded-full bg-blue-500"></div>
                    <span class="text-[10px] font-black uppercase tracking-widest text-slate-600 dark:text-slate-300">Upload</span>
                  </div>
                </template>
              </Tag>
            </div>
          </div>

          <div class="h-[300px] w-full">
            <template v-if="loading && trafficSeries[0].data.length === 0">
              <div class="skeleton-chart h-full flex flex-col justify-end gap-1 p-4">
                <Skeleton width="100%" height="60%" />
              </div>
            </template>
            <template v-else>
              <apexchart v-if="trafficSeries[0].data.length > 0" type="area" height="100%" :options="trafficChartOptions"
                :series="trafficSeries" />
              <div v-else class="h-full flex flex-col items-center justify-center text-slate-400 italic space-y-3">
                <div class="p-4 bg-slate-100 dark:bg-slate-900/50 rounded-full">
                  <Activity class="w-8 h-8 opacity-20" />
                </div>
                <p class="text-sm">No traffic data recorded in the last 24h</p>
              </div>
            </template>
          </div>
        </template>
      </Card>

      <!-- Device Distribution -->
      <Card
        :pt="{
          root: 'dashboard-card overflow-hidden',
          body: 'p-4',
          content: 'p-0'
        }"
      >
        <template #content>
          <h2 class="text-lg font-bold text-slate-900 dark:text-white mb-1">Device Types</h2>
          <p class="text-xs text-slate-500 mb-6">Inventory by category</p>

          <div class="h-[250px] flex items-center justify-center">
            <template v-if="loading && distributionSeries.length === 0">
              <Skeleton shape="circle" size="12rem" />
            </template>
            <template v-else>
              <apexchart v-if="distributionSeries.length > 0" type="donut" height="100%" :options="distributionOptions"
                :series="distributionSeries" />
              <div v-else class="text-slate-400 text-sm italic">Insufficient data</div>
            </template>
          </div>

          <div class="mt-6 space-y-2">
            <div v-for="(item, index) in distributionData.types.slice(0, 4)" :key="item.label"
              class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full" :class="categoryColorClasses[index]"></div>
                <span class="text-xs text-slate-600 dark:text-slate-400 capitalize">{{ item.label }}</span>
              </div>
              <span class="text-xs font-bold text-slate-900 dark:text-white">{{ item.value }}</span>
            </div>
          </div>
        </template>
      </Card>
    </div>

    <!-- DNS Activity Row -->
    <Card
      :pt="{
        root: 'dashboard-card overflow-hidden',
        body: 'p-4',
        content: 'p-0'
      }"
    >
      <template #content>
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-lg">
              <ShieldCheck class="w-5 h-5" />
            </div>
            <div>
              <h2 class="text-lg font-bold text-slate-900 dark:text-white">DNS Security Pulse</h2>
              <p class="text-xs text-slate-500">Global DNS activity and blocked threats (24h)</p>
            </div>
          </div>
          <div class="hidden sm:flex items-center gap-4">
            <Tag :pt="{ root: 'bg-transparent border-0 px-0 py-0' }">
              <template #default>
                <div class="flex items-center gap-2">
                  <div class="w-2.5 h-2.5 rounded-full bg-emerald-500"></div>
                  <span class="text-[10px] font-black uppercase tracking-widest text-slate-600 dark:text-slate-300">Passed</span>
                </div>
              </template>
            </Tag>
            <Tag :pt="{ root: 'bg-transparent border-0 px-0 py-0' }">
              <template #default>
                <div class="flex items-center gap-2">
                  <div class="w-2.5 h-2.5 rounded-full bg-rose-500"></div>
                  <span class="text-[10px] font-black uppercase tracking-widest text-slate-600 dark:text-slate-300">Blocked</span>
                </div>
              </template>
            </Tag>
          </div>
        </div>

        <div class="h-[200px] w-full">
          <template v-if="loading && dnsHistory.length === 0">
            <div class="skeleton-chart h-full flex flex-col justify-end gap-1 p-4">
              <Skeleton width="100%" height="50%" />
            </div>
          </template>
          <template v-else>
            <apexchart v-if="dnsHistory.length > 0" type="area" height="100%" :options="dnsChartOptions"
              :series="dnsHistorySeries" />
            <div v-else class="h-full flex flex-col items-center justify-center text-slate-400 italic space-y-3">
              <p class="text-sm">Waiting for DNS data sync...</p>
            </div>
          </template>
        </div>
      </template>
    </Card>

    <!-- Bottom Row: Activity & Top Consumers -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Live Activity -->
      <Card
        :pt="{
          root: 'dashboard-card-lg overflow-hidden',
          body: 'p-6',
          content: 'p-0'
        }"
      >
        <template #content>
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-lg font-bold text-slate-900 dark:text-white">Recent Activity</h2>
            <router-link to="/events"
              class="text-xs font-bold text-blue-500 hover:text-blue-600 transition-colors uppercase tracking-widest">
              View All
            </router-link>
          </div>

          <div class="space-y-4">
            <template v-if="loading && recentEvents.length === 0">
              <div v-for="i in 4" :key="'skel-event-' + i"
                class="flex items-center gap-4 p-3 bg-white/50 dark:bg-slate-900/30 rounded-xl border border-slate-100 dark:border-slate-700/50">
                <Skeleton shape="circle" size="2.25rem" />
                <div class="flex-1 space-y-2">
                  <Skeleton width="60%" height="0.875rem" />
                  <Skeleton width="40%" height="0.625rem" />
                </div>
                <Skeleton width="3rem" height="0.625rem" />
              </div>
            </template>
            <template v-else>
              <div v-for="event in recentEvents" :key="event.id"
                class="flex items-center gap-4 p-3 bg-white/50 dark:bg-slate-900/30 rounded-xl border border-slate-100 dark:border-slate-700/50 hover:border-blue-500/30 transition-all group">
                <div :class="[
                  event.status === 'online' ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600' : 'bg-slate-100 dark:bg-slate-700 text-slate-500',
                  'p-2 rounded-lg'
                ]">
                  <component :is="getIcon(event.icon || 'help-circle')" class="w-4 h-4" />
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between">
                    <p
                      class="text-sm font-bold text-slate-900 dark:text-white truncate group-hover:text-blue-600 transition-colors">
                      {{ event.display_name || event.ip }}
                    </p>
                    <span class="text-[10px] font-medium text-slate-500 whitespace-nowrap">{{ formatTime(event.changed_at)
                    }}</span>
                  </div>
                  <p class="text-xs text-slate-500 flex items-center gap-1.5 mt-0.5">
                    <Tag
                      :severity="event.status === 'online' ? 'success' : 'secondary'"
                      :value="event.status"
                      :pt="{
                        root: 'px-1.5 py-0 text-[9px] font-black uppercase tracking-widest rounded-md'
                      }"
                    />
                  </p>
                </div>
              </div>
              <div v-if="recentEvents.length === 0" class="py-12 text-center text-slate-400 italic text-sm">
                No recent activity detected
              </div>
            </template>
          </div>
        </template>
      </Card>

      <!-- Top Consumers -->
      <Card
        :pt="{
          root: 'dashboard-card-lg overflow-hidden',
          body: 'p-6',
          content: 'p-0'
        }"
      >
        <template #content>
          <h2 class="text-lg font-bold text-slate-900 dark:text-white mb-6">Top Consumers <span
              class="text-xs font-normal text-slate-500 ml-2">(24h)</span></h2>

          <div class="space-y-4">
            <template v-if="loading && topConsumers.length === 0">
              <div v-for="i in 5" :key="'skel-consumer-' + i" class="flex items-center gap-4">
                <Skeleton width="2.5rem" height="2.5rem" borderRadius="12px" />
                <div class="flex-1 space-y-2">
                  <Skeleton width="50%" height="0.875rem" />
                  <Skeleton width="30%" height="0.625rem" />
                </div>
                <div class="space-y-1 flex flex-col items-end">
                  <Skeleton width="3.5rem" height="0.875rem" />
                  <Skeleton width="5rem" height="0.5rem" />
                </div>
              </div>
            </template>
            <template v-else>
              <div v-for="(device, idx) in topConsumers" :key="device.id" class="group">
                <div class="flex items-center gap-4">
                  <div class="relative">
                    <div
                      class="w-10 h-10 p-2 bg-slate-100 dark:bg-slate-900/50 rounded-xl group-hover:bg-blue-50 dark:group-hover:bg-blue-900/30 transition-colors">
                      <component :is="getIcon(device.icon || 'help-circle')"
                        class="w-full h-full text-slate-600 dark:text-slate-400" />
                    </div>
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-bold text-slate-900 dark:text-white truncate">{{ device.name || device.ip }}</p>
                    <p class="text-[10px] text-slate-500 font-mono">{{ device.ip }}</p>
                  </div>
                  <div class="text-right">
                    <p class="text-sm font-black text-slate-900 dark:text-white">{{ formatBytes(device.total) }}</p>
                    <div class="flex items-center justify-end gap-2 text-[9px] font-bold text-slate-500">
                      <span class="flex items-center gap-0.5">
                        <ArrowDown class="w-2 h-2 text-emerald-500" /> {{ formatBytes(device.download, 0) }}
                      </span>
                      <span class="flex items-center gap-0.5">
                        <ArrowUp class="w-2 h-2 text-blue-500" /> {{ formatBytes(device.upload, 0) }}
                      </span>
                    </div>
                  </div>
                </div>
                <!-- Bandwidth proportion bar -->
                <div v-if="maxConsumerTotal > 0" class="mt-2 ml-14">
                  <ProgressBar
                    :value="Math.round((device.total / maxConsumerTotal) * 100)"
                    :showValue="false"
                    :pt="{
                      root: 'h-1 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden',
                      value: 'h-full rounded-full transition-all duration-500 ' + consumerBarColors[idx % consumerBarColors.length]
                    }"
                  />
                </div>
              </div>
              <div v-if="topConsumers.length === 0" class="py-12 text-center text-slate-400 italic text-sm">
                No traffic data available. Ensure OpenWRT integration is active.
              </div>
            </template>
          </div>

          <!-- Summary Card -->
          <div v-if="topConsumers.length > 0"
            class="mt-8 p-4 bg-blue-600 rounded-2xl text-white overflow-hidden relative group">
            <Zap class="absolute -right-4 -bottom-4 w-24 h-24 text-white/10 group-hover:scale-110 transition-transform" />
            <p class="text-[10px] font-black uppercase tracking-[0.2em] opacity-80">Total Throughput</p>
            <div class="mt-1 flex items-baseline gap-2">
              <span class="text-3xl font-black">{{ formatBytes(aggregateTotals.download + aggregateTotals.upload)
              }}</span>
              <span class="text-xs font-bold opacity-70">processed in 24h</span>
            </div>
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import api from '@/utils/api'
import * as LucideIcons from 'lucide-vue-next'
import {
  Database, Wifi, WifiOff, ShieldAlert, Activity, RefreshCw,
  Layers, ArrowDown, ArrowUp, Zap, HelpCircle, Lock, ShieldCheck, Search, Globe
} from 'lucide-vue-next'
import { formatRelativeTime, parseUTC } from '@/utils/date'
import { useWebSockets } from '@/composables/useWebSockets'
import { watch } from 'vue'

// PrimeVue components
import Card from 'primevue/card'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import ProgressBar from 'primevue/progressbar'
import Skeleton from 'primevue/skeleton'

const { lastNotification } = useWebSockets()

watch(lastNotification, (notif) => {
  if (notif && (notif.event_type === 'new_device' || notif.event_type === 'status_changed' || notif.event_type === 'completed')) {
    fetchAllData()
  }
})

const loading = ref(false)
const statsLoaded = ref(false)
const globalStats = ref({
  total: 0,
  online: 0,
  offline: 0,
  untrusted: 0,
  trusted: 0,
  new_24h: 0,
  total_ports: 0,
  unique_vendors: 0
})
const trafficData = ref([])
const aggregateTotals = ref({ download: 0, upload: 0 })
const distributionData = ref({ vendors: [], types: [] })
const recentEvents = ref([])
const topConsumers = ref([])
const dnsHistory = ref([])
const summary = ref({
  traffic: { download: 0, upload: 0 },
  dns: { total: 0, blocked: 0, block_rate: 0, top_client: 'None' }
})

const mainStats = computed(() => [
  {
    label: 'Total Devices',
    value: globalStats.value.total,
    icon: Database,
    bgClass: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
    trend: `${Math.round((globalStats.value.trusted / (globalStats.value.total || 1)) * 100)}% Trusted`,
    trendColor: 'text-blue-600 dark:text-blue-400'
  },
  {
    label: 'Online Now',
    value: globalStats.value.online,
    icon: Wifi,
    bgClass: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400',
    trend: `${Math.round((globalStats.value.online / (globalStats.value.total || 1)) * 100)}% Active`,
    trendColor: 'text-emerald-600 dark:text-emerald-400'
  },
  {
    label: 'Open Ports',
    value: globalStats.value.total_ports || 0,
    icon: Lock,
    bgClass: 'bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400',
    trend: 'Audited',
    trendColor: 'text-amber-600'
  },
  {
    label: 'Untrusted',
    value: globalStats.value.untrusted,
    icon: ShieldAlert,
    bgClass: 'bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400',
    trend: globalStats.value.untrusted > 0 ? `${globalStats.value.untrusted} Verify` : 'Secure',
    trendColor: globalStats.value.untrusted > 0 ? 'text-rose-600' : 'text-emerald-600'
  }
])

const categoryColorClasses = [
  'bg-blue-500',
  'bg-emerald-500',
  'bg-amber-500',
  'bg-red-500',
  'bg-violet-500',
  'bg-cyan-500'
]

const consumerBarColors = [
  'bg-blue-500',
  'bg-emerald-500',
  'bg-amber-500',
  'bg-violet-500',
  'bg-cyan-500'
]

const maxConsumerTotal = computed(() => {
  if (topConsumers.value.length === 0) return 0
  return Math.max(...topConsumers.value.map(d => d.total || 0))
})

const getIcon = (name) => {
  if (!name) return HelpCircle
  const camel = name.split('-').map(p => p.charAt(0).toUpperCase() + p.slice(1)).join('')
  return LucideIcons[camel] || LucideIcons[name] || HelpCircle
}

const formatTime = (ts) => formatRelativeTime(ts)

const formatBytes = (bytes, decimals = 2) => {
  if (!bytes) return '0 B'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

// Chart Options
const trafficChartOptions = computed(() => ({
  chart: {
    id: 'aggregate-traffic',
    toolbar: { show: false },
    background: 'transparent',
    fontFamily: 'inherit',
    sparkline: { enabled: false },
    zoom: { enabled: false }
  },
  xaxis: {
    type: 'datetime',
    labels: {
      style: { colors: '#94a3b8', fontSize: '9px', fontWeight: 600 },
      datetimeFormatter: { hour: 'HH:mm' }
    },
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  yaxis: {
    labels: {
      style: { colors: '#94a3b8', fontSize: '9px' },
      formatter: (val) => formatBytes(val, 0)
    }
  },
  stroke: { curve: 'smooth', width: 3 },
  colors: ['#10b981', '#3b82f6'],
  fill: {
    type: 'gradient',
    gradient: { opacityFrom: 0.4, opacityTo: 0.05 }
  },
  dataLabels: { enabled: false },
  grid: { borderColor: 'rgba(148, 163, 184, 0.05)', strokeDashArray: 4 },
  tooltip: {
    theme: 'dark',
    x: { format: 'HH:mm' },
    y: { formatter: (val) => formatBytes(val) }
  }
}))

const trafficSeries = computed(() => [
  { name: 'Download', data: trafficData.value.map(d => ({ x: parseUTC(d.timestamp).toJSDate().getTime(), y: d.download || 0 })) },
  { name: 'Upload', data: trafficData.value.map(d => ({ x: parseUTC(d.timestamp).toJSDate().getTime(), y: d.upload || 0 })) }
])

const distributionOptions = computed(() => ({
  chart: { fontFamily: 'inherit' },
  labels: distributionData.value.types.map(t => t.label),
  colors: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],
  stroke: { show: false },
  legend: { show: false },
  dataLabels: { enabled: false },
  plotOptions: {
    pie: {
      donut: {
        size: '75%',
        labels: {
          show: true,
          total: {
            show: true,
            label: 'Total',
            fontSize: '10px',
            fontFamily: 'inherit',
            fontWeight: 800,
            color: '#94a3b8',
            formatter: () => globalStats.value.total
          },
          value: {
            fontSize: '20px',
            fontWeight: 900,
            fontFamily: 'inherit',
            color: '#1e293b'
          }
        }
      }
    }
  }
}))

const dnsHistorySeries = computed(() => [
  { name: 'Passed', data: dnsHistory.value.map(d => ({ x: parseUTC(d.timestamp).toJSDate().getTime(), y: d.total - d.blocked })) },
  { name: 'Blocked', data: dnsHistory.value.map(d => ({ x: parseUTC(d.timestamp).toJSDate().getTime(), y: d.blocked })) }
])

const dnsChartOptions = computed(() => ({
  ...trafficChartOptions.value,
  chart: { ...trafficChartOptions.value.chart, id: 'dns-security-trend' },
  colors: ['#10b981', '#ef4444'],
  yaxis: { ...trafficChartOptions.value.yaxis, labels: { ...trafficChartOptions.value.yaxis.labels, formatter: (val) => Math.round(val) } },
  tooltip: { ...trafficChartOptions.value.tooltip, y: { formatter: (val) => `${Math.round(val)} queries` } }
}))

const distributionSeries = computed(() => distributionData.value.types.map(t => t.value))

const fetchAllData = async () => {
  loading.value = true
  try {
    const [devs, traffic, dist, events, top, dnsTr] = await Promise.all([
      api.get('/devices/'),
      api.get('/analytics/traffic?range=24h'),
      api.get('/analytics/distribution'),
      api.get('/events/?limit=5'),
      api.get('/analytics/top-devices?limit=5'),
      api.get('/analytics/dns/traffic?range=24h')
    ])

    if (devs.data.global_stats) globalStats.value = devs.data.global_stats
    trafficData.value = traffic.data.series
    aggregateTotals.value = traffic.data.totals
    distributionData.value = dist.data
    recentEvents.value = events.data
    topConsumers.value = top.data
    dnsHistory.value = dnsTr.data
    statsLoaded.value = true

    try {
      const gSummary = await api.get('/analytics/summary')
      summary.value = gSummary.data
    } catch (e) {
      console.error('Failed to fetch summary:', e)
    }
  } catch (e) {
    console.error('Failed to fetch dashboard data:', e)
  } finally {
    loading.value = false
  }
}

let pollTimer = null

onMounted(() => {
  fetchAllData()
  pollTimer = setInterval(fetchAllData, 30000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>
