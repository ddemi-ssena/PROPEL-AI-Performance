# Propel Agent Notes

## Persistent instruction

- Her sohbetin sonunda yapilan calisma ozeti, kalinan nokta ve sonraki adimlar bu dosyaya kaydedilecek.

## 2026-05-10 KPI / ML Analizi - Takim Analizi UI

- `propel-frontend/src/views/manager/ManagerAnalyticsView.vue` icinde Takim Analizi ekrani yonetici odakli mini dashboard haline getirildi.
- Secili takim icin gradient header, KPI kartlari, ana sorun karti, 12 haftalik risk trend grafigi, AI aksiyon paneli, takim uyeleri kart grid'i, konusulacaklar accordion/checklist'i ve sticky aksiyon bar eklendi.
- Takim sekmesindeki genel/tekrar eden "Grafik Yorumu / Risk yogunlugu / Ana neden dagilimi" blogu ekrandan kaldirildi; secilen takim detayi ilk siraya alindi.
- Risk skorlari secili datasetten gelen `team_analytics` / model olasiliklari uzerinden gosterilecek sekilde tasarlandi; zaman filtresi tablo/grafik ortalamalarini etkileyecek bicimde baglandi.
- Loading, empty ve error state eklendi. Dataset seciliyse empty state artik "Veri Yukle" yerine "Analizi Calistir" CTA'si gosterir; takim sekmesine dataset seciliyken girilirse toplu analiz otomatik baslatilir.
- Hover, pulse, shimmer, fade-in ve stagger micro-interaction katmani eklendi. `prefers-reduced-motion` destegi korunuyor.

## Sonraki dikkat noktasi

- Kullanici son olarak sayfanin yavas yuklendigini soyledi. Frontend tarafinda CTA ve state akisi duzeltildi; sonraki adim backend performansini olcmek olmali.
- Oncelikli inceleme: `loadBulkPredictions` isteginin backend tarafinda hangi adimda bekledigini structured timing log ile olcmek.
- Muhtemel performans kaynaklari: tum calisanlar icin feature build/predict, LLM narrative cagrilari, dataset satirlarindan takim analytics hesaplama.
- LLM yorumlari yavas/timeout oluyorsa takim analizinde default bulk prediction LLM'siz calismali; LLM sadece butonla tetiklenmeli.

## 2026-05-10 Senior Analiz - Nerede Kaldik

- Repo iki ana parcadan olusuyor: `propel-frontend` Vue 3/TypeScript/Tailwind, `propel-backend` FastAPI/SQLAlchemy/scikit-learn.
- Calisma agacinda uygulama kodu degisikligi gorunmedi; yalnizca bu not dosyasi izlenmeyen durumda.
- Takim Analizi UI tarafinda son gelinen nokta dogru: `ManagerAnalyticsView.vue` bulk state, empty/error/loading ve dataset seciliyken takim sekmesinde otomatik `loadBulkPredictions(false)` akisini kurmus.
- Yavaslik icin asil supheli backend `SoftwareMLService.predict_all_from_upload`: CSV/XLSX satirlari okunuyor, calisan bazinda gruplanıyor, her calisan icin `SoftwarePredictionService.predict_latest` ile tekrar feature build yapiliyor, sonra ayrica tum dataset icin `_team_analytics` tekrar feature build ve her satir icin predict/proba calistiriyor.
- Default takim analizi LLM'siz calisiyor; `use_llm_narrative=false` iken deterministic narrative donuyor. LLM sadece butonla `use_llm_narrative=true` geldiginde devreye giriyor ve secili takim icin 18-24 sn bloklayici cagrilar yapabilir.
- Backendde sadece toplam `software_bulk_predict_ok` latency log'u var; hangi alt adimin beklettigini gosteren structured timing henuz yok.

## 2026-05-10 Onerilen Sonraki Adimlar

- Ilk adim: `predict_all_from_upload` icine asama bazli timing log ekle (`load_rows`, `group_rows`, `load_artifact`, `employee_predictions`, `team_analytics`, `narratives`, `serialize_total`).
- Ikinci adim: lokal ya da mevcut demo dataset ile bulk endpoint'i calistirip loglardan p95/p50 ve en yavas asamayi tespit et.
- Ucuncu adim: eger `employee_predictions` veya `_team_analytics` yavas cikarsa feature dataset'i bir kez uretilip hem kisi tahminleri hem takim trendi ayni datasetten beslenecek sekilde refactor et.
- Dörduncu adim: LLM aksiyonunu async/job veya ayri endpoint olarak ayirmayi degerlendir; default dashboard response'u deterministic ve hizli kalmali.

