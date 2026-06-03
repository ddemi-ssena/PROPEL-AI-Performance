<template>
  <div>
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold text-slate-900 tracking-tight">Yapay Zeka İçgörüleri</h1>
        <p class="text-slate-500 mt-1">ML modeli + Gemini AI ile oluşturulan performans raporu.</p>
      </div>
      <button @click="fetchInsights" :disabled="isLoading"
        class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2.5 rounded-lg transition-colors flex items-center gap-2 shadow-sm shadow-blue-600/20 disabled:opacity-50">
        <ArrowPathIcon class="w-5 h-5" :class="{'animate-spin': isLoading}" />
        {{ isLoading ? 'Analiz ediliyor...' : 'Yeniden Oluştur' }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="flex flex-col items-center justify-center py-20 gap-4">
      <div class="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
      <p class="text-slate-500 text-sm">ML modelleri çalıştırılıyor ve Gemini rapor oluşturuyor...</p>
    </div>

    <template v-else>
      <!-- KPI Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        <div v-for="kpi in kpis" :key="kpi.title"
          class="bg-white rounded-xl p-5 shadow-sm border border-slate-200">
          <div class="flex items-start justify-between mb-3">
            <p class="text-sm font-medium text-slate-500">{{ kpi.title }}</p>
            <component :is="kpi.icon" class="w-5 h-5 flex-shrink-0" :class="kpi.iconColor" />
          </div>
          <div class="flex items-baseline gap-2 mb-1">
            <span class="text-3xl font-bold text-slate-900">{{ kpi.value }}</span>
            <span class="text-sm font-semibold" :class="kpi.trendColor">{{ kpi.trend }}</span>
          </div>
          <p class="text-xs text-slate-400">{{ kpi.comparison }}</p>
        </div>
      </div>

      <!-- Risk + Gemini Rapor -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <!-- Risk Donut -->
        <div class="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
          <h3 class="text-lg font-bold text-slate-900 mb-5">Risk Dağılımı (ML)</h3>
          <div class="h-52 flex items-center justify-center relative">
            <div class="absolute inset-0 flex items-center justify-center flex-col pointer-events-none">
              <span class="text-3xl font-bold text-slate-900">{{ stats.total }}</span>
              <span class="text-xs text-slate-500">Çalışan</span>
            </div>
            <DoughnutChart :labels="riskLabels" :data="riskData" :colors="riskColors" />
          </div>
          <div class="mt-4 space-y-2">
            <div class="flex justify-between text-sm">
              <span class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-red-500 inline-block"></span>Yüksek Risk</span>
              <span class="font-bold text-red-600">{{ stats.high_risk }} çalışan</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-emerald-500 inline-block"></span>Düşük Risk</span>
              <span class="font-bold text-emerald-600">{{ stats.low_risk }} çalışan</span>
            </div>
          </div>
        </div>

        <!-- Gemini Narratif -->
        <div class="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div class="flex items-center justify-between p-5 border-b border-slate-100">
            <div class="flex items-center gap-2">
              <SparklesIcon class="w-5 h-5 text-violet-500" />
              <h3 class="text-lg font-bold text-slate-900">Gemini AI Raporu</h3>
            </div>
            <span v-if="geminiUsed" class="text-xs bg-violet-50 text-violet-600 font-medium px-2 py-1 rounded-full border border-violet-200">
              Gemini {{ geminiModel }}
            </span>
            <span v-else class="text-xs bg-amber-50 text-amber-600 font-medium px-2 py-1 rounded-full border border-amber-200">
              Deterministik (API kapalı)
            </span>
          </div>
          <div class="p-5 overflow-y-auto max-h-96">
            <div v-if="narrative" class="prose prose-sm prose-slate max-w-none">
              <div v-for="(section, i) in narrativeSections" :key="i" class="mb-5">
                <h4 v-if="section.title" class="text-sm font-bold text-slate-800 mb-2 flex items-center gap-1.5">
                  <span class="w-5 h-5 rounded-full bg-violet-100 text-violet-600 text-xs flex items-center justify-center font-bold">{{ i + 1 }}</span>
                  {{ section.title }}
                </h4>
                <div class="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">{{ section.body }}</div>
              </div>
            </div>
            <div v-else class="space-y-3">
              <div v-for="rec in recommendations" :key="rec.title" class="flex gap-3 p-3 rounded-lg bg-slate-50">
                <LightBulbIcon class="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p class="text-sm font-semibold text-slate-800">{{ rec.title }}</p>
                  <p v-if="rec.description" class="text-xs text-slate-500 mt-0.5">{{ rec.description }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Aksiyon Önerileri (Gemini'den çıkarılan) -->
      <div v-if="recommendations.length" class="bg-white rounded-xl p-6 shadow-sm border border-slate-200 mb-8">
        <div class="flex items-center gap-2 mb-5">
          <BoltIcon class="w-5 h-5 text-amber-500" />
          <h3 class="text-lg font-bold text-slate-900">Aksiyon Önerileri</h3>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="(rec, i) in recommendations" :key="i"
            class="flex gap-3 p-4 rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white hover:border-blue-300 transition-colors">
            <div class="w-7 h-7 rounded-full bg-blue-100 text-blue-600 text-xs font-bold flex items-center justify-center flex-shrink-0">
              {{ i + 1 }}
            </div>
            <div>
              <p class="text-sm font-semibold text-slate-800">{{ rec.title }}</p>
              <p v-if="rec.description" class="text-xs text-slate-500 mt-1">{{ rec.description }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Tüm Çalışan Tablosu -->
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div class="flex items-center justify-between p-5 border-b border-slate-200">
          <div class="flex items-center gap-2">
            <TableCellsIcon class="w-5 h-5 text-slate-400" />
            <h3 class="text-lg font-bold text-slate-900">Tüm Çalışan ML Raporu</h3>
          </div>
          <div class="flex items-center gap-3">
            <input v-model="tableSearch" type="text" placeholder="İsim veya kod ara..."
              class="text-sm bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-blue-500 focus:outline-none w-52" />
            <select v-model="tableRiskFilter"
              class="text-sm bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-blue-500 focus:outline-none">
              <option value="">Tüm Riskler</option>
              <option value="High">Yüksek Risk</option>
              <option value="Low">Düşük Risk</option>
            </select>
            <select v-model="tableDeptFilter"
              class="text-sm bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-blue-500 focus:outline-none">
              <option value="">Tüm Departmanlar</option>
              <option value="Satış">Satış</option>
              <option value="Yazılım">Yazılım</option>
            </select>
          </div>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <th class="px-5 py-3">Çalışan</th>
                <th class="px-5 py-3">Departman / Takım</th>
                <th class="px-5 py-3">Performans</th>
                <th class="px-5 py-3">Risk (ML)</th>
                <th class="px-5 py-3">Ana Sürücü</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="emp in visibleTableRows" :key="emp.code" class="hover:bg-slate-50 transition-colors">
                <td class="px-5 py-3">
                  <div class="flex items-center gap-2.5">
                    <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                      :class="emp.department === 'Satış' ? 'bg-emerald-500' : 'bg-indigo-500'">
                      {{ initials(emp.name) }}
                    </div>
                    <div>
                      <p class="text-sm font-medium text-slate-900">{{ emp.name }}</p>
                      <p class="text-xs text-slate-400">{{ emp.code }}</p>
                    </div>
                  </div>
                </td>
                <td class="px-5 py-3">
                  <span class="text-xs font-medium px-2 py-0.5 rounded-full"
                    :class="emp.department === 'Satış' ? 'bg-emerald-50 text-emerald-700' : 'bg-indigo-50 text-indigo-700'">
                    {{ emp.department }}
                  </span>
                  <p class="text-xs text-slate-400 mt-0.5">{{ emp.team }}</p>
                </td>
                <td class="px-5 py-3">
                  <div class="flex items-center gap-2">
                    <div class="w-20 bg-slate-200 rounded-full h-1.5 overflow-hidden">
                      <div class="h-full rounded-full" :class="perfColor(emp.performance_score)"
                        :style="{ width: `${emp.performance_score}%` }"></div>
                    </div>
                    <span class="text-sm font-bold text-slate-700">{{ emp.performance_score }}</span>
                  </div>
                </td>
                <td class="px-5 py-3">
                  <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border"
                    :class="emp.risk_level === 'High'
                      ? 'bg-red-50 text-red-700 border-red-200'
                      : 'bg-emerald-50 text-emerald-700 border-emerald-200'">
                    <span class="w-1.5 h-1.5 rounded-full bg-current"></span>
                    {{ emp.risk_level === 'High' ? 'Yüksek' : 'Düşük' }}
                  </span>
                </td>
                <td class="px-5 py-3 text-xs text-slate-500 max-w-[180px] truncate">{{ emp.top_driver }}</td>
              </tr>
              <tr v-if="filteredTableRows.length === 0">
                <td colspan="5" class="px-5 py-10 text-center text-slate-400 text-sm">Eşleşen çalışan bulunamadı.</td>
              </tr>
            </tbody>
          </table>
        </div>
        <!-- Pagination -->
        <div v-if="filteredTableRows.length > TABLE_PAGE_SIZE" class="px-5 py-3 border-t border-slate-200 flex items-center justify-between">
          <p class="text-sm text-slate-500">{{ filteredTableRows.length }} çalışan · Sayfa {{ tablePage }}/{{ totalTablePages }}</p>
          <div class="flex gap-2">
            <button :disabled="tablePage <= 1" @click="tablePage--"
              class="px-3 py-1.5 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-40">Önceki</button>
            <button :disabled="tablePage >= totalTablePages" @click="tablePage++"
              class="px-3 py-1.5 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-40">Sonraki</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  ArrowPathIcon, ArrowTrendingUpIcon, ArrowTrendingDownIcon,
  ExclamationCircleIcon, LightBulbIcon, UserGroupIcon,
  SparklesIcon, BoltIcon, TableCellsIcon,
} from '@heroicons/vue/24/outline'
import DoughnutChart from '@/components/charts/DoughnutChart.vue'
import { apiClient } from '@/services/api/client'

// ── Veri ──────────────────────────────────────────────────────────────────
const isLoading = ref(true)
const kpis = ref<any[]>([])
const riskLabels = ['Düşük Risk', 'Orta Risk', 'Yüksek Risk']
const riskData = ref<number[]>([0, 0, 0])
const riskColors = ['#22c55e', '#f59e0b', '#ef4444']
const recommendations = ref<any[]>([])
const narrative = ref<string | null>(null)
const geminiUsed = ref(false)
const geminiModel = ref('gemini-1.5-flash')
const employeeTable = ref<any[]>([])
const stats = ref({ total: 0, high_risk: 0, low_risk: 0, avg_perf_all: 0, avg_perf_sales: 0, avg_perf_sw: 0 })

const iconMap: Record<string, any> = {
  ArrowTrendingUpIcon, ArrowTrendingDownIcon,
  ExclamationCircleIcon, LightBulbIcon, UserGroupIcon,
}

const fetchInsights = async () => {
  isLoading.value = true
  try {
    const { data } = await apiClient.get('/admin/uploads/ai-insights')

    kpis.value = data.kpis.map((kpi: any) => {
      let icon = UserGroupIcon
      if (kpi.title.includes('Riskli') && kpi.trendColor?.includes('red')) icon = ExclamationCircleIcon
      else if (kpi.title.includes('Performans')) icon = ArrowTrendingUpIcon
      else if (kpi.title.includes('Güvenli')) icon = ArrowTrendingUpIcon
      return { ...kpi, icon, iconColor: kpi.trendColor }
    })

    riskData.value = data.riskData
    recommendations.value = data.recommendations.map((r: any) => ({
      ...r,
      icon: iconMap[r.icon] || LightBulbIcon,
    }))
    narrative.value = data.narrative || null
    geminiUsed.value = data.gemini_used
    employeeTable.value = data.employee_table || []
    stats.value = data.stats || stats.value
  } catch (e) {
    console.error('[AIInsights] fetch error', e)
  } finally {
    isLoading.value = false
  }
}

onMounted(fetchInsights)

// ── Gemini narratifi bölümlere ayır ───────────────────────────────────────
const narrativeSections = computed(() => {
  if (!narrative.value) return []
  const sections: { title: string; body: string }[] = []
  const lines = narrative.value.split('\n')
  let current = { title: '', body: '' }
  for (const line of lines) {
    if (line.startsWith('###')) {
      if (current.body.trim()) sections.push({ ...current })
      current = { title: line.replace(/^#+\s*/, '').trim(), body: '' }
    } else {
      current.body += (current.body ? '\n' : '') + line
    }
  }
  if (current.body.trim()) sections.push(current)
  return sections
})

// ── Tablo filtreleme ───────────────────────────────────────────────────────
const tableSearch = ref('')
const tableRiskFilter = ref('')
const tableDeptFilter = ref('')
const tablePage = ref(1)
const TABLE_PAGE_SIZE = 20

const filteredTableRows = computed(() => {
  const q = tableSearch.value.toLowerCase()
  return employeeTable.value.filter((e: any) => {
    const matchSearch = !q || e.name?.toLowerCase().includes(q) || e.code?.toLowerCase().includes(q)
    const matchRisk = !tableRiskFilter.value || e.risk_level === tableRiskFilter.value
    const matchDept = !tableDeptFilter.value || e.department === tableDeptFilter.value
    return matchSearch && matchRisk && matchDept
  })
})

const totalTablePages = computed(() => Math.max(1, Math.ceil(filteredTableRows.value.length / TABLE_PAGE_SIZE)))

const visibleTableRows = computed(() => {
  const start = (tablePage.value - 1) * TABLE_PAGE_SIZE
  return filteredTableRows.value.slice(start, start + TABLE_PAGE_SIZE)
})

// ── Yardımcı ──────────────────────────────────────────────────────────────
function initials(name: string) {
  return (name || '?').split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()
}

function perfColor(score: number) {
  if (score >= 80) return 'bg-emerald-500'
  if (score >= 60) return 'bg-blue-500'
  if (score >= 40) return 'bg-amber-500'
  return 'bg-red-500'
}
</script>
