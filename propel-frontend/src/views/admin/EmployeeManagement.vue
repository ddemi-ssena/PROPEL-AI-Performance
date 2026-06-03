<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
      <div>
        <h1 class="text-3xl font-bold text-slate-900 tracking-tight">Personel Yönetimi</h1>
        <p class="text-slate-500 mt-1">
          Performans ve risk verileri
          <span class="font-medium text-indigo-600">en son yüklenen ML modellerinden</span>
          hesaplanmaktadır.
        </p>
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

      <div class="flex gap-3 w-full md:w-auto overflow-x-auto pb-2 md:pb-0">
        <!-- Departman filtresi — dinamik -->
        <select v-model="selectedDepartment" class="bg-slate-50 border-none rounded-lg text-sm py-2 pl-3 pr-8 focus:ring-2 focus:ring-blue-500 text-slate-600 font-medium">
          <option value="">Tüm Departmanlar</option>
          <option v-for="d in departmentOptions" :key="d" :value="d">{{ d }}</option>
        </select>

        <!-- Risk filtresi — ML'den -->
        <select v-model="selectedRisk" class="bg-slate-50 border-none rounded-lg text-sm py-2 pl-3 pr-8 focus:ring-2 focus:ring-blue-500 text-slate-600 font-medium">
          <option value="">Tüm Risk Seviyeleri</option>
          <option value="High">Yüksek Risk</option>
          <option value="Low">Düşük Risk</option>
        </select>

        <!-- Sıralama -->
        <select v-model="sortField" class="bg-slate-50 border-none rounded-lg text-sm py-2 pl-3 pr-8 focus:ring-2 focus:ring-blue-500 text-slate-600 font-medium">
          <option value="">Sıralama</option>
          <option value="perf_desc">Performans ↓</option>
          <option value="perf_asc">Performans ↑</option>
          <option value="risk_desc">Risk ↓</option>
          <option value="name_asc">İsim A-Z</option>
        </select>
      </div>

      <!-- ML veri kaynağı göstergesi -->
      <div class="ml-auto flex items-center gap-2 text-xs text-slate-400 whitespace-nowrap">
        <span class="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>
        ML: upload #{{ latestSalesId || '—' }} (Satış) · #{{ latestSoftwareId || '—' }} (Yazılım)
      </div>
    </div>

    <!-- Yükleniyor -->
    <div v-if="isLoading" class="flex items-center justify-center py-16 text-slate-400">
      <svg class="animate-spin w-6 h-6 mr-3" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
      </svg>
      ML verileri yükleniyor...
    </div>

    <!-- Tablo -->
    <div v-else class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <th class="px-6 py-4">Personel</th>
              <th class="px-6 py-4">Departman / Takım</th>
              <th class="px-6 py-4">
                <button class="flex items-center gap-1 hover:text-blue-600" @click="toggleSort('perf')">
                  Performans Skoru
                  <ArrowsUpDownIcon class="w-4 h-4" />
                </button>
              </th>
              <th class="px-6 py-4">
                <button class="flex items-center gap-1 hover:text-blue-600" @click="toggleSort('risk')">
                  Risk Durumu (ML)
                  <ArrowsUpDownIcon class="w-4 h-4" />
                </button>
              </th>
              <th class="px-6 py-4 text-right">İşlemler</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr
              v-for="emp in paginatedEmployees"
              :key="emp.id"
              class="hover:bg-slate-50 transition-colors cursor-pointer"
              @click="navigateToDetails(emp.id)"
            >
              <!-- Personel -->
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white flex-shrink-0"
                    :class="emp.mlDept === 'Satis' ? 'bg-emerald-500' : 'bg-indigo-600'">
                    {{ initials(emp.name) }}
                  </div>
                  <div>
                    <p class="font-medium text-slate-900 text-sm">{{ emp.name }}</p>
                    <p class="text-xs text-slate-400">{{ emp.email }}</p>
                  </div>
                </div>
              </td>

              <!-- Departman / Takım -->
              <td class="px-6 py-4">
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                  :class="emp.mlDept === 'Satis'
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'bg-indigo-50 text-indigo-700'">
                  {{ emp.department }}
                </span>
                <p class="text-xs text-slate-400 mt-0.5">{{ emp.mlTeam || emp.position || '—' }}</p>
              </td>

              <!-- Performans Skoru -->
              <td class="px-6 py-4">
                <template v-if="emp.mlPerformance !== null">
                  <div class="flex items-center gap-2">
                    <div class="w-20 bg-slate-200 rounded-full h-2 overflow-hidden">
                      <div class="h-full rounded-full transition-all"
                        :class="getPerfColor(emp.mlPerformance)"
                        :style="{ width: `${emp.mlPerformance}%` }">
                      </div>
                    </div>
                    <span class="text-sm font-bold text-slate-700">{{ emp.mlPerformance }}</span>
                  </div>
                  <p class="text-[10px] text-slate-400 mt-0.5">{{ emp.mlBand || '—' }}</p>
                </template>
                <span v-else class="text-xs text-slate-400">—</span>
              </td>

              <!-- Risk Durumu -->
              <td class="px-6 py-4">
                <template v-if="emp.mlRisk">
                  <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border"
                    :class="getRiskClass(emp.mlRisk)">
                    <span class="w-1.5 h-1.5 rounded-full bg-current"></span>
                    {{ getRiskLabel(emp.mlRisk) }}
                  </span>
                  <p v-if="emp.mlTopDriver" class="text-[10px] text-slate-400 mt-0.5 max-w-[160px] truncate">
                    {{ emp.mlTopDriver }}
                  </p>
                </template>
                <span v-else class="text-xs text-slate-400">Veri yok</span>
              </td>

              <!-- İşlemler -->
              <td class="px-6 py-4 text-right">
                <button class="text-slate-400 hover:text-blue-600 p-2 transition-colors" @click.stop>
                  <EllipsisHorizontalIcon class="w-5 h-5" />
                </button>
              </td>
            </tr>

            <tr v-if="filteredEmployees.length === 0">
              <td colspan="5" class="px-6 py-12 text-center text-slate-400 text-sm">
                Filtrelerle eşleşen personel bulunamadı.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="px-6 py-4 border-t border-slate-200 flex items-center justify-between">
        <p class="text-sm text-slate-500">
          Toplam <span class="font-medium text-slate-900">{{ filteredEmployees.length }}</span> personel ·
          Sayfa {{ currentPage }} / {{ totalPages }}
        </p>
        <div class="flex gap-2">
          <button
            :disabled="currentPage <= 1"
            @click="currentPage--"
            class="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed">
            Önceki
          </button>
          <button
            :disabled="currentPage >= totalPages"
            @click="currentPage++"
            class="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed">
            Sonraki
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { UserPlusIcon, MagnifyingGlassIcon, ArrowsUpDownIcon, EllipsisHorizontalIcon } from '@heroicons/vue/24/outline'
import { apiClient } from '@/services/api/client'
import { employeeApi } from '@/services/api/employee.api'
import { adminUploadApi } from '@/services/api/admin_upload.api'

