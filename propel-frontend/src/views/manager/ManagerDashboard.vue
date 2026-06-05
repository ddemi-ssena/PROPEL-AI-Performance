<template>
  <div class="space-y-6 pb-10">
    <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
            Hibrit Dashboard
          </p>
          <h1 class="mt-2 text-3xl font-bold tracking-tight text-slate-900">
            Departman Performans&#305;
          </h1>
          <p class="mt-2 text-sm text-slate-600">
            KPI/ML + 360 Feedback + Haftal&#305;k Nab&#305;z
          </p>
        </div>

        <div class="text-left lg:text-right">
          <p class="text-xs text-slate-500">
            Son g&#252;ncelleme: {{ formatDateTime(dashboard?.generated_at) }}
          </p>
          <button
            type="button"
            class="mt-3 inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
            :disabled="loading"
            @click="refreshDashboard(false)"
          >
            <ArrowPathIcon class="h-4 w-4" :class="{ 'animate-spin': loading }" />
            Yenile
          </button>
        </div>
      </div>

      <div class="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
          <p class="text-sm text-slate-600">Departman</p>
          <p class="mt-2 text-2xl font-bold text-slate-900">{{ department.name }}</p>
        </div>
        <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
          <p class="text-sm text-slate-600">&#199;al&#305;&#351;an Say&#305;s&#305;</p>
          <p class="mt-2 text-2xl font-bold text-slate-900">{{ department.member_count }}</p>
        </div>
        <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
          <p class="text-sm text-slate-600">Tak&#305;m Say&#305;s&#305;</p>
          <p class="mt-2 text-2xl font-bold text-slate-900">{{ department.team_count }}</p>
        </div>
        <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
          <label for="dashboard-period" class="text-sm text-slate-600">Rapor D&#246;nemi</label>
          <select
            id="dashboard-period"
            v-model="selectedPeriod"
            class="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700"
            @change="refreshDashboard(false)"
          >
            <option value="week">Bu Hafta</option>
            <option value="month">Bu Ay</option>
            <option value="quarter">Bu &#199;eyrek</option>
            <option value="year">Bu Y&#305;l</option>
          </select>
        </div>
      </div>

      <div class="mt-6 rounded-2xl border border-blue-100 bg-blue-50 p-4">
        <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 class="text-sm font-bold text-slate-900">Veri Kapsama Oran&#305;</h2>
            <p class="mt-1 text-xs text-slate-600">
              Hibrit skorun güveni: {{ score(coverage.confidence_score) }}/100
            </p>
          </div>
          <span class="rounded-full bg-white px-3 py-1 text-xs font-bold text-blue-700">
            {{ coverage.confidence_score }}% confidence
          </span>
        </div>

        <div class="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <CoverageTile
            title="KPI/ML Analizi"
            tone="blue"
            :main="`${coverage.kpi_employee_count}/${department.member_count}`"
            :sub="`${coverage.kpi_percentage}% çalışan`"
            :date="formatDateTime(coverage.last_kpi_update)"
          />
          <CoverageTile
            title="Haftal&#305;k Nab&#305;z"
            tone="emerald"
            :main="`${coverage.pulse_response_count}/${department.member_count}`"
            :sub="`${coverage.pulse_percentage}% cevap`"
            :date="formatDate(coverage.last_pulse_update)"
          />
          <CoverageTile
            title="360 Feedback"
            tone="violet"
            :main="`${coverage.feedback_response_count}`"
            :sub="`${coverage.feedback_employee_count} kisi, ${coverage.feedback_percentage}% kapsama`"
            :date="formatDateTime(coverage.last_feedback_update)"
          />
        </div>
      </div>
    </section>

    <div v-if="loading" class="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500 shadow-sm">
      Hibrit departman verileri yükleniyor...
    </div>

    <div v-else-if="errorMessage" class="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
      {{ errorMessage }}
    </div>

    <template v-else>
      <section class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KPICard
          v-for="card in hybridScoreCards"
          :key="card.title"
          :card="card"
        />
      </section>

      <section class="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-600">
                Departman Genel Durumu
              </p>
              <h2 class="mt-2 text-xl font-bold text-slate-900">Hibrit sağlık özeti</h2>
            </div>
            <div class="flex flex-col items-end gap-2">
              <span class="rounded-full px-3 py-1 text-xs font-bold" :class="statusBadge(overallStatus)">
                {{ statusLabel(overallStatus) }}
              </span>
              <button
                type="button"
                class="rounded-xl border border-indigo-200 bg-indigo-50 px-3 py-2 text-xs font-bold text-indigo-700 shadow-sm transition hover:bg-indigo-100 disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="loading || llmLoading"
                @click="refreshDashboard(true)"
              >
                {{ llmLoading ? 'LLM yorumluyor...' : 'LLM ile detaylı yorumla' }}
              </button>
            </div>
          </div>

          <div class="mt-6 grid grid-cols-[auto_minmax(0,1fr)] gap-5">
            <HybridGauge
              title="Genel Sa&#287;l&#305;k"
              :value="scores.department_health"
              :risk-mode="false"
            />
            <div class="min-w-0">
              <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <div class="mb-2 flex flex-wrap items-center gap-2">
                  <span class="rounded-full bg-white px-2.5 py-1 text-[11px] font-bold text-slate-600">
                    {{ aiSummarySourceLabel }}
                  </span>
                  <span class="rounded-full bg-white px-2.5 py-1 text-[11px] font-bold text-slate-600">
                    Backend skorları: gerçek API sonucu
                  </span>
                </div>
                <p class="text-sm leading-6 text-slate-700">{{ aiSummary.summary }}</p>
              </div>

              <div
                v-if="aiSummary.strengths.length || aiSummary.risks.length || aiSummary.recommendations.length"
                class="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-3"
              >
                <div class="rounded-xl border border-emerald-100 bg-emerald-50 p-3">
                  <p class="text-xs font-bold uppercase tracking-[0.14em] text-emerald-700">Güçlü kanıtlar</p>
                  <ul class="mt-2 space-y-1 text-xs leading-5 text-emerald-950">
                    <li v-for="item in aiSummary.strengths" :key="item">- {{ item }}</li>
                  </ul>
                </div>
                <div class="rounded-xl border border-rose-100 bg-rose-50 p-3">
                  <p class="text-xs font-bold uppercase tracking-[0.14em] text-rose-700">Risk yorumu</p>
                  <ul class="mt-2 space-y-1 text-xs leading-5 text-rose-950">
                    <li v-for="item in aiSummary.risks" :key="item">- {{ item }}</li>
                  </ul>
                </div>
                <div class="rounded-xl border border-indigo-100 bg-indigo-50 p-3">
                  <p class="text-xs font-bold uppercase tracking-[0.14em] text-indigo-700">Yönetici aksiyonu</p>
                  <ul class="mt-2 space-y-1 text-xs leading-5 text-indigo-950">
                    <li v-for="item in aiSummary.recommendations" :key="item">- {{ item }}</li>
                  </ul>
                </div>
              </div>

              <div class="mt-4 flex flex-wrap gap-2">
                <span class="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">
                  KPI/ML %{{ scores.weights.kpiMl ?? 0 }}
                </span>
                <span class="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-700">
                  Nabız %{{ scores.weights.weeklyPulse ?? 0 }}
                </span>
                <span class="rounded-full bg-violet-50 px-3 py-1 text-xs font-bold text-violet-700">
                  360 %{{ scores.weights.feedback360 ?? 0 }}
                </span>
                <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
                  Güven {{ score(scores.confidence_score) }}/100
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
                Kaynak Durumlar&#305;
              </p>
              <h2 class="mt-2 text-xl font-bold text-slate-900">Her kayna&#287;&#305; ayr&#305; oku</h2>
            </div>
            <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
              {{ generalStatusRows.length }} sinyal
            </span>
          </div>

          <div class="mt-5 space-y-4">
            <div
              v-for="row in generalStatusRows"
              :key="row.key"
              class="rounded-xl border border-slate-100 bg-slate-50 p-4"
            >
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
                <div class="min-w-0">
                  <p class="font-bold text-slate-900">{{ row.label }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ row.description }}</p>
                  <div class="mt-3 h-2 overflow-hidden rounded-full bg-white">
                    <div
                      class="h-full rounded-full"
                      :class="row.barClass"
                      :style="{ width: `${row.progress}%` }"
                    ></div>
                  </div>
                  <p class="mt-2 text-xs font-semibold text-slate-400">{{ row.detail }}</p>
                </div>
                <HybridGauge
                  :title="row.gaugeTitle"
                  :value="row.progress"
                  :display="row.display"
                  :risk-mode="row.riskMode"
                  size="sm"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <SourceSummaryCard
          v-for="source in sourceCards"
          :key="source.key"
          :source="source"
        />
      </section>

      <DepartmentTrendChart
        title="Hibrit Takım Karşılaştırması"
        eyebrow="Takım Bazlı Hibrit Okuma"
        description="Bu grafik zaman trendi değil; Yazılım departmanındaki takımları aynı ölçekte karşılaştırır. Performans KPI/ML tahmininden, kapasite haftalık nabızdan, risk skoru ise KPI/ML + nabız + 360 birleşik riskinden gelir."
        :data="departmentTrendData"
        :target="85"
        x-label-prefix="Takım"
        show-guide
      />

      <section class="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <PipelineTracking
          title="Hibrit Performans Pipeline"
          eyebrow="Departman Akışı"
          :stages="pipelineStages"
        />

        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-[0.16em] text-sky-600">Akış Özeti</p>
          <h2 class="mt-2 text-xl font-bold text-slate-900">Dönüşüm yorumları</h2>
          <div class="mt-5 space-y-3">
            <div
              v-for="item in pipelineInsights"
              :key="item"
              class="rounded-xl border border-sky-100 bg-sky-50 px-4 py-3 text-sm leading-6 text-sky-900"
            >
              {{ item }}
            </div>
          </div>
        </div>
      </section>

      <section class="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        <FunnelChart
          title="Hibrit analiz için veri tamamlığı"
          eyebrow="KPI + Nabız + 360 kapsamı"
          badge-text="Eksik veri kontrolü"
          description="Bu kart performans sonucunu değil, departman skorunu hesaplamak için gerekli veri kaynaklarının kaç çalışanda mevcut olduğunu gösterir."
          :rows="funnelRows"
        />

        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-[0.16em] text-violet-600">Eksik veri etkisi</p>
          <h2 class="mt-2 text-xl font-bold text-slate-900">Skorun hangi kısmı eksik veri yüzünden zayıf?</h2>
          <p class="mt-2 text-sm leading-6 text-slate-600">
            Hibrit skor KPI/ML, haftalık nabız ve 360 feedback sinyallerini birleştirir.
            Bir kaynak eksikse o alan skorlanamaz; bu kart eksikliğin hangi kaynaktan geldiğini ve karar güvenini nasıl etkilediğini açıklar.
          </p>
          <div class="mt-5 space-y-3">
            <div
              v-for="item in funnelInsights"
              :key="item.title"
              class="rounded-xl border border-violet-100 bg-violet-50 px-4 py-3"
            >
              <p class="text-sm font-bold text-violet-950">{{ item.title }}</p>
              <p class="mt-1 text-sm leading-6 text-violet-900">{{ item.description }}</p>
              <p class="mt-2 text-xs leading-5 text-violet-700">{{ item.impact }}</p>
            </div>
          </div>
        </div>
      </section>

      <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
              Hibrit İçgörüler
            </p>
            <h2 class="mt-2 text-xl font-bold text-slate-900">Kesişim analizi</h2>
            <p class="mt-2 text-sm text-slate-600">
              KPI/ML, haftalık nabız ve 360 kaynaklarının birlikte verdiği sinyaller.
            </p>
          </div>
          <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
            {{ insights.length }} bulgu
          </span>
        </div>

        <div class="mt-6 space-y-4">
          <article
            v-for="insight in insights"
            :key="`${insight.type}-${insight.title}`"
            class="rounded-r-2xl border-l-4 p-5"
            :class="insightTone(insight.severity).surface"
          >
            <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p class="text-xs font-bold uppercase tracking-[0.12em]" :class="insightTone(insight.severity).text">
                  {{ insightTone(insight.severity).label }}
                </p>
                <h3 class="mt-1 text-lg font-bold text-slate-900">
                  {{ insight.title }}
                </h3>
              </div>
              <div class="flex flex-wrap gap-2">
                <span class="w-fit rounded-full px-2.5 py-1 text-xs font-bold" :class="insightTone(insight.severity).badge">
                  {{ actionLabel(insight.action) }}
                </span>
                <span class="w-fit rounded-full bg-white/80 px-2.5 py-1 text-xs font-bold text-slate-500">
                  {{ insightSourceLabel(insight) }}
                </span>
              </div>
            </div>
            <p class="mt-3 text-sm leading-6 text-slate-700">{{ insight.description }}</p>
            <p v-if="insight.team" class="mt-2 text-xs font-semibold text-slate-500">
              Takım: {{ insight.team }}
            </p>

            <div v-if="insight.evidence?.length" class="mt-4 rounded-xl border border-white/80 bg-white/70 p-4">
              <p class="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">Kanıtlar</p>
              <ul class="mt-2 grid grid-cols-1 gap-2 text-sm leading-5 text-slate-700 md:grid-cols-2">
                <li v-for="evidence in insight.evidence" :key="evidence" class="flex gap-2">
                  <span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400"></span>
                  <span>{{ evidence }}</span>
                </li>
              </ul>
            </div>

            <div class="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
              <div v-if="insight.manager_interpretation" class="rounded-xl bg-white/60 p-4">
                <p class="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">Yönetici yorumu</p>
                <p class="mt-2 text-sm leading-6 text-slate-700">{{ insight.manager_interpretation }}</p>
              </div>
              <div v-if="insight.impact" class="rounded-xl bg-white/60 p-4">
                <p class="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">Etkisi</p>
                <p class="mt-2 text-sm leading-6 text-slate-700">{{ insight.impact }}</p>
              </div>
            </div>

            <div class="mt-4 rounded-xl border border-slate-200 bg-white p-4">
              <p class="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">Önerilen aksiyon</p>
              <p class="mt-2 text-sm font-semibold leading-6 text-slate-900">
                {{ insight.recommendation }}
              </p>
            </div>

            <div v-if="insight.follow_up_metrics?.length" class="mt-3 flex flex-wrap gap-2">
              <span class="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">Takip:</span>
              <span
                v-for="metric in insight.follow_up_metrics"
                :key="metric"
                class="rounded-full bg-white/80 px-2.5 py-1 text-xs font-semibold text-slate-600"
              >
                {{ metric }}
              </span>
            </div>
          </article>
        </div>
      </section>

      <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
              Takım Karşılaştırması
            </p>
            <h2 class="mt-2 text-xl font-bold text-slate-900">Tüm metrikler</h2>
          </div>
          <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
            {{ teamBreakdown.length }} takım
          </span>
        </div>

        <div class="mt-6 overflow-x-auto">
          <table class="w-full min-w-[840px] text-sm">
            <thead class="bg-slate-50 text-slate-600">
              <tr>
                <th class="px-4 py-3 text-left font-semibold">Takım</th>
                <th class="px-4 py-3 text-right font-semibold">Sağlık</th>
                <th class="px-4 py-3 text-right font-semibold">KPI</th>
                <th class="px-4 py-3 text-right font-semibold">Nabız</th>
                <th class="px-4 py-3 text-right font-semibold">360</th>
                <th class="px-4 py-3 text-right font-semibold">Risk</th>
                <th class="px-4 py-3 text-center font-semibold">Status</th>
                <th class="px-4 py-3 text-center font-semibold">Trend</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="team in teamBreakdown"
                :key="team.team"
                class="border-t border-slate-100 hover:bg-slate-50"
              >
                <td class="px-4 py-3 font-semibold text-slate-900">
                  {{ team.team }} <span class="text-slate-400">({{ team.member_count }})</span>
                </td>
                <td class="px-4 py-3 text-right text-lg font-bold text-slate-900">{{ score(team.scores.health) }}</td>
                <td class="px-4 py-3 text-right">{{ score(team.scores.kpi) }}</td>
                <td class="px-4 py-3 text-right">{{ score(team.scores.pulse) }}</td>
                <td class="px-4 py-3 text-right">{{ score(team.scores.feedback) }}</td>
                <td class="px-4 py-3 text-right font-bold text-orange-600">{{ score(team.scores.risk) }}</td>
                <td class="px-4 py-3 text-center">
                  <span class="rounded-full px-2.5 py-1 text-xs font-bold" :class="statusBadge(team.status)">
                    {{ statusLabel(team.status) }}
                  </span>
                </td>
                <td class="px-4 py-3 text-center font-bold" :class="trendClass(team.trend)">
                  {{ trendIcon(team.trend) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,0.85fr)]">
        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.16em] text-blue-600">AI Özet</p>
              <h2 class="mt-2 text-xl font-bold text-slate-900">Birleşik departman yorumu</h2>
            </div>
            <span class="w-fit rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-700">
              {{ aiSummarySourceLabel }}
            </span>
          </div>
          <p class="mt-4 text-sm leading-6 text-slate-700">{{ aiSummary.summary }}</p>

          <div class="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
            <SummaryList title="AI'nin Dayandığı Güçlü Kanıtlar" :items="aiSummary.strengths" tone="emerald" />
            <SummaryList title="AI Risk Yorumu" :items="aiSummary.risks" tone="rose" />
            <SummaryList title="AI Aksiyon Önerileri" :items="aiSummary.recommendations" tone="blue" />
          </div>
        </div>

        <div class="grid grid-cols-1 gap-6">
          <RiskIndicators :risks="riskIndicatorGroups" />
          <QuickActions :actions="quickActionItems" />
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref, type Component, type PropType } from 'vue'
import {
  ArrowPathIcon,
  ChartBarIcon,
  ChartPieIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  SparklesIcon,
  UsersIcon,
} from '@heroicons/vue/24/outline'
import KPICard from '@/components/dashboard/KPICard.vue'
import PipelineTracking, { type PipelineStage } from '@/components/dashboard/PipelineTracking.vue'
import FunnelChart, { type FunnelRow } from '@/components/dashboard/FunnelChart.vue'
import DepartmentTrendChart, { type DepartmentTrendPoint } from '@/components/dashboard/DepartmentTrendChart.vue'
import RiskIndicators, { type RiskIndicatorGroups } from '@/components/dashboard/RiskIndicators.vue'
import QuickActions, { type QuickActionItem } from '@/components/dashboard/QuickActions.vue'
import {
  analyticsApi,
  type DepartmentDashboardAISummaryResponse,
  type DepartmentDashboardCoverageResponse,
  type DepartmentDashboardDepartmentResponse,
  type DepartmentDashboardInsightResponse,
  type DepartmentDashboardSourceResponse,
  type DepartmentDashboardTeamResponse,
  type SoftwareDepartmentDashboardResponse,
} from '@/services/api/analytics.api'

