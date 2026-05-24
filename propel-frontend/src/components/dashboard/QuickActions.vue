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
        class="flex cursor-pointer items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-3 transition hover:bg-white/10"
      >
        <input
          type="checkbox"
          :checked="Boolean(completed[index])"
          class="h-5 w-5 rounded border-slate-500 bg-slate-800 text-sky-500 focus:ring-sky-500"
          @change="toggleAction(index)"
        />
        <span
          class="text-sm"
          :class="completed[index] ? 'text-slate-500 line-through' : 'text-slate-100'"
        >
          {{ action.title }}
        </span>
        <span
          v-if="action.priority"
          class="ml-auto rounded-full px-2 py-1 text-xs font-bold"
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
</script>
