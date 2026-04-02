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
          <label class="block text-sm font-medium text-slate-700 mb-2">Haftalik Ozel Yanit *</label>
          <textarea
            v-model="responseText"
            rows="4"
            placeholder="Bu haftanin sorusuna yanitinizi yazin..."
            class="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none resize-none"
          />
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
import { computed, ref, watch } from 'vue'
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
const loadingQuestion = ref(false)
const submitting = ref(false)
const errorText = ref('')
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
  if (!receiverId.value) {
    errorText.value = 'Lutfen bir kisi secin'
    return
  }
  if (!responseText.value.trim()) {
    errorText.value = 'Lutfen haftalik soruya yanit yazin'
    return
  }
  errorText.value = ''
  submitting.value = true
  try {
    await feedbackApi.submitWeeklyFeedback({
      receiver_id: receiverId.value,
      response_text: responseText.value.trim(),
      score_communication: scores.value.score_communication,
      score_teamwork: scores.value.score_teamwork,
      score_leadership: scores.value.score_leadership,
      score_technical: scores.value.score_technical,
    })
    receiverId.value = null
    currentQuestion.value = null
    responseText.value = ''
    emit('submitted')
    emit('close')
  } catch (e: any) {
    errorText.value = e?.response?.data?.detail ?? 'Gonderim sirasinda hata olustu'
  } finally {
    submitting.value = false
  }
}

watch(receiverId, loadQuestion)
watch(
  () => props.open,
  (isOpen) => {
    if (!isOpen) {
      receiverId.value = null
      currentQuestion.value = null
      responseText.value = ''
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
</script>
