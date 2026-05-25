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

## 2026-05-23 Yazilim Calisan KPI Metrik Kartlari

- Kullanici satis calisan dashboard'undaki `KPI Detayi / Satis Metrikleri` kartlarinin yazilim departmaninda nerede oldugunu sordu.
- Tespit: satis ekrani `/employee/sales` route'u ve `SalesEmployeeDashboard.vue` icinde; yazilim calisan karsiligi `/employee` ve `EmployeeDashboard.vue` idi, fakat yazilim KPI detay kartlari yoktu.
- Backend'e `GET /api/v1/analytics/departments/software/my-performance` endpoint'i eklendi.
- Endpoint giris yapan kullanicinin `Employee` kaydini bulur, en son basarili `department_key=software` KPI upload'unu secer, dataset satirlarini calisanla eslestirir ve son haftanin KPI kartlarini dondurur.
- KPI kartlari artik rastgele/secili metinlerden degil `SOFTWARE_KPI_REGISTRY` ve dataset kaynak kolonlarindan uretilir; `KPI-1`..`KPI-20` resmi yazilim KPI listesi desteklenir.
- Model feature olmayan ama dataset'te bulunan hedef aday KPI'lar (`KPI-18 GPS`, `KPI-19 ARS`, `KPI-20 PPE`) da raw dataset satirindan okunacak sekilde eklendi.
- Frontend `analyticsApi.getMySoftwarePerformance()` eklendi ve `EmployeeDashboard.vue` icinde `Yazilim Metrikleri` kart bolumu olusturuldu.
- Kartlar kod, ad, formatli deger, durum, renk tonu, bar yuzdesi, hedef ipucu ve kategori bilgilerini backend response'undan alir.
- Dogrulama: lokal `python -m py_compile app\\api\\routers\\analytics.py app\\schemas\\analytics.py app\\services\\software_ml_service.py`, `npm.cmd run type-check`, `npm.cmd run build-only` basarili.
- Docker container icinde py_compile/restart/API smoke test denenmek istendi fakat Docker erisimi icin izin verilmedigi icin calistirilamadi.

## Sonraki Adim

- Backend container yeniden baslatilmali: `docker restart propel_backend`.
- Ardindan yazilim calisaniyla `/employee` ekraninda `Yazilim Metrikleri` kartlari ve `/analytics/departments/software/my-performance` endpoint'i canli test edilmeli.

## 2026-05-23 Yazilim Dataset-Calisan Eslesmesi Duzeltmesi

- Kullanici v8 CSV dataset'indeki calisanlar ile uygulamadaki seed calisanlarin gercekten birebir eslesip eslesmedigini sordu.
- Tespit: v8 CSV 30 kisi x 52 hafta = 1560 satir iceriyor; employee_id seti `1,4,5,6,7,9,10,13,14,16,17,18,20,25,26,27,28,31,32,33,34,35,38,40,42,45,46,47,48,49`.
- Eski seed yazilim calisanlari `SE-001..SE-030` idi. Bu nedenle sayi 30 olsa da birebir kimlik uyumu yoktu; Canan `SE-001 -> employee_id=1` calisiyordu ama bazi seed calisanlarin CSV karsiligi yoktu.
- `seed_data.py` icindeki `EMPLOYEE_SPECS` v8 dataset ID listesine gore guncellendi. Artik yazilim seed kodlari CSV employee_id setiyle birebir ayni: `SE-001, SE-004, ..., SE-049`.
- Canli DB'deki mevcut 30 yazilim calisani da iki asamali unique-safe guncellemeyle ayni mapping'e tasindi; kullanici email'leri de kodlarla hizalandi (`developer1@propel.com` SE-001 olarak korundu, digerleri `se-004@propel.com` vb.).
- Dogrulama: DB `external_employee_code` seti ile CSV `employee_id` seti birebir karsilastirildi; `missing_in_db=[]`, `missing_in_csv=[]`.
- Canan Dagdelen testi: `/analytics/departments/software/my-performance` endpoint'i Canan icin `2025-W52`, `Backend`, `Mid Backend Engineer` ve v8 metriklerini dondurdu (`GTO %84`, `ZTO %72`, `GKE %125`, `KKKE %49`, `BY 0.37`).

## Sonraki Adim

- Frontendde `/employee` sayfasi yazilim calisaniyla kontrol edilmeli; artik gorulen kisi profili ve KPI metrikleri ayni dataset kimligine dayaniyor.

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

## 2026-05-22 Origin Master PR #28 Analizi

- Kullanici yeni commit geldigini, merge/pull sonrasi neler eklendigini analiz etmemi istedi.
- `git fetch --all --prune` sonrasi `origin/master` `ee4a364` -> `6a9ed1a` ilerledi; yeni merge PR #28, asil feature commit `392554c`.
- Commit basligi: `feat: sales employee dashboard backend baglantisi, dataset ve seed guncellemeleri`.
- Eklenenler:
  - `GET /analytics/departments/sales/my-performance` endpoint'i.
  - `SalesEmployeePerformanceResponse`, `SalesKPIMetric`, `SalesWeeklyTrendPoint` semalari.
  - `SalesEmployeeDashboard.vue` hardcoded verilerden `analyticsApi.getMyPerformance()` verisine geciyor.
  - `surveyApi.createSurvey()` eklendi; sales dashboard icindeki pulse formu gercek `/surveys/` POST'una baglaniyor.
  - `generate_sales_dataset.py` eklendi; 31 satis calisani x 52 hafta dataset uretiyor.
  - `seed_data.py` satis takim isimlerini Excel region isimleriyle eslestiriyor; satis manager `SA-031`/Hatice Yildirim olarak guncelleniyor.
- Riskler/regression notlari:
  - `AppLayout.vue` ve `router/index.ts` bizim onceki 360/KPI menu netlestirmemizi kismen geri aliyor: admin `KPI & ML Analizi` route/menu kaldirilmis gorunuyor, 360 menuleri tekrar `Calisan Analizi` / `Departman Analizi` gibi belirsiz adlara donuyor.
  - Satis tespiti yeniden hardcoded `dept_id=2/14/18` fallback'lerine yaslaniyor; `department_name` kullanimi var ama onceki normalize `satış -> satis` mantigi kadar temiz degil.
  - Frontend `SalesKPIMetric` tipi `bar_pct` bekliyor, fakat backend semasi ve servis cevabi `bar_pct` uretmiyor. Bu KPI progress bar'larinin 0% gorunmesine yol acabilir.
  - `EmployeePulseView.vue` icinde hesaplanan `dashboardRoute` kullanilmiyor; geri butonu kaldirildigi icin etkisiz/olmus kod.
  - `SalesEmployeeDashboard.vue` icinde employee verisi `employeeApi.getEmployees()` ile tum listeyi cekerek bulunuyor; kendi employee endpoint'i yoksa calisir ama gereksiz genis veri cekiyor.
- Merge-tree analizinde teknik conflict gorunmedi; fakat merge edilirse davranissal regression'lar elle korunarak cozulmeli.

## Sonraki Adim

- PR #28 merge edilecekse faydali sales dashboard/backend endpoint degisiklikleri alinmali, fakat admin KPI route/menu, 360 menu adlari ve normalize satis departmani tespiti korunmali.
- `bar_pct` ya backend response'una eklenmeli ya frontend tipi/hesabi backend semasiyla uyumlu hale getirilmeli.

## 2026-05-23 Satis Ensemble Sayfa Analizi

- Kullanici `/admin/sales-analytics` ekranindaki LightGBM + XGBoost + RandomForest -> LogisticRegression ensemble yapisinin gercekten backend'de kullanilip kullanilmadigini sordu.
- Frontend ekran metni `SalesAnalyticsView.vue` icinde; `Model Egit` butonu `analyticsApi.trainSalesModel()` ile `POST /analytics/departments/sales/models/train` endpoint'ine gidiyor.
- Backend router `analytics.py` bu istegi `SalesMLService.train_from_upload()` fonksiyonuna yonlendiriyor.
- `SalesMLService.train_from_upload()` `SalesStackingTrainer.train()` cagiriyor.
- Gercek ensemble `app/analytics/training/sales.py` icinde: `StackingClassifier` base estimators olarak LightGBM (`lgbm`), XGBoost (`xgb`) ve RandomForest (`rf`) kullaniyor; final estimator LogisticRegression. `cv=3`.
- Satis trainer sinif dagilimi yetersizse (`min_class_count < 6`) stacking yerine `random_forest_fallback` kullaniyor. Ekranda model adi `stacking_lgbm_xgb_rf_lr` ise gercek ensemble egitilmis demektir.
- Yazilim departmani su anda ayni yapida degil. `app/analytics/training/software.py` `SoftwareBaselineTrainer` ile tek model secerek calisiyor: `logistic_regression`, `random_forest` veya `hist_gradient_boosting`.
- Yazilim tarafinda da satis benzeri ensemble icin yeni `SoftwareStackingTrainer` veya mevcut trainer'a `stacking_lgbm_xgb_rf_lr` model secenegi eklenmeli; `SoftwareMLService.train_from_upload()`, schema/model option, frontend model secimi ve artifact metadata uyumlu hale getirilmeli.

