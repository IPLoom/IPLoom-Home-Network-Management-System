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
      <v-list nav class="flex-grow-1 overflow-y-auto px-2 py-4">
        <v-list-item
          v-for="item in navItems"
          :key="item.name"
          :to="item.path"
          :value="item.name"
          color="primary"
          rounded="lg"
          class="mb-1"
          v-tooltip:right="sidebarCollapsed ? item.name : null"
        >
          <template v-slot:prepend>
            <div class="position-relative d-flex align-center justify-center" style="width: 24px; height: 24px; margin-right: 24px;">
              <component :is="item.icon" style="width: 20px; height: 20px;" />
              <v-badge
                v-if="sidebarCollapsed && item.badge"
                dot
                color="success"
                class="position-absolute"
                style="top: -4px; right: -4px;"
              ></v-badge>
            </div>
          </template>
          
          <v-list-item-title class="text-body-2 font-weight-medium" v-if="!sidebarCollapsed">{{ item.name }}</v-list-item-title>

          <template v-slot:append v-if="!sidebarCollapsed && item.badge">
            <v-badge
              :content="item.badge"
              color="success"
              inline
            ></v-badge>
          </template>
        </v-list-item>
      </v-list>

      <template v-slot:append>
        <div class="pa-2 border-t">
          <div v-if="!sidebarCollapsed" class="text-center font-weight-bold text-uppercase text-medium-emphasis mb-2" style="letter-spacing: 0.1em; font-size: 10px;">
            {{ version }}
          </div>
          <v-btn
            block
            variant="text"
            color="medium-emphasis"
            @click="sidebarCollapsed = !sidebarCollapsed"
            v-tooltip:right="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          >
            <component :is="sidebarCollapsed ? ChevronRightIcon : ChevronLeftIcon" style="width: 20px; height: 20px;" />
            <span v-if="!sidebarCollapsed" class="ml-2">Collapse</span>
          </v-btn>
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
  { name: 'Integrations', path: '/integrations', icon: SquaresPlusIcon },
  { name: 'Events', path: '/events', icon: BellIcon },
  { name: 'Analytics', path: '/analytics', icon: ChartBarIcon },
  { name: 'Logs & Activity', path: '/logs', icon: CommandLineIcon },
  { name: 'Settings', path: '/settings', icon: Cog6ToothIcon },
])
</script>

<style scoped>
</style>
