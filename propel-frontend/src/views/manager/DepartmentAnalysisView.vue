<template>
  <div class="space-y-8 pb-10">
    <div class="flex flex-col md:flex-row justify-between items-end gap-4 border-b border-slate-200 pb-6">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 tracking-tight">Departman Analizi</h2>
        <p class="text-slate-500 mt-1">Departmana ait yalnızca enerji, motivasyon ve NLP sinyallerini gösterir</p>
      </div>
      <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <select
          v-if="isAdmin"
          v-model="selectedDepartment"
          class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm"
        >
          <option v-for="dept in departments" :key="dept.id" :value="dept.id">
            {{ dept.name }}
          </option>
        </select>
        <select
          v-model="selectedTeam"
          class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm"
        >
          <option value="all">Tum Takimlar</option>
          <option v-for="team in teamOptions" :key="team" :value="team">
            {{ team }}
          </option>
        </select>
        <button class="px-4 py-2 bg-white border border-gray-200 text-slate-600 text-sm font-medium rounded-lg hover:bg-gray-50 flex items-center gap-2 shadow-sm transition-all">
          Rapor İndir
        </button>
        <button
          type="button"
          class="ai-analysis-pulse rounded-lg bg-gradient-to-r from-violet-600 to-blue-600 px-6 py-3 text-sm font-black text-white shadow-lg shadow-violet-500/25 transition hover:scale-105 hover:shadow-xl hover:shadow-blue-500/30"
          @click="showLlmAnalysisModal = true"
        >
          &#129302; AI ile Analiz
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-6 gap-4">
      <article
        v-for="card in departmentKpiCards"
        :key="card.title"
        class="rounded-xl border border-slate-100 bg-white p-5 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-lg"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="grid h-11 w-11 place-items-center rounded-xl bg-slate-50 text-2xl">{{ card.icon }}</div>
          <span v-if="card.trend" class="rounded-full bg-emerald-50 px-2 py-1 text-xs font-bold text-emerald-700">{{ card.trend }}</span>
        </div>
        <p class="mt-4 text-xs font-bold uppercase tracking-[0.14em] text-slate-400">{{ card.title }}</p>
        <p class="mt-2 text-[32px] font-black leading-none" :class="card.valueClass">{{ card.value }}</p>
        <p class="mt-2 text-sm font-medium text-slate-500">{{ card.subtitle }}</p>

        <div v-if="card.type === 'teams'" class="mt-4 flex flex-wrap gap-1.5">
          <span
            v-for="team in teamCountChips"
            :key="team.label"
            class="rounded-full border border-slate-100 bg-slate-50 px-2 py-1 text-[11px] font-semibold text-slate-600"
          >
            {{ team.icon }} {{ team.label }} ({{ team.count }})
          </span>
        </div>
        <div v-else-if="card.type === 'sparkline'" class="mt-4 flex h-8 items-end gap-1">
          <span
            v-for="(point, index) in performanceSparkline"
            :key="`spark-${index}`"
            class="w-full rounded-t bg-emerald-400"
            :style="{ height: `${point}%`, opacity: `${0.45 + index * 0.15}` }"
          ></span>
        </div>
        <div v-else-if="card.type === 'avatars'" class="mt-4 flex items-center">
          <div
            v-for="person in topPerformerAvatars"
            :key="person.id"
            class="-ml-2 first:ml-0 grid h-8 w-8 place-items-center rounded-full border-2 border-white text-xs font-black text-white"
            :style="{ backgroundColor: person.color }"
            :title="person.name"
          >
            {{ person.initials }}
          </div>
          <span v-if="topPerformerMoreCount > 0" class="-ml-2 grid h-8 w-8 place-items-center rounded-full border-2 border-white bg-slate-900 text-[10px] font-bold text-white">
            +{{ topPerformerMoreCount }}
          </span>
        </div>
        <div v-else-if="card.type === 'progress'" class="mt-4">
          <div class="h-2 overflow-hidden rounded-full bg-orange-100">
            <div class="h-full rounded-full bg-orange-500" :style="{ width: `${declinePercent}%` }"></div>
          </div>
          <p class="mt-2 text-xs font-semibold text-orange-600">{{ decliningEmployees.length }}/{{ scopedEmployees.length || 0 }} ({{ declinePercent }}%)</p>
        </div>
        <p v-else class="mt-4 text-xs font-bold" :class="card.metaClass">{{ card.meta }}</p>
      </article>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-[minmax(0,65fr)_minmax(320px,35fr)] gap-6">
      <section class="rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h3 class="text-lg font-black text-slate-900">&#128200; Calisan Performans Haritasi</h3>
            <p class="mt-1 text-sm text-slate-500">KPI skoru, 4 haftalik trend ve takim dagilimini tek grafikte izleyin.</p>
          </div>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="team in performanceLegend"
              :key="team.label"
              class="inline-flex items-center gap-1.5 rounded-full border border-slate-100 bg-slate-50 px-2.5 py-1 text-xs font-bold text-slate-600"
            >
              <span class="h-2.5 w-2.5 rounded-full" :style="{ backgroundColor: team.color }"></span>
              {{ team.label }}
            </span>
          </div>
        </div>
        <div class="mt-5 h-[430px]">
          <Bubble :data="performanceBubbleData" :options="performanceBubbleOptions" :plugins="[quadrantBackgroundPlugin]" />
        </div>
        <div class="mt-5 grid grid-cols-1 gap-3 md:grid-cols-4">
          <div
            v-for="quadrant in quadrantLegend"
            :key="quadrant.title"
            class="rounded-lg border border-slate-100 p-3"
            :class="quadrant.class"
          >
            <p class="text-xs font-black text-slate-800">{{ quadrant.title }}</p>
            <p class="mt-1 text-xs text-slate-500">{{ quadrant.description }}</p>
          </div>
        </div>
      </section>

      <aside class="rounded-xl bg-gradient-to-br from-violet-600 to-blue-600 p-6 text-white shadow-lg">
        <div class="flex items-center gap-3">
          <div class="grid h-11 w-11 place-items-center rounded-xl bg-white/15 text-2xl">&#129302;</div>
          <div>
            <h3 class="text-lg font-black">AI Analiz Ozeti</h3>
            <p class="text-xs font-semibold text-white/70">{{ selectedTeam === 'all' ? 'Departman geneli' : selectedTeam + ' takimi' }}</p>
          </div>
        </div>
        <div class="mt-6 space-y-4">
          <div
            v-for="insight in aiInsightCards"
            :key="insight.title"
            class="rounded-xl border border-white/10 p-4 backdrop-blur"
            :class="insight.class"
          >
            <div class="flex gap-3">
              <span class="text-xl">{{ insight.icon }}</span>
              <div>
                <p class="text-xs font-black uppercase tracking-[0.14em] text-white/75">{{ insight.title }}</p>
                <p class="mt-2 text-sm leading-6 text-white">{{ insight.text }}</p>
              </div>
            </div>
          </div>
        </div>
        <button
          type="button"
          class="mt-6 w-full rounded-xl bg-white px-4 py-3 text-sm font-black text-violet-700 shadow-sm transition hover:bg-violet-50"
          @click="showLlmAnalysisModal = true"
        >
          &#129302; Detayli LLM Analizi Iste
        </button>
      </aside>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <StatCard title="Departman Motivasyonu" :value="departmentMotivationValue" :change="departmentMotivationChange" :changeType="departmentMotivationChangeType" :icon="BoltIcon" color="indigo" />
      <StatCard title="Psikolojik Guven" :value="departmentSafetyValue" :change="departmentSafetyChange" :changeType="departmentSafetyChangeType" :icon="HeartIcon" color="rose" />
      <StatCard title="Yuksek Flight Risk" :value="departmentFlightRiskValue" :change="departmentFlightRiskChange" :changeType="departmentFlightRiskChangeType" :icon="CheckCircleIcon" color="emerald" />
      <StatCard title="Onerilen Aksiyon" :value="departmentActionValue" :change="departmentActionChange" :changeType="departmentActionChangeType" :icon="ScaleIcon" color="amber" />
    </div>

    <div v-if="departmentReport" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-sm text-slate-500">{{ departmentReport.report_title }}</p>
            <h3 class="text-xl font-bold text-slate-900 mt-1">{{ departmentReport.department_name }} Departmanı</h3>
          </div>
          <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
            Hafta {{ departmentReport.period_week }}
          </span>
        </div>

        <div class="mt-4 rounded-xl border border-indigo-100 bg-indigo-50 p-4">
          <p class="text-xs font-semibold text-indigo-700 mb-1">Haftalık Departman Özeti</p>
          <p class="text-sm text-slate-700">{{ renderText(departmentReport.report_summary) }}</p>
        </div>

        <div v-if="departmentQualityWarningSection || departmentBiasWarningSection" class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            v-if="departmentQualityWarningSection"
            class="rounded-xl border border-amber-200 bg-amber-50 p-4"
          >
            <p class="text-xs font-semibold uppercase tracking-[0.14em] text-amber-700">Veri Kalitesi Uyarısı</p>
            <div class="mt-3 flex flex-wrap gap-2">
              <span
                v-for="item in departmentQualityWarningSection.items"
                :key="`dept-quality-${item}`"
                class="rounded-full border border-amber-200 bg-white px-2 py-1 text-xs text-amber-700"
              >
                {{ renderText(item) }}
              </span>
            </div>
          </div>

          <div
            v-if="departmentBiasWarningSection"
            class="rounded-xl border border-rose-200 bg-rose-50 p-4"
          >
            <p class="text-xs font-semibold uppercase tracking-[0.14em] text-rose-700">Karşılıklı Bias Şüphesi</p>
            <div class="mt-3 flex flex-wrap gap-2">
              <span
                v-for="item in departmentBiasWarningSection.items"
                :key="`dept-bias-${item}`"
                class="rounded-full border border-rose-200 bg-white px-2 py-1 text-xs text-rose-700"
              >
                {{ renderText(item) }}
              </span>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div
            v-for="section in departmentReport.sections"
            :key="section.title"
            class="rounded-xl p-4"
            :class="getSectionClass(section.title)"
          >
            <p class="text-xs font-semibold mb-2" :class="getSectionTitleClass(section.title)">{{ section.title }}</p>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="item in section.items"
                :key="`${section.title}-${item}`"
                class="rounded-full border bg-white px-2 py-1 text-xs"
                :class="getSectionPillClass(section.title)"
              >
                {{ renderText(item) }}
              </span>
              <span v-if="!section.items.length" class="text-sm text-slate-400">Veri yok</span>
            </div>
          </div>
        </div>
      </div>

      <div class="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-lg">
          <p class="text-xs uppercase tracking-[0.2em] text-slate-400">Departman Skorları</p>
        <div class="mt-5 space-y-4">
          <div
            v-for="metric in departmentReport.metrics"
            :key="metric.label"
            class="rounded-xl border border-white/10 bg-white/5 p-4"
          >
            <p class="text-xs font-semibold text-slate-300">{{ metric.label }}</p>
            <p class="mt-1 text-2xl font-bold text-white">{{ metric.display_value }}</p>
            <p v-if="metric.description" class="mt-1 text-xs text-slate-400">{{ metric.description }}</p>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div class="lg:col-span-2 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <div class="flex justify-between items-center mb-6">
          <h3 class="font-bold text-slate-800">NLP Trendleri</h3>
          <span class="text-xs font-bold text-indigo-700 bg-indigo-50 px-2 py-1 rounded-full border border-indigo-100">Aylık takip</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="h-72">
            <p class="text-sm text-slate-500 mb-3">Motivasyon trendi</p>
            <LineChart :labels="motivationTrendLabels" :data="motivationTrendValues" label="Motivasyon" color="#4f46e5" />
          </div>
          <div class="h-72">
            <p class="text-sm text-slate-500 mb-3">Psikolojik güven trendi</p>
            <LineChart :labels="safetyTrendLabels" :data="safetyTrendValues" label="Psikolojik Guven" color="#ef4444" />
          </div>
        </div>
      </div>

      <div class="bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-700">
        <div class="flex items-center gap-2 mb-6">
          <div class="p-2 bg-indigo-500/20 rounded-lg border border-indigo-500/30">
            <SparklesIcon class="w-5 h-5 text-indigo-300" />
          </div>
          <div>
            <h3 class="font-bold text-white">Rapor Notları</h3>
            <p class="text-xs text-slate-400">Tema ve aksiyon odagi</p>
          </div>
        </div>

        <div class="space-y-4">
          <div class="bg-white/5 p-4 rounded-xl border border-white/10">
            <div class="flex gap-2 text-rose-400 text-xs font-bold mb-2 items-center">
              <ExclamationTriangleIcon class="w-4 h-4" />
              <span>Kritik Tema</span>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed">{{ renderText(topDepartmentRiskNarrative) }}</p>
          </div>
          <div class="bg-white/5 p-4 rounded-xl border border-white/10">
            <div class="flex gap-2 text-emerald-400 text-xs font-bold mb-2 items-center">
              <TrophyIcon class="w-4 h-4" />
              <span>Güçlü Alan</span>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed">{{ renderText(topDepartmentStrengthNarrative) }}</p>
          </div>
          <div class="bg-white/5 p-4 rounded-xl border border-white/10">
            <div class="flex gap-2 text-amber-400 text-xs font-bold mb-2 items-center">
              <SparklesIcon class="w-4 h-4" />
              <span>Önerilen Aksiyon</span>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed">
              {{ renderText(departmentReport?.recommended_action || 'Departman için belirgin bir aksiyon sinyali henüz oluşmadı.') }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <div class="flex items-center justify-between mb-6">
          <h3 class="font-bold text-slate-800">Risk Dağılımı</h3>
          <span class="text-xs font-bold text-amber-700 bg-amber-50 px-2 py-1 rounded-full border border-amber-100">Son hafta</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="h-72">
            <p class="text-sm text-slate-500 mb-3">Flight risk</p>
            <BarChart :labels="flightRiskLabels" :data="flightRiskValues" label="Flight Risk" color="#f97316" />
          </div>
          <div class="h-72">
            <p class="text-sm text-slate-500 mb-3">Burnout risk</p>
            <BarChart :labels="burnoutRiskLabels" :data="burnoutRiskValues" label="Burnout Risk" color="#e11d48" />
          </div>
        </div>
      </div>

      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <div class="flex items-center justify-between mb-6">
          <h3 class="font-bold text-slate-800">En Sık Risk Temaları</h3>
          <span class="text-xs font-bold text-rose-700 bg-rose-50 px-2 py-1 rounded-full border border-rose-100">NLP sinyali</span>
        </div>
        <div class="h-80">
          <BarChart :labels="riskThemeLabels" :data="riskThemeValues" label="Risk Temalari" color="#8b5cf6" />
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-[minmax(0,1.2fr)_360px] gap-6">
      <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex items-center justify-between gap-3">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Aylık Derin Analiz</p>
            <h4 class="mt-1 text-lg font-bold text-slate-900">Departman trend ve tema özeti</h4>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <select
              v-model="selectedMonth"
              class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
            >
              <option v-for="month in monthOptions" :key="month.value" :value="month.value">
                {{ month.label }}
              </option>
            </select>
            <select
              v-model="selectedYear"
              class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
            >
              <option v-for="year in yearOptions" :key="year" :value="year">
                {{ year }}
              </option>
            </select>
          </div>
        </div>

        <div v-if="monthlyDeepAnalysis" class="mt-6 space-y-6">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
              <p class="text-xs text-slate-500">Motivasyon trendi</p>
              <p class="mt-2 text-xl font-bold text-slate-900">{{ formatTrend(monthlyDeepAnalysis.motivation_trend_direction) }}</p>
            </div>
            <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
              <p class="text-xs text-slate-500">Duygu trendi</p>
              <p class="mt-2 text-xl font-bold text-slate-900">{{ formatTrend(monthlyDeepAnalysis.sentiment_trend_direction) }}</p>
            </div>
            <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
              <p class="text-xs text-slate-500">Ortalama ayrılma riski</p>
              <p class="mt-2 text-xl font-bold text-slate-900">{{ monthlyDeepAnalysis.avg_flight_risk_score ?? '-' }}/10</p>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="rounded-xl border border-rose-100 bg-rose-50 p-4">
              <p class="text-xs font-semibold text-rose-700">En sık şikayet konuları</p>
              <div class="mt-3 flex flex-wrap gap-2">
                <span
                  v-for="item in monthlyDeepAnalysis.top_complaint_topics"
                  :key="`dept-complaint-${item}`"
                  class="rounded-full border border-rose-200 bg-white px-2 py-1 text-xs text-rose-700"
                >
                  {{ renderText(item) }}
                </span>
                <span v-if="!monthlyDeepAnalysis.top_complaint_topics.length" class="text-sm text-slate-400">Veri yok</span>
              </div>
            </div>

            <div class="rounded-xl border border-emerald-100 bg-emerald-50 p-4">
              <p class="text-xs font-semibold text-emerald-700">En sık övgü konuları</p>
              <div class="mt-3 flex flex-wrap gap-2">
                <span
                  v-for="item in monthlyDeepAnalysis.top_praise_topics"
                  :key="`dept-praise-${item}`"
                  class="rounded-full border border-emerald-200 bg-white px-2 py-1 text-xs text-emerald-700"
                >
                  {{ renderText(item) }}
                </span>
                <span v-if="!monthlyDeepAnalysis.top_praise_topics.length" class="text-sm text-slate-400">Veri yok</span>
              </div>
            </div>

            <div class="rounded-xl border border-sky-100 bg-sky-50 p-4">
              <p class="text-xs font-semibold text-sky-700">Öne çıkan temalar</p>
              <div class="mt-3 flex flex-wrap gap-2">
                <span
                  v-for="item in monthlyDeepAnalysis.top_themes"
                  :key="`dept-theme-${item}`"
                  class="rounded-full border border-sky-200 bg-white px-2 py-1 text-xs text-sky-700"
                >
                  {{ renderText(item) }}
                </span>
                <span v-if="!monthlyDeepAnalysis.top_themes.length" class="text-sm text-slate-400">Veri yok</span>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="mt-6 text-sm text-slate-400">
          Bu ay için departman derin analiz verisi henüz oluşmadı.
        </div>

        <div v-if="monthlyRagReport" class="mt-6 rounded-2xl border border-violet-100 bg-violet-50 p-5">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.16em] text-violet-700">Aylık Hafızalı Analiz</p>
              <p class="mt-2 text-sm leading-6 text-slate-700">{{ renderText(monthlyRagReport.report_summary) }}</p>
            </div>
            <span class="rounded-full border border-violet-200 bg-white px-3 py-1 text-xs font-semibold text-violet-700">
              {{ formatMemoryCount(monthlyRagReport.retrieved_memory_count) }}
            </span>
          </div>

          <div class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="rounded-xl border border-violet-100 bg-white p-4">
              <p class="text-xs font-semibold text-violet-700">Trend değerlendirmesi</p>
              <p class="mt-2 text-sm leading-6 text-slate-700">{{ renderText(monthlyRagReport.trend_summary) }}</p>
            </div>
            <div class="rounded-xl border border-violet-100 bg-white p-4">
              <p class="text-xs font-semibold text-violet-700">Departman elde tutma riski</p>
              <p class="mt-2 text-sm leading-6 text-slate-700">
                Skor: {{ monthlyRagReport.flight_risk_score ?? '-' }}/10
                <span v-if="monthlyRagReport.retention_risk_level"> - {{ formatRiskLabel(monthlyRagReport.retention_risk_level) }}</span>
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-lg">
        <p class="text-xs uppercase tracking-[0.2em] text-slate-400">Aylık Departman İçgörüsü</p>
        <div v-if="monthlyDeepAnalysis" class="mt-5 space-y-4">
          <div class="rounded-xl border border-white/10 bg-white/5 p-4">
            <p class="text-xs font-semibold text-rose-300">Öne çıkan risk nedenleri</p>
            <div class="mt-3 flex flex-wrap gap-2">
              <span
                v-for="item in monthlyDeepAnalysis.top_flight_risk_reasons"
                :key="`dept-risk-reason-${item}`"
                class="rounded-full border border-rose-500/20 bg-white/5 px-2 py-1 text-xs text-rose-200"
              >
                {{ renderText(item) }}
              </span>
              <span v-if="!monthlyDeepAnalysis.top_flight_risk_reasons.length" class="text-sm text-slate-500">Veri yok</span>
            </div>
          </div>

          <div class="rounded-xl border border-white/10 bg-white/5 p-4">
            <p class="text-xs font-semibold text-amber-300">Aksiyon önerisi</p>
            <p class="mt-2 text-sm leading-6 text-slate-200">
              {{ renderText(monthlyDeepAnalysis.action_recommendation || 'Departman için aylık aksiyon önerisi henüz oluşmadı.') }}
            </p>
          </div>

          <div class="rounded-xl border border-white/10 bg-white/5 p-4">
            <p class="text-xs font-semibold text-indigo-300">Analiz kapsamı</p>
            <p class="mt-2 text-sm leading-6 text-slate-200">
              Bu rapor {{ monthlyDeepAnalysis.analyzed_employee_count }} çalışanın toplam {{ monthlyDeepAnalysis.analyzed_feedback_count }} feedback cevabından oluştu.
            </p>
          </div>

          <div v-if="monthlyRagReport" class="rounded-xl border border-white/10 bg-white/5 p-4">
            <p class="text-xs font-semibold text-violet-300">Ana bulgular</p>
            <div class="mt-3 flex flex-wrap gap-2">
              <span
                v-for="item in monthlyRagReport.key_takeaways"
                :key="`dept-rag-takeaway-${item}`"
                class="rounded-full border border-violet-500/20 bg-white/5 px-2 py-1 text-xs text-violet-200"
              >
                {{ renderText(item) }}
              </span>
              <span v-if="!monthlyRagReport.key_takeaways.length" class="text-sm text-slate-500">Veri yok</span>
            </div>
          </div>
        </div>
        <div v-else class="mt-5 text-sm text-slate-500">
          Aylık departman içgörüleri veri geldikçe burada gösterilecek.
        </div>
      </div>
    </div>

    <div
      v-if="selectedPerformanceEmployee"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm"
      @click.self="selectedPerformanceEmployee = null"
    >
      <div class="w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-xs font-bold uppercase tracking-[0.18em] text-slate-400">Calisan Detayi</p>
            <h3 class="mt-1 text-2xl font-black text-slate-900">{{ selectedPerformanceEmployee.name }}</h3>
            <p class="mt-1 text-sm text-slate-500">{{ selectedPerformanceEmployee.role }} - {{ selectedPerformanceEmployee.team }}</p>
          </div>
          <button class="rounded-full border border-slate-200 px-3 py-1 text-sm font-bold text-slate-500 hover:bg-slate-50" @click="selectedPerformanceEmployee = null">Kapat</button>
        </div>
        <div class="mt-6 grid grid-cols-3 gap-3">
          <div class="rounded-xl bg-slate-50 p-4">
            <p class="text-xs text-slate-500">KPI Skoru</p>
            <p class="mt-1 text-2xl font-black text-slate-900">{{ selectedPerformanceEmployee.kpiScore }}/100</p>
          </div>
          <div class="rounded-xl bg-slate-50 p-4">
            <p class="text-xs text-slate-500">4 Hafta Trend</p>
            <p class="mt-1 text-2xl font-black" :class="selectedPerformanceEmployee.trend >= 0 ? 'text-emerald-600' : 'text-orange-600'">
              {{ formatSigned(selectedPerformanceEmployee.trend) }}
            </p>
          </div>
          <div class="rounded-xl bg-slate-50 p-4">
            <p class="text-xs text-slate-500">Segment</p>
            <p class="mt-1 text-lg font-black text-slate-900">{{ selectedPerformanceEmployee.quadrant }}</p>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="showLlmAnalysisModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4 backdrop-blur-sm"
      @click.self="showLlmAnalysisModal = false"
    >
      <div class="flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
        <div class="flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-5">
          <div>
            <p class="text-xs font-bold uppercase tracking-[0.18em] text-violet-500">AI Destekli Departman Analizi</p>
            <h3 class="mt-1 text-2xl font-black text-slate-900">&#129302; AI ile Detaylı Performans Analizi</h3>
            <p class="mt-1 text-sm text-slate-500">{{ scopedEmployees.length }} çalışanlı ekip için KPI, trend, rol ve risk yorumu</p>
          </div>
          <button class="rounded-full border border-slate-200 px-3 py-1 text-sm font-bold text-slate-500 hover:bg-slate-50" @click="showLlmAnalysisModal = false">✕</button>
        </div>

        <div class="overflow-y-auto px-6 py-5">
          <div class="rounded-2xl border border-violet-100 bg-violet-50 p-5">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p class="text-sm font-black text-violet-800">Analiz yapılıyor...</p>
                <p class="mt-1 text-xs font-semibold text-violet-500">Canlı KPI ve departman sinyalleri işleniyor</p>
              </div>
              <span class="text-2xl font-black text-violet-700">85%</span>
            </div>
            <div class="mt-4 h-2 overflow-hidden rounded-full bg-white">
              <div class="h-full w-[85%] rounded-full bg-gradient-to-r from-violet-600 to-blue-600"></div>
            </div>
          </div>

          <div class="mt-5 space-y-5">
            <section class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
              <h4 class="text-sm font-black uppercase tracking-[0.16em] text-slate-900">Genel Durum Analizi</h4>
              <p class="mt-3 text-sm leading-6 text-slate-700">
                {{ scopedEmployees.length }} çalışanlı ekibinizde genel performans ortalaması
                <span class="font-black text-slate-900">{{ averageKpiScore || 0 }}/100</span>.
                Son 4 haftalık ortalama trend {{ formatSigned(averageTrend || 0) }} ile
                {{ averageTrend >= 0 ? 'olumlu bir ivme gösteriyor' : 'yakın takip gerektiriyor' }}.
              </p>
              <div class="mt-4 space-y-2">
                <p class="text-sm font-black text-slate-900">&#128202; Takım Dağılımı:</p>
                <p v-for="team in teamPerformanceStats" :key="`llm-team-${team.label}`" class="text-sm leading-6 text-slate-700">
                  • {{ team.label }}: {{ team.count }} kişi (Avg: {{ team.avgKpi.toFixed(1) }}) -
                  {{ team.avgKpi >= 90 ? 'Güçlü durumdalar' : team.avgKpi >= 85 ? 'İyileşme fırsatı var' : 'Dikkat gerekli' }}
                </p>
              </div>
            </section>

            <section class="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
              <h4 class="text-sm font-black uppercase tracking-[0.16em] text-slate-900">&#127919; Rol Bazlı Bulgular</h4>
              <div class="mt-3 space-y-4">
                <div v-for="role in rolePerformanceStats" :key="`llm-role-${role.key}`" class="rounded-xl bg-slate-50 p-4">
                  <p class="text-sm font-black text-slate-900">{{ role.label }} Çalışanlar ({{ role.count }} kişi)</p>
                  <p class="mt-2 text-sm leading-6 text-slate-700">
                    Ortalama {{ role.avgKpi.toFixed(1) }} KPI ve {{ formatSigned(role.avgTrend) }} trend ile
                    {{ role.avgKpi >= averageKpiScore ? 'departman ortalamasının üzerinde ilerliyorlar.' : 'gelişim desteği alabilirler.' }}
                  </p>
                  <p v-if="role.top" class="mt-2 text-sm leading-6 text-slate-700">
                    Öne çıkan: {{ role.top.name }} ({{ role.top.kpiScore }}/100, {{ formatSigned(role.top.trend) }} trend).
                  </p>
                </div>
              </div>
            </section>

            <section class="rounded-2xl border border-amber-100 bg-amber-50 p-5 shadow-sm">
              <h4 class="text-sm font-black uppercase tracking-[0.16em] text-amber-900">&#9888; Risk Analizi</h4>
              <p class="mt-3 text-sm leading-6 text-amber-900">{{ decliningEmployees.length }} çalışan düşüş trendi gösteriyor:</p>
              <div class="mt-3 space-y-3">
                <div v-for="person in llmRiskPeople" :key="`llm-risk-${person.id}`" class="rounded-xl bg-white p-4">
                  <p class="text-sm font-black text-slate-900">{{ person.name }} ({{ person.team }}, {{ person.role }})</p>
                  <p class="mt-1 text-sm text-slate-700">• Skor: {{ person.kpiScore }}/100 ({{ formatSigned(person.trend) }} trend)</p>
                  <p class="text-sm text-slate-700">• Sebep: İş yükü ve sürdürülebilirlik sinyalleri kontrol edilmeli.</p>
                  <p class="text-sm text-slate-700">• Öneri: 1-on-1 görüşme ve workload review planlansın.</p>
                </div>
              </div>
            </section>

            <section class="rounded-2xl border border-emerald-100 bg-emerald-50 p-5 shadow-sm">
              <h4 class="text-sm font-black uppercase tracking-[0.16em] text-emerald-900">&#9989; Başarı Hikayeleri</h4>
              <div class="mt-3 space-y-3">
                <div v-for="person in llmSuccessPeople" :key="`llm-success-${person.id}`" class="rounded-xl bg-white p-4">
                  <p class="text-sm font-black text-slate-900">&#127942; {{ person.name }} ({{ person.team }}, {{ person.role }})</p>
                  <p class="mt-1 text-sm text-slate-700">• Skor: {{ person.kpiScore }}/100 ({{ formatSigned(person.trend) }} trend)</p>
                  <p class="text-sm text-slate-700">• Not: Liderlik, mentorluk veya kritik iş sahipliği için değerlendirilebilir.</p>
                </div>
              </div>
            </section>

            <section class="rounded-2xl border border-blue-100 bg-blue-50 p-5 shadow-sm">
              <h4 class="text-sm font-black uppercase tracking-[0.16em] text-blue-900">&#128161; Öneriler ve Aksiyonlar</h4>
              <div class="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
                <div v-for="group in llmActionGroups" :key="group.title" class="rounded-xl bg-white p-4">
                  <p class="text-sm font-black text-slate-900">{{ group.title }}</p>
                  <div class="mt-3 space-y-2">
                    <label v-for="item in group.items" :key="item" class="flex gap-2 text-sm leading-5 text-slate-700">
                      <input type="checkbox" class="mt-1 h-4 w-4 rounded border-slate-300 text-blue-600" />
                      <span>{{ item }}</span>
                    </label>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>

        <div class="flex flex-wrap justify-end gap-3 border-t border-slate-100 px-6 py-4">
          <button class="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-black text-slate-700 hover:bg-slate-50">&#128202; PDF İndir</button>
          <button class="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-black text-slate-700 hover:bg-slate-50">&#128231; Email Gönder</button>
          <button class="rounded-xl bg-slate-900 px-4 py-2 text-sm font-black text-white hover:bg-slate-800">&#128190; Kaydet</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { BoltIcon, HeartIcon, CheckCircleIcon, ScaleIcon, SparklesIcon, ExclamationTriangleIcon, TrophyIcon } from '@heroicons/vue/24/outline'
