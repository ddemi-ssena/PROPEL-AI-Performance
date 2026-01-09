<template>
  <div class="pb-10">
    <!-- Stronger Header Section (Gradient Banner) -->
    <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-900 shadow-xl mb-8">
        <!-- Decorative Pattern -->
        <div class="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 rounded-full bg-indigo-500/20 blur-3xl"></div>
        <div class="absolute bottom-0 left-0 -ml-20 -mb-20 w-60 h-60 rounded-full bg-blue-500/20 blur-3xl"></div>
        
        <div class="relative z-10 flex flex-col md:flex-row items-center justify-between p-8 gap-6">
            <div class="flex items-center gap-6 w-full md:w-auto">
                 <div class="w-20 h-20 rounded-full ring-4 ring-white/10 shadow-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-2xl font-bold text-white shrink-0">
                    {{ userStore.user?.full_name?.split(' ').map((n: string) => n[0]).join('').substring(0,2).toUpperCase() || 'U' }}
                 </div>
                 <div>
                     <h1 class="text-3xl font-bold text-white tracking-tight">
                        Hoş Geldin, <br class="md:hidden"/>
                        <span class="text-transparent bg-clip-text bg-gradient-to-r from-indigo-200 to-blue-200">{{ userStore.user?.full_name }}</span>
                     </h1>
                     <div class="flex flex-wrap items-center gap-3 mt-3 text-sm font-medium">
                        <span class="bg-white/10 text-indigo-100 px-3 py-1 rounded-full backdrop-blur-sm border border-white/10">Senior Developer</span>
                        <span class="text-slate-400 hidden md:inline">•</span>
                        <span class="text-slate-300">Yazılım Geliştirme Departmanı</span>
                     </div>
                 </div>
            </div>

            <div class="flex gap-3 w-full md:w-auto">
                 <button class="flex-1 md:flex-none px-5 py-3 bg-white/5 border border-white/10 text-white text-sm font-medium rounded-xl hover:bg-white/10 hover:border-white/20 transition-all backdrop-blur-sm shadow-lg">
                    Rapor İndir
                </button>
                 <button class="flex-1 md:flex-none px-5 py-3 bg-indigo-500 text-white text-sm font-bold rounded-xl hover:bg-indigo-400 shadow-lg shadow-indigo-900/40 transition-all transform hover:-translate-y-0.5 border-t border-white/20">
                    + Yeni Hedef
                </button>
            </div>
        </div>
    </div>

    <!-- Stats Row -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <StatCard title="Genel Skor" value="92/100" change="+2.4%" changeType="increase" :icon="TrophyIcon" color="indigo" />
        <StatCard title="Tamamlanan Görev" value="14" change="+3" changeType="increase" :icon="CheckCircleIcon" color="emerald" />
        <StatCard title="Mutluluk Skoru" value="4.8/5" change="0.1" changeType="increase" :icon="FaceSmileIcon" color="amber" />
        <StatCard title="Gelişim Aktiviteleri" value="3 Saat" change="-10%" changeType="decrease" :icon="SparklesIcon" color="rose" />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        <!-- Performance Trend Chart -->
        <div class="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow group">
            <div class="flex justify-between items-center mb-6">
                <div>
                    <h3 class="font-bold text-slate-800 text-lg">Kişisel Performans Trendi</h3>
                    <p class="text-xs text-slate-500 mt-1">Son 6 aylık veriler</p>
                </div>
                <select class="bg-slate-50 border-slate-200 text-xs font-bold text-slate-600 rounded-lg py-2 px-3 focus:ring-2 focus:ring-indigo-500 outline-none cursor-pointer hover:bg-slate-100 transition-colors">
                    <option>Son 6 Ay</option>
                </select>
            </div>
            <div class="h-72">
                <LineChart 
                    :labels="['Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim']" 
                    :data="[75, 82, 80, 88, 85, 92]" 
                    label="Kişisel Skor"
                    color="#4f46e5" 
                />
            </div>
        </div>

        <!-- AI Growth Recommendations (Redesigned) -->
        <div class="bg-slate-900 rounded-2xl p-6 text-white relative overflow-hidden shadow-xl group border border-slate-800">
             <!-- Background Pattern -->
             <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <SparklesIcon class="w-32 h-32 text-indigo-400 transform rotate-12" />
             </div>

            <div class="relative z-10">
                <div class="flex items-center gap-3 mb-6">
                    <div class="p-2.5 bg-indigo-500/20 rounded-xl backdrop-blur-sm border border-indigo-500/30 shadow-inner">
                        <SparklesIcon class="w-6 h-6 text-indigo-300" />
                    </div>
                    <div>
                         <h3 class="font-bold text-xl text-white tracking-tight">AI Koç</h3>
                         <p class="text-xs text-slate-400 font-medium tracking-wide">Kişisel Gelişim Tavsiyeleri</p>
                    </div>
                </div>
                
                <div class="space-y-4">
                    <div class="bg-white/5 p-4 rounded-xl border border-white/5 hover:border-indigo-500/30 hover:bg-white/10 transition-all backdrop-blur-sm cursor-pointer group/item">
                        <h4 class="text-sm font-bold text-indigo-200 mb-2 group-hover/item:text-indigo-100 transition-colors">Kod İncelemelerine Katılım</h4>
                        <p class="text-xs text-slate-300 mb-4 leading-relaxed">Teknik liderliğini güçlendirmek için bu hafta 2 junior pull request'i incelemen öneriliyor.</p>
                        <button class="w-full py-2 bg-indigo-600 text-white text-xs font-bold rounded-lg hover:bg-indigo-500 transition shadow-lg shadow-indigo-900/20">
                            Planla
                        </button>
                    </div>
                    <div class="bg-white/5 p-4 rounded-xl border border-white/5 hover:border-rose-500/30 hover:bg-white/10 transition-all">
                        <h4 class="text-sm font-bold text-rose-200 mb-1">Mola Dengesi</h4>
                        <p class="text-xs text-slate-300">Geçen hafta %15 fazla çalıştın. Verimliliğini korumak için kısa molaları artır.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Creative Features Row: Pulse & Peer Praise -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <!-- Weekly Pulse Feedback (Clean UI) -->
        <div class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-lg hover:border-indigo-100 transition-all duration-300">
            <div class="flex items-center justify-between mb-6">
                 <div>
                    <h3 class="font-bold text-slate-800 flex items-center gap-2 text-lg">
                        <HeartIcon class="w-6 h-6 text-rose-500" />
                        Haftalık Nabız
                    </h3>
                    <p class="text-sm text-slate-500 mt-1">Bu hafta projede nasıl hissediyorsun?</p>
                 </div>
                 <span class="text-[10px] uppercase font-bold bg-slate-100 text-slate-500 px-2 py-1 rounded border border-slate-200">Anonim</span>
            </div>
            
            <div class="grid grid-cols-4 gap-4">
                <button class="group flex flex-col items-center justify-center p-4 rounded-2xl border-2 border-slate-50 bg-slate-50/50 hover:border-rose-200 hover:bg-rose-50 transition-all active:scale-95">
                    <span class="text-3xl mb-2 grayscale group-hover:grayscale-0 transition-all filter">😫</span>
                    <span class="text-[10px] font-bold text-slate-400 group-hover:text-rose-600">Stresli</span>
                </button>
                <button class="group flex flex-col items-center justify-center p-4 rounded-2xl border-2 border-slate-50 bg-slate-50/50 hover:border-amber-200 hover:bg-amber-50 transition-all active:scale-95">
                    <span class="text-3xl mb-2 grayscale group-hover:grayscale-0 transition-all filter">😐</span>
                    <span class="text-[10px] font-bold text-slate-400 group-hover:text-amber-600">Normal</span>
                </button>
                <button class="group flex flex-col items-center justify-center p-4 rounded-2xl border-2 border-slate-50 bg-slate-50/50 hover:border-emerald-200 hover:bg-emerald-50 transition-all active:scale-95">
                    <span class="text-3xl mb-2 grayscale group-hover:grayscale-0 transition-all filter">🙂</span>
                    <span class="text-[10px] font-bold text-slate-400 group-hover:text-emerald-600">İyi</span>
                </button>
                <button class="group flex flex-col items-center justify-center p-4 rounded-2xl border-2 border-indigo-100 bg-indigo-50 hover:bg-indigo-100 transition-all active:scale-95 shadow-sm">
                    <span class="text-3xl mb-2">🤩</span>
                    <span class="text-[10px] font-bold text-indigo-700">Harika</span>
                </button>
            </div>
            <div class="mt-6">
                <textarea placeholder="Eklemek istediğin bir not var mı? (İsteğe bağlı)" class="w-full text-sm p-3 rounded-xl bg-slate-50 border-none focus:ring-2 focus:ring-indigo-500/50 text-slate-700 placeholder-slate-400 transition-shadow"></textarea>
            </div>
        </div>

        <!-- Peer Praise (Professional UI) -->
        <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-lg hover:border-indigo-100 transition-all duration-300">
            <div class="flex justify-between items-center mb-6">
                <div>
                     <h3 class="font-bold text-slate-800 flex items-center gap-2 text-lg">
                        <StarIcon class="w-6 h-6 text-amber-500" />
                        Takımdan Övgüler
                    </h3>
                    <p class="text-sm text-slate-500 mt-1">Son alınan teşekkürler</p>
                </div>
                <button class="text-xs font-bold text-indigo-600 hover:bg-indigo-50 px-4 py-2 rounded-lg border border-indigo-100 transition-colors uppercase tracking-wide">
                    + Teşekkür Et
                </button>
            </div>

            <div class="space-y-4">
                <div class="flex gap-4 items-start p-4 rounded-2xl bg-slate-50 border border-slate-100 hover:bg-white hover:border-slate-200 hover:shadow-md transition-all group cursor-default">
                    <div class="w-12 h-12 rounded-2xl bg-white border border-slate-200 flex items-center justify-center text-slate-600 font-bold text-sm shrink-0 shadow-sm group-hover:scale-105 transition-transform">
                        ZK
                    </div>
                    <div class="flex-1">
                        <div class="flex justify-between items-start mb-1">
                            <div>
                                <h4 class="font-bold text-slate-900 text-sm">Zeynep Kaya</h4>
                                <p class="text-[10px] text-slate-400 font-medium uppercase tracking-wide">Product Owner</p>
                            </div>
                            <span class="text-[10px] text-slate-400 bg-white px-2 py-1 rounded-full border border-slate-100 shadow-sm">2 saat önce</span>
                        </div>
                        <p class="text-sm text-slate-600 leading-relaxed mt-2">"API entegrasyonundaki hızlı çözümün projenin yetişmesini sağladı, teşekkürler!"</p>
                        <div class="mt-3 flex gap-2">
                             <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-100">
                                🧠 Problem Çözücü
                             </span>
                        </div>
                    </div>
                </div>
                
                <div class="flex gap-4 items-start p-4 rounded-2xl bg-slate-50 border border-slate-100 hover:bg-white hover:border-slate-200 hover:shadow-md transition-all group cursor-default">
                    <div class="w-12 h-12 rounded-2xl bg-white border border-slate-200 flex items-center justify-center text-slate-600 font-bold text-sm shrink-0 shadow-sm group-hover:scale-105 transition-transform">
                        MD
                    </div>
                    <div class="flex-1">
                        <div class="flex justify-between items-start mb-1">
                             <div>
                                <h4 class="font-bold text-slate-900 text-sm">Mehmet Demir</h4>
                                <p class="text-[10px] text-slate-400 font-medium uppercase tracking-wide">Tech Lead</p>
                            </div>
                            <span class="text-[10px] text-slate-400 bg-white px-2 py-1 rounded-full border border-slate-100 shadow-sm">Dün</span>
                        </div>
                        <p class="text-sm text-slate-600 leading-relaxed mt-2">"Takım sunumundaki desteğin için çok sağ ol."</p>
                         <div class="mt-3 flex gap-2">
                            <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-100">
                                🤝 Takım Oyuncusu
                             </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
    TrophyIcon, 
    FaceSmileIcon, 
    CheckCircleIcon, 
    SparklesIcon,
    HeartIcon,
    StarIcon
} from '@heroicons/vue/24/outline'
import StatCard from '@/components/dashboard/StatCard.vue'
import LineChart from '@/components/dashboard/LineChart.vue'
import { useAuthStore } from '@/stores/auth'
const userStore = useAuthStore()
</script>
