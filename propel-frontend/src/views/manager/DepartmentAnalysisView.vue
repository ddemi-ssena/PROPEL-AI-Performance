<template>
  <div class="space-y-8 pb-10">
    <div class="flex flex-col md:flex-row justify-between items-end gap-4 border-b border-slate-200 pb-6">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 tracking-tight">360 Departman Raporu</h2>
        <p class="text-slate-500 mt-1">Departmana ait yalnizca 360 feedback kaynakli enerji, motivasyon ve NLP sinyallerini gosterir</p>
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
          Rapor Ä°ndir
        </button>
      </div>
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
            <h3 class="text-xl font-bold text-slate-900 mt-1">{{ departmentReport.department_name }} DepartmanÄ±</h3>
          </div>
          <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
            Hafta {{ departmentReport.period_week }}
          </span>
        </div>

        <div class="mt-4 rounded-xl border border-indigo-100 bg-indigo-50 p-4">
          <p class="text-xs font-semibold text-indigo-700 mb-1">HaftalÄ±k Departman Ã–zeti</p>
          <p class="text-sm text-slate-700">{{ renderText(departmentReport.report_summary) }}</p>
        </div>

        <div v-if="departmentQualityWarningSection || departmentBiasWarningSection" class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            v-if="departmentQualityWarningSection"
            class="rounded-xl border border-amber-200 bg-amber-50 p-4"
          >
            <p class="text-xs font-semibold uppercase tracking-[0.14em] text-amber-700">Veri Kalitesi UyarÄ±sÄ±</p>
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
            <p class="text-xs font-semibold uppercase tracking-[0.14em] text-rose-700">KarÅŸÄ±lÄ±klÄ± Bias ÅÃ¼phesi</p>
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
          <p class="text-xs uppercase tracking-[0.2em] text-slate-400">Departman SkorlarÄ±</p>
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
          <span class="text-xs font-bold text-indigo-700 bg-indigo-50 px-2 py-1 rounded-full border border-indigo-100">AylÄ±k takip</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="h-72">
            <p class="text-sm text-slate-500 mb-3">Motivasyon trendi</p>
            <LineChart :labels="motivationTrendLabels" :data="motivationTrendValues" label="Motivasyon" color="#4f46e5" />
          </div>
          <div class="h-72">
            <p class="text-sm text-slate-500 mb-3">Psikolojik gÃ¼ven trendi</p>
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
            <h3 class="font-bold text-white">Rapor NotlarÄ±</h3>
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
              <span>GÃ¼Ã§lÃ¼ Alan</span>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed">{{ renderText(topDepartmentStrengthNarrative) }}</p>
          </div>
          <div class="bg-white/5 p-4 rounded-xl border border-white/10">
            <div class="flex gap-2 text-amber-400 text-xs font-bold mb-2 items-center">
              <SparklesIcon class="w-4 h-4" />
              <span>Ã–nerilen Aksiyon</span>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed">
              {{ renderText(departmentReport?.recommended_action || 'Departman iÃ§in belirgin bir aksiyon sinyali henÃ¼z oluÅŸmadÄ±.') }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <div class="flex items-center justify-between mb-6">
          <h3 class="font-bold text-slate-800">Risk DaÄŸÄ±lÄ±mÄ±</h3>
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
          <h3 class="font-bold text-slate-800">En SÄ±k Risk TemalarÄ±</h3>
          <span class="text-xs font-bold text-rose-700 bg-rose-50 px-2 py-1 rounded-full border border-rose-100">NLP sinyali</span>
        </div>
        <div class="h-80">
          <BarChart :labels="riskThemeLabels" :data="riskThemeValues" label="Risk Temalari" color="#8b5cf6" />
        </div>
      </div>
    </div>

    <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">NLP Laboratuvari</p>
          <h3 class="mt-1 text-lg font-bold text-slate-900">Test cumlesi analizi</h3>
          <p class="mt-1 text-sm text-slate-500">360 feedback analiz motorunu kayit olusturmadan test eder.</p>
        </div>
        <div v-if="nlpTestResult" class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm">
          <p class="text-xs font-semibold text-slate-500">Model</p>
          <p class="font-bold text-slate-900">{{ nlpTestResult.model_provider }} / {{ nlpTestResult.model_name }}</p>
        </div>
      </div>

      <div class="mt-5 grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_420px] gap-6">
        <div class="space-y-4">
          <div class="flex flex-wrap gap-2">
            <button
              v-for="sample in nlpTestSamples"
              :key="sample.label"
              type="button"
              class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:border-indigo-200 hover:bg-indigo-50"
              @click="applyNlpSample(sample)"
            >
              {{ sample.label }}
            </button>
          </div>

          <textarea
            v-model="nlpTestText"
            rows="5"
            class="w-full rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-700 outline-none focus:border-indigo-300 focus:ring-4 focus:ring-indigo-100"
            placeholder="Test edilecek 360 feedback cumlesini yazin..."
          />

          <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <label v-for="score in nlpScoreControls" :key="score.key" class="text-xs font-semibold text-slate-500">
              {{ score.label }}
              <input
                v-model.number="score.model.value"
                type="number"
                min="1"
                max="5"
                step="1"
                class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700"
              />
            </label>
          </div>

          <div class="flex items-center gap-3">
            <button
              type="button"
              class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              :disabled="isNlpTestLoading || !nlpTestText.trim()"
              @click="runNlpTest"
            >
              {{ isNlpTestLoading ? 'Analiz ediliyor...' : 'Analiz Et' }}
            </button>
            <p v-if="nlpTestError" class="text-sm font-medium text-rose-600">{{ nlpTestError }}</p>
          </div>
        </div>

        <div class="rounded-2xl border border-slate-900 bg-slate-950 p-5 text-white">
          <div v-if="nlpTestResult" class="space-y-5">
            <div class="grid grid-cols-2 gap-3">
              <div class="rounded-xl border border-white/10 bg-white/5 p-3">
                <p class="text-xs text-slate-400">Duygu</p>
                <p class="mt-1 text-lg font-bold">{{ formatSentiment(nlpTestAnalysis.sentiment_label) }}</p>
                <p class="text-xs text-slate-400">{{ nlpTestAnalysis.sentiment_score ?? 0 }}</p>
              </div>
              <div class="rounded-xl border border-white/10 bg-white/5 p-3">
                <p class="text-xs text-slate-400">Flight risk</p>
                <p class="mt-1 text-lg font-bold">{{ formatRiskLabel(nlpTestAnalysis.flight_risk) }}</p>
                <p class="text-xs text-slate-400">{{ nlpTestAnalysis.flight_risk_score ?? '-' }}/10</p>
              </div>
              <div class="rounded-xl border border-white/10 bg-white/5 p-3">
                <p class="text-xs text-slate-400">Motivasyon</p>
                <p class="mt-1 text-lg font-bold">{{ nlpTestAnalysis.motivation_score ?? '-' }}/5</p>
              </div>
              <div class="rounded-xl border border-white/10 bg-white/5 p-3">
                <p class="text-xs text-slate-400">Psikolojik guven</p>
                <p class="mt-1 text-lg font-bold">{{ nlpTestAnalysis.psychological_safety_score ?? '-' }}/5</p>
              </div>
            </div>

            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Yonetici ozeti</p>
              <p class="mt-2 text-sm leading-relaxed text-slate-200">{{ renderText(nlpTestAnalysis.manager_summary) }}</p>
            </div>

            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Aksiyon</p>
              <p class="mt-2 text-sm leading-relaxed text-slate-200">{{ renderText(nlpTestAnalysis.action_recommendation) }}</p>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <p class="text-xs font-semibold text-slate-400">Temalar</p>
                <div class="mt-2 flex flex-wrap gap-2">
                  <span v-for="item in nlpTestList('theme_labels')" :key="`theme-${item}`" class="rounded-full bg-indigo-400/15 px-2 py-1 text-xs text-indigo-100">
                    {{ renderText(item) }}
                  </span>
                </div>
              </div>
              <div>
                <p class="text-xs font-semibold text-slate-400">Risk bayraklari</p>
                <div class="mt-2 flex flex-wrap gap-2">
                  <span v-for="item in nlpTestList('risk_flags')" :key="`risk-${item}`" class="rounded-full bg-rose-400/15 px-2 py-1 text-xs text-rose-100">
                    {{ renderText(item) }}
                  </span>
                </div>
              </div>
            </div>

            <div class="rounded-xl border border-white/10 bg-white/5 p-3">
              <p class="text-xs text-slate-400">Guven skoru</p>
              <p class="mt-1 text-sm text-slate-200">{{ nlpTestAnalysis.confidence ?? '-' }}</p>
            </div>
          </div>
          <div v-else class="flex h-full min-h-[320px] items-center justify-center text-center text-sm text-slate-400">
            Test sonucu burada gorunecek.
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-[minmax(0,1.2fr)_360px] gap-6">
      <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex items-center justify-between gap-3">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">AylÄ±k Derin Analiz</p>
            <h4 class="mt-1 text-lg font-bold text-slate-900">Departman trend ve tema Ã¶zeti</h4>
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
              <p class="text-xs text-slate-500">Ortalama ayrÄ±lma riski</p>
              <p class="mt-2 text-xl font-bold text-slate-900">{{ monthlyDeepAnalysis.avg_flight_risk_score ?? '-' }}/10</p>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="rounded-xl border border-rose-100 bg-rose-50 p-4">
              <p class="text-xs font-semibold text-rose-700">En sÄ±k ÅŸikayet konularÄ±</p>
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
              <p class="text-xs font-semibold text-emerald-700">En sÄ±k Ã¶vgÃ¼ konularÄ±</p>
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
              <p class="text-xs font-semibold text-sky-700">Ã–ne Ã§Ä±kan temalar</p>
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
          Bu ay iÃ§in departman derin analiz verisi henÃ¼z oluÅŸmadÄ±.
        </div>

        <div v-if="monthlyRagReport" class="mt-6 rounded-2xl border border-violet-100 bg-violet-50 p-5">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.16em] text-violet-700">AylÄ±k HafÄ±zalÄ± Analiz</p>
              <p class="mt-2 text-sm leading-6 text-slate-700">{{ renderText(monthlyRagReport.report_summary) }}</p>
            </div>
            <span class="rounded-full border border-violet-200 bg-white px-3 py-1 text-xs font-semibold text-violet-700">
              {{ formatMemoryCount(monthlyRagReport.retrieved_memory_count) }}
            </span>
          </div>

          <div class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="rounded-xl border border-violet-100 bg-white p-4">
              <p class="text-xs font-semibold text-violet-700">Trend deÄŸerlendirmesi</p>
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
        <p class="text-xs uppercase tracking-[0.2em] text-slate-400">AylÄ±k Departman Ä°Ã§gÃ¶rÃ¼sÃ¼</p>
        <div v-if="monthlyDeepAnalysis" class="mt-5 space-y-4">
          <div class="rounded-xl border border-white/10 bg-white/5 p-4">
            <p class="text-xs font-semibold text-rose-300">Ã–ne Ã§Ä±kan risk nedenleri</p>
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
            <p class="text-xs font-semibold text-amber-300">Aksiyon Ã¶nerisi</p>
            <p class="mt-2 text-sm leading-6 text-slate-200">
              {{ renderText(monthlyDeepAnalysis.action_recommendation || 'Departman iÃ§in aylÄ±k aksiyon Ã¶nerisi henÃ¼z oluÅŸmadÄ±.') }}
            </p>
          </div>

          <div class="rounded-xl border border-white/10 bg-white/5 p-4">
            <p class="text-xs font-semibold text-indigo-300">Analiz kapsamÄ±</p>
            <p class="mt-2 text-sm leading-6 text-slate-200">
              Bu rapor {{ monthlyDeepAnalysis.analyzed_employee_count }} Ã§alÄ±ÅŸanÄ±n toplam {{ monthlyDeepAnalysis.analyzed_feedback_count }} feedback cevabÄ±ndan oluÅŸtu.
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
          AylÄ±k departman iÃ§gÃ¶rÃ¼leri veri geldikÃ§e burada gÃ¶sterilecek.
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { BoltIcon, HeartIcon, CheckCircleIcon, ScaleIcon, SparklesIcon, ExclamationTriangleIcon, TrophyIcon } from '@heroicons/vue/24/outline'
import StatCard from '@/components/dashboard/StatCard.vue'
import LineChart from '@/components/dashboard/LineChart.vue'
import BarChart from '@/components/dashboard/BarChart.vue'
import { feedbackApi, type Department360SummaryReportResponse, type DepartmentMonthlyDeepAnalysisResponse, type DepartmentMonthlyRAGReportResponse, type DepartmentNLPChartsResponse, type NLPTestAnalysisResponse, type SummaryMetric } from '@/services/api/feedback.api'
import { employeeApi } from '@/services/api/employee.api'
import { useAuthStore } from '@/stores/auth'