## Sonraki Adim

- Yazilim departmanina satis ile paralel stacking ensemble uygulanacaksa once `app/analytics/training/software.py` icinde pipeline eklenmeli, sonra service/schema/frontend akisi guncellenmeli ve mevcut random_forest fallback korunmali.

## 2026-05-23 Yazilim Stacking Ensemble Uygulamasi

- Kullanici satis sayfasindaki LightGBM + XGBoost + RandomForest -> LogisticRegression ensemble yapisinin yazilim departmanina da uygulanmasini istedi.
- `app/analytics/training/software.py` guncellendi:
  - `stacking_lgbm_xgb_rf_lr` model secenegi eklendi.
  - Base learner'lar: LightGBM, XGBoost ve RandomForest.
  - Meta learner: LogisticRegression.
  - XGBoost string/multiclass label'larda sorun cikarmasin diye `LabelEncodedClassifier` adapter'i eklendi.
  - Sinif basina ornek sayisi 6'dan azsa ensemble yerine RandomForest ile egitilip metadata `random_forest_fallback` donuyor.
  - Stacking icin base learner feature importance ortalamasi `top_features` olarak uretiliyor.
- `SoftwareMLService.SUPPORTED_MODELS` icine `stacking_lgbm_xgb_rf_lr` eklendi.
- `SoftwareModelTrainRequest` varsayilan modeli `stacking_lgbm_xgb_rf_lr` oldu.
- Frontend `ManagerAnalyticsView.vue` yazilim ML panelinde model secimi eklendi: Stacking Ensemble, Random Forest, Hist Gradient Boosting, Logistic Regression.
- Frontend `analyticsApi.trainSoftwareModel()` varsayilan modeli artik `stacking_lgbm_xgb_rf_lr` gonderiyor.
- Dogrulama:
  - Lokal `py_compile` basarili.
  - Container icinde sentetik yazilim datasiyla `SoftwareBaselineTrainer.train(..., "stacking_lgbm_xgb_rf_lr")` gercek `StackingClassifier` uretip tahmin servisinde probability dondu.
  - Container icinde sinif dagilimi yetersiz sentetik data `random_forest_fallback` dondu.
  - `npm.cmd run type-check` ve `npm.cmd run build-only` basarili.
  - Container icinde `py_compile` basarili.
  - Ilk denemede image icinde `pytest` kurulu olmadigi icin test runner calismadi; `requirements-dev.txt` ile container icine `pytest==8.3.4` kuruldu.
  - Software analytics odakli testler basarili: `python -m pytest app/tests/test_software_artifact_prediction.py app/tests/test_software_analytics_endpoints.py app/tests/test_software_ml_rows.py -q` -> 6 passed.
  - Tum backend test suite basarili: `python -m pytest app/tests -q` -> 17 passed, 23 Pydantic deprecation warning.
  - Backend container `docker restart propel_backend` ile yeniden baslatildi; `/docs` 200 dondu.
- Gercek v8 dataset testi:
  - `uploads/4_kutup_dataset_final_realistic_v8_fixed.csv` dosyasi vardi fakat `data_uploads` tablosu seed/reset sonrasi bostu.
  - Admin upload API ile dosya tekrar kaydedildi: upload id `5`, 1560 satir, `department_key=software`.
  - `UploadService` icinde CSV fallback path'i icin eksik `import csv` eklendi.
  - `performance_band` stacking egitimi basarili: model `stacking_lgbm_xgb_rf_lr`, train/test `1200/360`, weighted F1 `0.806142`.
  - `attrition_risk_band` stacking egitimi basarili: model `stacking_lgbm_xgb_rf_lr`, train/test `1200/360`, weighted F1 `0.844117`.
  - Model state iki target icin `is_trained=True`, `is_current_dataset=True`, model `stacking_lgbm_xgb_rf_lr`.
  - Tekil tahmin smoke testi basarili: employee `1`, `performance_band=Stabil`, confidence `0.495503`, model `stacking_lgbm_xgb_rf_lr`, probability map dondu.
- Yazilim model durumu UI guncellemesi:
  - Kullanici satis ekranindaki target bazli hazir/model kartlarinin yazilim tarafinda olmadigini ve model durumu ekranina eklemenin mantikli olup olmadigini sordu.
  - `ManagerAnalyticsView.vue` model durumu bolumunde her software target icin renkli kart eklendi.
  - Kartlar artik target label, model adi, durum rozeti (`Hazir`, `Model var`, `Model yok`), son egitim, Weighted F1 ve Train/Test bilgisini gosteriyor.
  - `softwareModelStateCardClass` ve `softwareModelStateBadgeClass` helper'lari eklendi.
  - Dogrulama: `npm.cmd run type-check` ve `npm.cmd run build-only` basarili.

## Sonraki Adim

- UI'da `/admin/kpi-ml-analysis?section=model` veya manager KPI & ML ekraninda upload id `5` secilerek model state ve tahmin sonucunun gorundugu manuel olarak kontrol edilebilir.

## 2026-05-24 Yazilim Departman Performansi Sayfa Analizi

- Kullanici yazilim departmani `Departman Performansi` sayfasinda hardcoded alanlar ve iyilestirme firsatlarini incelememi istedi.
- Incelenen ana sayfa `/manager` route'undaki `ManagerDashboard.vue`; ust baslik `Departman Performansi` olsa da sayfa buyuk oranda 360 feedback raporlari icin gecis/ozet paneli gibi tasarlanmis.
- Sayfa veri kaynaklari:
  - `feedbackApi.getDepartment360SummaryReport()` -> `/feedbacks/reports/department`
  - `feedbackApi.getFeedbackCandidates()` -> secilebilir calisan sayisi
  - `kpiApi.getAllVisibleRecords()` -> eski KPI kayit ozeti
- Hardcoded/fallback alanlar tespit edildi: hero metinleri, hizli yol aciklamalari, ayrim mantigi kartlari, metric label eslesmeleri (`Departman Motivasyonu`, `Yuksek Flight Risk`), KPI unit suffix map'i ve veri yok fallback metinleri.
- Kritik bulgu: `Departman Performansi` olarak gorunen KPI ozeti yazilim ML/v8 datasetinden veya `/analytics/departments/software/predictions/bulk` sonucundan degil, genel `/kpis/records` kayitlarindan hesaplanıyor. Bu nedenle yazilim ML performansi, risk dagilimi, model confidence ve takim trendleriyle dogrudan bagli degil.
- `DepartmentAnalysisView.vue` tamamen 360/NLP odakli; burada da grafikte bos veri icin `Hafta 1..4`, `Dusuk/Orta/Yuksek`, `Veri yok` fallback'leri var. Backend `NLPService.build_department_nlp_charts` da haftalari 1..4 sabit uretip veri yoksa 0 degeri donduruyor.
- Encoding sorunu hala gorunuyor: bazi Vue dosyalarinda `DepartmanÄ±`, `HaftalÄ±k`, `GÃ¼ven` gibi mojibake metinler var.

## Sonraki Adim

- `/manager` sayfasi gercek yazilim departman performansi olacaksa 360 feedback hero/gecis paneli ayrilmali; KPI/ML odakli ozetler `analyticsApi.getSoftwareDatasets`, `getSoftwareModelStates`, `getBulkSoftwarePredictions` ve `team_analytics` verilerine baglanmali.
- 360 rapor gecisleri ayri ve daha kucuk bir bolum olarak kalabilir; fakat sayfa dili `Departman Performansi` ile `360 Feedback Raporlari` arasinda net ayrilmali.
- KPI ozetindeki eski `/kpis/records` tabanli kartlar ya kaldirilmali ya da "manuel KPI kayitlari" olarak etiketlenmeli; yazilim v8 dataset metrikleri icin ayri backend ozet endpoint'i dusunulebilir.

## 2026-05-24 Departman Performansi Dashboard Layout Adim 1

