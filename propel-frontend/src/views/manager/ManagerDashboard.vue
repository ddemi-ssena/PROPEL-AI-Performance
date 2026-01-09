<template>
  <div class="space-y-8 pb-10">
    <!-- Header Section -->
    <div class="flex flex-col md:flex-row justify-between items-end gap-4 border-b border-slate-200 pb-6">
        <div>
            <h2 class="text-2xl font-bold text-slate-900 tracking-tight">Yazılım Geliştirme Departmanı</h2>
            <p class="text-slate-500 mt-1">Performans Özeti ve Ekip Durumu</p>
        </div>
        <div class="flex gap-3">
            <button class="px-4 py-2 bg-white border border-gray-200 text-slate-600 text-sm font-medium rounded-lg hover:bg-gray-50 flex items-center gap-2 shadow-sm transition-all">
                <ArrowDownTrayIcon class="w-4 h-4" />
                Rapor İndir
            </button>
            <button class="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 shadow-md shadow-indigo-200 transition-all">
                Yeni Değerlendirme
            </button>
        </div>
    </div>
    
    <!-- Stats Row -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard title="Genel Üretkenlik" value="8.2/10" change="+5%" changeType="increase" :icon="BoltIcon" color="indigo" />
        <StatCard title="Ekip Bağlılığı" value="89%" change="-2%" changeType="decrease" :icon="HeartIcon" color="rose" />
        <StatCard title="Tamamlanan Görev" value="1,204" change="+10%" changeType="increase" :icon="CheckCircleIcon" color="emerald" />
        <StatCard title="Ortalama İş Yükü" value="95%" change="+1%" changeType="increase" :icon="ScaleIcon" color="amber" />
    </div>

    <!-- Charts Section -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Main Chart -->
        <div class="lg:col-span-2 bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div class="flex justify-between items-center mb-6">
                <h3 class="font-bold text-slate-800">Üretkenlik Trendleri</h3>
                <span class="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-1 rounded-full border border-emerald-100">+2.5% Bu Ay</span>
            </div>
            <div class="h-72">
                <LineChart 
                    :labels="['Hafta 1', 'Hafta 2', 'Hafta 3', 'Hafta 4']" 
                    :data="[65, 78, 72, 85]" 
                    label="Üretkenlik Skoru"
                    color="#4f46e5"
                />
            </div>
        </div>

        <!-- AI Insights Sidebar (Premium Dark) -->
        <div class="bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-700 relative overflow-hidden group">
            <div class="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity">
                <SparklesIcon class="w-16 h-16 text-white" />
            </div>
            
            <div class="relative z-10">
                <div class="flex items-center gap-2 mb-6">
                    <div class="p-2 bg-indigo-500/20 rounded-lg backdrop-blur-sm border border-indigo-500/30">
                        <SparklesIcon class="w-5 h-5 text-indigo-300" />
                    </div>
                    <div>
                        <h3 class="font-bold text-white">YZ Analizleri</h3>
                        <p class="text-xs text-slate-400">Veriye dayalı öngörüler</p>
                    </div>
                </div>
                
                <div class="space-y-4">
                    <div class="bg-white/5 p-4 rounded-xl border border-white/10 hover:bg-white/10 transition backdrop-blur-md">
                        <div class="flex gap-2 text-rose-400 text-xs font-bold mb-2 items-center">
                            <ExclamationTriangleIcon class="w-4 h-4" />
                            <span>Yüksek Risk</span>
                        </div>
                        <p class="text-xs text-slate-300 leading-relaxed">Takım üzerinde sürdürülebilir olmayan iş yükü tespit edildi. Tükenmişlik riski artıyor.</p>
                    </div>

                    <div class="bg-white/5 p-4 rounded-xl border border-white/10 hover:bg-white/10 transition backdrop-blur-md">
                        <div class="flex gap-2 text-emerald-400 text-xs font-bold mb-2 items-center">
                            <TrophyIcon class="w-4 h-4" />
                            <span>Haftanın Yıldızı</span>
                        </div>
                        <p class="text-xs text-slate-300 leading-relaxed"><strong class="text-white">Ahmet Yılmaz</strong>, hedefleri %25 oranında aştı.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Creative Features: Talent Matrix & Skill Radar -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 pb-10">
        <!-- 9-Box Talent Matrix (Enhanced) -->
        <div class="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 hover:shadow-lg transition-all duration-300">
            <div class="flex justify-between items-center mb-8">
                <div>
                   <h3 class="font-bold text-slate-800 text-lg flex items-center gap-2">
                        <div class="w-1.5 h-6 bg-indigo-500 rounded-full"></div>
                        9-Box Yetenek Matrisi
                   </h3> 
                   <p class="text-sm text-slate-500 mt-1 pl-3.5">Potansiyel vs Performans Analizi</p>
                </div>
                <button class="px-3 py-1.5 text-xs font-bold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors border border-indigo-100">
                    Detaylı Rapor
                </button>
            </div>
            
            <div class="relative h-[400px] pl-8 pb-8">
                <!-- Axis Labels -->
                <div class="absolute -left-6 top-1/2 -rotate-90 text-xs font-bold text-slate-400 tracking-[0.2em] transform -translate-y-1/2">POTANSİYEL</div>
                <div class="absolute bottom-0 left-1/2 -translate-x-1/2 text-xs font-bold text-slate-400 tracking-[0.2em]">PERFORMANS</div>

                <!-- Main Grid Container -->
                <div class="grid grid-cols-3 grid-rows-3 h-full w-full gap-1 p-1 bg-slate-100 rounded-xl overflow-hidden border border-slate-200">
                    <!-- Row 1: High Potential -->
                    <div class="bg-amber-50 relative group hover:bg-amber-100 transition-colors cursor-pointer p-2 flex flex-col items-center justify-center">
                         <span class="absolute top-1 left-2 text-[8px] font-bold text-amber-700/50 uppercase tracking-wide opacity-0 group-hover:opacity-100 transition-opacity">Puzzle</span>
                         <div class="flex -space-x-2 overflow-hidden">
                            <div class="w-9 h-9 rounded-full bg-white text-slate-600 border-2 border-amber-100 shadow-sm flex items-center justify-center text-[10px] font-bold z-10" title="Ali Veli">AV</div>
                         </div>
                    </div>
                    <div class="bg-emerald-50 relative group hover:bg-emerald-100 transition-colors cursor-pointer p-2 flex flex-col items-center justify-center">
                         <span class="absolute top-1 left-2 text-[8px] font-bold text-emerald-700/50 uppercase tracking-wide opacity-0 group-hover:opacity-100 transition-opacity">Growth</span>
                         <div class="w-9 h-9 rounded-full bg-white text-emerald-700 border-2 border-emerald-100 shadow-sm flex items-center justify-center text-[10px] font-bold" title="Ayşe Yılmaz">AY</div>
                    </div>
                    <div class="bg-indigo-50 relative group hover:bg-indigo-100 transition-colors cursor-pointer p-2 flex flex-col items-center justify-center ring-inset ring-2 ring-indigo-500/10">
                        <span class="absolute top-1 right-2 w-2 h-2 bg-indigo-500 rounded-full animate-pulse"></span>
                        <span class="absolute bottom-1 right-2 text-[8px] font-bold text-indigo-600 uppercase tracking-wide">Star</span>
                         <div class="w-12 h-12 rounded-full bg-indigo-600 text-white text-sm flex items-center justify-center font-bold border-4 border-white shadow-lg z-20" title="Mehmet Demir">MD</div>
                    </div>

                    <!-- Row 2: Medium Potential -->
                    <div class="bg-slate-50 relative group hover:bg-slate-100 transition-colors cursor-pointer p-2 flex flex-col items-center justify-center">
                         <!-- Core Players -->
                         <div class="flex -space-x-3 hover:space-x-1 transition-all duration-300">
                             <div class="w-9 h-9 rounded-full bg-white text-slate-600 border-2 border-slate-200 shadow-sm flex items-center justify-center text-[10px] font-bold">BÇ</div>
                             <div class="w-9 h-9 rounded-full bg-white text-slate-600 border-2 border-slate-200 shadow-sm flex items-center justify-center text-[10px] font-bold">EK</div>
                         </div>
                    </div>
                    <div class="bg-emerald-50 relative group hover:bg-emerald-100 transition-colors cursor-pointer p-2 flex flex-col items-center justify-center">
                        <span class="absolute top-1 left-2 text-[8px] font-bold text-emerald-700/50 uppercase tracking-wide opacity-0 group-hover:opacity-100 transition-opacity">High Perf</span>
                        <div class="w-9 h-9 rounded-full bg-white text-emerald-700 border-2 border-emerald-100 shadow-sm flex items-center justify-center text-[10px] font-bold">ZP</div>
                    </div>
                    <div class="bg-indigo-50/50 relative group hover:bg-indigo-100 transition-colors cursor-pointer p-2">
                        <!-- Empty for now -->
                    </div>

                    <!-- Row 3: Low Potential -->
                    <div class="bg-rose-50 relative group hover:bg-rose-100 transition-colors cursor-pointer p-2 flex flex-col items-center justify-center">
                        <span class="absolute top-1 left-2 text-[8px] font-bold text-rose-400 uppercase tracking-wide">Risk</span>
                        <div class="w-9 h-9 rounded-full bg-rose-100 text-rose-600 border-2 border-white shadow-sm flex items-center justify-center text-[10px] font-bold animate-bounce" title="Riskli Personel">?!</div>
                    </div>
                    <div class="bg-slate-50 relative group hover:bg-slate-100 transition-colors cursor-pointer p-2">
                        <!-- Empty -->
                    </div>
                    <div class="bg-amber-50 relative group hover:bg-amber-100 transition-colors cursor-pointer p-2 flex flex-col items-center justify-center">
                         <span class="absolute top-1 left-2 text-[8px] font-bold text-amber-700/50 uppercase tracking-wide opacity-0 group-hover:opacity-100 transition-opacity">Effective</span>
                         <div class="w-9 h-9 rounded-full bg-white text-amber-700 border-2 border-amber-100 shadow-sm flex items-center justify-center text-[10px] font-bold">CK</div>
                    </div>
                </div>
            </div>
            <!-- Legend -->
            <div class="flex gap-4 mt-6 justify-center">
                <div class="flex items-center gap-2">
                    <div class="w-3 h-3 rounded bg-indigo-50 border border-indigo-200"></div>
                    <span class="text-[10px] font-bold text-slate-500 uppercase">Yıldızlar</span>
                </div>
                <div class="flex items-center gap-2">
                    <div class="w-3 h-3 rounded bg-emerald-50 border border-emerald-200"></div>
                    <span class="text-[10px] font-bold text-slate-500 uppercase">Yüksek Performans</span>
                </div>
                 <div class="flex items-center gap-2">
                    <div class="w-3 h-3 rounded bg-rose-50 border border-rose-200"></div>
                    <span class="text-[10px] font-bold text-slate-500 uppercase">Risk</span>
                </div>
            </div>
        </div>

        <!-- Skill Gap Radar (Enhanced) -->
        <div class="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 hover:shadow-lg transition-all duration-300 flex flex-col">
             <div class="flex justify-between items-start mb-8">
                <div>
                   <h3 class="font-bold text-slate-800 text-lg flex items-center gap-2">
                        <div class="w-1.5 h-6 bg-pink-500 rounded-full"></div>
                        Teknik Yetenek Haritası
                   </h3> 
                   <p class="text-sm text-slate-500 mt-1 pl-3.5">Mevcut vs Hedeflenen Yetkinlik</p>
                </div>
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-600 border border-rose-100 shadow-sm animate-pulse">
                    DevOps Eksiği Var
                </span>
            </div>
            
            <div class="flex-1 relative">
                 <div class="h-[350px] w-full">
                    <RadarChart 
                        :labels="['Python/Django', 'Vue.js/Frontend', 'DevOps/CI-CD', 'SQL Opt.', 'System Design', 'Testing']"
                        :datasets="[
                            {
                                label: 'Hedeflenen Seviye',
                                data: [90, 85, 80, 85, 90, 85],
                                borderColor: '#94a3b8', // Slate-400
                                borderWidth: 2,
                                borderDash: [5, 5],
                                backgroundColor: 'rgba(241, 245, 249, 0.5)',
                                pointRadius: 0
                            },
                            {
                                label: 'Mevcut Takım Ort.',
                                data: [92, 88, 55, 75, 82, 70],
                                borderColor: '#6366f1', // Indigo-500
                                borderWidth: 3,
                                backgroundColor: 'rgba(99, 102, 241, 0.2)',
                                pointBackgroundColor: '#fff',
                                pointBorderColor: '#6366f1',
                                pointHoverRadius: 6
                            }
                        ]"
                    />
                </div>
                
                <!-- Skill Breakdown Badge List -->
                 <div class="absolute top-0 right-0 flex flex-col gap-2 pointer-events-none opacity-80">
                    <div class="flex items-center gap-2 justify-end">
                         <span class="text-[10px] font-bold text-slate-400">Güçlü:</span>
                         <span class="px-2 py-0.5 bg-indigo-50 text-indigo-700 text-[10px] font-bold rounded">Python</span>
                    </div>
                     <div class="flex items-center gap-2 justify-end">
                         <span class="text-[10px] font-bold text-slate-400">Zayıf:</span>
                         <span class="px-2 py-0.5 bg-rose-50 text-rose-700 text-[10px] font-bold rounded">DevOps</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
    ArrowDownTrayIcon, 
    BoltIcon, 
    HeartIcon, 
    CheckCircleIcon, 
    ScaleIcon,
    SparklesIcon,
    ExclamationTriangleIcon,
    TrophyIcon
} from '@heroicons/vue/24/outline'
import StatCard from '@/components/dashboard/StatCard.vue'
import LineChart from '@/components/dashboard/LineChart.vue'
import RadarChart from '@/components/dashboard/RadarChart.vue'
</script>
