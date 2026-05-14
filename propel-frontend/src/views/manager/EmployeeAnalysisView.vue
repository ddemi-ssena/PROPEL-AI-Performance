<template>
  <div class="space-y-8 pb-10">
    <div class="flex flex-col md:flex-row justify-between items-end gap-4 border-b border-slate-200 pb-6">
      <div>
        <h2 class="text-2xl font-bold text-slate-900 tracking-tight">Çalışan Analizi</h2>
        <p class="text-slate-500 mt-1">
          Ekipteki çalışanların 360 derece geri bildirim raporlarını, skorlarını ve yönetici özetlerini ayrı ayrı inceleyin.
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
                <!-- Monthly KPIs -->
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

    <section class="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div class="flex flex-col gap-4 border-b border-slate-100 p-6 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <p class="text-xs font-bold uppercase tracking-[0.18em] text-indigo-500">KPI ML Analizi</p>
          <h3 class="mt-2 text-xl font-black text-slate-900">&#128101; Tüm Çalışanlar - Detaylı Performans Analizi</h3>
          <p class="mt-1 text-sm font-medium text-slate-500">{{ paginatedPerformanceRows.length }} / {{ sortedPerformanceRows.length }} çalışan gösteriliyor</p>
        </div>
        <button
          type="button"
          class="inline-flex items-center justify-center rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-black text-white shadow-sm transition hover:bg-slate-800"
          @click="exportPerformanceTable"
        >
          &#128202; Tabloyu Excel'e İndir
        </button>
      </div>

      <div class="border-b border-slate-100 bg-slate-50/60 p-4">
        <div class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
          <label class="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">
            Takım
            <select v-model="tableTeamFilter" class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold normal-case tracking-normal text-slate-700">
              <option value="all">Tüm Takımlar</option>
              <option v-for="team in teamOptions" :key="`table-team-${team}`" :value="team">{{ team }}</option>
            </select>
          </label>
          <label class="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">
            Rol
            <select v-model="tableRoleFilter" class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold normal-case tracking-normal text-slate-700">
              <option value="all">Tüm Roller</option>
              <option value="junior">Junior</option>
              <option value="mid">Mid</option>
              <option value="senior">Senior</option>
              <option value="lead">Lead</option>
            </select>
          </label>
          <label class="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">
            KPI Alt Sınır: {{ tableKpiMin }}
            <input v-model.number="tableKpiMin" type="range" min="0" max="100" step="5" class="mt-3 w-full accent-indigo-600" />
          </label>
          <label class="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">
            Trend
            <select v-model="tableTrendFilter" class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold normal-case tracking-normal text-slate-700">
              <option value="all">Tümü</option>
              <option value="up">Artış</option>
              <option value="down">Düşüş</option>
              <option value="flat">Stabil</option>
            </select>
          </label>
          <label class="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">
            Durum
            <select v-model="tableStatusFilter" class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold normal-case tracking-normal text-slate-700">
              <option value="all">Tümü</option>
              <option value="stable">Stabil</option>
              <option value="watch">İzlenmeli</option>
              <option value="risk">Riskli</option>
            </select>
          </label>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="min-w-[1120px] w-full border-separate border-spacing-0">
          <thead class="sticky top-0 z-10 bg-[#F9FAFB]">
            <tr>
              <th
                v-for="column in performanceTableColumns"
                :key="column.key"
                class="border-b border-slate-200 px-4 py-4 text-left text-xs font-black uppercase tracking-[0.12em] text-slate-500"
                :class="column.align === 'right' ? 'text-right' : ''"
              >
                <button
                  v-if="column.sortable"
                  type="button"
                  class="inline-flex items-center gap-1 transition hover:text-indigo-600"
                  :class="tableSortKey === column.key ? 'text-indigo-600' : ''"
                  @click="setTableSort(column.key)"
                >
                  {{ column.label }}
                  <span class="text-[10px]">{{ tableSortKey === column.key ? (tableSortDirection === 'asc' ? '▲' : '▼') : '↕' }}</span>
                </button>
                <span v-else>{{ column.label }}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, index) in paginatedPerformanceRows"
              :key="row.id"
              class="cursor-pointer transition hover:bg-[#F3F4F6] hover:shadow-sm"
              :class="index % 2 === 0 ? 'bg-white' : 'bg-[#FAFAFA]'"
              @click="openPerformanceRow(row)"
            >
              <td class="border-b border-slate-100 px-4 py-4 text-sm font-bold text-slate-400">{{ row.rank }}</td>
              <td class="border-b border-slate-100 px-4 py-4">
                <div class="flex items-center gap-3">
                  <div
                    class="grid h-10 w-10 shrink-0 place-items-center rounded-full border-2 border-white text-sm font-black text-white shadow-sm"
                    :style="{ background: row.avatarGradient }"
                  >
                    {{ row.initials }}
                  </div>
                  <div>
                    <p class="text-base font-black text-slate-900">{{ row.name }}</p>
                    <p class="text-xs font-semibold text-slate-400">{{ row.code }}</p>
                  </div>
                </div>
              </td>
              <td class="border-b border-slate-100 px-4 py-4">
                <span class="inline-flex items-center gap-1.5 rounded-full bg-slate-50 px-2.5 py-1 text-xs font-black text-slate-700">
                  <span>{{ row.teamIcon }}</span>
                  {{ row.team }}
                </span>
              </td>
              <td class="border-b border-slate-100 px-4 py-4">
                <span class="rounded-full px-2.5 py-1 text-xs font-black" :class="roleBadgeClass(row.roleLevel)">
                  {{ row.roleLabel }}
                </span>
              </td>
              <td class="border-b border-slate-100 px-4 py-4">
                <div class="flex min-w-[170px] items-center gap-3">
                  <div class="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                    <div class="h-full rounded-full" :class="kpiBarClass(row.kpiScore)" :style="{ width: `${row.kpiScore}%` }"></div>
                  </div>
                  <span class="w-16 text-right text-sm font-black text-slate-900">{{ row.kpiScore.toFixed(1) }}/100</span>
                </div>
              </td>
              <td class="border-b border-slate-100 px-4 py-4">
                <span class="text-sm font-black" :class="trendClass(row.trend)">
                  {{ trendArrow(row.trend) }} {{ formatSigned(row.trend) }}
                </span>
              </td>
              <td class="border-b border-slate-100 px-4 py-4">
                <svg class="h-[30px] w-[60px]" viewBox="0 0 60 30" fill="none" aria-hidden="true">
                  <polyline
                    :points="row.sparklinePoints"
                    fill="none"
                    :stroke="row.trend >= 0 ? '#10B981' : '#EF4444'"
                    stroke-width="2.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </td>
              <td class="border-b border-slate-100 px-4 py-4">
                <span
                  class="inline-flex rounded-full bg-sky-50 px-2.5 py-1 text-xs font-black text-sky-700"
                  :title="row.strengthTooltip"
                >
                  {{ row.strength }}
                </span>
              </td>
              <td class="border-b border-slate-100 px-4 py-4">
                <span class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-black" :class="statusBadgeClass(row.status)">
                  {{ row.statusIcon }} {{ row.statusLabel }}
                </span>
              </td>
            </tr>
            <tr v-if="!paginatedPerformanceRows.length">
              <td colspan="9" class="px-4 py-12 text-center text-sm font-semibold text-slate-400">
                Filtrelere uygun çalışan bulunamadı.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="flex flex-col gap-3 border-t border-slate-100 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
        <p class="text-sm font-semibold text-slate-500">
          {{ paginationStart }}-{{ paginationEnd }} / {{ sortedPerformanceRows.length }} çalışan
        </p>
        <div class="flex flex-wrap items-center gap-3">
          <select v-model.number="tablePageSize" class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-bold text-slate-700">
            <option :value="15">15</option>
            <option :value="30">30</option>
            <option :value="50">50</option>
          </select>
          <div class="flex items-center gap-2">
            <button
              type="button"
              class="rounded-lg border border-slate-200 px-3 py-2 text-sm font-bold text-slate-600 disabled:cursor-not-allowed disabled:opacity-40"
              :disabled="tablePage === 1"
              @click="tablePage--"
            >
              Önceki
            </button>
            <span class="text-sm font-black text-slate-700">{{ tablePage }} / {{ totalTablePages }}</span>
            <button
              type="button"
              class="rounded-lg border border-slate-200 px-3 py-2 text-sm font-bold text-slate-600 disabled:cursor-not-allowed disabled:opacity-40"
              :disabled="tablePage === totalTablePages"
              @click="tablePage++"
            >
              Sonraki
            </button>
          </div>
        </div>
      </div>
    </section>

    <section class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div class="flex flex-col gap-6 xl:flex-row">
        <div class="min-w-0 flex-1">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h3 class="text-xl font-black text-slate-900">&#127919; Rol Bazlı Performans Karşılaştırması</h3>
              <p class="mt-1 text-sm text-slate-500">Junior, Mid, Senior ve Lead seviyelerinde ortalama performans</p>
            </div>
            <div class="flex flex-wrap gap-3">
              <span class="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 text-xs font-black text-blue-700">
                <span class="h-2.5 w-2.5 rounded-full bg-blue-500"></span>
                KPI Skoru
              </span>
              <span class="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-xs font-black text-emerald-700">
                <span class="h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
                Trend (4 hafta)
              </span>
            </div>
          </div>

          <div class="mt-6 h-[360px]">
            <Bar :data="roleComparisonChartData" :options="roleComparisonChartOptions" :plugins="roleComparisonPlugins" />
          </div>
        </div>

        <aside class="w-full rounded-xl border border-slate-100 bg-slate-50 p-5 xl:w-80">
          <div class="flex items-center gap-3">
            <div class="grid h-10 w-10 place-items-center rounded-xl bg-white text-xl shadow-sm">&#128202;</div>
            <h4 class="text-lg font-black text-slate-900">İstatistikler</h4>
          </div>
          <div class="mt-5 space-y-5">
            <div>
              <p class="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">En yüksek fark</p>
              <p class="mt-1 text-sm font-black text-slate-900">{{ roleComparisonStats.highestGap }}</p>
            </div>
            <div>
              <p class="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">En hızlı gelişen</p>
              <p class="mt-1 text-sm font-black text-slate-900">{{ roleComparisonStats.fastestImproving }}</p>
            </div>
            <div>
              <p class="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">İyileştirme önerisi</p>
              <p class="mt-1 text-sm leading-6 font-semibold text-slate-700">{{ roleComparisonStats.recommendation }}</p>
            </div>
          </div>
        </aside>
      </div>
    </section>

    <div
      v-if="selectedTableRow"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm"
      @click.self="selectedTableRow = null"
    >
      <div class="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-2xl">
        <div class="flex items-start justify-between gap-4">
          <div class="flex items-center gap-4">
            <div class="grid h-14 w-14 place-items-center rounded-2xl border-2 border-white text-lg font-black text-white shadow-sm" :style="{ background: selectedTableRow.avatarGradient }">
              {{ selectedTableRow.initials }}
            </div>
            <div>
              <p class="text-xs font-bold uppercase tracking-[0.18em] text-slate-400">Çalışan Detayı</p>
              <h3 class="mt-1 text-2xl font-black text-slate-900">{{ selectedTableRow.name }}</h3>
              <p class="mt-1 text-sm text-slate-500">{{ selectedTableRow.role }} · {{ selectedTableRow.team }} · {{ selectedTableRow.code }}</p>
            </div>
          </div>
          <button class="rounded-full border border-slate-200 px-3 py-1 text-sm font-bold text-slate-500 hover:bg-slate-50" @click="selectedTableRow = null">Kapat</button>
        </div>
        <div class="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div class="rounded-xl bg-slate-50 p-4">
            <p class="text-xs text-slate-500">KPI Skoru</p>
            <p class="mt-1 text-2xl font-black text-slate-900">{{ selectedTableRow.kpiScore.toFixed(1) }}/100</p>
          </div>
          <div class="rounded-xl bg-slate-50 p-4">
            <p class="text-xs text-slate-500">Trend</p>
            <p class="mt-1 text-2xl font-black" :class="trendClass(selectedTableRow.trend)">
              {{ trendArrow(selectedTableRow.trend) }} {{ formatSigned(selectedTableRow.trend) }}
            </p>
          </div>
          <div class="rounded-xl bg-slate-50 p-4">
            <p class="text-xs text-slate-500">Durum</p>
            <p class="mt-1 text-xl font-black text-slate-900">{{ selectedTableRow.statusLabel }}</p>
          </div>
        </div>
        <p class="mt-5 rounded-xl border border-indigo-100 bg-indigo-50 p-4 text-sm leading-6 text-slate-700">
          {{ selectedTableRow.name }} için öne çıkan güç alanı {{ selectedTableRow.strength }}. Satıra tıklandığında bu modal açılır ve aynı çalışan sağdaki detay panelinde de seçilir.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
  type ChartOptions,
  type Plugin,
} from 'chart.js'
import { Bar } from 'vue-chartjs'
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
  type SummaryMetric,
} from '@/services/api/feedback.api'
import { employeeApi } from '@/services/api/employee.api'
import { analyticsApi, type DepartmentPerformanceSummaryResponse, type PerformanceEmployeeRowResponse } from '@/services/api/analytics.api'
import { useAuthStore } from '@/stores/auth'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

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
const selectedTableRow = ref<EmployeePerformanceRow | null>(null)
const tableTeamFilter = ref('all')
const tableRoleFilter = ref('all')
const tableTrendFilter = ref('all')
const tableStatusFilter = ref('all')
const tableKpiMin = ref(0)
const tableSortKey = ref<PerformanceSortKey>('rank')
const tableSortDirection = ref<'asc' | 'desc'>('asc')
const tablePage = ref(1)
const tablePageSize = ref(15)
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