type SourceCard = {
  key: string
  title: string
  badge: string
  tone: 'emerald' | 'blue' | 'violet'
  source: DepartmentDashboardSourceResponse
  metrics: Array<{ label: string; value: string; hint?: string }>
  explainer: string
}

const selectedPeriod = ref<'week' | 'month' | 'quarter' | 'year'>('week')
const dashboard = ref<SoftwareDepartmentDashboardResponse | null>(null)
const loading = ref(false)
const llmLoading = ref(false)
const errorMessage = ref('')

const emptyDepartment: DepartmentDashboardDepartmentResponse = {
  id: 0,
  name: 'Yazılım Geliştirme',
  member_count: 0,
  team_count: 0,
  teams: [],
}

const emptyCoverage: DepartmentDashboardCoverageResponse = {
  kpi_employee_count: 0,
  kpi_percentage: 0,
  pulse_response_count: 0,
  pulse_employee_count: 0,
  pulse_percentage: 0,
  feedback_response_count: 0,
  feedback_employee_count: 0,
  feedback_percentage: 0,
  confidence_score: 0,
  last_kpi_update: null,
  last_pulse_update: null,
  last_feedback_update: null,
}

const emptyAiSummary: DepartmentDashboardAISummaryResponse = {
  summary: 'Hibrit dashboard verisi yüklenince birleşik özet burada görünecek.',
  strengths: [],
  risks: [],
  recommendations: [],
  source: 'deterministic',
  model: null,
  fallback_used: false,
}

