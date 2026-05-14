<template>
  <div
    v-if="open"
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
    @click.self="$emit('close')"
  >
    <div class="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
      <div class="p-6 border-b border-slate-100 flex justify-between items-center sticky top-0 bg-white rounded-t-2xl">
        <h3 class="text-lg font-bold text-slate-800">Haftalik Nabiz Geri Bildirimi</h3>
        <button @click="$emit('close')" class="text-slate-400 hover:text-slate-600 text-2xl leading-none">&times;</button>
      </div>

      <div class="p-6 space-y-6">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">Kisi Sec *</label>
          <p v-if="isMandatoryLocked" class="mb-2 text-xs text-indigo-700">
            Bu hafta once sistemin atadigi kisiyi tamamlaman gerekiyor.
          </p>
          <select
            v-model="receiverId"
            :disabled="isMandatoryLocked"
            class="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          >
            <option :value="null">- Kisi secin -</option>
            <optgroup
              v-for="group in candidateGroups"
              :key="group.key"
              :label="group.label"
            >
              <option v-for="emp in group.items" :key="emp.id" :value="emp.id">
                {{ emp.user.full_name }} · {{ getRoleLabel(emp.user.role) }} · {{ emp.position ?? emp.department.name }}
              </option>
            </optgroup>
          </select>
          <div v-if="candidateGroups.length" class="mt-3 space-y-2">
            <p class="text-xs font-semibold text-slate-500">Secim gruplari</p>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="group in candidateGroups"
                :key="`pill-${group.key}`"
                class="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-600"
              >
                {{ group.label }}
              </span>
            </div>
            <p v-if="slotHint" class="text-xs text-slate-500">
              {{ slotHint }}
            </p>
          </div>
        </div>

        <div v-if="loadingQuestion" class="text-sm text-slate-500">Haftalik soru yukleniyor...</div>
        <div v-else-if="currentQuestion" class="bg-indigo-50 border border-indigo-100 rounded-lg p-4">
          <p class="text-xs font-semibold text-indigo-700 mb-2">
            {{ currentQuestion.week_number }}. Hafta · {{ currentQuestion.category }}
          </p>
          <p class="text-sm text-slate-800">{{ currentQuestion.question_text }}</p>
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-3">Genel Yetkinlik Puanlari (1-5) *</label>
          <div class="space-y-4">
            <div v-for="skill in scoreFields" :key="skill.key">
              <div class="flex justify-between items-center mb-1">
                <span class="text-sm text-slate-700">{{ skill.label }}</span>
                <span class="text-sm font-semibold text-slate-600">{{ scores[skill.key] }}</span>
              </div>
              <input
                v-model.number="scores[skill.key]"
                type="range"
                min="1"
                max="5"
                step="1"
                class="w-full accent-indigo-600"
              />
            </div>
          </div>
        </div>

        <div>
          <div class="mb-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <label class="block text-sm font-medium text-slate-700">Haftalik Ozel Yanit *</label>
            <div class="flex flex-wrap items-center gap-2">
              <button
                type="button"
                @click="toggleListening"
                :disabled="!speechSupported"
                class="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-semibold transition disabled:cursor-not-allowed disabled:opacity-50"
                :class="isListening ? 'bg-rose-600 text-white hover:bg-rose-700' : 'bg-indigo-600 text-white hover:bg-indigo-700'"
              >
                <StopCircleIcon v-if="isListening" class="h-4 w-4 animate-pulse" />
                <MicrophoneIcon v-else class="h-4 w-4" />
                {{ isListening ? 'Dinlemeyi Durdur' : 'Sesle Cevapla' }}
              </button>
              <button
                v-if="responseText || interimTranscript"
                type="button"
                @click="clearResponse"
                class="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"
              >
                <ArrowPathIcon class="h-4 w-4" />
                Temizle
              </button>
            </div>
          </div>
          <div class="relative">
            <textarea
              v-model="responseText"
              rows="5"
              placeholder="Cevabinizi yazin veya mikrofonla soyleyin..."
              class="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none resize-none"
            />
            <div
              v-if="isListening && interimTranscript"
              class="pointer-events-none absolute bottom-3 left-3 right-3 rounded-lg border border-indigo-100 bg-white/95 px-3 py-2 text-xs text-indigo-700 shadow-sm"
            >
              <span class="font-semibold">Dinleniyor:</span> {{ interimTranscript }}
            </div>
          </div>
          <div class="mt-2 flex flex-col gap-1 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
            <span>{{ responseText.length }} / 2000 karakter</span>
            <span v-if="isListening" class="font-semibold text-rose-600">Mikrofon acik, Turkce dinleniyor.</span>
            <span v-else-if="speechSupported" class="text-slate-400">Sesle yanit tarayicida metne cevrilir; ses kaydi backend'e gitmez.</span>
            <span v-else class="font-semibold text-amber-600">Bu tarayici Speech Recognition desteklemiyor.</span>
          </div>
          <div v-if="speechError" class="mt-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
            {{ speechError }}
          </div>
        </div>

        <div v-if="errorText" class="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
          {{ errorText }}
        </div>

        <button
          @click="submit"
          :disabled="submitting || !receiverId || !currentQuestion"
          class="w-full py-3 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ submitting ? 'Gonderiliyor...' : 'Geri Bildirimi Gonder' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { ArrowPathIcon, MicrophoneIcon, StopCircleIcon } from '@heroicons/vue/24/outline'
