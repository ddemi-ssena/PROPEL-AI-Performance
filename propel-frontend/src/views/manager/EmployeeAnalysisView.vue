<template>
  <div class="space-y-8 pb-10">
    <div class="flex flex-col md:flex-row justify-between items-end gap-4 border-b border-slate-200 pb-6">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 tracking-tight">Çalışan Analizi</h2>
        <p class="text-slate-500 mt-1">
          Ekipteki çalışanların 360 derece geri bildirim raporlarını, skorlarını ve yönetici özetlerini ayrı ayrı inceleyin.
        </p>
      </div>
      <div class="rounded-full border border-indigo-100 bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-700">
        {{ teamMembers.length }} çalışan listeleniyor
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-[320px_minmax(0,1fr)] gap-6">
      <aside class="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div class="border-b border-slate-100 px-5 py-4">
          <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Çalışanlar</p>
          <h3 class="mt-1 text-lg font-bold text-slate-900">Rapor seçimi</h3>
        </div>

        <div v-if="teamMembers.length" class="max-h-[720px] overflow-y-auto p-3 space-y-3">
          <button
            v-for="employee in teamMembers"
            :key="employee.id"
            type="button"
            class="w-full rounded-2xl border p-4 text-left transition-all"
            :class="selectedEmployeeId === employee.id
              ? 'border-indigo-200 bg-indigo-50 shadow-sm'
              : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'"
            @click="selectedEmployeeId = employee.id"
          >
            <div class="flex items-start justify-between gap-3">
              <div>
                <div class="flex items-center gap-2">
                  <p class="font-semibold text-slate-900">{{ employee.user.full_name }}</p>
                  <div v-if="employeeReportBadges(employee.id).length" class="flex items-center gap-1">
                    <BadgeMedal
                      v-for="badge in employeeReportBadges(employee.id).slice(0, 2)"
                      :key="`list-badge-${employee.id}-${badge.id}`"
                      :badge-type="badge.badge_type"
                      :badge-level="badge.badge_level"
                      size="xs"
                      :description="getBadgeDescription(badge)"
                    />
                    <span
                      v-if="employeeReportBadges(employee.id).length > 2"
                      class="rounded-full border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[10px] font-semibold text-slate-500"
                    >
                      +{{ employeeReportBadges(employee.id).length - 2 }}
                    </span>
                  </div>
                </div>
                <div class="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-500">
                  <span>{{ employee.position || 'Calisan' }}</span>
                  <span
                    v-if="employee.team"
                    class="rounded-full border border-sky-200 bg-sky-50 px-2 py-0.5 text-[11px] font-semibold text-sky-700"
                  >
                    {{ employee.team }}
                  </span>
                </div>
              </div>
              <span
                class="rounded-full px-2.5 py-1 text-[11px] font-semibold"
                :class="selectedEmployeeId === employee.id
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-100 text-slate-500'"
              >
                {{ employee.department?.name || 'Departman yok' }}
              </span>
            </div>
            <p class="mt-3 text-xs leading-5 text-slate-500">
              {{ getPreviewSummary(employee.id) }}
            </p>
          </button>
        </div>

        <div v-else class="p-6 text-sm text-slate-400">
          Bu yönetici için listelenecek çalışan bulunamadı.
        </div>
      </aside>

      <section v-if="selectedEmployeeReport" class="space-y-6">
        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
            <div>
              <p class="text-sm text-slate-500">{{ selectedEmployeeReport.report_title }}</p>
              <h3 class="mt-1 text-2xl font-bold text-slate-900">
                {{ selectedEmployeeReport.employee_name }}
              </h3>
              <p class="mt-1 text-sm text-slate-500">
                {{ selectedEmployeeReport.position || 'Çalışan' }}
                <span v-if="selectedEmployeeReport.department_name"> - {{ selectedEmployeeReport.department_name }}</span>
              </p>
              <div v-if="selectedEmployeeReport.team" class="mt-3">
                <span class="rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-700">
                  {{ selectedEmployeeReport.team }} Takimi
                </span>
              </div>
              <div v-if="selectedEmployeeReport.badges?.length" class="mt-4 flex flex-wrap gap-3">
                <div
                  v-for="badge in selectedEmployeeReport.badges"
                  :key="`report-badge-${badge.id}`"
                  class="flex items-center"
                >
                  <BadgeMedal
                    :badge-type="badge.badge_type"
                    :badge-level="badge.badge_level"
                    size="xs"
                    show-label
                    :description="getBadgeDescription(badge)"
                  />
                </div>
              </div>
            </div>

            <div class="flex flex-wrap gap-3">
              <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
                Hafta {{ selectedEmployeeReport.period_week }}
              </span>
              <span class="rounded-full border border-indigo-100 bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
                360 derece geri bildirim özeti
              </span>
            </div>
          </div>

          <div class="mt-5 rounded-2xl border border-indigo-100 bg-indigo-50 p-5">
            <p class="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-700">Haftalık Yönetici Özeti</p>
            <p class="mt-2 text-sm leading-6 text-slate-700">
              {{ renderText(selectedEmployeeReport.report_summary) }}
            </p>
          </div>

          <div v-if="qualityWarningSection || biasWarningSection" class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div
              v-if="qualityWarningSection"
              class="rounded-2xl border border-amber-200 bg-amber-50 p-4"
            >
              <p class="text-xs font-semibold uppercase tracking-[0.14em] text-amber-700">Veri Kalitesi Uyarısı</p>
              <div class="mt-3 flex flex-wrap gap-2">
                <span
                  v-for="item in qualityWarningSection.items"
                  :key="`quality-${item}`"
                  class="rounded-full border border-amber-200 bg-white px-2 py-1 text-xs text-amber-700"
                >
                  {{ renderText(item) }}
                </span>
              </div>
            </div>

            <div
              v-if="biasWarningSection"
              class="rounded-2xl border border-rose-200 bg-rose-50 p-4"
            >
              <p class="text-xs font-semibold uppercase tracking-[0.14em] text-rose-700">Karşılıklı Bias Şüphesi</p>
              <div class="mt-3 flex flex-wrap gap-2">
                <span
                  v-for="item in biasWarningSection.items"
                  :key="`bias-${item}`"
                  class="rounded-full border border-rose-200 bg-white px-2 py-1 text-xs text-rose-700"
                >
                  {{ renderText(item) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 xl:grid-cols-[minmax(0,1.2fr)_360px] gap-6">
          <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Aylık Derin Analiz</p>
                <h4 class="mt-1 text-lg font-bold text-slate-900">Trend ve tema özeti</h4>
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
                  <p class="text-xs text-slate-500">Ayrılma riski skoru</p>
                  <p class="mt-2 text-xl font-bold text-slate-900">{{ monthlyDeepAnalysis.flight_risk_score ?? '-' }}/10</p>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="rounded-xl border border-rose-100 bg-rose-50 p-4">
                  <p class="text-xs font-semibold text-rose-700">En sık şikayet konuları</p>
                  <div class="mt-3 flex flex-wrap gap-2">
                    <span
                      v-for="item in monthlyDeepAnalysis.top_complaint_topics"
                      :key="`complaint-${item}`"
                      class="rounded-full border border-rose-200 bg-white px-2 py-1 text-xs text-rose-700"
                    >
                      {{ item }}
                    </span>
                    <span v-if="!monthlyDeepAnalysis.top_complaint_topics.length" class="text-sm text-slate-400">Veri yok</span>
                  </div>
                </div>

                <div class="rounded-xl border border-emerald-100 bg-emerald-50 p-4">
                  <p class="text-xs font-semibold text-emerald-700">En sık övgü konuları</p>
                  <div class="mt-3 flex flex-wrap gap-2">
                    <span
                      v-for="item in monthlyDeepAnalysis.top_praise_topics"
                      :key="`praise-${item}`"
                      class="rounded-full border border-emerald-200 bg-white px-2 py-1 text-xs text-emerald-700"
                    >
                      {{ item }}
                    </span>
                    <span v-if="!monthlyDeepAnalysis.top_praise_topics.length" class="text-sm text-slate-400">Veri yok</span>
                  </div>
                </div>

                <div class="rounded-xl border border-sky-100 bg-sky-50 p-4">
                  <p class="text-xs font-semibold text-sky-700">Öne çıkan temalar</p>
                  <div class="mt-3 flex flex-wrap gap-2">
                    <span
                      v-for="item in monthlyDeepAnalysis.top_themes"
                      :key="`theme-${item}`"
                      class="rounded-full border border-sky-200 bg-white px-2 py-1 text-xs text-sky-700"
                    >
                      {{ item }}
                    </span>
                    <span v-if="!monthlyDeepAnalysis.top_themes.length" class="text-sm text-slate-400">Veri yok</span>
                  </div>
                </div>
              </div>
            </div>

            <div v-else class="mt-6 text-sm text-slate-400">
              Aylık derin analiz verisi henüz oluşmadı.
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
                  <p class="text-xs font-semibold text-violet-700">Elde tutma riski</p>
                  <p class="mt-2 text-sm leading-6 text-slate-700">
                    Skor: {{ monthlyRagReport.flight_risk_score ?? '-' }}/10
                    <span v-if="monthlyRagReport.retention_risk_level"> - {{ formatRiskLabel(monthlyRagReport.retention_risk_level) }}</span>
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div class="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-lg">
            <p class="text-xs uppercase tracking-[0.2em] text-slate-400">Aylık İçgörüler</p>
            <div v-if="monthlyDeepAnalysis" class="mt-5 space-y-4">
              <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                <p class="text-xs font-semibold text-rose-300">Ayrılma riski nedenleri</p>
                <div class="mt-3 flex flex-wrap gap-2">
                  <span
                    v-for="item in monthlyDeepAnalysis.flight_risk_reasons"
                    :key="`risk-reason-${item}`"
                    class="rounded-full border border-rose-500/20 bg-white/5 px-2 py-1 text-xs text-rose-200"
                  >
                    {{ renderText(item) }}
                  </span>
                  <span v-if="!monthlyDeepAnalysis.flight_risk_reasons.length" class="text-sm text-slate-500">Veri yok</span>
                </div>
              </div>

              <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                <p class="text-xs font-semibold text-amber-300">Aksiyon önerisi</p>
                <p class="mt-2 text-sm leading-6 text-slate-200">
                  {{ renderText(monthlyDeepAnalysis.action_recommendation || 'Bu çalışan için aylık aksiyon önerisi henüz oluşmadı.') }}
                </p>
              </div>

              <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                <p class="text-xs font-semibold text-indigo-300">Analiz kapsamı</p>
                <p class="mt-2 text-sm leading-6 text-slate-200">
                  Bu rapor son ay içinde toplanan {{ monthlyDeepAnalysis.feedback_count }} feedback cevabı üzerinden hesaplandı.
                </p>
              </div>

              <div v-if="monthlyRagReport" class="rounded-xl border border-white/10 bg-white/5 p-4">
                <p class="text-xs font-semibold text-violet-300">Ana bulgular</p>
                <div class="mt-3 flex flex-wrap gap-2">
                  <span
                    v-for="item in monthlyRagReport.key_takeaways"
                    :key="`rag-takeaway-${item}`"
                    class="rounded-full border border-violet-500/20 bg-white/5 px-2 py-1 text-xs text-violet-200"
                  >
                    {{ renderText(item) }}
                  </span>
                  <span v-if="!monthlyRagReport.key_takeaways.length" class="text-sm text-slate-500">Veri yok</span>
                </div>
              </div>
            </div>
            <div v-else class="mt-5 text-sm text-slate-500">
              Aylık içgörüler veri geldikçe burada gösterilecek.
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_340px] gap-6">
          <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Skorlar</p>
                <h4 class="mt-1 text-lg font-bold text-slate-900">Çalışan değerlendirme grafiği</h4>
              </div>
              <span class="rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                1-5 puan aralığı
              </span>
            </div>

            <div class="mt-6 grid grid-cols-2 md:grid-cols-3 gap-4">
              <div
                v-for="metric in scoreMetrics"
                :key="metric.label"
                class="rounded-xl border border-slate-100 bg-slate-50 p-4"
              >
                <p class="text-xs text-slate-500">{{ metric.label }}</p>
                <p class="mt-1 text-2xl font-bold text-slate-900">{{ metric.display_value }}</p>
                <p v-if="metric.description" class="mt-1 text-xs text-slate-400">{{ metric.description }}</p>
              </div>
            </div>

            <div class="mt-6 h-80">
              <BarChart
                :labels="scoreMetricLabels"
                :data="scoreMetricValues"
                label="Çalışan Skorları"
                color="#4f46e5"
              />
            </div>

            <div class="mt-4 rounded-xl border border-amber-100 bg-amber-50 p-4">
              <p class="text-xs font-semibold text-amber-700">Not</p>
              <p class="mt-1 text-sm text-slate-600">
                Veri modelinde şu an klasik NPS yerine haftalık 1-5 davranış puanları tutuluyor. Bu grafik, ekip arkadaşlarının birbirine verdiği güncel değerlendirme skorlarını gösterir.
              </p>
            </div>
          </div>

          <div class="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-lg">
            <p class="text-xs uppercase tracking-[0.2em] text-slate-400">Yönetici Gözlemi</p>
            <div class="mt-5 space-y-4">
              <div class="rounded-xl border border-white/10 bg-white/5 p-4">
                <p class="text-xs font-semibold text-amber-300">Önerilen aksiyon</p>
                <p class="mt-2 text-sm leading-6 text-slate-200">
                  {{ renderText(selectedEmployeeReport.recommended_action || 'Bu çalışan için belirgin bir aksiyon sinyali henüz oluşmadı.') }}
                </p>
              </div>

              <div
                v-for="section in selectedEmployeeReport.sections"
                :key="section.title"
                class="rounded-xl border p-4"
                :class="getDarkSectionClass(section.title)"
              >
                <p class="text-xs font-semibold mb-2" :class="getDarkSectionTitleClass(section.title)">
                  {{ section.title }}
                </p>
                <div class="flex flex-wrap gap-2">
                  <span
                    v-for="item in section.items"
                    :key="`${section.title}-${item}`"
                    class="rounded-full border px-2 py-1 text-xs bg-white/5"
                    :class="getDarkSectionPillClass(section.title)"
                  >
                    {{ renderText(item) }}
                  </span>
                  <span v-if="!section.items.length" class="text-sm text-slate-500">Veri yok</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section
        v-else
        class="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-400"
      >
        Soldaki listeden bir çalışan seçtiğinde burada rapor özeti, skor grafiği ve yönetici içgörü alanı görünecek.
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import BarChart from '@/components/dashboard/BarChart.vue'
import BadgeMedal from '@/components/common/BadgeMedal.vue'
import {
  feedbackApi,
  type BadgeResponse,
  type BadgeType,
  type Employee360SummaryReportResponse,
  type EmployeeMonthlyDeepAnalysisResponse,
  type EmployeeMonthlyRAGReportResponse,
  type EmployeeForFeedback,
  type SummaryMetric,
} from '@/services/api/feedback.api'

const teamMembers = ref<EmployeeForFeedback[]>([])
const selectedEmployeeId = ref<number | null>(null)
const selectedEmployeeReport = ref<Employee360SummaryReportResponse | null>(null)
const monthlyDeepAnalysis = ref<EmployeeMonthlyDeepAnalysisResponse | null>(null)
const monthlyRagReport = ref<EmployeeMonthlyRAGReportResponse | null>(null)
const employeeReports = ref<Record<number, Employee360SummaryReportResponse>>({})
const today = new Date()
const selectedMonth = ref<number>(today.getMonth() + 1)
const selectedYear = ref<number>(today.getFullYear())

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
    ['destek ihtiyaci', 'destek ihtiyacı'],
    ['ekip uyumu', 'ekip uyumu'],
    ['yukselis', 'yükseliş'],
    ['dusus', 'düşüş'],
    ['gorunuyor', 'görünüyor'],
    ['Tekrarlanan sikayet konulari', 'Tekrarlanan şikayet konuları'],
    ['En belirgin sikayet alanlari', 'En belirgin şikayet alanları'],
    ['Olumlu sinyaller', 'Olumlu sinyaller'],
    ['Gecmis benzer yorumlar', 'Geçmiş benzer yorumlar'],
    ['kayitta', 'kayıtta'],
    ['ayrilma riski', 'ayrılma riski'],
    ['olumlu davranislari', 'olumlu davranışları'],
    ['takdir edin', 'takdir edin'],
    ['gorusme', 'görüşme'],
    ['blokajlari', 'blokajları'],
    ['Çalışan geri bildiriminde', 'Çalışan geri bildiriminde'],
    ['Calisan geri bildiriminde', 'Çalışan geri bildiriminde'],
    ['karisik', 'karışık'],
    ['olumlu', 'olumlu'],
    ['olumsuz', 'olumsuz'],
  ]

  let rendered = value
  for (const [from, to] of replacements) {
    rendered = rendered.split(from).join(to)
  }
  return rendered
}

