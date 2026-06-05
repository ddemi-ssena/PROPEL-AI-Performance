<template>
  <div
    class="rounded-lg border-2 p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
    :class="card.statusSurfaceClass"
  >
    <div class="mb-4 flex items-center justify-between gap-3">
      <div class="min-w-0">
        <h3 class="truncate text-sm font-semibold text-slate-700">{{ card.title }}</h3>
        <p class="mt-1 text-xs text-slate-500">{{ card.subtitle }}</p>
      </div>
      <span class="rounded-xl p-2.5" :class="card.iconClass">
        <component :is="card.icon" class="h-6 w-6" />
      </span>
    </div>

    <div class="mb-4">
      <div class="text-4xl font-bold tracking-tight text-slate-900">
        {{ card.value }}
      </div>
      <div class="mt-1 text-sm font-medium text-slate-500">
        {{ card.value }} / {{ card.max }}
      </div>
    </div>

    <div class="mb-3 flex items-center gap-2">
      <span class="inline-flex h-8 w-8 items-center justify-center rounded-full" :class="card.trendClass">
        {{ card.trendIcon }}
      </span>
      <span class="text-sm font-semibold" :class="card.trendTextClass">
        {{ card.trendLabel }}
      </span>
    </div>

    <div class="mb-4">
      <span class="inline-flex rounded-full px-2.5 py-1 text-xs font-bold" :class="card.statusBadgeClass">
        {{ card.statusLabel }}
      </span>
    </div>

    <div class="grid grid-cols-2 gap-2 text-xs">
      <div class="rounded-lg bg-white/70 px-3 py-2">
        <p class="text-slate-400">Hedef</p>
        <p class="mt-1 font-bold text-slate-700">{{ card.target }}</p>
      </div>
      <div class="rounded-lg bg-white/70 px-3 py-2">
        <p class="text-slate-400">Kaynak</p>
        <p class="mt-1 font-bold text-slate-700">{{ card.benchmark }}</p>
      </div>
    </div>

    <p v-if="card.sourceNote" class="mt-3 rounded-lg bg-white/60 px-3 py-2 text-xs leading-5 text-slate-600">
      {{ card.sourceNote }}
    </p>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  card: {
    title: string
    subtitle: string
    value: number | string
    max: number | string
    target: string
    benchmark: string
    icon: Component
    iconClass: string
    trendIcon: string
    trendLabel: string
    trendClass: string
    trendTextClass: string
    statusLabel: string
    statusSurfaceClass: string
    statusBadgeClass: string
    sourceNote?: string
  }
}>()
</script>