- Kullanici once gorunumu degistirip sonra hardcoded/fallback alanlari backend'e baglama planini onayladi.
- `ManagerDashboard.vue` 3 katmanli dashboard iskeletine tasindi:
  - Header: departman adi, donem filtresi, Export ve Refresh aksiyonlari.
  - Ust metrik kartlari: gorunen KPI, hedef uyumu, risk sinyali, ekip kapsami.
  - Orta katman: departman genel durum gauge'i ve performans-vs-hedef gauge'i.
  - Trend katmani: son donem KPI egilimi icin LineChart.
  - Alt katman: risk gostergeleri, takim metrikleri, hizli aksiyon listesi.
  - En altta acilip kapanabilir AI departman ozeti paneli.
- Bu adimda yeni backend kontrati eklenmedi; mevcut `feedbackApi.getDepartment360SummaryReport`, `getFeedbackCandidates` ve `kpiApi.getAllVisibleRecords` verileri yeni layout'a yerlestirildi.
- Dogrulama:
  - Kod degisikliginden once `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklikten sonra `npm.cmd run type-check` ve `npm.cmd run build-only` basarili.
  - `docker compose restart frontend` basarili.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- Dashboard metriklerini gercek yazilim ML/dataset backend kontratina baglamak icin yeni veya mevcut analytics endpointleri netlestirilmeli.
- Export ve donem filtresi su an gorsel aksiyon olarak duruyor; sonraki adimda backend parametreleri ve export davranisi baglanmali.
- 360/NLP kaynakli alanlar ile yazilim KPI/ML performans alanlari veri modelinde net ayrilmali.

## 2026-05-24 Departman Performansi KPI Kartlari Adim 2

- Kullanici KPI kartlarini profesyonellestirmemi istedi: icon+baslik, buyuk ana deger, `/100` kesir formati, trend oku/yuzde, durum etiketi ve target/vs ort alt bilgileri.
- `ManagerDashboard.vue` ust KPI kartlari yeniden tasarlandi.
- Kartlar artik 4 metrik gosteriyor:
  - Ortalama Performans
  - Hedef Uyumu
  - Risk Kontrolu
  - Veri Kapsami
- Durum renklendirmesi eklendi: `85+ Basarili` yesil, `70-85 Dikkat` sari, `<70 Risk` kirmizi.
- Trend gosterimi eklendi: pozitif `↑`, negatif `↓`, sabit `→`; trend yuzdesi mevcut KPI trend serisinden turetiliyor.
- Bu adimda backend kontrati eklenmedi; kart verileri mevcut `kpiRecords`, `teamMembers` ve `departmentReport` state'lerinden turetiliyor.
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `npm.cmd run type-check` ve `npm.cmd run build-only` basarili.
  - `docker compose restart frontend` basarili.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- KPI kartlarindaki `target`, `benchmark`, trend ve skor hesaplari backend'den gelen resmi departman performans kontratina baglanmali.
- Kart metrikleri yazilim v8 dataset/ML bulk prediction sonucu ile uyumlu hale getirilmeli; mevcut eski `/kpis/records` turetimi gecici kabul edilmeli.

## 2026-05-24 Departman Performansi Gauge Chart Adim 3

- Kullanici hedef karsilastirmasi icin gauge chart tasarimi istedi.
- React/Recharts ornegi Vue 3 yapisina uyarlandi; ek paket eklenmedi.
- `ManagerDashboard.vue` icinde `GaugeComparisonCard` component'i olusturuldu.
- Iki panelde eski conic full-circle gauge yerine yarim daire hedef karsilastirma gauge'i kullaniliyor:
  - `Ortalama Performans`
  - `Performans vs Hedef`
- Gauge ozellikleri:
  - Kirmizi/sari/yesil zonlar: `<60 Risk`, `60-80 Dikkat`, `80-100 Iyi`.
  - Dinamik ibre acisi: mevcut deger yuzdesine gore hesaplanir.
  - Mevcut deger, hedef deger, ilerleme yuzdesi, minimum ve maksimum gosterilir.
  - Durum rozeti yuzdeye gore `Hedefi Gecti`, `Dikkat`, `Risk`.
- Bu adimda backend kontrati eklenmedi; gauge degerleri mevcut frontend state'inden turetiliyor.
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `npm.cmd run type-check` ve `npm.cmd run build-only` basarili.
  - `docker compose restart frontend` basarili.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- Gauge `current`, `target`, `min`, `max`, `status` ve zone esikleri backend kontratindan gelmeli.
- Hedef karsilastirma yazilim ML/v8 datasetindeki resmi KPI hedefleriyle baglanmali.

## 2026-05-24 Departman Performansi KPI Componentlestirme

- Kullanici React/MUI grid ve React `KPICard` ornegini paylasti.
- Mevcut Vue/Tailwind dashboard yapisi korunarak React orneginin component mantigi uyarlandi.
- Yeni `propel-frontend/src/components/dashboard/KPICard.vue` component'i eklendi.
- `ManagerDashboard.vue` ust KPI kartlari artik inline markup yerine `KPICard` component'i ile render ediliyor.
- `KPICard` ozellikleri:
  - Icon + baslik + subtitle.
  - Buyuk ana deger ve `value / max` kesir formati.
  - Trend oku ve trend metni.
  - Status badge.
  - Target ve `vs Ort` alt bilgileri.
  - Success/warning/danger yuzey renklendirmesi.
- React/MUI veya lucide dependency eklenmedi; mevcut Vue + Heroicons + Tailwind ile devam edildi.
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `npm.cmd run type-check` ve `npm.cmd run build-only` basarili.
  - `docker compose restart frontend` basarili.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- Grid katmanlari icin benzer sekilde `GaugeComparisonCard`, `RiskIndicators`, `TeamMetrics`, `QuickActions` ve `AIInsightsPanel` component'lerine ayirma dusunulebilir.
- KPI card props'lari backend'den gelecek resmi departman dashboard response'una gore sade ve stabil bir tipe baglanmali.

## 2026-05-24 Departman Performansi Pipeline Tracking Adim 4

- Kullanici sales funnel/pipeline tracking tasarimini paylasti.
- React/lucide ornegi Vue/Tailwind yapisina uyarlandi; yeni dependency eklenmedi.
- Yeni `propel-frontend/src/components/dashboard/PipelineTracking.vue` component'i eklendi.
- `ManagerDashboard.vue` icine `Performans Pipeline Tracking` bolumu eklendi.
- Pipeline asamalari su an mevcut frontend state'inden turetiliyor:
  - Ekip Kapsami
  - KPI Kaydi
  - Performans Normal
  - Hedef Uyumlu
  - Risk Kontrolu
  - Aksiyon Hazir
- Her asamada deger, yuzde progress bar, renk, donusum orani ve legend gosteriliyor.
- Eski risk/takim/aksiyon satiri yeniden duzenlendi:
  - Pipeline solda genis kolon.
  - Risk gostergeleri ve hizli aksiyon sag kolonda.
  - Takim metrikleri ve akis ozeti altta.
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `npm.cmd run type-check` ve `npm.cmd run build-only` basarili.
  - `docker compose restart frontend` basarili.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- Pipeline stage listesi backend'den gelmeli; frontend yalnizca gelen stage adlarini, degerleri, yuzdeleri, donusum oranlarini ve renk/status bilgisini render etmeli.
- Yazilim departmani icin sales funnel yerine performans pipeline isimleri kalacaksa backend kontratinda bu alanlar netlestirilmeli; satis departmani icin ayrica gercek Lead/Deal funnel stage'leri kullanilabilir.

## 2026-05-24 Departman Performansi Funnel Analizi Adim 5

- Kullanici lead conversion funnel chart tasarimini paylasti.
- React/Recharts ornegi Vue/Tailwind yapisina uyarlandi; yeni chart dependency eklenmedi.
- Yeni `propel-frontend/src/components/dashboard/FunnelChart.vue` component'i eklendi.
- `ManagerDashboard.vue` icine `Lead Conversion Funnel` bolumu eklendi.
- Funnel component ozellikleri:
  - Stage bazli yatay barlar.
  - Deger, conversion yuzdesi, drop-off yuzdesi.
  - Asamalar arasi donusum satiri.
  - Detayli tablo: Stage, Value, Conv. Rate, Drop-off.
- Funnel verisi su an mevcut pipeline stage'lerinden turetiliyor ve gecici olarak lead/deal isimlerine map ediliyor:
  - Leads Created
  - Leads Contacted
  - Deal Qualified
  - Deal Converted
- Sag tarafa funnel ozeti eklendi: toplam donusum, en yuksek kayip asamasi ve son asama conversion yorumu.
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `npm.cmd run type-check` ve `npm.cmd run build-only` basarili.
  - `docker compose restart frontend` basarili.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- Funnel `rows` verisi backend'den gelmeli; yazilim departmani icin lead/deal terimleri yerine performans pipeline asamalari kullanilacaksa isimlendirme backend kontratinda netlestirilmeli.
- Satis departmani dashboard'unda ayni component gercek CRM/satis funnel verileriyle yeniden kullanilabilir.

## 2026-05-24 Departman Performansi Trend Line Chart Adim 6

- Kullanici 6 aylik multi-line trend chart tasarimini paylasti.
- React/Recharts ornegi mevcut Chart.js/vue-chartjs stack'ine uyarlandi; yeni dependency eklenmedi.
- Yeni `propel-frontend/src/components/dashboard/DepartmentTrendChart.vue` component'i eklendi.
- `ManagerDashboard.vue` icindeki eski tek serili `LineChart` trend alani kaldirildi.
- Yeni chart serileri:
  - Performans (mavi, kalin cizgi, alan dolgusu)
  - Kapasite (yesil)
  - Risk Skoru (kirmizi)
  - Hedef (85, sari kesikli cizgi)
- Chart ozellikleri:
  - 0-100 Y ekseni.
  - 6 aylik X ekseni.
  - Bottom legend.
  - Tooltip formatter ve `Ay: ...` label'i.
  - Responsive 400px chart alani.
- Bu adimda backend kontrati eklenmedi; trend verisi mevcut `kpiRecords`, `coverageScore` ve `riskScore` state'lerinden turetiliyor.
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `npm.cmd run type-check` ve `npm.cmd run build-only` basarili.
  - `docker compose restart frontend` basarili.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- Trend chart `performance`, `capacity`, `risk` ve hedef cizgisi backend'den gelen resmi 6 aylik seriyle beslenmeli.
- Frontend fallback ay etiketleri ve turetilmis kapasite/risk hesaplari backend kontrati geldikten sonra kaldirilmali.

## 2026-05-24 Departman Performansi Risk ve Quick Actions Adim 7

- Kullanici risk gostergeleri ve hizli aksiyonlar tasarimini paylasti.
- Yeni `propel-frontend/src/components/dashboard/RiskIndicators.vue` component'i eklendi.
  - Kritik Riskler, Uyarilar ve Olumlu Isaretler olarak 3 kategori gosterir.
  - Kategori ikonlari ve kirmizi/sari/yesil nokta sistemi var.
- Yeni `propel-frontend/src/components/dashboard/QuickActions.vue` component'i eklendi.
  - Checkbox'li aksiyon listesi.
  - Tamamlanan aksiyonlarda line-through ve soluk metin.
  - `HIGH` / `MEDIUM` priority badge'leri.
- `ManagerDashboard.vue` icindeki inline risk ve aksiyon kartlari bu component'lerle degistirildi.
- Risk gruplari ve aksiyonlar su an mevcut `departmentReport`, `riskItems`, `quickActions`, `targetAlignmentRate`, `kpiTrendPercent`, `riskScore` state'lerinden turetiliyor.
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `npm.cmd run type-check` ve `npm.cmd run build-only` basarili.
  - `docker compose restart frontend` basarili.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- Risk kategorileri ve aksiyon priority/status bilgileri backend'den resmi olarak gelmeli.
- Quick action checkbox state'i kalici olacaksa backend'e veya local storage'a baglanmali; su an component state'i sayfa yenilenince sifirlanir.

## 2026-05-24 Departman Performansi AI Departman Ozeti Adim 8

- Kullanici LLM destekli AI departman analizi backend endpoint'i ve frontend panel tasarimini paylasti.
- Projeye yeni OpenAI dependency eklenmedi; mevcut `AIService` Gemini/Ollama altyapisi ve `SoftwareNarrativeService` kullanildi.
- Backend:
  - `SoftwareDepartmentInsightsResponse` semasi eklendi.
  - `GET /api/v1/analytics/departments/software/insights` endpoint'i eklendi.
  - Endpoint opsiyonel `upload_id`, `period`, `target_column`, `use_llm` parametrelerini aliyor.
  - `SoftwareMLService.generate_department_insights` eklendi.
  - Upload verilmezse en son basarili software upload seciliyor.
  - Bulk prediction + department narrative uzerinden 6 bolumlu insight metni uretiliyor: ozet, guclu yonler, gelistirme alanlari, departman sagligi, oneriler, sonraki hafta beklentisi.
  - `use_llm=true` ile mevcut Gemini/Ollama narrative deneniyor; provider yoksa deterministik fallback donuyor.
- Frontend:
  - `SoftwareDepartmentInsightsResponse` tipi ve `analyticsApi.getSoftwareDepartmentInsights()` eklendi.
  - Yeni `AIInsightsPanel.vue` component'i eklendi.
  - Eski statik AI ozet paneli kaldirildi; `ManagerDashboard.vue` artik `AIInsightsPanel` kullanıyor.
  - Panel gradient tasarimli, loading skeleton, expand/collapse, yenile, PDF indir ve ekibe gonder aksiyonlari iceriyor.
  - Yenile butonu gercek endpoint'i tekrar cagiriyor; PDF/ekibe gonder su an gorsel aksiyon olarak duruyor.
- Dogrulama:
  - `py_compile` basarili.
  - `npm.cmd run type-check` basarili.
  - `npm.cmd run build-only` basarili.
  - Backend kodu degistigi icin `docker restart propel_backend` calistirildi.
  - Frontend `docker compose restart frontend` ile yeniden baslatildi.
  - `http://localhost:8001/docs` HTTP 200 dondu.
  - `http://localhost:5173/manager` HTTP 200 dondu.
  - Auth ile `/api/v1/analytics/departments/software/insights?use_llm=false&period=week` smoke testi basarili; upload `5`, source `deterministic`, fallback `true`, health_score `88.1` dondu.

