<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-6">
      <div>
        <h1 class="text-3xl font-bold text-slate-900 tracking-tight">Ekip Yönetimi</h1>
        <p class="text-slate-500 mt-1">
          KPI, 360 geri bildirim ve haftalık nabız sinyallerini birlikte takip edin.
        </p>
        <p v-if="teamHealth" class="text-xs text-slate-400 mt-2">
          {{ teamHealth.department_name || 'Departman' }} · Güncelleme: {{ formatDateTime(teamHealth.generated_at) }}
        </p>
      </div>
      <button
        class="bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white font-medium px-4 py-2.5 rounded-lg transition-colors flex items-center gap-2 shadow-sm shadow-indigo-600/20"
        :disabled="riskMeetingCandidates.length === 0"
        @click="openMeetingModal()"
      >
        <CalendarDaysIcon class="w-5 h-5" />
        Risk Toplantısı Planla
      </button>
    </div>

    <div v-if="loadError" class="mb-6 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
      {{ loadError }}
    </div>

    <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
      <div
        v-for="stat in stats"
        :key="stat.key"
        class="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex items-center justify-between min-h-[112px]"
      >
        <div class="min-w-0">
          <p class="text-sm font-medium text-slate-500">{{ stat.label }}</p>
          <p class="text-2xl font-bold text-slate-900 mt-1">{{ stat.value }}</p>
          <p class="text-xs text-slate-400 mt-1 truncate" :title="stat.hint">{{ stat.hint }}</p>
        </div>
        <div class="p-3 rounded-lg shrink-0" :class="statIconClass(stat.tone)">
          <component :is="statIcon(stat.key)" class="w-6 h-6" />
        </div>
      </div>
    </div>

    <div class="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
      <div class="p-5 border-b border-slate-200 flex flex-col xl:flex-row gap-4 justify-between">
        <div>
          <h2 class="text-lg font-bold text-slate-900">Ekip Üyeleri</h2>
          <p class="text-xs text-slate-500 mt-1">{{ sourceSummaryText }}</p>
        </div>

        <div class="flex flex-col sm:flex-row gap-3">
          <div class="relative">
            <MagnifyingGlassIcon class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              v-model="searchTerm"
              type="text"
              placeholder="Ekipte ara..."
              class="pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:ring-1 focus:ring-indigo-500 w-full md:w-64"
            />
          </div>
          <select
            v-model="riskFilter"
            class="px-3 py-2 border border-slate-200 rounded-lg text-slate-600 bg-white hover:bg-slate-50 text-sm font-medium"
          >
            <option value="all">Tüm riskler</option>
            <option value="High">Yüksek risk</option>
            <option value="Medium">Orta risk</option>
            <option value="Low">Düşük risk</option>
          </select>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <th class="px-6 py-4">Çalışan</th>
              <th class="px-6 py-4">Rol / Takım</th>
              <th class="px-6 py-4">KPI</th>
              <th class="px-6 py-4">Nabız</th>
              <th class="px-6 py-4">360 Profil</th>
              <th class="px-6 py-4">Birleşik Risk</th>
              <th class="px-6 py-4 text-right">İşlemler</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-if="isLoading">
              <td colspan="7" class="px-6 py-10 text-center text-sm text-slate-500">Ekip verileri yükleniyor...</td>
            </tr>
            <tr v-else-if="filteredMembers.length === 0">
              <td colspan="7" class="px-6 py-10 text-center text-sm text-slate-500">Bu filtreyle eşleşen çalışan yok.</td>
            </tr>
            <tr v-for="member in filteredMembers" :key="member.id" class="hover:bg-slate-50 transition-colors">
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <img :src="avatarUrl(member.name)" :alt="member.name" class="w-8 h-8 rounded-full" />
                  <div>
                    <span class="font-medium text-slate-900 text-sm">{{ member.name }}</span>
                    <div class="flex gap-1 mt-1">
                      <span
                        v-for="source in member.data_sources"
                        :key="source"
                        class="px-1.5 py-0.5 rounded bg-slate-100 text-[10px] font-semibold text-slate-500"
                      >
                        {{ source }}
                      </span>
                    </div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 text-sm text-slate-600">
                <p>{{ member.role }}</p>
                <p class="text-xs text-slate-400">{{ member.team || 'Takım yok' }}</p>
              </td>
              <td class="px-6 py-4 text-sm text-slate-600">
                <p class="font-medium text-slate-800">{{ formatScore(member.kpi_score, '/100') }}</p>
                <p class="text-xs" :class="trendClass(member.kpi_trend)">
                  {{ formatTrend(member.kpi_trend) }}
                </p>
              </td>
              <td class="px-6 py-4 text-sm text-slate-600">
                <p class="font-medium text-slate-800">{{ formatScore(member.latest_pulse_score, '/5') }}</p>
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium mt-1" :class="mteClass(member.latest_mte)">
                  {{ mteLabel(member.latest_mte) }}
                </span>
              </td>
              <td class="px-6 py-4 text-sm text-slate-600">
                <p class="font-medium text-slate-800">{{ member.feedback_count }} yanıt</p>
                <p class="text-xs text-slate-400">
                  Uçuş: {{ riskLevelLabel(member.feedback_flight_risk_level) }} · Tükenmişlik: {{ riskLevelLabel(member.feedback_burnout_risk_level) }}
                </p>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full" :class="riskDotClass(member.combined_risk_level)"></span>
                  <span class="text-sm font-medium text-slate-700">{{ riskLabel(member.combined_risk_level) }}</span>
                  <span class="text-xs text-slate-400">{{ member.combined_risk_score }}/100</span>
                </div>
                <p class="text-xs text-slate-400 mt-1">{{ member.recommended_action }}</p>
              </td>
              <td class="px-6 py-4 text-right">
                <div class="flex justify-end gap-2">
                  <button
                    class="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                    title="Çalışan analizini aç"
                    @click="openEmployeeAnalysis(member)"
                  >
                    <ChartBarIcon class="w-5 h-5" />
                  </button>
                  <button
                    class="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                    title="Bu çalışanla toplantı planla"
                    @click="openMeetingModal(member)"
                  >
                    <CalendarDaysIcon class="w-5 h-5" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="showMeetingModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50">
      <div class="w-full max-w-2xl bg-white rounded-lg shadow-xl border border-slate-200">
        <div class="p-5 border-b border-slate-200 flex items-start justify-between gap-4">
          <div>
            <h3 class="text-lg font-bold text-slate-900">Risk Toplantısı Planla</h3>
            <p class="text-sm text-slate-500 mt-1">{{ selectedMeetingMembers.length }} çalışan için toplantı daveti oluşturulacak.</p>
          </div>
          <button class="p-2 rounded-lg hover:bg-slate-100 text-slate-500" @click="showMeetingModal = false">
            <XMarkIcon class="w-5 h-5" />
          </button>
        </div>

        <div class="p-5 space-y-4">
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <label class="text-sm font-medium text-slate-600">
              Tarih
              <input v-model="meetingForm.scheduled_date" type="date" class="mt-1 w-full rounded-lg border-slate-200 text-sm" />
            </label>
            <label class="text-sm font-medium text-slate-600">
              Saat
              <input v-model="meetingForm.scheduled_time" type="time" class="mt-1 w-full rounded-lg border-slate-200 text-sm" />
            </label>
            <label class="text-sm font-medium text-slate-600">
              Süre
              <select v-model.number="meetingForm.duration_minutes" class="mt-1 w-full rounded-lg border-slate-200 text-sm">
                <option :value="30">30 dk</option>
                <option :value="45">45 dk</option>
                <option :value="60">60 dk</option>
              </select>
            </label>
          </div>

          <label class="text-sm font-medium text-slate-600 block">
            Başlık
            <input v-model="meetingForm.title" type="text" class="mt-1 w-full rounded-lg border-slate-200 text-sm" />
          </label>

          <label class="text-sm font-medium text-slate-600 block">
            Toplantı Linki
            <input v-model="meetingForm.meeting_url" type="url" placeholder="https://meet.google.com/..." class="mt-1 w-full rounded-lg border-slate-200 text-sm" />
          </label>

          <label class="text-sm font-medium text-slate-600 block">
            Not
            <textarea v-model="meetingForm.note" rows="3" class="mt-1 w-full rounded-lg border-slate-200 text-sm"></textarea>
          </label>

          <div>
            <p class="text-sm font-medium text-slate-600 mb-2">Katılımcılar</p>
            <div class="max-h-44 overflow-y-auto rounded-lg border border-slate-200 divide-y divide-slate-100">
              <label
                v-for="member in meetingCandidatePool"
                :key="member.id"
                class="flex items-center justify-between gap-3 px-3 py-2 text-sm"
              >
                <span>
                  <span class="font-medium text-slate-800">{{ member.name }}</span>
                  <span class="text-slate-400 ml-2">{{ riskLabel(member.combined_risk_level) }}</span>
                </span>
                <input v-model="selectedMeetingMemberIds" :value="member.id" type="checkbox" class="rounded border-slate-300 text-indigo-600" />
              </label>
            </div>
          </div>

          <div v-if="meetingError" class="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
            {{ meetingError }}
          </div>
          <div v-if="meetingSuccess" class="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
            {{ meetingSuccess }}
          </div>
        </div>

        <div class="p-5 border-t border-slate-200 flex justify-end gap-3">
          <button class="px-4 py-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 text-sm font-medium" @click="showMeetingModal = false">
            Vazgeç
          </button>
          <button
            class="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white text-sm font-medium"
            :disabled="meetingSubmitting || selectedMeetingMembers.length === 0"
            @click="submitMeeting"
          >
            Davet Oluştur
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  CalendarDaysIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  MagnifyingGlassIcon,
  ShieldCheckIcon,
  SignalIcon,
  UserGroupIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'
