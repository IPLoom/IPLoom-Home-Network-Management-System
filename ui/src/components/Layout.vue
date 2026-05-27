<template>
  <v-layout style="height: 100vh; overflow: hidden;">
    <!-- Full Width Top Bar -->
    <TopBar @toggle-mobile-menu="drawer = !drawer" />

    <v-navigation-drawer
      v-model="drawer"
      :rail="sidebarCollapsed"
      :permanent="!mobile"
      border="right"
    >
      <!-- Navigation -->
      <nav class="nav-container">
        <ul class="nav-list">
          <li v-for="item in navItems" :key="item.name">
            <router-link :to="item.path" class="layout-nav-item" :class="[
              $route.path === item.path || ($route.path.startsWith(item.path) && item.path !== '/')
                ? 'active'
                : '',
              sidebarCollapsed ? 'collapsed' : 'expanded'
            ]" v-tooltip:right="sidebarCollapsed ? item.name : null">
              <!-- Active Indicator Line -->
              <div v-if="$route.path === item.path || ($route.path.startsWith(item.path) && item.path !== '/')"
                class="active-indicator"></div>

              <div class="icon-wrapper">
                <component :is="item.icon" class="nav-icon" />
                <span v-if="sidebarCollapsed && item.badge" 
                  class="badge-dot animate-pulse"></span>
              </div>
              <span v-if="!sidebarCollapsed" class="nav-label">{{ item.name }}</span>
              <span v-if="!sidebarCollapsed && item.badge" 
                class="nav-badge animate-pulse-slow">
                {{ item.badge }}
              </span>
            </router-link>
          </li>
        </ul>
      </nav>

      <template v-slot:append>
        <div class="sidebar-footer">
          <div v-if="!sidebarCollapsed" class="version-text">
            {{ version }}
          </div>
          <button @click="sidebarCollapsed = !sidebarCollapsed"
            class="collapse-btn"
            :class="sidebarCollapsed ? 'collapsed' : 'expanded'"
            v-tooltip:right="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'">
            <component :is="sidebarCollapsed ? ChevronRightIcon : ChevronLeftIcon" style="height: 20px; width: 20px; flex-shrink: 0;" />
            <span v-if="!sidebarCollapsed">Collapse</span>
          </button>
        </div>
      </template>
    </v-navigation-drawer>

    <!-- Main Content Area -->
    <v-main style="flex: 1; overflow-y: auto;">
      <v-container fluid style="padding: 24px; height: 100%;">
        <router-view />
      </v-container>
    </v-main>

    <!-- Global Notifications -->
    <NotificationToast />
  </v-layout>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useDisplay } from 'vuetify'
import AppLogo from './AppLogo.vue'
import TopBar from './TopBar.vue'
import NotificationToast from './NotificationToast.vue'
import { useWebSockets } from '@/composables/useWebSockets'
import { useNotifications } from '@/composables/useNotifications'
import { useNotificationStore } from '@/stores/notifications'
import { useDeviceStore } from '@/stores/devices'

const { connect } = useWebSockets()
const { notifyInfo, notifyError, notifySuccess } = useNotifications()
const notificationStore = useNotificationStore()
const deviceStore = useDeviceStore()
const { mobile } = useDisplay()

onMounted(() => {
  connect()
})

import {
  HomeIcon,
  ComputerDesktopIcon,
  TableCellsIcon,
  Cog6ToothIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  BellIcon,
  ChartBarIcon,
  CommandLineIcon,
  ShareIcon,
  SquaresPlusIcon
} from '@heroicons/vue/24/outline'

const sidebarCollapsed = ref(true)
const drawer = ref(true)
const version = import.meta.env.VITE_APP_VERSION || 'v0.3.1'

const navItems = computed(() => [
  { name: 'Dashboard', path: '/', icon: HomeIcon },
  { name: 'Devices', path: '/devices', icon: ComputerDesktopIcon, badge: deviceStore.stats.new_24h > 0 ? deviceStore.stats.new_24h : null },
  { name: 'Topology', path: '/topology', icon: ShareIcon },
  { name: 'Integrations', path: '/integrations', icon: SquaresPlusIcon },
  { name: 'Events', path: '/events', icon: BellIcon },
  { name: 'Analytics', path: '/analytics', icon: ChartBarIcon },
  { name: 'IP Occupancy', path: '/occupancy', icon: TableCellsIcon },
  { name: 'Logs & Activity', path: '/logs', icon: CommandLineIcon },
  { name: 'Settings', path: '/settings', icon: Cog6ToothIcon },
])
</script>

<style scoped>
.nav-container {
  flex-grow: 1;
  overflow-y: auto;
  padding: 16px 0;
}

.nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.layout-nav-item {
  position: relative;
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  width: 100%;
  box-sizing: border-box;
  transition: all 0.2s;
  color: rgb(var(--color-text-secondary));
}

.layout-nav-item:hover {
  background-color: rgba(var(--color-text-secondary), 0.08);
  color: rgb(var(--color-text-primary));
}

.layout-nav-item.active {
  background-color: rgba(var(--color-primary), 0.1);
  color: rgb(var(--color-primary));
  font-weight: 700;
}

.layout-nav-item.collapsed {
  justify-content: center;
  padding: 12px 0;
}

.layout-nav-item.expanded {
  justify-content: flex-start;
  padding: 12px 16px 12px 24px;
}

.active-indicator {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background-color: rgb(var(--color-primary));
}

.icon-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.nav-icon {
  height: 20px;
  width: 20px;
  flex-shrink: 0;
  transition: margin 0.2s;
}

.layout-nav-item.expanded .nav-icon {
  margin-right: 12px;
}

.badge-dot {
  position: absolute;
  top: -4px;
  right: -4px;
  height: 8px;
  width: 8px;
  background-color: #10b981;
  border-radius: 50%;
  border: 1px solid rgb(var(--color-background));
}

.nav-label {
  flex: 1;
  font-size: 14px;
}

.nav-badge {
  margin-left: auto;
  padding: 2px 6px;
  font-size: 9px;
  font-weight: 900;
  background-color: #10b981;
  color: white;
  border-radius: 9999px;
}

.sidebar-footer {
  padding: 8px;
  border-top: 1px solid rgb(var(--color-border));
}

.version-text {
  font-size: 10px;
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: rgb(var(--color-text-tertiary));
  text-align: center;
  padding: 8px 0;
}

.collapse-btn {
  width: 100%;
  display: flex;
  align-items: center;
  padding: 8px;
  border-radius: 12px;
  border: none;
  background: transparent;
  color: rgb(var(--color-text-secondary));
  transition: all 0.2s;
  cursor: pointer;
}

.collapse-btn:hover {
  background-color: rgba(var(--color-text-secondary), 0.08);
}

.collapse-btn.collapsed {
  justify-content: center;
}

.collapse-btn.expanded {
  padding: 8px 12px;
}

.collapse-btn.expanded span {
  margin-left: 12px;
  font-size: 14px;
  font-weight: 500;
}
</style>
