import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/api'

export const useDeviceStore = defineStore('devices', () => {
  const stats = ref({
    total: 0,
    online: 0,
    offline: 0,
    new_24h: 0,
    untrusted: 0
  })
  const newDevices = ref([])
  const isLoading = ref(false)

  const fetchStats = async () => {
    isLoading.value = true
    try {
      // Fetch just the first page with limit 1 to get global_stats efficiently
      const response = await api.get('/devices/', { params: { limit: 1 } })
      if (response.data.global_stats) {
        stats.value = response.data.global_stats
      }
    } catch (error) {
      console.error('Failed to fetch device stats:', error)
    } finally {
      isLoading.value = false
    }
  }

  const fetchNewDevices = async () => {
    try {
      const response = await api.get('/devices/', { params: { new_only: true, limit: 10, sort_by: 'first_seen', sort_order: 'desc' } })
      newDevices.value = response.data.items
    } catch (error) {
      console.error('Failed to fetch new devices:', error)
    }
  }

  return {
    stats,
    newDevices,
    isLoading,
    fetchStats,
    fetchNewDevices
  }
})

