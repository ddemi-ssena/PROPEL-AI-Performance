<template>
  <div class="space-y-6 pb-10">
    <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
            Hibrit Dashboard
          </p>
          <h1 class="mt-2 text-3xl font-bold tracking-tight text-slate-900">
            Departman Performansi
          </h1>
          <p class="mt-2 text-sm text-slate-600">
            KPI/ML + 360 Feedback + Haftalik Nabiz
          </p>
        </div>

        <div class="text-left lg:text-right">
          <p class="text-xs text-slate-500">
            Son guncelleme: {{ formatDateTime(dashboard?.generated_at) }}
          </p>
          <button
            type="button"
            class="mt-3 inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
            :disabled="loading"
            @click="refreshDashboard"
          >
            <ArrowPathIcon class="h-4 w-4" :class="{ 'animate-spin': loading }" />
            Yenile
          </button>
        </div>
      </div>

      <div class="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
          <p class="text-sm text-slate-600">Departman</p>
          <p class="mt-2 text-2xl font-bold text-slate-900">{{ department.name }}</p>
        </div>
        <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
          <p class="text-sm text-slate-600">Calisan Sayisi</p>
          <p class="mt-2 text-2xl font-bold text-slate-900">{{ department.member_count }}</p>
        </div>
        <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
          <p class="text-sm text-slate-600">Takim Sayisi</p>
          <p class="mt-2 text-2xl font-bold text-slate-900">{{ department.team_count }}</p>
        </div>
        <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
          <label for="dashboard-period" class="text-sm text-slate-600">Rapor Donemi</label>
          <select
            id="dashboard-period"
            v-model="selectedPeriod"
            class="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700"
            @change="refreshDashboard"
          >
            <option value="week">Bu Hafta</option>
            <option value="month">Bu Ay</option>
            <option value="quarter">Bu Ceyrek</option>
            <option value="year">Bu Yil</option>
          </select>
        </div>
      </div>

      <div class="mt-6 rounded-2xl border border-blue-100 bg-blue-50 p-4">
        <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 class="text-sm font-bold text-slate-900">Veri Kapsama Orani</h2>
            <p class="mt-1 text-xs text-slate-600">
              Hibrit skorun guveni: {{ score(coverage.confidence_score) }}/100
            </p>
          </div>
          <span class="rounded-full bg-white px-3 py-1 text-xs font-bold text-blue-700">
            {{ coverage.confidence_score }}% confidence
          </span>
        </div>

        <div class="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <CoverageTile
            title="KPI/ML Analizi"
            tone="blue"
            :main="`${coverage.kpi_employee_count}/${department.member_count}`"
            :sub="`${coverage.kpi_percentage}% calisan`"
            :date="formatDateTime(coverage.last_kpi_update)"
          />
          <CoverageTile
            title="Haftalik Nabiz"
            tone="emerald"
            :main="`${coverage.pulse_response_count}/${department.member_count}`"
            :sub="`${coverage.pulse_percentage}% cevap`"
            :date="formatDate(coverage.last_pulse_update)"
          />
          <CoverageTile
            title="360 Feedback"
            tone="violet"
            :main="`${coverage.feedback_response_count}`"
            :sub="`${coverage.feedback_employee_count} kisi, ${coverage.feedback_percentage}% kapsama`"
            :date="formatDateTime(coverage.last_feedback_update)"
          />
        </div>
      </div>
    </section>

    <div v-if="loading" class="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500 shadow-sm">
      Hibrit departman verileri yukleniyor...
    </div>

    <div v-else-if="errorMessage" class="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
      {{ errorMessage }}
    </div>

    <template v-else>
      <section class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KPICard
          v-for="card in hybridScoreCards"
          :key="card.title"
          :card="card"
        />
      </section>

      <section class="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-600">
                Departman Genel Durumu
              </p>
              <h2 class="mt-2 text-xl font-bold text-slate-900">Hibrit saglik ozeti</h2>
            </div>
            <span class="rounded-full px-3 py-1 text-xs font-bold" :class="statusBadge(overallStatus)">
              {{ statusLabel(overallStatus) }}
            </span>
          </div>

          <div class="mt-6 grid grid-cols-[auto_minmax(0,1fr)] gap-5">
            <HybridGauge
              title="Genel Saglik"
              :value="scores.department_health"
              :risk-mode="false"
            />
            <div class="min-w-0">
              <p class="text-sm leading-6 text-slate-700">{{ aiSummary.summary }}</p>
              <div class="mt-4 flex flex-wrap gap-2">
                <span class="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">
                  KPI/ML %{{ scores.weights.kpiMl ?? 0 }}
                </span>
                <span class="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-700">
                  Nabiz %{{ scores.weights.weeklyPulse ?? 0 }}
                </span>
                <span class="rounded-full bg-violet-50 px-3 py-1 text-xs font-bold text-violet-700">
                  360 %{{ scores.weights.feedback360 ?? 0 }}
                </span>
                <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
                  Guven {{ score(scores.confidence_score) }}/100
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
                Kaynak Durumlari
              </p>
              <h2 class="mt-2 text-xl font-bold text-slate-900">Her kaynagi ayri oku</h2>
            </div>
            <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
              {{ generalStatusRows.length }} sinyal
            </span>
          </div>

          <div class="mt-5 space-y-4">
            <div
              v-for="row in generalStatusRows"
              :key="row.key"
              class="rounded-xl border border-slate-100 bg-slate-50 p-4"
            >
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
                <div class="min-w-0">
                  <p class="font-bold text-slate-900">{{ row.label }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ row.description }}</p>
                  <div class="mt-3 h-2 overflow-hidden rounded-full bg-white">
                    <div
                      class="h-full rounded-full"
                      :class="row.barClass"
                      :style="{ width: `${row.progress}%` }"
                    ></div>
                  </div>
                  <p class="mt-2 text-xs font-semibold text-slate-400">{{ row.detail }}</p>
                </div>
                <HybridGauge
                  :title="row.gaugeTitle"
                  :value="row.progress"
                  :display="row.display"
                  :risk-mode="row.riskMode"
                  size="sm"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <SourceSummaryCard
          v-for="source in sourceCards"
          :key="source.key"
          :source="source"
        />
      </section>

      <DepartmentTrendChart
        title="Hibrit Performans Trendi"
        eyebrow="Departman Trend Analizi"
        :data="departmentTrendData"
        :target="85"
      />

      <section class="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <PipelineTracking
          title="Hibrit Performans Pipeline"
          eyebrow="Departman Akisi"
          :stages="pipelineStages"
        />

        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-[0.16em] text-sky-600">Akis Ozeti</p>
          <h2 class="mt-2 text-xl font-bold text-slate-900">Donusum yorumlari</h2>
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

      <section class="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        <FunnelChart
          title="Hibrit analiz icin veri tamamligi"
          eyebrow="KPI + Nabiz + 360 kapsami"
          badge-text="Eksik veri kontrolu"
          description="Bu kart performans sonucunu degil, departman skorunu hesaplamak icin gerekli veri kaynaklarinin kac calisanda mevcut oldugunu gosterir."
          :rows="funnelRows"
        />

        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-[0.16em] text-violet-600">Eksik veri etkisi</p>
          <h2 class="mt-2 text-xl font-bold text-slate-900">Skorun hangi kismi eksik veri yuzunden zayif?</h2>
          <p class="mt-2 text-sm leading-6 text-slate-600">
            Hibrit skor KPI/ML, haftalik nabiz ve 360 feedback sinyallerini birlestirir.
            Bir kaynak eksikse o alan skorlanamaz; bu kart eksikligin hangi kaynaktan geldigini ve karar guvenini nasil etkiledigini aciklar.
          </p>
          <div class="mt-5 space-y-3">
            <div
              v-for="item in funnelInsights"
              :key="item.title"
              class="rounded-xl border border-violet-100 bg-violet-50 px-4 py-3"
            >
              <p class="text-sm font-bold text-violet-950">{{ item.title }}</p>
              <p class="mt-1 text-sm leading-6 text-violet-900">{{ item.description }}</p>
              <p class="mt-2 text-xs leading-5 text-violet-700">{{ item.impact }}</p>
            </div>
          </div>
        </div>
      </section>

      <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
              Hibrit Icgoruler
            </p>
            <h2 class="mt-2 text-xl font-bold text-slate-900">Kesisim analizi</h2>
            <p class="mt-2 text-sm text-slate-600">
              KPI/ML, haftalik nabiz ve 360 kaynaklarinin birlikte verdigi sinyaller.
            </p>
          </div>
          <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
            {{ insights.length }} bulgu
          </span>
        </div>

        <div class="mt-6 space-y-4">
          <article
            v-for="insight in insights"
            :key="`${insight.type}-${insight.title}`"
            class="rounded-r-2xl border-l-4 p-5"
            :class="insightTone(insight.severity).surface"
          >
            <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p class="text-xs font-bold uppercase tracking-[0.12em]" :class="insightTone(insight.severity).text">
                  {{ insightTone(insight.severity).label }}
                </p>
                <h3 class="mt-1 text-lg font-bold text-slate-900">
                  {{ insight.title }}
                </h3>
              </div>
              <div class="flex flex-wrap gap-2">
                <span class="w-fit rounded-full px-2.5 py-1 text-xs font-bold" :class="insightTone(insight.severity).badge">
                  {{ actionLabel(insight.action) }}
                </span>
                <span class="w-fit rounded-full bg-white/80 px-2.5 py-1 text-xs font-bold text-slate-500">
                  {{ insightSourceLabel(insight) }}
                </span>
              </div>
            </div>
            <p class="mt-3 text-sm leading-6 text-slate-700">{{ insight.description }}</p>
            <p v-if="insight.team" class="mt-2 text-xs font-semibold text-slate-500">
              Takim: {{ insight.team }}
            </p>

            <div v-if="insight.evidence?.length" class="mt-4 rounded-xl border border-white/80 bg-white/70 p-4">
              <p class="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">Kanitlar</p>
              <ul class="mt-2 grid grid-cols-1 gap-2 text-sm leading-5 text-slate-700 md:grid-cols-2">
                <li v-for="evidence in insight.evidence" :key="evidence" class="flex gap-2">
                  <span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400"></span>
                  <span>{{ evidence }}</span>
                </li>
              </ul>
            </div>

            <div class="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
              <div v-if="insight.manager_interpretation" class="rounded-xl bg-white/60 p-4">
                <p class="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">Yonetici yorumu</p>
                <p class="mt-2 text-sm leading-6 text-slate-700">{{ insight.manager_interpretation }}</p>
              </div>
              <div v-if="insight.impact" class="rounded-xl bg-white/60 p-4">
                <p class="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">Etkisi</p>
                <p class="mt-2 text-sm leading-6 text-slate-700">{{ insight.impact }}</p>
              </div>
            </div>

            <div class="mt-4 rounded-xl border border-slate-200 bg-white p-4">
              <p class="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">Onerilen aksiyon</p>
              <p class="mt-2 text-sm font-semibold leading-6 text-slate-900">
                {{ insight.recommendation }}
              </p>
            </div>

            <div v-if="insight.follow_up_metrics?.length" class="mt-3 flex flex-wrap gap-2">
              <span class="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">Takip:</span>
              <span
                v-for="metric in insight.follow_up_metrics"
                :key="metric"
                class="rounded-full bg-white/80 px-2.5 py-1 text-xs font-semibold text-slate-600"
              >
                {{ metric }}
              </span>
            </div>
          </article>
        </div>
      </section>

      <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
              Takim Karsilastirmasi
            </p>
            <h2 class="mt-2 text-xl font-bold text-slate-900">Tum metrikler</h2>
          </div>
          <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
            {{ teamBreakdown.length }} takim
          </span>
        </div>

        <div class="mt-6 overflow-x-auto">
          <table class="w-full min-w-[840px] text-sm">
            <thead class="bg-slate-50 text-slate-600">
              <tr>
                <th class="px-4 py-3 text-left font-semibold">Takim</th>
                <th class="px-4 py-3 text-right font-semibold">Saglik</th>
                <th class="px-4 py-3 text-right font-semibold">KPI</th>
                <th class="px-4 py-3 text-right font-semibold">Nabiz</th>
                <th class="px-4 py-3 text-right font-semibold">360</th>
                <th class="px-4 py-3 text-right font-semibold">Risk</th>
                <th class="px-4 py-3 text-center font-semibold">Status</th>
                <th class="px-4 py-3 text-center font-semibold">Trend</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="team in teamBreakdown"
                :key="team.team"
                class="border-t border-slate-100 hover:bg-slate-50"
              >
                <td class="px-4 py-3 font-semibold text-slate-900">
                  {{ team.team }} <span class="text-slate-400">({{ team.member_count }})</span>
                </td>
                <td class="px-4 py-3 text-right text-lg font-bold text-slate-900">{{ score(team.scores.health) }}</td>
                <td class="px-4 py-3 text-right">{{ score(team.scores.kpi) }}</td>
                <td class="px-4 py-3 text-right">{{ score(team.scores.pulse) }}</td>
                <td class="px-4 py-3 text-right">{{ score(team.scores.feedback) }}</td>
                <td class="px-4 py-3 text-right font-bold text-orange-600">{{ score(team.scores.risk) }}</td>
                <td class="px-4 py-3 text-center">
                  <span class="rounded-full px-2.5 py-1 text-xs font-bold" :class="statusBadge(team.status)">
                    {{ statusLabel(team.status) }}
                  </span>
                </td>
                <td class="px-4 py-3 text-center font-bold" :class="trendClass(team.trend)">
                  {{ trendIcon(team.trend) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,0.85fr)]">
        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.16em] text-blue-600">AI Ozet</p>
              <h2 class="mt-2 text-xl font-bold text-slate-900">Birlesik departman yorumu</h2>
            </div>
            <span class="w-fit rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-700">
              {{ aiSummarySourceLabel }}
            </span>
          </div>
          <p class="mt-4 text-sm leading-6 text-slate-700">{{ aiSummary.summary }}</p>

          <div class="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
            <SummaryList title="AI'nin Dayandigi Guclu Kanitlar" :items="aiSummary.strengths" tone="emerald" />
            <SummaryList title="AI Risk Yorumu" :items="aiSummary.risks" tone="rose" />
            <SummaryList title="AI Aksiyon Onerileri" :items="aiSummary.recommendations" tone="blue" />
          </div>
        </div>

        <div class="grid grid-cols-1 gap-6">
          <RiskIndicators :risks="riskIndicatorGroups" />
          <QuickActions :actions="quickActionItems" />
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref, type Component, type PropType } from 'vue'
import {
  ArrowPathIcon,
  ChartBarIcon,
  ChartPieIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  SparklesIcon,
  UsersIcon,
} from '@heroicons/vue/24/outline'
import KPICard from '@/components/dashboard/KPICard.vue'
import PipelineTracking, { type PipelineStage } from '@/components/dashboard/PipelineTracking.vue'
import FunnelChart, { type FunnelRow } from '@/components/dashboard/FunnelChart.vue'
import DepartmentTrendChart, { type DepartmentTrendPoint } from '@/components/dashboard/DepartmentTrendChart.vue'
import RiskIndicators, { type RiskIndicatorGroups } from '@/components/dashboard/RiskIndicators.vue'
import QuickActions, { type QuickActionItem } from '@/components/dashboard/QuickActions.vue'
import {
  analyticsApi,
  type DepartmentDashboardAISummaryResponse,
  type DepartmentDashboardCoverageResponse,
  type DepartmentDashboardDepartmentResponse,
  type DepartmentDashboardInsightResponse,
  type DepartmentDashboardSourceResponse,
  type DepartmentDashboardTeamResponse,
  type SoftwareDepartmentDashboardResponse,
} from '@/services/api/analytics.api'

