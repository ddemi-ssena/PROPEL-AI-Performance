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
            @click="loadBulkPredictions(activeAnalyticsSection === 'department' || activeAnalyticsSection === 'teams')"
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
            @click="loadBulkPredictions(activeAnalyticsSection === 'department' || activeAnalyticsSection === 'teams')"
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

        <div v-if="teamRiskSummaries.length" v-show="activeAnalyticsSection === 'teams'">
          <div class="mb-4 border-b border-slate-100 pb-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Takim Karsilastirmasi</p>
            <h4 class="mt-1 text-lg font-bold text-slate-900">Takimlar arasi risk, yogunluk ve ana neden karsilastirmasi</h4>
          </div>
          <div class="mb-5 grid grid-cols-1 gap-3">
            <div
              v-for="team in teamRiskSummaries"
              :key="`bar-${team.team}`"
              class="rounded-xl border border-slate-200 bg-slate-50 p-4"
            >
              <div class="flex items-center justify-between gap-3 text-sm">
                <p class="font-bold text-slate-900">{{ team.team }}</p>
                <p class="text-xs font-semibold text-slate-500">
                  {{ team.high }} yuksek / {{ team.medium }} orta / {{ team.total }} kisi
                </p>
              </div>
              <div class="mt-3 h-3 overflow-hidden rounded-full bg-white">
                <div
                  class="h-full rounded-full"
                  :class="team.tone === 'high' ? 'bg-rose-500' : team.tone === 'medium' ? 'bg-amber-500' : 'bg-emerald-500'"
                  :style="{ width: `${teamRiskWidth(team)}%` }"
                ></div>
              </div>
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            <div
              v-for="team in teamRiskSummaries"
              :key="team.team"
              class="rounded-2xl border border-slate-200 bg-slate-50 p-5"
            >
              <div class="flex items-center justify-between gap-3">
                <p class="text-sm font-bold text-slate-900">{{ team.team }}</p>
                <span
                  class="rounded-full px-2.5 py-1 text-xs font-semibold"
                  :class="team.tone === 'high'
                    ? 'bg-rose-50 text-rose-700 border border-rose-200'
                    : team.tone === 'medium'
                      ? 'bg-amber-50 text-amber-700 border border-amber-200'
                      : 'bg-emerald-50 text-emerald-700 border border-emerald-200'"
                >
                  {{ riskToneLabel(team.tone) }}
                </span>
              </div>
              <div class="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
                <div class="rounded-lg bg-white p-2">
                  <p class="font-bold text-slate-900">{{ team.total }}</p>
                  <p class="text-slate-500">Kisi</p>
                </div>
                <div class="rounded-lg bg-white p-2">
                  <p class="font-bold text-rose-700">{{ team.high }}</p>
                  <p class="text-slate-500">Yuksek</p>
                </div>
                <div class="rounded-lg bg-white p-2">
                  <p class="font-bold text-amber-700">{{ team.medium }}</p>
                  <p class="text-slate-500">Orta</p>
                </div>
              </div>
              <p class="mt-4 text-xs font-semibold text-slate-500">Ana neden</p>
              <p class="mt-1 text-sm text-slate-800">{{ team.topReason }}</p>
              <p class="mt-3 text-xs font-semibold text-slate-500">Takim aksiyonu</p>
              <p class="mt-1 text-sm leading-6 text-slate-700">{{ team.action }}</p>
              <div
                v-if="teamNarrative(team.team)"
                class="mt-4 rounded-xl border border-white bg-white p-3"
              >
                <p class="text-xs font-semibold text-violet-600">
                  {{ narrativeSourceLabel(teamNarrative(team.team)?.source) }}
                </p>
                <p class="mt-2 text-sm leading-6 text-slate-700">
                  {{ teamNarrative(team.team)?.manager_summary }}
                </p>
                <ul class="mt-3 space-y-2 text-xs leading-5 text-slate-600">
                  <li
                    v-for="point in aggregateTalkingPoints(teamNarrative(team.team)).slice(0, 2)"
                    :key="point"
                  >
                    - {{ point }}
                  </li>
                </ul>
              </div>
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
import { computed, onMounted, ref, watch } from 'vue'
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

const route = useRoute()
const departmentConfigs = ref<DepartmentAnalyticsConfigResponse[]>([])
const overview = ref<DepartmentAnalyticsOverviewResponse | null>(null)
const selectedDepartment = ref('software')
const selectedTeam = ref('all')
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
type AnalyticsSectionKey = 'model' | 'department' | 'teams' | 'watchlist' | 'technical'
const analyticsSectionKeys: AnalyticsSectionKey[] = ['model', 'department', 'teams', 'watchlist', 'technical']
const activeAnalyticsSection = ref<AnalyticsSectionKey>('model')
const bulkSections: AnalyticsSectionKey[] = ['department', 'teams', 'watchlist', 'technical']

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
      return {
        team,
        total: teamItems.length,
        high,
        medium,
        tone,
        topReason,
        action: buildBulkActions([topReason], team)[0],
      }
    })
    .sort((a, b) => b.high - a.high || b.medium - a.medium || b.total - a.total)
})

const maxTeamRiskScore = computed(() => {
  const scores = teamRiskSummaries.value.map((team) => team.high * 2 + team.medium)
  return Math.max(1, ...scores)
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

async function loadBulkPredictions(useLlmNarrative = false) {
  if (!mlUploadId.value) return
  mlLoading.value = useLlmNarrative ? 'narrative' : 'bulk'
  mlError.value = null
  try {
    bulkPredictionResult.value = await analyticsApi.getBulkSoftwarePredictions({
      upload_id: mlUploadId.value,
      target_column: mlTargetColumn.value,
      use_llm_narrative: useLlmNarrative,
    })
    activeAnalyticsSection.value = 'department'
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
})

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