type RoleLevel = 'junior' | 'mid' | 'senior' | 'lead'
type StatusLevel = 'stable' | 'watch' | 'risk'
type PerformanceSortKey = 'rank' | 'employee' | 'team' | 'role' | 'kpi' | 'trend' | 'strength' | 'status'

type EmployeePerformanceRow = {
  id: number
  rank: number
  name: string
  code: string
  initials: string
  avatarGradient: string
  team: string
  teamIcon: string
  role: string
  roleLevel: RoleLevel
  roleLabel: string
  kpiScore: number
  trend: number
  sparklineValues: number[]
  sparklinePoints: string
  strength: string
  strengthTooltip: string
  status: StatusLevel
  statusLabel: string
  statusIcon: string
}

type RoleComparisonGroup = {
  key: RoleLevel
  label: string
  count: number
  avgKpi: number
  avgTrend: number
  highest?: EmployeePerformanceRow
  lowest?: EmployeePerformanceRow
}

const performanceTableColumns: Array<{ key: PerformanceSortKey | 'sparkline'; label: string; sortable?: boolean; align?: 'right' }> = [
  { key: 'rank', label: '#', sortable: true },
  { key: 'employee', label: 'Çalışan', sortable: true },
  { key: 'team', label: 'Takım', sortable: true },
  { key: 'role', label: 'Rol', sortable: true },
  { key: 'kpi', label: 'KPI Skoru', sortable: true },
  { key: 'trend', label: 'Trend', sortable: true },
  { key: 'sparkline', label: '4H Trend' },
  { key: 'strength', label: 'Güç', sortable: true },
  { key: 'status', label: 'Durum', sortable: true },
]

