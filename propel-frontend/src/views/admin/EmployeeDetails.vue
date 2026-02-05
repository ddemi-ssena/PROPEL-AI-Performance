<template>
  <div v-if="employee">
    <!-- Header with Breadcrumb-like nav -->
    <div class="mb-8">
      <button @click="router.back()" class="flex items-center text-slate-500 hover:text-slate-900 mb-4 transition-colors">
        <ArrowLeftIcon class="w-4 h-4 mr-1" />
        Personel Listesine Dön
      </button>
      
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
        <div class="flex items-center gap-6">
          <img :src="employee.avatar" class="w-24 h-24 rounded-full border-4 border-white shadow-md relative -my-2" />
          <div>
            <h1 class="text-3xl font-bold text-slate-900">{{ employee.name }}</h1>
            <div class="flex items-center gap-3 mt-1 text-slate-500">
              <span>{{ employee.role }}</span>
              <span class="w-1 h-1 bg-slate-300 rounded-full"></span>
              <span>{{ employee.department }}</span>
            </div>
          </div>
        </div>
        
        <div class="flex gap-3">
          <div class="text-right px-4 border-r border-slate-100">
            <p class="text-xs text-slate-500 uppercase font-semibold">Risk Seviyesi</p>
            <span class="inline-flex items-center mt-1 px-2.5 py-0.5 rounded-full text-sm font-medium" :class="getRiskBadgeClasses(employee.risk)">
               {{ getRiskLabel(employee.risk) }}
            </span>
          </div>
          <div class="text-right pl-2">
            <p class="text-xs text-slate-500 uppercase font-semibold">Başlangıç</p>
            <p class="text-slate-900 font-medium mt-1">{{ employee.joinDate }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div v-for="stat in stats" :key="stat.title" class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
        <p class="text-sm font-medium text-slate-500 mb-1">{{ stat.title }}</p>
        <div class="flex items-baseline gap-2">
          <span class="text-2xl font-bold text-slate-900">{{ stat.value }}</span>
          <span class="text-xs font-medium px-2 py-0.5 rounded-full" :class="stat.trend > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'">
            {{ stat.trend > 0 ? '+' : '' }}{{ stat.trend }}%
          </span>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Main Chart Area -->
      <div class="lg:col-span-2 space-y-8">
        <!-- Performance Chart -->
        <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-bold text-slate-900">Performans Trendi</h3>
            <select class="bg-slate-50 border-none rounded-lg text-sm text-slate-600 focus:ring-2 focus:ring-blue-500">
              <option>Son 6 Ay</option>
              <option>Son 1 Yıl</option>
            </select>
          </div>
          <div class="h-80">
            <TrendChart :labels="months" :data="performanceData" />
          </div>
        </div>

        <!-- AI Insights -->
        <div class="bg-gradient-to-br from-indigo-900 to-slate-900 rounded-xl p-6 text-white shadow-lg overflow-hidden relative">
          <div class="absolute top-0 right-0 p-32 bg-blue-500/10 rounded-full blur-3xl"></div>
          
          <div class="relative z-10">
            <div class="flex items-center gap-3 mb-6">
              <SparklesIcon class="w-6 h-6 text-yellow-400" />
              <h3 class="text-lg font-bold">AI Performans Analizi</h3>
            </div>

            <div class="space-y-4">
              <div v-for="(insight, idx) in insights" :key="idx" class="bg-white/10 backdrop-blur-sm p-4 rounded-lg border border-white/10">
                <p class="text-indigo-200 text-xs font-bold uppercase tracking-wider mb-1">{{ insight.category }}</p>
                <p class="text-sm leading-relaxed">{{ insight.text }}</p>
              </div>
            </div>

            <div class="mt-6 pt-6 border-t border-white/10 flex items-center justify-between">
               <p class="text-xs text-slate-400">Son güncelleme: 2 dakika önce</p>
               <button class="text-xs bg-white text-slate-900 px-3 py-1.5 rounded-lg font-medium hover:bg-blue-50 transition-colors">
                 Detaylı Rapor İndir
               </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Side Panel -->
      <div class="space-y-8">
         <!-- Motivation Score -->
         <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 class="text-lg font-bold text-slate-900 mb-6">Motivasyon Skoru</h3>
            <div class="relative pt-2 pb-6 flex justify-center">
                 <div class="w-48 h-24 overflow-hidden relative">
                     <div class="absolute top-0 left-0 w-full h-full bg-slate-100 rounded-t-full"></div>
                     <div class="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-red-400 via-yellow-400 to-green-500 rounded-t-full origin-bottom transition-transform duration-1000" style="transform: rotate(-30deg)"></div>
                     <div class="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-40 h-40 bg-white rounded-full flex items-start justify-center pt-8">
                         <span class="text-4xl font-bold text-slate-900">{{ motivationScore }}</span>
                     </div>
                 </div>
            </div>
             <p class="text-center text-sm text-slate-500">Çok iyi durumda. Ekip içi iletişimi yüksek.</p>
         </div>

         <!-- Skills -->
         <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 class="text-lg font-bold text-slate-900 mb-4">Yetkinlikler</h3>
            <div class="space-y-4">
                <div v-for="skill in skills" :key="skill.name">
                    <div class="flex justify-between text-xs mb-1">
                        <span class="font-medium text-slate-700">{{ skill.name }}</span>
                        <span class="text-slate-500">{{ skill.level }}%</span>
                    </div>
                    <div class="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                        <div class="h-full bg-blue-600 rounded-full" :style="{ width: `${skill.level}%` }"></div>
                    </div>
                </div>
            </div>
         </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeftIcon, SparklesIcon } from '@heroicons/vue/24/outline'