import { feedbackApi, type EmployeeForFeedback, type WeeklyQuestionResponse, type WeeklyAssignmentStateResponse } from '@/services/api/feedback.api'

const props = defineProps<{
  open: boolean
  candidates: EmployeeForFeedback[]
  weeklyAssignment?: WeeklyAssignmentStateResponse | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submitted'): void
}>()

const receiverId = ref<number | null>(null)
const currentQuestion = ref<WeeklyQuestionResponse | null>(null)
const responseText = ref('')
const interimTranscript = ref('')
const isListening = ref(false)
const speechError = ref('')
const recognitionRef = ref<any | null>(null)
const loadingQuestion = ref(false)
const submitting = ref(false)
const errorText = ref('')
const speechSupported = computed(() => {
  if (typeof window === 'undefined') return false
  const win = window as any
  return Boolean(win.SpeechRecognition || win.webkitSpeechRecognition)
})
const scoreFields = [
  { key: 'score_communication', label: 'Iletisim' },
  { key: 'score_teamwork', label: 'Takim Calismasi' },
  { key: 'score_leadership', label: 'Liderlik' },
  { key: 'score_technical', label: 'Teknik Beceri' },
] as const
const scores = ref({
  score_communication: 3,
  score_teamwork: 3,
  score_leadership: 3,
  score_technical: 3,
})

const managerCandidates = computed(() =>
  props.candidates.filter((candidate) => candidate.user.role === 'department_manager')
)

const employeeCandidates = computed(() =>
  props.candidates.filter((candidate) => candidate.user.role === 'employee')
)

const isMandatoryLocked = computed(() =>
  props.weeklyAssignment?.assignment_required && !!props.weeklyAssignment?.mandatory_assignment
)

const mandatoryTargetId = computed(() => props.weeklyAssignment?.mandatory_assignment?.employee.id ?? null)

const candidateGroups = computed(() => {
  const groups: Array<{ key: string; label: string; items: EmployeeForFeedback[] }> = []
  const slot = props.weeklyAssignment?.current_slot
  const departmentName =
    props.weeklyAssignment?.mandatory_assignment?.employee.department.name
    || props.candidates[0]?.department?.name
    || 'Departman'

  if (managerCandidates.value.length) {
    groups.push({
      key: 'managers',
      label: slot === 'mandatory_random'
        ? `Atanan/Yonetici (${managerCandidates.value.length})`
        : `${departmentName} Yoneticileri (${managerCandidates.value.length})`,
      items: managerCandidates.value,
    })
  }

  if (employeeCandidates.value.length) {
    groups.push({
      key: 'employees',
      label: `${departmentName} Ekip Arkadaslari (${employeeCandidates.value.length})`,
      items: employeeCandidates.value,
    })
  }

  return groups
})

const slotHint = computed(() => {
  const slot = props.weeklyAssignment?.current_slot
  if (slot === 'department_internal') {
    return '2. slotta yalnizca kendi departmanindaki yonetici ve ekip arkadaslari listelenir.'
  }
  if (slot === 'cross_functional') {
    return '3. slotta da secim departman ici tutulur; ardısık hafta ve bu hafta tekrar kurallari listeyi daraltabilir.'
  }
  return ''
})

function getRoleLabel(role: string) {
  const labels: Record<string, string> = {
    admin: 'Admin',
    department_manager: 'Yonetici',
    employee: 'Calisan',
  }
  return labels[role] ?? role
}

async function loadQuestion() {
  if (!receiverId.value) {
    currentQuestion.value = null
    return
  }
  errorText.value = ''
  loadingQuestion.value = true
  try {
    currentQuestion.value = await feedbackApi.getCurrentQuestion(receiverId.value)
  } catch (e: any) {
    currentQuestion.value = null
    errorText.value = e?.response?.data?.detail ?? 'Haftalik soru alinamadi'
  } finally {
    loadingQuestion.value = false
  }
}

