<template>
  <div>
    <!-- Loading -->
    <div v-if="isLoading" class="flex items-center justify-center h-64">
      <div class="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700">
      {{ error }}
    </div>

    <!-- Content -->
    <div v-else-if="employee">
      <!-- Header with Breadcrumb-like nav -->
      <div class="mb-8">
        <button @click="router.back()" class="flex items-center text-slate-500 hover:text-slate-900 mb-4 transition-colors">
          <ArrowLeftIcon class="w-4 h-4 mr-1" />
          Personel Listesine Dön
        </button>

        <div class="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <div class="flex items-center gap-6">
            <img :src="avatarUrl" class="w-24 h-24 rounded-full border-4 border-white shadow-md relative -my-2" />
            <div>
              <h1 class="text-3xl font-bold text-slate-900">{{ employee.user.full_name }}</h1>
              <div class="flex items-center gap-3 mt-1 text-slate-500">
                <span>{{ employee.position || 'Pozisyon belirtilmemiş' }}</span>
                <span class="w-1 h-1 bg-slate-300 rounded-full"></span>
                <span>{{ employee.department.name }}</span>
                <span v-if="employee.team" class="w-1 h-1 bg-slate-300 rounded-full"></span>
                <span v-if="employee.team">{{ employee.team }}</span>
              </div>
              <p class="text-sm text-slate-400 mt-1">{{ employee.user.email }}</p>
            </div>
          </div>

          <div class="flex gap-3">
            <div class="text-right px-4 border-r border-slate-100">
              <p class="text-xs text-slate-500 uppercase font-semibold">Risk Seviyesi</p>
              <span class="inline-flex items-center mt-1 px-2.5 py-0.5 rounded-full text-sm font-medium" :class="getRiskBadgeClasses(employee.risk_level)">
                 {{ getRiskLabel(employee.risk_level) }}
              </span>
            </div>
            <div class="text-right pl-2">
              <p class="text-xs text-slate-500 uppercase font-semibold">İşe Başlama</p>
              <p class="text-slate-900 font-medium mt-1">{{ formatHireDate(employee.hire_date) }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Stats Grid -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div v-for="stat in stats" :key="stat.title" class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
          <p class="text-sm font-medium text-slate-500 mb-1">{{ stat.title }}</p>
          <div class="flex items-baseline gap-2">
            <span class="text-2xl font-bold text-slate-900">{{ stat.value }}</span>
            <span v-if="stat.trend !== null" class="text-xs font-medium px-2 py-0.5 rounded-full"
              :class="stat.trend >= 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'">
              {{ stat.trend >= 0 ? '+' : '' }}{{ stat.trend }}
            </span>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Main Chart Area -->
        <div class="lg:col-span-2 space-y-8">
          <!-- Performance Chart -->
          <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div class="flex items-center justify-between mb-6">
              <h3 class="text-lg font-bold text-slate-900">KPI Performans Trendi</h3>
              <span class="text-xs text-slate-400">Son {{ chartLabels.length }} dönem</span>
            </div>
            <div v-if="chartLabels.length > 0" class="h-80">
              <TrendChart :labels="chartLabels" :data="chartData" />
            </div>
            <div v-else class="h-80 flex items-center justify-center text-slate-400 text-sm">
              KPI kaydı bulunamadı
            </div>
          </div>

          <!-- AI Insights -->
          <div class="bg-gradient-to-br from-indigo-900 to-slate-900 rounded-xl p-6 text-white shadow-lg overflow-hidden relative">
            <div class="absolute top-0 right-0 p-32 bg-blue-500/10 rounded-full blur-3xl"></div>

            <div class="relative z-10">
              <div class="flex items-center gap-3 mb-6">
                <SparklesIcon class="w-6 h-6 text-yellow-400" />
                <h3 class="text-lg font-bold">Performans Analizi</h3>
              </div>

              <div class="space-y-4">
                <div v-for="(insight, idx) in insights" :key="idx" class="bg-white/10 backdrop-blur-sm p-4 rounded-lg border border-white/10">
                  <p class="text-indigo-200 text-xs font-bold uppercase tracking-wider mb-1">{{ insight.category }}</p>
                  <p class="text-sm leading-relaxed">{{ insight.text }}</p>
                </div>
              </div>

              <div class="mt-6 pt-6 border-t border-white/10 flex items-center justify-between">
                 <p class="text-xs text-slate-400">Çalışan ID: {{ employee.external_employee_code || `EMP-${employee.id}` }}</p>
                 <span class="text-xs bg-white/10 text-slate-300 px-3 py-1.5 rounded-lg font-medium">
                   {{ employee.experience_years ? `${employee.experience_years} yıl deneyim` : 'Deneyim bilgisi yok' }}
                 </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Side Panel -->
        <div class="space-y-8">
           <!-- Motivation Score -->
           <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h3 class="text-lg font-bold text-slate-900 mb-6">Motivasyon Skoru</h3>
              <div class="relative pt-2 pb-6 flex justify-center">
                   <div class="w-48 h-24 overflow-hidden relative">
                       <div class="absolute top-0 left-0 w-full h-full bg-slate-100 rounded-t-full"></div>
                       <div
                         class="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-red-400 via-yellow-400 to-green-500 rounded-t-full origin-bottom transition-transform duration-1000"
                         :style="{ transform: `rotate(${gaugeRotation}deg)` }"
                       ></div>
                       <div class="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-40 h-40 bg-white rounded-full flex items-start justify-center pt-8">
                           <span class="text-4xl font-bold text-slate-900">{{ motivationDisplay }}</span>
                       </div>
                   </div>
              </div>
              <p class="text-center text-sm text-slate-500">{{ motivationLabel }}</p>
           </div>

           <!-- KPI Özeti -->
           <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h3 class="text-lg font-bold text-slate-900 mb-4">KPI Özeti</h3>
              <div v-if="topKpis.length > 0" class="space-y-4">
                  <div v-for="kpi in topKpis" :key="kpi.name">
                      <div class="flex justify-between text-xs mb-1">
                          <span class="font-medium text-slate-700 truncate max-w-[140px]">{{ kpi.name }}</span>
                          <span class="text-slate-500">{{ kpi.display }}</span>
                      </div>
                      <div class="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                          <div class="h-full bg-indigo-500 rounded-full transition-all duration-700" :style="{ width: `${kpi.pct}%` }"></div>
                      </div>
                  </div>
              </div>
              <p v-else class="text-sm text-slate-400">KPI kaydı bulunamadı</p>
           </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeftIcon, SparklesIcon } from '@heroicons/vue/24/outline'