const router = useRouter()
const isLoading = ref(true)

// ── Veri ──────────────────────────────────────────────────────────────────
const employees = ref<any[]>([])
const latestSalesId = ref<number | null>(null)
const latestSoftwareId = ref<number | null>(null)

// flight-risk'ten gelen employee_code → ML verisi haritası
const mlMap = ref<Record<string, { risk_level: string; performance_score: number; top_driver: string | null; predicted_band: string; team: string | null; department: string }>>({})

const fetchAll = async () => {
  isLoading.value = true
  try {
    const [empData, flightData] = await Promise.all([
      employeeApi.getEmployees(),
      adminUploadApi.getFlightRisk(),
    ])

    // ML haritasını oluştur
    const map: typeof mlMap.value = {}
    for (const e of flightData.employees) {
      map[e.employee_code] = {
        risk_level: e.risk_level,
        performance_score: e.performance_score,
        top_driver: e.top_driver,
        predicted_band: e.predicted_band,
        team: e.team,
        department: e.department,
      }
    }
    mlMap.value = map

    // En son upload ID'lerini bul
    try {
      const [salesDs, swDs] = await Promise.all([
        apiClient.get('/analytics/departments/sales/datasets').then((r: any) => r.data),
        apiClient.get('/analytics/departments/software/datasets').then((r: any) => r.data),
      ])
      latestSalesId.value = salesDs?.[0]?.id ?? null
      latestSoftwareId.value = swDs?.[0]?.id ?? null
    } catch (_) { /* opsiyonel */ }

    // Çalışan listesini ML verisiyle zenginleştir
    const empArray = Array.isArray(empData) ? empData : (empData?.items ?? [])
    employees.value = empArray.map((emp: any) => {
      const extCode = emp.external_employee_code || ''
      const ml = mlMap.value[extCode] || null
      return {
        id: emp.id,
        name: emp.user?.full_name || '?',
        email: emp.user?.email || '',
        department: emp.department?.name || '?',
        position: emp.position || emp.user?.role || '',
        mlRisk: ml?.risk_level ?? null,
        mlPerformance: ml?.performance_score ?? null,
        mlBand: ml?.predicted_band ?? null,
        mlTopDriver: ml?.top_driver ?? null,
        mlTeam: ml?.team ?? null,
        mlDept: ml?.department ?? null,
      }
    })
  } catch (err) {
    console.error('[EmployeeManagement] fetch error', err)
  } finally {
    isLoading.value = false
  }
}

