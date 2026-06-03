<template>
    <Dialog v-model:visible="visible" modal :draggable="false" :pt="{
        root: 'rounded-2xl border border-slate-800/80 bg-slate-950/95 backdrop-blur-md shadow-2xl p-0 overflow-hidden max-w-[95vw] w-[850px] h-[580px] flex flex-col outline-none focus:outline-none',
        header: 'flex items-center justify-between px-6 py-4 bg-slate-950 border-b border-slate-900 shrink-0',
        content: 'flex-1 p-0 bg-slate-950 flex flex-col min-h-0 outline-none focus:outline-none'
    }">
        <template #header>
            <div class="flex items-center justify-between w-full pr-4">
                <div class="flex items-center space-x-2">
                    <TerminalIcon class="w-4.5 h-4.5 text-sky-400" />
                    <span class="text-xs font-semibold text-slate-200 font-mono tracking-tight">
                        {{ username || 'root' }}@{{ device.ip }}
                    </span>
                </div>
                
                <!-- Status indicator & controls -->
                <div class="flex items-center space-x-3">
                    <span v-if="connecting" class="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-[10px] font-bold text-amber-400 tracking-wide uppercase font-mono">
                        <Loader2 class="w-2.5 h-2.5 animate-spin" />
                        <span>Connecting</span>
                    </span>
                    <span v-else-if="connected" class="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-bold text-emerald-400 tracking-wide uppercase font-mono">
                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                        <span>Online</span>
                    </span>
                    <span v-else-if="terminalActive" class="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-rose-500/10 border border-rose-500/20 text-[10px] font-bold text-rose-400 tracking-wide uppercase font-mono">
                        <span class="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
                        <span>Disconnected</span>
                    </span>

                    <div v-if="terminalActive" class="flex items-center space-x-1.5">
                        <button @click="copyTerminalText" class="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700 transition-colors cursor-pointer" title="Copy Screen Text">
                            <component :is="copied ? Check : Copy" class="w-3.5 h-3.5" :class="{'text-emerald-400': copied}" />
                        </button>
                        <button @click="clearTerminal" class="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700 transition-colors cursor-pointer" title="Clear Terminal">
                            <Trash2 class="w-3.5 h-3.5" />
                        </button>
                        <button @click="closeConnection" class="p-1.5 rounded-lg bg-rose-950/30 border border-rose-900/30 text-rose-400 hover:bg-rose-900/20 hover:text-rose-300 transition-all cursor-pointer" title="Disconnect">
                            <Power class="w-3.5 h-3.5" />
                        </button>
                    </div>
                </div>
            </div>
        </template>

        <!-- Auth Form -->
        <div v-if="!connected && !terminalActive"
            class="flex-1 flex items-center justify-center p-6 min-h-0 bg-slate-950/40 backdrop-blur-md">
            <div class="w-full max-w-sm p-6 rounded-2xl border border-slate-900 bg-slate-900/50 shadow-2xl space-y-5">
                <div class="text-center space-y-1.5">
                    <div class="inline-flex p-3 rounded-2xl bg-sky-500/10 border border-sky-500/20 text-sky-400 mb-2">
                        <TerminalIcon class="w-6 h-6 animate-pulse" />
                    </div>
                    <h3 class="text-white text-lg font-bold font-mono tracking-tight">Establish SSH Session</h3>
                    <p class="text-[10px] text-slate-400 font-mono">Connecting to {{ device.display_name || device.name || device.ip }}</p>
                </div>
                
                <div class="space-y-4">
                    <div class="space-y-1.5">
                        <label class="block text-[10px] font-black uppercase tracking-wider text-slate-500 ml-1">Username</label>
                        <div class="relative flex items-center">
                            <span class="absolute left-3 text-slate-500">
                                <User class="w-4 h-4" />
                            </span>
                            <input v-model="username" type="text"
                                class="w-full bg-slate-950/80 border border-slate-800 hover:border-slate-700 focus:border-blue-500 rounded-xl py-2.5 pl-10 pr-4 text-xs text-white placeholder-slate-600 outline-none transition-all font-mono"
                                placeholder="e.g. root or pi" />
                        </div>
                    </div>
                    
                    <div class="space-y-1.5">
                        <label class="block text-[10px] font-black uppercase tracking-wider text-slate-500 ml-1">Password</label>
                        <div class="relative flex items-center">
                            <span class="absolute left-3 text-slate-500">
                                <Lock class="w-4 h-4" />
                            </span>
                            <input v-model="password" type="password"
                                class="w-full bg-slate-950/80 border border-slate-800 hover:border-slate-700 focus:border-blue-500 rounded-xl py-2.5 pl-10 pr-4 text-xs text-white placeholder-slate-600 outline-none transition-all font-mono"
                                placeholder="••••••••" />
                        </div>
                    </div>
                </div>

                <div v-if="error" class="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center gap-2">
                    <span class="text-rose-400 font-medium text-xs font-mono">{{ error }}</span>
                </div>

                <button @click="connect" :disabled="connecting"
                    class="w-full bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 disabled:opacity-50 text-white text-xs font-bold font-mono uppercase tracking-wider py-3 rounded-xl shadow-lg shadow-sky-500/15 border-none flex items-center justify-center gap-2 cursor-pointer transition-all active:scale-[0.98]">
                    <Loader2 v-if="connecting" class="w-4 h-4 animate-spin" />
                    <span>{{ connecting ? 'Connecting...' : 'Connect Session' }}</span>
                    <ChevronRight v-if="!connecting" class="w-4 h-4" />
                </button>
                
                <p class="text-[9px] text-center text-slate-500 leading-relaxed font-mono">
                    All terminal sessions are secure and encrypted.
                </p>
            </div>
        </div>

        <!-- Terminal -->
        <div v-show="terminalActive" class="flex-grow bg-slate-950 p-4 overflow-hidden relative min-h-0">
            <div ref="terminalContainer" class="h-full w-full custom-terminal"></div>
        </div>
    </Dialog>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import Dialog from 'primevue/dialog'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'