## Sonraki Adim

- AI panelindeki PDF indir ve ekibe gonder butonlari gercek export/notification endpoint'lerine baglanmali.
- LLM acik modda Gemini/Ollama provider ayarlariyla manuel test yapilmali; provider yoksa fallback beklenen davranis.
- Insight response'u ileride dashboard'un tum hardcoded metriklerini besleyecek resmi `department_dashboard` kontratina dahil edilebilir.

## 2026-05-24 Departman Performansi Header ve Filtreler Adim 9

- Kullanici dashboard header tasarimini paylasti.
- Yeni `propel-frontend/src/components/dashboard/DashboardHeader.vue` component'i eklendi.
- `ManagerDashboard.vue` ust header section'i bu component ile degistirildi.
- Header ozellikleri:
  - Panel etiketi ve departman adi.
  - `Calisan | Takim | Saglik Skoru` ozet satiri.
  - 4 bilgi karti: Genel Saglik Skoru, Ort. Performans, Risk Duzeyi, Trend.
  - Donem filtresi: Bu Hafta, Bu Ay, Bu Ceyrek, Bu Yil.
  - Karsilastirma filtresi: Onceki Donem, Departman Ort., Hedef.
  - Refresh, PDF ve Email aksiyonlari.
- Header metrikleri mevcut frontend state'inden turetiliyor:
  - `departmentHealthScore`
  - `kpiAverageScore`
  - `dashboardRiskLevel`
  - `dashboardTrendLabel`
  - `teamMemberCount`, `teamMetricCards.length`
- PDF ve Email butonlari su an placeholder event olarak console bilgisi verir; backend baglantisi sonraki adima birakildi.
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `npm.cmd run type-check` ve `npm.cmd run build-only` basarili.
  - `docker compose restart frontend` basarili.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- Donem ve karsilastirma filtreleri backend query parametrelerine baglanmali.
- Header saglik skoru, risk duzeyi ve trend bilgileri resmi backend dashboard kontratindan gelmeli.
- PDF ve Email aksiyonlari export/notification endpoint'lerine baglanmali.

## 2026-05-24 Departman Performansi Hibrit Dashboard Backend Adim 1

- Kullanici Departman Performansi sayfasinin KPI/ML, 360 Derece Feedback ve Haftalik Nabiz Anketlerini tek hibrit dashboard olarak gostermesini istedi.
- Ilk fazda cache tablosu eklenmedi; veri modeli taslasmadan once canli aggregator endpoint tercih edildi.
- Backend `SoftwareDepartmentDashboardResponse` ve alt Pydantic semalari eklendi:
  - `department`, `coverage`, `scores`, `sources`, `hybrid_insights`, `team_breakdown`, `actions`, `ai_summary`.
