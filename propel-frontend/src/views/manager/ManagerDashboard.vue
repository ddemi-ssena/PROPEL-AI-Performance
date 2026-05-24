<template>
  <div class="space-y-6 pb-10">
    <DashboardHeader
      v-model:period="selectedPeriod"
      v-model:comparison="selectedComparison"
      :department-name="departmentName"
      :member-count="teamMemberCount"
      :team-count="teamMetricCards.length"
      :health-score="departmentHealthScore"
      :performance-score="kpiAverageScore"
      :risk-level="dashboardRiskLevel"
      :trend-label="dashboardTrendLabel"
      @refresh="refreshDashboard"
      @export="handleDashboardExport"
      @share="handleDashboardShare"
    />

    <section class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      <KPICard
        v-for="card in kpiMetricCards"
        :key="card.title"
        :card="card"
      />
    </section>

    <section class="grid grid-cols-1 gap-6 xl:grid-cols-2">
      <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-600">Performans Skoru</p>
            <h3 class="mt-2 text-xl font-bold text-slate-900">Departman genel durumu</h3>
          </div>
          <span class="rounded-full border border-indigo-100 bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
            {{ selectedPeriodLabel }}
          </span>
        </div>

        <div class="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:items-center">
          <GaugeComparisonCard :gauge="performanceGauge" />
          <div class="space-y-4">
            <p class="text-sm leading-6 text-slate-600">
              {{ departmentReport?.report_summary || 'Departman performans ozeti veri geldikce burada gosterilecek.' }}
            </p>
            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div
                v-for="metric in previewMetrics"
                :key="metric.label"
                class="rounded-xl border border-slate-100 bg-slate-50 p-4"
              >
                <p class="text-xs text-slate-500">{{ metric.label }}</p>
                <p class="mt-2 text-xl font-bold text-slate-900">{{ metric.display_value }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-sky-600">Hedef Uyumu</p>
            <h3 class="mt-2 text-xl font-bold text-slate-900">Performans vs hedefler</h3>
          </div>
          <span class="rounded-full border border-sky-100 bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-700">
            KPI katmani
          </span>
        </div>

        <div class="mt-6 grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1fr)] lg:items-center">
          <GaugeComparisonCard :gauge="targetGauge" />
          <div class="space-y-3">
            <div
              v-for="row in kpiRows.slice(0, 4)"
              :key="row.name"
              class="rounded-xl border border-slate-100 bg-slate-50 p-4"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="truncate text-sm font-semibold text-slate-900">{{ row.name }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ row.description }}</p>
                </div>
                <div class="text-right">
                  <p class="text-sm font-bold text-slate-900">{{ row.averageDisplay }}</p>
                  <p class="text-xs text-slate-400">Hedef {{ row.targetDisplay }}</p>
                </div>
              </div>
            </div>
            <div v-if="!kpiRows.length" class="rounded-xl border border-dashed border-slate-200 p-5 text-sm text-slate-400">
              Bu departman icin KPI kaydi bulunamadi.
            </div>
          </div>
        </div>
      </div>
    </section>

    <DepartmentTrendChart
      title="Performans KPI'lari (Son 6 Ay)"
      eyebrow="Departman Trend Analizi"
      :data="departmentTrendData"
      :target="85"
    />

    <section class="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
      <PipelineTracking
        title="Performans Pipeline Tracking"
        eyebrow="Departman Akisi"
        :stages="pipelineStages"
      />

      <div class="grid grid-cols-1 gap-6">
        <RiskIndicators :risks="riskIndicatorGroups" />
        <QuickActions :actions="quickActionItems" />
      </div>
    </section>

    <section class="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
      <FunnelChart
        title="Lead Conversion Funnel"
        eyebrow="Funnel Analizi"
        :rows="funnelRows"
      />

      <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p class="text-xs font-semibold uppercase tracking-[0.16em] text-violet-600">Funnel Ozeti</p>
        <h3 class="mt-2 text-lg font-bold text-slate-900">Darbogaz ve kayip analizi</h3>
        <div class="mt-5 space-y-3">
          <div
            v-for="item in funnelInsights"
            :key="item"
            class="rounded-xl border border-violet-100 bg-violet-50 px-4 py-3 text-sm leading-6 text-violet-950"
          >
            {{ item }}
          </div>
        </div>
      </div>
    </section>

    <section class="grid grid-cols-1 gap-6 xl:grid-cols-2">
      <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p class="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-600">Takim Metrikleri</p>
        <h3 class="mt-2 text-lg font-bold text-slate-900">Takim kirilimi</h3>
        <div class="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-1">
          <div
            v-for="team in teamMetricCards"
            :key="team.name"
            class="rounded-xl border border-slate-100 bg-slate-50 p-4"
          >
            <div class="flex items-center justify-between">
              <p class="font-semibold text-slate-900">{{ team.name }}</p>
              <p class="text-sm font-bold text-slate-700">{{ team.count }}</p>
            </div>
            <p class="mt-1 text-xs text-slate-500">Secilebilir calisan</p>
          </div>
        </div>
      </div>

      <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p class="text-xs font-semibold uppercase tracking-[0.16em] text-sky-600">Akis Ozeti</p>
        <h3 class="mt-2 text-lg font-bold text-slate-900">Donusum yorumlari</h3>
        <div class="mt-5 space-y-3">
          <div
            v-for="item in pipelineInsights"
            :key="item"
            class="rounded-xl border border-sky-100 bg-sky-50 px-4 py-3 text-sm leading-6 text-sky-900"
          >
            {{ item }}
          </div>
        </div>
      </div>
    </section>

    <AIInsightsPanel :period="selectedPeriod" :use-llm="true" />
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref, type PropType } from 'vue'
import {
  ChartBarIcon,
  ChartPieIcon,
  ExclamationTriangleIcon,
  UsersIcon,
} from '@heroicons/vue/24/outline'
import KPICard from '@/components/dashboard/KPICard.vue'
import PipelineTracking, { type PipelineStage } from '@/components/dashboard/PipelineTracking.vue'
import FunnelChart, { type FunnelRow } from '@/components/dashboard/FunnelChart.vue'
import DepartmentTrendChart, { type DepartmentTrendPoint } from '@/components/dashboard/DepartmentTrendChart.vue'
import RiskIndicators, { type RiskIndicatorGroups } from '@/components/dashboard/RiskIndicators.vue'
import QuickActions, { type QuickActionItem } from '@/components/dashboard/QuickActions.vue'
import AIInsightsPanel from '@/components/dashboard/AIInsightsPanel.vue'
import DashboardHeader from '@/components/dashboard/DashboardHeader.vue'
import {
  feedbackApi,
  type Department360SummaryReportResponse,
  type EmployeeForFeedback,
  type SummaryMetric,
} from '@/services/api/feedback.api'
import { kpiApi, type KPIRecordDetailResponse } from '@/services/api/kpi.api'