import {
  BubbleController,
  Chart as ChartJS,
  Legend,
  LinearScale,
  PointElement,
  Tooltip,
  type ChartOptions,
  type Plugin,
} from 'chart.js'
import { Bubble } from 'vue-chartjs'
import StatCard from '@/components/dashboard/StatCard.vue'
import LineChart from '@/components/dashboard/LineChart.vue'
import BarChart from '@/components/dashboard/BarChart.vue'
import { feedbackApi, type Department360SummaryReportResponse, type DepartmentMonthlyDeepAnalysisResponse, type DepartmentMonthlyRAGReportResponse, type DepartmentNLPChartsResponse, type SummaryMetric } from '@/services/api/feedback.api'
import { analyticsApi, type DepartmentPerformanceSummaryResponse } from '@/services/api/analytics.api'
import { employeeApi } from '@/services/api/employee.api'
import { useAuthStore } from '@/stores/auth'

ChartJS.register(BubbleController, LinearScale, PointElement, Tooltip, Legend)

const departmentReport = ref<Department360SummaryReportResponse | null>(null)
const departmentCharts = ref<DepartmentNLPChartsResponse | null>(null)
const monthlyDeepAnalysis = ref<DepartmentMonthlyDeepAnalysisResponse | null>(null)
const monthlyRagReport = ref<DepartmentMonthlyRAGReportResponse | null>(null)
const performanceSummary = ref<DepartmentPerformanceSummaryResponse | null>(null)
const selectedPerformanceEmployee = ref<PerformanceEmployee | null>(null)
const showLlmAnalysisModal = ref(false)
const today = new Date()
const selectedMonth = ref<number>(today.getMonth() + 1)
const selectedYear = ref<number>(today.getFullYear())
const selectedTeam = ref<string>('all')

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin' || localStorage.getItem('role') === 'admin')
const departments = ref<any[]>([])
const employees = ref<any[]>([])
const selectedDepartment = ref<number | null>(null)