const teamVisuals: Record<string, { icon: string; from: string; to: string; color: string }> = {
  Backend: { icon: '💻', from: '#F87171', to: '#DC2626', color: '#EF4444' },
  Frontend: { icon: '🎨', from: '#A78BFA', to: '#7C3AED', color: '#8B5CF6' },
  DevOps: { icon: '⚙️', from: '#60A5FA', to: '#2563EB', color: '#3B82F6' },
  QA: { icon: '🔍', from: '#34D399', to: '#059669', color: '#10B981' },
  'Kurumsal Satis': { icon: '🏢', from: '#38BDF8', to: '#0284C7', color: '#0EA5E9' },
  'Bireysel Satis': { icon: '🤝', from: '#FBBF24', to: '#D97706', color: '#F59E0B' },
  'Musteri Basarisi': { icon: '✅', from: '#34D399', to: '#059669', color: '#10B981' },
}

const fallbackGradients = [
  { from: '#818CF8', to: '#4F46E5', color: '#6366F1' },
  { from: '#FB7185', to: '#E11D48', color: '#F43F5E' },
  { from: '#2DD4BF', to: '#0F766E', color: '#14B8A6' },
  { from: '#FACC15', to: '#CA8A04', color: '#EAB308' },
]

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

const performanceRows = computed<EmployeePerformanceRow[]>(() => {
  const scopedIds = new Set(filteredTeamMembers.value.map((employee) => employee.id))
  return (performanceSummary.value?.employees || [])
    .filter((employee) => scopedIds.has(employee.employee_id))
    .map((employee, index) => buildPerformanceRow(employee, index))
    .sort((a, b) => b.kpiScore - a.kpiScore)
    .map((row, index) => ({ ...row, rank: index + 1 }))
})

