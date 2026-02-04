<template>
  <div>
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold text-slate-900 tracking-tight">Veri Yönetimi</h1>
        <p class="text-slate-500 mt-1">Sistem verilerini içe aktarın, dışa aktarın ve yönetin.</p>
      </div>
      <button class="bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-medium px-4 py-2.5 rounded-lg transition-colors flex items-center gap-2 shadow-sm">
        <ArrowDownTrayIcon class="w-5 h-5" />
        Şablon İndir
      </button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Upload Section -->
      <div class="lg:col-span-1 space-y-6">
         <div class="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
             <h2 class="text-lg font-bold text-slate-900 mb-4">Veri Yükleme</h2>
             
             <div class="mb-4">
                 <label class="block text-sm font-medium text-slate-700 mb-1">Veri Tipi</label>
                 <select class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none">
                     <option>Performans Metrikleri (KPI)</option>
                     <option>Personel Listesi</option>
                     <option>Anket Sonuçları</option>
                 </select>
             </div>

             <div class="border-2 border-dashed border-slate-300 rounded-xl p-8 flex flex-col items-center justify-center text-center hover:bg-slate-50 transition-colors cursor-pointer">
                 <CloudArrowUpIcon class="w-12 h-12 text-blue-500 mb-3" />
                 <p class="text-sm font-medium text-slate-900">Dosyayı sürükleyin veya seçin</p>
                 <p class="text-xs text-slate-500 mt-1">CSV, Excel veya JSON (max 10MB)</p>
             </div>

             <button class="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded-lg transition-colors shadow-sm shadow-blue-600/20">
                 Yüklemeyi Başlat
             </button>
         </div>

         <!-- Warning Alert -->
         <div class="bg-amber-50 border border-amber-200 rounded-xl p-4 flex gap-3">
             <ExclamationTriangleIcon class="w-5 h-5 text-amber-600 flex-shrink-0" />
             <div>
                 <p class="text-sm font-bold text-amber-800">Eksik Veri Tespiti</p>
                 <p class="text-xs text-amber-700 mt-1">Son yüklenen veri setinde "Pazarlama" departmanı için 2 aylık KPI verisi eksik görünüyor.</p>
             </div>
         </div>
      </div>

      <!-- Recent Uploads / Data Preview -->
      <div class="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div class="p-6 border-b border-slate-200 flex justify-between items-center">
              <h2 class="text-lg font-bold text-slate-900">Veri Önizleme</h2>
              <span class="text-xs font-medium bg-slate-100 text-slate-600 px-2 py-1 rounded">Son Yüklenen: performance_q3.csv</span>
          </div>
          
          <div class="overflow-x-auto">
              <table class="w-full text-left border-collapse">
                  <thead>
                      <tr class="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase">
                          <th class="px-6 py-3">ID</th>
                          <th class="px-6 py-3">Tarih</th>
                          <th class="px-6 py-3">Dosya Adı</th>
                          <th class="px-6 py-3">Kayıt Sayısı</th>
                          <th class="px-6 py-3">Durum</th>
                      </tr>
                  </thead>
                  <tbody class="divide-y divide-slate-100">
                      <tr v-for="item in uploadHistory" :key="item.id" class="hover:bg-slate-50">
                          <td class="px-6 py-3 text-sm text-slate-600">#{{ item.id }}</td>
                          <td class="px-6 py-3 text-sm text-slate-600">{{ item.date }}</td>
                          <td class="px-6 py-3 text-sm font-medium text-slate-900">{{ item.filename }}</td>
                          <td class="px-6 py-3 text-sm text-slate-600">{{ item.records }}</td>
                          <td class="px-6 py-3">
                              <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium" 
                                :class="item.status === 'Başarılı' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'">
                                  {{ item.status }}
                              </span>
                          </td>
                      </tr>
                  </tbody>
              </table>
          </div>
          
          <div class="p-4 border-t border-slate-200 flex justify-center">
               <button class="text-sm text-blue-600 hover:text-blue-700 font-medium">Tüm Geçmişi Görüntüle</button>
          </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { CloudArrowUpIcon, ArrowDownTrayIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'

const uploadHistory = ref([
    { id: 1042, date: '02.02.2026', filename: 'performance_q3.csv', records: 1450, status: 'Başarılı' },
    { id: 1041, date: '01.02.2026', filename: 'employees_update.xlsx', records: 42, status: 'Başarılı' },
    { id: 1040, date: '28.01.2026', filename: 'survey_results.json', records: 0, status: 'Hata' },
    { id: 1039, date: '15.01.2026', filename: 'performance_q2_final.csv', records: 1420, status: 'Başarılı' },
])
</script>