type PerformanceEmployee = {
  id: number
  name: string
  role: string
  team: string
  kpiScore: number
  trend: number
  seniority: 'junior' | 'senior' | 'mid'
  initials: string
  color: string
  quadrant: string
  hasKpiData: boolean
  latestPeriod?: string | null
}

type KpiCard = {
  icon: string
  title: string
  value: string
  subtitle: string
  valueClass?: string
  trend?: string
  type?: 'teams' | 'sparkline' | 'avatars' | 'progress'
  meta?: string
  metaClass?: string
}

const teamVisuals: Record<string, { icon: string; color: string }> = {
  Backend: { icon: '\uD83D\uDCBB', color: '#EF4444' },
  Frontend: { icon: '\uD83C\uDFA8', color: '#8B5CF6' },
  DevOps: { icon: '\u2699', color: '#3B82F6' },
  QA: { icon: '\uD83D\uDD0D', color: '#10B981' },
  'Kurumsal Satis': { icon: '\u25CF', color: '#0EA5E9' },
  'Bireysel Satis': { icon: '\u25CF', color: '#F59E0B' },
  'Musteri Basarisi': { icon: '\u25CF', color: '#10B981' },
}
const fallbackTeamColors = ['#EF4444', '#8B5CF6', '#3B82F6', '#10B981', '#F59E0B', '#EC4899']