type SourceCard = {
  key: string
  title: string
  badge: string
  tone: 'emerald' | 'blue' | 'violet'
  source: DepartmentDashboardSourceResponse
  metrics: Array<{ label: string; value: string; hint?: string }>
  explainer: string
}

const selectedPeriod = ref<'week' | 'month' | 'quarter' | 'year'>('week')
const dashboard = ref<SoftwareDepartmentDashboardResponse | null>(null)
const loading = ref(false)
const errorMessage = ref('')

const emptyDepartment: DepartmentDashboardDepartmentResponse = {
  id: 0,
  name: 'Yazilim Gelistirme',
  member_count: 0,
  team_count: 0,
  teams: [],
}

const emptyCoverage: DepartmentDashboardCoverageResponse = {
  kpi_employee_count: 0,
  kpi_percentage: 0,
  pulse_response_count: 0,
  pulse_employee_count: 0,
  pulse_percentage: 0,
  feedback_response_count: 0,
  feedback_employee_count: 0,
  feedback_percentage: 0,
  confidence_score: 0,
  last_kpi_update: null,
  last_pulse_update: null,
  last_feedback_update: null,
}

const emptyAiSummary: DepartmentDashboardAISummaryResponse = {
  summary: 'Hibrit dashboard verisi yuklenince birlesik ozet burada gorunecek.',
  strengths: [],
  risks: [],
  recommendations: [],
  source: 'deterministic',
  model: null,
  fallback_used: false,
}

