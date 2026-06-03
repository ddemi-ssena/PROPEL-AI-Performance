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
          <p class="text-xs text-slate-400 mt-1">Departman ML analizine gitmek için Analize Git butonunu kullanın</p>
        </div>
      </div>

      <div class="divide-y divide-gray-100">
        <div
          v-for="dept in departments"
          :key="dept.id"
          class="flex items-center justify-between px-6 py-5 hover:bg-slate-50/50 transition-colors"
        >
          <!-- Sol: departman adı + personel badge -->
          <div class="flex items-center gap-4 min-w-0">
            <div class="w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold shadow-sm flex-shrink-0"
              :class="dept.isSales ? 'bg-emerald-100 text-emerald-700' : 'bg-indigo-100 text-indigo-700'">
              {{ dept.name.charAt(0) }}
            </div>
            <div class="min-w-0">
              <p class="font-semibold text-slate-800 text-sm">{{ dept.name }}</p>
              <span class="inline-flex items-center gap-1 text-[11px] text-slate-400 font-medium mt-0.5">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0" /></svg>
                {{ dept.employees }} personel
              </span>
            </div>
          </div>

          <!-- Orta: yönetici -->
          <div class="flex items-center gap-3 flex-1 justify-center">
            <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border border-white shadow-sm flex-shrink-0"
              :class="dept.isSales ? 'bg-emerald-200 text-emerald-700' : 'bg-indigo-200 text-indigo-700'">
              {{ dept.managerInitials }}
            </div>
            <div>
              <p class="text-sm font-medium text-slate-700 leading-tight">{{ dept.manager }}</p>
              <p class="text-[11px] text-slate-400">Departman Yöneticisi</p>
            </div>
          </div>

          <!-- Sağ: buton -->
          <button
            @click="$router.push(dept.analyticsRoute)"
            class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all flex-shrink-0"
            :class="dept.isSales
              ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200'
              : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200'"
          >
            ML Analize Git
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>
          </button>
        </div>

        <div v-if="departments.length === 0" class="px-6 py-8 text-center text-slate-400 text-sm">
          Departman verisi yükleniyor...
        </div>
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
                    :key="emp.employee_code"
                    class="bg-white p-4 rounded-xl shadow-sm border border-rose-100 flex items-center justify-between hover:scale-[1.02] transition-transform duration-200 cursor-pointer"
                >
                    <div class="flex items-center gap-3">
                         <div class="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center font-bold text-slate-600 border border-slate-200 text-xs">
                            {{ initials(emp.employee_name) }}
                         </div>
                         <div>
                             <h4 class="font-bold text-slate-800 text-sm">{{ emp.employee_name || emp.employee_code }}</h4>
                             <p class="text-[10px] text-slate-400 font-medium uppercase tracking-wide">{{ emp.position || emp.department }} · {{ emp.team || emp.employee_code }}</p>
                         </div>
                    </div>
                    <div class="text-right">
                        <span class="inline-flex items-center px-2 py-1 rounded-md text-xs font-bold"
                          :class="emp.risk_level === 'High' ? 'bg-rose-100 text-rose-700 border border-rose-200' : 'bg-amber-100 text-amber-700 border border-amber-200'">
                            {{ emp.risk_level === 'High' ? 'Yüksek Risk' : 'Orta Risk' }}
                        </span>
                        <p class="text-[10px] mt-1 font-medium text-rose-600">
                            ML: %{{ emp.risk_score }}
                        </p>
                    </div>
                </div>
            </div>

            <!-- Decor -->
            <div class="absolute -bottom-12 -right-12 w-48 h-48 bg-rose-100/50 rounded-full blur-3xl z-0"></div>
        </div>

        <!-- Organizational Network Analysis (ONA) -->
        <div class="bg-white rounded-xl border border-gray-100 p-6 flex flex-col relative overflow-hidden shadow-sm hover:shadow-md transition-shadow">
            <div class="flex justify-between items-center mb-4 z-10">
                <div>
                    <h3 class="font-bold text-slate-800">Organizasyonel Ağ Analizi</h3>
                    <p class="text-xs text-slate-400">Departmanlar arası iletişim köprüleri</p>
                </div>
                <div class="flex items-center gap-2">
                    <span v-if="onaData" class="px-2 py-0.5 rounded text-[10px] font-bold"
                        :class="onaData.data_source === 'feedback'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-amber-50 text-amber-700 border border-amber-200'">
                        {{ onaData.data_source === 'feedback' ? 'Gerçek Veri' : 'Tahminsel' }}
                    </span>
                    <span class="px-2.5 py-1 bg-indigo-50 text-indigo-700 text-[10px] font-bold rounded border border-indigo-100">BETA</span>
                </div>
            </div>

            <!-- SVG Network Visualization -->
            <div class="flex-1 relative min-h-[260px] bg-slate-50/50 rounded-xl border border-slate-200 overflow-visible">
                <div class="absolute inset-0" style="background-image: radial-gradient(#cbd5e1 1px, transparent 1px); background-size: 20px 20px; opacity: 0.3;"></div>

                <svg v-if="onaData && onaData.nodes.length" class="absolute inset-0 w-full h-full" style="z-index:1;">
                    <!-- Kenarlar -->
                    <g v-for="edge in onaData.edges" :key="`${edge.source_id}-${edge.target_id}`">
                        <line
                            :x1="onaNodePos(edge.source_id).x + '%'"
                            :y1="onaNodePos(edge.source_id).y + '%'"
                            :x2="onaNodePos(edge.target_id).x + '%'"
                            :y2="onaNodePos(edge.target_id).y + '%'"
                            :stroke="edge.strength === 'strong' ? '#6366f1' : edge.strength === 'medium' ? '#94a3b8' : '#cbd5e1'"
                            :stroke-width="edge.strength === 'strong' ? 3 : edge.strength === 'medium' ? 2 : 1"
                            :stroke-dasharray="edge.strength === 'weak' ? '6' : 'none'"
                            stroke-linecap="round"
                            opacity="0.8"
                        />
                        <!-- Kenar etiketi -->
                        <text
                            :x="((onaNodePos(edge.source_id).x + onaNodePos(edge.target_id).x) / 2) + '%'"
                            :y="((onaNodePos(edge.source_id).y + onaNodePos(edge.target_id).y) / 2 - 2) + '%'"
                            text-anchor="middle"
                            class="text-[10px]"
                            fill="#64748b"
                            font-size="10"
                            font-weight="600"
                        >{{ edge.weight }} etkileşim</text>
                    </g>
                </svg>

                <!-- Node'lar -->
                <template v-if="onaData && onaData.nodes.length">
                    <div
                        v-for="node in onaData.nodes"
                        :key="node.id"
                        class="absolute flex flex-col items-center -translate-x-1/2 -translate-y-1/2 cursor-pointer group hover:z-50"
                        :style="`left:${onaNodePos(node.id).x}%; top:${onaNodePos(node.id).y}%; z-index:10;`"
                    >
                        <!-- Silo animasyonu -->
                        <div v-if="node.is_silo"
                            class="absolute rounded-full border-2 border-dashed border-rose-300 opacity-50 animate-ping"
                            :style="`width:${onaNodeSize(node) + 16}px; height:${onaNodeSize(node) + 16}px; margin:${-8}px;`">
                        </div>
                        <!-- Node dairesi -->
                        <div
                            class="rounded-full border-4 border-white shadow-xl flex flex-col items-center justify-center text-center transition-transform group-hover:scale-110"
                            :style="`width:${onaNodeSize(node)}px; height:${onaNodeSize(node)}px;`"
                            :class="node.is_silo
                                ? 'bg-rose-400 text-white'
                                : onaNodeColor(node)"
                        >
                            <span class="font-bold leading-tight px-1"
                                :style="`font-size:${onaNodeSize(node) > 60 ? 11 : 9}px;`">
                                {{ node.name.split(' ')[0] }}
                            </span>
                            <span v-if="onaNodeSize(node) > 55"
                                :style="`font-size:8px; opacity:0.8;`">
                                {{ node.is_silo ? 'Silo' : 'Merkez' }}
                            </span>
                        </div>
                        <!-- Tooltip — node pozisyonuna göre üstte veya altta açılır -->
                        <div
                            class="absolute bg-white border border-gray-200 rounded-lg shadow-xl p-2.5 text-xs w-44 hidden group-hover:block z-50 pointer-events-none"
                            :class="onaNodePos(node.id).y < 35 ? 'top-full mt-2' : 'bottom-full mb-2'"
                        >
                            <p class="font-bold text-slate-800 text-sm mb-1">{{ node.name }}</p>
                            <div class="space-y-0.5 text-slate-600">
                                <p>👥 {{ node.employee_count }} personel</p>
                                <p>📡 Merkezilik: <span class="font-semibold text-indigo-600">%{{ Math.round(node.centrality * 100) }}</span></p>
                                <p>🔗 {{ node.external_count }} çapraz bağlantı</p>
                                <p v-if="node.is_silo" class="text-rose-600 font-semibold">⚠️ Silo tespit edildi</p>
                            </div>
                        </div>
                    </div>
                </template>

                <!-- Yükleniyor -->
                <div v-if="!onaData" class="absolute inset-0 flex items-center justify-center text-slate-400 text-sm">
                    Ağ analizi yükleniyor...
                </div>

                <!-- Legend -->
                <div v-if="onaData" class="absolute bottom-3 left-3 bg-white/95 p-2.5 rounded-lg text-xs border border-gray-100 backdrop-blur-sm shadow-md z-20 max-w-[210px]">
                    <div v-if="onaData.summary.bridges.length" class="flex items-start gap-2 mb-1.5">
                        <div class="w-2 h-2 rounded-full bg-indigo-600 mt-0.5 flex-shrink-0"></div>
                        <span><span class="font-bold text-slate-700">Güçlü Bağ:</span> <span class="text-slate-500">{{ onaData.summary.bridges[0] }}</span></span>
                    </div>
                    <div v-if="onaData.summary.silos.length" class="flex items-start gap-2">
                        <div class="w-2 h-2 rounded-full bg-rose-400 mt-0.5 flex-shrink-0"></div>
                        <span><span class="font-bold text-slate-700">Silo:</span> <span class="text-slate-500">{{ onaData.summary.silos.join(', ') }}</span></span>
                    </div>
                    <div v-if="!onaData.summary.silos.length && !onaData.summary.bridges.length" class="text-slate-400">
                        Henüz yeterli veri yok
                    </div>
                </div>
            </div>

            <!-- Özet istatistikler -->
            <div v-if="onaData" class="mt-3 grid grid-cols-3 gap-2">
                <div class="bg-slate-50 rounded-lg p-2 text-center">
                    <p class="text-lg font-bold text-slate-800">{{ onaData.nodes.length }}</p>
                    <p class="text-[10px] text-slate-500">Departman</p>
                </div>
                <div class="bg-indigo-50 rounded-lg p-2 text-center">
                    <p class="text-lg font-bold text-indigo-700">{{ onaData.summary.cross_dept_interactions }}</p>
                    <p class="text-[10px] text-indigo-500">Çapraz Bağlantı</p>
                </div>
                <div class="bg-rose-50 rounded-lg p-2 text-center">
                    <p class="text-lg font-bold text-rose-700">{{ onaData.summary.silos.length }}</p>
                    <p class="text-[10px] text-rose-500">Silo Tespiti</p>
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
import { adminUploadApi } from '@/services/api/admin_upload.api'