import TrendChart from '@/components/charts/TrendChart.vue'
import { employeeApi } from '@/services/api/employee.api'
import { kpiApi } from '@/services/api/kpi.api'

const router = useRouter()
const route = useRoute()

const isLoading = ref(true)
const error = ref<string | null>(null)
const employee = ref<any>(null)
const kpiRecords = ref<any[]>([])

const avatarUrl = computed(() => {
  if (!employee.value) return ''
  const name = encodeURIComponent(employee.value.user.full_name)
  return `https://ui-avatars.com/api/?name=${name}&background=6366f1&color=fff`
})

// Stats cards
const stats = computed(() => {
  if (!employee.value) return []
  const ms = employee.value.latest_ms
  const ars = employee.value.latest_ars
  const mte = employee.value.latest_mte
  return [
    {
      title: 'Motivasyon Skoru',
      value: ms !== null && ms !== undefined ? ms.toFixed(1) : '—',
      trend: mte !== null && mte !== undefined ? parseFloat(mte.toFixed(2)) : null,
    },
    {
      title: 'İşten Ayrılma Riski',
      value: ars !== null && ars !== undefined ? `%${Math.round(ars)}` : '—',
      trend: null,
    },
    {
      title: 'Deneyim (yıl)',
      value: employee.value.experience_years !== null ? employee.value.experience_years : '—',
      trend: null,
    },
    {
      title: 'KPI Kaydı',
      value: kpiRecords.value.length.toString(),
      trend: null,
    },
  ]
})

// Performance trend chart — son 8 dönemi al, dönem başına ortalama KPI değeri
const chartLabels = computed(() => {
  const periods = getPeriodAverages()
  return periods.map(p => p.label)
})

const chartData = computed(() => {
  const periods = getPeriodAverages()
  return periods.map(p => p.avg)
})

