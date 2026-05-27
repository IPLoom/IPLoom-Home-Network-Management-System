<template>
    <v-app-bar :elevation="0" class="border-b" height="64" style="background-color: rgb(var(--color-surface-elevated) / 80%) !important; backdrop-filter: blur(12px);">
        <div class="top-bar-container">
            <!-- Left: Branding & Mobile Trigger -->
            <div class="brand-section">
                <div class="mobile-trigger">
                    <v-btn icon variant="text" size="small" @click="$emit('toggle-mobile-menu')" style="color: rgb(var(--color-text-primary));">
                        <MenuIcon style="height: 24px; width: 24px;" />
                    </v-btn>
                </div>
                <AppLogo style="transform: scale(1); transform-origin: left;" />
                <div class="divider"></div>
            </div>

            <v-spacer class="hidden-sm-and-down"></v-spacer>

            <!-- Center: Search Bar -->
            <div class="search-section">
                <TopBarSearch />
            </div>

            <v-spacer></v-spacer>

            <!-- Right: Actions -->
            <div class="actions-section">
                <!-- Integrations Status -->
                <div class="status-panel integrations">
                    <div v-for="integration in ['mqtt', 'openwrt', 'adguard', 'deco']" :key="integration" 
                        @click="router.push('/settings')"
                        class="status-btn">
                        <component :is="integration === 'mqtt' ? Share2Icon : (integration === 'openwrt' ? RouterIcon : (integration === 'deco' ? Wifi : ShieldCheckIcon))" 
                            style="height: 16px; width: 16px; transition: color 0.2s;" 
                            :style="{ color: getIntegrationStatus(integration) ? getIntegrationColorValue(integration) : 'rgb(var(--color-text-tertiary))' }" />
                        <div v-if="getIntegrationStatus(integration)" 
                            class="status-indicator-dot"
                            :style="{ backgroundColor: getIntegrationColorValue(integration) }"
                            :class="{ 'pulse-animation': getIntegrationPulse(integration) }"></div>
                        
                        <v-tooltip activator="parent" location="bottom" content-class="!px-2 !py-1 !text-[10px] !min-h-0">
                            <div style="display: flex; flex-direction: column; gap: 2px;">
                                <div style="display: flex; align-items: center; gap: 6px; font-weight: bold;">
                                    <span style="width: 6px; height: 6px; border-radius: 50%;" :style="{ backgroundColor: getIntegrationStatus(integration) ? '#10b981' : '#ef4444' }"></span>
                                    <span>{{ integration.toUpperCase() }}: {{ getIntegrationStatus(integration) ? 'Active' : 'Offline' }}</span>
                                </div>
                                <span style="color: #94a3b8; font-style: italic; font-size: 9px;">Manage in Settings</span>
                            </div>
                        </v-tooltip>
                    </div>
                </div>

                <!-- System Hub: Live & Notifications -->
                <div class="status-panel">
                    <!-- New Devices Alert -->
                    <v-menu location="bottom end" transition="scale-transition" offset="8" :close-on-content-click="false" v-model="showNewDevices">
                        <template v-slot:activator="{ props }">
                            <button v-bind="props" @click="deviceStore.fetchNewDevices" class="status-btn">
                                <Radar style="width: 16px; height: 16px; transition: color 0.2s;" :style="{ color: hasNewDevices ? '#10b981' : 'rgb(var(--color-text-secondary))' }" :class="{ 'pulse-animation': hasNewDevices }" />
                                <span v-if="hasNewDevices" class="badge-count">
                                    {{ deviceStore.stats.new_24h }}
                                </span>
                                <v-tooltip activator="parent" location="bottom" content-class="!px-2 !py-1 !text-[10px] !min-h-0">
                                    <span>Discovered Devices</span>
                                </v-tooltip>
                            </button>
                        </template>

                        <!-- New Devices Popover -->
                        <div class="popover-card">
                            <div class="popover-header">
                                <h3>Newly Discovered</h3>
                                <button @click="dismissNewDevices">Dismiss</button>
                            </div>
                            <div style="max-h: 320px; overflow-y: auto;">
                                <div v-if="deviceStore.newDevices.length === 0" style="padding: 32px; text-align: center; color: rgb(var(--color-text-secondary)); font-size: 10px; font-weight: 500;">Loading devices...</div>
                                <button v-for="device in deviceStore.newDevices" :key="device.id" @click="goToDevice(device)" class="new-device-item">
                                    <div class="new-device-icon">
                                        <component :is="getIcon(device.icon || 'help-circle')" style="height: 16px; width: 16px;" />
                                    </div>
                                    <div style="flex: 1; min-width: 0;">
                                        <div style="font-size: 12px; font-weight: bold; color: rgb(var(--color-text-primary)); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ device.display_name || device.name }}</div>
                                        <div style="font-size: 10px; color: rgb(var(--color-text-secondary)); font-family: monospace;">{{ device.ip }}</div>
                                    </div>
                                    <ChevronRightIcon style="height: 12px; width: 12px; color: rgb(var(--color-text-tertiary));" />
                                </button>
                            </div>
                            <div style="padding: 8px; border-top: 1px solid rgba(var(--color-border), 0.5);">
                                <router-link to="/devices" @click="showNewDevices = false" class="popover-footer-link">
                                    <span>Manage all devices</span>
                                    <ArrowRightIcon style="height: 12px; width: 12px;" />
                                </router-link>
                            </div>
                        </div>
                    </v-menu>

                    <!-- Connection Status -->
                    <div class="status-btn">
                        <Zap style="width: 16px; height: 16px;" :style="{ color: ws.connected.value ? '#10b981' : '#rose-500' }" :class="{ 'pulse-animation': ws.connected.value }" />
                        <v-tooltip activator="parent" location="bottom" content-class="!px-2 !py-1 !text-[10px] !min-h-0">
                            <span>System Status: {{ ws.connected.value ? 'Live' : 'Offline' }}</span>
                        </v-tooltip>
                    </div>

                    <div class="separator"></div>

                    <!-- Notifications Dropdown -->
                    <v-menu location="bottom end" transition="scale-transition" offset="8" :close-on-content-click="false" v-model="showNotifications" @update:modelValue="onNotificationsToggle">
                        <template v-slot:activator="{ props }">
                            <button v-bind="props" class="status-btn">
                                <BellIcon style="height: 16px; width: 16px; color: rgb(var(--color-text-secondary));" />
                                <span v-if="notificationStore.unreadCount > 0" class="badge-count notifications">
                                    {{ notificationStore.unreadCount }}
                                </span>
                                <v-tooltip activator="parent" location="bottom" content-class="!px-2 !py-1 !text-[10px] !min-h-0">
                                    <span>System Activity</span>
                                </v-tooltip>
                            </button>
                        </template>

                        <div class="popover-card" style="width: 320px;">
                            <div class="popover-header">
                                <h3>Recent Activity</h3>
                                <button @click="markAllAsRead" style="color: #2563eb;">Clear all</button>
                            </div>
                            <div style="max-h: 384px; overflow-y: auto;">
                                <div v-if="notificationStore.events.length === 0" style="padding: 40px; text-align: center; color: rgb(var(--color-text-secondary)); font-size: 10px; font-weight: 500;">All caught up!</div>
                                <button v-for="event in notificationStore.events" :key="event.id" @click="goToEvent(event)" class="notif-item">
                                    <div v-if="!event.read_at" class="notif-indicator"></div>
                                    <div style="padding: 8px; border-radius: 12px; display: flex; align-items: center; justify-content: center;" :style="getEventColorStyles(event.level)">
                                        <component :is="getEventIcon(event)" style="height: 16px; width: 16px;" />
                                    </div>
                                    <div style="flex: 1; min-width: 0;">
                                        <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
                                            <span style="font-size: 10px; font-weight: 900; text-transform: uppercase; color: rgb(var(--color-text-tertiary));">{{ event.task_type?.replace('_', ' ') || 'System' }}</span>
                                            <span style="font-size: 9px; color: rgb(var(--color-text-tertiary));">{{ formatRelativeTime(parseUTC(event.created_at)) }}</span>
                                        </div>
                                        <p style="font-size: 12px; font-weight: 500; color: rgb(var(--color-text-primary)); margin: 2px 0 0 0; line-height: 1.3; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">{{ event.message }}</p>
                                    </div>
                                </button>
                            </div>
                            <div style="padding: 8px; border-top: 1px solid rgba(var(--color-border), 0.5);">
                                <router-link to="/logs" @click="showNotifications = false" class="popover-footer-link">
                                    <span>View all events</span>
                                    <ArrowRightIcon style="height: 12px; width: 12px;" />
                                </router-link>
                            </div>
                        </div>
                    </v-menu>
                </div>

                <!-- Theme Toggle -->
                <div class="status-panel">
                    <button @click="toggleTheme" class="status-btn">
                        <SunIcon v-if="theme.global.current.value.dark" style="height: 16px; width: 16px;" />
                        <MoonIcon v-else style="height: 16px; width: 16px;" />
                        <v-tooltip activator="parent" location="bottom" content-class="!px-2 !py-1 !text-[10px] !min-h-0">
                            <span>{{ theme.global.current.value.dark ? 'Light Mode' : 'Dark Mode' }}</span>
                        </v-tooltip>
                    </button>
                </div>

                <!-- User Profile -->
                <div class="status-panel">
                    <v-menu location="bottom end" transition="scale-transition" offset="8" :close-on-content-click="false" v-model="showUserMenu">
                        <template v-slot:activator="{ props }">
                            <button v-bind="props" class="profile-btn">
                                <div class="profile-avatar">
                                    {{ authStore.user?.username?.charAt(0).toUpperCase() || 'U' }}
                                </div>
                                <span class="profile-name">{{ authStore.user?.username || 'User' }}</span>
                                <ChevronDownIcon style="height: 12px; width: 12px; color: rgb(var(--color-text-secondary)); transition: transform 0.2s;" :style="{ transform: showUserMenu ? 'rotate(180deg)' : 'rotate(0)' }" />
                                <v-tooltip activator="parent" location="bottom" content-class="!px-2 !py-1 !text-[10px] !min-h-0">
                                    <span>User Account</span>
                                </v-tooltip>
                            </button>
                        </template>
                        <v-card style="width: 224px; border-radius: 12px; border: 1px solid rgb(var(--color-border)); background-color: rgb(var(--color-surface-elevated)); overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);">
                            <div style="padding: 16px; background-color: rgba(var(--color-surface), 0.3); border-bottom: 1px solid rgba(var(--color-border), 0.5);">
                                <p style="font-size: 12px; font-weight: 900; text-transform: uppercase; color: rgb(var(--color-text-primary)); margin: 0;">{{ authStore.user?.full_name || authStore.user?.username }}</p>
                                <p style="font-size: 10px; color: rgb(var(--color-text-secondary)); margin: 2px 0 0 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">System Administrator</p>
                            </div>
                            <div style="padding: 6px;">
                                <router-link to="/settings" @click="showUserMenu = false" class="user-menu-item" style="border-radius: 8px;">
                                    <UserIcon style="height: 16px; width: 16px;" />
                                    <span>Profile Settings</span>
                                </router-link>
                                <button @click="handleLogout" class="user-menu-item" style="border-radius: 8px; color: #ef4444; width: 100%; text-align: left; background: transparent; border: none; margin-top: 4px;">
                                    <LogOutIcon style="height: 16px; width: 16px;" />
                                    <span>Sign Out</span>
                                </button>
                            </div>
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
    theme.global.name.value = nextTheme
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