const department = computed(() => dashboard.value?.department || emptyDepartment)
const coverage = computed(() => dashboard.value?.coverage || emptyCoverage)
const scores = computed(() => dashboard.value?.scores || {
  department_health: 0,
  execution_score: 0,
  people_health_score: 0,
  risk_score: 0,
  confidence_score: 0,
  weights: {},
})
const sources = computed(() => dashboard.value?.sources || {})
const insights = computed<DepartmentDashboardInsightResponse[]>(() => dashboard.value?.hybrid_insights || [])
const teamBreakdown = computed<DepartmentDashboardTeamResponse[]>(() => dashboard.value?.team_breakdown || [])
const aiSummary = computed(() => dashboard.value?.ai_summary || emptyAiSummary)
const aiSummarySourceLabel = computed(() => {
  if (aiSummary.value.fallback_used) return 'Kural bazli ozet'
  if (['gemini', 'ollama'].includes(aiSummary.value.source)) return 'LLM yorumu'
  if (aiSummary.value.source?.includes('llm')) return 'LLM yorumu'
  return 'Kural bazli ozet'
})

const CoverageTile = defineComponent({
  props: {
    title: { type: String, required: true },
    tone: { type: String as PropType<'blue' | 'emerald' | 'violet'>, required: true },
    main: { type: String, required: true },
    sub: { type: String, required: true },
    date: { type: String, required: true },
  },
  setup(props) {
    const toneClass = computed(() => ({
      blue: 'border-blue-100 bg-white text-blue-700',
      emerald: 'border-emerald-100 bg-white text-emerald-700',
      violet: 'border-violet-100 bg-white text-violet-700',
    }[props.tone]))
    return () => h('div', { class: `rounded-xl border p-4 ${toneClass.value}` }, [
      h('p', { class: 'text-sm font-semibold text-slate-700' }, props.title),
      h('p', { class: 'mt-2 text-2xl font-bold' }, props.main),
      h('p', { class: 'mt-1 text-xs text-slate-600' }, props.sub),
      h('p', { class: 'mt-1 text-xs text-slate-400' }, `Son: ${props.date}`),
    ])
  },
})

