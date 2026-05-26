<template>
  <div class="pb-10">
    <!-- Header -->
    <div class="flex items-start justify-between mb-8">
      <div>
        <p class="text-xs font-bold text-emerald-600 uppercase tracking-widest mb-1">Satış Departmanı</p>
        <h1 class="text-2xl font-bold text-slate-900">360° Geri Bildirim Raporu</h1>
        <p class="text-slate-500 mt-1 text-sm">
          {{ period }} · {{ nlpSummary?.analyzed_employee_count ?? '–' }} çalışan analiz edildi
        </p>
      </div>
      <button @click="loadAll" :disabled="loading" class="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl text-slate-600 text-sm font-medium hover:bg-slate-50 transition-colors disabled:opacity-50">
        <ArrowPathIcon class="w-4 h-4" :class="{ 'animate-spin': loading }" />
        Yenile
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-24">
      <div class="flex flex-col items-center gap-4">
        <div class="w-12 h-12 rounded-full border-4 border-emerald-100 border-t-emerald-500 animate-spin"></div>
        <p class="text-slate-500 text-sm font-medium">Veriler yükleniyor…</p>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-2xl p-8 text-center">
      <ExclamationTriangleIcon class="w-10 h-10 text-red-400 mx-auto mb-3" />
      <p class="text-red-700 font-semibold">{{ error }}</p>
      <button @click="loadAll" class="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 transition-colors">
        Tekrar Dene
      </button>
    </div>

    <template v-else-if="nlpSummary">
      <!-- KPI Overview Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <p class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Analiz Edilen</p>
          <p class="text-3xl font-bold text-slate-900">{{ nlpSummary.analyzed_employee_count }}</p>
          <p class="text-xs text-slate-400 mt-1">çalışan</p>
        </div>
        <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <p class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Ort. Motivasyon</p>
          <p class="text-3xl font-bold" :class="scoreColor(nlpSummary.avg_motivation_score)">
            {{ nlpSummary.avg_motivation_score != null ? nlpSummary.avg_motivation_score.toFixed(1) : '–' }}
          </p>
          <p class="text-xs text-slate-400 mt-1">/ 5.0</p>
        </div>
        <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <p class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Uçuş Riski</p>
          <p class="text-3xl font-bold" :class="nlpSummary.high_flight_risk_count > 0 ? 'text-amber-600' : 'text-emerald-600'">
            {{ nlpSummary.high_flight_risk_count }}
          </p>
          <p class="text-xs text-slate-400 mt-1">kişi yüksek risk</p>
        </div>
        <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <p class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Ort. İşbirliği</p>
          <p class="text-3xl font-bold" :class="scoreColor(nlpSummary.avg_collaboration_score)">
            {{ nlpSummary.avg_collaboration_score != null ? nlpSummary.avg_collaboration_score.toFixed(1) : '–' }}
          </p>
          <p class="text-xs text-slate-400 mt-1">/ 5.0</p>
        </div>
      </div>

      <!-- Headline + Signal Strips -->
      <div class="bg-gradient-to-br from-emerald-600 to-teal-700 rounded-2xl p-6 mb-8 shadow-lg shadow-emerald-900/20">
        <div class="flex items-start gap-4">
          <div class="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center flex-shrink-0">
            <SparklesIcon class="w-5 h-5 text-white" />
          </div>
          <div class="flex-1">
            <p class="text-emerald-100 text-xs font-bold uppercase tracking-widest mb-2">Departman Sinyali</p>
            <p class="text-white text-lg font-semibold">{{ nlpSummary.headline }}</p>
            <p v-if="nlpSummary.recommended_action" class="text-emerald-200 text-sm mt-2">
              Öneri: {{ nlpSummary.recommended_action }}
            </p>
          </div>
        </div>

        <div class="mt-5 grid grid-cols-3 gap-3">
          <div class="bg-white/10 rounded-xl p-3">
            <p class="text-emerald-200 text-[10px] font-bold uppercase tracking-wider mb-2">Güçlü Yönler</p>
            <ul class="space-y-1">
              <li v-for="s in nlpSummary.top_strengths" :key="s" class="text-white text-xs flex items-center gap-1.5">
                <CheckCircleIcon class="w-3.5 h-3.5 text-emerald-300 flex-shrink-0" />
                {{ s }}
              </li>
            </ul>
          </div>
          <div class="bg-white/10 rounded-xl p-3">
            <p class="text-amber-200 text-[10px] font-bold uppercase tracking-wider mb-2">Risk Alanları</p>
            <ul class="space-y-1">
              <li v-for="r in nlpSummary.top_risk_areas" :key="r" class="text-white text-xs flex items-center gap-1.5">
                <ExclamationTriangleIcon class="w-3.5 h-3.5 text-amber-300 flex-shrink-0" />
                {{ r }}
              </li>
            </ul>
          </div>
          <div class="bg-white/10 rounded-xl p-3">
            <p class="text-blue-200 text-[10px] font-bold uppercase tracking-wider mb-2">Destek İhtiyaçları</p>
            <ul class="space-y-1">
              <li v-for="n in nlpSummary.top_support_needs" :key="n" class="text-white text-xs flex items-center gap-1.5">
                <LightBulbIcon class="w-3.5 h-3.5 text-blue-300 flex-shrink-0" />
                {{ n }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <!-- Report Sections -->
        <div v-if="deptReport" class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div class="p-5 border-b border-slate-100">
            <p class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Dönemsel Rapor</p>
            <h3 class="text-base font-bold text-slate-800">{{ deptReport.report_title }}</h3>
            <p class="text-sm text-slate-500 mt-1">{{ deptReport.report_summary }}</p>
          </div>
          <div class="divide-y divide-slate-100">
            <div v-for="section in deptReport.sections" :key="section.title" class="p-5">
              <p class="text-xs font-bold text-emerald-700 uppercase tracking-wider mb-2">{{ section.title }}</p>
              <ul class="space-y-1.5">
                <li v-for="item in section.items" :key="item" class="flex items-start gap-2 text-sm text-slate-700">
                  <span class="mt-1 w-1.5 h-1.5 rounded-full bg-emerald-400 flex-shrink-0"></span>
                  {{ item }}
                </li>
              </ul>
            </div>
          </div>
          <div v-if="deptReport.recommended_action" class="px-5 py-4 bg-amber-50 border-t border-amber-100">
            <p class="text-xs font-bold text-amber-700 uppercase tracking-wider mb-1">Önerilen Aksiyon</p>
            <p class="text-sm text-amber-800">{{ deptReport.recommended_action }}</p>
          </div>
        </div>

        <!-- Report Metrics -->
        <div v-if="deptReport" class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
          <p class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Temel Metrikler</p>
          <div class="space-y-3">
            <div v-for="m in deptReport.metrics" :key="m.label" class="flex items-center justify-between gap-3">
              <div class="flex-1">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-sm font-medium text-slate-700">{{ m.label }}</span>
                  <span class="text-sm font-bold" :class="metricValueColor(m.risk_level)">{{ m.display_value }}</span>
                </div>
                <div v-if="m.value != null" class="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div class="h-full rounded-full transition-all duration-500" :class="metricBarColor(m.risk_level)" :style="{ width: `${Math.min((m.value / 5) * 100, 100)}%` }"></div>
                </div>
                <p v-if="m.description" class="text-[11px] text-slate-400 mt-1">{{ m.description }}</p>
              </div>
            </div>
          </div>

          <!-- Avg scores radar-style bars -->
          <div class="mt-6 pt-5 border-t border-slate-100">
            <p class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Puan Profili</p>
            <div class="space-y-3">
              <div v-for="[label, val] in scoreProfile" :key="label">
                <div class="flex justify-between text-xs mb-1">
                  <span class="text-slate-600 font-medium">{{ label }}</span>
                  <span class="font-bold" :class="scoreColor(val)">{{ val != null ? val.toFixed(1) : '–' }}</span>
                </div>
                <div class="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div class="h-full rounded-full" :class="scoreBarColor(val)" :style="{ width: `${val != null ? (val / 5) * 100 : 0}%` }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Charts Row -->
      <div v-if="charts" class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <!-- Flight Risk Distribution -->
        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
          <p class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Uçuş Riski Dağılımı</p>
          <div class="space-y-3">
            <div v-for="pt in charts.flight_risk_distribution" :key="pt.label">
              <div class="flex justify-between text-xs mb-1">
                <span class="text-slate-600 capitalize">{{ riskLevelLabel(pt.label) }}</span>
                <span class="font-bold text-slate-800">{{ pt.value }}</span>
              </div>
              <div class="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                <div class="h-full rounded-full" :class="riskBarColor(pt.label)" :style="{ width: `${flightRiskPct(pt.value)}%` }"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Burnout Risk Distribution -->
        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
          <p class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Tükenmişlik Dağılımı</p>
          <div class="space-y-3">
            <div v-for="pt in charts.burnout_risk_distribution" :key="pt.label">
              <div class="flex justify-between text-xs mb-1">
                <span class="text-slate-600 capitalize">{{ riskLevelLabel(pt.label) }}</span>
                <span class="font-bold text-slate-800">{{ pt.value }}</span>
              </div>
              <div class="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                <div class="h-full rounded-full" :class="riskBarColor(pt.label)" :style="{ width: `${burnoutRiskPct(pt.value)}%` }"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Top Risk Themes -->
        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
          <p class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Öne Çıkan Risk Temaları</p>
          <div class="space-y-3">
            <div v-for="(pt, i) in charts.top_risk_themes" :key="pt.label">
              <div class="flex items-center gap-2 mb-1">
                <span class="w-4 h-4 rounded-sm flex-shrink-0 text-[10px] font-bold flex items-center justify-center" :class="themeIndexBg(Number(i))">{{ Number(i) + 1 }}</span>
                <span class="text-xs text-slate-700 flex-1 truncate">{{ pt.label }}</span>
                <span class="text-xs font-bold text-slate-500">{{ pt.value }}</span>
              </div>
              <div class="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div class="h-full rounded-full bg-rose-400" :style="{ width: `${themeBarPct(pt.value)}%` }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Motivation Trend Line Chart (SVG) -->
      <div v-if="charts && motivationTrendPts" class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 mb-8">
        <p class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Motivasyon Trendi</p>
        <svg :viewBox="`0 0 ${tW} 80`" class="w-full" style="height:80px;" preserveAspectRatio="none">
          <defs>
            <linearGradient id="motGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#10b981" stop-opacity="0.25" />
              <stop offset="100%" stop-color="#10b981" stop-opacity="0" />
            </linearGradient>
          </defs>
          <polygon v-if="motivationFillPts" :points="motivationFillPts" fill="url(#motGrad)" />
          <polyline :points="motivationTrendPts" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
          <circle v-for="(pt, i) in charts.motivation_trend" :key="i" :cx="tX(i, charts.motivation_trend.length)" :cy="tY(pt.value)" r="3.5" fill="#10b981" />
        </svg>
        <div class="flex justify-between mt-2">
          <span v-for="pt in charts.motivation_trend" :key="pt.label" class="text-[10px] text-slate-400">{{ pt.label }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  ArrowPathIcon,
  ExclamationTriangleIcon,
  SparklesIcon,
  CheckCircleIcon,
  LightBulbIcon,
} from '@heroicons/vue/24/outline'
import {
  feedbackApi,
  type DepartmentWeeklyNLPResponse,
  type Department360SummaryReportResponse,
  type DepartmentNLPChartsResponse,
  type TrendPoint,
  type DistributionPoint,
  type ThemePoint,
} from '@/services/api/feedback.api'

const loading = ref(false)
const error = ref<string | null>(null)
const nlpSummary = ref<DepartmentWeeklyNLPResponse | null>(null)
const deptReport = ref<Department360SummaryReportResponse | null>(null)
const charts = ref<DepartmentNLPChartsResponse | null>(null)

const period = computed(() => {
  if (!nlpSummary.value) return ''
  const months = ['Ocak','Şubat','Mart','Nisan','Mayıs','Haziran','Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık']
  return `${months[nlpSummary.value.period_month - 1]} ${nlpSummary.value.period_year} — Hafta ${nlpSummary.value.period_week}`
})

const scoreProfile = computed((): [string, number | undefined][] => {
  if (!nlpSummary.value) return []
  return [
    ['Motivasyon', nlpSummary.value.avg_motivation_score],
    ['Psikolojik Güven', nlpSummary.value.avg_psychological_safety_score],
    ['İşbirliği', nlpSummary.value.avg_collaboration_score],
    ['Gelişim Sinyali', nlpSummary.value.avg_growth_signal_score],
  ]
})

// chart helpers
const tW = 600
const tY = (v: number) => Math.round(70 - ((v / 5) * 60))
const tX = (i: number, total: number) => Math.round((i / (total - 1)) * tW)

const motivationTrendPts = computed(() => {
  const pts = charts.value?.motivation_trend
  if (!pts || pts.length < 2) return null
  return pts.map((p: TrendPoint, i: number) => `${tX(i, pts.length)},${tY(p.value)}`).join(' ')
})
const motivationFillPts = computed(() => {
  const pts = charts.value?.motivation_trend
  if (!pts || pts.length < 2) return null
  const line = pts.map((p: TrendPoint, i: number) => `${tX(i, pts.length)},${tY(p.value)}`).join(' ')
  return `${tX(0, pts.length)},80 ${line} ${tX(pts.length - 1, pts.length)},80`
})

const flightTotal = computed(() => charts.value?.flight_risk_distribution.reduce((a: number, b: DistributionPoint) => a + b.value, 0) ?? 1)
const burnoutTotal = computed(() => charts.value?.burnout_risk_distribution.reduce((a: number, b: DistributionPoint) => a + b.value, 0) ?? 1)
const maxTheme = computed(() => Math.max(...(charts.value?.top_risk_themes.map((t: ThemePoint) => t.value) ?? [1])))

const flightRiskPct = (v: number) => Math.round((v / flightTotal.value) * 100)
const burnoutRiskPct = (v: number) => Math.round((v / burnoutTotal.value) * 100)
const themeBarPct = (v: number) => Math.round((v / maxTheme.value) * 100)

function riskBarColor(label: string) {
  const l = label.toLowerCase()
  if (l === 'high' || l === 'yuksek' || l === 'yüksek') return 'bg-rose-500'
  if (l === 'medium' || l === 'orta') return 'bg-amber-400'
  return 'bg-emerald-400'
}
function riskLevelLabel(label: string) {
  const l = label.toLowerCase()
  if (l === 'high' || l === 'yuksek' || l === 'yüksek') return 'Yüksek'
  if (l === 'medium' || l === 'orta') return 'Orta'
  return 'Düşük'
}
function themeIndexBg(i: number) {
  const colors = ['bg-rose-100 text-rose-700', 'bg-amber-100 text-amber-700', 'bg-orange-100 text-orange-700', 'bg-slate-100 text-slate-600', 'bg-slate-100 text-slate-500']
  return colors[Math.min(i, colors.length - 1)]
}
function scoreColor(v?: number | null) {
  if (v == null) return 'text-slate-400'
  if (v >= 4) return 'text-emerald-600'
  if (v >= 3) return 'text-amber-600'
  return 'text-rose-600'
}
function scoreBarColor(v?: number | null) {
  if (v == null) return 'bg-slate-200'
  if (v >= 4) return 'bg-emerald-500'
  if (v >= 3) return 'bg-amber-400'
  return 'bg-rose-500'
}
function metricValueColor(riskLevel?: string) {
  if (riskLevel === 'high') return 'text-rose-600'
  if (riskLevel === 'medium') return 'text-amber-600'
  if (riskLevel === 'low') return 'text-emerald-600'
  return 'text-slate-700'
}
function metricBarColor(riskLevel?: string) {
  if (riskLevel === 'high') return 'bg-rose-500'
  if (riskLevel === 'medium') return 'bg-amber-400'
  return 'bg-emerald-500'
}

async function loadAll() {
  loading.value = true
  error.value = null
  try {
    const [summary, report, chartData] = await Promise.all([
      feedbackApi.getDepartmentWeeklyNlpSummary(),
      feedbackApi.getDepartment360SummaryReport(),
      feedbackApi.getDepartmentNlpCharts(),
    ])
    nlpSummary.value = summary
    deptReport.value = report
    charts.value = chartData
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'Veri yüklenirken bir hata oluştu.'
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)
</script>
