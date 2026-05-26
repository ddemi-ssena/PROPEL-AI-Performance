<template>
  <div class="pb-10 space-y-8">

    <!-- Hero Banner ---------------------------------------------------------->
    <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-emerald-900 via-teal-800 to-emerald-900 shadow-xl">
      <div class="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 rounded-full bg-emerald-500/20 blur-3xl pointer-events-none"></div>
      <div class="absolute bottom-0 left-0 -ml-20 -mb-20 w-60 h-60 rounded-full bg-teal-500/20 blur-3xl pointer-events-none"></div>

      <div class="relative z-10 flex flex-col md:flex-row items-center justify-between p-8 gap-6">
        <div class="flex items-center gap-6 w-full md:w-auto">
          <div class="w-20 h-20 rounded-full ring-4 ring-white/10 shadow-2xl bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center text-2xl font-bold text-white shrink-0">
            {{ userInitials }}
          </div>
          <div>
            <h1 class="text-3xl font-bold text-white tracking-tight">
              Hoş Geldin,
              <span class="text-transparent bg-clip-text bg-gradient-to-r from-emerald-200 to-teal-200">{{ userName }}</span>
            </h1>
            <div class="flex flex-wrap items-center gap-3 mt-3 text-sm font-medium">
              <span class="bg-white/10 text-emerald-100 px-3 py-1 rounded-full border border-white/10">{{ employee?.position || 'Satış Uzmanı' }}</span>
              <span class="text-slate-300">Satış Departmanı</span>
              <span v-if="perfData?.latest_period" class="text-slate-400 text-xs">{{ perfData.latest_period }}</span>
            </div>
            <div v-if="badges.length" class="mt-4 flex flex-wrap gap-2">
              <BadgeMedal
                v-for="badge in badges.slice(0, 4)"
                :key="badge.id"
                :badge-type="badge.badge_type"
                :badge-level="badge.badge_level"
                size="xs"
                show-label
                :description="badge.badge_type"
              />
            </div>
          </div>
        </div>

        <div class="flex gap-3 w-full md:w-auto">
          <button class="flex-1 md:flex-none px-5 py-3 bg-white/5 border border-white/10 text-white text-sm font-medium rounded-xl hover:bg-white/10 transition-all backdrop-blur-sm">
            Rapor İndir
          </button>
          <router-link
            to="/feedback"
            class="flex-1 md:flex-none px-5 py-3 bg-emerald-500 text-white text-sm font-bold rounded-xl hover:bg-emerald-400 shadow-lg shadow-emerald-900/40 transition-all border-t border-white/20 text-center"
          >
            Feedback Ver
          </router-link>
        </div>
      </div>
    </div>

    <!-- Loading state --------------------------------------------------------->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-4 gap-5">
      <div v-for="i in 4" :key="i" class="rounded-2xl border bg-white p-6 shadow-sm animate-pulse h-28"></div>
    </div>

    <!-- No data banner (non-blocking) ---------------------------------------->
    <div v-if="!loading && !perfData?.has_upload" class="rounded-2xl border border-amber-200 bg-amber-50 px-5 py-3 flex items-center gap-3">
      <svg class="w-4 h-4 text-amber-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
      <p class="text-sm font-medium text-amber-700">Satış dataseti henüz yüklenmedi — veriler yüklenince KPI'lar otomatik dolacak.</p>
    </div>

    <template v-if="!loading">
      <!-- KPI Stats Row ------------------------------------------------------->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div
          v-for="card in kpiCards"
          :key="card.code"
          class="rounded-2xl border bg-white p-6 shadow-sm hover:shadow-md transition-shadow"
          :class="card.borderClass"
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.18em]" :class="card.labelClass">{{ card.title }}</p>
              <p class="mt-3 text-3xl font-bold text-slate-900">{{ card.value }}</p>
            </div>
            <span class="rounded-xl p-2.5" :class="card.iconBg">
              <component :is="card.icon" class="h-5 w-5" :class="card.iconColor" />
            </span>
          </div>
          <div class="mt-4 flex items-center gap-2 text-xs font-semibold" :class="card.changeClass">
            <span>{{ card.change }}</span>
            <span class="text-slate-400">{{ card.subtitle }}</span>
          </div>
        </div>
      </div>

      <!-- Main content grid -------------------------------------------------->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

        <!-- Performance Trend (2/3 width) ------------------------------------>
        <div class="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
          <div class="flex justify-between items-center mb-6">
            <div>
              <h3 class="font-bold text-slate-800 text-lg">Satış Performans Trendi</h3>
              <p class="text-xs text-slate-500 mt-1">Son {{ trendLabels.length }} haftalık satış KPI ortalaması</p>
            </div>
            <span class="rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">Canlı</span>
          </div>
          <div class="h-72">
            <LineChart
              :labels="trendLabels"
              :data="trendData"
              label="Satış Skoru"
              color="#10b981"
            />
          </div>
        </div>

        <!-- AI Sales Coach (1/3 width) -------------------------------------->
        <div class="bg-slate-900 rounded-2xl p-6 text-white relative overflow-hidden shadow-xl border border-slate-800">
          <div class="absolute top-0 right-0 p-4 opacity-10">
            <TrophyIcon class="w-32 h-32 text-emerald-400 transform rotate-12" />
          </div>
          <div class="relative z-10">
            <div class="flex items-center gap-3 mb-6">
              <div class="p-2.5 bg-emerald-500/20 rounded-xl border border-emerald-500/30">
                <SparklesIcon class="w-6 h-6 text-emerald-300" />
              </div>
              <div>
                <h3 class="font-bold text-xl text-white">AI Satış Koçu</h3>
                <p class="text-xs text-slate-400">Kişisel Gelişim Tavsiyeleri</p>
              </div>
            </div>

            <!-- ML tavsiyeler (varsa) -->
            <div v-if="aiTips.length" class="space-y-3">
              <div
                v-for="tip in aiTips"
                :key="tip.title"
                class="rounded-xl border border-white/10 bg-white/5 p-4"
              >
                <div class="flex items-center gap-2 mb-2">
                  <span class="text-base">{{ tip.emoji }}</span>
                  <p class="text-sm font-semibold text-white">{{ tip.title }}</p>
                </div>
                <p class="text-xs leading-5 text-slate-400">{{ tip.text }}</p>
              </div>
            </div>

            <!-- ML risk bandı göstergesi -->
            <div v-if="perfData?.prediction" class="mt-4 rounded-xl border border-white/10 bg-white/5 p-4">
              <p class="text-xs text-slate-400 mb-1">Performans Değerlendirmesi</p>
              <div class="flex items-center gap-2">
                <span
                  class="px-2.5 py-1 rounded-full text-xs font-bold"
                  :class="riskBandClass"
                >{{ perfData.prediction.predicted_band }}</span>
                <span class="text-xs text-slate-400">%{{ Math.round(perfData.prediction.confidence * 100) }} güven</span>
              </div>
              <p class="text-xs text-slate-400 mt-2 leading-5">{{ perfData.prediction.risk_summary }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Sales KPI Detail Cards -------------------------------------------->
      <div>
        <div class="flex items-center justify-between gap-4 mb-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">KPI Detayı</p>
            <h3 class="mt-1 text-xl font-bold text-slate-900">Satış Metrikleri</h3>
          </div>
          <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
            {{ perfData?.latest_period || 'Bu hafta' }}
          </span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          <div
            v-for="metric in salesMetrics"
            :key="metric.code"
            class="rounded-2xl border bg-white p-5 shadow-sm hover:shadow-md transition-shadow"
            :class="metric.tone === 'good' ? 'border-emerald-100' : metric.tone === 'warn' ? 'border-amber-100' : 'border-rose-100'"
          >
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{{ metric.code }}</p>
                <p class="mt-1 text-sm font-semibold text-slate-700">{{ metric.label }}</p>
              </div>
              <span
                class="rounded-full px-2.5 py-1 text-xs font-semibold shrink-0"
                :class="metric.tone === 'good' ? 'bg-emerald-50 text-emerald-700' : metric.tone === 'warn' ? 'bg-amber-50 text-amber-700' : 'bg-rose-50 text-rose-700'"
              >
                {{ metric.status }}
              </span>
            </div>
            <p class="mt-4 text-2xl font-bold text-slate-900">{{ metric.value }}</p>
            <div class="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
              <div
                class="h-full rounded-full transition-all duration-500"
                :class="metric.tone === 'good' ? 'bg-emerald-500' : metric.tone === 'warn' ? 'bg-amber-500' : 'bg-rose-500'"
                :style="{ width: metric.barWidth }"
              ></div>
            </div>
            <p class="mt-2 text-xs text-slate-500">{{ metric.hint }}</p>
          </div>
        </div>
      </div>

      <!-- Weekly Pulse & Peer Praise ----------------------------------------->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

        <!-- Weekly Pulse -->
        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex items-center justify-between gap-4 mb-5">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Haftalık</p>
              <h3 class="mt-1 text-lg font-bold text-slate-900">Nabız Anketi</h3>
            </div>
            <router-link
              to="/employee/pulse"
              class="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2 text-xs font-semibold text-emerald-700 hover:bg-emerald-100 transition-colors"
            >
              Ankete Git
            </router-link>
          </div>

          <div class="grid grid-cols-5 gap-2">
            <button
              v-for="mood in moods"
              :key="mood.emoji"
              class="flex flex-col items-center gap-2 rounded-xl border p-3 text-center text-xs font-semibold transition-all hover:scale-105"
              :class="selectedMood === mood.value ? 'border-emerald-300 bg-emerald-50 text-emerald-700' : 'border-slate-200 text-slate-500 hover:border-slate-300'"
              @click="selectedMood = mood.value"
            >
              <span class="text-2xl">{{ mood.emoji }}</span>
              <span>{{ mood.label }}</span>
            </button>
          </div>

          <div v-if="selectedMood" class="mt-4">
            <textarea
              v-model="pulseNote"
              rows="2"
              class="w-full rounded-xl border border-slate-200 p-3 text-sm text-slate-700 resize-none focus:outline-none focus:ring-2 focus:ring-emerald-300"
              placeholder="Bu haftaki satış notunuz… (isteğe bağlı)"
            ></textarea>
            <button
              class="mt-3 w-full rounded-xl py-2.5 text-sm font-semibold text-white transition-colors"
              :class="pulseSubmitting ? 'bg-slate-400 cursor-not-allowed' : 'bg-emerald-600 hover:bg-emerald-700'"
              :disabled="pulseSubmitting"
              @click="submitPulse"
            >
              {{ pulseSubmitting ? 'Gönderiliyor…' : 'Gönder' }}
            </button>
            <p v-if="pulseSuccess" class="mt-2 text-xs text-emerald-600 font-semibold text-center">✓ Nabız anketiniz kaydedildi!</p>
            <p v-if="pulseError" class="mt-2 text-xs text-rose-600 font-semibold text-center">{{ pulseError }}</p>
          </div>
        </div>

        <!-- Peer Praise -------------------------------------------------------->
        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex items-center justify-between gap-4 mb-5">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Takım</p>
              <h3 class="mt-1 text-lg font-bold text-slate-900">Ekipten Gelen Övgüler</h3>
            </div>
            <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-500">{{ badges.length }} rozet</span>
          </div>

          <div v-if="badges.length" class="space-y-3">
            <div
              v-for="badge in badges.slice(0, 4)"
              :key="badge.id"
              class="flex items-center gap-4 rounded-xl border border-slate-100 bg-slate-50 p-4"
            >
              <BadgeMedal
                :badge-type="badge.badge_type"
                :badge-level="badge.badge_level"
                size="sm"
              />
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ badgeLabel(badge.badge_type) }}</p>
                <p class="text-xs text-slate-500 mt-0.5">{{ badgeLevelLabel(badge.badge_level) }}</p>
              </div>
            </div>
          </div>

          <div v-else class="flex flex-col items-center justify-center py-8 text-center">
            <div class="text-4xl mb-3">🏅</div>
            <p class="text-sm font-semibold text-slate-700">Henüz rozet yok</p>
            <p class="text-xs text-slate-400 mt-1">Harika işler yapınca takımın seni ödüllendirecek!</p>
          </div>
        </div>
      </div>

      <!-- Focus Areas -------------------------------------------------------->
      <div class="rounded-3xl border border-slate-800 bg-slate-900 p-8 shadow-lg">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Bu Hafta Odak</p>
        <h3 class="mt-2 text-xl font-bold text-white">Satış Geliştirme Alanları</h3>
        <div class="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div
            v-for="area in focusAreas"
            :key="area.title"
            class="rounded-2xl border border-white/10 bg-white/5 p-5"
          >
            <p class="text-base">{{ area.emoji }}</p>
            <p class="mt-3 text-sm font-semibold" :class="area.color">{{ area.title }}</p>
            <p class="mt-2 text-sm leading-6 text-slate-200">{{ area.text }}</p>
          </div>
        </div>
      </div>
    </template>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { SparklesIcon, TrophyIcon, ChartBarIcon, UserGroupIcon, ClockIcon } from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import { feedbackApi, type BadgeResponse } from '@/services/api/feedback.api'
