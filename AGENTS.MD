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