const mojibakeReplacements: Array<[RegExp, string]> = [
  [/Ä±/g, 'ı'],
  [/Ä°/g, 'İ'],
  [/ÄŸ/g, 'ğ'],
  [/Äž/g, 'Ğ'],
  [/ÅŸ/g, 'ş'],
  [/Åž/g, 'Ş'],
  [/Ã¼/g, 'ü'],
  [/Ãœ/g, 'Ü'],
  [/Ã¶/g, 'ö'],
  [/Ã–/g, 'Ö'],
  [/Ã§/g, 'ç'],
  [/Ã‡/g, 'Ç'],
]

function repairText(value?: string | null) {
  if (!value) return value
  let repaired = value
  for (let index = 0; index < 2; index += 1) {
    try {
      const decoded = decodeURIComponent(escape(repaired))
      if (decoded === repaired) break
      repaired = decoded
    } catch {
      break
    }
  }
  for (const [pattern, replacement] of mojibakeReplacements) {
    repaired = repaired.replace(pattern, replacement)
  }
  return repaired
}

const department = computed(() => {
  const source = dashboard.value?.department || emptyDepartment
  return {
    ...source,
    name: repairText(source.name) || source.name,
    teams: source.teams.map((team) => repairText(team) || team),
  }
})
const coverage = computed(() => dashboard.value?.coverage || emptyCoverage)
const scores = computed(() => dashboard.value?.scores || {
  department_health: 0,
  execution_score: 0,
  people_health_score: 0,
  risk_score: 0,
  confidence_score: 0,
  weights: {},
})
const sources = computed(() => dashboard.value?.sources || {})
const insights = computed<DepartmentDashboardInsightResponse[]>(() => dashboard.value?.hybrid_insights || [])
const teamBreakdown = computed<DepartmentDashboardTeamResponse[]>(() => dashboard.value?.team_breakdown || [])
const aiSummary = computed(() => dashboard.value?.ai_summary || emptyAiSummary)
const aiSummarySourceLabel = computed(() => {
  if (aiSummary.value.fallback_used) return 'Kural bazlı özet'
  if (['gemini', 'ollama'].includes(aiSummary.value.source)) return 'LLM yorumu'
  if (aiSummary.value.source?.includes('llm')) return 'LLM yorumu'
  return 'Kural bazlı özet'
})