function employeeName(employee: any) {
  return employee?.user?.full_name || `Calisan ${employee?.id ?? ''}`.trim()
}

function employeeInitials(name: string) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('') || 'C'
}

function teamColor(team: string) {
  if (teamVisuals[team]?.color) return teamVisuals[team].color
  const index = Math.abs(team.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0)) % fallbackTeamColors.length
  return fallbackTeamColors[index]
}

function teamIcon(team: string) {
  return teamVisuals[team]?.icon || '\u25CF'
}

function formatSigned(value: number) {
  if (value > 0) return `+${value.toFixed(1)}`
  return value.toFixed(1)
}

function average(values: number[]) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0
}

function inferSeniority(employee: any): 'junior' | 'senior' | 'mid' {
  const role = String(employee?.position || '').toLowerCase()
  const years = Number(employee?.experience_years || 0)
  if (role.includes('junior') || years <= 2) return 'junior'
  if (role.includes('senior') || role.includes('lead') || role.includes('principal') || years >= 5) return 'senior'
  return 'mid'
}

function employeeQuadrant(score: number, trend: number) {
  if (score >= 90 && trend >= 0) return 'Star Performers'
  if (score < 90 && trend >= 0) return 'Yukselen Yildizlar'
  if (score >= 90 && trend < 0) return 'Izlenmeli'
  return 'Dususte'
}

