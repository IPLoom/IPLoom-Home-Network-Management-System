<template>
  <v-container fluid class="pa-4 d-flex flex-column gap-4">
    <!-- Header -->
    <div class="d-flex flex-column flex-md-row align-md-center justify-space-between mb-2 gap-4">
      <div>
        <h1 class="text-h4 font-weight-bold">Dashboard</h1>
        <p class="text-subtitle-2 text-medium-emphasis mt-1">Network overview and real-time monitoring</p>
      </div>
      <div class="d-none d-md-flex align-center px-3 py-1 rounded-pill" style="background-color: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2);">
        <div class="bg-success rounded-circle pulse-animation mr-2" style="width: 8px; height: 8px;"></div>
        <span class="text-caption font-weight-bold text-uppercase text-success" style="letter-spacing: 0.05em;">Scanner Active</span>
      </div>
    </div>

    <!-- Stats Grid -->
    <v-row>
      <v-col v-for="stat in mainStats" :key="stat.label" cols="12" sm="6" lg="3">
        <v-card variant="flat" border class="h-100 position-relative overflow-hidden bg-surface-elevated">
          <component :is="stat.icon" class="position-absolute text-medium-emphasis" style="width: 96px; height: 96px; right: -16px; top: -16px; opacity: 0.05;" />
          <v-card-item>
            <div class="d-flex align-center justify-space-between mb-4">
              <v-avatar rounded :class="stat.bgClass" size="40">
                <component :is="stat.icon" style="width: 20px; height: 20px;" />
              </v-avatar>
              <v-chip v-if="stat.trend" size="small" :color="stat.trendColor" variant="tonal" class="font-weight-bold">
                {{ stat.trend }}
              </v-chip>
            </div>
            <div class="text-h4 font-weight-bold">{{ stat.value }}</div>
            <div class="text-overline text-medium-emphasis">{{ stat.label }}</div>
          </v-card-item>
        </v-card>
      </v-col>
    </v-row>

    <!-- Insights Row -->
    <v-row>
      <v-col cols="12" sm="6" md="3">
        <v-card class="bg-blue-darken-2 position-relative overflow-hidden text-white" elevation="4" rounded="lg">
          <Layers class="position-absolute" style="width: 64px; height: 64px; right: -8px; bottom: -8px; opacity: 0.1;" />
          <v-card-item>
            <div class="d-flex align-center gap-4">
              <v-avatar color="rgba(255,255,255,0.2)" rounded>
                <Layers style="width: 24px; height: 24px;" />
              </v-avatar>
              <div>
                <div class="text-caption font-weight-bold text-uppercase opacity-70">Inventory</div>
                <div class="text-h6 font-weight-bold">{{ globalStats.unique_vendors || 0 }} Brands</div>
              </div>
            </div>
          </v-card-item>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="bg-indigo-darken-2 position-relative overflow-hidden text-white" elevation="4" rounded="lg">
          <Globe class="position-absolute" style="width: 64px; height: 64px; right: -8px; bottom: -8px; opacity: 0.1;" />
          <v-card-item>
            <div class="d-flex align-center gap-4">
              <v-avatar color="rgba(255,255,255,0.2)" rounded>
                <Globe style="width: 24px; height: 24px;" />
              </v-avatar>
              <div>
                <div class="text-caption font-weight-bold text-uppercase opacity-70">DNS Queries</div>
                <div class="text-h6 font-weight-bold">{{ summary.dns?.total?.toLocaleString() || 0 }} <span class="text-caption opacity-60">24h</span></div>
              </div>
            </div>
          </v-card-item>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="bg-pink-darken-2 position-relative overflow-hidden text-white" elevation="4" rounded="lg">
          <ShieldAlert class="position-absolute" style="width: 64px; height: 64px; right: -8px; bottom: -8px; opacity: 0.1;" />
          <v-card-item>
            <div class="d-flex align-center gap-4">
              <v-avatar color="rgba(255,255,255,0.2)" rounded>
                <ShieldAlert style="width: 24px; height: 24px;" />
              </v-avatar>
              <div>
                <div class="text-caption font-weight-bold text-uppercase opacity-70">Block Rate</div>
                <div class="text-h6 font-weight-bold">{{ summary.dns?.block_rate || 0 }}% <span class="text-caption opacity-60">Threats</span></div>
              </div>
            </div>
          </v-card-item>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="bg-blue-grey-darken-3 position-relative overflow-hidden text-white" elevation="4" rounded="lg">
          <Activity class="position-absolute" style="width: 64px; height: 64px; right: -8px; bottom: -8px; opacity: 0.1;" />
          <v-card-item>
            <div class="d-flex align-center gap-4">
              <v-avatar color="rgba(255,255,255,0.2)" rounded>
                <Zap style="width: 24px; height: 24px;" />
              </v-avatar>
              <div>
                <div class="text-caption font-weight-bold text-uppercase opacity-70">Top DNS Client</div>
                <div class="text-subtitle-2 font-weight-bold text-truncate" style="max-width: 120px;">{{ summary.dns?.top_client || 'None' }}</div>
              </div>
            </div>
          </v-card-item>
        </v-card>
      </v-col>
    </v-row>

    <!-- Charts Row -->
    <v-row>
      <!-- Aggregate Traffic Chart -->
      <v-col cols="12" lg="8">
        <v-card variant="flat" border class="h-100 bg-surface-elevated" rounded="lg">
          <v-card-title class="d-flex align-center justify-space-between pa-4 pb-0">
            <div class="d-flex align-center gap-3">
              <v-avatar color="blue-lighten-5 text-blue" rounded size="40">
                <Activity style="width: 20px; height: 20px;" />
              </v-avatar>
              <div>
                <div class="text-h6 font-weight-bold">Network Throughput</div>
                <div class="text-caption text-medium-emphasis">Aggregate traffic across all devices (24h)</div>
              </div>
            </div>
          </v-card-title>
          <v-card-text style="height: 300px;" class="mt-4">
            <apexchart v-if="trafficSeries[0].data.length > 0" type="area" height="100%" :options="trafficChartOptions" :series="trafficSeries" />
            <div v-else class="h-100 d-flex flex-column align-center justify-center text-medium-emphasis font-italic">
              <v-avatar color="surface-variant" size="64" class="mb-4">
                <Activity style="width: 32px; height: 32px; opacity: 0.2;" />
              </v-avatar>
              No traffic data recorded in the last 24h
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Device Distribution -->
      <v-col cols="12" lg="4">
        <v-card variant="flat" border class="h-100 bg-surface-elevated" rounded="lg">
          <v-card-title class="pa-4 pb-0">
            <div class="text-h6 font-weight-bold">Device Types</div>
            <div class="text-caption text-medium-emphasis">Inventory by category</div>
          </v-card-title>
          <v-card-text class="d-flex flex-column mt-4">
            <div style="height: 200px;" class="d-flex align-center justify-center">
              <apexchart v-if="distributionSeries.length > 0" type="donut" height="100%" :options="distributionOptions" :series="distributionSeries" />
              <div v-else class="text-medium-emphasis font-italic">Insufficient data</div>
            </div>
            <div class="mt-4 d-flex flex-column gap-2">
              <div v-for="(item, index) in distributionData.types.slice(0, 4)" :key="item.label" class="d-flex align-center justify-space-between">
                <div class="d-flex align-center gap-2">
                  <v-badge dot inline :color="categoryColorClasses[index]" class="mr-2"></v-badge>
                  <span class="text-caption text-capitalize text-medium-emphasis">{{ item.label }}</span>
                </div>
                <span class="text-caption font-weight-bold">{{ item.value }}</span>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- DNS Activity Row -->
    <v-row>
      <v-col cols="12">
        <v-card variant="flat" border class="h-100 bg-surface-elevated" rounded="lg">
          <v-card-title class="d-flex align-center justify-space-between pa-4 pb-0">
            <div class="d-flex align-center gap-3">
              <v-avatar color="indigo-lighten-5 text-indigo" rounded size="40">
                <ShieldCheck style="width: 20px; height: 20px;" />
              </v-avatar>
              <div>
                <div class="text-h6 font-weight-bold">DNS Security Pulse</div>
                <div class="text-caption text-medium-emphasis">Global DNS activity and blocked threats (24h)</div>
              </div>
            </div>
          </v-card-title>
          <v-card-text style="height: 250px;" class="mt-4">
            <apexchart v-if="dnsHistory.length > 0" type="area" height="100%" :options="dnsChartOptions" :series="dnsHistorySeries" />
            <div v-else class="h-100 d-flex flex-column align-center justify-center text-medium-emphasis font-italic">
              Waiting for DNS data sync...
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Bottom Row: Activity & Top Consumers -->
    <v-row>
      <!-- Live Activity -->
      <v-col cols="12" lg="6">
        <v-card variant="flat" border class="h-100 bg-surface-elevated" rounded="lg">
          <v-card-title class="d-flex align-center justify-space-between pa-4">
            <div class="text-h6 font-weight-bold">Recent Activity</div>
            <v-btn variant="text" color="primary" size="small" class="text-overline" to="/events">View All</v-btn>
          </v-card-title>
          <v-list bg-color="transparent" class="px-2 pb-4">
            <div v-if="recentEvents.length === 0" class="text-center text-medium-emphasis font-italic py-8">No recent activity detected</div>
            <v-list-item v-for="event in recentEvents" :key="event.id" class="mb-2 bg-surface-variant rounded-lg border">
              <template v-slot:prepend>
                <v-avatar rounded :color="event.status === 'online' ? 'success' : 'grey'" variant="tonal" size="40" class="mr-4">
                  <component :is="getIcon(event.icon || 'help-circle')" style="width: 20px; height: 20px;" />
                </v-avatar>
              </template>
              <div class="d-flex justify-space-between align-center">
                <v-list-item-title class="font-weight-bold text-truncate" style="max-width: 250px;">{{ event.display_name || event.ip }}</v-list-item-title>
                <span class="text-caption text-medium-emphasis">{{ formatTime(event.changed_at) }}</span>
              </div>
              <v-list-item-subtitle class="mt-1 d-flex align-center gap-1">
                <v-badge dot inline :color="event.status === 'online' ? 'success' : 'grey'"></v-badge>
                Became {{ event.status }}
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>

      <!-- Top Consumers -->
      <v-col cols="12" lg="6">
        <v-card variant="flat" border class="h-100 bg-surface-elevated" rounded="lg">
          <v-card-title class="pa-4">
            <span class="text-h6 font-weight-bold">Top Consumers</span>
            <span class="text-caption text-medium-emphasis ml-2">(24h)</span>
          </v-card-title>
          <v-list bg-color="transparent" class="px-2">
            <div v-if="topConsumers.length === 0" class="text-center text-medium-emphasis font-italic py-8">No traffic data available. Ensure OpenWRT integration is active.</div>
            <v-list-item v-for="device in topConsumers" :key="device.id" class="mb-2">
              <template v-slot:prepend>
                <v-avatar rounded color="grey" variant="tonal" size="40" class="mr-4">
                  <component :is="getIcon(device.icon || 'help-circle')" style="width: 20px; height: 20px;" />
                </v-avatar>
              </template>
              <v-list-item-title class="font-weight-bold text-truncate" style="max-width: 180px;">{{ device.name || device.ip }}</v-list-item-title>
              <v-list-item-subtitle class="font-family-mono mt-1">{{ device.ip }}</v-list-item-subtitle>
              <template v-slot:append>
                <div class="text-right">
                  <div class="text-body-2 font-weight-black">{{ formatBytes(device.total) }}</div>
                  <div class="text-caption text-medium-emphasis font-weight-bold mt-1 d-flex align-center justify-end gap-2">
                    <span class="d-flex align-center"><ArrowDown style="width: 10px; height: 10px; color: #10b981; margin-right: 2px;" /> {{ formatBytes(device.download, 0) }}</span>
                    <span class="d-flex align-center"><ArrowUp style="width: 10px; height: 10px; color: #3b82f6; margin-right: 2px;" /> {{ formatBytes(device.upload, 0) }}</span>
                  </div>
                </div>
              </template>
            </v-list-item>
          </v-list>
          <div v-if="topConsumers.length > 0" class="ma-4 pa-4 bg-blue-darken-2 text-white rounded-lg position-relative overflow-hidden">
            <Zap class="position-absolute" style="width: 96px; height: 96px; right: -16px; bottom: -16px; opacity: 0.1;" />
            <div class="text-caption font-weight-black text-uppercase opacity-80" style="letter-spacing: 0.2em;">Total Throughput</div>
            <div class="d-flex align-baseline gap-2 mt-1">
              <span class="text-h4 font-weight-black">{{ formatBytes(aggregateTotals.download + aggregateTotals.upload) }}</span>
              <span class="text-caption font-weight-bold opacity-70">processed in 24h</span>
            </div>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
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

