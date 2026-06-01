<template>
  <div class="space-y-6 pb-12">
    <!-- Page Header -->
    <div class="page-header">
      <div>
        <h1 class="text-2xl font-semibold text-slate-900 dark:text-white">Events Log</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">Track device connectivity and network activity trends</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="badge-live-label hidden sm:flex h-[34px]">
          <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse flex-shrink-0"></div>
          <span>{{ onlineNowCount }} Online Now</span>
        </div>
        <button @click="fetchData(); fetchStats()" class="btn-action" v-tooltip="'Refresh All'">
          <RefreshCw :class="{ 'animate-spin': loading }" class="h-4 w-4" />
        </button>
      </div>
    </div>

    <!-- Summary Stats -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- Total Events -->
      <div class="premium-card !p-5 !rounded-2xl group">
        <div class="flex items-start justify-between mb-4">
          <div class="p-2.5 bg-blue-500/10 rounded-xl">
            <Activity class="h-4 w-4 text-blue-500" />
          </div>
          <span class="text-[9px] font-black uppercase tracking-[0.2em] text-blue-500/80 bg-blue-500/10 px-2 py-1 rounded-lg">All Time</span>
        </div>
        <div class="text-3xl font-black text-slate-900 dark:text-white tabular-nums">{{ totalEvents.toLocaleString() }}</div>
        <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mt-1">Total Events</div>
      </div>

      <!-- Online Events -->
      <div class="premium-card !p-5 !rounded-2xl group">
        <div class="flex items-start justify-between mb-4">
          <div class="p-2.5 bg-emerald-500/10 rounded-xl">
            <Wifi class="h-4 w-4 text-emerald-500" />
          </div>
          <span class="text-[9px] font-black uppercase tracking-[0.2em] text-emerald-500/80 bg-emerald-500/10 px-2 py-1 rounded-lg">Online</span>
        </div>
        <div class="text-3xl font-black text-slate-900 dark:text-white tabular-nums">{{ onlineCount.toLocaleString() }}</div>
        <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mt-1">Connect Events</div>
      </div>

      <!-- Offline Events -->
      <div class="premium-card !p-5 !rounded-2xl group">
        <div class="flex items-start justify-between mb-4">
          <div class="p-2.5 bg-red-500/10 rounded-xl">
            <WifiOff class="h-4 w-4 text-red-500" />
          </div>
          <span class="text-[9px] font-black uppercase tracking-[0.2em] text-red-500/80 bg-red-500/10 px-2 py-1 rounded-lg">Offline</span>
        </div>
        <div class="text-3xl font-black text-slate-900 dark:text-white tabular-nums">{{ offlineCount.toLocaleString() }}</div>
        <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mt-1">Disconnect Events</div>
      </div>

      <!-- Online Now -->
      <div class="premium-card !p-5 !rounded-2xl group">
        <div class="flex items-start justify-between mb-4">
          <div class="p-2.5 bg-indigo-500/10 rounded-xl">
            <Network class="h-4 w-4 text-indigo-500" />
          </div>
          <div class="flex items-center gap-1.5">
            <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
            <span class="text-[9px] font-black uppercase tracking-[0.2em] text-emerald-600 dark:text-emerald-400">Live</span>
          </div>
        </div>
        <div class="text-3xl font-black text-slate-900 dark:text-white tabular-nums">{{ onlineNowCount }}</div>
        <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mt-1">Devices Online Now</div>
      </div>
    </div>

    <!-- Trend Chart -->
    <div class="premium-card !rounded-2xl">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div class="flex items-center gap-3">
          <div class="p-2.5 bg-blue-500/10 rounded-xl">
            <BarChart2 class="h-5 w-5 text-blue-500" />
          </div>
          <div>
            <h3 class="text-base font-black text-slate-900 dark:text-white">Network Activity Trend</h3>
            <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mt-0.5">Hourly aggregation of connectivity events</p>
          </div>
        </div>
        <div class="flex bg-slate-100/80 dark:bg-slate-900/80 rounded-xl p-1 border border-slate-200/50 dark:border-slate-700/50 self-start sm:self-auto">
          <button v-for="opt in timeOptions" :key="opt.value" @click="statsTimeRange = opt.value; fetchStats()"
            class="px-4 py-1.5 text-xs font-black uppercase tracking-widest rounded-lg transition-all"
            :class="statsTimeRange === opt.value
              ? 'bg-white dark:bg-slate-800 shadow-md text-blue-600 dark:text-blue-400'
              : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'">
            {{ opt.label }}
          </button>
        </div>
      </div>
      <div class="h-64">
        <apexchart v-if="chartSeries[0].data.length > 0" type="line" height="100%" :options="chartOptions" :series="chartSeries" />
        <div v-else-if="!loadingStats" class="h-full flex flex-col items-center justify-center text-slate-400 italic gap-2">
          <ZapOff class="h-8 w-8 text-slate-300 opacity-40" />
          <span class="text-sm">No trend data for this period</span>
        </div>
        <div v-else class="h-full flex items-center justify-center">
          <Loader2 class="h-8 w-8 animate-spin text-blue-500/30" />
        </div>
      </div>
    </div>

    <!-- Filters & Events Table -->
    <div class="premium-card !rounded-2xl !p-0 overflow-hidden">
      <!-- Filter Bar -->
      <div class="px-6 py-4 border-b border-slate-100 dark:border-slate-700/50 flex flex-col md:flex-row gap-3 items-center">
        <!-- Search -->
        <div class="relative flex-1 w-full">
          <Search class="absolute left-3.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
          <input v-model="search" @input="debounceFetch" type="text" placeholder="Search IP, MAC or name..."
            class="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-700/50 rounded-xl outline-none focus:ring-2 focus:ring-blue-500/20 text-sm transition-all" />
        </div>
        <!-- Status Filter -->
        <div class="flex items-center gap-2 flex-shrink-0">
          <button v-for="opt in [{ label: 'All', value: '' }, { label: 'Online', value: 'online' }, { label: 'Offline', value: 'offline' }]"
            :key="opt.value"
            @click="statusFilter = opt.value; currentPage = 1; fetchData()"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-black uppercase tracking-widest transition-all border"
            :class="statusFilter === opt.value
              ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
              : 'bg-transparent text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:border-blue-500/50'">
            <div v-if="opt.value" class="w-1.5 h-1.5 rounded-full"
              :class="opt.value === 'online' ? 'bg-emerald-400' : 'bg-red-400'"></div>
            {{ opt.label }}
          </button>
        </div>
        <!-- Count -->
        <div class="flex items-center gap-2 text-[11px] font-bold text-slate-400 flex-shrink-0">
          <Activity class="h-3.5 w-3.5 text-blue-500" />
          <span><b class="text-slate-700 dark:text-slate-200">{{ events.length }}</b> of <b class="text-slate-700 dark:text-slate-200">{{ totalEvents }}</b> events</span>
        </div>
      </div>

      <!-- Table -->
      <div class="overflow-x-auto">
        <table class="min-w-full">
          <thead>
            <tr class="border-b border-slate-100 dark:border-slate-800">
              <th class="py-3 px-6 text-[10px] font-black uppercase tracking-widest text-slate-400 text-left">Device</th>
              <th class="py-3 px-6 text-[10px] font-black uppercase tracking-widest text-slate-400 text-left hidden md:table-cell">Status</th>
              <th class="py-3 px-6 text-[10px] font-black uppercase tracking-widest text-slate-400 text-left hidden md:table-cell">Activity</th>
              <th class="py-3 px-6 text-[10px] font-black uppercase tracking-widest text-slate-400 text-left hidden md:table-cell">Time</th>
              <th class="py-3 px-6 text-[10px] font-black uppercase tracking-widest text-slate-400 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800/70">
            <template v-for="event in events" :key="event.id">
              <tr class="group hover:bg-slate-50/60 dark:hover:bg-slate-800/30 transition-colors">
                <!-- Device -->
                <td class="py-4 px-6">
                  <div class="flex items-center gap-3">
                    <!-- Status dot + icon -->
                    <div class="relative flex-shrink-0">
                      <div class="w-10 h-10 rounded-xl flex items-center justify-center transition-colors"
                        :class="event.status === 'online'
                          ? 'bg-emerald-500/10 group-hover:bg-emerald-500/15'
                          : 'bg-red-500/10 group-hover:bg-red-500/15'">
                        <component :is="getIcon(event.icon || event.device_type)" class="h-4.5 w-4.5"
                          :class="event.status === 'online' ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-500 dark:text-red-400'" />
                      </div>
                      <div class="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-white dark:border-slate-900"
                        :class="event.status === 'online' ? 'bg-emerald-500' : 'bg-slate-400'"></div>
                    </div>
                    <div class="min-w-0">
                      <div class="text-sm font-bold text-slate-900 dark:text-white truncate">{{ event.display_name }}</div>
                      <div class="text-[10px] font-mono text-slate-400 tracking-wider mt-0.5">{{ event.ip }}</div>
                    </div>
                  </div>
                </td>

                <!-- Status badge -->
                <td class="py-4 px-6 hidden md:table-cell">
                  <span v-if="event.status === 'online'"
                    class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                    <div class="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
                    Online
                  </span>
                  <span v-else
                    class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest bg-red-500/10 text-red-600 dark:text-red-400">
                    <div class="w-1.5 h-1.5 rounded-full bg-red-500"></div>
                    Offline
                  </span>
                </td>

                <!-- Activity -->
                <td class="py-4 px-6 hidden md:table-cell">
                  <p class="text-xs font-medium text-slate-600 dark:text-slate-400">
                    {{ event.status === 'online' ? 'Joined the network' : 'Disconnected from network' }}
                  </p>
                </td>

                <!-- Time -->
                <td class="py-4 px-6 hidden md:table-cell whitespace-nowrap">
                  <div class="text-xs font-bold text-slate-800 dark:text-slate-200">{{ formatRelativeTime(event.changed_at) }}</div>
                  <div class="text-[10px] text-slate-400 font-mono mt-0.5">{{ formatDate(event.changed_at) }}</div>
                </td>

                <!-- Actions -->
                <td class="py-4 px-6 text-right">
                  <div class="flex items-center justify-end gap-2">
                    <!-- Mobile expand -->
                    <button @click="toggleById(event.id)"
                      class="md:hidden p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-all"
                      v-tooltip="expandedRowIds.has(event.id) ? 'Collapse' : 'Expand'">
                      <component :is="expandedRowIds.has(event.id) ? ChevronUp : ChevronDown" class="h-4 w-4" />
                    </button>
                    <!-- View detail -->
                    <button @click="showDeviceDetail(event)"
                      class="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-[10px] font-black uppercase tracking-widest transition-all shadow-sm opacity-0 group-hover:opacity-100"
                      v-tooltip="'View Device History'">
                      <ArrowRightCircle class="h-3.5 w-3.5" />
                      <span class="hidden sm:inline">History</span>
                    </button>
                  </div>
                </td>
              </tr>

              <!-- Mobile Expanded Row -->
              <tr v-if="expandedRowIds.has(event.id)" class="md:hidden bg-slate-50/50 dark:bg-slate-800/20">
                <td colspan="5" class="px-6 py-4">
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <p class="text-[10px] uppercase tracking-wider text-slate-400 font-black mb-1">Status</p>
                      <span v-if="event.status === 'online'"
                        class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                        <div class="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>Online
                      </span>
                      <span v-else
                        class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest bg-red-500/10 text-red-600 dark:text-red-400">
                        <div class="w-1.5 h-1.5 rounded-full bg-red-500"></div>Offline
                      </span>
                    </div>
                    <div>
                      <p class="text-[10px] uppercase tracking-wider text-slate-400 font-black mb-1">Time</p>
                      <p class="text-xs font-bold text-slate-800 dark:text-slate-200">{{ formatRelativeTime(event.changed_at) }}</p>
                      <p class="text-[10px] font-mono text-slate-400">{{ formatDate(event.changed_at) }}</p>
                    </div>
                    <div class="col-span-2">
                      <p class="text-[10px] uppercase tracking-wider text-slate-400 font-black mb-1">Activity</p>
                      <p class="text-xs text-slate-600 dark:text-slate-400">
                        {{ event.status === 'online' ? 'Device joined the network' : 'Device disconnected from network' }}
                      </p>
                    </div>
                    <div class="col-span-2">
                      <button @click="showDeviceDetail(event)"
                        class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-black uppercase tracking-widest transition-all w-full justify-center">
                        <ArrowRightCircle class="h-3.5 w-3.5" />
                        View Full History
                      </button>
                    </div>
                  </div>
                </td>
              </tr>
            </template>

            <!-- Empty state -->
            <tr v-if="events.length === 0 && !loading">
              <td colspan="5" class="py-20 text-center">
                <div class="flex flex-col items-center gap-3 text-slate-400">
                  <div class="w-16 h-16 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                    <Inbox class="h-8 w-8 text-slate-300 dark:text-slate-600" />
                  </div>
                  <p class="text-sm font-semibold">No events match your criteria</p>
                  <p class="text-xs text-slate-400">Try adjusting your search or filters</p>
                </div>
              </td>
            </tr>

            <!-- Loading state -->
            <tr v-if="loading">
              <td colspan="5" class="py-20 text-center">
                <Loader2 class="h-8 w-8 animate-spin text-blue-500/30 mx-auto" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1"
        class="flex justify-end items-center gap-2 p-4 border-t border-slate-100 dark:border-slate-700/50 bg-slate-50/50 dark:bg-slate-900/30">
        <button @click="changePage(currentPage - 1)" :disabled="currentPage <= 1" class="pagination-btn">
          Previous
        </button>
        <div class="px-4 py-2 bg-slate-900 dark:bg-white rounded-lg text-sm font-medium text-white dark:text-slate-900">
          {{ currentPage }} / {{ totalPages }}
        </div>
        <button @click="changePage(currentPage + 1)" :disabled="currentPage >= totalPages" class="pagination-btn">
          Next
        </button>
      </div>
    </div>

    <!-- Device History Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="selectedDevice" class="fixed inset-0 z-[9999] flex items-center justify-center p-4 md:p-8"
          @click.self="closeModal">
          <!-- Backdrop -->
          <div class="absolute inset-0 bg-slate-950/70 backdrop-blur-md"></div>

          <!-- Modal -->
          <div class="relative bg-white dark:bg-slate-900 rounded-3xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col border border-slate-200 dark:border-slate-700/50 overflow-hidden">
            <!-- Top shimmer border -->
            <div class="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-blue-400/60 to-transparent z-10"></div>

            <!-- Modal Header -->
            <div class="p-6 flex items-start justify-between border-b border-slate-100 dark:border-slate-800 flex-shrink-0">
              <div class="flex items-center gap-4">
                <!-- Icon with gradient bg -->
                <div class="relative flex-shrink-0">
                  <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                    <component :is="getIcon(selectedDevice.icon || selectedDevice.device_type)" class="h-7 w-7 text-white" />
                  </div>
                  <div :class="selectedDevice.status === 'online' ? 'bg-emerald-500' : 'bg-red-500'"
                    class="absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white dark:border-slate-900 shadow-sm"></div>
                </div>
                <div>
                  <h3 class="text-xl font-black text-slate-900 dark:text-white">{{ selectedDevice.display_name }}</h3>
                  <div class="flex items-center gap-2 mt-1">
                    <span class="text-xs font-mono text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-lg">{{ selectedDevice.ip }}</span>
                    <span v-if="selectedDevice.status === 'online'"
                      class="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] font-black uppercase tracking-widest bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                      <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>Online
                    </span>
                    <span v-else
                      class="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] font-black uppercase tracking-widest bg-red-500/10 text-red-600 dark:text-red-400">
                      <div class="w-1.5 h-1.5 rounded-full bg-red-500"></div>Offline
                    </span>
                  </div>
                </div>
              </div>
              <button @click="closeModal"
                class="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-all hover:rotate-90 duration-300">
                <X class="h-5 w-5" />
              </button>
            </div>

            <!-- Mini Chart -->
            <div class="px-6 pt-5 flex-shrink-0">
              <div class="bg-slate-50 dark:bg-slate-800/60 rounded-2xl border border-slate-100 dark:border-slate-700/50 p-4">
                <div class="flex items-center justify-between mb-3">
                  <h4 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Connectivity Timeline</h4>
                  <div class="flex items-center gap-4 text-[10px] font-bold">
                    <div class="flex items-center gap-1.5">
                      <div class="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
                      <span class="text-emerald-600 dark:text-emerald-400">Online</span>
                    </div>
                    <div class="flex items-center gap-1.5">
                      <div class="w-1.5 h-1.5 rounded-full bg-red-500"></div>
                      <span class="text-red-500 dark:text-red-400">Offline</span>
                    </div>
                  </div>
                </div>
                <div class="h-28">
                  <apexchart v-if="deviceHistory.length > 0" type="line" height="100%"
                    :options="deviceChartOptions" :series="deviceChartSeries" />
                  <div v-else class="h-full flex items-center justify-center text-slate-400 text-xs italic">
                    <Loader2 class="h-5 w-5 animate-spin text-blue-500/40 mr-2" />
                    Generating timeline...
                  </div>
                </div>
              </div>
            </div>

            <!-- History List (scrollable) -->
            <div class="flex-1 overflow-y-auto p-6 pt-4 custom-scrollbar">
              <div class="flex items-center justify-between mb-4 px-1">
                <h4 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Event History</h4>
                <span class="text-[10px] font-bold text-slate-400">{{ historyTotal }} total events</span>
              </div>

              <div class="space-y-2">
                <div v-for="h in deviceHistory" :key="h.id"
                  class="flex items-center justify-between p-3.5 rounded-xl border transition-all hover:shadow-sm"
                  :class="h.status === 'online'
                    ? 'bg-emerald-50/50 dark:bg-emerald-900/10 border-emerald-100 dark:border-emerald-900/30 hover:border-emerald-200 dark:hover:border-emerald-800/50'
                    : 'bg-red-50/50 dark:bg-red-900/10 border-red-100 dark:border-red-900/30 hover:border-red-200 dark:hover:border-red-800/50'">
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0"
                      :class="h.status === 'online' ? 'bg-emerald-500 text-white' : 'bg-red-500 text-white'">
                      <component :is="h.status === 'online' ? Wifi : WifiOff" class="h-4 w-4" />
                    </div>
                    <div>
                      <span class="text-xs font-black uppercase tracking-widest"
                        :class="h.status === 'online' ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'">
                        {{ h.status === 'online' ? 'Connected' : 'Disconnected' }}
                      </span>
                      <p class="text-[10px] text-slate-400 mt-0.5">
                        {{ h.status === 'online' ? 'Device joined the network' : 'Connection lost or device powered off' }}
                      </p>
                    </div>
                  </div>
                  <div class="text-right flex-shrink-0 ml-4">
                    <div class="text-[11px] font-bold text-slate-700 dark:text-slate-300">{{ formatRelativeTime(h.changed_at) }}</div>
                    <div class="text-[10px] font-mono text-slate-400 mt-0.5">{{ formatDate(h.changed_at) }}</div>
                  </div>
                </div>
              </div>

              <!-- Load More -->
              <div v-if="deviceHistory.length < historyTotal" class="pt-4">
                <button @click="loadMoreHistory" :disabled="loadingHistory"
                  class="w-full flex items-center justify-center gap-2 py-3 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-black uppercase tracking-widest text-slate-500 hover:border-blue-500/50 hover:text-blue-600 transition-all">
                  <Loader2 v-if="loadingHistory" class="h-3.5 w-3.5 animate-spin text-blue-500" />
                  <span v-else>Load Older Events</span>
                </button>
              </div>

              <!-- End of history -->
              <div v-else-if="deviceHistory.length > 0" class="py-8 text-center">
                <div class="w-1.5 h-1.5 bg-slate-300 dark:bg-slate-700 rounded-full mx-auto mb-2 opacity-50"></div>
                <p class="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em]">End of History</p>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import api from '@/utils/api'
