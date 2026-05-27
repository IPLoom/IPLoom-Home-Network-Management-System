<template>
  <v-layout class="h-screen w-full bg-slate-50 dark:bg-slate-900 overflow-hidden">
    <!-- Full Width Top Bar -->
    <TopBar @toggle-mobile-menu="drawer = !drawer" />

    <v-navigation-drawer
      v-model="drawer"
      :rail="sidebarCollapsed"
      class="bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700"
    >
      <!-- Navigation -->
      <nav class="flex-grow overflow-y-auto py-4 px-0">
        <ul class="space-y-1">
          <li v-for="item in navItems" :key="item.name">
            <router-link :to="item.path" class="relative flex items-center text-sm font-medium transition-colors group w-full" :class="[
              $route.path === item.path || ($route.path.startsWith(item.path) && item.path !== '/')
                ? 'bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 font-bold'
                : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700',
              sidebarCollapsed ? 'justify-center py-3' : 'pl-6 pr-4 py-3'
            ]" v-tooltip:right="sidebarCollapsed ? item.name : null">
              <!-- Active Indicator Line -->
              <div v-if="$route.path === item.path || ($route.path.startsWith(item.path) && item.path !== '/')"
                class="absolute left-0 top-0 bottom-0 w-1 bg-blue-600 dark:bg-blue-500"></div>

              <div class="relative flex items-center">
                <component :is="item.icon" class="h-5 w-5 flex-shrink-0" :class="sidebarCollapsed ? '' : 'mr-3'" />
                <span v-if="sidebarCollapsed && item.badge" 
                  class="absolute -top-1 -right-1 h-2 w-2 bg-emerald-500 rounded-full border border-white dark:border-slate-800 animate-pulse"></span>
              </div>
              <span v-if="!sidebarCollapsed" class="flex-1 text-sm">{{ item.name }}</span>
              <span v-if="!sidebarCollapsed && item.badge" 
                class="ml-auto px-1.5 py-0.5 text-[9px] font-black bg-emerald-500 text-white rounded-full animate-pulse-slow">
                {{ item.badge }}
              </span>
            </router-link>
          </li>
        </ul>
      </nav>

      <template v-slot:append>
        <div class="p-2 border-t border-slate-200 dark:border-slate-700 space-y-2">
          <div v-if="!sidebarCollapsed"
            class="text-[10px] uppercase font-bold tracking-widest text-slate-400 dark:text-slate-600 text-center py-2">
            {{ version }}
          </div>
          <button @click="sidebarCollapsed = !sidebarCollapsed"
            class="w-full flex items-center p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 transition-all duration-300"
            :class="sidebarCollapsed ? 'justify-center' : 'px-3 space-x-3'"
            v-tooltip:right="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'">
            <component :is="sidebarCollapsed ? ChevronRightIcon : ChevronLeftIcon" class="h-5 w-5 flex-shrink-0" />
            <span v-if="!sidebarCollapsed" class="text-sm font-medium">Collapse</span>
          </button>
        </div>
      </template>
    </v-navigation-drawer>

    <!-- Main Content Area -->
    <v-main class="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-900">
      <v-container fluid class="py-6 md:py-8 h-full">
        <router-view />
      </v-container>
    </v-main>

    <!-- Global Notifications -->
    <NotificationToast />
  </v-layout>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
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
const drawer = ref(null)
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
