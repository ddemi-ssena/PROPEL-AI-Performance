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
                 <select v-model="selectedDataType" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none">
                     <option>Performans Metrikleri (KPI)</option>
                     <option>Personel Listesi</option>
                     <option>Anket Sonuçları</option>
                 </select>
             </div>

             <div v-if="selectedDataType === 'Performans Metrikleri (KPI)'" class="mb-4">
                 <label class="block text-sm font-medium text-slate-700 mb-1">Departman</label>
                 <select v-model="selectedDepartmentKey" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none">
                     <option value="software">Yazilim</option>
                     <option value="sales">Satis</option>
                 </select>
                 <p class="mt-2 text-xs text-slate-500">
                   Yazilim importer'i canli, satis importer'i ise ayni analytics omurgasina baglanmaya hazir placeholder modunda.
                 </p>
             </div>

             <div 
                class="border-2 border-dashed border-slate-300 rounded-xl p-8 flex flex-col items-center justify-center text-center hover:bg-slate-50 transition-colors cursor-pointer"
                @click="triggerFileInput"
                @dragover.prevent="isDragging = true"
                @dragleave.prevent="isDragging = false"
                @drop.prevent="handleDrop"
                :class="{ 'border-blue-500 bg-blue-50': isDragging }"
             >
                 <CloudArrowUpIcon class="w-12 h-12 text-blue-500 mb-3" />
                 <p class="text-sm font-medium text-slate-900">
                   {{ selectedFile ? selectedFile.name : 'Dosyayı sürükleyin veya seçin' }}
                 </p>
                 <p class="text-xs text-slate-500 mt-1">CSV, Excel veya JSON (max 10MB)</p>
                 <input 
                    type="file" 
                    ref="fileInput" 
                    class="hidden" 
                    accept=".csv,.xlsx,.json"
                    @change="handleFileChange"
                 />
             </div>

             <button 
                class="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded-lg transition-colors shadow-sm shadow-blue-600/20 flex items-center justify-center gap-2"
                @click="startUpload"
                :disabled="isUploading || !selectedFile"
             >
                 <span v-if="isUploading" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                 {{ isUploading ? 'Yükleniyor...' : 'Yüklemeyi Başlat' }}
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
              <span v-if="latestUpload" class="text-xs font-medium bg-slate-100 text-slate-600 px-2 py-1 rounded">
                Son Yüklenen: {{ latestUpload.file_name }}
              </span>
          </div>
          
          <div class="overflow-x-auto min-h-[300px] relative">
              <div v-if="isLoadingHistory" class="absolute inset-0 bg-white/50 flex items-center justify-center z-10">
                  <div class="w-8 h-8 border-4 border-blue-600/20 border-t-blue-600 rounded-full animate-spin"></div>
              </div>
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
                          <td class="px-6 py-3 text-sm text-slate-600">{{ formatDate(item.upload_date) }}</td>
                          <td class="px-6 py-3 text-sm font-medium text-slate-900">
                            <div>{{ item.file_name }}</div>
                            <div v-if="item.raw_info?.department_key" class="mt-1 text-xs font-medium text-slate-500">
                              {{ item.raw_info.department_key }}
                            </div>
                          </td>
                          <td class="px-6 py-3 text-sm text-slate-600">{{ item.record_count }}</td>
                          <td class="px-6 py-3">
                              <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium" 
                                :class="getStatusClass(item.status)">
                                  {{ getStatusLabel(item.status) }}
                              </span>
                          </td>
                      </tr>
                      <tr v-if="uploadHistory.length === 0 && !isLoadingHistory">
                          <td colspan="5" class="px-6 py-8 text-center text-slate-500 text-sm">
                              Henüz bir veri yüklemesi yapılmamış.
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
import { ref, onMounted, computed } from 'vue'
import { CloudArrowUpIcon, ArrowDownTrayIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import { adminUploadApi } from '@/services/api/admin_upload.api'

const uploadHistory = ref<any[]>([])
const selectedDataType = ref('Performans Metrikleri (KPI)')
const selectedDepartmentKey = ref('software')
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const isDragging = ref(false)
const isUploading = ref(false)
const isLoadingHistory = ref(false)

const latestUpload = computed(() => uploadHistory.value[0] || null)

const fetchHistory = async () => {
    isLoadingHistory.value = true
    try {
        const data = await adminUploadApi.getUploadHistory()
        uploadHistory.value = data
    } catch (e) {
        console.error("Failed to fetch upload history", e)
    } finally {
        isLoadingHistory.value = false
    }
}

onMounted(() => {
    fetchHistory()
})

const triggerFileInput = () => {
    fileInput.value?.click()
}

const handleFileChange = (event: Event) => {
    const target = event.target as HTMLInputElement
    if (target.files && target.files[0]) {
        selectedFile.value = target.files[0]
    }
}

const handleDrop = (event: DragEvent) => {
    isDragging.value = false
    if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
        selectedFile.value = event.dataTransfer.files[0]
    }
}

const startUpload = async () => {
    if (!selectedFile.value) return
    
    isUploading.value = true
    try {
        await adminUploadApi.uploadFile(
          selectedFile.value,
          selectedDataType.value,
          selectedDataType.value === 'Performans Metrikleri (KPI)' ? selectedDepartmentKey.value : undefined
        )
        selectedFile.value = null
        await fetchHistory()
    } catch (e: any) {
        alert(e.response?.data?.detail || "Yükleme sırasında bir hata oluştu.")
    } finally {
        isUploading.value = false
    }
}

const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('tr-TR')
}

const getStatusClass = (status: string) => {
    switch (status) {
        case 'Success': return 'bg-green-100 text-green-700'
        case 'Error': return 'bg-red-100 text-red-700'
        case 'Processing': return 'bg-blue-100 text-blue-700'
        default: return 'bg-slate-100 text-slate-700'
    }
}

const getStatusLabel = (status: string) => {
    switch (status) {
        case 'Success': return 'Başarılı'
        case 'Error': return 'Hata'
        case 'Processing': return 'İşleniyor'
        default: return status
    }
}
</script>