const getEventColorStyles = (level) => {
    if (level === 'ERROR') return { backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#ef4444' }
    if (level === 'WARNING') return { backgroundColor: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b' }
    return { backgroundColor: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6' }
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
.top-bar-container {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 0 16px;
  justify-content: space-between;
}

.brand-section {
  display: flex;
  align-items: center;
}

.mobile-trigger {
  display: flex;
  align-items: center;
}
@media (min-width: 768px) {
  .mobile-trigger {
    display: none !important;
  }
}

.divider {
  display: none;
  height: 24px;
  width: 1px;
  background-color: rgb(var(--color-border));
  margin: 0 16px;
}
@media (min-width: 1024px) {
  .divider {
    display: block;
  }
}

.search-section {
  flex-grow: 1;
  max-width: 32rem;
  width: 100%;
  padding: 0 8px;
}
@media (max-width: 767px) {
  .search-section {
    display: none;
  }
}

.actions-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-panel {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  background-color: rgb(var(--color-surface) / 40%);
  border-radius: 8px;
  border: 1px solid rgb(var(--color-border) / 50%);
}
@media (max-width: 1023px) {
  .status-panel.integrations {
    display: none !important;
  }
}

.status-btn {
  position: relative;
  display: flex;
  align-items: center;
  height: 32px;
  width: 32px;
  justify-content: center;
  cursor: pointer;
  background: transparent;
  border: none;
  border-radius: 6px;
  transition: all 0.2s;
  color: rgb(var(--color-text-secondary));
}
.status-btn:hover {
  background-color: rgb(var(--color-surface-elevated));
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.status-indicator-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  height: 8px;
  width: 8px;
  border-radius: 50%;
  border: 2px solid rgb(var(--color-surface));
}

.badge-count {
  position: absolute;
  top: -4px;
  right: -4px;
  display: flex;
  height: 16px;
  width: 16px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background-color: #10b981;
  font-size: 8px;
  font-weight: 900;
  color: white;
  border: 1px solid rgb(var(--color-surface));
}

.badge-count.notifications {
  background-color: #3b82f6;
}

.separator {
  width: 1px;
  height: 16px;
  background-color: rgb(var(--color-border));
  margin: 0 2px;
}
@media (max-width: 639px) {
  .separator {
    display: none !important;
  }
}

.profile-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 32px;
  padding: 0 10px 0 4px;
  border: none;
  background: transparent;
  border-radius: 6px;
  transition: all 0.2s;
  cursor: pointer;
  color: rgb(var(--color-text-primary));
}
.profile-btn:hover {
  background-color: rgb(var(--color-surface-elevated));
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.profile-avatar {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 10px;
  font-weight: 700;
}

.profile-name {
  font-size: 11px;
  font-weight: 700;
  color: rgb(var(--color-text-primary));
}
@media (max-width: 639px) {
  .profile-name {
    display: none !important;
  }
}

.popover-card {
  width: 288px;
  border-radius: 12px;
  border: 1px solid rgb(var(--color-border));
  background-color: rgb(var(--color-surface-elevated) / 95%);
  backdrop-filter: blur(24px);
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.popover-header {
  padding: 12px 16px;
  border-bottom: 1px solid rgb(var(--color-border) / 50%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: rgb(var(--color-surface) / 30%);
}

.popover-header h3 {
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: rgb(var(--color-text-primary));
  margin: 0;
}

.popover-header button {
  font-size: 9px;
  font-weight: 700;
  color: rgb(var(--color-text-secondary));
  background: transparent;
  border: none;
  cursor: pointer;
}
.popover-header button:hover {
  color: rgb(var(--color-text-primary));
}

.new-device-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: transparent;
  border: none;
  border-bottom: 1px solid rgb(var(--color-border) / 30%);
  text-align: left;
  cursor: pointer;
}
.new-device-item:hover {
  background-color: rgba(59, 130, 246, 0.05);
}
.new-device-item:last-child {
  border-bottom: none;
}

.new-device-icon {
  padding: 8px;
  background-color: rgb(var(--color-surface) / 50%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgb(var(--color-text-secondary));
}

.new-device-item:hover .new-device-icon {
  background-color: rgba(59, 130, 246, 0.1);
  color: #2563eb;
}

.popover-footer-link {
  width: 100%;
  padding: 8px 16px;
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #2563eb;
  text-decoration: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
}
.popover-footer-link:hover {
  background-color: rgba(59, 130, 246, 0.05);
}

.pulse-animation {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
