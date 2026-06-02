<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="page-header">
            <div>
                <h1 class="text-2xl font-semibold text-slate-900 dark:text-white">Logs & Activity</h1>
                <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    {{ currentTab === 'scans' ? 'Discovery activity log and network scans.' : 'View backend system events and monitoring.' }}
                </p>
            </div>
            <!-- Tab Switcher (Custom) -->
            <div class="flex items-center gap-1.5 p-1 bg-slate-50/80 dark:bg-slate-800/40 rounded-xl border border-slate-200/50 dark:border-slate-700/30 overflow-x-auto whitespace-nowrap shrink-0">
                <button @click="currentTab = 'all'"
                    class="px-3 h-9 rounded-lg flex items-center gap-2 text-xs font-semibold transition-all border-none outline-none cursor-pointer"
                    :class="currentTab === 'all' ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' : 'text-slate-600 dark:text-slate-400 hover:bg-white dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-white bg-transparent'">
                    <Activity class="w-3.5 h-3.5" />
                    <span>System</span>
                </button>
                <button @click="currentTab = 'tasks'"
                    class="px-3 h-9 rounded-lg flex items-center gap-2 text-xs font-semibold transition-all border-none outline-none cursor-pointer"
                    :class="currentTab === 'tasks' ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' : 'text-slate-600 dark:text-slate-400 hover:bg-white dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-white bg-transparent'">
                    <Cog class="w-3.5 h-3.5" />
                    <span>Tasks</span>
                </button>
                <button @click="currentTab = 'scans'"
                    class="px-3 h-9 rounded-lg flex items-center gap-2 text-xs font-semibold transition-all border-none outline-none cursor-pointer"
                    :class="currentTab === 'scans' ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' : 'text-slate-600 dark:text-slate-400 hover:bg-white dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-white bg-transparent'">
                    <Radar class="w-3.5 h-3.5" />
                    <span>Scans</span>
                </button>
            </div>
        </div>

        <template v-if="currentTab === 'scans'">
            <!-- Scan Specific Toolbar -->
            <div class="glass-panel flex flex-col md:flex-row gap-4 items-center justify-between">
                <div class="flex items-center gap-2 text-slate-500 text-sm">
                    <Activity class="w-4 h-4" />
                    <span>Recent scans and discovery history</span>
                </div>
                <div class="flex items-center gap-2">
                    <button @click="scanTabRef?.runDiscovery()" :disabled="scanTabRef?.isScanning" class="h-10 px-6 flex items-center justify-center gap-2 bg-blue-500/10 text-blue-600 border border-blue-500/20 hover:bg-blue-500 hover:text-white rounded-xl text-xs font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap" v-tooltip="'Start Network Discovery'">
                        <component :is="scanTabRef?.isScanning ? RefreshCw : Radar" class="w-4 h-4" :class="{ 'animate-spin': scanTabRef?.isScanning }" />
                        Run Discovery
                    </button>
                    <button @click="scanTabRef?.clearQueue()" class="btn-action hover:!text-red-500 dark:hover:!text-red-400"
                        v-tooltip="'Clear Scan Queue'">
                        <Trash2 class="w-4 h-4" />
                    </button>
                    <button @click="scanTabRef?.fetchScans()" class="btn-action" v-tooltip="'Refresh Scan History'">
                        <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': scanTabRef?.isRefreshing }" />
                    </button>
                </div>
            </div>
            <ScanHistoryTab ref="scanTabRef" />
        </template>
        <template v-else>
            <!-- Filters & Search Toolbar (PrimeVue Select and InputText) -->
            <div class="glass-panel flex flex-col gap-4">
                <div class="flex flex-col md:flex-row gap-4 items-center">
                    <div class="relative flex-1 w-full">
                        <IconField>
                            <InputIcon class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400">
                                <Search class="h-4 w-4" />
                            </InputIcon>
                            <InputText v-model="search" @input="debounceSearch" type="text" placeholder="Search logs..."
                                class="w-full !pl-10 h-10 border border-slate-200 dark:border-slate-700/60 bg-white dark:bg-slate-800 rounded-xl text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none" />
                        </IconField>
                    </div>
                    <div class="flex flex-col sm:flex-row items-center gap-2 w-full md:w-auto">
                        <!-- Task Type Filter -->
                        <Select v-if="currentTab === 'tasks'"
                            v-model="taskTypeFilter"
                            :options="taskTypeOptions"
                            optionLabel="label"
                            optionValue="value"
                            @change="fetchLogs"
                            placeholder="All Types"
                            class="w-full md:w-56"
                            :pt="{
                                root: { class: 'h-10 px-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/60 rounded-xl flex items-center justify-between text-sm outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500' }
                            }"
                        />

                        <!-- Level Filter -->
                        <Select v-else
                            v-model="levelFilter"
                            :options="levelOptions"
                            optionLabel="label"
                            optionValue="value"
                            @change="fetchLogs"
                            placeholder="All Levels"
                            class="w-full md:w-44"
                            :pt="{
                                root: { class: 'h-10 px-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/60 rounded-xl flex items-center justify-between text-sm outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500' }
                            }"
                        />

                        <!-- Rows Limit Filter -->
                        <Select
                            v-model="limit"
                            :options="[20, 50, 100, 200]"
                            @change="fetchLogs"
                            placeholder="Limit"
                            class="w-full md:w-28"
                            :pt="{
                                root: { class: 'h-10 px-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/60 rounded-xl flex items-center justify-between text-sm outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500' }
                            }"
                        />

                        <!-- Toolbar Actions -->
                        <div class="flex items-center gap-2 ml-1">
                            <button @click="fetchLogs" class="btn-action h-10" v-tooltip="'Refresh Logs'">
                                <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
                            </button>
                            <button @click.stop="promptClearLogs"
                                class="btn-action h-10 hover:!text-red-500 hover:!bg-red-50 dark:hover:!bg-red-900/20"
                                v-tooltip="'Clear All Logs'">
                                <Trash2 class="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Display Info Line -->
                <div
                    class="px-2 flex items-center justify-between text-[11px] font-medium text-slate-500 dark:text-slate-400">
                    <div class="flex items-center gap-2">
                        <Activity class="h-3.5 w-3.5 text-blue-500" />
                        <span>Showing <b>{{ displayedLogs.length }}</b> of <b>{{ displayTotal }}</b> logs matching current
                            filters</span>
                    </div>
                    <div v-if="currentTab === 'tasks'" class="flex items-center gap-2">
                        <span class="text-xs font-medium text-slate-500 dark:text-slate-400">Auto-refresh (5s)</span>
                        <ToggleSwitch v-model="autoRefresh" />
                    </div>
                </div>
            </div>

            <!-- Logs Table -->
            <div class="content-panel">
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                        <thead class="bg-slate-50 dark:bg-slate-900/50">
                            <tr>
                                <th scope="col" class="table-header-cell w-48">Timestamp</th>
                                <th scope="col" class="table-header-cell w-24">
                                    {{ currentTab === 'tasks' ? 'Type' : 'Level' }}
                                </th>
                                <th scope="col" class="table-header-cell w-48">
                                    {{ currentTab === 'tasks' ? 'Target' : 'Module' }}
                                </th>
                                <th scope="col" class="table-header-cell">Message</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-200 dark:divide-slate-700">
                            <tr v-if="loading && logs.length === 0">
                                <td colspan="4" class="px-6 py-20 text-center">
                                    <RefreshCw class="h-8 w-8 mx-auto animate-spin mb-2 text-slate-400" />
                                    <p class="text-slate-500 dark:text-slate-400">Loading logs...</p>
                                </td>
                            </tr>
                            <tr v-else-if="logs.length === 0">
                                <td colspan="4" class="px-6 py-20 text-center">
                                    <p class="text-slate-500 dark:text-slate-400 italic">No logs found matching your
                                        criteria.</p>
                                </td>
                            </tr>
                            <tr v-for="(log, idx) in displayedLogs" :key="idx" class="hover-row">
                                <td class="table-data-cell font-mono text-xs opacity-70">
                                    {{ formatTime(log.timestamp) }}
                                </td>

                                <!-- Task Type or Level -->
                                <td class="table-data-cell">
                                    <span v-if="currentTab === 'tasks'" :class="[
                                        'inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider',
                                        getTaskColor(log.task_type)
                                    ]">
                                        <component :is="getTaskIcon(log.task_type)" class="w-3 h-3" />
                                        {{ getTaskLabel(log.task_type) }}
                                    </span>
                                    <span v-else :class="[
                                        'inline-flex items-center px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider',
                                        levelColors[log.level] || 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300'
                                    ]">
                                        {{ log.level }}
                                    </span>
                                </td>

                                <!-- Target or Module -->
                                <td class="table-data-cell font-mono text-xs opacity-70">
                                    <div v-if="currentTab === 'tasks'" class="flex flex-col">
                                        <span class="font-bold text-slate-700 dark:text-slate-300">{{ log.target || '-'
                                        }}</span>
                                        <span v-if="log.event_type" class="text-[10px] uppercase tracking-wide"
                                            :class="{ 'text-green-600': log.event_type === 'completed', 'text-blue-600': log.event_type === 'started', 'text-red-600': log.event_type === 'failed' }">
                                            {{ log.event_type }}
                                        </span>
                                    </div>
                                    <span v-else :title="log.path">{{ log.module }}:{{ log.line }}</span>
                                </td>

                                <!-- Message and Details -->
                                <td class="table-data-cell font-mono text-sm break-all">
                                    {{ log.message }}

                                    <!-- Task Duration Badge -->
                                    <span v-if="log.duration_ms"
                                        class="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                                        ⏱ {{ log.duration_ms }}ms
                                    </span>

                                    <!-- Task Details JSON -->
                                    <div v-if="log.details" class="mt-2 text-xs text-slate-500 font-mono">
                                        <span v-for="(val, key) in log.details" :key="key" class="mr-3 inline-block">
                                            <span class="opacity-70">{{ key }}:</span> <span class="font-medium">{{ val
                                            }}</span>
                                        </span>
                                    </div>

                                    <div v-if="log.exception"
                                        class="mt-2 p-3 bg-red-50/50 dark:bg-red-900/10 rounded-lg border border-red-100 dark:border-red-900/30 text-xs text-red-600 dark:text-red-400 whitespace-pre-wrap font-mono overflow-x-auto">
                                        {{ log.exception }}
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Pagination -->
                <div v-if="totalPages > 1"
                    class="flex justify-center items-center gap-2 p-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/30">
                    <button @click="changePage(page - 1)" :disabled="page <= 1" class="pagination-btn">
                        Previous
                    </button>
                    <div
                        class="px-4 py-2 bg-slate-900 dark:bg-white rounded-lg text-sm font-medium text-white dark:text-slate-900">
                        {{ page }} / {{ totalPages }}
                    </div>
                    <button @click="changePage(page + 1)" :disabled="page >= totalPages" class="pagination-btn">
                        Next
                    </button>
                </div>
            </div>
        </template>
    </div>

    <ConfirmationModal :isOpen="showClearConfirm" title="Clear All Logs"
        message="Are you sure you want to delete all system logs? This action cannot be undone and you will lose all historical event data."
        confirmText="Yes, Clear Logs" type="danger" :loading="isClearing" @close="showClearConfirm = false"
        @confirm="confirmClearLogs" />
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import api from '@/utils/api'
import * as LucideIcons from 'lucide-vue-next'
import ConfirmationModal from '@/components/ConfirmationModal.vue'
import ScanHistoryTab from '@/components/ScanHistoryTab.vue'
const { RefreshCw, Search, Filter, ChevronDown, Activity, Trash2, Cog, ShieldCheck, Router, Network, Radar } = LucideIcons
import { useNotifications } from '@/composables/useNotifications'
import { useWebSockets } from '@/composables/useWebSockets'
import { formatDate } from '@/utils/date'

