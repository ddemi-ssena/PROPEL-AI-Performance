<template>
  <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">{{ eyebrow }}</p>
        <h3 class="mt-1 text-lg font-bold text-slate-900">{{ title }}</h3>
      </div>
      <div class="flex flex-wrap gap-2 text-xs font-semibold">
        <span class="rounded-full bg-blue-50 px-3 py-1 text-blue-700">Performans</span>
        <span class="rounded-full bg-emerald-50 px-3 py-1 text-emerald-700">Kapasite</span>
        <span class="rounded-full bg-rose-50 px-3 py-1 text-rose-700">Risk Skoru</span>
      </div>
    </div>

    <div class="mt-6 h-[400px]">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

export type DepartmentTrendPoint = {
  month: string
  performance: number
  capacity: number
  risk: number
}

const props = withDefaults(defineProps<{
  title: string
  eyebrow?: string
  data: DepartmentTrendPoint[]
  target?: number
}>(), {
  eyebrow: 'Trend Chart',
  target: 85,
})

const chartData = computed(() => {
  const labels = props.data.map((item) => item.month)
  const targetValues = props.data.map(() => props.target)

  return {
    labels,
    datasets: [
      {
        label: 'Hedef',
        data: targetValues,
        borderColor: '#f59e0b',
        borderDash: [6, 6],
        borderWidth: 2,
        pointRadius: 0,
        tension: 0,
        fill: false,
      },
      {
        label: 'Performans',
        data: props.data.map((item) => item.performance),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.12)',
        borderWidth: 3,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        tension: 0.42,
        fill: true,
      },
      {
        label: 'Kapasite',
        data: props.data.map((item) => item.capacity),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.08)',
        borderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: '#10b981',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        tension: 0.42,
        fill: false,
      },
      {
        label: 'Risk Skoru',
        data: props.data.map((item) => item.risk),
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.08)',
        borderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: '#ef4444',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        tension: 0.42,
        fill: false,
      },
    ],
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index' as const,
    intersect: false,
  },
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: {
        usePointStyle: true,
        boxWidth: 8,
        color: '#475569',
        padding: 20,
      },
    },
    tooltip: {
      backgroundColor: '#ffffff',
      titleColor: '#0f172a',
      bodyColor: '#334155',
      borderColor: '#cbd5e1',
      borderWidth: 1,
      padding: 12,
      cornerRadius: 8,
      callbacks: {
        label(context: any) {
          const value = typeof context.parsed.y === 'number' ? context.parsed.y.toFixed(1) : context.parsed.y
          return `${context.dataset.label}: ${value}`
        },
        title(items: any[]) {
          return items.length ? `Ay: ${items[0].label}` : ''
        },
      },
    },
  },
  scales: {
    y: {
      min: 0,
      max: 100,
      grid: {
        color: '#e5e7eb',
        borderDash: [3, 3],
      },
      ticks: {
        color: '#64748b',
        stepSize: 20,
      },
      title: {
        display: true,
        text: 'Score / Value',
        color: '#64748b',
      },
    },
    x: {
      grid: {
        display: false,
      },
      ticks: {
        color: '#64748b',
      },
    },
  },
}))
</script>
