<template>
  <div class="space-y-8 pb-10">
    <section class="rounded-[28px] border border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(79,70,229,0.18),_transparent_35%),linear-gradient(135deg,_#ffffff,_#eef2ff)] p-8 shadow-sm">
      <div class="flex flex-col xl:flex-row xl:items-end xl:justify-between gap-6">
        <div class="max-w-3xl">
          <p class="text-xs font-semibold uppercase tracking-[0.22em] text-indigo-600">Yonetici Overview</p>
          <h2 class="mt-3 text-3xl font-bold tracking-tight text-slate-900">360 derece feedback raporlarini artik ayri analiz ekranlarinda yonetiyoruz.</h2>
          <p class="mt-3 text-sm leading-6 text-slate-600">
            Soldaki sidebar altindaki yeni rapor bolumunden calisan ve departman analizlerini ayri ayri inceleyebilirsin.
            Bu ana ekran, o raporlara hizli gecis ve mevcut haftanin genel durumunu gormek icin sade bir kontrol paneli olarak duruyor.
          </p>
        </div>

        <div class="flex flex-col gap-4 min-w-[320px]">
          <router-link
            to="/feedback"
            class="inline-flex items-center justify-center rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
          >
            360 Feedback Ver
          </router-link>

          <div class="grid grid-cols-2 gap-4">
          <div class="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Bu hafta</p>
            <p class="mt-2 text-3xl font-bold text-slate-900">Hafta {{ departmentReport?.period_week ?? '-' }}</p>
            <p class="mt-1 text-sm text-slate-500">Aktif 360 feedback donemi</p>
          </div>
          <div class="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Departman ozeti</p>
            <p class="mt-2 text-3xl font-bold text-slate-900">{{ departmentName }}</p>
            <p class="mt-1 text-sm text-slate-500">NLP ve rapor merkezi</p>
          </div>
          </div>
        </div>
      </div>
    </section>

    <section class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <router-link
        to="/manager/feedback-reports/employees"
        class="group rounded-3xl border border-slate-200 bg-white p-7 shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg"
      >
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">Calisan Analizi</p>
            <h3 class="mt-2 text-2xl font-bold text-slate-900">Kisi bazli raporlar</h3>
          </div>
          <div class="rounded-2xl bg-indigo-50 p-3 text-indigo-600 transition-colors group-hover:bg-indigo-600 group-hover:text-white">
            <UsersIcon class="h-6 w-6" />
          </div>
        </div>

        <p class="mt-4 text-sm leading-6 text-slate-600">
          Ekipteki her calisan icin ayri rapor, skor grafigi, guclu yonler, risk alanlari ve yonetici aksiyon onerilerini gor.
        </p>

        <div class="mt-6 grid grid-cols-2 gap-4">
          <div class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <p class="text-xs text-slate-500">Secilebilir calisan</p>
            <p class="mt-2 text-2xl font-bold text-slate-900">{{ teamMemberCount }}</p>
          </div>
          <div class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <p class="text-xs text-slate-500">Odak</p>
            <p class="mt-2 text-lg font-bold text-slate-900">Bireysel durum</p>
          </div>
        </div>
      </router-link>

      <router-link
        to="/manager/feedback-reports/department"
        class="group rounded-3xl border border-slate-200 bg-white p-7 shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg"
      >
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600">Departman Analizi</p>
            <h3 class="mt-2 text-2xl font-bold text-slate-900">Toplu trend ve riskler</h3>
          </div>
          <div class="rounded-2xl bg-emerald-50 p-3 text-emerald-600 transition-colors group-hover:bg-emerald-600 group-hover:text-white">
            <BuildingOffice2Icon class="h-6 w-6" />
          </div>
        </div>

        <p class="mt-4 text-sm leading-6 text-slate-600">
          Bu alan yalnizca 360 feedback kaynakli enerji, motivasyon, psikolojik guven, flight risk ve risk temalari gibi NLP sinyallerini gosterir.
        </p>

        <div class="mt-6 grid grid-cols-2 gap-4">
          <div class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <p class="text-xs text-slate-500">Departman motivasyonu</p>
            <p class="mt-2 text-2xl font-bold text-slate-900">{{ departmentMotivation }}</p>
          </div>
          <div class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <p class="text-xs text-slate-500">Yuksek flight risk</p>
            <p class="mt-2 text-2xl font-bold text-slate-900">{{ highFlightRisk }}</p>
          </div>
        </div>
      </router-link>
    </section>

    <section class="grid grid-cols-1 xl:grid-cols-[minmax(0,1.1fr)_420px] gap-6">
      <div class="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
        <div class="flex items-center justify-between gap-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Bu haftanin ozeti</p>
            <h3 class="mt-2 text-xl font-bold text-slate-900">Departman snapshot</h3>
          </div>
          <span class="rounded-full border border-indigo-100 bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
            360 feedback summary
          </span>
        </div>

        <div class="mt-5 rounded-2xl border border-indigo-100 bg-indigo-50 p-5">
          <p class="text-sm leading-6 text-slate-700">
            {{ departmentReport?.report_summary || 'Bu hafta icin departman ozet raporu henuz olusmadi.' }}
          </p>
        </div>

        <div class="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div
            v-for="metric in previewMetrics"
            :key="metric.label"
            class="rounded-2xl border border-slate-100 bg-slate-50 p-4"
          >
            <p class="text-xs text-slate-500">{{ metric.label }}</p>
            <p class="mt-2 text-2xl font-bold text-slate-900">{{ metric.display_value }}</p>
            <p v-if="metric.description" class="mt-1 text-xs text-slate-400">{{ metric.description }}</p>
          </div>
        </div>
      </div>

      <div class="rounded-3xl border border-slate-800 bg-slate-900 p-7 shadow-lg">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Hizli yol</p>
        <h3 class="mt-2 text-xl font-bold text-white">Raporlari nasil okuyacaksin?</h3>

        <div class="mt-6 space-y-4">
          <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p class="text-xs font-semibold text-indigo-300">1. Calisan Analizi</p>
            <p class="mt-2 text-sm leading-6 text-slate-200">
              Tek bir calisanin son haftadaki skorlarini ve rapor ozetini incele. Burada kisisel destek ihtiyaclarini ve davranis sinyallerini yakalayabilirsin.
            </p>
          </div>

          <div class="rounded-2xl border border-white/10 bg-white/5 p-4">
            <p class="text-xs font-semibold text-emerald-300">2. Departman Analizi</p>
            <p class="mt-2 text-sm leading-6 text-slate-200">
              Tum ekibin ortak risklerini, trendlerini ve tekrar eden temalarini grafiklerle gor. Bu ekran aksiyon planlamak icin ana referans noktan olacak.
            </p>
          </div>

          <div class="rounded-2xl border border-amber-500/20 bg-amber-500/10 p-4">
            <p class="text-xs font-semibold text-amber-300">Onerilen ilk adim</p>
            <p class="mt-2 text-sm leading-6 text-slate-200">
              {{ departmentReport?.recommended_action || 'Daha fazla veri geldikce sistem ilk aksiyon onerilerini burada netlestirecek.' }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <section class="grid grid-cols-1 xl:grid-cols-[minmax(0,1.2fr)_380px] gap-6">
      <div class="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
        <div class="flex items-center justify-between gap-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Departman Performansi</p>
            <h3 class="mt-2 text-xl font-bold text-slate-900">KPI ozeti</h3>
          </div>
          <span class="rounded-full border border-sky-100 bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-700">
            KPI katmani
          </span>
        </div>

        <div class="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <p class="text-xs text-slate-500">Gorunen KPI kaydi</p>
            <p class="mt-2 text-2xl font-bold text-slate-900">{{ visibleKpiRecordCount }}</p>
            <p class="mt-1 text-xs text-slate-400">Yoneticiye acik kayitlar</p>
          </div>
          <div class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <p class="text-xs text-slate-500">Aktif KPI tanimi</p>
            <p class="mt-2 text-2xl font-bold text-slate-900">{{ activeKpiCount }}</p>
            <p class="mt-1 text-xs text-slate-400">Departmana bagli KPI adedi</p>
          </div>
          <div class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <p class="text-xs text-slate-500">Hedef uyumu</p>
            <p class="mt-2 text-2xl font-bold text-slate-900">{{ targetAlignmentRate }}</p>
            <p class="mt-1 text-xs text-slate-400">Hedefe ulasan kayit orani</p>
          </div>
        </div>

        <div class="mt-6 overflow-hidden rounded-2xl border border-slate-200">
          <div class="grid grid-cols-[minmax(0,1.3fr)_120px_120px] bg-slate-50 px-5 py-3 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
            <span>KPI</span>
            <span>Ortalama</span>
            <span>Hedef</span>
          </div>
          <div v-if="kpiRows.length">
            <div
              v-for="row in kpiRows"
              :key="row.name"
              class="grid grid-cols-[minmax(0,1.3fr)_120px_120px] items-center gap-3 border-t border-slate-100 px-5 py-4 text-sm"
            >
              <div>
                <p class="font-semibold text-slate-900">{{ row.name }}</p>
                <p class="mt-1 text-xs text-slate-500">{{ row.description }}</p>
              </div>
              <span class="font-semibold text-slate-700">{{ row.averageDisplay }}</span>
              <span class="font-semibold text-slate-700">{{ row.targetDisplay }}</span>
            </div>
          </div>
          <div v-else class="px-5 py-8 text-sm text-slate-400">
            Bu departman icin KPI kaydi bulunamadi.
          </div>
        </div>
      </div>

      <div class="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Ayrim mantigi</p>
        <h3 class="mt-2 text-xl font-bold text-slate-900">Hangi ekran neyi gosteriyor?</h3>

        <div class="mt-6 space-y-4">
          <div class="rounded-2xl border border-sky-100 bg-sky-50 p-4">
            <p class="text-xs font-semibold text-sky-700">Departman Performansi</p>
            <p class="mt-2 text-sm leading-6 text-slate-700">
              KPI tarafini ve yonetsel performans ozetini gosterir. Sayisal hedeflerin ve kayitlarin genel gorunumudur.
            </p>
          </div>

          <div class="rounded-2xl border border-indigo-100 bg-indigo-50 p-4">
            <p class="text-xs font-semibold text-indigo-700">360 Feedback Raporlari</p>
            <p class="mt-2 text-sm leading-6 text-slate-700">
              Yalnizca enerji, motivasyon, psikolojik guven, burnout ve flight risk gibi feedback kaynakli analizleri gosterir.
            </p>
          </div>

          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-xs font-semibold text-slate-700">360 Feedback Ver</p>
            <p class="mt-2 text-sm leading-6 text-slate-700">
              Manager olarak baska kisilere haftalik feedback vermeye devam edebilirsin. Ustteki buton seni dogrudan feedback ekranina goturur.
            </p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { BuildingOffice2Icon, UsersIcon } from '@heroicons/vue/24/outline'
import {
  feedbackApi,
  type Department360SummaryReportResponse,
  type EmployeeForFeedback,
  type SummaryMetric,
} from '@/services/api/feedback.api'
import { kpiApi, type KPIRecordDetailResponse } from '@/services/api/kpi.api'

const departmentReport = ref<Department360SummaryReportResponse | null>(null)
const teamMembers = ref<EmployeeForFeedback[]>([])
const kpiRecords = ref<KPIRecordDetailResponse[]>([])

const previewMetrics = computed<SummaryMetric[]>(() => departmentReport.value?.metrics.slice(0, 3) || [])
const teamMemberCount = computed(() => teamMembers.value.filter((employee) => employee.user.role === 'employee').length)
const departmentName = computed(() => departmentReport.value?.department_name || 'Departman')
const departmentMotivation = computed(
  () => departmentReport.value?.metrics.find((metric) => metric.label === 'Departman Motivasyonu')?.display_value || '-'
)
const highFlightRisk = computed(
  () => departmentReport.value?.metrics.find((metric) => metric.label === 'Yuksek Flight Risk')?.display_value || '-'
)
const visibleKpiRecordCount = computed(() => kpiRecords.value.length)
const activeKpiCount = computed(() => new Set(kpiRecords.value.map((record) => record.kpi_id)).size)

const targetAlignmentRate = computed(() => {
  const withTarget = kpiRecords.value.filter((record) => typeof record.kpi.target_value === 'number' && (record.kpi.target_value ?? 0) > 0)
  if (!withTarget.length) {
    return '-'
  }

  const aligned = withTarget.filter((record) => record.value >= (record.kpi.target_value ?? 0)).length
  return `%${Math.round((aligned / withTarget.length) * 100)}`
})

const kpiRows = computed(() => {
  const grouped = new Map<number, KPIRecordDetailResponse[]>()
  for (const record of kpiRecords.value) {
    const current = grouped.get(record.kpi_id) || []
    current.push(record)
    grouped.set(record.kpi_id, current)
  }

  return Array.from(grouped.values()).map((records) => {
    const sample = records[0]
    const average = records.reduce((sum, record) => sum + record.value, 0) / records.length
    const unitSuffix = sample.kpi.unit === 'percentage'
      ? '%'
      : sample.kpi.unit === 'hours'
        ? ' sa'
        : sample.kpi.unit === 'currency'
          ? ' TL'
          : ''

    return {
      name: sample.kpi.name,
      description: sample.kpi.description || 'Departman KPI kaydi',
      averageDisplay: `${average.toFixed(1)}${unitSuffix}`,
      targetDisplay: typeof sample.kpi.target_value === 'number'
        ? `${sample.kpi.target_value.toFixed(1)}${unitSuffix}`
        : '-',
    }
  })
})

async function loadDepartmentReport() {
  try {
    departmentReport.value = await feedbackApi.getDepartment360SummaryReport()
  } catch (error) {
    console.error('Departman raporu yuklenemedi:', error)
    departmentReport.value = null
  }
}

async function loadTeamMembers() {
  try {
    const candidates = await feedbackApi.getFeedbackCandidates()
    teamMembers.value = candidates
  } catch (error) {
    console.error('Ekip uyeleri yuklenemedi:', error)
    teamMembers.value = []
  }
}

async function loadKpiRecords() {
  try {
    kpiRecords.value = await kpiApi.getAllVisibleRecords()
  } catch (error) {
    console.error('KPI kayitlari yuklenemedi:', error)
    kpiRecords.value = []
  }
}

onMounted(async () => {
  await loadDepartmentReport()
  await loadTeamMembers()
  await loadKpiRecords()
})
</script>
