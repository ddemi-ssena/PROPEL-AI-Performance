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
                <select v-model="filterDept" class="bg-slate-50 border border-slate-200 rounded-xl py-2 px-4 text-sm focus:ring-2 focus:ring-indigo-500 outline-none">
                    <option value="all">Tüm Departmanlar</option>
                    <option value="satis">Satış</option>
                    <option value="yazilim">Yazılım</option>
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

    <!-- Gemini Panel (sağ alt köşe) -->
    <div class="fixed bottom-6 right-6 z-40 w-96 max-h-[80vh] flex flex-col">
      <!-- Kapalı hali: sadece buton -->
      <div v-if="!geminiOpen" class="self-end">
        <button @click="openGemini"
          class="flex items-center gap-2 bg-violet-600 hover:bg-violet-700 text-white font-semibold px-4 py-3 rounded-2xl shadow-xl shadow-violet-300 transition-all">
          <SparklesIcon class="w-5 h-5" />
          Gemini ile Yorumla
        </button>
      </div>

      <!-- Açık panel -->
      <div v-else class="bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden max-h-[80vh]">
        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-violet-600 to-indigo-600 flex-shrink-0">
          <div class="flex items-center gap-2">
            <SparklesIcon class="w-5 h-5 text-white" />
            <span class="text-white font-semibold text-sm">Gemini AI Yorumu</span>
            <span class="text-xs bg-white/20 text-white px-2 py-0.5 rounded-full">{{ geminiDeptLabel }}</span>
          </div>
          <div class="flex items-center gap-1">
            <button @click="openGemini" :disabled="geminiLoading" title="Yenile"
              class="p-1.5 hover:bg-white/20 rounded-lg transition-colors text-white disabled:opacity-40">
              <ArrowPathIcon class="w-4 h-4" :class="{'animate-spin': geminiLoading}" />
            </button>
            <button @click="geminiOpen = false"
              class="p-1.5 hover:bg-white/20 rounded-lg transition-colors text-white">
              <XMarkIcon class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Stats bar -->
        <div v-if="geminiStats" class="flex gap-px bg-slate-100 flex-shrink-0">
          <div class="flex-1 bg-white px-3 py-2 text-center">
            <p class="text-[10px] text-slate-400 uppercase font-bold">Yanıt</p>
            <p class="text-sm font-bold text-slate-800">{{ geminiStats.total }}</p>
          </div>
          <div class="flex-1 bg-white px-3 py-2 text-center">
            <p class="text-[10px] text-slate-400 uppercase font-bold">Ort. MS</p>
            <p class="text-sm font-bold" :class="geminiStats.avg_ms >= 3.5 ? 'text-emerald-600' : 'text-amber-500'">{{ geminiStats.avg_ms }}</p>
          </div>
          <div class="flex-1 bg-white px-3 py-2 text-center">
            <p class="text-[10px] text-slate-400 uppercase font-bold">Yüksek Risk</p>
            <p class="text-sm font-bold text-red-600">{{ geminiStats.high_risk }}</p>
          </div>
          <div class="flex-1 bg-white px-3 py-2 text-center">
            <p class="text-[10px] text-slate-400 uppercase font-bold">MTE</p>
            <p class="text-sm font-bold" :class="geminiStats.avg_mte >= 0 ? 'text-emerald-600' : 'text-red-500'">
              {{ geminiStats.avg_mte > 0 ? '+' : '' }}{{ geminiStats.avg_mte }}
            </p>
          </div>
        </div>

        <!-- İçerik -->
        <div class="flex-1 overflow-y-auto p-4">
          <!-- Yükleniyor -->
          <div v-if="geminiLoading" class="flex flex-col items-center justify-center py-10 gap-3">
            <div class="w-8 h-8 border-4 border-violet-200 border-t-violet-600 rounded-full animate-spin"></div>
            <p class="text-sm text-slate-400">Gemini analiz ediyor...</p>
          </div>

          <!-- Narratif -->
          <div v-else-if="geminiNarrative" class="space-y-4">
            <div v-for="(sec, i) in geminiSections" :key="i">
              <h4 v-if="sec.title" class="text-xs font-bold text-violet-700 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                <span class="w-4 h-4 rounded-full bg-violet-100 text-violet-600 text-[10px] flex items-center justify-center font-bold">{{ i + 1 }}</span>
                {{ sec.title }}
              </h4>
              <div class="text-xs text-slate-600 leading-relaxed whitespace-pre-wrap bg-slate-50 rounded-xl p-3 border border-slate-100">{{ sec.body }}</div>
            </div>
          </div>

          <!-- Hata -->
          <div v-else class="text-center py-8 text-slate-400 text-sm">
            Yorum alınamadı. Tekrar deneyin.
          </div>
        </div>
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
import { ref, onMounted, computed, watch } from 'vue'
import {
    ArrowPathIcon,
    MagnifyingGlassIcon,
    EyeIcon,
    XMarkIcon,
    DocumentTextIcon,
    SparklesIcon,
} from '@heroicons/vue/24/outline'
import { apiClient } from '@/services/api/client'
import { surveyApi, type SurveyResponse } from '@/services/api/survey.api'

