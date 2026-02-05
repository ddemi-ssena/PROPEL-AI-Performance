<template>
  <div class="w-full h-64">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>

<script setup lang="ts">
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Line } from 'vue-chartjs'
import { computed } from 'vue'

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

const props = defineProps<{
  labels: string[]
  data: number[]
}>()

const chartData = computed(() => ({
  labels: props.labels,
  datasets: [
    {
      label: 'Performance Score',
      backgroundColor: (context: any) => {
        const ctx = context.chart.ctx
        const gradient = ctx.createLinearGradient(0, 0, 0, 400)
        gradient.addColorStop(0, 'rgba(16, 185, 129, 0.2)')
        gradient.addColorStop(1, 'rgba(16, 185, 129, 0)')
        return gradient
      },
      borderColor: '#10b981',
      pointBackgroundColor: '#ffffff',
      pointBorderColor: '#10b981',
      pointBorderWidth: 2,
      pointRadius: 4,
      pointHoverRadius: 6,
      data: props.data,
      fill: true,
      tension: 0.4
    }
  ]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      backgroundColor: '#1e293b',
      padding: 12,
      titleFont: {
        size: 13
      },
      bodyFont: {
        size: 13
      },
      cornerRadius: 8,
      displayColors: false
    }
  },
  scales: {
    x: {
      grid: {
        display: false
      },
      ticks: {
        color: '#64748b'
      }
    },
    y: {
      min: 0,
      max: 100,
      grid: {
        color: '#f1f5f9'
      },
      ticks: {
        stepSize: 20,
        color: '#64748b'
      }
    }
  }
}
</script>