import { employeeApi } from '@/services/api/employee.api'
import { surveyApi } from '@/services/api/survey.api'
import { analyticsApi, type SalesEmployeePerformanceResponse, type SalesWeeklyTrendPoint } from '@/services/api/analytics.api'
import BadgeMedal from '@/components/common/BadgeMedal.vue'
import LineChart from '@/components/dashboard/LineChart.vue'

const authStore = useAuthStore()
const employee = ref<any>(null)
const badges = ref<BadgeResponse[]>([])
const perfData = ref<SalesEmployeePerformanceResponse | null>(null)
const loading = ref(true)

const userName = computed(() => authStore.user?.full_name || 'Satış Uzmanı')
const userInitials = computed(() =>
  userName.value.split(' ').map((n: string) => n[0]).join('').toUpperCase().substring(0, 2)
)

// ── KPI formatters ────────────────────────────────────────────────────────────

function formatKpiValue(code: string, raw: number | null | undefined): string {
  if (raw == null) return '—'
  const kpi = perfData.value?.kpis?.[code]
  if (!kpi) return String(raw)
  if (kpi.unit === 'ratio') return `%${Math.round(raw * 100)}`
  if (kpi.unit === 'days') return `${Math.round(raw)} gün`
  if (kpi.unit === 'score_5') {
    return raw > 5 ? `%${Math.round(raw)}` : `${raw.toFixed(1)}/5`
  }
  if (kpi.unit === 'score_10') return `${raw.toFixed(1)}/10`
  return String(raw)
}