import { employeeApi, type TeamHealthMember, type TeamHealthResponse, type TeamHealthStat } from '@/services/api/employee.api'
import { meetingsApi } from '@/services/api/meetings.api'

const router = useRouter()
const teamHealth = ref<TeamHealthResponse | null>(null)
const isLoading = ref(true)
const loadError = ref('')
const searchTerm = ref('')
const riskFilter = ref('all')
const showMeetingModal = ref(false)
const meetingSubmitting = ref(false)
const meetingError = ref('')
const meetingSuccess = ref('')
const selectedMeetingMemberIds = ref<number[]>([])

const meetingForm = reactive({
  title: 'Risk ve destek görüşmesi',
  scheduled_date: defaultMeetingDate(),
  scheduled_time: '10:00',
  duration_minutes: 45,
  meeting_url: '',
  note: 'KPI, 360 geri bildirim ve nabız sinyallerindeki riskleri birlikte değerlendirme.',
})

const stats = computed<TeamHealthStat[]>(() => teamHealth.value?.stats || [])
const members = computed<TeamHealthMember[]>(() => teamHealth.value?.members || [])
const riskMeetingCandidates = computed(() =>
  members.value.filter((member) => ['High', 'Medium'].includes(member.combined_risk_level))
)
const meetingCandidatePool = computed(() => riskMeetingCandidates.value.length ? riskMeetingCandidates.value : members.value)
const selectedMeetingMembers = computed(() =>
  meetingCandidatePool.value.filter((member) => selectedMeetingMemberIds.value.includes(member.id))
)
const filteredMembers = computed(() => {
  const term = searchTerm.value.trim().toLocaleLowerCase('tr-TR')
  return members.value.filter((member) => {
    const matchesSearch = !term || [member.name, member.role, member.team, member.external_employee_code]
      .filter(Boolean)
      .some((value) => String(value).toLocaleLowerCase('tr-TR').includes(term))
    const matchesRisk = riskFilter.value === 'all' || member.combined_risk_level === riskFilter.value
    return matchesSearch && matchesRisk
  })
})
const sourceSummaryText = computed(() => {
  const summary = teamHealth.value?.source_summary
  if (!summary) return 'KPI, 360 ve nabız kaynakları yükleniyor.'
  return `KPI: ${summary.kpi_analyzed_count} · Nabız: ${summary.pulse_response_count} · 360: ${summary.feedback_profile_count}`
})

