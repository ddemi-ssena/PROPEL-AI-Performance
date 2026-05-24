<template>
  <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <div class="mb-6">
      <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Yazilim Departmani Analiz Paneli</p>
      <h1 class="mt-2 text-3xl font-bold tracking-tight text-slate-900">{{ departmentName }}</h1>
      <p class="mt-2 text-sm text-slate-600">
        {{ memberCount }} Calisan | {{ teamCount }} Takim | Saglik Skoru: {{ healthScore }}/100
      </p>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div class="rounded-xl border border-blue-200 bg-blue-50 p-4">
        <p class="text-sm text-slate-600">Genel Saglik Skoru</p>
        <p class="mt-2 text-3xl font-bold text-blue-600">{{ healthScore }}/100</p>
      </div>
      <div class="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
        <p class="text-sm text-slate-600">Ort. Performans</p>
        <p class="mt-2 text-3xl font-bold text-emerald-600">{{ performanceScore }}/100</p>
      </div>
      <div class="rounded-xl border border-amber-200 bg-amber-50 p-4">
        <p class="text-sm text-slate-600">Risk Duzeyi</p>
        <p class="mt-2 text-3xl font-bold text-amber-600">{{ riskLevel }}</p>
      </div>
      <div class="rounded-xl border border-violet-200 bg-violet-50 p-4">
        <p class="text-sm text-slate-600">Trend</p>
        <p class="mt-2 text-3xl font-bold text-violet-600">{{ trendLabel }}</p>
      </div>
    </div>

    <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
      <div class="flex flex-col gap-2 sm:flex-row">
        <select
          :value="period"
          class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
          @change="$emit('update:period', ($event.target as HTMLSelectElement).value)"
        >
          <option value="current_week">Bu Hafta</option>
          <option value="last_month">Bu Ay</option>
          <option value="last_quarter">Bu Ceyrek</option>
          <option value="year">Bu Yil</option>
        </select>

        <select
          :value="comparison"
          class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
          @change="$emit('update:comparison', ($event.target as HTMLSelectElement).value)"
        >
          <option value="previous_period">Onceki Donem</option>
          <option value="department_average">Departman Ort.</option>
          <option value="target">Hedef</option>
        </select>
      </div>

      <div class="flex flex-wrap gap-2">
        <button
          type="button"
          class="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-slate-700 shadow-sm transition hover:bg-slate-50"
          title="Yenile"
          @click="$emit('refresh')"
        >
          <ArrowPathIcon class="h-4 w-4" />
        </button>
        <button
          type="button"
          class="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
          @click="$emit('export')"
        >
          <ArrowDownTrayIcon class="h-4 w-4" />
          PDF
        </button>
        <button
          type="button"
          class="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
          @click="$emit('share')"
        >
          <ShareIcon class="h-4 w-4" />
          Email
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowDownTrayIcon, ArrowPathIcon, ShareIcon } from '@heroicons/vue/24/outline'

defineProps<{
  departmentName: string
  memberCount: number
  teamCount: number
  healthScore: number
  performanceScore: number
  riskLevel: string
  trendLabel: string
  period: string
  comparison: string
}>()

defineEmits<{
  'update:period': [value: string]
  'update:comparison': [value: string]
  refresh: []
  export: []
  share: []
}>()
</script>