async function submit() {
  stopListening()
  if (!receiverId.value) {
    errorText.value = 'Lutfen bir kisi secin'
    return
  }
  const finalResponseText = [responseText.value, interimTranscript.value].filter(Boolean).join(' ').trim()
  if (!finalResponseText) {
    errorText.value = 'Lutfen haftalik soruya yanit yazin'
    return
  }
  errorText.value = ''
  submitting.value = true
  try {
    await feedbackApi.submitWeeklyFeedback({
      receiver_id: receiverId.value,
      response_text: finalResponseText,
      score_communication: scores.value.score_communication,
      score_teamwork: scores.value.score_teamwork,
      score_leadership: scores.value.score_leadership,
      score_technical: scores.value.score_technical,
    })
    receiverId.value = null
    currentQuestion.value = null
    responseText.value = ''
    interimTranscript.value = ''
    emit('submitted')
    emit('close')
  } catch (e: any) {
    errorText.value = e?.response?.data?.detail ?? 'Gonderim sirasinda hata olustu'
  } finally {
    submitting.value = false
  }
}

function getSpeechRecognition() {
  const win = window as any
  return win.SpeechRecognition || win.webkitSpeechRecognition
}

function startListening() {
  if (!speechSupported.value) {
    speechError.value = 'Tarayiciniz Speech Recognition desteklemiyor. Chrome veya Edge ile deneyebilirsiniz.'
    return
  }

  speechError.value = ''
  const SpeechRecognition = getSpeechRecognition()
  const recognition = new SpeechRecognition()
  recognitionRef.value = recognition

  recognition.continuous = true
  recognition.interimResults = true
  recognition.lang = 'tr-TR'

  recognition.onstart = () => {
    isListening.value = true
  }

  recognition.onresult = (event: any) => {
    let currentInterim = ''
    let finalText = ''

    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const transcript = event.results[i][0].transcript
      if (event.results[i].isFinal) {
        finalText += `${transcript} `
      } else {
        currentInterim += transcript
      }
    }

    if (finalText.trim()) {
      responseText.value = `${responseText.value}${responseText.value.trim() ? ' ' : ''}${finalText.trim()} `
    }
    interimTranscript.value = currentInterim.trim()
  }

  recognition.onerror = (event: any) => {
    const error = event?.error || 'bilinmeyen_hata'
    const messages: Record<string, string> = {
      'not-allowed': 'Mikrofon izni verilmedi. Tarayici adres cubugundan mikrofon iznini acabilirsiniz.',
      'no-speech': 'Ses algilanamadi. Biraz daha yakindan ve net konusmayi deneyin.',
      'audio-capture': 'Mikrofon bulunamadi veya baska bir uygulama tarafindan kullaniliyor.',
      network: 'Speech Recognition servisine ulasilamadi. Internet baglantisini kontrol edin.',
    }
    speechError.value = messages[error] ?? `Mikrofon hatasi: ${error}`
  }

  recognition.onend = () => {
    isListening.value = false
    interimTranscript.value = ''
  }

  recognition.start()
}

function stopListening() {
  if (recognitionRef.value) {
    recognitionRef.value.stop()
    recognitionRef.value = null
  }
  isListening.value = false
}

function toggleListening() {
  if (isListening.value) {
    stopListening()
  } else {
    startListening()
  }
}

function clearResponse() {
  responseText.value = ''
  interimTranscript.value = ''
  speechError.value = ''
}

watch(receiverId, loadQuestion)
watch(
  () => props.open,
  (isOpen) => {
    if (!isOpen) {
      stopListening()
      receiverId.value = null
      currentQuestion.value = null
      responseText.value = ''
      interimTranscript.value = ''
      speechError.value = ''
      scores.value = {
        score_communication: 3,
        score_teamwork: 3,
        score_leadership: 3,
        score_technical: 3,
      }
      errorText.value = ''
    } else if (isMandatoryLocked.value && mandatoryTargetId.value) {
      receiverId.value = mandatoryTargetId.value
    }
  }
)

watch(
  () => props.weeklyAssignment,
  (assignment) => {
    if (props.open && assignment?.assignment_required && assignment.mandatory_assignment) {
      receiverId.value = assignment.mandatory_assignment.employee.id
    }
  },
  { deep: true }
)

onBeforeUnmount(() => {
  stopListening()
})
</script>
