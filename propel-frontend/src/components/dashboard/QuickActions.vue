<template>
  <div class="rounded-2xl border border-slate-900 bg-slate-900 p-6 shadow-sm">
    <div class="mb-5 flex items-center gap-3">
      <CheckBadgeIcon class="h-6 w-6 text-sky-300" />
      <h3 class="text-lg font-bold text-white">Hizli Aksiyonlar</h3>
    </div>

    <div class="space-y-2">
      <label
        v-for="(action, index) in actions"
        :key="`${action.title}-${index}`"
        class="grid cursor-pointer grid-cols-[auto_minmax(0,1fr)_auto] gap-3 rounded-xl border border-white/10 bg-white/5 p-3 transition hover:bg-white/10"
      >
        <input
          type="checkbox"
          :checked="Boolean(completed[index])"
          class="mt-1 h-5 w-5 rounded border-slate-500 bg-slate-800 text-sky-500 focus:ring-sky-500"
          @change="toggleAction(index)"
        />
        <span class="min-w-0">
          <span
            class="block text-sm font-semibold leading-5"
            :class="completed[index] ? 'text-slate-500 line-through' : 'text-slate-100'"
          >
            {{ action.title }}
          </span>
          <span
            v-if="action.description"
            class="mt-1 block text-xs leading-5"
            :class="completed[index] ? 'text-slate-600' : 'text-slate-300'"
          >
            {{ action.description }}
          </span>
          <span class="mt-2 flex flex-wrap gap-2 text-[11px] font-semibold text-slate-400">
            <span v-if="action.owner" class="rounded-full bg-white/5 px-2 py-1">Sahip: {{ action.owner }}</span>
            <span v-if="action.dueDate" class="rounded-full bg-white/5 px-2 py-1">Vade: {{ action.dueDate }}</span>
            <span v-if="action.source" class="rounded-full bg-white/5 px-2 py-1">Kaynak: {{ sourceLabel(action.source) }}</span>
          </span>
        </span>
        <span
          v-if="action.priority"
          class="h-fit rounded-full px-2 py-1 text-xs font-bold"
          :class="action.priority === 'HIGH' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'"
        >
          {{ action.priority }}
        </span>
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { CheckBadgeIcon } from '@heroicons/vue/24/outline'

export type QuickActionItem = {
  title: string
  priority?: 'HIGH' | 'MEDIUM'
  description?: string
  owner?: string
  dueDate?: string
  source?: string
}

defineProps<{
  actions: QuickActionItem[]
}>()

const completed = ref<Record<number, boolean>>({})

function toggleAction(index: number) {
  completed.value = {
    ...completed.value,
    [index]: !completed.value[index],
  }
}

function sourceLabel(source: string) {
  const labels: Record<string, string> = {
    risk_overlap: 'Hibrit risk',
    feedback_blind_spot: '360 eksigi',
    performance_vs_health: 'KPI + Nabiz',
    trust_vs_execution: 'KPI + 360',
    coverage_gap: 'Veri guveni',
    team_breakdown: 'Takim skoru',
    coverage: 'Kapsama',
  }
  return labels[source] || source
}
</script>
