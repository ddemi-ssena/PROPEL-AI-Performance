<template>
  <div class="overflow-hidden rounded-2xl bg-gradient-to-r from-violet-700 to-blue-700 shadow-lg">
    <button
      type="button"
      class="flex w-full items-center justify-between gap-4 px-6 py-4 text-left transition hover:bg-black/10"
      @click="expanded = !expanded"
    >
      <div class="flex items-center gap-3">
        <SparklesIcon class="h-6 w-6 text-white" :class="{ 'animate-pulse': loading }" />
        <div>
          <h3 class="text-lg font-bold text-white">
            {{ loading ? 'Departman Analizi Yapiliyor...' : 'AI Departman Analizi & Onerileri' }}
          </h3>
          <p v-if="insights" class="mt-1 text-xs font-medium text-white/70">
            {{ sourceLabel }} · {{ generatedAtLabel }}
          </p>
        </div>
      </div>
      <ChevronDownIcon class="h-5 w-5 text-white transition" :class="{ 'rotate-180': expanded }" />
    </button>

    <div v-if="expanded" class="border-t border-white/20 bg-white/10 px-6 py-5 text-white backdrop-blur-sm">
      <div v-if="loading" class="space-y-3">
        <div class="h-4 rounded bg-white/20"></div>
        <div class="h-4 w-11/12 rounded bg-white/20"></div>
        <div class="h-4 w-9/12 rounded bg-white/20"></div>
      </div>

      <div v-else-if="errorMessage" class="rounded-xl border border-white/20 bg-white/10 p-4 text-sm leading-6">
        {{ errorMessage }}
      </div>

      <div v-else class="space-y-3">
        <p
          v-for="(line, index) in insightLines"
          :key="`${index}-${line}`"
          class="text-sm leading-7 text-white/95"
          :class="isHeading(line) ? 'pt-2 text-base font-bold text-white' : ''"
        >
          {{ line }}
        </p>
      </div>

      <div class="mt-6 flex flex-wrap gap-3">
        <button
          type="button"
          class="rounded-xl bg-white/20 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/30 disabled:cursor-wait disabled:opacity-60"
          :disabled="loading"
          @click="fetchInsights"
        >
          Yenile
        </button>
        <button
          type="button"
          class="rounded-xl bg-white/20 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/30"
        >
          PDF Indir
        </button>
        <button
          type="button"
          class="rounded-xl bg-white/20 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/30"
        >
          Ekibe Gonder
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ChevronDownIcon, SparklesIcon } from '@heroicons/vue/24/outline'
import { analyticsApi, type SoftwareDepartmentInsightsResponse } from '@/services/api/analytics.api'

const props = withDefaults(defineProps<{
  uploadId?: number | null
  period?: string
  useLlm?: boolean
}>(), {
  period: 'week',
  useLlm: true,
})

const insights = ref<SoftwareDepartmentInsightsResponse | null>(null)
const loading = ref(true)
const expanded = ref(true)
const errorMessage = ref('')

const insightLines = computed(() =>
  (insights.value?.insights || '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
)

const sourceLabel = computed(() => {
  if (!insights.value) return ''
  const provider = insights.value.source || 'deterministic'
  const model = insights.value.model ? ` / ${insights.value.model}` : ''
  return insights.value.fallback_used ? `${provider}${model} fallback` : `${provider}${model}`
})

const generatedAtLabel = computed(() => {
  if (!insights.value?.generated_at) return ''
  return new Date(insights.value.generated_at).toLocaleString('tr-TR')
})

function isHeading(line: string) {
  return /^\d+\.\s/.test(line)
}

async function fetchInsights() {
  loading.value = true
  errorMessage.value = ''
  try {
    insights.value = await analyticsApi.getSoftwareDepartmentInsights({
      upload_id: props.uploadId || undefined,
      period: props.period,
      use_llm: props.useLlm,
    })
  } catch (error) {
    console.error('AI departman analizi yuklenemedi:', error)
    errorMessage.value = 'AI departman analizi su anda yuklenemedi. Model ve dataset hazirligini kontrol edin.'
  } finally {
    loading.value = false
  }
}

watch(() => [props.uploadId, props.period, props.useLlm], () => {
  fetchInsights()
})

onMounted(() => {
  fetchInsights()
})
</script>
