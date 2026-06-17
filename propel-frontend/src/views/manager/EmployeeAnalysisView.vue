<template>
  <div class="space-y-8 pb-10">
    <div class="flex flex-col md:flex-row justify-between items-end gap-4 border-b border-slate-200 pb-6">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 tracking-tight">360 Calisan Raporu</h2>
        <p class="text-slate-500 mt-1">
          Ekipteki calisanlarin KPI performansi, 360 feedback, NLP sinyali ve yonetici ozetlerini birlikte inceleyin.
        </p>
      </div>
      <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <!-- Admin Department Filter -->
        <select
          v-if="isAdmin"
          v-model="selectedDepartmentId"
          class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm"
        >
          <option :value="null">Tüm Departmanlar</option>
          <option v-for="dept in departments" :key="dept.id" :value="dept.id">
            {{ dept.name }}
          </option>
        </select>

        <select
          v-model="selectedTeam"
          class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm"
        >
          <option value="all">Tüm Takımlar</option>
          <option v-for="team in teamOptions" :key="team" :value="team">
            {{ team }}
          </option>
        </select>
        <div class="rounded-full border border-indigo-100 bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-700">
          {{ filteredTeamMembers.length }} çalışan listeleniyor
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-[360px_minmax(0,1fr)] gap-8">
      <!-- Left Selection Sidebar -->
      <aside class="xl:sticky xl:top-24 h-fit max-h-[calc(100vh-120px)] flex flex-col rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div class="border-b border-slate-100 px-5 py-4 bg-slate-50/50">
          <div class="flex items-center justify-between mb-3">
             <h3 class="text-lg font-bold text-slate-900">Çalışan Seçimi</h3>
             <UsersIcon class="w-5 h-5 text-slate-400" />
          </div>
          <!-- Search Bar -->
          <div class="relative">
            <MagnifyingGlassIcon class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input 
              v-model="searchQuery"
              type="text" 
              placeholder="İsim veya pozisyon ara..." 
              class="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none transition-all"
            />
          </div>
        </div>

        <div v-if="filteredAndSearchedMembers.length" class="flex-1 overflow-y-auto p-3 space-y-3 custom-scrollbar">
          <button
            v-for="employee in filteredAndSearchedMembers"
            :key="employee.id"
            type="button"
            class="w-full rounded-2xl border p-4 text-left transition-all group relative overflow-hidden"
            :class="selectedEmployeeId === employee.id
              ? 'border-indigo-600 bg-indigo-50/50 ring-1 ring-indigo-600 shadow-md'
              : 'border-slate-100 bg-white hover:border-slate-300 hover:bg-slate-50'"
            @click="selectedEmployeeId = employee.id"
          >
            <!-- Active Indicator -->
            <div v-if="selectedEmployeeId === employee.id" class="absolute left-0 top-0 bottom-0 w-1 bg-indigo-600"></div>

            <div class="flex items-start justify-between gap-3">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <p class="font-bold text-slate-900 truncate">{{ employee.user.full_name }}</p>
                </div>
                <div class="mt-1 flex flex-col gap-1">
                  <span class="text-xs text-slate-500 truncate font-medium">{{ employee.position || 'Çalışan' }}</span>
                  <div class="flex flex-wrap gap-1.5 mt-1">
                    <span
                      v-if="employee.team"
                      class="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-600 uppercase tracking-tight"
                    >
                      {{ employee.team }}
                    </span>
                    <span
                      class="rounded-full bg-indigo-100 px-2 py-0.5 text-[10px] font-bold text-indigo-700 uppercase tracking-tight"
                    >
                      {{ employee.department?.name || 'Genel' }}
                    </span>
                  </div>
                </div>
              </div>
              <div class="flex flex-col items-end gap-2">
                  <div v-if="employeeReportBadges(employee.id).length" class="flex -space-x-1">
                    <BadgeMedal
                      v-for="badge in employeeReportBadges(employee.id).slice(0, 3)"
                      :key="`list-badge-${employee.id}-${badge.id}`"
                      :badge-type="badge.badge_type"
                      :badge-level="badge.badge_level"
                      size="xs"
                      :description="getBadgeDescription(badge)"
                    />
                  </div>
                  <ChevronRightIcon class="w-4 h-4 text-slate-300 group-hover:text-indigo-400 transition-colors" />
              </div>
            </div>
            
            <p v-if="getPreviewSummary(employee.id)" class="mt-3 text-[11px] leading-4 text-slate-500 line-clamp-2 border-t border-slate-100 pt-2 italic">
              "{{ getPreviewSummary(employee.id) }}"
            </p>
          </button>
        </div>

        <div v-else class="p-8 text-center">
          <div class="bg-slate-50 rounded-2xl p-4 mb-4 inline-block">
            <UsersIcon class="w-8 h-8 text-slate-300" />
          </div>
          <p class="text-sm font-medium text-slate-900">Çalışan Bulunamadı</p>
          <p class="text-xs text-slate-500 mt-1">Arama kriterlerini değiştirmeyi deneyin.</p>
        </div>
      </aside>

      <!-- Right Content Area -->
      <div class="min-w-0">
        <section v-if="selectedEmployeeReport" class="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <!-- Main Profile Card -->
          <div class="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm relative overflow-hidden">
            <!-- Decorative Gradient -->
            <div class="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full -mr-32 -mt-32 blur-3xl"></div>

            <div class="relative z-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
              <div class="flex items-center gap-6">
                 <div class="w-20 h-20 rounded-2xl bg-indigo-600 flex items-center justify-center text-2xl font-bold text-white shadow-xl shadow-indigo-600/20">
                    {{ selectedEmployeeReport.employee_name.split(' ').map(n => n[0]).join('').toUpperCase() }}
                 </div>
                 <div>
                    <div class="flex items-center gap-3">
                      <h3 class="text-3xl font-bold text-slate-900 tracking-tight">{{ selectedEmployeeReport.employee_name }}</h3>
                      <span class="rounded-full border border-indigo-100 bg-indigo-50 px-3 py-1 text-xs font-bold text-indigo-700 uppercase tracking-wider">
                        Hafta {{ selectedEmployeeReport.period_week }}
                      </span>
                    </div>
                    <div class="mt-2 flex flex-wrap items-center gap-4 text-slate-500 font-medium">
                      <span class="flex items-center gap-1.5">
                        <BriefcaseIcon class="w-4 h-4" />
                        {{ selectedEmployeeReport.position || 'Çalışan' }}
                      </span>
                      <span class="w-1 h-1 bg-slate-300 rounded-full"></span>
                      <span class="flex items-center gap-1.5">
                        <BuildingOfficeIcon class="w-4 h-4" />
                        {{ selectedEmployeeReport.department_name || 'Departman Atanmadı' }}
                      </span>
                      <span v-if="selectedEmployeeReport.team" class="w-1 h-1 bg-slate-300 rounded-full"></span>
                      <span v-if="selectedEmployeeReport.team" class="flex items-center gap-1.5">
                        <UserGroupIcon class="w-4 h-4" />
                        {{ selectedEmployeeReport.team }} Takımı
                      </span>
                    </div>
                 </div>
              </div>
              
              <div class="flex gap-3">
                 <button class="px-5 py-2.5 bg-white border border-slate-200 text-slate-700 text-sm font-bold rounded-xl hover:bg-slate-50 transition-all shadow-sm">
                    PDF Raporu
                 </button>
                 <button class="px-5 py-2.5 bg-slate-900 text-white text-sm font-bold rounded-xl hover:bg-slate-800 transition-all shadow-lg shadow-slate-900/20">
                    Feedback İste
                 </button>
              </div>
            </div>

            <!-- Weekly Summary Box -->
            <div class="mt-8 grid grid-cols-1 lg:grid-cols-4 gap-6">
              <div class="lg:col-span-3 rounded-2xl bg-slate-50 border border-slate-100 p-6">
                <div class="flex items-center gap-2 mb-4">
                   <div class="p-1.5 bg-indigo-600 rounded-lg">
                      <DocumentTextIcon class="w-4 h-4 text-white" />
                   </div>
                   <h4 class="text-sm font-bold text-slate-900 uppercase tracking-wider">Haftalık Yönetici Özeti</h4>
                </div>
                <p class="text-slate-700 leading-relaxed text-sm md:text-base">
                  {{ renderText(selectedEmployeeReport.report_summary) }}
                </p>

                <div v-if="managerEvidenceSection?.items.length" class="mt-5 rounded-xl border border-indigo-100 bg-white p-4">
                  <p class="text-[11px] font-bold uppercase tracking-widest text-indigo-600 mb-3">Veriye Dayalı Kanıtlar</p>
                  <ul class="space-y-2">
                    <li
                      v-for="item in managerEvidenceSection.items.slice(0, 6)"
                      :key="item"
                      class="flex gap-2 text-sm text-slate-700"
                    >
                      <span class="mt-2 h-1.5 w-1.5 flex-none rounded-full bg-indigo-500"></span>
                      <span>{{ renderText(item) }}</span>
                    </li>
                  </ul>
                </div>
                
                <div v-if="qualityWarningSection || biasWarningSection" class="mt-6 flex flex-wrap gap-4">
                  <div v-if="qualityWarningSection" class="flex items-center gap-2 bg-amber-50 text-amber-700 px-3 py-2 rounded-xl border border-amber-100 text-xs font-bold">
                    <ExclamationTriangleIcon class="w-4 h-4" />
                    <span>Veri Kalitesi Uyarısı: {{ qualityWarningSection.items.join(', ') }}</span>
                  </div>
                  <div v-if="biasWarningSection" class="flex items-center gap-2 bg-rose-50 text-rose-700 px-3 py-2 rounded-xl border border-rose-100 text-xs font-bold">
                    <HandRaisedIcon class="w-4 h-4" />
                    <span>Bias Şüphesi: {{ biasWarningSection.items.join(', ') }}</span>
                  </div>
                </div>
              </div>
              
              <!-- Mini Stats Sidebar in Profile -->
              <div class="space-y-4">
                <div v-if="selectedEmployeeReport.badges?.length" class="bg-white rounded-2xl border border-slate-100 p-5 shadow-sm">
                   <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4">Kazanılan Rozetler</p>
                   <div class="flex flex-wrap gap-3">
                      <div v-for="badge in selectedEmployeeReport.badges" :key="`badge-big-${badge.id}`">
                        <BadgeMedal
                          :badge-type="badge.badge_type"
                          :badge-level="badge.badge_level"
                          size="sm"
                          show-label
                          :description="getBadgeDescription(badge)"
                        />
                      </div>
                   </div>
                </div>
              </div>
            </div>
          </div>

          <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-5">
              <div>
                <h4 class="text-lg font-bold text-slate-900">KPI / ML Performans Özeti</h4>
                <p class="mt-1 text-sm text-slate-500">Seçili çalışanın canlı KPI performans özetinden gelen sinyaller.</p>
              </div>
              <span
                class="w-fit rounded-full border px-3 py-1 text-xs font-bold"
                :class="kpiStatusClass(selectedKpiRow?.status)"
              >
                {{ selectedKpiRow ? kpiStatusLabel(selectedKpiRow.status) : 'KPI verisi yok' }}
              </span>
            </div>

            <div v-if="selectedKpiRow?.has_kpi_data" class="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <p class="text-xs font-bold uppercase tracking-wider text-slate-500">KPI Skoru</p>
                <p class="mt-2 text-2xl font-bold text-slate-900">{{ selectedKpiRow.kpi_score ?? '-' }}/100</p>
              </div>
              <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <p class="text-xs font-bold uppercase tracking-wider text-slate-500">Trend</p>
                <p class="mt-2 text-2xl font-bold" :class="Number(selectedKpiRow.trend || 0) < 0 ? 'text-rose-600' : 'text-emerald-600'">
                  {{ formatKpiTrend(selectedKpiRow.trend) }}
                </p>
              </div>
              <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <p class="text-xs font-bold uppercase tracking-wider text-slate-500">Kayıt Sayısı</p>
                <p class="mt-2 text-2xl font-bold text-slate-900">{{ selectedKpiRow.record_count }}</p>
              </div>
              <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <p class="text-xs font-bold uppercase tracking-wider text-slate-500">Son Dönem</p>
                <p class="mt-2 text-sm font-bold text-slate-900">{{ selectedKpiRow.latest_period || '-' }}</p>
              </div>
            </div>
            <div v-else class="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
              Bu çalışan için KPI kaydı bulunamadı. KPI analizi görünmüyorsa admin dataset/KPI kayıtlarını ve seçili departman kapsamını kontrol edin.
            </div>
          </div>

          <!-- Analysis Grid -->
          <div class="grid grid-cols-1 xl:grid-cols-[minmax(0,1.2fr)_360px] gap-8">
            <!-- Monthly Deep Analysis -->
            <div class="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
              <div class="flex items-center justify-between gap-4 mb-8">
                <div>
                  <h4 class="text-xl font-bold text-slate-900">Aylık Derin Analiz</h4>
                  <p class="text-sm text-slate-500 mt-1">NLP tabanlı duygu ve trend analizi</p>
                </div>
                <div class="flex gap-2">
                  <select v-model="selectedMonth" class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-bold text-slate-700 outline-none focus:ring-2 focus:ring-indigo-500/20">
                    <option v-for="month in monthOptions" :key="month.value" :value="month.value">{{ month.label }}</option>
                  </select>
                  <select v-model="selectedYear" class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-bold text-slate-700 outline-none focus:ring-2 focus:ring-indigo-500/20">
                    <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}</option>
                  </select>
                </div>
              </div>

              <div v-if="monthlyDeepAnalysis" class="space-y-8">
                <!-- Monthly 360 metrics -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div class="bg-slate-50 rounded-2xl p-5 border border-slate-100 flex flex-col items-center text-center">
                    <div class="p-2 bg-indigo-100 rounded-xl mb-3"><ArrowTrendingUpIcon class="w-5 h-5 text-indigo-600" /></div>
                    <p class="text-xs font-bold text-slate-500 uppercase tracking-wider">Motivasyon</p>
                    <p class="mt-2 text-2xl font-bold text-slate-900">{{ formatTrend(monthlyDeepAnalysis.motivation_trend_direction) }}</p>
                  </div>
                  <div class="bg-slate-50 rounded-2xl p-5 border border-slate-100 flex flex-col items-center text-center">
                    <div class="p-2 bg-blue-100 rounded-xl mb-3"><FaceSmileIcon class="w-5 h-5 text-blue-600" /></div>
                    <p class="text-xs font-bold text-slate-500 uppercase tracking-wider">Duygu Trendi</p>
                    <p class="mt-2 text-2xl font-bold text-slate-900">{{ formatTrend(monthlyDeepAnalysis.sentiment_trend_direction) }}</p>
                  </div>
                  <div class="bg-slate-50 rounded-2xl p-5 border border-slate-100 flex flex-col items-center text-center">
                    <div class="p-2 bg-rose-100 rounded-xl mb-3"><ExclamationCircleIcon class="w-5 h-5 text-rose-600" /></div>
                    <p class="text-xs font-bold text-slate-500 uppercase tracking-wider">Ayrılma Riski</p>
                    <p class="mt-2 text-2xl font-bold text-slate-900">{{ monthlyDeepAnalysis.flight_risk_score ?? '-' }}/10</p>
                  </div>
                </div>

                <div v-if="burnoutDriverItems.length" class="rounded-2xl border border-amber-200 bg-amber-50 p-5">
                  <div class="flex items-start justify-between gap-4">
                    <div>
                      <h5 class="text-xs font-bold text-amber-700 uppercase tracking-widest">Burnout Risk Drivers</h5>
                      <p class="mt-1 text-sm text-amber-900">
                        Risk etiketi, tekrarlayan tema ve skor trendlerinden uretilen aciklanabilir sinyallerle desteklenir.
                      </p>
                    </div>
                    <span
                      v-if="monthlyDeepAnalysis.burnout_risk_level"
                      class="rounded-full border border-amber-300 bg-white px-3 py-1 text-xs font-bold text-amber-800"
                    >
                      {{ formatRiskLabel(monthlyDeepAnalysis.burnout_risk_level) }}
                    </span>
                  </div>
                  <div class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div
                      v-for="driver in burnoutDriverItems"
                      :key="driver.label + driver.evidence"
                      class="rounded-xl border border-amber-100 bg-white p-4"
                    >
                      <p class="text-sm font-bold text-slate-900">{{ renderText(driver.label) }}</p>
                      <p class="mt-2 text-xs leading-5 text-slate-600">{{ renderText(driver.evidence) }}</p>
                    </div>
                  </div>
                </div>

                <!-- Theme Lists -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div class="space-y-4">
                    <h5 class="text-xs font-bold text-rose-600 uppercase tracking-widest flex items-center gap-2">
                       <span class="w-1.5 h-1.5 bg-rose-600 rounded-full"></span>
                       Şikayet Konuları
                    </h5>
                    <div class="flex flex-wrap gap-2">
                      <span v-for="item in monthlyDeepAnalysis.top_complaint_topics" :key="item" class="bg-rose-50 text-rose-700 px-2.5 py-1 rounded-lg text-xs font-bold border border-rose-100">
                        {{ renderText(item) }}
                      </span>
                      <p v-if="!monthlyDeepAnalysis.top_complaint_topics.length" class="text-xs text-slate-400">Veri yok</p>
                    </div>
                  </div>
                  <div class="space-y-4">
                    <h5 class="text-xs font-bold text-emerald-600 uppercase tracking-widest flex items-center gap-2">
                       <span class="w-1.5 h-1.5 bg-emerald-600 rounded-full"></span>
                       Güçlü Alanlar
                    </h5>
                    <div class="flex flex-wrap gap-2">
                      <span v-for="item in monthlyDeepAnalysis.top_praise_topics" :key="item" class="bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-lg text-xs font-bold border border-emerald-100">
                        {{ renderText(item) }}
                      </span>
                      <p v-if="!monthlyDeepAnalysis.top_praise_topics.length" class="text-xs text-slate-400">Veri yok</p>
                    </div>
                  </div>
                  <div class="space-y-4">
                    <h5 class="text-xs font-bold text-sky-600 uppercase tracking-widest flex items-center gap-2">
                       <span class="w-1.5 h-1.5 bg-sky-600 rounded-full"></span>
                       Öne Çıkan Temalar
                    </h5>
                    <div class="flex flex-wrap gap-2">
                      <span v-for="item in monthlyDeepAnalysis.top_themes" :key="item" class="bg-sky-50 text-sky-700 px-2.5 py-1 rounded-lg text-xs font-bold border border-sky-100">
                        {{ renderText(item) }}
                      </span>
                      <p v-if="!monthlyDeepAnalysis.top_themes.length" class="text-xs text-slate-400">Veri yok</p>
                    </div>
                  </div>
                </div>
                
                <!-- RAG Section -->
                <div v-if="monthlyRagReport" class="bg-indigo-900 rounded-2xl p-6 text-white relative overflow-hidden shadow-xl">
                   <div class="absolute top-0 right-0 p-4 opacity-5">
                      <SparklesIcon class="w-24 h-24 text-indigo-200" />
                   </div>
                   <div class="relative z-10">
                      <div class="flex items-center justify-between mb-4">
                         <h5 class="text-sm font-bold uppercase tracking-widest text-indigo-300">Yapay Zeka Bellek Analizi (RAG)</h5>
                         <div class="bg-white/10 px-2 py-1 rounded-lg text-[10px] font-bold backdrop-blur-sm border border-white/10">
                            {{ monthlyRagReport.retrieved_memory_count }} Benzer Kayıt Taraması
                         </div>
                      </div>
                      <p class="text-sm leading-relaxed text-indigo-50 font-medium">
                        {{ renderText(monthlyRagReport.report_summary) }}
                      </p>
                      
                      <div class="mt-6 grid grid-cols-2 gap-4">
                         <div class="bg-white/5 rounded-xl p-4 border border-white/10">
                            <p class="text-[10px] font-bold text-indigo-300 uppercase mb-2">Trend Değerlendirmesi</p>
                            <p class="text-xs text-indigo-100 leading-relaxed">{{ renderText(monthlyRagReport.trend_summary) }}</p>
                         </div>
                         <div class="bg-white/5 rounded-xl p-4 border border-white/10">
                            <p class="text-[10px] font-bold text-indigo-300 uppercase mb-2">Elde Tutma Riski</p>
                            <div class="flex items-baseline gap-2">
                               <span class="text-xl font-bold">{{ monthlyRagReport.flight_risk_score ?? '-' }}/10</span>
                               <span v-if="monthlyRagReport.retention_risk_level" class="text-[10px] font-bold px-2 py-0.5 rounded bg-white/10">{{ formatRiskLabel(monthlyRagReport.retention_risk_level) }}</span>
                            </div>
                         </div>
                      </div>
                   </div>
                </div>
              </div>

              <div v-else class="py-20 text-center text-slate-400">
                <CloudIcon class="w-12 h-12 mx-auto mb-4 opacity-20" />
                <p>Seçili dönem için analiz verisi henüz bulunmuyor.</p>
              </div>
            </div>

            <!-- Side Cards -->
            <div class="space-y-8">
              <!-- Manager Action Card -->
              <div class="rounded-2xl border border-slate-900 bg-slate-900 p-8 shadow-xl text-white">
                 <div class="flex items-center gap-3 mb-6">
                    <div class="p-2 bg-indigo-500 rounded-xl"><BoltIcon class="w-5 h-5 text-white" /></div>
                    <h4 class="text-lg font-bold">Yönetici Aksiyonu</h4>
                 </div>
                 <div class="p-5 bg-white/5 rounded-2xl border border-white/10 mb-6">
                    <p class="text-[10px] font-bold text-indigo-300 uppercase tracking-widest mb-3">Önerilen İlk Adım</p>
                    <p class="text-sm leading-relaxed text-slate-200 italic">
                      "{{ renderText(selectedEmployeeReport.recommended_action || 'Bu çalışan için belirgin bir aksiyon sinyali henüz oluşmadı.') }}"
                    </p>
                 </div>
                 
                 <div v-if="monthlyDeepAnalysis" class="space-y-4">
                    <div class="flex flex-col gap-1">
                       <span class="text-[10px] font-bold text-slate-400 uppercase">Ayrılma Nedeni Sinyalleri</span>
                       <div class="flex flex-wrap gap-2 mt-2">
                          <span v-for="item in monthlyDeepAnalysis.flight_risk_reasons" :key="item" class="bg-rose-500/10 text-rose-300 px-2 py-1 rounded text-[10px] font-bold border border-rose-500/20">
                            {{ renderText(item) }}
                          </span>
                       </div>
                    </div>
                 </div>
              </div>

              <!-- Metrics Chart -->
              <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                 <div class="flex items-center justify-between mb-6">
                    <h4 class="font-bold text-slate-900">Yetenek Dağılımı</h4>
                    <span class="text-[10px] font-bold text-slate-400 uppercase">1-5 Puan</span>
                 </div>
                 <div class="h-64">
                    <BarChart
                      :labels="scoreMetricLabels"
                      :data="scoreMetricValues"
                      label="Skorlar"
                      color="#4f46e5"
                    />
                 </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Empty State -->
        <section
          v-else
          class="flex flex-col items-center justify-center min-h-[600px] rounded-3xl border-2 border-dashed border-slate-200 bg-white p-12 text-center"
        >
          <div class="w-24 h-24 bg-indigo-50 rounded-full flex items-center justify-center mb-6">
             <UserPlusIcon class="w-12 h-12 text-indigo-300" />
          </div>
          <h3 class="text-2xl font-bold text-slate-900">Çalışan Analiz Paneli</h3>
          <p class="mt-4 text-slate-500 max-w-sm mx-auto leading-relaxed">
            Soldaki listeden bir çalışan seçtiğinizde kisisel performans trendleri, 360 feedback özetleri ve AI destekli yönetici içgörüleri burada listelenecektir.
          </p>
          <div class="mt-8 flex gap-4">
             <div class="flex flex-col items-center">
                <div class="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-xs font-bold text-slate-500 mb-2">1</div>
                <span class="text-[10px] font-bold text-slate-400 uppercase">Seç</span>
             </div>
             <div class="w-12 h-px bg-slate-100 mt-4"></div>
             <div class="flex flex-col items-center">
                <div class="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-xs font-bold text-slate-500 mb-2">2</div>
                <span class="text-[10px] font-bold text-slate-400 uppercase">Analiz Et</span>
             </div>
             <div class="w-12 h-px bg-slate-100 mt-4"></div>
             <div class="flex flex-col items-center">
                <div class="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-xs font-bold text-slate-500 mb-2">3</div>
                <span class="text-[10px] font-bold text-slate-400 uppercase">Aksiyon Al</span>
             </div>
          </div>
        </section>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { 
  UsersIcon, 
  MagnifyingGlassIcon, 
  ChevronRightIcon, 
  BriefcaseIcon, 
  BuildingOfficeIcon, 
  UserGroupIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  HandRaisedIcon,
  ArrowTrendingUpIcon,
  FaceSmileIcon,
  ExclamationCircleIcon,
  CloudIcon,
  BoltIcon,
  UserPlusIcon,
  StarIcon,
  HeartIcon,
  SparklesIcon
} from '@heroicons/vue/24/outline'
import BarChart from '@/components/dashboard/BarChart.vue'
import BadgeMedal from '@/components/common/BadgeMedal.vue'
import { useRoute } from 'vue-router'
import {
  feedbackApi,
  type BadgeResponse,
  type BadgeType,
  type Employee360SummaryReportResponse,
  type EmployeeMonthlyDeepAnalysisResponse,
  type EmployeeMonthlyRAGReportResponse,
  type EmployeeForFeedback,
  type RiskDriver,
  type SummaryMetric,
} from '@/services/api/feedback.api'
import { employeeApi } from '@/services/api/employee.api'
import { analyticsApi, type DepartmentPerformanceSummaryResponse, type PerformanceEmployeeRowResponse } from '@/services/api/analytics.api'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')
const departments = ref<any[]>([])
const selectedDepartmentId = ref<number | null>(null)
const searchQuery = ref('')