const monthOptions = [
  { value: 1, label: 'Ocak' },
  { value: 2, label: 'Subat' },
  { value: 3, label: 'Mart' },
  { value: 4, label: 'Nisan' },
  { value: 5, label: 'Mayis' },
  { value: 6, label: 'Haziran' },
  { value: 7, label: 'Temmuz' },
  { value: 8, label: 'Agustos' },
  { value: 9, label: 'Eylul' },
  { value: 10, label: 'Ekim' },
  { value: 11, label: 'Kasim' },
  { value: 12, label: 'Aralik' },
]

const yearOptions = computed(() => {
  const baseYear = today.getFullYear()
  return [baseYear - 1, baseYear, baseYear + 1]
})

const scopedEmployees = computed(() => employees.value.filter((employee) => {
  const isEmployee = employee?.user?.role === 'employee'
  const inDepartment = !selectedDepartment.value || employee.department_id === selectedDepartment.value
  const inTeam = selectedTeam.value === 'all' || employee.team === selectedTeam.value
  const hasOperationalTeam = employee.team && employee.team !== 'Yonetim'
  return isEmployee && inDepartment && inTeam && hasOperationalTeam
}))

const performanceEmployees = computed<PerformanceEmployee[]>(() => (
  performanceSummary.value?.employees || []
).filter((employee) => employee.has_kpi_data && employee.kpi_score !== null && employee.kpi_score !== undefined).map((employee) => {
  const team = employee.team || 'Takimsiz'
  const kpiScore = Number(employee.kpi_score ?? 0)
  const trend = Number(employee.trend ?? 0)
  return {
    id: employee.employee_id,
    name: employee.employee_name,
    role: employee.position || 'Rol tanimli degil',
    team,
    kpiScore,
    trend,
    seniority: (employee.role_level === 'junior' || employee.role_level === 'senior' ? employee.role_level : 'mid') as PerformanceEmployee['seniority'],
    initials: employeeInitials(employee.employee_name),
    color: teamColor(team),
    quadrant: employeeQuadrant(kpiScore, trend),
    hasKpiData: employee.has_kpi_data,
    latestPeriod: employee.latest_period,
  }
}).sort((a, b) => b.kpiScore - a.kpiScore))

const teamCountChips = computed(() => (
  performanceSummary.value?.teams || []
).map((team) => ({ label: team.team, count: team.employee_count, analyzedCount: team.analyzed_count, icon: teamIcon(team.team), color: teamColor(team.team) }))
  .sort((a, b) => b.count - a.count))

const topPerformers = computed(() => performanceEmployees.value.filter((employee) => employee.kpiScore > 92))
const decliningEmployees = computed(() => performanceEmployees.value.filter((employee) => employee.trend < 0))
const juniorEmployees = computed(() => performanceEmployees.value.filter((employee) => employee.seniority === 'junior'))
const seniorEmployees = computed(() => performanceEmployees.value.filter((employee) => employee.seniority === 'senior'))
const averageKpiScore = computed(() => performanceSummary.value?.summary.average_kpi ?? 0)
const averageTrend = computed(() => performanceSummary.value?.summary.average_trend ?? 0)
const juniorAverage = computed(() => performanceSummary.value?.summary.junior_average ?? 0)
const seniorAverage = computed(() => performanceSummary.value?.summary.senior_average ?? 0)
const declinePercent = computed(() => scopedEmployees.value.length ? Math.round((decliningEmployees.value.length / scopedEmployees.value.length) * 100) : 0)
const topPerformerAvatars = computed(() => topPerformers.value.slice(0, 3))
const topPerformerMoreCount = computed(() => Math.max(0, topPerformers.value.length - topPerformerAvatars.value.length))
const performanceSparkline = computed(() => {
  const series = (performanceSummary.value?.employees || [])
    .filter((employee) => employee.sparkline_values.length)
    .map((employee) => employee.sparkline_values)
  const maxLength = Math.max(0, ...series.map((values) => values.length))
  if (!maxLength) return []
  const values = Array.from({ length: maxLength }, (_, index) => average(series.map((points) => points[index]).filter((value) => Number.isFinite(value))))
  const min = Math.min(...values)
  const max = Math.max(...values)
  return values.map((value) => Math.max(18, Math.round(((value - min) / Math.max(1, max - min)) * 70) + 20))
})

