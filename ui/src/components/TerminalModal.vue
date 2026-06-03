<template>
    <Dialog v-model:visible="visible" modal :draggable="false" :pt="{
        root: 'rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl p-0 overflow-hidden max-w-[90vw] w-[800px] h-[550px] flex flex-col',
        header: 'flex items-center justify-between px-6 py-4 bg-slate-950 border-b border-slate-800 shrink-0',
        content: 'flex-1 p-0 bg-black flex flex-col min-h-0'
    }">
        <template #header>
            <div class="flex items-center space-x-2">
                <div class="h-3 w-3 rounded-full bg-red-500"></div>
                <div class="h-3 w-3 rounded-full bg-yellow-500"></div>
                <div class="h-3 w-3 rounded-full bg-green-500"></div>
                <span class="ml-2 text-gray-300 font-mono text-xs">ssh {{ device.ip }}</span>
            </div>
        </template>

        <!-- Auth Form -->
        <div v-if="!connected && !terminalActive"
            class="flex-1 flex items-center justify-center p-6 min-h-0 bg-slate-900">
            <div class="w-full max-w-xs space-y-4">
                <h3 class="text-white text-base font-bold text-center">SSH Credentials</h3>
                <div>
                    <label class="block text-xs font-mono text-gray-400 mb-1">Username</label>
                    <InputText v-model="username" type="text"
                        class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:border-blue-500 outline-none"
                        placeholder="pi" />
                </div>
                <div>
                    <label class="block text-xs font-mono text-gray-400 mb-1">Password</label>
                    <InputText v-model="password" type="password"
                        class="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:border-blue-500 outline-none" />
                </div>
                <Button @click="connect" :disabled="connecting" :loading="connecting" label="Connect"
                    :pt="{ root: 'w-full bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold py-2.5 rounded-lg border-none flex items-center justify-center cursor-pointer' }" />
                <p v-if="error" class="text-red-400 text-xs text-center font-semibold">{{ error }}</p>
            </div>
        </div>

        <!-- Terminal -->
        <div v-show="terminalActive" class="flex-grow bg-black p-2 overflow-hidden relative min-h-0">
            <div ref="terminalContainer" class="h-full w-full"></div>
        </div>
    </Dialog>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'

const props = defineProps({
    device: Object,
    port: {
        type: Number,
        default: 22
    }
})

const emit = defineEmits(['close'])

const visible = ref(true)
const username = ref('')
const password = ref('')
const connecting = ref(false)
const connected = ref(false)
const terminalActive = ref(false)
const error = ref('')
const terminalContainer = ref(null)

let term = null
let fitAddon = null
let ws = null

watch(visible, (newVal) => {
    if (!newVal) {
        emit('close')
    }
})

const connect = async () => {
    if (!username.value || !password.value) {
        error.value = "Username and password required"
        return
    }

    connecting.value = true
    error.value = ''

    // Switch UI immediately to terminal style logs
    terminalActive.value = true

    await nextTick()
    initTerminal()

    term.write(`\r\nConnecting to ${props.device.ip}:${props.port}...\r\n`)

    const token = localStorage.getItem('token')
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ssh/ws/${props.device.ip}?token=${token}`

    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
        // Send auth
        ws.send(JSON.stringify({
            username: username.value,
            password: password.value,
            port: props.port
        }))
    }

    ws.onmessage = (event) => {
        if (event.data instanceof Blob) {
            const reader = new FileReader()
            reader.onload = () => {
                term.write(new Uint8Array(reader.result))
            }
            reader.readAsArrayBuffer(event.data)
        } else {
            term.write(event.data)
        }
    }

    ws.onclose = (e) => {
        term.write(`\r\n*** Connection Closed (${e.code}: ${e.reason || 'No reason'}) ***\r\n`)
        console.error("WebSocket Close:", e)
        connected.value = false
        connecting.value = false
    }

    ws.onerror = (e) => {
        term.write('\r\n*** WebSocket Error ***\r\n')
        console.error("WebSocket Error:", e)
        connecting.value = false
    }

    term.onData(data => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(data)
        }
    })
}

const initTerminal = () => {
    if (term) return

    term = new Terminal({
        cursorBlink: true,
        fontSize: 14,
        fontFamily: 'Menlo, Monaco, "Courier New", monospace',
        theme: {
            background: '#000000',
        }
    })

    fitAddon = new FitAddon()
    term.loadAddon(fitAddon)

    term.open(terminalContainer.value)
    fitAddon.fit()

    term.write('Welcome to Network Scanner SSH Console\r\n')

    window.addEventListener('resize', handleResize)
}

const handleResize = () => {
    if (fitAddon) fitAddon.fit()
}

onUnmounted(() => {
    if (ws) ws.close()
    if (term) term.dispose()
    window.removeEventListener('resize', handleResize)
})
</script>