## 2026-05-10 Timing Log Uygulamasi

- `propel-backend/app/services/software_ml_service.py` icindeki `predict_all_from_upload` fonksiyonuna structured timing log eklendi.
- Olculen asamalar: `load_rows_ms`, `group_rows_ms`, `load_artifact_ms`, `employee_predictions_ms`, `summaries_ms`, `team_analytics_ms`, `narratives_ms`, `total_ms`.
- Log mesaji `software_bulk_predict_timing {...}` seklinde JSON payload ile terminalde gorunur; ayni payload `extra` alanina da veriliyor.
- Ek metadata: `upload_id`, `target_column`, `row_count`, `employee_group_count`, `prediction_count`, `team_count`, `use_llm_narrative`, `llm_team`.
- Dogrulama: `python -m py_compile app/services/software_ml_service.py` basarili. `pytest` calistirilamadi; sistem PATH'inde yok ve mevcut `venv` icinde pytest kurulu degil.

## 2026-05-10 Siradaki Net Adim

- Backend server calisirken Takim Analizi ekranindan `Analizi Calistir` tetiklenmeli ve backend logundaki `software_bulk_predict_timing` satiri okunmali.
- En yuksek sure `employee_predictions_ms` ise kisi bazli tahminlerde tekrar feature build azaltilecek.
- En yuksek sure `team_analytics_ms` ise takim trendi icin tek tek satir prediction yerine batch/tek feature dataset refactor'u yapilacak.
- `narratives_ms` yuksekse LLM narrative tamamen ayri endpoint/job akisi olarak ayrilmali.

## 2026-05-10 Backend Performans Olcumu ve Refactor

- Docker backend container icinde `uploads/4_kutup_dataset_final_realistic_v8_fixed.csv` ile performans benchmark'i calistirildi.
- Ilk olcum: `row_count=1560`, `employee_group_count=30`, `team_count=4`, `employee_predictions_ms=1230`, `team_analytics_ms=43562`, `total_ms=45074`.
- Darbogaz net olarak `_team_analytics` icindeki satir satir `predict` / `predict_proba` cagrilari cikti.
- `SoftwareMLService._team_analytics` batch prediction kullanacak sekilde refactor edildi: tum `dataset.feature_rows` tek seferde `pipeline.predict` ve `pipeline.predict_proba` icine veriliyor, sonra sonuclar takim/period kirilimina dagitiliyor.
- Refactor sonrasi olcum: `employee_predictions_ms=1377`, `team_analytics_ms=736`, `total_ms=2504`.
- Backend container yeniden baslatildi; yeni kod aktif. Dogrulama: lokal ve container `py_compile` basarili. Container icinde `pytest` yok, bu nedenle test suite calistirilamadi.

## 2026-05-10 Sonraki Kontrol

- Frontend `http://localhost:5173` uzerinden Takim Analizi ekraninda `Analizi Calistir` denenmeli.
- Backend logunda `software_bulk_predict_timing` satiri kontrol edilip gercek endpoint response suresi dogrulanmali.
- Sonraki optimizasyon gerekecekse siradaki aday `employee_predictions_ms`; burada da kisi bazli tekrar feature build yerine tek datasetten latest-row tahmini tasarlanabilir.

## 2026-05-10 Takim Analizi - Toplanti Planla Aksiyonu

- `Toplanti Planla` butonu daha once yalnizca statik UI idi; `@click` handler yoktu.
- `ManagerAnalyticsView.vue` icinde toplantı planlama modalı eklendi.
- Modal secili takim icin baslik, varsayilan tarih/saat/sure, yonetici notu, otomatik gundem ve takim katilimci listesini dolduruyor.
- Onay butonu simdilik gercek bildirim gondermiyor; "bildirim taslagi hazirlandi" durumunu gosteriyor. Bunun nedeni backend tarafinda meeting/notification/calendar modeli ve API'sinin henuz olmamasi.
- Gercek urun akisi icin sonraki adim: backend'e `meetings` ve `notifications` kaynaklari eklenmeli; toplantı onaylaninca takim uyelerine uygulama ici bildirim, opsiyonel email/calendar entegrasyonu gonderilmeli.
- Dogrulama: `npm.cmd run type-check` calistirildi; eklenen dosyada hata cikmadi fakat mevcut proje hatasi olarak `EmployeeAnalysisView.vue` icinde `department_id` tipi eksik hatasi var.

