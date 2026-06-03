<template>
    <Dialog 
        v-model:visible="visible" 
        modal 
        :draggable="false"
        :closable="!isSaving"
        :pt="{
            root: 'w-full max-w-md rounded-2xl bg-white dark:bg-slate-800 p-6 shadow-xl border border-slate-200 dark:border-slate-700 max-h-[95vh] overflow-y-auto flex flex-col',
            header: 'hidden',
            content: 'p-0 flex flex-col gap-6'
        }"
    >
        <div class="flex flex-col items-center mb-6">
            <Button 
                @click="toggleIconPopover($event)"
                :pt="{ root: 'h-20 w-20 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 shadow-lg flex items-center justify-center hover:border-blue-500 transition-all group overflow-hidden p-0 relative cursor-pointer' }"
            >
                <img v-if="form.icon && form.icon.startsWith('/static/')" :src="form.icon" class="h-12 w-12 object-contain" />
                <component v-else :is="getIcon(form.icon || 'help-circle')" class="h-10 w-10 text-slate-500 group-hover:text-blue-500 transition-colors" />
                
                <div class="absolute -bottom-2 -right-2 bg-blue-600 text-white p-1.5 rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity">
                    <Pencil class="w-3 h-3" />
                </div>
            </Button>

            <!-- Icon Picker Popover -->
            <Popover ref="iconPopover" :pt="{ content: 'p-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl w-[320px] overflow-hidden' }">
                <div class="mb-3">
                    <IconField class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                        <InputIcon><Search class="w-3.5 h-3.5 text-slate-400" /></InputIcon>
                        <InputText v-model="iconSearch" placeholder="Search icons or categories..." class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full p-0" />
                    </IconField>
                </div>
                <div class="max-h-[360px] overflow-y-auto overflow-x-hidden pr-1 custom-scrollbar">
                    <div v-for="(icons, category) in groupedIcons" :key="category" class="mb-5">
                        <h4 class="text-[9px] font-black uppercase tracking-[0.15em] text-slate-400 mb-2.5 px-1">{{ category }}</h4>
                        <div class="grid grid-cols-4 gap-2">
                            <button v-for="icon in icons" :key="icon.name" type="button"
                                @click="form.icon = icon.name; iconPopover.hide()"
                                class="group/item relative flex flex-col items-center gap-1.5 p-2 rounded-xl transition-all border-none cursor-pointer"
                                :class="form.icon === icon.name ? 'bg-blue-600 text-white shadow-lg' : 'hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 bg-transparent'">
                                <div class="h-8 w-8 flex items-center justify-center">
                                    <img v-if="icon.name.startsWith('/static/')" :src="icon.name" class="h-6 w-6 object-contain" />
                                    <component v-else :is="getIcon(icon.name)" class="h-6 w-6" />
                                </div>
                                <span class="text-[8px] font-bold truncate w-full text-center px-0.5 opacity-80 group-hover/item:opacity-100">
                                    {{ icon.label }}
                                </span>
                            </button>
                        </div>
                    </div>
                </div>
            </Popover>

            <!-- Brand Logo Picker Button -->
            <Button
                @click="toggleBrandIconPopover($event)"
                :pt="{ root: 'h-10 w-10 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-lg flex items-center justify-center hover:scale-110 transition-transform group overflow-hidden p-0 relative -ml-4 -mt-4 z-10 cursor-pointer' }"
            >
                <img v-if="form.brand_icon" :src="form.brand_icon" class="h-6 w-6 object-contain" />
                <div v-else class="flex flex-col items-center">
                    <component :is="getIcon('shield-question')" class="h-4 w-4 text-slate-300 group-hover:text-blue-500 transition-colors" />
                </div>
                <div class="absolute inset-0 bg-blue-600/10 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <Pencil class="w-3 h-3 text-blue-600" />
                </div>
            </Button>

            <!-- Brand Logo Popover -->
            <Popover ref="brandIconPopover" :pt="{ content: 'p-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-2xl w-[280px]' }">
                <div class="mb-3 px-1">
                    <p class="text-[9px] font-black uppercase tracking-[0.15em] text-slate-400 mb-2 px-1">Assign Brand</p>
                    <IconField class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                        <InputIcon><Search class="w-3.5 h-3.5 text-slate-400" /></InputIcon>
                        <InputText v-model="brandSearch" placeholder="Search brands..." class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full p-0" />
                    </IconField>
                </div>
                <div class="max-h-[280px] overflow-y-auto pr-1 custom-scrollbar">
                    <div class="grid grid-cols-2 gap-2">
                        <button type="button" @click="form.brand = ''; form.brand_icon = ''; brandIconPopover.hide()"
                            class="flex items-center gap-2 p-2 rounded-xl border border-dashed border-slate-200 dark:border-slate-700 hover:border-blue-500 transition-all text-left bg-transparent cursor-pointer">
                            <div class="w-8 h-8 rounded-lg bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
                                <X class="w-4 h-4 text-slate-400" />
                            </div>
                            <span class="text-[10px] font-bold text-slate-500">None</span>
                        </button>
                        <button v-for="brand in filteredBrands" :key="brand.id" type="button"
                            @click="form.brand = brand.name; form.brand_icon = brand.path; brandIconPopover.hide()"
                            class="flex items-center gap-2 p-2 rounded-xl border transition-all text-left bg-transparent cursor-pointer"
                            :class="form.brand === brand.name ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-transparent hover:bg-slate-50 dark:hover:bg-slate-900/50'">
                            <img :src="brand.path" class="w-8 h-8 object-contain rounded-lg bg-white p-1" />
                            <span class="text-[10px] font-black truncate text-slate-700 dark:text-slate-200">{{ brand.name }}</span>
                        </button>
                    </div>
                </div>
            </Popover>
            
            <div class="w-full px-8 text-center mt-4">
                <input v-model="form.display_name" type="text"
                    class="w-full bg-transparent border-none text-xl font-black text-slate-900 dark:text-white text-center focus:ring-0 placeholder:text-slate-300"
                    placeholder="Enter device name..." />
                <p class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mt-1">Device Configuration</p>
            </div>
        </div>

        <form @submit.prevent="saveDevice" class="space-y-6">
            <!-- IP Address (Read Only) -->
            <div>
                <label class="block text-xs font-black uppercase tracking-widest text-slate-400 dark:text-slate-500 ml-1">IP Address</label>
                <p class="mt-1 text-sm text-slate-700 dark:text-slate-300 font-mono font-bold pl-1">{{ device.ip }}</p>
            </div>

            <!-- Device Category -->
            <div class="space-y-1.5 flex flex-col">
                <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500 ml-1">Device Category</label>
                <Button
                    @click="toggleCategoryPopover($event)"
                    severity="secondary"
                    text
                    outlined
                    :pt="{ root: 'w-full flex items-center justify-between px-4 py-3 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-2xl text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all group cursor-pointer' }"
                >
                    <div class="flex items-center gap-3">
                        <component :is="getIcon(form.device_type)" class="w-5 h-5 text-blue-500" />
                        <span class="text-sm font-medium">{{ form.device_type || 'Select Category' }}</span>
                    </div>
                    <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200" />
                </Button>

                <Popover ref="categoryPopover" :pt="{ content: 'w-[320px] bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-xl overflow-hidden focus:outline-none p-2' }">
                    <div class="p-1 border-b border-slate-100 dark:border-slate-700/50 mb-2">
                        <IconField class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                            <InputIcon><Search class="w-3.5 h-3.5 text-slate-400" /></InputIcon>
                            <InputText v-model="categorySearch" placeholder="Search categories..." class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full p-0" />
                        </IconField>
                    </div>
                    <div class="max-h-48 overflow-y-auto custom-scrollbar p-1">
                        <button v-for="type in filteredDeviceTypes" :key="type"
                            type="button" @click="form.device_type = type; categoryPopover.hide()"
                            class="w-full flex items-center px-4 py-2.5 text-sm text-left rounded-xl hover:bg-blue-600 hover:text-white transition-colors border-none bg-transparent cursor-pointer"
                            :class="form.device_type === type ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                            {{ type }}
                        </button>
                    </div>
                </Popover>
            </div>

            <!-- Brand Selection -->
            <div class="space-y-1.5 flex flex-col">
                <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500 ml-1">Manufacturer / Brand</label>
                <Button
                    @click="toggleBrandPopover($event)"
                    severity="secondary"
                    text
                    outlined
                    :pt="{ root: 'w-full flex items-center justify-between px-4 py-3 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-2xl text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all group cursor-pointer' }"
                >
                    <div class="flex items-center gap-3">
                        <div class="w-6 h-6 rounded-lg bg-white flex items-center justify-center border border-slate-100 overflow-hidden shrink-0">
                            <img v-if="form.brand_icon" :src="form.brand_icon" class="w-full h-full object-contain" />
                            <div v-else class="text-[8px] font-bold text-slate-300">N/A</div>
                        </div>
                        <span class="text-sm font-medium">{{ form.brand || 'Select or type brand...' }}</span>
                    </div>
                    <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200" />
                </Button>

                <Popover ref="brandPopover" :pt="{ content: 'w-[320px] bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-xl overflow-hidden focus:outline-none p-2' }">
                    <div class="p-1 border-b border-slate-100 dark:border-slate-700/50 mb-2">
                        <IconField class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                            <InputIcon><Search class="w-3.5 h-3.5 text-slate-400" /></InputIcon>
                            <InputText v-model="brandSearch" placeholder="Search brand or type new..." class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full p-0" />
                        </IconField>
                    </div>
                    <div class="max-h-48 overflow-y-auto custom-scrollbar p-1">
                        <button v-for="brand in filteredBrands" :key="brand.id"
                            type="button" @click="form.brand = brand.name; form.brand_icon = brand.path; brandPopover.hide()"
                            class="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left rounded-xl hover:bg-blue-600 hover:text-white transition-colors border-none bg-transparent cursor-pointer"
                            :class="form.brand === brand.name ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                            <img :src="brand.path" class="w-6 h-6 object-contain rounded bg-white p-0.5" />
                            {{ brand.name }}
                        </button>
                        <div v-if="brandSearch && !filteredBrands.length" class="p-4 text-center">
                            <p class="text-xs text-slate-500 mb-2">No matching brand found.</p>
                            <button type="button" @click="form.brand = brandSearch; brandPopover.hide()"
                                class="text-xs font-bold text-blue-600 hover:underline border-none bg-transparent cursor-pointer">
                                Use "{{ brandSearch }}" as custom name
                            </button>
                        </div>
                    </div>
                </Popover>
            </div>

            <!-- Parent Device Selection -->
            <div class="space-y-1.5 flex flex-col">
                <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-500 ml-1">Connected Via (Parent)</label>
                <Button
                    @click="toggleParentPopover($event)"
                    severity="secondary"
                    text
                    outlined
                    :pt="{ root: 'w-full flex items-center justify-between px-4 py-3 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-2xl text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all group cursor-pointer' }"
                >
                    <span class="text-sm font-medium truncate">{{ getParentLabel }}</span>
                    <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200" />
                </Button>

                <Popover ref="parentPopover" :pt="{ content: 'w-[320px] bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-xl overflow-hidden focus:outline-none p-2' }">
                    <div class="p-1 border-b border-slate-100 dark:border-slate-700/50 mb-2">
                        <IconField class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                            <InputIcon><Search class="w-3.5 h-3.5 text-slate-400" /></InputIcon>
                            <InputText v-model="parentSearch" placeholder="Search devices..." class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full p-0" />
                        </IconField>
                    </div>
                    <div class="max-h-48 overflow-y-auto custom-scrollbar p-1">
                        <button type="button" @click="form.parent_id = null; parentPopover.hide()"
                            class="w-full flex items-center px-4 py-2.5 text-sm text-left rounded-xl hover:bg-blue-600 hover:text-white transition-colors border-none bg-transparent cursor-pointer"
                            :class="!form.parent_id ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                            Main Gateway (Default)
                        </button>
                        <button v-for="d in filteredPotentialParents" :key="d.id"
                            type="button" @click="form.parent_id = d.id; parentPopover.hide()"
                            class="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-left rounded-xl hover:bg-blue-600 hover:text-white transition-colors border-none bg-transparent cursor-pointer"
                            :class="form.parent_id === d.id ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                            <component :is="getIcon(d.icon)" class="w-4 h-4 mr-3 opacity-70" />
                            <span class="truncate">{{ d.display_name || d.name || d.ip }}</span>
                        </button>
                    </div>
                </Popover>
            </div>

            <!-- Footer Controls -->
            <div class="mt-6 flex justify-end gap-3">
                <Button 
                    label="Cancel" 
                    severity="secondary" 
                    text 
                    @click="closeModal"
                    :disabled="isSaving"
                    :pt="{ root: 'px-4 py-2 rounded-lg text-sm font-semibold hover:bg-slate-100 dark:hover:bg-slate-700/50 border-none cursor-pointer bg-transparent text-slate-700 dark:text-slate-300' }"
                />
                <Button 
                    :label="isSaving ? 'Saving...' : 'Save Changes'" 
                    severity="primary" 
                    :loading="isSaving" 
                    type="submit"
                    :pt="{ root: 'px-4 py-2 rounded-lg text-sm font-semibold shadow-sm flex items-center gap-2 border-none bg-blue-600 hover:bg-blue-750 text-white cursor-pointer' }"
                />
            </div>
        </form>
    </Dialog>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import Dialog from 'primevue/dialog'