// PrimeVue components
import Select from 'primevue/select'
import InputText from 'primevue/inputtext'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import ToggleSwitch from 'primevue/toggleswitch'

const { notifySuccess, notifyError } = useNotifications()
const { lastNotification } = useWebSockets()

watch(lastNotification, (notif) => {
    if (notif && (
        currentTab.value === 'tasks' || 
        notif.level === 'ERROR' || 
        notif.level === 'WARNING' ||
        ['started', 'completed', 'failed'].includes(notif.event_type)
    )) {
        fetchLogs()
    }
})

const scanTabRef = ref<any>(null)

interface LogRecord {
    timestamp: string
    level: string
    message: string
    module: string
    funcName: string
    line: number
    path: string
    exception?: string
    // Task Event Fields
    task_type?: string
    event_type?: string
    target?: string
    duration_ms?: number
    details?: Record<string, any>
}

const logs = ref<LogRecord[]>([])
const loading = ref(false)
const limit = ref(20)
const page = ref(1)
const total = ref(0)
const totalPages = ref(1)
const search = ref('')
const levelFilter = ref('WARNING')
const taskTypeFilter = ref('')
const levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

const levelOptions = [
    { value: '', label: 'All Levels' },
    { value: 'DEBUG', label: 'DEBUG' },
    { value: 'INFO', label: 'INFO' },
    { value: 'WARNING', label: 'WARNING' },
    { value: 'ERROR', label: 'ERROR' },
    { value: 'CRITICAL', label: 'CRITICAL' }
]

