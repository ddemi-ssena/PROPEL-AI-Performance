<template>
  <div class="min-h-screen bg-slate-50 pb-12">

    <!-- ══════════════════ HEADER ══════════════════ -->
    <div class="bg-white border-b border-slate-200 px-6 py-5 shadow-sm">
      <div class="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-5 max-w-screen-2xl mx-auto">
        <div class="flex items-start gap-4">
          <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-600 shadow-sm">
            <svg class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
            </svg>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <span class="inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <p class="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-600">Satış Departmanı · KPI & ML</p>
            </div>
            <h1 class="mt-0.5 text-xl font-bold text-slate-900">Satış Performansı Analizi</h1>
            <p class="mt-0.5 text-xs text-slate-400 max-w-lg">LightGBM + XGBoost + RandomForest stacking ensemble — performans düşüşü, tükenmişlik, istifa ve yüksek risk tahmini</p>
          </div>
        </div>
        <div class="flex flex-wrap items-end gap-3 shrink-0">
          <div class="flex flex-col gap-1">
            <label class="text-[10px] font-semibold uppercase tracking-wider text-slate-400 ml-0.5">Dataset</label>
            <select
              v-model.number="uploadId"
              class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm min-w-[210px] focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100 transition"
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
              class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm min-w-[155px] focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100 transition"
            >
              <option v-for="t in TARGETS" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-screen-2xl mx-auto px-6 space-y-5 pt-5">

      <!-- ══════════════════ KPI OVERVIEW ══════════════════ -->
      <div v-if="overview" class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3">
        <div
          v-for="metric in overview.metrics"
          :key="metric.key"
          class="bg-white rounded-xl border border-slate-200 px-4 py-4 shadow-sm hover:shadow-md transition-shadow"
        >
          <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">{{ metric.label }}</p>
          <p class="mt-2 text-2xl font-bold text-slate-900">{{ metric.value }}</p>
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
              <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">Stacking Ensemble</p>
              <p class="text-sm font-bold text-slate-900">LightGBM + XGB + RF <span class="text-slate-400 font-normal">→</span> LR</p>
            </div>
          </div>
          <button
            @click="trainModel"
            :disabled="!!loading || !uploadId"
            class="inline-flex items-center gap-2 rounded-lg bg-emerald-700 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-600 active:scale-95 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400 disabled:shadow-none"
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
          <span v-if="trainResult" class="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
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
              class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm min-w-[190px] focus:border-emerald-400 focus:outline-none focus:ring-1 focus:ring-emerald-200 transition"
            >
              <option :value="null">Çalışan seçin</option>
              <option v-for="e in datasetEmployees" :key="e.employee_id" :value="e.employee_id">
                {{ e.display_label || `${e.team || 'Takım'} / #${e.employee_id}` }}
              </option>
            </select>
            <button
              @click="predict"
              :disabled="!!loading || !uploadId || !employeeId"
              class="inline-flex items-center gap-1.5 rounded-lg border border-emerald-300 bg-emerald-50 px-3.5 py-2 text-sm font-semibold text-emerald-800 shadow-sm transition hover:bg-emerald-100 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40"
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
        <div v-if="uploadId && modelStates.length" class="p-4 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
          <div
            v-for="state in modelStates"
            :key="state.target_column"
            class="rounded-xl border p-4 transition-shadow hover:shadow-sm"
            :class="stateCardClass(state)"
          >
            <div class="flex items-start justify-between gap-2">
              <p class="text-sm font-bold text-slate-800 leading-tight">{{ state.target_label }}</p>
              <span class="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold" :class="stateBadgeClass(state)">
                {{ stateLabel(state) }}
              </span>
            </div>
            <p class="mt-1.5 text-[11px] text-slate-500">
              {{ state.is_trained ? `Son eğitim: ${formatDt(state.trained_at)}` : 'Henüz eğitilmedi' }}
            </p>
            <div v-if="state.is_trained" class="mt-3 grid grid-cols-2 gap-2">
              <div class="rounded-lg bg-white/70 px-2.5 py-2 text-xs">
                <p class="text-slate-400 text-[10px]">Weighted F1</p>
                <p class="mt-0.5 font-bold text-slate-800">{{ formatPct(state.metrics?.weighted_f1) }}</p>
              </div>
              <div class="rounded-lg bg-white/70 px-2.5 py-2 text-xs">
                <p class="text-slate-400 text-[10px]">Train / Test</p>
                <p class="mt-0.5 font-bold text-slate-800">{{ state.train_count }} / {{ state.test_count }}</p>
              </div>
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
                <circle cx="18" cy="18" r="14" fill="none" stroke="#10b981" stroke-width="3"
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
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-100'
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
            <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-600 mb-3">Önerilen Aksiyonlar</p>
            <div class="space-y-2">
              <div
                v-for="(a, i) in predResult.recommended_actions"
                :key="a"
                class="flex items-start gap-3 rounded-lg border border-emerald-100 bg-emerald-50/60 px-4 py-2.5"
              >
                <span class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-white text-[10px] font-bold mt-0.5">{{ (i as number) + 1 }}</span>
                <p class="text-sm text-slate-700 leading-5">{{ a }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ══════════════════ BULK RESULTS ══════════════════ -->
      <template v-if="bulkResult">

        <!-- LLM fallback notice -->
        <div
          v-if="bulkResult.items?.[0]?.narrative?.fallback_used"
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
            <p class="mt-3 text-4xl font-bold text-rose-700 tabular-nums">{{ bulkResult.high_risk_count }}</p>
            <p class="mt-1 text-xs text-slate-500">çalışan izleniyor</p>
          </div>
          <div class="bg-white rounded-2xl border border-slate-200 border-l-4 border-l-amber-400 p-5 shadow-sm">
            <div class="flex items-center justify-between gap-2">
              <p class="text-xs font-semibold uppercase tracking-[0.15em] text-amber-500">Orta Risk</p>
              <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50">
                <svg class="h-4 w-4 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              </div>
            </div>
            <p class="mt-3 text-4xl font-bold text-amber-600 tabular-nums">{{ bulkResult.medium_risk_count }}</p>
            <p class="mt-1 text-xs text-slate-500">dikkat listesinde</p>
          </div>
          <div class="bg-white rounded-2xl border border-slate-200 border-l-4 border-l-emerald-500 p-5 shadow-sm">
            <div class="flex items-center justify-between gap-2">
              <p class="text-xs font-semibold uppercase tracking-[0.15em] text-emerald-600">Düşük Risk</p>
              <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50">
                <svg class="h-4 w-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              </div>
            </div>
            <p class="mt-3 text-4xl font-bold text-emerald-700 tabular-nums">{{ bulkResult.low_risk_count }}</p>
            <p class="mt-1 text-xs text-slate-500">stabil çalışan</p>
          </div>
          <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
            <div class="flex items-center justify-between gap-2">
              <p class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">Toplam Analiz</p>
              <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100">
                <svg class="h-4 w-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
              </div>
            </div>
            <p class="mt-3 text-4xl font-bold text-slate-900 tabular-nums">{{ bulkResult.prediction_count }}</p>
            <p class="mt-1 text-xs text-slate-500">{{ targetLabel(bulkResult.target_column) }}</p>
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
            <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">Bölge / Takım Analizi</p>
            <h4 class="mt-0.5 text-base font-bold text-slate-900">Satış Takımları Risk Özeti
              <span class="ml-2 text-xs font-normal text-slate-400">— Satır seçerek detay görün</span>
            </h4>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-sm">
              <thead>
                <tr class="bg-slate-50 border-b border-slate-100 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                  <th class="px-6 py-3 text-left">Bölge / Takım</th>
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
                  :class="selectedTeamName === row.team ? 'bg-emerald-50' : 'hover:bg-slate-50/80'"
                >
                  <td class="px-6 py-4 font-semibold text-slate-900">
                    <div class="flex items-center gap-2">
                      <span class="h-2 w-2 rounded-full transition-all" :class="selectedTeamName === row.team ? 'bg-emerald-500' : 'bg-slate-200'"></span>
                      {{ row.team }}
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <div class="flex items-center gap-2.5">
                      <div class="w-24 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          class="h-full rounded-full transition-all"
                          :class="row.avgRisk > 60 ? 'bg-rose-500' : row.avgRisk > 35 ? 'bg-amber-400' : 'bg-emerald-500'"
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
                      :class="row.avgRisk > 60 ? 'bg-rose-50 text-rose-700 border-rose-200' : row.avgRisk > 35 ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-emerald-50 text-emerald-700 border-emerald-200'"
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
          <div class="bg-gradient-to-r from-emerald-700 to-teal-600 px-6 py-5 flex items-center justify-between gap-4">
            <div>
              <p class="text-[10px] font-semibold uppercase tracking-[0.18em] text-emerald-200">Seçili Takım</p>
              <h4 class="mt-0.5 text-xl font-bold text-white">{{ selectedTeamName }}</h4>
              <p class="mt-0.5 text-xs text-emerald-200">{{ selectedTeamPeople.length }} çalışan analizi</p>
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
              class="rounded-xl border border-slate-100 bg-white p-4 shadow-sm hover:border-emerald-200 hover:shadow-md transition-all"
            >
              <div class="flex items-center gap-3">
                <span
                  class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-white text-xs font-bold"
                  :class="avatarGradient(idx)"
                >{{ empInitials(person) }}</span>
                <div class="min-w-0 flex-1">
                  <p class="font-bold text-slate-900 truncate text-sm">{{ displayName(person) }}</p>
                  <p class="text-xs text-slate-400 truncate mt-0.5">{{ person.summary_payload?.role || person.summary_payload?.region || 'Satış' }}</p>
                </div>
                <span class="shrink-0 rounded-full border px-2 py-0.5 text-xs font-semibold" :class="bandClass(person.predicted_band, person.target_column)">
                  {{ bandLabel(person.predicted_band, person.target_column) }}
                </span>
              </div>
              <div class="mt-3">
                <div class="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                  <span>Model güveni</span>
                  <span class="font-semibold text-slate-600">{{ pct(person.confidence) }}</span>
                </div>
                <div class="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                  <div class="h-full rounded-full bg-emerald-500 transition-all" :style="{ width: pct(person.confidence) }"/>
                </div>
              </div>
              <div v-if="person.top_drivers?.[0]" class="mt-3 rounded-lg bg-slate-50 border border-slate-100 px-3 py-2 text-xs">
                <span class="text-slate-400">Ana sinyal: </span>
                <span class="font-semibold text-slate-700">{{ person.top_drivers[0].metric_name }}</span>
              </div>
              <div v-if="person.recommended_actions?.[0]" class="mt-2 rounded-lg bg-emerald-50 border border-emerald-100 px-3 py-2 text-xs text-emerald-700 leading-4">
                {{ person.recommended_actions[0] }}
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
                <span class="ml-1.5 text-sm font-normal text-slate-400">· {{ filteredItems.length }} çalışan</span>
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
                class="rounded-lg border border-slate-200 pl-9 pr-4 py-2 text-sm text-slate-700 shadow-sm w-52 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100 transition"
              />
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-sm">
              <thead>
                <tr class="bg-slate-50 border-b border-slate-100 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                  <th class="px-6 py-3 text-left">Çalışan</th>
                  <th class="px-6 py-3 text-left">Bölge / Rol</th>
                  <th class="px-6 py-3 text-left">Tahmin</th>
                  <th class="px-6 py-3 text-left">Güven</th>
                  <th class="px-6 py-3 text-left">Ana Sinyal</th>
                  <th class="px-6 py-3 text-left">Öneri</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-50">
                <tr
                  v-for="item in filteredItems"
                  :key="item.employee_id"
                  class="hover:bg-slate-50/70 transition-colors"
                >
                  <td class="px-6 py-3.5 font-semibold text-slate-900">{{ displayName(item) }}</td>
                  <td class="px-6 py-3.5 text-slate-500">{{ item.summary_payload?.region || item.summary_payload?.role || '—' }}</td>
                  <td class="px-6 py-3.5">
                    <span class="rounded-full border px-2.5 py-0.5 text-xs font-semibold" :class="bandClass(item.predicted_band, item.target_column)">
                      {{ bandLabel(item.predicted_band, item.target_column) }}
                    </span>
                  </td>
                  <td class="px-6 py-3.5">
                    <div class="flex items-center gap-2">
                      <div class="w-16 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                        <div class="h-full rounded-full bg-emerald-500" :style="{ width: pct(item.confidence) }"/>
                      </div>
                      <span class="text-xs text-slate-600 tabular-nums">{{ pct(item.confidence) }}</span>
                    </div>
                  </td>
                  <td class="px-6 py-3.5 text-slate-600">{{ item.top_drivers?.[0]?.metric_name || '—' }}</td>
                  <td class="px-6 py-3.5 text-slate-500 max-w-xs">
                    <p class="truncate text-xs">{{ item.recommended_actions?.[0] || '—' }}</p>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>

      <!-- ══════════════════ EMPTY STATE ══════════════════ -->
      <div
        v-if="!bulkResult && !predResult && !loading"
        class="rounded-2xl border-2 border-dashed border-slate-200 bg-white p-16 text-center"
      >
        <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-50">
          <svg class="h-8 w-8 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
          </svg>
        </div>
        <h4 class="mt-5 text-lg font-bold text-slate-900">Satış ML Analizine Hoş Geldiniz</h4>
        <p class="mt-2 text-sm text-slate-500 max-w-sm mx-auto leading-6">
          Dataset ve hedef değişkeni seçin, ardından <strong class="text-slate-700">Toplu Tara</strong> ile tüm satış ekibinin risk profilini tek tıkla çıkarın.
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
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-400"></span> Yüksek risk skoru
          </span>
        </div>
      </div>

    </div>

    <!-- ══════════════════ LOADING OVERLAY ══════════════════ -->
    <div v-if="loading" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/25 backdrop-blur-sm">
      <div class="rounded-2xl bg-white p-8 shadow-2xl border border-slate-200 text-center w-full max-w-xs mx-4">
        <div class="mx-auto h-12 w-12 rounded-full border-4 border-slate-100 border-t-emerald-600 animate-spin"/>
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
    const items = bulkResult.value!.items.filter((i: SalesPredictionResponse) => (i.summary_payload?.region || i.summary_payload?.team || 'Genel') === ta.team)
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
  return bulkResult.value.items.filter((i: SalesPredictionResponse) => {
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
  return items.filter((i: SalesPredictionResponse) => displayName(i).toLowerCase().includes(q) || (i.summary_payload?.region || '').toLowerCase().includes(q))
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
    return 'bg-rose-50 text-rose-700 border-rose-200'
  }
  if (b.includes('medium') || b.includes('orta') || b.includes('moderate')) {
    return 'bg-amber-50 text-amber-700 border-amber-200'
  }
  if (b === '0' || b === 'false' || b.includes('low') || b.includes('düşük')) {
    return 'bg-emerald-50 text-emerald-700 border-emerald-200'
  }
  return 'bg-slate-100 text-slate-700 border-slate-200'
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