const responses = ref<SurveyResponse[]>([])
const isLoading = ref(true)
const isRefreshing = ref(false)
const searchQuery = ref('')
const filterType = ref('all')
const filterDept = ref('all')
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

const isSalesEmployee = (position: string | undefined) =>
    (position || '').toLowerCase().includes('sales')

const filteredResponses = computed(() => {
    return responses.value.filter(res => {
        const matchesSearch = res.employee.full_name?.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                             res.employee.position?.toLowerCase().includes(searchQuery.value.toLowerCase())
        const matchesDept = filterDept.value === 'all' ||
            (filterDept.value === 'satis' && isSalesEmployee(res.employee.position)) ||
            (filterDept.value === 'yazilim' && !isSalesEmployee(res.employee.position))
        return matchesSearch && matchesDept
    })
})

// ── Gemini Panel ──────────────────────────────────────────────────────────
const geminiOpen = ref(false)
const geminiLoading = ref(false)
const geminiNarrative = ref<string | null>(null)
const geminiStats = ref<any>(null)

const geminiDeptLabel = computed(() => ({
  all: 'Tüm', satis: 'Satış', yazilim: 'Yazılım'
}[filterDept.value] || 'Tüm'))

const geminiSections = computed(() => {
  if (!geminiNarrative.value) return []
  const sections: { title: string; body: string }[] = []
  let current = { title: '', body: '' }
  for (const line of geminiNarrative.value.split('\n')) {
    if (line.startsWith('###')) {
      if (current.body.trim()) sections.push({ ...current })
      current = { title: line.replace(/^#+\s*/, '').trim(), body: '' }
    } else {
      current.body += (current.body ? '\n' : '') + line
    }
  }
  if (current.body.trim()) sections.push(current)
  return sections
})

const openGemini = async () => {
  geminiOpen.value = true
  geminiLoading.value = true
  geminiNarrative.value = null

  // Sayfadaki filtrelenmiş veriden istatistik ve yorumları derle
  const visible = filteredResponses.value
  const scores  = visible.map((r: any) => r.score).filter(Boolean)
  const mteVals = visible.map((r: any) => r.mte_score).filter((v: any) => v != null)
  const arsVals = visible.map((r: any) => r.ars_score).filter((v: any) => v != null)

  const avg = (arr: number[]) => arr.length ? Math.round(arr.reduce((a, b) => a + b, 0) / arr.length * 1000) / 1000 : 0

  const stats = {
    total: visible.length,
    avg_ms:  avg(scores),
    avg_mte: avg(mteVals),
    avg_ars: avg(arsVals),
    high_risk: arsVals.filter((a: number) => a >= 0.6).length,
    med_risk:  arsVals.filter((a: number) => a >= 0.2 && a < 0.6).length,
    low_risk:  arsVals.filter((a: number) => a < 0.2).length,
    neg_mte: mteVals.filter((m: number) => m < -0.1).length,
    pos_mte: mteVals.filter((m: number) => m > 0.1).length,
  }

  // Her çalışanın gerçek açık uçlu yanıtlarını topla
  const sample_comments = visible.slice(0, 20).map((r: any) => ({
    name: r.employee?.full_name || '?',
    score: r.score,
    mte: r.mte_score,
    ars: r.ars_score,
    challenge:  r.raw_data?.q4 || null,
    success:    r.raw_data?.q5 || null,
    suggestion: r.raw_data?.q6 || null,
  }))

  const deptLabels: Record<string, string> = { all: 'Tüm Departmanlar', satis: 'Satış Departmanı', yazilim: 'Yazılım Departmanı' }
  const dept_label = deptLabels[filterDept.value] || 'Tüm Departmanlar'

  geminiStats.value = stats

  try {
    const { data } = await apiClient.post('/surveys/analytics/gemini-insights', {
      stats,
      sample_comments,
      dept_label,
    })
    geminiNarrative.value = data.narrative || null
  } catch (e) {
    console.error('[Gemini Survey]', e)
  } finally {
    geminiLoading.value = false
  }
}

// Departman filtresi değişince açık panel varsa yenile
watch(filterDept, () => { if (geminiOpen.value) openGemini() })

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
