<template>
    <v-app-bar :elevation="0" class="bg-white/80 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 transition-all px-4" height="64">
        <!-- Left: Branding & Mobile Trigger -->
        <div class="flex items-center gap-2">
            <div class="flex items-center gap-2 md:hidden">
                <v-btn icon variant="text" size="small" @click="$emit('toggle-mobile-menu')" class="text-slate-700 dark:text-slate-300">
                    <MenuIcon class="h-6 w-6" />
                </v-btn>
            </div>
            <AppLogo class="scale-100 origin-left" />
            <div class="hidden lg:block h-6 w-px bg-slate-200 dark:bg-slate-700 mx-4"></div>
        </div>

        <v-spacer class="hidden md:block"></v-spacer>

        <!-- Center: Search Bar -->
        <div class="flex-grow-1 max-w-lg w-full md:w-96 px-2">
            <TopBarSearch />
        </div>

        <v-spacer></v-spacer>

        <!-- Right: Actions -->
        <div class="flex items-center gap-3">
            <!-- Integrations Status -->
            <div class="hidden lg:flex items-center gap-1 p-1 bg-slate-50/60 dark:bg-slate-800/40 rounded-lg border border-slate-200/50 dark:border-slate-700/30">
                <div v-for="integration in ['mqtt', 'openwrt', 'adguard', 'deco']" :key="integration" 
                    @click="router.push('/settings')"
                    class="group relative flex items-center h-8 w-8 justify-center cursor-pointer hover:bg-white dark:hover:bg-slate-700 rounded-md transition-all shadow-sm shadow-transparent hover:shadow-slate-200/50">
                    <component :is="integration === 'mqtt' ? Share2Icon : (integration === 'openwrt' ? RouterIcon : (integration === 'deco' ? Wifi : ShieldCheckIcon))" 
                        class="h-4 w-4 transition-colors" 
                        :class="getIntegrationStatus(integration) ? getIntegrationColor(integration) : 'text-slate-400'" />
                    <div v-if="getIntegrationStatus(integration)" 
                        class="absolute top-1 right-1 h-2 w-2 rounded-full border-2 border-white dark:border-slate-800"
                        :class="getIntegrationPulse(integration)"></div>
                    
                    <v-tooltip activator="parent" location="bottom" content-class="!px-2 !py-1 !text-[10px] !min-h-0">
                        <div class="flex flex-col gap-0.5">
                            <div class="flex items-center gap-1.5 font-bold">
                                <span class="w-1.5 h-1.5 rounded-full" :class="getIntegrationStatus(integration) ? 'bg-emerald-500' : 'bg-red-500'"></span>
                                <span>{{ integration.toUpperCase() }}: {{ getIntegrationStatus(integration) ? 'Active' : 'Offline' }}</span>
                            </div>
                            <span class="text-slate-400 italic text-[9px]">Manage in Settings</span>
                        </div>
                    </v-tooltip>
                </div>
            </div>

            <!-- System Hub: Live & Notifications -->
            <div class="flex items-center gap-1 p-1 bg-slate-50/60 dark:bg-slate-800/40 rounded-lg border border-slate-200/50 dark:border-slate-700/30">
                <!-- New Devices Alert -->
                <v-menu location="bottom end" transition="scale-transition" offset="8" :close-on-content-click="false" v-model="showNewDevices">
                    <template v-slot:activator="{ props }">
                        <button v-bind="props" @click="deviceStore.fetchNewDevices"
                            class="group relative flex items-center h-8 w-8 justify-center cursor-pointer hover:bg-white dark:hover:bg-slate-700 rounded-md transition-all shadow-sm shadow-transparent hover:shadow-slate-200/50">
                            <Radar class="w-4 h-4 transition-colors" :class="hasNewDevices ? 'text-emerald-500 animate-pulse' : 'text-slate-400 dark:text-slate-500'" />
                            <span v-if="hasNewDevices" class="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-emerald-500 text-[8px] font-black text-white border border-white dark:border-slate-800">
                                {{ deviceStore.stats.new_24h }}
                            </span>
                            <v-tooltip activator="parent" location="bottom" content-class="!px-2 !py-1 !text-[10px] !min-h-0">
                                <span>Discovered Devices</span>
                            </v-tooltip>
                        </button>
                    </template>

                    <!-- New Devices Popover -->
                    <v-card class="w-72 rounded-xl shadow-2xl overflow-hidden border border-slate-200 dark:border-slate-700 bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl">
                        <div class="px-4 py-3 border-b border-slate-100 dark:border-slate-700/50 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/30">
                            <h3 class="text-[10px] font-black uppercase tracking-widest text-slate-900 dark:text-white">Newly Discovered</h3>
                            <button @click="dismissNewDevices" class="text-[9px] font-bold text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors">Dismiss</button>
                        </div>
                        <div class="max-h-80 overflow-y-auto custom-scrollbar">
                            <div v-if="deviceStore.newDevices.length === 0" class="p-8 text-center text-slate-500 text-[10px] font-medium">Loading devices...</div>
                            <button v-for="device in deviceStore.newDevices" :key="device.id" @click="goToDevice(device)" 
                                class="w-full flex items-center gap-3 px-4 py-3 hover:bg-blue-50 dark:hover:bg-blue-900/10 transition-colors text-left border-b border-slate-50 dark:border-slate-700/30 last:border-0 group/new">
                                <div class="p-2 bg-slate-100 dark:bg-slate-700 rounded-lg group-hover/new:bg-blue-100 dark:group-hover/new:bg-blue-900/30 transition-colors">
                                    <component :is="getIcon(device.icon || 'help-circle')" class="h-4 w-4 text-slate-600 dark:text-slate-400 group-hover/new:text-blue-500" />
                                </div>
                                <div class="flex-1 min-w-0">
                                    <div class="text-xs font-bold text-slate-900 dark:text-white truncate">{{ device.display_name || device.name }}</div>
                                    <div class="text-[10px] text-slate-500 font-mono">{{ device.ip }}</div>
                                </div>
                                <ChevronRightIcon class="h-3 w-3 text-slate-300 group-hover/new:text-blue-500 transition-colors" />
                            </button>
                        </div>
                        <div class="p-2 border-t border-slate-100 dark:border-slate-700/50">
                            <router-link to="/devices" @click="showNewDevices = false" class="w-full py-2 px-4 text-[10px] font-black uppercase tracking-widest text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-500/10 rounded-xl transition-all flex items-center justify-between">
                                <span>Manage all devices</span>
                                <ArrowRightIcon class="h-3 w-3" />
                            </router-link>
                        </div>
                    </v-card>
                </v-menu>

                <!-- Connection Status -->
                <div class="flex items-center h-8 w-8 justify-center rounded-md transition-all relative">
                    <Zap class="w-4 h-4" :class="ws.connected.value ? 'text-emerald-500 animate-pulse' : 'text-rose-500'" />
                    <v-tooltip activator="parent" location="bottom" content-class="!px-2 !py-1 !text-[10px] !min-h-0">
                        <span>System Status: {{ ws.connected.value ? 'Live' : 'Offline' }}</span>
                    </v-tooltip>
                </div>

                <div class="w-px h-4 bg-slate-200 dark:bg-slate-700 mx-0.5 hidden sm:block"></div>

                <v-menu location="bottom end" transition="scale-transition" offset="8" :close-on-content-click="false" v-model="showNotifications" @update:modelValue="onNotificationsToggle">
                    <template v-slot:activator="{ props }">
                        <button v-bind="props"
                            class="group relative flex items-center h-8 w-8 justify-center cursor-pointer hover:bg-white dark:hover:bg-slate-700 rounded-md transition-all shadow-sm shadow-transparent hover:shadow-slate-200/50">
                            <BellIcon class="h-4 w-4 text-slate-500 dark:text-slate-400" />
                            <span v-if="notificationStore.unreadCount > 0" class="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-blue-500 text-[8px] font-black text-white border border-white dark:border-slate-800">
                                {{ notificationStore.unreadCount }}
                            </span>
                            <v-tooltip activator="parent" location="bottom" content-class="!px-2 !py-1 !text-[10px] !min-h-0">
                                <span>System Activity</span>
                            </v-tooltip>
                        </button>
                    </template>

                    <v-card class="w-80 rounded-xl shadow-2xl overflow-hidden border border-slate-200 dark:border-slate-700 bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl">
                        <div class="px-4 py-3 border-b border-slate-100 dark:border-slate-700/50 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/30">
                            <h3 class="text-xs font-black uppercase tracking-widest text-slate-900 dark:text-white">Recent Activity</h3>
                            <button @click="markAllAsRead" class="text-[10px] font-bold text-blue-600 dark:text-blue-400 hover:underline">Clear all</button>
                        </div>
                        <div class="max-h-96 overflow-y-auto custom-scrollbar">
                            <div v-if="notificationStore.events.length === 0" class="p-10 text-center text-slate-500 text-[10px] font-medium">All caught up!</div>
                            <button v-for="event in notificationStore.events" :key="event.id" @click="goToEvent(event)" class="notif-item group/notif">
                                <div v-if="!event.read_at" class="notif-indicator"></div>
                                <div class="p-2 rounded-xl" :class="getEventColor(event.level)"><component :is="getEventIcon(event)" class="h-4 w-4" /></div>
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center justify-between gap-2">
                                        <span class="text-[10px] font-black uppercase tracking-tighter text-slate-400">{{ event.task_type?.replace('_', ' ') || 'System' }}</span>
                                        <span class="text-[9px] text-slate-400">{{ formatRelativeTime(parseUTC(event.created_at)) }}</span>
                                    </div>
                                    <p class="text-xs font-medium text-slate-900 dark:text-slate-100 line-clamp-2 mt-0.5 leading-snug">{{ event.message }}</p>
                                </div>
                            </button>
                        </div>
                        <div class="p-2 border-t border-slate-100 dark:border-slate-700/50">
                            <router-link to="/logs" @click="showNotifications = false" class="w-full py-2 px-4 text-[10px] font-black uppercase tracking-widest text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-500/10 rounded-xl transition-all flex items-center justify-between">
                                <span>View all events</span>
                                <ArrowRightIcon class="h-3 w-3" />
                            </router-link>
                        </div>
                    </v-card>
                </v-menu>
            </div>

            <!-- Theme Toggle -->
            <div class="flex items-center p-1 bg-slate-50/60 dark:bg-slate-800/40 rounded-lg border border-slate-200/50 dark:border-slate-700/30">
                <button @click="toggleTheme"
                    class="group relative flex items-center h-8 w-8 justify-center cursor-pointer hover:bg-white dark:hover:bg-slate-700 rounded-md transition-all text-slate-500 dark:text-slate-400">
                    <SunIcon v-if="theme.global.current.value.dark" class="h-4 w-4" />
                    <MoonIcon v-else class="h-4 w-4" />
                    <v-tooltip activator="parent" location="bottom" content-class="!px-2 !py-1 !text-[10px] !min-h-0">
                        <span>{{ theme.global.current.value.dark ? 'Light Mode' : 'Dark Mode' }}</span>
                    </v-tooltip>
                </button>
            </div>

            <!-- User Profile -->
            <div class="flex items-center p-1 bg-slate-50/60 dark:bg-slate-800/40 rounded-lg border border-slate-200/50 dark:border-slate-700/30">
                <v-menu location="bottom end" transition="scale-transition" offset="8" :close-on-content-click="false" v-model="showUserMenu">
                    <template v-slot:activator="{ props }">
                        <button v-bind="props"
                            class="flex items-center gap-2 h-8 pl-1 pr-2.5 hover:bg-white dark:hover:bg-slate-700 rounded-md transition-all relative group shadow-sm shadow-transparent hover:shadow-slate-200/50">
                            <div class="w-6 h-6 rounded-md bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white text-[10px] font-bold transition-transform">
                                {{ authStore.user?.username?.charAt(0).toUpperCase() || 'U' }}
                            </div>
                            <span class="hidden sm:block text-[11px] font-bold text-slate-700 dark:text-slate-300">{{ authStore.user?.username || 'User' }}</span>
                            <ChevronDownIcon class="h-3 w-3 text-slate-400 transition-transform duration-200" :class="showUserMenu ? 'rotate-180' : ''" />
                            <v-tooltip activator="parent" location="bottom" content-class="!px-2 !py-1 !text-[10px] !min-h-0">
                                <span>User Account</span>
                            </v-tooltip>
                        </button>
                    </template>
                    <v-card class="w-56 rounded-xl shadow-2xl overflow-hidden border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
                        <div class="px-4 py-4 bg-slate-50 dark:bg-slate-800/30 border-b border-slate-100 dark:border-slate-700/50">
                            <p class="text-xs font-black uppercase tracking-tight text-slate-900 dark:text-white">{{ authStore.user?.full_name || authStore.user?.username }}</p>
                            <p class="text-[10px] text-slate-500 truncate mt-0.5">System Administrator</p>
                        </div>
                        <div class="p-1.5">
                            <router-link to="/settings" @click="showUserMenu = false" class="user-menu-item rounded-lg">
                                <UserIcon class="h-4 w-4" />
                                <span>Profile Settings</span>
                            </router-link>
                            <button @click="handleLogout" class="user-menu-item rounded-lg text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 w-full text-left mt-1">
                                <LogOutIcon class="h-4 w-4" />
                                <span>Sign Out</span>
                            </button>
                        </div>
                    </v-card>
                </v-menu>
            </div>
        </div>
    </v-app-bar>