const departmentReport = ref<Department360SummaryReportResponse | null>(null)
const departmentCharts = ref<DepartmentNLPChartsResponse | null>(null)
const monthlyDeepAnalysis = ref<DepartmentMonthlyDeepAnalysisResponse | null>(null)
const monthlyRagReport = ref<DepartmentMonthlyRAGReportResponse | null>(null)
const today = new Date()
const selectedMonth = ref<number>(today.getMonth() + 1)
const selectedYear = ref<number>(today.getFullYear())
const selectedTeam = ref<string>('all')
const nlpTestText = ref('Bu hafta code review surecinde cok destekleyiciydi; blokajimi hizla acti ve ekibe guven verdi.')
const nlpScoreCommunication = ref(4)
const nlpScoreTeamwork = ref(4)
const nlpScoreLeadership = ref(4)
const nlpScoreTechnical = ref(4)
const nlpTestResult = ref<NLPTestAnalysisResponse | null>(null)
const isNlpTestLoading = ref(false)
const nlpTestError = ref('')

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin' || localStorage.getItem('role') === 'admin')
const departments = ref<any[]>([])
const employees = ref<any[]>([])
const selectedDepartment = ref<number | null>(null)

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

const nlpTestSamples = [
  {
    label: 'Olumlu sinyal',
    text: 'Bu hafta code review surecinde cok destekleyiciydi; blokajimi hizla acti ve ekibe guven verdi.',
    scores: [4, 4, 4, 4],
  },
  {
    label: 'Burnout riski',
    text: 'Son iki haftadir deadline baskisi ve toplanti yogunlugu nedeniyle cok yorulmus gorunuyor; destek istemekte cekingen kaliyor.',
    scores: [2, 2, 2, 2],
  },
  {
    label: 'Flight riski',
    text: 'Artik fikirlerinin onemsenmedigini soyluyor, ekipten kopuk davraniyor ve blokajlar cozulmedigi icin motivasyonu belirgin dusmus.',
    scores: [2, 2, 1, 2],
  },
]

