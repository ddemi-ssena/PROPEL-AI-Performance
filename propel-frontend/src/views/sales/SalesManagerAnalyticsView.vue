<template>
  <div class="space-y-8 pb-10">

    <!-- ── Header + Section tabs ──────────────────────────────── -->
    <div class="flex flex-col xl:flex-row xl:items-end xl:justify-between gap-4 border-b border-slate-200 pb-6">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 tracking-tight">KPI & ML Analizi</h2>
        <p class="mt-1 text-slate-500">
          Satış departmanı risk tahmini, KPI omurgası ve takım analizini tek ekranda yönetin.
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <select
          v-model.number="uploadId"
          class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 shadow-sm"
          @change="onDatasetChange"
        >
          <option :value="null">Dataset seç</option>
          <option v-for="ds in datasets" :key="ds.id" :value="ds.id">#{{ ds.id }} — {{ ds.file_name }}</option>
        </select>
        <select
          v-model="targetColumn"
          class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 shadow-sm"
        >
          <option v-for="t in TARGETS" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
      </div>
    </div>

    <!-- ── Metric cards ───────────────────────────────────────── -->
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

    <!-- ── ML Model panel ─────────────────────────────────────── -->
    <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div class="flex flex-col xl:flex-row xl:items-start xl:justify-between gap-5">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Admin ML Kaynagi</p>
          <p class="mt-2 text-sm leading-6 text-slate-500">
            Model egitimi yalnizca admin ekraninda yapilir; bu sayfa adminin current dataset icin egittigi sonuclari okur.
          </p>
          <h3 class="mt-1 text-lg font-bold text-slate-900">Satış risk tahmini — LightGBM + XGB + RF → LR</h3>
        </div>
        <div class="flex flex-wrap gap-2 w-full xl:max-w-4xl">
          <select
            v-model.number="employeeId"
            class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 shadow-sm"
          >
            <option :value="null">Çalışan seç</option>
            <option v-for="e in datasetEmployees" :key="e.employee_id" :value="e.employee_id">
              {{ e.display_label || `${e.team || 'Takım yok'} / #${e.employee_id}` }}
            </option>
          </select>
          <button
            class="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm disabled:cursor-not-allowed disabled:text-slate-300"
            :disabled="!!mlLoading || !hasAdminCurrentModel || !employeeId"
            @click="runPredict"
          >
            {{ mlLoading === 'predict' ? 'Hesaplanıyor…' : 'Tahmin Al' }}
          </button>
          <button
            class="rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-2.5 text-sm font-semibold text-indigo-800 shadow-sm disabled:cursor-not-allowed disabled:text-indigo-300"
            :disabled="!!mlLoading || !hasAdminCurrentModel"
            @click="runBulk(false)"
          >
            {{ mlLoading === 'bulk' ? 'Tarıyor…' : 'Toplu Tara' }}
          </button>
          <button
            class="rounded-xl border border-violet-200 bg-violet-50 px-4 py-2.5 text-sm font-semibold text-violet-800 shadow-sm disabled:cursor-not-allowed disabled:text-violet-300"
            :disabled="!!mlLoading || !hasAdminCurrentModel"
            @click="runBulk(true)"
          >
            {{ mlLoading === 'narrative' ? 'Yorumlanıyor…' : 'LLM Yorumla' }}
          </button>
        </div>
      </div>

      <!-- Status badges -->
      <div v-if="currentTargetState || mlError" class="mt-4 flex flex-wrap items-center gap-2 text-xs">
        <span v-if="currentTargetState"
          class="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 font-medium text-emerald-700">
          Admin modeli hazir: {{ targetLabel(currentTargetState.target_column) }} - F1 {{ fmtPct(currentTargetState.metrics?.weighted_f1) }}
        </span>
        <span v-if="mlError"
          class="rounded-full border border-rose-200 bg-rose-50 px-3 py-1 font-medium text-rose-700">
          {{ mlError }}
        </span>
      </div>
    </div>

    <!-- ── Section eyebrow card ───────────────────────────────── -->
    <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{{ activeMeta.eyebrow }}</p>
          <h3 class="mt-1 text-xl font-bold text-slate-900">{{ activeMeta.title }}</h3>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{{ activeMeta.description }}</p>
        </div>
        <button
          v-if="activeMeta.action"
          class="w-fit rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-2.5 text-sm font-semibold text-indigo-800 shadow-sm disabled:cursor-not-allowed disabled:text-indigo-300"
          :disabled="!!mlLoading || !hasAdminCurrentModel"
          @click="activeMeta.onAction()"
        >
          {{ mlLoading ? 'Çalışıyor…' : activeMeta.action }}
        </button>
      </div>
    </div>

    <!-- ── Section: Model Durumu ──────────────────────────────── -->
    <template v-if="activeSection === 'model'">

      <!-- Model state cards (per target) -->
      <div v-if="modelStates.length" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <div
          v-for="state in modelStates"
          :key="state.target_column"
          class="rounded-2xl border p-5"
          :class="state.is_trained
            ? state.is_current_dataset
              ? 'border-emerald-200 bg-emerald-50'
              : 'border-amber-200 bg-amber-50'
            : 'border-slate-200 bg-slate-50'"
        >
          <div class="flex items-start justify-between gap-3">
            <p class="text-sm font-bold text-slate-900 leading-5">{{ state.target_label }}</p>
            <span class="rounded-full px-2.5 py-1 text-xs font-semibold whitespace-nowrap"
              :class="state.is_trained
                ? state.is_current_dataset
                  ? 'border border-emerald-200 bg-white text-emerald-700'
                  : 'border border-amber-200 bg-white text-amber-700'
                : 'border border-slate-200 bg-white text-slate-500'">
              {{ state.is_trained ? (state.is_current_dataset ? 'Hazır' : 'Eski dataset') : 'Eğitilmedi' }}
            </span>
          </div>
          <p class="mt-2 text-xs text-slate-500">
            {{ state.is_trained ? `Son eğitim: ${fmtDate(state.trained_at)}` : 'Henüz eğitim yapılmadı.' }}
          </p>
          <div v-if="state.is_trained" class="mt-3 grid grid-cols-2 gap-2 text-xs">
            <div class="rounded-lg bg-white/70 px-2 py-1.5">
              <p class="text-slate-400">Weighted F1</p>
              <p class="font-bold text-slate-800">{{ fmtPct(state.metrics?.weighted_f1) }}</p>
            </div>
            <div class="rounded-lg bg-white/70 px-2 py-1.5">
              <p class="text-slate-400">Train / Test</p>
              <p class="font-bold text-slate-800">{{ state.train_count || '—' }} / {{ state.test_count || '—' }}</p>
            </div>
          </div>
        </div>
      </div>
      <div v-else-if="uploadId" class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center text-sm text-slate-500">
        Dataset için model durumu yüklenemedi. Önce "Model Eğit"i çalıştırın.
      </div>

      <!-- Individual prediction result -->
      <div v-if="predResult" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 mb-4">Bireysel Tahmin Sonucu</p>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
            <p class="text-xs font-semibold text-slate-500">Tahmin</p>
            <p class="mt-2 text-xl font-bold text-slate-900">{{ bandLabel(predResult.predicted_band, predResult.target_column) }}</p>
            <p class="mt-1 text-xs text-slate-400">{{ targetLabel(predResult.target_column) }}</p>
          </div>
          <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
            <p class="text-xs font-semibold text-slate-500">Güven</p>
            <p class="mt-2 text-xl font-bold text-emerald-700">{{ Math.round(predResult.confidence * 100) }}%</p>
            <div class="mt-2 h-1.5 rounded-full bg-slate-200 overflow-hidden">
              <div class="h-full rounded-full bg-emerald-500" :style="{ width: `${predResult.confidence * 100}%` }"></div>
            </div>
          </div>
          <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
            <p class="text-xs font-semibold text-slate-500">Ana Sinyal</p>
            <p class="mt-2 text-sm font-bold text-slate-900">{{ predResult.top_drivers?.[0]?.metric_name || '—' }}</p>
          </div>
        </div>
        <div v-if="predResult.recommended_actions?.length" class="mt-4">
          <p class="text-xs font-semibold text-slate-500 mb-2">Önerilen Aksiyonlar</p>
          <ul class="space-y-1.5">
            <li v-for="(action, i) in predResult.recommended_actions" :key="i"
              class="flex items-start gap-2 text-sm text-slate-700">
              <span class="mt-0.5 w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-bold shrink-0">{{ (i as number) + 1 }}</span>
              {{ action }}
            </li>
          </ul>
        </div>
      </div>

      <!-- Bulk summary cards -->
      <div v-if="bulkResult" class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="rounded-2xl border-l-4 border-rose-400 bg-white p-5 shadow-sm">
          <p class="text-xs font-semibold uppercase text-slate-400">Yüksek Risk</p>
          <p class="mt-2 text-3xl font-bold text-rose-600">{{ bulkResult.high_risk_count }}</p>
        </div>
        <div class="rounded-2xl border-l-4 border-amber-400 bg-white p-5 shadow-sm">
          <p class="text-xs font-semibold uppercase text-slate-400">Orta Risk</p>
          <p class="mt-2 text-3xl font-bold text-amber-600">{{ bulkResult.medium_risk_count }}</p>
        </div>
        <div class="rounded-2xl border-l-4 border-emerald-400 bg-white p-5 shadow-sm">
          <p class="text-xs font-semibold uppercase text-slate-400">Düşük Risk</p>
          <p class="mt-2 text-3xl font-bold text-emerald-600">{{ bulkResult.low_risk_count }}</p>
        </div>
        <div class="rounded-2xl border-l-4 border-slate-400 bg-white p-5 shadow-sm">
          <p class="text-xs font-semibold uppercase text-slate-400">Toplam Analiz</p>
          <p class="mt-2 text-3xl font-bold text-slate-700">{{ bulkResult.prediction_count }}</p>
        </div>
      </div>
    </template>

    <!-- ── Section: Departman Analizi ────────────────────────── -->
    <template v-if="activeSection === 'department' && overview">
      <div class="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_320px] gap-6">
        <!-- Bar chart -->
        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 mb-1">KPI Takım Karşılaştırması</p>
          <h3 class="text-lg font-bold text-slate-900 mb-5">Takım bazlı performans ve trend</h3>
          <div v-if="overview.team_summaries.length" class="overflow-x-auto">
            <svg :width="deptChartW" height="260" class="w-full" :viewBox="`0 0 ${deptChartW} 260`" preserveAspectRatio="xMidYMid meet">
              <g v-for="tick in [0,25,50,75,100,125]" :key="tick">
                <line :x1="42" :y1="dYPos(tick)" :x2="deptChartW - 20" :y2="dYPos(tick)" stroke="#F1F5F9" stroke-width="1"/>
                <text :x="38" :y="dYPos(tick)+4" text-anchor="end" font-size="11" fill="#94A3B8">{{ tick }}</text>
              </g>
              <g v-for="(team, i) in overview.team_summaries" :key="team.team">
                <rect :x="dBarX(i)" :y="dYPos(team.average_score)" :width="56" :height="210-dYPos(team.average_score)+20" rx="4" fill="#2563EB" opacity="0.85"/>
                <text :x="dBarX(i)+28" :y="dYPos(team.average_score)-5" text-anchor="middle" font-size="11" font-weight="700" fill="#1D4ED8">{{ Math.round(team.average_score) }}</text>
                <text :x="dBarX(i)+28" y="252" text-anchor="middle" font-size="10" fill="#64748B">{{ shortName(team.team) }}</text>
              </g>
              <polyline v-if="overview.team_summaries.length > 1" :points="dTrendPts" fill="none" stroke="#EF4444" stroke-width="2" stroke-linecap="round"/>
              <circle v-for="(t,i) in overview.team_summaries" :key="`d-${t.team}`"
                :cx="dBarX(i)+28" :cy="dTrendY(t)"
                r="4" :fill="(t.average_trend_delta??0)>=0?'#10B981':'#EF4444'"/>
            </svg>
            <div class="flex items-center gap-5 mt-2 text-xs font-semibold text-slate-500">
              <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-sm bg-blue-500 opacity-85"></span>Ortalama KPI</span>
              <span class="flex items-center gap-1.5"><span class="w-4 h-1 bg-red-400 rounded-full"></span>4H Trend</span>
            </div>
          </div>
        </div>
        <!-- Team summary list -->
        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 mb-4">Takım KPI Özeti</p>
          <div class="space-y-4">
            <div v-for="team in overview.team_summaries" :key="team.team">
              <div class="flex items-start justify-between gap-2 mb-1.5">
                <p class="text-sm font-bold text-slate-800 truncate">{{ team.team }}</p>
                <span class="text-sm font-bold shrink-0" :class="sColor(team.average_score)">{{ Math.round(team.average_score) }}/100</span>
              </div>
              <div class="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div class="h-full rounded-full" :class="sBarColor(team.average_score)" :style="{ width: `${Math.min(100,team.average_score)}%` }"></div>
              </div>
              <div class="flex items-center justify-between mt-1 text-xs text-slate-400">
                <span>{{ team.employee_count }} çalışan analizi</span>
                <span v-if="team.average_trend_delta!=null" :class="(team.average_trend_delta??0)>=0?'text-emerald-600':'text-rose-500'" class="font-semibold">
                  {{ (team.average_trend_delta??0)>=0?'▲':'▼' }} {{ (team.average_trend_delta??0).toFixed(1) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Analytics omurgası + sprint -->
      <div class="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_340px] gap-6">
        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex items-start justify-between gap-4 mb-1">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Analytics Omurgası</p>
            <span class="text-xs font-semibold px-2.5 py-1 rounded-full border text-emerald-700 bg-emerald-50 border-emerald-200">Canlı</span>
          </div>
          <h3 class="text-lg font-bold text-slate-900 mb-2">{{ overview.definition.label }}</h3>
          <p class="text-sm text-slate-500 leading-6 mb-5">{{ overview.definition.description }}</p>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div v-for="layer in overview.definition.layers" :key="layer.key"
              class="rounded-xl border border-slate-100 bg-slate-50 p-4">
              <p class="text-sm font-bold text-slate-700 mb-1">{{ layer.title }}</p>
              <p class="text-xs text-slate-500 leading-5">{{ layer.summary }}</p>
            </div>
          </div>
        </div>
        <div class="rounded-2xl bg-slate-900 p-6 text-white shadow-sm">
          <p class="text-xs font-semibold text-slate-400">Sprint 1</p>
          <h3 class="mt-1 text-lg font-bold mb-5">Yapılanlar ve sıradaki adım</h3>
          <p class="text-xs font-semibold text-slate-400 mb-2">Planlanan hedefler</p>
          <div class="flex flex-wrap gap-2 mb-5">
            <span v-for="t in overview.definition.planned_targets" :key="t"
              class="text-xs font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 border border-slate-700">{{ t }}</span>
          </div>
          <p class="text-xs font-semibold text-slate-400 mb-2">Sprint odağı</p>
          <ul class="space-y-2.5">
            <li v-for="item in overview.sprint_focus" :key="item" class="flex items-start gap-2 text-sm text-slate-300 leading-5">
              <span class="mt-1 w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0"></span>{{ item }}
            </li>
          </ul>
        </div>
      </div>
    </template>

    <!-- ── Section: Takım Analizi ─────────────────────────────── -->
    <template v-if="activeSection === 'teams'">
      <div v-if="!bulkResult" class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
        <p class="text-sm font-semibold text-slate-900">Takim analizi adminin egittigi current sales modeliyle uretilir.</p>
        <p class="mt-2 text-sm text-slate-500">Bolge risk dagilimi, 6 aylik trend ve satis baskisi ayni bulk prediction sonucundan okunur.</p>
        <button class="mt-4 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm disabled:bg-slate-300" :disabled="!!mlLoading || !hasAdminCurrentModel" @click="runBulk(false)">
          Analizi Calistir
        </button>
      </div>
      <div v-else class="grid grid-cols-1 gap-5 xl:grid-cols-[240px_minmax(0,1fr)]">
        <aside class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Takimlar</p>
          <div class="mt-4 space-y-2">
            <button v-for="row in teamRows" :key="row.team" type="button" class="w-full rounded-xl border px-3 py-3 text-left transition" :class="selectedTeam === row.team ? 'border-blue-300 bg-white shadow-sm' : 'border-transparent hover:bg-white'" @click="selectedTeam = row.team">
              <div class="flex items-center justify-between gap-2">
                <p class="truncate text-sm font-bold text-slate-900">{{ row.team }}</p>
                <span class="h-2 w-2 rounded-full" :class="teamDotClass(row)"></span>
              </div>
              <p class="mt-1 text-xs text-slate-500">{{ row.highCount }} yuksek / {{ row.mediumCount }} orta</p>
            </button>
          </div>
        </aside>

        <div v-if="selectedTeamRow" class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div class="bg-gradient-to-r from-blue-700 to-sky-500 p-6 text-white">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div class="min-w-0">
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-white/70">Satis Takim Analizi</p>
                <h3 class="mt-1 truncate text-3xl font-black">{{ selectedTeamRow.team }}</h3>
                <p class="mt-2 text-sm text-white/80">{{ selectedTeamRow.total }} kisilik grupta {{ selectedTeamRow.highCount }} yuksek, {{ selectedTeamRow.mediumCount }} orta risk sinyali var.</p>
              </div>
              <span class="inline-flex w-fit items-center gap-2 rounded-full bg-white/15 px-5 py-3 text-sm font-bold">
                <span class="h-2.5 w-2.5 rounded-full" :class="teamDotClass(selectedTeamRow)"></span>
                {{ teamRiskLabel(selectedTeamRow) }}
              </span>
            </div>
          </div>

          <div class="grid grid-cols-1 gap-4 p-5 md:grid-cols-2 xl:grid-cols-4">
            <article v-for="card in selectedTeamMetricCards" :key="card.label" class="rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
              <div class="flex items-start justify-between gap-4">
                <span class="flex h-10 w-10 items-center justify-center rounded-xl text-sm font-black" :class="card.indexClass">{{ card.index }}</span>
                <span class="text-xs font-semibold text-slate-400">{{ card.group }}</span>
              </div>
              <p class="mt-4 text-sm font-semibold text-slate-500">{{ card.label }}</p>
              <p class="mt-2 text-[32px] font-bold leading-none" :class="card.valueClass">{{ card.value }}</p>
              <p class="mt-3 text-sm text-slate-500">{{ card.hint }}</p>
            </article>
          </div>

          <div class="px-5 pb-5">
            <article class="rounded-xl border-2 border-amber-300 bg-gradient-to-r from-amber-50 to-rose-50 p-6">
              <div class="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,0.7fr)_minmax(240px,0.3fr)] lg:items-center">
                <div>
                  <span class="inline-flex rounded-full border border-amber-300 bg-white/70 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-amber-800">Bu hafta odaklanilacak</span>
                  <h5 class="mt-4 text-2xl font-bold text-amber-950">{{ selectedTeamRow.topReason }} kritik sinyal</h5>
                  <p class="mt-3 text-base leading-7 text-amber-900">{{ selectedTeamProblemDescription }}</p>
                </div>
                <div class="rounded-xl border border-amber-200 bg-white/70 p-5 shadow-sm">
                  <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-100 text-2xl font-black text-amber-700">!</div>
                  <p class="mt-4 text-xs font-semibold uppercase tracking-[0.16em] text-amber-700">Ana Neden</p>
                  <p class="mt-2 text-lg font-bold leading-6 text-amber-950">{{ selectedTeamRow.topReason }}</p>
                  <div class="mt-4 h-2 overflow-hidden rounded-full bg-white">
                    <div class="h-full rounded-full bg-gradient-to-r from-amber-400 to-rose-500" :style="{ width: `${selectedTeamRow.riskScore}%` }"></div>
                  </div>
                  <p class="mt-2 text-xs text-amber-800">{{ selectedTeamRow.riskScore }}/100 admin model takim risk skoru</p>
                </div>
              </div>
            </article>
          </div>

          <div class="grid grid-cols-1 gap-5 px-5 pb-5 xl:grid-cols-[minmax(0,0.65fr)_minmax(320px,0.35fr)]">
            <article class="rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
              <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p class="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-500">Performans Trendi</p>
                  <h5 class="mt-1 text-lg font-bold text-slate-900">6 Aylik Performans Trendi</h5>
                  <p class="mt-2 text-sm leading-6 text-slate-500">Y ekseni 0-100 performans sagligi; admin ensemble risk serisinin ters cevrilmis takim performans sinyalidir.</p>
                </div>
                <span class="w-fit rounded-full bg-emerald-50 px-3 py-1 text-sm font-bold text-emerald-700">{{ selectedTeamPerformanceChangeLabel }}</span>
              </div>
              <div class="mt-6 h-[260px] rounded-xl border border-slate-100 bg-slate-50 p-4">
                <svg viewBox="0 0 600 220" class="h-full w-full" preserveAspectRatio="none">
                  <line v-for="tick in [0, 25, 50, 75, 100]" :key="tick" x1="28" :y1="trendY(tick)" x2="585" :y2="trendY(tick)" stroke="#E2E8F0" stroke-width="1" />
                  <polyline :points="selectedTeamPerformanceTrendPoints" fill="none" stroke="#10B981" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
                  <circle v-for="(point, index) in selectedTeamPerformanceCirclePoints" :key="index" :cx="point.x" :cy="point.y" r="4" fill="#10B981" />
                </svg>
              </div>
            </article>

            <aside class="rounded-xl bg-gradient-to-br from-violet-600 to-blue-600 p-6 text-white shadow-sm">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <p class="text-xs font-semibold uppercase tracking-[0.18em] text-white/70">AI Aksiyon Paneli</p>
                  <h5 class="mt-1 text-xl font-bold">Onerilen Aksiyonlar</h5>
                </div>
                <span class="rounded-full bg-white/15 px-3 py-1 text-xs font-bold text-white/90">Admin ML</span>
              </div>
              <div class="mt-5 space-y-3">
                <article v-for="action in selectedTeamSalesActions" :key="action.title" class="rounded-lg border border-white/10 bg-white/10 p-3">
                  <p class="text-sm font-bold leading-5">{{ action.title }}</p>
                  <p class="mt-2 text-sm leading-6 text-white/80">{{ action.reason }}</p>
                </article>
                <button class="mt-2 rounded-lg bg-white px-3 py-2 text-xs font-bold text-violet-700 disabled:cursor-not-allowed disabled:opacity-60" :disabled="Boolean(mlLoading) || !selectedTeamRow" @click="runBulk(true)">
                  {{ mlLoading === 'narrative' ? 'Yorumlaniyor...' : 'LLM ile Takimi Yorumla' }}
                </button>
              </div>
            </aside>
          </div>

          <div class="px-5 pb-5">
            <section class="rounded-xl bg-slate-50 p-6">
              <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p class="text-xl font-bold text-slate-950">Bu Hafta Konusulacak Konular</p>
                  <p class="mt-1 text-sm text-slate-500">{{ selectedTeamTalkingPointItems.length }} oncelikli satis konusu belirlendi</p>
                </div>
                <span class="w-fit rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600">Manager checklist</span>
              </div>

              <div class="mt-5 space-y-3">
                <article v-for="item in selectedTeamTalkingPointItems" :key="item.id" class="rounded-xl border border-slate-200 bg-white p-4">
                  <div class="flex flex-col gap-3 sm:flex-row sm:items-start">
                    <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">{{ item.index }}</span>
                    <div class="min-w-0 flex-1">
                      <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                        <p class="text-base font-bold text-slate-900">{{ item.title }}</p>
                        <span class="w-fit rounded-full px-3 py-1 text-xs font-bold" :class="item.badgeClass">{{ item.priority }}</span>
                      </div>
                      <p class="mt-2 text-sm leading-6 text-slate-600">{{ item.detail }}</p>
                      <ul class="mt-3 space-y-1 text-sm leading-6 text-slate-500">
                        <li v-for="bullet in item.bullets" :key="bullet">- {{ bullet }}</li>
                      </ul>
                    </div>
                  </div>
                </article>
              </div>
            </section>
          </div>

          <div v-if="selectedTeamNarrative" class="mx-5 mb-5 rounded-xl border border-violet-100 bg-violet-50 p-4">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-violet-500">Takim Yorumu</p>
            <p class="mt-3 text-sm leading-6 text-slate-700">{{ selectedTeamNarrative.manager_summary }}</p>
          </div>

          <div class="px-5 pb-5">
            <section class="rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
              <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p class="text-2xl font-bold text-slate-950">Takim Uyeleri - Detayli Risk Analizi</p>
                  <p class="mt-1 text-sm text-slate-500">{{ selectedTeamRow.highCount }} kisi yuksek risk seviyesinde</p>
                </div>
                <span class="w-fit rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{{ selectedTeamPeople.length }} kisi listeleniyor</span>
              </div>
              <div class="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 2xl:grid-cols-3">
                <article v-for="person in selectedTeamPeople" :key="person.employee_id" class="rounded-xl border border-slate-200 bg-white p-5">
                  <div class="flex items-start gap-4">
                    <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-black text-white">{{ initials(displayName(person)) }}</span>
                    <div class="min-w-0">
                      <p class="truncate text-lg font-bold text-slate-950">{{ displayName(person) }}</p>
                      <p class="mt-1 truncate text-sm text-slate-500">{{ salesPersonRoleLabel(person) }}</p>
                    </div>
                  </div>
                  <div class="my-4 border-t border-slate-100"></div>
                  <div class="flex items-center justify-between gap-3">
                    <p class="text-sm font-semibold text-slate-600">Model Riski</p>
                    <p class="text-sm font-bold text-slate-950">{{ personRiskScore(person) }}/100</p>
                  </div>
                  <div class="mt-2 h-2 overflow-hidden rounded bg-slate-100">
                    <div class="h-full rounded bg-rose-500" :style="{ width: `${personRiskScore(person)}%` }"></div>
                  </div>
                  <div class="mt-4 flex items-center justify-between gap-3">
                    <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">#{{ person.summary_payload?.external_code || person.summary_payload?.employee_code || person.employee_id }}</span>
                    <span class="rounded-full px-3 py-1 text-xs font-bold" :class="bandClass(person.predicted_band, person.target_column)">{{ bandLabel(person.predicted_band, person.target_column) }}</span>
                  </div>
                  <p class="mt-3 text-xs leading-5 text-slate-500">{{ personTopDriver(person) }}</p>
                </article>
                <div v-if="!selectedTeamPeople.length" class="col-span-full rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm font-semibold text-slate-500">
                  Bu takim icin admin bulk prediction sonucunda eslesen calisan bulunamadi. Dataset bolge/takim kodu ve calisan eslesmesi kontrol edilmeli.
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>
    </template>

    <template v-if="false && activeSection === 'teams'">
      <div v-if="!bulkResult" class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
        <p class="text-sm font-semibold text-slate-900">Takım analizi için önce toplu tahmin çalıştırılmalı.</p>
        <button class="mt-4 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm disabled:bg-slate-300"
          :disabled="!!mlLoading || !uploadId" @click="runBulk(false)">
          Analizi Çalıştır
        </button>
      </div>
      <template v-else>
        <!-- Team risk table -->
        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 mb-4">Takım Risk Özeti</p>
          <div class="overflow-x-auto rounded-xl border border-slate-100">
            <table class="min-w-full text-sm">
              <thead>
                <tr class="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-400">
                  <th class="px-5 py-3 text-left">Takım</th>
                  <th class="px-5 py-3 text-left">Çalışan</th>
                  <th class="px-5 py-3 text-left">Yüksek Risk</th>
                  <th class="px-5 py-3 text-left">Risk Oranı</th>
                  <th class="px-5 py-3 text-left">Durum</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, idx) in teamRows" :key="row.team"
                  class="border-t border-slate-100 hover:bg-slate-50 cursor-pointer transition-colors"
                  :class="selectedTeam === row.team ? 'ring-1 ring-inset ring-indigo-200 bg-indigo-50/30' : ''"
                  @click="selectedTeam = row.team">
                  <td class="px-5 py-3.5 font-bold text-slate-800">{{ row.team }}</td>
                  <td class="px-5 py-3.5 text-slate-600">{{ row.total }}</td>
                  <td class="px-5 py-3.5">
                    <span class="font-bold" :class="row.highCount > 0 ? 'text-rose-600' : 'text-emerald-600'">{{ row.highCount }}</span>
                  </td>
                  <td class="px-5 py-3.5">
                    <div class="flex items-center gap-2">
                      <div class="w-20 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div class="h-full rounded-full" :class="row.avgRisk > 50 ? 'bg-rose-500' : row.avgRisk > 25 ? 'bg-amber-500' : 'bg-emerald-500'"
                          :style="{ width: `${row.avgRisk}%` }"></div>
                      </div>
                      <span class="text-xs text-slate-600 tabular-nums">%{{ row.avgRisk }}</span>
                    </div>
                  </td>
                  <td class="px-5 py-3.5">
                    <span class="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border"
                      :class="row.avgRisk > 50 ? 'text-rose-700 bg-rose-50 border-rose-200' : row.avgRisk > 25 ? 'text-amber-700 bg-amber-50 border-amber-200' : 'text-emerald-700 bg-emerald-50 border-emerald-200'">
                      <span class="w-1.5 h-1.5 rounded-full" :class="row.avgRisk > 50 ? 'bg-rose-500' : row.avgRisk > 25 ? 'bg-amber-500' : 'bg-emerald-500'"></span>
                      {{ row.avgRisk > 50 ? 'Kritik' : row.avgRisk > 25 ? 'İzlemede' : 'Stabil' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Selected team detail -->
        <div v-if="selectedTeamPeople.length" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 mb-1">Takım Detayı</p>
          <h3 class="text-lg font-bold text-slate-900 mb-4">{{ selectedTeam }}</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            <div v-for="person in selectedTeamPeople" :key="person.employee_id"
              class="rounded-xl border border-slate-100 bg-slate-50 p-4">
              <div class="flex items-center justify-between gap-3 mb-2">
                <p class="text-sm font-bold text-slate-800 truncate">{{ displayName(person) }}</p>
                <span class="text-xs font-semibold px-2 py-0.5 rounded-full border"
                  :class="bandClass(person.predicted_band, person.target_column)">
                  {{ bandLabel(person.predicted_band, person.target_column) }}
                </span>
              </div>
              <div class="flex items-center gap-2">
                <div class="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                  <div class="h-full rounded-full bg-emerald-500" :style="{ width: `${person.confidence * 100}%` }"></div>
                </div>
                <span class="text-xs text-slate-500 tabular-nums">{{ Math.round(person.confidence * 100) }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Department narrative -->
        <div v-if="deptNarrative" class="rounded-2xl border border-violet-100 bg-violet-50/70 p-5">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-violet-500">Departman Yorumu</p>
          <h4 class="mt-1 text-base font-bold text-slate-900">{{ deptNarrative?.manager_summary }}</h4>
          <p class="mt-3 text-sm leading-6 text-slate-700">{{ deptNarrative?.risk_interpretation }}</p>
        </div>
      </template>
    </template>

    <!-- ── Section: Çalışan Analizi ───────────────────────────── -->
    <template v-if="activeSection === 'watchlist'">
      <div v-if="!bulkResult" class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
        <p class="text-sm font-semibold text-slate-900">Çalışan analizi için önce toplu tahmin çalıştırılmalı.</p>
        <button class="mt-4 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm disabled:bg-slate-300"
          :disabled="!!mlLoading || !uploadId" @click="runBulk(false)">
          Analizi Çalıştır
        </button>
      </div>
      <div v-else class="space-y-6">
        <div class="mb-4 border-b border-slate-100 pb-4">
          <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Calisan Analizi</p>
              <h4 class="mt-1 text-lg font-bold text-slate-900">Calisan listesi ve bireysel analiz girisi</h4>
              <p class="mt-2 text-sm leading-6 text-slate-500">
                Kaynak: admin tarafinda egitilen current satis modelinin bulk prediction sonucu.
              </p>
            </div>
            <div class="rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-xs text-emerald-800">
              <p class="font-bold">Admin model dogrulandi</p>
              <p class="mt-1">
                {{ targetLabel(currentTargetState?.target_column || targetColumn) }}
                <span v-if="currentTargetState?.trained_at"> / {{ fmtDate(currentTargetState.trained_at) }}</span>
                <span v-if="currentTargetState?.metrics?.weighted_f1"> / F1 {{ fmtPct(currentTargetState.metrics.weighted_f1) }}</span>
              </p>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 gap-5 2xl:grid-cols-[minmax(0,1.25fr)_minmax(360px,0.75fr)]">
          <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white p-4">
            <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p class="text-sm font-bold text-slate-900">
                {{ filteredItems.length }} calisan icin {{ targetLabel(bulkResult.target_column) }}
              </p>
              <div class="relative">
                <svg class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
                <input
                  v-model="tableSearch"
                  type="text"
                  placeholder="Calisan ara..."
                  class="w-full rounded-xl border border-slate-200 py-2 pl-9 pr-4 text-sm text-slate-700 shadow-sm focus:outline-none sm:w-56"
                />
              </div>
            </div>
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-slate-200 text-sm">
                <thead>
                  <tr class="text-left text-slate-500">
                    <th class="pb-3 font-medium">Calisan</th>
                    <th class="pb-3 font-medium">Takim / Pozisyon</th>
                    <th class="pb-3 font-medium">Risk Durumu</th>
                    <th class="pb-3 font-medium">Risk Skoru</th>
                    <th class="pb-3 font-medium">KPI Trend</th>
                    <th class="pb-3 font-medium">Ana Sinyal</th>
                    <th class="pb-3 font-medium">Haftalik Odak</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                  <tr
                    v-for="person in filteredItems"
                    :key="person.employee_id"
                    class="cursor-pointer align-top transition hover:bg-indigo-50/50"
                    @click="openEmployeeAnalysis(person)"
                  >
                    <td class="py-3 pr-4">
                      <p class="font-semibold text-slate-900">{{ displayName(person) }}</p>
                      <p class="text-xs text-slate-500">{{ person.summary_payload?.external_employee_code || `Dataset #${person.employee_id}` }}</p>
                    </td>
                    <td class="py-3 pr-4 text-slate-600">{{ salesPersonRoleLabel(person) }}</td>
                    <td class="py-3 pr-4">
                      <span class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="bandClass(person.predicted_band, person.target_column)">
                        {{ bandLabel(person.predicted_band, person.target_column) }}
                      </span>
                    </td>
                    <td class="py-3 pr-4">
                      <div class="flex min-w-[120px] items-center gap-2">
                        <div class="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                          <div
                            class="h-full rounded-full"
                            :class="personRiskScore(person) >= 67 ? 'bg-rose-500' : personRiskScore(person) >= 34 ? 'bg-amber-400' : 'bg-emerald-500'"
                            :style="{ width: `${personRiskScore(person)}%` }"
                          ></div>
                        </div>
                        <span class="w-12 text-right font-bold text-slate-900">{{ personRiskScore(person) }}/100</span>
                      </div>
                    </td>
                    <td class="py-3 pr-4 text-slate-600">{{ salesEmployeeTrendLabel(person) }}</td>
                    <td class="py-3 pr-4 text-slate-600">{{ person.top_drivers?.[0]?.metric_name || 'KPI sinyali' }}</td>
                    <td class="py-3 text-slate-600">{{ person.recommended_actions?.[0] || 'KPI kirilimi incelenmeli.' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <aside class="rounded-2xl border border-indigo-100 bg-indigo-50 p-5">
            <template v-if="predResult">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-500">Secili Calisan</p>
                  <h4 class="mt-1 text-lg font-bold text-slate-900">{{ displayName(predResult) }}</h4>
                  <p class="mt-1 text-sm text-slate-600">{{ salesPersonRoleLabel(predResult) }}</p>
                </div>
                <span class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="bandClass(predResult.predicted_band, predResult.target_column)">
                  {{ bandLabel(predResult.predicted_band, predResult.target_column) }}
                </span>
              </div>

              <p class="mt-5 text-sm leading-6 text-slate-800">
                {{ predResult.narrative?.manager_summary || predResult.risk_summary }}
              </p>

              <div
                v-if="predResult.narrative?.risk_interpretation"
                class="mt-4 rounded-xl border border-indigo-200 bg-white p-4 text-sm leading-6 text-slate-700"
              >
                {{ predResult.narrative.risk_interpretation }}
              </div>

              <p class="mt-5 text-xs font-semibold uppercase tracking-[0.18em] text-indigo-500">Haftalik Manager Onerileri</p>
              <div class="mt-3 space-y-3">
                <div
                  v-for="action in salesActionPlan(predResult).slice(0, 3)"
                  :key="action.title"
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
                Secilen calisanin KPI yorumu, risk nedeni ve haftalik yonetici onerileri burada acilacak.
              </p>
            </template>
          </aside>
        </div>

        <div class="border-t border-slate-100 pt-5">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Oncelikli takip kartlari</p>
          <div class="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
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
                <p class="text-sm font-bold text-slate-900">{{ displayName(person) }}</p>
                <span class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="bandClass(person.predicted_band, person.target_column)">
                  {{ bandLabel(person.predicted_band, person.target_column) }}
                </span>
              </div>
              <p class="mt-2 text-xs text-slate-500">{{ salesPersonRoleLabel(person) }}</p>
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
      <div v-if="false" class="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Çalışan Listesi</p>
            <h4 class="mt-0.5 text-base font-bold text-slate-900">Tüm Tahminler
              <span class="ml-1.5 text-sm font-normal text-slate-400">· {{ filteredItems.length }} çalışan</span>
            </h4>
          </div>
          <div class="relative">
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
            <input v-model="tableSearch" type="text" placeholder="Çalışan ara…"
              class="rounded-xl border border-slate-200 pl-9 pr-4 py-2 text-sm text-slate-700 shadow-sm w-52 focus:outline-none"/>
          </div>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full text-sm">
            <thead>
              <tr class="bg-slate-50 border-b border-slate-100 text-xs font-semibold uppercase tracking-wider text-slate-400">
                <th class="px-6 py-3 text-left">Çalışan</th>
                <th class="px-6 py-3 text-left">Takım / Bölge</th>
                <th class="px-6 py-3 text-left">Tahmin</th>
                <th class="px-6 py-3 text-left">Güven</th>
                <th class="px-6 py-3 text-left">Ana Sinyal</th>
                <th class="px-6 py-3 text-left">Öneri</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-50">
              <tr v-for="item in filteredItems" :key="item.employee_id" class="hover:bg-slate-50/70 transition-colors">
                <td class="px-6 py-3.5 font-semibold text-slate-900">{{ displayName(item) }}</td>
                <td class="px-6 py-3.5 text-slate-500">{{ item.summary_payload?.region || item.summary_payload?.team || '—' }}</td>
                <td class="px-6 py-3.5">
                  <span class="rounded-full border px-2.5 py-0.5 text-xs font-semibold" :class="bandClass(item.predicted_band, item.target_column)">
                    {{ bandLabel(item.predicted_band, item.target_column) }}
                  </span>
                </td>
                <td class="px-6 py-3.5">
                  <div class="flex items-center gap-2">
                    <div class="w-16 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                      <div class="h-full rounded-full bg-emerald-500" :style="{ width: `${item.confidence * 100}%` }"/>
                    </div>
                    <span class="text-xs text-slate-600 tabular-nums">{{ Math.round(item.confidence * 100) }}%</span>
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

    <!-- ── Section: Teknik Detaylar ───────────────────────────── -->
    <template v-if="activeSection === 'technical'">
      <div v-if="!modelStates.some(s => s.is_trained)"
        class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center text-sm text-slate-500">
        Teknik detaylar icin admin tarafinda current satis modeli egitilmeli.
      </div>
      <template v-else>
        <div class="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Aktif Model Ozeti</p>
            <h4 class="mt-2 text-lg font-bold text-slate-900">{{ targetLabel(targetColumn) }}</h4>
            <p class="mt-2 text-sm leading-6 text-slate-500">
              Bu bolum kimin riskli oldugunu degil, ekrandaki tahminlerin hangi admin modeli ve dataset ile uretildigini gosterir.
            </p>
            <div class="mt-5 grid grid-cols-2 gap-3 text-sm">
              <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <p class="text-xs font-semibold text-slate-400">Durum</p>
                <p class="mt-1 font-bold" :class="currentTargetState ? 'text-emerald-700' : 'text-rose-700'">
                  {{ currentTargetState ? 'Current model hazir' : 'Current model yok' }}
                </p>
              </div>
              <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <p class="text-xs font-semibold text-slate-400">Model</p>
                <p class="mt-1 font-bold text-slate-900">{{ currentTargetState?.model_name || '-' }}</p>
              </div>
              <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <p class="text-xs font-semibold text-slate-400">Son Egitim</p>
                <p class="mt-1 font-bold text-slate-900">{{ fmtDate(currentTargetState?.trained_at) }}</p>
              </div>
              <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <p class="text-xs font-semibold text-slate-400">Prediction</p>
                <p class="mt-1 font-bold text-slate-900">{{ bulkResult?.prediction_count || 0 }} calisan</p>
              </div>
            </div>
          </section>

          <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Dataset ve Artifact Eslesmesi</p>
            <h4 class="mt-2 text-lg font-bold text-slate-900">Admin modeli bu dataset icin mi?</h4>
            <div class="mt-5 grid grid-cols-1 gap-3 md:grid-cols-3">
              <div v-for="item in technicalAuditCards" :key="item.label" class="rounded-xl border p-4" :class="item.toneClass">
                <p class="text-xs font-semibold uppercase tracking-[0.14em] opacity-70">{{ item.label }}</p>
                <p class="mt-2 text-xl font-black">{{ item.value }}</p>
                <p class="mt-2 text-xs leading-5">{{ item.hint }}</p>
              </div>
            </div>
          </section>
        </div>

        <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Target Bazli Model Performansi</p>
              <h4 class="mt-2 text-lg font-bold text-slate-900">4 hedefin egitim ve kalite durumu</h4>
            </div>
            <span class="w-fit rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
              {{ trainedCurrentTargetCount }}/{{ modelStates.length }} current target
            </span>
          </div>
          <div class="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div
              v-for="state in modelStates"
              :key="state.target_column"
              class="rounded-2xl border p-5"
              :class="state.is_trained ? state.is_current_dataset ? 'border-emerald-200 bg-emerald-50' : 'border-amber-200 bg-amber-50' : 'border-slate-200 bg-slate-50'"
            >
              <div class="flex items-start justify-between gap-3">
                <p class="text-sm font-bold leading-5 text-slate-900">{{ state.target_label }}</p>
                <span
                  class="rounded-full border bg-white px-2.5 py-1 text-xs font-semibold"
                  :class="state.is_trained ? state.is_current_dataset ? 'border-emerald-200 text-emerald-700' : 'border-amber-200 text-amber-700' : 'border-slate-200 text-slate-500'"
                >
                  {{ state.is_trained ? (state.is_current_dataset ? 'Current' : 'Eski') : 'Yok' }}
                </span>
              </div>
              <div class="mt-4 space-y-2 text-xs">
                <div class="flex justify-between gap-3"><span class="text-slate-500">Model</span><span class="font-semibold text-slate-800">{{ state.model_name || '-' }}</span></div>
                <div class="flex justify-between gap-3"><span class="text-slate-500">Weighted F1</span><span class="font-bold text-slate-900">{{ fmtPct(state.metrics?.weighted_f1) }}</span></div>
                <div class="flex justify-between gap-3"><span class="text-slate-500">Accuracy</span><span class="font-semibold text-slate-800">{{ fmtPct(state.metrics?.accuracy) }}</span></div>
                <div class="flex justify-between gap-3"><span class="text-slate-500">Train / Test</span><span class="font-semibold text-slate-800">{{ state.train_count || '-' }} / {{ state.test_count || '-' }}</span></div>
                <div class="flex justify-between gap-3"><span class="text-slate-500">Son egitim</span><span class="font-semibold text-slate-800">{{ fmtDate(state.trained_at) }}</span></div>
              </div>
            </div>
          </div>
        </section>

        <section class="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
          <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">KPI Driver Ozeti</p>
            <h4 class="mt-2 text-lg font-bold text-slate-900">Tahminleri en cok tasiyan sinyaller</h4>
            <div v-if="technicalDriverRows.length" class="mt-5 space-y-4">
              <div v-for="row in technicalDriverRows" :key="row.name">
                <div class="mb-1 flex items-center justify-between gap-3 text-sm">
                  <span class="font-semibold text-slate-800">{{ row.name }}</span>
                  <span class="text-xs font-bold text-slate-500">{{ row.count }} calisan</span>
                </div>
                <div class="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div class="h-full rounded-full bg-indigo-500" :style="{ width: `${row.width}%` }"></div>
                </div>
              </div>
            </div>
            <p v-else class="mt-5 rounded-xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
              Driver dagilimi icin once Toplu Tara calistirilmali.
            </p>
          </div>

          <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Model Uyarilari</p>
            <h4 class="mt-2 text-lg font-bold text-slate-900">Guven ve veri kalitesi kontrolu</h4>
            <div class="mt-5 space-y-3">
              <div v-for="warning in technicalWarnings" :key="warning.title" class="rounded-xl border p-4" :class="warning.toneClass">
                <p class="text-sm font-bold">{{ warning.title }}</p>
                <p class="mt-1 text-xs leading-5">{{ warning.body }}</p>
              </div>
            </div>
          </div>
        </section>

        <details class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <summary class="cursor-pointer text-sm font-semibold text-slate-700">
            Ham prediction denetim tablosunu goster
          </summary>
          <div v-if="bulkResult" class="mt-5 overflow-x-auto">
            <table class="min-w-full divide-y divide-slate-200 text-sm">
              <thead>
                <tr class="text-left text-slate-500">
                  <th class="pb-3 font-medium">Calisan</th>
                  <th class="pb-3 font-medium">Takim / Rol</th>
                  <th class="pb-3 font-medium">Sonuc</th>
                  <th class="pb-3 font-medium">Guven</th>
                  <th class="pb-3 font-medium">Risk Skoru</th>
                  <th class="pb-3 font-medium">Ana Sinyal</th>
                  <th class="pb-3 font-medium">Neden</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr v-for="item in bulkResult.items" :key="item.employee_id" class="align-top">
                  <td class="py-3 pr-4 font-semibold text-slate-900">
                    {{ displayName(item) }}
                    <div class="text-xs text-slate-500">{{ item.summary_payload?.external_employee_code || `Dataset #${item.employee_id}` }}</div>
                  </td>
                  <td class="py-3 pr-4 text-slate-600">{{ salesPersonRoleLabel(item) }}</td>
                  <td class="py-3 pr-4">
                    <span class="rounded-full border px-2.5 py-1 text-xs font-semibold" :class="bandClass(item.predicted_band, item.target_column)">
                      {{ bandLabel(item.predicted_band, item.target_column) }}
                    </span>
                  </td>
                  <td class="py-3 pr-4 font-semibold text-slate-900">{{ fmtPct(item.confidence) }}</td>
                  <td class="py-3 pr-4 font-semibold text-slate-900">{{ personRiskScore(item) }}/100</td>
                  <td class="py-3 pr-4 text-slate-600">{{ item.top_drivers?.[0]?.metric_name || '-' }}</td>
                  <td class="py-3 text-slate-600">{{ item.top_drivers?.[0]?.threshold_status || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="mt-4 rounded-xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
            Ham prediction tablosu icin once Toplu Tara calistirilmali.
          </p>
        </details>
      </template>
    </template>

    <template v-if="false && activeSection === 'technical'">
      <div v-if="!modelStates.some(s => s.is_trained)"
        class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center text-sm text-slate-500">
        Teknik detaylar icin admin tarafinda current satis modeli egitilmeli.
      </div>
      <template v-else>
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          <div v-for="state in modelStates.filter(s => s.is_trained)" :key="state.target_column"
            class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p class="text-xs font-semibold text-slate-500 mb-2">{{ state.target_label }}</p>
            <div class="space-y-2 text-xs">
              <div class="flex justify-between"><span class="text-slate-400">Model</span><span class="font-semibold text-slate-700">{{ state.model_name || '—' }}</span></div>
              <div class="flex justify-between"><span class="text-slate-400">Weighted F1</span><span class="font-bold text-emerald-700">{{ fmtPct(state.metrics?.weighted_f1) }}</span></div>
              <div class="flex justify-between"><span class="text-slate-400">Accuracy</span><span class="font-semibold text-slate-700">{{ fmtPct(state.metrics?.accuracy) }}</span></div>
              <div class="flex justify-between"><span class="text-slate-400">Train</span><span class="font-semibold text-slate-700">{{ state.train_count || '—' }}</span></div>
              <div class="flex justify-between"><span class="text-slate-400">Test</span><span class="font-semibold text-slate-700">{{ state.test_count || '—' }}</span></div>
              <div class="flex justify-between"><span class="text-slate-400">Son eğitim</span><span class="font-semibold text-slate-700">{{ fmtDate(state.trained_at) }}</span></div>
            </div>
          </div>
        </div>
        <div v-if="false" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 mb-4">En Önemli Özellikler</p>
          <div class="space-y-3">
            <div v-for="(feat, idx) in (trainResult?.top_features || []).slice(0, 10)" :key="idx">
              <div class="flex items-center justify-between text-xs mb-1">
                <span class="font-semibold text-slate-700 truncate max-w-[60%]">{{ feat.feature || feat.name || `Özellik ${(idx as number) + 1}` }}</span>
                <span class="text-slate-400 tabular-nums">{{ typeof feat.importance === 'number' ? feat.importance.toFixed(4) : feat.importance }}</span>
              </div>
              <div class="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div class="h-full rounded-full bg-indigo-500"
                  :style="{ width: `${Math.min(100, (feat.importance / ((trainResult?.top_features || [])[0]?.importance || 1)) * 100)}%` }"></div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </template>

    <!-- ── Loading overlay ────────────────────────────────────── -->
    <div v-if="mlLoading" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/25 backdrop-blur-sm">
      <div class="rounded-2xl bg-white p-8 shadow-2xl border border-slate-200 text-center w-full max-w-xs mx-4">
        <div class="mx-auto h-12 w-12 rounded-full border-4 border-slate-100 border-t-emerald-600 animate-spin"/>
        <p class="mt-5 text-base font-bold text-slate-900">
          {{ mlLoading === 'train' ? 'Model eğitiliyor…'
           : mlLoading === 'predict' ? 'Tahmin hesaplanıyor…'
           : mlLoading === 'narrative' ? 'AI yorumu oluşturuluyor…'
           : 'Toplu analiz çalışıyor…' }}
        </p>
        <p class="mt-1.5 text-sm text-slate-400">Bu işlem birkaç saniye sürebilir.</p>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  analyticsApi,
  type DepartmentAnalyticsOverviewResponse,
  type SalesBulkPredictionResponse,
  type SalesModelStateResponse,
  type SalesModelTrainResponse,
  type SalesPredictionResponse,
  type SalesTargetColumn,
  type SoftwareDatasetEmployeeResponse,
  type SoftwareDatasetResponse,
  type TeamAnalyticsSnapshotResponse,
} from '@/services/api/analytics.api'

const route = useRoute()

// ── Section navigation ──────────────────────────────────────────
const activeSection = computed(() => {
  const section = (route.query.section as string) || 'department'
  return section === 'model' ? 'department' : section
})

const SECTION_META: Record<string, { eyebrow: string; title: string; description: string; action?: string; onAction: () => void }> = {
  model: {
    eyebrow: 'Model Durumu',
    title: 'Satış risk tahmini — aktif model durumu',
    description: 'Dataset seçin ve hedef değişkeni belirleyin. "Model Eğit" ile stacking ensemble çalıştırın, ardından bireysel veya toplu tahmin alın.',
    onAction: () => {},
  },
  department: {
    eyebrow: 'Departman Analizi',
    title: 'Satış departmanı KPI omurgası ve takım özeti',
    description: 'Normalize edilmiş KPI skorları, takım karşılaştırması ve analytics mimarisi katmanlarını inceleyin.',
    onAction: () => {},
  },
  teams: {
    eyebrow: 'Takım Analizi',
    title: 'Takımlar arası karşılaştırma ve risk dağılımı',
    description: 'Kurumsal Satış, Bireysel Satış ve Müşteri Başarısı takımlarını risk yoğunluğuna göre karşılaştırın.',
    action: 'Takımları Tara',
    onAction: () => runBulk(false),
  },
  watchlist: {
    eyebrow: 'Çalışan Analizi',
    title: 'Çalışan bazlı risk profilleri',
    description: 'Toplu tahmin sonuçlarını filtreleyin, yüksek riskli çalışanları tespit edin ve aksiyon önceliklerini belirleyin.',
    action: 'Toplu Tara',
    onAction: () => runBulk(false),
  },
  technical: {
    eyebrow: 'Teknik Detaylar',
    title: 'Model metrikleri ve özellik önem sıralaması',
    description: 'Her hedef için Weighted F1, Accuracy, train/test ayrımı ve en önemli KPI özelliklerini inceleyin.',
    onAction: () => {},
  },
}

const activeMeta = computed(() => SECTION_META[activeSection.value] || SECTION_META.model)

// ── Targets ─────────────────────────────────────────────────────
const TARGETS: { value: SalesTargetColumn; label: string }[] = [
  { value: 'Performance_Drop_Target', label: 'Performans Düşüşü' },
  { value: 'Burnout_Target', label: 'Tükenmişlik' },
  { value: 'Resignation_Target', label: 'İstifa Riski' },
  { value: 'High_Risk_Target', label: 'Yüksek Risk' },
]

// ── State ────────────────────────────────────────────────────────
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
const mlLoading = ref<string | null>(null)
const mlError = ref<string | null>(null)
const tableSearch = ref('')
const selectedTeam = ref<string | null>(null)

// ── Computed ────────────────────────────────────────────────────
const deptNarrative = computed(() => bulkResult.value?.department_narrative || null)

const currentTargetState = computed(() =>
  modelStates.value.find((state) =>
    state.target_column === targetColumn.value
    && state.is_trained
    && state.is_current_dataset
  ) || null
)

const hasAdminCurrentModel = computed(() => Boolean(currentTargetState.value))

const teamRows = computed(() => {
  const analytics = bulkResult.value?.team_analytics
  if (!analytics?.length) return []
  return analytics.map((ta: any) => ({
    team: ta.team as string,
    avgRisk: Math.round((ta.high_risk_rate ?? 0) * 100),
    riskScore: Math.round(ta.risk_score ?? 0),
    highCount: ta.high_risk_count ?? 0,
    mediumCount: ta.medium_risk_count ?? 0,
    lowCount: ta.low_risk_count ?? 0,
    total: ta.employee_count ?? 0,
    topReason: ta.top_reason || 'KPI sinyali',
    roleCounts: ta.role_counts || {},
    trendValues: Array.isArray(ta.trend_values) ? ta.trend_values.map((v: any) => Math.round(Number(v) || 0)) : [],
    trendPeriods: Array.isArray(ta.trend_periods) ? ta.trend_periods : [],
    salesPressureScore: Math.round(ta.sales_pressure_score ?? 0),
    pipelinePressureScore: Math.round(ta.pipeline_pressure_score ?? 0),
  }))
})

const selectedTeamRow = computed(() => teamRows.value.find((row) => row.team === selectedTeam.value) || teamRows.value[0] || null)

const selectedTeamPeople = computed(() => {
  if (!selectedTeam.value || !bulkResult.value) return []
  const selectedKey = normalizeSalesTeamKey(selectedTeam.value)
  return bulkResult.value.items.filter((i: SalesPredictionResponse) =>
    normalizeSalesTeamKey(salesItemTeamName(i)) === selectedKey
  )
})

const selectedTeamNarrative = computed(() =>
  (bulkResult.value?.team_narratives || []).find((item: any) => item.team === selectedTeam.value) || null
)

const selectedTeamMonitorRate = computed(() => {
  if (!selectedTeamRow.value?.total) return 0
  return Math.round(((selectedTeamRow.value.highCount + selectedTeamRow.value.mediumCount) / selectedTeamRow.value.total) * 100)
})

const selectedTeamHighWidth = computed(() => {
  if (!selectedTeamRow.value?.total) return 0
  return Math.round((selectedTeamRow.value.highCount / selectedTeamRow.value.total) * 100)
})

const selectedTeamMediumWidth = computed(() => {
  if (!selectedTeamRow.value?.total) return 0
  return Math.round((selectedTeamRow.value.mediumCount / selectedTeamRow.value.total) * 100)
})

const selectedTeamPressureScore = computed(() =>
  Math.max(selectedTeamRow.value?.salesPressureScore || 0, selectedTeamRow.value?.pipelinePressureScore || 0)
)

const selectedTeamRoleMix = computed(() => {
  const counts = selectedTeamRow.value?.roleCounts || {}
  const entries = Object.entries(counts).sort((a, b) => Number(b[1]) - Number(a[1]))
  if (!entries.length && selectedTeamPeople.value.length) {
    const personRoleCounts: Record<string, number> = {}
    selectedTeamPeople.value.forEach((person) => {
      const role = String(person.summary_payload?.position || person.summary_payload?.role || 'Rol yok')
      personRoleCounts[role] = (personRoleCounts[role] || 0) + 1
    })
    return Object.entries(personRoleCounts)
      .sort((a, b) => Number(b[1]) - Number(a[1]))
      .slice(0, 2)
      .map(([role, count]) => `${count} ${role}`)
      .join(', ')
  }
  if (!entries.length) return 'Rol dagilimi dataset profilinden okunur'
  return entries.slice(0, 2).map(([role, count]) => `${count} ${role}`).join(', ')
})

const selectedTeamMetricCards = computed(() => {
  const row = selectedTeamRow.value
  if (!row) return []
  return [
    {
      index: '01',
      group: 'Takim',
      label: 'Toplam Kisi',
      value: `${row.total} kisi`,
      hint: selectedTeamRoleMix.value,
      indexClass: 'bg-blue-50 text-blue-700',
      valueClass: 'text-slate-950',
    },
    {
      index: '02',
      group: 'Model',
      label: 'Takim Riski',
      value: `${row.highCount + row.mediumCount} / ${row.total}`,
      hint: `%${selectedTeamMonitorRate.value} izleme orani`,
      indexClass: 'bg-rose-50 text-rose-700',
      valueClass: 'text-rose-600',
    },
    {
      index: '03',
      group: 'Alarm',
      label: 'Yuksek Riskli',
      value: `${row.highCount} kisi`,
      hint: row.highCount ? 'Haftalik takip gerekli' : 'Kritik sinyal yok',
      indexClass: 'bg-red-50 text-red-700',
      valueClass: 'text-red-600',
    },
    {
      index: '04',
      group: 'Satis',
      label: 'Pipeline / Hedef Baskisi',
      value: `${selectedTeamPressureScore.value}/100`,
      hint: selectedTeamPressureScore.value >= 70 ? 'Yuksek baski' : selectedTeamPressureScore.value >= 45 ? 'Kontrollu baski' : 'Dengeli',
      indexClass: 'bg-amber-50 text-amber-700',
      valueClass: 'text-amber-600',
    },
  ]
})

const selectedTeamProblemDescription = computed(() => {
  const row = selectedTeamRow.value
  if (!row) return ''
  const pressure = selectedTeamPressureScore.value >= 70
    ? 'pipeline, takip disiplini ve hedef baskisi birlikte yuksek gorunuyor'
    : 'model sinyali takim icinde odakli takip gerektiriyor'
  return `${row.team} icin admin ensemble modeli ${row.riskScore}/100 takim risk skoru uretti. Ana sinyal ${row.topReason}; ${pressure}. Bu okuma satis KPI registry esikleri, son donem tahminleri ve 6 aylik takim trendinden gelir.`
})

const selectedTeamTrendValues = computed(() => selectedTeamRow.value?.trendValues?.length ? selectedTeamRow.value.trendValues : [0])

const selectedTeamTrendChangeLabel = computed(() => {
  const values = selectedTeamTrendValues.value
  if (values.length < 2) return 'Trend yeni olusuyor'
  const diff = values[values.length - 1] - values[0]
  if (diff > 0) return `+${diff} puan son 6 ayda`
  if (diff < 0) return `${diff} puan son 6 ayda`
  return 'Degisim yok'
})

const selectedTeamTrendCirclePoints = computed(() => {
  const values = selectedTeamTrendValues.value
  const step = values.length > 1 ? 540 / (values.length - 1) : 0
  return values.map((value: number, index: number) => ({
    x: 35 + index * step,
    y: trendY(value),
  }))
})

const selectedTeamTrendPoints = computed(() =>
  selectedTeamTrendCirclePoints.value.map((point: { x: number; y: number }) => `${point.x},${point.y}`).join(' ')
)

const selectedTeamPerformanceValues = computed(() =>
  selectedTeamTrendValues.value.map((value: number) => Math.max(0, Math.min(100, 100 - value)))
)

const selectedTeamPerformanceChangeLabel = computed(() => {
  const values = selectedTeamPerformanceValues.value
  if (values.length < 2) return 'Trend yeni olusuyor'
  const diff = values[values.length - 1] - values[0]
  if (diff > 0) return `+${diff} puan son 6 ayda`
  if (diff < 0) return `${diff} puan son 6 ayda`
  return 'Degisim yok'
})

const selectedTeamPerformanceCirclePoints = computed(() => {
  const values = selectedTeamPerformanceValues.value
  const step = values.length > 1 ? 540 / (values.length - 1) : 0
  return values.map((value: number, index: number) => ({
    x: 35 + index * step,
    y: trendY(value),
  }))
})

const selectedTeamPerformanceTrendPoints = computed(() =>
  selectedTeamPerformanceCirclePoints.value.map((point: { x: number; y: number }) => `${point.x},${point.y}`).join(' ')
)

const selectedTeamSalesActions = computed(() => {
  const row = selectedTeamRow.value
  if (!row) return []
  const reason = row.topReason
  return [
    {
      title: `${reason} icin haftalik takip ritmi kur`,
      reason: `${row.team} icinde ${row.highCount} yuksek riskli kisi var; once bu sinyalin hedef, pipeline veya takip disiplini kaynakli olup olmadigi netlestirilmeli.`,
    },
    {
      title: 'Pipeline ve hedef baskisini birlikte oku',
      reason: `Pipeline/hedef baskisi ${selectedTeamPressureScore.value}/100. Dusuk pipeline sagligi, geciken takipler ve is yuku ayni ekipte birikiyorsa aksiyon onceligi artar.`,
    },
    {
      title: 'Kisi bazli gorusmeleri ana driver ile ac',
      reason: 'Takim uyesi kartlarindaki ana sinyal, manager gorusmesinde genel performans yorumu yerine somut satis KPI konusu olarak kullanilmali.',
    },
  ]
})

const selectedTeamTalkingPointItems = computed(() => {
  const row = selectedTeamRow.value
  if (!row) return []
  const pressure = selectedTeamPressureScore.value
  const riskLabel = `${row.highCount} yuksek, ${row.mediumCount} orta riskli kisi`
  const people = [...selectedTeamPeople.value].sort((a, b) => personRiskScore(b) - personRiskScore(a))
  const highPeople = people.filter((person) => personRiskScore(person) >= 70)
  const topPeople = highPeople.slice(0, 3)
  const driverCounts: Record<string, number> = {}
  people.forEach((person) => {
    const driver = String(person.top_drivers?.[0]?.metric_name || row.topReason || 'KPI sinyali')
    driverCounts[driver] = (driverCounts[driver] || 0) + 1
  })
  const driverEntries = Object.entries(driverCounts).sort((a, b) => b[1] - a[1])
  const mainDriver = driverEntries[0]?.[0] || row.topReason || 'KPI sinyali'
  const secondDriver = driverEntries.find(([driver]) => driver !== mainDriver)?.[0]
  const trendValues = selectedTeamTrendValues.value
  const trendDiff = trendValues.length > 1 ? trendValues[trendValues.length - 1] - trendValues[0] : 0
  const trendText = trendDiff > 0 ? `son 6 ayda risk ${trendDiff} puan artmis` : trendDiff < 0 ? `son 6 ayda risk ${Math.abs(trendDiff)} puan azalmis` : 'son 6 ayda risk yatay'
  const items = [
    {
      id: 'driver',
      index: '01',
      title: `${mainDriver} sinyalini kisi bazinda ayristir`,
      priority: row.highCount ? 'Yuksek' : 'Orta',
      badgeClass: row.highCount ? 'bg-rose-50 text-rose-700' : 'bg-amber-50 text-amber-700',
      detail: `${row.team} icin admin modeli ${row.riskScore}/100 takim risk skoru uretti; dagilim ${riskLabel}. En cok tekrar eden driver ${mainDriver}${secondDriver ? `, ikinci sinyal ${secondDriver}` : ''}. Bu haftaki gorusmede driver'i genel yorum olarak degil, kisi/hesap/teklif davranisina bagla.`,
      bullets: [
        topPeople.length ? `Once ${topPeople.map((person) => displayName(person)).join(', ')} icin ayni sinyalin neden tekrar ettigini kontrol et.` : 'Yuksek riskli kisi yoksa orta riskli kisilerde erken uyari sinyalini kontrol et.',
        secondDriver ? `${mainDriver} ve ${secondDriver} ayni kisilerde mi, farkli alt gruplarda mi ayrisiyor?` : 'Tek ana driver yogunsa sebebi bireysel performans mi, bolge/pipeline kosulu mu ayristir.',
      ],
    },
  ]

  if (pressure >= 45 || mainDriver.toLowerCase().includes('pipeline') || mainDriver.toLowerCase().includes('takip') || mainDriver.toLowerCase().includes('crm')) {
    items.push({
      id: 'pipeline',
      index: String(items.length + 1).padStart(2, '0'),
      title: 'Pipeline, hedef ve takip disiplini dengelemesi',
      priority: pressure >= 70 ? 'Kritik' : pressure >= 45 ? 'Izleme' : 'Normal',
      badgeClass: pressure >= 70 ? 'bg-rose-50 text-rose-700' : pressure >= 45 ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700',
      detail: `Pipeline/hedef baskisi ${pressure}/100. Bu skor pipeline sagligi, pipeline yasi, takip disiplini ve CRM disiplininden uretilen takim baski okumasidir.`,
      bullets: [
        'Acil kapanis baskisi ile yeni firsat uretimi dengede mi?',
        'Geciken follow-up veya eksik CRM kaydi tahmin riskini buyutuyor mu?',
      ],
    })
  }

  if (trendDiff >= 3 || trendDiff <= -3) {
    items.push({
      id: 'trend',
      index: String(items.length + 1).padStart(2, '0'),
      title: '6 aylik trendin yonunu haftalik plana cevir',
      priority: trendDiff > 0 ? 'Risk artisi' : 'Iyilesme',
      badgeClass: trendDiff > 0 ? 'bg-rose-50 text-rose-700' : 'bg-emerald-50 text-emerald-700',
      detail: `${row.team} icin ${trendText}. Bu trend sadece bu haftanin sonucu degil, admin modelinin aylik takim risk serisinden okunuyor.`,
      bullets: [
        trendDiff > 0 ? 'Risk artisinin hangi ayda kirildigini ve o donemdeki pipeline/aktivite degisimini kontrol et.' : 'Iyilesen sinyali hangi davranisin tasidigini bulup takim geneline yay.',
        'Trend yorumu ile bu haftaki kisi gorusmelerini ayni driver uzerinden bagla.',
      ],
    })
  }

  items.push({
      id: 'people',
      index: String(items.length + 1).padStart(2, '0'),
      title: topPeople.length ? `${topPeople.length} oncelikli kisi icin satis destek plani` : 'Takim icin erken uyari kontrolu',
      priority: row.highCount ? 'Ilk 48 saat' : 'Bu hafta',
      badgeClass: row.highCount ? 'bg-blue-50 text-blue-700' : 'bg-slate-100 text-slate-600',
      detail: topPeople.length
        ? `Oncelik ${topPeople.map((person) => `${displayName(person)} (${personRiskScore(person)}/100)`).join(', ')}. Amac performans etiketi koymak degil, her kisi icin satis engelini ve destek ihtiyacini netlestirmek.`
        : 'Yuksek riskli kisi yoksa, orta risk sinyali bulunan kisilerde erken destek ihtiyacini kontrol et.',
      bullets: [
        'Her riskli kisi icin tek bir haftalik hedef, sahip ve kontrol tarihi belirle.',
        `Gorusme acilisinda ana driver olarak ${mainDriver} kullanilsin; farkli driver varsa kisiye gore ayrilsin.`,
      ],
  })

  return items
})

const filteredItems = computed(() => {
  const q = tableSearch.value.trim().toLowerCase()
  if (!bulkResult.value) return []
  return bulkResult.value.items.filter((i: SalesPredictionResponse) =>
    !q
    || displayName(i).toLowerCase().includes(q)
    || salesPersonRoleLabel(i).toLowerCase().includes(q)
    || String(i.summary_payload?.external_employee_code || '').toLowerCase().includes(q)
  )
})

const riskyPeople = computed(() =>
  [...(bulkResult.value?.items || [])]
    .sort((a, b) => personRiskScore(b) - personRiskScore(a))
    .slice(0, 4)
)

const trainedCurrentTargetCount = computed(() =>
  modelStates.value.filter((state) => state.is_trained && state.is_current_dataset).length
)

const selectedDataset = computed(() =>
  datasets.value.find((dataset) => dataset.id === uploadId.value) || null
)

const technicalAuditCards = computed(() => {
  const current = currentTargetState.value
  const predictionCount = bulkResult.value?.prediction_count || 0
  const datasetCount = datasetEmployees.value.length
  const countsMatch = predictionCount > 0 && datasetCount > 0 && predictionCount === datasetCount

  return [
    {
      label: 'Dataset',
      value: selectedDataset.value ? `#${selectedDataset.value.id}` : '-',
      hint: selectedDataset.value?.file_name || 'Secili dataset bulunamadi.',
      toneClass: selectedDataset.value
        ? 'border-slate-200 bg-slate-50 text-slate-800'
        : 'border-rose-200 bg-rose-50 text-rose-800',
    },
    {
      label: 'Artifact',
      value: current?.is_current_dataset ? 'Eslesiyor' : 'Eslesmiyor',
      hint: current?.is_current_dataset
        ? 'Backend tahmin endpointleri bu upload ile egitilmis current artifact ister.'
        : 'Bu target icin admin current modeli secili dataset ile eslesmiyor.',
      toneClass: current?.is_current_dataset
        ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
        : 'border-rose-200 bg-rose-50 text-rose-800',
    },
    {
      label: 'Kapsam',
      value: predictionCount ? `${predictionCount}/${datasetCount || '?'}` : 'Bekliyor',
      hint: countsMatch
        ? 'Prediction sayisi dataset calisan sayisiyla eslesiyor.'
        : 'Kapsam kontrolu icin Toplu Tara sonucu dataset calisan sayisiyla karsilastirilir.',
      toneClass: countsMatch
        ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
        : 'border-amber-200 bg-amber-50 text-amber-800',
    },
  ]
})

const technicalDriverRows = computed(() => {
  const counts: Record<string, number> = {}
  ;(bulkResult.value?.items || []).forEach((item) => {
    const driver = String(item.top_drivers?.[0]?.metric_name || item.top_features?.[0]?.feature || 'KPI sinyali')
    counts[driver] = (counts[driver] || 0) + 1
  })
  const max = Math.max(...Object.values(counts), 1)
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([name, count]) => ({
      name,
      count,
      width: Math.max(8, Math.round((count / max) * 100)),
    }))
})

const technicalWarnings = computed(() => {
  const warnings: Array<{ title: string; body: string; toneClass: string }> = []
  const current = currentTargetState.value
  const predictionCount = bulkResult.value?.prediction_count || 0
  const datasetCount = datasetEmployees.value.length
  const lowConfidenceCount = (bulkResult.value?.items || []).filter((item) => item.confidence < 0.65).length
  const staleTargets = modelStates.value.filter((state) => state.is_trained && !state.is_current_dataset)
  const untrainedTargets = modelStates.value.filter((state) => !state.is_trained)

  if (!current) {
    warnings.push({
      title: 'Current model eksik',
      body: 'Secili target icin admin tarafinda bu dataset ile eslesen current model yok. Tahmin ekranlari bu durumda calismamali.',
      toneClass: 'border-rose-200 bg-rose-50 text-rose-800',
    })
  } else {
    warnings.push({
      title: 'Current model korumasi aktif',
      body: 'Backend tahmin endpointleri artifact upload_id ile secili dataset upload_id eslesmesini zorunlu tutuyor.',
      toneClass: 'border-emerald-200 bg-emerald-50 text-emerald-800',
    })
  }

  if (!predictionCount) {
    warnings.push({
      title: 'Bulk prediction bekleniyor',
      body: 'Driver dagilimi, risk skoru kapsami ve ham denetim tablosu icin Toplu Tara calistirilmali.',
      toneClass: 'border-amber-200 bg-amber-50 text-amber-800',
    })
  } else if (datasetCount && predictionCount !== datasetCount) {
    warnings.push({
      title: 'Kapsam farki var',
      body: `Dataset ${datasetCount} calisan iceriyor, bulk prediction ${predictionCount} calisan dondu. Employee id eslesmeleri kontrol edilmeli.`,
      toneClass: 'border-amber-200 bg-amber-50 text-amber-800',
    })
  } else {
    warnings.push({
      title: 'Prediction kapsami tutarli',
      body: `${predictionCount} calisan icin admin modelinden bulk prediction uretildi.`,
      toneClass: 'border-emerald-200 bg-emerald-50 text-emerald-800',
    })
  }

  if (lowConfidenceCount > 0) {
    warnings.push({
      title: 'Dusuk guvenli tahminler',
      body: `${lowConfidenceCount} calisanin confidence degeri %65 altinda. Bu kisilerde karar yerine ek veri ve manager gorusmesi tercih edilmeli.`,
      toneClass: 'border-amber-200 bg-amber-50 text-amber-800',
    })
  }

  if (staleTargets.length || untrainedTargets.length) {
    warnings.push({
      title: 'Tum hedefler esit hazir degil',
      body: `${staleTargets.length} hedef eski dataset modelinde, ${untrainedTargets.length} hedef egitimsiz gorunuyor.`,
      toneClass: 'border-amber-200 bg-amber-50 text-amber-800',
    })
  }

  return warnings
})

// ── Chart helpers (Departman section) ───────────────────────────
const deptChartW = computed(() => Math.max(460, 42 + (overview.value?.team_summaries.length ?? 1) * 110 + 40))

function dBarX(i: number): number {
  const teams = overview.value?.team_summaries.length ?? 1
  const spacing = (deptChartW.value - 42 - 40) / teams
  return 42 + i * spacing + spacing / 2 - 28
}

function dYPos(val: number): number {
  return 20 + 190 * (1 - val / 130)
}

function dTrendY(team: TeamAnalyticsSnapshotResponse): number {
  const delta = team.average_trend_delta ?? 0
  return dYPos(Math.max(0, Math.min(130, team.average_score + delta * 5)))
}

const dTrendPts = computed(() => {
  const teams = overview.value?.team_summaries ?? []
  if (teams.length < 2) return ''
  return teams.map((t: TeamAnalyticsSnapshotResponse, i: number) => `${dBarX(i) + 28},${dTrendY(t)}`).join(' ')
})

// ── API calls ────────────────────────────────────────────────────
async function loadDatasets() {
  try {
    datasets.value = await analyticsApi.getSalesDatasets()
    if (datasets.value.length) {
      let selectedDataset = datasets.value[0]
      for (const dataset of datasets.value) {
        const states = await analyticsApi.getSalesModelState(dataset.id).catch(() => [])
        if (states.some((state) => state.is_trained && state.is_current_dataset)) {
          selectedDataset = dataset
          break
        }
      }
      uploadId.value = selectedDataset.id
      await onDatasetChange()
    }
  } catch {}
}

async function loadOverview() {
  try {
    overview.value = await analyticsApi.getDepartmentOverview('sales')
  } catch {}
}

async function onDatasetChange() {
  if (!uploadId.value) return
  datasetEmployees.value = []
  modelStates.value = []
  predResult.value = null
  bulkResult.value = null
  try {
    const [employees, states] = await Promise.all([
      analyticsApi.getSalesDatasetEmployees(uploadId.value),
      analyticsApi.getSalesModelState(uploadId.value),
    ])
    datasetEmployees.value = employees
    modelStates.value = states
    if (employees.length) employeeId.value = employees[0].employee_id
  } catch {}
}

async function trainModel() {
  if (!uploadId.value) return
  mlLoading.value = 'train'
  mlError.value = null
  try {
    trainResult.value = await analyticsApi.trainSalesModel({ upload_id: uploadId.value, target_column: targetColumn.value })
    modelStates.value = await analyticsApi.getSalesModelState(uploadId.value)
  } catch (e: any) {
    mlError.value = e?.response?.data?.detail || e?.message || 'Eğitim hatası'
  } finally {
    mlLoading.value = null
  }
}

async function runPredict() {
  if (!uploadId.value || !employeeId.value) return
  if (!hasAdminCurrentModel.value) {
    mlError.value = "Admin tarafinda bu satis dataset'i icin current egitilmis model bulunamadi."
    return
  }
  mlLoading.value = 'predict'
  mlError.value = null
  try {
    predResult.value = await analyticsApi.getLatestSalesPrediction({
      upload_id: uploadId.value,
      employee_id: employeeId.value,
      target_column: targetColumn.value,
    })
  } catch (e: any) {
    mlError.value = e?.response?.data?.detail || e?.message || 'Tahmin hatası'
  } finally {
    mlLoading.value = null
  }
}

async function openEmployeeAnalysis(person: SalesPredictionResponse) {
  if (!uploadId.value || !hasAdminCurrentModel.value) return
  const employeeIdNum = Number(person.employee_id)
  employeeId.value = employeeIdNum
  predResult.value = person
  mlError.value = null

  try {
    predResult.value = await analyticsApi.getLatestSalesPrediction({
      upload_id: uploadId.value,
      employee_id: employeeIdNum,
      target_column: targetColumn.value,
    })
  } catch (e: any) {
    mlError.value = e?.response?.data?.detail || e?.message || 'Calisan detayi alinamadi'
  }
}

async function runBulk(withNarrative: boolean) {
  if (!uploadId.value) return
  if (!hasAdminCurrentModel.value) {
    mlError.value = "Admin tarafinda bu satis dataset'i icin current egitilmis model bulunamadi."
    return
  }
  mlLoading.value = withNarrative ? 'narrative' : 'bulk'
  mlError.value = null
  try {
    bulkResult.value = await analyticsApi.getBulkSalesPredictions({
      upload_id: uploadId.value,
      target_column: targetColumn.value,
      use_llm_narrative: withNarrative,
    })
    if (teamRows.value.length) selectedTeam.value = teamRows.value[0].team
    if (bulkResult.value.items.length) predResult.value = bulkResult.value.items[0]
  } catch (e: any) {
    mlError.value = e?.response?.data?.detail || e?.message || 'Toplu tahmin hatası'
  } finally {
    mlLoading.value = null
  }
}

// ── Helpers ──────────────────────────────────────────────────────
function trendY(value: number): number {
  const bounded = Math.max(0, Math.min(100, Number(value) || 0))
  return 200 - bounded * 1.8
}

function teamRiskLabel(row: { riskScore: number; highCount: number; mediumCount: number }): string {
  if (row.riskScore >= 70 || row.highCount > 0) return 'Yuksek Risk'
  if (row.riskScore >= 45 || row.mediumCount > 0) return 'Izlemede'
  return 'Stabil'
}

function teamDotClass(row: { riskScore: number; highCount: number; mediumCount: number }): string {
  if (row.riskScore >= 70 || row.highCount > 0) return 'bg-rose-500'
  if (row.riskScore >= 45 || row.mediumCount > 0) return 'bg-amber-500'
  return 'bg-emerald-500'
}

function personRiskScore(item: SalesPredictionResponse): number {
  if (typeof item.risk_score === 'number') return Math.round(Math.max(0, Math.min(100, item.risk_score)))
  const probabilities = item.probabilities || {}
  const high = (probabilities.Yuksek ?? probabilities.Evet ?? probabilities['1'] ?? 0) * 100
  const medium = (probabilities.Orta ?? 0) * 55
  const low = (probabilities.Dusuk ?? probabilities.Hayir ?? probabilities['0'] ?? 0) * 15
  const score = high + medium + low
  if (score > 0) return Math.round(Math.max(0, Math.min(100, score)))
  const band = String(item.predicted_band)
  if (['Yuksek', 'Evet', '1'].includes(band)) return Math.round(75 + item.confidence * 20)
  if (band === 'Orta') return Math.round(45 + item.confidence * 20)
  return Math.round(15 + item.confidence * 20)
}

function personTopDriver(item: SalesPredictionResponse): string {
  const driver = item.top_drivers?.[0]
  const name = driver?.metric_name || driver?.feature || 'KPI sinyali'
  const status = driver?.threshold_status || driver?.status
  const trend = driver?.trend_signal || driver?.trend
  return [name, status, trend].filter(Boolean).join(' / ')
}

function salesEmployeeTrendLabel(item: SalesPredictionResponse): string {
  const driver = item.top_drivers?.[0] || {}
  const trend = driver.trend_signal || driver.trend
  const status = driver.threshold_status || driver.status
  if (trend && status) return `${trend} / ${status}`
  if (trend) return String(trend)
  if (status) return String(status)
  if (personRiskScore(item) >= 67) return 'Negatif sinyal'
  if (personRiskScore(item) >= 34) return 'Izleme gerekli'
  return 'Stabil'
}

function salesActionPlan(item: SalesPredictionResponse): Array<{ title: string; reason: string; owner: string; timeframe: string }> {
  const actions = item.recommended_actions || []
  const drivers = item.top_drivers || []
  const primaryDriver = drivers[0]
  const primaryMetric = primaryDriver?.metric_name || primaryDriver?.feature || 'KPI sinyali'
  const primaryReason = [
    primaryDriver?.threshold_status,
    primaryDriver?.trend_signal,
    item.risk_summary,
  ].filter(Boolean).join(' / ')

  const plan = actions.slice(0, 3).map((action: string, index: number) => ({
    title: action,
    reason: index === 0
      ? `${primaryMetric}: ${primaryReason || 'Admin ML modeli bu calisani izleme listesine tasidi.'}`
      : `${primaryMetric} sinyali icin haftalik takip notu ac.`,
    owner: 'Manager',
    timeframe: index === 0 ? 'Bu hafta' : '7 gun',
  }))

  if (plan.length) return plan

  return [
    {
      title: `${primaryMetric} icin satis destek gorusmesi`,
      reason: primaryReason || 'Admin ML modeli bu calisan icin aksiyon gerektiren sinyal uretmedi, yine de KPI kirilimi kontrol edilmeli.',
      owner: 'Manager',
      timeframe: 'Bu hafta',
    },
  ]
}

function salesPersonRoleLabel(item: SalesPredictionResponse): string {
  const payload = item.summary_payload || {}
  return [payload.region || payload.team, payload.position || payload.role].filter(Boolean).join(' / ') || 'Satis ekibi'
}

function salesItemTeamName(item: SalesPredictionResponse): string {
  return String(item.summary_payload?.region || item.summary_payload?.team || 'Genel')
}

function normalizeSalesTeamKey(value: string | null | undefined): string {
  return String(value || 'Genel')
    .toLowerCase()
    .replace(/ä°|i̇/g, 'i')
    .replace(/ä±/g, 'i')
    .replace(/Ã¼|ã¼|ü/g, 'u')
    .replace(/Ã¶|ã¶|ö/g, 'o')
    .replace(/ÄŸ|ä|ğ/g, 'g')
    .replace(/ÅŸ|åÿ|ş/g, 's')
    .replace(/Ã§|ã§|ç/g, 'c')
    .replace(/Ä|Äž|Ğ/g, 'g')
    .replace(/İ/g, 'i')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '')
}

function initials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()
}

function targetLabel(col: string): string {
  return TARGETS.find(t => t.value === col)?.label ?? col
}

function bandLabel(band: string | number, target: string): string {
  const b = String(band)
  if (target === 'Performance_Drop_Target') return b === '0' ? 'Düşüş Yok' : b === '1' ? 'Hafif Düşüş' : 'Belirgin Düşüş'
  if (target === 'Burnout_Target') return b === '0' ? 'Normal' : b === '1' ? 'Risk' : 'Yüksek Risk'
  if (target === 'Resignation_Target') return b === '0' ? 'Stabil' : b === '1' ? 'İzleme' : 'Kritik'
  return b === '0' ? 'Düşük' : b === '1' ? 'Orta' : 'Yüksek'
}

function bandClass(band: string | number, target: string): string {
  const b = String(band)
  if (b === '0') return 'border-emerald-200 bg-emerald-50 text-emerald-700'
  if (b === '1') return 'border-amber-200 bg-amber-50 text-amber-700'
  return 'border-rose-200 bg-rose-50 text-rose-700'
}

function displayName(item: SalesPredictionResponse): string {
  return item.summary_payload?.employee_name || item.summary_payload?.name || `Çalışan #${item.employee_id}`
}

function fmtPct(val: number | undefined | null): string {
  if (val == null) return '—'
  return `${(val * 100).toFixed(1)}%`
}

function fmtDate(val: string | null | undefined): string {
  if (!val) return '—'
  return new Date(val).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', year: 'numeric' })
}

function sColor(score: number): string {
  if (score >= 100) return 'text-emerald-600'
  if (score >= 80) return 'text-blue-600'
  if (score >= 60) return 'text-amber-600'
  return 'text-rose-600'
}

function sBarColor(score: number): string {
  if (score >= 100) return 'bg-emerald-500'
  if (score >= 80) return 'bg-blue-500'
  if (score >= 60) return 'bg-amber-500'
  return 'bg-rose-500'
}

function shortName(name: string): string {
  if (name.length <= 10) return name
  return name.split(' ').map((w: string) => w[0]).join('').toUpperCase()
}

onMounted(async () => {
  await Promise.all([loadDatasets(), loadOverview()])
})

watch(targetColumn, () => {
  predResult.value = null
  bulkResult.value = null
  tableSearch.value = ''
})
</script>