const teamMembers = ref<EmployeeForFeedback[]>([])
const selectedTeam = ref<string>('all')
const selectedEmployeeId = ref<number | null>(null)
const selectedEmployeeReport = ref<Employee360SummaryReportResponse | null>(null)
const monthlyDeepAnalysis = ref<EmployeeMonthlyDeepAnalysisResponse | null>(null)
const monthlyRagReport = ref<EmployeeMonthlyRAGReportResponse | null>(null)
const employeeReports = ref<Record<number, Employee360SummaryReportResponse>>({})
const performanceSummary = ref<DepartmentPerformanceSummaryResponse | null>(null)
let employeeReportRequestId = 0
let monthlyAnalysisRequestId = 0
const today = new Date()
const selectedMonth = ref<number>(today.getMonth() + 1)
const selectedYear = ref<number>(today.getFullYear())

const monthOptions = [
  { value: 1, label: 'Ocak' },
  { value: 2, label: 'Şubat' },
  { value: 3, label: 'Mart' },
  { value: 4, label: 'Nisan' },
  { value: 5, label: 'Mayıs' },
  { value: 6, label: 'Haziran' },
  { value: 7, label: 'Temmuz' },
  { value: 8, label: 'Ağustos' },
  { value: 9, label: 'Eylül' },
  { value: 10, label: 'Ekim' },
  { value: 11, label: 'Kasım' },
  { value: 12, label: 'Aralık' },
]

