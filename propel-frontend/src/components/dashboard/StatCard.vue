<template>
  <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center justify-between">
    <div>
      <p class="text-sm font-medium text-gray-500">{{ title }}</p>
      <p class="text-2xl font-bold text-gray-900 mt-1">{{ value }}</p>
      <div v-if="change" :class="[isPositive ? 'text-green-600' : 'text-red-600', 'text-xs font-medium mt-1 flex items-center gap-1']">
        <span v-if="isPositive">↑</span>
        <span v-else>↓</span>
        <span>{{ change }}</span>
        <span class="text-gray-400">geçen aya göre</span>
      </div>
    </div>
    <div :class="[colorBg, 'p-3 rounded-lg bg-opacity-10']">
      <component :is="icon" class="w-6 h-6" :class="colorText" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  title: string
  value: string | number
  change?: string
  changeType?: 'increase' | 'decrease' | 'neutral'
  icon: any
  color?: 'blue' | 'green' | 'red' | 'purple' | 'orange'
}>()

const isPositive = computed(() => props.changeType === 'increase')

const colorBg = computed(() => {
  const colors = {
    blue: 'bg-blue-50',
    green: 'bg-green-50',
    red: 'bg-red-50',
    purple: 'bg-purple-50',
    orange: 'bg-orange-50'
  }
  return colors[props.color || 'blue']
})

const colorText = computed(() => {
  const colors = {
    blue: 'text-blue-600',
    green: 'text-green-600',
    red: 'text-red-600',
    purple: 'text-purple-600',
    orange: 'text-orange-600'
  }
  return colors[props.color || 'blue']
})
</script>