- Yeni endpoint eklendi: `GET /api/v1/analytics/departments/software/dashboard`.
- Endpoint parametreleri: `upload_id`, `period=week|month|quarter|year`, `target_column`, `use_llm`.
- `SoftwareMLService.generate_department_dashboard` eklendi.
- Aggregator su kaynaklari birlestiriyor:
  - KPI/ML: en son software upload + bulk prediction + team analytics.
  - Haftalik Nabiz: `survey_responses` icindeki `weekly_pulse` kayitlari.
  - 360 Feedback: `feedback_nlp_analyses` icindeki haftalik NLP sinyalleri.
- Hibrit skorlar hesaplandi:
  - `department_health = KPI/ML %50 + Nabiz %25 + 360 %25`
  - `execution_score`, `people_health_score`, `risk_score`, `confidence_score`.
- Coverage metrikleri eklendi: KPI, pulse ve 360 icin kisi/yanit sayisi, yuzde ve son guncelleme bilgileri.
- Hibrit icgoruler ve aksiyon listeleri deterministik ilk kurallarla uretiliyor.
- Frontend API tarafina `SoftwareDepartmentDashboardResponse` tipleri ve `analyticsApi.getSoftwareDepartmentDashboard()` eklendi.
- Canli smoke test basarili:
  - `/api/v1/analytics/departments/software/dashboard?period=week&use_llm=false`
  - upload `5`, status `success`, confidence `72.6`, KPI coverage `96.8`, pulse coverage `96.8`, 360 coverage `0.0`.
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `py_compile` ve `npm.cmd run type-check` basarili.
  - Backend container `docker restart propel_backend` ile yeniden baslatildi.

## Sonraki Adim

- `ManagerDashboard.vue` parca parca endpointlerden veri birlestirmek yerine yeni `getSoftwareDepartmentDashboard()` response'una baglanmali.
- 360 coverage su an canli haftalik NLP kaydi yoksa `0` geliyor; veri yoklugu UI'da source badge/confidence ile net gosterilmeli.
- Cache tablosu (`department_dashboards`) ve AI LLM sentezi, response kontrati frontendde oturduktan sonra ikinci fazda eklenmeli.

## 2026-05-24 Departman Performansi Hibrit Dashboard Frontend Adim 2

- Kullanici frontend sayfanin yeni hibrit dashboard endpoint'ine baglanmasini istedi.
- `ManagerDashboard.vue` yeniden yapilandirildi ve eski parca parca loader'lar kaldirildi:
  - `feedbackApi.getDepartment360SummaryReport`
  - `feedbackApi.getFeedbackCandidates`
  - `kpiApi.getAllVisibleRecords`
- Sayfa artik tek kaynak kullanir: `analyticsApi.getSoftwareDepartmentDashboard()`.
- Baslik guncellendi:
  - `Departman Performansi`
  - Alt baslik: `KPI/ML + 360 Feedback + Haftalik Nabiz`
- Header icinde departman, calisan sayisi, takim sayisi, rapor donemi ve son guncelleme gosteriliyor.
- Veri kapsama bolumu eklendi:
  - KPI/ML coverage
  - Haftalik Nabiz coverage
  - 360 Feedback coverage
  - confidence score
- KPI kartlari hibrit skorlara baglandi:
  - Departman Sagligi
  - Performans Ciktilari
  - Insan Sagligi
  - Risk Skoru
- Kaynak bazli ozet bolumu eklendi:
  - Performans Ciktilari (KPI/ML)
  - Insan Sagligi Sinyalleri (Nabiz)
  - Davranis ve Iliskiler (360)
- Hibrit icgoruler bolumu backend `hybrid_insights` listesinden render ediliyor.
- Takim karsilastirma tablosu backend `team_breakdown` verisinden render ediliyor.
- AI ozet paneli backend `ai_summary` verisini kullaniyor; eski ayri insights endpoint paneli kaldirildi.
- Risk gostergeleri ve hizli aksiyonlar backend `insights/actions` response'undan turetiliyor.
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `npm.cmd run type-check` basarili.
  - `npm.cmd run build-only` basarili.
  - Frontend container `docker compose restart frontend` ile yeniden baslatildi.
  - `http://localhost:5173/manager` HTTP 200 dondu.
  - Backend dashboard smoke testi `success 43.1 72.6` dondu.

## Sonraki Adim

- UI gorsel QA icin browser uzerinde mobil/desktop kontrol yapilmali.
- 360 verisi olmayan durumda source card'da daha acik `Veri yok` empty state'i gosterilebilir.
- Grafik/pipeline/funnel bilesenleri yeni hibrit response'taki trend alanlariyla tekrar entegre edilebilir.

## 2026-05-24 Departman Performansi Grafiklerin Geri Eklenmesi

- Kullanici hibrit dashboard'a gecilirken eski sayfadaki grafik, pipeline ve funnel yapilarinin tamamen kalktigini belirtti.
- `ManagerDashboard.vue` icine eski dashboard katmanlari yeni hibrit endpoint verisiyle yeniden eklendi:
  - `DepartmentTrendChart`
  - `PipelineTracking`
  - `FunnelChart`
  - Akis ozeti
  - Funnel ozeti
- Grafikler artik eski parca parca frontend state'inden degil yeni `SoftwareDepartmentDashboardResponse` uzerinden uretiliyor.
- Trend chart verisi `team_breakdown` skorlarindan uretiliyor:
  - KPI performansi
  - Nabiz/pulse kapasite-insan sinyali
  - Risk skoru
- Pipeline verisi coverage ve hibrit aksiyon akisiyle olusturuluyor:
  - Departman kapsami
  - KPI/ML verisi
  - Nabiz verisi
  - 360 NLP verisi
  - Saglikli takim
  - Aksiyon hazir
- Funnel analizi veri kapsama darbogazlarini gosteriyor; ozellikle 360 coverage dusukse drop-off olarak gorunur.
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `npm.cmd run type-check` ve `npm.cmd run build-only` basarili.
  - Frontend container `docker compose restart frontend` ile yeniden baslatildi.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- Browser ekraninda eski ve yeni layout birlikte incelenmeli; gerekirse grafiklerin sirasi ve alan genislikleri kullanici beklentisine gore yeniden duzenlenmeli.
- Trend chart icin daha iyi backend trend kontrati eklenebilir; su an takim kirilimi uzerinden hibrit trend gorunumu uretiliyor.

## 2026-05-25 Departman Performansi Genel Durum Paneli

- Kullanici hibrit dashboard'da eski `Departman genel durumu` bolumunun de yer almasini istedi.
- `ManagerDashboard.vue` icine KPI kartlarindan sonra yeni `Departman Genel Durumu` section'i eklendi.
- Sol panel:
  - Hibrit saglik ozeti
  - Genel departman saglik skoru
  - `ai_summary.summary`
  - Skor agirliklari: KPI/ML, Nabiz, 360
  - Veri guveni
- Sag panel:
  - Kaynak durumlari ayri ayri gosteriliyor:
    - KPI/ML Performans
    - Haftalik Nabiz
    - 360 Feedback
    - Birlesik Risk
  - Her kaynak icin skor/deger, detay, aciklama ve progress bar var.
- 360 feedback verisi yoksa panel `Veri yok` empty state'i gosteriyor; skor gibi davranmiyor.
- Yeni helper fonksiyonlar eklendi:
  - `scoreToneClass`
  - `barToneClass`
  - `riskToneClass`
  - `riskBarClass`
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `npm.cmd run type-check` ve `npm.cmd run build-only` basarili.
  - Frontend container `docker compose restart frontend` ile yeniden baslatildi.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- Bu genel durum paneli icin browser gorsel kontrol yapilip, eski gauge gorunumune daha yakin bir tasarim istenirse radial/gauge layout'a cevrilebilir.

## 2026-05-25 Departman Genel Durumu Gauge Duzeltmesi

- Kullanici eski sayfadaki renkli yarim ay gauge gorunumunun yeni genel durum panelinde olmadigini belirtti.
- `ManagerDashboard.vue` icine inline `HybridGauge` component'i eklendi.
- Gauge yari daire olarak CSS `conic-gradient` ile ciziliyor:
  - Kirmizi risk bolgesi
  - Sari dikkat bolgesi
  - Yesil iyi bolgesi
  - Igne/needle gosterimi
  - Merkez nokta
  - Alt segment etiketi
- Ana `Departman Genel Durumu` bolumunde genel saglik skoru artik yuvarlak skor yerine yarim ay gauge olarak gosteriliyor.
- Sag taraftaki kaynak durumlari icin de kucuk gauge eklendi:
  - KPI/ML
  - Nabiz
  - 360
  - Risk
