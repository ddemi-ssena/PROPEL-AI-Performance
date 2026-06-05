<template>
  <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">{{ eyebrow }}</p>
        <h3 class="mt-1 text-lg font-bold text-slate-900">{{ title }}</h3>
        <p v-if="description" class="mt-2 max-w-4xl text-sm leading-6 text-slate-600">{{ description }}</p>
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

    <div v-if="showGuide" class="mt-5 grid grid-cols-1 gap-3 border-t border-slate-100 pt-4 md:grid-cols-3">
      <div class="rounded-xl border border-blue-100 bg-blue-50/60 p-3">
        <p class="text-xs font-bold uppercase tracking-[0.12em] text-blue-700">Performans</p>
        <p class="mt-1 text-xs leading-5 text-slate-700">KPI/ML modelinden gelen takım performans skorudur. Düşük değer, modelin o takımda daha yüksek performans riski gördüğünü anlatır.</p>
      </div>
      <div class="rounded-xl border border-emerald-100 bg-emerald-50/60 p-3">
        <p class="text-xs font-bold uppercase tracking-[0.12em] text-emerald-700">Kapasite</p>
        <p class="mt-1 text-xs leading-5 text-slate-700">Haftalık nabız yanıtlarından okunan motivasyon/bağlılık sinyalidir. Takımın sürdürülebilir çalışma kapasitesini yorumlamak için kullanılır.</p>
      </div>
      <div class="rounded-xl border border-rose-100 bg-rose-50/60 p-3">
        <p class="text-xs font-bold uppercase tracking-[0.12em] text-rose-700">Risk Skoru</p>
        <p class="mt-1 text-xs leading-5 text-slate-700">KPI/ML, nabız ve 360 risklerinin birleşik özetidir. Yüksek değer daha fazla yönetici müdahalesi ihtiyacı demektir.</p>
      </div>
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
  description?: string
  data: DepartmentTrendPoint[]
  target?: number
  xLabelPrefix?: string
  showGuide?: boolean
}>(), {
  eyebrow: 'Trend Chart',
  target: 85,
  xLabelPrefix: 'Ay',
  showGuide: false,
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
          return items.length ? `${props.xLabelPrefix}: ${items[0].label}` : ''
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
        text: 'Skor (0-100)',
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