const stats = ref({
  totalEmployees: '0',
  totalDepartments: '0',
  avgScore: '0',
  highRiskCount: '0'
})

const allEmployees = ref<any[]>([])
const departments = ref<any[]>([])
const mlFlightRisk = ref<any[]>([])   // ML tabanlı uçuş riski listesi
const onaData = ref<any>(null)        // ONA network verisi

// Her departmandan en fazla 2 yüksek riskli çalışan — toplam 4
const flightRiskEmployees = computed(() => {
    const high = mlFlightRisk.value.filter(e => e.risk_level === 'High')
    const byDept: Record<string, any[]> = {}
    for (const e of high) {
        const key = e.department ?? 'Diger'
        if (!byDept[key]) byDept[key] = []
        byDept[key].push(e)
    }
    const result: any[] = []
    let perDept = Math.max(1, Math.floor(4 / Math.max(1, Object.keys(byDept).length)))
    for (const deptEmps of Object.values(byDept)) {
        result.push(...deptEmps.slice(0, perDept))
    }
    // 4'e tamamla
    if (result.length < 4) {
        const extras = high.filter(e => !result.includes(e))
        result.push(...extras.slice(0, 4 - result.length))
    }
    return result.slice(0, 4)
})

const fetchDashboardData = async () => {
    // 1. Çalışanları yükle
    try {
        const empData = await employeeApi.getEmployees()
        const empArray: any[] = Array.isArray(empData) ? empData : (empData?.items ?? [])
        allEmployees.value = empArray
        stats.value.totalEmployees = empArray.length.toString()

        const deptNames = new Set<string>(empArray.map((e: any) => e.department?.name).filter(Boolean))
        stats.value.totalDepartments = deptNames.size.toString()

        const managerByDept: Record<string, any> = {}
        for (const emp of empArray) {
            if (emp.user?.role === 'department_manager' && emp.department?.name) {
                managerByDept[emp.department.name] = emp
            }
        }
        departments.value = Array.from(deptNames).map((name, index) => {
            const deptEmps = empArray.filter((e: any) => e.department?.name === name)
            const mgr = managerByDept[name as string]
            const mgrName = mgr?.user?.full_name ?? 'Yönetici Atanmadı'
            const mgrInitials = mgrName === 'Yönetici Atanmadı' ? 'YA' : initials(mgrName)
            const isSales = name.toLowerCase().includes('sat')
            const analyticsRoute = isSales ? '/manager/sales-analytics' : '/manager/kpi-ml-analysis'
            return { id: index + 1, name, manager: mgrName, managerInitials: mgrInitials, employees: deptEmps.length, isSales, analyticsRoute }
        })
    } catch (_err: unknown) {
        console.error('[Dashboard] employees error', _err)
    }

    // 2. Anket & bağlılık verisi
    try {
        const insightData = await dashboardApi.getInsights()
        const scoreKpi = insightData.kpis?.find((k: any) => k.title?.includes('Bağlılık') || k.title?.includes('Ortalama'))
        stats.value.avgScore = scoreKpi ? scoreKpi.value : '—'
    } catch (_err: unknown) {
        console.error('[Dashboard] insights error', _err)
    }

    // 3. ML uçuş riski
    try {
        const flightRiskData = await adminUploadApi.getFlightRisk()
        stats.value.highRiskCount = flightRiskData.high_risk_count.toString()
        mlFlightRisk.value = flightRiskData.employees
    } catch (_err: unknown) {
        console.error('[Dashboard] flight-risk error', _err)
        stats.value.highRiskCount = '0'
    }

    // 4. ONA network
    try {
        const resp = await adminUploadApi.getOrgNetwork()
        onaData.value = resp
    } catch (_err: unknown) {
        console.error('[Dashboard] org-network error', _err)
    }
}

