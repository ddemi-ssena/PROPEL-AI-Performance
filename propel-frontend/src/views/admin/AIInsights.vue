<template>
  <div>
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold text-slate-900 tracking-tight">Yapay Zeka İçgörüleri</h1>
        <p class="text-slate-500 mt-1">Ekip performansı ve riskleri üzerine tahminsel analizler.</p>
      </div>
      <button class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2.5 rounded-lg transition-colors flex items-center gap-2 shadow-sm shadow-blue-600/20">
        <ArrowPathIcon class="w-5 h-5" />
        Yeniden Oluştur
      </button>
    </div>

    <!-- KPI Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div v-for="kpi in kpis" :key="kpi.title" class="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
        <div class="flex items-start justify-between mb-2">
          <p class="text-sm font-medium text-slate-500">{{ kpi.title }}</p>
          <component :is="kpi.icon" class="w-5 h-5" :class="kpi.iconColor" />
        </div>
        <div class="flex items-baseline gap-2 mb-2">
          <span class="text-3xl font-bold text-slate-900">{{ kpi.value }}</span>
          <span class="text-sm font-medium" :class="kpi.trendColor">{{ kpi.trend }}</span>
        </div>
        <p class="text-xs text-slate-400">{{ kpi.comparison }}</p>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Risk Distribution Chart -->
      <div class="lg:col-span-2 bg-white rounded-xl p-6 shadow-sm border border-slate-200">
        <h3 class="text-lg font-bold text-slate-900 mb-6">Risk Dağılımı</h3>
        <div class="h-80 flex items-center justify-center relative">
             <div class="absolute inset-0 flex items-center justify-center flex-col pointer-events-none">
                 <span class="text-4xl font-bold text-slate-900">Toplam</span>
                 <span class="text-sm text-slate-500">Çalışan</span>
             </div>
             <DoughnutChart :labels="riskLabels" :data="riskData" :colors="riskColors" />
        </div>
      </div>

      <!-- AI Recommendations -->
      <div class="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
        <h3 class="text-lg font-bold text-slate-900 mb-6">AI Tavsiyeleri</h3>
        <div class="space-y-6">
          <div v-for="rec in recommendations" :key="rec.title" class="flex gap-4">
             <div class="mt-1 flex-shrink-0">
                 <component :is="rec.icon" class="w-6 h-6 text-blue-600" />
             </div>
             <div>
                 <h4 class="text-sm font-bold text-slate-900 mb-1">{{ rec.title }}</h4>
                 <p class="text-xs text-slate-600 leading-relaxed">{{ rec.description }}</p>
             </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { 
  ArrowPathIcon, 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon,
  ExclamationCircleIcon,
  LightBulbIcon,
  MegaphoneIcon,
  AcademicCapIcon
} from '@heroicons/vue/24/outline'
import DoughnutChart from '@/components/charts/DoughnutChart.vue'

const kpis = ref([
  {
    title: 'Tahmini Bağlılık',
    value: '82%',
    trend: '+3.5%',
    trendColor: 'text-emerald-600',
    comparison: 'geçen çeyreğe göre',
    icon: ArrowTrendingUpIcon,
    iconColor: 'text-emerald-500'
  },
  {
    title: 'İşten Ayrılma Riski',
    value: '14%',
    trend: '+1.2%',
    trendColor: 'text-amber-500',
    comparison: 'geçen çeyreğe göre',
    icon: ArrowTrendingDownIcon,
    iconColor: 'text-amber-500'
  },
  {
    title: 'Üretkenlik Endeksi',
    value: '96',
    trend: '+5 puan',
    trendColor: 'text-emerald-600',
    comparison: 'geçen çeyreğe göre',
    icon: ArrowTrendingUpIcon,
    iconColor: 'text-emerald-500'
  },
  {
    title: 'Yüksek Riskli Çalışanlar',
    value: '8',
    trend: '2 yeni',
    trendColor: 'text-red-600',
    comparison: 'bu hafta',
    icon: ExclamationCircleIcon,
    iconColor: 'text-red-500'
  }
])

const riskLabels = ['Düşük Risk', 'Orta Risk', 'Yüksek Risk']
const riskData = [65, 25, 10]
const riskColors = ['#22c55e', '#f59e0b', '#ef4444']

const recommendations = ref([
  {
    title: 'Tükenmişlik Riski Yönetimi',
    description: 'Tasarım ekibinde erken tükenmişlik belirtileri gözleniyor. İş yükü yönetimi üzerine bir atölye planlanabilir.',
    icon: LightBulbIcon
  },
  {
    title: 'Başarıyı Ödüllendirin',
    description: 'Yazılım ekibinde bağlılık rekor seviyede. Topluluk önünde takdir moral motivasyonu daha da artırabilir.',
    icon: MegaphoneIcon
  },
  {
    title: 'Hedefli Eğitimler',
    description: 'Bazı junior pazarlama üyeleri ileri düzey analitik eğitimi alarak verimlerini artırabilir.',
    icon: AcademicCapIcon
  }
])
</script>
