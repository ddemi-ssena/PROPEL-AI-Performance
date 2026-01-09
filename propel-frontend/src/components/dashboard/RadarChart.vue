<template>
  <div class="relative w-full h-full">
    <Radar :data="chartData" :options="chartOptions" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
} from 'chart.js'
import { Radar } from 'vue-chartjs'

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
)

const props = defineProps<{
  labels: string[]
  datasets: {
    label: string
    data: number[]
    borderColor: string
    backgroundColor: string
  }[]
}>()

const chartData = computed(() => ({
  labels: props.labels,
  datasets: props.datasets.map(ds => ({
    ...ds,
    borderWidth: 2,
    pointBackgroundColor: ds.borderColor,
    pointBorderColor: '#fff',
    pointHoverBackgroundColor: '#fff',
    pointHoverBorderColor: ds.borderColor
  }))
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    r: {
      angleLines: {
        display: true,
        color: '#f3f4f6'
      },
      grid: {
        color: '#f3f4f6'
      },
      pointLabels: {
        font: {
            size: 11,
            family: "'Inter', sans-serif"
        },
        color: '#6b7280'
      },
      suggestedMin: 0,
      suggestedMax: 100,
      ticks: {
          stepSize: 20,
          backdropColor: 'transparent',
          color: '#9ca3af'
      }
    }
  },
  plugins: {
    legend: {
      position: 'top' as const,
      align: 'end' as const,
      labels: {
        usePointStyle: true,
        boxWidth: 8
      }
    }
  }
}
</script>