const SourceSummaryCard = defineComponent({
  props: {
    source: { type: Object as PropType<SourceCard>, required: true },
  },
  setup(props) {
    const borderClass = computed(() => ({
      emerald: 'border-emerald-500 bg-emerald-50 text-emerald-700',
      blue: 'border-blue-500 bg-blue-50 text-blue-700',
      violet: 'border-violet-500 bg-violet-50 text-violet-700',
    }[props.source.tone]))

    return () => h('article', { class: `rounded-2xl border border-slate-200 border-l-4 bg-white p-6 shadow-sm ${borderClass.value.split(' ')[0]}` }, [
      h('div', { class: 'mb-5 flex items-start justify-between gap-3' }, [
        h('div', [
          h('p', { class: 'text-xs font-semibold uppercase tracking-[0.16em] text-slate-400' }, props.source.badge),
          h('h3', { class: 'mt-2 text-lg font-bold text-slate-900' }, props.source.title),
        ]),
        h('span', { class: `rounded-full px-2.5 py-1 text-xs font-bold ${borderClass.value.replace('border-', 'bg-')}` }, statusLabel(props.source.source.status)),
      ]),
      h('div', { class: 'space-y-4' }, props.source.metrics.map((metric) => h('div', { class: 'border-t border-slate-100 pt-3 first:border-t-0 first:pt-0' }, [
        h('p', { class: 'text-sm text-slate-500' }, metric.label),
        h('p', { class: 'mt-1 text-2xl font-bold text-slate-900' }, metric.value),
        metric.hint ? h('p', { class: 'mt-1 text-xs text-slate-400' }, metric.hint) : null,
      ]))),
      h('div', { class: `mt-5 rounded-xl p-3 text-sm ${borderClass.value.replace('border-', 'bg-')}` }, [
        h('p', { class: 'font-bold' }, 'Ne olcuyor?'),
        h('p', { class: 'mt-1 text-xs leading-5' }, props.source.explainer),
      ]),
    ])
  },
})

const HybridGauge = defineComponent({
  props: {
    title: { type: String, required: true },
    value: { type: Number, required: true },
    display: { type: String, default: '' },
    riskMode: { type: Boolean, default: false },
    size: { type: String as PropType<'md' | 'sm'>, default: 'md' },
  },
  setup(props) {
    const normalized = computed(() => clamp(score(props.value), 0, 100))
    const fillDegrees = computed(() => normalized.value * 1.8)
    const needleDegrees = computed(() => -90 + fillDegrees.value)
    const isSmall = computed(() => props.size === 'sm')
    const displayValue = computed(() => props.display || `${normalized.value}/100`)
    const status = computed(() => props.riskMode ? riskLabel(normalized.value) : scoreStatus(normalized.value))
    const statusClass = computed(() => props.riskMode ? riskToneClass(normalized.value) : scoreToneClass(normalized.value))

    return () => h('div', { class: isSmall.value ? 'w-28 shrink-0' : 'w-36 shrink-0' }, [
      h('div', {
        class: [
          'relative overflow-hidden',
          isSmall.value ? 'h-16 w-28' : 'h-20 w-36',
        ],
      }, [
        h('div', {
          class: 'absolute inset-x-0 top-0 rounded-t-full',
          style: {
            height: isSmall.value ? '112px' : '144px',
            background: 'conic-gradient(from 270deg at 50% 100%, #ef4444 0deg 54deg, #f59e0b 54deg 108deg, #10b981 108deg 180deg, transparent 180deg 360deg)',
          },
        }),
        h('div', {
          class: 'absolute left-1/2 top-4 -translate-x-1/2 rounded-t-full bg-white',
          style: {
            width: isSmall.value ? '72px' : '96px',
            height: isSmall.value ? '72px' : '96px',
          },
        }),
        h('div', {
          class: 'absolute bottom-0 left-1/2 h-1 origin-left rounded-full bg-slate-900 shadow',
          style: {
            width: isSmall.value ? '38px' : '50px',
            transform: `rotate(${needleDegrees.value}deg)`,
          },
        }),
        h('div', {
          class: [
            'absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 rounded-full bg-slate-950 ring-4 ring-white',
            isSmall.value ? 'h-4 w-4' : 'h-5 w-5',
          ],
        }),
      ]),
      h('div', { class: 'mt-2 text-center' }, [
        h('p', { class: `font-bold ${isSmall.value ? 'text-lg' : 'text-2xl'} ${statusClass.value}` }, displayValue.value),
        h('p', { class: 'mt-0.5 text-xs font-semibold text-slate-500' }, props.title),
        h('p', { class: `mt-0.5 text-xs font-bold ${statusClass.value}` }, status.value),
      ]),
      h('div', { class: 'mt-2 grid grid-cols-3 overflow-hidden rounded-lg border border-slate-200 text-[10px] font-semibold' }, [
        h('span', { class: 'bg-rose-50 py-1 text-center text-rose-600' }, 'Risk'),
        h('span', { class: 'bg-amber-50 py-1 text-center text-amber-600' }, 'Dikkat'),
        h('span', { class: 'bg-emerald-50 py-1 text-center text-emerald-600' }, 'Iyi'),
      ]),
    ])
  },
})