- Risk gauge'i ters mantikla label uretiyor; yuksek risk daha kotu okunuyor.
- Dogrulama:
  - `npm.cmd run type-check` basarili.
  - `npm.cmd run build-only` basarili.
  - Frontend container `docker compose restart frontend` ile yeniden baslatildi.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- Browser uzerinde gauge igne acisi ve mobil genislik kontrol edilmeli; gerekirse gauge boyutu ya da kart dizilimi viewport'a gore ayarlanabilir.

## 2026-05-25 Departman Performansi Hardcoded/Fallback Skor Analizi

- Kullanici Departman Performansi sayfasinda hardcoded veri kalip kalmadigini ve `veri guveni`, `insan sagligi` gibi basliklarin nereden geldigini sordu.
- Inceleme sonucu frontenddeki gorunen skorlarin hardcoded olmadigi, backend `GET /analytics/departments/software/dashboard` endpoint'inden geldigi dogrulandi.
- Ancak backendde veri olmayan kaynaklar icin `50.0` notr fallback'in skor hesaplarina karistigi tespit edildi.
- Ozellikle 360 feedback verisi yokken:
  - `feedback_score=50.0`
  - `feedback_risk=50.0`
  degerleri departman sagligi, insan sagligi ve risk hesabina giriyordu.
- Bu davranis duzeltildi:
  - Pulse/360 verisi yoksa kaynak skoru hesaplamaya katilmiyor.
  - 360 verisi yoksa `feedback360` agirligi `0.0` oluyor.
  - Aktif kaynak agirliklari normalize ediliyor.
  - 360 verisi yokken UI hala `Veri yok` gosteriyor.
- Ornek canli endpoint sonucu guncellendi:
  - `department_health: 40.8`
  - `execution_score: 28.0`
  - `people_health_score: 66.4`
  - `risk_score: 60.0`
  - `confidence_score: 72.6`
  - `weights: KPI/ML 66.7, Nabiz 33.3, 360 0.0`
- Frontendde agirlik gosterimindeki `|| 50` / `|| 25` fallback'leri `?? 0` olarak duzeltildi; artik `0` gercekten `0` olarak gorunuyor.
- Kalan hardcoded kalemler veri degil, UI/urun kurali:
  - Kaynak basliklari ve aciklama metinleri.
  - Gauge renk esikleri.
  - Baslangic/empty-state metinleri.
  - Base agirlik tasarimi: KPI/ML 50, Nabiz 25, 360 25.
- Dogrulama:
  - `py_compile` basarili.
  - `npm.cmd run type-check` basarili.
  - `npm.cmd run build-only` basarili.
  - Backend `docker restart propel_backend` ile yeniden baslatildi.
  - Frontend `docker compose restart frontend` ile yeniden baslatildi.
  - Dashboard endpoint smoke testi basarili.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- Base agirliklari backendde sabit kural olarak tutmak yerine konfigurable hale getirilebilir.
- `AI summary` metni deterministik template yerine LLM/kuralli narrative response'u ile ayrica kaynak aciklamalari icerecek sekilde genisletilebilir.

## 2026-05-25 Departman Performansi Veri Hunisi Netlestirmesi

- Kullanici `Hibrit Veri Funnel` / `Darbogaz ve kayip analizi` bolumunun ne anlattiginin belirsiz oldugunu belirtti.
- Tespit: Bolum aslinda performans veya satis donusum hunisi degil, hibrit dashboard icin veri kapsama/hazirlik hunisiydi; fakat baslik ve icerik bunu acik anlatmiyordu.
- `FunnelChart.vue` icine opsiyonel `badgeText` prop'u eklendi; boylece sabit `Lead Conversion` etiketi yerine sayfa baglamina uygun etiket kullanilabiliyor.
- `ManagerDashboard.vue` icindeki funnel bolumu yeniden adlandirildi:
  - Baslik: `Veri Kapsama Hunisi`
  - Eyebrow: `Hibrit Analiz Hazirligi`
  - Badge: `Data Coverage`
- Sag ozet karti `Hibrit profil nerede eksiliyor?` olarak degistirildi ve bolumun performans dususunu degil, veri kapsamasini gosterdigini anlatan kisa aciklama eklendi.
- Huni adimlari sade ve dogrudan veri tamamlanma akisi olacak sekilde duzenlendi:
  - Toplam Calisan
  - KPI/ML Verisi Olan
  - Nabiz Yaniti Olan
  - 360 NLP Analizi Olan
  - Tam Hibrit Profili Olan
- Kafa karistiran `Dusuk Riskli Takim` ve `Aksiyon Hazir` adimlari huniden kaldirildi; bunlar performans/aksiyon sonucu oldugu icin veri kapsama hunisinde yanlis baglam olusturuyordu.
- Ozet cumleleri de `tam hibrit profil`, `en buyuk veri eksigi` ve `360 NLP verisi yoksa neden tam profil olusmadigi` uzerinden yeniden yazildi.
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `npm.cmd run type-check` ve `npm.cmd run build-only` basarili.
  - Frontend container `docker compose restart frontend` ile yeniden baslatildi.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- Bu huniye tooltip veya mini yardim metni eklenebilir: `Tam hibrit profil = KPI/ML + Nabiz + 360 NLP sinyali ayni calisan/takim icin mevcut`.

## 2026-05-25 Veri Hunisi Baslik ve Sonuc Aciklamalari Netlestirmesi

- Kullanici `Veri Kapsama Hunisi` ve `Hibrit profil nerede eksiliyor?` basliklarinin hala ne anlattiginin net olmadigini belirtti.
- Bolumun amaci daha acik hale getirildi: performans sonucu degil, hibrit skor icin veri kaynaklarinin calisan bazinda tamamlanma durumunu gosteriyor.
- `FunnelChart.vue` icine `description` prop'u ve satir bazli `description` alani eklendi.
- Sol kart yeni metinlerle guncellendi:
  - Baslik: `Hibrit analiz icin veri tamamligi`
  - Eyebrow: `KPI + Nabiz + 360 kapsami`
  - Badge: `Eksik veri kontrolu`
  - Aciklama: performans sonucu degil, skor hesaplamasi icin gerekli veri kaynaklarinin kac calisanda mevcut oldugunu anlatir.
- Huni satirlarinin altina ne anlama geldikleri eklendi:
  - Departmandaki calisanlar
  - KPI/ML verisi olanlar
  - Nabiz yaniti olanlar
  - 360 NLP analizi olanlar
  - Tam hibrit profili olanlar
- Tablo basliklari `Stage/Value/Conv. Rate/Drop-off` yerine `Veri Adimi/Kisi/Kapsama/Eksik` olarak Turkcelestirildi.
- Sag ozet karti yeni amaca gore guncellendi:
  - Eyebrow: `Eksik veri etkisi`
  - Baslik: `Skorun hangi kismi eksik veri yuzunden zayif?`
  - Her sonuca artik `title`, `description`, `impact` alanlariyla aciklama ekleniyor.
- 360 verisi yoksa ozet artik acikca soyluyor: 360 NLP sinyali skora katilamiyor; psikolojik guven, is birligi, destek ihtiyaci ve burnout metin sinyalleri hesaplanamiyor.
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `npm.cmd run type-check` ve `npm.cmd run build-only` basarili.
  - Frontend container `docker compose restart frontend` ile yeniden baslatildi.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- Gerekirse bu bolumun adi tamamen `Veri Tamamligi ve Guven Etkisi` yapilarak `funnel` kavrami UI'dan tamamen kaldirilabilir.

## 2026-05-25 Hibrit Icgoruler LLM Yorum Katmani

- Kullanici `Hibrit Icgoruler / Kesisim analizi` bolumunun cok detaysiz kaldigini ve LLM ile detayli prompt kullanilip kullanilamayacagini sordu.
- Yaklasim: Skor ve metrik hesaplari backendde deterministik kaldi; LLM yalnizca verilen gercek dashboard JSON'unu yorumlayan katman olarak eklendi.
- `DepartmentDashboardInsightResponse` semasi genisletildi:
  - `evidence`
  - `manager_interpretation`
  - `impact`
  - `follow_up_metrics`
  - `source`
  - `model`
  - `fallback_used`
