<template>
  <div class="space-y-8 pb-10">

    <!-- Başlık -->
    <div class="flex flex-col md:flex-row justify-between items-end gap-4 border-b border-slate-200 pb-6">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 tracking-tight">360° Geri Bildirim</h2>
        <p class="text-slate-500 mt-1">Ekip arkadaşlarına geri bildirim ver, kendi gelişimini takip et</p>
      </div>
      <button
        @click="showFeedbackForm = true"
        class="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 shadow-md shadow-indigo-200 transition-all flex items-center gap-2"
      >
        <span class="text-lg">+</span>
        Geri Bildirim Ver
      </button>
    </div>

    <div class="bg-white rounded-xl p-4 border border-slate-200">
      <p class="text-sm text-slate-700">
        Bu haftaki zorunlu {{ weeklyProgress?.required_count ?? 3 }} feedbackten
        <strong>{{ weeklyProgress?.completed_count ?? 0 }}</strong> tanesini tamamladin.
      </p>
      <div class="w-full bg-slate-100 rounded-full h-2.5 mt-3">
        <div
          class="h-2.5 rounded-full bg-indigo-600 transition-all"
          :style="{ width: progressPercent + '%' }"
        />
      </div>
    </div>

    <div v-if="weeklyProgress && !weeklyProgress.is_completed" class="bg-amber-50 rounded-xl p-4 border border-amber-200">
      <p class="text-sm text-amber-800">
        Haftalik zorunlu feedback hedefin henuz tamamlanmadi.
        Kalan: <strong>{{ weeklyProgress.remaining_count }}</strong>
      </p>
    </div>

    <div v-if="weeklyAssignment" class="bg-indigo-50 rounded-xl p-5 border border-indigo-200">
      <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-700">Haftalik Atama Akisi</p>
          <h3 class="mt-1 text-lg font-bold text-slate-900">{{ getSlotTitle(weeklyAssignment.current_slot) }}</h3>
          <p class="mt-2 text-sm text-slate-700">
            {{ getSlotDescription(weeklyAssignment.current_slot) }}
          </p>
        </div>
        <div v-if="weeklyAssignment.mandatory_assignment" class="rounded-xl border border-indigo-100 bg-white px-4 py-3 text-sm text-slate-700">
          <p class="text-xs font-semibold text-indigo-700 mb-1">Sistemin bu hafta atadigi kisi</p>
          <p class="font-semibold text-slate-900">{{ weeklyAssignment.mandatory_assignment.employee.user.full_name }}</p>
          <p class="text-xs text-slate-500 mt-1">
            {{ weeklyAssignment.mandatory_assignment.employee.department.name }} · {{ weeklyAssignment.mandatory_assignment.employee.position || 'Calisan' }}
          </p>
        </div>
      </div>

      <div class="mt-4 flex flex-wrap gap-2">
        <span
          v-for="rule in weeklyAssignment.rules_summary"
          :key="rule"
          class="px-2.5 py-1 text-xs rounded-full bg-white text-slate-600 border border-indigo-100"
        >
          {{ rule }}
        </span>
      </div>
    </div>

    <div v-if="myNlpInsight" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-sm text-slate-500">Bu Haftaki NLP Ozetin</p>
            <h3 class="text-lg font-bold text-slate-900 mt-1">Duygu ve risk sinyalleri</h3>
          </div>
          <span
            class="px-3 py-1 rounded-full text-xs font-semibold border"
            :class="getRiskBadgeClass(myNlpInsight.profile.flight_risk_level)"
          >
            Ucus riski: {{ getRiskLabel(myNlpInsight.profile.flight_risk_level) }}
            <span v-if="myNlpInsight.profile.flight_risk_confidence != null">
              · Guven {{ formatConfidence(myNlpInsight.profile.flight_risk_confidence) }}
            </span>
          </span>
        </div>

        <div class="mt-5 rounded-lg border border-amber-200 bg-amber-50 p-4">
          <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.16em] text-amber-700">Karar destek notu</p>
              <p class="mt-1 text-sm text-amber-900">
                Bu NLP sonucu otomatik uretilmis bir oneridir; performans karari veya aksiyon icin yonetici onayi gerekir.
              </p>
            </div>
            <span class="self-start md:self-center rounded-full border border-amber-300 bg-white px-3 py-1 text-xs font-semibold text-amber-800">
              {{ humanReviewStatusLabel }}
            </span>
          </div>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div class="rounded-lg bg-slate-50 p-4 border border-slate-100">
            <p class="text-xs text-slate-500">Motivasyon</p>
            <p class="text-2xl font-bold text-slate-900">{{ formatScore(myNlpInsight.profile.avg_motivation_score) }}</p>
          </div>
          <div class="rounded-lg bg-slate-50 p-4 border border-slate-100">
            <p class="text-xs text-slate-500">Psikolojik guven</p>
            <p class="text-2xl font-bold text-slate-900">{{ formatScore(myNlpInsight.profile.avg_psychological_safety_score) }}</p>
          </div>
          <div class="rounded-lg bg-slate-50 p-4 border border-slate-100">
            <p class="text-xs text-slate-500">Is birligi</p>
            <p class="text-2xl font-bold text-slate-900">{{ formatScore(myNlpInsight.profile.avg_collaboration_score) }}</p>
          </div>
          <div class="rounded-lg bg-slate-50 p-4 border border-slate-100">
            <p class="text-xs text-slate-500">Geri bildirim sayisi</p>
            <p class="text-2xl font-bold text-slate-900">{{ myNlpInsight.profile.feedback_count }}</p>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <div class="rounded-lg bg-rose-50 p-4 border border-rose-100">
            <p class="text-xs text-rose-700">Flight risk confidence</p>
            <p class="mt-1 text-xl font-bold text-rose-800">
              {{ formatConfidence(myNlpInsight.profile.flight_risk_confidence) }}
            </p>
            <p class="mt-1 text-xs text-rose-700">Kategori: {{ getRiskLabel(myNlpInsight.profile.flight_risk_level) }}</p>
          </div>
          <div class="rounded-lg bg-amber-50 p-4 border border-amber-100">
            <p class="text-xs text-amber-700">Burnout risk confidence</p>
            <p class="mt-1 text-xl font-bold text-amber-800">
              {{ formatConfidence(myNlpInsight.profile.burnout_risk_confidence) }}
            </p>
            <p class="mt-1 text-xs text-amber-700">Kategori: {{ getRiskLabel(myNlpInsight.profile.burnout_risk_level) }}</p>
          </div>
        </div>

        <div v-if="myNlpInsight.profile.manager_summary" class="mt-5 rounded-lg bg-indigo-50 border border-indigo-100 p-4">
          <p class="text-xs font-semibold text-indigo-700 mb-1">Kisa ozet</p>
          <p class="text-sm text-slate-700">{{ myNlpInsight.profile.manager_summary }}</p>
        </div>
      </div>

      <div class="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
        <p class="text-sm text-slate-500">Odak Alanlari</p>
        <div class="mt-4">
          <p class="text-xs font-semibold text-slate-500 mb-2">Guclu yonler</p>
          <div class="flex flex-wrap gap-2">
            <span v-for="item in myNlpInsight.profile.top_strengths" :key="`strength-${item}`" class="px-2 py-1 text-xs rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
              {{ item }}
            </span>
            <span v-if="!myNlpInsight.profile.top_strengths.length" class="text-sm text-slate-400">Henuz veri yok</span>
          </div>
        </div>
        <div class="mt-4">
          <p class="text-xs font-semibold text-slate-500 mb-2">Destek ihtiyaclari</p>
          <div class="flex flex-wrap gap-2">
            <span v-for="item in myNlpInsight.profile.top_support_needs" :key="`support-${item}`" class="px-2 py-1 text-xs rounded-full bg-amber-50 text-amber-700 border border-amber-200">
              {{ item }}
            </span>
            <span v-if="!myNlpInsight.profile.top_support_needs.length" class="text-sm text-slate-400">Henuz veri yok</span>
          </div>
        </div>
        <div class="mt-4">
          <p class="text-xs font-semibold text-slate-500 mb-2">Risk alanlari</p>
          <div class="flex flex-wrap gap-2">
            <span v-for="item in myNlpInsight.profile.top_risk_areas" :key="`risk-${item}`" class="px-2 py-1 text-xs rounded-full bg-rose-50 text-rose-700 border border-rose-200">
              {{ item }}
            </span>
            <span v-if="!myNlpInsight.profile.top_risk_areas.length" class="text-sm text-slate-400">Henuz veri yok</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Özet Kartlar -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Genel Ortalama -->
      <div class="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
        <p class="text-sm text-slate-500 mb-1">Genel Ortalama</p>
        <p class="text-4xl font-bold text-indigo-600">
          {{ summary?.overall_avg?.toFixed(1) ?? '—' }}
          <span class="text-lg text-slate-400">/5</span>
        </p>
        <p class="text-xs text-slate-400 mt-1">{{ summary?.total_received ?? 0 }} geri bildirim alındı</p>
      </div>

      <!-- Rozetler -->
      <div class="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
        <p class="text-sm text-slate-500 mb-3">Rozetlerim</p>
        <div v-if="summary?.badges?.length" class="flex flex-wrap gap-2">
          <div
            v-for="badge in summary.badges"
            :key="badge.id"
            class="flex items-center"
            :title="getBadgeDescription(badge)"
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
        <p v-else class="text-sm text-slate-400">Henüz rozet kazanılmadı</p>
      </div>

      <!-- Bekleyen Talepler -->
      <div class="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
        <p class="text-sm text-slate-500 mb-1">Bekleyen Talepler</p>
        <p class="text-4xl font-bold text-amber-500">{{ incomingRequests.length }}</p>
        <p class="text-xs text-slate-400 mt-1">yanıt bekliyor</p>
      </div>
    </div>

    <!-- Skor Breakdown -->
    <div v-if="summary" class="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
      <h3 class="font-bold text-slate-800 mb-6">Yetkinlik Skorlarım</h3>
      <div class="space-y-4">
        <div v-for="skill in skillScores" :key="skill.key" class="flex items-center gap-4">
          <span class="w-36 text-sm text-slate-600 shrink-0">{{ skill.label }}</span>
          <div class="flex-1 bg-slate-100 rounded-full h-2.5">
            <div
              class="h-2.5 rounded-full transition-all duration-500"
              :class="getScoreColor(skill.value)"
              :style="{ width: skill.value ? (skill.value / 5 * 100) + '%' : '0%' }"
            ></div>
          </div>
          <span class="w-8 text-sm font-bold text-slate-700 text-right">
            {{ skill.value?.toFixed(1) ?? '—' }}
          </span>
        </div>
      </div>
    </div>

    <!-- Bekleyen Talepler Listesi -->
    <div v-if="incomingRequests.length > 0" class="bg-amber-50 rounded-xl p-6 border border-amber-200">
      <h3 class="font-bold text-amber-800 mb-4">📬 Bekleyen Feedback Talepleri</h3>
      <div class="space-y-3">
        <div
          v-for="req in incomingRequests"
          :key="req.id"
          class="bg-white rounded-lg p-4 border border-amber-100 flex justify-between items-center"
        >
          <div>
            <p class="text-sm font-medium text-slate-800">
              Çalışan #{{ req.requester_id }} sizden geri bildirim talep ediyor
            </p>
            <p class="text-xs text-slate-500 mt-1">
              Dönem: {{ req.period_date }}
              <span v-if="req.deadline"> · Son tarih: {{ req.deadline }}</span>
            </p>
            <p v-if="req.message" class="text-xs text-slate-600 mt-1 italic">"{{ req.message }}"</p>
          </div>
          <div class="flex gap-2">
            <button
              @click="acceptRequest(req)"
              class="px-3 py-1.5 bg-indigo-600 text-white text-xs rounded-lg hover:bg-indigo-700 transition"
            >
              Geri Bildirim Ver
            </button>
            <button
              @click="declineRequest(req.id)"
              class="px-3 py-1.5 bg-white border border-slate-200 text-slate-600 text-xs rounded-lg hover:bg-slate-50 transition"
            >
              Reddet
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Aldığım Feedbackler -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
      <div class="p-6 border-b border-slate-100 flex justify-between items-center">
        <h3 class="font-bold text-slate-800">Aldığım Geri Bildirimler</h3>
        <span class="text-xs text-slate-400">{{ receivedFeedbacks.length }} toplam</span>
      </div>

      <div v-if="receivedFeedbacks.length === 0" class="p-12 text-center text-slate-400">
        <p class="text-4xl mb-3">💬</p>
        <p class="text-sm">Henüz geri bildirim almadınız</p>
      </div>

      <div v-else class="divide-y divide-slate-50">
        <div
          v-for="fb in receivedFeedbacks"
          :key="fb.id"
          class="p-6 hover:bg-slate-50/50 transition"
        >
          <div class="flex justify-between items-start mb-3">
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-sm">
                {{ fb.is_anonymous ? '?' : (fb.reviewer?.full_name?.[0] ?? '#') }}
              </div>
              <div>
                <p class="text-sm font-medium text-slate-800">
                  {{ fb.is_anonymous ? 'Anonim' : (fb.reviewer?.full_name ?? 'Çalışan #' + fb.reviewer_id) }}
                </p>
                <p class="text-xs text-slate-400">
                  {{ getFeedbackTypeLabel(fb.feedback_type) }} · {{ fb.period_date }}
                </p>
              </div>
            </div>
            <!-- Mini skor göstergesi -->
            <div v-if="getAvgScore(fb)" class="text-right">
              <span class="text-lg font-bold" :class="getScoreTextColor(getAvgScore(fb))">
                {{ getAvgScore(fb) }}
              </span>
              <p class="text-xs text-slate-400">/5</p>
            </div>
          </div>

          <!-- Metin yorumlar -->
          <div class="space-y-2 mt-3">
            <div v-if="fb.strength_text" class="bg-emerald-50 rounded-lg p-3 border border-emerald-100">
              <p class="text-xs font-semibold text-emerald-700 mb-1">💪 Güçlü Yön</p>
              <p class="text-sm text-slate-700">{{ fb.strength_text }}</p>
            </div>
            <div v-if="fb.improvement_text" class="bg-amber-50 rounded-lg p-3 border border-amber-100">
              <p class="text-xs font-semibold text-amber-700 mb-1">🎯 Gelişim Alanı</p>
              <p class="text-sm text-slate-700">{{ fb.improvement_text }}</p>
            </div>
            <div v-if="fb.general_comment" class="bg-slate-50 rounded-lg p-3 border border-slate-100">
              <p class="text-xs font-semibold text-slate-500 mb-1">💬 Genel Yorum</p>
              <p class="text-sm text-slate-700">{{ fb.general_comment }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <FeedbackModal
      :open="showFeedbackForm"
      :candidates="feedbackCandidates"
      :weekly-assignment="weeklyAssignment"
      @close="showFeedbackForm = false"
      @submitted="loadData"
    />

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { feedbackApi, type FeedbackResponse, type FeedbackRequestResponse, type FeedbackSummary, type EmployeeForFeedback, type WeeklyProgressResponse, type ClassicFeedbackType, type BadgeType, type BadgeLevel, type BadgeResponse, type WeeklyNLPInsightResponse, type NLPRiskLevel, type WeeklyAssignmentStateResponse } from '@/services/api/feedback.api'
import FeedbackModal from '@/components/feedback/FeedbackModal.vue'
import BadgeMedal from '@/components/common/BadgeMedal.vue'

// ── State ──────────────────────────────────────
const receivedFeedbacks  = ref<FeedbackResponse[]>([])
const incomingRequests   = ref<FeedbackRequestResponse[]>([])
const summary            = ref<FeedbackSummary | null>(null)
const employees          = ref<EmployeeForFeedback[]>([])
const showFeedbackForm   = ref(false)
const weeklyProgress     = ref<WeeklyProgressResponse | null>(null)
const weeklyAssignment   = ref<WeeklyAssignmentStateResponse | null>(null)
const myNlpInsight       = ref<WeeklyNLPInsightResponse | null>(null)
const authStore          = useAuthStore()

const skillScores = computed(() => [
  { key: 'communication',   label: 'İletişim',         value: summary.value?.avg_communication },
  { key: 'teamwork',        label: 'Takım Çalışması',  value: summary.value?.avg_teamwork },
  { key: 'problem_solving', label: 'Problem Çözme',    value: summary.value?.avg_problem_solving },
  { key: 'leadership',      label: 'Liderlik',         value: summary.value?.avg_leadership },
  { key: 'technical',       label: 'Teknik Beceri',    value: summary.value?.avg_technical },
])

const feedbackCandidates = computed(() =>
  (weeklyAssignment.value?.available_candidates || employees.value).filter(emp => emp.user_id !== authStore.user?.id)
)

const progressPercent = computed(() => {
  if (!weeklyProgress.value) return 0
  const { completed_count, required_count } = weeklyProgress.value
  if (!required_count) return 0
  return Math.min((completed_count / required_count) * 100, 100)
})

const humanReviewStatusLabel = computed(() => {
  const role = authStore.user?.role
  if (role === 'admin' || role === 'department_manager') return 'Yonetici onayi bekliyor'
  return 'Yonetici dogrulamasi gerekli'
})

// ── Yardımcı fonksiyonlar ──────────────────────
function getAvgScore(fb: FeedbackResponse): string | null {
  const scores = [fb.score_communication, fb.score_teamwork, fb.score_problem_solving, fb.score_leadership, fb.score_technical].filter(s => s != null) as number[]
  if (!scores.length) return null
  return (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1)
}

function getScoreColor(val?: number | null) {
  if (!val) return 'bg-slate-300'
  if (val >= 4) return 'bg-emerald-500'
  if (val >= 3) return 'bg-amber-400'
  return 'bg-red-400'
}

function getScoreTextColor(val: string | null) {
  if (!val) return 'text-slate-400'
  const n = parseFloat(val)
  if (n >= 4) return 'text-emerald-600'
  if (n >= 3) return 'text-amber-500'
  return 'text-red-500'
}

function getFeedbackTypeLabel(type: ClassicFeedbackType) {
  const map: Record<ClassicFeedbackType, string> = {
    peer_to_peer:        'Eş Değerlendirme',
    manager_to_employee: 'Yöneticiden',
    employee_to_manager: 'Çalışandan Yöneticiye',
    self_assessment:     'Öz Değerlendirme',
  }
  return map[type] ?? type
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

function formatScore(value?: number | null) {
  return value != null ? value.toFixed(1) : '—'
}

function formatConfidence(value?: number | null) {
  if (value == null || Number.isNaN(Number(value))) return 'Belirsiz'
  return `%${Math.round(Math.max(0, Math.min(1, Number(value))) * 100)}`
}

function getRiskLabel(level?: NLPRiskLevel) {
  const map: Record<NLPRiskLevel, string> = {
    low: 'Dusuk',
    medium: 'Orta',
    high: 'Yuksek',
  }
  return level ? map[level] : 'Belirsiz'
}

function getRiskBadgeClass(level?: NLPRiskLevel) {
  if (level === 'high') return 'bg-rose-50 text-rose-700 border-rose-200'
  if (level === 'medium') return 'bg-amber-50 text-amber-700 border-amber-200'
  if (level === 'low') return 'bg-emerald-50 text-emerald-700 border-emerald-200'
  return 'bg-slate-50 text-slate-600 border-slate-200'
}

function getSlotTitle(slot?: WeeklyAssignmentStateResponse['current_slot']) {
  const map = {
    mandatory_random: '1. Slot · Zorunlu Sistem Atamasi',
    department_internal: '2. Slot · Departman Ici Secim',
    cross_functional: '3. Slot · Departman Ici Son Secim',
    completed: 'Bu haftaki 3 feedback hakki tamamlandi',
  }
  return slot ? map[slot] : 'Haftalik atama'
}

function getSlotDescription(slot?: WeeklyAssignmentStateResponse['current_slot']) {
  const map = {
    mandatory_random: 'Oncelikle sistemin atadigi kisiye geri bildirim vererek haftalik akisi baslatman gerekiyor.',
    department_internal: 'Simdi kendi departmanindan bir ekip arkadasini veya yoneticini secerek ikinci feedbackini tamamlayabilirsin.',
    cross_functional: 'Ucuncu feedbackte de yalnizca kendi departmanindan birini secerek haftalik donguyu tamamlayabilirsin.',
    completed: 'Haftalik zorunlu akisi tamamladin. Dilersen daha fazla geri bildirim vermeye devam edebilirsin.',
  }
  return slot ? map[slot] : ''
}

// ── API çağrıları ──────────────────────────────
async function loadData() {
  try {
    if (!authStore.user && authStore.token) {
      await authStore.fetchCurrentUser()
    }

    const [received, requests, sum, emps, progress, assignment, nlpInsight] = await Promise.all([
      feedbackApi.getReceivedFeedbacks(),
      feedbackApi.getIncomingRequests(),
      feedbackApi.getMyFeedbackSummary(),
      feedbackApi.getFeedbackCandidates(),
      feedbackApi.getWeeklyProgress(),
      feedbackApi.getWeeklyAssignmentState().catch(() => null),
      feedbackApi.getMyWeeklyNlpProfile().catch(() => null),
    ])
    receivedFeedbacks.value = received
    incomingRequests.value  = requests
    summary.value           = sum
    employees.value         = emps
    weeklyProgress.value    = progress
    weeklyAssignment.value  = assignment
    myNlpInsight.value      = nlpInsight
  } catch (e) {
    console.error('Veri yüklenemedi:', e)
  }
}

async function declineRequest(requestId: number) {
  try {
    await feedbackApi.updateRequestStatus(requestId, 'declined')
    await loadData()
  } catch (e) {
    console.error(e)
  }
}

function acceptRequest(req: FeedbackRequestResponse) {
  showFeedbackForm.value = true
}

onMounted(loadData)
</script>

