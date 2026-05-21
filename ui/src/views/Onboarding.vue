<template>
  <div class="min-h-screen bg-slate-50 text-slate-900 font-sans selection:bg-blue-100">
    <!-- Header -->
    <header class="max-w-6xl mx-auto px-6 py-8 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl overflow-hidden shadow-lg shadow-blue-600/20 bg-white p-1">
          <img src="/brand/icon.png" alt="IPLoom" class="w-full h-full object-contain" />
        </div>
        <h1 class="text-lg font-bold tracking-tight text-slate-900">IPLoom <span class="text-blue-600">Onboarding</span></h1>
      </div>
      <div class="flex items-center gap-4">
        <div class="px-3 py-1 rounded-full bg-white border border-slate-200 shadow-sm text-[10px] font-black uppercase tracking-widest text-slate-500">
          Step {{ currentStep }} of {{ totalSteps }}
        </div>
      </div>
    </header>

    <main class="max-w-3xl mx-auto px-6 pb-20">

      <!-- Step Content -->
      <div class="bg-white/80 backdrop-blur-xl border border-slate-200 rounded-3xl p-8 shadow-xl shadow-slate-200/50 relative overflow-hidden group">
        <!-- Decoration -->
        <div class="absolute -top-24 -right-24 w-48 h-48 bg-blue-600/5 rounded-full blur-3xl group-hover:bg-blue-600/10 transition-all duration-1000"></div>

        <!-- Step 1: Subnet (Required) -->
        <div v-if="currentStep === 1" class="animate-in">
          <div class="flex items-center gap-4 mb-8">
            <div class="w-11 h-11 rounded-2xl bg-blue-50 flex items-center justify-center overflow-hidden p-2">
              <img src="/brand/icon.png" alt="Discovery" class="w-full h-full object-contain" />
            </div>
            <div>
              <h2 class="text-xl font-bold text-slate-900">Network Discovery</h2>
              <p class="text-slate-500 text-[13px]">Define your local network range.</p>
            </div>
          </div>

          <div class="space-y-6">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div class="flex items-center justify-between mb-1.5 px-1">
                    <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest">Network Subnet</label>
                    <span v-if="isAutoDetected.subnet" class="text-[9px] text-blue-600 font-bold uppercase tracking-widest bg-blue-50 px-1.5 rounded">Auto-detected</span>
                  </div>
                  <div class="flex gap-2">
                    <input v-model="network.subnet" type="text" class="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all outline-none text-sm" placeholder="192.168.1.0/24">
                    <button @click="detectSubnet" class="px-4 bg-white border border-slate-200 rounded-xl text-slate-600 hover:text-slate-900 hover:border-slate-300 transition-all text-[10px] font-black uppercase tracking-widest shadow-sm">Refresh</button>
                  </div>
                </div>
                <div>
                  <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 px-1">Scan Interval</label>
                  <select v-model="network.interval" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all outline-none text-sm appearance-none">
                    <option :value="5">Every 5 minutes</option>
                    <option :value="10">Every 10 minutes</option>
                    <option :value="30">Every 30 minutes</option>
                    <option :value="60">Every hour</option>
                    <option :value="1440">Once per day</option>
                  </select>
                </div>
              </div>
            
          </div>
        </div>

        <!-- Step 2: OpenWRT -->
        <div v-if="currentStep === 2" class="animate-in">
          <div class="flex items-center justify-between mb-8">
            <div class="flex items-center gap-4">
              <div class="w-11 h-11 rounded-2xl bg-teal-50 flex items-center justify-center overflow-hidden p-2">
                <img src="/brand/openwrt.png" alt="OpenWrt" class="w-full h-full object-contain" />
              </div>
              <div>
                <h2 class="text-xl font-bold text-slate-900">Router Integration</h2>
                <p class="text-slate-500 text-[13px]">OpenWRT traffic monitoring.</p>
              </div>
            </div>
            <button @click="toggleSkip('openwrt')" :class="skippedSteps['openwrt'] ? 'bg-teal-50 text-teal-600 border-teal-200' : 'bg-white border-slate-200 text-slate-400 hover:text-slate-600'" class="px-3 py-1 rounded-lg border text-[10px] font-black uppercase tracking-widest transition-all shadow-sm">
              {{ skippedSteps['openwrt'] ? 'Skipped' : 'Skip Step' }}
            </button>
          </div>

          <div :class="{ 'opacity-40 grayscale pointer-events-none transition-all': skippedSteps['openwrt'] }" class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
               <div>
                  <div class="flex items-center justify-between mb-1.5 px-1">
                    <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest">Router Host</label>
                    <span v-if="isAutoDetected.openwrt" class="text-[9px] text-blue-600 font-bold uppercase tracking-widest bg-blue-50 px-1.5 rounded">Auto-detected</span>
                  </div>
                  <input v-model="openwrt.host" type="text" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all outline-none text-sm" placeholder="192.168.1.1">
              </div>
              <div>
                <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 px-1">SSH Port</label>
                <input v-model="openwrt.port" type="number" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all outline-none text-sm" placeholder="22">
              </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 px-1">Username</label>
                <input v-model="openwrt.user" type="text" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all outline-none text-sm" placeholder="root">
              </div>
              <div>
                <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 px-1">Password</label>
                <input v-model="openwrt.pass" type="password" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all outline-none text-sm" placeholder="••••••••">
              </div>
            </div>

            <!-- Access Point Toggle -->
            <div class="flex items-center justify-between p-3.5 bg-slate-50 border border-slate-200 rounded-2xl mt-4">
              <div>
                <div class="text-xs font-bold text-slate-800">Use as Wireless Access Point</div>
                <div class="text-[10px] text-slate-400 font-medium">Query OpenWRT's radios for Wi-Fi clients, RSSI, and bands</div>
              </div>
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" v-model="openwrt.is_access_point" class="sr-only peer">
                <div class="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-teal-500"></div>
              </label>
            </div>
          </div>
        </div>

        <!-- Step 3: AdGuard -->
        <div v-if="currentStep === 3" class="animate-in">
          <div class="flex items-center justify-between mb-8">
            <div class="flex items-center gap-4">
              <div class="w-11 h-11 rounded-2xl bg-green-50 flex items-center justify-center overflow-hidden p-2">
                <img src="/brand/adguard.png" alt="AdGuard" class="w-full h-full object-contain" />
              </div>
              <div>
                <h2 class="text-xl font-bold text-slate-900">AdGuard Home</h2>
                <p class="text-slate-500 text-[13px]">DNS filtering & protection.</p>
              </div>
            </div>
            <button @click="toggleSkip('adguard')" :class="skippedSteps['adguard'] ? 'bg-green-50 text-green-600 border-green-200' : 'bg-white border-slate-200 text-slate-400 hover:text-slate-600'" class="px-3 py-1 rounded-lg border text-[10px] font-black uppercase tracking-widest transition-all shadow-sm">
              {{ skippedSteps['adguard'] ? 'Skipped' : 'Skip Step' }}
            </button>
          </div>

          <div :class="{ 'opacity-40 grayscale pointer-events-none transition-all': skippedSteps['adguard'] }" class="space-y-5">
            <div>
              <div class="flex items-center justify-between mb-1.5 px-1">
                <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest">AdGuard URL</label>
                <span v-if="isAutoDetected.adguard" class="text-[9px] text-blue-600 font-bold uppercase tracking-widest bg-blue-50 px-1.5 rounded">Auto-detected</span>
              </div>
              <input v-model="adguard.url" type="text" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all outline-none text-sm" placeholder="http://192.168.1.5:8080">
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 px-1">Username</label>
                <input v-model="adguard.user" type="text" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all outline-none text-sm" placeholder="admin">
              </div>
              <div>
                <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 px-1">Password</label>
                <input v-model="adguard.pass" type="password" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all outline-none text-sm" placeholder="••••••••">
              </div>
            </div>
          </div>
        </div>

        <!-- Step 4: TP-Link Deco Mesh -->
        <div v-if="currentStep === 4" class="animate-in">
          <div class="flex items-center justify-between mb-8">
            <div class="flex items-center gap-4">
              <div class="w-11 h-11 rounded-2xl bg-teal-50 flex items-center justify-center overflow-hidden p-2">
                <svg viewBox="0 0 24 24" class="w-full h-full text-teal-600 shrink-0" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 20a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z" />
                  <path d="M12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12Z" />
                  <path d="M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" />
                </svg>
              </div>
              <div>
                <h2 class="text-xl font-bold text-slate-900">TP-Link Deco Mesh</h2>
                <p class="text-slate-500 text-[13px]">Sync signal strength (RSSI), client nodes & bands</p>
              </div>
            </div>
            <button @click="toggleSkip('deco')" :class="skippedSteps['deco'] ? 'bg-teal-50 text-teal-600 border-teal-200' : 'bg-white border-slate-200 text-slate-400 hover:text-slate-600'" class="px-3 py-1 rounded-lg border text-[10px] font-black uppercase tracking-widest transition-all shadow-sm">
              {{ skippedSteps['deco'] ? 'Skipped' : 'Skip Step' }}
            </button>
          </div>

          <div :class="{ 'opacity-40 grayscale pointer-events-none transition-all': skippedSteps['deco'] }" class="space-y-4">
            <!-- Warning Alert -->
            <div class="p-3.5 bg-amber-50 border border-amber-200 rounded-2xl flex items-start gap-2.5">
              <svg viewBox="0 0 24 24" class="w-4 h-4 text-amber-600 shrink-0 mt-0.5" fill="none" stroke="currentColor" stroke-width="2">
                <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
              <div class="text-[10px] text-amber-800 leading-normal font-medium">
                <strong>Admin Session Restriction:</strong> TP-Link Deco only supports a single active administrator session. Running background syncs may temporarily sign you out of the official Deco mobile app.
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 px-1">Deco Host / IP</label>
                <input v-model="deco.host" type="text" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all outline-none text-sm" placeholder="192.168.1.1">
              </div>
              <div>
                <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 px-1">Password</label>
                <input v-model="deco.pass" type="password" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all outline-none text-sm" placeholder="••••••••">
              </div>
            </div>
          </div>
        </div>

        <!-- Step 5: MQTT -->
        <div v-if="currentStep === 5" class="animate-in">
          <div class="flex items-center justify-between mb-8">
            <div class="flex items-center gap-4">
              <div class="w-11 h-11 rounded-2xl bg-orange-50 flex items-center justify-center overflow-hidden p-2">
                <img src="/brand/mqtt.png" alt="MQTT" class="w-full h-full object-contain" />
              </div>
              <div>
                <h2 class="text-xl font-bold text-slate-900">MQTT Broker</h2>
                <p class="text-slate-500 text-[13px]">Real-time device communication.</p>
              </div>
            </div>
            <button @click="toggleSkip('mqtt')" :class="skippedSteps['mqtt'] ? 'bg-orange-50 text-orange-600 border-orange-200' : 'bg-white border-slate-200 text-slate-400 hover:text-slate-600'" class="px-3 py-1 rounded-lg border text-[10px] font-black uppercase tracking-widest transition-all shadow-sm">
              {{ skippedSteps['mqtt'] ? 'Skipped' : 'Skip Step' }}
            </button>
          </div>

          <div :class="{ 'opacity-40 grayscale pointer-events-none transition-all': skippedSteps['mqtt'] }">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div class="space-y-4">
                <div>
                  <div class="flex items-center justify-between mb-1.5 px-1">
                    <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest">Broker Host</label>
                    <span v-if="isAutoDetected.mqtt" class="text-[9px] text-blue-600 font-bold uppercase tracking-widest bg-blue-50 px-1.5 rounded">Auto-detected</span>
                  </div>
                  <input v-model="mqtt.host" type="text" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all outline-none text-sm" placeholder="192.168.1.10">
                </div>
                <div>
                  <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 px-1">Port</label>
                  <input v-model="mqtt.port" type="number" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all outline-none text-sm" placeholder="1883">
                </div>
              </div>
              <div class="space-y-4">
                <div>
                  <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 px-1">Username</label>
                  <input v-model="mqtt.user" type="text" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all outline-none text-sm" placeholder="Optional">
                </div>
                <div>
                  <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 px-1">Password</label>
                  <input v-model="mqtt.pass" type="password" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all outline-none text-sm" placeholder="••••••••">
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 6: Welcome / Summary -->
        <div v-if="currentStep === 6" class="animate-in text-center py-4">
          <div class="w-20 h-20 rounded-full bg-blue-50 flex items-center justify-center mx-auto mb-6 overflow-hidden p-4 shadow-inner">
            <img src="/brand/icon.png" alt="Ready" class="w-full h-full object-contain" />
          </div>
          <h2 class="text-2xl font-bold text-slate-900 mb-2">Ready to Launch!</h2>
          <p class="text-slate-500 text-[14px] mb-10">Review your configuration before we finalize everything.</p>

          <div class="grid grid-cols-2 gap-3 text-left max-w-md mx-auto">
            <div class="p-4 rounded-2xl bg-slate-50 border border-slate-100">
              <label class="block text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Network</label>
              <div class="text-[13px] font-bold text-slate-900">{{ network.subnet }}</div>
              <div class="text-[10px] text-slate-400 font-medium mt-1">Automatic discovery enabled</div>
            </div>
            <div class="p-4 rounded-2xl bg-slate-50 border border-slate-100">
              <label class="block text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Router</label>
              <div v-if="!skippedSteps['openwrt']" class="text-[13px] font-bold text-slate-900 truncate">{{ openwrt.host }}</div>
              <div v-else class="text-[13px] font-bold text-slate-300 italic">Skipped</div>
            </div>
            <div class="p-4 rounded-2xl bg-slate-50 border border-slate-100">
              <label class="block text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">AdGuard</label>
              <div v-if="!skippedSteps['adguard']" class="text-[13px] font-bold text-slate-900 truncate">{{ adguard.url }}</div>
              <div v-else class="text-[13px] font-bold text-slate-300 italic">Skipped</div>
            </div>
            <div class="p-4 rounded-2xl bg-slate-50 border border-slate-100">
              <label class="block text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Deco Mesh</label>
              <div v-if="!skippedSteps['deco']" class="text-[13px] font-bold text-slate-900 truncate">{{ deco.host }}</div>
              <div v-else class="text-[13px] font-bold text-slate-300 italic">Skipped</div>
            </div>
            <div class="p-4 rounded-2xl bg-slate-50 border border-slate-100 col-span-2">
              <label class="block text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">MQTT</label>
              <div v-if="!skippedSteps['mqtt']" class="text-[13px] font-bold text-slate-900 truncate">{{ mqtt.host }}</div>
              <div v-else class="text-[13px] font-bold text-slate-300 italic">Skipped</div>
            </div>
          </div>
        </div>

        <!-- Navigation Buttons -->
        <div class="flex items-center justify-between mt-10 pt-8 border-t border-slate-100">
          <button 
            @click="prevStep" 
            class="px-6 py-2.5 rounded-xl border border-slate-200 text-slate-400 font-bold text-[11px] uppercase tracking-widest hover:bg-slate-50 hover:text-slate-600 hover:border-slate-300 transition-all flex items-center gap-2 shadow-sm"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" /></svg>
            {{ currentStep === 1 ? 'Back to Login' : 'Back' }}
          </button>
          <div></div>

          <button 
            @click="nextStep"
            :disabled="saving || !canContinue"
            class="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-black rounded-xl shadow-lg shadow-blue-600/20 transform transition-all active:scale-[0.98] flex items-center gap-2 disabled:opacity-30 disabled:cursor-not-allowed text-[11px] uppercase tracking-widest"
          >
            <span v-if="saving" class="animate-spin h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full"></span>
            {{ currentStep === totalSteps ? 'Launch Dashboard' : 'Continue' }}
            <svg v-if="currentStep < totalSteps" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" /></svg>
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import api from '@/utils/api'

