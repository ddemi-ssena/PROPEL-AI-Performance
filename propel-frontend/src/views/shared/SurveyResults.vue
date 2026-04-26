<template>
  <div class="pb-10">
    <div class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Anket Sonuçları</h1>
        <p class="text-slate-500 mt-1">Haftalık nabız anketleri ve NLP analiz detayları</p>
      </div>
      <div class="flex gap-3">
        <button @click="fetchResponses" class="p-2 text-slate-400 hover:text-indigo-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
          <ArrowPathIcon class="w-5 h-5" :class="{ 'animate-spin': isRefreshing }" />
        </button>
      </div>
    </div>

    <!-- Filters & Stats Summary -->
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
        <div class="lg:col-span-3 bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
            <div class="flex flex-wrap gap-4 items-center">
                <div class="flex-1 min-w-[200px] relative">
                    <MagnifyingGlassIcon class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input 
                        v-model="searchQuery" 
                        type="text" 
                        placeholder="Personel ara..." 
                        class="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
                    />
                </div>
                <select v-model="filterType" class="bg-slate-50 border border-slate-200 rounded-xl py-2 px-4 text-sm focus:ring-2 focus:ring-indigo-500 outline-none">
                    <option value="all">Tüm Anketler</option>
                    <option value="weekly_pulse">Haftalık Nabız</option>
                    <option value="motivation">Motivasyon</option>
                </select>
            </div>
        </div>
        <div class="bg-indigo-600 p-6 rounded-2xl shadow-lg shadow-indigo-200 text-white flex flex-col justify-center">
            <p class="text-indigo-100 text-xs font-bold uppercase tracking-wider mb-1">Toplam Yanıt</p>
            <h3 class="text-3xl font-bold">{{ filteredResponses.length }}</h3>
        </div>
    </div>

    <!-- Results Table -->
    <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <table class="w-full text-left">
            <thead class="bg-slate-50 border-b border-slate-200">
                <tr>
                    <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Tarih</th>
                    <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Personel</th>
                    <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-center">MS (Bağlılık)</th>
                    <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-center">MTE (Duygu)</th>
                    <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-center">ARS (Risk)</th>
                    <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Detay</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
                <tr v-for="res in filteredResponses" :key="res.id" class="hover:bg-slate-50 transition-colors group">
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                        {{ new Date(res.period_date).toLocaleDateString('tr-TR') }}
                    </td>
                    <td class="px-6 py-4">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-xs font-bold">
                                {{ res.employee.full_name?.substring(0,2).toUpperCase() }}
                            </div>
                            <div>
                                <p class="text-sm font-bold text-slate-800">{{ res.employee.full_name }}</p>
                                <p class="text-[10px] text-slate-400 uppercase font-medium">{{ res.employee.position }}</p>
                            </div>
                        </div>
                    </td>
                    <td class="px-6 py-4 text-center">
                        <span :class="getScoreClass(res.score)" class="px-2.5 py-1 rounded-full text-xs font-bold border">
                            {{ res.score }}
                        </span>
                    </td>
                    <td class="px-6 py-4 text-center">
                        <div v-if="res.mte_score !== null && res.mte_score !== undefined" class="flex flex-col items-center">
                            <span :class="getMTEClass(res.mte_score)" class="text-sm font-bold">
                                {{ res.mte_score > 0 ? '+' : '' }}{{ res.mte_score.toFixed(3) }}
                            </span>
                            <div class="w-16 h-1 bg-slate-100 rounded-full mt-1 overflow-hidden">
                                <div :class="getMTEBarClass(res.mte_score)" :style="{ width: Math.abs(res.mte_score * 100) + '%' }"></div>
                            </div>
                        </div>
                        <span v-else class="text-slate-300 text-xs">-</span>
                    </td>
                    <td class="px-6 py-4 text-center">
                        <span v-if="res.ars_score !== null" :class="getRiskLabelClass(res.ars_score)" class="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase border">
                            {{ getRiskLabel(res.ars_score) }}
                        </span>
                        <span v-else class="text-slate-300 text-xs">-</span>
                    </td>
                    <td class="px-6 py-4">
                        <button @click="showDetail(res)" class="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all">
                            <EyeIcon class="w-5 h-5" />
                        </button>
                    </td>
                </tr>
            </tbody>
        </table>
        
        <div v-if="isLoading" class="p-10 text-center">
            <div class="animate-spin w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p class="text-slate-500 text-sm">Veriler yükleniyor...</p>
        </div>
        
        <div v-if="!isLoading && filteredResponses.length === 0" class="p-20 text-center">
            <div class="mb-4 text-slate-200">
                <DocumentTextIcon class="w-16 h-16 mx-auto" />
            </div>
            <h3 class="text-lg font-bold text-slate-800">Yanıt Bulunamadı</h3>
            <p class="text-slate-500 text-sm mt-1">Arama kriterlerinize uygun anket yanıtı bulunmuyor.</p>
        </div>
    </div>

    <!-- Detail Modal -->
    <div v-if="selectedSurvey" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
        <div class="bg-white w-full max-w-2xl rounded-3xl shadow-2xl overflow-hidden border border-slate-200 animate-in fade-in zoom-in duration-200">
            <div class="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                <div class="flex items-center gap-4">
                    <div class="w-12 h-12 rounded-2xl bg-indigo-600 text-white flex items-center justify-center text-lg font-bold shadow-lg shadow-indigo-200">
                        {{ selectedSurvey.employee.full_name?.substring(0,2).toUpperCase() }}
                    </div>
                    <div>
                        <h3 class="font-bold text-slate-900">{{ selectedSurvey.employee.full_name }}</h3>
                        <p class="text-xs text-slate-500">{{ new Date(selectedSurvey.period_date).toLocaleDateString('tr-TR') }} • {{ selectedSurvey.employee.position }}</p>
                    </div>
                </div>
                <button @click="selectedSurvey = null" class="p-2 hover:bg-slate-200 rounded-full transition-colors text-slate-400">
                    <XMarkIcon class="w-6 h-6" />
                </button>
            </div>
            
            <div class="p-8 space-y-8 max-h-[70vh] overflow-y-auto">
                <!-- Scores Row -->
                <div class="grid grid-cols-3 gap-4">
                    <div class="p-4 bg-slate-50 rounded-2xl border border-slate-100 text-center">
                        <p class="text-[10px] font-bold text-slate-400 uppercase mb-1">Bağlılık (MS)</p>
                        <p class="text-2xl font-bold text-indigo-600">{{ selectedSurvey.score }}</p>
                    </div>
                    <div class="p-4 bg-slate-50 rounded-2xl border border-slate-100 text-center">
                        <p class="text-[10px] font-bold text-slate-400 uppercase mb-1">Duygu Trendi (MTE)</p>
                        <p class="text-2xl font-bold text-blue-600">{{ selectedSurvey.mte_score?.toFixed(3) || '0.000' }}</p>
                    </div>
                    <div class="p-4 bg-slate-50 rounded-2xl border border-slate-100 text-center">
                        <p class="text-[10px] font-bold text-slate-400 uppercase mb-1">Ayrılma Riski (ARS)</p>
                        <p class="text-2xl font-bold text-rose-600">{{ selectedSurvey.ars_score?.toFixed(3) || '0.000' }}</p>
                    </div>
                </div>

                <!-- Open Ended Questions -->
                <div v-if="selectedSurvey.raw_data" class="space-y-6">
                    <div>
                        <h4 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                             <div class="w-1 h-3 bg-indigo-500 rounded"></div>
                             1. Bu haftaki en büyük zorluk neydi?
                        </h4>
                        <div class="p-4 bg-indigo-50/50 rounded-xl border border-indigo-100 text-sm text-slate-700 leading-relaxed italic">
                            "{{ selectedSurvey.raw_data.q4 }}"
                        </div>
                    </div>
                    <div>
                        <h4 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                             <div class="w-1 h-3 bg-indigo-500 rounded"></div>
                             2. En önemli başarınız nedir?
                        </h4>
                        <div class="p-4 bg-emerald-50/50 rounded-xl border border-emerald-100 text-sm text-slate-700 leading-relaxed italic">
                            "{{ selectedSurvey.raw_data.q5 }}"
                        </div>
                    </div>
                    <div>
                        <h4 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                             <div class="w-1 h-3 bg-indigo-500 rounded"></div>
                             3. Herhangi bir öneri/feedback?
                        </h4>
                        <div class="p-4 bg-amber-50/50 rounded-xl border border-amber-100 text-sm text-slate-700 leading-relaxed italic">
                            "{{ selectedSurvey.raw_data.q6 }}"
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="p-6 bg-slate-50 border-t border-slate-100 text-center">
                <button @click="selectedSurvey = null" class="px-8 py-3 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 shadow-lg shadow-indigo-200 transition-all">
                    Kapat
                </button>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { 
    ArrowPathIcon, 
    MagnifyingGlassIcon, 
    EyeIcon, 
    XMarkIcon,
    DocumentTextIcon
} from '@heroicons/vue/24/outline'
import { surveyApi, type SurveyResponse } from '@/services/api/survey.api'