const departmentReport = ref<Department360SummaryReportResponse | null>(null)
const teamMembers = ref<EmployeeForFeedback[]>([])
const kpiRecords = ref<KPIRecordDetailResponse[]>([])
const selectedPeriod = ref('current_week')
const selectedComparison = ref('previous_period')

const previewMetrics = computed<SummaryMetric[]>(() => departmentReport.value?.metrics.slice(0, 4) || [])
const teamMemberCount = computed(() => teamMembers.value.filter((employee) => employee.user.role === 'employee').length)
const departmentName = computed(() => departmentReport.value?.department_name || 'Yazilim Gelistirme')
const departmentMotivationMetric = computed(() =>
  departmentReport.value?.metrics.find((metric) => metric.label === 'Departman Motivasyonu') || null
)
const highFlightRisk = computed(
  () => departmentReport.value?.metrics.find((metric) => metric.label === 'Yuksek Flight Risk')?.display_value || '-'
)
const visibleKpiRecordCount = computed(() => kpiRecords.value.length)
const activeKpiCount = computed(() => new Set(kpiRecords.value.map((record) => record.kpi_id)).size)

const selectedPeriodLabel = computed(() => {
  const labels: Record<string, string> = {
    current_week: 'Bu hafta',
    last_month: 'Son 1 ay',
    last_quarter: 'Son 3 ay',
  }
  return labels[selectedPeriod.value] || 'Bu hafta'
})