function getDarkSectionClass(title: string) {
  const normalized = title.toLowerCase()
  if (normalized.includes('guclu')) return 'border-emerald-500/20 bg-emerald-500/10'
  if (normalized.includes('risk')) return 'border-rose-500/20 bg-rose-500/10'
  return 'border-amber-500/20 bg-amber-500/10'
}

function getDarkSectionTitleClass(title: string) {
  const normalized = title.toLowerCase()
  if (normalized.includes('guclu')) return 'text-emerald-300'
  if (normalized.includes('risk')) return 'text-rose-300'
  return 'text-amber-300'
}

function getDarkSectionPillClass(title: string) {
  const normalized = title.toLowerCase()
  if (normalized.includes('guclu')) return 'text-emerald-200 border-emerald-500/20'
  if (normalized.includes('risk')) return 'text-rose-200 border-rose-500/20'
  return 'text-amber-200 border-amber-500/20'
}

function employeeReportBadges(employeeId: number) {
  return employeeReports.value[employeeId]?.badges || []
}

function getBadgeDescription(badge: BadgeResponse | { badge_type: BadgeType; source_feedback_ids?: number[] }) {
  const baseMap = {
    team_player: "Ekip enerjisini ve uyumu yukseltiyor.",
    problem_solver: "Blokajlara hizli ve sogukkanli yaklasiyor.",
    communicator: "Geri bildirimlerinde net ve ogretici bir cizgi var.",
    speed_champion: "Yuksek tempo ve hizli adaptasyon sagliyor.",
    mentor: "Bilgi paylasimi ve mentorlukta one cikiyor.",
    innovator: "Gelisime acik ve cevik ilerliyor.",
    reliable: "Teknik sahiplenme ve saglam uygulama disiplini gosteriyor.",
  } as const
  return baseMap[badge.badge_type] ?? "Bu ayin analizlerinde istikrarli bir guc sergiledi."
}

