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

        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-6 gap-3 w-full xl:max-w-6xl">
          <select
            v-model.number="mlUploadId"
            class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 shadow-sm"
          >
            <option :value="null">Dataset sec</option>
            <option
              v-for="upload in softwareUploads"
              :key="upload.id"
              :value="upload.id"
            >
              #{{ upload.id }} - {{ upload.file_name }}
            </option>
          </select>

          <select
            v-model="mlTargetColumn"
            class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 shadow-sm"
          >
            <option value="performance_band">Performans</option>
            <option value="attrition_risk_band">Ayrilma Riski</option>
          </select>

          <button
            class="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm disabled:cursor-not-allowed disabled:bg-slate-300"
            :disabled="Boolean(mlLoading) || !mlUploadId"
            @click="trainModel"
          >
            {{ mlLoading === 'train' ? 'Egitiliyor...' : 'Model Egit' }}
          </button>

          <select
            v-model.number="mlEmployeeId"
            class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 shadow-sm"
          >
            <option
              v-for="employee in datasetEmployees"
              :key="employee.employee_id"
              :value="employee.employee_id"
            >
              {{ employee.display_label || `${employee.team || 'Takim yok'} / ${employee.role || 'Rol yok'} - Dataset #${employee.employee_id}` }}
            </option>
          </select>

          <button
            class="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm disabled:cursor-not-allowed disabled:text-slate-300"
            :disabled="Boolean(mlLoading) || !mlUploadId || !mlEmployeeId"
            @click="loadPrediction()"
          >
            {{ mlLoading === 'predict' ? 'Hesaplaniyor...' : 'Tahmin Al' }}
          </button>

          <button
            class="rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-2.5 text-sm font-semibold text-indigo-800 shadow-sm disabled:cursor-not-allowed disabled:text-indigo-300"
            :disabled="Boolean(mlLoading) || !mlUploadId"
            @click="loadBulkPredictions()"
          >
            {{ mlLoading === 'bulk' ? 'Taraniyor...' : 'Toplu Tara' }}
          </button>

          <button
            class="rounded-xl border border-violet-200 bg-violet-50 px-4 py-2.5 text-sm font-semibold text-violet-800 shadow-sm disabled:cursor-not-allowed disabled:text-violet-300"
            :disabled="Boolean(mlLoading) || !mlUploadId"
            @click="loadBulkPredictions(true)"
          >
            {{ mlLoading === 'narrative' ? 'Yorumlaniyor...' : 'LLM Yorumla' }}
          </button>
        </div>
      </div>

      <div class="mt-4 flex flex-wrap items-center gap-2 text-xs text-slate-500">
        <span
          v-if="latestSoftwareUpload"
          class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 font-medium text-slate-600"
        >
          Son dataset: #{{ latestSoftwareUpload.id }} - {{ latestSoftwareUpload.file_name }}
        </span>
        <span
          v-if="trainingResult"
          class="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 font-medium text-emerald-700"
        >
          Model hazir: {{ targetLabel(trainingResult.target_column) }}
        </span>
      </div>

      <div class="mt-5 min-w-0 space-y-5">
      <div class="rounded-2xl border border-slate-200 bg-white p-5">
        <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{{ activeSectionMeta.eyebrow }}</p>
            <h3 class="mt-1 text-xl font-bold text-slate-900">{{ activeSectionMeta.title }}</h3>
            <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{{ activeSectionMeta.description }}</p>
          </div>
          <button
            v-if="activeSectionNeedsBulk"
            class="w-fit rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-2.5 text-sm font-semibold text-indigo-800 shadow-sm disabled:cursor-not-allowed disabled:text-indigo-300"
            :disabled="Boolean(mlLoading) || !mlUploadId"
            @click="loadBulkPredictions(activeAnalyticsSection === 'department')"
          >
            {{ mlLoading === 'bulk' || mlLoading === 'narrative' ? 'Hazirlaniyor...' : activeSectionMeta.action }}
          </button>
        </div>
      </div>

      <div v-if="mlUploadId" v-show="activeAnalyticsSection === 'model'" class="rounded-2xl border border-slate-200 bg-slate-50 p-5">
        <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Model Durumu</p>
            <h4 class="mt-1 text-base font-bold text-slate-900">
              {{ selectedTargetState?.target_label || targetLabel(mlTargetColumn) }}
            </h4>
          </div>
          <span
            class="rounded-full px-3 py-1 text-xs font-bold"
            :class="selectedTargetState?.is_trained
              ? selectedTargetState?.is_current_dataset
                ? 'border border-emerald-200 bg-emerald-50 text-emerald-700'
                : 'border border-amber-200 bg-amber-50 text-amber-700'
              : 'border border-rose-200 bg-rose-50 text-rose-700'"
          >
            {{ modelStateLabel(selectedTargetState) }}
          </span>
        </div>

        <div class="mt-4 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
          <div class="rounded-xl border border-slate-200 bg-white p-4">
            <p class="text-xs font-semibold text-slate-500">Son egitim</p>
            <p class="mt-2 text-sm font-bold text-slate-900">{{ formatDateTime(selectedTargetState?.trained_at) }}</p>
          </div>
          <div class="rounded-xl border border-slate-200 bg-white p-4">
            <p class="text-xs font-semibold text-slate-500">Model</p>
            <p class="mt-2 text-sm font-bold text-slate-900">{{ selectedTargetState?.model_name || '-' }}</p>
          </div>
          <div class="rounded-xl border border-slate-200 bg-white p-4">
            <p class="text-xs font-semibold text-slate-500">Weighted F1</p>
            <p class="mt-2 text-sm font-bold text-slate-900">{{ formatPercent(selectedTargetState?.metrics?.weighted_f1) }}</p>
          </div>
          <div class="rounded-xl border border-slate-200 bg-white p-4">
            <p class="text-xs font-semibold text-slate-500">Train/Test</p>
            <p class="mt-2 text-sm font-bold text-slate-900">
              {{ selectedTargetState?.train_count || '-' }} / {{ selectedTargetState?.test_count || '-' }}
            </p>
          </div>
        </div>

        <div class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
          <div
            v-for="state in modelStates"
            :key="state.target_column"
            class="rounded-xl border border-slate-200 bg-white p-4"
          >
            <div class="flex items-center justify-between gap-3">
              <p class="text-sm font-bold text-slate-900">{{ state.target_label }}</p>
              <span
                class="rounded-full px-2.5 py-1 text-xs font-semibold"
                :class="state.is_trained
                  ? state.is_current_dataset
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-amber-50 text-amber-700 border border-amber-200'
                  : 'bg-rose-50 text-rose-700 border border-rose-200'"
              >
                {{ modelStateLabel(state) }}
              </span>
            </div>
            <p class="mt-2 text-xs leading-5 text-slate-500">
              {{ state.is_trained ? `Son egitim: ${formatDateTime(state.trained_at)}` : 'Bu target icin model henuz egitilmedi.' }}
            </p>
          </div>
        </div>
      </div>

      <div v-if="mlError" class="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
        {{ mlError }}
      </div>

      <div
        v-if="bulkSections.includes(activeAnalyticsSection)"
        class="rounded-2xl border border-slate-200 bg-white p-5"
      >
        <div
          v-if="!bulkPredictionResult"
          class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center"
        >
          <p class="text-sm font-semibold text-slate-900">Bu bolum icin once dataset analizi calistirilmali.</p>
          <p class="mt-2 text-sm text-slate-500">Toplu tahmin sonucu olusunca bu sayfa sadece kendi basligina ait icgoruleri gosterir.</p>
          <button
            class="mt-4 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm disabled:cursor-not-allowed disabled:bg-slate-300"
            :disabled="Boolean(mlLoading) || !mlUploadId"
            @click="loadBulkPredictions(activeAnalyticsSection === 'department')"
          >
            Analizi Calistir
          </button>
        </div>

        <template v-else>
        <div v-if="bulkInsight" v-show="activeAnalyticsSection === 'department'" class="mb-4 border-b border-slate-100 pb-4">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Departman Risk Resmi</p>
          <h4 class="mt-1 text-lg font-bold text-slate-900">Software departmaninin bu haftaki genel durumu</h4>
        </div>

        <div v-if="bulkInsight" v-show="activeAnalyticsSection === 'department'" class="grid grid-cols-1 xl:grid-cols-3 gap-4">
          <div
            class="rounded-2xl border p-5"
            :class="bulkInsight.tone === 'high'
              ? 'border-rose-200 bg-rose-50'
              : bulkInsight.tone === 'medium'
                ? 'border-amber-200 bg-amber-50'
                : 'border-emerald-200 bg-emerald-50'"
          >
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Durum</p>
            <p class="mt-3 text-2xl font-bold text-slate-900">{{ bulkInsight.riskLabel }}</p>
            <p class="mt-2 text-sm leading-6 text-slate-700">{{ bulkInsight.statusText }}</p>
          </div>

          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-5">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Neden?</p>
            <ul class="mt-3 space-y-2 text-sm leading-6 text-slate-700">
              <li v-for="reason in bulkInsight.reasons" :key="reason">- {{ reason }}</li>
            </ul>
          </div>

          <div class="rounded-2xl border border-indigo-100 bg-indigo-50 p-5">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-500">Haftalik Yonetici Onerisi</p>
            <ul class="mt-3 space-y-2 text-sm leading-6 text-indigo-950">
              <li v-for="action in bulkInsight.actions" :key="action">- {{ action }}</li>
            </ul>
          </div>

        </div>

        <div
          v-if="bulkPredictionResult.department_narrative"
          v-show="activeAnalyticsSection === 'department'"
          class="mt-5 rounded-2xl border border-violet-100 bg-violet-50/70 p-5"
        >
          <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-violet-500">Departman Yorumu</p>
              <h4 class="mt-1 text-base font-bold text-slate-900">
                {{ bulkPredictionResult.department_narrative.manager_summary }}
              </h4>
            </div>
            <span class="w-fit rounded-full border border-violet-200 bg-white px-3 py-1 text-xs font-semibold text-violet-700">
              {{ narrativeSourceLabel(bulkPredictionResult.department_narrative.source) }}
            </span>
          </div>

          <p class="mt-4 text-sm leading-6 text-slate-700">
            {{ bulkPredictionResult.department_narrative.risk_interpretation }}
          </p>
          <p
            v-if="narrativeFallbackReason(bulkPredictionResult.department_narrative)"
            class="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-800"
          >
            {{ narrativeFallbackReason(bulkPredictionResult.department_narrative) }}
          </p>

          <div class="mt-5 grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div class="rounded-xl border border-white/70 bg-white p-4">
              <p class="text-xs font-semibold text-slate-500">Bu haftaki aksiyonlar</p>
              <div class="mt-3 space-y-3">
                <div
                  v-for="action in aggregateActionPlan(bulkPredictionResult.department_narrative)"
                  :key="action.title"
                  class="border-b border-slate-100 pb-3 last:border-b-0 last:pb-0"
                >
                  <p class="text-sm font-semibold text-slate-900">{{ action.title }}</p>
                  <p class="mt-1 text-xs leading-5 text-slate-600">{{ action.reason }}</p>
                  <p class="mt-1 text-xs font-semibold text-violet-700">
                    {{ action.owner }} / {{ action.timeframe }}
                  </p>
                </div>
              </div>
            </div>

            <div class="rounded-xl border border-white/70 bg-white p-4">
              <p class="text-xs font-semibold text-slate-500">Takim liderleriyle konusulacaklar</p>
              <ul class="mt-3 space-y-2 text-sm leading-6 text-slate-700">
                <li
                  v-for="point in aggregateTalkingPoints(bulkPredictionResult.department_narrative)"
                  :key="point"
                >
                  - {{ point }}
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div v-show="activeAnalyticsSection === 'teams'">
          <div class="mb-5 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <div class="flex flex-wrap items-center gap-2">
                <span class="mr-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Zaman Araligi</span>
                <button
                  v-for="range in teamTimeRanges"
                  :key="range.value"
                  class="rounded-lg px-3 py-2 text-xs font-bold transition"
                  :class="selectedTeamTimeRange === range.value
                    ? 'bg-blue-500 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
                  @click="applyTeamTimeRange(range.value)"
                >
                  {{ range.label }}
                </button>
              </div>

              <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
                <button
                  class="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"
                  @click="showDateRangePanel = !showDateRangePanel"
                >
                  <span aria-hidden="true">&#128197;</span>
                  {{ selectedDateRangeLabel }}
                </button>

                <div class="relative">
                  <button
                    class="inline-flex min-w-[128px] items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
                    @click="showRiskFilterMenu = !showRiskFilterMenu"
                  >
                    Filtre ({{ selectedRiskFilters.length }})
                    <span class="text-slate-400">v</span>
                  </button>
                  <div
                    v-if="showRiskFilterMenu"
                    class="absolute right-0 z-20 mt-2 w-44 rounded-xl border border-slate-200 bg-white p-2 shadow-lg"
                  >
                    <label
                      v-for="filter in riskFilterOptions"
                      :key="filter.value"
                      class="flex cursor-pointer items-center gap-2 rounded-lg px-2 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                    >
                      <input
                        v-model="selectedRiskFilters"
                        type="checkbox"
                        :value="filter.value"
                        class="h-3.5 w-3.5 rounded border-slate-300"
                      />
                      <span class="h-2.5 w-2.5 rounded-full" :class="filter.dotClass"></span>
                      {{ filter.label }}
                    </label>
                  </div>
                </div>

                <button
                  class="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-bold text-slate-600 transition hover:bg-slate-100"
                  @click="resetTeamFilters"
                >
                  <span aria-hidden="true">&#8635;</span>
                  Sifirla
                </button>
              </div>
            </div>

            <div
              v-if="showDateRangePanel"
              class="mt-4 grid grid-cols-1 gap-3 border-t border-slate-100 pt-4 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]"
            >
              <label class="text-xs font-semibold text-slate-600">
                Baslangic
                <input
                  v-model="customDateStart"
                  type="date"
                  class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700"
                />
              </label>
              <label class="text-xs font-semibold text-slate-600">
                Bitis
                <input
                  v-model="customDateEnd"
                  type="date"
                  class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700"
                />
              </label>
              <button
                class="self-end rounded-lg bg-blue-500 px-4 py-2 text-xs font-bold text-white transition hover:bg-blue-600"
                @click="applyCustomDateRange"
              >
                Uygula
              </button>
            </div>

            <div
              v-if="teamFilterLoading"
              class="mt-3 flex items-center gap-2 text-xs font-semibold text-blue-600"
            >
              <span class="h-3 w-3 animate-spin rounded-full border-2 border-blue-200 border-t-blue-600"></span>
              Filtreler uygulanıyor...
            </div>
          </div>

          <div class="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            <article
              v-for="metric in teamKpiCards"
              :key="metric.label"
              class="rounded-xl border border-slate-100 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <div class="flex items-start justify-between gap-4">
                <div>
                  <p class="text-sm font-medium text-slate-500">{{ metric.label }}</p>
                  <p class="mt-3 text-[32px] font-bold leading-none text-slate-950">
                    <span v-if="metric.valueDirection === 'down'">&#8595;</span>
                    <span v-else-if="metric.valueDirection === 'up'">&#8593;</span>
                    {{ metric.value }}
                  </p>
                </div>
                <span
                  class="rounded-full px-2.5 py-1 text-xs font-bold"
                  :class="metric.badgeClass"
                >
                  <span v-if="metric.direction === 'down'">&#8595;</span>
                  <span v-else>&#8593;</span>
                  {{ metric.trend }}
                </span>
              </div>

              <div class="mt-5 flex items-end justify-between gap-4">
                <p class="text-sm font-semibold" :class="metric.trendClass">{{ metric.change }}</p>
                <svg viewBox="0 0 120 36" class="h-9 w-32 shrink-0" aria-hidden="true">
                  <polyline
                    fill="none"
                    stroke="currentColor"
                    stroke-width="3"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    :class="metric.sparkClass"
                    :points="metric.sparkline"
                  />
                </svg>
              </div>
            </article>
          </div>

          <div class="mb-4 border-b border-slate-100 pb-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Takim Karsilastirmasi</p>
            <h4 class="mt-1 text-lg font-bold text-slate-900">Takimlar arasi risk, yogunluk ve ana neden karsilastirmasi</h4>
          </div>
          <div v-if="filteredTeamRiskSummaries.length" class="grid grid-cols-1 gap-5 xl:grid-cols-[260px_minmax(0,1fr)]">
            <aside class="rounded-2xl border border-slate-200 bg-slate-50 p-3">
              <p class="px-2 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Takimlar</p>
              <div class="space-y-2">
                <button
                  v-for="team in filteredTeamRiskSummaries"
                  :key="`team-tab-${team.team}`"
                  class="flex w-full items-center justify-between gap-3 rounded-xl border px-3 py-3 text-left transition"
                  :class="selectedTeamAnalysisName === team.team
                    ? 'border-indigo-200 bg-white text-slate-950 shadow-sm'
                    : 'border-transparent bg-transparent text-slate-600 hover:bg-white'"
                  @click="selectedTeamAnalysisName = team.team"
                >
                  <span>
                    <span class="block text-sm font-bold">{{ team.team }}</span>
                    <span class="mt-0.5 block text-xs">{{ team.high }} yuksek / {{ team.medium }} orta</span>
                  </span>
                  <span
                    class="h-2.5 w-2.5 rounded-full"
                    :class="team.tone === 'high' ? 'bg-rose-500' : team.tone === 'medium' ? 'bg-amber-500' : 'bg-emerald-500'"
                  ></span>
                </button>
              </div>
            </aside>

            <div class="min-w-0 space-y-5">
              <section class="rounded-2xl border border-slate-200 bg-white p-5">
                <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Grafik Yorumu</p>
                    <h5 class="mt-1 text-base font-bold text-slate-900">{{ teamComparisonInsight.title }}</h5>
                    <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{{ teamComparisonInsight.summary }}</p>
                  </div>
                  <span class="w-fit rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
                    {{ filteredTeamRiskSummaries.length }} takim
                  </span>
                </div>

                <div class="mt-5 grid grid-cols-1 gap-3 lg:grid-cols-3">
                  <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
                    <p class="text-xs font-semibold text-slate-500">Kritik takim</p>
                    <p class="mt-2 text-lg font-bold text-slate-900">{{ teamComparisonInsight.criticalTeam }}</p>
                    <p class="mt-1 text-xs leading-5 text-slate-500">{{ teamComparisonInsight.criticalTeamNote }}</p>
                  </div>
                  <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
                    <p class="text-xs font-semibold text-slate-500">Toplam izleme</p>
                    <p class="mt-2 text-lg font-bold text-slate-900">{{ teamComparisonInsight.totalRiskCount }}</p>
                    <p class="mt-1 text-xs leading-5 text-slate-500">Yuksek ve orta riskteki toplam kisi.</p>
                  </div>
                  <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
                    <p class="text-xs font-semibold text-slate-500">Tekrar eden neden</p>
                    <p class="mt-2 text-sm font-bold leading-6 text-slate-900">{{ teamComparisonInsight.repeatedReason }}</p>
                    <p class="mt-1 text-xs leading-5 text-slate-500">Takimlar arasinda en cok tekrar eden ana sinyal.</p>
                  </div>
                </div>

                <div class="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(280px,0.8fr)]">
                  <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
                    <div class="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p class="text-xs font-semibold text-slate-500">Risk yogunlugu</p>
                        <p class="mt-1 text-[11px] leading-5 text-slate-500">
                          Bar 0-100 risk skorunu gosterir; marker secili datasetin son donem takim skorunu isaretler.
                        </p>
                      </div>
                      <div class="flex items-center gap-3 text-xs text-slate-500">
                        <span class="inline-flex items-center gap-1"><span class="h-2 w-2 rounded-full bg-emerald-500"></span>Dusuk</span>
                        <span class="inline-flex items-center gap-1"><span class="h-2 w-2 rounded-full bg-amber-500"></span>Orta</span>
                        <span class="inline-flex items-center gap-1"><span class="h-2 w-2 rounded-full bg-rose-500"></span>Yuksek</span>
                      </div>
                    </div>
                    <div class="mt-4 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-xs leading-5 text-blue-900">
                      Risk skoru ve trend, secili datasetin haftalik satirlarindan uretilen model olasiliklarina dayanir. Trend grafigi son 4 dataset donemini, marker ise son donem takim skorunu gosterir.
                    </div>
                    <div class="mt-5 overflow-x-auto rounded-xl border border-slate-200 bg-white">
                      <div class="sticky top-0 z-10 grid min-w-[760px] grid-cols-[18%_30%_17%_9%_16%_10%] items-center gap-3 bg-[#F9FAFB] px-4 py-4 text-xs font-bold uppercase tracking-wide text-[#6B7280]">
                        <span>Takim Adi</span>
                        <span>Risk Skoru (0-100)</span>
                        <span>Trend (Son 4 Hafta)</span>
                        <span>Kisi</span>
                        <span>Status</span>
                        <span>Izleme</span>
                      </div>
                      <button
                        v-for="(team, index) in filteredTeamRiskSummaries"
                        :key="`risk-bar-${team.team}`"
                        class="grid min-w-[760px] w-full grid-cols-[18%_30%_17%_9%_16%_10%] items-center gap-3 border-b border-[#E5E7EB] px-4 py-5 text-left text-xs transition duration-200 ease-in-out last:border-b-0 hover:bg-[#F3F4F6] hover:shadow-sm"
                        :class="[
                          index % 2 === 0 ? 'bg-white' : 'bg-[#FAFAFA]',
                          selectedTeamAnalysisName === team.team ? 'ring-1 ring-inset ring-indigo-200' : ''
                        ]"
                        :title="`${team.team}: ${teamRiskScore(team)}/100 - ${teamRiskCategory(team)}`"
                        @click="selectedTeamAnalysisName = team.team"
                      >
                        <span class="flex min-w-0 items-center truncate font-bold text-slate-800">
                          <span class="truncate">{{ team.team }}</span>
                        </span>
                        <span class="relative block pt-5">
                          <span
                            class="absolute top-0 -translate-x-1/2 rounded-md border border-slate-300 bg-white px-1.5 py-0.5 text-[10px] font-bold text-slate-800 shadow-sm"
                            :style="{ left: `${teamRiskMarkerPosition(team)}%` }"
                          >
                            {{ teamRiskScore(team) }}
                          </span>
                          <span
                            class="absolute top-[18px] h-0 w-0 -translate-x-1/2 border-x-[5px] border-t-[6px] border-x-transparent border-t-slate-800"
                            :style="{ left: `${teamRiskMarkerPosition(team)}%` }"
                          ></span>
                          <span class="relative flex h-6 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-inner">
                            <span class="h-full flex-1 bg-emerald-500"></span>
                            <span class="h-full w-px bg-slate-200"></span>
                            <span class="h-full flex-1 bg-amber-500"></span>
                            <span class="h-full w-px bg-slate-200"></span>
                            <span class="h-full flex-1 bg-rose-500"></span>
                            <span
                              class="absolute top-1/2 h-7 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-slate-900 bg-white shadow"
                              :style="{ left: `${teamRiskMarkerPosition(team)}%` }"
                            ></span>
                          </span>
                        </span>
                        <span
                          class="flex justify-center"
                          :title="teamTrendTooltip(team.team)"
                        >
                          <svg viewBox="0 0 100 40" class="h-10 w-[100px]" aria-hidden="true">
                            <path
                              :d="teamTrendPath(team.team)"
                              fill="none"
                              stroke="currentColor"
                              stroke-width="2"
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              :class="teamTrendLineClass(team)"
                            />
                          </svg>
                        </span>
                        <span class="text-sm font-bold text-slate-800">
                          {{ team.total }}
                        </span>
                        <span class="flex justify-start">
                          <span
                            class="inline-flex min-w-[104px] items-center justify-center gap-1.5 rounded-2xl border-2 px-2.5 py-1.5 text-[11px] font-semibold"
                            :class="teamRiskBadgeClass(team)"
                          >
                            <span class="h-2 w-2 rounded-full" :class="teamRiskDotClass(team)"></span>
                            {{ teamRiskCategory(team) }}
                          </span>
                        </span>
                        <span class="text-sm font-bold text-slate-800">
                          {{ team.high + team.medium }}
                        </span>
                      </button>
                    </div>
                  </div>

                  <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
                    <p class="text-xs font-semibold text-slate-500">Ana neden dagilimi</p>
                    <div class="mt-4 space-y-3">
                      <div v-for="reason in teamReasonDistribution" :key="reason.name">
                        <div class="flex items-center justify-between gap-3 text-xs">
                          <p class="truncate font-semibold text-slate-700">{{ reason.name }}</p>
                          <p class="text-slate-500">{{ reason.count }} takim</p>
                        </div>
                        <div class="mt-2 h-2 overflow-hidden rounded-full bg-white">
                          <div class="h-full rounded-full bg-indigo-500" :style="{ width: `${reason.width}%` }"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </section>

              <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Trend Karsilastirma</p>
                    <h5 class="mt-1 text-lg font-bold text-slate-900">6 Aylik Performans Trendi</h5>
                    <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
                      Secili datasetten uretilen ay bazli takim risk skorlari. Y ekseni 0-100 risk skorunu, X ekseni dataset donemlerini gosterir.
                    </p>
                  </div>
                  <div class="flex flex-wrap gap-2">
                    <label
                      v-for="team in filteredTeamRiskSummaries"
                      :key="`trend-toggle-${team.team}`"
                      class="inline-flex cursor-pointer items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-white"
                    >
                      <input
                        v-model="visibleTrendTeams[team.team]"
                        type="checkbox"
                        class="h-3.5 w-3.5 rounded border-slate-300"
                      />
                      <span class="h-2.5 w-2.5 rounded-full" :style="{ backgroundColor: teamLineColor(team.team) }"></span>
                      {{ team.team }}
                    </label>
                  </div>
                </div>

                <div class="mt-6 h-[400px] max-w-[800px]">
                  <Line :data="teamTrendChartData" :options="teamTrendChartOptions" />
                </div>
              </section>

              <section v-if="selectedTeamAnalysis" class="rounded-2xl border border-indigo-100 bg-indigo-50/70 p-5">
                <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-500">Secili Takim</p>
                    <h5 class="mt-1 text-xl font-bold text-slate-900">{{ selectedTeamAnalysis.team }}</h5>
                    <p class="mt-2 text-sm leading-6 text-slate-700">
                      {{ selectedTeamAnalysis.total }} kisilik takimda {{ selectedTeamAnalysis.high }} yuksek,
                      {{ selectedTeamAnalysis.medium }} orta risk sinyali var. Ana neden: {{ selectedTeamAnalysis.topReason }}.
                    </p>
                  </div>
                  <span
                    class="w-fit rounded-full px-3 py-1 text-xs font-semibold"
                    :class="selectedTeamAnalysis.tone === 'high'
                      ? 'bg-rose-50 text-rose-700 border border-rose-200'
                      : selectedTeamAnalysis.tone === 'medium'
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-emerald-50 text-emerald-700 border border-emerald-200'"
                  >
                    {{ riskToneLabel(selectedTeamAnalysis.tone) }}
                  </span>
                </div>

                <div class="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-3">
                  <div class="rounded-xl border border-white bg-white p-4">
                    <p class="text-xs font-semibold text-slate-500">Takim riski</p>
                    <p class="mt-2 text-2xl font-bold text-slate-900">{{ selectedTeamAnalysis.high + selectedTeamAnalysis.medium }}</p>
                    <p class="mt-1 text-xs text-slate-500">%{{ teamRiskPercent(selectedTeamAnalysis) }} izleme orani</p>
                    <div class="mt-3 flex h-2 overflow-hidden rounded-full bg-slate-100">
                      <span class="bg-rose-500" :style="{ width: `${teamHighWidth(selectedTeamAnalysis)}%` }"></span>
                      <span class="bg-amber-400" :style="{ width: `${teamMediumWidth(selectedTeamAnalysis)}%` }"></span>
                    </div>
                  </div>
                  <div class="rounded-xl border border-white bg-white p-4">
                    <p class="text-xs font-semibold text-slate-500">Ana neden</p>
                    <p class="mt-2 text-sm font-bold leading-6 text-slate-900">{{ selectedTeamAnalysis.topReason }}</p>
                  </div>
                  <div class="rounded-xl border border-white bg-white p-4">
                    <p class="text-xs font-semibold text-slate-500">Haftalik odak</p>
                    <p class="mt-2 text-sm leading-6 text-slate-700">{{ selectedTeamAnalysis.action }}</p>
                  </div>
                </div>

                <div v-if="selectedTeamNarrative" class="mt-5 rounded-xl border border-white bg-white p-4">
                  <div class="flex items-center justify-between gap-3">
                    <p class="text-xs font-semibold uppercase tracking-[0.18em] text-violet-500">Takim Yorumu</p>
                    <div class="flex flex-wrap items-center justify-end gap-2">
                      <span class="rounded-full border border-violet-100 bg-violet-50 px-3 py-1 text-xs font-semibold text-violet-700">
                        {{ narrativeSourceLabel(selectedTeamNarrative.source) }}
                      </span>
                      <button
                        class="rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-semibold text-indigo-700 disabled:cursor-not-allowed disabled:text-indigo-300"
                        :disabled="Boolean(mlLoading) || !selectedTeamAnalysis"
                        @click="loadBulkPredictions(true, selectedTeamAnalysis?.team)"
                      >
                        {{ mlLoading === 'narrative' ? 'Yorumlaniyor...' : 'Secili takimi LLM ile yorumla' }}
                      </button>
                    </div>
                  </div>
                  <p class="mt-3 text-sm leading-6 text-slate-700">{{ selectedTeamNarrative.manager_summary }}</p>
                  <p
                    v-if="narrativeFallbackReason(selectedTeamNarrative)"
                    class="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-800"
                  >
                    {{ narrativeFallbackReason(selectedTeamNarrative) }}
                  </p>
                  <div class="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
                    <div>
                      <p class="text-xs font-semibold text-slate-500">Haftalik oneriler</p>
                      <div class="mt-3 space-y-3">
                        <div
                          v-for="action in aggregateActionPlan(selectedTeamNarrative)"
                          :key="action.title"
                          class="rounded-lg border border-slate-100 bg-slate-50 p-3"
                        >
                          <p class="text-sm font-semibold text-slate-900">{{ action.title }}</p>
                          <p class="mt-1 text-xs leading-5 text-slate-600">{{ action.reason }}</p>
                        </div>
                      </div>
                    </div>
                    <div>
                      <p class="text-xs font-semibold text-slate-500">Takim lideriyle konusulacaklar</p>
                      <ul class="mt-3 space-y-2 text-sm leading-6 text-slate-700">
                        <li v-for="point in aggregateTalkingPoints(selectedTeamNarrative)" :key="point">- {{ point }}</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div class="mt-5 rounded-xl border border-white bg-white p-4">
                  <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Takimdaki Riskli Kisiler</p>
                  <div class="mt-3 divide-y divide-slate-100">
                    <button
                      v-for="person in selectedTeamPeople"
                      :key="`team-person-${person.employee_id}`"
                      class="flex w-full items-center justify-between gap-3 py-3 text-left"
                      @click="openEmployeeAnalysis(person)"
                    >
                      <span>
                        <span class="block text-sm font-semibold text-slate-900">{{ displayEmployeeName(person) }}</span>
                        <span class="mt-0.5 block text-xs text-slate-500">{{ employeeSubtitle(person) }}</span>
                      </span>
                      <span class="rounded-full px-2.5 py-1 text-xs font-semibold" :class="predictionBandClass(person.predicted_band, person.target_column)">
                        {{ person.predicted_band }}
                      </span>
                    </button>
                    <p v-if="!selectedTeamPeople.length" class="py-4 text-sm leading-6 text-slate-500">
                      Bu takim icin yuksek veya orta riskte kisi gorunmuyor.
                    </p>
                  </div>
                </div>
              </section>
            </div>
          </div>
        </div>

        <div v-if="employeeAnalysisRows.length" v-show="activeAnalyticsSection === 'watchlist'">
          <div class="mb-4 border-b border-slate-100 pb-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Calisan Analizi</p>
            <h4 class="mt-1 text-lg font-bold text-slate-900">Calisan listesi ve bireysel analiz girisi</h4>
          </div>
          <div class="grid grid-cols-1 gap-5 2xl:grid-cols-[minmax(0,1.25fr)_minmax(360px,0.75fr)]">
            <div class="overflow-x-auto rounded-2xl border border-slate-200 bg-white p-4">
              <table class="min-w-full divide-y divide-slate-200 text-sm">
              <thead>
                <tr class="text-left text-slate-500">
                  <th class="pb-3 font-medium">Calisan</th>
                  <th class="pb-3 font-medium">Takim / Pozisyon</th>
                  <th class="pb-3 font-medium">Risk Durumu</th>
                  <th class="pb-3 font-medium">Ana Sinyal</th>
                  <th class="pb-3 font-medium">Haftalik Odak</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr
                  v-for="person in employeeAnalysisRows"
                  :key="person.employee_id"
                  class="cursor-pointer align-top transition hover:bg-indigo-50/50"
                  @click="openEmployeeAnalysis(person)"
                >
                  <td class="py-3 pr-4">
                    <p class="font-semibold text-slate-900">{{ displayEmployeeName(person) }}</p>
                    <p class="text-xs text-slate-500">{{ person.summary_payload?.external_employee_code || `Dataset #${person.employee_id}` }}</p>
                  </td>
                  <td class="py-3 pr-4 text-slate-600">{{ employeeSubtitle(person) }}</td>
                  <td class="py-3 pr-4">
                    <span
                      class="rounded-full px-2.5 py-1 text-xs font-semibold"
                      :class="predictionBandClass(person.predicted_band, person.target_column)"
                    >
                      {{ person.predicted_band }}
                    </span>
                  </td>
                  <td class="py-3 pr-4 text-slate-600">{{ person.top_drivers?.[0]?.metric_name || 'KPI sinyali' }}</td>
                  <td class="py-3 text-slate-600">{{ person.recommended_actions?.[0] || 'KPI kirilimi incelenmeli.' }}</td>
                </tr>
              </tbody>
              </table>
            </div>

            <aside class="rounded-2xl border border-indigo-100 bg-indigo-50 p-5">
              <template v-if="predictionResult">
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-500">Secili Calisan</p>
                    <h4 class="mt-1 text-lg font-bold text-slate-900">{{ displayEmployeeName(predictionResult) }}</h4>
                    <p class="mt-1 text-sm text-slate-600">{{ employeeSubtitle(predictionResult) }}</p>
                  </div>
                  <span
                    class="rounded-full px-2.5 py-1 text-xs font-semibold"
                    :class="predictionBandClass(predictionResult.predicted_band, predictionResult.target_column)"
                  >
                    {{ predictionResult.predicted_band }}
                  </span>
                </div>

                <p class="mt-5 text-sm leading-6 text-slate-800">
                  {{ predictionResult.narrative?.manager_summary || predictionResult.risk_summary }}
                </p>
                <p
                  v-if="narrativeFallbackReason(predictionResult.narrative)"
                  class="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-800"
                >
                  {{ narrativeFallbackReason(predictionResult.narrative) }}
                </p>

                <div
                  v-if="predictionResult.narrative?.risk_interpretation"
                  class="mt-4 rounded-xl border border-indigo-200 bg-white p-4 text-sm leading-6 text-slate-700"
                >
                  {{ predictionResult.narrative.risk_interpretation }}
                </div>

                <p class="mt-5 text-xs font-semibold uppercase tracking-[0.18em] text-indigo-500">Haftalik Manager Onerileri</p>
                <div class="mt-3 space-y-3">
                  <div
                    v-for="action in narrativeActionPlan(predictionResult).slice(0, 3)"
                    :key="`${action.title}-${action.metric_name}`"
                    class="rounded-xl border border-emerald-100 bg-emerald-50 p-3"
                  >
                    <p class="text-sm font-bold leading-5 text-emerald-950">{{ action.title }}</p>
                    <p class="mt-1 text-xs leading-5 text-emerald-900">{{ action.reason }}</p>
                    <p class="mt-2 text-xs font-semibold text-emerald-800">{{ action.owner }} / {{ action.timeframe }}</p>
                  </div>
                </div>
              </template>
              <template v-else>
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-500">Calisan Detayi</p>
                <h4 class="mt-2 text-lg font-bold text-slate-900">Listeden bir calisana tikla</h4>
                <p class="mt-2 text-sm leading-6 text-slate-600">
                  Secilen calisanin takimi, KPI yorumu, LLM ozeti, risk nedeni ve haftalik yonetici onerileri burada acilacak.
                </p>
              </template>
            </aside>
          </div>

          <div class="mt-6 border-t border-slate-100 pt-5">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Oncelikli takip kartlari</p>
            <div class="mt-4 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            <div
              v-for="person in riskyPeople"
              :key="person.employee_id"
              class="rounded-2xl border border-slate-200 bg-white p-5 text-left transition hover:border-indigo-200 hover:bg-indigo-50/40"
              role="button"
              tabindex="0"
              @click="openEmployeeAnalysis(person)"
              @keydown.enter="openEmployeeAnalysis(person)"
            >
              <div class="flex items-center justify-between gap-3">
                <p class="text-sm font-bold text-slate-900">{{ displayEmployeeName(person) }}</p>
                <span
                  class="rounded-full px-2.5 py-1 text-xs font-semibold"
                  :class="predictionBandClass(person.predicted_band, person.target_column)"
                >
                  {{ person.predicted_band }}
                </span>
              </div>
              <p class="mt-2 text-xs text-slate-500">
                {{ employeeSubtitle(person) }}
              </p>
              <p class="mt-4 text-xs font-semibold text-slate-500">Ana sinyal</p>
              <p class="mt-1 text-sm text-slate-800">{{ person.top_drivers?.[0]?.metric_name || 'KPI sinyali' }}</p>
              <p class="mt-3 text-xs leading-5 text-slate-600">
                {{ person.top_drivers?.[0]?.threshold_status || 'Izleme gerekli' }}
                <span v-if="person.top_drivers?.[0]?.trend_signal">
                  / {{ person.top_drivers[0].trend_signal }}
                </span>
              </p>
            </div>
          </div>
          </div>
        </div>

        <details
          v-show="activeAnalyticsSection === 'technical'"
          open
          class="rounded-2xl border border-slate-200 bg-white p-4"
        >
          <summary class="cursor-pointer text-sm font-semibold text-slate-700">
            Teknik detaylari ve kisi bazli tabloyu goster
          </summary>
        <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Toplu Risk Taramasi</p>
            <h4 class="mt-1 text-base font-bold text-slate-900">
              {{ bulkPredictionResult.prediction_count }} calisan icin {{ targetLabel(bulkPredictionResult.target_column) }}
            </h4>
          </div>
          <div class="grid grid-cols-3 gap-2 text-center text-xs">
            <div class="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-rose-700">
              <p class="font-bold text-base">{{ bulkPredictionResult.high_risk_count }}</p>
              <p>Yuksek</p>
            </div>
            <div class="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-amber-700">
              <p class="font-bold text-base">{{ bulkPredictionResult.medium_risk_count }}</p>
              <p>Orta</p>
            </div>
            <div class="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-emerald-700">
              <p class="font-bold text-base">{{ bulkPredictionResult.low_risk_count }}</p>
              <p>Dusuk</p>
            </div>
          </div>
        </div>

        <div class="mt-5 overflow-x-auto">
          <table class="min-w-full divide-y divide-slate-200 text-sm">
            <thead>
              <tr class="text-left text-slate-500">
                <th class="pb-3 font-medium">Calisan</th>
                <th class="pb-3 font-medium">Takim / Rol</th>
                <th class="pb-3 font-medium">Sonuc</th>
                <th class="pb-3 font-medium">Guven</th>
                <th class="pb-3 font-medium">Ana Sinyal</th>
                <th class="pb-3 font-medium">Neden</th>
                <th class="pb-3 font-medium">Aksiyon</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="item in bulkPredictionResult.items"
                :key="item.employee_id"
                class="align-top"
              >
                <td class="py-3 pr-4 font-semibold text-slate-900">
                  {{ displayEmployeeName(item) }}
                  <div class="text-xs text-slate-500">{{ employeeSubtitle(item) }}</div>
                </td>
                <td class="py-3 pr-4 text-slate-600">
                  {{ item.summary_payload?.team || '-' }} / {{ item.summary_payload?.position || item.summary_payload?.role || '-' }}
                </td>
                <td class="py-3 pr-4">
                  <span
                    class="rounded-full px-2.5 py-1 text-xs font-semibold"
                    :class="predictionBandClass(item.predicted_band, item.target_column)"
                  >
                    {{ item.predicted_band }}
                  </span>
                </td>
                <td class="py-3 pr-4 font-semibold text-slate-900">{{ formatPercent(item.confidence) }}</td>
                <td class="py-3 pr-4 text-slate-600">
                  {{ item.top_drivers?.[0]?.metric_name || formatFeatureName(item.top_features?.[0]?.feature) }}
                </td>
                <td class="py-3 pr-4 text-slate-600">
                  <div class="max-w-md leading-5">
                    {{ item.top_drivers?.[0]?.threshold_status || '-' }}
                    <span v-if="item.top_drivers?.[0]?.trend_signal">
                      / {{ item.top_drivers[0].trend_signal }}
                    </span>
                  </div>
                </td>
                <td class="py-3 text-slate-600">
                  {{ item.recommended_actions?.[0] || '-' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        </details>
        </template>
      </div>

      <div
        v-if="false && predictionResult"
        class="grid grid-cols-1 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)] gap-4"
      >
        <div
          v-if="!predictionResult"
          class="xl:col-span-2 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center"
        >
          <p class="text-sm font-semibold text-slate-900">Once Calisan Analizi sayfasindan bir calisan sec.</p>
          <p class="mt-2 text-sm text-slate-500">Calisan adina tikladiginda bireysel KPI yorumu, LLM ozeti ve haftalik oneriler burada acilacak.</p>
          <button
            class="mt-4 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm"
            @click="activeAnalyticsSection = 'watchlist'"
          >
            Calisan Listesine Git
          </button>
        </div>

        <template v-else>
        <div class="rounded-2xl border border-slate-200 bg-white p-5">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Yonetici Karari</p>
              <div class="mt-3 flex flex-wrap items-center gap-2">
                <span
                  class="rounded-full px-3 py-1 text-xs font-bold"
                  :class="predictionBandClass(predictionResult?.predicted_band || '', predictionResult?.target_column || '')"
                >
                  {{ predictionResult?.predicted_band }}
                </span>
                <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
                  Guven {{ formatPercent(predictionResult?.confidence) }}
                </span>
                <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-500">
                  {{ narrativeSourceLabel(predictionResult?.narrative?.source) }}
                </span>
              </div>
            </div>
            <button
              class="rounded-xl border border-indigo-200 bg-white px-3 py-2 text-xs font-semibold text-indigo-700 shadow-sm disabled:cursor-not-allowed disabled:text-indigo-300"
              :disabled="Boolean(mlLoading) || !mlUploadId || !mlEmployeeId"
              @click="loadPrediction(true)"
            >
              {{ mlLoading === 'narrative' ? 'LLM deneniyor...' : 'LLM Ozeti Dene' }}
            </button>
          </div>

          <div class="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Calisan</p>
            <p class="mt-2 text-base font-bold text-slate-900">{{ displayEmployeeName(predictionResult) }}</p>
            <p class="mt-1 text-sm text-slate-600">{{ employeeSubtitle(predictionResult) }}</p>
          </div>

          <p class="mt-5 text-base leading-7 text-slate-800">
            {{ predictionResult?.narrative?.manager_summary || predictionResult?.risk_summary }}
          </p>
          <p
            v-if="narrativeFallbackReason(predictionResult?.narrative)"
            class="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-800"
          >
            {{ narrativeFallbackReason(predictionResult?.narrative) }}
          </p>

          <div
            v-if="predictionResult?.narrative?.risk_interpretation"
            class="mt-4 rounded-xl border border-indigo-100 bg-indigo-50 p-4 text-sm leading-6 text-indigo-950"
          >
            {{ predictionResult?.narrative?.risk_interpretation }}
          </div>

          <div class="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div class="rounded-xl border border-slate-200 bg-slate-50 p-3">
              <p class="font-semibold text-slate-500">Donem</p>
              <p class="mt-1 text-slate-900">{{ formatPeriod(predictionResult?.summary_payload?.period_date) }}</p>
            </div>
            <div class="rounded-xl border border-slate-200 bg-slate-50 p-3">
              <p class="font-semibold text-slate-500">Aksiyon kaynagi</p>
              <p class="mt-1 text-slate-900">{{ predictionResult?.narrative?.action_source || 'KPI Registry + trend kurallari' }}</p>
            </div>
          </div>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-white p-5">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Bu Hafta Ne Yapilmali?</p>
          <div class="mt-4 space-y-3">
            <div
              v-for="action in narrativeActionPlan(predictionResult)"
              :key="`${action.title}-${action.metric_name}`"
              class="rounded-xl border border-emerald-100 bg-emerald-50 p-4"
            >
              <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p class="text-sm font-bold leading-6 text-emerald-950">{{ action.title }}</p>
                  <p class="mt-1 text-xs leading-5 text-emerald-900">{{ action.reason }}</p>
                </div>
                <span class="shrink-0 rounded-full border border-emerald-200 bg-white px-2.5 py-1 text-xs font-semibold text-emerald-800">
                  {{ action.timeframe }}
                </span>
              </div>
              <p class="mt-3 text-xs font-semibold text-emerald-800">
                Sorumlu: {{ action.owner }}
              </p>
            </div>
          </div>
          <p
            v-if="predictionResult?.narrative?.confidence_note"
            class="mt-4 text-xs leading-5 text-slate-500"
          >
            {{ predictionResult?.narrative?.confidence_note }}
          </p>
        </div>

        <details class="xl:col-span-2 rounded-2xl border border-slate-200 bg-slate-50 p-5">
          <summary class="cursor-pointer text-sm font-semibold text-slate-700">
            Teknik detaylari goster
          </summary>
          <p class="mt-4 text-sm leading-6 text-slate-700">{{ predictionResult?.risk_summary }}</p>
          <div class="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-3">
            <div
              v-for="driver in predictionResult?.top_drivers || []"
              :key="driver.feature"
              class="rounded-xl border border-slate-200 bg-white p-4"
            >
              <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div>
                  <p class="text-sm font-semibold text-slate-900">{{ driver.metric_name }}</p>
                  <p class="text-xs text-slate-500">{{ driver.category }} / {{ driver.signal }}</p>
                </div>
                <span class="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-slate-600">
                  {{ Number(driver.importance || 0).toFixed(3) }}
                </span>
              </div>
              <p class="mt-2 text-xs leading-5 text-slate-600">{{ driver.rationale }}</p>
            </div>
          </div>
        </details>
        </template>
      </div>

      <div v-if="false && predictionResult" class="mt-5 grid grid-cols-1 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] gap-4">
        <div class="rounded-2xl border border-slate-200 bg-white p-5">
          <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Yonetici Ozeti</p>
              <p class="mt-3 text-sm leading-6 text-slate-700">
                {{ predictionResult?.narrative?.manager_summary || predictionResult?.risk_summary }}
              </p>
            </div>
            <span class="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-semibold text-slate-500">
              {{ narrativeSourceLabel(predictionResult?.narrative?.source) }}
            </span>
          </div>
          <button
            class="mt-4 rounded-xl border border-indigo-200 bg-white px-3 py-2 text-xs font-semibold text-indigo-700 shadow-sm disabled:cursor-not-allowed disabled:text-indigo-300"
            :disabled="Boolean(mlLoading) || !mlUploadId || !mlEmployeeId"
            @click="loadPrediction(true)"
          >
            {{ mlLoading === 'narrative' ? 'LLM deneniyor...' : 'LLM Ozeti Dene' }}
          </button>

          <div
            v-if="predictionResult?.narrative?.risk_interpretation"
            class="mt-4 rounded-xl border border-indigo-100 bg-indigo-50 p-4 text-sm leading-6 text-indigo-950"
          >
            {{ predictionResult?.narrative?.risk_interpretation }}
          </div>

          <p class="mt-5 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Deterministic Aciklama</p>
          <p class="mt-3 text-sm leading-6 text-slate-700">{{ predictionResult?.risk_summary }}</p>

          <div class="mt-5 space-y-3">
            <div
              v-for="driver in predictionResult?.top_drivers || []"
              :key="driver.feature"
              class="rounded-xl border border-slate-200 bg-slate-50 p-4"
            >
              <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div>
                  <p class="text-sm font-semibold text-slate-900">{{ driver.metric_name }}</p>
                  <p class="text-xs text-slate-500">{{ driver.category }} · {{ driver.signal }}</p>
                </div>
                <span class="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-slate-600">
                  {{ Number(driver.importance || 0).toFixed(3) }}
                </span>
              </div>
              <p class="mt-2 text-xs leading-5 text-slate-600">{{ driver.rationale }}</p>
            </div>
          </div>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-white p-5">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Aksiyon Onerileri</p>
          <div class="mt-4 space-y-3">
            <div
              v-for="action in narrativeActions(predictionResult)"
              :key="action"
              class="rounded-xl border border-emerald-100 bg-emerald-50 p-4 text-sm leading-6 text-emerald-900"
            >
              {{ action }}
            </div>
          </div>
          <p
            v-if="predictionResult?.narrative?.confidence_note"
            class="mt-4 text-xs leading-5 text-slate-500"
          >
            {{ predictionResult?.narrative?.confidence_note }}
          </p>
        </div>
      </div>
    </div>
    </div>

    <div
      v-if="selectedDepartmentConfig && activeAnalyticsSection === 'department'"
      class="grid grid-cols-1 xl:grid-cols-[minmax(0,1.25fr)_360px] gap-6"
    >
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

    <div
      v-if="overview?.team_summaries.length && activeAnalyticsSection === 'watchlist'"
      class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
    >
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

    <div
      v-if="overview && activeAnalyticsSection === 'watchlist'"
      class="grid grid-cols-1 xl:grid-cols-[minmax(0,1.2fr)_360px] gap-6"
    >
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
import {
  CategoryScale,
  Chart as ChartJS,
  type ChartOptions,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from 'chart.js'
import { computed, onMounted, ref, watch } from 'vue'
import { Line } from 'vue-chartjs'
import { useRoute } from 'vue-router'
import {
  analyticsApi,
  type DepartmentAnalyticsConfigResponse,
  type DepartmentAnalyticsOverviewResponse,
  type SoftwareBulkPredictionResponse,
  type SoftwareDatasetEmployeeResponse,
  type SoftwareDatasetResponse,
  type SoftwareModelStateResponse,
  type SoftwareModelTrainResponse,
  type SoftwarePredictionResponse,
} from '@/services/api/analytics.api'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

const route = useRoute()
const departmentConfigs = ref<DepartmentAnalyticsConfigResponse[]>([])
const overview = ref<DepartmentAnalyticsOverviewResponse | null>(null)
const selectedDepartment = ref('software')
const selectedTeam = ref('all')
const selectedTeamAnalysisName = ref('')
const loading = ref(false)
const error = ref<string | null>(null)
const mlUploadId = ref<number | null>(null)
const mlTargetColumn = ref('performance_band')
const mlEmployeeId = ref<number | null>(null)
const mlLoading = ref<'train' | 'predict' | 'bulk' | 'narrative' | null>(null)
const mlError = ref<string | null>(null)
const trainingResult = ref<SoftwareModelTrainResponse | null>(null)
const predictionResult = ref<SoftwarePredictionResponse | null>(null)
const bulkPredictionResult = ref<SoftwareBulkPredictionResponse | null>(null)
const softwareDatasets = ref<SoftwareDatasetResponse[]>([])
const datasetEmployees = ref<SoftwareDatasetEmployeeResponse[]>([])
const modelStates = ref<SoftwareModelStateResponse[]>([])
const visibleTrendTeams = ref<Record<string, boolean>>({})
const selectedTeamTimeRange = ref<'1m' | '3m' | '6m' | '1y' | 'all' | 'custom'>('6m')
const selectedRiskFilters = ref<string[]>(['low', 'medium', 'high'])
const showRiskFilterMenu = ref(false)
const showDateRangePanel = ref(false)
const customDateStart = ref('')
const customDateEnd = ref('')
const teamFilterLoading = ref(false)
type AnalyticsSectionKey = 'model' | 'department' | 'teams' | 'watchlist' | 'technical'
const analyticsSectionKeys: AnalyticsSectionKey[] = ['model', 'department', 'teams', 'watchlist', 'technical']
const activeAnalyticsSection = ref<AnalyticsSectionKey>('model')
const bulkSections: AnalyticsSectionKey[] = ['department', 'teams', 'watchlist', 'technical']
const teamTimeRanges = [
  { label: 'Son 1 Ay', value: '1m' },
  { label: 'Son 3 Ay', value: '3m' },
  { label: 'Son 6 Ay', value: '6m' },
  { label: 'Son 1 Yil', value: '1y' },
  { label: 'Tumu', value: 'all' },
] as const
const riskFilterOptions = [
  { label: 'Dusuk Risk', value: 'low', dotClass: 'bg-emerald-500' },
  { label: 'Orta Risk', value: 'medium', dotClass: 'bg-amber-500' },
  { label: 'Yuksek Risk', value: 'high', dotClass: 'bg-rose-500' },
]

const selectedDepartmentConfig = computed(() =>
  departmentConfigs.value.find((item) => item.key === selectedDepartment.value) || null
)

const softwareUploads = computed(() =>
  softwareDatasets.value
)

const latestSoftwareUpload = computed(() => softwareUploads.value[0] || null)

const selectedTargetState = computed(() =>
  modelStates.value.find((item) => item.target_column === mlTargetColumn.value) || null
)

const sectionMeta: Record<AnalyticsSectionKey, { eyebrow: string; title: string; description: string; action: string }> = {
  model: {
    eyebrow: 'Model Durumu',
    title: 'Modelin hazirligi ve egitim kalitesi',
    description: 'Bu bolum sadece model artifact durumunu, son egitim bilgisini ve teknik egitim metriklerini gosterir.',
    action: 'Modeli Yenile',
  },
  department: {
    eyebrow: 'Departman Analizi',
    title: 'Software departmaninin haftalik risk resmi',
    description: 'Departman seviyesinde toplam risk, tekrar eden KPI nedenleri, LLM yonetici yorumu ve haftalik aksiyon onerileri burada toplanir.',
    action: 'Departmani Yorumla',
  },
  teams: {
    eyebrow: 'Takim Analizi',
    title: 'Takimlar arasi karsilastirma ve liderlik notlari',
    description: 'Backend, Frontend, DevOps ve QA takimlarini risk yogunlugu, ana neden ve takim lideriyle konusulacak basliklara gore karsilastirir.',
    action: 'Takimlari Yorumla',
  },
  watchlist: {
    eyebrow: 'Calisan Analizi',
    title: 'Calisan listesi ve bireysel analiz girisi',
    description: 'Bu bolumde tum calisanlar listelenir. Bir calisan adina tiklayinca detayli bireysel KPI yorumu ve haftalik oneriler acilir.',
    action: 'Calisanlari Tara',
  },
  technical: {
    eyebrow: 'Teknik Detaylar',
    title: 'Model ciktilari ve kisi bazli ham prediction tablosu',
    description: 'Yonetici ekranindan ayrilmasi gereken teknik model ciktisi, confidence ve driver tablosu burada tutulur.',
    action: 'Teknik Ciktiyi Getir',
  },
}

const activeSectionMeta = computed(() => sectionMeta[activeAnalyticsSection.value])

const activeSectionNeedsBulk = computed(() =>
  bulkSections.includes(activeAnalyticsSection.value) && !bulkPredictionResult.value
)

const bulkInsight = computed(() => {
  const result = bulkPredictionResult.value
  if (!result) return null

  const items = result.items || []
  const riskRatio = result.prediction_count ? result.high_risk_count / result.prediction_count : 0
  const tone = result.high_risk_count >= 4 || riskRatio >= 0.25
    ? 'high'
    : result.high_risk_count > 0 || result.medium_risk_count >= 4
      ? 'medium'
      : 'low'
  const riskLabel = tone === 'high' ? 'Yuksek Risk' : tone === 'medium' ? 'Orta Risk' : 'Dusuk Risk'

  const negativeTrendCount = items.filter((item) =>
    String(item.top_drivers?.[0]?.trend_signal || '').toLowerCase().includes('olumsuz')
  ).length
  const trendText = negativeTrendCount > 0
    ? `${negativeTrendCount} kiside negatif trend sinyali var`
    : 'Genel trend kritik dusus gostermiyor'

  const driverCounts = countBy(items, (item) => String(item.top_drivers?.[0]?.metric_name || 'KPI sinyali'))
  const teamCounts = countBy(
    items.filter((item) => predictionRiskTone(item.predicted_band, item.target_column) !== 'low'),
    (item) => String(item.summary_payload?.team || 'Takim bilgisi yok')
  )
  const topDrivers = topEntries(driverCounts, 3)
  const topTeam = topEntries(teamCounts, 1)[0]

  const reasons = [
    ...topDrivers.map(([name, count]) => `${name} ${count} kiside one cikiyor`),
    ...(topTeam ? [`${topTeam[0]} takimi izleme listesinde yogunlasiyor`] : []),
    trendText,
  ].slice(0, 4)

  const actions = buildBulkActions(topDrivers.map(([name]) => name), topTeam?.[0])
  const people = items
    .filter((item) => predictionRiskTone(item.predicted_band, item.target_column) !== 'low')
    .slice(0, 4)

  return {
    tone,
    riskLabel,
    statusText: `${result.high_risk_count} kisi yuksek riskte, ${result.medium_risk_count} kisi izleme seviyesinde. ${trendText}.`,
    reasons,
    actions,
    people,
  }
})

const riskyPeople = computed(() => {
  const items = bulkPredictionResult.value?.items || []
  return items
    .filter((item) => predictionRiskTone(item.predicted_band, item.target_column) !== 'low')
    .slice(0, 8)
})

const employeeAnalysisRows = computed(() => bulkPredictionResult.value?.items || [])

const teamRiskSummaries = computed(() => {
  const items = bulkPredictionResult.value?.items || []
  const analyticsByTeam = new Map(
    (bulkPredictionResult.value?.team_analytics || [])
      .map((item) => [String(item.team), item])
  )
  const grouped = items.reduce<Record<string, SoftwarePredictionResponse[]>>((acc, item) => {
    const team = String(item.summary_payload?.team || 'Takim bilgisi yok')
    if (!acc[team]) acc[team] = []
    acc[team].push(item)
    return acc
  }, {})

  return Object.entries(grouped)
    .map(([team, teamItems]) => {
      const high = teamItems.filter((item) => predictionRiskTone(item.predicted_band, item.target_column) === 'high').length
      const medium = teamItems.filter((item) => predictionRiskTone(item.predicted_band, item.target_column) === 'medium').length
      const topReason = topEntries(
        countBy(teamItems, (item) => String(item.top_drivers?.[0]?.metric_name || 'KPI sinyali')),
        1
      )[0]?.[0] || 'KPI sinyali'
      const tone = high > 0 ? 'high' : medium > 0 ? 'medium' : 'low'
      const analytics = analyticsByTeam.get(team)
      const riskScore = Number(analytics?.risk_score ?? averageRiskScore(teamItems))
      return {
        team,
        total: teamItems.length,
        high,
        medium,
        tone,
        topReason,
        action: buildBulkActions([topReason], team)[0],
        riskScore,
        trendValues: Array.isArray(analytics?.trend_values) ? analytics.trend_values.map((value: unknown) => Number(value)) : [riskScore],
        trendPeriods: Array.isArray(analytics?.trend_periods) ? analytics.trend_periods.map((value: unknown) => String(value)) : [],
        trendBasis: String(analytics?.trend_basis || 'latest_prediction_probability'),
      }
    })
    .sort((a, b) => b.high - a.high || b.medium - a.medium || b.total - a.total)
})

const filteredTeamRiskSummaries = computed(() =>
  teamRiskSummaries.value.filter((team) => selectedRiskFilters.value.includes(teamRiskLevel(team)))
)

const maxTeamRiskScore = computed(() => {
  const scores = filteredTeamRiskSummaries.value.map((team) => team.high * 2 + team.medium)
  return Math.max(1, ...scores)
})

const selectedTeamAnalysis = computed(() => {
  if (!filteredTeamRiskSummaries.value.length) return null
  return filteredTeamRiskSummaries.value.find((team) => team.team === selectedTeamAnalysisName.value)
    || filteredTeamRiskSummaries.value[0]
})

const selectedTeamNarrative = computed(() => {
  if (!selectedTeamAnalysis.value) return null
  return teamNarrative(selectedTeamAnalysis.value.team)
})

const selectedTeamPeople = computed(() => {
  const team = selectedTeamAnalysis.value?.team
  if (!team) return []
  return (bulkPredictionResult.value?.items || [])
    .filter((item) => String(item.summary_payload?.team || 'Takim bilgisi yok') === team)
    .filter((item) => predictionRiskTone(item.predicted_band, item.target_column) !== 'low')
    .slice(0, 6)
})

const teamReasonDistribution = computed(() => {
  const counts = countBy(filteredTeamRiskSummaries.value, (team) => team.topReason)
  const entries = topEntries(counts, 4)
  const max = Math.max(1, ...entries.map(([, count]) => count))
  return entries.map(([name, count]) => ({
    name,
    count,
    width: Math.max(12, Math.round((count / max) * 100)),
  }))
})

const teamComparisonInsight = computed(() => {
  const teams = filteredTeamRiskSummaries.value
  const highest = teams[0]
  const selected = selectedTeamAnalysis.value
  if (!highest || !selected) {
    return {
      title: 'Takim verisi bekleniyor',
      summary: 'Takim analizi calistirildiginda risk yogunlugu ve ana nedenler burada yorumlanir.',
      criticalTeam: '-',
      criticalTeamNote: 'Veri geldikten sonra hesaplanir.',
      totalRiskCount: 0,
      repeatedReason: '-',
    }
  }

  const totalRisk = teams.reduce((sum, team) => sum + team.high + team.medium, 0)
  const repeatedReason = teamReasonDistribution.value[0]?.name || highest.topReason
  const highestRiskCount = highest.high + highest.medium
  return {
    title: `${highest.team} risk yogunlugunda one cikiyor`,
    summary: (
      `${teams.length} takim arasinda toplam ${totalRisk} kisi izleme listesinde. ` +
      `${highest.team} takimi ${highest.high} yuksek ve ${highest.medium} orta risk sinyaliyle ilk sirada; ` +
      `tekrar eden ana neden ${repeatedReason}. Secili ${selected.team} takimi icin odak, ` +
      `${selected.topReason} sinyalinin takim ritmi ve kapasiteyle birlikte okunmasi.`
    ),
    criticalTeam: highest.team,
    criticalTeamNote: `${highestRiskCount}/${highest.total} kisi izleme listesinde, oran %${teamRiskPercent(highest)}.`,
    totalRiskCount: totalRisk,
    repeatedReason,
  }
})

const teamKpiCards = computed(() => [
  {
    label: 'Toplam Takim',
    value: '4 takim',
    trend: '+0%',
    direction: 'up',
    change: 'Son 4 hafta stabil',
    badgeClass: 'bg-blue-50 text-blue-700',
    trendClass: 'text-slate-500',
    sparkClass: 'text-blue-500',
    sparkline: '4,24 40,18 78,18 116,14',
  },
  {
    label: 'Ortalama Risk Skoru',
    value: '88.2/100',
    trend: '+8%',
    direction: 'up',
    change: 'Risk yukseliyor',
    badgeClass: 'bg-rose-50 text-rose-700',
    trendClass: 'text-rose-600',
    sparkClass: 'text-rose-500',
    sparkline: '4,28 40,22 78,15 116,8',
  },
  {
    label: 'Yuksek Riskli Takimlar',
    value: '3 takim',
    trend: '+1',
    direction: 'up',
    change: 'Yakindan izlenmeli',
    badgeClass: 'bg-amber-50 text-amber-700',
    trendClass: 'text-amber-600',
    sparkClass: 'text-amber-500',
    sparkline: '4,26 40,26 78,16 116,12',
  },
  {
    label: 'Bu Ay Trend',
    value: '-5%',
    valueDirection: 'down',
    trend: '-5%',
    direction: 'down',
    change: 'Performans dususu',
    badgeClass: 'bg-rose-50 text-rose-700',
    trendClass: 'text-rose-600',
    sparkClass: 'text-rose-500',
    sparkline: '4,8 40,13 78,20 116,28',
  },
])

const teamTrendChartLabels = computed(() => {
  const labels = Array.from(new Set(
    filteredTeamRiskSummaries.value.flatMap((team) => filterPeriodsByTeamRange(team.trendPeriods || []))
  )).sort()

  if (labels.length) return labels.slice(-6).map((period) => formatMonthLabel(period))
  return ["Ara '24", "Oca '25", "Sub '25", "Mar '25", "Nis '25", "May '25"]
})

const teamTrendChartData = computed(() => {
  const rawPeriods = Array.from(new Set(
    filteredTeamRiskSummaries.value.flatMap((team) => filterPeriodsByTeamRange(team.trendPeriods || []))
  )).sort()
  const fallbackLabels = ["Ara '24", "Oca '25", "Sub '25", "Mar '25", "Nis '25", "May '25"]
  const labels = rawPeriods.length ? rawPeriods.map((period) => formatMonthLabel(period)) : fallbackLabels

  return {
    labels,
    datasets: filteredTeamRiskSummaries.value
      .filter((team) => visibleTrendTeams.value[team.team] !== false)
      .map((team) => {
        const valuesByPeriod = new Map(
          (team.trendPeriods || []).map((period: string, index: number) => [period, team.trendValues?.[index] ?? teamRiskScore(team)])
        )
        const data = rawPeriods.length
          ? rawPeriods.map((period) => Number(valuesByPeriod.get(period) ?? null))
          : normalizeTrendSeries(team.trendValues || [teamRiskScore(team)], labels.length)

        return {
          label: team.team,
          data,
          borderColor: teamLineColor(team.team),
          backgroundColor: teamLineColor(team.team),
          borderWidth: 3,
          pointRadius: 0,
          pointHoverRadius: 5,
          tension: 0.42,
          fill: false,
          spanGaps: true,
        }
      }),
  }
})

const teamTrendChartOptions = computed<ChartOptions<'line'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index' as const,
    intersect: false,
  },
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
      backgroundColor: '#111827',
      borderColor: '#1F2937',
      borderWidth: 1,
      padding: 12,
      cornerRadius: 8,
      callbacks: {
        label: (context: any) => `${context.dataset.label}: ${context.parsed.y}/100`,
      },
    },
  },
  scales: {
    y: {
      min: 0,
      max: 100,
      title: {
        display: true,
        text: 'Risk skoru',
        color: '#6B7280',
        font: { size: 12, weight: 'bold' },
      },
      grid: {
        color: '#E5E7EB',
        borderDash: [5, 5],
      },
      ticks: {
        stepSize: 20,
        color: '#6B7280',
      },
    },
    x: {
      grid: {
        display: false,
      },
      ticks: {
        color: '#6B7280',
      },
    },
  },
}))

