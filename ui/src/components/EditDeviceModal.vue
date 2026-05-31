<template>
  <v-dialog v-model="internalIsOpen" max-width="500" persistent>
    <v-card rounded="xl" class="bg-surface">
      <v-card-text class="pt-8 px-6 pb-6 text-center">
        <!-- Icon and Brand Selectors -->
        <div class="d-flex flex-column align-center mb-6 position-relative">
          
          <!-- Icon Picker -->
          <v-menu v-model="isIconMenuOpen" :close-on-content-click="false" location="bottom center" transition="scale-transition">
            <template v-slot:activator="{ props }">
              <v-btn v-bind="props" icon variant="outlined" width="80" height="80" class="rounded-xl border-opacity-50" color="medium-emphasis">
                <img v-if="form.icon && form.icon.startsWith('/static/')" :src="form.icon" style="width: 48px; height: 48px; object-fit: contain;" />
                <component v-else :is="getIcon(form.icon || 'help-circle')" style="width: 40px; height: 40px;" />
                <v-badge color="primary" icon="mdi-pencil" location="bottom right" offset-x="10" offset-y="10" class="position-absolute h-100 w-100" style="pointer-events: none;"></v-badge>
              </v-btn>
            </template>

            <v-card width="320" rounded="xl" elevation="8" class="mt-2">
              <v-card-text class="pa-2">
                <v-text-field
                  v-model="iconSearch"
                  prepend-inner-icon="mdi-magnify"
                  placeholder="Search icons..."
                  density="compact"
                  variant="solo-filled"
                  flat
                  hide-details
                  class="mb-2"
                ></v-text-field>

                <div style="max-height: 300px; overflow-y: auto;" class="pr-1">
                  <div v-for="(icons, category) in groupedIcons" :key="category" class="mb-4">
                    <div class="text-[10px] font-weight-black text-uppercase text-medium-emphasis mb-2 px-2">{{ category }}</div>
                    <v-row dense>
                      <v-col cols="3" v-for="icon in icons" :key="icon.name">
                        <v-btn
                          icon
                          variant="text"
                          width="100%"
                          height="56"
                          rounded="lg"
                          :color="form.icon === icon.name ? 'primary' : 'medium-emphasis'"
                          :class="{'bg-primary-lighten-4': form.icon === icon.name}"
                          @click="form.icon = icon.name; isIconMenuOpen = false"
                          class="d-flex flex-column"
                        >
                          <img v-if="icon.name.startsWith('/static/')" :src="icon.name" style="width: 24px; height: 24px; object-fit: contain;" />
                          <component v-else :is="getIcon(icon.name)" style="width: 24px; height: 24px;" />
                        </v-btn>
                      </v-col>
                    </v-row>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-menu>

          <!-- Brand Picker (Absolute positioned over Icon Picker) -->
          <v-menu v-model="isBrandMenuOpen" :close-on-content-click="false" location="bottom start" transition="scale-transition">
            <template v-slot:activator="{ props }">
              <v-btn v-bind="props" icon variant="elevated" size="small" class="position-absolute" style="top: -10px; left: calc(50% - 50px);" color="surface">
                <img v-if="form.brand_icon" :src="form.brand_icon" style="width: 20px; height: 20px; object-fit: contain;" />
                <component v-else :is="getIcon('shield-question')" class="text-medium-emphasis" style="width: 16px; height: 16px;" />
              </v-btn>
            </template>

            <v-card width="280" rounded="xl" elevation="8" class="mt-2">
              <v-card-text class="pa-2">
                <div class="text-[10px] font-weight-black text-uppercase text-medium-emphasis mb-2 px-2">Assign Brand</div>
                <v-text-field
                  v-model="brandSearch"
                  prepend-inner-icon="mdi-magnify"
                  placeholder="Search brands..."
                  density="compact"
                  variant="solo-filled"
                  flat
                  hide-details
                  class="mb-2"
                ></v-text-field>

                <div style="max-height: 250px; overflow-y: auto;" class="pr-1">
                  <v-list density="compact" bg-color="transparent">
                    <v-list-item @click="form.brand = ''; form.brand_icon = ''; isBrandMenuOpen = false" class="rounded-lg mb-1" border>
                      <template v-slot:prepend>
                        <v-avatar size="24" color="surface-variant" rounded="sm" class="mr-3">
                          <component :is="LucideIcons.X" class="w-4 h-4 text-medium-emphasis" />
                        </v-avatar>
                      </template>
                      <v-list-item-title class="text-caption font-weight-bold">None</v-list-item-title>
                    </v-list-item>
                    
                    <v-list-item v-for="brand in filteredBrands" :key="brand.id"
                                 @click="form.brand = brand.name; form.brand_icon = brand.path; isBrandMenuOpen = false"
                                 class="rounded-lg mb-1"
                                 :class="{'bg-primary-lighten-4 text-primary': form.brand === brand.name}" border>
                      <template v-slot:prepend>
                        <img :src="brand.path" style="width: 24px; height: 24px; object-fit: contain;" class="mr-3 bg-white rounded pa-1" />
                      </template>
                      <v-list-item-title class="text-caption font-weight-bold">{{ brand.name }}</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </div>
              </v-card-text>
            </v-card>
          </v-menu>
          
          <v-text-field
            v-model="form.display_name"
            placeholder="Enter device name..."
            variant="plain"
            class="text-h5 font-weight-black text-center mt-4 w-100"
            hide-details
            style="text-align: center;"
          ></v-text-field>
          <div class="text-[10px] font-weight-black text-uppercase text-medium-emphasis mt-1" style="letter-spacing: 0.2em;">Device Configuration</div>
        </div>

        <v-form @submit.prevent="saveDevice" class="text-left mt-6">
          <div class="mb-4">
            <div class="text-[10px] font-weight-black text-uppercase text-medium-emphasis mb-1">IP Address</div>
            <div class="text-body-2 font-family-mono">{{ device?.ip }}</div>
          </div>

          <div class="mb-4">
            <div class="text-[10px] font-weight-black text-uppercase text-medium-emphasis mb-1">Device Category</div>
            <v-autocomplete
              v-model="form.device_type"
              :items="filteredDeviceTypes"
              placeholder="Select Category"
              variant="outlined"
              density="comfortable"
              hide-details
              rounded="lg"
            >
              <template v-slot:prepend-inner>
                <component :is="getIcon(form.device_type)" class="w-5 h-5 text-primary mr-2" />
              </template>
            </v-autocomplete>
          </div>

          <div class="mb-4">
            <div class="text-[10px] font-weight-black text-uppercase text-medium-emphasis mb-1">Manufacturer / Brand</div>
            <v-autocomplete
              v-model="form.brand"
              :items="filteredBrands"
              item-title="name"
              item-value="name"
              placeholder="Select or type brand..."
              variant="outlined"
              density="comfortable"
              hide-details
              rounded="lg"
            >
              <template v-slot:prepend-inner>
                <div class="w-6 h-6 rounded bg-white d-flex align-center justify-center border mr-2 overflow-hidden flex-shrink-0">
                    <img v-if="form.brand_icon" :src="form.brand_icon" class="w-100 h-100" style="object-fit: contain;" />
                    <div v-else class="text-[8px] font-weight-bold text-medium-emphasis">N/A</div>
                </div>
              </template>
              <template v-slot:item="{ props, item }">
                <v-list-item v-bind="props" title="">
                  <div class="d-flex align-center">
                    <img :src="item.raw.path" style="width: 24px; height: 24px; object-fit: contain;" class="mr-3 rounded bg-white pa-1" />
                    <span class="text-caption font-weight-bold">{{ item.raw.name }}</span>
                  </div>
                </v-list-item>
              </template>
            </v-autocomplete>
          </div>

          <div class="mb-6">
            <div class="text-[10px] font-weight-black text-uppercase text-medium-emphasis mb-1">Connected Via (Parent)</div>
            <v-autocomplete
              v-model="form.parent_id"
              :items="parentOptions"
              item-title="title"
              item-value="id"
              placeholder="Search devices..."
              variant="outlined"
              density="comfortable"
              hide-details
              rounded="lg"
            >
              <template v-slot:item="{ props, item }">
                <v-list-item v-bind="props" :title="item.raw.title">
                  <template v-slot:prepend v-if="item.raw.icon">
                    <component :is="getIcon(item.raw.icon)" class="w-4 h-4 mr-3 opacity-70" />
                  </template>
                </v-list-item>
              </template>
            </v-autocomplete>
          </div>

          <div class="d-flex justify-end gap-2">
            <v-btn variant="text" color="medium-emphasis" class="text-none" @click="closeModal">Cancel</v-btn>
            <v-btn type="submit" color="primary" variant="flat" class="text-none px-6" :loading="isSaving">Save Changes</v-btn>
          </div>
        </v-form>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import api from '@/utils/api'