const responses = ref<SurveyResponse[]>([])
const isLoading = ref(true)
const isRefreshing = ref(false)
const searchQuery = ref('')
const filterType = ref('all')
const selectedSurvey = ref<SurveyResponse | null>(null)

const fetchResponses = async () => {
    isLoading.value = true
    isRefreshing.value = true
    try {
        const data = await surveyApi.getResponses()
        responses.value = data.sort((a,b) => new Date(b.period_date).getTime() - new Date(a.period_date).getTime())
    } catch (e) {
        console.error("Survey fetch error:", e)
    } finally {
        isLoading.value = false
        isRefreshing.value = false
    }
}

onMounted(() => {
    fetchResponses()
})

const filteredResponses = computed(() => {
    return responses.value.filter(res => {
        const matchesSearch = res.employee.full_name?.toLowerCase().includes(searchQuery.value.toLowerCase()) || 
                             res.employee.position?.toLowerCase().includes(searchQuery.value.toLowerCase())
        const matchesType = filterType.value === 'all' || res.survey_type === filterType.value
        return matchesSearch && matchesType
    })
})

const showDetail = (survey: SurveyResponse) => {
    selectedSurvey.value = survey
}

const getScoreClass = (score: number) => {
    if (score >= 4.0) return 'bg-emerald-50 text-emerald-700 border-emerald-100'
    if (score >= 3.0) return 'bg-amber-50 text-amber-700 border-amber-100'
    return 'bg-rose-50 text-rose-700 border-rose-100'
}

const getMTEClass = (score: number | undefined) => {
    if (score === undefined) return 'text-slate-500'
    if (score > 0.1) return 'text-emerald-600'
    if (score < -0.1) return 'text-rose-600'
    return 'text-slate-500'
}

const getMTEBarClass = (score: number | undefined) => {
    if (score === undefined) return 'h-full bg-slate-100'
    if (score > 0.1) return 'h-full bg-emerald-500'
    if (score < -0.1) return 'h-full bg-rose-500'
    return 'h-full bg-slate-300'
}

const getRiskLabel = (score: number | undefined) => {
    if (score === undefined) return 'Belirsiz'
    if (score >= 0.6) return 'Yüksek Risk'
    if (score >= 0.2) return 'Orta Risk'
    return 'Düşük Risk'
}

const getRiskLabelClass = (score: number | undefined) => {
    if (score === undefined) return 'bg-slate-50 text-slate-400 border-slate-100'
    if (score >= 0.6) return 'bg-rose-50 text-rose-700 border-rose-100'
    if (score >= 0.2) return 'bg-amber-50 text-amber-700 border-amber-100'
    return 'bg-emerald-50 text-emerald-700 border-emerald-100'
}
</script>
