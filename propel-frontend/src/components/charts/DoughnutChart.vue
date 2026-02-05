<template>
  <div class="w-full h-64">
    <Doughnut :data="chartData" :options="chartOptions" />
  </div>
</template>

<script setup lang="ts">
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Doughnut } from 'vue-chartjs'
import { computed } from 'vue'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{
  labels: string[]
  data: number[]
  colors: string[]
}>()

const chartData = computed(() => ({
  labels: props.labels,
  datasets: [
    {
      backgroundColor: props.colors,
      data: props.data,
      borderWidth: 0,
      hoverOffset: 4
    }
  ]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '75%',
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: {
        usePointStyle: true,
        padding: 20,
        font: {
            size: 12
        },
        color: '#64748b'
      }
    },
    tooltip: {
       backgroundColor: '#1e293b',
       padding: 12,
       cornerRadius: 8,
       displayColors: true 
    }
  }
}
</script>