</template>

<script setup>
import {
    Bell as BellIcon,
    Menu as MenuIcon,
    ArrowRight as ArrowRightIcon,
    HelpCircle,
    Smartphone,
    Tablet,
    Laptop,
    Monitor,
    Server,
    Router,
    Network,
    Wifi,
    WifiOff,
    User as UserIcon,
    LogOut as LogOutIcon,
    ChevronDown as ChevronDownIcon,
    Tv,
    Printer,
    Activity,
    CheckCircle,
    AlertTriangle,
    ShieldAlert,
    ScanSearch,
    Zap,
    Share2 as Share2Icon,
    Router as RouterIcon,
    ShieldCheck as ShieldCheckIcon,
    ChevronRight as ChevronRightIcon,
    Radar,
    Sun as SunIcon,
    Moon as MoonIcon
} from 'lucide-vue-next'
import { useNotifications } from '@/composables/useNotifications'
import { ref, onMounted, watch, computed } from 'vue'
import { useTheme } from 'vuetify'
import AppLogo from './AppLogo.vue'
import TopBarSearch from './TopBarSearch.vue'
import { useNotificationStore } from '@/stores/notifications'
import { useIntegrationStore } from '@/stores/integrations'
import { useAuthStore } from '@/stores/authStore'
import { useDeviceStore } from '@/stores/devices'
import { useRouter } from 'vue-router'
import { formatRelativeTime, parseUTC } from '@/utils/date'
import { useWebSockets } from '@/composables/useWebSockets'