const departmentKpiCards = computed<KpiCard[]>(() => {
  const total = performanceSummary.value?.summary.total_employees ?? scopedEmployees.value.length
  const teamCount = performanceSummary.value?.summary.team_count ?? teamCountChips.value.length
  const juniorDiff = juniorEmployees.value.length && seniorEmployees.value.length ? juniorAverage.value - seniorAverage.value : 0
  const seniorDiff = seniorEmployees.value.length ? seniorAverage.value - averageKpiScore.value : 0
  const analyzed = performanceSummary.value?.summary.analyzed_employees ?? performanceEmployees.value.length
  return [
    { icon: '\uD83D\uDC65', title: 'Toplam Calisan', value: `${total} kisi`, subtitle: `${teamCount} takimda`, type: 'teams', valueClass: 'text-slate-900' },
    { icon: '\uD83D\uDCCA', title: 'Ortalama Performans', value: analyzed ? `${averageKpiScore.value} / 100` : 'Veri yok', subtitle: analyzed ? `4H trend: ${formatSigned(averageTrend.value || 0)}` : 'KPI kaydi bekleniyor', trend: averageTrend.value >= 0 ? 'UP' : 'DOWN', type: 'sparkline', valueClass: 'text-emerald-600' },
    { icon: '\u2B50', title: 'Top Performers', value: `${performanceSummary.value?.summary.top_performer_count ?? topPerformers.value.length} kisi`, subtitle: 'Skor > 92', type: 'avatars', valueClass: 'text-amber-500' },
    { icon: '\u26A0', title: 'Dusus Gosteren', value: `${performanceSummary.value?.summary.declining_count ?? decliningEmployees.value.length} kisi`, subtitle: 'Son 4 haftada', type: 'progress', valueClass: 'text-orange-500' },
    { icon: '\uD83C\uDD95', title: 'Junior Avg.', value: performanceSummary.value?.summary.junior_average != null ? `${juniorAverage.value} / 100` : 'Veri yok', subtitle: `${performanceSummary.value?.summary.junior_count ?? juniorEmployees.value.length} junior calisan`, meta: `${formatSigned(juniorDiff)} from senior`, metaClass: juniorDiff >= 0 ? 'text-emerald-600' : 'text-rose-500', valueClass: 'text-slate-900' },
    { icon: '\uD83C\uDFC6', title: 'Senior Avg.', value: performanceSummary.value?.summary.senior_average != null ? `${seniorAverage.value} / 100` : 'Veri yok', subtitle: `${performanceSummary.value?.summary.senior_count ?? seniorEmployees.value.length} senior calisan`, meta: `${formatSigned(seniorDiff)} from avg`, metaClass: seniorDiff >= 0 ? 'text-emerald-600' : 'text-rose-500', valueClass: 'text-slate-900' },
  ]
})

const performanceLegend = computed(() => teamCountChips.value.map((team) => ({ label: team.label, color: team.color })))
const quadrantLegend = [
  { title: 'Yukselen Yildizlar', description: 'KPI < 90, trend pozitif', class: 'bg-emerald-50' },
  { title: 'Star Performers', description: 'KPI >= 90, trend pozitif', class: 'bg-sky-50' },
  { title: 'Dususte', description: 'KPI < 90, trend negatif', class: 'bg-rose-50' },
  { title: 'Izlenmeli', description: 'KPI >= 90, trend negatif', class: 'bg-amber-50' },
]

const quadrantBackgroundPlugin: Plugin<'bubble'> = {
  id: 'departmentPerformanceQuadrants',
  beforeDraw(chart) {
    const { ctx, chartArea, scales } = chart
    if (!chartArea || !scales.x || !scales.y) return
    const x90 = scales.x.getPixelForValue(90)
    const y0 = scales.y.getPixelForValue(0)
    const { left, right, top, bottom } = chartArea
    const regions = [
      { x: left, y: top, w: x90 - left, h: y0 - top, color: 'rgba(16, 185, 129, 0.07)' },
      { x: x90, y: top, w: right - x90, h: y0 - top, color: 'rgba(14, 165, 233, 0.08)' },
      { x: left, y: y0, w: x90 - left, h: bottom - y0, color: 'rgba(244, 63, 94, 0.07)' },
      { x: x90, y: y0, w: right - x90, h: bottom - y0, color: 'rgba(245, 158, 11, 0.08)' },
    ]
    ctx.save()
    regions.forEach((region) => {
      ctx.fillStyle = region.color
      ctx.fillRect(region.x, region.y, region.w, region.h)
    })
    ctx.strokeStyle = 'rgba(15, 23, 42, 0.22)'
    ctx.setLineDash([6, 6])
    ctx.beginPath()
    ctx.moveTo(x90, top)
    ctx.lineTo(x90, bottom)
    ctx.moveTo(left, y0)
    ctx.lineTo(right, y0)
    ctx.stroke()
    ctx.restore()
  },
}

const performanceBubbleData = computed(() => {
  const grouped = performanceEmployees.value.reduce<Record<string, PerformanceEmployee[]>>((acc, employee) => {
    acc[employee.team] ||= []
    acc[employee.team].push(employee)
    return acc
  }, {})
  return {
    datasets: Object.entries(grouped).map(([team, items]) => ({
      label: team,
      data: items.map((employee) => ({ x: employee.kpiScore, y: employee.trend, r: Math.max(8, Math.min(16, 8 + (employee.seniority === 'senior' ? 4 : employee.seniority === 'mid' ? 2 : 0))), employee })),
      backgroundColor: `${teamColor(team)}B8`,
      borderColor: teamColor(team),
      borderWidth: 2,
      hoverBorderWidth: 4,
      hoverRadius: 3,
    })),
  }
})

const performanceBubbleOptions = computed<ChartOptions<'bubble'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  onClick: (_event, elements, chart) => {
    const element = elements[0]
    if (!element) return
    const raw = chart.data.datasets[element.datasetIndex].data[element.index] as any
    selectedPerformanceEmployee.value = raw.employee
  },
  scales: {
    x: { min: 0, max: 100, title: { display: true, text: 'KPI Skoru', color: '#475569', font: { weight: 'bold' } }, grid: { color: '#EEF2F7' }, ticks: { color: '#64748B' } },
    y: { min: -10, max: 10, title: { display: true, text: '4 Haftalik Trend', color: '#475569', font: { weight: 'bold' } }, grid: { color: '#EEF2F7' }, ticks: { color: '#64748B' } },
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#0f172a',
      padding: 12,
      cornerRadius: 10,
      displayColors: false,
      callbacks: {
        label(context) {
          const raw = context.raw as any
          const employee = raw.employee as PerformanceEmployee
          return [employee.name, `${employee.role} - ${employee.team}`, `KPI: ${employee.kpiScore}/100`, `Trend: ${formatSigned(employee.trend)}`]
        },
      },
    },
  },
  elements: { point: { hitRadius: 8 } },
  interaction: { mode: 'nearest', intersect: true },
  layout: { padding: 6 },
}))

const aiInsightCards = computed(() => {
  if (performanceSummary.value?.insights.length) {
    const classMap: Record<string, string> = {
      neutral: 'bg-white/10',
      warning: 'bg-orange-400/15',
      success: 'bg-emerald-400/15',
      info: 'bg-blue-400/15',
    }
    return performanceSummary.value.insights.map((insight) => ({
      title: insight.title,
      icon: insight.icon,
      text: insight.text,
      class: classMap[insight.tone] || 'bg-white/10',
    }))
  }
  const teamStats = teamCountChips.value.map((team) => {
    const teamEmployees = performanceEmployees.value.filter((employee) => employee.team === team.label)
    return { ...team, trend: average(teamEmployees.map((employee) => employee.trend)), declining: teamEmployees.filter((employee) => employee.trend < 0).length }
  })
  const strongestTeam = [...teamStats].sort((a, b) => b.trend - a.trend)[0]
  const riskiestTeam = [...teamStats].sort((a, b) => b.declining - a.declining)[0]
  return [
    { title: 'Genel Durum', icon: '\uD83D\uDCCA', text: `${scopedEmployees.value.length} calisandan ${topPerformers.value.length}'si yuksek performansli. Genel trend ${averageTrend.value >= 0 ? 'pozitif' : 'negatif'} (${formatSigned(averageTrend.value || 0)} degisim).`, class: 'bg-white/10' },
    { title: 'Risk Tespiti', icon: '\u26A0', text: `${riskiestTeam?.label || 'Departman'} takiminda ${riskiestTeam?.declining || 0} calisan dusus trendinde. Oncelikli gorusme ve yakin takip onerilir.`, class: 'bg-orange-400/15' },
    { title: 'Basari Hikayesi', icon: '\u2705', text: `${strongestTeam?.label || 'Ekip'} takimi istikrarli yukselis gosteriyor. Ortalama ${formatSigned(Number((strongestTeam?.trend || 0).toFixed(1)))} artis.`, class: 'bg-emerald-400/15' },
    { title: 'Junior-Senior Farki', icon: '\uD83D\uDCC8', text: `Senior calisanlar ortalama ${formatSigned(seniorAverage.value - juniorAverage.value)} puan onde. Mentorluk programi onerilir.`, class: 'bg-blue-400/15' },
  ]
})

