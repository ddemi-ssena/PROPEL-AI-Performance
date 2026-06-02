<template>
  <div class="space-y-8 pb-10">
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <StatCard
        title="Toplam Personel"
        :value="stats.totalEmployees"
        change="+12%"
        changeType="increase"
        :icon="UsersIcon"
        color="indigo"
      />
      <StatCard
        title="Departmanlar"
        :value="stats.totalDepartments"
        change="0%"
        changeType="neutral"
        :icon="BuildingOfficeIcon"
        color="slate"
      />
      <StatCard
        title="Ortalama Bağlılık"
        :value="stats.avgScore"
        change="+2.1%"
        changeType="increase"
        :icon="ChartBarIcon"
        color="emerald"
      />
      <StatCard
        title="Yüksek Riskli Personel"
        :value="stats.highRiskCount"
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
                  {{ dept.scoreDisplay ?? dept.score }}
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
                <div v-if="flightRiskEmployees.length === 0" class="text-sm text-slate-400 text-center py-4">
                    Yüksek riskli personel bulunamadı.
                </div>
                <div
                    v-for="emp in flightRiskEmployees"
                    :key="emp.id"
                    class="bg-white p-4 rounded-xl shadow-sm border border-rose-100 flex items-center justify-between hover:scale-[1.02] transition-transform duration-200 cursor-pointer"
                    @click="$router.push(`/admin/employees/${emp.id}`)"
                >
                    <div class="flex items-center gap-3">
                         <div class="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center font-bold text-slate-600 border border-slate-200 text-xs">
                            {{ initials(emp.user?.full_name) }}
                         </div>
                         <div>
                             <h4 class="font-bold text-slate-800 text-sm">{{ emp.user?.full_name }}</h4>
                             <p class="text-[10px] text-slate-400 font-medium uppercase tracking-wide">{{ emp.position || emp.department?.name }}</p>
                         </div>
                    </div>
                    <div class="text-right">
                        <span class="inline-flex items-center px-2 py-1 rounded-md text-xs font-bold"
                          :class="emp.risk_level === 'High' ? 'bg-rose-100 text-rose-700 border border-rose-200' : 'bg-amber-100 text-amber-700 border border-amber-200'">
                            {{ emp.risk_level === 'High' ? 'Yüksek Risk' : 'Orta Risk' }}
                        </span>
                        <p class="text-[10px] mt-1 font-medium" :class="emp.risk_level === 'High' ? 'text-rose-600' : 'text-amber-600'">
                            {{ emp.latest_ms !== null && emp.latest_ms !== undefined ? `MS: ${emp.latest_ms.toFixed(1)}` : 'Veri yok' }}
                        </p>
                    </div>
                </div>
            </div>

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
import { ref, computed, onMounted } from 'vue'
import { UsersIcon, BuildingOfficeIcon, ChartBarIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import StatCard from '@/components/dashboard/StatCard.vue'
import { employeeApi } from '@/services/api/employee.api'
import { dashboardApi } from '@/services/api/dashboard.api'

const stats = ref({
  totalEmployees: '0',
  totalDepartments: '0',
  avgScore: '0',
  highRiskCount: '0'
})

const allEmployees = ref<any[]>([])
const departments = ref<any[]>([])

// Uçuş riski: High önce, sonra Medium — en fazla 4 kişi
const flightRiskEmployees = computed(() =>
  allEmployees.value
    .filter((e: any) => e.risk_level === 'High' || e.risk_level === 'Medium')
    .sort((a: any, b: any) => {
      const order: Record<string, number> = { High: 0, Medium: 1 }
      return (order[a.risk_level] ?? 2) - (order[b.risk_level] ?? 2)
    })
    .slice(0, 4)
)

const fetchDashboardData = async () => {
    try {
        const [empData, insightData] = await Promise.all([
            employeeApi.getEmployees(),
            dashboardApi.getInsights()
        ])

        allEmployees.value = empData
        stats.value.totalEmployees = empData.length.toString()

        // Benzersiz departman isimleri
        const deptNames = new Set<string>(empData.map((e: any) => e.department?.name).filter(Boolean))
        stats.value.totalDepartments = deptNames.size.toString()

        // İstatistikler
        const scoreKpi = insightData.kpis?.find((k: any) => k.title?.includes('Bağlılık') || k.title?.includes('Ortalama'))
        stats.value.avgScore = scoreKpi ? scoreKpi.value : '—'
        stats.value.highRiskCount = insightData.riskData?.[2]?.toString() ?? '0'

        // Departman tablosu — yönetici: department_manager rolündeki çalışan
        const managerByDept: Record<string, any> = {}
        for (const emp of empData) {
            if (emp.user?.role === 'department_manager' && emp.department?.name) {
                managerByDept[emp.department.name] = emp
            }
        }

        departments.value = Array.from(deptNames).map((name, index) => {
            const deptEmps = empData.filter((e: any) => e.department?.name === name)
            const msValues = deptEmps.map((e: any) => e.latest_ms).filter((v: any) => v !== null && v !== undefined)
            const avgMs = msValues.length ? (msValues.reduce((a: number, b: number) => a + b, 0) / msValues.length).toFixed(1) : '—'
            const mgr = managerByDept[name as string]
            const mgrName = mgr?.user?.full_name ?? 'Yönetici Atanmadı'
            const mgrInitials = mgrName === 'Yönetici Atanmadı' ? 'YA' : initials(mgrName)

            return {
                id: index + 1,
                name: name,
                manager: mgrName,
                managerInitials: mgrInitials,
                employees: deptEmps.length,
                score: avgMs === '—' ? 0 : parseFloat(avgMs),
                scoreDisplay: avgMs,
            }
        })

    } catch (e) {
        console.error("Dashboard data fetch failed", e)
    }
}

function initials(name: string | undefined): string {
    if (!name) return '?'
    return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
}

onMounted(() => {
    fetchDashboardData()
})

const getScoreBadgeClass = (score: number) => {
  if (score >= 7) return 'bg-emerald-50 text-emerald-700 border-emerald-100'
  if (score >= 4) return 'bg-amber-50 text-amber-700 border-amber-100'
  return 'bg-rose-50 text-rose-700 border-rose-100'
}
</script>