const router = useRouter()
const authStore = useAuthStore()

const currentStep = ref(1)
const totalSteps = 6
const saving = ref(false)
const skippedSteps = ref({})

const mqtt = ref({ host: '', port: 1883, user: '', pass: '' })
const openwrt = ref({ host: '', port: 22, user: 'root', pass: '', is_access_point: true })
const adguard = ref({ url: '', user: 'admin', pass: '' })
const deco = ref({ host: '', pass: '' })
const network = ref({ subnet: '', interval: 5, autoScan: true })

const isAutoDetected = ref({
  mqtt: false,
  openwrt: false,
  adguard: false,
  subnet: false
})

const canContinue = computed(() => {
  if (currentStep.value === 1) return network.value.subnet
  if (currentStep.value === 2) return skippedSteps.value['openwrt'] || (openwrt.value.host && openwrt.value.port && openwrt.value.user && openwrt.value.pass)
  if (currentStep.value === 3) return skippedSteps.value['adguard'] || (adguard.value.url && adguard.value.user && adguard.value.pass)
  if (currentStep.value === 4) return skippedSteps.value['deco'] || (deco.value.host && deco.value.pass)
  if (currentStep.value === 5) return skippedSteps.value['mqtt'] || (mqtt.value.host && mqtt.value.port)
  return true
})

