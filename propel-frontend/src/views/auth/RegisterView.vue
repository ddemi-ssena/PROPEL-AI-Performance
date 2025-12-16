<template>
  <div class="min-h-screen flex">
    <!-- Sol Panel - Bilgi (Login ile aynı görsel) -->
    <div class="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-500 to-primary-700 p-12 flex-col justify-between">
      <div class="flex items-center gap-3">
        <div class="w-12 h-12 bg-white rounded-full flex items-center justify-center">
          <span class="text-primary-500 font-bold text-xl">P</span>
        </div>
        <h1 class="text-white text-2xl font-bold">propel</h1>
      </div>

      <div class="text-white">
        <h2 class="text-4xl font-bold mb-4">
          Veriyle Güçlen,<br />
          Ekibini Kur
        </h2>
        <p class="text-lg text-primary-100">
          Hemen hesap oluşturarak ekibinizin performansını izlemeye başlayın.
        </p>
      </div>

      <div class="w-full h-64 bg-white/10 rounded-lg backdrop-blur-sm flex items-center justify-center">
        <p class="text-white/50">Illustration placeholder</p>
      </div>
    </div>

    <!-- Sağ Panel - Kayıt Formu -->
    <div class="w-full lg:w-1/2 flex items-center justify-center p-8">
      <div class="w-full max-w-lg">
        <div class="mb-8">
          <h2 class="text-3xl font-bold text-gray-900 mb-2">Yeni Hesap Oluştur</h2>
          <p class="text-gray-600">Performans yönetim sistemine katılın.</p>
        </div>

        <!-- Hata Mesajı -->
        <div v-if="authStore.error" class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p class="text-red-700 text-sm">{{ authStore.error }}</p>
        </div>
        <div v-if="successMessage" class="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p class="text-green-700 text-sm">{{ successMessage }}</p>
        </div>

        <form @submit.prevent="handleRegister" class="space-y-6">
          
          <!-- Tam Ad -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Tam Adınız</label>
            <input v-model="registerData.full_name" type="text" placeholder="Ad Soyad" class="input-field" required />
          </div>

          <!-- Email -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Kurumsal E-posta</label>
            <input v-model="registerData.email" type="email" placeholder="ornek@propel.com" class="input-field" required />
          </div>

          <!-- Password -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Şifre</label>
            <div class="relative">
              <input 
                v-model="registerData.password" 
                :type="showPassword ? 'text' : 'password'" 
                placeholder="Güçlü bir şifre girin" 
                class="input-field pr-10" 
                required 
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute inset-y-0 right-0 flex items-center pr-3"
              >
                 <svg v-if="!showPassword" class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <svg v-else class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Rol Seçimi (Sadece Admin ilk kurulumda Admin/Manager olabilir, normalde sadece Employee) -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Rol Seçimi</label>
            <select v-model="registerData.role" class="input-field">
                <option value="employee">Çalışan (Employee)</option>
                <option value="department_manager">Departman Müdürü (Manager)</option>
                <option value="admin">Yönetici (Admin)</option>
            </select>
          </div>

          <!-- Kayıt Butonu -->
          <button
            type="submit"
            :disabled="authStore.loading"
            class="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="!authStore.loading">Hesap Oluştur</span>
            <span v-else class="flex items-center justify-center gap-2">
              <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Oluşturuluyor...
            </span>
          </button>
        </form>

        <!-- Login Link -->
        <p class="mt-6 text-center text-sm text-gray-600">
          Zaten bir hesabınız var mı?
          <router-link to="/login" class="text-primary-500 hover:text-primary-600 font-medium">
            Giriş Yapın
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { RegisterData } from '@/services/types/auth.types'
import { authApi } from '@/services/api/auth.api' // authApi'yi import ettik

const router = useRouter()
const authStore = useAuthStore()

const registerData = ref<RegisterData>({
  email: '',
  password: '',
  full_name: '',
  role: 'employee', // Varsayılan rol
})

const showPassword = ref(false)
const successMessage = ref<string | null>(null)

async function handleRegister() {
  authStore.error = null // Hata mesajını temizle
  successMessage.value = null // Başarı mesajını temizle
  authStore.loading = true

  try {
    // API çağrısı
    await authApi.register(registerData.value)
    
    // Başarılı olursa
    successMessage.value = 'Hesap başarıyla oluşturuldu! Şimdi giriş yapabilirsiniz.'
    
    // Yönlendirme: Başarılı kayıttan sonra Login sayfasına yönlendir
    setTimeout(() => {
      router.push({ name: 'login' })
    }, 2000)

  } catch (err: any) {
    authStore.error = err.response?.data?.detail || 'Kayıt Başarısız. E-posta zaten kayıtlı olabilir.'
  } finally {
    authStore.loading = false
  }
}
</script>