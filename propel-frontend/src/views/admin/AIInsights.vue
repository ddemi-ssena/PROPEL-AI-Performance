<template>
  <div>
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold text-slate-900 tracking-tight">Yapay Zeka İçgörüleri</h1>
        <p class="text-slate-500 mt-1">ML modeli + Gemini AI ile oluşturulan çok boyutlu risk ve performans raporu.</p>
      </div>
      <button
        @click="fetchInsights"
        :disabled="isLoading"
        class="bg-violet-600 hover:bg-violet-700 text-white font-medium px-4 py-2.5 rounded-lg transition-colors flex items-center gap-2 shadow-sm shadow-violet-600/20 disabled:opacity-50"
      >
        <ArrowPathIcon class="w-5 h-5" :class="{ 'animate-spin': isLoading }" />
        {{ isLoading ? 'Analiz ediliyor...' : 'Yeniden Oluştur' }}
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex flex-col items-center justify-center py-24 gap-5">
      <div class="relative">
        <div class="w-16 h-16 border-4 border-violet-100 border-t-violet-600 rounded-full animate-spin"></div>
        <SparklesIcon class="w-6 h-6 text-violet-500 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
      </div>
      <div class="text-center">
        <p class="text-slate-700 font-medium">ML modelleri çalıştırılıyor...</p>
        <p class="text-slate-400 text-sm mt-1">Gemini AI ile yönetici raporu oluşturuluyor. Bu 15–20 saniye sürebilir.</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="errorMsg" class="flex flex-col items-center justify-center py-20 gap-4">
      <ExclamationCircleIcon class="w-12 h-12 text-red-400" />
      <p class="text-slate-600 font-medium">Veri yüklenemedi</p>
      <p class="text-slate-400 text-sm">{{ errorMsg }}</p>
      <button @click="fetchInsights" class="mt-2 px-4 py-2 bg-slate-800 text-white rounded-lg text-sm hover:bg-slate-700 transition-colors">
        Tekrar Dene
      </button>
    </div>

    <!-- Content -->
    <template v-else>

      <!-- ── Section 1: KPI Cards ─────────────────────────────────────────── -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        <div
          v-for="(kpi, idx) in data.kpis"
          :key="kpi.title"
          class="bg-white rounded-xl p-5 shadow-sm border border-slate-200 hover:border-slate-300 transition-colors"
        >
          <div class="flex items-start justify-between mb-3">
            <p class="text-sm font-medium text-slate-500 leading-snug">{{ kpi.title }}</p>
            <component :is="kpiIcons[idx]" class="w-5 h-5 flex-shrink-0" :class="kpiIconColors[idx]" />
          </div>
          <div class="flex items-baseline gap-2 mb-1">
            <span class="text-3xl font-bold text-slate-900">{{ kpi.value }}</span>
            <span class="text-sm font-semibold" :class="kpi.trendColor">{{ kpi.trend }}</span>
          </div>
          <p class="text-xs text-slate-400">{{ kpi.comparison }}</p>
        </div>
      </div>

      <!-- ── Section 2: Risk Hedef Tanımları ────────────────────────────── -->
      <div class="mb-8">
        <div class="flex items-center gap-2 mb-4">
          <InformationCircleIcon class="w-5 h-5 text-slate-400" />
          <h2 class="text-lg font-bold text-slate-900">Risk Hedef Tanımları</h2>
          <span class="text-xs text-slate-400 font-normal ml-1">&#8212; 4 ML tahmin hedefi</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          <div
            v-for="def in data.risk_definitions"
            :key="def.key"
            class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden"
            :class="riskDefBorderClass(def.color)"
          >
            <!-- Colored top bar -->
            <div class="h-1 w-full" :class="riskDefTopBarClass(def.color)"></div>
            <div class="p-4">
              <div class="flex items-start justify-between gap-2 mb-2">
                <span class="text-sm font-bold text-slate-900 leading-snug">{{ def.label }}</span>
                <span class="text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0" :class="riskDefBadgeClass(def.color)">
                  {{ def.target }}
                </span>
              </div>
              <p class="text-xs text-slate-500 leading-relaxed mb-3">{{ def.description }}</p>
              <div class="flex items-start gap-1.5 mb-3 p-2 rounded-lg" :class="riskDefBgClass(def.color)">
                <ChartBarIcon class="w-3.5 h-3.5 flex-shrink-0 mt-0.5" :class="riskDefIconClass(def.color)" />
                <p class="text-xs leading-snug" :class="riskDefIconClass(def.color)">{{ def.boundary }}</p>
              </div>
              <ul class="space-y-1">
                <li
                  v-for="signal in def.signals"
                  :key="signal"
                  class="flex items-start gap-1.5 text-xs text-slate-600"
                >
                  <span class="w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1.5" :class="riskDefDotClass(def.color)"></span>
                  {{ signal }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Section 3: Departman Risk Dağılımı ─────────────────────────── -->
      <div class="mb-8">
        <div class="flex items-center gap-2 mb-4">
          <ChartBarIcon class="w-5 h-5 text-slate-400" />
          <h2 class="text-lg font-bold text-slate-900">Departman Risk Dağılımı</h2>
          <span class="text-xs text-slate-400 font-normal ml-1">— Satış vs Yazılım karşılaştırması</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            v-for="def in data.risk_definitions"
            :key="`chart-${def.key}`"
            class="bg-white rounded-xl p-5 shadow-sm border border-slate-200"
          >
            <div class="flex items-center gap-2 mb-4">
              <span class="w-2.5 h-2.5 rounded-full flex-shrink-0" :class="riskDefDotClass(def.color)"></span>
              <h3 class="text-sm font-bold text-slate-800">{{ def.label }}</h3>
            </div>

            <!-- Sales row -->
            <div class="mb-3">
              <div class="flex items-center justify-between text-xs text-slate-500 mb-1.5">
                <div class="flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                  <span class="font-medium text-slate-700">Satış</span>
                </div>
                <span>
                  <span class="font-semibold text-slate-800">
                    {{ chartDist('sales', def.key).risky_pct.toFixed(0) }}% riskli
                  </span>
                  &nbsp;({{ chartDist('sales', def.key).risky }}/{{ chartDist('sales', def.key).total }})
                </span>
              </div>
              <div class="w-full h-3 bg-slate-100 rounded-full overflow-hidden flex">
                <div
                  class="h-full transition-all duration-500"
                  :class="riskBarRiskyClass(def.color)"
                  :style="{ width: `${chartDist('sales', def.key).risky_pct}%` }"
                ></div>
                <div
                  class="h-full bg-emerald-200 transition-all duration-500"
                  :style="{ width: `${100 - chartDist('sales', def.key).risky_pct}%` }"
                ></div>
              </div>
              <div class="flex justify-between text-xs text-slate-400 mt-0.5">
                <span>Riskli</span>
                <span>Güvenli</span>
              </div>
            </div>

            <!-- Software row -->
            <div>
              <div class="flex items-center justify-between text-xs text-slate-500 mb-1.5">
                <div class="flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full bg-indigo-500"></span>
                  <span class="font-medium text-slate-700">Yazılım</span>
                </div>
                <span>
                  <span class="font-semibold text-slate-800">
                    {{ chartDist('software', def.key).risky_pct.toFixed(0) }}% riskli
                  </span>
                  &nbsp;({{ chartDist('software', def.key).risky }}/{{ chartDist('software', def.key).total }})
                </span>
              </div>
              <div class="w-full h-3 bg-slate-100 rounded-full overflow-hidden flex">
                <div
                  class="h-full transition-all duration-500"
                  :class="riskBarRiskyClass(def.color)"
                  :style="{ width: `${chartDist('software', def.key).risky_pct}%` }"
                ></div>
                <div
                  class="h-full bg-emerald-200 transition-all duration-500"
                  :style="{ width: `${100 - chartDist('software', def.key).risky_pct}%` }"
                ></div>
              </div>
              <div class="flex justify-between text-xs text-slate-400 mt-0.5">
                <span>Riskli</span>
                <span>Güvenli</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Section 4: Çalışan ML Raporu (Tablo) ───────────────────────── -->
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mb-8">
        <div class="p-5 border-b border-slate-200">
          <div class="flex items-center justify-between flex-wrap gap-3">
            <div class="flex items-center gap-2">
              <TableCellsIcon class="w-5 h-5 text-slate-400" />
              <h2 class="text-lg font-bold text-slate-900">Tüm Çalışan ML Raporu</h2>
              <span class="text-xs text-slate-400 font-normal ml-1">— {{ filteredTableRows.length }} çalışan</span>
            </div>
            <div class="flex items-center gap-2 flex-wrap">
              <input
                v-model="tableSearch"
                type="text"
                placeholder="İsim veya kod ara..."
                class="text-sm bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-violet-500 focus:outline-none w-48"
              />
              <select
                v-model="tableDeptFilter"
                class="text-sm bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-violet-500 focus:outline-none"
              >
                <option value="">Tüm Departmanlar</option>
                <option value="Satış">Satış</option>
                <option value="Yazılım">Yazılım</option>
              </select>
            </div>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <th class="px-4 py-3">Çalışan</th>
                <th class="px-4 py-3">Departman / Takım</th>
                <th class="px-4 py-3 text-center">Perf. Düşüşü %</th>
                <th class="px-4 py-3 text-center">Tükenmişlik %</th>
                <th class="px-4 py-3 text-center">İstifa Riski %</th>
                <th class="px-4 py-3 text-center">Yüksek Risk %</th>
                <th class="px-4 py-3 text-center">Genel Risk %</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="emp in visibleTableRows"
                :key="emp.code"
                class="hover:bg-slate-50/70 transition-colors"
              >
                <td class="px-4 py-3">
                  <div class="flex items-center gap-2.5">
                    <div
                      class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                      :class="emp.department === 'Satış' ? 'bg-emerald-500' : 'bg-indigo-500'"
                    >
                      {{ initials(emp.name) }}
                    </div>
                    <div>
                      <p class="text-sm font-medium text-slate-900">{{ emp.name }}</p>
                      <p class="text-xs text-slate-400">{{ emp.code }}</p>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <span
                    class="text-xs font-medium px-2 py-0.5 rounded-full"
                    :class="emp.department === 'Satış' ? 'bg-emerald-50 text-emerald-700' : 'bg-indigo-50 text-indigo-700'"
                  >
                    {{ emp.department }}
                  </span>
                  <p class="text-xs text-slate-400 mt-0.5">{{ emp.team }}</p>
                </td>
                <td class="px-4 py-3 text-center">
                  <span class="inline-block text-xs font-bold px-2 py-1 rounded-full" :class="riskPctBadge(emp.perf_drop)">
                    {{ emp.perf_drop }}%
                  </span>
                </td>
                <td class="px-4 py-3 text-center">
                  <span class="inline-block text-xs font-bold px-2 py-1 rounded-full" :class="riskPctBadge(emp.burnout)">
                    {{ emp.burnout }}%
                  </span>
                </td>
                <td class="px-4 py-3 text-center">
                  <span class="inline-block text-xs font-bold px-2 py-1 rounded-full" :class="riskPctBadge(emp.resignation)">
                    {{ emp.resignation }}%
                  </span>
                </td>
                <td class="px-4 py-3 text-center">
                  <span class="inline-block text-xs font-bold px-2 py-1 rounded-full" :class="riskPctBadge(emp.high_risk)">
                    {{ emp.high_risk }}%
                  </span>
                </td>
                <td class="px-4 py-3 text-center">
                  <div class="flex flex-col items-center gap-1">
                    <span class="inline-block text-xs font-bold px-2 py-1 rounded-full" :class="riskPctBadge(emp.composite)">
                      {{ emp.composite }}%
                    </span>
                    <div class="w-16 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                      <div
                        class="h-full rounded-full transition-all"
                        :class="compositeBarColor(emp.composite)"
                        :style="{ width: `${emp.composite}%` }"
                      ></div>
                    </div>
                  </div>
                </td>
              </tr>
              <tr v-if="filteredTableRows.length === 0">
                <td colspan="7" class="px-5 py-10 text-center text-slate-400 text-sm">
                  Eşleşen çalışan bulunamadı.
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div
          v-if="filteredTableRows.length > TABLE_PAGE_SIZE"
          class="px-5 py-3 border-t border-slate-200 flex items-center justify-between"
        >
          <p class="text-sm text-slate-500">
            {{ filteredTableRows.length }} çalışan &middot; Sayfa {{ tablePage }}/{{ totalTablePages }}
          </p>
          <div class="flex gap-2">
            <button
              :disabled="tablePage <= 1"
              @click="tablePage--"
              class="px-3 py-1.5 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-40 transition-colors"
            >
              Önceki
            </button>
            <button
              :disabled="tablePage >= totalTablePages"
              @click="tablePage++"
              class="px-3 py-1.5 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-40 transition-colors"
            >
              Sonraki
            </button>
          </div>
        </div>
      </div>

      <!-- ── Section 5: Gemini LLM Yorumu ───────────────────────────────── -->
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mb-8">
        <div class="flex items-center justify-between p-5 border-b border-slate-100">
          <div class="flex items-center gap-2">
            <SparklesIcon class="w-5 h-5 text-violet-500" />
            <h2 class="text-lg font-bold text-slate-900">Gemini AI Yorumu</h2>
          </div>
          <div class="flex items-center gap-2">
            <span
              v-if="data.gemini_used"
              class="text-xs bg-violet-50 text-violet-600 font-semibold px-2.5 py-1 rounded-full border border-violet-200 flex items-center gap-1"
            >
              <SparklesIcon class="w-3.5 h-3.5" /> Gemini ✓
            </span>
            <span
              v-else
              class="text-xs bg-amber-50 text-amber-600 font-semibold px-2.5 py-1 rounded-full border border-amber-200"
            >
              Deterministik
            </span>
            <button
              @click="showNarrativePanel = !showNarrativePanel"
              class="flex items-center gap-1.5 text-sm font-medium text-violet-600 hover:text-violet-800 transition-colors"
            >
              {{ showNarrativePanel ? 'Gizle' : 'Göster' }}
              <ChevronDownIcon class="w-4 h-4 transition-transform" :class="{ 'rotate-180': showNarrativePanel }" />
            </button>
          </div>
        </div>

        <!-- Narrative sections (collapsible) -->
        <div v-show="showNarrativePanel" class="p-5">
          <div v-if="narrativeSections.length > 0" class="grid grid-cols-1 gap-4 mb-6">
            <div
              v-for="(section, i) in narrativeSections"
              :key="i"
              class="rounded-xl border border-violet-100 bg-gradient-to-br from-violet-50/40 to-white p-4"
            >
              <h4 v-if="section.title" class="text-sm font-bold text-violet-900 mb-2 flex items-center gap-2">
                <span class="w-5 h-5 rounded-full bg-violet-100 text-violet-600 text-xs flex items-center justify-center font-bold flex-shrink-0">
                  {{ sectionLabel(i) }}
                </span>
                {{ section.title }}
              </h4>
              <p class="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">{{ section.body }}</p>
            </div>
          </div>
          <div v-else-if="!data.narrative" class="py-6 text-center text-slate-400 text-sm">
            Narrative verisi bulunamadı. Endpoint'ten dönen <code class="bg-slate-100 px-1 rounded">narrative</code> null.
          </div>

          <!-- Recommendations -->
          <div v-if="data.recommendations && data.recommendations.length">
            <div class="flex items-center gap-2 mb-3">
              <BoltIcon class="w-4 h-4 text-amber-500" />
              <h3 class="text-sm font-bold text-slate-800">Aksiyon Önerileri</h3>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              <div
                v-for="(rec, i) in data.recommendations"
                :key="i"
                class="flex gap-3 p-4 rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white hover:border-violet-300 hover:shadow-sm transition-all"
              >
                <div
                  class="w-7 h-7 rounded-full bg-violet-100 text-violet-600 text-xs font-bold flex items-center justify-center flex-shrink-0"
                >
                  {{ sectionLabel(i) }}
                </div>
                <div>
                  <p class="text-sm font-semibold text-slate-800">{{ rec.title }}</p>
                  <p v-if="rec.description" class="text-xs text-slate-500 mt-1 leading-relaxed">{{ rec.description }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Collapsed preview -->
        <div v-if="!showNarrativePanel && data.narrative" class="px-5 pb-4">
          <p class="text-xs text-slate-400 line-clamp-2">
            {{ narrativePreview }}
          </p>
        </div>
      </div>

    </template>

    <!-- Fixed Gemini button (bottom-right) -->
    <div
      v-if="!isLoading && !errorMsg && !showNarrativePanel"
      class="fixed bottom-6 right-6 z-50"
    >
      <button
        @click="showNarrativePanel = true; scrollToNarrative()"
        class="flex items-center gap-2 bg-violet-600 hover:bg-violet-700 text-white font-medium px-4 py-3 rounded-full shadow-lg shadow-violet-600/30 transition-all hover:scale-105"
      >
        <SparklesIcon class="w-5 h-5" />
        <span class="text-sm">Gemini ile Yorumla</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  ArrowPathIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ExclamationCircleIcon,
  UserGroupIcon,
  SparklesIcon,
  BoltIcon,
  TableCellsIcon,
  InformationCircleIcon,
  ChartBarIcon,
  ChevronDownIcon,
  ShieldExclamationIcon,
} from '@heroicons/vue/24/outline'
import { apiClient } from '@/services/api/client'

// ── Types ────────────────────────────────────────────────────────────────────
interface RiskDist {
  risky: number
  safe: number
  total: number
  risky_pct: number
}

interface DeptChart {
  total: number
  perf_drop: RiskDist
  burnout: RiskDist
  resignation: RiskDist
  high_risk: RiskDist
}

interface RiskDefinition {
  key: string
  target: string
  label: string
  color: string
  description: string
  boundary: string
  signals: string[]
}

interface EmployeeRow {
  code: string
  name: string
  department: string
  team: string
  perf_drop: number
  burnout: number
  resignation: number
  high_risk: number
  composite: number
}

interface KpiCard {
  title: string
  value: string
  trend: string
  trendColor: string
  comparison: string
}

interface Recommendation {
  title: string
  description: string
  icon: string
}

interface InsightsData {
  kpis: KpiCard[]
  risk_definitions: RiskDefinition[]
  chart_data: {
    sales: DeptChart
    software: DeptChart
  }
  employee_table: EmployeeRow[]
  stats: {
    total: number
    high_risk: number
    low_risk: number
    avg_composite: number
    avg_sales: number
    avg_sw: number
    sales_total: number
    sw_total: number
  }
  narrative: string | null
  recommendations: Recommendation[]
  gemini_used: boolean
}

const EMPTY_RISK_DIST: RiskDist = { risky: 0, safe: 0, total: 0, risky_pct: 0 }

const EMPTY_DATA: InsightsData = {
  kpis: [],
  risk_definitions: [],
  chart_data: {
    sales: { total: 0, perf_drop: { ...EMPTY_RISK_DIST }, burnout: { ...EMPTY_RISK_DIST }, resignation: { ...EMPTY_RISK_DIST }, high_risk: { ...EMPTY_RISK_DIST } },
    software: { total: 0, perf_drop: { ...EMPTY_RISK_DIST }, burnout: { ...EMPTY_RISK_DIST }, resignation: { ...EMPTY_RISK_DIST }, high_risk: { ...EMPTY_RISK_DIST } },
  },
  employee_table: [],
  stats: { total: 0, high_risk: 0, low_risk: 0, avg_composite: 0, avg_sales: 0, avg_sw: 0, sales_total: 0, sw_total: 0 },
  narrative: null,
  recommendations: [],
  gemini_used: false,
}

// ── State ────────────────────────────────────────────────────────────────────
const isLoading = ref(true)
const errorMsg = ref<string | null>(null)
const data = ref<InsightsData>({ ...EMPTY_DATA })
const showNarrativePanel = ref(false)

// ── Icons for KPI cards (positional) ─────────────────────────────────────────
const kpiIcons = [UserGroupIcon, ShieldExclamationIcon, ArrowTrendingUpIcon, ArrowTrendingDownIcon]
const kpiIconColors = ['text-slate-400', 'text-red-400', 'text-emerald-500', 'text-amber-500']

// ── Fetch ────────────────────────────────────────────────────────────────────
const fetchInsights = async () => {
  isLoading.value = true
  errorMsg.value = null
  try {
    const { data: resp } = await apiClient.get('/admin/uploads/ai-insights')
    data.value = resp as InsightsData
    // Auto-open narrative panel if narrative available
    if (resp.narrative) showNarrativePanel.value = true
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail || e?.message || 'Bilinmeyen hata'
  } finally {
    isLoading.value = false
  }
}

onMounted(fetchInsights)

// ── Narrative parsing ────────────────────────────────────────────────────────
const narrativeSections = computed(() => {
  if (!data.value.narrative) return []
  const sections: { title: string; body: string }[] = []
  const lines = data.value.narrative.split('\n')
  let current = { title: '', body: '' }
  for (const line of lines) {
    if (line.startsWith('###') || line.startsWith('##')) {
      if (current.title || current.body.trim()) sections.push({ ...current })
      current = { title: line.replace(/^#+\s*/, '').trim(), body: '' }
    } else {
      current.body += (current.body ? '\n' : '') + line
    }
  }
  if (current.title || current.body.trim()) sections.push(current)
  return sections
})

const narrativePreview = computed(() => {
  if (!data.value.narrative) return ''
  return data.value.narrative.replace(/^#+\s*.+$/gm, '').replace(/\n{2,}/g, ' ').trim().slice(0, 200) + '...'
})

// ── Chart data helper ─────────────────────────────────────────────────────────
function chartDist(dept: 'sales' | 'software', key: string): RiskDist {
  const d = data.value.chart_data?.[dept] as any
  return (d?.[key] as RiskDist) ?? { ...EMPTY_RISK_DIST }
}

// ── Table filters ─────────────────────────────────────────────────────────────
const tableSearch = ref('')
const tableDeptFilter = ref('')
const tablePage = ref(1)
const TABLE_PAGE_SIZE = 15

const filteredTableRows = computed(() => {
  const q = tableSearch.value.toLowerCase()
  tablePage.value = 1
  return (data.value.employee_table ?? []).filter((e: EmployeeRow) => {
    const matchSearch = !q || e.name?.toLowerCase().includes(q) || e.code?.toLowerCase().includes(q)
    const matchDept = !tableDeptFilter.value || e.department === tableDeptFilter.value
    return matchSearch && matchDept
  })
})

const totalTablePages = computed(() => Math.max(1, Math.ceil(filteredTableRows.value.length / TABLE_PAGE_SIZE)))

const visibleTableRows = computed(() => {
  const start = (tablePage.value - 1) * TABLE_PAGE_SIZE
  return filteredTableRows.value.slice(start, start + TABLE_PAGE_SIZE)
})

// ── Scroll to narrative ───────────────────────────────────────────────────────
function scrollToNarrative() {
  setTimeout(() => {
    const el = document.getElementById('narrative-section')
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, 50)
}

// ── Utility: initials ─────────────────────────────────────────────────────────
function sectionLabel(i: string | number): string {
  return String(Number(i) + 1)
}

function initials(name: string) {
  return (name || '?')
    .split(' ')
    .map((n: string) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

// ── Color helpers: risk % badges ─────────────────────────────────────────────
function riskPctBadge(pct: number): string {
  if (pct >= 50) return 'bg-red-100 text-red-700'
  if (pct >= 25) return 'bg-amber-100 text-amber-700'
  return 'bg-emerald-100 text-emerald-700'
}

function compositeBarColor(pct: number): string {
  if (pct >= 50) return 'bg-red-500'
  if (pct >= 25) return 'bg-amber-500'
  return 'bg-emerald-500'
}

// ── Color helpers: risk definition cards ─────────────────────────────────────
function riskDefBorderClass(color: string): string {
  const map: Record<string, string> = {
    rose: 'border-l-4 border-l-rose-400',
    amber: 'border-l-4 border-l-amber-400',
    orange: 'border-l-4 border-l-orange-400',
    purple: 'border-l-4 border-l-violet-400',
    violet: 'border-l-4 border-l-violet-400',
  }
  return map[color] ?? 'border-l-4 border-l-slate-300'
}

function riskDefTopBarClass(color: string): string {
  const map: Record<string, string> = {
    rose: 'bg-rose-400',
    amber: 'bg-amber-400',
    orange: 'bg-orange-400',
    purple: 'bg-violet-400',
    violet: 'bg-violet-400',
  }
  return map[color] ?? 'bg-slate-300'
}

function riskDefBadgeClass(color: string): string {
  const map: Record<string, string> = {
    rose: 'bg-rose-100 text-rose-700',
    amber: 'bg-amber-100 text-amber-700',
    orange: 'bg-orange-100 text-orange-700',
    purple: 'bg-violet-100 text-violet-700',
    violet: 'bg-violet-100 text-violet-700',
  }
  return map[color] ?? 'bg-slate-100 text-slate-600'
}

function riskDefBgClass(color: string): string {
  const map: Record<string, string> = {
    rose: 'bg-rose-50',
    amber: 'bg-amber-50',
    orange: 'bg-orange-50',
    purple: 'bg-violet-50',
    violet: 'bg-violet-50',
  }
  return map[color] ?? 'bg-slate-50'
}

function riskDefIconClass(color: string): string {
  const map: Record<string, string> = {
    rose: 'text-rose-600',
    amber: 'text-amber-600',
    orange: 'text-orange-600',
    purple: 'text-violet-600',
    violet: 'text-violet-600',
  }
  return map[color] ?? 'text-slate-500'
}

function riskDefDotClass(color: string): string {
  const map: Record<string, string> = {
    rose: 'bg-rose-400',
    amber: 'bg-amber-400',
    orange: 'bg-orange-400',
    purple: 'bg-violet-400',
    violet: 'bg-violet-400',
  }
  return map[color] ?? 'bg-slate-300'
}

function riskBarRiskyClass(color: string): string {
  const map: Record<string, string> = {
    rose: 'bg-rose-400',
    amber: 'bg-amber-400',
    orange: 'bg-orange-400',
    purple: 'bg-violet-400',
    violet: 'bg-violet-400',
  }
  return map[color] ?? 'bg-red-400'
}
</script>