const filteredPerformanceRows = computed(() => {
  return performanceRows.value.filter((row) => {
    const teamMatch = tableTeamFilter.value === 'all' || row.team === tableTeamFilter.value
    const roleMatch = tableRoleFilter.value === 'all' || row.roleLevel === tableRoleFilter.value
    const kpiMatch = row.kpiScore >= tableKpiMin.value
    const trendMatch =
      tableTrendFilter.value === 'all'
      || (tableTrendFilter.value === 'up' && row.trend > 0.2)
      || (tableTrendFilter.value === 'down' && row.trend < -0.2)
      || (tableTrendFilter.value === 'flat' && Math.abs(row.trend) <= 0.2)
    const statusMatch = tableStatusFilter.value === 'all' || row.status === tableStatusFilter.value
    return teamMatch && roleMatch && kpiMatch && trendMatch && statusMatch
  })
})

const sortedPerformanceRows = computed(() => {
  const direction = tableSortDirection.value === 'asc' ? 1 : -1
  return [...filteredPerformanceRows.value].sort((a, b) => {
    const left = sortValue(a, tableSortKey.value)
    const right = sortValue(b, tableSortKey.value)
    if (typeof left === 'number' && typeof right === 'number') return (left - right) * direction
    return String(left).localeCompare(String(right), 'tr') * direction
  })
})