onMounted(fetchAll)

// ── Filtreler ──────────────────────────────────────────────────────────────
const searchQuery = ref('')
const selectedDepartment = ref('')
const selectedRisk = ref('')
const sortField = ref('')
const currentPage = ref(1)
const PAGE_SIZE = 15

const departmentOptions = computed(() => {
  const names = new Set(employees.value.map((e: any) => e.department).filter(Boolean))
  return Array.from(names).sort()
})

const filteredEmployees = computed(() => {
  let list = employees.value.filter((emp: any) => {
    const q = searchQuery.value.toLowerCase()
    const matchSearch = !q || emp.name.toLowerCase().includes(q) ||
      emp.email.toLowerCase().includes(q) ||
      (emp.position || '').toLowerCase().includes(q)
    const matchDept = !selectedDepartment.value || emp.department === selectedDepartment.value
    const matchRisk = !selectedRisk.value || emp.mlRisk === selectedRisk.value
    return matchSearch && matchDept && matchRisk
  })

  // Sıralama
  if (sortField.value === 'perf_desc') list = [...list].sort((a, b) => (b.mlPerformance ?? 0) - (a.mlPerformance ?? 0))
  else if (sortField.value === 'perf_asc') list = [...list].sort((a, b) => (a.mlPerformance ?? 0) - (b.mlPerformance ?? 0))
  else if (sortField.value === 'risk_desc') {
    const order: Record<string, number> = { High: 0, Medium: 1, Low: 2 }
    list = [...list].sort((a, b) => (order[a.mlRisk ?? 'Low'] ?? 2) - (order[b.mlRisk ?? 'Low'] ?? 2))
  }
  else if (sortField.value === 'name_asc') list = [...list].sort((a, b) => a.name.localeCompare(b.name))

  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredEmployees.value.length / PAGE_SIZE)))

const paginatedEmployees = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredEmployees.value.slice(start, start + PAGE_SIZE)
})

// Filtre değişince ilk sayfaya dön
function resetPage() { currentPage.value = 1 }
watch([searchQuery, selectedDepartment, selectedRisk, sortField], resetPage)

// ── Yardımcı ──────────────────────────────────────────────────────────────
function toggleSort(field: 'perf' | 'risk') {
  if (field === 'perf') sortField.value = sortField.value === 'perf_desc' ? 'perf_asc' : 'perf_desc'
  else sortField.value = 'risk_desc'
  resetPage()
}

function getPerfColor(score: number) {
  if (score >= 80) return 'bg-emerald-500'
  if (score >= 60) return 'bg-blue-500'
  if (score >= 40) return 'bg-amber-500'
  return 'bg-red-500'
}

function getRiskClass(risk: string) {
  if (risk === 'High') return 'bg-red-50 text-red-700 border-red-200'
  if (risk === 'Medium') return 'bg-amber-50 text-amber-700 border-amber-200'
  return 'bg-emerald-50 text-emerald-700 border-emerald-200'
}

function getRiskLabel(risk: string) {
  if (risk === 'High') return 'Yüksek'
  if (risk === 'Medium') return 'Orta'
  return 'Düşük'
}

function initials(name: string) {
  return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
}

function navigateToDetails(id: number) {
  router.push(`/admin/employees/${id}`)
}
</script>
