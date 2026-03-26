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
          <span
            v-for="badge in summary.badges"
            :key="badge.id"
            :class="getBadgeClass(badge.badge_level)"
            class="px-2 py-1 rounded-full text-xs font-bold border"
          >
            {{ getBadgeEmoji(badge.badge_type) }} {{ getBadgeLabel(badge.badge_type) }}
          </span>
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

    <!-- ─────────────────────────────────────── -->
    <!-- FEEDBACK VERME MODAL -->
    <!-- ─────────────────────────────────────── -->
    <div
      v-if="showFeedbackForm"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click.self="showFeedbackForm = false"
    >
      <div class="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
        <div class="p-6 border-b border-slate-100 flex justify-between items-center sticky top-0 bg-white rounded-t-2xl">
          <h3 class="text-lg font-bold text-slate-800">Geri Bildirim Ver</h3>
          <button @click="showFeedbackForm = false" class="text-slate-400 hover:text-slate-600 text-2xl leading-none">&times;</button>
        </div>

        <div class="p-6 space-y-6">

          <!-- Kişi Seç -->
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Kişi Seç *</label>
            <select
              v-model="form.reviewee_id"
              class="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            >
              <option value="">— Kişi seçin —</option>
              <option v-for="emp in employees" :key="emp.id" :value="emp.id">
                {{ emp.user.full_name }} · {{ emp.position ?? emp.department.name }}
              </option>
            </select>
          </div>

          <!-- Feedback Tipi -->
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Geri Bildirim Türü *</label>
            <div class="grid grid-cols-2 gap-2">
              <button
                v-for="type in feedbackTypes"
                :key="type.value"
                @click="form.feedback_type = type.value"
                :class="form.feedback_type === type.value
                  ? 'bg-indigo-600 text-white border-indigo-600'
                  : 'bg-white text-slate-600 border-slate-200 hover:border-indigo-300'"
                class="px-3 py-2 rounded-lg border text-sm font-medium transition text-left"
              >
                {{ type.emoji }} {{ type.label }}
              </button>
            </div>
          </div>

          <!-- Dönem -->
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Değerlendirme Dönemi *</label>
            <input
              v-model="form.period_date"
              type="date"
              class="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </div>

          <!-- Skorlar -->
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-4">Yetkinlik Skorları <span class="text-slate-400 font-normal">(1–5, opsiyonel)</span></label>
            <div class="space-y-3">
              <div v-for="skill in formSkills" :key="skill.key" class="flex items-center gap-4">
                <span class="w-36 text-sm text-slate-600 shrink-0">{{ skill.label }}</span>
                <div class="flex gap-2">
                  <button
                    v-for="n in 5"
                    :key="n"
                    @click="setScore(skill.key, n)"
                    :class="(form as any)[skill.key] >= n ? 'bg-indigo-500 text-white' : 'bg-slate-100 text-slate-400'"
                    class="w-8 h-8 rounded-lg text-sm font-bold transition hover:bg-indigo-400 hover:text-white"
                  >
                    {{ n }}
                  </button>
                </div>
                <span class="text-sm text-slate-500 w-4">{{ (form as any)[skill.key] ?? '—' }}</span>
              </div>
            </div>
          </div>

          <!-- Metin Alanları -->
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-emerald-700 mb-2">💪 En güçlü yönü nedir?</label>
              <textarea
                v-model="form.strength_text"
                rows="2"
                placeholder="Bu kişinin öne çıkan güçlü özelliklerini yazın..."
                class="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none resize-none"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-amber-700 mb-2">🎯 Geliştirebileceği alan?</label>
              <textarea
                v-model="form.improvement_text"
                rows="2"
                placeholder="Gelişim fırsatı olarak gördüğünüz alanı yazın..."
                class="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none resize-none"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-600 mb-2">💬 Genel yorum</label>
              <textarea
                v-model="form.general_comment"
                rows="2"
                placeholder="Eklemek istediğiniz genel bir yorum..."
                class="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none resize-none"
              />
            </div>
          </div>

          <!-- Anonim seçeneği -->
          <div class="flex items-center gap-3">
            <input type="checkbox" id="anon" v-model="form.is_anonymous" class="w-4 h-4 text-indigo-600 rounded" />
            <label for="anon" class="text-sm text-slate-600">Anonim olarak gönder</label>
          </div>

          <!-- Hata mesajı -->
          <div v-if="formError" class="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
            {{ formError }}
          </div>

          <!-- Gönder -->
          <button
            @click="submitFeedback"
            :disabled="submitting"
            class="w-full py-3 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ submitting ? 'Gönderiliyor...' : 'Geri Bildirimi Gönder' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { feedbackApi, type FeedbackResponse, type FeedbackRequestResponse, type FeedbackSummary, type EmployeeForFeedback, type FeedbackType, type BadgeType, type BadgeLevel } from '@/services/api/feedback.api'

// ── State ──────────────────────────────────────
const receivedFeedbacks  = ref<FeedbackResponse[]>([])
const incomingRequests   = ref<FeedbackRequestResponse[]>([])
const summary            = ref<FeedbackSummary | null>(null)
const employees          = ref<EmployeeForFeedback[]>([])
const showFeedbackForm   = ref(false)
const submitting         = ref(false)
const formError          = ref('')