const SummaryList = defineComponent({
  props: {
    title: { type: String, required: true },
    items: { type: Array as PropType<string[]>, required: true },
    tone: { type: String as PropType<'emerald' | 'rose' | 'blue'>, required: true },
  },
  setup(props) {
    const toneClass = computed(() => ({
      emerald: 'border-emerald-100 bg-emerald-50 text-emerald-900',
      rose: 'border-rose-100 bg-rose-50 text-rose-900',
      blue: 'border-blue-100 bg-blue-50 text-blue-900',
    }[props.tone]))
    return () => h('div', { class: `rounded-xl border p-4 ${toneClass.value}` }, [
      h('h3', { class: 'text-sm font-bold' }, props.title),
      h('ul', { class: 'mt-3 space-y-2 text-sm leading-5' },
        (props.items.length ? props.items : ['Veri geldikce netlesecek.']).map((item) => h('li', item))
      ),
    ])
  },
})

const hybridScoreCards = computed(() => [
  buildScoreCard({
    title: 'Departman Sagligi',
    subtitle: 'Aktif veri kaynaklarina gore',
    value: scores.value.department_health,
    target: '85',
    benchmark: `${scores.value.confidence_score} guven`,
    icon: SparklesIcon,
  }),
  buildScoreCard({
    title: 'Performans Ciktilari',
    subtitle: 'KPI/ML analizi',
    value: scores.value.execution_score,
    target: '85',
    benchmark: 'Objektif',
    icon: ChartBarIcon,
  }),
  buildScoreCard({
    title: 'Insan Sagligi',
    subtitle: '360 + haftalik nabiz',
    value: scores.value.people_health_score,
    target: '80',
    benchmark: 'Davranis + psikoloji',
    icon: UsersIcon,
  }),
  buildScoreCard({
    title: 'Risk Skoru',
    subtitle: 'Attrition + burnout + stres',
    value: scores.value.risk_score,
    target: '< 40',
    benchmark: riskLabel(scores.value.risk_score),
    icon: ExclamationTriangleIcon,
    inverse: true,
  }),
])

const overallStatus = computed(() => {
  const health = scores.value.department_health
  if (health >= 85) return 'success'
  if (health >= 70) return 'warning'
  return 'danger'
})

const generalStatusRows = computed(() => [
  {
    key: 'kpi',
    label: 'KPI/ML Performans',
    description: 'Uretkenlik, hedef uyumu ve model bazli performans riski.',
    display: `${score(scores.value.execution_score)}/100`,
    detail: `${coverage.value.kpi_employee_count}/${department.value.member_count} calisan`,
    gaugeTitle: 'KPI/ML',
    riskMode: false,
    progress: score(scores.value.execution_score),
    valueClass: scoreToneClass(scores.value.execution_score),
    barClass: barToneClass(scores.value.execution_score),
  },
  {
    key: 'pulse',
    label: 'Haftalik Nabiz',
    description: 'Motivasyon, baglilik, stres ve ayrilma riski sinyali.',
    display: `${metric('weeklyPulse', 'motivationAverage')}/100`,
    detail: `${coverage.value.pulse_response_count} cevap`,
    gaugeTitle: 'Nabiz',
    riskMode: false,
    progress: score(sources.value.weeklyPulse?.score ?? 0),
    valueClass: scoreToneClass(sources.value.weeklyPulse?.score ?? 0),
    barClass: barToneClass(sources.value.weeklyPulse?.score ?? 0),
  },
  {
    key: 'feedback',
    label: '360 Feedback',
    description: 'Psikolojik guven, is birligi, destek ihtiyaci ve burnout NLP sinyali.',
    display: coverage.value.feedback_response_count ? `${score(sources.value.feedback360?.score ?? 0)}/100` : 'Veri yok',
    detail: `${coverage.value.feedback_response_count} analiz`,
    gaugeTitle: '360',
    riskMode: false,
    progress: coverage.value.feedback_response_count ? score(sources.value.feedback360?.score ?? 0) : 0,
    valueClass: coverage.value.feedback_response_count ? scoreToneClass(sources.value.feedback360?.score ?? 0) : 'text-slate-400',
    barClass: coverage.value.feedback_response_count ? barToneClass(sources.value.feedback360?.score ?? 0) : 'bg-slate-300',
  },
  {
    key: 'risk',
    label: 'Birlesik Risk',
    description: 'KPI/ML riski, nabiz flight/stres sinyali ve 360 burnout riski.',
    display: `${score(scores.value.risk_score)}/100`,
    detail: riskLabel(scores.value.risk_score),
    gaugeTitle: 'Risk',
    riskMode: true,
    progress: score(scores.value.risk_score),
    valueClass: riskToneClass(scores.value.risk_score),
    barClass: riskBarClass(scores.value.risk_score),
  },
])