onMounted(async () => {
  await detectSubnet()
})

const toggleSkip = (step) => {
  skippedSteps.value[step] = !skippedSteps.value[step]
}

const detectSubnet = async () => {
  try {
    const res = await api.get('/config/discover')
    const d = res.data
    
    if (d.subnet) {
      network.value.subnet = d.subnet
      isAutoDetected.value.subnet = true
    }
    
    if (d.mqtt_host && !mqtt.value.host) {
      mqtt.value.host = d.mqtt_host
      isAutoDetected.value.mqtt = true
    }
    
    if (d.openwrt_host && !openwrt.value.host) {
      openwrt.value.host = d.openwrt_host
      isAutoDetected.value.openwrt = true
    }
    
    if (d.adguard_url && !adguard.value.url) {
      adguard.value.url = d.adguard_url
      isAutoDetected.value.adguard = true
    }

    // Auto-detect Deco from gateway ip if OpenWrt detected it
    if (d.openwrt_host && !deco.value.host) {
      deco.value.host = d.openwrt_host
    }
  } catch (err) {
    console.error('Auto-discovery failed', err)
  }
}

const nextStep = async () => {
  if (currentStep.value < totalSteps) {
    currentStep.value++
  } else {
    await finishOnboarding()
  }
}

const prevStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--
  } else {
    authStore.logout()
    router.push('/login')
  }
}