const yearOptions = computed(() => {
  const baseYear = today.getFullYear()
  return [baseYear - 1, baseYear, baseYear + 1]
})

const teamOptions = computed(() => {
  return [...new Set(teamMembers.value.map((employee) => employee.team).filter((team): team is string => Boolean(team)))].sort()
})

const filteredTeamMembers = computed(() => {
  let list = teamMembers.value
  
  // Department Filter (Admin Only)
  if (isAdmin.value && selectedDepartmentId.value) {
    list = list.filter(m => m.department_id === selectedDepartmentId.value)
  }
  
  // Team Filter
  if (selectedTeam.value !== 'all') {
    list = list.filter((employee) => employee.team === selectedTeam.value)
  }
  
  return list
})

const filteredAndSearchedMembers = computed(() => {
  let list = filteredTeamMembers.value
  
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(m => 
      m.user.full_name.toLowerCase().includes(q) || 
      (m.position || '').toLowerCase().includes(q)
    )
  }
  
  return list
})

function formatRiskLabel(value?: string | null) {
  const map: Record<string, string> = {
    low: 'Düşük',
    medium: 'Orta',
    high: 'Yüksek',
  }
  return value ? (map[value] || value) : '-'
}

function formatMemoryCount(value: number) {
  return `${value} benzer kayıt`
}