## 2026-05-10 Toplanti ve Bildirim Backend Akisi

- Backend'e `Meeting`, `MeetingAttendee`, `Notification` modelleri eklendi.
- `POST /api/v1/meetings/team-risk` endpoint'i eklendi; manager/admin toplantı planlayinca katilimcilar ve uygulama ici bildirimler DB'ye yaziliyor.
- `GET /api/v1/notifications/me` endpoint'i eklendi; calisan kendi `in_app` bildirimlerini okuyabiliyor.
- Frontend `Toplanti Planla` modalindaki onay butonu artik gercek backend endpoint'ine POST atiyor ve donen `notification_count` bilgisini gosteriyor.
- `feedback.api.ts` icindeki `EmployeeForFeedback` tipine `department_id` eklendi; onceki type-check hatasi temizlendi.
- Docker backend yeniden baslatildi; `create_all` ile yeni tablolar olustu.
- Manuel dogrulama yapildi: `manager.yazilim@propel.com / manager123` ile toplantı olusturuldu, `developer1@propel.com / dev123` ile `/notifications/me` cagrisi bildirimi dondurdu.
- Test kayitlari: `meetings.id=1` icin 2 bildirim, `meetings.id=2` icin 1 bildirim olusturuldu.
- Dogrulama: backend `py_compile` basarili, frontend `npm.cmd run type-check` basarili.

## 2026-05-10 Toplanti Planla Butonu Canli Frontend Duzeltmesi

- Kullanici butonun halen calismadigini bildirdi.
- Kontrol sonucu yerel dosyada yeni kod olmasina ragmen `localhost:5173` uzerinden servis edilen Vite modulunde `openTeamMeetingPlanner`, `showMeetingPlanner`, `meetingsApi` guncellemeleri gorunmuyordu.
- Frontend container yeniden baslatildi: `docker compose restart frontend`.
- Yeniden baslatma sonrasi `http://localhost:5173/src/views/manager/ManagerAnalyticsView.vue?t=check` icinde `openTeamMeetingPlanner=True`, `Toplantiyi Planla=True`, `showMeetingPlanner=True`, `meetingsApi=True` dogrulandi.
- `npm.cmd run type-check` tekrar basarili. Frontend ve backend container'lari ayakta.
- Kullanici tarafinda sayfa hard refresh edilerek test edilmeli; eski HMR/cache state'i butonu pasif gostermis olabilir.

## 2026-05-10 Toplanti Modal Metni ve Bildirim Dogrulama

- Kullanici modalda halen "Bu asamada gercek bildirim gonderilmiyor..." metninin gorundugunu bildirdi.
- DB kontrolunde kullanicinin denemesinin gercekten kaydedildigi dogrulandi: `meetings.id=3` olustu ve `meeting_id=3` icin 9 notification kaydi var.
- Modal uyarisi guncellendi: artik onay verildiginde toplanti kaydi olusturulacagi ve takim uyelerine uygulama ici bildirim gonderilecegi yaziyor.
- Varsayilan durum metni de "Taslak hazir. Onaylayinca toplanti planlanir ve bildirimler gonderilir." olarak degistirildi.
- `npm.cmd run type-check` basarili. Frontend container yeniden baslatildi.
- Vite modul kontrolu: eski metin `False`, yeni `uygulama ici bildirim gonderilir=True`, `bildirimler gonderilir=True`.

## 2026-05-10 Takim Analizi - Excel Export

- Kullanici `XLS Indir` butonunun da calismadigini bildirdi ve multi-sheet Excel rehberi verdi.
- Backend'e `TeamReportExportRequest` semasi ve `TeamReportExportService` eklendi.
- `POST /api/v1/analytics/departments/software/team-report/export` endpoint'i eklendi; `openpyxl` ile `.xlsx` workbook uretip streaming response donuyor.
- Excel 5 sheet iceriyor: `Ozet Rapor`, `Takim Uyeleri Detay`, `12 Haftalik Trend`, `Risk Faktorleri`, `Aksiyon Plani`.
- Frontend `analyticsApi.exportSoftwareTeamReport` eklendi; `Excel Indir` butonu `downloadSelectedTeamExcel` fonksiyonuna baglandi.
- Payload secili takimdan uretiliyor: temel metrikler, ana sorun, aksiyonlar, tum takim uyeleri, 12 haftalik trend ve risk faktorleri.
- Dogrulama: backend `py_compile` basarili, frontend `npm.cmd run type-check` basarili.
- Manuel endpoint testi yapildi; `team_report_export_test.xlsx` 8480 byte olarak uretildi ve workbook sheetleri zip/xml kontrolu ile dogrulandi. Test dosyasi silindi.
- Backend/frontend container yeniden baslatildi. Canli Vite modul kontrolu: `downloadSelectedTeamExcel=True`, `exportSoftwareTeamReport=True`, `Excel raporu hazirlandi=True`.

