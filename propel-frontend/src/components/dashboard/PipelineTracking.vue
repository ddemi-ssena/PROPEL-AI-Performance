<template>
  <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">{{ eyebrow }}</p>
        <h3 class="text-lg font-bold text-slate-900">{{ title }}</h3>
      </div>
      <span class="w-fit rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
        {{ stages.length }} asama
      </span>
    </div>

    <div class="mt-6 space-y-5">
      <div v-for="(stage, index) in stages" :key="stage.name">
        <div class="mb-2 flex items-center justify-between gap-4">
          <span class="truncate text-sm font-semibold text-slate-700">{{ stage.name }}</span>
          <div class="flex items-baseline gap-2">
            <span class="text-2xl font-bold text-slate-900">{{ stage.value }}</span>
            <span class="text-sm font-semibold text-slate-500">%{{ stage.percentage }}</span>
          </div>
        </div>

        <div class="h-8 overflow-hidden rounded-full bg-slate-100">
          <div
            class="flex h-full items-center justify-center rounded-full text-xs font-bold text-white transition-all"
            :style="{ width: `${stage.percentage}%`, backgroundColor: stage.color }"
          >
            <span v-if="stage.percentage > 20">%{{ stage.percentage }}</span>
          </div>
        </div>

        <div v-if="index < stages.length - 1" class="my-2 flex items-center justify-center gap-2">
          <ChevronDownIcon class="h-4 w-4 text-slate-400" />
          <span class="text-xs font-medium text-slate-500">Donusum: %{{ stage.conversionRate }}</span>
        </div>
      </div>
    </div>

    <div class="mt-6 border-t border-slate-100 pt-5">
      <div class="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
        <div
          v-for="stage in stages"
          :key="`legend-${stage.name}`"
          class="flex items-center gap-2"
        >
          <span class="h-3 w-3 rounded-full" :style="{ backgroundColor: stage.color }"></span>
          <span class="text-slate-600">{{ stage.name }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ChevronDownIcon } from '@heroicons/vue/24/outline'

export type PipelineStage = {
  name: string
  value: number | string
  percentage: number
  conversionRate: number
  color: string
}

withDefaults(defineProps<{
  title: string
  eyebrow?: string
  stages: PipelineStage[]
}>(), {
  eyebrow: 'Pipeline Tracking',
})
</script>