import Popover from 'primevue/popover'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import {
    Search,
    ChevronDown,
    Loader2,
    Pencil,
    X
} from 'lucide-vue-next'
import api from '@/utils/api'
import { getIcon } from '@/utils/icons'
import { useNotifications } from '@/composables/useNotifications'
import { useSystemStore } from '@/stores/system'

const systemStore = useSystemStore()

const props = defineProps({
    isOpen: Boolean,
    device: Object
})

const emit = defineEmits(['close', 'save'])

const isSaving = ref(false)
const allDevices = ref([])
const parentSearch = ref('')

const iconPopover = ref(null)
const brandIconPopover = ref(null)
const categoryPopover = ref(null)
const brandPopover = ref(null)
const parentPopover = ref(null)

const toggleIconPopover = (event) => iconPopover.value.toggle(event)
const toggleBrandIconPopover = (event) => brandIconPopover.value.toggle(event)
const toggleCategoryPopover = (event) => categoryPopover.value.toggle(event)
const toggleBrandPopover = (event) => brandPopover.value.toggle(event)
const toggleParentPopover = (event) => parentPopover.value.toggle(event)

const { notifySuccess, notifyError } = useNotifications()

const form = ref({
    display_name: '',
    device_type: '',
    icon: '',
    brand: '',
    brand_icon: '',
    parent_id: null
})