import { 
    Terminal as TerminalIcon, 
    User, 
    Lock,
    Loader2, 
    Copy, 
    Check, 
    Trash2, 
    Power,
    ChevronRight
} from 'lucide-vue-next'

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
const copied = ref(false)

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
    terminalActive.value = true

    await nextTick()
    initTerminal()

    term.write(`\r\n\x1b[33mConnecting to ${props.device.ip}:${props.port}...\x1b[0m\r\n`)

    const token = localStorage.getItem('token')
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ssh/ws/${props.device.ip}?token=${token}`

    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
        ws.send(JSON.stringify({
            username: username.value,
            password: password.value,
            port: props.port
        }))
    }

    ws.onmessage = (event) => {
        const text = typeof event.data === 'string' ? event.data : ''
        if (text.includes('*** Connected to')) {
            connected.value = true
            connecting.value = false
        } else if (text.includes('*** Connection Failed ***')) {
            connected.value = false
            connecting.value = false
        }

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
        term.write(`\r\n\x1b[31m*** Connection Closed (${e.code}: ${e.reason || 'No reason'}) ***\x1b[0m\r\n`)
        console.error("WebSocket Close:", e)
        connected.value = false
        connecting.value = false
    }

    ws.onerror = (e) => {
        term.write('\r\n\x1b[31m*** WebSocket Error ***\x1b[0m\r\n')
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
        fontSize: 13,
        fontFamily: 'Fira Code, JetBrains Mono, Menlo, Monaco, "Courier New", monospace',
        theme: {
            background: '#020617', // Slate 950
            foreground: '#e2e8f0', // Slate 200
            cursor: '#38bdf8', // Sky 400
            cursorAccent: '#020617',
            selectionBackground: 'rgba(56, 189, 248, 0.25)',
            black: '#0f172a',
            red: '#ef4444',
            green: '#22c55e',
            yellow: '#eab308',
            blue: '#3b82f6',
            magenta: '#a855f7',
            cyan: '#06b6d4',
            white: '#cbd5e1',
            brightBlack: '#475569',
            brightRed: '#f87171',
            brightGreen: '#4ade80',
            brightYellow: '#facc15',
            brightBlue: '#60a5fa',
            brightMagenta: '#c084fc',
            brightCyan: '#22d3ee',
            brightWhite: '#f8fafc'
        },
        allowProposedApi: true
    })

    fitAddon = new FitAddon()
    term.loadAddon(fitAddon)

    term.open(terminalContainer.value)
    fitAddon.fit()

    term.write('\x1b[32mWelcome to Network Scanner SSH Console\x1b[0m\r\n')

    window.addEventListener('resize', handleResize)
}

const handleResize = () => {
    if (fitAddon) fitAddon.fit()
}

const copyTerminalText = () => {
    if (!term) return
    term.selectAll()
    const text = term.getSelection()
    term.clearSelection()
    if (text) {
        navigator.clipboard.writeText(text)
        copied.value = true
        setTimeout(() => copied.value = false, 2000)
    }
}

const clearTerminal = () => {
    if (term) {
        term.clear()
        term.focus()
    }
}

const closeConnection = () => {
    if (ws) {
        ws.close()
    }
    connected.value = false
    terminalActive.value = false
}

onUnmounted(() => {
    if (ws) ws.close()
    if (term) term.dispose()
    window.removeEventListener('resize', handleResize)
})
</script>

<style>
/* Force dark border on the PrimeVue Dialog component in dark mode */
.dark .p-dialog,
.p-dialog {
    border: 1px solid rgba(30, 41, 59, 0.8) !important; /* slate-800 */
}

.custom-terminal .xterm-viewport::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
.custom-terminal .xterm-viewport::-webkit-scrollbar-track {
    background: #020617;
}
.custom-terminal .xterm-viewport::-webkit-scrollbar-thumb {
    background: #1e293b;
    border-radius: 4px;
}
.custom-terminal .xterm-viewport::-webkit-scrollbar-thumb:hover {
    background: #334155;
}
</style>