function renderText(value?: string | null) {
  if (!value) return ''
  return value // Backend already provides mostly clean strings, UI handles specific replacements if needed
}

function employeeReportBadges(employeeId: number) {
  return employeeReports.value[employeeId]?.badges || []
}

function getBadgeDescription(badge: BadgeResponse | { badge_type: BadgeType; source_feedback_ids?: number[] }) {
  const baseMap = {
    team_player: "Ekip enerjisini ve uyumu yükseltiyor.",
    problem_solver: "Blokajlara hızlı ve soğukkanlı yaklaşıyor.",
    communicator: "Geri bildirimlerinde net ve öğretici bir çizgi var.",
    speed_champion: "Yüksek tempo ve hızlı adaptasyon sağlıyor.",
    mentor: "Bilgi paylaşımı ve mentorlukta öne çıkıyor.",
    innovator: "Gelişime açık ve çevik ilerliyor.",
    reliable: "Teknik sahiplenme ve sağlam uygulama disiplini gösteriyor.",
  } as const
  return baseMap[badge.badge_type] ?? "Analizlerde istikrarlı bir güç sergiledi."
}

const scoreMetrics = computed<SummaryMetric[]>(() =>
  (selectedEmployeeReport.value?.metrics || []).filter((metric) => typeof metric.value === 'number')
)