const CoverageTile = defineComponent({
  props: {
    title: { type: String, required: true },
    tone: { type: String as PropType<'blue' | 'emerald' | 'violet'>, required: true },
    main: { type: String, required: true },
    sub: { type: String, required: true },
    date: { type: String, required: true },
  },
  setup(props) {
    const toneClass = computed(() => ({
      blue: 'border-blue-100 bg-white text-blue-700',
      emerald: 'border-emerald-100 bg-white text-emerald-700',
      violet: 'border-violet-100 bg-white text-violet-700',
    }[props.tone]))
    return () => h('div', { class: `rounded-xl border p-4 ${toneClass.value}` }, [
      h('p', { class: 'text-sm font-semibold text-slate-700' }, props.title),
      h('p', { class: 'mt-2 text-2xl font-bold' }, props.main),
      h('p', { class: 'mt-1 text-xs text-slate-600' }, props.sub),
      h('p', { class: 'mt-1 text-xs text-slate-400' }, `Son: ${props.date}`),
    ])
  },
})

const SourceSummaryCard = defineComponent({
  props: {
    source: { type: Object as PropType<SourceCard>, required: true },
  },
  setup(props) {
    const toneClass = computed(() => ({
      emerald: {
        accent: 'border-emerald-500',
        badge: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-100',
        explainer: 'border-emerald-100 bg-emerald-50/70 text-emerald-950',
        rule: 'text-emerald-700',
      },
      blue: {
        accent: 'border-blue-500',
        badge: 'bg-blue-50 text-blue-700 ring-1 ring-blue-100',
        explainer: 'border-blue-100 bg-blue-50/70 text-blue-950',
        rule: 'text-blue-700',
      },
      violet: {
        accent: 'border-violet-500',
        badge: 'bg-violet-50 text-violet-700 ring-1 ring-violet-100',
        explainer: 'border-violet-100 bg-violet-50/70 text-violet-950',
        rule: 'text-violet-700',
      },
    }[props.source.tone]))
    const statusRule = computed(() => statusRuleText(props.source.source.status))

    return () => h('article', { class: `rounded-2xl border border-slate-200 border-l-4 bg-white p-6 shadow-sm ${toneClass.value.accent}` }, [
      h('div', { class: 'mb-5 flex items-start justify-between gap-3' }, [
        h('div', [
          h('p', { class: 'text-xs font-semibold uppercase tracking-[0.16em] text-slate-400' }, props.source.badge),
          h('h3', { class: 'mt-2 text-lg font-bold text-slate-900' }, props.source.title),
          h('p', { class: `mt-2 text-xs font-semibold ${toneClass.value.rule}` }, statusRule.value),
        ]),
        h('span', { class: `rounded-full px-2.5 py-1 text-xs font-bold ${toneClass.value.badge}` }, statusLabel(props.source.source.status)),
      ]),
      h('div', { class: 'space-y-4' }, props.source.metrics.map((metric) => h('div', { class: 'border-t border-slate-100 pt-3 first:border-t-0 first:pt-0' }, [
        h('p', { class: 'text-sm text-slate-500' }, metric.label),
        h('p', { class: 'mt-1 text-2xl font-bold text-slate-900' }, metric.value),
        metric.hint ? h('p', { class: 'mt-1 text-xs text-slate-400' }, metric.hint) : null,
      ]))),
      h('div', { class: `mt-5 rounded-xl border p-4 text-sm ${toneClass.value.explainer}` }, [
        h('p', { class: 'font-bold text-slate-900' }, 'Ne ölçüyor?'),
        h('p', { class: 'mt-1 text-xs leading-5 text-slate-700' }, props.source.explainer),
      ]),
    ])
  },
})

