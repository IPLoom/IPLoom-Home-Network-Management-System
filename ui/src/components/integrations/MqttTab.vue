<template>
  <div class="space-y-6">
    <!-- Header Card -->
    <div class="bg-white/80 dark:bg-slate-800/80 backdrop-blur-md rounded-2xl p-6 border border-slate-200/50 dark:border-slate-700/50 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
          <span>MQTT Message Broker</span>
          <span :class="[
            'px-2 py-0.5 text-xs font-semibold rounded-full uppercase tracking-wider',
            mqttStatus.reachable
              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-400'
              : 'bg-rose-100 text-rose-800 dark:bg-rose-500/20 dark:text-rose-400'
          ]">
            {{ mqttStatus.reachable ? 'Connected' : 'Disconnected' }}
          </span>
        </h2>
        <p class="text-xs font-mono text-slate-400 dark:text-slate-500 mt-1 truncate max-w-sm sm:max-w-md">
          Broker: {{ mqttStatus.broker || 'N/A' }} (Port {{ mqttStatus.port || 1883 }})
        </p>
      </div>

      <div class="flex items-center gap-3">
        <button 
          @click="refreshMqtt" 
          :disabled="loading"
          class="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 rounded-xl text-sm font-medium transition-all active:scale-95"
        >
          <svg class="h-4 w-4" :class="{ 'animate-spin': loading }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89H18v3" />
          </svg>
          <span>Refresh</span>
        </button>
      </div>
    </div>

    <!-- Error State -->
    <div v-if="mqttStatus.error" class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-2xl p-4 text-red-700 dark:text-red-400 text-sm flex items-start gap-3">
      <svg class="h-5 w-5 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <div>
        <h4 class="font-semibold">Broker Connection Failure</h4>
        <p class="mt-0.5">{{ mqttStatus.error }}</p>
      </div>
    </div>

    <!-- Details Card -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Connection Status Card -->
      <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200/60 dark:border-slate-700/60 p-6 shadow-sm space-y-4">
        <h3 class="text-sm font-bold text-slate-400 uppercase tracking-wider">Broker Status Details</h3>
        <div class="space-y-3">
          <div class="flex justify-between items-center text-sm py-1.5 border-b border-slate-50 dark:border-slate-700/50">
            <span class="text-slate-400">Connection Reachable</span>
            <span class="font-semibold" :class="mqttStatus.reachable ? 'text-emerald-600' : 'text-rose-600'">
              {{ mqttStatus.reachable ? 'Yes' : 'No' }}
            </span>
          </div>
          <div class="flex justify-between items-center text-sm py-1.5 border-b border-slate-50 dark:border-slate-700/50">
            <span class="text-slate-400">Client ID</span>
            <span class="font-mono text-slate-700 dark:text-slate-300 font-semibold">{{ mqttStatus.client_id || 'hnms-backend' }}</span>
          </div>
          <div class="flex justify-between items-center text-sm py-1.5 border-b border-slate-50 dark:border-slate-700/50">
            <span class="text-slate-400">Clean Session</span>
            <span class="font-semibold text-slate-700 dark:text-slate-300">True</span>
          </div>
          <div class="flex justify-between items-center text-sm py-1.5">
            <span class="text-slate-400">Subscriptions</span>
            <span class="font-semibold text-slate-700 dark:text-slate-300">Active</span>
          </div>
        </div>
      </div>

      <!-- MQTT Statistics -->
      <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200/60 dark:border-slate-700/60 p-6 shadow-sm space-y-4">
        <h3 class="text-sm font-bold text-slate-400 uppercase tracking-wider">Active Subscribed Topics</h3>
        <div class="space-y-2">
          <div 
            v-for="topic in activeTopics" 
            :key="topic"
            class="flex items-center justify-between text-xs py-2 px-3 bg-slate-50 dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800"
          >
            <span class="font-mono text-slate-600 dark:text-slate-400">{{ topic }}</span>
            <span class="px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400 rounded">
              Subscribed
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/utils/api'

const loading = ref(false)
const mqttStatus = ref({ status: 'unknown', reachable: false, broker: 'localhost', port: 1883, error: null })

const activeTopics = [
  'device/status',
  'device/telemetry',
  'network/events'
]

const refreshMqtt = async () => {
  loading.value = true
  try {
    const res = await api.get('/mqtt/status')
    mqttStatus.value = res.data
  } catch (err) {
    console.error('Failed to get MQTT status:', err)
    mqttStatus.value.reachable = false
    mqttStatus.value.error = err.response?.data?.detail || 'MQTT broker is offline.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refreshMqtt()
})
</script>