## 2026-05-10 Excel Export - Sheet 2 Detaylari

- Kullanici Sheet 2 icin detayli tablo yapisini verdi.
- `Takim Uyeleri Detay` sheet'i guncellendi: ana tablo kolonlari `No`, `Isim Soyisim`, `Rol`, `Bolum`, `Risk Skoru`, `Risk Seviyesi`, `Durum`.
- Uyeler risk skoruna gore azalan siralaniyor.
- Risk skoru kolonuna data bar conditional formatting eklendi.
- Risk seviyesi renkli/emoji etiketlerle yaziliyor (`Yuksek`, `Orta`, `Dusuk`).
- Ana tablonun altina `EK BILGILER` bolumu eklendi: `Isim`, `Motivasyon Skoru`, `Is Tamamlama Orani`, `Devamsizlik Gunu`.
- Motivasyon kolonuna kirmizi-sari-yesil color scale conditional formatting eklendi.
- Frontend payload'i genisletildi: `department_code`, `risk_score`, `status`, `motivation_score`, `completion_rate`, `absence_days`.
- Veri yoksa ek KPI alanlari Excel'de `-` olarak kaliyor; risk skoru/takip durumu model olasiliklarindan uretiliyor.
- Dogrulama: backend `py_compile` ve frontend `npm.cmd run type-check` basarili. Manuel export dosyasi 8938 byte uretildi; Sheet 2 basliklari, `dataBar` ve `colorScale` XML icinde dogrulandi. Test dosyasi silindi.

## 2026-05-10 Excel Export - Sheet 3 Trend

- Kullanici Sheet 3 icin 12 haftalik trend tablosu ve chart beklentisini verdi.
- `12 Haftalik Trend` sheet'i guncellendi: kolonlar `Hafta`, `Tarih`, `Risk Skoru`, `Motivasyon Ort.`, `Kapasite Kullanimi`.
- Frontend trend payload'i genisletildi: `date`, `motivation_avg`, `capacity_usage`.
- Backend trend sheet'e `DEGISIM`, `OZET ISTATISTIK` ve `DEGERLENDIRME` bolumleri eklendi.
- Kapasite > %100 durumlari kirmizi dolgu/renk skalasi ile vurgulaniyor.
- Risk ve motivasyon cizgileri icin line chart eklendi.
- Ortalama/min/max/trend arrow ozeti eklendi.
- Dogrulama: backend `py_compile` ve frontend `npm.cmd run type-check` basarili. Manuel export dosyasi 11631 byte uretildi; Sheet 3 basliklari, `colorScale`, chart drawing ve `xl/charts/chart1.xml` dogrulandi. Test dosyasi silindi.

## 2026-05-10 Excel Export - Sheet 4 ve Sheet 5

- Kullanici Sheet 4 Risk Faktorleri ve Sheet 5 Aksiyon Plani formatini verdi.
- Sheet 4 guncellendi: ana tablo kolonlari `No`, `Risk Faktoru`, `Etki Seviyesi`, `Olasilik`, `Oncelik`.
- Sheet 4 altina `DETAYLI ACIKLAMALAR` bolumu eklendi: mevcut durum, hedef, gap, etkilenen kisi, beklenen sonuc.
- Risk faktorleri icin frontend payload'i genisletildi: `impact_level`, `probability`, `priority`, `current_state`, `target_state`, `gap`, `affected_people`, `expected_result`.
- Sheet 5 guncellendi: ana tablo kolonlari `No`, `Aksiyon`, `Sorumlu`, `Hedef Tarih`, `Oncelik`, `Durum`.
- Sheet 5 altina `AKSIYON DETAYLARI` ve `KONUSULACAK KONULAR` bolumleri eklendi.
- Aksiyonlar icin frontend payload'i genisletildi: `target_date`, `priority`, `status`; `talking_points` export payload'ina eklendi.
- Dogrulama: backend `py_compile` ve frontend `npm.cmd run type-check` basarili. Manuel export dosyasi 12643 byte uretildi; Sheet 4/5 basliklari ve detay bolumleri XML icinde dogrulandi. Test dosyasi silindi.

## 2026-05-10 Rapor Gonder Akisi