const teamPerformanceStats = computed(() => {
  if (performanceSummary.value?.teams.length) {
    return performanceSummary.value.teams.map((team) => ({
      label: team.team,
      count: team.employee_count,
      analyzedCount: team.analyzed_count,
      icon: teamIcon(team.team),
      color: teamColor(team.team),
      avgKpi: team.average_kpi ?? 0,
      avgTrend: team.average_trend ?? 0,
      declining: team.declining_count,
    }))
  }
  return teamCountChips.value.map((team) => {
    const members = performanceEmployees.value.filter((employee) => employee.team === team.label)
    return {
      ...team,
      avgKpi: average(members.map((employee) => employee.kpiScore)),
      avgTrend: average(members.map((employee) => employee.trend)),
      declining: members.filter((employee) => employee.trend < 0).length,
    }
  })
})

const rolePerformanceStats = computed(() => {
  if (performanceSummary.value?.roles.length) {
    return performanceSummary.value.roles.map((role) => ({
      key: role.role_level,
      label: role.label,
      count: role.employee_count,
      avgKpi: role.average_kpi ?? 0,
      avgTrend: role.average_trend ?? 0,
      top: role.highest_employee_name ? { name: role.highest_employee_name, kpiScore: role.highest_kpi ?? 0, trend: 0 } : null,
      low: role.lowest_employee_name ? { name: role.lowest_employee_name, kpiScore: role.lowest_kpi ?? 0, trend: 0 } : null,
    }))
  }
  const roles: Array<{ key: PerformanceEmployee['seniority']; label: string }> = [
    { key: 'junior', label: 'Junior' },
    { key: 'mid', label: 'Mid' },
    { key: 'senior', label: 'Senior' },
  ]

  return roles.map((role) => {
    const members = performanceEmployees.value.filter((employee) => employee.seniority === role.key)
    const sorted = [...members].sort((a, b) => b.kpiScore - a.kpiScore)
    return {
      ...role,
      count: members.length,
      avgKpi: average(members.map((employee) => employee.kpiScore)),
      avgTrend: average(members.map((employee) => employee.trend)),
      top: sorted[0] || null,
      low: sorted[sorted.length - 1] || null,
    }
  })
})

const llmRiskPeople = computed(() => (
  (performanceSummary.value?.risk_people.length
    ? performanceSummary.value.risk_people.map((employee) => {
      const team = employee.team || 'Takimsiz'
      const kpiScore = employee.kpi_score ?? 0
      const trend = employee.trend ?? 0
      return {
        id: employee.employee_id,
        name: employee.employee_name,
        role: employee.position || 'Rol tanimli degil',
        team,
        kpiScore,
        trend,
        seniority: (employee.role_level === 'junior' || employee.role_level === 'senior' ? employee.role_level : 'mid') as PerformanceEmployee['seniority'],
        initials: employeeInitials(employee.employee_name),
        color: teamColor(team),
        quadrant: employeeQuadrant(kpiScore, trend),
        hasKpiData: employee.has_kpi_data,
        latestPeriod: employee.latest_period,
      } as PerformanceEmployee
    })
    : [...decliningEmployees.value])
    .sort((a, b) => a.trend - b.trend)
    .slice(0, 5)
))

const llmSuccessPeople = computed(() => (
  (performanceSummary.value?.success_people.length
    ? performanceSummary.value.success_people.map((employee) => {
      const team = employee.team || 'Takimsiz'
      const kpiScore = employee.kpi_score ?? 0
      const trend = employee.trend ?? 0
      return {
        id: employee.employee_id,
        name: employee.employee_name,
        role: employee.position || 'Rol tanimli degil',
        team,
        kpiScore,
        trend,
        seniority: (employee.role_level === 'junior' || employee.role_level === 'senior' ? employee.role_level : 'mid') as PerformanceEmployee['seniority'],
        initials: employeeInitials(employee.employee_name),
        color: teamColor(team),
        quadrant: employeeQuadrant(kpiScore, trend),
        hasKpiData: employee.has_kpi_data,
        latestPeriod: employee.latest_period,
      } as PerformanceEmployee
    })
    : [...performanceEmployees.value])
    .filter((employee) => employee.trend > 0)
    .sort((a, b) => (b.trend - a.trend) || (b.kpiScore - a.kpiScore))
    .slice(0, 3)
))

const llmActionGroups = computed(() => performanceSummary.value?.action_groups || [])

const teamOptions = computed(() => {
  if (!employees.value.length) return []
  const teams = new Set(employees.value.map(e => e.team).filter(t => t && t !== 'Yonetim'))
  return Array.from(teams).sort()
})

function currentTeamParam() {
  return selectedTeam.value === 'all' ? undefined : selectedTeam.value
}

function currentDepartmentParam() {
  return isAdmin.value ? (selectedDepartment.value || undefined) : undefined
}

function getMetric(report: { metrics: SummaryMetric[] } | null, label: string) {
  return report?.metrics.find((metric) => metric.label === label) ?? null
}

function getSectionClass(title: string) {
  const normalized = title.toLowerCase()
  if (normalized.includes('guclu')) return 'border border-emerald-100 bg-emerald-50'
  if (normalized.includes('risk')) return 'border border-rose-100 bg-rose-50'
  return 'border border-amber-100 bg-amber-50'
}

function getSectionTitleClass(title: string) {
  const normalized = title.toLowerCase()
  if (normalized.includes('guclu')) return 'text-emerald-700'
  if (normalized.includes('risk')) return 'text-rose-700'
  return 'text-amber-700'
}

function getSectionPillClass(title: string) {
  const normalized = title.toLowerCase()
  if (normalized.includes('guclu')) return 'text-emerald-700 border-emerald-200'
  if (normalized.includes('risk')) return 'text-rose-700 border-rose-200'
  return 'text-amber-700 border-amber-200'
}

function formatTrend(value: string) {
  const map: Record<string, string> = {
    yukselis: 'Yükseliş',
    dusus: 'Düşüş',
    stabil: 'Stabil',
  }
  return map[value] || 'Stabil'
}

function formatRiskLabel(value?: string | null) {
  const map: Record<string, string> = {
    low: 'Düşük',
    medium: 'Orta',
    high: 'Yüksek',
  }
  return value ? (map[value] || value) : '-'
}

function formatMemoryCount(value: number) {
  return `${value} benzer kayıt`
}

function renderText(value?: string | null) {
  if (!value) return ''

  const replacements: Array<[string, string]> = [
    ['surec yavasligi', 'süreç yavaşlığı'],
    ['toplanti yogunlugu', 'toplantı yoğunluğu'],
    ['deadline baskisi', 'deadline baskısı'],
    ['mentorluk eksikligi', 'mentorluk eksikliği'],
    ['psikolojik guven', 'psikolojik güven'],
    ['is birligi', 'iş birliği'],
    ['gelisime aciklik', 'gelişime açıklık'],
    ['teknik borc', 'teknik borç'],
    ['liderlik destegi', 'liderlik desteği'],
    ['yonetsel destek', 'yönetsel destek'],
    ['yukselis', 'yükseliş'],
    ['dusus', 'düşüş'],
    ['gorunuyor', 'görünüyor'],
    ['Tekrarlanan sikayet konulari', 'Tekrarlanan şikayet konuları'],
    ['En belirgin sikayet alanlari', 'En belirgin şikayet alanları'],
    ['Gecmis benzer yorumlar', 'Geçmiş benzer yorumlar'],
    ['kayitta', 'kayıtta'],
    ['ayrilma riski', 'ayrılma riski'],
    ['Departmanda tekrar eden ana risk temasi', 'Departmanda tekrar eden ana risk teması'],
    ['Departmanda olumlu sinyal veren ana alan', 'Departmanda olumlu sinyal veren ana alan'],
  ]

  let rendered = value
  for (const [from, to] of replacements) {
    rendered = rendered.split(from).join(to)
  }
  return rendered
}

