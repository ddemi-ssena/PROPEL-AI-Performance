<template>
  <div class="min-h-screen flex items-center justify-center bg-[#0f172a] relative overflow-hidden font-sans">
    <!-- Background Decorative Elements -->
    <div class="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
      <div class="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-blue-600/20 blur-[120px] rounded-full"></div>
      <div class="absolute -bottom-[10%] -right-[10%] w-[40%] h-[40%] bg-indigo-600/20 blur-[120px] rounded-full"></div>
    </div>

    <!-- Main Container -->
    <div class="relative z-10 w-full max-w-5xl flex flex-col lg:flex-row items-stretch justify-center p-4 lg:p-0 gap-0 shadow-2xl rounded-3xl overflow-hidden border border-white/10 backdrop-blur-sm bg-slate-900/40">
      
      <!-- Left Panel: Branding & Marketing -->
      <div class="hidden lg:flex lg:w-5/12 bg-gradient-to-br from-indigo-600 via-blue-600 to-cyan-500 p-12 flex-col justify-between relative overflow-hidden">
        <!-- Pattern Overlay -->
        <div class="absolute inset-0 opacity-10 pointer-events-none">
           <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
             <defs>
               <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                 <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" stroke-width="1"/>
               </pattern>
             </defs>
             <rect width="100%" height="100%" fill="url(#grid)" />
           </svg>
        </div>

        <div class="relative z-10">
          <div class="flex items-center gap-3 group cursor-default">
            <div class="w-12 h-12 bg-white rounded-2xl flex items-center justify-center shadow-lg transform group-hover:rotate-12 transition-transform duration-300">
              <span class="text-indigo-600 font-black text-2xl">K</span>
            </div>
            <h1 class="text-white text-3xl font-black tracking-tighter">KUTUP</h1>
          </div>
        </div>

        <div class="relative z-10 text-white">
          <h2 class="text-5xl font-black mb-6 leading-tight tracking-tight">
            Performansın <br />
            Yeni <span class="text-cyan-200">Zirvesi.</span>
          </h2>
          <p class="text-xl text-blue-50/80 leading-relaxed font-medium">
            Yapay zeka destekli analizlerle ekibinizin gerçek potansiyelini keşfedin ve hedeflerinize emin adımlarla ilerleyin.
          </p>
        </div>

        <div class="relative z-10 flex items-center gap-4">
          <div class="flex -space-x-3">
             <div v-for="i in 4" :key="i" class="w-10 h-10 rounded-full border-2 border-white/20 bg-slate-800 flex items-center justify-center text-[10px] font-bold">
                {{ ['AY', 'MS', 'CD', 'ME'][i-1] }}
             </div>
          </div>
          <p class="text-sm text-white/70 font-medium">40+ Lider ekip tarafından kullanılıyor</p>
        </div>
      </div>

      <!-- Right Panel: Form & Test Accounts -->
      <div class="w-full lg:w-7/12 flex flex-col p-8 lg:p-16 bg-slate-900/60">
        <div class="w-full max-w-md mx-auto">
          <!-- Mobile Header -->
          <div class="lg:hidden flex items-center gap-2 mb-10">
            <div class="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center">
              <span class="text-white font-black text-xl">K</span>
            </div>
            <h1 class="text-white text-2xl font-black">KUTUP</h1>
          </div>

          <div class="mb-10 text-center lg:text-left">
            <h2 class="text-4xl font-black text-white mb-3 tracking-tight">Hoş Geldiniz</h2>
            <p class="text-slate-400 font-medium">Dashboard'unuza erişmek için giriş yapın.</p>
          </div>

          <!-- Error Alert -->
          <transition name="fade">
            <div v-if="authStore.error" class="mb-6 p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-center gap-3">
              <div class="w-8 h-8 rounded-full bg-rose-500/20 flex items-center justify-center shrink-0">
                <svg class="w-4 h-4 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p class="text-rose-200 text-sm font-medium">{{ authStore.error }}</p>
            </div>
          </transition>

          <form @submit.prevent="handleLogin" class="space-y-5">
            <!-- Email -->
            <div class="space-y-2">
              <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">
                E-POSTA ADRESİ
              </label>
              <div class="relative group">
                <span class="absolute inset-y-0 left-0 flex items-center pl-4 text-slate-500 group-focus-within:text-indigo-400 transition-colors">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </span>
                <input
                  v-model="credentials.username"
                  type="email"
                  placeholder="name@company.com"
                  class="w-full bg-slate-800/50 border border-slate-700 text-white text-sm rounded-2xl py-4 pl-12 pr-4 focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 outline-none transition-all placeholder:text-slate-600"
                  required
                />
              </div>
            </div>

            <!-- Password -->
            <div class="space-y-2">
              <div class="flex items-center justify-between px-1">
                <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest">
                  ŞİFRE
                </label>
                <a href="#" class="text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors">
                  Şifremi Unuttum?
                </a>
              </div>
              <div class="relative group">
                <span class="absolute inset-y-0 left-0 flex items-center pl-4 text-slate-500 group-focus-within:text-indigo-400 transition-colors">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </span>
                <input
                  v-model="credentials.password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="••••••••"
                  class="w-full bg-slate-800/50 border border-slate-700 text-white text-sm rounded-2xl py-4 pl-12 pr-12 focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 outline-none transition-all placeholder:text-slate-600"
                  required
                />
                <button
                  type="button"
                  @click="showPassword = !showPassword"
                  class="absolute inset-y-0 right-0 flex items-center pr-4 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  <svg v-if="!showPassword" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Login Button -->
            <button
              type="submit"
              :disabled="authStore.loading"
              class="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-4 rounded-2xl shadow-lg shadow-indigo-600/30 transition-all transform active:scale-[0.98] flex items-center justify-center overflow-hidden relative group"
            >
              <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:animate-[shimmer_2s_infinite]"></div>
              <span v-if="!authStore.loading" class="relative z-10">Giriş Yap</span>
              <span v-else class="relative z-10 flex items-center gap-2">
                <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Yükleniyor...
              </span>
            </button>
          </form>

          <!-- Quick Access / Test Accounts (Redesigned) -->
          <div class="mt-10">
            <div class="flex items-center gap-3 mb-4">
              <div class="h-px bg-slate-800 flex-1"></div>
              <span class="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">HIZLI ERİŞİM</span>
              <div class="h-px bg-slate-800 flex-1"></div>
            </div>
            
            <div class="grid grid-cols-1 gap-3">
              <!-- Admin -->
              <div 
                @click="fillCredentials('admin@propel.com', 'admin123')"
                class="group p-3 rounded-2xl bg-slate-800/40 border border-slate-700 hover:border-indigo-500/50 hover:bg-indigo-500/5 transition-all cursor-pointer flex items-center justify-between"
              >
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 group-hover:bg-indigo-500 group-hover:text-white transition-all">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                  </div>
                  <div>
                    <p class="text-xs font-bold text-white">Sistem Admin</p>
                    <p class="text-[10px] text-slate-500">Tam Yetki</p>
                  </div>
                </div>
                <div class="text-[10px] text-slate-600 font-mono group-hover:text-slate-400 transition-colors">admin123</div>
              </div>

              <!-- Software Group -->
              <div class="grid grid-cols-2 gap-3">
                <div 
                  @click="fillCredentials('manager.yazilim@propel.com', 'manager123')"
                  class="group p-3 rounded-2xl bg-slate-800/40 border border-slate-700 hover:border-blue-500/50 hover:bg-blue-500/5 transition-all cursor-pointer"
                >
                  <p class="text-[10px] font-bold text-slate-500 mb-1 group-hover:text-blue-400 transition-colors uppercase">YAZILIM</p>
                  <p class="text-xs font-bold text-white mb-1">Bölüm Müdürü</p>
                  <p class="text-[10px] text-slate-600 font-mono">manager123</p>
                </div>
                <div 
                  @click="fillCredentials('developer1@propel.com', 'dev123')"
                  class="group p-3 rounded-2xl bg-slate-800/40 border border-slate-700 hover:border-blue-500/50 hover:bg-blue-500/5 transition-all cursor-pointer"
                >
                  <p class="text-[10px] font-bold text-slate-500 mb-1 group-hover:text-blue-400 transition-colors uppercase">YAZILIM</p>
                  <p class="text-xs font-bold text-white mb-1">Yazılım Uzmanı</p>
                  <p class="text-[10px] text-slate-600 font-mono">dev123</p>
                </div>
              </div>

              <!-- Sales Group -->
              <div class="grid grid-cols-2 gap-3">
                <div 
                  @click="fillCredentials('manager.satis@propel.com', 'manager123')"
                  class="group p-3 rounded-2xl bg-slate-800/40 border border-slate-700 hover:border-cyan-500/50 hover:bg-cyan-500/5 transition-all cursor-pointer"
                >
                  <p class="text-[10px] font-bold text-slate-500 mb-1 group-hover:text-cyan-400 transition-colors uppercase">SATIŞ</p>
                  <p class="text-xs font-bold text-white mb-1">Bölüm Müdürü</p>
                  <p class="text-[10px] text-slate-600 font-mono">manager123</p>
                </div>
                <div 
                  @click="fillCredentials('satis.employee@propel.com', 'satis123')"
                  class="group p-3 rounded-2xl bg-slate-800/40 border border-slate-700 hover:border-cyan-500/50 hover:bg-cyan-500/5 transition-all cursor-pointer"
                >
                  <p class="text-[10px] font-bold text-slate-500 mb-1 group-hover:text-cyan-400 transition-colors uppercase">SATIŞ</p>
                  <p class="text-xs font-bold text-white mb-1">Satış Uzmanı</p>
                  <p class="text-[10px] text-slate-600 font-mono">satis123</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Register Link -->
          <p class="mt-10 text-center text-sm text-slate-500">
            Hesabınız yok mu?
            <router-link to="/register" class="text-indigo-400 hover:text-indigo-300 font-bold transition-colors">
              Hemen Kaydolun
            </router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const credentials = ref({
  username: '',
  password: '',
})

const showPassword = ref(false)

function fillCredentials(user: string, pass: string) {
  credentials.value.username = user
  credentials.value.password = pass
}

async function handleLogin() {
  const success = await authStore.login(credentials.value)

  if (success) {
    const role = authStore.user?.role

    if (role === 'admin') {
      router.push('/admin')
    } else if (role === 'department_manager') {
      router.push('/manager')
    } else if (role === 'employee') {
      const departmentName = authStore.user?.department_name?.toLocaleLowerCase('tr-TR') || ''
      const normalizedDepartmentName = departmentName.replace(/\u0131/g, 'i').replace(/\u015f/g, 's')
      const email = authStore.user?.email?.toLocaleLowerCase('tr-TR') || ''
      const isSales = normalizedDepartmentName.includes('satis') || email.includes('satis') || email.startsWith('sa-') || email.startsWith('sl-')
      router.push(isSales ? '/employee/sales' : '/employee')
    } else {
      router.push('/dashboard')
    }
  }
}
</script>

<style scoped>
@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Custom Scrollbar for the container if needed */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