const taskTypes = [
    { value: 'scan', label: 'Network Scan', icon: Network },
    { value: 'adguard_sync', label: 'AdGuard Sync', icon: ShieldCheck },
    { value: 'openwrt_sync', label: 'OpenWRT Sync', icon: Router },
]

const taskTypeOptions = [
    { value: '', label: 'All Types' },
    { value: 'scan', label: 'Network Scan' },
    { value: 'adguard_sync', label: 'AdGuard Sync' },
    { value: 'openwrt_sync', label: 'OpenWRT Sync' }
]

// Tab and Auto-refresh State
const currentTab = ref('all')
const autoRefresh = ref(false)
let autoRefreshInterval = null

// Confirmation Modal State
const showClearConfirm = ref(false)
const isClearing = ref(false)

const levelColors: Record<string, string> = {
    'INFO': 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
    'WARNING': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
    'ERROR': 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
    'CRITICAL': 'bg-red-200 text-red-900 dark:bg-red-900/50 dark:text-red-100 animate-pulse',
    'DEBUG': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
}

// Task Helper Functions
const getTaskColor = (type?: string) => {
    switch (type) {
        case 'scan': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300'
        case 'adguard_sync': return 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300'
        case 'openwrt_sync': return 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300'
        default: return 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300'
    }
}

