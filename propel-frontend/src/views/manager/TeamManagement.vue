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
              <th class="px-6 py-4">Son Anket Skoru</th>
              <th class="px-6 py-4">Motivasyon Trendi (MTE)</th>
              <th class="px-6 py-4">Ayrılma Riski (ARS)</th>
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
import { ref, onMounted, computed } from 'vue'
import { 
  PlusIcon,
  MagnifyingGlassIcon,
  EllipsisHorizontalIcon,
  RocketLaunchIcon,
  CommandLineIcon,
  ChartBarIcon
} from '@heroicons/vue/24/outline'
import { employeeApi } from '@/services/api/employee.api'

const teamMembers = ref<any[]>([])
const isLoading = ref(true)

const fetchTeamMembers = async () => {
    isLoading.value = true
    try {
        const data = await employeeApi.getEmployees()
        teamMembers.value = data.map((emp: any) => ({
            id: emp.id,
            name: emp.user.full_name,
            role: emp.position || emp.user.role,
            task: emp.latest_ms ? `Bağlılık: ${emp.latest_ms}/5` : 'Anket Yok',
            status: getMteStatus(emp.latest_mte),
            priority: emp.risk_level || 'Low',
            avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(emp.user.full_name)}&background=f3e8ff&color=6b21a8`
        }))
    } catch(e) {
        console.error("Failed to load team members", e)
    } finally {
        isLoading.value = false
    }
}

onMounted(() => {
    fetchTeamMembers()
})

const getMteStatus = (mte: number | null) => {
    if (mte === null) return 'Bilinmiyor'
    if (mte > 0.1) return 'Pozitif (+)'
    if (mte < -0.1) return 'Negatif (-)'
    return 'Stabil'
}

const getStatusColor = (status: string) => {
    switch(status) {
        case 'Pozitif (+)': return 'bg-emerald-50 text-emerald-700'
        case 'Stabil': return 'bg-blue-50 text-blue-700'
        case 'Negatif (-)': return 'bg-red-50 text-red-700'
        default: return 'bg-slate-50 text-slate-700'
    }
}

const getStatusLabel = (status: string) => status

const getPriorityColor = (priority: string) => {
    switch(priority) {
        case 'High': return 'bg-red-500'
        case 'Medium': return 'bg-amber-500'
        case 'Low': return 'bg-emerald-500'
        default: return 'bg-slate-400'
    }
}

const getPriorityLabel = (priority: string) => {
    switch(priority) {
        case 'High': return 'Yüksek (Risk)'
        case 'Medium': return 'Orta (Risk)'
        case 'Low': return 'Düşük (Risk)'
        default: return priority
    }
}
</script>