import TrendChart from '@/components/charts/TrendChart.vue'

const router = useRouter()
const route = useRoute()

// Mock Data - In real app, fetch based on route.params.id
const employee = ref({
  id: 2,
  name: 'Canan Dağdelen',
  email: 'developer1@propel.com',
  role: 'Senior Developer',
  department: 'Yazılım Geliştirme',
  risk: 'Medium',
  joinDate: '15 Ocak 2023',
  avatar: 'https://ui-avatars.com/api/?name=Canan+Dagdelen&background=e11d48&color=fff'
})

const stats = ref([
  { title: 'Genel Skor', value: '88', trend: 2.4 },
  { title: 'Tamamlanan Görevler', value: '142', trend: 12 },
  { title: 'İşbirliği', value: '9.2', trend: 5.1 },
  { title: 'Motivasyon', value: '8.5', trend: -1.2 },
])

const months = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz']
const performanceData = [75, 78, 82, 80, 85, 88]

const insights = ref([
  { category: 'Güçlü Yön', text: 'Kod incelemelerinde detaycı yaklaşımı ile potansiyel hataları erkenden yakalıyor.' },
  { category: 'Gelişim Alanı', text: 'Toplantı katılımlarında daha aktif rol alması teşvik edilebilir.' },
  { category: 'Tahmin', text: 'Mevcut performans artışı ile sonraki çeyrekte "Lead Developer" pozisyonuna aday olabilir.' },
])

const motivationScore = ref(85)

const skills = ref([
  { name: 'Vue.js / Frontend', level: 95 },
  { name: 'TypeScript', level: 90 },
  { name: 'UI/UX Design', level: 80 },
  { name: 'Backend Integration', level: 75 },
])

function getRiskBadgeClasses(risk: string) {
  switch (risk) {
    case 'High': return 'bg-red-50 text-red-700 border border-red-200'
    case 'Medium': return 'bg-amber-50 text-amber-700 border border-amber-200'
    case 'Low': return 'bg-emerald-50 text-emerald-700 border border-emerald-200'
    default: return 'bg-slate-50 text-slate-700 border border-slate-200'
  }
}

function getRiskLabel(risk: string) {
    switch (risk) {
        case 'High': return 'Yüksek'
        case 'Medium': return 'Orta'
        case 'Low': return 'Düşük'
        default: return risk
    }
}
</script>