const getTaskIcon = (type?: string) => {
    switch (type) {
        case 'scan': return Network
        case 'adguard_sync': return ShieldCheck
        case 'openwrt_sync': return Router
        default: return Activity
    }
}

const getTaskLabel = (type?: string) => {
    switch (type) {
        case 'scan': return 'Network Scan'
        case 'adguard_sync': return 'AdGuard Sync'
        case 'openwrt_sync': return 'OpenWRT Sync'
        default: return type || 'Unknown'
    }
}

const formatTime = (ts: string) => {
    return formatDate(ts)
}

let debounceTimer: any = null
const debounceSearch = () => {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
        page.value = 1
        fetchLogs()
    }, 400)
}

const changePage = (newPage: number) => {
    if (newPage < 1 || newPage > totalPages.value) return
    page.value = newPage
    fetchLogs()
    window.scrollTo({ top: 0, behavior: 'smooth' })
}

const fetchLogs = async () => {
    if (currentTab.value === 'scans') return
    loading.value = true
    try {
        const endpoint = currentTab.value === 'tasks' ? '/task-events/' : '/logs/'
        const params: any = {
            limit: limit.value,
            page: page.value
        }

        if (currentTab.value === 'all') {
            if (search.value) params.search = search.value
            if (levelFilter.value) params.level = levelFilter.value
        } else {
            // Task filtering
            if (taskTypeFilter.value) params.task_type = taskTypeFilter.value
        }

        const res = await api.get(endpoint, { params })

        logs.value = res.data.items
        total.value = res.data.total
        totalPages.value = res.data.total_pages
        page.value = res.data.page
    } catch (e) {
        notifyError('Failed to fetch logs')
        console.error('Error fetching logs:', e)
    } finally {
        loading.value = false
    }
}

const promptClearLogs = () => {
    showClearConfirm.value = true
}

const confirmClearLogs = async () => {
    isClearing.value = true
    try {
        await api.delete('/logs/')
        notifySuccess('All logs cleared successfully')
        logs.value = []
        total.value = 0
        totalPages.value = 1
        page.value = 1
        showClearConfirm.value = false
        // Refresh to ensure empty state
        await fetchLogs()
    } catch (e) {
        notifyError('Failed to clear logs')
        console.error('Error clearing logs:', e)
    } finally {
        isClearing.value = false
    }
}

onMounted(() => {
    fetchLogs()
})

// Computed property for filtered logs based on current tab
// Since API handles filtering, we just return logs
const displayedLogs = computed(() => logs.value)

const displayTotal = computed(() => total.value)

// Auto-refresh watcher
watch(autoRefresh, (enabled) => {
    if (enabled) {
        // Start auto-refresh
        autoRefreshInterval = setInterval(() => {
            if (currentTab.value === 'tasks') {
                fetchLogs()
            }
        }, 5000)
    } else {
        // Stop auto-refresh
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval)
            autoRefreshInterval = null
        }
    }
})

// Stop auto-refresh when switching away from tasks tab
watch(currentTab, (newTab, oldTab) => {
    if (newTab !== 'tasks' && autoRefresh.value) {
        autoRefresh.value = false
    }

    if (newTab === 'scans') return

    // Reset page and filters when switching tabs
    page.value = 1
    if (newTab === 'tasks') {
        taskTypeFilter.value = ''
    } else {
        levelFilter.value = 'WARNING'
    }

    fetchLogs()
})
</script>