const sourceCards = computed<SourceCard[]>(() => [
  {
    key: 'kpiMl',
    title: 'Performans Ciktilari (KPI/ML)',
    badge: 'Objektif',
    tone: 'emerald' as const,
    source: sources.value.kpiMl,
    metrics: [
      { label: 'Ortalama Performans', value: `${metric('kpiMl', 'averagePerformance')}/100`, hint: `Trend: ${metric('kpiMl', 'trend')}` },
      { label: 'Hedef Uyumu', value: `${metric('kpiMl', 'targetAlignment')}/100` },
      { label: 'ML Risk Tahmini', value: `${metric('kpiMl', 'mlRiskScore')}/100` },
      { label: 'Yuksek Risk', value: `${metric('kpiMl', 'highRiskCount')} kisi` },
    ],
    explainer: 'Ne oldu? Uretkenlik, hedefe ulasma, kalite ve model bazli performans riski.',
  },
  {
    key: 'weeklyPulse',
    title: 'Insan Sagligi Sinyalleri (Nabiz)',
    badge: 'Haftalik',
    tone: 'blue' as const,
    source: sources.value.weeklyPulse,
    metrics: [
      { label: 'Motivasyon Ort.', value: `${metric('weeklyPulse', 'motivationAverage')}/100`, hint: `Trend: ${metric('weeklyPulse', 'motivationTrend')}` },
      { label: 'Stres Seviyesi', value: `${metric('weeklyPulse', 'stressLevel')}/100` },
      { label: 'Baglilik Skoru', value: `${metric('weeklyPulse', 'engagementScore')}/100` },
      { label: 'Ayrilma Riski', value: `${metric('weeklyPulse', 'attritionRisk')}/100` },
    ],
    explainer: 'Ekip bu hafta nasil hissediyor? Motivasyon, duygu trendi, baglilik ve ayrilma riski.',
  },
  {
    key: 'feedback360',
    title: 'Davranis ve Iliskiler (360)',
    badge: 'Iliskisel',
    tone: 'violet' as const,
    source: sources.value.feedback360,
    metrics: [
      { label: 'Is Birligi', value: `${metric('feedback360', 'collaborationScore')}/100` },
      { label: 'Psikolojik Guven', value: `${metric('feedback360', 'trustScore')}/100` },
      { label: 'Liderlik Destegi', value: `${metric('feedback360', 'leadershipSupportScore')}/100` },
      { label: 'Burnout Riski', value: `${metric('feedback360', 'burnoutRisk')}` },
    ],
    explainer: 'Ekip birbirini nasil deneyimliyor? Is birligi, guven, destek ihtiyaci ve davranis sinyalleri.',
  },
].filter((item) => item.source))

const departmentTrendData = computed<DepartmentTrendPoint[]>(() => {
  const teams = teamBreakdown.value
  if (!teams.length) {
    return [{
      month: selectedPeriod.value,
      performance: score(scores.value.execution_score),
      capacity: score(scores.value.people_health_score),
      risk: score(scores.value.risk_score),
    }]
  }

  return teams.map((team) => ({
    month: team.team,
    performance: score(team.scores.kpi),
    capacity: score(team.scores.pulse),
    risk: score(team.scores.risk),
  }))
})

const pipelineStages = computed<PipelineStage[]>(() => {
  const total = Math.max(department.value.member_count, 1)
  const kpiCount = Math.min(coverage.value.kpi_employee_count, total)
  const pulseCount = Math.min(coverage.value.pulse_employee_count, total)
  const feedbackCount = Math.min(coverage.value.feedback_employee_count, total)
  const healthyTeams = teamBreakdown.value.filter((team) => (team.scores.health || 0) >= 70).length
  const actionCount = quickActionItems.value.length

  const rawStages = [
    {
      name: 'Departman Kapsami',
      value: total,
      percentage: 100,
      color: '#ef5350',
    },
    {
      name: 'KPI/ML Verisi',
      value: kpiCount,
      percentage: coverage.value.kpi_percentage,
      color: '#ffa726',
    },
    {
      name: 'Nabiz Verisi',
      value: pulseCount,
      percentage: coverage.value.pulse_percentage,
      color: '#29b6f6',
    },
    {
      name: '360 NLP Verisi',
      value: feedbackCount,
      percentage: coverage.value.feedback_percentage,
      color: '#8b5cf6',
    },
    {
      name: 'Saglikli Takim',
      value: healthyTeams,
      percentage: percent(healthyTeams, Math.max(teamBreakdown.value.length, 1)),
      color: '#66bb6a',
    },
    {
      name: 'Aksiyon Hazir',
      value: actionCount,
      percentage: percent(actionCount, Math.max(insights.value.length + teamBreakdown.value.length, 1)),
      color: '#ab47bc',
    },
  ]

  return rawStages.map((stage, index) => {
    const next = rawStages[index + 1]
    return {
      ...stage,
      percentage: clamp(Math.round(stage.percentage), 0, 100),
      conversionRate: next ? percent(Number(next.value), Math.max(Number(stage.value), 1)) : 0,
    }
  })
})

const pipelineInsights = computed(() => {
  const weakestCoverage = [
    { label: 'KPI/ML', value: coverage.value.kpi_percentage },
    { label: 'Haftalik Nabiz', value: coverage.value.pulse_percentage },
    { label: '360 Feedback', value: coverage.value.feedback_percentage },
  ].sort((a, b) => a.value - b.value)[0]
  const weakestTeam = [...teamBreakdown.value].sort((a, b) => (a.scores.health || 0) - (b.scores.health || 0))[0]

  return [
    `En dusuk veri kapsami: ${weakestCoverage.label} (%${score(weakestCoverage.value)}).`,
    `Departman sagligi ${score(scores.value.department_health)}/100; risk skoru ${score(scores.value.risk_score)}/100.`,
    weakestTeam
      ? `En dusuk hibrit takim skoru ${weakestTeam.team}: ${score(weakestTeam.scores.health)}/100.`
      : 'Takim bazli akis verisi geldikce netlesecek.',
  ]
})