const qualityWarningSection = computed(() =>
  selectedEmployeeReport.value?.sections.find((section) => section.title.toLowerCase().includes('veri kalitesi')) || null
)

const managerEvidenceSection = computed(() =>
  selectedEmployeeReport.value?.sections.find((section) => section.title.toLowerCase().includes('yonetici kanitlari')) || null
)

const biasWarningSection = computed(() =>
  selectedEmployeeReport.value?.sections.find((section) => section.title.toLowerCase().includes('bias')) || null
)

const scoreMetricLabels = computed(() => scoreMetrics.value.map((metric) => metric.label))
const scoreMetricValues = computed(() => scoreMetrics.value.map((metric) => metric.value ?? 0))

const selectedKpiRow = computed<PerformanceEmployeeRowResponse | null>(() => {
  if (!selectedEmployeeId.value) return null
  return performanceSummary.value?.employees.find((employee) => employee.employee_id === selectedEmployeeId.value) || null
})

const burnoutMetric = computed(() =>
  selectedEmployeeReport.value?.metrics.find((metric) => metric.label === 'Burnout Risk') || null
)

const burnoutDriverItems = computed<RiskDriver[]>(() => {
  const monthlyDrivers = monthlyDeepAnalysis.value?.burnout_risk_drivers || []
  if (monthlyDrivers.length) return monthlyDrivers
  const metricDrivers = burnoutMetric.value?.drivers || []
  if (metricDrivers.length) return metricDrivers
  return (monthlyDeepAnalysis.value?.burnout_risk_evidence || []).map((item) => ({
    label: 'Burnout risk evidence',
    evidence: item,
    severity: monthlyDeepAnalysis.value?.burnout_risk_level || null,
  }))
})

