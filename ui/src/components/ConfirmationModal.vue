<template>
    <Dialog 
        v-model:visible="visible" 
        modal 
        :closable="!loading"
        :draggable="false"
        :pt="{
            root: 'rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-2xl p-6 overflow-hidden max-w-[90vw] w-[450px]',
            header: 'flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-700/50',
            content: 'py-4 text-sm text-slate-500 dark:text-slate-400',
            footer: 'flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-700/50 mt-2'
        }"
    >
        <template #header>
            <div class="flex items-center gap-3">
                <div :class="[
                    'p-2 rounded-xl flex-shrink-0',
                    type === 'danger' ? 'bg-red-500/10 text-red-600 dark:text-red-400' : 'bg-blue-500/10 text-blue-600 dark:text-blue-400'
                ]">
                    <component :is="type === 'danger' ? AlertTriangle : Info" class="w-5 h-5" />
                </div>
                <span class="text-base font-bold text-slate-900 dark:text-white">{{ title }}</span>
            </div>
        </template>

        <div class="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
            <slot>{{ message }}</slot>
        </div>

        <template #footer>
            <Button 
                label="Cancel" 
                severity="secondary" 
                text 
                @click="close"
                :disabled="loading"
                :pt="{ root: 'px-4 py-2 rounded-lg text-sm font-semibold hover:bg-slate-100 dark:hover:bg-slate-700/50 border-none' }"
            />
            <Button 
                :label="confirmText" 
                :severity="type === 'danger' ? 'danger' : 'primary'" 
                :loading="loading" 
                @click="confirm"
                :pt="{ 
                    root: 'px-4 py-2 rounded-lg text-sm font-semibold shadow-sm flex items-center gap-2 border-none ' + 
                    (type === 'danger' ? 'bg-red-600 hover:bg-red-750 text-white' : 'bg-blue-600 hover:bg-blue-750 text-white')
                }"
            />
        </template>
    </Dialog>
</template>

<script setup>
import { computed } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import { AlertTriangle, Info } from 'lucide-vue-next'

const props = defineProps({
    isOpen: Boolean,
    title: {
        type: String,
        default: 'Confirmation'
    },
    message: {
        type: String,
        required: true
    },
    confirmText: {
        type: String,
        default: 'Confirm'
    },
    type: {
        type: String,
        default: 'primary', // 'primary' or 'danger'
        validator: (value) => ['primary', 'danger'].includes(value)
    },
    loading: {
        type: Boolean,
        default: false
    }
})

const emit = defineEmits(['close', 'confirm'])

const visible = computed({
    get: () => props.isOpen,
    set: (value) => {
        if (!value) {
            close()
        }
    }
})

const close = () => {
    if (!props.loading) {
        emit('close')
    }
}

const confirm = () => {
    emit('confirm')
}
</script>