const targetAlignmentRate = computed(() => {
  const withTarget = kpiRecords.value.filter((record) => typeof record.kpi.target_value === 'number' && (record.kpi.target_value ?? 0) > 0)
  if (!withTarget.length) {
    return '-'
  }

  const aligned = withTarget.filter((record) => record.value >= (record.kpi.target_value ?? 0)).length
  return `%${Math.round((aligned / withTarget.length) * 100)}`
})

const targetAlignmentPercent = computed(() => {
  if (targetAlignmentRate.value === '-') return 0
  return Number(targetAlignmentRate.value.replace('%', '')) || 0
})

const performanceScorePercent = computed(() => {
  const value = departmentMotivationMetric.value?.value
  if (typeof value !== 'number') return 0
  return Math.max(0, Math.min(100, value * 10))
})

type GaugeStatus = 'good' | 'warning' | 'risk'

type GaugeViewModel = {
  title: string
  current: number
  target: number
  min: number
  max: number
  unit: string
  percentage: number
  needleStyle: Record<string, string>
  statusLabel: string
  statusClass: string
  indicatorClass: string
  formattedCurrent: string
  formattedTarget: string
  formattedMin: string
  formattedMax: string
}

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value))
}

function gaugeStatus(percentage: number): GaugeStatus {
  if (percentage >= 80) return 'good'
  if (percentage >= 60) return 'warning'
  return 'risk'
}

function formatGaugeValue(value: number, unit: string) {
  if (unit === '%') return `%${Math.round(value)}`
  return `${Math.round(value)}${unit}`
}

function buildGauge(params: {
  title: string
  current: number
  target: number
  min?: number
  max?: number
  unit?: string
}): GaugeViewModel {
  const min = params.min ?? 0
  const max = params.max ?? 100
  const current = clamp(params.current, min, max)
  const percentage = max === min ? 0 : clamp(((current - min) / (max - min)) * 100, 0, 100)
  const angle = (percentage / 100) * 180 - 90
  const status = gaugeStatus(percentage)
  const statusMap: Record<GaugeStatus, Pick<GaugeViewModel, 'statusLabel' | 'statusClass' | 'indicatorClass'>> = {
    good: {
      statusLabel: 'Hedefi Gecti',
      statusClass: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-100',
      indicatorClass: 'bg-emerald-500',
    },
    warning: {
      statusLabel: 'Dikkat',
      statusClass: 'bg-amber-50 text-amber-700 ring-1 ring-amber-100',
      indicatorClass: 'bg-amber-500',
    },
    risk: {
      statusLabel: 'Risk',
      statusClass: 'bg-rose-50 text-rose-700 ring-1 ring-rose-100',
      indicatorClass: 'bg-rose-500',
    },
  }
  const unit = params.unit ?? ''

  return {
    title: params.title,
    current,
    target: params.target,
    min,
    max,
    unit,
    percentage,
    needleStyle: { transform: `translateX(-50%) rotate(${angle}deg)` },
    formattedCurrent: formatGaugeValue(current, unit),
    formattedTarget: formatGaugeValue(params.target, unit),
    formattedMin: formatGaugeValue(min, unit),
    formattedMax: formatGaugeValue(max, unit),
    ...statusMap[status],
  }
}