const nlpScoreControls = [
  { key: 'communication', label: 'Iletisim', model: nlpScoreCommunication },
  { key: 'teamwork', label: 'Takim', model: nlpScoreTeamwork },
  { key: 'leadership', label: 'Liderlik', model: nlpScoreLeadership },
  { key: 'technical', label: 'Teknik', model: nlpScoreTechnical },
]

const scopedEmployees = computed(() => employees.value.filter((employee) => {
  const isEmployee = employee?.user?.role === 'employee'
  const inDepartment = !selectedDepartment.value || employee.department_id === selectedDepartment.value
  const inTeam = selectedTeam.value === 'all' || employee.team === selectedTeam.value
  const hasOperationalTeam = employee.team && employee.team !== 'Yonetim'
  return isEmployee && inDepartment && inTeam && hasOperationalTeam
}))

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
    yukselis: 'YÃ¼kseliÅŸ',
    dusus: 'DÃ¼ÅŸÃ¼ÅŸ',
    stabil: 'Stabil',
  }
  return map[value] || 'Stabil'
}

function formatRiskLabel(value?: string | null) {
  const map: Record<string, string> = {
    low: 'DÃ¼ÅŸÃ¼k',
    medium: 'Orta',
    high: 'YÃ¼ksek',
  }
  return value ? (map[value] || value) : '-'
}