const form = ref({
  reviewee_id:           '' as number | '',
  feedback_type:         'peer_to_peer' as FeedbackType,
  period_date:           new Date().toISOString().split('T')[0],
  score_communication:   null as number | null,
  score_teamwork:        null as number | null,
  score_problem_solving: null as number | null,
  score_leadership:      null as number | null,
  score_technical:       null as number | null,
  strength_text:         '',
  improvement_text:      '',
  general_comment:       '',
  is_anonymous:          false,
})

// ── Sabit veriler ──────────────────────────────
const feedbackTypes = [
  { value: 'peer_to_peer',        label: 'Eş Değerlendirme',    emoji: '🤝' },
  { value: 'manager_to_employee', label: 'Yöneticiden Çalışana', emoji: '📋' },
  { value: 'employee_to_manager', label: 'Çalışandan Yöneticiye',emoji: '⬆️' },
  { value: 'self_assessment',     label: 'Öz Değerlendirme',     emoji: '🪞' },
]

const formSkills = [
  { key: 'score_communication',   label: 'İletişim' },
  { key: 'score_teamwork',        label: 'Takım Çalışması' },
  { key: 'score_problem_solving', label: 'Problem Çözme' },
  { key: 'score_leadership',      label: 'Liderlik' },
  { key: 'score_technical',       label: 'Teknik Beceri' },
]

const skillScores = computed(() => [
  { key: 'communication',   label: 'İletişim',         value: summary.value?.avg_communication },
  { key: 'teamwork',        label: 'Takım Çalışması',  value: summary.value?.avg_teamwork },
  { key: 'problem_solving', label: 'Problem Çözme',    value: summary.value?.avg_problem_solving },
  { key: 'leadership',      label: 'Liderlik',         value: summary.value?.avg_leadership },
  { key: 'technical',       label: 'Teknik Beceri',    value: summary.value?.avg_technical },
])

// ── Yardımcı fonksiyonlar ──────────────────────
function setScore(key: string, value: number) {
  ;(form.value as any)[key] = (form.value as any)[key] === value ? null : value
}

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

function getFeedbackTypeLabel(type: FeedbackType) {
  const map: Record<FeedbackType, string> = {
    peer_to_peer:        'Eş Değerlendirme',
    manager_to_employee: 'Yöneticiden',
    employee_to_manager: 'Çalışandan Yöneticiye',
    self_assessment:     'Öz Değerlendirme',
  }
  return map[type] ?? type
}

function getBadgeEmoji(type: BadgeType) {
  const map: Record<BadgeType, string> = {
    team_player:    '🤝',
    problem_solver: '💡',
    communicator:   '🗣️',
    speed_champion: '⚡',
    mentor:         '🎓',
    innovator:      '🚀',
    reliable:       '🔒',
  }
  return map[type] ?? '🏅'
}

function getBadgeLabel(type: BadgeType) {
  const map: Record<BadgeType, string> = {
    team_player:    'Takım Kaptanı',
    problem_solver: 'Problem Avcısı',
    communicator:   'Kristal Konuşmacı',
    speed_champion: 'Hız Şampiyonu',
    mentor:         'Bilgi Aktarıcı',
    innovator:      'Yenilikçi',
    reliable:       'Güvenilir',
  }
  return map[type] ?? type
}

function getBadgeClass(level: BadgeLevel) {
  const map: Record<BadgeLevel, string> = {
    bronze: 'bg-amber-50 text-amber-700 border-amber-200',
    silver: 'bg-slate-100 text-slate-700 border-slate-300',
    gold:   'bg-yellow-50 text-yellow-700 border-yellow-300',
  }
  return map[level]
}

// ── API çağrıları ──────────────────────────────
async function loadData() {
  try {
    const [received, requests, sum, emps] = await Promise.all([
      feedbackApi.getReceivedFeedbacks(),
      feedbackApi.getIncomingRequests(),
      feedbackApi.getMyFeedbackSummary(),
      feedbackApi.getAllEmployees(),
    ])
    receivedFeedbacks.value = received
    incomingRequests.value  = requests
    summary.value           = sum
    employees.value         = emps
  } catch (e) {
    console.error('Veri yüklenemedi:', e)
  }
}

async function submitFeedback() {
  formError.value = ''

  if (!form.value.reviewee_id) {
    formError.value = 'Lütfen bir kişi seçin'
    return
  }
  if (!form.value.period_date) {
    formError.value = 'Lütfen dönem tarihi girin'
    return
  }

  submitting.value = true
  try {
    await feedbackApi.createFeedback({
      reviewee_id:           form.value.reviewee_id as number,
      feedback_type:         form.value.feedback_type,
      period_date:           form.value.period_date,
      score_communication:   form.value.score_communication ?? undefined,
      score_teamwork:        form.value.score_teamwork ?? undefined,
      score_problem_solving: form.value.score_problem_solving ?? undefined,
      score_leadership:      form.value.score_leadership ?? undefined,
      score_technical:       form.value.score_technical ?? undefined,
      strength_text:         form.value.strength_text || undefined,
      improvement_text:      form.value.improvement_text || undefined,
      general_comment:       form.value.general_comment || undefined,
      is_anonymous:          form.value.is_anonymous,
    })
    showFeedbackForm.value = false
    await loadData()
  } catch (e: any) {
    formError.value = e.response?.data?.detail ?? 'Bir hata oluştu, tekrar deneyin'
  } finally {
    submitting.value = false
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
  form.value.reviewee_id = req.requester_id
  form.value.period_date = req.period_date
  showFeedbackForm.value = true
}

onMounted(loadData)
</script>