const departmentMotivationValue = computed(() => getMetric(departmentReport.value, 'Departman Motivasyonu')?.display_value || '-')
const departmentMotivationChange = computed(() => getMetric(departmentReport.value, 'Departman Motivasyonu')?.description || 'Veri bekleniyor')
const departmentMotivationChangeType = computed(() => ((getMetric(departmentReport.value, 'Departman Motivasyonu')?.risk_level ?? 'medium') === 'high' ? 'decrease' : 'increase'))

const departmentSafetyValue = computed(() => getMetric(departmentReport.value, 'Psikolojik Guven')?.display_value || '-')
const departmentSafetyChange = computed(() => getMetric(departmentReport.value, 'Psikolojik Guven')?.description || 'Veri bekleniyor')
const departmentSafetyChangeType = computed(() => ((getMetric(departmentReport.value, 'Psikolojik Guven')?.risk_level ?? 'medium') === 'high' ? 'decrease' : 'increase'))

const departmentFlightRiskValue = computed(() => getMetric(departmentReport.value, 'Yuksek Flight Risk')?.display_value || '-')
const departmentFlightRiskChange = computed(() => getMetric(departmentReport.value, 'Yuksek Flight Risk')?.description || 'Veri bekleniyor')
const departmentFlightRiskChangeType = computed(() => ((getMetric(departmentReport.value, 'Yuksek Flight Risk')?.risk_level ?? 'medium') === 'high' ? 'decrease' : 'increase'))

const departmentActionValue = computed(() => departmentReport.value?.recommended_action || '-')
const departmentActionChange = computed(() => departmentReport.value?.report_summary || 'Oncelik sinyali bekleniyor')
const departmentActionChangeType = computed(() => (departmentReport.value?.recommended_action ? 'increase' : 'decrease'))

const topDepartmentRiskNarrative = computed(() => {
  const riskSection = departmentReport.value?.sections.find((section) => section.title.toLowerCase().includes('risk'))
  if (!riskSection?.items.length) return 'Bu hafta one cikan bir risk temasi henuz olusmadi.'
  return `Departmanda tekrar eden ana risk temasi: ${riskSection.items[0]}.`
})

const departmentQualityWarningSection = computed(() =>
  departmentReport.value?.sections.find((section) => section.title.toLowerCase().includes('veri kalitesi')) || null
)

const departmentBiasWarningSection = computed(() =>
  departmentReport.value?.sections.find((section) => section.title.toLowerCase().includes('bias')) || null
)

const topDepartmentStrengthNarrative = computed(() => {
  const strengthSection = departmentReport.value?.sections.find((section) => section.title.toLowerCase().includes('guclu'))
  if (!strengthSection?.items.length) return 'Bu hafta one cikan belirgin bir guclu alan henuz olusmadi.'
  return `Departmanda olumlu sinyal veren ana alan: ${strengthSection.items[0]}.`
})

const motivationTrendLabels = computed(() => departmentCharts.value?.motivation_trend.map((item) => item.label) || ['Hafta 1', 'Hafta 2', 'Hafta 3', 'Hafta 4'])
const motivationTrendValues = computed(() => departmentCharts.value?.motivation_trend.map((item) => item.value) || [0, 0, 0, 0])
const safetyTrendLabels = computed(() => departmentCharts.value?.psychological_safety_trend.map((item) => item.label) || ['Hafta 1', 'Hafta 2', 'Hafta 3', 'Hafta 4'])
const safetyTrendValues = computed(() => departmentCharts.value?.psychological_safety_trend.map((item) => item.value) || [0, 0, 0, 0])
const flightRiskLabels = computed(() => departmentCharts.value?.flight_risk_distribution.map((item) => item.label) || ['Dusuk', 'Orta', 'Yuksek'])
const flightRiskValues = computed(() => departmentCharts.value?.flight_risk_distribution.map((item) => item.value) || [0, 0, 0])
const burnoutRiskLabels = computed(() => departmentCharts.value?.burnout_risk_distribution.map((item) => item.label) || ['Dusuk', 'Orta', 'Yuksek'])
const burnoutRiskValues = computed(() => departmentCharts.value?.burnout_risk_distribution.map((item) => item.value) || [0, 0, 0])
const riskThemeLabels = computed(() => departmentCharts.value?.top_risk_themes.map((item) => item.label) || ['Veri yok'])
const riskThemeValues = computed(() => departmentCharts.value?.top_risk_themes.map((item) => item.value) || [0])

async function loadDepartmentReport() {
  try {
    departmentReport.value = await feedbackApi.getDepartment360SummaryReport({ department_id: currentDepartmentParam(), team: currentTeamParam() })
  } catch (error) {
    console.error('Departman 360 raporu yuklenemedi:', error)
    departmentReport.value = null
  }
}

async function loadDepartmentCharts() {
  try {
    departmentCharts.value = await feedbackApi.getDepartmentNlpCharts({ department_id: currentDepartmentParam(), team: currentTeamParam() })
  } catch (error) {
    console.error('Departman NLP grafikleri yuklenemedi:', error)
    departmentCharts.value = null
  }
}

async function loadMonthlyDeepAnalysis() {
  try {
    monthlyDeepAnalysis.value = await feedbackApi.getDepartmentMonthlyDeepAnalysis({
      department_id: currentDepartmentParam(),
      team: currentTeamParam(),
      year: selectedYear.value,
      month: selectedMonth.value,
    })
    monthlyRagReport.value = await feedbackApi.getDepartmentMonthlyRagReport({
      department_id: currentDepartmentParam(),
      team: currentTeamParam(),
      year: selectedYear.value,
      month: selectedMonth.value,
    })
  } catch (error) {
    console.error('Departman aylik derin analizi yuklenemedi:', error)
    monthlyDeepAnalysis.value = null
    monthlyRagReport.value = null
  }
}

async function loadPerformanceSummary() {
  try {
    performanceSummary.value = await analyticsApi.getPerformanceSummary({
      department_id: currentDepartmentParam(),
      team: currentTeamParam(),
    })
  } catch (error) {
    console.error('Performans ozeti yuklenemedi:', error)
    performanceSummary.value = null
  }
}

async function loadDepartments() {
  try {
    if (isAdmin.value) {
      departments.value = await employeeApi.getDepartments()
      if (departments.value.length > 0 && !selectedDepartment.value) {
        selectedDepartment.value = departments.value[0].id
      }
    } else {
      // Manager is already restricted to their department in the backend,
      // but we fetch the employee list to get the teams.
    }
    
    // Fetch employees to determine teams
    const employeesData = await employeeApi.getEmployees()
    employees.value = employeesData
    
    // For non-admin, use the department of the first employee (self/department)
    if (!isAdmin.value && employeesData.length > 0) {
      selectedDepartment.value = employeesData[0].department_id
    }
  } catch (error) {
    console.error('Veriler yuklenemedi:', error)
  }
}

watch([selectedMonth, selectedYear, selectedTeam, selectedDepartment], async () => {
  await loadPerformanceSummary()
  await loadDepartmentReport()
  await loadDepartmentCharts()
  await loadMonthlyDeepAnalysis()
})

onMounted(async () => {
  await loadDepartments()
  await loadPerformanceSummary()
  await loadDepartmentReport()
  await loadDepartmentCharts()
  await loadMonthlyDeepAnalysis()
})
</script>

<style scoped>
.ai-analysis-pulse {
  animation: ai-analysis-pulse 2.2s ease-in-out infinite;
}

@keyframes ai-analysis-pulse {
  0%, 100% {
    box-shadow: 0 10px 24px rgba(124, 58, 237, 0.22);
  }
  50% {
    box-shadow: 0 14px 34px rgba(37, 99, 235, 0.38);
  }
}

@media (prefers-reduced-motion: reduce) {
  .ai-analysis-pulse {
    animation: none;
  }
}
</style>