const totalTablePages = computed(() => Math.max(1, Math.ceil(sortedPerformanceRows.value.length / tablePageSize.value)))
const paginatedPerformanceRows = computed(() => {
  const start = (tablePage.value - 1) * tablePageSize.value
  return sortedPerformanceRows.value.slice(start, start + tablePageSize.value)
})
const paginationStart = computed(() => sortedPerformanceRows.value.length ? ((tablePage.value - 1) * tablePageSize.value) + 1 : 0)
const paginationEnd = computed(() => Math.min(tablePage.value * tablePageSize.value, sortedPerformanceRows.value.length))
const roleComparisonGroups = computed<RoleComparisonGroup[]>(() => {
  const order: Array<{ key: RoleLevel; label: string }> = [
    { key: 'junior', label: 'Junior' },
    { key: 'mid', label: 'Mid' },
    { key: 'senior', label: 'Senior' },
    { key: 'lead', label: 'Lead' },
  ]

  return order.map(({ key, label }) => {
    const rows = performanceRows.value.filter((row) => row.roleLevel === key)
    const sortedByKpi = [...rows].sort((a, b) => b.kpiScore - a.kpiScore)
    return {
      key,
      label,
      count: rows.length,
      avgKpi: Number(average(rows.map((row) => row.kpiScore)).toFixed(1)),
      avgTrend: Number(average(rows.map((row) => row.trend)).toFixed(1)),
      highest: sortedByKpi[0],
      lowest: sortedByKpi[sortedByKpi.length - 1],
    }
  })
})

const roleComparisonAverage = computed(() => Number(average(performanceRows.value.map((row) => row.kpiScore)).toFixed(1)))

const roleComparisonChartData = computed(() => ({
  labels: roleComparisonGroups.value.map((group) => group.label),
  datasets: [
    {
      label: 'KPI Skoru',
      data: roleComparisonGroups.value.map((group) => group.avgKpi),
      backgroundColor: '#3B82F6',
      borderRadius: 8,
      maxBarThickness: 52,
      yAxisID: 'y',
    },
    {
      label: 'Trend (4 hafta)',
      data: roleComparisonGroups.value.map((group) => group.avgTrend),
      backgroundColor: roleComparisonGroups.value.map((group) => group.avgTrend >= 0 ? '#10B981' : '#EF4444'),
      borderRadius: 8,
      maxBarThickness: 52,
      yAxisID: 'yTrend',
    },
  ],
}))

const roleComparisonAverageLinePlugin: Plugin<'bar'> = {
  id: 'roleComparisonAverageLine',
  afterDatasetsDraw(chart) {
    const yScale = chart.scales.y
    const area = chart.chartArea
    if (!yScale || !area) return
    const y = yScale.getPixelForValue(roleComparisonAverage.value)
    const { ctx } = chart
    ctx.save()
    ctx.setLineDash([6, 6])
    ctx.strokeStyle = '#94A3B8'
    ctx.lineWidth = 1.5
    ctx.beginPath()
    ctx.moveTo(area.left, y)
    ctx.lineTo(area.right, y)
    ctx.stroke()
    ctx.setLineDash([])
    ctx.fillStyle = '#475569'
    ctx.font = '700 11px Inter, sans-serif'
    ctx.fillText(`Genel Ort. ${roleComparisonAverage.value}`, area.right - 108, y - 8)
    ctx.restore()
  },
}

const roleComparisonValueLabelsPlugin: Plugin<'bar'> = {
  id: 'roleComparisonValueLabels',
  afterDatasetsDraw(chart) {
    const { ctx } = chart
    ctx.save()
    ctx.font = '700 11px Inter, sans-serif'
    ctx.textAlign = 'center'
    chart.data.datasets.forEach((dataset, datasetIndex) => {
      const meta = chart.getDatasetMeta(datasetIndex)
      meta.data.forEach((bar, index) => {
        const value = Number(dataset.data[index] || 0)
        const position = bar.tooltipPosition(true)
        if (position.x === null || position.y === null) return
        ctx.fillStyle = datasetIndex === 0 ? '#1E40AF' : (value >= 0 ? '#047857' : '#B91C1C')
        ctx.fillText(datasetIndex === 0 ? value.toFixed(1) : formatSigned(value), position.x, position.y - 8)
      })
    })
    ctx.restore()
  },
}

