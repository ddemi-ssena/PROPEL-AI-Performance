<template>
  <div class="space-y-8 pb-10">
    <!-- ── Page header ────────────────────────────────────────────── -->
    <div class="flex flex-col xl:flex-row xl:items-end xl:justify-between gap-4 border-b border-slate-200 pb-6">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 tracking-tight">Departman Analizi</h2>
        <p class="mt-1 text-slate-500">
          Satış departmanı KPI omurgası, takım karşılaştırması ve çalışan risk profilini tek ekranda izleyin.
        </p>
      </div>
      <button
        @click="loadOverview"
        :disabled="loading"
        class="flex items-center gap-2 px-4 py-2.5 text-sm font-semibold rounded-xl border border-slate-200 bg-white shadow-sm hover:bg-slate-50 transition disabled:opacity-50 self-start xl:self-auto"
      >
        <svg class="w-4 h-4" :class="loading ? 'animate-spin' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Yenile
      </button>
    </div>

    <!-- ── Loading skeleton ───────────────────────────────────────── -->
    <template v-if="loading">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div v-for="i in 4" :key="i" class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm animate-pulse">
          <div class="h-2.5 bg-slate-200 rounded w-3/4 mb-4"></div>
          <div class="h-8 bg-slate-200 rounded w-1/2 mb-3"></div>
          <div class="h-2 bg-slate-100 rounded w-full"></div>
        </div>
      </div>
      <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm animate-pulse h-72"></div>
    </template>

    <!-- ── Error ──────────────────────────────────────────────────── -->
    <template v-else-if="error">
      <div class="rounded-2xl border border-rose-200 bg-rose-50 p-10 text-center">
        <p class="text-rose-700 font-semibold text-lg">Veriler yüklenemedi</p>
        <p class="text-rose-500 text-sm mt-2 mb-5">{{ error }}</p>
        <button @click="loadOverview"
          class="px-5 py-2.5 bg-rose-600 text-white text-sm font-semibold rounded-xl hover:bg-rose-700 transition-colors">
          Tekrar Dene
        </button>
      </div>
    </template>

    <template v-else-if="overview">
      <!-- ── Metric cards ────────────────────────────────────────── -->
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
        <div
          v-for="metric in overview.metrics"
          :key="metric.key"
          class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{{ metric.label }}</p>
          <p class="mt-3 text-2xl font-bold" :class="metricValueClass(metric.tone)">{{ metric.value }}</p>
          <p class="mt-2 text-xs leading-5 text-slate-500">{{ metric.hint }}</p>
        </div>
      </div>

      <!-- ── Team KPI chart + Team summary ─────────────────────── -->
      <div class="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_320px] gap-6">

        <!-- Bar chart -->
        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex items-start justify-between gap-4 mb-6">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">KPI Takım Karşılaştırması</p>
              <h3 class="mt-1 text-lg font-bold text-slate-900">Takım bazlı performans ve trend</h3>
            </div>
            <span class="text-xs font-medium text-slate-400 bg-slate-50 border border-slate-200 rounded-full px-3 py-1">
              {{ overview.team_summaries.length }} takım analizi
            </span>
          </div>

          <!-- SVG Chart -->
          <div v-if="overview.team_summaries.length" class="overflow-x-auto">
            <div :style="{ minWidth: `${Math.max(480, overview.team_summaries.length * 140)}px` }">
              <svg
                :width="chartWidth"
                height="280"
                class="w-full"
                :viewBox="`0 0 ${chartWidth} 280`"
                preserveAspectRatio="xMidYMid meet"
              >
                <!-- Y axis grid lines -->
                <g>
                  <line v-for="tick in yTicks" :key="tick"
                    :x1="chartPad" :y1="yPos(tick)" :x2="chartWidth - 20" :y2="yPos(tick)"
                    stroke="#F1F5F9" stroke-width="1" />
                  <text v-for="tick in yTicks" :key="`lbl-${tick}`"
                    :x="chartPad - 8" :y="yPos(tick) + 4"
                    text-anchor="end" font-size="11" fill="#94A3B8">{{ tick }}</text>
                </g>

                <!-- Bars + team labels -->
                <g v-for="(team, i) in overview.team_summaries" :key="team.team">
                  <!-- Bar -->
                  <rect
                    :x="barX(i)"
                    :y="yPos(team.average_score)"
                    :width="barW"
                    :height="chartH - yPos(team.average_score) + chartPadTop"
                    rx="4"
                    fill="#3B82F6"
                    opacity="0.85"
                  />
                  <!-- Score label on bar -->
                  <text
                    :x="barX(i) + barW / 2"
                    :y="yPos(team.average_score) - 6"
                    text-anchor="middle"
                    font-size="11"
                    font-weight="700"
                    fill="#1E40AF"
                  >{{ Math.round(team.average_score) }}</text>

                  <!-- Team label -->
                  <text
                    :x="barX(i) + barW / 2"
                    y="268"
                    text-anchor="middle"
                    font-size="11"
                    fill="#64748B"
                  >{{ shortTeamName(team.team) }}</text>
                </g>

                <!-- Trend line -->
                <polyline
                  v-if="trendPoints.length > 1"
                  :points="trendPoints"
                  fill="none"
                  stroke="#EF4444"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <circle
                  v-for="(team, i) in overview.team_summaries"
                  :key="`dot-${team.team}`"
                  :cx="barX(i) + barW / 2"
                  :cy="trendY(team)"
                  r="4"
                  :fill="(team.average_trend_delta ?? 0) >= 0 ? '#10B981' : '#EF4444'"
                />
              </svg>
            </div>

            <!-- Legend -->
            <div class="flex items-center gap-5 mt-3 text-xs font-semibold text-slate-500">
              <span class="flex items-center gap-1.5">
                <span class="w-3 h-3 rounded-sm bg-blue-500 opacity-85"></span>
                Ortalama KPI
              </span>
              <span class="flex items-center gap-1.5">
                <span class="w-3 h-1.5 bg-red-400 rounded-full"></span>
                4H Trend
              </span>
            </div>
          </div>

          <div v-else class="flex items-center justify-center h-48 text-slate-400 text-sm">
            Takım verisi bulunamadı.
          </div>
        </div>

        <!-- Team KPI summary -->
        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 mb-4">Takım KPI Özeti</p>
          <div class="space-y-4">
            <div
              v-for="team in overview.team_summaries"
              :key="team.team"
              class="group"
            >
              <div class="flex items-start justify-between gap-2 mb-1.5">
                <p class="text-sm font-bold text-slate-800 leading-5">{{ team.team }}</p>
                <span class="text-sm font-bold" :class="scoreColor(team.average_score)">
                  {{ Math.round(team.average_score) }}/100
                </span>
              </div>
              <!-- KPI progress bar -->
              <div class="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :class="scoreBarColor(team.average_score)"
                  :style="{ width: `${Math.min(100, team.average_score)}%` }"
                ></div>
              </div>
              <div class="flex items-center justify-between mt-1 text-xs text-slate-400">
                <span>{{ team.employee_count }} çalışan analizi</span>
                <span v-if="team.average_trend_delta != null"
                  :class="(team.average_trend_delta ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-500'"
                  class="font-semibold"
                >
                  {{ (team.average_trend_delta ?? 0) >= 0 ? '▲' : '▼' }}
                  trend {{ (team.average_trend_delta ?? 0) >= 0 ? '+' : '' }}{{ team.average_trend_delta?.toFixed(1) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Employee watchlist table ───────────────────────────── -->
      <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-5">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Çalışan Risk Tablosu</p>
            <h3 class="mt-1 text-base font-bold text-slate-900">{{ filteredEmployees.length }} çalışan · skor sıralaması</h3>
          </div>
          <select
            v-model="riskFilter"
            class="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 shadow-sm"
          >
            <option value="">Tüm Risk Seviyeleri</option>
            <option value="high">İzleme Gerekli</option>
            <option value="medium">Stabil</option>
            <option value="low">Güçlü</option>
          </select>
        </div>

        <div class="overflow-x-auto rounded-xl border border-slate-100">
          <table class="min-w-full text-sm">
            <thead>
              <tr class="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-400">
                <th class="px-4 py-3 text-left">Çalışan</th>
                <th class="px-4 py-3 text-left">Takım</th>
                <th class="px-4 py-3 text-left">KPI Skoru</th>
                <th class="px-4 py-3 text-left">Trend</th>
                <th class="px-4 py-3 text-left">Risk Bandı</th>
                <th class="px-4 py-3 text-left">En Güçlü</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(emp, idx) in filteredEmployees"
                :key="emp.employee_id"
                class="border-t border-slate-100 hover:bg-slate-50 transition-colors"
                :class="(idx as number) % 2 === 1 ? 'bg-slate-50/40' : ''"
              >
                <td class="px-4 py-3">
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-slate-600 font-bold text-xs shrink-0">
                      {{ nameInitials(emp.employee_name) }}
                    </div>
                    <span class="font-semibold text-slate-800 truncate max-w-[160px]">{{ emp.employee_name }}</span>
                  </div>
                </td>
                <td class="px-4 py-3 text-slate-500">{{ emp.team || '—' }}</td>
                <td class="px-4 py-3">
                  <div class="flex items-center gap-2">
                    <span class="font-bold" :class="scoreColor(emp.latest_score)">
                      {{ Math.round(emp.latest_score) }}
                    </span>
                    <div class="w-20 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div class="h-full rounded-full" :class="scoreBarColor(emp.latest_score)"
                        :style="{ width: `${Math.min(100, emp.latest_score)}%` }"></div>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <span v-if="emp.trend_delta != null" class="text-xs font-semibold"
                    :class="(emp.trend_delta ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-500'">
                    {{ (emp.trend_delta ?? 0) >= 0 ? '▲' : '▼' }}
                    {{ Math.abs(emp.trend_delta ?? 0).toFixed(1) }}
                  </span>
                  <span v-else class="text-slate-300">—</span>
                </td>
                <td class="px-4 py-3">
                  <span class="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border"
                    :class="riskBandClass(emp.risk_band)">
                    <span class="w-1.5 h-1.5 rounded-full" :class="riskBandDotClass(emp.risk_band)"></span>
                    {{ emp.risk_band }}
                  </span>
                </td>
                <td class="px-4 py-3 text-xs text-slate-500">{{ emp.strongest_category || '—' }}</td>
              </tr>
              <tr v-if="!filteredEmployees.length">
                <td colspan="6" class="px-4 py-10 text-center text-slate-400">Filtre kriterine uyan çalışan bulunamadı.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── Analytics omurgasi + Sprint focus ─────────────────── -->
      <div class="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_340px] gap-6">

        <!-- Analytics omurgasi -->
        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex items-start justify-between gap-4 mb-1">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Analytics Omurgası</p>
            <span class="text-xs font-semibold px-2.5 py-1 rounded-full border"
              :class="overview.definition.readiness_status === 'live'
                ? 'text-emerald-700 bg-emerald-50 border-emerald-200'
                : 'text-amber-700 bg-amber-50 border-amber-200'">
              {{ overview.definition.readiness_status === 'live' ? 'Canlı' : overview.definition.readiness_status }}
            </span>
          </div>
          <h3 class="text-lg font-bold text-slate-900 mb-2">{{ overview.definition.label }}</h3>
          <p class="text-sm text-slate-500 leading-6 mb-6">{{ overview.definition.description }}</p>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div
              v-for="layer in overview.definition.layers"
              :key="layer.key"
              class="rounded-xl border border-slate-100 bg-slate-50 p-4"
            >
              <p class="text-sm font-bold text-slate-700 mb-1.5">{{ layer.title }}</p>
              <p class="text-xs text-slate-500 leading-5">{{ layer.summary }}</p>
            </div>
          </div>
        </div>

        <!-- Sprint focus -->
        <div class="rounded-2xl bg-slate-900 p-6 text-white shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Sprint 1</p>
          <h3 class="mt-1 text-lg font-bold mb-5">Yapılanlar ve sıradaki adım</h3>

          <div class="mb-5">
            <p class="text-xs font-semibold text-slate-400 mb-3">Planlanan hedefler</p>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="target in overview.definition.planned_targets"
                :key="target"
                class="text-xs font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 border border-slate-700"
              >
                {{ target }}
              </span>
            </div>
          </div>

          <div>
            <p class="text-xs font-semibold text-slate-400 mb-3">Sprint odağı</p>
            <ul class="space-y-2.5">
              <li
                v-for="item in overview.sprint_focus"
                :key="item"
                class="flex items-start gap-2 text-sm text-slate-300 leading-5"
              >
                <span class="mt-1 w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0"></span>
                {{ item }}
              </li>
            </ul>
          </div>

          <div v-if="overview.notes?.length" class="mt-6 border-t border-slate-800 pt-5">
            <p class="text-xs font-semibold text-slate-400 mb-3">Notlar</p>
            <ul class="space-y-2">
              <li v-for="note in overview.notes" :key="note"
                class="text-xs text-slate-400 leading-5">— {{ note }}</li>
            </ul>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  analyticsApi,
  type DepartmentAnalyticsOverviewResponse,
  type EmployeeAnalyticsSnapshotResponse,
  type TeamAnalyticsSnapshotResponse,
} from '@/services/api/analytics.api'

const loading = ref(false)
const error = ref<string | null>(null)
const overview = ref<DepartmentAnalyticsOverviewResponse | null>(null)
const riskFilter = ref('')

// ── Chart geometry ──────────────────────────────────────────────
const chartPad = 42
const chartPadTop = 20
const chartH = 230  // usable chart height in px
const barW = 60
const yMax = 130

const yTicks = [0, 25, 50, 75, 100, 125]

const chartWidth = computed(() => {
  const teams = overview.value?.team_summaries.length ?? 1
  return Math.max(500, chartPad + teams * (barW + 60) + 40)
})

function barX(i: number): number {
  const spacing = (chartWidth.value - chartPad - 40) / (overview.value?.team_summaries.length ?? 1)
  return chartPad + i * spacing + spacing / 2 - barW / 2
}

function yPos(val: number): number {
  return chartPadTop + (chartH - chartPadTop) * (1 - val / yMax)
}

function trendY(team: TeamAnalyticsSnapshotResponse): number {
  // show trend delta as offset from the bar top
  const delta = team.average_trend_delta ?? 0
  const indicatorVal = Math.max(0, Math.min(yMax, team.average_score + delta * 5))
  return yPos(indicatorVal)
}

const trendPoints = computed(() => {
  const teams = overview.value?.team_summaries ?? []
  if (teams.length < 2) return ''
  return teams
    .map((t: TeamAnalyticsSnapshotResponse, i: number) => `${barX(i) + barW / 2},${trendY(t)}`)
    .join(' ')
})

// ── Filtering ───────────────────────────────────────────────────
const filteredEmployees = computed<EmployeeAnalyticsSnapshotResponse[]>(() => {
  if (!overview.value) return []
  const emps = overview.value.employee_summaries
  if (!riskFilter.value) return emps
  return emps.filter((e: EmployeeAnalyticsSnapshotResponse) => {
    const b = (e.risk_band || '').toLowerCase()
    if (riskFilter.value === 'high') return b.includes('izleme') || b === 'high'
    if (riskFilter.value === 'medium') return b.includes('stabil') || b === 'medium'
    if (riskFilter.value === 'low') return b.includes('güçlü') || b.includes('guclu') || b === 'low'
    return true
  })
})

// ── API ─────────────────────────────────────────────────────────
async function loadOverview() {
  loading.value = true
  error.value = null
  try {
    overview.value = await analyticsApi.getDepartmentOverview('sales')
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || 'Bilinmeyen hata'
  } finally {
    loading.value = false
  }
}

// ── Helpers ─────────────────────────────────────────────────────
function metricValueClass(tone: string): string {
  if (tone === 'good' || tone === 'success' || tone === 'primary') return 'text-emerald-600'
  if (tone === 'warn' || tone === 'warning') return 'text-amber-600'
  if (tone === 'bad') return 'text-rose-600'
  return 'text-slate-900'
}

function scoreColor(score: number): string {
  if (score >= 100) return 'text-emerald-600'
  if (score >= 80) return 'text-blue-600'
  if (score >= 60) return 'text-amber-600'
  return 'text-rose-600'
}

function scoreBarColor(score: number): string {
  if (score >= 100) return 'bg-emerald-500'
  if (score >= 80) return 'bg-blue-500'
  if (score >= 60) return 'bg-amber-500'
  return 'bg-rose-500'
}

function riskBandClass(band: string): string {
  const b = (band || '').toLowerCase()
  if (b.includes('izleme') || b === 'high') return 'text-rose-700 bg-rose-50 border-rose-200'
  if (b.includes('stabil') || b === 'medium') return 'text-blue-700 bg-blue-50 border-blue-200'
  if (b.includes('güçlü') || b.includes('guclu') || b === 'low') return 'text-emerald-700 bg-emerald-50 border-emerald-200'
  return 'text-slate-600 bg-slate-50 border-slate-200'
}

function riskBandDotClass(band: string): string {
  const b = (band || '').toLowerCase()
  if (b.includes('izleme') || b === 'high') return 'bg-rose-500'
  if (b.includes('stabil') || b === 'medium') return 'bg-blue-500'
  return 'bg-emerald-500'
}

function nameInitials(name: string): string {
  return (name || '?').split(' ').map((p) => p[0]).join('').toUpperCase().substring(0, 2)
}

function shortTeamName(name: string): string {
  if (name.length <= 12) return name
  return name.split(' ').map((w) => w[0]).join('').toUpperCase()
}

onMounted(loadOverview)
</script>