- `SoftwareMLService._dashboard_insights` artik deterministik insight'lari da detayli alanlarla olusturuyor.
- `use_llm=true` geldiginde yeni `_dashboard_llm_insights` akisi calisiyor:
  - KPI/ML, nabiz, 360, skorlar, veri kapsama ve kural bazli sinyaller prompt payload'una konuyor.
  - LLM'e yeni sayi/metrik/olay uydurmamasi, 360 verisi yoksa dogrulanamiyor demesi ve yalnizca JSON dondurmesi soyleniyor.
  - Beklenen JSON: type, severity, title, description, evidence, manager_interpretation, impact, recommendation, action, follow_up_metrics.
  - LLM provider yoksa veya gecersiz JSON donerse detayli deterministik fallback kullaniliyor.
- Frontend `ManagerDashboard.vue` artik dashboard endpoint'ini `use_llm: true` ile cagiriyor.
- Hibrit icgoru kartlari yeniden tasarlandi:
  - Severity etiketi
  - Aksiyon etiketi
  - LLM/kural bazli kaynak etiketi
  - Kanitlar listesi
  - Yonetici yorumu
  - Etki
  - Onerilen aksiyon
  - Takip metrikleri
- `analytics.api.ts` frontend tipleri yeni insight alanlariyla guncellendi.
- Canli smoke testte `/analytics/departments/software/dashboard?period=week&use_llm=true` Gemini kaynakli detayli insight dondurdu (`source=gemini`, `model=gemini-2.5-flash-lite`, `fallback_used=false`).
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `py_compile`, `npm.cmd run type-check`, `npm.cmd run build-only` basarili.
  - Backend `docker restart propel_backend` ile yeniden baslatildi.
  - Frontend `docker compose restart frontend` ile yeniden baslatildi.
  - Backend dashboard endpoint smoke testi basarili.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- LLM yorumlari yavas gelirse bu endpoint icin cache veya `LLM ile yenile` butonu dusunulebilir; su an sayfa yuklenirken LLM cagrisi senkron calisiyor.

## 2026-05-25 AI Ozet LLM Analizine Baglandi

- Kullanici `AI Ozet / Birlesik departman yorumu` bolumunun gercek AI analizi gibi gorunmedigini belirtti.
- Tespit: Hibrit icgoruler LLM'e baglanmisti; fakat `ai_summary` hala deterministik skor cumlesi ve insight basliklarindan uretiliyordu.
- `DepartmentDashboardAISummaryResponse` semasi genisletildi:
  - `model`
  - `fallback_used`
- `SoftwareMLService._dashboard_ai_summary` artik `use_llm=true` geldiginde ayri bir LLM prompt'u calistiriyor.
- Yeni prompt KPI/ML, nabiz, 360, coverage, skorlar, LLM/kural bazli hibrit icgoruler ve aksiyonlari tek payload olarak veriyor.
- LLM'den JSON bekleniyor:
  - `summary`
  - `strengths`
  - `risks`
  - `recommendations`
- Prompt kurallari:
  - Yeni sayi/metrik/olay uydurma.
  - 360 verisi yoksa psikolojik guven/is birligi/burnout tarafinin dogrulanamadigini acikca soyle.
  - Summary 4-6 cumlelik yonetici ozet raporu olsun.
  - Riskler ve oneriler baslik listesi degil, aciklayici ve uygulanabilir metinler olsun.
- LLM basarisiz olursa daha acik deterministik fallback donuyor ve `source=deterministic_llm_fallback`, `fallback_used=true` ile isaretleniyor.
- Frontend `AI Ozet` kartina kaynak etiketi eklendi:
  - `LLM yorumu`
  - `Kural bazli ozet`
- Kart alt basliklari netlestirildi:
  - `AI'nin Dayandigi Guclu Kanitlar`
  - `AI Risk Yorumu`
  - `AI Aksiyon Onerileri`
- Canli smoke testte `ai_summary` Gemini'den geldi:
  - `source=gemini`
  - `model=gemini-2.5-flash-lite`
  - `fallback_used=false`
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `py_compile`, `npm.cmd run type-check`, `npm.cmd run build-only` basarili.
  - Backend `docker restart propel_backend` ile yeniden baslatildi.
  - Frontend `docker compose restart frontend` ile yeniden baslatildi.
  - Backend dashboard endpoint smoke testi basarili.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- Dashboard yukleme suresi iki LLM cagrisi nedeniyle uzarsa AI ozet ve hibrit icgoruler icin cache veya manuel `AI analizi yenile` butonu eklenebilir.

## 2026-05-25 Hizli Aksiyonlar Veri Dayanagi Gosterimi

- Kullanici `Hizli Aksiyonlar` bolumundeki onerilerin neye gore uretildigini ve hardcoded olmamasi gerektigini belirtti.
- Tespit:
  - Aksiyon basliklari backendden geliyordu.
  - Insight kaynakli aksiyonlar LLM/kural bazli hibrit icgorulerden turetiliyordu.
  - Takim aksiyonlari `team_breakdown` icindeki dusuk saglik skorlarindan turetiliyordu.
  - Ancak frontend yalnizca `title + priority` gosterdigi icin aksiyonlar hardcoded gibi gorunuyordu.
- Backend `SoftwareMLService._dashboard_actions` guncellendi:
  - Insight aksiyonlarinin `description` alani artik `Dayanak` ve `Yonetici yorumu` bilgisini iceriyor.
  - Dayanak olarak insight evidence maddeleri kullaniliyor.
  - Takim aksiyonlari `QA takim sagligini izle` gibi genel metin yerine gercek skor kirilimiyla uretiliyor.
  - Takim aksiyonlarinda hibrit saglik, KPI/ML, nabiz, 360, risk ve en zayif kaynak yaziyor.
  - Veri kapsama aksiyonunda veri guveni skoru acikca belirtiliyor.
- Frontend `QuickActions.vue` guncellendi:
  - Aksiyon basligi disinda aciklama/dayanak metni gosteriliyor.
  - Sahip, vade ve kaynak rozetleri eklendi.
  - Kaynak etiketleri kullanici dostu hale getirildi (`Hibrit risk`, `360 eksigi`, `KPI + Nabiz`, `Takim skoru`, vb.).
- `ManagerDashboard.vue` quick action mapping'i genisletildi:
  - `description`
  - `owner`
  - `dueDate`
  - `source`
  alanlari QuickActions component'ine aktariliyor.
- Canli smoke testte aksiyonlar artik ornek olarak su dayanaklarla donuyor:
  - KPI/ML performansi 28.0, ML risk skoru 72.0, yuksek riskli calisan sayisi 14.
  - 360 kapsami %0 ve davranissal metriklerin dogrulanamadigi.
  - QA hibrit saglik 24.9, KPI/ML 18.0, nabiz 63.6, 360 0.0, risk 44.3.
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `py_compile`, `npm.cmd run type-check`, `npm.cmd run build-only` basarili.
  - Backend `docker restart propel_backend` ile yeniden baslatildi.
  - Frontend `docker compose restart frontend` ile yeniden baslatildi.
  - Backend dashboard endpoint smoke testi basarili.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- Aksiyonlar ileride kalici task modeline baglanabilir; checkbox state'i backendde saklanabilir ve aksiyon tamamlanma durumu yonetici bazli takip edilebilir.

## 2026-05-25 Sidebar Sticky Layout Duzeltmesi

- Kullanici uzun dashboard sayfasinda asagi inerken sidebar yazilarinin kayboldugunu ve her zaman gorunur kalmasinin daha iyi olacagini belirtti.
- `AppLayout.vue` layout yapisi guncellendi:
  - Dis kapsayici `min-h-screen` yerine `h-screen overflow-hidden` oldu.
  - Sidebar `sticky top-0 h-screen shrink-0` olarak sabitlendi.
  - Main icerik alani `h-screen overflow-y-auto` yapildi.
- Bu yapiyla sidebar viewport boyunca sabit kaliyor; sayfa icerigi kendi alaninda scroll ediyor.
- Sidebar icindeki nav zaten `overflow-y-auto` oldugu icin menu fazla uzarsa sidebar kendi icinde kayabiliyor.
- Dogrulama:
  - Degisiklik oncesi `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `npm.cmd run type-check` ve `npm.cmd run build-only` basarili.
  - Frontend `docker compose restart frontend` ile yeniden baslatildi.
  - `http://localhost:5173/manager` HTTP 200 dondu.

## Sonraki Adim

- Mobil icin mevcut `md:hidden` davranisi korunuyor; gerekirse ayrica mobil drawer/sidebar tasarimi ele alinabilir.

## 2026-05-25 Demo 360 Feedback Seed Verisi

