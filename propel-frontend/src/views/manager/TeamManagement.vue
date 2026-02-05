<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
      <div>
        <h1 class="text-3xl font-bold text-slate-900 tracking-tight">Ekip Yönetimi</h1>
        <p class="text-slate-500 mt-1">Ekibinizin performansını ve güncel durumunu buradan takip edin.</p>
      </div>
      <button class="bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-4 py-2.5 rounded-lg transition-colors flex items-center gap-2 shadow-sm shadow-indigo-600/20">
        <PlusIcon class="w-5 h-5" />
        Görev Atama
      </button>
    </div>

    <!-- Stats Row -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
           <p class="text-sm font-medium text-slate-500">Aktif Sprintler</p>
           <p class="text-2xl font-bold text-slate-900 mt-1">3</p>
        </div>
        <div class="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
           <RocketLaunchIcon class="w-6 h-6" />
        </div>
      </div>
      <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
           <p class="text-sm font-medium text-slate-500">Devam Eden Görevler</p>
           <p class="text-2xl font-bold text-slate-900 mt-1">12</p>
        </div>
        <div class="p-3 bg-blue-50 text-blue-600 rounded-lg">
           <CommandLineIcon class="w-6 h-6" />
        </div>
      </div>
      <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
           <p class="text-sm font-medium text-slate-500">Ekip Hızı (Velocity)</p>
           <p class="text-2xl font-bold text-slate-900 mt-1">42 pts</p>
        </div>
        <div class="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
           <ChartBarIcon class="w-6 h-6" />
        </div>
      </div>
    </div>

    <!-- Team Table -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      <div class="p-6 border-b border-slate-200 flex flex-col md:flex-row gap-4 justify-between">
        <h2 class="text-lg font-bold text-slate-900">Ekip Üyeleri</h2>
        
        <div class="flex gap-4">
             <div class="relative">
                <MagnifyingGlassIcon class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input 
                  type="text" 
                  placeholder="Ekipte ara..." 
                  class="pl-10 pr-4 py-2 bg-slate-50 border-none rounded-lg text-sm focus:ring-1 focus:ring-indigo-500 w-full md:w-64"
                />
             </div>
             <button class="px-3 py-2 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 text-sm font-medium">
                Filtrele
             </button>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <th class="px-6 py-4">Çalışan</th>
              <th class="px-6 py-4">Rol</th>
              <th class="px-6 py-4">Mevcut Görev</th>
              <th class="px-6 py-4">Durum</th>
              <th class="px-6 py-4">Öncelik</th>
              <th class="px-6 py-4 text-right">İşlemler</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="member in teamMembers" :key="member.id" class="hover:bg-slate-50 transition-colors">
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <img :src="member.avatar" :alt="member.name" class="w-8 h-8 rounded-full" />
                  <span class="font-medium text-slate-900 text-sm">{{ member.name }}</span>
                </div>
              </td>
              <td class="px-6 py-4 text-sm text-slate-600">
                {{ member.role }}
              </td>
              <td class="px-6 py-4 text-sm text-slate-600">
                <span class="truncate block max-w-xs" :title="member.task">{{ member.task }}</span>
              </td>
              <td class="px-6 py-4">
                 <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                      :class="getStatusColor(member.status)">
                  {{ getStatusLabel(member.status) }}
                </span>
              </td>
               <td class="px-6 py-4">
                 <div class="flex items-center gap-1">
                    <span class="w-2 h-2 rounded-full" :class="getPriorityColor(member.priority)"></span>
                    <span class="text-sm text-slate-600">{{ getPriorityLabel(member.priority) }}</span>
                 </div>
              </td>
              <td class="px-6 py-4 text-right">
                <button class="text-slate-400 hover:text-indigo-600 transition-colors">
                  <EllipsisHorizontalIcon class="w-5 h-5" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { 
  PlusIcon,
  MagnifyingGlassIcon,
  EllipsisHorizontalIcon,
  RocketLaunchIcon,
  CommandLineIcon,
  ChartBarIcon
} from '@heroicons/vue/24/outline'

const teamMembers = ref([
  {
    id: 1,
    name: 'Ahmet Yılmaz',
    role: 'Yazılım Müdürü',
    task: 'Çeyrek Raporlaması',
    status: 'In Progress',
    priority: 'High',
    avatar: 'https://ui-avatars.com/api/?name=Ahmet+Yilmaz&background=fde68a&color=1e293b'
  },
  {
    id: 2,
    name: 'Canan Dağdelen',
    role: 'Senior Developer',
    task: 'Personel Detay Ekranı Geliştirmesi',
    status: 'In Progress',
    priority: 'High',
    avatar: 'https://ui-avatars.com/api/?name=Canan+Dagdelen&background=cffafe&color=0e7490'
  },
  {
    id: 3,
    name: 'Berkant Demir',
    role: 'Mid-Level Developer',
    task: 'Frontend Performans Optimizasyonu',
    status: 'In Review',
    priority: 'Medium',
    avatar: 'https://ui-avatars.com/api/?name=Berkant+Demir&background=fee2e2&color=991b1b'
  },
   {
    id: 4,
    name: 'Elif Öztürk',
    role: 'Junior Developer',
    task: 'Unit Test Yazımı',
    status: 'Blocked',
    priority: 'Low',
    avatar: 'https://ui-avatars.com/api/?name=Elif+Ozturk&background=f3e8ff&color=6b21a8'
  },
  {
    id: 5,
    name: 'Murat Kaya',
    role: 'Senior Developer',
    task: 'API Entegrasyonu Süreci',
    status: 'Done',
    priority: 'Critical',
    avatar: 'https://ui-avatars.com/api/?name=Murat+Kaya&background=dcfce7&color=166534'
  }
])

const getStatusColor = (status: string) => {
    switch(status) {
        case 'In Progress': return 'bg-blue-50 text-blue-700'
        case 'In Review': return 'bg-amber-50 text-amber-700'
        case 'Done': return 'bg-emerald-50 text-emerald-700'
        case 'Blocked': return 'bg-red-50 text-red-700'
        default: return 'bg-slate-50 text-slate-700'
    }
}

const getStatusLabel = (status: string) => {
    switch(status) {
        case 'In Progress': return 'Devam Ediyor'
        case 'In Review': return 'İncelemede'
        case 'Done': return 'Tamamlandı'
        case 'Blocked': return 'Engellendi'
        default: return status
    }
}

const getPriorityColor = (priority: string) => {
    switch(priority) {
        case 'High': return 'bg-orange-500'
        case 'Critical': return 'bg-red-500'
        case 'Medium': return 'bg-blue-500'
        default: return 'bg-slate-400'
    }
}

const getPriorityLabel = (priority: string) => {
    switch(priority) {
        case 'High': return 'Yüksek'
        case 'Critical': return 'Kritik'
        case 'Medium': return 'Orta'
        case 'Low': return 'Düşük'
        default: return priority
    }
}
</script>
