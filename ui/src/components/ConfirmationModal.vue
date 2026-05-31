<template>
  <v-dialog v-model="internalIsOpen" max-width="400" persistent @click:outside="close">
    <v-card rounded="lg">
      <v-card-title class="d-flex align-center pt-4">
        <v-avatar :color="type === 'danger' ? 'error-lighten-4' : 'primary-lighten-4'" size="40" class="mr-4">
          <component :is="type === 'danger' ? AlertTriangle : Info" :class="type === 'danger' ? 'text-error' : 'text-primary'" class="w-6 h-6" />
        </v-avatar>
        <span class="text-h6 font-weight-bold">{{ title }}</span>
      </v-card-title>

      <v-card-text class="pt-2 text-body-2 text-medium-emphasis">
        {{ message }}
      </v-card-text>

      <v-card-actions class="px-4 pb-4">
        <v-spacer></v-spacer>
        <v-btn variant="text" color="medium-emphasis" @click="close">
          Cancel
        </v-btn>
        <v-btn :color="type === 'danger' ? 'error' : 'primary'" variant="flat" :loading="loading" @click="confirm" class="px-4">
          {{ confirmText }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { computed } from 'vue'
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
        default: 'primary',
        validator: (value) => ['primary', 'danger'].includes(value)
    },
    loading: {
        type: Boolean,
        default: false
    }
})

const emit = defineEmits(['close', 'confirm'])

const internalIsOpen = computed({
  get: () => props.isOpen,
  set: (val) => {
    if (!val) close()
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