onMounted(fetchTeamHealth)

async function fetchTeamHealth() {
  isLoading.value = true
  loadError.value = ''
  try {
    teamHealth.value = await employeeApi.getTeamHealth()
  } catch (error) {
    console.error('Failed to load team health', error)
    loadError.value = 'Ekip verileri alınamadı. Oturum yetkisini ve backend bağlantısını kontrol edin.'
  } finally {
    isLoading.value = false
  }
}

function openMeetingModal(member?: TeamHealthMember) {
  meetingError.value = ''
  meetingSuccess.value = ''
  selectedMeetingMemberIds.value = member
    ? [member.id]
    : riskMeetingCandidates.value.map((candidate) => candidate.id)
  const names = selectedMeetingMembers.value.map((item) => item.name).slice(0, 2).join(', ')
  meetingForm.title = member ? `${member.name} risk ve destek görüşmesi` : 'Riskli çalışanlar destek toplantısı'
  meetingForm.note = names
    ? `${names}${selectedMeetingMembers.value.length > 2 ? ' ve diğerleri' : ''} için birleşik risk sinyalleri değerlendirilecek.`
    : 'KPI, 360 geri bildirim ve nabız sinyallerindeki riskleri birlikte değerlendirme.'
  showMeetingModal.value = true
}

async function submitMeeting() {
  meetingSubmitting.value = true
  meetingError.value = ''
  meetingSuccess.value = ''
  try {
    const attendees = selectedMeetingMembers.value.map((member) => ({
      db_employee_id: member.id,
      name: member.name,
      role: member.role,
    }))
    const response = await meetingsApi.createTeamRiskMeeting({
      team: teamHealth.value?.department_name || 'Ekip',
      title: meetingForm.title,
      scheduled_date: meetingForm.scheduled_date,
      scheduled_time: meetingForm.scheduled_time,
      duration_minutes: meetingForm.duration_minutes,
      meeting_url: meetingForm.meeting_url.trim() || null,
      note: meetingForm.note,
      agenda_items: [
        'Birleşik risk skorundaki ana sinyalleri değerlendirme',
        'KPI düşüşü, nabız skoru ve 360 NLP bulgularını birlikte okuma',
        'Çalışan için destek ve takip aksiyonunu netleştirme',
      ],
      attendees,
    })
    const linkText = response.meeting_url ? ' Toplantı linki davetlere eklendi.' : ''
    meetingSuccess.value = `${response.attendee_count} katılımcı için toplantı ve ${response.notification_count} bildirim oluşturuldu.${linkText}`
  } catch (error) {
    console.error('Meeting create failed', error)
    meetingError.value = 'Toplantı oluşturulamadı. Tarih, saat ve katılımcı seçimini kontrol edin.'
  } finally {
    meetingSubmitting.value = false
  }
}