const finishOnboarding = async () => {
  saving.value = true
  try {
    // Save Subnet (Required for UI)
    await api.put('/config/default_subnet', { value: network.value.subnet })
    
    // Save Background Scan Config
    await api.put('/config/scan_subnets', { value: JSON.stringify([network.value.subnet]) })
    await api.put('/config/scan_interval', { value: String(network.value.interval * 60) })

    // Save OpenWRT Config if not skipped
    if (!skippedSteps.value['openwrt']) {
      await api.post('/integrations/openwrt/config', {
        url: `http://${openwrt.value.host}`,
        username: openwrt.value.user,
        password: openwrt.value.pass,
        interval: 15,
        is_access_point: openwrt.value.is_access_point
      })
    }

    // Save AdGuard Config if not skipped
    if (!skippedSteps.value['adguard']) {
      await api.post('/integrations/adguard/config', {
        url: adguard.value.url,
        username: adguard.value.user,
        password: adguard.value.pass,
        interval: 5
      })
    }

    // Save Deco Config if not skipped
    if (!skippedSteps.value['deco']) {
      await api.post('/integrations/deco/config', {
        host: deco.value.host,
        password: deco.value.pass,
        interval: 15,
        enabled: true
      })
    }

    // Save MQTT Config if not skipped
    if (!skippedSteps.value['mqtt']) {
      await api.post('/config/', {
        mqtt_broker: mqtt.value.host,
        mqtt_port: String(mqtt.value.port),
        mqtt_username: mqtt.value.user,
        mqtt_password: mqtt.value.pass
      })
    }

    // MANDATORY initial scan
    await api.post('/scans/', {
      target: network.value.subnet,
      scan_type: 'arp'
    })

    // Mark onboarding as complete
    await authStore.completeOnboarding()
    
    // Redirect to home
    router.push('/')
  } catch (err) {
    console.error('Failed to complete onboarding', err)
    alert('Failed to save settings. Please try again.')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.animate-in {
  animation: fadeInZoom 0.4s ease-out forwards;
}
@keyframes fadeInZoom {
  from { opacity: 0; transform: scale(0.98) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
</style>