import { formatRelativeTime, formatDate, parseUTC, DateTime } from '@/utils/date'
import * as LucideIcons from 'lucide-vue-next'
const {
  RefreshCw, Search, Activity, ArrowRightCircle, X, Loader2, ZapOff, Inbox,
  ChevronDown, ChevronUp, Wifi, WifiOff,
  Network, BarChart2
} = LucideIcons
import { getIcon } from '@/utils/icons'
import { useNotifications } from '@/composables/useNotifications'
import { useWebSockets } from '@/composables/useWebSockets'

const { notifyError } = useNotifications()
const { lastNotification } = useWebSockets()

watch(lastNotification, (notif) => {
  if (notif && (notif.event_type === 'new_device' || notif.event_type === 'status_changed' || notif.event_type === 'completed')) {
    fetchData()
    fetchStats()
  }
})

// State
const events = ref([])
const expandedRowIds = ref(new Set())
const stats = ref([])
const loading = ref(false)
const loadingStats = ref(false)
const onlineNowCount = ref(0)
const onlineCount = ref(0)
const offlineCount = ref(0)
const statsTimeRange = ref(24)
const timeOptions = [
  { label: '24h', value: 24 },
  { label: '7d', value: 168 },
  { label: '30d', value: 720 }
]

// Pagination & Filtering
const currentPage = ref(1)
const totalEvents = ref(0)
const itemsPerPage = 20
const search = ref('')
const statusFilter = ref('')