function getPreviewSummary(employeeId: number) {
  const report = employeeReports.value[employeeId]
  if (!report?.report_summary) return ''
  return report.report_summary.length > 80 ? report.report_summary.slice(0, 80) + '...' : report.report_summary
}

function firstQueryValue(value: unknown) {
  return Array.isArray(value) ? value[0] : value
}

function routeEmployeeId() {
  const raw = firstQueryValue(route.query.employeeId ?? route.query.employee_id)
  const id = Number(raw)
  return Number.isFinite(id) && id > 0 ? id : null
}

function routeTeam() {
  const raw = firstQueryValue(route.query.team)
  return typeof raw === 'string' && raw.trim() ? raw.trim() : null
}

function applyRouteSelection() {
  const team = routeTeam()
  if (team && teamOptions.value.includes(team)) {
    selectedTeam.value = team
  }

  const employeeId = routeEmployeeId()
  if (employeeId && teamMembers.value.some((employee) => employee.id === employeeId)) {
    selectedEmployeeId.value = employeeId
  }
}

function formatTrend(value: string) {
  const map: Record<string, string> = {
    yukselis: 'Yükseliş',
    dusus: 'Düşüş',
    stabil: 'Stabil',
  }
  return map[value] || 'Stabil'
}

async function loadData() {
  if (isAdmin.value) {
    try {
      departments.value = await employeeApi.getDepartments()
    } catch (error) {
      console.warn('Departman listesi yüklenemedi:', error)
      departments.value = []
    }
  }

  try {
    const [employeeResult, summary] = await Promise.all([
      employeeApi.getEmployees(),
      analyticsApi.getPerformanceSummary().catch(() => null),
    ])
    performanceSummary.value = summary
    setTeamMembers(employeeResult)
  } catch (error) {
    console.warn('Çalışan listesi /employees üzerinden yüklenemedi, feedback adaylarına düşülüyor:', error)
    try {
      const candidates = await feedbackApi.getFeedbackCandidates()
      performanceSummary.value = await analyticsApi.getPerformanceSummary().catch(() => null)
      setTeamMembers(candidates)
    } catch (fallbackError) {
      console.error('Veriler yüklenemedi:', fallbackError)
      teamMembers.value = []
    }
  }

  applyRouteSelection()

  if (!selectedEmployeeId.value && teamMembers.value.length) {
    selectedEmployeeId.value = teamMembers.value[0].id
  }
}

