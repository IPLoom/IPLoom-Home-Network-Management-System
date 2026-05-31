<template>
    <v-app-bar :elevation="0" class="border-b" height="64" style="background-color: rgb(var(--color-surface-elevated) / 80%) !important; backdrop-filter: blur(12px);">
        <div class="d-flex align-center w-100 px-4 justify-space-between">
            <!-- Left: Branding & Mobile Trigger -->
            <div class="d-flex align-center">
                <v-btn class="d-md-none mr-2" icon variant="text" size="small" @click="$emit('toggle-mobile-menu')">
                    <MenuIcon style="height: 24px; width: 24px;" />
                </v-btn>
                <AppLogo style="transform: scale(1); transform-origin: left;" />
                <v-divider vertical class="mx-4 d-none d-lg-block"></v-divider>
            </div>

            <v-spacer class="hidden-sm-and-down"></v-spacer>

            <!-- Center: Search Bar -->
            <div class="flex-grow-1 px-2 d-none d-md-block" style="max-width: 32rem;">
                <TopBarSearch />
            </div>

            <v-spacer></v-spacer>

            <!-- Right: Actions -->
            <div class="d-flex align-center" style="gap: 12px;">
                <!-- Integrations Status -->
                <div class="d-none d-lg-flex align-center pa-1 rounded-lg border bg-surface" style="gap: 4px;">
                    <v-btn
                        v-for="integration in ['mqtt', 'openwrt', 'adguard', 'deco']"
                        :key="integration"
                        icon
                        size="small"
                        variant="text"
                        @click="router.push('/settings')"
                    >
                        <v-badge
                            :model-value="getIntegrationStatus(integration)"
                            dot
                            :color="getIntegrationColorValue(integration)"
                        >
                            <component
                                :is="integration === 'mqtt' ? Share2Icon : (integration === 'openwrt' ? RouterIcon : (integration === 'deco' ? Wifi : ShieldCheckIcon))"
                                style="height: 16px; width: 16px; transition: color 0.2s;"
                                :style="{ color: getIntegrationStatus(integration) ? getIntegrationColorValue(integration) : 'rgb(var(--color-text-tertiary))' }"
                            />
                        </v-badge>
                        <v-tooltip activator="parent" location="bottom">
                            <span class="text-caption font-weight-bold text-uppercase">{{ integration }}: {{ getIntegrationStatus(integration) ? 'Active' : 'Offline' }}</span>
                        </v-tooltip>
                    </v-btn>
                </div>

                <!-- System Hub -->
                <div class="d-flex align-center pa-1 rounded-lg border bg-surface" style="gap: 4px;">
                    <!-- New Devices Alert -->
                    <v-menu location="bottom end" transition="scale-transition" offset="8" :close-on-content-click="false" v-model="showNewDevices">
                        <template v-slot:activator="{ props }">
                            <v-btn icon size="small" variant="text" v-bind="props" @click="deviceStore.fetchNewDevices">
                                <v-badge
                                    :model-value="hasNewDevices"
                                    :content="deviceStore.stats.new_24h"
                                    color="success"
                                >
                                    <Radar style="width: 16px; height: 16px; transition: color 0.2s;" :style="{ color: hasNewDevices ? '#10b981' : 'rgb(var(--color-text-secondary))' }" />
                                </v-badge>
                                <v-tooltip activator="parent" location="bottom"><span class="text-caption">Discovered Devices</span></v-tooltip>
                            </v-btn>
                        </template>

                        <!-- Popover -->
                        <v-card width="340" rounded="lg" elevation="8">
                            <v-card-title class="d-flex align-center justify-space-between text-caption font-weight-bold text-uppercase py-3 px-4 border-b">
                                Newly Discovered
                                <v-btn variant="text" size="small" class="text-none text-medium-emphasis" @click="dismissNewDevices">Dismiss</v-btn>
                            </v-card-title>
                            <v-list class="overflow-hidden pa-0" lines="two" density="compact">
                                <v-list-item v-if="deviceStore.newDevices.length === 0" class="text-center text-caption text-medium-emphasis py-4">Loading devices...</v-list-item>
                                <v-list-item
                                    v-for="device in deviceStore.newDevices.slice(0, 3)"
                                    :key="device.id"
                                    @click="goToDevice(device)"
                                    class="border-b"
                                    density="compact"
                                >
                                    <template v-slot:prepend>
                                        <v-avatar color="grey" variant="tonal" rounded size="32" class="mr-3">
                                            <component :is="getIcon(device.icon || 'help-circle')" style="width: 16px; height: 16px;" />
                                        </v-avatar>
                                    </template>
                                    <v-list-item-title class="text-body-2 font-weight-bold">{{ device.display_name || device.name }}</v-list-item-title>
                                    <v-list-item-subtitle class="text-caption font-family-mono" style="font-size: 11px;">{{ device.ip }}</v-list-item-subtitle>
                                    <template v-slot:append>
                                        <ChevronRightIcon style="width: 14px; height: 14px; color: rgb(var(--color-text-tertiary));" />
                                    </template>
                                </v-list-item>
                            </v-list>
                            <div class="pa-2 bg-surface-variant opacity-80">
                                <v-btn block color="primary" variant="tonal" class="text-none d-flex justify-space-between px-4" @click="showNewDevices = false; router.push('/devices')">
                                    Manage all devices <ArrowRightIcon style="width: 16px; height: 16px;" />
                                </v-btn>
                            </div>
                        </v-card>
                    </v-menu>

                    <!-- Connection Status -->
                    <v-btn icon size="small" variant="text">
                        <Zap style="width: 16px; height: 16px;" :style="{ color: ws.connected.value ? '#10b981' : '#ef4444' }" />
                        <v-tooltip activator="parent" location="bottom"><span class="text-caption">System Status: {{ ws.connected.value ? 'Live' : 'Offline' }}</span></v-tooltip>
                    </v-btn>
                    
                    <v-divider vertical class="mx-1 my-2" style="height: 16px;"></v-divider>

                    <!-- Notifications -->
                    <v-menu location="bottom end" transition="scale-transition" offset="8" :close-on-content-click="false" v-model="showNotifications" @update:modelValue="onNotificationsToggle">
                        <template v-slot:activator="{ props }">
                            <v-btn icon size="small" variant="text" v-bind="props">
                                <v-badge
                                    :model-value="notificationStore.unreadCount > 0"
                                    :content="notificationStore.unreadCount"
                                    color="primary"
                                >
                                    <BellIcon style="height: 16px; width: 16px; color: rgb(var(--color-text-secondary));" />
                                </v-badge>
                                <v-tooltip activator="parent" location="bottom"><span class="text-caption">System Activity</span></v-tooltip>
                            </v-btn>
                        </template>

                        <v-card width="380" rounded="lg" elevation="8">
                            <v-card-title class="d-flex align-center justify-space-between text-caption font-weight-bold text-uppercase py-3 px-4 border-b">
                                System Activity
                                <v-btn variant="text" size="small" class="text-none" color="primary" @click="markAllAsRead">Clear all</v-btn>
                            </v-card-title>
                            <v-list class="overflow-hidden pa-0" density="compact">
                                <v-list-item v-if="notificationStore.events.length === 0" class="text-center text-caption text-medium-emphasis py-4">All caught up!</v-list-item>
                                <v-list-item
                                    v-for="event in notificationStore.events.slice(0, 4)"
                                    :key="event.id"
                                    @click="goToEvent(event)"
                                    class="border-b"
                                    :active="!event.read_at"
                                    color="primary"
                                    active-class="bg-blue-lighten-5 dark:bg-blue-darken-4"
                                    density="compact"
                                >
                                    <template v-slot:prepend>
                                        <v-badge :model-value="!event.read_at" dot color="primary" class="mr-3">
                                            <v-avatar size="28" :color="getEventColor(event.level)" variant="tonal">
                                                <component :is="getEventIcon(event)" style="height: 14px; width: 14px;" />
                                            </v-avatar>
                                        </v-badge>
                                    </template>
                                    <div class="d-flex justify-space-between align-center mb-1">
                                        <span class="text-caption font-weight-bold text-uppercase text-medium-emphasis" :class="{ 'text-primary': !event.read_at }">{{ event.task_type?.replace('_', ' ') || 'System' }}</span>
                                        <span class="text-caption text-medium-emphasis" style="font-size: 10px;">{{ formatRelativeTime(parseUTC(event.created_at)) }}</span>
                                    </div>
                                    <div class="text-body-2" style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.4;">{{ event.message }}</div>
                                </v-list-item>
                            </v-list>
                            <div class="pa-2 bg-surface-variant opacity-80">
                                <v-btn block color="primary" variant="tonal" class="text-none d-flex justify-space-between px-4" @click="showNotifications = false; router.push('/logs')">
                                    View all events <ArrowRightIcon style="width: 16px; height: 16px;" />
                                </v-btn>
                            </div>
                        </v-card>
                    </v-menu>
                </div>

                <!-- Theme Toggle -->
                <div class="d-flex align-center pa-1 rounded-lg border bg-surface">
                    <v-btn icon size="small" variant="text" @click="toggleTheme">
                        <SunIcon v-if="theme.global.current.value.dark" style="height: 16px; width: 16px;" />
                        <MoonIcon v-else style="height: 16px; width: 16px;" />
                        <v-tooltip activator="parent" location="bottom"><span class="text-caption">{{ theme.global.current.value.dark ? 'Light Mode' : 'Dark Mode' }}</span></v-tooltip>
                    </v-btn>
                </div>

                <!-- User Profile -->
                <div class="d-flex align-center pa-1 rounded-lg border bg-surface">
                    <v-menu location="bottom end" transition="scale-transition" offset="8" :close-on-content-click="false" v-model="showUserMenu">
                        <template v-slot:activator="{ props }">
                            <v-btn variant="text" class="px-2" height="32" v-bind="props">
                                <v-avatar size="24" color="primary" class="mr-2 text-caption font-weight-bold">
                                    {{ authStore.user?.username?.charAt(0).toUpperCase() || 'U' }}
                                </v-avatar>
                                <span class="text-caption font-weight-bold d-none d-sm-block">{{ authStore.user?.username || 'User' }}</span>
                                <ChevronDownIcon style="height: 14px; width: 14px; margin-left: 4px;" class="text-medium-emphasis" />
                            </v-btn>
                        </template>
                        <v-card width="224" rounded="lg" elevation="4">
                            <div class="pa-4 border-b bg-surface-variant">
                                <p class="text-overline font-weight-black mb-0">{{ authStore.user?.full_name || authStore.user?.username }}</p>
                                <p class="text-caption text-medium-emphasis mb-0">System Administrator</p>
                            </div>
                            <v-list density="compact" class="pa-2">
                                <v-list-item rounded="lg" @click="showUserMenu = false; router.push('/settings')">
                                    <template v-slot:prepend><UserIcon style="height: 16px; width: 16px; margin-right: 12px;" /></template>
                                    <v-list-item-title class="text-body-2">Profile Settings</v-list-item-title>
                                </v-list-item>
                                <v-list-item rounded="lg" color="error" class="text-error mt-1" @click="handleLogout">
                                    <template v-slot:prepend><LogOutIcon style="height: 16px; width: 16px; margin-right: 12px;" /></template>
                                    <v-list-item-title class="text-body-2">Sign Out</v-list-item-title>
                                </v-list-item>
                            </v-list>
                        </v-card>
                    </v-menu>
                </div>
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
        lastDismissed.value = 'new_event'
        localStorage.removeItem('new_devices_last_dismissed')
    }
})

