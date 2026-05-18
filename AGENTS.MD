# AGENTS.MD — KUTUP Agent Kılavuzu

> Bu dosya hem AI agent'lar için canlı bir proje rehberi hem de geliştirme günlüğüdür.
> Her sohbetin sonunda yapılan çalışma özeti, kalınan nokta ve sonraki adımlar buraya eklenir.

---

## Kalıcı Talimatlar

- Her sohbet sonunda yapılan çalışma özeti, kalınan nokta ve sonraki adımlar bu dosyaya kaydedilecek.
- Kod değişikliklerinden önce `py_compile` (backend) ve `npm.cmd run type-check` (frontend) doğrulaması yapılacak.
- Container yeniden başlatma: `docker compose restart backend` / `docker compose restart frontend`.
- Backend kod değişikliklerinden sonra **mutlaka** `docker restart propel_backend` çalıştır — uvicorn hot-reload kapalı.
- Yeni Python bağımlılıkları eklenirse `docker compose build backend` ile image yeniden build et.

---

## Proje Genel Bakış

**KUTUP**, yapay zeka destekli bir performans yönetim platformudur. Yazılım ve Satış departmanları için ML tabanlı KPI analizi, 360 derece geri bildirim, haftalık nabız anketleri ve departman/takım raporlama özellikleri sunar.

| Bileşen | Teknoloji | Port |
|---|---|---|
| Frontend | Vue 3 + TypeScript + Tailwind CSS | 5173 |
| Backend | FastAPI + SQLAlchemy | 8001 |
| Veritabanı | PostgreSQL 15 + pgvector | 5432 |

---

## Mimari

```
┌──────────────────────────────────────────────┐
│         Vue.js 3 SPA (propel-frontend)        │
│  Admin / Manager / Employee Dashboard'ları    │
│  Analytics Views · Feedback · Reports         │
└────────────────────┬─────────────────────────┘
                     │ REST / Axios + JWT
┌────────────────────▼─────────────────────────┐
│         FastAPI (propel-backend)              │
│  /api/v1/auth · /analytics · /kpis           │
│  /employees · /meetings · /notifications      │
└──────┬───────────────────────────────────────┘
       │ SQLAlchemy ORM
  ┌────┴──────────────────────────────────────┐
  │            Services Layer                  │
  │  SoftwareMLService · SalesMLService       │
  │  SoftwareNarrativeService                 │
  │  SalesNarrativeService                    │
  │  AnalyticsService · TeamReportExportSvc   │
  └────┬──────────────────────────────────────┘
       │
  ┌────▼──────────────────────────────────────┐
  │         Analytics / ML Layer              │
  │  analytics/departments/  (adapters)       │
  │    software.py · sales.py                 │
  │  analytics/features/                      │
  │    software.py · sales.py (feature eng.)  │
  │  analytics/training/                      │
  │    software.py (RF/HGB/LR)               │
  │    sales.py    (LightGBM+XGB+RF→LR stack) │
  │  analytics/prediction/                    │
  │    software.py · sales.py                 │
  │  analytics/artifacts/                     │
  │    software.py · sales.py (joblib store)  │
  │  analytics/explain/                       │
  │    software.py · sales.py (KPI drivers)   │
  │  analytics/importers/                     │
  │    software.py · sales.py (KPI import)    │
  │  analytics/kpi_registry.py                │
  │    SOFTWARE_KPI_REGISTRY (20 KPI)         │
  │    SALES_KPI_REGISTRY    (25 KPI)         │
  └────┬──────────────────────────────────────┘
       │
  ┌────▼──────────────────┐
  │ PostgreSQL + pgvector │
  │ 15+ tablo, embedding  │
  └───────────────────────┘
```

---

## Teknoloji Yığını