const roleComparisonPlugins = [roleComparisonAverageLinePlugin, roleComparisonValueLabelsPlugin]

const roleComparisonChartOptions = computed<ChartOptions<'bar'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false,
  },
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      backgroundColor: '#0F172A',
      padding: 12,
      cornerRadius: 10,
      displayColors: false,
      callbacks: {
        title(items) {
          return items[0]?.label || ''
        },
        label(context) {
          const group = roleComparisonGroups.value[context.dataIndex]
          if (!group) return ''
          return [
            `${group.count} ${group.label} çalışan`,
            `Ortalama KPI: ${group.avgKpi}`,
            `Ortalama Trend: ${formatSigned(group.avgTrend)}`,
            `En yüksek: ${group.highest ? `${group.highest.kpiScore.toFixed(1)} (${group.highest.name})` : '-'}`,
            `En düşük: ${group.lowest ? `${group.lowest.kpiScore.toFixed(1)} (${group.lowest.name})` : '-'}`,
          ]
        },
      },
    },
  },
  scales: {
    x: {
      grid: {
        display: false,
      },
      ticks: {
        color: '#475569',
        font: {
          weight: 'bold',
        },
      },
    },
    y: {
      min: 0,
      max: 100,
      title: {
        display: true,
        text: 'KPI Skoru',
        color: '#475569',
        font: {
          weight: 'bold',
        },
      },
      grid: {
        color: '#E5E7EB',
        borderDash: [4, 4],
      },
      ticks: {
        color: '#64748B',
      },
    },
    yTrend: {
      position: 'right',
      min: -10,
      max: 10,
      title: {
        display: true,
        text: 'Trend',
        color: '#475569',
        font: {
          weight: 'bold',
        },
      },
      grid: {
        drawOnChartArea: false,
      },
      ticks: {
        color: '#64748B',
        callback(value) {
          return formatSigned(Number(value))
        },
      },
    },
  },
}))

const roleComparisonStats = computed(() => {
  const junior = roleComparisonGroups.value.find((group) => group.key === 'junior')
  const senior = roleComparisonGroups.value.find((group) => group.key === 'senior')
  const lead = roleComparisonGroups.value.find((group) => group.key === 'lead')
  const fastest = [...roleComparisonGroups.value].sort((a, b) => b.avgTrend - a.avgTrend)[0]
  const pairs = roleComparisonGroups.value.flatMap((left) =>
    roleComparisonGroups.value
      .filter((right) => right.key !== left.key)
      .map((right) => ({ from: left, to: right, gap: Number((left.avgKpi - right.avgKpi).toFixed(1)) }))
  )
  const highestGap = pairs.sort((a, b) => Math.abs(b.gap) - Math.abs(a.gap))[0]
  const defaultGap = senior && junior ? `Senior → Junior: ${formatSigned(senior.avgKpi - junior.avgKpi)}` : 'Veri bekleniyor'

  return {
    highestGap: highestGap
      ? `${highestGap.from.label} → ${highestGap.to.label}: ${formatSigned(highestGap.gap)}`
      : defaultGap,
    fastestImproving: fastest ? `${fastest.label} Level (${formatSigned(fastest.avgTrend)} trend)` : 'Veri bekleniyor',
    recommendation: junior && senior && senior.avgKpi - junior.avgKpi > 3
      ? 'Junior mentorship programı başlatılsın.'
      : lead && lead.avgTrend < 0
        ? 'Lead seviyesinde iş yükü ve delegasyon dengesi incelensin.'
        : 'Rol bazlı gelişim ritüelleri aylık takip edilsin.',
  }
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

function employeeInitials(name: string) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('') || 'Ç'
}

function teamVisual(team?: string) {
  if (team && teamVisuals[team]) return teamVisuals[team]
  const seed = (team || 'default').split('').reduce((sum, char) => sum + char.charCodeAt(0), 0)
  return fallbackGradients[Math.abs(seed) % fallbackGradients.length]
}

function average(values: number[]) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0
}

function formatSigned(value: number) {
  if (value > 0) return `+${value.toFixed(1)}`
  return value.toFixed(1)
}

function inferRoleLevel(position?: string | null, experienceYears?: number): RoleLevel {
  const role = String(position || '').toLowerCase()
  const years = Number(experienceYears || 0)
  if (role.includes('lead') || role.includes('manager')) return 'lead'
  if (role.includes('senior') || years >= 5) return 'senior'
  if (role.includes('junior') || years <= 2) return 'junior'
  return 'mid'
}

