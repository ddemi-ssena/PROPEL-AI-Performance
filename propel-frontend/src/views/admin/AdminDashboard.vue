<template>
  <div class="space-y-8 pb-10">
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <StatCard
        title="Toplam Personel"
        value="48"
        change="+12%"
        changeType="increase"
        :icon="UsersIcon"
        color="indigo"
      />
      <StatCard
        title="Departmanlar"
        value="6"
        change="0%"
        changeType="neutral"
        :icon="BuildingOfficeIcon"
        color="slate"
      />
      <StatCard
        title="Ortalama Skor"
        value="8.4"
        change="+2.1%"
        changeType="increase"
        :icon="ChartBarIcon"
        color="emerald"
      />
      <StatCard
        title="Riskli Personel"
        value="3"
        change="-1"
        changeType="decrease"
        :icon="ExclamationTriangleIcon"
        color="rose"
      />
    </div>

    <!-- Departments Table Section -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow">
      <div class="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
        <div>
          <h3 class="text-lg font-bold text-slate-800">Departman Performansları</h3>
          <p class="text-xs text-slate-400 mt-1">Tüm departmanların genel durum özeti</p>
        </div>
        <button class="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 shadow-md shadow-indigo-200 transition-all">
          + Departman Ekle
        </button>
      </div>
      
      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm text-slate-600">
          <thead class="bg-slate-50/80 text-slate-900 font-semibold border-b border-gray-100">
            <tr>
              <th class="px-6 py-4">Departman</th>
              <th class="px-6 py-4">Yönetici</th>
              <th class="px-6 py-4">Personel</th>
              <th class="px-6 py-4">Ort. Skor</th>
              <th class="px-6 py-4 text-right">İşlem</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="dept in departments" :key="dept.id" class="hover:bg-slate-50/50 transition-colors group">
              <td class="px-6 py-4 font-medium text-slate-900">{{ dept.name }}</td>
              <td class="px-6 py-4 flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-xs font-bold text-slate-600 border border-white shadow-sm">
                    {{ dept.managerInitials }}
                </div>
                <span class="text-slate-700">{{ dept.manager }}</span>
              </td>
              <td class="px-6 py-4">{{ dept.employees }}</td>
              <td class="px-6 py-4">
                <span :class="getScoreBadgeClass(dept.score)" class="px-2.5 py-1 rounded-md text-xs font-bold border">
                  {{ dept.score }}
                </span>
              </td>
              <td class="px-6 py-4 text-right">
                <button class="text-indigo-600 hover:text-indigo-800 font-medium text-xs hover:underline">Detaylar</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Creative Features: Flight Risk & ONA -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Flight Risk Radar -->
        <div class="bg-rose-50/50 rounded-xl border border-rose-100 p-6 relative overflow-hidden group hover:border-rose-200 transition-colors">
            <div class="flex items-center gap-3 mb-6 relative z-10">
                <div class="p-2.5 bg-rose-100 rounded-lg text-rose-600 border border-rose-200">
                    <ExclamationTriangleIcon class="w-6 h-6" />
                </div>
                <div>
                   <h3 class="font-bold text-rose-950">Uçuş Riski Radarı</h3> 
                   <p class="text-xs text-rose-700/80">Ayrılma ihtimali yüksek kilit personeller</p>
                </div>
            </div>

            <div class="space-y-3 relative z-10">
                <div class="bg-white p-4 rounded-xl shadow-sm border border-rose-100 flex items-center justify-between hover:scale-[1.02] transition-transform duration-200 cursor-pointer">
                    <div class="flex items-center gap-3">
                         <div class="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center font-bold text-slate-600 border border-slate-200">
                            ED
                         </div>
                         <div>
                             <h4 class="font-bold text-slate-800 text-sm">Elif Demir</h4>
                             <p class="text-[10px] text-slate-400 font-medium uppercase tracking-wide">Senior DevOps</p>
                         </div>
                    </div>
                    <div class="text-right">
                        <span class="inline-flex items-center px-2 py-1 rounded-md text-xs font-bold bg-rose-100 text-rose-700 border border-rose-200">
                            %85 Risk
                        </span>
                        <p class="text-[10px] text-rose-600 mt-1 font-medium">Motivasyon Düşüşü</p>
                    </div>
                </div>

                <div class="bg-white p-4 rounded-xl shadow-sm border border-rose-100 flex items-center justify-between hover:scale-[1.02] transition-transform duration-200 cursor-pointer">
                    <div class="flex items-center gap-3">
                         <div class="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center font-bold text-slate-600 border border-slate-200">
                            CK
                         </div>
                         <div>
                             <h4 class="font-bold text-slate-800 text-sm">Can Kaya</h4>
                             <p class="text-[10px] text-slate-400 font-medium uppercase tracking-wide">Sales Lead</p>
                         </div>
                    </div>
                    <div class="text-right">
                        <span class="inline-flex items-center px-2 py-1 rounded-md text-xs font-bold bg-amber-100 text-amber-700 border border-amber-200">
                            %65 Risk
                        </span>
                        <p class="text-[10px] text-amber-600 mt-1 font-medium">Aşırı İş Yükü</p>
                    </div>
                </div>
            </div>
            
            <button class="w-full mt-4 py-2.5 bg-white border border-rose-200 text-rose-700 text-xs font-bold rounded-lg hover:bg-rose-50 transition shadow-sm z-10 relative">
                Tüm Risk Raporunu İncele
            </button>
            
            <!-- Decor -->
            <div class="absolute -bottom-12 -right-12 w-48 h-48 bg-rose-100/50 rounded-full blur-3xl z-0"></div>
        </div>

        <!-- Organizational Network Analysis (ONA) -->
        <div class="bg-white rounded-xl border border-gray-100 p-6 flex flex-col relative overflow-hidden shadow-sm hover:shadow-md transition-shadow">
             <div class="flex justify-between items-center mb-6 z-10">
                <div>
                   <h3 class="font-bold text-slate-800">Organizasyonel Ağ Analizi</h3> 
                   <p class="text-xs text-slate-400">İletişim köprüleri ve silolar</p>
                </div>
                <div class="px-2.5 py-1 bg-indigo-50 text-indigo-700 text-[10px] font-bold rounded border border-indigo-100">
                    BETA
                </div>
            </div>

            <!-- Visualization Mock -->
            <div class="flex-1 relative min-h-[250px] bg-slate-50/50 rounded-xl border border-slate-200 flex items-center justify-center overflow-hidden">
                <!-- Background Grid -->
                <div class="absolute inset-0" style="background-image: radial-gradient(#cbd5e1 1px, transparent 1px); background-size: 20px 20px; opacity: 0.3;"></div>

                <!-- Central Hub -->
                <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-20 bg-indigo-600 rounded-full border-4 border-white shadow-xl z-20 flex items-center justify-center flex-col text-center transition-transform hover:scale-110 cursor-pointer">
                    <span class="text-white font-bold text-xs leading-tight">Yazılım<br>Ekibi</span>
                    <span class="text-[8px] text-indigo-200 mt-0.5">Merkez</span>
                </div>
                
                <!-- Satellite Nodes -->
                <div class="absolute top-1/4 left-1/4 w-12 h-12 bg-slate-400 rounded-full border-2 border-white shadow-md opacity-50 z-10 animate-pulse"></div>
                <div class="absolute bottom-1/4 right-1/4 w-10 h-10 bg-slate-300 rounded-full border-2 border-white shadow-sm opacity-40 z-10"></div>
                <div class="absolute top-1/3 right-1/3 w-16 h-16 bg-emerald-500 rounded-full border-4 border-white shadow-lg z-10 flex items-center justify-center text-white text-[10px] font-bold cursor-pointer hover:scale-110 transition-transform">
                    Satış
                </div>

                <!-- Lines (SVG) -->
                <svg class="absolute inset-0 w-full h-full pointer-events-none z-0">
                    <line x1="50%" y1="50%" x2="25%" y2="25%" stroke="#94a3b8" stroke-width="2" stroke-dasharray="6" opacity="0.5" />
                    <line x1="50%" y1="50%" x2="66%" y2="33%" stroke="#6366f1" stroke-width="3" stroke-linecap="round" />
                </svg>

                <div class="absolute bottom-4 left-4 bg-white/95 p-3 rounded-lg text-xs border border-gray-100 backdrop-blur-sm shadow-lg z-30 max-w-[200px]">
                    <div class="flex items-center gap-2 mb-1.5">
                        <div class="w-2 h-2 rounded-full bg-indigo-600"></div>
                        <span class="font-bold text-slate-700">Güçlü Bağ:</span>
                        <span class="text-slate-500">Yazılım ↔ Satış</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <div class="w-2 h-2 rounded-full bg-slate-300"></div>
                        <span class="font-bold text-slate-700">Kopuk:</span>
                        <span class="text-slate-500">Pazarlama (Silo)</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { UsersIcon, BuildingOfficeIcon, ChartBarIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import StatCard from '@/components/dashboard/StatCard.vue'

const departments = [
  { id: 1, name: 'Yazılım Geliştirme', manager: 'Ahmet Yılmaz', managerInitials: 'AY', employees: 15, score: 8.9 },
  { id: 2, name: 'Satış', manager: 'Ayşe Kaya', managerInitials: 'AK', employees: 22, score: 9.2 },
  { id: 3, name: 'Pazarlama', manager: 'Mehmet Demir', managerInitials: 'MD', employees: 8, score: 7.5 },
  { id: 4, name: 'İnsan Kaynakları', manager: 'Zeynep Çelik', managerInitials: 'ZÇ', employees: 5, score: 7.9 },
]

const getScoreBadgeClass = (score: number) => {
  if (score >= 8.5) return 'bg-emerald-50 text-emerald-700 border-emerald-100'
  if (score >= 7.0) return 'bg-amber-50 text-amber-700 border-amber-100'
  return 'bg-rose-50 text-rose-700 border-rose-100'
}
</script>
