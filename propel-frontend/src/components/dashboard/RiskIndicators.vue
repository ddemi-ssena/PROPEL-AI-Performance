<template>
  <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <div class="mb-5 flex items-center gap-3">
      <ExclamationTriangleIcon class="h-6 w-6 text-amber-500" />
      <h3 class="text-lg font-bold text-slate-900">Risk Gostergeleri</h3>
    </div>

    <div class="space-y-4">
      <section>
        <div class="mb-2 flex items-center gap-2 font-semibold text-rose-700">
          <ExclamationCircleIcon class="h-4 w-4" />
          <h4>Kritik Riskler</h4>
        </div>
        <ul class="space-y-2">
          <li
            v-for="risk in risks.critical"
            :key="`critical-${risk}`"
            class="flex items-start gap-2 text-sm text-slate-700"
          >
            <span class="mt-2 h-2 w-2 rounded-full bg-rose-500"></span>
            <span>{{ risk }}</span>
          </li>
        </ul>
      </section>

      <section class="border-t border-slate-100 pt-4">
        <div class="mb-2 flex items-center gap-2 font-semibold text-amber-700">
          <ExclamationTriangleIcon class="h-4 w-4" />
          <h4>Uyarilar</h4>
        </div>
        <ul class="space-y-2">
          <li
            v-for="warning in risks.warnings"
            :key="`warning-${warning}`"
            class="flex items-start gap-2 text-sm text-slate-700"
          >
            <span class="mt-2 h-2 w-2 rounded-full bg-amber-500"></span>
            <span>{{ warning }}</span>
          </li>
        </ul>
      </section>

      <section class="border-t border-slate-100 pt-4">
        <div class="mb-2 flex items-center gap-2 font-semibold text-emerald-700">
          <CheckCircleIcon class="h-4 w-4" />
          <h4>Olumlu Isaretler</h4>
        </div>
        <ul class="space-y-2">
          <li
            v-for="positive in risks.positive"
            :key="`positive-${positive}`"
            class="flex items-start gap-2 text-sm text-slate-700"
          >
            <span class="mt-2 h-2 w-2 rounded-full bg-emerald-500"></span>
            <span>{{ positive }}</span>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/vue/24/outline'

export type RiskIndicatorGroups = {
  critical: string[]
  warnings: string[]
  positive: string[]
}

defineProps<{
  risks: RiskIndicatorGroups
}>()
</script>
