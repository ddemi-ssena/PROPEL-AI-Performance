<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 text-left">
    <!-- Backdrop -->
    <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" @click="closeModal"></div>

    <!-- Modal Panel -->
    <div class="relative w-full max-w-3xl bg-white rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] sm:max-h-[85vh] animate-in fade-in zoom-in duration-200">
      
      <!-- Header -->
      <div class="flex-shrink-0 bg-slate-900 px-6 py-5 flex items-center justify-between border-b border-white/10 relative overflow-hidden">
        <!-- Decoration -->
        <div class="absolute top-0 right-0 -mr-10 -mt-10 w-40 h-40 rounded-full bg-indigo-500/20 blur-3xl pointer-events-none"></div>
        <div class="relative z-10">
          <h2 class="text-xl font-bold text-white flex items-center gap-2">
            <HeartIcon class="w-6 h-6 text-rose-500" />
            Haftalık Nabız Anketi
          </h2>
          <p class="text-xs text-indigo-200 mt-1 font-medium bg-indigo-500/10 inline-block px-2 py-1 rounded-md mt-2 flex items-center gap-1.5 border border-indigo-500/20">
            <UserIcon class="w-3.5 h-3.5" />
            Yanıtlarınız kişisel motivasyon analiziniz için AI tarafından değerlendirilmekte ve yöneticinize sunulmaktadır.
          </p>
        </div>
        <button @click="closeModal" class="relative z-10 text-slate-400 hover:text-white transition-colors p-2 rounded-xl hover:bg-white/10">
          <XMarkIcon class="w-6 h-6" />
        </button>
      </div>

      <!-- Body / Form -->
      <div class="flex-1 overflow-y-auto p-6 bg-slate-50 relative document-scroll">
        <!-- Progress Indicator -->
        <div class="mb-6 flex items-center justify-between">
          <span class="text-sm font-bold text-slate-600">Doldurulan: <span :class="{'text-emerald-500': canSubmit, 'text-amber-500': !canSubmit}">{{ answeredCount }} / 6</span></span>
          <span class="text-xs font-semibold px-2.5 py-1 rounded-full text-white shadow-sm" :class="canSubmit ? 'bg-emerald-500' : 'bg-slate-300'">
            {{ canSubmit ? 'Göndermeye Hazır' : 'En az 5 soru yanıtlanmalı' }}
          </span>
        </div>

        <div class="space-y-8">
          
          <!-- Bölüm 1: Sayısal Değerlendirme -->
          <section>
            <div class="mb-4">
              <h3 class="text-sm uppercase tracking-wider font-bold text-indigo-500 flex items-center gap-2">
                <span class="w-6 h-6 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-700">1</span>
                Sayısal Değerlendirme
              </h3>
              <p class="text-xs text-slate-500 font-medium mt-1">Motivasyon Skoru (MS) için kullanılır.</p>
            </div>

            <div class="space-y-4">
              <!-- Q1 -->
              <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm transition-all focus-within:ring-2 focus-within:ring-indigo-500/20 focus-within:border-indigo-300">
                <label class="block text-sm font-bold text-slate-800 mb-3">Bu hafta genel motivasyon seviyenizi nasıl değerlendirirsiniz?</label>
                <div class="flex gap-2 sm:gap-4 justify-between">
                  <span class="text-[10px] font-bold text-slate-400 mt-2 hidden sm:block w-16 text-center">Çok Düşük</span>
                  <div class="flex flex-1 justify-between gap-2 max-w-sm mx-auto">
                    <button v-for="n in 5" :key="'q1-'+n" @click="form.q1 = n" type="button" 
                      :class="['w-10 h-10 sm:w-12 sm:h-12 rounded-xl border-2 flex flex-col items-center justify-center font-bold text-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500', 
                      form.q1 === n ? 'border-indigo-500 bg-indigo-50 text-indigo-700 scale-110 shadow-md' : 'border-slate-200 bg-slate-50 text-slate-500 hover:border-indigo-300 hover:bg-slate-100']">
                      {{ n }}
                    </button>
                  </div>
                  <span class="text-[10px] font-bold text-slate-400 mt-2 hidden sm:block w-16 text-center">Çok İyi</span>
                </div>
              </div>

              <!-- Q2 -->
              <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm transition-all focus-within:ring-2 focus-within:ring-indigo-500/20 focus-within:border-indigo-300">
                <label class="block text-sm font-bold text-slate-800 mb-3">Bu haftaki iş yükünüzün dengeli olduğunu düşünüyor musunuz?</label>
                <div class="flex gap-2 sm:gap-4 justify-between">
                  <span class="text-[10px] font-bold text-slate-400 mt-2 hidden sm:block w-20 text-center">Hiç Dengeli Değil</span>
                  <div class="flex flex-1 justify-between gap-2 max-w-sm mx-auto">
                    <button v-for="n in 5" :key="'q2-'+n" @click="form.q2 = n" type="button" 
                      :class="['w-10 h-10 sm:w-12 sm:h-12 rounded-xl border-2 flex flex-col items-center justify-center font-bold text-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500', 
                      form.q2 === n ? 'border-indigo-500 bg-indigo-50 text-indigo-700 scale-110 shadow-md' : 'border-slate-200 bg-slate-50 text-slate-500 hover:border-indigo-300 hover:bg-slate-100']">
                      {{ n }}
                    </button>
                  </div>
                  <span class="text-[10px] font-bold text-slate-400 mt-2 hidden sm:block w-20 text-center">Çok Dengeli</span>
                </div>
              </div>

              <!-- Q3 -->
              <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm transition-all focus-within:ring-2 focus-within:ring-indigo-500/20 focus-within:border-indigo-300">
                <label class="block text-sm font-bold text-slate-800 mb-3">İhtiyaç duyduğunuzda ekip arkadaşlarınızdan veya yöneticinizden yeterli desteği alabildiniz mi?</label>
                <div class="flex gap-2 sm:gap-4 justify-between">
                  <span class="text-[10px] font-bold text-slate-400 mt-2 hidden sm:block w-20 text-center">Hiç Alamadım</span>
                  <div class="flex flex-1 justify-between gap-2 max-w-sm mx-auto">
                    <button v-for="n in 5" :key="'q3-'+n" @click="form.q3 = n" type="button" 
                      :class="['w-10 h-10 sm:w-12 sm:h-12 rounded-xl border-2 flex flex-col items-center justify-center font-bold text-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500', 
                      form.q3 === n ? 'border-indigo-500 bg-indigo-50 text-indigo-700 scale-110 shadow-md' : 'border-slate-200 bg-slate-50 text-slate-500 hover:border-indigo-300 hover:bg-slate-100']">
                      {{ n }}
                    </button>
                  </div>
                  <span class="text-[10px] font-bold text-slate-400 mt-2 hidden sm:block w-20 text-center">Tamamen Aldım</span>
                </div>
              </div>
            </div>
          </section>

          <!-- Bölüm 2: Açık Uçlu Sorular -->
          <section>
            <div class="mb-4">
              <h3 class="text-sm uppercase tracking-wider font-bold text-emerald-600 flex items-center gap-2">
                <span class="w-6 h-6 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-700">2</span>
                Açık Uçlu NLP Değerlendirmesi
              </h3>
              <p class="text-xs text-slate-500 font-medium mt-1">AI modelleriyle analiz edilerek Motivasyon Trendi belirlenir.</p>
            </div>

            <div class="space-y-4">
              <!-- Q4 -->
              <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm group focus-within:ring-2 focus-within:ring-emerald-500/20 focus-within:border-emerald-300 transition-all">
                <label for="q4" class="block text-sm font-bold text-slate-800 mb-2">Zorluk Analizi</label>
                <p class="text-xs text-slate-500 mb-3">Bu hafta sizi teknik veya operasyonel olarak en çok zorlayan engel neydi? Lütfen kısaca açıklayınız.</p>
                <textarea id="q4" v-model="form.q4" rows="2" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm focus:bg-white focus:outline-none focus:ring-0 focus:border-emerald-400 transition-colors resize-none placeholder-slate-400 text-slate-700" placeholder="Örn: X API entegrasyonu belgelendirme eksikliği yüzünden vakit aldı..."></textarea>
              </div>

              <!-- Q5 -->
              <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm group focus-within:ring-2 focus-within:ring-emerald-500/20 focus-within:border-emerald-300 transition-all">
                <label for="q5" class="block text-sm font-bold text-slate-800 mb-2">Başarı ve Tatmin</label>
                <p class="text-xs text-slate-500 mb-3">Bu hafta kendinizi en başarılı veya verimli hissettiğiniz an/görev neydi?</p>
                <textarea id="q5" v-model="form.q5" rows="2" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm focus:bg-white focus:outline-none focus:ring-0 focus:border-emerald-400 transition-colors resize-none placeholder-slate-400 text-slate-700" placeholder="Örn: Refactoring işlemini bitirip testleri %100 geçirdiğim an..."></textarea>
              </div>

              <!-- Q6 -->
              <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm group focus-within:ring-2 focus-within:ring-emerald-500/20 focus-within:border-emerald-300 transition-all">
                <label for="q6" class="block text-sm font-bold text-slate-800 mb-2">Öneri ve Geri Bildirim</label>
                <p class="text-xs text-slate-500 mb-3">Önümüzdeki hafta çalışma sürecinizi iyileştirmek için tek bir şeyi değiştirebilseydiniz bu ne olurdu?</p>
                <textarea id="q6" v-model="form.q6" rows="2" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm focus:bg-white focus:outline-none focus:ring-0 focus:border-emerald-400 transition-colors resize-none placeholder-slate-400 text-slate-700" placeholder="Örn: Toplantıların daha kısa ve odaklı olması..."></textarea>
              </div>
            </div>
          </section>

        </div>
      </div>

      <!-- Footer -->
      <div class="flex-shrink-0 bg-white px-6 py-4 border-t border-slate-100 flex items-center justify-between">
        <button type="button" @click="closeModal" class="px-5 py-2.5 text-sm font-bold text-slate-500 hover:bg-slate-100 rounded-xl transition-colors">
          İptal Et
        </button>
        <button type="button" @click="submit" :disabled="!canSubmit || isSubmitting" 
          :class="['px-6 py-2.5 text-sm font-bold rounded-xl transition-all shadow-md flex items-center gap-2', 
          canSubmit && !isSubmitting ? 'bg-indigo-600 text-white hover:bg-indigo-500 hover:shadow-indigo-500/25 cursor-pointer active:scale-95' : 'bg-slate-200 text-slate-400 shadow-none cursor-not-allowed']">
          <span v-if="isSubmitting" class="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></span>
          {{ isSubmitting ? 'Gönderiliyor...' : 'Yanıtları Gönder' }}
        </button>
      </div>
      
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { HeartIcon, XMarkIcon, UserIcon } from '@heroicons/vue/24/outline'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', data: any): void
}>()