function toneFromStatus(status: string | null | undefined, direction: string): 'good' | 'warn' | 'bad' {
  if (!status) return 'warn'
  if (status.includes('Guclu')) return 'good'
  if (status.includes('Risk')) return direction === 'lower_is_better' ? 'good' : 'bad'
  return 'warn'
}

function statusLabel(tone: string): string {
  if (tone === 'good') return 'İyi'
  if (tone === 'bad') return 'Dikkat'
  return 'İzle'
}

// ── KPI stat cards (4 cards) ─────────────────────────────────────────────────

const kpiCards = computed(() => {
  const kpis = perfData.value?.kpis
  const cardDefs = [
    {
      code: 'SHGO',
      title: 'Hedef Gerçekleşme',
      icon: TrophyIcon,
      borderClass: 'border-emerald-100',
      labelClass: 'text-emerald-600',
      iconBg: 'bg-emerald-50',
      iconColor: 'text-emerald-600',
    },
    {
      code: 'PSO',
      title: 'Pipeline Sağlığı',
      icon: ChartBarIcon,
      borderClass: 'border-amber-100',
      labelClass: 'text-amber-600',
      iconBg: 'bg-amber-50',
      iconColor: 'text-amber-600',
    },
    {
      code: 'CRMD',
      title: 'CRM Kullanım',
      icon: ClockIcon,
      borderClass: 'border-sky-100',
      labelClass: 'text-sky-600',
      iconBg: 'bg-sky-50',
      iconColor: 'text-sky-600',
    },
    {
      code: 'CSAT',
      title: 'Müşteri Memnuniyeti',
      icon: UserGroupIcon,
      borderClass: 'border-indigo-100',
      labelClass: 'text-indigo-600',
      iconBg: 'bg-indigo-50',
      iconColor: 'text-indigo-600',
    },
  ]

  return cardDefs.map((def) => {
    const kpi = kpis?.[def.code]
    const raw = kpi?.raw_value
    const tone = toneFromStatus(kpi?.threshold_status, kpi?.direction ?? 'higher_is_better')
    const trendText = kpi?.trend_signal?.includes('iyi') ? '↑' : kpi?.trend_signal?.includes('olumsuz') ? '↓' : '—'
    const changeClass = tone === 'good' ? 'text-emerald-600' : tone === 'bad' ? 'text-rose-600' : 'text-amber-600'
    return {
      ...def,
      value: formatKpiValue(def.code, raw),
      change: trendText,
      subtitle: kpi?.trend_signal ?? '—',
      changeClass,
    }
  })
})