const HybridGauge = defineComponent({
  props: {
    title: { type: String, required: true },
    value: { type: Number, required: true },
    display: { type: String, default: '' },
    riskMode: { type: Boolean, default: false },
    size: { type: String as PropType<'md' | 'sm'>, default: 'md' },
  },
  setup(props) {
    const normalized = computed(() => clamp(score(props.value), 0, 100))
    const isSmall = computed(() => props.size === 'sm')
    const displayValue = computed(() => props.display || `${normalized.value}/100`)
    const status = computed(() => props.riskMode ? riskLabel(normalized.value) : scoreStatus(normalized.value))
    const statusClass = computed(() => props.riskMode ? riskToneClass(normalized.value) : scoreToneClass(normalized.value))
    const radius = computed(() => isSmall.value ? 46 : 54)
    const centerX = 80
    const centerY = 84
    const startX = computed(() => centerX - radius.value)
    const endX = computed(() => {
      const radians = (180 - normalized.value * 1.8) * Math.PI / 180
      return centerX + radius.value * Math.cos(radians)
    })
    const endY = computed(() => {
      const radians = (180 - normalized.value * 1.8) * Math.PI / 180
      return centerY - radius.value * Math.sin(radians)
    })
    const needleX = computed(() => {
      const radians = (180 - normalized.value * 1.8) * Math.PI / 180
      return centerX + (radius.value - 14) * Math.cos(radians)
    })
    const needleY = computed(() => {
      const radians = (180 - normalized.value * 1.8) * Math.PI / 180
      return centerY - (radius.value - 14) * Math.sin(radians)
    })
    const largeArc = computed(() => normalized.value > 50 ? 1 : 0)
    const progressPath = computed(() =>
      `M ${startX.value} ${centerY} A ${radius.value} ${radius.value} 0 ${largeArc.value} 1 ${endX.value} ${endY.value}`
    )
    const basePath = computed(() => `M ${startX.value} ${centerY} A ${radius.value} ${radius.value} 0 0 1 ${centerX + radius.value} ${centerY}`)
    const strokeColor = computed(() => {
      const value = normalized.value
      if (props.riskMode) {
        if (value >= 60) return '#e11d48'
        if (value >= 40) return '#f59e0b'
        return '#10b981'
      }
      if (value >= 80) return '#10b981'
      if (value >= 60) return '#f59e0b'
      return '#e11d48'
    })

    return () => h('div', { class: isSmall.value ? 'w-32 shrink-0 text-center' : 'w-40 shrink-0 text-center' }, [
      h('svg', {
        viewBox: '0 0 160 108',
        class: isSmall.value ? 'h-[86px] w-32 overflow-visible' : 'h-[100px] w-40 overflow-visible',
        role: 'img',
        'aria-label': `${props.title}: ${displayValue.value}`,
      }, [
        h('path', {
          d: basePath.value,
          fill: 'none',
          stroke: '#e5e7eb',
          'stroke-width': isSmall.value ? 9 : 11,
          'stroke-linecap': 'round',
        }),
        h('path', {
          d: progressPath.value,
          fill: 'none',
          stroke: strokeColor.value,
          'stroke-width': isSmall.value ? 9 : 11,
          'stroke-linecap': 'round',
        }),
        h('line', {
          x1: centerX,
          y1: centerY,
          x2: needleX.value,
          y2: needleY.value,
          stroke: '#0f172a',
          'stroke-width': isSmall.value ? 3 : 4,
          'stroke-linecap': 'round',
        }),
        h('circle', { cx: centerX, cy: centerY, r: isSmall.value ? 4 : 5, fill: '#0f172a', stroke: '#ffffff', 'stroke-width': 3 }),
      ]),
      h('div', { class: 'mt-2 text-center' }, [
        h('p', { class: `font-bold ${isSmall.value ? 'text-lg' : 'text-2xl'} ${statusClass.value}` }, displayValue.value),
        h('p', { class: 'mt-0.5 text-xs font-semibold text-slate-500' }, props.title),
        h('p', { class: `mt-0.5 text-xs font-bold ${statusClass.value}` }, status.value),
      ]),
      h('div', { class: 'mt-2 grid grid-cols-3 overflow-hidden rounded-lg border border-slate-200 text-[10px] font-semibold' }, [
        h('span', { class: 'bg-rose-50 py-1 text-center text-rose-600' }, 'Risk'),
        h('span', { class: 'bg-amber-50 py-1 text-center text-amber-600' }, 'Dikkat'),
        h('span', { class: 'bg-emerald-50 py-1 text-center text-emerald-600' }, 'İyi'),
      ]),
    ])
  },
})

const SummaryList = defineComponent({
  props: {
    title: { type: String, required: true },
    items: { type: Array as PropType<string[]>, required: true },
    tone: { type: String as PropType<'emerald' | 'rose' | 'blue'>, required: true },
  },
  setup(props) {
    const toneClass = computed(() => ({
      emerald: 'border-emerald-100 bg-emerald-50 text-emerald-900',
      rose: 'border-rose-100 bg-rose-50 text-rose-900',
      blue: 'border-blue-100 bg-blue-50 text-blue-900',
    }[props.tone]))
    return () => h('div', { class: `rounded-xl border p-4 ${toneClass.value}` }, [
      h('h3', { class: 'text-sm font-bold' }, props.title),
      h('ul', { class: 'mt-3 space-y-2 text-sm leading-5' },
        (props.items.length ? props.items : ['Veri geldikçe netleşecek.']).map((item) => h('li', item))
      ),
    ])
  },
})

const hybridScoreCards = computed(() => [
  buildScoreCard({
    title: 'Departman Sağlığı',
    subtitle: 'Aktif veri kaynaklarına göre',
    value: scores.value.department_health,
    target: '85',
    benchmark: `${scores.value.confidence_score} güven`,
    sourceNote: 'Backend: KPI/ML %50 + haftalık nabız %25 + 360 feedback %25 ağırlıklı hibrit skor.',
    icon: SparklesIcon,
  }),
  buildScoreCard({
    title: 'Performans Çıktıları',
    subtitle: 'KPI/ML analizi',
    value: scores.value.execution_score,
    target: '85',
    benchmark: 'Objektif',
    sourceNote: 'Backend: seçili software datasetindeki ML toplu tahminlerinden 100 - risk skoru.',
    icon: ChartBarIcon,
  }),
  buildScoreCard({
    title: 'İnsan Sağlığı',
    subtitle: '360 + haftalık nabız',
    value: scores.value.people_health_score,
    target: '80',
    benchmark: 'Davranış + psikoloji',
    sourceNote: 'Backend: haftalık nabız skoru ile 360 NLP skorunun ortalaması.',
    icon: UsersIcon,
  }),
  buildScoreCard({
    title: 'Risk Skoru',
    subtitle: 'Attrition + burnout + stres',
    value: scores.value.risk_score,
    target: '< 40',
    benchmark: riskLabel(scores.value.risk_score),
    sourceNote: 'Backend: KPI/ML riski, nabız stresi/ayrılma riski ve 360 burnout/flight risk ortalaması.',
    icon: ExclamationTriangleIcon,
    inverse: true,
  }),
])

const overallStatus = computed(() => {
  const health = scores.value.department_health
  if (health >= 85) return 'success'
  if (health >= 70) return 'warning'
  return 'danger'
})

