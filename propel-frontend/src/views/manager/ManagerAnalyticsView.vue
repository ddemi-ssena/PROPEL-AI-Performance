<template>
  <div class="space-y-8 pb-10">
    <div class="flex flex-col xl:flex-row xl:items-end xl:justify-between gap-4 border-b border-slate-200 pb-6">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 tracking-tight">KPI & ML Analizi</h2>
        <p class="mt-1 text-slate-500">
          Departman bazli KPI omurgasi, ensemble mimarisi ve sprint hazirlik durumunu tek ekranda izleyin.
        </p>
      </div>

      <div class="flex flex-col sm:flex-row gap-3">
        <select
          v-model="selectedDepartment"
          class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 shadow-sm"
        >
          <option
            v-for="config in departmentConfigs"
            :key="config.key"
            :value="config.key"
          >
            {{ config.label }}
          </option>
        </select>

        <select
          v-model="selectedTeam"
          class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 shadow-sm"
        >
          <option value="all">Tum Takimlar</option>
          <option
            v-for="team in selectedDepartmentConfig?.supported_teams || []"
            :key="team"
            :value="team"
          >
            {{ team }}
          </option>
        </select>
      </div>
    </div>

    <div v-if="overview" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
      <div
        v-for="metric in overview.metrics"
        :key="metric.key"
        class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
      >
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
          {{ metric.label }}
        </p>
        <p class="mt-3 text-2xl font-bold text-slate-900">{{ metric.value }}</p>
        <p class="mt-2 text-xs leading-5 text-slate-500">{{ metric.hint }}</p>
      </div>
    </div>

    <div
      v-if="selectedDepartment === 'software'"
      class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
    >
      <div class="flex flex-col xl:flex-row xl:items-start xl:justify-between gap-5">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">ML Model</p>
          <h3 class="mt-1 text-lg font-bold text-slate-900">Software risk tahmini</h3>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-3 w-full xl:max-w-5xl">
          <input
            v-model.number="mlUploadId"
            type="number"
            min="1"
            placeholder="Upload ID"
            class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 shadow-sm"
          />

          <select
            v-model="mlTargetColumn"
            class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 shadow-sm"
          >
            <option value="performance_band">Performans</option>
            <option value="attrition_risk_band">Ayrilma Riski</option>
          </select>

          <select
            v-model.number="mlEmployeeId"
            class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 shadow-sm"
          >
            <option
              v-for="employee in overview?.employee_summaries || []"
              :key="employee.employee_id"
              :value="employee.employee_id"
            >
              {{ employee.employee_name }}
            </option>
          </select>

          <button
            class="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm disabled:cursor-not-allowed disabled:bg-slate-300"
            :disabled="Boolean(mlLoading) || !mlUploadId"
            @click="trainModel"
          >
            {{ mlLoading === 'train' ? 'Egitiliyor...' : 'Model Egit' }}
          </button>

          <button
            class="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm disabled:cursor-not-allowed disabled:text-slate-300"
            :disabled="Boolean(mlLoading) || !mlUploadId || !mlEmployeeId"
            @click="loadPrediction"
          >
            {{ mlLoading === 'predict' ? 'Hesaplaniyor...' : 'Tahmin Al' }}
          </button>
        </div>
      </div>

      <div v-if="mlError" class="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
        {{ mlError }}
      </div>

      <div v-if="trainingResult || predictionResult" class="mt-5 grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div v-if="trainingResult" class="rounded-2xl border border-slate-200 bg-slate-50 p-5">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Egitim Sonucu</p>
          <p class="mt-3 text-2xl font-bold text-slate-900">
            {{ formatPercent(trainingResult.metrics?.weighted_f1) }}
          </p>
          <div class="mt-3 space-y-1 text-xs text-slate-500">
            <p>Train/Test: {{ trainingResult.train_count }} / {{ trainingResult.test_count }}</p>
            <p>Accuracy: {{ formatPercent(trainingResult.metrics?.accuracy) }}</p>
            <p>Macro F1: {{ formatPercent(trainingResult.metrics?.macro_f1) }}</p>
          </div>
        </div>

        <div v-if="predictionResult" class="rounded-2xl border border-slate-200 bg-slate-50 p-5">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Son Tahmin</p>
          <p class="mt-3 text-2xl font-bold text-slate-900">{{ predictionResult.predicted_band }}</p>
          <div class="mt-3 space-y-1 text-xs text-slate-500">
            <p>Guven: {{ formatPercent(predictionResult.confidence) }}</p>
            <p>Donem: {{ formatPeriod(predictionResult.summary_payload?.period_date) }}</p>
            <p>Model: {{ predictionResult.summary_payload?.model_name || '-' }}</p>
          </div>
        </div>

        <div
          v-if="(predictionResult?.top_features?.length || trainingResult?.top_features?.length)"
          class="rounded-2xl border border-slate-200 bg-slate-50 p-5"
        >
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Etkili Sinyaller</p>
          <div class="mt-3 space-y-2">
            <div
              v-for="item in (predictionResult?.top_features || trainingResult?.top_features || []).slice(0, 5)"
              :key="item.feature"
              class="flex items-center justify-between gap-3 text-xs"
            >
              <span class="font-medium text-slate-700">{{ formatFeatureName(item.feature) }}</span>
              <span class="text-slate-500">{{ Number(item.importance || 0).toFixed(3) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="selectedDepartmentConfig" class="grid grid-cols-1 xl:grid-cols-[minmax(0,1.25fr)_360px] gap-6">
      <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Analytics Omurgasi</p>
            <h3 class="mt-1 text-xl font-bold text-slate-900">
              {{ selectedDepartmentConfig.label }} Departmani
            </h3>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              {{ selectedDepartmentConfig.description }}
            </p>
          </div>
          <span
            class="rounded-full px-3 py-1 text-xs font-semibold"
            :class="selectedDepartmentConfig.readiness_status === 'live'
              ? 'border border-emerald-200 bg-emerald-50 text-emerald-700'
              : 'border border-amber-200 bg-amber-50 text-amber-700'"
          >
            {{ readinessLabel(selectedDepartmentConfig.readiness_status) }}
          </span>
        </div>

        <div class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            v-for="layer in selectedDepartmentConfig.layers"
            :key="layer.key"
            class="rounded-2xl border border-indigo-100 bg-indigo-50 p-5"
          >
            <p class="text-sm font-semibold text-indigo-900">{{ layer.title }}</p>
            <p class="mt-2 text-sm leading-6 text-slate-700">{{ layer.summary }}</p>
          </div>
        </div>
      </div>

      <div class="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-lg">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Sprint 1</p>
        <h3 class="mt-2 text-lg font-bold text-white">Yapilanlar ve siradaki adim</h3>

        <div class="mt-5 space-y-4">
          <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p class="text-xs font-semibold text-slate-300">Planlanan hedefler</p>
            <div class="mt-3 flex flex-wrap gap-2">
              <span
                v-for="target in selectedDepartmentConfig.planned_targets"
                :key="target"
                class="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-2 py-1 text-xs text-indigo-100"
              >
                {{ target }}
              </span>
            </div>
          </div>

          <div v-if="overview" class="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p class="text-xs font-semibold text-slate-300">Sprint odagi</p>
            <ul class="mt-3 space-y-2 text-sm text-slate-200">
              <li v-for="item in overview.sprint_focus" :key="item">• {{ item }}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <div v-if="overview?.team_summaries.length" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div class="flex items-center justify-between gap-3">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Takim Karsilastirmasi</p>
          <h3 class="mt-1 text-lg font-bold text-slate-900">Canli KPI kapsam ozeti</h3>
        </div>
        <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
          Son donem: {{ formatPeriod(overview.latest_period) }}
        </span>
      </div>

      <div class="mt-6 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <div
          v-for="teamSummary in overview.team_summaries"
          :key="teamSummary.team"
          class="rounded-2xl border border-slate-200 bg-slate-50 p-5"
        >
          <p class="text-sm font-semibold text-slate-900">{{ teamSummary.team }}</p>
          <p class="mt-3 text-2xl font-bold text-slate-900">{{ teamSummary.average_score }}/100</p>
          <div class="mt-3 space-y-1 text-xs text-slate-500">
            <p>{{ teamSummary.employee_count }} calisan</p>
            <p>{{ teamSummary.watchlist_count }} izleme gerekli</p>
            <p v-if="teamSummary.average_trend_delta !== null && teamSummary.average_trend_delta !== undefined">
              Trend: {{ formatSigned(teamSummary.average_trend_delta) }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <div v-if="overview" class="grid grid-cols-1 xl:grid-cols-[minmax(0,1.2fr)_360px] gap-6">
      <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex items-center justify-between gap-3">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Calisan Snapshot</p>
            <h3 class="mt-1 text-lg font-bold text-slate-900">KPI performans ve risk gorunumu</h3>
          </div>
          <span class="text-xs font-semibold text-slate-500">
            {{ overview.employee_summaries.length }} kisi
          </span>
        </div>

        <div class="mt-5 overflow-x-auto">
          <table class="min-w-full divide-y divide-slate-200 text-sm">
            <thead>
              <tr class="text-left text-slate-500">
                <th class="pb-3 font-medium">Calisan</th>
                <th class="pb-3 font-medium">Takim</th>
                <th class="pb-3 font-medium">Skor</th>
                <th class="pb-3 font-medium">Trend</th>
                <th class="pb-3 font-medium">Guc</th>
                <th class="pb-3 font-medium">Risk</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="employee in overview.employee_summaries"
                :key="employee.employee_id"
                class="align-top"
              >
                <td class="py-3 pr-4">
                  <div class="font-semibold text-slate-900">{{ employee.employee_name }}</div>
                  <div class="text-xs text-slate-500">
                    {{ employee.external_employee_code || '-' }} · {{ employee.position || 'Calisan' }}
                  </div>
                </td>
                <td class="py-3 pr-4 text-slate-600">{{ employee.team || '-' }}</td>
                <td class="py-3 pr-4 font-semibold text-slate-900">{{ employee.latest_score }}/100</td>
                <td class="py-3 pr-4" :class="trendClass(employee.trend_delta)">
                  {{ formatSigned(employee.trend_delta) }}
                </td>
                <td class="py-3 pr-4 text-slate-600">{{ employee.strongest_category || '-' }}</td>
                <td class="py-3">
                  <span
                    class="rounded-full px-2.5 py-1 text-xs font-semibold"
                    :class="riskBandClass(employee.risk_band)"
                  >
                    {{ employee.risk_band }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Mimari Notlar</p>
        <h3 class="mt-2 text-lg font-bold text-slate-900">Departman adapter mantigi</h3>
        <ul class="mt-5 space-y-3 text-sm leading-6 text-slate-600">
          <li v-for="note in overview.notes" :key="note">
            • {{ note }}
          </li>
        </ul>
      </div>
    </div>

    <div v-if="loading" class="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500 shadow-sm">
      Analytics ozeti yukleniyor...
    </div>

    <div v-if="error" class="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700 shadow-sm">
      {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  analyticsApi,
  type DepartmentAnalyticsConfigResponse,
  type DepartmentAnalyticsOverviewResponse,
  type SoftwareModelTrainResponse,
  type SoftwarePredictionResponse,
} from '@/services/api/analytics.api'

const departmentConfigs = ref<DepartmentAnalyticsConfigResponse[]>([])
const overview = ref<DepartmentAnalyticsOverviewResponse | null>(null)
const selectedDepartment = ref('software')
const selectedTeam = ref('all')
const loading = ref(false)
const error = ref<string | null>(null)
const mlUploadId = ref<number | null>(null)
const mlTargetColumn = ref('performance_band')
const mlEmployeeId = ref<number | null>(null)
const mlLoading = ref<'train' | 'predict' | null>(null)
const mlError = ref<string | null>(null)
const trainingResult = ref<SoftwareModelTrainResponse | null>(null)
const predictionResult = ref<SoftwarePredictionResponse | null>(null)

const selectedDepartmentConfig = computed(() =>
  departmentConfigs.value.find((item) => item.key === selectedDepartment.value) || null
)

function readinessLabel(status: string) {
  if (status === 'live') return 'Canli'
  if (status === 'awaiting_dataset') return 'Veri Bekleniyor'
  return status
}

function formatPeriod(value?: string | null) {
  if (!value) return 'Veri yok'
  return new Date(value).toLocaleDateString('tr-TR', { month: 'long', year: 'numeric' })
}

function formatSigned(value?: number | null) {
  if (value === null || value === undefined) return '-'
  return `${value > 0 ? '+' : ''}${value}`
}

function formatPercent(value?: number | null) {
  if (value === null || value === undefined) return '-'
  return `${Math.round(value * 1000) / 10}%`
}

function formatFeatureName(value?: string) {
  if (!value) return '-'
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function trendClass(value?: number | null) {
  if (value === null || value === undefined) return 'text-slate-500'
  if (value > 0) return 'text-emerald-600 font-semibold'
  if (value < 0) return 'text-rose-600 font-semibold'
  return 'text-slate-500'
}

function riskBandClass(band: string) {
  if (band === 'Guclu') return 'bg-emerald-50 text-emerald-700 border border-emerald-200'
  if (band === 'Stabil') return 'bg-amber-50 text-amber-700 border border-amber-200'
  return 'bg-rose-50 text-rose-700 border border-rose-200'
}

async function loadDepartmentConfigs() {
  departmentConfigs.value = await analyticsApi.getDepartmentConfigs()
  if (!departmentConfigs.value.find((item) => item.key === selectedDepartment.value) && departmentConfigs.value[0]) {
    selectedDepartment.value = departmentConfigs.value[0].key
  }
}

async function loadOverview() {
  loading.value = true
  error.value = null
  try {
    overview.value = await analyticsApi.getDepartmentOverview(
      selectedDepartment.value,
      { team: selectedTeam.value === 'all' ? undefined : selectedTeam.value }
    )
    if (!mlEmployeeId.value && overview.value.employee_summaries[0]) {
      mlEmployeeId.value = overview.value.employee_summaries[0].employee_id
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Analytics ozeti yuklenemedi.'
  } finally {
    loading.value = false
  }
}

async function trainModel() {
  if (!mlUploadId.value) return
  mlLoading.value = 'train'
  mlError.value = null
  try {
    trainingResult.value = await analyticsApi.trainSoftwareModel({
      upload_id: mlUploadId.value,
      target_column: mlTargetColumn.value,
    })
    predictionResult.value = null
  } catch (err: any) {
    mlError.value = err.response?.data?.detail || 'Model egitimi basarisiz oldu.'
  } finally {
    mlLoading.value = null
  }
}

async function loadPrediction() {
  if (!mlUploadId.value || !mlEmployeeId.value) return
  mlLoading.value = 'predict'
  mlError.value = null
  try {
    predictionResult.value = await analyticsApi.getLatestSoftwarePrediction({
      upload_id: mlUploadId.value,
      employee_id: mlEmployeeId.value,
      target_column: mlTargetColumn.value,
    })
  } catch (err: any) {
    mlError.value = err.response?.data?.detail || 'Tahmin alinamadi.'
  } finally {
    mlLoading.value = null
  }
}

watch(selectedDepartment, async () => {
  selectedTeam.value = 'all'
  await loadOverview()
})

watch(selectedTeam, async () => {
  await loadOverview()
})

onMounted(async () => {
  await loadDepartmentConfigs()
  await loadOverview()
})
</script>