const GaugeComparisonCard = defineComponent({
  name: 'GaugeComparisonCard',
  props: {
    gauge: {
      type: Object as PropType<GaugeViewModel>,
      required: true,
    },
  },
  setup(props) {
    return () => h('div', { class: 'rounded-2xl border border-slate-100 bg-slate-50 p-4' }, [
      h('div', { class: 'flex items-start justify-between gap-3' }, [
        h('div', [
          h('p', { class: 'text-xs font-semibold uppercase tracking-[0.14em] text-slate-400' }, 'Hedef Karsilastirmasi'),
          h('h4', { class: 'mt-1 text-base font-bold text-slate-900' }, props.gauge.title),
        ]),
        h('span', { class: ['rounded-full px-3 py-1 text-xs font-bold', props.gauge.statusClass] }, props.gauge.statusLabel),
      ]),
      h('div', { class: 'mt-5 grid grid-cols-1 gap-4 sm:grid-cols-[minmax(0,1fr)_150px] sm:items-center' }, [
        h('div', { class: 'relative mx-auto h-36 w-full max-w-[260px]' }, [
          h('div', { class: 'absolute left-1/2 top-0 h-32 w-64 max-w-full -translate-x-1/2 overflow-hidden' }, [
            h('div', {
              class: 'absolute left-1/2 top-0 h-64 w-64 max-w-none -translate-x-1/2 rounded-full bg-[conic-gradient(from_270deg,#ef4444_0deg_54deg,#f59e0b_54deg_108deg,#10b981_108deg_180deg,transparent_180deg_360deg)]',
            }),
            h('div', { class: 'absolute left-1/2 top-8 h-48 w-48 -translate-x-1/2 rounded-full bg-slate-50' }),
          ]),
          h('div', {
            class: 'absolute bottom-5 left-1/2 h-1.5 w-[92px] origin-left rounded-full bg-slate-900 shadow-sm transition-transform',
            style: props.gauge.needleStyle,
          }, [
            h('span', { class: ['absolute -right-1 -top-1 h-3.5 w-3.5 rounded-full ring-4 ring-white', props.gauge.indicatorClass] }),
          ]),
          h('div', { class: 'absolute bottom-1 left-1/2 h-4 w-4 -translate-x-1/2 rounded-full bg-slate-900 ring-4 ring-white' }),
          h('div', { class: 'absolute bottom-0 left-0 text-xs font-semibold text-slate-400' }, props.gauge.formattedMin),
          h('div', { class: 'absolute bottom-0 right-0 text-xs font-semibold text-slate-400' }, props.gauge.formattedMax),
        ]),
        h('div', { class: 'space-y-3' }, [
          h('div', [
            h('p', { class: 'text-xs text-slate-500' }, 'Mevcut Deger'),
            h('p', { class: 'mt-1 text-2xl font-bold text-slate-900' }, props.gauge.formattedCurrent),
          ]),
          h('div', [
            h('p', { class: 'text-xs text-slate-500' }, 'Hedef Deger'),
            h('p', { class: 'mt-1 text-xl font-bold text-sky-700' }, props.gauge.formattedTarget),
          ]),
          h('div', [
            h('p', { class: 'text-xs text-slate-500' }, 'Ilerleme'),
            h('p', { class: 'mt-1 text-xl font-bold text-slate-900' }, `%${props.gauge.percentage.toFixed(1)}`),
          ]),
        ]),
      ]),
      h('div', { class: 'mt-4 grid grid-cols-3 overflow-hidden rounded-xl border border-slate-200 bg-white text-center text-xs' }, [
        h('div', { class: 'border-r border-slate-100 px-2 py-2 text-rose-700' }, 'Risk <60%'),
        h('div', { class: 'border-r border-slate-100 px-2 py-2 text-amber-700' }, 'Dikkat 60-80%'),
        h('div', { class: 'px-2 py-2 text-emerald-700' }, 'Iyi 80-100%'),
      ]),
    ])
  },
})

