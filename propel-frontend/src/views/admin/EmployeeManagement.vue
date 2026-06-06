<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
      <div>
        <h1 class="text-3xl font-bold text-slate-900 tracking-tight">Personel Yönetimi</h1>
        <p class="text-slate-500 mt-1">
          ML · Nabız Anketi · 360° Geri Bildirim verilerinden hesaplanan
          <span class="font-medium text-indigo-600">bütünleşik çalışan skoru</span>
        </p>
      </div>
      <button
        @click="fetchAll"
        :disabled="isLoading"
        class="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium px-4 py-2.5 rounded-lg transition-colors flex items-center gap-2 shadow-sm"
      >
        <ArrowPathIcon class="w-5 h-5" :class="isLoading ? 'animate-spin' : ''" />
        {{ isLoading ? 'Yükleniyor...' : 'Yenile' }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="flex flex-col items-center justify-center py-24 text-slate-400 gap-4">
      <svg class="animate-spin w-8 h-8" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
      </svg>
      <span class="text-sm">ML modelleri çalıştırılıyor, veriler birleştiriliyor...</span>
    </div>

    <template v-else>
      <!-- KPI Cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Toplam Personel</p>
          <p class="text-3xl font-bold text-slate-900">{{ enriched.length }}</p>
          <p class="text-xs text-slate-400 mt-1">ML + Anket verisi mevcut</p>
        </div>
        <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Ort. Genel Skor</p>
          <p class="text-3xl font-bold" :class="avgScoreColor">{{ avgGenel }}</p>
          <p class="text-xs text-slate-400 mt-1">100 üzerinden sağlık skoru</p>
        </div>
        <div class="bg-white rounded-2xl border border-red-100 p-5 shadow-sm bg-red-50/40">
          <p class="text-xs font-semibold text-red-400 uppercase tracking-wider mb-1">Yüksek Risk</p>
          <p class="text-3xl font-bold text-red-600">{{ highRiskCount }}</p>
          <p class="text-xs text-red-400 mt-1">Genel skor &lt; 40</p>
        </div>
        <div class="bg-white rounded-2xl border border-emerald-100 p-5 shadow-sm bg-emerald-50/40">
          <p class="text-xs font-semibold text-emerald-500 uppercase tracking-wider mb-1">Güvenli Bölge</p>
          <p class="text-3xl font-bold text-emerald-600">{{ safeCount }}</p>
          <p class="text-xs text-emerald-500 mt-1">Genel skor ≥ 70</p>
        </div>
      </div>

      <!-- Top 5 / Bottom 5 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <!-- Top 5 -->
        <div class="bg-white rounded-2xl border border-emerald-200 shadow-sm overflow-hidden">
          <div class="bg-emerald-50 px-6 py-4 border-b border-emerald-100 flex items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <TrophyIcon class="w-5 h-5 text-emerald-600" />
              <h3 class="font-bold text-emerald-800">En Yüksek Skor — Top 5</h3>
            </div>
            <button
              @click="showTopActionsModal = true"
              class="flex items-center gap-1.5 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 rounded-lg transition-colors shadow-sm"
            >
              <StarIcon class="w-3.5 h-3.5" />
              Aksiyonlar
            </button>
          </div>
          <div class="p-4 space-y-3">
            <div
              v-for="(emp, i) in topFive"
              :key="emp.code"
              class="flex items-center gap-3"
            >
              <span class="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold flex items-center justify-center flex-shrink-0">
                {{ Number(i) + 1 }}
              </span>
              <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                :class="emp.dept === 'Satış' ? 'bg-emerald-500' : 'bg-indigo-500'">
                {{ initials(emp.name) }}
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-slate-800 truncate">{{ emp.name }}</p>
                <p class="text-xs text-slate-400 truncate">{{ emp.dept }} · {{ emp.team }}</p>
              </div>
              <div class="text-right flex-shrink-0">
                <span class="text-lg font-bold text-emerald-600">{{ emp.genel_skor }}</span>
                <p class="text-[10px] text-slate-400">/ 100</p>
              </div>
              <div class="w-20">
                <div class="bg-slate-100 rounded-full h-1.5 overflow-hidden">
                  <div class="h-full bg-emerald-500 rounded-full" :style="{ width: `${emp.genel_skor}%` }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Bottom 5 -->
        <div class="bg-white rounded-2xl border border-red-200 shadow-sm overflow-hidden">
          <div class="bg-red-50 px-6 py-4 border-b border-red-100 flex items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <ExclamationTriangleIcon class="w-5 h-5 text-red-600" />
              <h3 class="font-bold text-red-800">Dikkat Gerektiren — Bottom 5</h3>
            </div>
            <button
              @click="showBottomActionsModal = true"
              class="flex items-center gap-1.5 text-xs font-semibold bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded-lg transition-colors shadow-sm"
            >
              <ClipboardDocumentListIcon class="w-3.5 h-3.5" />
              Aksiyonlar
            </button>
          </div>
          <div class="p-4 space-y-3">
            <div
              v-for="(emp, i) in bottomFive"
              :key="emp.code"
              class="flex items-center gap-3"
            >
              <span class="w-6 h-6 rounded-full bg-red-100 text-red-700 text-xs font-bold flex items-center justify-center flex-shrink-0">
                {{ i + 1 }}
              </span>
              <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                :class="emp.dept === 'Satış' ? 'bg-emerald-500' : 'bg-indigo-500'">
                {{ initials(emp.name) }}
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-slate-800 truncate">{{ emp.name }}</p>
                <p class="text-xs text-slate-400 truncate">{{ emp.dept }} · {{ emp.team }}</p>
              </div>
              <div class="text-right flex-shrink-0">
                <span class="text-lg font-bold text-red-600">{{ emp.genel_skor }}</span>
                <p class="text-[10px] text-slate-400">/ 100</p>
              </div>
              <div class="w-20">
                <div class="bg-slate-100 rounded-full h-1.5 overflow-hidden">
                  <div class="h-full bg-red-500 rounded-full" :style="{ width: emp.genel_skor + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Top 5 Aksiyonlar Modalı ──────────────────────────────────────── -->
      <Teleport to="body">
        <Transition name="modal-fade">
          <div v-if="showTopActionsModal" class="fixed inset-0 z-50 flex items-start justify-center p-4 pt-16 overflow-y-auto" @click.self="showTopActionsModal = false">
            <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="showTopActionsModal = false"></div>
            <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-3xl z-10 overflow-hidden">
              <!-- Modal Header -->
              <div class="bg-gradient-to-r from-emerald-600 to-teal-600 px-6 py-5 text-white flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <TrophyIcon class="w-6 h-6 text-yellow-300" />
                  <div>
                    <h2 class="text-lg font-bold">Ödüllendirme ve Destek Aksiyonları</h2>
                    <p class="text-xs text-emerald-100">En yüksek performanslı 5 çalışan için öneriler</p>
                  </div>
                </div>
                <button @click="showTopActionsModal = false" class="p-1.5 hover:bg-white/20 rounded-lg transition-colors">
                  <XMarkIcon class="w-5 h-5" />
                </button>
              </div>

              <div class="p-6 space-y-7 max-h-[70vh] overflow-y-auto">
                <!-- Ödüllendirme Önerileri -->
                <section>
                  <h3 class="text-sm font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <span class="text-lg">🌟</span> Ödüllendirme Önerileri
                  </h3>
                  <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    <div v-for="reward in rewardSuggestions" :key="reward.title"
                      class="bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-100 rounded-xl p-3 hover:shadow-sm transition-shadow">
                      <div class="text-2xl mb-1.5">{{ reward.icon }}</div>
                      <p class="text-xs font-bold text-emerald-800">{{ reward.title }}</p>
                      <p class="text-[10px] text-slate-500 mt-0.5 leading-relaxed">{{ reward.desc }}</p>
                    </div>
                  </div>
                </section>

                <!-- Hayır Kurumu Bağışı -->
                <section>
                  <h3 class="text-sm font-bold text-slate-700 uppercase tracking-wider mb-1 flex items-center gap-2">
                    <span class="text-lg">❤️</span> Hayır Kurumu Bağışı
                  </h3>
                  <p class="text-xs text-slate-500 mb-4">Her çalışan adına yapılacak bağış için tercih edilen kurumu seçin. Çalışanlar kendi seçimlerini yapabilir.</p>

                  <div class="space-y-4">
                    <div v-for="emp in topFive" :key="emp.code" class="bg-slate-50 rounded-xl p-4 border border-slate-200">
                      <div class="flex items-center gap-3 mb-3">
                        <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                          :class="emp.dept === 'Satış' ? 'bg-emerald-500' : 'bg-indigo-500'">
                          {{ initials(emp.name) }}
                        </div>
                        <div>
                          <p class="text-sm font-bold text-slate-800">{{ emp.name }}</p>
                          <p class="text-xs text-slate-400">{{ emp.dept }} · Skor: {{ emp.genel_skor }}/100</p>
                        </div>
                        <div class="ml-auto">
                          <span v-if="selectedCharities[emp.code]" class="text-[10px] font-semibold bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full">
                            ✓ Seçildi
                          </span>
                        </div>
                      </div>
                      <div class="grid grid-cols-3 gap-1.5">
                        <button
                          v-for="charity in charities"
                          :key="charity.name"
                          @click="selectedCharities[emp.code] = selectedCharities[emp.code] === charity.name ? '' : charity.name"
                          :class="[
                            'text-left px-2.5 py-2 rounded-lg border text-[10px] font-medium transition-all',
                            selectedCharities[emp.code] === charity.name
                              ? 'bg-emerald-600 border-emerald-600 text-white shadow-md scale-105'
                              : 'bg-white border-slate-200 text-slate-600 hover:border-emerald-300 hover:bg-emerald-50'
                          ]"
                        >
                          <span class="mr-1">{{ charity.emoji }}</span>{{ charity.name }}
                        </button>
                      </div>
                    </div>
                  </div>

                  <!-- Seçim Özeti -->
                  <div v-if="Object.values(selectedCharities).some(v => v)" class="mt-4 bg-emerald-50 border border-emerald-200 rounded-xl p-4">
                    <p class="text-xs font-bold text-emerald-700 mb-2">📋 Bağış Özeti</p>
                    <div class="space-y-1">
                      <div v-for="emp in topFive" :key="emp.code">
                        <div v-if="selectedCharities[emp.code]" class="flex items-center gap-2 text-xs text-emerald-800">
                          <span class="font-semibold">{{ emp.name.split(' ')[0] }}:</span>
                          <span>{{ selectedCharities[emp.code] }}</span>
                        </div>
                      </div>
                    </div>
                    <p class="text-[10px] text-emerald-600 mt-2">Bu seçimler İK sistemine kaydedilebilir veya bağış koordinatörüne iletilebilir.</p>
                  </div>
                </section>

                <!-- Hayır Kurumları Bilgi Kartları -->
                <section>
                  <h3 class="text-sm font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <span class="text-lg">🏛️</span> Desteklenen Kurumlar
                  </h3>
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <div v-for="charity in charities" :key="charity.name"
                      class="flex items-start gap-2.5 bg-white border border-slate-100 rounded-lg p-3 hover:border-slate-200 transition-colors">
                      <span class="text-xl flex-shrink-0">{{ charity.emoji }}</span>
                      <div>
                        <p class="text-xs font-bold text-slate-800">{{ charity.name }}</p>
                        <p class="text-[10px] text-slate-400 leading-relaxed mt-0.5">{{ charity.desc }}</p>
                      </div>
                    </div>
                  </div>
                </section>
              </div>

              <div class="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-end gap-3">
                <button @click="showTopActionsModal = false" class="px-4 py-2 text-sm text-slate-600 hover:bg-slate-200 rounded-lg transition-colors">
                  Kapat
                </button>
                <button class="px-4 py-2 text-sm font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors">
                  Seçimleri Kaydet
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </Teleport>

      <!-- ── Bottom 5 Aksiyonlar Modalı ──────────────────────────────────── -->
      <Teleport to="body">
        <Transition name="modal-fade">
          <div v-if="showBottomActionsModal" class="fixed inset-0 z-50 flex items-start justify-center p-4 pt-16 overflow-y-auto" @click.self="showBottomActionsModal = false">
            <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="showBottomActionsModal = false"></div>
            <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-3xl z-10 overflow-hidden">
              <!-- Modal Header -->
              <div class="bg-gradient-to-r from-red-600 to-rose-600 px-6 py-5 text-white flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <ExclamationTriangleIcon class="w-6 h-6 text-yellow-300" />
                  <div>
                    <h2 class="text-lg font-bold">Risk Azaltma Aksiyonları</h2>
                    <p class="text-xs text-red-100">Dikkat gerektiren 5 çalışan için alınması gereken önlemler</p>
                  </div>
                </div>
                <button @click="showBottomActionsModal = false" class="p-1.5 hover:bg-white/20 rounded-lg transition-colors">
                  <XMarkIcon class="w-5 h-5" />
                </button>
              </div>

              <div class="p-6 space-y-5 max-h-[70vh] overflow-y-auto">
                <div v-for="(emp, idx) in bottomFive" :key="emp.code"
                  class="bg-white border rounded-xl overflow-hidden shadow-sm"
                  :class="emp.genel_skor < 30 ? 'border-red-200' : 'border-amber-200'"
                >
                  <!-- Çalışan başlığı -->
                  <div class="px-4 py-3 flex items-center gap-3"
                    :class="emp.genel_skor < 30 ? 'bg-red-50 border-b border-red-100' : 'bg-amber-50 border-b border-amber-100'"
                  >
                    <span class="w-6 h-6 rounded-full text-xs font-bold flex items-center justify-center flex-shrink-0"
                      :class="emp.genel_skor < 30 ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'">
                      {{ idx + 1 }}
                    </span>
                    <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                      :class="emp.dept === 'Satış' ? 'bg-emerald-500' : 'bg-indigo-500'">
                      {{ initials(emp.name) }}
                    </div>
                    <div class="flex-1">
                      <p class="text-sm font-bold text-slate-800">{{ emp.name }}</p>
                      <p class="text-xs text-slate-400">{{ emp.dept }} · {{ emp.team }}</p>
                    </div>
                    <div class="flex items-center gap-3 text-xs">
                      <span class="font-mono">
                        <span class="text-slate-400">Genel: </span>
                        <span class="font-bold" :class="emp.genel_skor < 30 ? 'text-red-600' : 'text-amber-600'">{{ emp.genel_skor }}/100</span>
                      </span>
                      <span class="px-2 py-0.5 rounded-full font-semibold"
                        :class="emp.genel_skor < 30 ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'">
                        {{ emp.genel_skor < 30 ? 'Kritik' : 'Yüksek Risk' }}
                      </span>
                    </div>
                  </div>

                  <!-- Risk sinyalleri -->
                  <div class="px-4 pt-3 pb-1 flex flex-wrap gap-1.5">
                    <span v-if="emp.perf_drop >= 50" class="text-[10px] bg-red-50 text-red-600 border border-red-100 px-2 py-0.5 rounded-full font-medium">📉 Performans Düşüşü %{{ emp.perf_drop }}</span>
                    <span v-if="emp.burnout >= 40" class="text-[10px] bg-orange-50 text-orange-600 border border-orange-100 px-2 py-0.5 rounded-full font-medium">🔥 Tükenmişlik %{{ emp.burnout }}</span>
                    <span v-if="emp.resignation >= 40" class="text-[10px] bg-purple-50 text-purple-600 border border-purple-100 px-2 py-0.5 rounded-full font-medium">🚪 İstifa Riski %{{ emp.resignation }}</span>
                    <span v-if="emp.high_risk >= 50" class="text-[10px] bg-red-50 text-red-700 border border-red-200 px-2 py-0.5 rounded-full font-medium">⚠️ Yüksek Risk %{{ emp.high_risk }}</span>
                    <span v-if="emp.survey_score !== null && emp.survey_score < 3" class="text-[10px] bg-amber-50 text-amber-600 border border-amber-100 px-2 py-0.5 rounded-full font-medium">💛 Düşük Motivasyon {{ emp.survey_score.toFixed(1) }}/5</span>
                    <span v-if="emp.survey_ars !== null && emp.survey_ars >= 0.6" class="text-[10px] bg-rose-50 text-rose-600 border border-rose-100 px-2 py-0.5 rounded-full font-medium">🔴 Yüksek ARS %{{ (emp.survey_ars * 100).toFixed(0) }}</span>
                  </div>

                  <!-- Aksiyon listesi -->
                  <div class="px-4 pb-4 pt-2 space-y-1.5">
                    <div v-for="action in bottomActionsForEmployee(emp)" :key="action.text"
                      class="flex items-start gap-2.5 p-2.5 rounded-lg border"
                      :class="{
                        'bg-red-50 border-red-100': action.priority === 'Acil',
                        'bg-amber-50 border-amber-100': action.priority === 'Yüksek',
                        'bg-blue-50 border-blue-100': action.priority === 'Orta',
                        'bg-slate-50 border-slate-100': action.priority === 'Düşük',
                      }"
                    >
                      <span class="text-base flex-shrink-0 mt-0.5">{{ action.icon }}</span>
                      <div class="flex-1">
                        <p class="text-xs text-slate-800 font-medium leading-snug">{{ action.text }}</p>
                      </div>
                      <span class="text-[9px] font-bold px-1.5 py-0.5 rounded flex-shrink-0"
                        :class="{
                          'bg-red-200 text-red-800': action.priority === 'Acil',
                          'bg-amber-200 text-amber-800': action.priority === 'Yüksek',
                          'bg-blue-200 text-blue-800': action.priority === 'Orta',
                          'bg-slate-200 text-slate-700': action.priority === 'Düşük',
                        }"
                      >
                        {{ action.priority }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Genel notlar -->
                <div class="bg-amber-50 border border-amber-200 rounded-xl p-4">
                  <p class="text-xs font-bold text-amber-800 mb-2">📌 Genel Uygulama Rehberi</p>
                  <ul class="text-xs text-amber-700 space-y-1 list-disc list-inside">
                    <li>"Acil" öncelikli aksiyonlar 1 hafta içinde başlatılmalı</li>
                    <li>Tüm görüşmeler İK kayıtlarına işlenmelidir</li>
                    <li>İyileşme süreci 4 haftalık dönemlerle takip edilmeli</li>
                    <li>Çalışanın onayı alınmadan üçüncü kişilerle veri paylaşılmamalı</li>
                  </ul>
                </div>
              </div>

              <div class="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-end">
                <button @click="showBottomActionsModal = false" class="px-4 py-2 text-sm font-semibold bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors">
                  Kapat
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </Teleport>

      <!-- Gemini Yorumu -->
      <div class="bg-gradient-to-br from-violet-900 via-indigo-900 to-slate-900 rounded-2xl p-6 mb-8 text-white shadow-xl">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-violet-500/30 rounded-xl">
              <SparklesIcon class="w-5 h-5 text-violet-300" />
            </div>
            <div>
              <h3 class="font-bold text-white">Gemini AI Bütünleşik Değerlendirme</h3>
              <p class="text-xs text-violet-300">ML + Nabız Anketi verileri birleştirilerek oluşturuldu</p>
            </div>
          </div>
          <button
            @click="fetchGemini"
            :disabled="geminiLoading"
            class="text-xs bg-violet-500/20 hover:bg-violet-500/30 border border-violet-500/30 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50"
          >
            <ArrowPathIcon class="w-3.5 h-3.5" :class="geminiLoading ? 'animate-spin' : ''" />
            {{ geminiLoading ? 'Yorumlanıyor...' : 'Yeniden Yorumla' }}
          </button>
        </div>

        <div v-if="geminiLoading" class="flex items-center gap-3 py-6 text-violet-300">
          <svg class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
          </svg>
          <span class="text-sm">Gemini 61 çalışanın verilerini analiz ediyor...</span>
        </div>

        <div v-else-if="geminiNarrative">
          <!-- Genel özet -->
          <p class="text-sm text-violet-100 leading-relaxed mb-5">{{ geminiNarrative.summary }}</p>

          <!-- Sections -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
            <div
              v-for="section in geminiNarrative.sections"
              :key="section.title"
              class="bg-white/5 border border-white/10 rounded-xl p-4"
            >
              <p class="text-xs font-bold text-violet-300 uppercase tracking-wider mb-2">{{ section.title }}</p>
              <p class="text-xs text-slate-300 leading-relaxed">{{ section.content }}</p>
            </div>
          </div>

          <!-- Actions -->
          <div v-if="geminiNarrative.actions?.length" class="flex flex-wrap gap-2">
            <span
              v-for="action in geminiNarrative.actions"
              :key="action"
              class="text-xs bg-violet-500/20 border border-violet-500/30 text-violet-200 px-3 py-1.5 rounded-lg"
            >
              {{ action }}
            </span>
          </div>

          <p v-if="!geminiUsed" class="text-[10px] text-violet-400 mt-3">
            ⚠ Gemini API yapılandırılmamış — deterministik özet gösteriliyor.
          </p>
        </div>

        <div v-else class="text-sm text-violet-300 py-4">
          Gemini yorumu yüklenemedi. "Yeniden Yorumla" butonuna tıklayın.
        </div>
      </div>

      <!-- Skor Kaynağı Açıklaması -->
      <div class="bg-white rounded-xl border border-slate-200 p-4 mb-6 flex flex-wrap gap-4 text-xs text-slate-500">
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded bg-indigo-500 inline-block"></span>
          <span><strong class="text-slate-700">ML Sağlık (%50)</strong> — 4 hedef riski (PD/TK/İR/YR) ters çevrilmiş</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded bg-blue-400 inline-block"></span>
          <span><strong class="text-slate-700">Nabız Skoru (%30)</strong> — Haftalık motivasyon ortalaması (0-5)</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded bg-emerald-400 inline-block"></span>
          <span><strong class="text-slate-700">Tutma Skoru (%20)</strong> — ARS elde tutma riski ters çevrilmiş</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded bg-slate-300 inline-block"></span>
          <span class="text-slate-400"><strong class="text-slate-500">360° Geri Bildirim</strong> — Backend entegrasyonu bekleniyor</span>
        </div>
      </div>

      <!-- Filters -->
      <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-200 mb-4 flex flex-col md:flex-row gap-4 items-center">
        <div class="relative w-full md:w-80">
          <MagnifyingGlassIcon class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="İsim veya departman ara..."
            class="w-full pl-9 pr-4 py-2 bg-slate-50 border-none rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 transition-shadow"
          />
        </div>
        <select v-model="selectedDepartment" class="bg-slate-50 border-none rounded-lg text-sm py-2 pl-3 pr-8 focus:ring-2 focus:ring-indigo-500 text-slate-600">
          <option value="">Tüm Departmanlar</option>
          <option v-for="d in departmentOptions" :key="d" :value="d">{{ d }}</option>
        </select>
        <select v-model="selectedRiskFilter" class="bg-slate-50 border-none rounded-lg text-sm py-2 pl-3 pr-8 focus:ring-2 focus:ring-indigo-500 text-slate-600">
          <option value="">Tüm Skor Seviyeleri</option>
          <option value="high_risk">Yüksek Risk (&lt;40)</option>
          <option value="medium_risk">Orta Risk (40-69)</option>
          <option value="safe">Güvenli (≥70)</option>
        </select>
        <select v-model="sortField" class="bg-slate-50 border-none rounded-lg text-sm py-2 pl-3 pr-8 focus:ring-2 focus:ring-indigo-500 text-slate-600">
          <option value="genel_desc">Genel Skor ↓</option>
          <option value="genel_asc">Genel Skor ↑</option>
          <option value="ml_desc">ML Risk ↓</option>
          <option value="nabiz_desc">Nabız ↓</option>
          <option value="name_asc">İsim A-Z</option>
        </select>
        <span class="ml-auto text-xs text-slate-400 whitespace-nowrap">
          {{ filteredEmployees.length }} personel gösteriliyor
        </span>
      </div>

      <!-- Tablo -->
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                <th class="px-5 py-3">Personel</th>
                <th class="px-5 py-3">Departman</th>
                <th class="px-5 py-3 text-center">
                  <div class="flex flex-col items-center gap-0.5">
                    <span>ML Hedefleri</span>
                    <span class="text-[9px] font-normal text-slate-300 normal-case">PD · TK · İR · YR</span>
                  </div>
                </th>
                <th class="px-5 py-3 text-center">
                  <div class="flex flex-col items-center gap-0.5">
                    <span>Nabız Anketi</span>
                    <span class="text-[9px] font-normal text-slate-300 normal-case">Motivasyon · ARS</span>
                  </div>
                </th>
                <th class="px-5 py-3 text-center">
                  <div class="flex flex-col items-center gap-0.5">
                    <span>360° Geri Bildirim</span>
                    <span class="text-[9px] font-normal text-slate-300 normal-case">Yakında</span>
                  </div>
                </th>
                <th class="px-5 py-3 text-center cursor-pointer" @click="sortField = sortField === 'genel_desc' ? 'genel_asc' : 'genel_desc'">
                  <div class="flex items-center justify-center gap-1">
                    Genel Skor
                    <ArrowsUpDownIcon class="w-3.5 h-3.5" />
                  </div>
                </th>
                <th class="px-5 py-3 text-right">İşlemler</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="emp in paginatedEmployees"
                :key="emp.code"
                class="hover:bg-slate-50/80 transition-colors cursor-pointer group"
                @click="navigateToDetails(emp.db_id)"
              >
                <!-- Personel -->
                <td class="px-5 py-3.5">
                  <div class="flex items-center gap-3">
                    <div class="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                      :class="emp.dept === 'Satış' ? 'bg-emerald-500' : 'bg-indigo-600'">
                      {{ initials(emp.name) }}
                    </div>
                    <div>
                      <p class="font-semibold text-slate-900 text-sm">{{ emp.name }}</p>
                      <p class="text-xs text-slate-400">{{ emp.team }}</p>
                    </div>
                  </div>
                </td>

                <!-- Departman -->
                <td class="px-5 py-3.5">
                  <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                    :class="emp.dept === 'Satış' ? 'bg-emerald-50 text-emerald-700' : 'bg-indigo-50 text-indigo-700'">
                    {{ emp.dept }}
                  </span>
                </td>

                <!-- ML Hedefleri -->
                <td class="px-5 py-3.5">
                  <div class="flex flex-col gap-1 min-w-[140px]">
                    <div class="flex items-center gap-1.5 text-[10px]">
                      <span class="w-12 text-slate-400 shrink-0">PD</span>
                      <div class="flex-1 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                        <div class="h-full rounded-full" :class="mlBarColor(emp.perf_drop)" :style="{ width: emp.perf_drop + '%' }"></div>
                      </div>
                      <span class="w-7 text-right font-mono font-semibold text-slate-600">{{ emp.perf_drop }}%</span>
                    </div>
                    <div class="flex items-center gap-1.5 text-[10px]">
                      <span class="w-12 text-slate-400 shrink-0">Tükenmişlik</span>
                      <div class="flex-1 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                        <div class="h-full rounded-full" :class="mlBarColor(emp.burnout)" :style="{ width: emp.burnout + '%' }"></div>
                      </div>
                      <span class="w-7 text-right font-mono font-semibold text-slate-600">{{ emp.burnout }}%</span>
                    </div>
                    <div class="flex items-center gap-1.5 text-[10px]">
                      <span class="w-12 text-slate-400 shrink-0">İstifa</span>
                      <div class="flex-1 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                        <div class="h-full rounded-full" :class="mlBarColor(emp.resignation)" :style="{ width: emp.resignation + '%' }"></div>
                      </div>
                      <span class="w-7 text-right font-mono font-semibold text-slate-600">{{ emp.resignation }}%</span>
                    </div>
                    <div class="flex items-center gap-1.5 text-[10px]">
                      <span class="w-12 text-slate-400 shrink-0">Yük. Risk</span>
                      <div class="flex-1 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                        <div class="h-full rounded-full" :class="mlBarColor(emp.high_risk)" :style="{ width: emp.high_risk + '%' }"></div>
                      </div>
                      <span class="w-7 text-right font-mono font-semibold text-slate-600">{{ emp.high_risk }}%</span>
                    </div>
                  </div>
                </td>

                <!-- Nabız Anketi -->
                <td class="px-5 py-3.5">
                  <div v-if="emp.survey_score !== null" class="flex flex-col gap-1 min-w-[100px]">
                    <div class="flex items-center gap-2">
                      <span class="text-[10px] text-slate-400 w-20 shrink-0">Motivasyon</span>
                      <span class="text-sm font-bold" :class="surveyScoreColor(emp.survey_score)">
                        {{ emp.survey_score.toFixed(1) }}<span class="text-xs font-normal text-slate-400">/5</span>
                      </span>
                    </div>
                    <div class="flex items-center gap-2">
                      <span class="text-[10px] text-slate-400 w-20 shrink-0">ARS Riski</span>
                      <span class="text-sm font-bold" :class="arsColor(emp.survey_ars)">
                        {{ (emp.survey_ars * 100).toFixed(0) }}<span class="text-xs font-normal text-slate-400">%</span>
                      </span>
                    </div>
                  </div>
                  <span v-else class="text-xs text-slate-300">—</span>
                </td>

                <!-- 360 placeholder -->
                <td class="px-5 py-3.5 text-center">
                  <span class="text-[10px] text-slate-300 bg-slate-50 px-2 py-1 rounded border border-slate-100">Yakında</span>
                </td>

                <!-- Genel Skor -->
                <td class="px-5 py-3.5 text-center">
                  <div class="flex flex-col items-center gap-1">
                    <span class="text-2xl font-black" :class="genelScorColor(emp.genel_skor)">
                      {{ emp.genel_skor }}
                    </span>
                    <div class="w-16 bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div class="h-full rounded-full transition-all" :class="genelScorBarColor(emp.genel_skor)" :style="{ width: emp.genel_skor + '%' }"></div>
                    </div>
                    <span class="text-[10px]" :class="genelScorLabel(emp.genel_skor).color">
                      {{ genelScorLabel(emp.genel_skor).text }}
                    </span>
                  </div>
                </td>

                <!-- İşlemler -->
                <td class="px-5 py-3.5 text-right">
                  <button
                    v-if="emp.db_id"
                    class="text-slate-300 group-hover:text-indigo-500 p-2 transition-colors"
                    @click.stop="navigateToDetails(emp.db_id)"
                  >
                    <ArrowTopRightOnSquareIcon class="w-4 h-4" />
                  </button>
                </td>
              </tr>

              <tr v-if="filteredEmployees.length === 0">
                <td colspan="7" class="px-6 py-12 text-center text-slate-400 text-sm">
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
            <button :disabled="currentPage <= 1" @click="currentPage--"
              class="px-3 py-1.5 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed">
              Önceki
            </button>
            <button :disabled="currentPage >= totalPages" @click="currentPage++"
              class="px-3 py-1.5 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed">
              Sonraki
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  MagnifyingGlassIcon,
  ArrowsUpDownIcon,
  ArrowPathIcon,
  SparklesIcon,
  TrophyIcon,
  ExclamationTriangleIcon,
  ArrowTopRightOnSquareIcon,
  StarIcon,
  ClipboardDocumentListIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'
import { apiClient } from '@/services/api/client'
import { employeeApi } from '@/services/api/employee.api'

const router = useRouter()
const isLoading = ref(true)
const geminiLoading = ref(false)
const geminiUsed = ref(false)

// ── Modal durumları ────────────────────────────────────────────────────────
const showTopActionsModal = ref(false)
const showBottomActionsModal = ref(false)
const selectedCharities = ref<Record<string, string>>({})

const charities = [
  { name: 'LÖSEV', desc: 'Lösemi ve kanser hastası çocuklara sağlık, eğitim ve sosyal destek', emoji: '🎗️' },
  { name: 'TEMA Vakfı', desc: 'Çevre, toprak koruma, ağaçlandırma ve iklim çalışmaları', emoji: '🌱' },
  { name: 'Darüşşafaka Cemiyeti', desc: 'Anne veya babasını kaybetmiş çocuklara eğitim desteği', emoji: '📚' },
  { name: 'Türk Eğitim Vakfı (TEV)', desc: 'Öğrencilere burs ve eğitim desteği', emoji: '🎓' },
  { name: 'Türk Kızılay', desc: 'Afet yardımları, kan bağışı ve sosyal destek', emoji: '❤️' },
  { name: 'UNICEF Türkiye', desc: 'Çocuk hakları, eğitim ve sağlık projeleri', emoji: '🌍' },
  { name: 'AHBAP Derneği', desc: 'İhtiyaç sahiplerine ve afet bölgelerine destek', emoji: '🤝' },
  { name: 'Mehmetçik Vakfı', desc: 'Şehit yakınları ve gazilere destek', emoji: '🏅' },
  { name: 'WWF-Türkiye', desc: 'Doğa koruma ve biyolojik çeşitlilik projeleri', emoji: '🐾' },
]

const rewardSuggestions = [
  { icon: '🏆', title: 'Performans Sertifikası', desc: 'Üstün başarı belgesi ve dijital rozet' },
  { icon: '🎁', title: 'Ekstra İzin Günü', desc: '1-3 gün ilave tatil hakkı' },
  { icon: '💡', title: 'Mentorluk Fırsatı', desc: 'Üst düzey yöneticilerle birebir koçluk' },
  { icon: '📈', title: 'Kariyer Gelişim Bütçesi', desc: 'Eğitim ve sertifika programı desteği' },
  { icon: '🌟', title: 'Şirket Geneli Takdir', desc: 'Tüm departmanlara duyurulan başarı paylaşımı' },
  { icon: '💰', title: 'Performans Primi', desc: 'Kısa vadeli ikramiye önerileri' },
]

function bottomActionsForEmployee(emp: EnrichedEmployee): { icon: string; text: string; priority: string }[] {
  const actions: { icon: string; text: string; priority: string }[] = []
  if (emp.high_risk >= 50) actions.push({ icon: '⚠️', text: 'Acil 1-on-1 yönetici görüşmesi planla', priority: 'Acil' })
  if (emp.perf_drop >= 50) actions.push({ icon: '📊', text: 'Haftalık KPI takip ve hedef revizyon toplantısı başlat', priority: 'Yüksek' })
  if (emp.burnout >= 40) actions.push({ icon: '🧘', text: 'Tükenmişlik önleme programına yönlendir, iş yükünü dengele', priority: 'Yüksek' })
  if (emp.resignation >= 40) actions.push({ icon: '🤝', text: 'Kariyer gelişim görüşmesi yap, elde tutma paketi hazırla', priority: 'Yüksek' })
  if (emp.survey_ars !== null && emp.survey_ars >= 0.6) actions.push({ icon: '🔒', text: 'Bağlılık planı oluştur, uzun vadeli teşvik görüşmesi yap', priority: 'Yüksek' })
  if (emp.survey_score !== null && emp.survey_score < 3) actions.push({ icon: '💬', text: 'Motivasyon artırıcı sorumluluk ve proje ata', priority: 'Orta' })
  actions.push({ icon: '📋', text: 'Bireysel gelişim planı (IDP) hazırla ve 4 haftada bir gözden geçir', priority: 'Orta' })
  actions.push({ icon: '👥', text: 'Peer destek programı ve buddy sistemi kur', priority: 'Düşük' })
  actions.push({ icon: '🎯', text: 'Kısa vadeli, ulaşılabilir alt hedefler belirle', priority: 'Orta' })
  return actions
}

// ── Raw veri ──────────────────────────────────────────────────────────────

interface EnrichedEmployee {
  code: string
  db_id: number | null
  name: string
  dept: string
  team: string
  // ML
  perf_drop: number
  burnout: number
  resignation: number
  high_risk: number
  ml_composite: number
  // Nabız
  survey_score: number | null
  survey_ars: number | null
  // 360 — backend bekleniyor
  // feedback_score: number | null
  // Bütünleşik
  genel_skor: number
}

const enriched = ref<EnrichedEmployee[]>([])

interface GeminiNarrative {
  summary: string
  sections: { title: string; content: string }[]
  actions: string[]
}
const geminiNarrative = ref<GeminiNarrative | null>(null)

// ── Veri yükleme ──────────────────────────────────────────────────────────

const fetchAll = async () => {
  isLoading.value = true
  try {
    const [aiInsightsRes, employeesRes, surveysRes] = await Promise.all([
      apiClient.get('/admin/uploads/ai-insights').then((r: any) => r.data).catch(() => null),
      employeeApi.getEmployees().catch(() => []),
      apiClient.get('/surveys/').then((r: any) => r.data).catch(() => []),
    ])

    // Gemini narrative'i parse et
    parseGeminiNarrative(aiInsightsRes)
    geminiUsed.value = aiInsightsRes?.gemini_used ?? false

    // employees: external_employee_code → db_id haritası
    const empArray = Array.isArray(employeesRes) ? employeesRes : (employeesRes?.items ?? [])
    const codeToDbId: Record<string, number> = {}
    for (const emp of empArray) {
      const code = (emp.external_employee_code || '').toUpperCase()
      if (code) codeToDbId[code] = emp.id
    }

    // surveys: employee_id → { avg_score, avg_ars }
    const surveyMap: Record<number, { scores: number[]; ars: number[] }> = {}
    for (const s of (Array.isArray(surveysRes) ? surveysRes : [])) {
      const eid = s.employee_id
      if (!surveyMap[eid]) surveyMap[eid] = { scores: [], ars: [] }
      if (typeof s.score === 'number') surveyMap[eid].scores.push(s.score)
      if (typeof s.ars_score === 'number') surveyMap[eid].ars.push(s.ars_score)
    }
    const surveyByEmpId: Record<number, { avg_score: number; avg_ars: number }> = {}
    for (const [eid, data] of Object.entries(surveyMap)) {
      surveyByEmpId[Number(eid)] = {
        avg_score: data.scores.length ? data.scores.reduce((a, b) => a + b, 0) / data.scores.length : 3,
        avg_ars: data.ars.length ? data.ars.reduce((a, b) => a + b, 0) / data.ars.length : 0.3,
      }
    }

    // ML employee_table birleştir
    const mlTable: any[] = aiInsightsRes?.employee_table ?? []
    enriched.value = mlTable.map((ml: any) => {
      const code = (ml.code || '').toUpperCase()
      const dbId = codeToDbId[code] ?? null
      const survey = dbId ? (surveyByEmpId[dbId] ?? null) : null

      const mlHealth = 100 - (ml.composite ?? 50)

      // Nabız bileşeni: motivasyon 0-5 → 0-100; ARS ters çevir
      let nabizHealth: number | null = null
      if (survey) {
        const nabizScore = (survey.avg_score / 5) * 100
        const tutmaScore = (1 - survey.avg_ars) * 100
        nabizHealth = nabizScore * 0.6 + tutmaScore * 0.4
      }

      // Genel skor: ML %50, Nabız %50 (360 gelince ağırlıklar dağıtılacak)
      const genel = nabizHealth !== null
        ? Math.round(mlHealth * 0.5 + nabizHealth * 0.5)
        : Math.round(mlHealth)

      return {
        code,
        db_id: dbId,
        name: ml.name || code,
        dept: ml.department || '—',
        team: ml.team || '—',
        perf_drop: ml.perf_drop ?? 0,
        burnout: ml.burnout ?? 0,
        resignation: ml.resignation ?? 0,
        high_risk: ml.high_risk ?? 0,
        ml_composite: ml.composite ?? 0,
        survey_score: survey?.avg_score ?? null,
        survey_ars: survey?.avg_ars ?? null,
        genel_skor: Math.min(100, Math.max(0, genel)),
      } as EnrichedEmployee
    })

  } catch (err) {
    console.error('[EmployeeManagement] fetch error', err)
  } finally {
    isLoading.value = false
  }
}

function parseGeminiNarrative(data: any) {
  if (!data) return
  const raw = data.narrative
  const stats = data.stats ?? {}

  if (raw && typeof raw === 'object') {
    // Gemini yanıtı geldi
    geminiNarrative.value = {
      summary: raw.summary || raw.genel_durum || 'Analiz tamamlandı.',
      sections: [
        raw.genel_durum ? { title: 'Genel Durum', content: raw.genel_durum } : null,
        raw.kritik_bulgular ? { title: 'Kritik Bulgular', content: raw.kritik_bulgular } : null,
        raw.aksiyon_onerileri ? { title: 'Aksiyon Önerileri', content: raw.aksiyon_onerileri } : null,
      ].filter(Boolean) as { title: string; content: string }[],
      actions: Array.isArray(raw.aksiyon_maddeleri) ? raw.aksiyon_maddeleri : [],
    }
    return
  }

  // Gemini kullanılamıyor — stats'tan deterministik özet üret
  const total: number = stats.total ?? enriched.value.length
  const highRisk: number = stats.high_risk ?? enriched.value.filter(e => e.genel_skor < 40).length
  const avgComposite: number = stats.avg_composite ?? 50
  const avgSales: number = stats.avg_sales ?? 0
  const avgSw: number = stats.avg_sw ?? 0
  const riskPct = total ? Math.round((highRisk / total) * 100) : 0
  const healthPct = Math.round(100 - avgComposite)

  const durum = healthPct >= 65 ? 'genel sağlık seviyesi iyi durumda'
    : healthPct >= 50 ? 'orta düzeyde risk içeriyor'
    : 'kritik risk seviyesinde'

  geminiNarrative.value = {
    summary: `${total} çalışanın ML, nabız anketi ve 360° feedback verileri birleştirilerek analiz edildi. Şirket geneli ${durum}; ortalama sağlık skoru ${healthPct}/100, yüksek riskli personel oranı %${riskPct}.`,
    sections: [
      {
        title: 'Genel Durum',
        content: `${total} çalışanın ${highRisk} tanesi (%${riskPct}) yüksek risk bandında. Satış departmanı ortalama ML bileşik riski %${avgSales.toFixed(0)}, Yazılım departmanı %${avgSw.toFixed(0)} ile seyretmekte.`,
      },
      {
        title: 'Kritik Bulgular',
        content: highRisk > 10
          ? `${highRisk} çalışan acil müdahale gerektiriyor. Performans Düşüşü, Tükenmişlik ve İstifa hedeflerinde eş zamanlı yüksek risk gözlemlendi. Öncelikli olarak bottom-5 listesindeki personelle birebir görüşme planlanmalı.`
          : `Risk düzeyi yönetilebilir seviyede. ${highRisk} çalışanda çoklu risk sinyali mevcut; proaktif destek ile daha kritik seviyelere inmesi önlenebilir.`,
      },
      {
        title: 'Aksiyon Önerileri',
        content: `Bottom-5 çalışanlar için acil 1-on-1 görüşme planlanması, tükenmişlik önleme programlarının devreye alınması ve nabız anketi sonuçlarının yöneticilerle paylaşılması önerilmektedir. 360° feedback entegrasyonu tamamlandığında bu analiz daha kapsamlı olacak.`,
      },
    ],
    actions: [
      `Bottom-5 için acil birebir görüşme (${bottomFive.value.map(e => e.name.split(' ')[0]).join(', ')})`,
      'Tükenmişlik riski yüksek çalışanlara mentorluk desteği',
      'Nabız anketi sıklığını artır (haftalık → günlük)',
      '360° feedback backend entegrasyonunu tamamla',
    ],
  }
}

const fetchGemini = async () => {
  geminiLoading.value = true
  try {
    const res = await apiClient.get('/admin/uploads/ai-insights').then((r: any) => r.data)
    parseGeminiNarrative(res)
    geminiUsed.value = res?.gemini_used ?? false
  } catch {
    //
  } finally {
    geminiLoading.value = false
  }
}

onMounted(fetchAll)

// ── Hesaplanan değerler ────────────────────────────────────────────────────

const avgGenel = computed(() => {
  if (!enriched.value.length) return 0
  return Math.round(enriched.value.reduce((s, e) => s + e.genel_skor, 0) / enriched.value.length)
})

const avgScoreColor = computed(() => {
  if (avgGenel.value >= 70) return 'text-emerald-600'
  if (avgGenel.value >= 50) return 'text-amber-500'
  return 'text-red-600'
})

const highRiskCount = computed(() => enriched.value.filter(e => e.genel_skor < 40).length)
const safeCount = computed(() => enriched.value.filter(e => e.genel_skor >= 70).length)

const sortedByGenel = computed(() =>
  [...enriched.value].sort((a, b) => b.genel_skor - a.genel_skor)
)
const topFive = computed(() => sortedByGenel.value.slice(0, 5))
const bottomFive = computed(() => [...enriched.value].sort((a, b) => a.genel_skor - b.genel_skor).slice(0, 5))

// ── Filtreler ──────────────────────────────────────────────────────────────

const searchQuery = ref('')
const selectedDepartment = ref('')
const selectedRiskFilter = ref('')
const sortField = ref('genel_desc')
const currentPage = ref(1)
const PAGE_SIZE = 12

const departmentOptions = computed(() => {
  const names = new Set(enriched.value.map(e => e.dept).filter(Boolean))
  return Array.from(names).sort()
})

const filteredEmployees = computed(() => {
  let list = enriched.value.filter(emp => {
    const q = searchQuery.value.toLowerCase()
    const matchSearch = !q || emp.name.toLowerCase().includes(q) || emp.dept.toLowerCase().includes(q) || emp.team.toLowerCase().includes(q)
    const matchDept = !selectedDepartment.value || emp.dept === selectedDepartment.value
    const matchRisk = !selectedRiskFilter.value ||
      (selectedRiskFilter.value === 'high_risk' && emp.genel_skor < 40) ||
      (selectedRiskFilter.value === 'medium_risk' && emp.genel_skor >= 40 && emp.genel_skor < 70) ||
      (selectedRiskFilter.value === 'safe' && emp.genel_skor >= 70)
    return matchSearch && matchDept && matchRisk
  })

  if (sortField.value === 'genel_desc') list = [...list].sort((a, b) => b.genel_skor - a.genel_skor)
  else if (sortField.value === 'genel_asc') list = [...list].sort((a, b) => a.genel_skor - b.genel_skor)
  else if (sortField.value === 'ml_desc') list = [...list].sort((a, b) => b.ml_composite - a.ml_composite)
  else if (sortField.value === 'nabiz_desc') list = [...list].sort((a, b) => (b.survey_score ?? 0) - (a.survey_score ?? 0))
  else if (sortField.value === 'name_asc') list = [...list].sort((a, b) => a.name.localeCompare(b.name, 'tr'))

  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredEmployees.value.length / PAGE_SIZE)))