const scoreMetrics = computed<SummaryMetric[]>(() =>
  (selectedEmployeeReport.value?.metrics || []).filter((metric) => typeof metric.value === 'number')
)

const qualityWarningSection = computed(() =>
  selectedEmployeeReport.value?.sections.find((section) => section.title.toLowerCase().includes('veri kalitesi')) || null
)

const biasWarningSection = computed(() =>
  selectedEmployeeReport.value?.sections.find((section) => section.title.toLowerCase().includes('bias')) || null
)

const scoreMetricLabels = computed(() => scoreMetrics.value.map((metric) => metric.label))
const scoreMetricValues = computed(() => scoreMetrics.value.map((metric) => metric.value ?? 0))

function getPreviewSummary(employeeId: number) {
  const report = employeeReports.value[employeeId]
  if (!report?.report_summary) {
    return 'Bu çalışan için ilk rapor yüklendiğinde kısa özet burada görünecek.'
  }

  const rendered = renderText(report.report_summary)
  return rendered.length > 120
    ? `${rendered.slice(0, 120)}...`
    : rendered
}

function formatTrend(value: string) {
  const map: Record<string, string> = {
    yukselis: 'Yükseliş',
    dusus: 'Düşüş',
    stabil: 'Stabil',
  }
  return map[value] || 'Stabil'
}