import { getIcon } from '@/utils/icons'
import * as LucideIcons from 'lucide-vue-next'
import { useNotifications } from '@/composables/useNotifications'
import { useSystemStore } from '@/stores/system'

const systemStore = useSystemStore()
const { notifySuccess, notifyError } = useNotifications()

const deviceTypes = computed(() => systemStore.deviceTypes)
const availableIcons = computed(() => systemStore.availableIcons)

const props = defineProps({
  isOpen: Boolean,
  device: Object
})

const emit = defineEmits(['close', 'save'])

const internalIsOpen = computed({
  get: () => props.isOpen,
  set: (val) => {
    if (!val) closeModal()
  }
})

const isSaving = ref(false)
const allDevices = ref([])

const isIconMenuOpen = ref(false)
const isBrandMenuOpen = ref(false)
const iconSearch = ref('')
const brandSearch = ref('')

const form = ref({
  display_name: '',
  device_type: '',
  icon: '',
  brand: '',
  brand_icon: '',
  parent_id: null
})

const filteredDeviceTypes = computed(() => {
  return deviceTypes.value
})

const filteredIcons = computed(() => {
  if (!iconSearch.value) return availableIcons.value
  const s = iconSearch.value.toLowerCase()
  return availableIcons.value.filter(icon => 
    (icon.label || '').toLowerCase().includes(s) || 
    (icon.category || '').toLowerCase().includes(s) ||
    (icon.name || '').toLowerCase().includes(s)
  )
})