const paginatedEmployees = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredEmployees.value.slice(start, start + PAGE_SIZE)
})

watch([searchQuery, selectedDepartment, selectedRiskFilter, sortField], () => { currentPage.value = 1 })

// ── Yardımcılar ───────────────────────────────────────────────────────────

function initials(name: string) {
  return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
}

function navigateToDetails(id: number | null) {
  if (id) router.push(`/admin/employees/${id}`)
}

function mlBarColor(val: number) {
  if (val >= 70) return 'bg-red-500'
  if (val >= 40) return 'bg-amber-400'
  return 'bg-emerald-400'
}

function surveyScoreColor(score: number) {
  if (score >= 4) return 'text-emerald-600'
  if (score >= 3) return 'text-amber-500'
  return 'text-red-500'
}

function arsColor(ars: number | null) {
  if (ars === null) return 'text-slate-400'
  if (ars >= 0.6) return 'text-red-600'
  if (ars >= 0.3) return 'text-amber-500'
  return 'text-emerald-600'
}

function genelScorColor(score: number) {
  if (score >= 70) return 'text-emerald-600'
  if (score >= 40) return 'text-amber-500'
  return 'text-red-600'
}

function genelScorBarColor(score: number) {
  if (score >= 70) return 'bg-emerald-500'
  if (score >= 40) return 'bg-amber-400'
  return 'bg-red-500'
}

function genelScorLabel(score: number) {
  if (score >= 70) return { text: 'Güvenli', color: 'text-emerald-500' }
  if (score >= 40) return { text: 'Orta Risk', color: 'text-amber-500' }
  return { text: 'Yüksek Risk', color: 'text-red-500' }
}
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
.modal-fade-enter-active > div:last-child,
.modal-fade-leave-active > div:last-child {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.modal-fade-enter-from > div:last-child,
.modal-fade-leave-to > div:last-child {
  transform: scale(0.95) translateY(-8px);
  opacity: 0;
}
</style>