function roleLabel(level: RoleLevel) {
  const map: Record<RoleLevel, string> = {
    junior: 'Junior',
    mid: 'Mid',
    senior: 'Senior',
    lead: 'Lead',
  }
  return map[level]
}

function roleBadgeClass(level: RoleLevel) {
  const map: Record<RoleLevel, string> = {
    junior: 'bg-blue-100 text-blue-800',
    mid: 'bg-violet-100 text-violet-800',
    senior: 'bg-amber-100 text-amber-800',
    lead: 'bg-red-100 text-red-800',
  }
  return map[level]
}

function kpiBarClass(score: number) {
  if (score >= 90) return 'bg-emerald-500'
  if (score >= 80) return 'bg-amber-400'
  return 'bg-rose-500'
}

function trendArrow(value: number) {
  if (value > 0.2) return '↑'
  if (value < -0.2) return '↓'
  return '→'
}

function trendClass(value: number) {
  if (value > 0.2) return 'text-emerald-600'
  if (value < -0.2) return 'text-rose-600'
  return 'text-slate-500'
}

function statusFor(score: number, trend: number): StatusLevel {
  if (score < 80 || trend < -2) return 'risk'
  if (score < 90 || trend < -0.2) return 'watch'
  return 'stable'
}

function statusBadgeClass(status: StatusLevel) {
  const map: Record<StatusLevel, string> = {
    stable: 'bg-emerald-50 text-emerald-700',
    watch: 'bg-amber-50 text-amber-700',
    risk: 'bg-rose-50 text-rose-700',
  }
  return map[status]
}

function statusLabel(status: StatusLevel) {
  const map: Record<StatusLevel, string> = {
    stable: 'Stabil',
    watch: 'İzlenmeli',
    risk: 'Riskli',
  }
  return map[status]
}

function statusIcon(status: StatusLevel) {
  const map: Record<StatusLevel, string> = {
    stable: '🟢',
    watch: '🟡',
    risk: '🔴',
  }
  return map[status]
}

