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
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">ML Model</p>
          <h3 class="mt-1 text-lg font-bold text-slate-900">Satış risk tahmini — LightGBM + XGB + RF → LR</h3>
        </div>
        <div class="flex flex-wrap gap-2 w-full xl:max-w-4xl">
          <button
            class="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm disabled:cursor-not-allowed disabled:bg-slate-300"
            :disabled="!!mlLoading || !uploadId"
            @click="trainModel"
          >
            {{ mlLoading === 'train' ? 'Eğitiliyor…' : 'Model Eğit' }}
          </button>
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
            :disabled="!!mlLoading || !uploadId || !employeeId"
            @click="runPredict"
          >
            {{ mlLoading === 'predict' ? 'Hesaplanıyor…' : 'Tahmin Al' }}
          </button>
          <button
            class="rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-2.5 text-sm font-semibold text-indigo-800 shadow-sm disabled:cursor-not-allowed disabled:text-indigo-300"
            :disabled="!!mlLoading || !uploadId"
            @click="runBulk(false)"
          >
            {{ mlLoading === 'bulk' ? 'Tarıyor…' : 'Toplu Tara' }}
          </button>
          <button
            class="rounded-xl border border-violet-200 bg-violet-50 px-4 py-2.5 text-sm font-semibold text-violet-800 shadow-sm disabled:cursor-not-allowed disabled:text-violet-300"
            :disabled="!!mlLoading || !uploadId"
            @click="runBulk(true)"
          >
            {{ mlLoading === 'narrative' ? 'Yorumlanıyor…' : 'LLM Yorumla' }}
          </button>
        </div>
      </div>

      <!-- Status badges -->
      <div v-if="trainResult || mlError" class="mt-4 flex flex-wrap items-center gap-2 text-xs">
        <span v-if="trainResult"
          class="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 font-medium text-emerald-700">
          Model hazır: {{ targetLabel(trainResult.target_column) }} — F1 {{ fmtPct(trainResult.metrics?.weighted_f1) }}
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
          :disabled="!!mlLoading || !uploadId"
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
          <h4 class="mt-1 text-base font-bold text-slate-900">{{ deptNarrative.manager_summary }}</h4>
          <p class="mt-3 text-sm leading-6 text-slate-700">{{ deptNarrative.risk_interpretation }}</p>
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
      <div v-else class="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
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
      <div v-if="!trainResult && !modelStates.some(s => s.is_trained)"
        class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center text-sm text-slate-500">
        Teknik detaylar için önce bir model eğitilmeli.
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
        <div v-if="trainResult?.top_features?.length" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 mb-4">En Önemli Özellikler</p>
          <div class="space-y-3">
            <div v-for="(feat, idx) in trainResult.top_features.slice(0, 10)" :key="idx">
              <div class="flex items-center justify-between text-xs mb-1">
                <span class="font-semibold text-slate-700 truncate max-w-[60%]">{{ feat.feature || feat.name || `Özellik ${(idx as number) + 1}` }}</span>
                <span class="text-slate-400 tabular-nums">{{ typeof feat.importance === 'number' ? feat.importance.toFixed(4) : feat.importance }}</span>
              </div>
              <div class="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div class="h-full rounded-full bg-indigo-500"
                  :style="{ width: `${Math.min(100, (feat.importance / (trainResult!.top_features[0]?.importance || 1)) * 100)}%` }"></div>
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
const activeSection = computed(() => (route.query.section as string) || 'model')

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

const teamRows = computed(() => {
  const analytics = bulkResult.value?.team_analytics
  if (!analytics?.length) return []
  return analytics.map((ta: any) => ({
    team: ta.team as string,
    avgRisk: Math.round((ta.high_risk_rate ?? 0) * 100),
    highCount: ta.high_risk_count ?? 0,
    total: ta.employee_count ?? 0,
  }))
})

const selectedTeamPeople = computed(() => {
  if (!selectedTeam.value || !bulkResult.value) return []
  return bulkResult.value.items.filter((i: SalesPredictionResponse) =>
    (i.summary_payload?.region || i.summary_payload?.team || 'Genel') === selectedTeam.value
  )
})

const filteredItems = computed(() => {
  const q = tableSearch.value.trim().toLowerCase()
  if (!bulkResult.value) return []
  return bulkResult.value.items.filter((i: SalesPredictionResponse) =>
    !q || displayName(i).toLowerCase().includes(q)
  )
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
      uploadId.value = datasets.value[datasets.value.length - 1].id
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

async function runBulk(withNarrative: boolean) {
  if (!uploadId.value) return
  mlLoading.value = withNarrative ? 'narrative' : 'bulk'
  mlError.value = null
  try {
    bulkResult.value = await analyticsApi.getBulkSalesPredictions({
      upload_id: uploadId.value,
      target_column: targetColumn.value,
      use_llm_narrative: withNarrative,
    })
    if (teamRows.value.length) selectedTeam.value = teamRows.value[0].team
  } catch (e: any) {
    mlError.value = e?.response?.data?.detail || e?.message || 'Toplu tahmin hatası'
  } finally {
    mlLoading.value = null
  }
}

// ── Helpers ──────────────────────────────────────────────────────
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
</script>