const performanceGauge = computed(() => buildGauge({
  title: 'Ortalama Performans',
  current: performanceScorePercent.value,
  target: 85,
  min: 0,
  max: 100,
  unit: '%',
}))

const targetGauge = computed(() => buildGauge({
  title: 'Performans vs Hedef',
  current: targetAlignmentPercent.value,
  target: 85,
  min: 0,
  max: 100,
  unit: '%',
}))

const kpiRows = computed(() => {
  const grouped = new Map<number, KPIRecordDetailResponse[]>()
  for (const record of kpiRecords.value) {
    const current = grouped.get(record.kpi_id) || []
    current.push(record)
    grouped.set(record.kpi_id, current)
  }

  return Array.from(grouped.values()).map((records) => {
    const sample = records[0]
    const average = records.reduce((sum, record) => sum + record.value, 0) / records.length
    const unitSuffix = sample.kpi.unit === 'percentage'
      ? '%'
      : sample.kpi.unit === 'hours'
        ? ' sa'
        : sample.kpi.unit === 'currency'
          ? ' TL'
          : ''

    return {
      name: sample.kpi.name,
      description: sample.kpi.description || 'Departman KPI kaydi',
      averageDisplay: `${average.toFixed(1)}${unitSuffix}`,
      targetDisplay: typeof sample.kpi.target_value === 'number'
        ? `${sample.kpi.target_value.toFixed(1)}${unitSuffix}`
        : '-',
    }
  })
})

const trendSeries = computed(() => {
  const grouped = new Map<string, KPIRecordDetailResponse[]>()
  for (const record of kpiRecords.value) {
    const key = record.period_date?.slice(0, 7) || 'Donem yok'
    const current = grouped.get(key) || []
    current.push(record)
    grouped.set(key, current)
  }

  return Array.from(grouped.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-6)
    .map(([label, records]) => ({
      label,
      value: Number((records.reduce((sum, record) => sum + record.value, 0) / records.length).toFixed(2)),
    }))
})

const trendLabels = computed(() => trendSeries.value.length ? trendSeries.value.map((item) => item.label) : ['Veri yok'])
const trendValues = computed(() => trendSeries.value.length ? trendSeries.value.map((item) => item.value) : [0])

const fallbackMonthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']

const departmentTrendData = computed<DepartmentTrendPoint[]>(() => {
  const points = trendSeries.value
  const labels = points.length
    ? points.map((item) => item.label)
    : fallbackMonthLabels

  return labels.slice(-6).map((label, index) => {
    const source = points[index]
    const performance = source?.value ?? kpiAverageScore.value
    const capacity = clamp(coverageScore.value || (72 + index * 3), 0, 100)
    const risk = clamp(100 - riskScore.value || (36 - index * 2), 0, 100)

    return {
      month: label,
      performance: clamp(Math.round(performance), 0, 100),
      capacity,
      risk,
    }
  })
})

const kpiAverageScore = computed(() => {
  if (!kpiRecords.value.length) return 0
  const average = kpiRecords.value.reduce((sum, record) => sum + record.value, 0) / kpiRecords.value.length
  return Math.round(Math.max(0, Math.min(100, average)))
})

const kpiTrendPercent = computed(() => {
  const points = trendSeries.value
  if (points.length < 2) return 0
  const previous = points[points.length - 2].value
  const current = points[points.length - 1].value
  if (!previous) return 0
  return Number((((current - previous) / Math.abs(previous)) * 100).toFixed(1))
})

const riskScore = computed(() => {
  const highRiskCount = Number(highFlightRisk.value) || 0
  if (!teamMemberCount.value) return 100
  return Math.max(0, Math.round(100 - (highRiskCount / teamMemberCount.value) * 100))
})

const departmentHealthScore = computed(() => {
  const performanceWeight = kpiAverageScore.value * 0.45
  const riskWeight = riskScore.value * 0.35
  const targetWeight = targetAlignmentPercent.value * 0.2
  return Math.round(performanceWeight + riskWeight + targetWeight)
})