const { lastNotification } = useWebSockets()

watch(lastNotification, (notif) => {
  if (notif && (notif.event_type === 'new_device' || notif.event_type === 'status_changed' || notif.event_type === 'completed')) {
    fetchAllData()
  }
})

const loading = ref(false)
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
    bgClass: 'bg-blue-lighten-4 text-blue',
    trend: `${Math.round((globalStats.value.trusted / (globalStats.value.total || 1)) * 100)}% Trusted`,
    trendColor: 'blue'
  },
  {
    label: 'Online Now',
    value: globalStats.value.online,
    icon: Wifi,
    bgClass: 'bg-green-lighten-4 text-green',
    trend: `${Math.round((globalStats.value.online / (globalStats.value.total || 1)) * 100)}% Active`,
    trendColor: 'success'
  },
  {
    label: 'Open Ports',
    value: globalStats.value.total_ports || 0,
    icon: Lock,
    bgClass: 'bg-amber-lighten-4 text-amber',
    trend: 'Audited',
    trendColor: 'warning'
  },
  {
    label: 'Untrusted',
    value: globalStats.value.untrusted,
    icon: ShieldAlert,
    bgClass: 'bg-red-lighten-4 text-red',
    trend: globalStats.value.untrusted > 0 ? `${globalStats.value.untrusted} Verify` : 'Secure',
    trendColor: globalStats.value.untrusted > 0 ? 'error' : 'success'
  }
])

const categoryColorClasses = [
  'blue',
  'green',
  'amber',
  'red',
  'deep-purple',
  'cyan'
]

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
            formatter: () => String(globalStats.value.total || 0)
          },
          value: {
            fontSize: '20px',
            fontWeight: 900,
            fontFamily: 'inherit'
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

<style scoped>
.pulse-animation {
  animation: pulse-dot-anim 2s infinite;
}

@keyframes pulse-dot-anim {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.5; }
}
</style>