defineEmits(['toggle-mobile-menu'])

const notificationStore = useNotificationStore()
const integrationStore = useIntegrationStore()
const authStore = useAuthStore()
const deviceStore = useDeviceStore()
const router = useRouter()
const ws = useWebSockets()

const showNotifications = ref(false)
const showUserMenu = ref(false)
const showNewDevices = ref(false)

// Last seen timestamp for "New" badge dismissal
const lastDismissed = ref(localStorage.getItem('new_devices_last_dismissed') || '0')

const hasNewDevices = computed(() => {
    if (deviceStore.stats.new_24h <= 0) return false
    // If we have new devices in 24h, we check if they were already dismissed
    // For simplicity, if new_24h > 0 and user hasn't dismissed in last hour, show it
    // Or more precisely: if we have new ones, show it. Dismissing just hides it until next one.
    return lastDismissed.value !== 'all_seen'
})

const toggleNewDevices = () => {
    showNewDevices.value = !showNewDevices.value
    if (showNewDevices.value) {
        showNotifications.value = false
        showUserMenu.value = false
        deviceStore.fetchNewDevices()
    }
}

const dismissNewDevices = () => {
    showNewDevices.value = false
    lastDismissed.value = 'all_seen'
    localStorage.setItem('new_devices_last_dismissed', 'all_seen')
}