const theme = useTheme()

const toggleTheme = () => {
    const nextTheme = theme.global.current.value.dark ? 'light' : 'dark'
    if (theme.change) {
        theme.change(nextTheme)
    } else {
        theme.global.name.value = nextTheme
    }
    localStorage.setItem('theme', nextTheme)
    
    // Sync with Tailwind dark mode if class exists, otherwise document
    if (nextTheme === 'dark') {
        document.documentElement.classList.add('dark')
    } else {
        document.documentElement.classList.remove('dark')
    }
}

onMounted(() => {
    const savedTheme = localStorage.getItem('theme') || 'light'
    if (theme.change) {
        theme.change(savedTheme)
    } else {
        theme.global.name.value = savedTheme
    }
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

const getIntegrationColorValue = (key) => {
    if (key === 'mqtt') return '#10b981' // emerald-500
    if (key === 'openwrt') return '#3b82f6' // blue-500
    if (key === 'adguard') return '#6366f1' // indigo-500
    if (key === 'deco') return '#14b8a6' // teal-500
    return '#94a3b8'
}

const getIntegrationPulse = (key) => {
    return key === 'mqtt'
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
    if (level === 'ERROR') return 'error'
    if (level === 'WARNING') return 'warning'
    return 'primary'
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

<style scoped>
/* Vuetify handles spacing, flex, borders, badges and popovers natively now */
</style>