const funnelRows = computed<FunnelRow[]>(() => {
  const total = Math.max(department.value.member_count, 1)
  const fullSignalCount = Math.min(
    coverage.value.kpi_employee_count,
    coverage.value.pulse_employee_count,
    coverage.value.feedback_employee_count
  )

  const rows = [
    {
      stage: 'Departmandaki calisanlar',
      value: total,
      description: 'Hibrit dashboardun baz aldigi toplam yazilim departmani calisan sayisi.',
    },
    {
      stage: 'KPI/ML verisi olanlar',
      value: coverage.value.kpi_employee_count,
      description: 'Performans, hedef uyumu ve ML risk sinyali hesaplanabilen calisanlar.',
    },
    {
      stage: 'Nabiz yaniti olanlar',
      value: coverage.value.pulse_employee_count,
      description: 'Motivasyon, stres, baglilik ve flight risk sinyali okunabilen calisanlar.',
    },
    {
      stage: '360 NLP analizi olanlar',
      value: coverage.value.feedback_employee_count,
      description: 'Geri bildirim metinlerinden guven, is birligi, destek ve burnout sinyali cikarilabilen calisanlar.',
    },
    {
      stage: 'Tam hibrit profili olanlar',
      value: fullSignalCount,
      description: 'KPI/ML, nabiz ve 360 sinyali birlikte bulunan; en guvenilir hibrit yoruma giren calisanlar.',
    },
  ]

  return rows.map((row, index) => {
    const previous = rows[index - 1]
    const conversion = index === 0 ? 100 : percent(Number(row.value), Math.max(Number(previous?.value), 1))
    return {
      stage: row.stage,
      value: row.value,
      conversion,
      dropoff: 100 - conversion,
      description: row.description,
    }
  })
})

const funnelInsights = computed(() => {
  const rows = funnelRows.value
  if (!rows.length) {
    return [{
      title: 'Veri bekleniyor',
      description: 'Hibrit analiz icin henuz yeterli veri yok.',
      impact: 'KPI/ML, nabiz veya 360 kaynaklarindan veri geldikce bu ozet otomatik dolacak.',
    }]
  }
  const worstDrop = rows.slice(1).reduce((worst, row) => row.dropoff > worst.dropoff ? row : worst, rows[1] || rows[0])
  const last = rows[rows.length - 1]
  const total = Number(rows[0].value) || 1
  const fullProfileRate = percent(Number(last.value), total)
  const feedbackMissing = coverage.value.feedback_employee_count === 0

  return [
    {
      title: `Tam hibrit profil: ${last.value}/${rows[0].value} calisan`,
      description: `Departmanda tum veri kaynaklari ayni calisanda birlesen oran %${fullProfileRate}. Bu oran yukseldikce departman sagligi yorumu daha guvenilir hale gelir.`,
      impact: 'Tam profil olmayan calisanlar yine dashboarda girer; ancak eksik kaynak olan boyutlar karar guvenini dusurur.',
    },
    {
      title: `En buyuk eksik kaynak: ${worstDrop.stage}`,
      description: `Bu adimda onceki veri adimina gore %${worstDrop.dropoff} eksilme var. Yani hibrit skorun en zayif veri halkasi burada olusuyor.`,
      impact: 'Once bu kaynagin kapsami artirilirsa hem veri guveni hem de icgoru kalitesi en hizli sekilde iyilesir.',
    },
    feedbackMissing
      ? {
          title: '360 NLP sinyali henuz skora katilamiyor',
          description: '360 feedback analiz kaydi olmadigi icin psikolojik guven, is birligi, destek ihtiyaci ve burnout metin sinyalleri hesaplanamiyor.',
          impact: 'Bu yuzden insan sagligi su anda agirlikla nabiz verisine dayaniyor; 360 cevaplari geldikce tam hibrit profil sayisi artacak.',
        }
      : {
          title: `360 NLP kapsami: %${score(coverage.value.feedback_percentage)}`,
          description: '360 feedback verisi mevcut oldugu icin davranis ve iliski kalitesi hibrit skora katiliyor.',
          impact: 'Bu kaynak KPI/ML sonucunu insan deneyimiyle birlikte yorumlamayi saglar.',
        },
  ]
})

const riskIndicatorGroups = computed<RiskIndicatorGroups>(() => {
  const critical = insights.value
    .filter((item) => item.severity === 'critical')
    .map((item) => item.title)
  const warnings = insights.value
    .filter((item) => item.severity === 'warning')
    .map((item) => item.title)
  const positive = aiSummary.value.strengths.length
    ? aiSummary.value.strengths
    : [`Departman saglik skoru ${score(scores.value.department_health)}/100`]

  return {
    critical: critical.length ? critical : ['Kritik birlesik risk sinyali yok.'],
    warnings: warnings.length ? warnings : ['Uyari sinyali veri geldikce netlesecek.'],
    positive: positive.slice(0, 3),
  }
})

const quickActionItems = computed<QuickActionItem[]>(() => {
  const actions = [
    ...((dashboard.value?.actions.urgent || []).map((item) => ({
      title: item.title,
      description: item.description,
      owner: item.owner,
      dueDate: item.due_date,
      source: item.source,
      priority: 'HIGH' as const,
    }))),
    ...((dashboard.value?.actions.this_week || []).map((item) => ({
      title: item.title,
      description: item.description,
      owner: item.owner,
      dueDate: item.due_date,
      source: item.source,
      priority: 'MEDIUM' as const,
    }))),
    ...((dashboard.value?.actions.monitoring || []).map((item) => ({
      title: item.title,
      description: item.description,
      owner: item.owner,
      dueDate: item.due_date,
      source: item.source,
      priority: 'MEDIUM' as const,
    }))),
  ]
  return actions.length ? actions.slice(0, 6) : [{
    title: 'Hibrit aksiyonlar veri geldikce olusacak.',
    description: 'KPI/ML, nabiz ve 360 kaynaklarindan yeterli sinyal gelince aksiyon onerileri otomatik uretilecek.',
    priority: 'MEDIUM',
  }]
})

