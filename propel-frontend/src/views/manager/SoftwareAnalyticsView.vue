<template>
  <div class="min-h-screen bg-slate-50 pb-12">

    <!-- ══════════════════ HEADER ══════════════════ -->
    <div class="bg-white border-b border-slate-200 px-6 py-5 shadow-sm">
      <div class="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-5 max-w-screen-2xl mx-auto">
        <div class="flex items-start gap-4">
          <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-indigo-600 shadow-sm">
            <svg class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
            </svg>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <span class="inline-flex h-1.5 w-1.5 rounded-full bg-indigo-500 animate-pulse"></span>
              <p class="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-600">Yazılım Departmanı · KPI & ML</p>
            </div>
            <h1 class="mt-0.5 text-xl font-bold text-slate-900">Yazılım Performansı Analizi</h1>
            <p class="mt-0.5 text-xs text-slate-400 max-w-lg">Random Forest / Hist Gradient Boosting / Logistic Regression — performans düşüşü, tükenmişlik, istifa ve yüksek risk tahmini</p>
          </div>
        </div>
        <div class="flex flex-wrap items-end gap-3 shrink-0">
          <div class="flex flex-col gap-1">
            <label class="text-[10px] font-semibold uppercase tracking-wider text-slate-400 ml-0.5">Dataset</label>
            <select
              v-model.number="uploadId"
              class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm min-w-[210px] focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition"
              @change="onDatasetChange"
            >
              <option :value="null">Dataset seçin</option>
              <option v-for="ds in datasets" :key="ds.id" :value="ds.id">#{{ ds.id }} — {{ ds.file_name }}</option>
            </select>
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-[10px] font-semibold uppercase tracking-wider text-slate-400 ml-0.5">Hedef</label>
            <select
              v-model="targetColumn"
              class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm min-w-[155px] focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition"
            >
              <option v-for="t in TARGETS" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-screen-2xl mx-auto px-6 space-y-5 pt-5">

      <!-- ══════════════════ KPI OVERVIEW ══════════════════ -->
      <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3">
        <div v-for="metric in mlOverviewMetrics" :key="metric.key"
          class="bg-white rounded-xl border border-slate-200 px-4 py-4 shadow-sm hover:shadow-md transition-shadow">
          <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">{{ metric.label }}</p>
          <p class="mt-2 text-2xl font-bold" :class="metric.color || 'text-slate-900'">{{ metric.value }}</p>
          <p class="mt-1 text-[11px] text-slate-500 leading-4">{{ metric.hint }}</p>
        </div>
      </div>

      <!-- ══════════════════ MODEL PANEL ══════════════════ -->
      <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">

        <!-- Panel header -->
        <div class="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div class="flex items-center gap-3">
            <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100">
              <svg class="h-4 w-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
              </svg>
            </div>
            <div>
              <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">ML Pipeline</p>
              <p class="text-sm font-bold text-slate-900">RF + HGB <span class="text-slate-400 font-normal">→</span> LR</p>
            </div>
          </div>
          <button
            @click="trainModel"
            :disabled="!!loading || !uploadId"
            class="inline-flex items-center gap-2 rounded-lg bg-indigo-700 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-600 active:scale-95 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400 disabled:shadow-none"
          >
            <svg v-if="loading !== 'train'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            <svg v-else class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            {{ loading === 'train' ? 'Eğitiliyor…' : 'Model Eğit' }}
          </button>
        </div>

        <!-- Status row -->
        <div v-if="trainResult || error" class="px-6 py-2.5 border-b border-slate-100 flex flex-wrap items-center gap-2 bg-slate-50/50">
          <span v-if="trainResult" class="inline-flex items-center gap-1.5 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
            <span class="h-1.5 w-1.5 rounded-full bg-indigo-500"></span>
            Model hazır: {{ targetLabel(trainResult.target_column) }} — F1 {{ formatPct(trainResult.metrics?.weighted_f1) }}
          </span>
          <span v-if="error" class="inline-flex items-center gap-1.5 rounded-full border border-rose-200 bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-700">
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            {{ error }}
          </span>
        </div>

        <!-- Action toolbar -->
        <div class="px-6 py-4 border-b border-slate-100 flex flex-wrap items-center gap-x-4 gap-y-3">
          <!-- Individual section -->
          <div class="flex items-center gap-2">
            <span class="text-[10px] font-semibold uppercase tracking-wider text-slate-300 hidden sm:block">Bireysel</span>
            <select
              v-model.number="employeeId"
              class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm min-w-[190px] focus:border-indigo-400 focus:outline-none focus:ring-1 focus:ring-indigo-200 transition"
            >
              <option :value="null">Çalışan seçin</option>
              <option v-for="e in datasetEmployees" :key="e.employee_id" :value="e.employee_id">
                {{ e.display_label || `${e.team || 'Takım'} / #${e.employee_id}` }}
              </option>
            </select>
            <button
              @click="predict"
              :disabled="!!loading || !uploadId || !employeeId"
              class="inline-flex items-center gap-1.5 rounded-lg border border-indigo-300 bg-indigo-50 px-3.5 py-2 text-sm font-semibold text-indigo-800 shadow-sm transition hover:bg-indigo-100 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <svg v-if="loading !== 'predict'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
              </svg>
              <svg v-else class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
              {{ loading === 'predict' ? 'Hesaplanıyor…' : 'Tahmin Al' }}
            </button>
          </div>

          <div class="hidden lg:block h-8 w-px bg-slate-200"></div>

          <!-- Bulk section -->
          <div class="flex items-center gap-2">
            <span class="text-[10px] font-semibold uppercase tracking-wider text-slate-300 hidden sm:block">Toplu</span>
            <button
              @click="bulkPredict(false)"
              :disabled="!!loading || !uploadId"
              class="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <svg v-if="loading !== 'bulk'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
              </svg>
              <svg v-else class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
              {{ loading === 'bulk' ? 'Taranıyor…' : 'Toplu Tara' }}
            </button>
            <button
              @click="bulkPredict(true)"
              :disabled="!!loading || !uploadId"
              class="inline-flex items-center gap-1.5 rounded-lg border border-violet-200 bg-violet-50 px-3.5 py-2 text-sm font-semibold text-violet-700 shadow-sm transition hover:bg-violet-100 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <svg v-if="loading !== 'narrative'" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
              </svg>
              <svg v-else class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
              {{ loading === 'narrative' ? 'Yorumlanıyor…' : 'LLM Yorumla' }}
            </button>
          </div>
        </div>

        <!-- Model state grid -->
        <div v-if="uploadId && filteredModelStates.length" class="p-4 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
          <div
            v-for="state in filteredModelStates"
            :key="state.target_column"
            class="rounded-xl border p-4 transition-all"
            :class="currentTrainingTarget === state.target_column
              ? 'border-indigo-400 bg-indigo-50 shadow-md ring-2 ring-indigo-200'
              : stateCardClass(state)"
          >
            <div class="flex items-start justify-between gap-2">
              <p class="text-sm font-bold leading-tight"
                :class="state.is_trained && state.is_current_dataset ? 'text-indigo-900' : 'text-slate-800'">
                {{ state.target_label }}
              </p>
              <!-- Eğitiliyor animasyonu -->
              <span v-if="currentTrainingTarget === state.target_column"
                class="shrink-0 inline-flex items-center gap-1 rounded-full bg-indigo-600 px-2 py-0.5 text-[10px] font-semibold text-white">
                <svg class="h-2.5 w-2.5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                </svg>
                Eğitiliyor...
              </span>
              <span v-else class="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold" :class="stateBadgeClass(state)">
                {{ stateLabel(state) }}
              </span>
            </div>
            <p class="mt-1.5 text-[11px]"
              :class="currentTrainingTarget === state.target_column ? 'text-indigo-600 font-medium' : 'text-slate-500'">
              {{ currentTrainingTarget === state.target_column
                ? 'Model şu an eğitiliyor, lütfen bekleyin...'
                : state.is_trained ? `Son eğitim: ${formatDt(state.trained_at)}` : 'Henüz eğitilmedi' }}
            </p>
            <div v-if="state.is_trained && currentTrainingTarget !== state.target_column" class="mt-3 grid grid-cols-2 gap-2">
              <div class="rounded-lg bg-white/70 px-2.5 py-2 text-xs">
                <p class="text-slate-400 text-[10px]">Weighted F1</p>
                <p class="mt-0.5 font-bold text-slate-800">{{ formatPct(state.metrics?.weighted_f1) }}</p>
              </div>
              <div class="rounded-lg bg-white/70 px-2.5 py-2 text-xs">
                <p class="text-slate-400 text-[10px]">Train / Test</p>
                <p class="mt-0.5 font-bold text-slate-800">{{ state.train_count }} / {{ state.test_count }}</p>
              </div>
            </div>
            <!-- Eğitim sırasında animasyonlu progress bar -->
            <div v-if="currentTrainingTarget === state.target_column" class="mt-3 h-1.5 rounded-full bg-indigo-100 overflow-hidden">
              <div class="h-full bg-indigo-500 rounded-full animate-pulse" style="width: 60%"/>
            </div>
          </div>
        </div>
      </div>

      <!-- ══════════════════ INDIVIDUAL PREDICTION ══════════════════ -->
      <div v-if="predResult" class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div class="px-6 py-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">Bireysel Tahmin</p>
            <div class="mt-1.5 flex flex-wrap items-center gap-3">
              <h3 class="text-xl font-bold text-slate-900">{{ displayName(predResult) }}</h3>
              <span class="rounded-full border px-3 py-0.5 text-sm font-semibold" :class="bandClass(predResult.predicted_band, predResult.target_column)">
                {{ bandLabel(predResult.predicted_band, predResult.target_column) }}
              </span>
            </div>
            <p class="mt-1 text-sm text-slate-500">{{ targetLabel(predResult.target_column) }}</p>
          </div>
          <!-- Confidence circle -->
          <div class="flex flex-col items-center gap-1 shrink-0">
            <div class="relative flex h-20 w-20 items-center justify-center">
              <svg class="absolute inset-0 h-full w-full -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="14" fill="none" stroke="#f1f5f9" stroke-width="3"/>
                <circle cx="18" cy="18" r="14" fill="none" stroke="#6366f1" stroke-width="3"
                  stroke-dasharray="87.96"
                  :stroke-dashoffset="87.96 - (predResult.confidence * 87.96)"
                  stroke-linecap="round"/>
              </svg>
              <span class="text-base font-bold text-slate-900">{{ pct(predResult.confidence) }}</span>
            </div>
            <p class="text-[10px] font-medium text-slate-400 uppercase tracking-wide">Güven</p>
          </div>
        </div>

        <!-- Summary -->
        <div class="px-6 py-4 bg-slate-50/60 border-b border-slate-100">
          <p class="text-sm leading-6 text-slate-700">{{ predResult.narrative?.manager_summary || predResult.risk_summary }}</p>
        </div>

        <!-- Drivers + Actions -->
        <div class="p-6 grid grid-cols-1 lg:grid-cols-2 gap-5">
          <div>
            <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400 mb-3">Temel Sürücüler</p>
            <div class="space-y-2">
              <div
                v-for="d in predResult.top_drivers.slice(0, 5)"
                :key="d.metric_name"
                class="flex items-center justify-between gap-3 rounded-lg border border-slate-100 bg-slate-50 px-4 py-2.5 hover:border-slate-200 transition-colors"
              >
                <div class="min-w-0">
                  <p class="text-sm font-semibold text-slate-900 truncate">{{ d.metric_name }}</p>
                  <p class="text-xs text-slate-500 mt-0.5">{{ d.threshold_status }}</p>
                </div>
                <span
                  class="shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold border"
                  :class="d.trend_signal === 'declining'
                    ? 'bg-rose-50 text-rose-700 border-rose-100'
                    : d.trend_signal === 'improving'
                    ? 'bg-indigo-50 text-indigo-700 border-indigo-100'
                    : 'bg-slate-100 text-slate-500 border-slate-200'"
                >
                  {{ d.trend_signal === 'declining' ? 'Trend olumsuzlaşıyor'
                   : d.trend_signal === 'improving' ? 'Trend iyileşiyor'
                   : d.trend_signal || 'Sabit' }}
                </span>
              </div>
            </div>
          </div>
          <div>
            <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-indigo-600 mb-3">Önerilen Aksiyonlar</p>
            <div class="space-y-2">
              <div
                v-for="(a, i) in predResult.recommended_actions"
                :key="a"
                class="flex items-start gap-3 rounded-lg border border-indigo-100 bg-indigo-50/60 px-4 py-2.5"
              >
                <span class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-white text-[10px] font-bold mt-0.5">{{ (i as number) + 1 }}</span>
                <p class="text-sm text-slate-700 leading-5">{{ a }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ══════════════════ BULK RESULTS ══════════════════ -->
      <template v-if="allTargetsResult != null || bulkResult != null">

        <!-- LLM fallback notice: departman narratifi deterministik ise göster -->
        <div
          v-if="bulkResult?.department_narrative?.fallback_used === true"
          class="rounded-xl border border-amber-200 bg-amber-50 px-5 py-3 flex items-start gap-3"
        >
          <svg class="h-5 w-5 text-amber-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <div>
            <p class="text-sm font-semibold text-amber-800">LLM aktif değil — deterministik analiz kullanıldı</p>
            <p class="text-xs text-amber-600 mt-0.5">Gemini API anahtarı <code class="bg-amber-100 px-1 rounded">.env</code> dosyasına eklendiğinde gerçek AI yorumu devreye girer.</p>
          </div>
        </div>

        <!-- Summary cards -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="bg-white rounded-2xl border border-slate-200 border-l-4 border-l-rose-500 p-5 shadow-sm">
            <div class="flex items-center justify-between gap-2">
              <p class="text-xs font-semibold uppercase tracking-[0.15em] text-rose-500">Yüksek Risk</p>
              <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-50">
                <svg class="h-4 w-4 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
              </div>
            </div>
            <p class="mt-3 text-4xl font-bold text-rose-700 tabular-nums">{{ riskCounts.high }}</p>
            <p class="mt-1 text-xs text-slate-500">çalışan izleniyor</p>
          </div>
          <div class="bg-white rounded-2xl border border-slate-200 border-l-4 border-l-amber-400 p-5 shadow-sm">
            <div class="flex items-center justify-between gap-2">
              <p class="text-xs font-semibold uppercase tracking-[0.15em] text-amber-500">Orta Risk</p>
              <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50">
                <svg class="h-4 w-4 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              </div>
            </div>
            <p class="mt-3 text-4xl font-bold text-amber-600 tabular-nums">{{ riskCounts.medium }}</p>
            <p class="mt-1 text-xs text-slate-500">dikkat listesinde</p>
          </div>
          <div class="bg-white rounded-2xl border border-slate-200 border-l-4 border-l-indigo-500 p-5 shadow-sm">
            <div class="flex items-center justify-between gap-2">
              <p class="text-xs font-semibold uppercase tracking-[0.15em] text-indigo-600">Düşük Risk</p>
              <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50">
                <svg class="h-4 w-4 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              </div>
            </div>
            <p class="mt-3 text-4xl font-bold text-indigo-700 tabular-nums">{{ riskCounts.low }}</p>
            <p class="mt-1 text-xs text-slate-500">stabil çalışan</p>
          </div>
          <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
            <div class="flex items-center justify-between gap-2">
              <p class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">Toplam Analiz</p>
              <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100">
                <svg class="h-4 w-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
              </div>
            </div>
            <p class="mt-3 text-4xl font-bold text-slate-900 tabular-nums">{{ riskCounts.total }}</p>
            <p class="mt-1 text-xs text-slate-500">4 hedef bileşik skor</p>
          </div>
        </div>

        <!-- Department narrative -->
        <div v-if="deptNarrative" class="bg-white rounded-2xl border border-violet-200 shadow-sm overflow-hidden">
          <div class="px-6 py-4 border-b border-violet-100 bg-gradient-to-r from-violet-50 to-white flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
            <div class="flex items-center gap-3">
              <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-100">
                <svg class="h-5 w-5 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                </svg>
              </div>
              <div>
                <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-violet-500">Departman Yorumu</p>
                <h4 class="mt-0.5 text-sm font-bold text-slate-900">{{ deptNarrative.manager_summary }}</h4>
              </div>
            </div>
            <span class="w-fit rounded-full border border-violet-200 bg-white px-3 py-1 text-xs font-semibold text-violet-700">
              {{ narrativeSrc(deptNarrative.source) }}
            </span>
          </div>
          <div class="px-6 py-4 border-b border-slate-100">
            <p class="text-sm leading-6 text-slate-700">{{ deptNarrative.risk_interpretation }}</p>
          </div>
          <div v-if="deptNarrative.action_plan?.length" class="p-6 grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div>
              <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400 mb-3">Aksiyon Planı</p>
              <div class="space-y-2.5">
                <div v-for="a in deptNarrative.action_plan.slice(0, 4)" :key="a.title" class="rounded-lg border border-slate-100 bg-slate-50 p-3.5">
                  <p class="text-sm font-semibold text-slate-900">{{ a.title }}</p>
                  <p class="mt-1 text-xs text-slate-600 leading-4">{{ a.reason }}</p>
                  <div class="mt-2 flex flex-wrap items-center gap-1.5">
                    <span class="rounded-full bg-violet-100 text-violet-700 px-2 py-0.5 text-xs font-medium">{{ a.owner }}</span>
                    <span class="text-slate-300 text-xs">·</span>
                    <span class="text-xs text-slate-500">{{ a.timeframe }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div>
              <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400 mb-3">Konuşma Noktaları</p>
              <div class="space-y-2">
                <div
                  v-for="tp in flatTalkingPoints(deptNarrative)"
                  :key="tp"
                  class="flex items-start gap-2.5 rounded-lg border border-slate-100 bg-slate-50 px-4 py-3"
                >
                  <span class="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-400"></span>
                  <p class="text-sm text-slate-700 leading-5">{{ tp }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Team analytics table -->
        <div v-if="teamRows.length" class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div class="px-6 py-4 border-b border-slate-100">
            <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">Takım Analizi</p>
            <h4 class="mt-0.5 text-base font-bold text-slate-900">Yazılım Takımları Risk Özeti
              <span class="ml-2 text-xs font-normal text-slate-400">— Satır seçerek detay görün</span>
            </h4>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-sm">
              <thead>
                <tr class="bg-slate-50 border-b border-slate-100 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                  <th class="px-6 py-3 text-left">Takım</th>
                  <th class="px-6 py-3 text-left">Risk Oranı</th>
                  <th class="px-6 py-3 text-left">Yüksek Risk</th>
                  <th class="px-6 py-3 text-left">Kişi</th>
                  <th class="px-6 py-3 text-left">Durum</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-50">
                <tr
                  v-for="row in teamRows"
                  :key="row.team"
                  @click="selectTeam(row.team)"
                  class="cursor-pointer transition-colors"
                  :class="selectedTeamName === row.team ? 'bg-indigo-50' : 'hover:bg-slate-50/80'"
                >
                  <td class="px-6 py-4 font-semibold text-slate-900">
                    <div class="flex items-center gap-2">
                      <span class="h-2 w-2 rounded-full transition-all" :class="selectedTeamName === row.team ? 'bg-indigo-500' : 'bg-slate-200'"></span>
                      {{ row.team }}
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <div class="flex items-center gap-2.5">
                      <div class="w-24 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          class="h-full rounded-full transition-all"
                          :class="row.avgRisk > 60 ? 'bg-rose-500' : row.avgRisk > 35 ? 'bg-amber-400' : 'bg-indigo-500'"
                          :style="{ width: `${row.avgRisk}%` }"
                        />
                      </div>
                      <span class="text-xs font-bold tabular-nums text-slate-700">{{ row.avgRisk }}%</span>
                    </div>
                  </td>
                  <td class="px-6 py-4 font-bold tabular-nums" :class="row.highCount > 0 ? 'text-rose-600' : 'text-slate-300'">{{ row.highCount }}</td>
                  <td class="px-6 py-4 text-slate-600 tabular-nums">{{ row.total }}</td>
                  <td class="px-6 py-4">
                    <span
                      class="rounded-full border px-2.5 py-1 text-xs font-semibold"
                      :class="row.avgRisk > 60 ? 'bg-rose-50 text-rose-700 border-rose-200' : row.avgRisk > 35 ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-indigo-50 text-indigo-700 border-indigo-200'"
                    >
                      {{ row.avgRisk > 60 ? 'Kritik' : row.avgRisk > 35 ? 'İzleme' : 'Stabil' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Selected team detail -->
        <div v-if="selectedTeamName" class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div class="bg-gradient-to-r from-indigo-700 to-indigo-500 px-6 py-5 flex items-center justify-between gap-4">
            <div>
              <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-indigo-200">Seçili Takım</p>
              <h4 class="mt-0.5 text-xl font-bold text-white">{{ selectedTeamName }}</h4>
              <p class="mt-0.5 text-xs text-indigo-200">{{ selectedTeamPeople.length }} çalışan analizi</p>
            </div>
            <button
              @click="selectedTeamName = null"
              class="rounded-lg border border-white/20 bg-white/10 px-3 py-1.5 text-xs font-semibold text-white hover:bg-white/20 transition"
            >
              Kapat ✕
            </button>
          </div>
          <div v-if="selectedTeamNarrative" class="px-6 py-4 border-b border-slate-100 bg-violet-50/30">
            <p class="text-sm font-semibold text-slate-900">{{ selectedTeamNarrative.manager_summary }}</p>
            <p class="mt-1.5 text-sm text-slate-600 leading-5">{{ selectedTeamNarrative.risk_interpretation }}</p>
          </div>
          <div class="p-6 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            <article
              v-for="(person, idx) in selectedTeamPeople"
              :key="person.employee_id"
              class="rounded-xl border border-slate-100 bg-white p-4 shadow-sm hover:border-indigo-200 hover:shadow-md transition-all"
            >
              <div class="flex items-center gap-3">
                <span
                  class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-white text-xs font-bold"
                  :class="avatarGradient(idx)"
                >{{ empInitials(person) }}</span>
                <div class="min-w-0 flex-1">
                  <p class="font-bold text-slate-900 truncate text-sm">{{ person.employee_name || person.external_employee_code || `#${person.employee_id}` }}</p>
                  <p class="text-xs text-slate-400 truncate mt-0.5">{{ person.role || person.team || 'Yazılım' }}</p>
                </div>
                <!-- Performans Düşüşü badge'i ana gösterge -->
                <span class="shrink-0 rounded-full border px-2 py-0.5 text-xs font-semibold"
                  :class="person.perf_drop?.predicted_band === '1'
                    ? 'bg-rose-50 text-rose-700 border-rose-200'
                    : 'bg-indigo-50 text-indigo-700 border-indigo-200'">
                  {{ person.perf_drop?.predicted_band === '1' ? 'Riskli' : 'Güvenli' }}
                </span>
              </div>
              <!-- 4 hedef: doğru key ile riskPct kullan -->
              <div class="mt-3 grid grid-cols-2 gap-1">
                <div v-for="key in ['perf_drop','burnout','resignation','high_risk']" :key="key"
                  class="flex items-center justify-between rounded px-2 py-1 text-[10px] font-semibold border"
                  :class="riskColor(riskPct((person as any)[key]))">
                  <span>{{ key === 'perf_drop' ? 'Perf.Düşüşü' : key === 'burnout' ? 'Tükenmişlik' : key === 'resignation' ? 'İstifa' : 'Y.Risk' }}</span>
                  <span class="tabular-nums">{{ riskPct((person as any)[key]) }}%</span>
                </div>
              </div>
              <!-- Genel risk -->
              <div class="mt-2 flex items-center justify-between rounded-lg px-3 py-1.5 text-xs font-bold border"
                :class="riskColor(compositeRisk(person))">
                <span>Genel Risk</span>
                <span class="tabular-nums">{{ compositeRisk(person) }}%</span>
              </div>
              <!-- En yüksek riskli hedef -->
              <div class="mt-2 rounded-lg bg-slate-50 border border-slate-100 px-3 py-2 text-xs">
                <span class="text-slate-400">En kritik: </span>
                <span class="font-semibold" :class="riskColor(Math.max(riskPct(person.perf_drop), riskPct(person.burnout), riskPct(person.resignation), riskPct(person.high_risk)))">
                  {{ [['perf_drop','Performans Düşüşü'],['burnout','Tükenmişlik'],['resignation','İstifa Riski'],['high_risk','Yüksek Risk']]
                      .map(([k,n]) => ({ n, p: riskPct((person as any)[k]) }))
                      .sort((a,b) => b.p - a.p)[0]?.n }} ({{ Math.max(riskPct(person.perf_drop), riskPct(person.burnout), riskPct(person.resignation), riskPct(person.high_risk)) }}%)
                </span>
              </div>
            </article>
          </div>
        </div>

        <!-- All employees table -->
        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div class="px-6 py-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">Çalışan Listesi</p>
              <h4 class="mt-0.5 text-base font-bold text-slate-900">
                Tüm Tahminler
                <span class="ml-1.5 text-sm font-normal text-slate-400">· {{ filteredAllTargets.length }} çalışan</span>
              </h4>
            </div>
            <div class="relative">
              <svg class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
              </svg>
              <input
                v-model="tableSearch"
                type="text"
                placeholder="Çalışan ara…"
                class="rounded-lg border border-slate-200 pl-9 pr-4 py-2 text-sm text-slate-700 shadow-sm w-52 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 transition"
              />
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-sm">
              <thead>
                <tr class="bg-slate-50 border-b border-slate-100 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                  <th class="px-6 py-3 text-left">Çalışan</th>
                  <th class="px-4 py-3 text-left">Takım / Rol</th>
                  <th class="px-4 py-3 text-center">
                    <div>Perf. Düşüşü</div>
                    <div class="text-[9px] font-normal text-slate-400 normal-case tracking-normal">Risk Olasılığı</div>
                  </th>
                  <th class="px-4 py-3 text-center">
                    <div>Tükenmişlik</div>
                    <div class="text-[9px] font-normal text-slate-400 normal-case tracking-normal">Risk Olasılığı</div>
                  </th>
                  <th class="px-4 py-3 text-center">
                    <div>İstifa Riski</div>
                    <div class="text-[9px] font-normal text-slate-400 normal-case tracking-normal">Risk Olasılığı</div>
                  </th>
                  <th class="px-4 py-3 text-center">
                    <div>Yüksek Risk</div>
                    <div class="text-[9px] font-normal text-slate-400 normal-case tracking-normal">Risk Olasılığı</div>
                  </th>
                  <th class="px-4 py-3 text-center">
                    <div>Genel Risk</div>
                    <div class="text-[9px] font-normal text-slate-400 normal-case tracking-normal">Bileşik Skor</div>
                  </th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-50">
                <tr
                  v-for="emp in filteredAllTargets"
                  :key="emp.employee_id"
                  class="hover:bg-slate-50/70 transition-colors"
                >
                  <!-- Çalışan -->
                  <td class="px-6 py-3 whitespace-nowrap">
                    <p class="font-semibold text-slate-900 text-sm">{{ emp.employee_name || emp.external_employee_code || `#${emp.employee_id}` }}</p>
                    <p class="text-[10px] text-slate-400 mt-0.5">{{ emp.external_employee_code }}</p>
                  </td>
                  <!-- Takım / Rol -->
                  <td class="px-4 py-3 text-slate-500 whitespace-nowrap">
                    <span class="text-xs">{{ emp.team || '—' }}</span>
                    <span v-if="emp.role" class="ml-1 text-[10px] text-slate-400">· {{ emp.role }}</span>
                  </td>
                  <!-- 4 Hedef: Risk Olasılığı — band=1 → confidence, band=0 → 1-confidence -->
                  <td v-for="field in ['perf_drop', 'burnout', 'resignation', 'high_risk']" :key="field" class="px-4 py-3 text-center">
                    <template v-if="(emp as any)[field]">
                      <div class="flex flex-col items-center gap-1">
                        <span
                          class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-bold tabular-nums"
                          :class="riskColor(riskPct((emp as any)[field]))"
                        >
                          {{ riskPct((emp as any)[field]) }}%
                        </span>
                        <div class="w-14 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            class="h-full rounded-full transition-all"
                            :class="riskBar(riskPct((emp as any)[field]))"
                            :style="{ width: riskPct((emp as any)[field]) + '%' }"
                          />
                        </div>
                      </div>
                    </template>
                    <span v-else class="text-slate-300 text-xs">—</span>
                  </td>
                  <!-- Bileşik Risk: 4 hedefin eşit ağırlıklı ortalaması -->
                  <td class="px-4 py-3 text-center">
                    <div class="flex flex-col items-center gap-1">
                      <span
                        class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-bold tabular-nums"
                        :class="riskColor(compositeRisk(emp))"
                      >
                        {{ compositeRisk(emp) }}%
                      </span>
                      <div class="w-14 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          class="h-full rounded-full transition-all"
                          :class="riskBar(compositeRisk(emp))"
                          :style="{ width: compositeRisk(emp) + '%' }"
                        />
                      </div>
                    </div>
                  </td>
                </tr>
                <tr v-if="filteredAllTargets.length === 0 && allTargetsResult">
                  <td colspan="6" class="px-6 py-8 text-center text-slate-400 text-sm">Sonuç bulunamadı.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>

      <!-- ══════════════════ EMPTY STATE ══════════════════ -->
      <div
        v-if="!allTargetsResult && !bulkResult && !predResult && !loading"
        class="rounded-2xl border-2 border-dashed border-slate-200 bg-white p-16 text-center"
      >
        <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-50">
          <svg class="h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
          </svg>
        </div>
        <h4 class="mt-5 text-lg font-bold text-slate-900">Yazılım ML Analizine Hoş Geldiniz</h4>
        <p class="mt-2 text-sm text-slate-500 max-w-sm mx-auto leading-6">
          Dataset ve hedef değişkeni seçin, ardından <strong class="text-slate-700">Toplu Tara</strong> ile tüm yazılım ekibinin risk profilini tek tıkla çıkarın.
        </p>
        <div class="mt-6 flex flex-wrap justify-center gap-3 text-xs text-slate-400">
          <span class="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5">
            <span class="h-1.5 w-1.5 rounded-full bg-rose-400"></span> Tükenmişlik tespiti
          </span>
          <span class="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5">
            <span class="h-1.5 w-1.5 rounded-full bg-amber-400"></span> Performans düşüşü
          </span>
          <span class="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5">
            <span class="h-1.5 w-1.5 rounded-full bg-violet-400"></span> İstifa riski
          </span>
          <span class="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5">
            <span class="h-1.5 w-1.5 rounded-full bg-indigo-400"></span> Yüksek risk skoru
          </span>
        </div>
      </div>

    </div>

    <!-- ══════════════════ LOADING OVERLAY ══════════════════ -->
    <div v-if="loading" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/25 backdrop-blur-sm">
      <div class="rounded-2xl bg-white p-8 shadow-2xl border border-slate-200 text-center w-full max-w-xs mx-4">
        <div class="mx-auto h-12 w-12 rounded-full border-4 border-slate-100 border-t-indigo-600 animate-spin"/>
        <p class="mt-5 text-base font-bold text-slate-900">
          {{ loading === 'train' ? 'Model eğitiliyor…'
           : loading === 'predict' ? 'Tahmin hesaplanıyor…'
           : loading === 'narrative' ? 'AI yorumu oluşturuluyor…'
           : 'Toplu analiz çalışıyor…' }}
        </p>
        <p class="mt-1.5 text-sm text-slate-400">Bu işlem birkaç saniye sürebilir.</p>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  analyticsApi,
  type SalesAllTargetsBulkResponse,
  type SalesEmployeeAllTargets,
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
const currentTrainingTarget = ref<string | null>(null)

// Sadece yeni 4 binary hedef — eski performance_band/attrition_risk_band gösterme
const SW_SHOW_TARGETS = new Set(['Performance_Drop_Target','Burnout_Target','Resignation_Target','High_Risk_Target'])
const filteredModelStates = computed(() =>
  modelStates.value.filter((s: any) => SW_SHOW_TARGETS.has(s.target_column))
)  // hangi hedef şu an eğitiliyor
const trainResult = ref<SalesModelTrainResponse | null>(null)
const predResult = ref<SalesPredictionResponse | null>(null)
const bulkResult = ref<SalesBulkPredictionResponse | null>(null)
const allTargetsResult = ref<SalesAllTargetsBulkResponse | null>(null)
const overview = ref<DepartmentAnalyticsOverviewResponse | null>(null)
const loading = ref<string | null>(null)
const error = ref<string | null>(null)
const tableSearch = ref('')
const selectedTeamName = ref<string | null>(null)

// ── Computed -----------------------------------------------------------------

// ML sonuçlarından üst KPI kartları
const mlOverviewMetrics = computed(() => {
  const emps = allTargetsResult.value?.employees ?? []
  const modelState = modelStates.value?.some((s: any) => s.is_trained || (s.metrics?.weighted_f1 ?? 0) > 0)

  if (emps.length === 0) {
    // Toplu Tara öncesi: overview verisi + ML hazırlık durumu (satışla aynı mantık)
    const base = (overview.value?.metrics ?? []).map((m: any) => ({ ...m, color: '' }))
    // readiness kartını ML durumuna göre güncelle
    return base.map((m: any) => {
      if (m.key === 'readiness') {
        return {
          ...m,
          value: modelState ? 'Aktif' : (m.value || 'Eğitim Gerekli'),
          color: modelState ? 'text-indigo-700' : 'text-amber-600',
        }
      }
      return m
    })
  }

  // Toplu Tara sonrası: ML verisi
  const highRisk = emps.filter((e: SalesEmployeeAllTargets) => compositeRisk(e) >= 50).length
  const medRisk  = emps.filter((e: SalesEmployeeAllTargets) => compositeRisk(e) >= 25 && compositeRisk(e) < 50).length
  const avgRisk  = Math.round(emps.reduce((s: number, e: SalesEmployeeAllTargets) => s + compositeRisk(e), 0) / emps.length)

  return [
    { key: 'scope',     label: 'Kapsamdaki Çalışan', value: emps.length,
      hint: 'Seçili datasetteki toplam çalışan sayısı.', color: 'text-slate-900' },
    { key: 'avg_risk',  label: 'Ort. Genel Risk',     value: `${avgRisk}%`,
      hint: '4 hedefin bileşik risk ortalaması (ML).',
      color: avgRisk >= 50 ? 'text-rose-700' : avgRisk >= 25 ? 'text-amber-600' : 'text-indigo-700' },
    { key: 'watchlist', label: 'Yüksek Risk',          value: highRisk,
      hint: 'Genel Risk ≥ %50 olan çalışan sayısı.',
      color: highRisk > 0 ? 'text-rose-700' : 'text-slate-900' },
    { key: 'monitoring',label: 'İzleme Gereken',       value: highRisk + medRisk,
      hint: 'Genel Risk ≥ %25 olan çalışan (yüksek + orta risk).',
      color: (highRisk + medRisk) > 0 ? 'text-amber-600' : 'text-slate-900' },
    { key: 'readiness', label: 'ML Hazırlık Durumu',   value: 'Aktif',
      hint: 'RF + HGB → LR pipeline modeli aktif.', color: 'text-indigo-700' },
  ]
})

// Genel Risk bileşik skoruna göre risk sayıları (≥50 yüksek, 25-49 orta, <25 düşük)
const riskCounts = computed(() => {
  const emps = allTargetsResult.value?.employees ?? []
  const high   = emps.filter((e: SalesEmployeeAllTargets) => compositeRisk(e) >= 50).length
  const medium = emps.filter((e: SalesEmployeeAllTargets) => compositeRisk(e) >= 25 && compositeRisk(e) < 50).length
  const low    = emps.filter((e: SalesEmployeeAllTargets) => compositeRisk(e) < 25).length
  return { high, medium, low, total: emps.length }
})

// Sadece LLM Yorumla'dan gelen bulkResult narratifi (Toplu Tara'da gösterme)
const deptNarrative = computed(() =>
  bulkResult.value?.department_narrative ?? null
)

const teamRows = computed(() => {
  const employees = allTargetsResult.value?.employees
  if (!employees?.length) return []

  // Takım bazında grupla
  const teamMap = new Map<string, SalesEmployeeAllTargets[]>()
  for (const emp of employees) {
    const team = emp.team || 'Genel'
    const bucket = teamMap.get(team) ?? []
    bucket.push(emp)
    teamMap.set(team, bucket)
  }

  return Array.from(teamMap.entries())
    .map(([team, emps]) => {
      const risks = emps.map(e => compositeRisk(e))
      const avgRisk = Math.round(risks.reduce((s, v) => s + v, 0) / risks.length)
      const highCount = emps.filter(e => compositeRisk(e) >= 50).length
      return { team, avgRisk, highCount, total: emps.length }
    })
    .sort((a, b) => b.avgRisk - a.avgRisk)
})

const selectedTeamPeople = computed((): SalesEmployeeAllTargets[] => {
  if (!selectedTeamName.value || !allTargetsResult.value) return []
  return allTargetsResult.value.employees.filter(
    (e: SalesEmployeeAllTargets) => (e.team || 'Genel') === selectedTeamName.value
  )
})

const selectedTeamNarrative = computed(() => {
  if (!selectedTeamName.value || !bulkResult.value) return null
  return bulkResult.value.team_narratives.find((n: any) => n.team === selectedTeamName.value) || null
})

const filteredAllTargets = computed((): SalesEmployeeAllTargets[] => {
  const q = tableSearch.value.trim().toLowerCase()
  if (!allTargetsResult.value) return []
  const employees = allTargetsResult.value.employees
  if (!q) return employees
  return employees.filter((e: SalesEmployeeAllTargets) =>
    (e.employee_name || '').toLowerCase().includes(q) ||
    (e.team || '').toLowerCase().includes(q) ||
    (e.role || '').toLowerCase().includes(q)
  )
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
  if (!s.is_trained) return 'border-slate-200 bg-white'
  if (!s.is_current_dataset) return 'border-amber-200 bg-amber-50'
  return 'border-indigo-300 bg-indigo-100'
}

function stateBadgeClass(s: SalesModelStateResponse) {
  if (!s.is_trained) return 'bg-slate-100 text-slate-400'
  if (!s.is_current_dataset) return 'bg-amber-100 text-amber-700'
  return 'bg-indigo-600 text-white'
}

function bandLabel(band: string, _col?: string): string {
  const b = String(band ?? '').toLowerCase().trim()
  // Binary 0/1 predictions
  if (b === '1' || b === 'true') {
    if ((_col ?? '').includes('Burnout')) return 'Tükenmişlik Var'
    if ((_col ?? '').includes('Resignation')) return 'İstifa Riski'
    if ((_col ?? '').includes('High_Risk')) return 'Yüksek Risk'
    return 'Riskli'
  }
  if (b === '0' || b === 'false') return 'Güvenli'
  // Text labels
  if (b.includes('high') || b.includes('yüksek')) return 'Yüksek Risk'
  if (b.includes('medium') || b.includes('orta')) return 'Orta Risk'
  if (b.includes('low') || b.includes('düşük')) return 'Düşük Risk'
  return band
}

function bandClass(band: string, _col?: string) {
  const b = String(band ?? '').toLowerCase().trim()
  if (b === '1' || b === 'true' || b.includes('high') || b.includes('yüksek')) {
    return 'bg-rose-50 text-rose-700 border-rose-200'
  }
  if (b.includes('medium') || b.includes('orta') || b.includes('moderate')) {
    return 'bg-amber-50 text-amber-700 border-amber-200'
  }
  if (b === '0' || b === 'false' || b.includes('low') || b.includes('düşük')) {
    return 'bg-indigo-50 text-indigo-700 border-indigo-200'
  }
  return 'bg-slate-100 text-slate-700 border-slate-200'
}

function displayName(item: SalesPredictionResponse | SalesEmployeeAllTargets) {
  if ('summary_payload' in item) {
    return item.summary_payload?.employee_name
      || item.summary_payload?.external_employee_code
      || `Çalışan #${item.employee_id}`
  }
  return item.employee_name || item.external_employee_code || `Çalışan #${item.employee_id}`
}

function empInitials(item: SalesPredictionResponse | SalesEmployeeAllTargets) {
  return displayName(item).split(' ').map((w: string) => w[0]).join('').toUpperCase().substring(0, 2)
}

const AVATAR_GRADIENTS = [
  'bg-gradient-to-br from-indigo-500 to-purple-600',
  'bg-gradient-to-br from-blue-500 to-indigo-600',
  'bg-gradient-to-br from-rose-500 to-pink-600',
  'bg-gradient-to-br from-amber-500 to-orange-600',
  'bg-gradient-to-br from-sky-500 to-blue-600',
  'bg-gradient-to-br from-violet-500 to-purple-600',
]

/** Risk olasılığı 0-100 arası tam sayı döndürür.
 *  band=1 → modelin risk tahmini (confidence)
 *  band=0 → modelin güvenli tahminine rağmen kalan marjinal risk (1-confidence)
 */
function riskPct(t: { predicted_band: string; confidence: number } | null | undefined): number {
  if (!t) return 0
  return Math.round(t.predicted_band === '1' ? t.confidence * 100 : (1 - t.confidence) * 100)
}

/** ≥50 kırmızı | 25-50 sarı | <25 mavi — badge arka planı */
function riskColor(pct: number): string {
  if (pct >= 50) return 'bg-rose-100 text-rose-800'
  if (pct >= 25) return 'bg-amber-100 text-amber-800'
  return 'bg-indigo-100 text-indigo-800'
}

/** ≥50 kırmızı | 25-50 sarı | <25 mavi — progress bar rengi */
function riskBar(pct: number): string {
  if (pct >= 50) return 'bg-rose-500'
  if (pct >= 25) return 'bg-amber-400'
  return 'bg-indigo-500'
}

/** 4 hedefin eşit ağırlıklı bileşik risk skoru (her biri %25) */
function compositeRisk(emp: SalesEmployeeAllTargets): number {
  const fields = ['perf_drop', 'burnout', 'resignation', 'high_risk'] as const
  let total = 0
  let count = 0
  for (const key of fields) {
    const t = (emp as any)[key]
    if (!t) continue
    total += riskPct(t)
    count++
  }
  return count > 0 ? Math.round(total / count) : 0
}

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
    datasets.value = await analyticsApi.getSoftwareDatasets()
    if (datasets.value.length) {
      uploadId.value = datasets.value[0].id
      await onDatasetChange()
    }
  } catch (e: any) {
    console.error('Yazılım dataset listesi alınamadı:', e)
  }
}

async function loadOverview() {
  try {
    overview.value = await analyticsApi.getDepartmentOverview('software')
  } catch {
    // silently ignore — overview is supplementary
  }
}

async function onDatasetChange() {
  if (!uploadId.value) return
  try {
    const [employees, states] = await Promise.all([
      analyticsApi.getSoftwareDatasetEmployees(uploadId.value),
      analyticsApi.getSoftwareModelState(uploadId.value),
    ])
    datasetEmployees.value = employees
    modelStates.value = states as unknown as SalesModelStateResponse[]
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
  currentTrainingTarget.value = targetColumn.value  // seçili hedef eğitiliyor
  try {
    const result = await analyticsApi.trainSoftwareModel({
      upload_id: uploadId.value,
      target_column: targetColumn.value,
    })
    trainResult.value = result as unknown as SalesModelTrainResponse
    const states = await analyticsApi.getSoftwareModelState(uploadId.value)
    modelStates.value = states as unknown as SalesModelStateResponse[]
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Model eğitimi başarısız oldu.'
  } finally {
    loading.value = null
    currentTrainingTarget.value = null
  }
}

async function predict() {
  if (!uploadId.value || !employeeId.value) return
  error.value = null
  loading.value = 'predict'
  try {
    const result = await analyticsApi.getLatestSoftwarePrediction({
      upload_id: uploadId.value,
      employee_id: employeeId.value,
      target_column: targetColumn.value,
    })
    predResult.value = result as unknown as SalesPredictionResponse
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Tahmin alınamadı.'
  } finally {
    loading.value = null
  }
}

async function bulkPredict(withNarrative: boolean) {
  if (!uploadId.value) return
  error.value = null
  selectedTeamName.value = null

  if (withNarrative) {
    // ── LLM Yorumla: 4-hedef ML + Gemini narratifi paralel ──
    loading.value = 'narrative'
    try {
      const [allTargets, bulk] = await Promise.all([
        analyticsApi.getBulkSoftwareAllTargets({
          upload_id: uploadId.value,
          use_llm_narrative: false,
        }),
        analyticsApi.getBulkSoftwarePredictions({
          upload_id: uploadId.value,
          target_column: 'Performance_Drop_Target',
          use_llm_narrative: true,
        }),
      ])
      allTargetsResult.value = allTargets
      bulkResult.value = bulk as unknown as SalesBulkPredictionResponse
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'LLM yorumu başarısız oldu.'
    } finally {
      loading.value = null
    }
  } else {
    // ── Toplu Tara: 4 hedef ML, LLM yok (hızlı) ──
    loading.value = 'bulk'
    try {
      allTargetsResult.value = await analyticsApi.getBulkSoftwareAllTargets({
        upload_id: uploadId.value,
        use_llm_narrative: false,
      })
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Toplu analiz başarısız oldu.'
    } finally {
      loading.value = null
    }
  }
}

watch([targetColumn, uploadId], () => {
  predResult.value = null
  bulkResult.value = null
  allTargetsResult.value = null
  selectedTeamName.value = null
})

onMounted(async () => {
  await Promise.all([loadDatasets(), loadOverview()])
})
</script>