function setTeamMembers(employees: EmployeeForFeedback[]) {
  teamMembers.value = employees.filter((employee) => {
    const role = employee.user?.role
    return !role || role === 'employee'
  })
}

async function loadEmployeeReport(employeeId: number) {
  const requestId = ++employeeReportRequestId
  selectedEmployeeReport.value = null
  try {
    const report = await feedbackApi.getEmployee360SummaryReport(employeeId)
    if (requestId !== employeeReportRequestId || selectedEmployeeId.value !== employeeId) return
    employeeReports.value = { ...employeeReports.value, [employeeId]: report }
    selectedEmployeeReport.value = report
  } catch (error) {
    if (requestId !== employeeReportRequestId || selectedEmployeeId.value !== employeeId) return
    console.error('Rapor yüklenemedi:', error)
    selectedEmployeeReport.value = null
  }
}

function formatKpiTrend(value?: number | null) {
  if (value === null || value === undefined) return 'Trend yok'
  const rounded = Math.round(Number(value) * 10) / 10
  return rounded > 0 ? `+${rounded}` : String(rounded)
}

function kpiStatusLabel(status?: string | null) {
  if (status === 'risk') return 'Risk'
  if (status === 'watch') return 'İzlemede'
  if (status === 'stable') return 'Stabil'
  if (status === 'no_data') return 'Veri yok'
  return 'KPI verisi yok'
}