### Backend (`propel-backend/`)
- **FastAPI** 0.104.1, **Uvicorn** 0.24.0
- **SQLAlchemy** 2.0.23, **Pydantic** 2.5.0
- **JWT**: python-jose 3.3.0, bcrypt 3.1.7
- **ML**: scikit-learn 1.3.2, pandas 2.1.3, numpy 1.26.2, joblib 1.3.2
- **Stacking Ensemble (Satış)**: **lightgbm 4.3.0**, **xgboost 2.0.3** + scikit-learn StackingClassifier
- **LLM**: Ollama (yerel) veya Google Gemini API
- **Export**: openpyxl 3.1.5
- **System dep**: `libgomp1` (LightGBM için, Dockerfile'da yüklü)

### Frontend (`propel-frontend/`)
- **Vue 3.4.0** + **TypeScript 5.3.0**, **Vite 5.0.12**
- **Pinia** 2.1.7 (state), **Vue Router** 4.2.5
- **Tailwind CSS** 3.4.1, **Chart.js** 4.4.1 + vue-chartjs 5.3.0
- **axios** 1.6.0

---

## Dizin Yapısı

```
kutup-neww/
├── propel-backend/
│   ├── app/
│   │   ├── api/routers/
│   │   │   ├── analytics.py        # Tüm ML/analytics endpoint'leri (software + sales)
│   │   │   ├── admin_uploads.py    # CSV/XLSX upload (department_key desteğiyle)
│   │   │   ├── auth.py · employees.py · kpis.py
│   │   │   ├── meetings.py · notifications.py
│   │   │   └── feedback.py · survey_responses.py
│   │   ├── db/models/              # SQLAlchemy modelleri
│   │   ├── schemas/
│   │   │   └── analytics.py        # Software + Sales Pydantic şemaları
│   │   ├── services/
│   │   │   ├── software_ml_service.py
│   │   │   ├── software_narrative_service.py
│   │   │   ├── sales_ml_service.py       # ★ YENİ
│   │   │   ├── sales_narrative_service.py # ★ YENİ
│   │   │   ├── analytics_service.py
│   │   │   └── team_report_export_service.py
│   │   ├── analytics/
│   │   │   ├── kpi_registry.py     # SOFTWARE_KPI_REGISTRY + SALES_KPI_REGISTRY
│   │   │   ├── registry.py         # Adapter kayıt (software + sales)
│   │   │   ├── contracts.py        # Shared data contracts
│   │   │   ├── departments/
│   │   │   │   ├── base.py
│   │   │   │   ├── software.py
│   │   │   │   └── sales.py        # ★ YENİ (tam implementasyon)
│   │   │   ├── features/
│   │   │   │   ├── software.py
│   │   │   │   └── sales.py        # ★ YENİ (25 KPI + derived features)
│   │   │   ├── training/
│   │   │   │   ├── software.py     # RF/HGB/LR
│   │   │   │   └── sales.py        # ★ YENİ (LightGBM+XGB+RF→LR stacking)
│   │   │   ├── prediction/
│   │   │   │   ├── software.py
│   │   │   │   └── sales.py        # ★ YENİ
│   │   │   ├── artifacts/
│   │   │   │   ├── software.py
│   │   │   │   └── sales.py        # ★ YENİ
│   │   │   ├── explain/
│   │   │   │   ├── software.py
│   │   │   │   └── sales.py        # ★ YENİ (KPI eşik/trend açıklamaları)
│   │   │   ├── importers/
│   │   │   │   ├── software.py
│   │   │   │   └── sales.py        # ★ YENİ
│   │   │   └── artifacts_store/
│   │   │       ├── software/       # Yazılım model artifact'ları (joblib)
│   │   │       └── sales/          # ★ YENİ — Satış model artifact'ları
│   │   ├── ml/                     # Genel ML (sentiment, risk)
│   │   └── core/                   # Config + güvenlik
│   ├── main.py
│   ├── seed_data.py
│   ├── Dockerfile                  # libgomp1 eklendi (LightGBM gereksinimi)
│   └── requirements.txt            # lightgbm==4.3.0, xgboost==2.0.3 eklendi
├── propel-frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── admin/
│   │   │   ├── manager/
│   │   │   ├── employee/
│   │   │   ├── feedback/
│   │   │   └── auth/
│   │   ├── components/
│   │   ├── services/api/
│   │   ├── stores/
│   │   ├── composables/
│   │   └── router/index.ts
│   └── package.json
├── docker-compose.yml
├── AGENTS.MD                       # Bu dosya
└── CLAUDE.md                       # AGENTS.MD kopyası (Claude Code için)
```

---

## API Endpoint'leri

### Kimlik Doğrulama
| Yöntem | Yol | Açıklama |
|---|---|---|
| POST | `/api/v1/auth/login` | Giriş → JWT (form-data: username + password) |
| POST | `/api/v1/auth/register` | Kayıt |
| GET | `/api/v1/auth/me` | Mevcut kullanıcı |

### Analitik & ML — Yazılım Departmanı
| Yöntem | Yol | Açıklama |
|---|---|---|
| GET | `/api/v1/analytics/departments` | Departman konfigürasyonları |
| GET | `/api/v1/analytics/departments/{key}/overview` | Departman özeti |
| GET | `/api/v1/analytics/departments/software/datasets` | Yüklü dataset'ler |
| GET | `/api/v1/analytics/departments/software/datasets/{id}/employees` | Dataset çalışanları |
| GET | `/api/v1/analytics/departments/software/datasets/{id}/model-state` | Model durumu |
| POST | `/api/v1/analytics/departments/software/models/train` | ML modeli eğit |
| GET | `/api/v1/analytics/departments/software/predictions/latest` | Tekil tahmin |
| GET | `/api/v1/analytics/departments/software/predictions/bulk` | Toplu tahmin |
| POST | `/api/v1/analytics/departments/software/team-report/export` | Excel raporu indir |
| GET | `/api/v1/analytics/performance/summary` | KPI/performans özeti |

### Analitik & ML — Satış Departmanı ★ YENİ
| Yöntem | Yol | Açıklama |
|---|---|---|
| GET | `/api/v1/analytics/departments/sales/datasets` | Satış dataset'leri |
| GET | `/api/v1/analytics/departments/sales/datasets/{id}/employees` | Dataset çalışanları |
| GET | `/api/v1/analytics/departments/sales/datasets/{id}/model-state` | 4 hedef model durumu |
| POST | `/api/v1/analytics/departments/sales/models/train` | Stacking ensemble eğit |
| GET | `/api/v1/analytics/departments/sales/predictions/latest` | Tekil satış tahmini |
| GET | `/api/v1/analytics/departments/sales/predictions/bulk` | Toplu satış tahmini |

### KPI
| Yöntem | Yol | Açıklama |
|---|---|---|
| GET | `/api/v1/kpis` | KPI tanımları |
| POST | `/api/v1/kpis` | KPI oluştur |
| GET | `/api/v1/kpis/records` | KPI kayıtları (sayfalı) |
| POST | `/api/v1/kpis/records` | KPI kaydı ekle |

### Çalışanlar, Departmanlar, Toplantılar, Bildirimler
| Yöntem | Yol | Açıklama |
|---|---|---|
| GET/POST/PUT | `/api/v1/employees[/{id}]` | CRUD |
| GET/POST | `/api/v1/departments` | CRUD |
| POST | `/api/v1/meetings/team-risk` | Risk toplantısı planla + bildirim gönder |
| GET | `/api/v1/meetings` | Toplantı listesi |
| GET | `/api/v1/notifications/me` | Kullanıcı bildirimleri |
| POST | `/api/v1/notifications/team-report` | Rapor paylaş |
| POST | `/api/v1/admin/uploads` | CSV/XLSX yükle (department_key parametresi ile) |
| GET/POST | `/api/v1/surveys[/responses]` | Anket |
| GET/POST | `/api/v1/feedback` | 360 geri bildirim |

---

## Veritabanı Modelleri

| Model | Önemli Alanlar |
|---|---|
| `User` | id, email, hashed_password, role (admin/department_manager/employee) |
| `Employee` | id, user_id→User, department_id→Department, team, position, experience_years, external_employee_code |
| `Department` | id, name (unique) |
| `KPI` | id, name, unit, department_id, target_value |
| `KPIRecord` | id, kpi_id, employee_id, value, period_date |
| `SurveyResponse` | id, employee_id, q1_motivation…q6_suggestion |
| `Feedback` / `FeedbackRequest` / `FeedbackQuestion` | 360 derece feedback sistemi |
| `Meeting` + `MeetingAttendee` | id, title, department_id, team, scheduled_at |
| `Notification` | id, recipient_id, notification_type, title, message, is_read |
| `DataUpload` | id, file_name, department_key (raw_info.department_key), row_count, status |
| `FeedbackNLPAnalysis` / `EmployeeNLPProfile` | NLP/sentiment sonuçları |
| `FeedbackMemoryChunk` | embedding (pgvector) — RAG desteği |

---

## Rol Bazlı Erişim (RBAC)

| Rol | Erişim |
|---|---|
| **admin** | Tüm sistem, veri yönetimi, tüm departmanlar, ML model eğitimi |
| **department_manager** | Kendi departmanı analitik, takım yönetimi, çalışan değerlendirme |
| **employee** | Kişisel performans verisi, self-assessment, geri bildirim |

---

## ML Sistemi

### Yazılım Departmanı Pipeline

**Hedefler**: `performance_band`, `attrition_risk_band`

**Model seçenekleri**: `logistic_regression`, `random_forest`, `hist_gradient_boosting`

1. **Upload**: CSV/XLSX `POST /admin/uploads?department_key=software` ile yüklenir.
2. **Train**: `POST /analytics/departments/software/models/train` → sklearn pipeline eğitilir, `artifacts_store/software/` altına joblib.
3. **Predict**: Tekil (`/predictions/latest`) veya toplu (`/predictions/bulk`).
4. **Team Analytics**: Dönem × takım kırılımında aggregated risk trend.
5. **Narrative**: `use_llm_narrative=true` → LLM, aksi halde deterministik fallback.

**KPI Registry**: `SOFTWARE_KPI_REGISTRY` — 20 KPI (GTO, ZTO, GKE, KKKE, BY, KBO, CRKO vb.)

---

### Satış Departmanı Pipeline ★ YENİ

**Hedefler**: `Performance_Drop_Target`, `Burnout_Target`, `Resignation_Target`, `High_Risk_Target`

**Model**: `stacking_lgbm_xgb_rf_lr` — LightGBM + XGBoost + RandomForest → LogisticRegression meta-learner (sklearn StackingClassifier, cv=3)

**Fallback**: Eğitim setinde herhangi bir sınıfta < 6 örnek varsa `random_forest_fallback` pipeline kullanılır (ör. Burnout_Target çok seyrek ise).

**Veri Akışı**:
1. **Upload**: CSV/XLSX `POST /admin/uploads` body'de `department_key=sales` ile yüklenir.
2. **Feature Engineering** (`analytics/features/sales.py`):
   - Doğrudan kolonlar: `Total_Activity`, `Lead_to_Win_Conversion`, `Average_Sales_Cycle_Days`, `Sales_Workload_Index`, `Followup_OnTime_Rate`, `Customer_Satisfaction`, `CRM_Usage_Rate`, `Motivation_Score`, `Peer_Support_Count` vb.
   - Türetilen özellikler: `sales_goal_attainment` (rev/target), `new_customer_rate`, `win_rate`, `pipeline_coverage`, `aged_pipeline_rate`, `complaint_rate`, `team_contribution`, `training_completion`
   - Time features: lag_1, rolling_4, trend_4 (her KPI için)
   - Takım-relatif: `revenue_vs_team` (KPI-8 GKP)
   - Rolling SIYS (iş yükü stres skoru), motivasyon eğimi (MTE)
   - Kolon normalizasyonu: case-insensitive (Excel'deki `Employee_ID`, `Week` vb. otomatik tanınır)
   - `employee_id` parseri: `EMP_001`, `SA-003`, `1` formatları desteklenir
   - `year` eksikse → 2024 varsayılan
3. **Train**: `POST /analytics/departments/sales/models/train` → `test_period_count` dönem test seti.
4. **Bulk Predict**: `GET /predictions/bulk` → 30 çalışan × bölge/rol bazlı sonuç, takım narratifi, team_analytics.
5. **Narrative**: LLM destekli veya deterministik satış odaklı yorum.

**KPI Registry**: `SALES_KPI_REGISTRY` — 25 KPI:

| # | Kod | Ad | Kaynak |
|---|---|---|---|
| 1 | SHGO | Satış Hedef Gerçekleşme Oranı | rev/target veya `Sales_Target_Achievement` |
| 2 | SAY | Satış Aktivite Yoğunluğu | `Total_Activity` |
| 3 | NMKO | Yeni Müşteri Kazanım Oranı | new/total veya `New_Customer_Acquisition_Rate` |
| 4 | LMDO | Lead→Müşteri Dönüşüm Oranı | `Lead_to_Win_Conversion` |
| 5 | TKO | Tekliften Kazanıma Dönüşüm | won/(won+lost) veya `Proposal_Win_Rate` |
| 6 | OSDS | Ort. Satış Döngüsü Süresi | `Average_Sales_Cycle_Days` |
| 7 | OSD | Ortalama Satış Değeri | `Average_Sale_Value` |
| 8 | GKP | Göreli Kazanım Performansı | rev/team_avg (hesaplanan) |
| 9 | KKS | Kazanım Kalite Skoru | `Won_Deal_Count` |
| 10 | PSO | Pipeline Sağlık Oranı | pipeline/target veya `Pipeline_Health_Ratio` |
| 11 | PYO | Pipeline Yaşta Olma Oranı | aged/open veya `Pipeline_Aging_Rate` |
| 12 | SIYE | Satış İş Yükü Endeksi | `Sales_Workload_Index` |
| 13 | SIYS | Sürekli İş Yükü Stres Skoru | rolling overload (hesaplanan) |
| 14 | TDO | Takip Disiplini Oranı | `Followup_OnTime_Rate` |
| 15 | CSAT | Müşteri Memnuniyeti | `Customer_Satisfaction` |
| 16 | SO | Şikayet Oranı | complaints/won veya `Complaint_Rate` |
| 17 | CRMD | CRM Disiplin Metriği | `CRM_Usage_Rate` |
| 18 | SEKS | Satış Ekibi Katkı Skoru | mentor+peer veya `Team_Contribution_Score` |
| 19 | MS | Motivasyon Skoru | `Motivation_Score` |
| 20 | EKS | Ekip Destek Katkı Skoru | `Peer_Support_Count` |
| 21 | MTE | Motivasyon Trend Eğimi | son 4 hafta lineer eğim (hesaplanan) |
| 22 | GKS | Gelişim Katılım Skoru | completed/recommended veya `Development_Participation_Rate` |
| 23-25 | SPS/BRS/PPE | Bileşik KPI'lar | target_candidate, model feature değil |

**Dataset Kolon Uyumluluğu**: Excel/CSV'deki `Employee_ID`, `Week`, `Region`, `Role_Level` gibi Pascal/mixed case kolonlar otomatik normalize edilir. `year` kolonu olmayan dataset'lerde 2024 varsayılan.

**Önemli Kısıt**: `Burnout_Target` çok seyrek (1560 satırda 1 pozitif örnek tipik) → eğitim başarısız olabilir; `Performance_Drop_Target`, `Resignation_Target`, `High_Risk_Target` çalışır.

---

### Ortak ML Altyapısı

- **Artifact store**: `analytics/artifacts_store/{department}/{target_column}/runs/{run_id}/` — `model.joblib` + `metadata.json` + `latest.json` pointer
- **Feature importance**: Stacking'de base learner'ların feature importance ortalaması alınır
- **Explanation**: `top_drivers` — KPI Registry'den eşik durumu (`threshold_status`), 4 haftalık trend sinyali (`trend_signal`), rasyonel metin
- **Narrative layer**: Deterministic fallback (her zaman) + LLM enhancement (isteğe bağlı, `use_llm_narrative=true`)

---

## Ortam Yapılandırması

### Backend `.env` (`propel-backend/.env`)
```env
SECRET_KEY=kutup-super-secret-key-2026
POSTGRES_PASSWORD=123456
ENABLE_PGVECTOR=false
ENABLE_LOCAL_SENTIMENT_MODEL=false
EMBEDDING_PROVIDER=hash
# Opsiyonel:
# OLLAMA_URL=http://ollama:11434
# GEMINI_API_KEY=...
# GEMINI_MODEL=gemini-pro
```

**Not**: `config.py`'de `extra="forbid"` var → `.env`'e tanımsız field ekleme!

### Docker Compose Servisleri
| Servis | Image | Port | Notlar |
|---|---|---|---|
| db | pgvector/pgvector:pg15 | 5432 | POSTGRES_PASSWORD=123456 |
| backend | FastAPI (custom) | 8001→8000 | env_file + DATABASE_URL override |
| frontend | Vue dev server | 5173 | VITE_API_URL=http://localhost:8001/api/v1 |

### Hızlı Başlatma
```bash
docker compose up -d
docker exec propel_backend python seed_data.py
# Admin: admin@propel.com / admin123
# Swagger: http://localhost:8001/docs
```

---

## Geliştirme Notları ve Bilinen Kısıtlamalar

- **Backend Restart Zorunlu**: uvicorn `--reload` olmadan çalışıyor. Kod değişikliği sonrası `docker restart propel_backend` şart.
- **Satış ML Kolon Normalizasyonu**: `SalesFeatureBuilder` tüm satır key'lerini lowercase yapıyor. `Employee_ID` → `employee_id`, `Region` → team olarak kullanılır.
- **Burnout_Target**: Gerçek dataset'te genellikle çok seyrek. Eğitim başarısız olabilir (normal).
- **Türkçe Karakter Encoding**: JSON response'larında bazı client'lar `DoÄu Anadolu` gösterebilir — bu UTF-8 display artifact, gerçek veri doğru.
- **Testler**: `pytest` yapılandırılmış fakat `app/tests/` dizini henüz boş.
- **Playwright**: Yerel ortamda yüklü değil; browser smoke testi çalışmıyor.
- **LLM Gecikme**: Narrative LLM çağrıları 18-24 sn bloklayıcı. Default `use_llm_narrative=false` ile deterministik ve hızlı.
- **pgvector**: `ENABLE_PGVECTOR=true` gerektirir, varsayılan `false`.
- **Swagger Login**: `/api/v1/auth/login` form-data (username/password), JSON değil!

---

## 2026-05-14 Devam Eden Yerel Calisma Notlari
- Durum: Takim sekmesi buyuk olcude `getBulkSoftwarePredictions` + `team_analytics` ile bagliydi; buna karsin ust KPI kartlari, karsilastirmali trend grafiginde sahte ay etiketleri, risk grafigi tooltip/alt notlari, `Son guncelleme` (istemci saati), Excel export trendinde uydurma motivasyon/kapasite/tarih vardi.
- Backend: `SoftwareBulkPredictionResponse` icine `generated_at` (UTC) eklendi; `predict_all_from_upload` donusunde set ediliyor. Testte `generated_at` anahtari dogrulaniyor.
- Frontend: `teamKpiCards` toplu tahmin + `teamRiskSummaries` + `aggregateDepartmentRiskSeries` ile hesaplaniyor; sparkline polyline gercek serilerden. Coklu takim trend grafigi donem yoksa `D1..Dn` etiketleri (sahte takvim yok). Secili takim risk grafigi ekseni `trend_periods` ile hizalaniyor; tooltip ve opsiyonel `selectedTeamRiskLegendHints` veriden turetiliyor. `Son guncelleme` artik `generated_at`. Excel export trend satirlari donem etiketi + `risk_score`; sahte motivasyon/kapasite/tarih fonksiyonlari kaldirildi. Risk faktoru olasilik yuzdesi `count/total` ile. Konusulacaklar alt maddeleri yalnizca narrative `action_plan[].manager_talking_points` varsa gosteriliyor.
- Dogrulama: `py_compile`, `npm.cmd run type-check` basarili. LLM yokken aksiyon/konusulacaklar metinleri hala KPI/takim alanlarindan turetilen kisa UX fallback'leri kullanabilir (tam metin icin LLM veya genisletilmis narrative gerekir).

## 2026-05-14 360 Feedback Soru Kaynagi Analizi

- Kullanici 360 derece feedback tarafindaki uretilen sorularin API'den gelip gelmedigini sordu.
- Frontend akisi dogrulandi: `FeedbackModal.vue` kisi secilince `feedbackApi.getCurrentQuestion(receiverId)` cagiriyor; servis `GET /feedbacks/current-question?receiver_id=...` endpoint'ine gidiyor.
- Backend akisi dogrulandi: `feedbacks.py` endpoint'i `FeedbackService.get_current_weekly_question` sonucunu `question_text` ve `is_ai_generated` ile donuyor.
- Soru uretim zinciri: once ayni hafta/yon/departman icin DB'deki AI-generated cache aranir; yoksa `AIService.generate_weekly_question` ile Gemini/Ollama denenir; basarisizsa seed edilen `feedback_questions` havuzuna; o da yoksa `AIService.build_template_question` deterministic fallback'ine duser.
- Canli DB kontrolu: `feedback_questions` tablosunda 9 kayit goruldu; 2 kayit `is_ai_generated=True`, kalanlar seed veya deterministic fallback. Yani soru metni frontend'de hardcoded degil, API/DB uzerinden geliyor; fakat her soru mutlaka canli AI uretimi degil.
- Sonraki adim: 360 analiz kalitesini iyilestirmek icin once soru lifecycle'i netlestirilmeli: soru kaynagi etiketi UI'da gosterilebilir, haftalik/departman/rol bazli soru kapsami genisletilebilir, seed ve AI promptlari analiz hedeflerine gore yeniden tasarlanabilir.

## 2026-05-14 360 Feedback NLP Uyumlu Soru Iyilestirmesi

- Kullanici Gemini'ye daha iyi komut vererek sorularin NLP analizine uygun, daha spesifik ve nitelikli hale getirilmesini istedi.
- `AIService._build_prompt` Gemini prompt'u guncellendi: model artik IK stratejisti + organizasyon psikologu + NLP veri tasarim uzmani roluyle calisir.
- Prompt'a NLP analiz hedefi eklendi: cevap metninden duygu tonu, motivasyon, psikolojik guven, is birligi, destek ihtiyaci, burnout/flight risk ve aksiyon onerisi cikarilabilmeli.
- Soru kurallari netlestirildi: 18-34 kelime, tek davranis/olay odagi, son haftadan somut ornek veya durum isteme, davranisin etkisini sordurma, destek/risk/motivasyon/guven/aidiyet/gelisim sinyali yakalama.
- Kompakt Ollama fallback prompt'u da ayni mantikla guncellendi.
- `AIService.is_question_nlp_ready` kalite kapisi eklendi; soru zorunlu odak terimini, kanit cue'larini (`somut`, `ornek`, `gozlem`, `hangi durumda` vb.) ve analiz sinyal cue'larini (`etki`, `risk`, `motivasyon`, `guven`, `destek` vb.) tasimiyorsa kabul edilmiyor.
- `generate_weekly_question` artik Gemini/Ollama ciktisini bu kalite kapisindan geciriyor.
- `build_template_question` fallback'leri yeniden yazildi; eski genel "nasil degerlendirirsin" sorulari yerine somut davranis + etki + risk/destek sinyali isteyen sorular uretiyor.
- `FeedbackService.get_current_weekly_question` eski AI cache veya seed soruyu yalnizca NLP kalite kapisindan gecerse donduruyor; gecmezse yeni AI sorusu deneniyor, olmazsa yeni nitelikli template fallback kullaniliyor.
- Dogrulama: lokal `python -m py_compile app/services/ai_service.py app/services/feedback_service.py` basarili; container icinde ayni py_compile basarili. Container icinde 4 ornek template soru `ready=True` dondurdu.
- Backend container yeniden baslatildi; yeni soru uretim mantigi aktif.

## Sonraki Adim

- 360 Feedback ekraninda farkli rol/departman kombinasyonlariyla soru cekilip DB'deki yeni `is_ai_generated=True` kayitlar incelenmeli.
- Gerekirse mevcut eski `feedback_questions` kayitlari arsivlenip/temizlenerek yeni prompt'un urettigi nitelikli sorularin daha tutarli gorunmesi saglanabilir.

## 2026-05-14 360 Feedback Speech-to-Text

- Kullanici 360 feedback cevaplarinin yalnizca klavye ile yazilmasinin vakit kaybi oldugunu, Web Speech API ile speech-to-text eklemek istedigini soyledi.
- `FeedbackModal.vue` icine Web Speech API entegrasyonu eklendi.
- Modalda `Sesle Cevapla` / `Dinlemeyi Durdur` butonu, mikrofon durum metni, canli ara transkript (`interimTranscript`), karakter sayaci, `Temizle` butonu ve tarayici/mikrofon hata mesajlari eklendi.
- `recognition.lang = 'tr-TR'`, `continuous = true`, `interimResults = true` ayarlari kullaniliyor.
- Final transkript mevcut textarea metnine ekleniyor; kullanici isterse elle duzenleyebiliyor. Gonderimde mevcut `response_text` alanina son metin gidiyor, bu nedenle backend NLP akisi degismeden calisiyor.
- Ses kaydi backend'e gonderilmiyor; metne cevirme tarayici tarafinda yapiliyor. Desteklenmeyen tarayicida buton disable olup uyari gorunuyor.
- Modal kapaninca veya component unmount olunca mikrofon otomatik durduruluyor.
- Dogrulama: `npm.cmd run type-check` basarili. Frontend container yeniden baslatildi. Canli Vite modulunde `SpeechRecognition=True`, `Sesle Cevapla=True`, `tr-TR=True` dogrulandi.

## Sonraki Adim

- Tarayicida mikrofon izni verilerek manuel ses testi yapilmali; Chrome/Edge ve `localhost` uzerinde Web Speech API beklenen sekilde calisir.
- Ileride analizlerde kaynak takibi istenirse backend `feedback_responses` tablosuna `input_method` ve opsiyonel `speech_duration_seconds` alanlari eklenebilir; mevcut ilk surumde ses sadece metin girisini hizlandirir.

## 2026-05-14 360 Feedback Gonderim Yavasligi ve Background NLP

- Kullanici speech-to-text ile cevap yazdiktan sonra `Gonder` isleminin uzun surdugunu soyledi ve testlerin backend'e gidip gitmedigini sordu.
- Canli DB kontrolu: son testler backend'e yazilmis. `feedback_responses.id=430` ve `id=431` kayitlari goruldu; ikisinde de `nlp_record=True`.
- Yavasligin nedeni speech-to-text degil; `POST /feedbacks/submit` icinde cevap kaydedildikten sonra ayni request suresince `AIService.analyze_weekly_feedback`, `NLPService.save_weekly_analysis`, `NLPService.rebuild_employee_profile`, `NLPService.refresh_employee_monthly_badges` ve `RAGService.upsert_weekly_feedback_memory` calisiyordu.
- `feedbacks.py` submit endpoint'i `BackgroundTasks` kullanacak sekilde guncellendi.
- `FeedbackService.submit_weekly_feedback` icine `process_nlp_sync` parametresi eklendi. Endpoint artik `process_nlp_sync=False` ile cevabi ve zorunlu atama durumunu hemen commit edip 201 donuyor.
- NLP/LLM/profil/rozet/RAG islemleri `FeedbackService.process_weekly_feedback_analysis_in_background` ile ayri DB session acilarak arka planda calisiyor.
- Senkron servis kullanimi gereken yerler icin varsayilan `process_nlp_sync=True` korundu.
- Dogrulama: lokal ve container `py_compile` basarili. Backend container yeniden baslatildi.

## Sonraki Adim

- UI tarafinda gonderimden sonra "Feedback kaydedildi, analiz arka planda hazirlaniyor" gibi kisa durum mesaji gosterilebilir.
- Daha saglam uretim mimarisi icin FastAPI BackgroundTasks yerine Celery/RQ gibi kalici job queue dusunulebilir; mevcut local/demo akisi icin background task yeterli.

## 2026-05-14 KPI / 360 Feedback Sayfa Ayrimi Analizi

- Kullanici KPI takim analizinden `Detaylar` ile gidilen Calisan Analizi'nin KPI & ML basligi altinda degil, 360 Derece Feedback basligi altinda konumlandigini; ayrica 360 Departman Analizi icinde KPI analizleri gorundugunu belirtti.
- Route kontrolu:
  - `ManagerAnalyticsView.vue` KPI & ML sayfasi `/manager/kpi-ml-analysis` altinda calisiyor ve `section=model|department|teams|watchlist|technical` kullaniyor.
  - KPI Takim Analizi `openEmployeeAnalysis` fonksiyonu su anda dogru rotaya gidiyor: `manager-kpi-ml-analysis?section=watchlist&employeeId=...&uploadId=...`.
  - Ancak `EmployeeAnalysisView.vue` `/manager/feedback-reports/employees` ve `/admin/feedback-reports/employees` rotalarina bagli; 360 Feedback menusu altinda gorunuyor.
  - `DepartmentAnalysisView.vue` `/manager/feedback-reports/department` ve `/admin/feedback-reports/department` rotalarina bagli; 360 Feedback menusu altinda gorunuyor.
- Icerik kontrolu:
  - `EmployeeAnalysisView.vue` 360 raporlarini (`feedbackApi.getEmployee360SummaryReport`) gosterirken ayni dosyada `analyticsApi.getPerformanceSummary` ile KPI modern tablo ve rol bazli performans chart'i da calistiriyor.
  - `DepartmentAnalysisView.vue` 360 NLP raporlarini (`feedbackApi.getDepartment360SummaryReport`, NLP charts/deep/RAG) gosterirken ustte KPI kartlari, KPI bubble chart ve KPI AI analiz modal'i da calistiriyor.
- Sonuc: Yonlendirme artik buyuk olcude dogru; esas problem KPI UI/analiz bloklarinin 360 feedback view dosyalarina yerlestirilmis olmasi. Bu yuzden 360 sayfalari KPI analizi yapiyormus gibi gorunuyor.

## Onerilen Duzeltme Sirasi

- 1. 360 Feedback sayfalarini saf hale getir: `EmployeeAnalysisView.vue` icinde yalnizca 360 feedback/NLP kaynakli calisan raporu kalsin; KPI modern tablo ve rol bazli chart kaldirilsin veya KPI sayfasina tasinsin.
- 2. `DepartmentAnalysisView.vue` icinde yalnizca 360 feedback/NLP kaynakli departman raporu kalsin; KPI kartlari, performans bubble chart ve KPI AI modal'i KPI & ML tarafina tasinsin.
- 3. KPI & ML tarafinda `ManagerAnalyticsView.vue` altindaki `section=department` ve `section=watchlist` alanlari bu KPI bloklarinin kalici evi olsun.
- 4. Admin icin de KPI & ML menusu/rotasi gerekiyorsa ayrica `/admin/kpi-ml-analysis` route'u eklenmeli; aksi halde admin 360 menusu KPI bilesenlerinden arindirilmali.
- 5. Terminoloji duzeltmesi: 360 sayfalarinda "Calisan Analizi" yerine "360 Calisan Raporu", "Departman Analizi" yerine "360 Departman Raporu"; KPI tarafinda "KPI Calisan Analizi" ve "KPI Departman Analizi" kullanilmali.
- 6. Son dogrulama: Takim Analizi -> Detaylar KPI & ML watchlist'e gider; 360 menusu sadece feedback/NLP gosterir; KPI menusu sadece KPI/ML gosterir.

## 2026-05-14 KPI / 360 Feedback Ayrimi Uygulamasi

- `EmployeeAnalysisView.vue` 360 sayfasi saf hale getirildi: baslik `360 Calisan Raporu` oldu; KPI modern performans tablosu, rol bazli KPI chart ve KPI detay modal'i gorunur akistan kaldirildi.
- `EmployeeAnalysisView.vue` icindeki `loadPerformanceSummary()` cagrilari kaldirildi; 360 calisan raporu artik KPI performance summary endpoint'ini yuklemez. Sayfa 360 rapor, aylik deep/RAG ve feedback/NLP verileriyle calisir.
- `DepartmentAnalysisView.vue` 360 sayfasi saf hale getirildi: baslik `360 Departman Raporu` oldu; KPI kartlari, KPI performans bubble chart, KPI AI analiz paneli ve KPI performans modallari gorunur akistan kaldirildi.
- `DepartmentAnalysisView.vue` icindeki `loadPerformanceSummary()` cagrilari kaldirildi; 360 departman raporu artik KPI performance summary endpoint'ini yuklemez. Sayfa 360 departman raporu, NLP chart, monthly deep ve monthly RAG akisiyle calisir.
- `router/index.ts` icine admin KPI route'u eklendi: `/admin/kpi-ml-analysis` (`admin-kpi-ml-analysis`) ayni `ManagerAnalyticsView.vue` component'ini kullanir.
- 360 route meta basliklari netlestirildi: `360 Calisan Raporu`, `360 Departman Raporu`.
- `AppLayout.vue` menuleri ayrildi:
  - KPI & ML: `KPI Departman Analizi`, `Takim Analizi`, `KPI Calisan Analizi`.
  - 360 Derece Feedback: `360 Calisan Raporu`, `360 Departman Raporu`.
  - Admin icin de ayri `KPI & ML Analizi` menusu eklendi.
- `ManagerAnalyticsView.vue` icinde section metinleri `KPI Departman Analizi` ve `KPI Calisan Analizi` olarak netlestirildi.
- `ManagerAnalyticsView.vue` `openEmployeeAnalysis` fonksiyonu aktif route admin ise `admin-kpi-ml-analysis`, manager ise `manager-kpi-ml-analysis` rotasina gider. Takim Analizi -> Detaylar KPI watchlist deep link akisi korunur.
- Dogrulama: `npm.cmd run type-check` basarili. Frontend container yeniden baslatildi. Canli Vite modulunde `admin-kpi-ml-analysis`, `KPI Calisan Analizi`, `KPI Departman Analizi`, `360 Calisan Raporu`, `360 Departman Raporu` etiketleri dogrulandi.

## Kalan Not

- Eski KPI tablo/chart kodlarinin bir kismi 360 component dosyalarinda pasif durumda duruyor; gorunur UI ve API yukleme akisi temizlendi. Sonraki temizlik/refactor adiminda bu pasif kodlar tamamen silinebilir veya KPI component'lerine ayrilabilir.

## 2026-05-14 KPI Pasif Kod Temizligi ve KPI Tarafina Tasima

- Kullanici, 360 component dosyalarinda pasif kalan eski KPI tablo/chart kodlarinin tamamen temizlenmesini istedi ve bu kodlarin KPI departman/calisan analizine tasinip tasinmamasini sordu.
- Netlestirme: KPI kodlari silinmeden once gerekli islevler KPI & ML tarafinda kalici eve tasindi; 360 tarafindan yalnizca pasif/yanlis sahiplikte duran kopyalar temizlendi.
- `ManagerAnalyticsView.vue?section=department` icine backend `analyticsApi.getPerformanceSummary` verisinden beslenen KPI departman kartlari, rol bazli KPI/trend bar chart'i ve takim KPI ozeti eklendi.
- `ManagerAnalyticsView.vue?section=watchlist` icine ayni backend performans summary verisinden beslenen KPI calisan tablosu eklendi; calisan, takim/rol, KPI progress, trend, guc ve durum alanlari burada gosteriliyor.
- `loadOverview()` artik departman overview ile birlikte performans summary'yi de yukler; KPI & ML departman/watchlist alanlari gercek backend KPI verisiyle beslenir.
- `EmployeeAnalysisView.vue` icindeki pasif KPI tablo/chart script kodlari, `analyticsApi.getPerformanceSummary` importu, chart.js KPI importlari, tablo filtre/siralama/pagination state'leri ve export fonksiyonlari kaldirildi.
- `DepartmentAnalysisView.vue` icindeki pasif KPI bubble chart, KPI AI modal, performans summary state/computed bloklari, chart.js bubble importlari ve gizli `AI ile Analiz` butonu kaldirildi.
- 360 dosyalarinda KPI API cagrisi ve KPI chart/table kodu kalmadigi `rg` ile kontrol edildi; KPI ile ilgili kalan kodlar `ManagerAnalyticsView.vue` icinde.
- Dogrulama: `npm.cmd run type-check` basarili. Frontend container yeniden baslatildi.

## Sonraki Adim

- KPI & ML tarafindaki yeni departman/watchlist bloklari buyurse `ManagerAnalyticsView.vue` icinden `KpiDepartmentAnalysis` ve `KpiEmployeeWatchlist` gibi ayri component'lere bolunebilir.
- Tarayicida son smoke test olarak 360 menulerinde KPI bloklarinin gorunmedigi, KPI menulerinde departman/calisan KPI bloklarinin gorundugu kontrol edilmeli.
## PR #25 Satis Departmani Notlari
## Test Kullanıcıları (seed_data.py)

| Email | Şifre | Rol | Yönlendirme |
|---|---|---|---|
| admin@propel.com | admin123 | Admin | `/admin` |
| manager.yazilim@propel.com | manager123 | Yazılım Yöneticisi | `/manager` → Yazılım nav |
| manager.satis@propel.com | manager123 | Satış Yöneticisi | `/manager` → Satış nav |
| developer1@propel.com | dev123 | Çalışan (Yazılım) | `/employee` |
| satis.employee@propel.com | satis123 | Çalışan (Satış, SA-011) | `/employee/sales` |
| sl-001@propel.com | satis123 | Çalışan (Satış, SA-001) | `/employee/sales` |

**Satış Dataset Çalışanları** (SA-001..SA-030, hepsi şifre: `satis123`):

| Kod | İsim | Bölge | Rol |
|---|---|---|---|
| SA-001 | Ali Yılmaz | Marmara | Senior |
| SA-002 | Ayşe Demir | Ege | Junior |
| SA-003 | Mehmet Kaya | Karadeniz | Manager |
| SA-004 | Fatma Çelik | Marmara | Mid-Level |
| SA-005 | Mustafa Koç | Karadeniz | Manager |
| SA-006 | Zeynep Şahin | Doğu Anadolu | Manager |
| SA-007 | Ahmet Öztürk | İç Anadolu | Senior |
| SA-008 | Elif Aydın | Marmara | Mid-Level |
| SA-009 | Caner Yıldız | Akdeniz | Mid-Level |
| SA-010 | Burcu Arslan | Akdeniz | Junior |
| SA-011 | Zeynep Kaya (satis.employee) | Akdeniz | Senior |
| SA-012 | Kerem Arslan | Güneydoğu Anadolu | Team Lead |
| SA-013 | Selin Yılmaz | İç Anadolu | Manager |
| SA-014 | Tuncay Doğan | Doğu Anadolu | Senior |
| SA-015 | Nihan Korkmaz | Doğu Anadolu | Junior |
| SA-016 | Baran Özdemir | Güneydoğu Anadolu | Junior |
| SA-017 | Derya Kaplan | Güneydoğu Anadolu | Team Lead |
| SA-018 | Serhat Bulut | Doğu Anadolu | Senior |
| SA-019 | Merve Polat | Akdeniz | Senior |
| SA-020 | Ozan Çetin | Doğu Anadolu | Junior |
| SA-021 | Gamze Kurt | Ege | Mid-Level |
| SA-022 | Hakan Acar | İç Anadolu | Manager |
| SA-023 | Rana Şimşek | Akdeniz | Junior |
| SA-024 | Emre Yıldız | Marmara | Senior |
| SA-025 | Pınar Gül | Marmara | Manager |
| SA-026 | Tolga Kara | Akdeniz | Team Lead |
| SA-027 | Aslı Erdoğan | Doğu Anadolu | Mid-Level |
| SA-028 | Volkan Şahin | Ege | Manager |
| SA-029 | İrem Özkan | Doğu Anadolu | Team Lead |
| SA-030 | Burak Çalışkan | İç Anadolu | Mid-Level |

---

## Geliştirme Günlüğü

### 2026-05-10 KPI / ML Analizi - Takım Analizi UI

- `ManagerAnalyticsView.vue` içinde Takım Analizi ekranı yönetici odaklı mini dashboard haline getirildi.
- Seçili takım için gradient header, KPI kartları, ana sorun kartı, 12 haftalık risk trend grafiği, AI aksiyon paneli, takım üyeleri kart grid'i eklendi.
- Sahte takvim etiketleri → `D1..Dn` dönem etiketleri; sparkline polyline gerçek serilerden.

### 2026-05-10 Backend Performans Ölçümü ve Refactor

- `_team_analytics` batch prediction refactor: `team_analytics_ms` 43562ms → 736ms.

### 2026-05-10 Toplantı ve Bildirim Backend Akışı

- `Meeting`, `MeetingAttendee`, `Notification` modelleri + `POST /meetings/team-risk`, `GET /notifications/me` eklendi.

### 2026-05-10 Takım Analizi - Excel Export (5 Sheet)

- `TeamReportExportService` + 5 sheet Excel export endpoint eklendi.

### 2026-05-10 Rapor Gönder Akışı

- `POST /notifications/team-report` endpoint'i + frontend modal eklendi.

### 2026-05-14 Uygulama Çalıştırma ve Seed İşlemi

- `.env` dosyası oluşturuldu, Docker başlatıldı, DB seed edildi (40 çalışan, 5100 KPI).

### 2026-05-14 Satış Departmanı Kullanıcıları

- `manager.satis@propel.com`, `satis.employee@propel.com` eklendi.

### 2026-05-14 Takım → Çalışan Analizi Yönlendirmesi

- `ManagerAnalyticsView.vue` → `manager-kpi-ml-analysis` deep-link yönlendirmesi.

### 2026-05-14 Departman Analizi KPI ML Üst Bölüm

- 6 KPI kartı + bubble chart + AI Analiz Özeti paneli eklendi.

### 2026-05-14 Çalışan Analizi Modern Performans Tablosu

- Full-width KPI ML tablosu, filtre bar, pagination, Excel export eklendi.

### 2026-05-14 Departman Analizi AI LLM Modal

- AI Analiz butonu + LLM modal eklendi.

### 2026-05-14 KPI ML Analizi Backend Bağlantısı

- `GET /analytics/performance/summary` endpoint'i + servis eklendi. DepartmentAnalysis + EmployeeAnalysis gerçek veriye bağlandı.

### 2026-05-14 Satış Departmanı Tam ML Pipeline ★ BÜYÜK

**Eklenen Dosyalar**:
- `analytics/kpi_registry.py` → `SALES_KPI_REGISTRY` (25 KPI) eklendi
- `analytics/features/sales.py` → `SalesFeatureBuilder` (114 feature, column normalization, derived ratios, time features, team-relative GKP, motivation trend)
- `analytics/training/sales.py` → `SalesStackingTrainer` (LightGBM + XGBoost + RandomForest → LogisticRegression meta-learner via StackingClassifier)
- `analytics/artifacts/sales.py` → `SalesArtifactStore`
- `analytics/explain/sales.py` → `SalesExplanationBuilder`
- `analytics/prediction/sales.py` → `SalesPredictionService`
- `analytics/departments/sales.py` → `SalesAnalyticsAdapter` (tam implementasyon, canlı KPI veritabanı görünümü)
- `analytics/importers/sales.py` → `SalesKPIImportService`
- `services/sales_ml_service.py` → `SalesMLService` (list, train, predict, bulk_predict, team_analytics)
- `services/sales_narrative_service.py` → `SalesNarrativeService`

**Güncellenen Dosyalar**:
- `schemas/analytics.py` → Sales şemaları eklendi
- `api/routers/analytics.py` → 6 sales endpoint eklendi
- `requirements.txt` → lightgbm==4.3.0, xgboost==2.0.3
- `Dockerfile` → `libgomp1` sistem bağımlılığı

**Test Sonuçları** (gerçek dataset: 30 çalışan × 52 hafta):
- Performance_Drop_Target: acc=1.0, macro_f1=1.0, train=1320, test=240
- Resignation_Target: acc=1.0, macro_f1=1.0
- High_Risk_Target: acc=0.996, macro_f1=0.996
- Top features: `kpi_1_shgo`, `average_sale_value`, `revenue_vs_team`

**Dataset Kolon Sorunları Çözüldü**:
- `Employee_ID` (büyük harf), `Week` (büyük harf), `Region` (team yerine), `Role_Level` (role yerine) — hepsi normalize edildi
- `year` kolonu yoktu → 2024 varsayılan
- `employee_id` `EMP_001` formatındaydı → numeric parse

---

### 2026-05-17 Satış Departmanı Frontend Dashboard ★ BÜYÜK

**Eklenen Frontend Dosyaları**:
- `propel-frontend/src/views/sales/SalesAnalyticsView.vue` → Satış yöneticisi ML analiz ekranı (dataset seçimi, 4 target, model eğit/tahmin/toplu tara, takım tablosu, kişi kartları, narratif)
- `propel-frontend/src/views/sales/SalesEmployeeDashboard.vue` → Satış çalışanı kişisel dashboard (emerald tema, 4 KPI kartı, 9 satış metriği, AI koç, nabız anketi, rozet)

**Güncellenen Frontend Dosyaları**:
- `services/api/analytics.api.ts` → Sales tipleri + 6 yeni API fonksiyonu (`getSalesDatasets`, `getSalesDatasetEmployees`, `getSalesModelState`, `trainSalesModel`, `getLatestSalesPrediction`, `getBulkSalesPredictions`)
- `router/index.ts` → `/manager/sales-analytics`, `/admin/sales-analytics`, `/employee/sales` rotaları; login sonrası satış çalışanı otomatik `/employee/sales`'e yönlendirme
- `layouts/AppLayout.vue` → `isSalesDept` computed (dept_id=2 veya 18); departmana göre dinamik sidebar nav (yazılım yöneticisi ≠ satış yöneticisi nav items)
- `stores/auth.ts` → `satis.employee@propel.com` (Zeynep Kaya, dept_id=18) mock kullanıcısı eklendi
- `views/auth/LoginView.vue` → Login sonrası `department_id` kontrolü ile satış çalışanı `/employee/sales`'e yönlendirildi

**Güncellenen Backend Dosyaları**:
- `schemas/user.py` → `UserResponse`'a `department_id: int | None = None` eklendi
- `api/routers/auth.py` → `/me` endpoint'i `Employee` tablosuna join yaparak `department_id` dönüyor
- `seed_data.py` → `SALES_EMPLOYEE_SPECS` SA-001..SA-030 (30 kişi) olarak güncellendi

**Veritabanı Güncellemeleri**:
- `external_employee_code` SA-001..SA-010 olarak güncellendi (SL-xxx → SA-xxx)
- SA-011 (satis.employee) eklendi
- SA-012..SA-030 arası 19 yeni kullanıcı + Employee kaydı oluşturuldu (email: `sa-12@propel.com`..`sa-30@propel.com`, şifre: `satis123`)

**Navigasyon Mantığı** (`department_id` bazlı):
- `dept_id=1` (Yazılım Yöneticisi) → KPI & ML Analizi grubu → `/manager/kpi-ml-analysis`
- `dept_id=2` (Satış Yöneticisi) → Satış KPI & ML grubu → `/manager/sales-analytics`
- Admin → her iki departman + Satış ML Analizi linki
- Satış çalışanı → Satış Performansım → `/employee/sales`

**ML Target Durumu** (upload_id=1, 30 çalışan × 52 hafta):
- `Performance_Drop_Target` ✅ eğitildi — 8 riskli, 22 güvenli
- `Burnout_Target` ❌ eğitilemez — dataset'te tek sınıf (tüm satırlar = 0)
- `Resignation_Target` ✅ eğitildi — 0 riskli, 30 güvenli
- `High_Risk_Target` ✅ eğitildi — 8 riskli, 22 güvenli

**Önemli Keşif**: `/api/v1/auth/me` endpoint'i `department_id` döndürmüyordu → frontend sidebar nav ve login yönlendirmesi çalışmıyordu. Backend fix ile çözüldü.

---

## Sonraki Adımlar / Roadmap

- [x] Satış departmanı frontend dashboard'u (Vue 3) — employee/manager/admin görünümleri
- [ ] `Burnout_Target` için dataset'e pozitif örnek ekleme veya UI'dan gizleme
- [ ] Satış çalışanı dashboard KPI kartlarını backend'e bağla (`/kpis/records?employee_id=X`)
- [ ] `app/tests/` dizinine temel pytest test suite'i (hedef: %80 coverage)
- [ ] Playwright kurulumu ile frontend smoke testleri
- [ ] LLM narrative endpoint'ini async/background job olarak ayır
- [ ] Departman Analizi AI Modal → PDF İndir ve Email Gönder backend bağlantısı
- [ ] Yeni departman desteği (İK, Pazarlama): registry + kpi_registry + seed genişletme
- [ ] WebSocket ile gerçek zamanlı bildirimler
- [ ] GDPR/KVKK uyumluluk özellikleri

## 2026-05-18 PR #25 Merge Conflict Cozumu

- Kullanici PR/branch #25 merge ederken conflict oldugunu soyledi ve adim adim cozum istedi.
- Aktif branch `ml-team-analytics`; GitHub PR #25 `git fetch origin pull/25/head:pr-25` ile yerel `pr-25` branch'i olarak cekildi.
- Merge oncesi analizde conflict kaynaklari `AGENTS.MD`, `AppLayout.vue` ve `router/index.ts` olarak gorundu. Gercek merge sonrasi `router/index.ts` otomatik birlesti; manuel conflict `AGENTS.MD` ve `AppLayout.vue` dosyalarinda kaldi.
- `AppLayout.vue` cozumunde PR #25'in satis/yazilim departman bazli navigasyon mantigi korundu; mevcut calismadaki admin `KPI & ML Analizi` menusu, `KPI Departman Analizi`, `KPI Calisan Analizi`, `360 Calisan Raporu`, `360 Departman Raporu` adlandirmalari geri uygulandi.
- `router/index.ts` kontrol edildi; admin KPI route'u, admin/manager satis analytics route'lari ve satis calisani `/employee/sales` route'u birlikte kaldi.
- `AGENTS.MD` conflict'i iki tarafin notlari korunarak cozuldu; yerel 360/KPI ayrimi notlari ile PR #25 satis departmani notlari ayni dosyada birlestirildi.
- Dogrulama: `npm.cmd run type-check` basarili. Backend sales dosyalari ve analytics router `python -m py_compile` ile basarili.

## Sonraki Adim

- Merge commit tamamlandiktan sonra gerekirse backend image yeniden build edilmeli; PR #25 `lightgbm`, `xgboost` ve `libgomp1` ekledigi icin eski container image yeterli olmayabilir.
- Smoke test: admin KPI menusu, admin satis analizi, satis manager nav, satis calisani `/employee/sales`, 360 menulerinin KPI gostermemesi.

## 2026-05-18 PR #26 Master Conflict Guncellemesi

- Kullanici GitHub PR #26 (`ml-team-analytics` -> `master`) ekraninda hala 3 conflict gorundugunu paylasti.
- Yerel kontrol: `ml-team-analytics` remote ile esitti, fakat PR #26 base branch'i olan `origin/master` branch'e henuz merge edilmemisti.
- `origin/master` `ml-team-analytics` icine merge edildi; merge lokal olarak conflict vermeden tamamlandi.
- Conflict marker kontrolu `AGENTS.MD`, `AppLayout.vue`, `router/index.ts` uzerinde temiz.
- Dogrulama: `npm.cmd run type-check` basarili; backend sales/analytics dosyalari `python -m py_compile` basarili.

## Sonraki Adim

- Yeni master merge commit'i ve bu not commit'i `origin/ml-team-analytics` branch'ine pushlaninca GitHub PR #26 conflict uyarisi guncellenmeli/kalkmali.

## 2026-05-18 PR #26 Test ve Smoke Dogrulamasi

- Kullanici "tum testleri ve kontrolleri" calistirmami istedi.
- Docker Desktop/servisler kontrol edildi; `propel_db`, `propel_backend`, `propel_frontend` ayakta. `http://localhost:8001/docs` ve `http://localhost:5173` 200 dondu.
- Backend image `docker compose build backend` ile basarili build edildi; `lightgbm==4.3.0` ve `xgboost==2.0.3` container icinde import edildi.
- `seed_data.py` calistirilirken `external_employee_code=SA-011` unique conflict yakalandi. Kok neden: `satis.employee@propel.com` icin SA-011 ozel kaydi varken `SALES_EMPLOYEE_SPECS` dongusu ayni kodu ikinci kez uretiyordu.
- `seed_data.py` icinde SA-011 genel satis kullanicisi/calisani dongulerinden atlandi; seed tekrar basarili: 63 user, 2 department, 62 employee, 45 KPI definition, 8100 KPI record, 1560 survey response, 10 feedback question.
- Canli login testleri basarili: admin, yazilim manager, satis manager, satis employee ve developer kullanicilari token aldi.
- Yeni canli sorun bulundu ve duzeltildi: seed sonrasinda department id'leri 26/27 oldugu icin frontend'in `dept_id === 2 || 18` satis tespiti kiriliyordu.
- `/auth/me` response'una `department_name` eklendi; frontend `auth.types`, mock auth store, `AppLayout.vue`, `router/index.ts`, `LoginView.vue` satis tespitini `department_name` + email fallback ile yapiyor.
- Dogrulama:
  - `python -m py_compile app/schemas/user.py app/api/routers/auth.py seed_data.py` basarili.
  - Container icinde ayni `py_compile` basarili.
  - `npm.cmd run type-check` basarili.
  - `npm.cmd run build-only` basarili.
  - `docker exec propel_backend python -m pytest` denendi fakat backend image icinde `pytest` kurulu degil (`No module named pytest`).
  - `GET /api/v1/analytics/departments` keys `software,sales`; `GET /api/v1/analytics/performance/summary` basarili.
  - `GET /api/v1/analytics/departments/sales/datasets` basarili, seed upload dataset'i olmadigi icin bos liste dondu.
  - 360 smoke: `feedbacks/reports/department`, `feedbacks/reports/employee/{id}` ve `feedbacks/current-question` basarili.
  - Statik kontrol: 360 sayfalarda KPI `getPerformanceSummary`/bubble kalintisi yok; KPI watchlist/department/team bolumleri `ManagerAnalyticsView.vue` tarafinda.

## Sonraki Adim

- PR #26 branch'i pushlandiktan sonra GitHub conflict/checks ekrani tekrar kontrol edilmeli.
- Backend test suite icin `pytest` dependency ve temel `app/tests/` smoke testleri eklenmeli; su an pytest runner image'da yok.