function getPeriodAverages() {
  if (!kpiRecords.value.length) return []

  const map = new Map<string, number[]>()
  for (const rec of kpiRecords.value) {
    const key = rec.period_date.slice(0, 7) // YYYY-MM
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(rec.value)
  }

  const sorted = Array.from(map.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .slice(-8)

  return sorted.map(([key, vals]) => {
    const avg = vals.reduce((a, b) => a + b, 0) / vals.length
    const [year, month] = key.split('-')
    const monthNames = ['Oca','Şub','Mar','Nis','May','Haz','Tem','Ağu','Eyl','Eki','Kas','Ara']
    return { label: `${monthNames[parseInt(month) - 1]} ${year.slice(2)}`, avg: parseFloat(avg.toFixed(1)) }
  })
}

// Motivation gauge
const motivationDisplay = computed(() => {
  const ms = employee.value?.latest_ms
  return ms !== null && ms !== undefined ? ms.toFixed(1) : '—'
})

const gaugeRotation = computed(() => {
  const ms = employee.value?.latest_ms
  if (ms === null || ms === undefined) return -90
  // 0→-90deg (sol), 10→+90deg (sağ)
  return -90 + (ms / 10) * 180
})

const motivationLabel = computed(() => {
  const ms = employee.value?.latest_ms
  if (ms === null || ms === undefined) return 'Veri yok'
  if (ms >= 7.5) return 'Yüksek motivasyon, ekip içi iletişimi güçlü.'
  if (ms >= 5) return 'Orta düzey motivasyon, gelişim desteği önerilir.'
  return 'Düşük motivasyon, acil destek gerekebilir.'
})

// Top KPIs by avg value (normalize 0-100 for bar)
const topKpis = computed(() => {
  if (!kpiRecords.value.length) return []

  const map = new Map<string, { name: string; values: number[]; unit: string }>()
  for (const rec of kpiRecords.value) {
    const id = rec.kpi_id
    if (!map.has(id)) map.set(id, { name: rec.kpi?.name || `KPI #${id}`, values: [], unit: rec.kpi?.unit || '' })
    map.get(id)!.values.push(rec.value)
  }

  const entries = Array.from(map.values()).map(e => {
    const avg = e.values.reduce((a, b) => a + b, 0) / e.values.length
    return { name: e.name, avg, unit: e.unit }
  })

  const maxVal = Math.max(...entries.map(e => e.avg), 1)
  return entries.slice(0, 5).map(e => ({
    name: e.name,
    pct: Math.min(100, Math.round((e.avg / maxVal) * 100)),
    display: e.unit === 'percentage' ? `%${e.avg.toFixed(0)}` : e.avg.toFixed(1),
  }))
})

// Deterministic insights
const insights = computed(() => {
  if (!employee.value) return []
  const risk = employee.value.risk_level || 'Low'
  const ms = employee.value.latest_ms
  const mte = employee.value.latest_mte
  const exp = employee.value.experience_years

  const strengthTexts: Record<string, string> = {
    Low: 'Düşük risk profiliyle ekip içindeki istikrarlı performansını sürdürüyor.',
    Medium: 'Orta risk profiline rağmen temel KPI hedeflerini karşılamaya devam ediyor.',
    High: 'Yüksek risk durumuna karşın çalışma disiplinini korumaya çalışıyor.',
  }
  const devTexts = () => {
    if (mte !== null && mte !== undefined && mte < -0.1) return 'Motivasyon trendi son dönemlerde düşüş gösteriyor; birebir görüşme ve destek önerilir.'
    if (ms !== null && ms !== undefined && ms < 5) return 'Motivasyon skoru kritik seviyenin altında; iş yükü ve iş tatmini değerlendirilmeli.'
    return 'Toplantı katılımlarında daha aktif rol alması teşvik edilebilir.'
  }
  const forecastTexts = () => {
    if (risk === 'High') return 'Mevcut risk seviyesinde acil müdahale planı oluşturulması önerilir.'
    if (exp !== null && exp !== undefined && exp >= 3) return `${exp} yıllık deneyimiyle liderlik rollerine aday olabilir.`
    return 'Performans trendi devam ederse gelecek çeyrekte kıdemli pozisyon hedeflenebilir.'
  }

  return [
    { category: 'Güçlü Yön', text: strengthTexts[risk] || strengthTexts['Low'] },
    { category: 'Gelişim Alanı', text: devTexts() },
    { category: 'Tahmin', text: forecastTexts() },
  ]
})

function getRiskBadgeClasses(risk: string) {
  switch (risk) {
    case 'High': return 'bg-red-50 text-red-700 border border-red-200'
    case 'Medium': return 'bg-amber-50 text-amber-700 border border-amber-200'
    default: return 'bg-emerald-50 text-emerald-700 border border-emerald-200'
  }
}

function getRiskLabel(risk: string) {
  switch (risk) {
    case 'High': return 'Yüksek'
    case 'Medium': return 'Orta'
    default: return 'Düşük'
  }
}

function formatHireDate(dateStr: string | null) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' })
}

onMounted(async () => {
  const id = Number(route.params.id)
  if (!id) {
    error.value = 'Geçersiz çalışan ID.'
    isLoading.value = false
    return
  }
  try {
    const [emp, records] = await Promise.all([
      employeeApi.getEmployee(id),
      kpiApi.getEmployeeRecords(id).catch(() => []),
    ])
    employee.value = emp
    kpiRecords.value = records
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'Çalışan bilgisi yüklenemedi.'
  } finally {
    isLoading.value = false
  }
})
</script>