const dashboardRiskLevel = computed(() => {
  if (riskScore.value >= 85) return 'Dusuk'
  if (riskScore.value >= 70) return 'Orta'
  return 'Yuksek'
})

const dashboardTrendLabel = computed(() => {
  if (kpiTrendPercent.value > 0.2) return `+${kpiTrendPercent.value}%`
  if (kpiTrendPercent.value < -0.2) return `${kpiTrendPercent.value}%`
  return 'Sabit'
})

const coverageScore = computed(() => {
  if (!teamMemberCount.value) return 0
  const ratio = visibleKpiRecordCount.value / Math.max(teamMemberCount.value, 1)
  return Math.max(0, Math.min(100, Math.round(ratio * 100)))
})

function metricTone(score: number) {
  if (score >= 85) {
    return {
      statusLabel: 'Basarili',
      statusSurfaceClass: 'border-emerald-200 bg-emerald-50',
      statusBadgeClass: 'bg-emerald-100 text-emerald-700',
      iconClass: 'bg-emerald-50 text-emerald-600',
    }
  }
  if (score >= 70) {
    return {
      statusLabel: 'Dikkat',
      statusSurfaceClass: 'border-amber-200 bg-amber-50',
      statusBadgeClass: 'bg-amber-100 text-amber-700',
      iconClass: 'bg-amber-50 text-amber-600',
    }
  }
  return {
    statusLabel: 'Risk',
    statusSurfaceClass: 'border-rose-200 bg-rose-50',
    statusBadgeClass: 'bg-rose-100 text-rose-700',
    iconClass: 'bg-rose-50 text-rose-600',
  }
}

function trendTone(value: number) {
  if (value > 0.2) {
    return {
      trendIcon: '↑',
      trendLabel: `+${value}% Trend`,
      trendClass: 'bg-emerald-100 text-emerald-700',
      trendTextClass: 'text-emerald-700',
    }
  }
  if (value < -0.2) {
    return {
      trendIcon: '↓',
      trendLabel: `${value}% Trend`,
      trendClass: 'bg-rose-100 text-rose-700',
      trendTextClass: 'text-rose-700',
    }
  }
  return {
    trendIcon: '→',
    trendLabel: 'Sabit Trend',
    trendClass: 'bg-slate-100 text-slate-600',
    trendTextClass: 'text-slate-600',
  }
}

const kpiMetricCards = computed(() => {
  const performanceTone = metricTone(kpiAverageScore.value)
  const targetTone = metricTone(targetAlignmentPercent.value)
  const riskTone = metricTone(riskScore.value)
  const coverageTone = metricTone(coverageScore.value)
  const primaryTrend = trendTone(kpiTrendPercent.value)

  return [
    {
      title: 'Ortalama Performans',
      subtitle: 'KPI kayit ortalamasi',
      value: kpiAverageScore.value,
      max: 100,
      target: '90',
      benchmark: '85',
      icon: ChartBarIcon,
      ...performanceTone,
      ...primaryTrend,
    },
    {
      title: 'Hedef Uyumu',
      subtitle: 'Hedefe ulasan kayitlar',
      value: targetAlignmentPercent.value,
      max: 100,
      target: '85',
      benchmark: `${kpiAverageScore.value}`,
      icon: ChartPieIcon,
      ...targetTone,
      ...trendTone(targetAlignmentPercent.value - 85),
    },
    {
      title: 'Risk Kontrolu',
      subtitle: 'Flight risk ters skoru',
      value: riskScore.value,
      max: 100,
      target: '95',
      benchmark: `${teamMemberCount.value} kisi`,
      icon: ExclamationTriangleIcon,
      ...riskTone,
      ...trendTone(riskScore.value - 85),
    },
    {
      title: 'Veri Kapsami',
      subtitle: 'KPI kaydi / ekip',
      value: coverageScore.value,
      max: 100,
      target: `${teamMemberCount.value}`,
      benchmark: `${visibleKpiRecordCount.value} kayit`,
      icon: UsersIcon,
      ...coverageTone,
      ...trendTone(coverageScore.value - 85),
    },
  ]
})

