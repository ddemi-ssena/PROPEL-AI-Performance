<template>
  <div class="w-full h-full">
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
  label?: string
  color?: string
}>()

const chartData = computed(() => ({
  labels: props.labels,
  datasets: [
    {
      label: props.label || 'Veri',
      backgroundColor: (context: any) => {
        const ctx = context.chart.ctx;
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.2)'); // Blue with opacity
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');
        return gradient;
      },
      borderColor: props.color || '#3B82F6', // Blue-500
      data: props.data,
      tension: 0.4,
      fill: true,
      pointRadius: 4,
      pointBackgroundColor: '#ffffff',
      pointBorderColor: props.color || '#3B82F6',
      pointBorderWidth: 2,
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
      intersect: false,
      backgroundColor: '#1E293B',
      padding: 12,
      cornerRadius: 8,
      displayColors: false,
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: {
        color: '#F3F4F6',
        drawBorder: false,
      },
      ticks: {
        font: {
          family: "'Inter', sans-serif",
          size: 11
        },
        color: '#9CA3AF'
      }
    },
    x: {
      grid: {
        display: false,
        drawBorder: false,
      },
      ticks: {
        font: {
          family: "'Inter', sans-serif",
          size: 11
        },
        color: '#9CA3AF'
      }
    }
  }
}
</script>
