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

## Test Kullanıcıları (seed_data.py)

| Email | Şifre | Rol |
|---|---|---|
| admin@propel.com | admin123 | Admin |
| manager.yazilim@propel.com | manager123 | Yazılım Yöneticisi |
| manager.satis@propel.com | manager123 | Satış Yöneticisi |
| developer1@propel.com | dev123 | Çalışan (Yazılım) |
| satis.employee@propel.com | satis123 | Çalışan (Satış) |

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

## Sonraki Adımlar / Roadmap

- [ ] Satış departmanı frontend dashboard'u (Vue 3) — employee/manager/admin görünümleri
- [ ] `app/tests/` dizinine temel pytest test suite'i (hedef: %80 coverage)
- [ ] Playwright kurulumu ile frontend smoke testleri
- [ ] LLM narrative endpoint'ini async/background job olarak ayır
- [ ] Departman Analizi AI Modal → PDF İndir ve Email Gönder backend bağlantısı
- [ ] Yeni departman desteği (İK, Pazarlama): registry + kpi_registry + seed genişletme
- [ ] WebSocket ile gerçek zamanlı bildirimler
- [ ] GDPR/KVKK uyumluluk özellikleri
