<template>
  <div class="pb-10 space-y-8">

    <!-- Hero Banner ---------------------------------------------------------->
    <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-emerald-900 via-teal-800 to-emerald-900 shadow-xl">
      <div class="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 rounded-full bg-emerald-500/20 blur-3xl pointer-events-none"></div>
      <div class="absolute bottom-0 left-0 -ml-20 -mb-20 w-60 h-60 rounded-full bg-teal-500/20 blur-3xl pointer-events-none"></div>

      <div class="relative z-10 flex flex-col md:flex-row items-center justify-between p-8 gap-6">
        <div class="flex items-center gap-6 w-full md:w-auto">
          <div class="w-20 h-20 rounded-full ring-4 ring-white/10 shadow-2xl bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center text-2xl font-bold text-white shrink-0">
            {{ userInitials }}
          </div>
          <div>
            <h1 class="text-3xl font-bold text-white tracking-tight">
              Hoş Geldin,
              <span class="text-transparent bg-clip-text bg-gradient-to-r from-emerald-200 to-teal-200">{{ userName }}</span>
            </h1>
            <div class="flex flex-wrap items-center gap-3 mt-3 text-sm font-medium">
              <span class="bg-white/10 text-emerald-100 px-3 py-1 rounded-full border border-white/10">{{ employee?.position || 'Satış Uzmanı' }}</span>
              <span class="text-slate-300">Satış Departmanı</span>
            </div>
            <div v-if="badges.length" class="mt-4 flex flex-wrap gap-2">
              <BadgeMedal
                v-for="badge in badges.slice(0, 4)"
                :key="badge.id"
                :badge-type="badge.badge_type"
                :badge-level="badge.badge_level"
                size="xs"
                show-label
                :description="badge.badge_type"
              />
            </div>
          </div>
        </div>

        <div class="flex gap-3 w-full md:w-auto">
          <button class="flex-1 md:flex-none px-5 py-3 bg-white/5 border border-white/10 text-white text-sm font-medium rounded-xl hover:bg-white/10 transition-all backdrop-blur-sm">
            Rapor İndir
          </button>
          <router-link
            to="/feedback"
            class="flex-1 md:flex-none px-5 py-3 bg-emerald-500 text-white text-sm font-bold rounded-xl hover:bg-emerald-400 shadow-lg shadow-emerald-900/40 transition-all border-t border-white/20 text-center"
          >
            Feedback Ver
          </router-link>
        </div>
      </div>
    </div>

    <!-- KPI Stats Row --------------------------------------------------------->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-5">
      <div
        v-for="card in kpiCards"
        :key="card.title"
        class="rounded-2xl border bg-white p-6 shadow-sm hover:shadow-md transition-shadow"
        :class="card.borderClass"
      >
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em]" :class="card.labelClass">{{ card.title }}</p>
            <p class="mt-3 text-3xl font-bold text-slate-900">{{ card.value }}</p>
          </div>
          <span class="rounded-xl p-2.5" :class="card.iconBg">
            <component :is="card.icon" class="h-5 w-5" :class="card.iconColor" />
          </span>
        </div>
        <div class="mt-4 flex items-center gap-2 text-xs font-semibold" :class="card.changeClass">
          <span>{{ card.change }}</span>
          <span class="text-slate-400">{{ card.subtitle }}</span>
        </div>
      </div>
    </div>

    <!-- Main content grid ---------------------------------------------------->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

      <!-- Performance Trend (2/3 width) --------------------------------------->
      <div class="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
        <div class="flex justify-between items-center mb-6">
          <div>
            <h3 class="font-bold text-slate-800 text-lg">Satış Performans Trendi</h3>
            <p class="text-xs text-slate-500 mt-1">Son 6 haftalık satış KPI ortalaması</p>
          </div>
          <span class="rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">Canlı</span>
        </div>
        <div class="h-72">
          <LineChart
            :labels="trendLabels"
            :data="trendData"
            label="Satış Skoru"
            color="#10b981"
          />
        </div>
      </div>

      <!-- AI Sales Coach (1/3 width) ----------------------------------------->
      <div class="bg-slate-900 rounded-2xl p-6 text-white relative overflow-hidden shadow-xl border border-slate-800">
        <div class="absolute top-0 right-0 p-4 opacity-10">
          <TrophyIcon class="w-32 h-32 text-emerald-400 transform rotate-12" />
        </div>
        <div class="relative z-10">
          <div class="flex items-center gap-3 mb-6">
            <div class="p-2.5 bg-emerald-500/20 rounded-xl border border-emerald-500/30">
              <SparklesIcon class="w-6 h-6 text-emerald-300" />
            </div>
            <div>
              <h3 class="font-bold text-xl text-white">AI Satış Koçu</h3>
              <p class="text-xs text-slate-400">Kişisel Gelişim Tavsiyeleri</p>
            </div>
          </div>

          <div class="space-y-3">
            <div
              v-for="tip in aiTips"
              :key="tip.title"
              class="rounded-xl border border-white/10 bg-white/5 p-4"
            >
              <div class="flex items-center gap-2 mb-2">
                <span class="text-base">{{ tip.emoji }}</span>
                <p class="text-sm font-semibold text-white">{{ tip.title }}</p>
              </div>
              <p class="text-xs leading-5 text-slate-400">{{ tip.text }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Sales KPI Detail Cards ----------------------------------------------->
    <div>
      <div class="flex items-center justify-between gap-4 mb-4">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">KPI Detayı</p>
          <h3 class="mt-1 text-xl font-bold text-slate-900">Satış Metrikleri</h3>
        </div>
        <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">Bu hafta</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        <div
          v-for="metric in salesMetrics"
          :key="metric.label"
          class="rounded-2xl border bg-white p-5 shadow-sm hover:shadow-md transition-shadow"
          :class="metric.tone === 'good' ? 'border-emerald-100' : metric.tone === 'warn' ? 'border-amber-100' : 'border-rose-100'"
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{{ metric.code }}</p>
              <p class="mt-1 text-sm font-semibold text-slate-700">{{ metric.label }}</p>
            </div>
            <span
              class="rounded-full px-2.5 py-1 text-xs font-semibold"
              :class="metric.tone === 'good' ? 'bg-emerald-50 text-emerald-700' : metric.tone === 'warn' ? 'bg-amber-50 text-amber-700' : 'bg-rose-50 text-rose-700'"
            >
              {{ metric.status }}
            </span>
          </div>
          <p class="mt-4 text-2xl font-bold text-slate-900">{{ metric.value }}</p>
          <div class="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
            <div
              class="h-full rounded-full transition-all duration-500"
              :class="metric.tone === 'good' ? 'bg-emerald-500' : metric.tone === 'warn' ? 'bg-amber-500' : 'bg-rose-500'"
              :style="{ width: metric.barWidth }"
            ></div>
          </div>
          <p class="mt-2 text-xs text-slate-500">{{ metric.hint }}</p>
        </div>
      </div>
    </div>

    <!-- Weekly Pulse & Peer Praise ------------------------------------------->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

      <!-- Weekly Pulse -->
      <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex items-center justify-between gap-4 mb-5">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Haftalık</p>
            <h3 class="mt-1 text-lg font-bold text-slate-900">Nabız Anketi</h3>
          </div>
          <router-link
            to="/employee/pulse"
            class="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2 text-xs font-semibold text-emerald-700 hover:bg-emerald-100 transition-colors"
          >
            Ankete Git
          </router-link>
        </div>

        <div class="grid grid-cols-5 gap-2">
          <button
            v-for="mood in moods"
            :key="mood.emoji"
            class="flex flex-col items-center gap-2 rounded-xl border p-3 text-center text-xs font-semibold transition-all hover:scale-105"
            :class="selectedMood === mood.value ? 'border-emerald-300 bg-emerald-50 text-emerald-700' : 'border-slate-200 text-slate-500 hover:border-slate-300'"
            @click="selectedMood = mood.value"
          >
            <span class="text-2xl">{{ mood.emoji }}</span>
            <span>{{ mood.label }}</span>
          </button>
        </div>

        <div v-if="selectedMood" class="mt-4">
          <textarea
            v-model="pulseNote"
            rows="2"
            class="w-full rounded-xl border border-slate-200 p-3 text-sm text-slate-700 resize-none focus:outline-none focus:ring-2 focus:ring-emerald-300"
            placeholder="Bu haftaki satış notunuz… (isteğe bağlı)"
          ></textarea>
          <button
            class="mt-3 w-full rounded-xl bg-emerald-600 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 transition-colors"
            @click="submitPulse"
          >
            Gönder
          </button>
        </div>
      </div>

      <!-- Peer Praise --------------------------------------------------------->
      <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex items-center justify-between gap-4 mb-5">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Takım</p>
            <h3 class="mt-1 text-lg font-bold text-slate-900">Ekipten Gelen Övgüler</h3>
          </div>
          <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-500">{{ badges.length }} rozet</span>
        </div>

        <div v-if="badges.length" class="space-y-3">
          <div
            v-for="badge in badges.slice(0, 4)"
            :key="badge.id"
            class="flex items-center gap-4 rounded-xl border border-slate-100 bg-slate-50 p-4"
          >
            <BadgeMedal
              :badge-type="badge.badge_type"
              :badge-level="badge.badge_level"
              size="sm"
            />
            <div>
              <p class="text-sm font-semibold text-slate-900">{{ badgeLabel(badge.badge_type) }}</p>
              <p class="text-xs text-slate-500 mt-0.5">{{ badgeLevelLabel(badge.badge_level) }}</p>
            </div>
          </div>
        </div>

        <div v-else class="flex flex-col items-center justify-center py-8 text-center">
          <div class="text-4xl mb-3">🏅</div>
          <p class="text-sm font-semibold text-slate-700">Henüz rozet yok</p>
          <p class="text-xs text-slate-400 mt-1">Harika işler yapınca takımın seni ödüllendirecek!</p>
        </div>
      </div>
    </div>

    <!-- Focus Areas ---------------------------------------------------------->
    <div class="rounded-3xl border border-slate-800 bg-slate-900 p-8 shadow-lg">
      <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Bu Hafta Odak</p>
      <h3 class="mt-2 text-xl font-bold text-white">Satış Geliştirme Alanları</h3>
      <div class="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
          v-for="area in focusAreas"
          :key="area.title"
          class="rounded-2xl border border-white/10 bg-white/5 p-5"
        >
          <p class="text-base">{{ area.emoji }}</p>
          <p class="mt-3 text-sm font-semibold" :class="area.color">{{ area.title }}</p>
          <p class="mt-2 text-sm leading-6 text-slate-200">{{ area.text }}</p>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { SparklesIcon, TrophyIcon, CurrencyDollarIcon, ChartBarIcon, UserGroupIcon, ClockIcon } from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import { feedbackApi, type BadgeResponse } from '@/services/api/feedback.api'
import { employeeApi } from '@/services/api/employee.api'
import BadgeMedal from '@/components/common/BadgeMedal.vue'
import LineChart from '@/components/dashboard/LineChart.vue'

const authStore = useAuthStore()
const employee = ref<any>(null)
const badges = ref<BadgeResponse[]>([])

const userName = computed(() => authStore.user?.full_name || 'Satış Uzmanı')
const userInitials = computed(() =>
  userName.value.split(' ').map((n: string) => n[0]).join('').toUpperCase().substring(0, 2)
)

// ── KPI stat cards -----------------------------------------------------------

const kpiCards = computed(() => [
  {
    title: 'Hedef Gerçekleşme',
    value: '%87',
    change: '+5%',
    subtitle: 'geçen haftaya göre',
    icon: TrophyIcon,
    borderClass: 'border-emerald-100',
    labelClass: 'text-emerald-600',
    iconBg: 'bg-emerald-50',
    iconColor: 'text-emerald-600',
    changeClass: 'text-emerald-600',
  },
  {
    title: 'Pipeline Sağlığı',
    value: '%72',
    change: '-3%',
    subtitle: 'geçen haftaya göre',
    icon: ChartBarIcon,
    borderClass: 'border-amber-100',
    labelClass: 'text-amber-600',
    iconBg: 'bg-amber-50',
    iconColor: 'text-amber-600',
    changeClass: 'text-amber-600',
  },
  {
    title: 'CRM Kullanım',
    value: '%94',
    change: '+2%',
    subtitle: 'uyum oranı',
    icon: ClockIcon,
    borderClass: 'border-sky-100',
    labelClass: 'text-sky-600',
    iconBg: 'bg-sky-50',
    iconColor: 'text-sky-600',
    changeClass: 'text-sky-600',
  },
  {
    title: 'Müşteri Memnuniyeti',
    value: '4.3/5',
    change: '0.0',
    subtitle: 'değişim yok',
    icon: UserGroupIcon,
    borderClass: 'border-indigo-100',
    labelClass: 'text-indigo-600',
    iconBg: 'bg-indigo-50',
    iconColor: 'text-indigo-600',
    changeClass: 'text-slate-500',
  },
])

// ── Performance trend --------------------------------------------------------

const trendLabels = ['H1', 'H2', 'H3', 'H4', 'H5', 'H6']
const trendData = [72, 78, 75, 84, 82, 87]

// ── Sales metrics detail ----------------------------------------------------

const salesMetrics = [
  { code: 'SHGO', label: 'Satış Hedef Gerçekleşme Oranı', value: '%87', status: 'İyi', tone: 'good', barWidth: '87%', hint: 'Hedef: %90 üzeri' },
  { code: 'LMDO', label: 'Lead → Müşteri Dönüşüm Oranı', value: '%24', status: 'İzle', tone: 'warn', barWidth: '24%', hint: 'Sektör ortalaması: %30' },
  { code: 'TKO', label: 'Tekliften Kazanıma Dönüşüm', value: '%41', status: 'Hedefte', tone: 'good', barWidth: '41%', hint: 'Hedef: %40 üzeri' },
  { code: 'OSDS', label: 'Ort. Satış Döngüsü (gün)', value: '18 gün', status: 'Hızlı', tone: 'good', barWidth: '60%', hint: 'Takım ortalaması: 22 gün' },
  { code: 'CSAT', label: 'Müşteri Memnuniyeti', value: '4.3/5', status: 'İyi', tone: 'good', barWidth: '86%', hint: 'Hedef: 4.0 üzeri' },
  { code: 'CRMD', label: 'CRM Disiplin Metriği', value: '%94', status: 'Mükemmel', tone: 'good', barWidth: '94%', hint: 'Hedef: %85 üzeri' },
  { code: 'TDO', label: 'Takip Disiplini Oranı', value: '%68', status: 'Dikkat', tone: 'warn', barWidth: '68%', hint: 'Hedef: %80 üzeri' },
  { code: 'PSO', label: 'Pipeline Sağlık Oranı', value: '%72', status: 'Orta', tone: 'warn', barWidth: '72%', hint: 'Hedef: %80 üzeri' },
  { code: 'MS', label: 'Motivasyon Skoru', value: '7.2/10', status: 'İyi', tone: 'good', barWidth: '72%', hint: 'Geçen hafta: 6.8' },
]

// ── AI Tips ------------------------------------------------------------------

const aiTips = [
  {
    emoji: '🎯',
    title: 'Takip Disiplini',
    text: 'Tekliften 48 saat içinde takip yapılmayan 3 fırsat var. Bu haftaki en önemli aksiyon.',
  },
  {
    emoji: '📊',
    title: 'Pipeline Temizle',
    text: '60 gün hareketsiz 2 fırsat pipeline\'ı şişiriyor. Bunları kapat veya kategorize et.',
  },
  {
    emoji: '🤝',
    title: 'Cross-sell Fırsatı',
    text: 'Mevcut 4 müşterinizde ek ürün satış potansiyeli var. Hesap yöneticisiyle görüşün.',
  },
]

// ── Focus areas -------------------------------------------------------------

const focusAreas = [
  {
    emoji: '🔥',
    title: 'Bu Hafta Kazanacaklar',
    text: 'Tekliften 5+ gün geçmiş olan 4 fırsat için acil takip zamanı. Her gün geciken kapanış olasılığını düşürür.',
    color: 'text-rose-300',
  },
  {
    emoji: '📈',
    title: 'Pipeline Büyüt',
    text: 'Yeni lead hedefin haftada 8. Bu hafta 5 lead girişi yapıldı. Networking ve referans kanallarını aktif kullan.',
    color: 'text-amber-300',
  },
  {
    emoji: '🎓',
    title: 'Gelişim',
    text: 'Bu ay önerilen ürün eğitimlerinden %40 tamamlandı. Yeni ürün lansmanı öncesi sertifikayı bitir.',
    color: 'text-emerald-300',
  },
]

// ── Pulse -------------------------------------------------------------------

const moods = [
  { emoji: '😫', label: 'Yorgun', value: 1 },
  { emoji: '😐', label: 'Nötr', value: 2 },
  { emoji: '🙂', label: 'İyi', value: 3 },
  { emoji: '😄', label: 'Harika', value: 4 },
  { emoji: '🤩', label: 'Süper', value: 5 },
]
const selectedMood = ref<number | null>(null)
const pulseNote = ref('')

function submitPulse() {
  selectedMood.value = null
  pulseNote.value = ''
  alert('Nabız anketiniz kaydedildi. Teşekkürler!')
}

// ── Badge helpers -----------------------------------------------------------

const BADGE_LABELS: Record<string, string> = {
  team_player: 'Takım Oyuncusu',
  problem_solver: 'Problem Çözücü',
  communicator: 'İletişimci',
  speed_champion: 'Hız Şampiyonu',
  mentor: 'Mentor',
  innovator: 'İnovatör',
  reliable: 'Güvenilir',
}

const BADGE_LEVEL_LABELS: Record<string, string> = {
  bronze: 'Bronz',
  silver: 'Gümüş',
  gold: 'Altın',
}

function badgeLabel(t: string) {
  return BADGE_LABELS[t] || t
}

function badgeLevelLabel(l: string) {
  return BADGE_LEVEL_LABELS[l] || l
}

// ── Data loading ------------------------------------------------------------

async function loadBadges() {
  try {
    badges.value = await feedbackApi.getMyBadges()
  } catch {
    badges.value = []
  }
}

async function loadEmployee() {
  try {
    const employees = await employeeApi.getEmployees()
    const userId = authStore.user?.id
    employee.value = employees.find((e: any) => e.user_id === userId || e.user?.id === userId) || employees[0] || null
  } catch {
    employee.value = null
  }
}

onMounted(async () => {
  await Promise.all([loadBadges(), loadEmployee()])
})
</script>