const riskItems = computed(() => {
  const section = departmentReport.value?.sections.find((item) => item.title.toLowerCase().includes('risk'))
  if (section?.items.length) return section.items.slice(0, 4)
  return ['Risk sinyalleri veri geldikce burada listelenecek.']
})

const quickActions = computed(() => {
  const supportSection = departmentReport.value?.sections.find((item) => item.title.toLowerCase().includes('destek'))
  const actions = [
    departmentReport.value?.recommended_action,
    ...(supportSection?.items || []),
  ].filter(Boolean) as string[]

  return actions.length ? actions.slice(0, 4) : ['Aksiyon onerileri veri geldikce burada listelenecek.']
})

const riskIndicatorGroups = computed<RiskIndicatorGroups>(() => {
  const strengthSection = departmentReport.value?.sections.find((item) => item.title.toLowerCase().includes('guclu'))
  const supportSection = departmentReport.value?.sections.find((item) => item.title.toLowerCase().includes('destek'))

  return {
    critical: riskItems.value.slice(0, 3),
    warnings: [
      ...((supportSection?.items || []).slice(0, 2)),
      `Hedef uyumu ${targetAlignmentRate.value}`,
    ].slice(0, 3),
    positive: [
      ...((strengthSection?.items || []).slice(0, 2)),
      `Performans trendi ${kpiTrendPercent.value > 0 ? '+' : ''}${kpiTrendPercent.value}%`,
      `Risk kontrol skoru ${riskScore.value}/100`,
    ].slice(0, 3),
  }
})

const quickActionItems = computed<QuickActionItem[]>(() => {
  const actions = quickActions.value
  return actions.map((title, index) => ({
    title,
    priority: index === 0 ? 'HIGH' : 'MEDIUM',
  }))
})