watch(ws.lastNotification, (notif) => {
    if (notif && notif.event_type === 'new_device') {
        deviceStore.fetchStats()
        // Reset dismissal if a literal new device event arrives
        lastDismissed.value = 'new_event'
        localStorage.removeItem('new_devices_last_dismissed')
    }
})

const theme = useTheme()

const toggleTheme = () => {
    const nextTheme = theme.global.current.value.dark ? 'light' : 'dark'
    theme.global.name.value = nextTheme
    localStorage.setItem('theme', nextTheme)
    
    // Sync with Tailwind dark mode
    if (nextTheme === 'dark') {
        document.documentElement.classList.add('dark')
    } else {
        document.documentElement.classList.remove('dark')
    }
}

onMounted(() => {
    const savedTheme = localStorage.getItem('theme') || 'light'
    theme.global.name.value = savedTheme
    if (savedTheme === 'dark') {
        document.documentElement.classList.add('dark')
    } else {
        document.documentElement.classList.remove('dark')
    }

    notificationStore.fetchNotifications(true)
    notificationStore.fetchUnreadCount()
    integrationStore.fetchStatuses()
    deviceStore.fetchStats()
})


const getIntegrationStatus = (key) => {
    if (key === 'mqtt') return integrationStore.mqttStatus.reachable
    if (key === 'openwrt') return integrationStore.openwrtStatus.verified
    if (key === 'adguard') return integrationStore.adguardStatus.verified
    if (key === 'deco') return integrationStore.decoStatus.verified
    return false
}