- Kullanici 360 derece geri bildirim verileri eksik oldugu icin yazilim departmani icin sorulara uygun sahte/demo 360 verisi olusturmanin mantikli olup olmadigini sordu ve onay verdi.
- Yaklasim:
  - Dashboard skorlarina direkt veri basilmadi.
  - Mevcut `feedback_responses` ve `feedback_nlp_analyses` pipeline'i kullanildi.
  - Veriler `model_provider=synthetic_seed`, `model_name=demo-360-software-v1` ile demo/synthetic olarak isaretlendi.
- Yeni script eklendi:
  - `propel-backend/scripts/seed_demo_360_feedback.py`
- Script davranisi:
  - Yazilim departmanini ve mevcut calisanlari DB'den bulur.
  - Mevcut hafta icin 360 sorusu yoksa department + direction bazli soru olusturur.
  - Her calisan icin en fazla 3 incoming feedback planlar.
  - Ayni takim, capraz takim ve manager/upward kombinasyonlariyla 360 iliski agi kurar.
  - Takim bazli sinyal cesitlendirir:
    - Backend/QA daha fazla risk ve gelisim sinyali
    - Frontend/DevOps daha dengeli pozitif-gelisim sinyali
    - Yonetim icin karar netligi/destek sinyali
  - Cevaplar soru odagina uygun olarak somut durum + davranis + etki + destek/risk onerisi icerecek sekilde uretilir.
  - NLP analizi `AIService._fallback_weekly_analysis` ve `NLPService.save_weekly_analysis` ile kaydedilir.
  - Haftalik profil ve aylik rozet refresh islemleri calistirilir.
  - Tekrar calistirilabilir; default olarak once eski `synthetic_seed` kayitlarini temizler.
- Calistirma:
  - `docker exec propel_backend python scripts/seed_demo_360_feedback.py --dry-run`
  - `docker exec propel_backend python scripts/seed_demo_360_feedback.py`
- Sonuc:
  - 31 yazilim calisani bulundu.
  - 92 yeni demo feedback/NLP kaydi olusturuldu.
- Dashboard smoke test sonucu:
  - 360 feedback cevap sayisi: 92
  - 360 kapsanan calisan: 31
  - 360 kapsama: %100
  - 360 skoru: 69.0/100
  - Departman sagligi: 47.9/100
  - Insan sagligi: 67.7/100
  - Birlesik risk: 53.7/100
  - Agirliklar yeniden KPI/ML %50, Nabiz %25, 360 %25 olarak aktif hale geldi.
- Dogrulama:
  - Script `py_compile` basarili.
  - Container icinde dry-run basarili.
  - Container icinde gercek seed basarili.
  - Dashboard endpoint smoke testi basarili.

## Sonraki Adim

- Demo 360 verileri UI'da gercek veri gibi algilanmasin istenirse, 360 kaynak detayinda `synthetic_seed` kayitlari icin kucuk bir `Demo veri` etiketi gosterilebilir.

## 2026-05-25 Ekibim Sayfasi Gercek Veri ve Risk Toplantisi

- Kullanici `Ekibim` sayfasinda hardcoded degerler olup olmadigini, KPI + 360 feedback + nabiz anketi birlesik gercek sonuclarinin gorunmesini ve calismayan butonlarin backend'e baglanmasini istedi.
- Tespit:
  - `TeamManagement.vue` ust kartlarinda `Aktif Sprintler=3`, `Devam Eden Gorevler=12`, `Velocity=42 pts` hardcoded idi.
  - Tablo sadece `/employees/` endpoint'inden gelen son nabiz alanlarini kullaniyordu; KPI ve 360 NLP profili bu sayfada yoktu.
  - Arama input'u state'e bagli degildi, filtre butonu islevsizdi, satir aksiyon butonu islevsizdi.
  - `Gorev Atama` butonu backend'e bagli degildi.
- Backend:
  - `GET /api/v1/employees/team-health` endpoint'i eklendi.
  - Endpoint manager/admin yetkisiyle calisir; manager icin kendi departmanini scope eder.
  - KPI sinyali `AnalyticsService.get_performance_summary`, nabiz sinyali son `weekly_pulse`, 360 sinyali son weekly `EmployeeNLPProfile` kaydindan alinip tek kontratta birlestiriliyor.
  - Her calisan icin `kpi_score`, `kpi_trend`, `latest_pulse_score`, `latest_mte`, `latest_ars`, `feedback_count`, 360 risk seviyeleri, `combined_risk_score`, `combined_risk_level`, `recommended_action` ve `data_sources` donuyor.
  - Ust kartlar artik KPI kapsami, nabiz ortalamasi, 360 profil kapsami, risk toplantisi adayi ve veri guveni olarak gercek kaynaktan hesaplanir.
- Frontend:
  - `employeeApi.getTeamHealth()` eklendi.
  - `TeamManagement.vue` yeni team-health kontratina baglandi.
  - Hardcoded sprint/gorev/velocity kartlari kaldirildi.
  - Tablo kolonlari KPI, Nabiz, 360 Profil ve Birlesik Risk olacak sekilde yenilendi.
  - Arama ve risk filtresi calisir hale geldi.
  - Satir aksiyonlari eklendi: calisan analizine gitme ve tek calisan icin toplantı planlama.
  - `Gorev Atama` yerine `Risk Toplantisi Planla` butonu geldi; riskli calisanlari secili getiriyor, tarih/saat/sure/not/katilimci modalindan `/meetings/team-risk` endpoint'ine kaydediyor.
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `py_compile` ve `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` ve `docker restart propel_frontend` calisti.
  - `GET /employees/team-health` smoke testinde 31 uye, KPI 30/31, nabiz 30/31, 360 profil 31/31 ve veri guveni %98 dondu.
  - `POST /meetings/team-risk` smoke testi basarili; meeting id 7, attendee id 40, notification id 43 olustu.
  - Browser ile `/manager/team` yenilendi; yeni kartlar, KPI/Nabiz/360 tablo kolonlari ve `Risk Toplantisi Planla` modalinin acildigi dogrulandi.

## Sonraki Adim

- Risk esikleri demo veride tum calisanlari orta riske cekiyor; gercek uretim kalibrasyonu icin KPI/ARS/360 agirliklari ve `medium/high` esikleri ekiple birlikte netlestirilebilir.

## 2026-05-25 Toplanti Daveti ve Meet Linki

- Kullanici `Davet olusturuldu` mesajinin gercek kayit olusturup olusturmadigini ve toplantilar icin dogrudan Meet linki gonderilip gonderilemeyecegini sordu.
- Canli DB kontrolu:
  - Son toplanti kaydi gercekten olusmustu: `meeting id=9`.
  - 24 katilimci ve 24 `meeting_invite` bildirimi vardi.
  - Eski bildirimlerde tarih/saat/gundem vardi fakat toplanti linki yoktu.
- Tasarim karari:
  - Google Meet linkini otomatik uretmek Google Calendar/OAuth entegrasyonu gerektirir.
  - Ilk guvenli surumde yonetici Meet/Teams/Zoom linkini modalda yapistirir; sistem linki toplantida saklar ve davet metnine ekler.
  - Toplantiyi kuran yoneticiye de ayrica `meeting_organizer` bildirimi olusturulur; boylece calisanlar ve yonetici ayni linke bildirimden ulasir.
- Backend:
  - `Meeting.meeting_url` alani eklendi.
  - `TeamMeetingCreateRequest` ve `TeamMeetingCreateResponse` icine `meeting_url` eklendi.
  - `ensure_meeting_columns` ile mevcut PostgreSQL DB'ye `meetings.meeting_url` kolonu otomatik eklenir.
  - `MeetingService` linki temizleyip kaydeder, katilimci bildirimlerine `Katilim linki: ...` ekler ve yoneticiye `meeting_organizer` bildirimi yaratir.
- Frontend:
  - `meetings.api.ts` payload/response tiplerine `meeting_url` eklendi.
  - `TeamManagement.vue` toplantı modalina `Toplantı Linki` input'u eklendi; link varsa davetlere gider.
  - `ManagerAnalyticsView.vue` takim toplantisi modalina ayni link alani eklendi.
- Dogrulama:
  - Degisiklik oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi `py_compile` ve `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` ve `docker restart propel_frontend` calisti.
  - Linkli smoke test basarili: `meeting id=10`, calisan bildirimi `id=98`, yonetici organizer bildirimi `id=99`.
  - Bildirim govdesinde `https://meet.google.com/abc-defg-hij` linki hem calisana hem yoneticiye eklendi.

## Sonraki Adim

- Ileride Google Calendar entegrasyonu istenirse OAuth + calendar event create akisi eklenerek Meet linki sistem tarafindan otomatik uretilebilir; mevcut surum link yapistirma ve uygulama ici bildirim dagitimini destekler.
