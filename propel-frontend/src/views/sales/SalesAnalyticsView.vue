<template>
  <div class="space-y-8 pb-10">
    <!-- Header ----------------------------------------------------------------->
    <div class="rounded-[28px] border border-emerald-100 bg-[radial-gradient(circle_at_top_left,rgba(16,185,129,0.12),transparent_35%),linear-gradient(135deg,#ffffff,#ecfdf5)] p-8 shadow-sm">
      <div class="flex flex-col xl:flex-row xl:items-end xl:justify-between gap-6">
        <div class="max-w-3xl">
          <p class="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-600">Satış Departmanı · KPI & ML</p>
          <h2 class="mt-3 text-3xl font-bold tracking-tight text-slate-900">Satış Performansı Analizi</h2>
          <p class="mt-3 text-sm leading-6 text-slate-600">
            LightGBM + XGBoost + RandomForest stacking ensemble mimarisi ile satış ekibinin performans düşüşü,
            tükenmişlik, istifa riski ve yüksek risk tahminlerini tek ekranda yönetin.
          </p>
        </div>
        <div class="flex flex-col sm:flex-row gap-3 min-w-[340px]">
          <select
            v-model.number="uploadId"
            class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 shadow-sm flex-1"
            @change="onDatasetChange"
          >
            <option :value="null">Dataset seçin</option>
            <option v-for="ds in datasets" :key="ds.id" :value="ds.id">
              #{{ ds.id }} — {{ ds.file_name }}
            </option>
          </select>
          <select
            v-model="targetColumn"
            class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 shadow-sm flex-1"
          >
            <option v-for="t in TARGETS" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- KPI Overview metrics (from dept overview) ----------------------------->
    <div v-if="overview" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
      <div
        v-for="metric in overview.metrics"
        :key="metric.key"
        class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
      >
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{{ metric.label }}</p>
        <p class="mt-3 text-2xl font-bold text-slate-900">{{ metric.value }}</p>
        <p class="mt-2 text-xs leading-5 text-slate-500">{{ metric.hint }}</p>
      </div>
    </div>

    <!-- Model Control Panel -------------------------------------------------->
    <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div class="flex flex-col xl:flex-row xl:items-start xl:justify-between gap-5">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Stacking Ensemble</p>
          <h3 class="mt-1 text-lg font-bold text-slate-900">Satış risk tahmini — LightGBM + XGB + RF → LR</h3>
        </div>
        <div class="flex flex-wrap gap-3">
          <button
            class="rounded-xl bg-emerald-700 px-5 py-2.5 text-sm font-semibold text-white shadow-sm disabled:cursor-not-allowed disabled:bg-slate-300"
            :disabled="!!loading || !uploadId"
            @click="trainModel"
          >
            {{ loading === 'train' ? 'Eğitiliyor...' : 'Model Eğit' }}
          </button>
          <select
            v-model.number="employeeId"
            class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 shadow-sm"
          >
            <option :value="null">Çalışan seçin</option>
            <option v-for="e in datasetEmployees" :key="e.employee_id" :value="e.employee_id">
              {{ e.display_label || `${e.team || 'Takım'} / #${e.employee_id}` }}
            </option>
          </select>
          <button
            class="rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 shadow-sm disabled:cursor-not-allowed disabled:text-slate-300"
            :disabled="!!loading || !uploadId || !employeeId"
            @click="predict"
          >
            {{ loading === 'predict' ? 'Hesaplanıyor...' : 'Tahmin Al' }}
          </button>
          <button
            class="rounded-xl border border-emerald-200 bg-emerald-50 px-5 py-2.5 text-sm font-semibold text-emerald-800 shadow-sm disabled:cursor-not-allowed disabled:text-emerald-300"
            :disabled="!!loading || !uploadId"
            @click="bulkPredict(false)"
          >
            {{ loading === 'bulk' ? 'Taranıyor...' : 'Toplu Tara' }}
          </button>
          <button
            class="rounded-xl border border-violet-200 bg-violet-50 px-5 py-2.5 text-sm font-semibold text-violet-800 shadow-sm disabled:cursor-not-allowed disabled:text-violet-300"
            :disabled="!!loading || !uploadId"
            @click="bulkPredict(true)"
          >
            {{ loading === 'narrative' ? 'Yorumlanıyor...' : 'LLM Yorumla' }}
          </button>
        </div>
      </div>

      <!-- Status badges -------------------------------------------------------->
      <div class="mt-4 flex flex-wrap items-center gap-2 text-xs text-slate-500">
        <span v-if="trainResult" class="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 font-semibold text-emerald-700">
          Model hazır: {{ targetLabel(trainResult.target_column) }} — F1 {{ formatPct(trainResult.metrics?.weighted_f1) }}
        </span>
        <span v-if="error" class="rounded-full border border-rose-200 bg-rose-50 px-3 py-1 font-semibold text-rose-700">
          {{ error }}
        </span>
      </div>

      <!-- Model state grid ----------------------------------------------------->
      <div v-if="uploadId && modelStates.length" class="mt-5 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
        <div
          v-for="state in modelStates"
          :key="state.target_column"
          class="rounded-xl border p-4"
          :class="stateCardClass(state)"
        >
          <div class="flex items-start justify-between gap-2">
            <p class="text-sm font-bold text-slate-900 leading-5">{{ state.target_label }}</p>
            <span class="rounded-full px-2.5 py-1 text-xs font-semibold whitespace-nowrap" :class="stateBadgeClass(state)">
              {{ stateLabel(state) }}
            </span>
          </div>
          <p class="mt-2 text-xs text-slate-500">
            {{ state.is_trained ? `Son eğitim: ${formatDt(state.trained_at)}` : 'Henüz eğitilmedi' }}
          </p>
          <div v-if="state.is_trained" class="mt-3 grid grid-cols-2 gap-2 text-xs">
            <div class="rounded-lg bg-white/70 px-2 py-1.5">
              <p class="text-slate-400">Weighted F1</p>
              <p class="font-bold text-slate-800">{{ formatPct(state.metrics?.weighted_f1) }}</p>
            </div>
            <div class="rounded-lg bg-white/70 px-2 py-1.5">
              <p class="text-slate-400">Train / Test</p>
              <p class="font-bold text-slate-800">{{ state.train_count }} / {{ state.test_count }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Individual prediction result ----------------------------------------->
    <div v-if="predResult" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Bireysel Tahmin</p>
          <h3 class="mt-1 text-xl font-bold text-slate-900">
            {{ displayName(predResult) }}
            <span class="ml-3 rounded-full px-3 py-1 text-sm" :class="bandClass(predResult.predicted_band, predResult.target_column)">
              {{ bandLabel(predResult.predicted_band, predResult.target_column) }}
            </span>
          </h3>
          <p class="mt-2 text-sm text-slate-600">{{ targetLabel(predResult.target_column) }} · Güven: {{ pct(predResult.confidence) }}</p>
        </div>
      </div>

      <p class="mt-5 text-sm leading-6 text-slate-700">
        {{ predResult.narrative?.manager_summary || predResult.risk_summary }}
      </p>

      <div class="mt-5 grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- Top drivers -->
        <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Temel Sürücüler</p>
          <div class="mt-3 space-y-3">
            <div v-for="d in predResult.top_drivers.slice(0, 5)" :key="d.metric_name" class="flex items-start justify-between gap-3 text-sm">
              <div>
                <p class="font-semibold text-slate-900">{{ d.metric_name }}</p>
                <p class="text-xs text-slate-500">{{ d.threshold_status }}</p>
              </div>
              <span
                class="rounded-full px-2 py-0.5 text-xs font-semibold"
                :class="d.trend_signal === 'declining' ? 'bg-rose-50 text-rose-700' : d.trend_signal === 'improving' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'"
              >{{ d.trend_signal }}</span>
            </div>
          </div>
        </div>
        <!-- Recommended actions -->
        <div class="rounded-xl border border-emerald-100 bg-emerald-50 p-4">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600">Önerilen Aksiyonlar</p>
          <ul class="mt-3 space-y-2 text-sm text-slate-700">
            <li v-for="a in predResult.recommended_actions" :key="a">— {{ a }}</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Bulk / Team Analytics ------------------------------------------------->
    <div v-if="bulkResult" class="space-y-6">

      <!-- Summary cards -------------------------------------------------------->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="rounded-2xl border border-rose-100 bg-rose-50 p-5 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-rose-400">Yüksek Risk</p>
          <p class="mt-3 text-3xl font-bold text-rose-700">{{ bulkResult.high_risk_count }}</p>
          <p class="mt-1 text-xs text-rose-600">çalışan izleniyor</p>
        </div>
        <div class="rounded-2xl border border-amber-100 bg-amber-50 p-5 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-amber-400">Orta Risk</p>
          <p class="mt-3 text-3xl font-bold text-amber-700">{{ bulkResult.medium_risk_count }}</p>
          <p class="mt-1 text-xs text-amber-600">çalışan dikkat listesinde</p>
        </div>
        <div class="rounded-2xl border border-emerald-100 bg-emerald-50 p-5 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-400">Düşük Risk</p>
          <p class="mt-3 text-3xl font-bold text-emerald-700">{{ bulkResult.low_risk_count }}</p>
          <p class="mt-1 text-xs text-emerald-600">çalışan stabil</p>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Toplam Analiz</p>
          <p class="mt-3 text-3xl font-bold text-slate-900">{{ bulkResult.prediction_count }}</p>
          <p class="mt-1 text-xs text-slate-500">{{ targetLabel(bulkResult.target_column) }}</p>
        </div>
      </div>

      <!-- Department narrative ------------------------------------------------->
      <div v-if="deptNarrative" class="rounded-2xl border border-violet-100 bg-violet-50/70 p-6 shadow-sm">
        <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-violet-500">Departman Yorumu</p>
            <h4 class="mt-1 text-lg font-bold text-slate-900">{{ deptNarrative.manager_summary }}</h4>
          </div>
          <span class="w-fit rounded-full border border-violet-200 bg-white px-3 py-1 text-xs font-semibold text-violet-700">
            {{ narrativeSrc(deptNarrative.source) }}
          </span>
        </div>
        <p class="mt-4 text-sm leading-6 text-slate-700">{{ deptNarrative.risk_interpretation }}</p>
        <div v-if="deptNarrative.action_plan?.length" class="mt-5 grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div class="rounded-xl border border-white/70 bg-white p-4">
            <p class="text-xs font-semibold text-slate-500">Aksiyon Planı</p>
            <div class="mt-3 space-y-3">
              <div v-for="a in deptNarrative.action_plan.slice(0, 4)" :key="a.title" class="border-b border-slate-100 pb-3 last:border-b-0 last:pb-0">
                <p class="text-sm font-semibold text-slate-900">{{ a.title }}</p>
                <p class="mt-1 text-xs text-slate-600">{{ a.reason }}</p>
                <p class="mt-1 text-xs font-semibold text-violet-700">{{ a.owner }} / {{ a.timeframe }}</p>
              </div>
            </div>
          </div>
          <div class="rounded-xl border border-white/70 bg-white p-4">
            <p class="text-xs font-semibold text-slate-500">Takım Liderlerine Konuşma Noktaları</p>
            <ul class="mt-3 space-y-2 text-sm text-slate-700">
              <li v-for="tp in flatTalkingPoints(deptNarrative)" :key="tp">— {{ tp }}</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Team analytics table ------------------------------------------------->
      <div v-if="teamRows.length" class="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-slate-100">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Bölge / Takım Analizi</p>
          <h4 class="mt-1 text-lg font-bold text-slate-900">Satış Takımları Risk Özeti</h4>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-slate-100 text-sm">
            <thead>
              <tr class="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <th class="px-5 py-3 text-left">Bölge / Takım</th>
                <th class="px-5 py-3 text-left">Ort. Risk</th>
                <th class="px-5 py-3 text-left">Yüksek Risk</th>
                <th class="px-5 py-3 text-left">Kişi</th>
                <th class="px-5 py-3 text-left">Durum</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="(row, i) in teamRows"
                :key="row.team"
                class="cursor-pointer transition hover:bg-emerald-50/40"
                :class="i % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'"
                @click="selectTeam(row.team)"
              >
                <td class="px-5 py-4 font-semibold text-slate-900">{{ row.team }}</td>
                <td class="px-5 py-4">
                  <div class="flex items-center gap-2">
                    <div class="w-20 h-2 rounded-full bg-slate-100 overflow-hidden">
                      <div class="h-full rounded-full" :class="row.avgRisk > 60 ? 'bg-rose-500' : row.avgRisk > 35 ? 'bg-amber-500' : 'bg-emerald-500'" :style="{ width: `${row.avgRisk}%` }"></div>
                    </div>
                    <span class="text-xs font-bold text-slate-700">{{ row.avgRisk }}</span>
                  </div>
                </td>
                <td class="px-5 py-4 font-bold" :class="row.highCount > 0 ? 'text-rose-600' : 'text-slate-400'">{{ row.highCount }}</td>
                <td class="px-5 py-4 text-slate-600">{{ row.total }}</td>
                <td class="px-5 py-4">
                  <span class="rounded-full px-2.5 py-1 text-xs font-semibold"
                    :class="row.avgRisk > 60 ? 'bg-rose-50 text-rose-700 border border-rose-200' : row.avgRisk > 35 ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'">
                    {{ row.avgRisk > 60 ? 'Kritik' : row.avgRisk > 35 ? 'İzleme' : 'Stabil' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Selected team detail ------------------------------------------------->
      <div v-if="selectedTeamName" class="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div class="bg-gradient-to-r from-emerald-700 to-teal-600 px-6 py-5 flex items-center justify-between gap-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-100">Seçili Takım</p>
            <h4 class="mt-1 text-2xl font-bold text-white">{{ selectedTeamName }}</h4>
            <p class="mt-1 text-sm text-emerald-100">{{ selectedTeamPeople.length }} çalışan analizi</p>
          </div>
          <button class="text-white/60 hover:text-white text-xl font-bold" @click="selectedTeamName = null">✕</button>
        </div>

        <!-- Team narrative -->
        <div v-if="selectedTeamNarrative" class="px-6 py-4 border-b border-slate-100 bg-violet-50/40">
          <p class="text-sm font-semibold text-slate-900">{{ selectedTeamNarrative.manager_summary }}</p>
          <p class="mt-2 text-sm text-slate-600">{{ selectedTeamNarrative.risk_interpretation }}</p>
        </div>

        <!-- People cards -->
        <div class="p-6 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <article
            v-for="(person, idx) in selectedTeamPeople"
            :key="person.employee_id"
            class="rounded-xl border border-slate-100 bg-white p-5 shadow-sm"
          >
            <div class="flex items-start gap-4">
              <span
                class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full text-white font-bold text-sm"
                :class="avatarGradient(idx)"
              >{{ empInitials(person) }}</span>
              <div class="min-w-0">
                <p class="font-bold text-slate-900 truncate">{{ displayName(person) }}</p>
                <p class="text-xs text-slate-500 mt-1">{{ person.summary_payload?.role || person.summary_payload?.region || 'Satış' }}</p>
              </div>
            </div>
            <div class="mt-4 flex items-center justify-between gap-3">
              <span class="text-xs text-slate-500">Güven: {{ pct(person.confidence) }}</span>
              <span class="rounded-full px-2.5 py-1 text-xs font-semibold" :class="bandClass(person.predicted_band, person.target_column)">
                {{ bandLabel(person.predicted_band, person.target_column) }}
              </span>
            </div>
            <div v-if="person.top_drivers?.[0]" class="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
              Ana sinyal: <span class="font-semibold">{{ person.top_drivers[0].metric_name }}</span>
            </div>
            <div v-if="person.recommended_actions?.[0]" class="mt-2 rounded-lg bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
              {{ person.recommended_actions[0] }}
            </div>
          </article>
        </div>
      </div>

      <!-- All employees table -------------------------------------------------->
      <div class="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between gap-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Çalışan Listesi</p>
            <h4 class="mt-1 text-lg font-bold text-slate-900">Tüm tahminler</h4>
          </div>
          <input
            v-model="tableSearch"
            type="text"
            placeholder="Çalışan ara…"
            class="rounded-xl border border-slate-200 px-4 py-2 text-sm text-slate-700 shadow-sm w-56"
          />
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-slate-100 text-sm">
            <thead>
              <tr class="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <th class="px-5 py-3 text-left">Çalışan</th>
                <th class="px-5 py-3 text-left">Bölge / Rol</th>
                <th class="px-5 py-3 text-left">Tahmin</th>
                <th class="px-5 py-3 text-left">Güven</th>
                <th class="px-5 py-3 text-left">Ana Sinyal</th>
                <th class="px-5 py-3 text-left">Öneri</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="(item, i) in filteredItems"
                :key="item.employee_id"
                class="hover:bg-emerald-50/40 transition"
                :class="i % 2 === 0 ? 'bg-white' : 'bg-slate-50/40'"
              >
                <td class="px-5 py-3 font-semibold text-slate-900">{{ displayName(item) }}</td>
                <td class="px-5 py-3 text-slate-500">{{ item.summary_payload?.region || item.summary_payload?.role || '—' }}</td>
                <td class="px-5 py-3">
                  <span class="rounded-full px-2.5 py-1 text-xs font-semibold" :class="bandClass(item.predicted_band, item.target_column)">
                    {{ bandLabel(item.predicted_band, item.target_column) }}
                  </span>
                </td>
                <td class="px-5 py-3 text-slate-600">{{ pct(item.confidence) }}</td>
                <td class="px-5 py-3 text-slate-600">{{ item.top_drivers?.[0]?.metric_name || '—' }}</td>
                <td class="px-5 py-3 text-slate-500 max-w-xs truncate">{{ item.recommended_actions?.[0] || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Empty state ---------------------------------------------------------->
    <div v-if="!bulkResult && !predResult && !loading" class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-12 text-center">
      <div class="text-5xl">📈</div>
      <h4 class="mt-4 text-xl font-bold text-slate-900">Satış ML Analizine Hoş Geldiniz</h4>
      <p class="mt-2 text-sm text-slate-500 max-w-md mx-auto">
        Bir dataset seçin, hedef değişkeni belirleyin ve "Toplu Tara" ile tüm satış ekibinin risk analizini başlatın.
      </p>
    </div>

    <!-- Loading overlay -------------------------------------------------------->
    <div v-if="loading" class="fixed inset-0 z-50 flex items-center justify-center bg-white/60 backdrop-blur-sm">
      <div class="rounded-2xl border border-slate-200 bg-white p-8 shadow-xl text-center">
        <div class="h-10 w-10 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600 mx-auto"></div>
        <p class="mt-4 text-sm font-semibold text-slate-700">
          {{ loading === 'train' ? 'Model eğitiliyor...' : loading === 'predict' ? 'Tahmin hesaplanıyor...' : 'Toplu analiz çalışıyor...' }}
        </p>
        <p class="mt-1 text-xs text-slate-400">Bu işlem birkaç saniye sürebilir.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  analyticsApi,
  type SalesBulkPredictionResponse,
  type SalesModelStateResponse,
  type SalesModelTrainResponse,
  type SalesPredictionResponse,
  type SalesTargetColumn,
  type SoftwareDatasetEmployeeResponse,
  type SoftwareDatasetResponse,
  type DepartmentAnalyticsOverviewResponse,
} from '@/services/api/analytics.api'

const TARGETS: { value: SalesTargetColumn; label: string }[] = [
  { value: 'Performance_Drop_Target', label: 'Performans Düşüşü' },
  { value: 'Burnout_Target', label: 'Tükenmişlik' },
  { value: 'Resignation_Target', label: 'İstifa Riski' },
  { value: 'High_Risk_Target', label: 'Yüksek Risk' },
]

const datasets = ref<SoftwareDatasetResponse[]>([])
const uploadId = ref<number | null>(null)
const targetColumn = ref<SalesTargetColumn>('Performance_Drop_Target')
const employeeId = ref<number | null>(null)
const datasetEmployees = ref<SoftwareDatasetEmployeeResponse[]>([])
const modelStates = ref<SalesModelStateResponse[]>([])
const trainResult = ref<SalesModelTrainResponse | null>(null)
const predResult = ref<SalesPredictionResponse | null>(null)
const bulkResult = ref<SalesBulkPredictionResponse | null>(null)
const overview = ref<DepartmentAnalyticsOverviewResponse | null>(null)
const loading = ref<string | null>(null)
const error = ref<string | null>(null)
const tableSearch = ref('')
const selectedTeamName = ref<string | null>(null)

// ── Computed -----------------------------------------------------------------

const deptNarrative = computed(() => bulkResult.value?.department_narrative || null)

const teamRows = computed(() => {
  const analytics = bulkResult.value?.team_analytics
  if (!analytics?.length) return []
  return analytics.map((ta: any) => {
    const items = bulkResult.value!.items.filter((i) => (i.summary_payload?.region || i.summary_payload?.team || 'Genel') === ta.team)
    const avgRisk = Math.round((ta.high_risk_rate ?? 0) * 100)
    return {
      team: ta.team as string,
      avgRisk,
      highCount: ta.high_risk_count ?? 0,
      total: ta.employee_count ?? items.length,
    }
  })
})

const selectedTeamPeople = computed(() => {
  if (!selectedTeamName.value || !bulkResult.value) return []
  return bulkResult.value.items.filter((i) => {
    const region = i.summary_payload?.region || i.summary_payload?.team || 'Genel'
    return region === selectedTeamName.value
  })
})

const selectedTeamNarrative = computed(() => {
  if (!selectedTeamName.value || !bulkResult.value) return null
  return bulkResult.value.team_narratives.find((n: any) => n.team === selectedTeamName.value) || null
})

const filteredItems = computed(() => {
  const q = tableSearch.value.trim().toLowerCase()
  if (!bulkResult.value) return []
  const items = bulkResult.value.items
  if (!q) return items
  return items.filter((i) => displayName(i).toLowerCase().includes(q) || (i.summary_payload?.region || '').toLowerCase().includes(q))
})

// ── Helpers ------------------------------------------------------------------

function targetLabel(col: string) {
  return TARGETS.find((t) => t.value === col)?.label ?? col
}

function formatPct(v?: number | null) {
  if (v == null) return '—'
  return (v * 100).toFixed(1) + '%'
}

function pct(v: number) {
  return (v * 100).toFixed(0) + '%'
}

function formatDt(v?: string | null) {
  if (!v) return '—'
  return new Date(v).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric' })
}

function stateLabel(s: SalesModelStateResponse) {
  if (!s.is_trained) return 'Eğitilmedi'
  if (!s.is_current_dataset) return 'Eski Dataset'
  return 'Hazır'
}

function stateCardClass(s: SalesModelStateResponse) {
  if (!s.is_trained) return 'border-slate-100 bg-slate-50'
  if (!s.is_current_dataset) return 'border-amber-100 bg-amber-50'
  return 'border-emerald-100 bg-emerald-50'
}

function stateBadgeClass(s: SalesModelStateResponse) {
  if (!s.is_trained) return 'bg-slate-100 text-slate-600'
  if (!s.is_current_dataset) return 'bg-amber-100 text-amber-700'
  return 'bg-emerald-100 text-emerald-700'
}

function bandLabel(band: string, col: string): string {
  const b = String(band ?? '').toLowerCase().trim()
  // Binary 0/1 predictions
  if (b === '1' || b === 'true') {
    if (col.includes('Burnout')) return 'Tükenmişlik Var'
    if (col.includes('Resignation')) return 'İstifa Riski'
    if (col.includes('High_Risk')) return 'Yüksek Risk'
    return 'Riskli'
  }
  if (b === '0' || b === 'false') return 'Güvenli'
  // Text labels
  if (b.includes('high') || b.includes('yüksek')) return 'Yüksek Risk'
  if (b.includes('medium') || b.includes('orta')) return 'Orta Risk'
  if (b.includes('low') || b.includes('düşük')) return 'Düşük Risk'
  return band
}

function bandClass(band: string, col: string) {
  const b = String(band ?? '').toLowerCase().trim()
  if (b === '1' || b === 'true' || b.includes('high') || b.includes('yüksek')) {
    return 'bg-rose-50 text-rose-700 border border-rose-200'
  }
  if (b.includes('medium') || b.includes('orta') || b.includes('moderate')) {
    return 'bg-amber-50 text-amber-700 border border-amber-200'
  }
  if (b === '0' || b === 'false' || b.includes('low') || b.includes('düşük')) {
    return 'bg-emerald-50 text-emerald-700 border border-emerald-200'
  }
  return 'bg-slate-100 text-slate-700'
}

function displayName(item: SalesPredictionResponse) {
  return item.summary_payload?.employee_name
    || item.summary_payload?.external_employee_code
    || `Çalışan #${item.employee_id}`
}

function empInitials(item: SalesPredictionResponse) {
  return displayName(item).split(' ').map((w: string) => w[0]).join('').toUpperCase().substring(0, 2)
}

const AVATAR_GRADIENTS = [
  'bg-gradient-to-br from-indigo-500 to-purple-600',
  'bg-gradient-to-br from-emerald-500 to-teal-600',
  'bg-gradient-to-br from-rose-500 to-pink-600',
  'bg-gradient-to-br from-amber-500 to-orange-600',
  'bg-gradient-to-br from-sky-500 to-blue-600',
  'bg-gradient-to-br from-violet-500 to-purple-600',
]

function avatarGradient(idx: number) {
  return AVATAR_GRADIENTS[idx % AVATAR_GRADIENTS.length]
}

function narrativeSrc(src?: string) {
  if (!src || src === 'deterministic') return 'Deterministik Analiz'
  if (src === 'llm' || src === 'gemini') return 'Gemini LLM'
  return src
}

function flatTalkingPoints(narrative: any): string[] {
  const pts: string[] = []
  if (Array.isArray(narrative.talking_points)) {
    for (const tp of narrative.talking_points) {
      if (typeof tp === 'string') pts.push(tp)
      else if (typeof tp === 'object' && tp.point) pts.push(tp.point)
    }
  }
  return pts.slice(0, 5)
}

function selectTeam(name: string) {
  selectedTeamName.value = selectedTeamName.value === name ? null : name
}

// ── Data loading -------------------------------------------------------------

async function loadDatasets() {
  try {
    datasets.value = await analyticsApi.getSalesDatasets()
    if (datasets.value.length) {
      uploadId.value = datasets.value[datasets.value.length - 1].id
      await onDatasetChange()
    }
  } catch (e: any) {
    console.error('Satış dataset listesi alınamadı:', e)
  }
}

async function loadOverview() {
  try {
    overview.value = await analyticsApi.getDepartmentOverview('sales')
  } catch {
    // silently ignore — overview is supplementary
  }
}

async function onDatasetChange() {
  if (!uploadId.value) return
  try {
    const [employees, states] = await Promise.all([
      analyticsApi.getSalesDatasetEmployees(uploadId.value),
      analyticsApi.getSalesModelState(uploadId.value),
    ])
    datasetEmployees.value = employees
    modelStates.value = states
    if (employees.length) employeeId.value = employees[0].employee_id
    predResult.value = null
    bulkResult.value = null
    selectedTeamName.value = null
  } catch (e: any) {
    console.error('Dataset detayları alınamadı:', e)
  }
}

async function trainModel() {
  if (!uploadId.value) return
  error.value = null
  loading.value = 'train'
  try {
    trainResult.value = await analyticsApi.trainSalesModel({
      upload_id: uploadId.value,
      target_column: targetColumn.value,
    })
    modelStates.value = await analyticsApi.getSalesModelState(uploadId.value)
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Model eğitimi başarısız oldu.'
  } finally {
    loading.value = null
  }
}

async function predict() {
  if (!uploadId.value || !employeeId.value) return
  error.value = null
  loading.value = 'predict'
  try {
    predResult.value = await analyticsApi.getLatestSalesPrediction({
      upload_id: uploadId.value,
      employee_id: employeeId.value,
      target_column: targetColumn.value,
    })
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Tahmin alınamadı.'
  } finally {
    loading.value = null
  }
}

async function bulkPredict(withNarrative: boolean) {
  if (!uploadId.value) return
  error.value = null
  loading.value = withNarrative ? 'narrative' : 'bulk'
  try {
    bulkResult.value = await analyticsApi.getBulkSalesPredictions({
      upload_id: uploadId.value,
      target_column: targetColumn.value,
      use_llm_narrative: withNarrative,
    })
    selectedTeamName.value = null
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Toplu analiz başarısız oldu.'
  } finally {
    loading.value = null
  }
}

watch(targetColumn, () => {
  predResult.value = null
  bulkResult.value = null
  selectedTeamName.value = null
})

onMounted(async () => {
  await Promise.all([loadDatasets(), loadOverview()])
})
</script>