const getIntegrationColor = (key) => {
    if (key === 'mqtt') return 'text-emerald-500'
    if (key === 'openwrt') return 'text-blue-500'
    if (key === 'adguard') return 'text-indigo-500'
    if (key === 'deco') return 'text-teal-500'
    return 'text-slate-400'
}

const getIntegrationPulse = (key) => {
    const base = 'absolute top-1.5 right-1.5 h-2 w-2 rounded-full border-2 border-white dark:border-slate-800 shadow-sm'
    if (key === 'mqtt') return `${base} bg-emerald-500 animate-pulse`
    if (key === 'openwrt') return `${base} bg-blue-500`
    if (key === 'adguard') return `${base} bg-indigo-500`
    if (key === 'deco') return `${base} bg-teal-500`
    return base
}

const getEventIcon = (event) => {
    if (event.level === 'ERROR' || event.event_type === 'failed') return AlertTriangle
    if (event.level === 'WARNING') return AlertTriangle
    if (event.task_type === 'audit') return ScanSearch
    if (event.event_type === 'completed') return CheckCircle
    if (event.event_type === 'security_alert') return ShieldAlert
    if (event.type === 'device') return event.event_type === 'status_changed' && event.message.includes('online') ? Wifi : WifiOff
    return Activity
}

const getEventColor = (level) => {
    if (level === 'ERROR') return 'bg-red-500/10 text-red-500'
    if (level === 'WARNING') return 'bg-amber-500/10 text-amber-500'
    return 'bg-blue-500/10 text-blue-500'
}

const onNotificationsToggle = (isOpen) => {
    if (isOpen) {
        showUserMenu.value = false
        notificationStore.fetchNotifications(true)
        notificationStore.fetchUnreadCount()
    }
}

const handleLogout = () => {
    authStore.logout()
    router.push('/login')
}

const markAllAsRead = async () => {
    await notificationStore.markAllAsRead()
    const { notifySuccess } = useNotifications()
    notifySuccess('All notifications marked as read')
}

const goToEvent = async (event) => {
    showNotifications.value = false
    if (!event.read_at) {
        try {
            await notificationStore.markAsRead([event.id])
        } catch (error) {
            console.error('Failed to mark notification as read:', error)
        }
    }
    const deviceId = event.type === 'device' ? (event.target || event.details?.id) : null
    if (deviceId && deviceId.length > 10) {
        router.push({ name: 'DeviceDetails', params: { id: deviceId } })
    } else if (event.task_type === 'scan') {
        router.push('/logs')
    } else if (event.task_type === 'adguard_sync' || event.task_type === 'openwrt_sync') {
        router.push('/analytics')
    }
}

const goToDevice = (device) => {
    showNewDevices.value = false
    router.push({ name: 'DeviceDetails', params: { id: device.id } })
}

const getIcon = (name) => {
    const iconMap = {
        'smartphone': Smartphone,
        'tablet': Tablet,
        'laptop': Laptop,
        'monitor': Monitor,
        'server': Server,
        'router': Router,
        'network': Network,
        'tv': Tv,
        'printer': Printer,
        'help-circle': HelpCircle
    }
    const key = name.toLowerCase().replace('device-', '')
    return iconMap[key] || HelpCircle
}
</script>