const generalStatusRows = computed(() => [
  {
    key: 'kpi',
    label: 'KPI/ML Performans',
    description: 'Üretkenlik, hedef uyumu ve model bazlı performans riski.',
    display: `${score(scores.value.execution_score)}/100`,
    detail: `${coverage.value.kpi_employee_count}/${department.value.member_count} çalışan`,
    gaugeTitle: 'KPI/ML',
    riskMode: false,
    progress: score(scores.value.execution_score),
    valueClass: scoreToneClass(scores.value.execution_score),
    barClass: barToneClass(scores.value.execution_score),
  },
  {
    key: 'pulse',
    label: 'Haftalık Nabız',
    description: 'Motivasyon, bağlılık, stres ve ayrılma riski sinyali.',
    display: `${metric('weeklyPulse', 'motivationAverage')}/100`,
    detail: `${coverage.value.pulse_response_count} cevap`,
    gaugeTitle: 'Nabız',
    riskMode: false,
    progress: score(sources.value.weeklyPulse?.score ?? 0),
    valueClass: scoreToneClass(sources.value.weeklyPulse?.score ?? 0),
    barClass: barToneClass(sources.value.weeklyPulse?.score ?? 0),
  },
  {
    key: 'feedback',
    label: '360 Feedback',
    description: 'Psikolojik güven, iş birliği, destek ihtiyacı ve burnout NLP sinyali.',
    display: coverage.value.feedback_response_count ? `${score(sources.value.feedback360?.score ?? 0)}/100` : 'Veri yok',
    detail: `${coverage.value.feedback_response_count} analiz`,
    gaugeTitle: '360',
    riskMode: false,
    progress: coverage.value.feedback_response_count ? score(sources.value.feedback360?.score ?? 0) : 0,
    valueClass: coverage.value.feedback_response_count ? scoreToneClass(sources.value.feedback360?.score ?? 0) : 'text-slate-400',
    barClass: coverage.value.feedback_response_count ? barToneClass(sources.value.feedback360?.score ?? 0) : 'bg-slate-300',
  },
  {
    key: 'risk',
    label: 'Birleşik Risk',
    description: 'KPI/ML riski, nabız flight/stres sinyali ve 360 burnout riski.',
    display: `${score(scores.value.risk_score)}/100`,
    detail: riskLabel(scores.value.risk_score),
    gaugeTitle: 'Risk',
    riskMode: true,
    progress: score(scores.value.risk_score),
    valueClass: riskToneClass(scores.value.risk_score),
    barClass: riskBarClass(scores.value.risk_score),
  },
])

const sourceCards = computed<SourceCard[]>(() => [
  {
    key: 'kpiMl',
    title: 'Performans Çıktıları (KPI/ML)',
    badge: 'Objektif',
    tone: 'emerald' as const,
    source: sources.value.kpiMl,
    metrics: [
      { label: 'Ortalama Performans', value: `${metric('kpiMl', 'averagePerformance')}/100`, hint: `Trend: ${metric('kpiMl', 'trend')}` },
      { label: 'Hedef Uyumu', value: `${metric('kpiMl', 'targetAlignment')}/100` },
      { label: 'ML Risk Tahmini', value: `${metric('kpiMl', 'mlRiskScore')}/100` },
      { label: 'Yüksek Risk', value: `${metric('kpiMl', 'highRiskCount')} kişi` },
    ],
    explainer: 'Ne oldu? Üretkenlik, hedefe ulaşma, kalite ve model bazlı performans riski.',
  },
  {
    key: 'weeklyPulse',
    title: 'İnsan Sağlığı Sinyalleri (Nabız)',
    badge: 'Haftalık',
    tone: 'blue' as const,
    source: sources.value.weeklyPulse,
    metrics: [
      { label: 'Motivasyon Ort.', value: `${metric('weeklyPulse', 'motivationAverage')}/100`, hint: `Trend: ${metric('weeklyPulse', 'motivationTrend')}` },
      { label: 'Stres Seviyesi', value: `${metric('weeklyPulse', 'stressLevel')}/100` },
      { label: 'Bağlılık Skoru', value: `${metric('weeklyPulse', 'engagementScore')}/100` },
      { label: 'Ayrılma Riski', value: `${metric('weeklyPulse', 'attritionRisk')}/100` },
    ],
    explainer: 'Ekip bu hafta nasıl hissediyor? Motivasyon, duygu trendi, bağlılık ve ayrılma riski.',
  },
  {
    key: 'feedback360',
    title: 'Davranış ve İlişkiler (360)',
    badge: 'İlişkisel',
    tone: 'violet' as const,
    source: sources.value.feedback360,
    metrics: [
      { label: 'İş Birliği', value: `${metric('feedback360', 'collaborationScore')}/100` },
      { label: 'Psikolojik Güven', value: `${metric('feedback360', 'trustScore')}/100` },
      { label: 'Liderlik Desteği', value: `${metric('feedback360', 'leadershipSupportScore')}/100` },
      { label: 'Burnout Riski', value: `${metric('feedback360', 'burnoutRisk')}` },
    ],
    explainer: 'Ekip birbirini nasıl deneyimliyor? İş birliği, güven, destek ihtiyacı ve davranış sinyalleri.',
  },
].filter((item) => item.source))

const departmentTrendData = computed<DepartmentTrendPoint[]>(() => {
  const teams = teamBreakdown.value
  if (!teams.length) {
    return [{
      month: selectedPeriod.value,
      performance: score(scores.value.execution_score),
      capacity: score(scores.value.people_health_score),
      risk: score(scores.value.risk_score),
    }]
  }

  return teams.map((team) => ({
    month: team.team,
    performance: score(team.scores.kpi),
    capacity: score(team.scores.pulse),
    risk: score(team.scores.risk),
  }))
})

const pipelineStages = computed<PipelineStage[]>(() => {
  const total = Math.max(department.value.member_count, 1)
  const kpiCount = Math.min(coverage.value.kpi_employee_count, total)
  const pulseCount = Math.min(coverage.value.pulse_employee_count, total)
  const feedbackCount = Math.min(coverage.value.feedback_employee_count, total)
  const healthyTeams = teamBreakdown.value.filter((team) => (team.scores.health || 0) >= 70).length
  const actionCount = quickActionItems.value.length

  const rawStages = [
    {
      name: 'Departman Kapsamı',
      value: total,
      percentage: 100,
      color: '#ef5350',
    },
    {
      name: 'KPI/ML Verisi',
      value: kpiCount,
      percentage: coverage.value.kpi_percentage,
      color: '#ffa726',
    },
    {
      name: 'Nabız Verisi',
      value: pulseCount,
      percentage: coverage.value.pulse_percentage,
      color: '#29b6f6',
    },
    {
      name: '360 NLP Verisi',
      value: feedbackCount,
      percentage: coverage.value.feedback_percentage,
      color: '#8b5cf6',
    },
    {
      name: 'Sağlıklı Takım',
      value: healthyTeams,
      percentage: percent(healthyTeams, Math.max(teamBreakdown.value.length, 1)),
      color: '#66bb6a',
    },
    {
      name: 'Aksiyon Hazır',
      value: actionCount,
      percentage: percent(actionCount, Math.max(insights.value.length + teamBreakdown.value.length, 1)),
      color: '#ab47bc',
    },
  ]

  return rawStages.map((stage, index) => {
    const next = rawStages[index + 1]
    return {
      ...stage,
      percentage: clamp(Math.round(stage.percentage), 0, 100),
      conversionRate: next ? percent(Number(next.value), Math.max(Number(stage.value), 1)) : 0,
    }
  })
})