- Kullanici `Rapor Gonder` butonunun takim lideri, admin ve departman yoneticisine gondermesini istedi.
- Backend `POST /api/v1/notifications/team-report` endpoint'i eklendi.
- Endpoint secili takim icin alicilari gruplara gore turetiyor: adminler, departman yoneticileri, takim icindeki `lead` pozisyonlu kisiler.
- Frontend'e `notifications.api.ts` eklendi.
- `Rapor Gonder` butonu modal acacak sekilde baglandi; modalda `Takim lideri`, `Admin`, `Departman yoneticileri` checkbox'lari var.
- Onayla aksiyonu `shareSelectedTeamReport` ile backend'e POST atiyor ve olusan bildirim sayisini gosteriyor.
- Dogrulama: backend `py_compile` ve frontend `npm.cmd run type-check` basarili. Docker backend/frontend yeniden baslatildi.
- Manuel API testi: Backend raporu icin 3 bildirim olustu: Admin Kullanici, Ahmet Yilmaz (Departman yoneticisi), Murat Kaya (Takim lideri).
- DB ozetinde `team_report=3`, `meeting_invite=39` gorundu. Canli Vite modulunde `showReportShareModal`, `shareSelectedTeamReport`, `notificationsApi`, `Raporu Gonder` dogrulandi.

## 2026-05-14 Uygulama Calistirma ve Seed Islemi

- Eksik olan `propel-backend/.env` dosyasi olusturuldu ve Docker container'lari `docker compose up -d` ile baslatildi.
- `seed_data.py` icindeki `create_employees` fonksiyonunda `NameError: name 'employees' is not defined` hatasi tespit edildi ve `employees = []` ilklendirmesi eklenerek duzeltildi.
- Veritabani `docker exec propel_backend python seed_data.py` ile basariyla seed edildi (40 calisan, 5100 KPI kaydi, 1040 anket cevabi).
- Uygulama `http://localhost:5173` uzerinden kontrol edildi; `admin@propel.com / admin123` ile giris yapildi ve Genel Mudur Paneli'nin dolu oldugu (40 personel, risk analizi, organizasyonel ag) dogrulandi.

## 2026-05-14 Yeni Kullanıcı Erişimi ve Departman Tanımlama

- `manager.satis@propel.com` (şifre: `manager123`) ve `satis.employee@propel.com` (şifre: `satis123`) hesapları sisteme eklendi.
- `seed_data.py` güncellenerek:
    - Yeni kullanıcıların login yetkileri tanımlandı.
    - Her iki manager (`manager.yazilim` ve `manager.satis`) için `Employee` kayıtları (`team="Yonetim"`) oluşturuldu. Bu sayede yönetici dashboard'larındaki raporlama ve takım listesi özellikleri aktif hale geldi.
    - `satis.employee@propel.com` için "Satış" departmanında `Senior Sales Executive` rolünde çalışan kaydı oluşturuldu.
- Veritabanı `seed_data.py` ile yeniden baslatıldı; yeni kullanıcılar ve onlara ait veriler (KPI, anket vb.) başarıyla yüklendi.
- Doğrulama:
    - Satış Yöneticisi dashboard'unda departman "Satış" olarak ve ekip listesi (11 kişi) doğru şekilde görüntülendi.
    - Satış Personeli dashboard'unda AI Koç ve metriklerin satış departmanına özel (Müşteri Takibi vb.) çalıştığı teyit edildi.

## Sonraki Adımlar

- Uygulama şu an Yazılım ve Satış departmanları için tam fonksiyonel durumda.
- İhtiyaca göre diğer departmanlar (IK, Pazarlama vb.) için de benzer tanımlamalar yapılabilir.
- Takım Analizi ekranındaki LLM aksiyonları ve Excel export özellikleri yeni satış verileriyle test edilebilir.

## 2026-05-14 Login Degisikligi Gorunmeme Analizi

- Kullanici arkadasinin login ekraninda yaptigi degisikligi cektigini ama uygulamada gormedigini soyledi.
- Kontrol sonucu aktif branch `ml-team-analytics`; `origin/master` ise daha ileride ve `53a081e Kutup redesign and sales department users added` commit'i login ekranini degistiriyor.
- `git diff ml-team-analytics..origin/master` yalnizca `AGENTS.MD`, `propel-backend/seed_data.py` ve `propel-frontend/src/views/auth/LoginView.vue` farki gosterdi.
- Aktif branch'teki ve Vite'in servis ettigi `LoginView.vue` eski `propel / Welcome Back` tasarimi; `origin/master` dosyasi yeni `KUTUP / Hos Geldiniz` tasarimini iceriyor.
- Sonuc: degisiklikler localde mevcut remote branch'te var, fakat calisan uygulama `ml-team-analytics` branch'inden kalktigi icin login redesign gorunmuyor.
- Dikkat: `/login` route'u `requiresGuest`; kullanici zaten login ise router login ekranini gostermek yerine role gore dashboard'a yonlendirir. Test icin logout/localStorage temizleme ya da gizli pencere gerekebilir.