// ── Performance trend ─────────────────────────────────────────────────────────

const trendLabels = computed(() => perfData.value?.weekly_trend.map((p: SalesWeeklyTrendPoint) => p.label) ?? [])
const trendData = computed(() => perfData.value?.weekly_trend.map((p: SalesWeeklyTrendPoint) => Math.round(p.score)) ?? [])

// ── Sales metrics detail (9 cards) ───────────────────────────────────────────

const METRIC_LABELS: Record<string, string> = {
  SHGO: 'Satış Hedef Gerçekleşme Oranı',
  LMDO: 'Lead → Müşteri Dönüşüm Oranı',
  TKO: 'Tekliften Kazanıma Dönüşüm',
  OSDS: 'Ort. Satış Döngüsü (gün)',
  CSAT: 'Müşteri Memnuniyeti',
  CRMD: 'CRM Disiplin Metriği',
  TDO: 'Takip Disiplini Oranı',
  PSO: 'Pipeline Sağlık Oranı',
  MS: 'Motivasyon Skoru',
}

const METRIC_HINTS: Record<string, string> = {
  SHGO: 'Hedef: %100 üzeri',
  LMDO: 'Hedef: %25 üzeri',
  TKO: 'Hedef: %50 üzeri',
  OSDS: 'Hedef: 30 gün altı',
  CSAT: 'Hedef: 4.5/5 üzeri',
  CRMD: 'Hedef: %90 üzeri',
  TDO: 'Hedef: %90 üzeri',
  PSO: 'Hedef: %80 üzeri',
  MS: 'Hedef: 4/5 üzeri',
}

