<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
      <div>
        <h1 class="text-3xl font-bold text-slate-900 tracking-tight">Personel Yönetimi</h1>
        <p class="text-slate-500 mt-1">Tüm çalışanların performans ve durumlarını buradan yönetebilirsiniz.</p>
      </div>
      <button class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2.5 rounded-lg transition-colors flex items-center gap-2 shadow-sm shadow-blue-600/20">
        <UserPlusIcon class="w-5 h-5" />
        Yeni Personel Ekle
      </button>
    </div>

    <!-- Filters -->
    <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-200 mb-6 flex flex-col md:flex-row gap-4 items-center">
      <div class="relative w-full md:w-96">
        <MagnifyingGlassIcon class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="İsim, e-posta veya pozisyon ara..." 
          class="w-full pl-10 pr-4 py-2 bg-slate-50 border-none rounded-lg text-sm focus:ring-2 focus:ring-blue-500 transition-shadow"
        />
      </div>
      
      <div class="flex gap-4 w-full md:w-auto overflow-x-auto pb-2 md:pb-0">
        <select v-model="selectedDepartment" class="bg-slate-50 border-none rounded-lg text-sm py-2 pl-3 pr-8 focus:ring-2 focus:ring-blue-500 text-slate-600 font-medium">
          <option value="">Tüm Departmanlar</option>
          <option value="Yazılım Geliştirme">Yazılım Geliştirme</option>
          <option value="Satış">Satış</option>
          <option value="Pazarlama">Pazarlama</option>
          <option value="İnsan Kaynakları">İnsan Kaynakları</option>
        </select>

        <select v-model="selectedRisk" class="bg-slate-50 border-none rounded-lg text-sm py-2 pl-3 pr-8 focus:ring-2 focus:ring-blue-500 text-slate-600 font-medium">
          <option value="">Tüm Risk Seviyeleri</option>
          <option value="Low">Düşük</option>
          <option value="Medium">Orta</option>
          <option value="High">Yüksek</option>
        </select>
      </div>
    </div>

    <!-- Data Table -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <th class="px-6 py-4">Personel</th>
              <th class="px-6 py-4">Departman</th>
              <th class="px-6 py-4 cursor-pointer hover:text-blue-600 group" @click="sortBy('score')">
                <div class="flex items-center gap-1">
                  Performans Skoru
                  <ArrowsUpDownIcon class="w-4 h-4 text-slate-400 group-hover:text-blue-600" />
                </div>
              </th>
              <th class="px-6 py-4">Risk Durumu</th>
              <th class="px-6 py-4 text-right">İşlemler</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr 
              v-for="employee in filteredEmployees" 
              :key="employee.id" 
              class="hover:bg-slate-50 transition-colors cursor-pointer"
              @click="navigateToDetails(employee.id)"
            >
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <img :src="employee.avatar" :alt="employee.name" class="w-10 h-10 rounded-full object-cover border border-slate-200" />
                  <div>
                    <p class="font-medium text-slate-900">{{ employee.name }}</p>
                    <p class="text-xs text-slate-500">{{ employee.email }}</p>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
                  {{ employee.department }}
                </span>
                <p class="text-xs text-slate-500 mt-1 pl-1">{{ employee.role }}</p>
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                  <div class="w-16 bg-slate-200 rounded-full h-2 overflow-hidden">
                    <div class="h-full rounded-full" :class="getPerformanceColor(employee.score)" :style="{ width: `${employee.score}%` }"></div>
                  </div>
                  <span class="text-sm font-bold text-slate-700">{{ employee.score }}</span>
                </div>
              </td>
              <td class="px-6 py-4">
                <span 
                  class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border"
                  :class="getRiskBadgeClasses(employee.risk)"
                >
                  <span class="w-1.5 h-1.5 rounded-full bg-current"></span>
                  {{ getRiskLabel(employee.risk) }}
                </span>
              </td>
              <td class="px-6 py-4 text-right">
                <button class="text-slate-400 hover:text-blue-600 p-2 transition-colors" @click.stop>
                  <EllipsisHorizontalIcon class="w-5 h-5" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="px-6 py-4 border-t border-slate-200 flex items-center justify-between">
        <p class="text-sm text-slate-500">Toplam <span class="font-medium text-slate-900">{{ filteredEmployees.length }}</span> personelden <span class="font-medium text-slate-900">1-{{ filteredEmployees.length }}</span> arası gösteriliyor</p>
        <div class="flex gap-2">
          <button class="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-50" disabled>Önceki</button>
          <button class="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-50" disabled>Sonraki</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  UserPlusIcon, 
  MagnifyingGlassIcon, 
  ArrowsUpDownIcon, 
  EllipsisHorizontalIcon 
} from '@heroicons/vue/24/outline'
import { employeeApi } from '@/services/api/employee.api'

const router = useRouter()

const employees = ref<any[]>([])
const isLoading = ref(true)

const fetchEmployees = async () => {
    isLoading.value = true
    try {
        const data = await employeeApi.getEmployees()
        employees.value = data.map((emp: any) => ({
            id: emp.id,
            name: emp.user.full_name,
            email: emp.user.email,
            department: emp.department.name,
            role: emp.position || emp.user.role,
            score: emp.latest_ms ? Math.round(emp.latest_ms * 20) : 0, // Convert 5 point scale to 100%
            risk: emp.risk_level || 'Low',
            avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(emp.user.full_name)}&background=0284c7&color=fff`
        }))
    } catch(e) {
        console.error("Failed to load employees for management", e)
    } finally {
        isLoading.value = false
    }
}

onMounted(() => {
    fetchEmployees()
})

const searchQuery = ref('')
const selectedDepartment = ref('')
const selectedRisk = ref('')

const filteredEmployees = computed(() => {
  return employees.value.filter(emp => {
    const matchesSearch = 
      emp.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
      emp.email.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      emp.role.toLowerCase().includes(searchQuery.value.toLowerCase())
    
    const matchesDept = selectedDepartment.value ? emp.department === selectedDepartment.value : true
    const matchesRisk = selectedRisk.value ? emp.risk === selectedRisk.value : true

    return matchesSearch && matchesDept && matchesRisk
  })
})

function getPerformanceColor(score: number) {
  if (score >= 90) return 'bg-emerald-500'
  if (score >= 70) return 'bg-blue-500'
  if (score >= 50) return 'bg-amber-500'
  return 'bg-red-500'
}

function getRiskBadgeClasses(risk: string) {
  switch (risk) {
    case 'High': return 'bg-red-50 text-red-700 border-red-200'
    case 'Medium': return 'bg-amber-50 text-amber-700 border-amber-200'
    case 'Low': return 'bg-emerald-50 text-emerald-700 border-emerald-200'
    default: return 'bg-slate-50 text-slate-700 border-slate-200'
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

function navigateToDetails(id: number) {
  router.push(`/admin/employees/${id}`)
}

function sortBy(field: string) {
  // Sorting logic mock
  console.log('Sorting by', field)
}
</script>