## 2026-05-14 Onerilen Sonraki Adim

- Eger yeni login tasarimi bu calisma branch'inde de isteniyorsa `origin/master` `ml-team-analytics` icine merge edilmeli ya da en dar cozum olarak `propel-frontend/src/views/auth/LoginView.vue` master'dan alinmali.
- Merge sonrasi frontend container/Vite yeniden baslatilip tarayicida hard refresh yapilmali; login'i gormek icin oturum aciksa cikis yapilmali.

## 2026-05-14 Takim Analizi Detaylar Yonlendirmesi

- Kullanici Takim Analizi ekranindaki uye kartlarinda `Detaylar` butonunun Calisan Analizi sayfasina yonlendirmesini istedi.
- `ManagerAnalyticsView.vue` icinde `openEmployeeAnalysis` artik prediction payload'indaki `summary_payload.db_employee_id` ile `manager-employee-analysis` rotasina gider.
- Yonlendirme query parametreleri: `employeeId` ve `team`; fallback olarak db employee id yoksa eski sayfa ici prediction akisi korunur.
- `EmployeeAnalysisView.vue` route query okumaya basladi; sayfa acildiginda `employeeId` eslesirse ilgili calisan otomatik seciliyor, `team` eslesirse takim filtresi de ayarlaniyor.
- Takim/departman filtresi degistiginde mevcut secili calisan filtre icinde kalmaya devam ediyorsa artik otomatik ilk calisana atlamiyor.
- Dogrulama: `npm.cmd run type-check` basarili. Canli Vite modulunde `EmployeeAnalysisView` icin `routeEmployeeId`, `applyRouteSelection` ve query watcher kodu goruldu.

## 2026-05-14 Departman Analizi KPI ML Ust Bolum

- Kullanici KPI ML analizindeki iki yeni adimin Calisan Analizi yerine Departman Analizi sayfasina konmasini istedi; urun mantigi geregi departman seviyesine uygulandi.
- `propel-frontend/src/views/manager/DepartmentAnalysisView.vue` icine sayfa ustunde 6 KPI karti eklendi: Toplam Calisan, Ortalama Performans, Top Performers, Dusus Gosteren, Junior Avg., Senior Avg.
- KPI kartlari secili departman/takim kapsamindaki calisanlar ve `/kpis/records` verisi uzerinden hesaplanir; KPI kaydi yoksa ekranin bos kalmamasi icin deterministik fallback skor/trend kullanilir.
- KPI kartlarinin altina Chart.js bubble chart eklendi: X ekseni KPI skoru, Y ekseni 4 haftalik trend, renkler takimlara gore; quadrant arka planlari ve X=90/Y=0 referans cizgileri var.
- Bubble chart tooltip'i isim, rol, takim, KPI ve trend gosterir; noktaya tiklayinca calisan detay modal'i acilir.
- Sag kolona gradient AI Analiz Ozeti paneli eklendi; genel durum, risk tespiti, basari hikayesi ve junior-senior farki canli metriklerden uretilir.
- `Detayli LLM Analizi Iste` butonu modal aciyor; simdilik canli KPI metriklerinden deterministik analiz taslagi gosteriyor, gercek LLM cagrisi sonraki adimda baglanabilir.
- Dogrulama: `npm.cmd run type-check` basarili. Frontend container yeniden baslatildi. `http://localhost:5173/admin/feedback-reports/department` uzerinde KPI kartlari, performans haritasi, AI paneli ve LLM modal'i in-app browser ile dogrulandi; konsol hatasi gorulmedi.

## 2026-05-14 Calisan Analizi Modern Performans Tablosu