function openEmployeeAnalysis(member: TeamHealthMember) {
  router.push({
    name: 'manager-kpi-ml-analysis',
    query: { section: 'watchlist', employeeId: String(member.id) },
  })
}

function avatarUrl(name: string) {
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=f3e8ff&color=6b21a8`
}

function statIcon(key: string) {
  if (key === 'kpi_coverage') return ChartBarIcon
  if (key === 'pulse_average') return SignalIcon
  if (key === 'feedback_coverage') return UserGroupIcon
  if (key === 'risk_candidates') return ExclamationTriangleIcon
  return ShieldCheckIcon
}

function statIconClass(tone: string) {
  const classes: Record<string, string> = {
    indigo: 'bg-indigo-50 text-indigo-600',
    blue: 'bg-blue-50 text-blue-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    amber: 'bg-amber-50 text-amber-600',
    rose: 'bg-rose-50 text-rose-600',
    slate: 'bg-slate-100 text-slate-600',
  }
  return classes[tone] || classes.slate
}

function formatScore(value?: number | null, suffix = '') {
  return value === null || value === undefined ? 'Veri yok' : `${value}${suffix}`
}

function formatTrend(value?: number | null) {
  if (value === null || value === undefined) return 'Trend yok'
  if (value > 0) return `+${value} trend`
  return `${value} trend`
}

function trendClass(value?: number | null) {
  if (value === null || value === undefined) return 'text-slate-400'
  if (value > 0) return 'text-emerald-600'
  if (value < 0) return 'text-rose-600'
  return 'text-slate-400'
}

function mteLabel(value?: number | null) {
  if (value === null || value === undefined) return 'MTE yok'
  if (value > 0.1) return 'Pozitif'
  if (value < -0.1) return 'Negatif'
  return 'Stabil'
}

function mteClass(value?: number | null) {
  if (value === null || value === undefined) return 'bg-slate-50 text-slate-600'
  if (value > 0.1) return 'bg-emerald-50 text-emerald-700'
  if (value < -0.1) return 'bg-rose-50 text-rose-700'
  return 'bg-blue-50 text-blue-700'
}

function riskLabel(level?: string | null) {
  if (level === 'High' || level === 'high') return 'Yüksek Risk'
  if (level === 'Medium' || level === 'medium') return 'Orta Risk'
  if (level === 'Low' || level === 'low') return 'Düşük Risk'
  return 'Bilinmiyor'
}

function riskLevelLabel(level?: string | null) {
  if (!level) return 'Yok'
  return riskLabel(level).replace(' Risk', '')
}

function riskDotClass(level?: string | null) {
  if (level === 'High') return 'bg-rose-500'
  if (level === 'Medium') return 'bg-amber-500'
  return 'bg-emerald-500'
}

function formatDateTime(value?: string | null) {
  if (!value) return 'Yok'
  return new Date(value).toLocaleString('tr-TR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function defaultMeetingDate() {
  const date = new Date()
  date.setDate(date.getDate() + 1)
  return date.toISOString().slice(0, 10)
}
</script>