async function loadTeamMembers() {
  try {
    const candidates = await feedbackApi.getFeedbackCandidates()
    teamMembers.value = candidates.filter((employee) => employee.user.role === 'employee')

    if (!selectedEmployeeId.value && teamMembers.value.length) {
      selectedEmployeeId.value = teamMembers.value[0].id
    }
  } catch (error) {
    console.error('Ekip uyeleri yuklenemedi:', error)
  }
}

async function loadEmployeeReport(employeeId: number) {
  try {
    const report = await feedbackApi.getEmployee360SummaryReport(employeeId)
    employeeReports.value = {
      ...employeeReports.value,
      [employeeId]: report,
    }
    selectedEmployeeReport.value = report
  } catch (error) {
    console.error('Calisan 360 raporu yuklenemedi:', error)
    selectedEmployeeReport.value = null
  }
}

async function loadMonthlyDeepAnalysis(employeeId: number) {
  try {
    const deepAnalysis = await feedbackApi.getEmployeeMonthlyDeepAnalysis(employeeId, {
      year: selectedYear.value,
      month: selectedMonth.value,
    })
    const ragReport = await feedbackApi.getEmployeeMonthlyRagReport(employeeId, {
      year: selectedYear.value,
      month: selectedMonth.value,
    })
    monthlyDeepAnalysis.value = deepAnalysis
    monthlyRagReport.value = ragReport
  } catch (error) {
    console.error('Calisan aylik derin analizi yuklenemedi:', error)
    monthlyDeepAnalysis.value = null
    monthlyRagReport.value = null
  }
}

watch(selectedEmployeeId, (value) => {
  if (typeof value === 'number') {
    void loadEmployeeReport(value)
    void loadMonthlyDeepAnalysis(value)
  }
})

watch([selectedMonth, selectedYear], () => {
  if (typeof selectedEmployeeId.value === 'number') {
    void loadMonthlyDeepAnalysis(selectedEmployeeId.value)
  }
})

onMounted(async () => {
  await loadTeamMembers()
  if (typeof selectedEmployeeId.value === 'number') {
    await loadEmployeeReport(selectedEmployeeId.value)
    await loadMonthlyDeepAnalysis(selectedEmployeeId.value)
  }
})
</script>



