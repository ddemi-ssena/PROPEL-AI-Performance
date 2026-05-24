<template>
  <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">{{ eyebrow }}</p>
        <h3 class="text-lg font-bold text-slate-900">{{ title }}</h3>
      </div>
      <span class="w-fit rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
        Lead Conversion
      </span>
    </div>

    <div class="mt-6 space-y-4">
      <div v-for="(row, index) in processedRows" :key="row.stage">
        <div class="mb-2 grid grid-cols-[minmax(0,1fr)_auto] items-end gap-4">
          <div>
            <p class="truncate text-sm font-bold text-slate-800">{{ row.stage }}</p>
            <p class="mt-0.5 text-xs text-slate-500">
              %{{ row.conversion }} donusum
              <span v-if="index === 0">(Baslangic)</span>
            </p>
          </div>
          <p class="text-2xl font-bold text-slate-900">{{ row.value }}</p>
        </div>

        <div class="flex items-center gap-3">
          <div class="h-8 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div
              class="flex h-full items-center justify-end rounded-full bg-blue-500 px-3 text-xs font-bold text-white transition-all"
              :style="{ width: `${row.width}%` }"
            >
              %{{ row.relativeWidth }}
            </div>
          </div>
          <span class="w-14 text-right text-xs font-bold text-slate-500">%{{ row.relativeWidth }}</span>
        </div>

        <div v-if="index < processedRows.length - 1" class="my-2 flex items-center justify-center gap-2">
          <ChevronDownIcon class="h-4 w-4 text-slate-400" />
          <span class="text-xs font-medium text-slate-500">Donusum: %{{ row.nextConversion }}</span>
        </div>
      </div>
    </div>

    <div class="mt-6 overflow-x-auto rounded-xl border border-slate-200">
      <table class="w-full min-w-[520px] text-sm">
        <thead class="bg-slate-50 text-xs uppercase tracking-[0.12em] text-slate-500">
          <tr>
            <th class="px-4 py-3 text-left font-semibold">Stage</th>
            <th class="px-4 py-3 text-right font-semibold">Value</th>
            <th class="px-4 py-3 text-right font-semibold">Conv. Rate</th>
            <th class="px-4 py-3 text-right font-semibold">Drop-off</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in processedRows"
            :key="`table-${row.stage}`"
            class="border-t border-slate-100 transition hover:bg-slate-50"
          >
            <td class="px-4 py-3 font-semibold text-slate-800">{{ row.stage }}</td>
            <td class="px-4 py-3 text-right text-slate-700">{{ row.value }}</td>
            <td class="px-4 py-3 text-right">
              <span class="font-bold text-emerald-600">%{{ row.conversion }}</span>
            </td>
            <td class="px-4 py-3 text-right">
              <span class="font-bold text-rose-600">%{{ row.dropoff }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ChevronDownIcon } from '@heroicons/vue/24/outline'

export type FunnelRow = {
  stage: string
  value: number | string
  conversion: number
  dropoff: number
}

const props = withDefaults(defineProps<{
  title: string
  eyebrow?: string
  rows: FunnelRow[]
}>(), {
  eyebrow: 'Funnel Analizi',
})

const processedRows = computed(() => {
  const numericRows = props.rows.map((row) => ({
    ...row,
    numericValue: typeof row.value === 'number' ? row.value : Number(row.value) || 0,
  }))
  const maxValue = Math.max(...numericRows.map((row) => row.numericValue), 1)

  return numericRows.map((row, index) => {
    const next = numericRows[index + 1]
    const relativeWidth = Math.round((row.numericValue / maxValue) * 100)
    const nextConversion = next
      ? Math.round((next.numericValue / Math.max(row.numericValue, 1)) * 100)
      : row.conversion

    return {
      ...row,
      relativeWidth,
      width: Math.max(18, relativeWidth),
      nextConversion,
    }
  })
})
</script>