function formatSentiment(value?: string | null) {
  const map: Record<string, string> = {
    positive: 'Olumlu',
    neutral: 'Notr',
    negative: 'Olumsuz',
  }
  return value ? (map[value] || value) : '-'
}

function formatMemoryCount(value: number) {
  return `${value} benzer kayÄ±t`
}

function renderText(value?: string | null) {
  if (!value) return ''

  const replacements: Array<[string, string]> = [
    ['surec yavasligi', 'sÃ¼reÃ§ yavaÅŸlÄ±ÄŸÄ±'],
    ['toplanti yogunlugu', 'toplantÄ± yoÄŸunluÄŸu'],
    ['deadline baskisi', 'deadline baskÄ±sÄ±'],
    ['mentorluk eksikligi', 'mentorluk eksikliÄŸi'],
    ['psikolojik guven', 'psikolojik gÃ¼ven'],
    ['is birligi', 'iÅŸ birliÄŸi'],
    ['gelisime aciklik', 'geliÅŸime aÃ§Ä±klÄ±k'],
    ['teknik borc', 'teknik borÃ§'],
    ['liderlik destegi', 'liderlik desteÄŸi'],
    ['yonetsel destek', 'yÃ¶netsel destek'],
    ['yukselis', 'yÃ¼kseliÅŸ'],
    ['dusus', 'dÃ¼ÅŸÃ¼ÅŸ'],
    ['gorunuyor', 'gÃ¶rÃ¼nÃ¼yor'],
    ['Tekrarlanan sikayet konulari', 'Tekrarlanan ÅŸikayet konularÄ±'],
    ['En belirgin sikayet alanlari', 'En belirgin ÅŸikayet alanlarÄ±'],
    ['Gecmis benzer yorumlar', 'GeÃ§miÅŸ benzer yorumlar'],
    ['kayitta', 'kayÄ±tta'],
    ['ayrilma riski', 'ayrÄ±lma riski'],
    ['Departmanda tekrar eden ana risk temasi', 'Departmanda tekrar eden ana risk temasÄ±'],
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
const nlpTestAnalysis = computed(() => nlpTestResult.value?.analysis || {})

function applyNlpSample(sample: { text: string; scores: number[] }) {
  nlpTestText.value = sample.text
  nlpScoreCommunication.value = sample.scores[0]
  nlpScoreTeamwork.value = sample.scores[1]
  nlpScoreLeadership.value = sample.scores[2]
  nlpScoreTechnical.value = sample.scores[3]
  nlpTestError.value = ''
}

function nlpTestList(key: string) {
  const value = nlpTestAnalysis.value[key]
  return Array.isArray(value) ? value.filter((item) => String(item).trim()).slice(0, 5) : []
}

async function runNlpTest() {
  if (!nlpTestText.value.trim()) return
  isNlpTestLoading.value = true
  nlpTestError.value = ''
  try {
    nlpTestResult.value = await feedbackApi.testNlpAnalysis({
      response_text: nlpTestText.value,
      department_id: currentDepartmentParam(),
      target_role: 'employee',
      score_communication: nlpScoreCommunication.value,
      score_teamwork: nlpScoreTeamwork.value,
      score_leadership: nlpScoreLeadership.value,
      score_technical: nlpScoreTechnical.value,
    })
  } catch (error) {
    console.error('NLP test analizi calistirilamadi:', error)
    nlpTestError.value = 'Analiz calistirilamadi.'
  } finally {
    isNlpTestLoading.value = false
  }
}

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
  await loadDepartmentReport()
  await loadDepartmentCharts()
  await loadMonthlyDeepAnalysis()
})

onMounted(async () => {
  await loadDepartments()
  await loadDepartmentReport()
  await loadDepartmentCharts()
  await loadMonthlyDeepAnalysis()
})
</script>