const salesMetrics = computed(() => {
  const kpis = perfData.value?.kpis
  return Object.keys(METRIC_LABELS).map((code) => {
    const kpi = kpis?.[code]
    const raw = kpi?.raw_value
    const tone = toneFromStatus(kpi?.threshold_status, kpi?.direction ?? 'higher_is_better')
    return {
      code,
      label: METRIC_LABELS[code],
      value: formatKpiValue(code, raw),
      status: statusLabel(tone),
      tone,
      barWidth: kpi ? `${Math.round((kpi.bar_pct ?? 0) * 100)}%` : '0%',
      hint: METRIC_HINTS[code] ?? '',
    }
  })
})

// ── AI tips from ML recommended_actions ──────────────────────────────────────

const EMOJI_POOL = ['🎯', '📊', '🤝', '💡', '📈', '🔑']

const aiTips = computed(() => {
  const actions = perfData.value?.prediction?.recommended_actions
  if (actions && actions.length > 0) {
    return actions.slice(0, 3).map((text: string, i: number) => ({
      emoji: EMOJI_POOL[i % EMOJI_POOL.length],
      title: `Aksiyon ${i + 1}`,
      text,
    }))
  }
  // Fallback genel tavsiyeler
  return [
    { emoji: '🎯', title: 'Takip Disiplini', text: 'Tekliften 48 saat içinde takip yapmak kapatma oranını artırır.' },
    { emoji: '📊', title: 'Pipeline Kalitesi', text: 'Hareketsiz fırsatları temizleyerek pipeline sağlığını koruyun.' },
    { emoji: '🤝', title: 'Müşteri İlişkisi', text: 'Mevcut müşterilerde cross-sell fırsatlarını değerlendirin.' },
  ]
})

// ── Risk band style ───────────────────────────────────────────────────────────