// ── ONA helper fonksiyonlar ────────────────────────────────────────────────

/** Node'ların %cinsinden SVG koordinatları — daire düzeni */
function onaNodePos(nodeId: number): { x: number; y: number } {
    if (!onaData.value) return { x: 50, y: 50 }
    const nodes: any[] = onaData.value.nodes
    const idx = nodes.findIndex((n: any) => n.id === nodeId)
    const total = nodes.length
    if (total === 0) return { x: 50, y: 50 }
    if (total === 1) return { x: 50, y: 50 }
    // En merkezi node ortada, diğerleri çevresinde
    const sorted = [...nodes].sort((a: any, b: any) => b.centrality - a.centrality)
    const centerNode = sorted[0]
    if (nodeId === centerNode.id) return { x: 50, y: 50 }
    const others = sorted.slice(1)
    const oIdx = others.findIndex((n: any) => n.id === nodeId)
    const angle = (2 * Math.PI * oIdx) / others.length - Math.PI / 2
    const r = 32
    return {
        x: Math.round(50 + r * Math.cos(angle)),
        y: Math.round(50 + r * Math.sin(angle)),
    }
}

/** Node boyutu — centrality'e göre 48–80px */
function onaNodeSize(node: any): number {
    return Math.round(48 + node.centrality * 32)
}

/** Node rengi — en merkezi indigo, diğerleri emerald */
function onaNodeColor(node: any): string {
    if (!onaData.value) return 'bg-indigo-600 text-white'
    const sorted = [...onaData.value.nodes].sort((a: any, b: any) => b.centrality - a.centrality)
    return node.id === sorted[0]?.id
        ? 'bg-indigo-600 text-white'
        : 'bg-emerald-500 text-white'
}

function initials(name: string | undefined): string {
    if (!name) return '?'
    return name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()
}

onMounted(() => {
    fetchDashboardData()
})

</script>