- Kullanici Calisan Analizi sayfasina full-width modern performans tablosu eklenmesini istedi.
- `propel-frontend/src/views/manager/EmployeeAnalysisView.vue` icinde iki kolonlu mevcut calisan secimi/detay bolumunun altina yeni KPI ML tablosu eklendi.
- Tablo kolonlari: sira, calisan/avatar/kod, takim, rol badge, KPI progress bar, trend, 4 haftalik sparkline, guc badge ve durum badge.
- Tablo verisi `feedbackApi.getFeedbackCandidates()` ve `kpiApi.getAllVisibleRecords()` sonucundan hesaplanir; KPI kaydi eksikse deterministic fallback skor/trend kullanilir.
- Filtre bar eklendi: takim, rol, KPI alt sinir slider'i, trend ve durum filtreleri.
- Siralama eklendi: sortable kolonlarda aktif kolon ve artan/azalan yon gosterimi var.
- Pagination eklendi: 15/30/50 sayfa boyutu ve onceki/sonraki kontrolleri.
- `Tabloyu Excel'e Indir` butonu HTML tabanli `.xls` export uretir.
- Satir click aksiyonu hem sagdaki calisan detay secimini degistirir hem de KPI ozet modal'i acar.
- Eksik `SparklesIcon` import'u eklendi.
- Dogrulama: `npm.cmd run type-check` basarili. Frontend container yeniden baslatildi. `http://localhost:5173/admin/feedback-reports/employees` uzerinde tablo, pagination, export butonu ve satir modal'i in-app browser ile dogrulandi; runtime error gorulmedi.

## 2026-05-14 Calisan Analizi Rol Bazli Karsilastirma Chart

- Kullanici Calisan Analizi tablosunun altina rol bazli performans karsilastirma chart'i istedi.
- `EmployeeAnalysisView.vue` icine full-width `Rol Bazli Performans Karsilastirmasi` section'i eklendi.
- Chart.js / vue-chartjs ile grouped bar chart kuruldu: Junior, Mid, Senior, Lead rolleri icin ortalama KPI skoru ve 4 haftalik ortalama trend gosteriliyor.
- KPI dataset'i mavi bar, trend dataset'i pozitifse yesil negatifse kirmizi bar olarak gosteriliyor; trend icin sag eksen kullaniliyor.
- Genel KPI ortalamasi icin yatay kesikli referans cizgisi ve `Genel Ort.` etiketi eklendi.
- Bar ustu deger etiketleri ve detayli tooltip eklendi: rol calisan sayisi, ortalama KPI, ortalama trend, en yuksek ve en dusuk calisan.
- Sag tarafta istatistik sidebar'i eklendi: en yuksek fark, en hizli gelisen rol ve iyilestirme onerisi.
- Dogrulama: `npm.cmd run type-check` basarili. Frontend container yeniden baslatildi. In-app browser ile chart basligi, istatistikler ve canvas render'i dogrulandi; console error yok.

## 2026-05-14 Departman Analizi AI LLM Modal

- Kullanici Adim 5 LLM analiz akisini Calisan Analizi yerine Departman Analizi sayfasina eklemeyi istedi.
- `DepartmentAnalysisView.vue` ust sag filtre alanina gradient/pulse `AI ile Analiz` butonu eklendi.
- Mevcut AI modal genisletildi: loading/progress, genel durum analizi, takim dagilimi, rol bazli bulgular, risk analizi, basari hikayeleri ve aksiyon checklistleri eklendi.
- Modal verileri mevcut departman KPI hesaplarindan uretiliyor: `scopedEmployees`, `performanceEmployees`, `teamPerformanceStats`, `rolePerformanceStats`, `llmRiskPeople`, `llmSuccessPeople`, `llmActionGroups`.
- Alt aksiyon butonlari UI olarak eklendi: PDF Indir, Email Gonder, Kaydet. Backend/gercek dosya-gonderim akisi henuz bagli degil.
- Dogrulama: `npm.cmd run type-check` basarili. Frontend container yeniden baslatildi. In-app browser'da `AI ile Analiz` butonu ve modal bolumleri dogrulandi.

## 2026-05-14 KPI ML Analizi Backend Baglantisi