const groupedIcons = computed(() => {
  const groups = {}
  filteredIcons.value.forEach(icon => {
    const cat = icon.category || 'Other'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(icon)
  })
  return groups
})

const filteredBrands = computed(() => {
  const registry = systemStore.brandRegistry || []
  return registry
})

const parentOptions = computed(() => {
  const others = allDevices.value.filter(d => d.id !== props.device?.id)
  const options = others.map(d => ({
    id: d.id,
    title: d.display_name || d.name || d.ip,
    icon: d.icon
  }))
  options.unshift({ id: null, title: 'Main Gateway (Default)', icon: 'router' })
  return options
})

watch(() => form.value.device_type, (newType) => {
  if (newType && systemStore.iconMap[newType]) {
    form.value.icon = systemStore.iconMap[newType]
  }
})

watch(() => form.value.brand, (newBrand) => {
    const match = systemStore.brandRegistry?.find(b => b.name === newBrand)
    if (match) {
        form.value.brand_icon = match.path
    }
})

const fetchAllDevices = async () => {
  try {
    const res = await api.get('/devices/?limit=-1')
    allDevices.value = res.data.items || []
  } catch (e) {
    console.error('Failed to fetch devices:', e)
  }
}

onMounted(() => {
  fetchAllDevices()
})

watch(() => props.device, (newVal) => {
  if (newVal) {
    form.value = {
      display_name: newVal.display_name || newVal.name || '',
      device_type: newVal.device_type || 'unknown',
      icon: newVal.icon || 'help-circle',
      brand: newVal.brand || '',
      brand_icon: newVal.brand_icon || '',
      parent_id: newVal.parent_id || null
    }
  }
}, { immediate: true })

const closeModal = () => {
  emit('close')
}

const saveDevice = async () => {
  if (!props.device) return
  isSaving.value = true
  try {
    const response = await api.patch(`/devices/${props.device.id}`, form.value)
    notifySuccess('Device updated successfully')
    emit('save', response.data)
    closeModal()
  } catch (error) {
    console.error('Failed to update device', error)
    notifyError('Failed to update device')
  } finally {
    isSaving.value = false
  }
}
</script>

<style scoped>
/* Scoped styles can be completely omitted as we use Vuetify classes */
</style>