// Modal / Device History
const selectedDevice = ref(null)
const deviceHistory = ref([])
const historyPage = ref(0)
const historyTotal = ref(0)
const loadingHistory = ref(false)

const totalPages = computed(() => Math.ceil(totalEvents.value / itemsPerPage) || 1)


// Data Fetching
const fetchCount = async () => {
  try {
    const params = { status: statusFilter.value || undefined, search: search.value || undefined }
    const res = await api.get('/events/count', { params })
    totalEvents.value = res.data.total
  } catch (err) { console.error('Count failed', err) }
}

const fetchData = async () => {
  loading.value = true
  try {
    await fetchCount()
    const offset = (currentPage.value - 1) * itemsPerPage
    const params = {
      limit: itemsPerPage,
      offset,
      status: statusFilter.value || undefined,
      search: search.value || undefined
    }
    const response = await api.get('/events/', { params })
    events.value = response.data

    // Fetch online devices count
    const devRes = await api.get('/devices/', { params: { limit: -1 } })
    const allDevices = devRes.data.items || []
    onlineNowCount.value = allDevices.filter(d => d.status === 'online').length

    // Fetch online/offline event counts (unfiltered)
    try {
      const onlineRes = await api.get('/events/count', { params: { status: 'online' } })
      const offlineRes = await api.get('/events/count', { params: { status: 'offline' } })
      onlineCount.value = onlineRes.data.total
      offlineCount.value = offlineRes.data.total
    } catch {}
  } catch (err) {
    console.error('Failed to fetch events', err)
    notifyError('Failed to refresh event log')
  } finally {
    loading.value = false
  }
}