- Kullanici Departman Analizi ve Calisan Analizi ekranlarindaki yeni KPI/AI bolumlerinin hardcoded kalmamasini, backend'e baglanip gercek istatistikleri gostermesini istedi.
- Backend'e `GET /api/v1/analytics/performance/summary` endpoint'i eklendi.
- Yeni endpoint yetkiye gore calisan kapsamlarini uygular: admin icin opsiyonel `department_id`, departman yoneticisi icin kendi departmani, calisan icin kendi kaydi; `team` filtresi desteklenir.
- `AnalyticsService.get_performance_summary` gercek `employees` ve tum yetkili `kpi_records` kayitlarindan hesaplama yapar; `/kpis/records` endpoint'indeki varsayilan 100 kayit limiti artik bu dashboard hesaplarini etkilemez.
- Backend response'u calisan satirlari, takim ozetleri, rol ozetleri, KPI kart summary, AI insight metinleri, risk/success kisileri ve aksiyon gruplarini doner.
- KPI skoru hesaplamasi KPI-18 `Genel Performans Skoru` varsa onu kullanir; yoksa KPI yonune gore normalize edilmis gercek KPI degerlerinden hesaplanir. KPI-19 `Ayrilma Riski Skoru` performans ortalamasina karistirilmaz.
- Frontend `analytics.api.ts` yeni performans summary tipleri ve `getPerformanceSummary` metodu ile genisletildi.
- `DepartmentAnalysisView.vue` KPI kartlari, bubble chart, AI paneli ve AI modal verileri artik yeni backend endpoint'inden geliyor; eski sahte skor/trend fallback'leri kaldirildi.
- `EmployeeAnalysisView.vue` modern calisan tablosu ve rol bazli karsilastirma chart'i artik ayni backend performance summary endpoint'inden besleniyor; tablo KPI skoru, trend, sparkline, guc ve durum alanlarini backend hesaplarindan aliyor.
- Dogrulama: backend `py_compile` basarili, frontend `npm.cmd run type-check` basarili. Docker `db`, `backend`, `frontend` servisleri ayaga kaldirildi.
- Manuel API dogrulamasi: `admin@propel.com / admin123` ile `/analytics/performance/summary` cagrisi 30 calisan, 30 analiz edilen calisan, 4 takim, rol ortalamalari ve 4 insight dondurdu.
- Not: Yerel Node ortaminda `playwright` paketi bulunmadigi icin otomatik browser smoke testi kosulamadi; API ve derleme dogrulamasi tamamlandi.

## 2026-05-14 Takim Analizi - Detaylar rotasi (KPI ML Calisan Analizi)

- Sorun: Takim Uyeleri kartinda `Detaylar` `manager-employee-analysis` (`/manager/feedback-reports/employees`, 360 raporlari) rotasina gidiyordu; KPI/ML tahmin sonuclari orada degil.
- Cozum: `ManagerAnalyticsView.vue` icinde `openEmployeeAnalysis` artik `manager-kpi-ml-analysis` sayfasina `section=watchlist`, `employeeId` (dataset `employee_id`) ve `uploadId` query ile yonlendiriyor.
- `applyEmployeeDeepLinkFromRoute` + watch: URL'deki `employeeId`/`uploadId` ile dogru dataset secilip `loadDatasetEmployees` ve `loadPrediction(false)` tetikleniyor.
- Dogrulama: `npm.cmd run type-check` basarili.

## 2026-05-14 Takim Analizi - Sabit verilerin kaldirilmasi ve backend zaman damgasi

- Durum: Takim sekmesi buyuk olcude `getBulkSoftwarePredictions` + `team_analytics` ile bagliydi; buna karsin ust KPI kartlari, karsilastirmali trend grafiginde sahte ay etiketleri, risk grafigi tooltip/alt notlari, `Son guncelleme` (istemci saati), Excel export trendinde uydurma motivasyon/kapasite/tarih vardi.
- Backend: `SoftwareBulkPredictionResponse` icine `generated_at` (UTC) eklendi; `predict_all_from_upload` donusunde set ediliyor. Testte `generated_at` anahtari dogrulaniyor.
- Frontend: `teamKpiCards` toplu tahmin + `teamRiskSummaries` + `aggregateDepartmentRiskSeries` ile hesaplaniyor; sparkline polyline gercek serilerden. Coklu takim trend grafigi donem yoksa `D1..Dn` etiketleri (sahte takvim yok). Secili takim risk grafigi ekseni `trend_periods` ile hizalaniyor; tooltip ve opsiyonel `selectedTeamRiskLegendHints` veriden turetiliyor. `Son guncelleme` artik `generated_at`. Excel export trend satirlari donem etiketi + `risk_score`; sahte motivasyon/kapasite/tarih fonksiyonlari kaldirildi. Risk faktoru olasilik yuzdesi `count/total` ile. Konusulacaklar alt maddeleri yalnizca narrative `action_plan[].manager_talking_points` varsa gosteriliyor.
- Dogrulama: `py_compile`, `npm.cmd run type-check` basarili. LLM yokken aksiyon/konusulacaklar metinleri hala KPI/takim alanlarindan turetilen kisa UX fallback'leri kullanabilir (tam metin icin LLM veya genisletilmis narrative gerekir).