function kpiStatusClass(status?: string | null) {
  if (status === 'risk') return 'border-rose-200 bg-rose-50 text-rose-700'
  if (status === 'watch') return 'border-amber-200 bg-amber-50 text-amber-700'
  if (status === 'stable') return 'border-emerald-200 bg-emerald-50 text-emerald-700'
  return 'border-slate-200 bg-slate-50 text-slate-600'
}

async function loadMonthlyDeepAnalysis(employeeId: number) {
  const requestId = ++monthlyAnalysisRequestId
  monthlyDeepAnalysis.value = null
  monthlyRagReport.value = null
  try {
    const [deepAnalysis, ragReport] = await Promise.all([
      feedbackApi.getEmployeeMonthlyDeepAnalysis(employeeId, { year: selectedYear.value, month: selectedMonth.value }),
      feedbackApi.getEmployeeMonthlyRagReport(employeeId, { year: selectedYear.value, month: selectedMonth.value })
    ])
    if (requestId !== monthlyAnalysisRequestId || selectedEmployeeId.value !== employeeId) return
    monthlyDeepAnalysis.value = deepAnalysis
    monthlyRagReport.value = ragReport
  } catch (error) {
    if (requestId !== monthlyAnalysisRequestId || selectedEmployeeId.value !== employeeId) return
    console.error('Aylık analizler yüklenemedi:', error)
    monthlyDeepAnalysis.value = null
    monthlyRagReport.value = null
  }
}

watch(selectedEmployeeId, (value) => {
  if (typeof value === 'number') {
    void loadEmployeeReport(value)
    void loadMonthlyDeepAnalysis(value)
  }
})

watch(selectedTeam, () => {
  if (!filteredTeamMembers.value.some((employee) => employee.id === selectedEmployeeId.value)) {
    selectedEmployeeId.value = filteredTeamMembers.value[0]?.id ?? null
  }
})

watch(selectedDepartmentId, () => {
  if (!filteredTeamMembers.value.some((employee) => employee.id === selectedEmployeeId.value)) {
    selectedEmployeeId.value = filteredTeamMembers.value[0]?.id ?? null
  }
})

watch([selectedMonth, selectedYear], () => {
  if (typeof selectedEmployeeId.value === 'number') {
    void loadMonthlyDeepAnalysis(selectedEmployeeId.value)
  }
})

watch(
  () => [route.query.employeeId, route.query.employee_id, route.query.team],
  () => applyRouteSelection()
)

onMounted(async () => {
  await loadData()
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #cbd5e1;
}
</style>