function sparklinePoints(values: number[]) {
  const safeValues = values.length ? values : [0]
  const min = Math.min(...safeValues)
  const max = Math.max(...safeValues)
  return safeValues.map((value, index) => {
    const x = safeValues.length === 1 ? 30 : (index / (safeValues.length - 1)) * 58 + 1
    const y = 28 - ((value - min) / Math.max(1, max - min)) * 24
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}

function buildPerformanceRow(employee: PerformanceEmployeeRowResponse, index: number): EmployeePerformanceRow {
  const kpiScore = Number(employee.kpi_score ?? 0)
  const trend = Number(employee.trend ?? 0)
  const trendValues = employee.sparkline_values.length ? employee.sparkline_values : [kpiScore]
  const visual = teamVisual(employee.team || undefined)
  const level = (['junior', 'mid', 'senior', 'lead'].includes(employee.role_level) ? employee.role_level : 'mid') as RoleLevel
  const status = employee.status === 'risk' || employee.status === 'watch' || employee.status === 'stable'
    ? employee.status
    : statusFor(kpiScore, trend)
  const strength = employee.strength || {
    label: employee.has_kpi_data ? 'KPI sinyali' : 'Veri yok',
    tooltip: employee.has_kpi_data ? 'Backend performans ozetinden gelen KPI sinyali.' : 'Bu calisan icin KPI kaydi bulunamadi.',
  }

  return {
    id: employee.employee_id,
    rank: index + 1,
    name: employee.employee_name,
    code: employee.external_employee_code || `EMP-${String(employee.employee_id).padStart(3, '0')}`,
    initials: employeeInitials(employee.employee_name),
    avatarGradient: `linear-gradient(135deg, ${visual.from}, ${visual.to})`,
    team: employee.team || 'Takimsiz',
    teamIcon: teamVisuals[employee.team || '']?.icon || '•',
    role: employee.position || 'Calisan',
    roleLevel: level,
    roleLabel: roleLabel(level),
    kpiScore,
    trend,
    sparklineValues: trendValues,
    sparklinePoints: sparklinePoints(trendValues),
    strength: strength.label,
    strengthTooltip: strength.tooltip,
    status,
    statusLabel: statusLabel(status),
    statusIcon: statusIcon(status),
  }
}

function sortValue(row: EmployeePerformanceRow, key: PerformanceSortKey) {
  const map: Record<PerformanceSortKey, string | number> = {
    rank: row.rank,
    employee: row.name,
    team: row.team,
    role: row.roleLevel,
    kpi: row.kpiScore,
    trend: row.trend,
    strength: row.strength,
    status: row.status,
  }
  return map[key]
}

function setTableSort(key: PerformanceSortKey | 'sparkline') {
  if (key === 'sparkline') return
  if (tableSortKey.value === key) {
    tableSortDirection.value = tableSortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    tableSortKey.value = key
    tableSortDirection.value = key === 'rank' ? 'asc' : 'desc'
  }
}

function openPerformanceRow(row: EmployeePerformanceRow) {
  selectedEmployeeId.value = row.id
  selectedTableRow.value = row
}

function exportPerformanceTable() {
  const headers = ['Sira', 'Calisan', 'Kod', 'Takim', 'Rol', 'KPI Skoru', 'Trend', 'Guc', 'Durum']
  const rows = sortedPerformanceRows.value.map((row) => [
    row.rank,
    row.name,
    row.code,
    row.team,
    row.roleLabel,
    row.kpiScore.toFixed(1),
    formatSigned(row.trend),
    row.strength,
    row.statusLabel,
  ])
  const html = `
    <html><head><meta charset="UTF-8"></head><body>
    <table border="1">
      <thead><tr>${headers.map((header) => `<th>${header}</th>`).join('')}</tr></thead>
      <tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${String(cell).replace(/</g, '&lt;')}</td>`).join('')}</tr>`).join('')}</tbody>
    </table>
    </body></html>
  `
  const blob = new Blob([html], { type: 'application/vnd.ms-excel;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `calisan_performans_tablosu_${new Date().toISOString().slice(0, 10)}.xls`
  link.click()
  URL.revokeObjectURL(url)
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

const biasWarningSection = computed(() =>
  selectedEmployeeReport.value?.sections.find((section) => section.title.toLowerCase().includes('bias')) || null
)

const scoreMetricLabels = computed(() => scoreMetrics.value.map((metric) => metric.label))
const scoreMetricValues = computed(() => scoreMetrics.value.map((metric) => metric.value ?? 0))

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
  try {
    if (isAdmin.value) {
      departments.value = await employeeApi.getDepartments()
    }
    
    const candidates = await feedbackApi.getFeedbackCandidates()
    teamMembers.value = candidates.filter((employee) => employee.user.role === 'employee')
    await loadPerformanceSummary()
    applyRouteSelection()

    if (!selectedEmployeeId.value && teamMembers.value.length) {
      selectedEmployeeId.value = teamMembers.value[0].id
    }
  } catch (error) {
    console.error('Veriler yüklenemedi:', error)
  }
}

async function loadPerformanceSummary() {
  try {
    performanceSummary.value = await analyticsApi.getPerformanceSummary({
      department_id: isAdmin.value ? (selectedDepartmentId.value || undefined) : undefined,
      team: selectedTeam.value === 'all' ? undefined : selectedTeam.value,
    })
  } catch (error) {
    console.error('Performans ozeti yuklenemedi:', error)
    performanceSummary.value = null
  }
}

async function loadEmployeeReport(employeeId: number) {
  try {
    const report = await feedbackApi.getEmployee360SummaryReport(employeeId)
    employeeReports.value = { ...employeeReports.value, [employeeId]: report }
    selectedEmployeeReport.value = report
  } catch (error) {
    console.error('Rapor yüklenemedi:', error)
    selectedEmployeeReport.value = null
  }
}

async function loadMonthlyDeepAnalysis(employeeId: number) {
  try {
    const [deepAnalysis, ragReport] = await Promise.all([
      feedbackApi.getEmployeeMonthlyDeepAnalysis(employeeId, { year: selectedYear.value, month: selectedMonth.value }),
      feedbackApi.getEmployeeMonthlyRagReport(employeeId, { year: selectedYear.value, month: selectedMonth.value })
    ])
    monthlyDeepAnalysis.value = deepAnalysis
    monthlyRagReport.value = ragReport
  } catch (error) {
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
  void loadPerformanceSummary()
  if (!filteredTeamMembers.value.some((employee) => employee.id === selectedEmployeeId.value)) {
    selectedEmployeeId.value = filteredTeamMembers.value[0]?.id ?? null
  }
})

watch(selectedDepartmentId, () => {
  void loadPerformanceSummary()
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
  [tableTeamFilter, tableRoleFilter, tableTrendFilter, tableStatusFilter, tableKpiMin, tablePageSize, selectedTeam, selectedDepartmentId],
  () => {
    tablePage.value = 1
  }
)

watch(totalTablePages, (value) => {
  if (tablePage.value > value) {
    tablePage.value = value
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
