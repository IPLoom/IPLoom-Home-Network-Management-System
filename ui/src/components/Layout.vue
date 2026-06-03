<template>
  <div class="flex flex-col h-screen w-full bg-slate-50 dark:bg-slate-900/95 text-slate-800 dark:text-slate-100 overflow-hidden">
    <!-- Full Width Top Bar -->
    <TopBar @toggle-mobile-menu="mobileMenuOpen = !mobileMenuOpen" />

    <div class="flex flex-1 overflow-hidden">
      <!-- Desktop Sidebar -->
      <aside :class="[
        'hidden md:flex flex-col bg-white dark:bg-slate-800/90 border-r border-slate-200 dark:border-slate-700/60 backdrop-blur-md transition-all duration-300 z-20',
        sidebarCollapsed ? 'w-16' : 'w-56'
      ]">
        <!-- Navigation -->
        <nav class="flex-1 overflow-y-auto py-4 px-2 custom-scrollbar">
          <ul class="space-y-1">
            <li v-for="item in navItems" :key="item.name">
              <router-link :to="item.path" class="nav-item group flex items-center justify-between" :class="[
                $route.path === item.path || ($route.path.startsWith(item.path) && item.path !== '/')
                  ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 font-bold border-l-2 border-blue-500 rounded-r-xl rounded-l-none'
                  : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700/50 rounded-xl'
              ]" v-tooltip:right="sidebarCollapsed ? item.name : null">
                <div class="flex items-center">
                  <div class="relative">
                    <component :is="item.icon" class="h-5 w-5 flex-shrink-0 transition-transform group-hover:scale-105" :class="sidebarCollapsed ? 'mx-auto' : 'mr-3'" />
                    <!-- Optional Badge dot on icon for collapsed state -->
                    <span v-if="sidebarCollapsed && item.badge" 
                      class="absolute -top-1 -right-1 h-2.5 w-2.5 bg-emerald-500 rounded-full border border-white dark:border-slate-800 animate-pulse"></span>
                  </div>
                  <span v-if="!sidebarCollapsed" class="text-sm tracking-wide">{{ item.name }}</span>
                </div>
                <Badge v-if="!sidebarCollapsed && item.badge" :value="item.badge" severity="success" class="scale-90" />
              </router-link>
            </li>
          </ul>
        </nav>

        <!-- Version & Toggle -->
        <div class="p-3 border-t border-slate-200 dark:border-slate-700/60 space-y-2">
          <div v-if="!sidebarCollapsed"
            class="text-[10px] uppercase font-black tracking-widest text-slate-400 dark:text-slate-500 text-center py-1">
            {{ version }}
          </div>
          <button @click="sidebarCollapsed = !sidebarCollapsed"
            class="w-full flex items-center p-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700/50 text-slate-500 dark:text-slate-400 transition-all duration-300"
            :class="sidebarCollapsed ? 'justify-center' : 'px-3 space-x-3'"
            v-tooltip:right="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'">
            <component :is="sidebarCollapsed ? ChevronRightIcon : ChevronLeftIcon" class="h-5 w-5 flex-shrink-0" />
            <span v-if="!sidebarCollapsed" class="text-sm font-semibold">Collapse</span>
          </button>
        </div>
      </aside>

      <!-- Mobile Menu (PrimeVue Drawer) -->
      <Drawer v-model:visible="mobileMenuOpen" position="left" class="w-72 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700/80">
        <template #header>
          <AppLogo class="scale-95 origin-left" />
        </template>
        <div class="flex flex-col h-full justify-between py-4">
          <nav class="flex-1 overflow-y-auto px-2">
            <ul class="space-y-1">
              <li v-for="item in navItems" :key="item.name">
                <router-link :to="item.path" @click="mobileMenuOpen = false" class="nav-item flex items-center justify-between !px-4 !py-3.5" :class="[
                  $route.path === item.path || ($route.path.startsWith(item.path) && item.path !== '/')
                    ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 font-bold border-l-2 border-blue-500'
                    : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700/50'
                ]">
                  <div class="flex items-center">
                    <component :is="item.icon" class="h-5 w-5 mr-3 flex-shrink-0" />
                    <span class="text-sm font-medium tracking-wide">{{ item.name }}</span>
                  </div>
                  <Badge v-if="item.badge" :value="item.badge" severity="success" class="scale-90" />
                </router-link>
              </li>
            </ul>
          </nav>
          <div class="px-6 py-4 border-t border-slate-100 dark:border-slate-700/50 text-[10px] uppercase font-bold tracking-widest text-slate-400 text-center">
            {{ version }}
          </div>
        </div>
      </Drawer>

      <!-- Main Content Area -->
      <main class="flex-1 overflow-y-auto bg-slate-50/50 dark:bg-slate-900/50">
        <div class="max-w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
          <router-view />
        </div>
      </main>
    </div>

    <!-- Global Notifications -->
    <NotificationToast />
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import AppLogo from './AppLogo.vue'
import TopBar from './TopBar.vue'
import NotificationToast from './NotificationToast.vue'
import { useWebSockets } from '@/composables/useWebSockets'
import { useNotifications } from '@/composables/useNotifications'
import Drawer from 'primevue/drawer'
import Badge from 'primevue/badge'

const { connect, lastNotification } = useWebSockets()
const { notifyInfo, notifyError, notifySuccess } = useNotifications()

import { useNotificationStore } from '@/stores/notifications'
const notificationStore = useNotificationStore()

onMounted(() => {
  connect()
})

import {
  HomeIcon,
  ComputerDesktopIcon,
  TableCellsIcon,
  Cog6ToothIcon,
  Bars3Icon,
  XMarkIcon,
  ListBulletIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  BellIcon,
  ChartBarIcon,
  CommandLineIcon,
  ShareIcon,
  SquaresPlusIcon
} from '@heroicons/vue/24/outline'

const sidebarCollapsed = ref(true)
const mobileMenuOpen = ref(false)
const version = import.meta.env.VITE_APP_VERSION || 'v0.3.1'

import { useDeviceStore } from '@/stores/devices'
const deviceStore = useDeviceStore()

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