const selectedDateRangeLabel = computed(() => {
  if (selectedTeamTimeRange.value !== 'custom') {
    return teamTimeRanges.find((range) => range.value === selectedTeamTimeRange.value)?.label || 'Son 6 Ay'
  }
  if (customDateStart.value && customDateEnd.value) {
    return `${formatPeriod(customDateStart.value)} - ${formatPeriod(customDateEnd.value)}`
  }
  return 'Ozel tarih araligi'
})

function readinessLabel(status: string) {
  if (status === 'live') return 'Canli'
  if (status === 'awaiting_dataset') return 'Veri Bekleniyor'
  return status
}

function targetLabel(value: string) {
  if (value === 'performance_band') return 'Performans'
  if (value === 'attrition_risk_band') return 'Ayrilma Riski'
  return value
}

function formatPeriod(value?: string | null) {
  if (!value) return 'Veri yok'
  return new Date(value).toLocaleDateString('tr-TR', { month: 'long', year: 'numeric' })
}

function formatDateTime(value?: string | null) {
  if (!value) return 'Egitim yok'
  return new Date(value).toLocaleString('tr-TR', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
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

function displayEmployeeName(item: SoftwarePredictionResponse | null) {
  if (!item) return '-'
  return item.summary_payload?.employee_name
    || item.summary_payload?.display_label
    || `Dataset #${item.employee_id}`
}

function employeeSubtitle(item: SoftwarePredictionResponse | null) {
  if (!item) return '-'
  const team = item.summary_payload?.team || 'Takim yok'
  const role = item.summary_payload?.position || item.summary_payload?.role || 'Rol yok'
  const code = item.summary_payload?.external_employee_code
  return code ? `${team} / ${role} / ${code}` : `${team} / ${role}`
}

function narrativeSourceLabel(source?: unknown) {
  if (source === 'gemini') return 'LLM: Gemini'
  if (source === 'ollama') return 'LLM: Ollama'
  return 'Deterministic'
}

function narrativeFallbackReason(narrative?: Record<string, any> | null) {
  if (!narrative?.fallback_used || !narrative.fallback_reason) return ''
  return narrative.fallback_reason
}

function narrativeActions(prediction: SoftwarePredictionResponse | null) {
  if (!prediction) return []
  const actions = prediction.narrative?.next_best_actions
  if (Array.isArray(actions) && actions.length) return actions
  return prediction.recommended_actions
}

function narrativeActionPlan(prediction: SoftwarePredictionResponse | null) {
  if (!prediction) return []
  const plan = prediction.narrative?.action_plan
  if (Array.isArray(plan) && plan.length) {
    return plan.map((item: any, index: number) => ({
      title: item.title || prediction.recommended_actions[index] || 'Ilgili KPI kirilimi incelenmeli.',
      reason: item.reason || 'Bu aksiyon modelin one cikardigi KPI sinyaline gore olusturuldu.',
      owner: item.owner || 'Takim lideri',
      timeframe: item.timeframe || 'Bu hafta',
      metric_name: item.metric_name || index,
    }))
  }

  return narrativeActions(prediction).map((title, index) => ({
    title,
    reason: 'Bu aksiyon KPI Registry aksiyon metni ve modelin one cikardigi sinyallerden turetildi.',
    owner: 'Takim lideri',
    timeframe: 'Bu hafta',
    metric_name: index,
  }))
}

function aggregateActionPlan(narrative?: Record<string, any> | null) {
  const plan = narrative?.action_plan
  if (!Array.isArray(plan)) return []
  return plan.map((item: any, index: number) => ({
    title: item?.title || `Aksiyon ${index + 1}`,
    reason: item?.reason || item?.expected_impact || 'Bu aksiyon toplu KPI/ML sinyallerinden uretildi.',
    owner: item?.owner || 'Departman yoneticisi',
    timeframe: item?.timeframe || 'Bu hafta',
  }))
}

function aggregateTalkingPoints(narrative?: Record<string, any> | null) {
  const points = narrative?.leadership_talking_points
  if (Array.isArray(points) && points.length) return points.map((item) => String(item))
  return ['Risk sinyalini takim ritmi, kapasite ve blokajlarla birlikte degerlendirin.']
}

function teamNarrative(teamName: string) {
  return (bulkPredictionResult.value?.team_narratives || [])
    .find((item) => String(item.team) === teamName) || null
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

function predictionBandClass(band: string, targetColumn: string) {
  if (targetColumn === 'attrition_risk_band') {
    if (band === 'Yuksek') return 'bg-rose-50 text-rose-700 border border-rose-200'
    if (band === 'Orta') return 'bg-amber-50 text-amber-700 border border-amber-200'
    return 'bg-emerald-50 text-emerald-700 border border-emerald-200'
  }

  if (band === 'Riskli') return 'bg-rose-50 text-rose-700 border border-rose-200'
  if (band === 'Stabil') return 'bg-amber-50 text-amber-700 border border-amber-200'
  return 'bg-emerald-50 text-emerald-700 border border-emerald-200'
}

function predictionRiskTone(band: string, targetColumn: string) {
  if (targetColumn === 'attrition_risk_band') {
    if (band === 'Yuksek') return 'high'
    if (band === 'Orta') return 'medium'
    return 'low'
  }

  if (band === 'Riskli') return 'high'
  if (band === 'Stabil') return 'medium'
  return 'low'
}

function riskToneLabel(tone: string) {
  if (tone === 'high') return 'Yuksek'
  if (tone === 'medium') return 'Orta'
  return 'Dusuk'
}

function teamRiskWidth(team: { high: number; medium: number }) {
  const score = team.high * 2 + team.medium
  return Math.max(8, Math.round((score / maxTeamRiskScore.value) * 100))
}

function teamHighWidth(team: { high: number; total: number }) {
  if (!team.total) return 0
  return Math.round((team.high / team.total) * 100)
}

function teamMediumWidth(team: { medium: number; total: number }) {
  if (!team.total) return 0
  return Math.round((team.medium / team.total) * 100)
}

function teamRiskPercent(team: { high: number; medium: number; total: number }) {
  if (!team.total) return 0
  return Math.round(((team.high + team.medium) / team.total) * 100)
}

function teamRiskScore(team: { riskScore?: number; high: number; medium: number; total: number }) {
  if (typeof team.riskScore === 'number' && Number.isFinite(team.riskScore)) {
    return Math.round(team.riskScore)
  }
  if (!team.total) return 0
  return Math.round(((team.high * 1) + (team.medium * 0.55)) / team.total * 100)
}

function teamRiskMarkerPosition(team: { riskScore?: number; high: number; medium: number; total: number }) {
  return Math.min(98, Math.max(2, teamRiskScore(team)))
}

function teamRiskCategory(team: { riskScore?: number; high: number; medium: number; total: number }) {
  const score = teamRiskScore(team)
  if (score >= 67) return 'Yuksek Risk'
  if (score >= 34) return 'Orta Risk'
  return 'Dusuk Risk'
}

function teamRiskLevel(team: { riskScore?: number; high: number; medium: number; total: number }) {
  const score = teamRiskScore(team)
  if (score >= 67) return 'high'
  if (score >= 34) return 'medium'
  return 'low'
}

function teamRiskBadgeClass(team: { riskScore?: number; high: number; medium: number; total: number }) {
  const score = teamRiskScore(team)
  if (score >= 67) return 'border-[#EF4444] bg-[#FEE2E2] text-[#991B1B]'
  if (score >= 34) return 'border-[#F59E0B] bg-[#FEF3C7] text-[#92400E]'
  return 'border-[#10B981] bg-[#D1FAE5] text-[#065F46]'
}

function teamRiskDotClass(team: { riskScore?: number; high: number; medium: number; total: number }) {
  const score = teamRiskScore(team)
  if (score >= 67) return 'bg-[#EF4444]'
  if (score >= 34) return 'bg-[#F59E0B]'
  return 'bg-[#10B981]'
}

function teamTrendValues(teamName: string) {
  const team = teamRiskSummaries.value.find((item) => item.team === teamName)
  const periods = team?.trendPeriods || []
  const allowedPeriods = new Set(filterPeriodsByTeamRange(periods))
  const values = periods.length
    ? (team?.trendValues || []).filter((_, index) => allowedPeriods.has(periods[index]))
    : (team?.trendValues || [])
  return values.length ? values : [team ? teamRiskScore(team) : 0]
}

function teamTrendPath(teamName: string) {
  const values = teamTrendValues(teamName)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const span = Math.max(1, max - min)
  const points = values.map((value, index) => {
    const x = Math.round((index / Math.max(1, values.length - 1)) * 96) + 2
    const y = Math.round(34 - ((value - min) / span) * 28)
    return { x, y: Math.max(4, Math.min(36, y)) }
  })

  return points
    .map((point, index) => {
      if (index === 0) return `M ${point.x} ${point.y}`
      const previous = points[index - 1]
      const controlX = Math.round((previous.x + point.x) / 2)
      return `C ${controlX} ${previous.y}, ${controlX} ${point.y}, ${point.x} ${point.y}`
    })
    .join(' ')
}

function teamTrendTooltip(teamName: string) {
  const team = teamRiskSummaries.value.find((item) => item.team === teamName)
  const periods = team?.trendPeriods || []
  return teamTrendValues(teamName)
    .map((value, index) => {
      const period = periods[index] ? formatPeriod(periods[index]) : `Donem ${index + 1}`
      return `${period}: ${value}`
    })
    .join(', ')
}

function teamTrendLineClass(team: { riskScore?: number; high: number; medium: number; total: number }) {
  const score = teamRiskScore(team)
  if (score >= 67) return 'text-[#EF4444]'
  if (score >= 34) return 'text-[#F59E0B]'
  return 'text-[#10B981]'
}

function teamLineColor(teamName: string) {
  const normalized = teamName.toLowerCase()
  if (normalized.includes('backend')) return '#EF4444'
  if (normalized.includes('frontend')) return '#F59E0B'
  if (normalized.includes('qa')) return '#10B981'
  if (normalized.includes('devops')) return '#3B82F6'
  return '#8B5CF6'
}

function normalizeTrendSeries(values: number[], length: number) {
  if (!values.length) return Array.from({ length }, () => 0)
  if (values.length >= length) return values.slice(-length)
  const first = values[0]
  return [...Array.from({ length: length - values.length }, () => first), ...values]
}

function formatMonthLabel(period: string) {
  const [year, month] = period.split('-').map((part) => Number(part))
  if (!year || !month) return period
  const date = new Date(year, month - 1, 1)
  const label = date.toLocaleDateString('tr-TR', { month: 'short', year: '2-digit' })
  return label.replace('.', '').replace(' ', " '")
}

function teamRangeLimit() {
  if (selectedTeamTimeRange.value === '1m') return 1
  if (selectedTeamTimeRange.value === '3m') return 3
  if (selectedTeamTimeRange.value === '6m') return 6
  if (selectedTeamTimeRange.value === '1y') return 12
  return Number.POSITIVE_INFINITY
}

function filterPeriodsByTeamRange(periods: string[]) {
  const sortedPeriods = [...periods].sort()
  if (selectedTeamTimeRange.value === 'custom') {
    return sortedPeriods.filter((period) => {
      const normalized = period.length === 7 ? `${period}-01` : period
      if (customDateStart.value && normalized < customDateStart.value) return false
      if (customDateEnd.value && normalized > customDateEnd.value) return false
      return true
    })
  }
  return sortedPeriods.slice(-teamRangeLimit())
}

function applyTeamTimeRange(value: '1m' | '3m' | '6m' | '1y' | 'all') {
  selectedTeamTimeRange.value = value
  showDateRangePanel.value = false
  flashTeamFilterLoading()
}

function applyCustomDateRange() {
  selectedTeamTimeRange.value = 'custom'
  showDateRangePanel.value = false
  flashTeamFilterLoading()
}

function resetTeamFilters() {
  selectedTeamTimeRange.value = '6m'
  selectedRiskFilters.value = ['low', 'medium', 'high']
  customDateStart.value = ''
  customDateEnd.value = ''
  showRiskFilterMenu.value = false
  showDateRangePanel.value = false
  flashTeamFilterLoading()
}

function flashTeamFilterLoading() {
  teamFilterLoading.value = true
  window.setTimeout(() => {
    teamFilterLoading.value = false
  }, 250)
}

function employeeRiskScore(item: SoftwarePredictionResponse) {
  if (item.target_column === 'attrition_risk_band') {
    return Math.round(
      ((item.probabilities?.Yuksek || 0) * 100)
      + ((item.probabilities?.Orta || 0) * 55)
      + ((item.probabilities?.Dusuk || 0) * 15)
    )
  }
  return Math.round(
    ((item.probabilities?.Riskli || 0) * 100)
    + ((item.probabilities?.Stabil || 0) * 55)
    + ((item.probabilities?.Yuksek || 0) * 20)
    + ((item.probabilities?.Guclu || 0) * 10)
  )
}

function averageRiskScore(items: SoftwarePredictionResponse[]) {
  if (!items.length) return 0
  return Math.round(items.reduce((sum, item) => sum + employeeRiskScore(item), 0) / items.length)
}

function countBy<T>(items: T[], getKey: (item: T) => string) {
  return items.reduce<Record<string, number>>((acc, item) => {
    const key = getKey(item)
    acc[key] = (acc[key] || 0) + 1
    return acc
  }, {})
}

function topEntries(record: Record<string, number>, limit: number) {
  return Object.entries(record)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
}

function buildBulkActions(driverNames: string[], team?: string) {
  const joinedDrivers = driverNames.join(' ').toLowerCase()
  const actions: string[] = []

  if (team && team !== 'Takim bilgisi yok') {
    actions.push(`${team} takiminin sprint kapasitesi ve gorev dagilimi bu hafta yeniden dengelenmeli.`)
  }

  if (joinedDrivers.includes('motivasyon')) {
    actions.push('Motivasyon dususu gorulen calisanlarla kisa 1:1 gorusmeler planlanmali.')
  }

  if (joinedDrivers.includes('fazla') || joinedDrivers.includes('yuk') || joinedDrivers.includes('toplanti')) {
    actions.push('Yuksek is yuku olan kisiler icin toplantilar ve acil olmayan isler azaltilmali.')
  }

  if (joinedDrivers.includes('bug') || joinedDrivers.includes('review') || joinedDrivers.includes('kalite')) {
    actions.push('Kod kalitesi sinyalleri icin review checklist ve release kalite kapilari gozden gecirilmeli.')
  }

  if (!actions.length) {
    actions.push('Izleme listesindeki kisiler icin KPI kirilimlari takim lideriyle birlikte incelenmeli.')
  }

  return actions.slice(0, 3)
}

function modelStateLabel(state?: SoftwareModelStateResponse | null) {
  if (!state?.is_trained) return 'Model yok'
  if (state.is_current_dataset) return 'Hazir'
  return 'Model var'
}

function syncAnalyticsSectionFromRoute(value: unknown) {
  const section = String(value || '')
  if (analyticsSectionKeys.includes(section as AnalyticsSectionKey)) {
    activeAnalyticsSection.value = section as AnalyticsSectionKey
  }
}

async function loadDepartmentConfigs() {
  departmentConfigs.value = await analyticsApi.getDepartmentConfigs()
  if (!departmentConfigs.value.find((item) => item.key === selectedDepartment.value) && departmentConfigs.value[0]) {
    selectedDepartment.value = departmentConfigs.value[0].key
  }
}

async function loadUploadHistory() {
  try {
    softwareDatasets.value = await analyticsApi.getSoftwareDatasets()
    if (!mlUploadId.value && latestSoftwareUpload.value) {
      mlUploadId.value = latestSoftwareUpload.value.id
    }
  } catch {
    softwareDatasets.value = []
  }
}

async function loadDatasetEmployees() {
  if (!mlUploadId.value) {
    datasetEmployees.value = []
    mlEmployeeId.value = null
    modelStates.value = []
    return
  }

  try {
    const [employees, states] = await Promise.all([
      analyticsApi.getSoftwareDatasetEmployees(mlUploadId.value),
      analyticsApi.getSoftwareModelState(mlUploadId.value),
    ])
    datasetEmployees.value = employees
    modelStates.value = states
    if (!datasetEmployees.value.find((item) => item.employee_id === mlEmployeeId.value)) {
      mlEmployeeId.value = datasetEmployees.value[0]?.employee_id || null
    }
  } catch {
    datasetEmployees.value = []
    mlEmployeeId.value = null
    modelStates.value = []
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
    modelStates.value = await analyticsApi.getSoftwareModelState(mlUploadId.value)
    activeAnalyticsSection.value = 'model'
    predictionResult.value = null
    bulkPredictionResult.value = null
  } catch (err: any) {
    mlError.value = err.response?.data?.detail || 'Model egitimi basarisiz oldu.'
  } finally {
    mlLoading.value = null
  }
}

async function loadPrediction(useLlmNarrative = false) {
  if (!mlUploadId.value || !mlEmployeeId.value) return
  mlLoading.value = useLlmNarrative ? 'narrative' : 'predict'
  mlError.value = null
  try {
    predictionResult.value = await analyticsApi.getLatestSoftwarePrediction({
      upload_id: mlUploadId.value,
      employee_id: mlEmployeeId.value,
      target_column: mlTargetColumn.value,
      use_llm_narrative: useLlmNarrative,
    })
    activeAnalyticsSection.value = 'watchlist'
  } catch (err: any) {
    mlError.value = err.response?.data?.detail || 'Tahmin alinamadi.'
  } finally {
    mlLoading.value = null
  }
}

async function openEmployeeAnalysis(person: SoftwarePredictionResponse) {
  mlEmployeeId.value = person.employee_id
  predictionResult.value = person
  await loadPrediction(true)
}

async function loadBulkPredictions(useLlmNarrative = false, llmTeam?: string) {
  if (!mlUploadId.value) return
  const requestedSection = activeAnalyticsSection.value
  mlLoading.value = useLlmNarrative ? 'narrative' : 'bulk'
  mlError.value = null
  try {
    bulkPredictionResult.value = await analyticsApi.getBulkSoftwarePredictions({
      upload_id: mlUploadId.value,
      target_column: mlTargetColumn.value,
      use_llm_narrative: useLlmNarrative,
      llm_team: llmTeam,
    })
    activeAnalyticsSection.value = bulkSections.includes(requestedSection) ? requestedSection : 'department'
  } catch (err: any) {
    mlError.value = err.response?.data?.detail || 'Toplu tahmin alinamadi.'
  } finally {
    mlLoading.value = null
  }
}

watch(selectedDepartment, async () => {
  selectedTeam.value = 'all'
  trainingResult.value = null
  predictionResult.value = null
  bulkPredictionResult.value = null
  await loadOverview()
})

watch(selectedTeam, async () => {
  await loadOverview()
})

watch(mlTargetColumn, () => {
  trainingResult.value = null
  predictionResult.value = null
  bulkPredictionResult.value = null
  selectedTeamAnalysisName.value = ''
})

watch(filteredTeamRiskSummaries, (teams) => {
  if (!teams.length) {
    selectedTeamAnalysisName.value = ''
    return
  }
  if (!teams.find((team) => team.team === selectedTeamAnalysisName.value)) {
    selectedTeamAnalysisName.value = teams[0].team
  }
  const nextVisible = { ...visibleTrendTeams.value }
  for (const team of teams) {
    if (nextVisible[team.team] === undefined) nextVisible[team.team] = true
  }
  for (const teamName of Object.keys(nextVisible)) {
    if (!teams.find((team) => team.team === teamName)) delete nextVisible[teamName]
  }
  visibleTrendTeams.value = nextVisible
})

watch(selectedRiskFilters, () => {
  flashTeamFilterLoading()
}, { deep: true })

watch(mlUploadId, () => {
  trainingResult.value = null
  predictionResult.value = null
  bulkPredictionResult.value = null
  loadDatasetEmployees()
})

watch(
  () => route.query.section,
  (section) => syncAnalyticsSectionFromRoute(section),
  { immediate: true }
)

onMounted(async () => {
  await loadDepartmentConfigs()
  await loadUploadHistory()
  await loadDatasetEmployees()
  await loadOverview()
})
</script>