function buildScoreCard(options: {
  title: string
  subtitle: string
  value: number
  target: string
  benchmark: string
  icon: Component
  inverse?: boolean
}) {
  const value = score(options.value)
  const good = options.inverse ? value <= 40 : value >= 85
  const warning = options.inverse ? value <= 60 : value >= 70
  const tone = good ? 'good' : warning ? 'warning' : 'risk'
  const statusMap = {
    good: {
      statusLabel: options.inverse ? 'Dusuk Risk' : 'Basarili',
      statusSurfaceClass: 'border-emerald-200 bg-emerald-50',
      statusBadgeClass: 'bg-emerald-100 text-emerald-700',
      iconClass: 'bg-emerald-100 text-emerald-700',
      trendClass: 'bg-emerald-100 text-emerald-700',
      trendTextClass: 'text-emerald-700',
    },
    warning: {
      statusLabel: 'Dikkat',
      statusSurfaceClass: 'border-amber-200 bg-amber-50',
      statusBadgeClass: 'bg-amber-100 text-amber-700',
      iconClass: 'bg-amber-100 text-amber-700',
      trendClass: 'bg-amber-100 text-amber-700',
      trendTextClass: 'text-amber-700',
    },
    risk: {
      statusLabel: 'Risk',
      statusSurfaceClass: 'border-rose-200 bg-rose-50',
      statusBadgeClass: 'bg-rose-100 text-rose-700',
      iconClass: 'bg-rose-100 text-rose-700',
      trendClass: 'bg-rose-100 text-rose-700',
      trendTextClass: 'text-rose-700',
    },
  }[tone]

  return {
    title: options.title,
    subtitle: options.subtitle,
    value,
    max: 100,
    target: options.target,
    benchmark: options.benchmark,
    icon: options.icon,
    trendIcon: options.inverse ? riskIcon(value) : scoreIcon(value),
    trendLabel: options.inverse ? riskLabel(value) : scoreStatus(value),
    ...statusMap,
  }
}

function metric(sourceKey: string, metricKey: string) {
  const value = sources.value[sourceKey]?.metrics?.[metricKey]
  if (value === null || value === undefined || value === '') return '-'
  if (typeof value === 'number') return score(value)
  return String(value)
}

function score(value: unknown) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 0
  return Math.round(numeric * 10) / 10
}

function clamp(value: number, min = 0, max = 100) {
  return Math.max(min, Math.min(max, value))
}

function percent(value: number, total: number) {
  return clamp(Math.round((value / Math.max(total, 1)) * 100), 0, 100)
}

function scoreStatus(value: number) {
  if (value >= 85) return 'Yuksek'
  if (value >= 70) return 'Normal'
  return 'Dusuk'
}

function scoreIcon(value: number) {
  if (value >= 85) return '↑'
  if (value >= 70) return '→'
  return '↓'
}

function scoreToneClass(value: number) {
  if (value >= 85) return 'text-emerald-700'
  if (value >= 70) return 'text-amber-700'
  return 'text-rose-700'
}

function barToneClass(value: number) {
  if (value >= 85) return 'bg-emerald-500'
  if (value >= 70) return 'bg-amber-500'
  return 'bg-rose-500'
}

function riskLabel(value: number) {
  if (value >= 60) return 'Yuksek Risk'
  if (value >= 40) return 'Orta Risk'
  return 'Dusuk Risk'
}

function riskToneClass(value: number) {
  if (value >= 60) return 'text-rose-700'
  if (value >= 40) return 'text-amber-700'
  return 'text-emerald-700'
}

function riskBarClass(value: number) {
  if (value >= 60) return 'bg-rose-500'
  if (value >= 40) return 'bg-amber-500'
  return 'bg-emerald-500'
}

function riskIcon(value: number) {
  if (value >= 60) return '↑'
  if (value >= 40) return '→'
  return '↓'
}

function insightTone(severity: string) {
  if (severity === 'critical') {
    return { label: 'Kritik', surface: 'border-rose-500 bg-rose-50', badge: 'bg-rose-100 text-rose-700', text: 'text-rose-700' }
  }
  if (severity === 'warning') {
    return { label: 'Uyari', surface: 'border-amber-500 bg-amber-50', badge: 'bg-amber-100 text-amber-700', text: 'text-amber-700' }
  }
  if (severity === 'success') {
    return { label: 'Olumlu', surface: 'border-emerald-500 bg-emerald-50', badge: 'bg-emerald-100 text-emerald-700', text: 'text-emerald-700' }
  }
  return { label: 'Bilgi', surface: 'border-blue-500 bg-blue-50', badge: 'bg-blue-100 text-blue-700', text: 'text-blue-700' }
}

function insightSourceLabel(insight: DepartmentDashboardInsightResponse) {
  if (insight.fallback_used) return 'Kural bazli'
  if (insight.source === 'gemini') return 'LLM'
  if (insight.source === 'ollama') return 'LLM'
  if (insight.source?.includes('llm')) return 'LLM'
  return 'Kural bazli'
}

function actionLabel(action: string) {
  if (action === 'urgent') return 'ACIL'
  if (action === 'this_week') return 'Bu Hafta'
  return 'Izleme'
}

function statusLabel(status: string) {
  if (status === 'success' || status === 'healthy') return 'OK'
  if (status === 'warning') return 'Dikkat'
  if (status === 'danger') return 'Risk'
  return status || '-'
}

function statusBadge(status: string) {
  if (status === 'success' || status === 'healthy') return 'bg-emerald-100 text-emerald-700'
  if (status === 'warning') return 'bg-amber-100 text-amber-700'
  return 'bg-rose-100 text-rose-700'
}

function trendIcon(trend: string) {
  if (trend === 'yukselis') return '↑'
  if (trend === 'dusus') return '↓'
  return '→'
}

function trendClass(trend: string) {
  if (trend === 'yukselis') return 'text-emerald-600'
  if (trend === 'dusus') return 'text-rose-600'
  return 'text-slate-500'
}

function formatDate(value?: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('tr-TR')
}

function formatDateTime(value?: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('tr-TR')
}

async function refreshDashboard() {
  loading.value = true
  errorMessage.value = ''
  try {
    dashboard.value = await analyticsApi.getSoftwareDepartmentDashboard({
      period: selectedPeriod.value,
      use_llm: true,
    })
  } catch (error) {
    console.error('Hibrit departman dashboard yuklenemedi:', error)
    errorMessage.value = 'Hibrit departman dashboard verisi yuklenemedi.'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await refreshDashboard()
})
</script>