let debounceTimer = null
const debounceFetch = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    currentPage.value = 1
    fetchData()
  }, 400)
}

const changePage = (p) => {
  if (p < 1 || p > totalPages.value) return
  currentPage.value = p
  fetchData()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const fetchStats = async () => {
  loadingStats.value = true
  try {
    const response = await api.get(`/events/stats?hours=${statsTimeRange.value}`)
    stats.value = response.data
  } catch (err) {
    console.error('Failed to fetch stats', err)
  } finally {
    loadingStats.value = false
  }
}

const toggleById = (id) => {
  if (expandedRowIds.value.has(id)) expandedRowIds.value.delete(id)
  else expandedRowIds.value.add(id)
}

const showDeviceDetail = async (device) => {
  selectedDevice.value = device
  deviceHistory.value = []
  historyPage.value = 0
  await fetchDeviceHistoryCount(device.device_id)
  await loadMoreHistory()
}

const fetchDeviceHistoryCount = async (id) => {
  try {
    const res = await api.get(`/events/device/${id}/count`)
    historyTotal.value = res.data.total
  } catch (err) { console.error(err) }
}

const loadMoreHistory = async () => {
  if (!selectedDevice.value) return
  loadingHistory.value = true
  try {
    const limit = 20
    const offset = historyPage.value * limit
    const response = await api.get(`/events/device/${selectedDevice.value.device_id}`, {
      params: { limit, offset }
    })
    deviceHistory.value = [...deviceHistory.value, ...response.data]
    historyPage.value++
  } catch (err) {
    console.error('Failed to fetch device history', err)
  } finally {
    loadingHistory.value = false
  }
}

const closeModal = () => {
  selectedDevice.value = null
}

// Charts
const chartOptions = computed(() => ({
  chart: {
    id: 'network-trend',
    type: 'line',
    stacked: false,
    toolbar: { show: false },
    animations: { enabled: true, easing: 'easeinout', speed: 800 },
    background: 'transparent',
    fontFamily: 'inherit'
  },
  colors: ['#10b981', '#ef4444'],
  stroke: { curve: 'smooth', width: 3 },
  xaxis: {
    type: 'datetime',
    labels: {
      style: { colors: '#94a3b8', fontSize: '9px', fontWeight: 600 },
      formatter: function (val, timestamp) {
        const ts = timestamp || val
        if (!ts) return ''
        const date = DateTime.fromMillis(Number(ts)).toLocal()
        if (!date.isValid) return ''
        if (statsTimeRange.value <= 24) {
          return date.toFormat('MMM d, HH:mm')
        }
        return date.toFormat('MMM d')
      }
    },
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  yaxis: {
    min: 0,
    forceNiceScale: true,
    labels: { style: { colors: '#94a3b8', fontSize: '9px', fontWeight: 600 } }
  },
  grid: { borderColor: 'rgba(148, 163, 184, 0.1)', strokeDashArray: 6, padding: { left: 10, right: 10 } },
  tooltip: { theme: 'dark', x: { format: 'HH:mm' } },
  dataLabels: { enabled: false },
  legend: {
    position: 'top',
    horizontalAlign: 'right',
    fontSize: '10px',
    fontWeight: 700,
    labels: { colors: '#94a3b8' },
    markers: { radius: 12 }
  }
}))

const chartSeries = computed(() => {
  const buckets = {}
  stats.value.forEach(s => {
    const dt = parseUTC(s.timestamp).toLocal()
    const key = dt.startOf(statsTimeRange.value <= 24 ? 'hour' : 'day').toMillis()
    if (!buckets[key]) buckets[key] = { online: 0, offline: 0 }
    buckets[key].online += s.online_count
    buckets[key].offline += s.offline_count
  })
  const sortedKeys = Object.keys(buckets).sort()
  return [
    { name: 'Online', data: sortedKeys.map(k => ({ x: parseInt(k), y: buckets[k].online })) },
    { name: 'Offline', data: sortedKeys.map(k => ({ x: parseInt(k), y: buckets[k].offline })) }
  ]
})

const deviceChartOptions = computed(() => ({
  chart: {
    toolbar: { show: false },
    background: 'transparent',
    animations: { enabled: true }
  },
  xaxis: {
    type: 'datetime',
    labels: { show: false },
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  yaxis: { labels: { show: false }, min: 0, max: 1.2 },
  grid: { show: false, padding: { left: -10, right: -10, top: 0, bottom: 0 } },
  tooltip: { theme: 'dark', x: { format: 'MMM d HH:mm' } },
  colors: ['#3b82f6'],
  stroke: { curve: 'stepline', width: 2.5 },
  markers: {
    size: 4,
    colors: ['#3b82f6'],
    strokeColors: '#fff',
    strokeWidth: 2,
    hover: { size: 6 }
  },
  dataLabels: { enabled: false }
}))

const deviceChartSeries = computed(() => [{
  name: 'State',
  data: deviceHistory.value.slice().reverse().map(h => ({
    x: parseUTC(h.changed_at).toMillis(),
    y: h.status === 'online' ? 1 : 0.2
  }))
}])

onMounted(() => {
  fetchData()
  fetchStats()
})
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
  transform: scale(0.96) translateY(8px);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.15);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.3);
}
</style>
