<template>
  <div class="space-y-6">
    <section class="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <div class="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
        <div class="max-w-2xl">
          <p class="text-xs font-semibold uppercase tracking-[0.22em] text-rose-500">Haftalik Nabiz</p>
          <h1 class="mt-3 text-3xl font-bold tracking-tight text-slate-900">Bu haftaki duygu ve motivasyon durumunu paylas.</h1>
          <p class="mt-3 text-sm leading-6 text-slate-600">
            Bu anket, haftalik enerji seviyeni, is yuku dengesini ve destek ihtiyaclarini anlamamiza yardimci olur.
            Yanitlarin NLP analizine girer ve kisisel gelisim sinyallerine donusur.
          </p>
        </div>

        <div class="rounded-2xl border border-rose-100 bg-rose-50 px-5 py-4 text-sm text-slate-700">
          <p class="font-semibold text-slate-900">Tahmini sure</p>
          <p class="mt-1">1 dakika</p>
          <p class="mt-4 font-semibold text-slate-900">Gizlilik</p>
          <p class="mt-1">Yanitlar analiz amacli kullanilir.</p>
        </div>
      </div>
    </section>

    <section class="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
      <div class="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <div class="flex items-center gap-3">
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-100 text-rose-600">
            <HeartIcon class="h-6 w-6" />
          </div>
          <div>
            <h2 class="text-xl font-bold text-slate-900">Nabiz anketi hazir</h2>
            <p class="text-sm text-slate-500">Sorular sayisal ve acik uclu olarak birlikte gonderilir.</p>
          </div>
        </div>

        <div class="mt-6 rounded-2xl border border-slate-100 bg-slate-50 p-5">
          <p class="text-sm leading-6 text-slate-700">
            Ankete basladiginda motivasyon, is yuku dengesi, destek seviyesi ve acik uclu geri bildirimlerini tek akista girebilirsin.
          </p>
        </div>

        <div class="mt-6 flex flex-wrap gap-3">
          <button
            @click="isWeeklyPulseModalOpen = true"
            class="inline-flex items-center justify-center rounded-2xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500"
          >
            Ankete Cevap Ver
          </button>
          <router-link
            to="/employee"
            class="inline-flex items-center justify-center rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            Personel Paneline Don
          </router-link>
        </div>
      </div>

      <aside class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Neler olculuyor?</p>
        <div class="mt-5 space-y-4">
          <div class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <p class="text-sm font-semibold text-slate-900">Motivasyon skoru</p>
            <p class="mt-1 text-xs leading-5 text-slate-500">Haftalik enerji ve baglilik durumu.</p>
          </div>
          <div class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <p class="text-sm font-semibold text-slate-900">Acik uclu sinyaller</p>
            <p class="mt-1 text-xs leading-5 text-slate-500">Blokajlar, basarilar ve iyilestirme onerileri.</p>
          </div>
          <div class="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <p class="text-sm font-semibold text-slate-900">Trend analizi</p>
            <p class="mt-1 text-xs leading-5 text-slate-500">Aylik derin analiz ve risk sinyalleri icin temel veri.</p>
          </div>
        </div>
      </aside>
    </section>

    <WeeklyPulseModal
      :is-open="isWeeklyPulseModalOpen"
      @close="isWeeklyPulseModalOpen = false"
      @submit="handlePulseSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { HeartIcon } from '@heroicons/vue/24/outline'
import WeeklyPulseModal from '@/components/dashboard/WeeklyPulseModal.vue'
import { employeeApi } from '@/services/api/employee.api'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const isWeeklyPulseModalOpen = ref(false)

const handlePulseSubmit = async (data: any) => {
  try {
    const payload = {
      employee_id: authStore.user?.id || 1,
      period_date: new Date().toISOString().split('T')[0],
      ...data,
    }
    await employeeApi.submitWeeklyPulse(payload)
    isWeeklyPulseModalOpen.value = false
    alert('Anketiniz basariyla kaydedildi. Motivasyon analiziniz guncellendi.')
  } catch (error: any) {
    if (error.response?.data?.detail) {
      alert(error.response.data.detail)
      return
    }
    alert('Anket gonderilirken bir hata olustu.')
  }
}
</script>