const categorySearch = ref('')
const iconSearch = ref('')
const brandSearch = ref('')

const visible = computed({
    get: () => props.isOpen,
    set: (value) => {
        if (!value) {
            closeModal()
        }
    }
})

const deviceTypes = computed(() => systemStore.deviceTypes)
const availableIcons = computed(() => systemStore.availableIcons)

const filteredDeviceTypes = computed(() => {
    if (!categorySearch.value) return deviceTypes.value
    return deviceTypes.value.filter(t => t.toLowerCase().includes(categorySearch.value.toLowerCase()))
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
    if (!brandSearch.value) return registry
    const s = brandSearch.value.toLowerCase()
    return registry.filter(b => b.name.toLowerCase().includes(s))
})

const filteredPotentialParents = computed(() => {
    const others = allDevices.value.filter(d => d.id !== props.device?.id)
    if (!parentSearch.value) return others
    const s = parentSearch.value.toLowerCase()
    return others.filter(d =>
        (d.display_name || '').toLowerCase().includes(s) ||
        (d.name || '').toLowerCase().includes(s) ||
        (d.ip || '').includes(s)
    )
})

const getParentLabel = computed(() => {
    if (!form.value.parent_id) return 'Main Gateway (Default)'
    const p = allDevices.value.find(d => d.id === form.value.parent_id)
    return p ? (p.display_name || p.name || p.ip) : 'Unknown Device'
})

watch(() => form.value.device_type, (newType) => {
    if (newType && systemStore.iconMap[newType]) {
        form.value.icon = systemStore.iconMap[newType]
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
