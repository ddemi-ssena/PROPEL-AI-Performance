<template>
  <div>
    <h1 class="text-3xl font-bold text-slate-900 mb-2">Ayarlar</h1>
    <p class="text-slate-500 mb-8">Hesabınızı ve uygulama tercihlerinizi yönetin.</p>

    <div class="space-y-6">
      <!-- Profile Section -->
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div class="p-6 border-b border-slate-200">
            <h2 class="text-lg font-bold text-slate-900">Profil Bilgileri</h2>
            <p class="text-sm text-slate-500 mt-1">Kişisel bilgilerinizi buradan güncelleyin.</p>
        </div>
        <div class="p-6 space-y-6">
            <div class="flex items-center gap-6">
                <img :src="userAvatar" alt="Avatar" class="w-20 h-20 rounded-full" />
                <div>
                    <button class="px-4 py-2 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors shadow-sm">
                        Avatar Değiştir
                    </button>
                    <p class="text-xs text-slate-400 mt-2">JPG, GIF veya PNG. Maksimum 1MB.</p>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-2">Ad Soyad</label>
                    <input type="text" :value="userFullName" class="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-2">Unvan</label>
                    <input type="text" :value="userRole" disabled class="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm text-slate-500 cursor-not-allowed" />
                </div>
            </div>

            <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">E-posta Adresi</label>
                <div class="relative">
                    <EnvelopeIcon class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input type="email" :value="userEmail" class="w-full pl-10 pr-4 py-2 bg-white border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
                </div>
            </div>
        </div>
        <div class="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-end">
            <button class="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors shadow-sm shadow-blue-600/20">
                Değişiklikleri Kaydet
            </button>
        </div>
      </div>

      <!-- Password Section -->
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div class="p-6 border-b border-slate-200">
            <h2 class="text-lg font-bold text-slate-900">Şifre Güncelleme</h2>
            <p class="text-sm text-slate-500 mt-1">Güvenliğiniz için güçlü bir şifre kullandığınızdan emin olun.</p>
        </div>
        <div class="p-6 space-y-6">
            <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">Mevcut Şifre</label>
                <input type="password" class="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">Yeni Şifre</label>
                <input type="password" class="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">Şifre Tekrar</label>
                <input type="password" class="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
            </div>
        </div>
        <div class="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-end">
            <button class="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors shadow-sm shadow-blue-600/20">
                Şifreyi Güncelle
            </button>
        </div>
      </div>

      <!-- Preferences Section -->
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div class="p-6 border-b border-slate-200">
            <h2 class="text-lg font-bold text-slate-900">Tercihler</h2>
            <p class="text-sm text-slate-500 mt-1">Uygulama görünümünü ve dilini özelleştirin.</p>
        </div>
        <div class="p-6 space-y-6">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm font-medium text-slate-900">Karanlık Mod</p>
                    <p class="text-sm text-slate-500">Açık ve koyu tema arasında geçiş yapın.</p>
                </div>
                <button class="w-11 h-6 bg-slate-200 rounded-full relative transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                    <span class="absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform"></span>
                </button>
            </div>
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm font-medium text-slate-900">Dil</p>
                    <p class="text-sm text-slate-500">Tercih ettiğiniz dili seçin.</p>
                </div>
                <select class="px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500">
                    <option>Türkçe</option>
                    <option>English</option>
                    <option>Español</option>
                </select>
            </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { EnvelopeIcon } from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const userFullName = computed(() => authStore.user?.full_name || 'Kullanıcı Adı')
const userEmail = computed(() => authStore.user?.email || 'kullanici@propel.com')
const userRole = computed(() => authStore.user?.role || 'Kullanıcı Rolü')
const userAvatar = computed(() => `https://ui-avatars.com/api/?name=${userFullName.value}&background=f87171&color=fff`)
</script>