const pipelineInsights = computed(() => {
  const weakestCoverage = [
    { label: 'KPI/ML', value: coverage.value.kpi_percentage },
    { label: 'Haftalık Nabız', value: coverage.value.pulse_percentage },
    { label: '360 Feedback', value: coverage.value.feedback_percentage },
  ].sort((a, b) => a.value - b.value)[0]
  const weakestTeam = [...teamBreakdown.value].sort((a, b) => (a.scores.health || 0) - (b.scores.health || 0))[0]

  return [
    `En düşük veri kapsamı: ${weakestCoverage.label} (%${score(weakestCoverage.value)}).`,
    `Departman sağlığı ${score(scores.value.department_health)}/100; risk skoru ${score(scores.value.risk_score)}/100.`,
    weakestTeam
      ? `En düşük hibrit takım skoru ${weakestTeam.team}: ${score(weakestTeam.scores.health)}/100.`
      : 'Takım bazlı akış verisi geldikçe netleşecek.',
  ]
})

const funnelRows = computed<FunnelRow[]>(() => {
  const total = Math.max(department.value.member_count, 1)
  const fullSignalCount = Math.min(
    coverage.value.kpi_employee_count,
    coverage.value.pulse_employee_count,
    coverage.value.feedback_employee_count
  )

  const rows = [
    {
      stage: 'Departmandaki çalışanlar',
      value: total,
      description: 'Hibrit dashboardun baz aldığı toplam yazılım departmanı çalışan sayısı.',
    },
    {
      stage: 'KPI/ML verisi olanlar',
      value: coverage.value.kpi_employee_count,
      description: 'Performans, hedef uyumu ve ML risk sinyali hesaplanabilen çalışanlar.',
    },
    {
      stage: 'Nabız yanıtı olanlar',
      value: coverage.value.pulse_employee_count,
      description: 'Motivasyon, stres, bağlılık ve flight risk sinyali okunabilen çalışanlar.',
    },
    {
      stage: '360 NLP analizi olanlar',
      value: coverage.value.feedback_employee_count,
      description: 'Geri bildirim metinlerinden güven, iş birliği, destek ve burnout sinyali çıkarılabilen çalışanlar.',
    },
    {
      stage: 'Tam hibrit profili olanlar',
      value: fullSignalCount,
      description: 'KPI/ML, nabız ve 360 sinyali birlikte bulunan; en güvenilir hibrit yoruma giren çalışanlar.',
    },
  ]

  return rows.map((row, index) => {
    const previous = rows[index - 1]
    const conversion = index === 0 ? 100 : percent(Number(row.value), Math.max(Number(previous?.value), 1))
    return {
      stage: row.stage,
      value: row.value,
      conversion,
      dropoff: 100 - conversion,
      description: row.description,
    }
  })
})

const funnelInsights = computed(() => {
  const rows = funnelRows.value
  if (!rows.length) {
    return [{
      title: 'Veri bekleniyor',
      description: 'Hibrit analiz için henüz yeterli veri yok.',
      impact: 'KPI/ML, nabız veya 360 kaynaklarından veri geldikçe bu özet otomatik dolacak.',
    }]
  }
  const worstDrop = rows.slice(1).reduce((worst, row) => row.dropoff > worst.dropoff ? row : worst, rows[1] || rows[0])
  const last = rows[rows.length - 1]
  const total = Number(rows[0].value) || 1
  const fullProfileRate = percent(Number(last.value), total)
  const feedbackMissing = coverage.value.feedback_employee_count === 0

  return [
    {
      title: `Tam hibrit profil: ${last.value}/${rows[0].value} çalışan`,
      description: `Departmanda tüm veri kaynakları aynı çalışanda birleşen oran %${fullProfileRate}. Bu oran yükseldikçe departman sağlığı yorumu daha güvenilir hale gelir.`,
      impact: 'Tam profil olmayan çalışanlar yine dashboarda girer; ancak eksik kaynak olan boyutlar karar güvenini düşürür.',
    },
    {
      title: `En büyük eksik kaynak: ${worstDrop.stage}`,
      description: `Bu adımda önceki veri adımına göre %${worstDrop.dropoff} eksilme var. Yani hibrit skorun en zayıf veri halkası burada oluşuyor.`,
      impact: 'Önce bu kaynağın kapsamı artırılırsa hem veri güveni hem de içgörü kalitesi en hızlı şekilde iyileşir.',
    },
    feedbackMissing
      ? {
          title: '360 NLP sinyali henüz skora katılamıyor',
          description: '360 feedback analiz kaydı olmadığı için psikolojik güven, iş birliği, destek ihtiyacı ve burnout metin sinyalleri hesaplanamıyor.',
          impact: 'Bu yüzden insan sağlığı şu anda ağırlıkla nabız verisine dayanıyor; 360 cevapları geldikçe tam hibrit profil sayısı artacak.',
        }
      : {
          title: `360 NLP kapsami: %${score(coverage.value.feedback_percentage)}`,
          description: '360 feedback verisi mevcut olduğu için davranış ve ilişki kalitesi hibrit skora katılıyor.',
          impact: 'Bu kaynak KPI/ML sonucunu insan deneyimiyle birlikte yorumlamayı sağlar.',
        },
  ]
})

const riskIndicatorGroups = computed<RiskIndicatorGroups>(() => {
  const critical = insights.value
    .filter((item) => item.severity === 'critical')
    .map((item) => item.title)
  const warnings = insights.value
    .filter((item) => item.severity === 'warning')
    .map((item) => item.title)
  const positive = aiSummary.value.strengths.length
    ? aiSummary.value.strengths
    : [`Departman sağlık skoru ${score(scores.value.department_health)}/100`]

  return {
    critical: critical.length ? critical : ['Kritik birleşik risk sinyali yok.'],
    warnings: warnings.length ? warnings : ['Uyarı sinyali veri geldikçe netleşecek.'],
    positive: positive.slice(0, 3),
  }
})

const quickActionItems = computed<QuickActionItem[]>(() => {
  const actions = [
    ...((dashboard.value?.actions.urgent || []).map((item) => ({
      title: item.title,
      description: item.description,
      owner: item.owner,
      dueDate: item.due_date,
      source: item.source,
      priority: 'HIGH' as const,
    }))),
    ...((dashboard.value?.actions.this_week || []).map((item) => ({
      title: item.title,
      description: item.description,
      owner: item.owner,
      dueDate: item.due_date,
      source: item.source,
      priority: 'MEDIUM' as const,
    }))),
    ...((dashboard.value?.actions.monitoring || []).map((item) => ({
      title: item.title,
      description: item.description,
      owner: item.owner,
      dueDate: item.due_date,
      source: item.source,
      priority: 'MEDIUM' as const,
    }))),
  ]
  return actions.length ? actions.slice(0, 6) : [{
    title: 'Hibrit aksiyonlar veri geldikçe oluşacak.',
    description: 'KPI/ML, nabız ve 360 kaynaklarından yeterli sinyal gelince aksiyon önerileri otomatik üretilecek.',
    priority: 'MEDIUM',
  }]
})