const teamMetricCards = computed(() => {
  const grouped = new Map<string, number>()
  for (const employee of teamMembers.value) {
    if (employee.user.role !== 'employee') continue
    const team = employee.team || 'Takim belirtilmedi'
    grouped.set(team, (grouped.get(team) || 0) + 1)
  }

  return Array.from(grouped.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(0, 5)
    .map(([name, count]) => ({ name, count }))
})

const pipelineStages = computed<PipelineStage[]>(() => {
  const totalEmployees = Math.max(teamMemberCount.value, 1)
  const kpiCoverageCount = Math.min(visibleKpiRecordCount.value, totalEmployees)
  const healthyPerformanceCount = Math.round((kpiAverageScore.value / 100) * totalEmployees)
  const targetAlignedCount = Math.round((targetAlignmentPercent.value / 100) * totalEmployees)
  const riskControlledCount = Math.round((riskScore.value / 100) * totalEmployees)
  const actionReadyCount = Math.max(quickActions.value.length, riskControlledCount)

  const rawStages = [
    {
      name: 'Ekip Kapsami',
      value: totalEmployees,
      percentage: 100,
      color: '#ef5350',
    },
    {
      name: 'KPI Kaydi',
      value: kpiCoverageCount,
      percentage: coverageScore.value,
      color: '#ffa726',
    },
    {
      name: 'Performans Normal',
      value: healthyPerformanceCount,
      percentage: kpiAverageScore.value,
      color: '#66bb6a',
    },
    {
      name: 'Hedef Uyumlu',
      value: targetAlignedCount,
      percentage: targetAlignmentPercent.value,
      color: '#29b6f6',
    },
    {
      name: 'Risk Kontrolu',
      value: riskControlledCount,
      percentage: riskScore.value,
      color: '#5c6bc0',
    },
    {
      name: 'Aksiyon Hazir',
      value: actionReadyCount,
      percentage: clamp(Math.round((actionReadyCount / totalEmployees) * 100), 0, 100),
      color: '#ab47bc',
    },
  ]

  return rawStages.map((stage, index) => {
    const next = rawStages[index + 1]
    return {
      ...stage,
      percentage: clamp(Math.round(stage.percentage), 0, 100),
      conversionRate: next ? clamp(Math.round((next.value / Math.max(stage.value, 1)) * 100), 0, 100) : 0,
    }
  })
})

const pipelineInsights = computed(() => {
  const weakestStage = pipelineStages.value
    .slice(1)
    .reduce((weakest, stage) => stage.percentage < weakest.percentage ? stage : weakest, pipelineStages.value[1] || pipelineStages.value[0])

  return [
    `En dusuk akis noktasi: ${weakestStage.name} (%${weakestStage.percentage}).`,
    `Hedef uyumu ${targetAlignmentRate.value}; performans ortalamasi ${kpiAverageScore.value}/100.`,
    `Risk kontrol skoru ${riskScore.value}/100; yuksek flight risk sayisi ${highFlightRisk.value}.`,
  ]
})

const funnelRows = computed<FunnelRow[]>(() => {
  const stages = pipelineStages.value
  if (!stages.length) return []

  return stages.slice(0, 4).map((stage, index) => {
    const previous = stages[index - 1]
    const conversion = index === 0
      ? 100
      : clamp(Math.round((Number(stage.value) / Math.max(Number(previous?.value) || 1, 1)) * 100), 0, 100)

    return {
      stage: index === 0
        ? 'Leads Created'
        : index === 1
          ? 'Leads Contacted'
          : index === 2
            ? 'Deal Qualified'
            : 'Deal Converted',
      value: stage.value,
      conversion,
      dropoff: 100 - conversion,
    }
  })
})

const funnelInsights = computed(() => {
  const rows = funnelRows.value
  if (!rows.length) return ['Funnel analizi icin veri bekleniyor.']
  const worstDrop = rows.slice(1).reduce((worst, row) => row.dropoff > worst.dropoff ? row : worst, rows[1] || rows[0])
  const finalRow = rows[rows.length - 1]
  const firstValue = Number(rows[0].value) || 1
  const finalValue = Number(finalRow.value) || 0
  const totalConversion = clamp(Math.round((finalValue / firstValue) * 100), 0, 100)

  return [
    `Toplam donusum: ${rows[0].value} baslangictan ${finalRow.value} son asamaya, yani %${totalConversion}.`,
    `En yuksek kayip ${worstDrop.stage} asamasinda: %${worstDrop.dropoff} drop-off.`,
    `Son asama conversion orani %${finalRow.conversion}; hedef baglantisi backend ile netlestirilecek.`,
  ]
})

async function loadDepartmentReport() {
  try {
    departmentReport.value = await feedbackApi.getDepartment360SummaryReport()
  } catch (error) {
    console.error('Departman raporu yuklenemedi:', error)
    departmentReport.value = null
  }
}

async function loadTeamMembers() {
  try {
    const candidates = await feedbackApi.getFeedbackCandidates()
    teamMembers.value = candidates
  } catch (error) {
    console.error('Ekip uyeleri yuklenemedi:', error)
    teamMembers.value = []
  }
}

async function loadKpiRecords() {
  try {
    kpiRecords.value = await kpiApi.getAllVisibleRecords()
  } catch (error) {
    console.error('KPI kayitlari yuklenemedi:', error)
    kpiRecords.value = []
  }
}

async function refreshDashboard() {
  await Promise.all([
    loadDepartmentReport(),
    loadTeamMembers(),
    loadKpiRecords(),
  ])
}

function handleDashboardExport() {
  console.info('Departman dashboard PDF export backend baglantisi sonraki adimda eklenecek.')
}

function handleDashboardShare() {
  console.info('Departman dashboard email paylasimi backend baglantisi sonraki adimda eklenecek.')
}

onMounted(async () => {
  await refreshDashboard()
})
</script>