const riskBandClass = computed(() => {
  const band = perfData.value?.prediction?.predicted_band
  if (band === 'Evet' || band === '1' || band === 'Yuksek') return 'bg-rose-100 text-rose-700'
  if (band === 'Hayir' || band === '0' || band === 'Dusuk') return 'bg-emerald-100 text-emerald-700'
  return 'bg-amber-100 text-amber-700'
})

// ── Focus areas (ML top_drivers → dynamic, else fallback) ────────────────────

const focusAreas = computed(() => {
  const drivers = perfData.value?.prediction?.top_drivers
  if (drivers && drivers.length >= 3) {
    const colors = ['text-rose-300', 'text-amber-300', 'text-emerald-300']
    const emojis = ['🔥', '📈', '🎓']
    return drivers.slice(0, 3).map((d: any, i: number) => ({
      emoji: emojis[i],
      title: d.metric_name ?? `KPI Sinyali ${i + 1}`,
      text: d.rationale ?? "Bu KPI'de iyileştirme fırsatı mevcut.",
      color: colors[i],
    }))
  }
  return [
    { emoji: '🔥', title: 'Bu Hafta Kazanacaklar', text: 'Tekliften 5+ gün geçmiş fırsatlar için takip zamanı.', color: 'text-rose-300' },
    { emoji: '📈', title: 'Pipeline Büyüt', text: 'Yeni lead hedeflerin için networking ve referans kanallarını aktif kullan.', color: 'text-amber-300' },
    { emoji: '🎓', title: 'Gelişim', text: 'Önerilen eğitimleri tamamlayarak yeni ürün lansmanına hazırlan.', color: 'text-emerald-300' },
  ]
})

// ── Pulse survey ─────────────────────────────────────────────────────────────

const moods = [
  { emoji: '😫', label: 'Yorgun', value: 1 },
  { emoji: '😐', label: 'Nötr', value: 2 },
  { emoji: '🙂', label: 'İyi', value: 3 },
  { emoji: '😄', label: 'Harika', value: 4 },
  { emoji: '🤩', label: 'Süper', value: 5 },
]
const selectedMood = ref<number | null>(null)
const pulseNote = ref('')
const pulseSubmitting = ref(false)
const pulseSuccess = ref(false)
const pulseError = ref('')

async function submitPulse() {
  if (!selectedMood.value || !employee.value?.id) return
  pulseSubmitting.value = true
  pulseSuccess.value = false
  pulseError.value = ''
  try {
    const today = new Date().toISOString().slice(0, 10)
    await surveyApi.createSurvey({
      employee_id: employee.value.id,
      survey_type: 'motivation',
      score: selectedMood.value,
      period_date: today,
      comments: pulseNote.value || undefined,
    })
    pulseSuccess.value = true
    selectedMood.value = null
    pulseNote.value = ''
  } catch (err: any) {
    pulseError.value = err?.response?.data?.detail ?? 'Gönderim başarısız. Tekrar deneyin.'
  } finally {
    pulseSubmitting.value = false
  }
}

// ── Badge helpers ─────────────────────────────────────────────────────────────

const BADGE_LABELS: Record<string, string> = {
  team_player: 'Takım Oyuncusu', problem_solver: 'Problem Çözücü',
  communicator: 'İletişimci', speed_champion: 'Hız Şampiyonu',
  mentor: 'Mentor', innovator: 'İnovatör', reliable: 'Güvenilir',
}
const BADGE_LEVEL_LABELS: Record<string, string> = {
  bronze: 'Bronz', silver: 'Gümüş', gold: 'Altın',
}
function badgeLabel(t: string) { return BADGE_LABELS[t] || t }
function badgeLevelLabel(l: string) { return BADGE_LEVEL_LABELS[l] || l }

// ── Data loading ──────────────────────────────────────────────────────────────

async function loadAll() {
  loading.value = true
  await Promise.allSettled([
    feedbackApi.getMyBadges().then((b) => { badges.value = b }).catch(() => {}),
    employeeApi.getEmployees().then((list: any[]) => {
      const userId = authStore.user?.id
      employee.value = list.find((e) => e.user_id === userId || e.user?.id === userId) || list[0] || null
    }).catch(() => {}),
    analyticsApi.getMyPerformance().then((data) => { perfData.value = data }).catch(() => {}),
  ])
  loading.value = false
}

onMounted(loadAll)
</script>