const form = ref({
  q1: null as number | null,
  q2: null as number | null,
  q3: null as number | null,
  q4: '',
  q5: '',
  q6: ''
})

const isSubmitting = ref(false)

const answeredCount = computed(() => {
  let count = 0
  if (form.value.q1 !== null) count++
  if (form.value.q2 !== null) count++
  if (form.value.q3 !== null) count++
  if (form.value.q4.trim().length > 0) count++
  if (form.value.q5.trim().length > 0) count++
  if (form.value.q6.trim().length > 0) count++
  return count
})

const canSubmit = computed(() => answeredCount.value >= 5)

const closeModal = () => {
  if (isSubmitting.value) return
  emit('close')
}

const submit = async () => {
  if (!canSubmit.value) return
  
  isSubmitting.value = true
  
  // Simulate network request
  await new Promise(resolve => setTimeout(resolve, 800))
  
  emit('submit', { ...form.value })
  isSubmitting.value = false
  
  // Reset form
  form.value = {
    q1: null,
    q2: null,
    q3: null,
    q4: '',
    q5: '',
    q6: ''
  }
}
</script>

<style scoped>
/* Custom scrollbar for inner container */
.document-scroll::-webkit-scrollbar {
  width: 6px;
}
.document-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.document-scroll::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 20px;
}
</style>