function buildScoreCard(options: {
  title: string
  subtitle: string
  value: number
  target: string
  benchmark: string
  sourceNote: string
  icon: Component
  inverse?: boolean
}) {
  const value = score(options.value)
  const good = options.inverse ? value <= 40 : value >= 80
  const warning = options.inverse ? value <= 60 : value >= 60
  const tone = good ? 'good' : warning ? 'warning' : 'risk'
  const statusMap = {
    good: {
      statusLabel: options.inverse ? 'Düşük Risk' : 'Başarılı',
      statusSurfaceClass: 'border-emerald-200 bg-emerald-50',
      statusBadgeClass: 'bg-emerald-100 text-emerald-700',
      iconClass: 'bg-emerald-100 text-emerald-700',
      trendClass: 'bg-emerald-100 text-emerald-700',
      trendTextClass: 'text-emerald-700',
    },
    warning: {
      statusLabel: 'Dikkat',
      statusSurfaceClass: 'border-amber-200 bg-amber-50',
      statusBadgeClass: 'bg-amber-100 text-amber-700',
      iconClass: 'bg-amber-100 text-amber-700',
      trendClass: 'bg-amber-100 text-amber-700',
      trendTextClass: 'text-amber-700',
    },
    risk: {
      statusLabel: 'Risk',
      statusSurfaceClass: 'border-rose-200 bg-rose-50',
      statusBadgeClass: 'bg-rose-100 text-rose-700',
      iconClass: 'bg-rose-100 text-rose-700',
      trendClass: 'bg-rose-100 text-rose-700',
      trendTextClass: 'text-rose-700',
    },
  }[tone]

  return {
    title: options.title,
    subtitle: options.subtitle,
    value,
    max: 100,
    target: options.target,
    benchmark: options.benchmark,
    sourceNote: options.sourceNote,
    icon: options.icon,
    trendIcon: options.inverse ? riskIcon(value) : scoreIcon(value),
    trendLabel: options.inverse ? riskLabel(value) : scoreStatus(value),
    ...statusMap,
  }
}

function metric(sourceKey: string, metricKey: string) {
  const value = sources.value[sourceKey]?.metrics?.[metricKey]
  if (value === null || value === undefined || value === '') return '-'
  if (typeof value === 'number') return score(value)
  return String(value)
}

function score(value: unknown) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 0
  return Math.round(numeric * 10) / 10
}

function clamp(value: number, min = 0, max = 100) {
  return Math.max(min, Math.min(max, value))
}

function percent(value: number, total: number) {
  return clamp(Math.round((value / Math.max(total, 1)) * 100), 0, 100)
}

function scoreStatus(value: number) {
  if (value >= 80) return 'Yüksek'
  if (value >= 60) return 'Normal'
  return 'Düşük'
}

function scoreIcon(value: number) {
  if (value >= 80) return '↑'
  if (value >= 60) return '→'
  return '↓'
}

function scoreToneClass(value: number) {
  if (value >= 80) return 'text-emerald-700'
  if (value >= 60) return 'text-amber-700'
  return 'text-rose-700'
}

function barToneClass(value: number) {
  if (value >= 80) return 'bg-emerald-500'
  if (value >= 60) return 'bg-amber-500'
  return 'bg-rose-500'
}

function riskLabel(value: number) {
  if (value >= 60) return 'Yüksek Risk'
  if (value >= 40) return 'Orta Risk'
  return 'Düşük Risk'
}

function riskToneClass(value: number) {
  if (value >= 60) return 'text-rose-700'
  if (value >= 40) return 'text-amber-700'
  return 'text-emerald-700'
}

function riskBarClass(value: number) {
  if (value >= 60) return 'bg-rose-500'
  if (value >= 40) return 'bg-amber-500'
  return 'bg-emerald-500'
}

function riskIcon(value: number) {
  if (value >= 60) return '↑'
  if (value >= 40) return '→'
  return '↓'
}

function insightTone(severity: string) {
  if (severity === 'critical') {
    return { label: 'Kritik', surface: 'border-rose-500 bg-rose-50', badge: 'bg-rose-100 text-rose-700', text: 'text-rose-700' }
  }
  if (severity === 'warning') {
    return { label: 'Uyarı', surface: 'border-amber-500 bg-amber-50', badge: 'bg-amber-100 text-amber-700', text: 'text-amber-700' }
  }
  if (severity === 'success') {
    return { label: 'Olumlu', surface: 'border-emerald-500 bg-emerald-50', badge: 'bg-emerald-100 text-emerald-700', text: 'text-emerald-700' }
  }
  return { label: 'Bilgi', surface: 'border-blue-500 bg-blue-50', badge: 'bg-blue-100 text-blue-700', text: 'text-blue-700' }
}

function insightSourceLabel(insight: DepartmentDashboardInsightResponse) {
  if (insight.fallback_used) return 'Kural bazlı'
  if (insight.source === 'gemini') return 'LLM'
  if (insight.source === 'ollama') return 'LLM'
  if (insight.source?.includes('llm')) return 'LLM'
  return 'Kural bazlı'
}

function actionLabel(action: string) {
  if (action === 'urgent') return 'ACIL'
  if (action === 'this_week') return 'Bu Hafta'
  return 'İzleme'
}

function statusLabel(status: string) {
  if (status === 'success' || status === 'healthy') return 'OK'
  if (status === 'warning') return 'Dikkat'
  if (status === 'danger') return 'Risk'
  return status || '-'
}

function statusRuleText(status: string) {
  const label = statusLabel(status)
  if (status === 'success' || status === 'healthy') return `${label}: kaynak skoru 85 ve üzeri`
  if (status === 'warning') return `${label}: kaynak skoru 70-84 arası`
  if (status === 'danger') return `${label}: kaynak skoru 70'in altında`
  return 'Durum backend kaynak skoruna göre hesaplanır'
}

function statusBadge(status: string) {
  if (status === 'success' || status === 'healthy') return 'bg-emerald-100 text-emerald-700'
  if (status === 'warning') return 'bg-amber-100 text-amber-700'
  return 'bg-rose-100 text-rose-700'
}

function trendIcon(trend: string) {
  if (trend === 'yukselis') return '↑'
  if (trend === 'dusus') return '↓'
  return '→'
}

function trendClass(trend: string) {
  if (trend === 'yukselis') return 'text-emerald-600'
  if (trend === 'dusus') return 'text-rose-600'
  return 'text-slate-500'
}

function formatDate(value?: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('tr-TR')
}

function formatDateTime(value?: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('tr-TR')
}

async function refreshDashboard(useLlm = false) {
  if (useLlm) {
    llmLoading.value = true
  } else {
    loading.value = true
  }
  errorMessage.value = ''
  try {
    dashboard.value = await analyticsApi.getSoftwareDepartmentDashboard({
      period: selectedPeriod.value,
      use_llm: useLlm,
    })
  } catch (error) {
    console.error('Hibrit departman dashboard yüklenemedi:', error)
    errorMessage.value = 'Hibrit departman dashboard verisi yüklenemedi.'
  } finally {
    loading.value = false
    llmLoading.value = false
  }
}

onMounted(async () => {
  await refreshDashboard()
})
</script>
