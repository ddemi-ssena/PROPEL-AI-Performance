# AGENTS.MD — KUTUP Agent Kılavuzu

> Bu dosya hem AI agent'lar için canlı bir proje rehberi hem de geliştirme günlüğüdür.
> Her sohbetin sonunda yapılan çalışma özeti, kalınan nokta ve sonraki adımlar buraya eklenir.

---

## Kalıcı Talimatlar

- Her sohbet sonunda yapılan çalışma özeti, kalınan nokta ve sonraki adımlar bu dosyaya kaydedilecek.
- Her sohbet sonunda `AGENTS.MD` ile birlikte `CLAUDE.md` de aynı çalışma günlüğüyle güncellenecek.
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

**Önemli Kısıt**: Yeni dataset (1612 satır, 31 çalışan) ile tüm 4 hedef başarıyla eğitiliyor:
- Performance_Drop: %100 F1, 1240/372 train/test
- Burnout: %99.4 F1
- Resignation: %99.5 F1
- High_Risk: %98.9 F1

**Aktif Dataset**: `KUTUP_Sales_52Week_2024.xlsx` — 31 çalışan (SA-001..SA-031) × 52 hafta = 1612 satır.
- SA-031: Hatice Yıldırım (Sales Department Manager, Genel bölge)
- Tüm "Manager" pozisyon unvanları → "Sales Team Lead" olarak güncellendi (sadece Hatice Yıldırım "Manager")

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

### 2026-05-26 Satış Uzmanı Giriş Bugları ve Dashboard İyileştirmesi

**Sorunlar ve Düzeltmeler:**

- **`propel-backend/.env` eksikti** → `DATABASE_URL`, `SECRET_KEY`, `POSTGRES_PASSWORD` içeren `.env` oluşturuldu. Docker Compose `env_file` direktifi bu dosya olmadan başlamıyordu.
- **`employees` tablosu boştu** → Hiçbir kullanıcının `department_id` / `department_name` bilgisi yoktu. `docker exec propel_backend python seed_data.py` ile 63 kullanıcı, 62 employee kaydı, 45 KPI tanımı, 8250 KPI kaydı yüklendi.
- **`client.ts` — 401 interceptor login'i engelliyordu** → `/api/v1/auth/login` isteği 401 döndürdüğünde interceptor `window.location.href = '/login'` tetikleyerek mock login fallback'in çalışmasını engelliyordu. `error.config?.url?.includes('/auth/login')` kontrolü eklenerek login isteği 401'leri bypass edildi.
- **`router/index.ts` — `isSalesUser` hatalıydı** → Satış kullanıcıları `sl-XXX@propel.com` formatındayken fonksiyon yalnızca `sa-` prefix ve yanlış dept ID'lerini (2, 14, 18) kontrol ediyordu. Gerçek Satış departman ID'si 20. `email.startsWith('sl-')` ve `deptId === 20` eklendi.
- **`LoginView.vue` — `isSales` hatalıydı** → Aynı sorun; `email.startsWith('sl-')` eklendi.
- **`seed_data.py` — Double UTF-8 encoding (mojibake)** → Dosya UTF-8 karakterleri Latin-1/Windows-1252 olarak okunup yeniden UTF-8 kaydedilmiş; `Ali Yılmaz` → `Ali YÄ±lmaz` gibi görünüyordu. Latin-1+cp1252 byte-level ters çevirme algoritmasıyla düzeltildi.
- **`SalesEmployeeDashboard.vue` — Veri yokken dashboard tamamen gizleniyordu** → `v-else-if="!perfData?.has_upload"` bloğu kaldırıldı; yerine küçük sarı uyarı banner'ı eklendi. KPI kartları artık her zaman görünür; Excel yüklenmemişse değerler `—` gösterir, yüklenince otomatik dolar.

**Kalıcı Notlar:**
- Frontend container'ı değişiklik sonrası `docker restart propel_frontend` + tarayıcıda `Ctrl+Shift+R` gerektirir; Vite Windows+Docker ortamında hot-reload'ı algılamayabiliyor.
- `CLAUDE.md` ve `seed_data.py` dosyaları da mojibake içeriyordu; aynı algoritmayla düzeltildi.
- Seed sonrası test hesabı: `satis.employee@propel.com` / `satis123` → `/employee/sales` (Zeynep Kaya, SA-011, Satış dept ID: 22).

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

**ML Target Durumu** (upload_id=4, 31 çalışan × 52 hafta = 1612 satır):
- `Performance_Drop_Target` ✅ F1=100%, 1240/372
- `Burnout_Target` ✅ F1=99.4%, 1240/372
- `Resignation_Target` ✅ F1=99.5%, 1240/372
- `High_Risk_Target` ✅ F1=98.9%, 1240/372

**Riskli Çalışanlar** (Performans Düşüşü hedefine göre):
Nihan Korkmaz, Baran Özdemir, Ozan Çetin, Tuncay Doğan, Aslı Erdoğan, Burcu Arslan, Serhat Bulut, Derya Kaplan

**Önemli Keşif**: `/api/v1/auth/me` endpoint'i `department_id` döndürmüyordu → `department_name` de eklendi. Frontend sidebar artık email + department_name + route üzerinden satış tespiti yapıyor.

---

## Geliştirme Günlüğü (Devam)

### 2026-05-21 Satış Çalışan Dashboard Backend Bağlantısı ★

**Yeni Backend Endpoint**:
- `GET /analytics/departments/sales/my-performance` — kimlik doğrulamalı çalışan için kişisel dashboard verisi
  - 9 KPI metriği (SHGO, LMDO, TKO, OSDS, CSAT, CRMD, TDO, PSO, MS) — gerçek Excel verisi
  - 8 haftalık bileşik performans trendi
  - ML tahmini (Performance_Drop_Target) — `predicted_band`, `recommended_actions`, `top_drivers`
  - `bar_pct` (0-1) — frontend progress bar için

**Yeni Şemalar** (`schemas/analytics.py`):
- `SalesKPIMetric` — code, name, raw_value, unit, direction, threshold_status, trend_signal, bar_pct
- `SalesWeeklyTrendPoint` — label, score
- `SalesEmployeePerformanceResponse` — tüm dashboard verisi

**Auth `/me` Güncelleme** (`api/routers/auth.py`, `schemas/user.py`):
- `department_name` alanı eklendi → sidebar ve router yönlendirmesi için

**Frontend Güncellemeleri**:
- `SalesEmployeeDashboard.vue` — tüm hardcoded veriler gerçek `getMyPerformance()` API'sine bağlandı
- `survey.api.ts` — `createSurvey()` metodu eklendi (nabız anketi gerçek POST /surveys/)
- `analytics.api.ts` — `getMyPerformance()`, `SalesEmployeePerformanceResponse`, `SalesKPIMetric`, `SalesWeeklyTrendPoint` eklendi
- `AppLayout.vue` — `isSalesDept` email + department_name + route tabanlı tespit
- `router/index.ts` — satış müdürü login sonrası `/manager/sales-analytics`'e yönlendirilir
- `EmployeePulseView.vue` — "Personel Paneline Dön" butonu kaldırıldı

**EMP_XXX Format Desteği**: `get_my_performance()` metodunda `SA-011` → `EMP_011` eşleştirmesi düzeltildi

### 2026-05-21 Satış Dataset ve Seed Güncellemesi ★

**Yeni Dataset**: `KUTUP_Sales_52Week_2024.xlsx`
- 31 çalışan (SA-001..SA-031) × 52 hafta = 1612 satır
- SA-031: Hatice Yıldırım (Sales Department Manager)
- Tüm pozisyon unvanları: "Sales Manager" → "Sales Team Lead" (sadece SA-031 "Manager")
- 28 kolon, 4 hedef değişken
- Target dağılımları: PerfDrop=%34, Burnout=%3.3, Resignation=%5, HighRisk=%6.3
- Generator script: `generate_sales_dataset.py`

**Seed Data Güncellemeleri** (`seed_data.py`):
- Tüm isimler Türkçe karakterlerle güncellendi (ı, ş, ğ, ç, ö, ü)
- `manager.satis@propel.com` → `Hatice Yıldırım` (department_manager, SA-031, Genel bölgesi)
- `satis.employee@propel.com` → `Zeynep Kaya` (SA-011)
- SALES_EMPLOYEE_SPECS takım isimleri Excel Region sütunuyla birebir eşleşiyor
- SA-011 loop'tan hariç tutuldu (ayrıca satis.employee olarak ekleniyor)

**Test Kullanıcıları (Güncel)**:
| Email | Şifre | Rol | Yönlendirme |
|---|---|---|---|
| admin@propel.com | admin123 | Admin | /admin |
| manager.satis@propel.com | manager123 | Hatice Yıldırım — Satış Müdürü | /manager/sales-analytics |
| manager.yazilim@propel.com | manager123 | Ahmet Yılmaz — Yazılım Müdürü | /manager |
| satis.employee@propel.com | satis123 | Zeynep Kaya (SA-011) | /employee/sales |
| sa-020@propel.com | employee123 | Ozan Çetin — Riskli profil | /employee/sales |
| sa-001@propel.com | employee123 | Ali Yılmaz — Güvenli profil | /employee/sales |

---

### 2026-05-26 Satış 360° Feedback — Seed, Backend Doğrulama, Frontend View ★

**Eklenen Dosyalar**:
- `propel-backend/scripts/seed_demo_360_sales.py` → Satış departmanı için demo 360° feedback seed scripti
  - 31 çalışan × ~3 feedback = 92 `FeedbackResponse` + 92 `FeedbackNLPAnalysis` + 31 `EmployeeNLPProfile`
  - Bölge bazlı sinyal seçimi (Doğu/Güneydoğu→risk, Marmara/Ege→positive, vb.)
  - Yönetici tespiti: "Genel" team = manager (SA-031 Hatice Yıldırım)
  - `model_provider = "synthetic_seed_sales"` → `--no-reset` ile yeniden seed edilebilir
- `propel-frontend/src/views/sales/SalesFeedbackView.vue` → Satış yöneticisi 360° feedback dashboard
  - Emerald/teal tema; 4 KPI kartı (analiz edilen çalışan, ort. motivasyon, uçuş riski, ort. işbirliği)
  - Gradient sinyal paneli (güçlü yönler / risk alanları / destek ihtiyaçları)
  - Departman 360 raporu (narrative + sections + recommended action)
  - Metrik çubukları, uçuş riski dağılımı, tükenmişlik dağılımı, risk tema sıralaması
  - SVG motivasyon trend grafiği (gradient fill + polyline)
  - TypeScript: `TrendPoint`, `DistributionPoint`, `ThemePoint` ile explicit tipler

**Güncellenen Dosyalar**:
- `propel-frontend/src/router/index.ts` → `/manager/sales-feedback` route eklendi
- `propel-frontend/src/layouts/AppLayout.vue` → KPI & ML Analizi grubuna "360 Geri Bildirim" eklendi
- `propel-frontend/src/views/manager/DepartmentAnalysisView.vue` → 32 mojibake sequence düzeltildi
- `propel-frontend/src/views/manager/EmployeeAnalysisView.vue` → 35 mojibake sequence düzeltildi

**Backend Doğrulama** (tüm endpointler `manager.satis@propel.com` ile test edildi):
- `GET /feedbacks/nlp/department-summary` → 31 çalışan, avg_motivation=3.34, flight_risk=5
- `GET /feedbacks/reports/department` → sections + metrics döndürüyor
- `GET /feedbacks/charts/department` → 4 trend noktası, flight/burnout dağılımı, risk temaları

**Encoding Düzeltmesi**:
- `DepartmentAnalysisView.vue` ve `EmployeeAnalysisView.vue` hardcoded template string'leri
  çift-encode edilmiş durumdaydı (UTF-8 bytes → Windows-1252 → UTF-8 olarak kaydedilmiş)
- Hedef map ile düzeltildi: `Ä±`→`ı`, `ÅŸ`→`ş`, `Ã¼`→`ü`, `ÄŸ`→`ğ`, `Ã§`→`ç`, `Ä°`→`İ`, `Ã–`→`Ö` vb.

---

### 2026-06-02 Admin Panel Mock Verileri Gerçek Backend'e Bağlandı ★

**Sorun**: Admin panelindeki 3 sayfa tamamen hardcoded/mock verilerle çalışıyordu:
- `EmployeeDetails.vue`: Her zaman "Canan Dağdelen" gösteriyordu, `route.params.id` okunmuyordu
- `AdminDashboard.vue`: Uçuş Riski Radarı hardcoded "Elif Demir" ve "Can Kaya"; departman yöneticisi hep "Yönetici Atanmadı"
- `DataManagement.vue`: "Şablon İndir" butonu tıklanamaz; hardcoded "Pazarlama uyarısı"

**Eklenen Backend Endpoint**:
- `GET /api/v1/admin/uploads/template?dept=software|sales` → UTF-8 BOM'lu CSV şablon dosyası indirme
  - Rota çakışması: `/template` rotası `/{upload_id}` ile çakışıyordu → `GET /template` `GET /{upload_id}`'den önce tanımlandı
  - Windows Docker volume sync gecikmesi: `docker cp` ile manuel kopyalama gerekti

**Güncellenen Frontend Dosyaları**:
- `views/admin/EmployeeDetails.vue` — tamamen yeniden yazıldı:
  - `route.params.id` okunarak `GET /employees/{id}` çağrılıyor
  - `GET /kpis/records/employee/{id}` → dönem bazlı ortalama trend grafiği
  - Stats: `latest_ms`, `latest_ars`, `experience_years`, KPI kayıt sayısı
  - Motivasyon gauge: `latest_ms` (0-10) → açı hesabı
  - AI insights: `risk_level` + `latest_mte` + `experience_years` tabanlı deterministik metin
  - KPI özeti: en yüksek 5 KPI progress bar olarak
  - Loading/error state eklendi
- `views/admin/AdminDashboard.vue`:
  - Uçuş Riski: employees listesinden `risk_level=High/Medium` filtre, `combined_risk_score`'a göre sıralı top 4
  - Departman yöneticisi: `user.role === 'department_manager'` ile tespit → gerçek isim ve initials
  - Departman skoru: `latest_ms` ortalaması (MS: 0-10 skalası)
- `views/admin/DataManagement.vue`:
  - "Şablon İndir" butonu `adminUploadApi.downloadTemplate(dept)` çağrısına bağlandı
  - Hardcoded "Pazarlama uyarısı" → yükleme başarısında gösterilen yeşil banner ile değiştirildi
- `services/api/employee.api.ts` — `getEmployee(id)` metodu eklendi
- `services/api/admin_upload.api.ts` — `downloadTemplate(dept)` metodu eklendi (blob download)

**Risk Seviyesi Kaynağı** (önemli not):
- `risk_level` Excel dosyalarından **gelmez**; nabız anketinden hesaplanır
- `SurveyResponse.ars_score` (işten ayrılma riski, 0-1): `ars_score ≥ 0.6` → High, `≥ 0.2` → Medium, `< 0.2` → Low
- `ars_score` iki kaynaktan gelir: (1) gerçek kullanımda ML motoru metin analizi, (2) seed_data.py deterministik formül

**Push**: `cansuyildirimmm/AI-Supported-Department-Employee-Performance-Analysis-System` → branch `99999999.branch` (commit `9061d68`)

---

### 2026-05-22 Satış Çalışanı Login Redirect Düzeltmesi ★

**Sorun**: `satis.employee@propel.com` ile giriş yapıldığında `/employee/sales` (SalesEmployeeDashboard, emerald tema) yerine `/employee` (genel EmployeeDashboard, lacivert tema) açılıyordu. Sayfa yenilendikten sonra veya eski oturumda da aynı sorun tekrar ediyordu.

**Kök Neden**: Pinia store'da `token` localStorage'dan restore ediliyordu (`ref(localStorage.getItem('token'))`) fakat `user` objesi `null` kalıyordu. Router guard `user = null` iken `isSales` kontrolü yapınca `false` döndürüyor ve `/employee`'ye yönlendiriyordu.

**Düzeltilen Dosyalar**:

`propel-frontend/src/stores/auth.ts`:
- `login()` fonksiyonu: başarılı girişten sonra `userEmail` ve `deptId` localStorage'a kaydediliyor
- `tryMockLogin()`: mock giriş için de aynı şekilde `userEmail` ve `deptId` kaydediliyor
- `logout()`: `userEmail` ve `deptId` localStorage'dan temizleniyor

`propel-frontend/src/router/index.ts`:
- `isSalesUser()` yardımcı fonksiyonu eklendi: `user` objesi yokken `localStorage.getItem('userEmail')` ve `localStorage.getItem('deptId')` fallback olarak kullanılıyor; `department_id === 14/18` kontrolü eklendi
- `router.beforeEach` guard `async` yapıldı: token varken `user = null` ise (sayfa yenileme / eski oturum) `/me` çekilip user restore ediliyor
- `requiresGuest` guard: `authStore.userRole || localStorage.getItem('role')` ile role tespiti güçlendirildi
- `employee-dashboard` guard eklendi: satış çalışanı `/employee`'ye gelirse otomatik `/employee/sales`'e yönlendiriliyor

**Önemli Teknik Not**: Windows'ta Docker Desktop volume sync gecikmesi nedeniyle HMR çalışmayabiliyor. Dosya değişikliklerinden sonra `docker cp` ile container'a manuel kopyalama gerekebilir:
```bash
docker cp propel-frontend/src/router/index.ts propel_frontend:/app/src/router/index.ts
docker cp propel-frontend/src/stores/auth.ts propel_frontend:/app/src/stores/auth.ts
docker restart propel_frontend
```

---

### 2026-06-03 Admin Panel ML Entegrasyonu + Gemini AI ★ BÜYÜK

**Personel Yönetimi (EmployeeManagement.vue) — Tam ML Entegrasyonu**
- `GET /admin/uploads/flight-risk` endpoint'i çağrılarak ML verileri alınır
- `external_employee_code` üzerinden employee listesi ile ML haritası birleştirilir
- Performans çubuğu: ML'den `performance_score` (0-100) — artık `latest_ms * 20` değil
- Risk rozeti: ML'den `risk_level` (High/Low) — artık seed ARS formülü değil
- Departman filtresi: veritabanından dinamik
- Sıralama (performans ↑↓, risk, isim) gerçekten çalışıyor
- En altta: hangi upload ID'lerinin kullanıldığı gösteriliyor

**Backend: `GET /admin/uploads/ai-insights` — Yeni Endpoint**
- ML flight-risk verisini (61 çalışan: 31 satış + 30 yazılım) çeker
- İstatistikleri derleyip Gemini'ye gönderir
- Gemini: Genel Durum / Kritik Bulgular / Aksiyon Önerileri raporu üretir
- KPI kartları, risk donut, çalışan tablosu, Gemini narratifi döndürür
- `gemini_used: true/false` ile Gemini durumu belirtilir

**Yapay Zeka İçgörüleri (AIInsights.vue) — Tamamen Yeniden Yazıldı**
- Eski: `GET /surveys/analytics/insights` (deterministik, 1586 kayıt, yanlış sayılar)
- Yeni: `GET /admin/uploads/ai-insights` (ML + Gemini)
- 4 KPI kartı: toplam çalışan, yüksek riskli, ort. performans, güvenli çalışan
- Risk donut: gerçek ML dağılımı
- Gemini raporu: 3 bölümlü Türkçe yönetici raporu, mor rozet
- Aksiyon önerileri: Gemini'den çıkarılan maddeler kart formatında
- Tüm çalışan tablosu: 61 çalışan, filtreli, sayfalı

**Gemini API Entegrasyonu**
- `GEMINI_API_KEY` `.env` dosyasına eklendi
- `AIService._generate_with_gemini()` kullanılıyor (mevcut altyapı)
- Model: `gemini-1.5-flash` (otomatik seçim)

**Veri Yönetimi (DataManagement.vue)**
- "Veri Tipi" dropdown: sadece "Performans Metrikleri (KPI)" kaldı (Personel Listesi + Anket Sonuçları kaldırıldı)
- "Tüm Geçmişi Görüntüle" butonu çalışıyor: ilk 6 kayıt görünür, butona tıklayınca tamamı açılır

**Anket Sonuçları (SurveyResults.vue) — Gemini Panel**
- Departman filtresi: "Haftalık Nabız / Motivasyon" → "Tüm Departmanlar / Satış / Yazılım" olarak değiştirildi
- Sağ alt köşeye sabitlenmiş mor "Gemini ile Yorumla" butonu eklendi
- Panel açılınca frontend filtrelenmiş veriyi (stats + gerçek q4/q5/q6 yanıtları) POST eder
- Backend `POST /surveys/analytics/gemini-insights`: gerçek anket yanıtlarını Gemini'ye iletir
- Gemini: sayfadaki gerçek çalışan yorumlarına atıfta bulunarak rapor üretir
- Departman değişince açık panel otomatik yenilenir

**Admin Menü**
- "Satis ML Analizi" admin sidebar'dan kaldırıldı

**Uçuş Riski Backend Düzeltmesi**
- Yazılım bloğu backend container'da çalışmıyordu (restart gerekirdi) → düzeltildi
- Artık flight-risk: 30 yazılım (SE-xxx) + 31 satış (SA-xxx) = 61 çalışan
- 61/62 employee_code eşleşiyor (MGR-SW datasette olmadığı için ML verisi yok — beklenen)

**Önemli Teknik Notlar**:
- `GET /admin/uploads/ai-insights` yaklaşık 15-20 sn sürer (ML prediction + Gemini)
- `POST /surveys/analytics/gemini-insights` yaklaşık 5-8 sn sürer
- `docker restart propel_backend` sonrası token yenilenmesi gerekiyor (JWT süre sıfırlanır)
- Flight-risk endpoint'i her çağrıda ML modellerini çalıştırır (cache yok)

---

---

### 2026-06-04/05 Satış + Yazılım ML Analizi Tam Yenileme ★ BÜYÜK

#### Gerçekçi Dataset Üretimi
- `scripts/generate_sales_dataset.py` → `scripts/sales_dataset_v3.xlsx`
  - 31 çalışan (SA-001..SA-031) × 52 hafta = 1612 satır
  - Her çalışan bireysel KPI profili: farklı güçlü/zayıf yönler
  - **Stokastik risk etiketleri** (Bernoulli çekimi) → model anlamlı olasılık öğrenir
  - PD=%32, Burnout=%40, Resignation=%30, HighRisk=%35 dağılımı
  - Aktif upload: #11
- `scripts/generate_software_dataset.py` → `scripts/software_dataset_v2.csv`
  - 31 çalışan (SE-001..SE-030 + MGR-SW) × 52 hafta = 1612 satır
  - 4 yeni binary hedef: `Performance_Drop_Target`, `Burnout_Target`, `Resignation_Target`, `High_Risk_Target`
  - Aktif upload: #12

#### Backend Değişiklikleri
- `analytics/features/software.py`
  - `SOFTWARE_TARGET_COLUMNS`'a 4 yeni binary hedef eklendi
  - SE-xxx, MGR-SW formatında employee_id parse desteği eklendi
- `services/software_ml_service.py`
  - `predict_all_targets()` metodu eklendi (satışla aynı yapı)
  - `list_dataset_employees()` ve `predict_all_from_upload()` SE-xxx parse düzeltmesi
- `services/sales_ml_service.py`
  - `_risk_score()` dict/object uyumlu hale getirildi
- `schemas/analytics.py`
  - `SalesTargetResult`, `SalesEmployeeAllTargets`, `SalesAllTargetsBulkResponse` eklendi
- `api/routers/analytics.py`
  - `GET /departments/software/predictions/bulk-all-targets` eklendi
  - `GET /departments/sales/predictions/bulk-all-targets` eklendi
- `analytics/departments/software.py`
  - `_resolve_department()` → `ilike("%yazılım%")` ile düzeltildi (DB'de "Yazılım Geliştirme")
- `api/routers/admin_uploads.py`
  - `_perf_from_drivers()`: confidence formülü yerine `threshold_status` eşik skorları (Güçlü=92, İzleme=55, Risk=25)
  - `GET /admin/uploads/ai-insights` tamamen yenilendi:
    - Her iki dept için `predict_all_targets()` çağrısı
    - `risk_definitions`: 4 hedef açıklaması + sinyaller + sınırlar
    - `chart_data`: departman × hedef bazlı risk dağılımı
    - `employee_table`: 4 hedef risk %'si + bileşik skor per çalışan
    - Gemini prompt: 4 hedef bazlı zengin bağlam
- `.env`
  - `GEMINI_MODEL=gemini-2.5-flash` (gemini-1.5-flash → 404 veriyordu, güncellendi)
  - `GEMINI_API_KEY` yeniden set edildi

#### Frontend Değişiklikleri
- `SalesAnalyticsView.vue` tam yenileme:
  - 4 hedef kolon tablosu: Risk Olasılığı % + progress bar (≥50 kırmızı, 25-49 sarı, <25 yeşil)
  - `compositeRisk()`: 4 hedefin ağırlıklı bileşik skoru
  - `riskPct()`, `riskColor()`, `riskBar()` helper'lar
  - `riskCounts`: bileşik skora göre yüksek/orta/düşük sayımı
  - `teamRows`: `allTargetsResult.employees`'dan bölge bazlı hesaplama
  - **Toplu Tara**: `getBulkSalesAllTargets()` (LLM yok, hızlı)
  - **LLM Yorumla**: `getBulkSalesAllTargets()` + `getBulkSalesPredictions(llm=true)` paralel
  - `mlOverviewMetrics`: Toplu Tara öncesi → overview verisi, sonrası → ML verisi
  - Dataset dropdown: her zaman en yeni dataset otomatik seçilir (`datasets[0].id`)
- `SoftwareAnalyticsView.vue` ★ YENİ (`views/manager/`)
  - Satış sayfasıyla birebir aynı yapı, indigo renk teması
  - Yazılım API'leri: `getSoftwareDatasets`, `getBulkSoftwareAllTargets`, vb.
  - **Model Eğit**: tek hedef eğitimi (dropdown seçimi), eğitilen kart anında mora döner
  - `filteredModelStates`: sadece 4 yeni hedef gösterilir (eski performance_band gizlenir)
  - `currentTrainingTarget`: hangi kart eğitiliyor göstergesi (spinner + animasyonlu progress bar)
- `AppLayout.vue`
  - Yazılım müdürü sidebar "KPI & ML Analizi" → `/manager/software-analytics`
- `router/index.ts`
  - `/manager/software-analytics` ve `/admin/software-analytics` rotaları eklendi
- `AdminDashboard.vue`
  - "ML Analize Git" → yazılım için `/manager/software-analytics`
- `DataManagement.vue`
  - Dosya adından otomatik departman tespiti: "sales/satis" → Satış, "software/yazilim" → Yazılım
- `AIInsights.vue` tamamen yeniden yazıldı:
  - **Bölüm 1**: 4 KPI kartı (bileşik risk bazlı)
  - **Bölüm 2**: 4 risk hedef tanım kartı (açıklama + sınırlar + sinyaller)
  - **Bölüm 3**: Departman risk dağılımı — her hedef için Satış vs Yazılım progress bar
  - **Bölüm 4**: Tüm çalışan tablosu — 4 hedef % + bileşik skor, arama + filtre
  - **Bölüm 5**: Gemini LLM yorumu — 3 bölümlü rapor, aksiyon kartları

#### Aktif Dataset ve Model Durumu
| Dept | Upload | Dataset | Çalışan | Hedefler |
|---|---|---|---|---|
| Satış | #11 | sales_dataset_v3.xlsx | 31 | PD/BK/RS/YR stokastik |
| Yazılım | #12 | software_dataset_v2.csv | 31 | PD/BK/RS/YR binary |

Yazılım model F1 skorları (Random Forest, test_period_count=8):
- Performance_Drop: 81.0%, Burnout: 76.3%, Resignation: 79.2%, High_Risk: 81.3%

#### Önemli Teknik Notlar
- **SE-xxx parse**: `software_ml_service.py` ve `features/software.py`'de `re.sub(r"[^0-9]", "")` ile parse edilir
- **MGR-SW**: sayısal karakter olmadığı için dataset'te atlanır (tahmin yapılamaz — beklenen)
- **Gemini model**: `gemini-2.5-flash` — `gemini-1.5-flash` API'den kaldırıldı
- **Toplu Tara vs LLM Yorumla ayrımı**: Toplu Tara hızlı (ML only), LLM Yorumla yavaş (+Gemini)
- **Model kartları**: Satışta hepsi birlikte eğitilir, yazılımda dropdown'dan tek tek

---

### 2026-06-05 360° Feedback Altyapısı, Yetenek Dağılımı Düzeltmesi, Personel Yönetimi Yenileme ★

#### 360° Feedback — Kişi Seç Dropdown Düzeltmesi
- **Sorun**: Admin kullanıcısının `Employee` kaydı olmadığından `Promise.all` içindeki `getReceivedFeedbacks()`, `getIncomingRequests()` vb. çağrılar 404/403 döndürüyor, tüm `Promise.all` reddediliyordu → `candidates` hiç set edilmiyordu.
- **Düzeltme** (`FeedbackView.vue`): Her API çağrısına `.catch(() => [])` / `.catch(() => null)` eklendi.
- **Dropdown düzeltmesi** (`FeedbackModal.vue`): `optgroup` grupları kaldırıldı, `sortedCandidates` computed (Türkçe alfabetik sıra) ile düz liste yapıldı.

#### 360° Feedback Gerçekçi Seed Dataseti
- **Yeni Script**: `scripts/seed_360_yazilim.py` — Yazılım + Satış departmanları için kapsamlı 360° seed
  - 4 haftalık tema × 3 yön × çalışan profili bazlı Türkçe yanıtlar
  - 9 dönem: (2026,4,1..4), (2026,5,1..4), (2026,6,1)
  - Toplam: 957 Yazılım + 834 Satış = 1883 `FeedbackResponse`, 558 `EmployeeNLPProfile`
- **Yeni Script**: `scripts/patch_nlp_raw_analysis.py` — 1791 `FeedbackNLPAnalysis` kaydına profil bazlı `raw_analysis` JSON eklendi
  - high: flight_risk_score=2.1, complaint_topics=[]
  - medium: flight_risk_score=3.8, complaint_topics=[inisiyatif eksikliği, dokümantasyon gecikmesi]
  - medium_risk: flight_risk_score=5.5, flight_risk_reasons=[motivasyon düşüşü, yorgunluk belirtileri]
  - atrisk: flight_risk_score=8.2, complaint_topics=[tükenmişlik riski, ayrılma sinyali, bağlılık kaybı]

#### Yetenek Dağılımı Grafiği — Gerçek 1-5 Peer Skorları
- **Sorun**: `EmployeeAnalysisView.vue` BarChart, `EmployeeNLPProfile` üzerindeki 0-1 normalize NLP skorlarını gösteriyordu; etiket "1-5 Puan" yazıyordu — yanıltıcı veri.
- **Kök Neden**: `build_employee_360_summary_report()` metrics alanında `avg_motivation_score`, `avg_psychological_safety_score`, `avg_collaboration_score` (hepsi 0-1 NLP sentiment skoru) dönüyordu.
- **Backend Düzeltmesi** (`app/services/nlp_service.py` ~852. satır): `FeedbackResponse.score_communication`, `score_teamwork`, `score_leadership`, `score_technical` alanlarının bu çalışana ait ortalamaları hesaplanıp `skill_scores` listesi olarak response'a eklendi.
- **Backend Şema** (`app/schemas/feedbacks.py`): `SkillScore(label, value)` modeli + `Employee360SummaryReportResponse.skill_scores: Optional[List[SkillScore]]` eklendi — yoksa Pydantic `response_model` tarafından kırpılıyordu.
- **Frontend Tip** (`services/api/feedback.api.ts`): `SkillScore` interface + `Employee360SummaryReportResponse.skill_scores` eklendi.
- **Frontend Görünüm** (`views/manager/EmployeeAnalysisView.vue`): `skillScoreLabels` / `skillScoreValues` computed'ları eklendi; grafik `skill_scores` varsa bunları (gerçek 1-5), yoksa eski NLP metriklerine fallback yapıyor.
- **Örnek çıktı**: İletişim=3.60, Takım Çalışması=3.62, Liderlik=3.46, Teknik Beceri=3.80

#### RAG / Yapay Zeka Bellek Analizi — Durum Tespiti
- `FeedbackMemoryChunk` tablosu boş (0 kayıt) çünkü seed scriptleri bu tabloyu doldurmaz — sadece gerçek kullanıcı feedback gönderince `RAGService.store_feedback_as_memory()` çağrılır.
- RAG raporu `model_provider: "heuristic"` (deterministik fallback) döndürüyor — LLM/Gemini bu servis için ayrıca yapılandırılmamış.
- `retrieved_memory_count: 0` tamamen doğru davranış — beklenen.

#### Personel Yönetimi — Bütünleşik Skor Sayfası ★ BÜYÜK
**Değiştirilen Dosya**: `propel-frontend/src/views/admin/EmployeeManagement.vue` (tamamen yeniden yazıldı)

**Veri Kaynakları** (3 paralel API çağrısı):
- `GET /admin/uploads/ai-insights` → `employee_table`: 61 çalışan × {code, name, dept, team, perf_drop, burnout, resignation, high_risk, composite}
- `GET /employees/` → `external_employee_code → db_id` haritası
- `GET /surveys/` → per employee: avg_score (0-5), avg_ars (0-1)

**Genel Skor Formülü** (0-100, yüksek = sağlıklı):
```
ml_sağlık    = 100 - composite           // ML riski ters çevir
nabız_sağlık = (avg_score / 5) * 100     // motivasyon skoru 0-5 → 0-100
nabız_tutma  = (1 - avg_ars) * 100       // ARS riski ters çevir
genel_skor   = ml_sağlık * 0.50 + (nabız_sağlık * 0.60 + nabız_tutma * 0.40) * 0.50
```
- Nabız verisi yoksa: `genel_skor = ml_sağlık`
- 360° sütunu şimdilik "Yakında" placeholder — backend entegrasyonu sonrası ağırlıklar dağıtılacak

**Yeni UI Bileşenleri**:
1. **4 KPI Kartı**: Toplam Personel · Ort. Genel Skor · Yüksek Risk (<40) · Güvenli Bölge (≥70)
2. **Top 5 / Bottom 5 Panelleri**: Yeşil (en yüksek) + Kırmızı (en düşük) skor bandında 5'er kart
3. **Gemini Yorumu Paneli** (koyu mor/indigo gradient):
   - Gemini API çalışıyorsa gerçek 3 bölümlü rapor
   - Gemini yoksa `stats` verisinden deterministik özet (total/high_risk/avg_composite) + bottom-5 isimlerini içeren 4 madde aksiyon listesi
   - "Yeniden Yorumla" butonu
4. **Skor Kaynağı Açıklama Şeridi**: ML %50 / Nabız %30 / Tutma %20 / 360° "Yakında"
5. **Tam Tablo** (12/sayfa):
   - Personel (avatar, isim, takım)
   - Departman rozeti
   - ML Hedefleri (4 mini progress bar: PD/Tükenmişlik/İstifa/Yüksek Risk)
   - Nabız Anketi (motivasyon X.X/5 + ARS %)
   - 360° sütunu (placeholder)
   - Genel Skor (büyük rakam + bar + Güvenli/Orta Risk/Yüksek Risk etiketi)
   - İşlemler (detay linki)
6. **Filtreler**: Arama · Departman dropdown · Risk seviyesi (Yüksek/Orta/Güvenli) · Sıralama (Genel ↑↓ / ML / Nabız / İsim)

**Renk kodlaması**:
- ML bar: ≥70% → Kırmızı, 40-69% → Amber, <40% → Yeşil (risk yüksekse kırmızı)
- Genel skor: ≥70 → Yeşil, 40-69 → Amber, <40 → Kırmızı

**Önemli Teknik Not**: IDE (VS Code/Volar) `vue`, `vue-router`, `@heroicons` modüllerini çözümleyemiyor çünkü `node_modules` sadece Docker container içinde var, yerel makinede değil. Bu tek `2307` hatası bütün script type environment'ını bozar ve cascade `7006` (implicit any) + `2365` (`+` operator) hataları üretir. Vite container'da bunları görmez — HMR temiz derledi.

---

### 2026-06-06 Personel Yönetimi — Top 5 / Bottom 5 Aksiyonlar Modalları ★

**Değiştirilen Dosya**: `propel-frontend/src/views/admin/EmployeeManagement.vue`

#### Top 5 "Aksiyonlar" Butonu ve Modalı
- "En Yüksek Skor — Top 5" panel başlığının yanına yeşil **Aksiyonlar** butonu eklendi (`StarIcon`)
- Modal iki ana bölümden oluşuyor:
  1. **Ödüllendirme Önerileri** — 6 kart (Performans Sertifikası, Ekstra İzin Günü, Mentorluk Fırsatı, Kariyer Gelişim Bütçesi, Şirket Geneli Takdir, Performans Primi)
  2. **Hayır Kurumu Bağışı** — Her Top 5 çalışanı için ayrı blok; 9 kurumdan biri seçiliyor:
     - LÖSEV, TEMA Vakfı, Darüşşafaka Cemiyeti, Türk Eğitim Vakfı (TEV), Türk Kızılay, UNICEF Türkiye, AHBAP Derneği, Mehmetçik Vakfı, WWF-Türkiye
     - Seçim yapıldıkça "Seçildi" rozeti + "Bağış Özeti" paneli beliriyor
     - Seçimler `selectedCharities` reactive map'inde tutulur (code → charity name)
  3. **Desteklenen Kurumlar** bilgi kartları — 9 kurumun açıklaması grid formatında

#### Bottom 5 "Aksiyonlar" Butonu ve Modalı
- "Dikkat Gerektiren — Bottom 5" panel başlığının yanına kırmızı **Aksiyonlar** butonu eklendi (`ClipboardDocumentListIcon`)
- Her çalışan için:
  - Risk sinyali rozetleri: PD%, Tükenmişlik%, İstifa%, ARS%, Motivasyon renk kodlu
  - `bottomActionsForEmployee()` fonksiyonu → ML değerlerine göre **otomatik öncelik sıralamalı aksiyon listesi** (Acil / Yüksek / Orta / Düşük)
  - Acil: `high_risk ≥ 50` → birebir yönetici görüşmesi; Yüksek: `perf_drop ≥ 50`, `burnout ≥ 40`, `resignation ≥ 40`, `ARS ≥ 0.6`; Orta/Düşük: IDP, peer buddy, kısa vadeli hedef
  - Alt kısımda genel uygulama rehberi (Acil = 1 hafta, İK kaydı, 4 haftalık izleme)

#### Teknik Detaylar
- `showTopActionsModal` / `showBottomActionsModal` — ref boolean
- `selectedCharities` — `Record<string, string>` (employee code → seçilen kurum)
- `charities` / `rewardSuggestions` — reactive olmayan sabit array'ler
- `Teleport to="body"` + `Transition name="modal-fade"` — backdrop blur, scale+fade animasyonu
- Yeni heroicon import'ları: `StarIcon`, `ClipboardDocumentListIcon`, `XMarkIcon`
- IDE'de `2307` (vue/vue-router/heroicons bulunamıyor) hataları beklenen — `node_modules` sadece Docker container'ında mevcut

---

## Sonraki Adımlar / Roadmap

- [x] Satış departmanı frontend dashboard'u (Vue 3) — employee/manager/admin görünümleri
- [x] Satış çalışanı dashboard KPI kartlarını backend'e bağla
- [x] Tüm 4 ML hedefi eğitilebilir hale getirildi (satış + yazılım)
- [x] Türkçe karakter düzeltmesi (tüm isimler)
- [x] Hatice Yıldırım — tek satış müdürü (SA-031, dataset'e eklendi)
- [x] Satış çalışanı login redirect düzeltmesi (router guard async + user restore)
- [x] Satış departmanı 360° feedback seed + NLP profil oluşturma (92 kayıt, 31 çalışan)
- [x] Satış yöneticisi 360° feedback view (SalesFeedbackView.vue) — emerald tema
- [x] DepartmentAnalysisView + EmployeeAnalysisView mojibake encoding düzeltmesi
- [x] Admin panel mock verileri gerçek backend'e bağlandı (EmployeeDetails, AdminDashboard, DataManagement)
- [x] Şablon indirme endpoint'i eklendi (GET /admin/uploads/template)
- [x] Personel Yönetimi: ML performans skoru + risk seviyesi (flight-risk endpoint'e bağlandı)
- [x] Yapay Zeka İçgörüleri: ML + Gemini AI entegrasyonu (AIInsights.vue tamamen yeniden yazıldı)
- [x] Gemini API anahtarı entegre edildi (gemini-2.5-flash)
- [x] Anket Sonuçları: departman filtresi + Gemini yorum paneli (gerçek q4/q5/q6 yanıtları)
- [x] Admin menüden "Satış ML Analizi" kaldırıldı
- [x] Satış ML analizi — 4 hedef tablosu, risk olasılığı, bileşik skor, LLM ayrımı
- [x] Yazılım ML analizi sayfası eklendi (SoftwareAnalyticsView.vue) — satışla aynı yapı
- [x] Gerçekçi dataset üretici scriptler (v3 satış, v2 yazılım) — bireysel profil + stokastik etiket
- [x] bulk-all-targets endpoint'leri (satış + yazılım) — 4 hedef tek çağrıda
- [x] AIInsights.vue yeniden tasarlandı — risk açıklamaları + grafikler + 4 hedef tablo
- [x] 360° Feedback kişi seç dropdown düzeltmesi (admin için catch fallback + flat sorted list)
- [x] 360° Feedback gerçekçi seed dataseti (1883 response, 558 NLPProfile, patch_nlp_raw_analysis)
- [x] Yetenek Dağılımı grafiği — gerçek 1-5 peer skorları (FeedbackResponse ortalamalar, skill_scores alanı)
- [x] Personel Yönetimi tamamen yenilendi — ML + Nabız Anketi bütünleşik skor, Top5/Bottom5, Gemini paneli
- [x] Personel Yönetimi Top 5 Aksiyonlar — ödüllendirme önerileri + 9 hayır kurumu bağış seçimi
- [x] Personel Yönetimi Bottom 5 Aksiyonlar — ML verisi bazlı öncelikli önlemler listesi (Acil/Yüksek/Orta/Düşük)
- [ ] Personel Yönetimi 360° sütunu backend entegrasyonu (per-employee 360 skoru endpoint'i)
- [ ] `app/tests/` dizinine temel pytest test suite'i (hedef: %80 coverage)
- [ ] Playwright kurulumu ile frontend smoke testleri
- [ ] LLM/Gemini endpoint'lerini async/background job olarak ayır (şu an bloklayıcı)
- [ ] Departman Analizi AI Modal → PDF İndir ve Email Gönder backend bağlantısı
- [ ] Yeni departman desteği (İK, Pazarlama): registry + kpi_registry + seed genişletme
- [ ] WebSocket ile gerçek zamanlı bildirimler
- [ ] GDPR/KVKK uyumluluk özellikleri
- Kalici not: AGENTS.MD'ye eklenen her calisma ozeti, kalinan nokta ve sonraki adim CLAUDE.md'ye de ayni sekilde kaydedilecek.

## 2026-06-06 Departman Performansi Gemini Paneli ve Dinamik Risk/Aksiyonlar

- Kullanici Departman Performansi ekranindaki buyuk/statik AI ozet alaninin sayfada gereksiz yer kapladigini, Gemini ile yorumlama deneyiminin sag alt sabit buton/panel olarak calismasini istedi.
- Frontend duzeltmeleri:
  - `ManagerDashboard.vue` icinde ust hibrit saglik kartindaki inline LLM butonu kaldirildi; kullanici sag alttaki sabit `Gemini ile Yorumla` butonuna yonlendirildi.
  - Sag alt Gemini paneli eklendi; panel `use_llm=true` ile ayni hibrit dashboard endpoint'ini cagirir ve KPI/ML + nabiz + 360 skorlarini, kaynak etiketini, model bilgisini, dayanak/risk/aksiyon listelerini gosterir.
  - Alttaki tekrar eden buyuk AI ozet karti kaldirildi; risk gostergeleri ve hizli aksiyonlar iki kolon olarak daha genis alanda gosterildi.
  - `riskIndicatorGroups` artik statik `kritik yok/veri geldikce netlesecek` mesajlari yerine backend `hybrid_insights`, KPI/ML risk sayilari, nabiz attrition/stres, 360 burnout/flight ve veri kapsama oranlarindan dinamik sinyal uretir.
  - `RiskIndicators.vue` bos kategorileri gizler; gercek sinyal yoksa tek veri durumu mesaji gosterir.
- Backend duzeltmesi:
  - `SoftwareMLService._dashboard_ai_summary_prompt()` Gemini prompt'u aksiyonlari departman durumuna gore degistirecek, KPI/ML+nabiz+360 kanitlarina baglayacak ve zayif kaynagi acik soyleyecek sekilde guclendirildi.
- Smoke:
  - Normal dashboard API: `status=success`, `health=50.6`, `risk=49.1`, `insights=1`, `monitoring=4`, `ai_source=deterministic`.
  - Gemini acik dashboard API: `ai_source=gemini`, `ai_model=gemini-2.5-flash-lite`, `fallback=false`, `insights=4`, `recommendations=4`, `monitoring=5`.
- Dogrulama:
  - `python -m py_compile propel-backend/app/services/software_ml_service.py` basarili.
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` ve `docker restart propel_frontend` calistirildi.

## Sonraki Adim

- Departman Performansi sayfasinda Gemini butonu sadece kullanici istediginde LLM maliyetini tetikler; risk ve hizli aksiyonlar varsayilan durumda backend hibrit sinyallerinden dinamik uretilmelidir.

## 2026-06-05 Ekibim KPI Kolonu Admin ML Risk Skoru Hizalama

- KPI/ML Calisan Analizi ekraninda Canan Dagdelen icin `Risk Skoru=56/100` gorunurken Ekibim sayfasinda KPI kolonunda `59.9/100` gorunmesi incelendi.
- Tespit: KPI/ML ekrani admin ML bulk prediction `risk_score` alanini, Ekibim ise eski KPI performans skorunu kullaniyordu; bu nedenle iki deger ayni metrik degildi.
- Backend:
  - `EmployeeService.get_team_health()` current admin software ensemble modelini bulup bulk prediction sonucunu alacak sekilde guncellendi.
  - Calisan eslestirmesi `external_employee_code` (`SE-001`) ve isim uzerinden yapildi.
  - TeamHealth member alanlarina `kpi_band`, `kpi_confidence`, `kpi_top_driver`, `kpi_source` eklendi.
  - `kpi_score` artik admin ML `risk_score` olarak doner.
- Frontend:
  - `TeamManagement.vue` tablo basligi `KPI/ML Risk` olarak guncellendi.
  - KPI/ML alt satiri model bandi ve ana driver'i gosterir.
- Smoke:
  - Canan Dagdelen icin KPI/ML `ml_risk_score=56`, Ekibim `team_kpi_score=56.0`, `team_kpi_source=admin_software_ml_bulk`.
- Dogrulama:
  - `python -m py_compile propel-backend/app/schemas/employee.py propel-backend/app/services/employee_service.py` basarili.
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` ve `docker restart propel_frontend` calistirildi.

## 2026-06-05 Ekibim Nabiz Olcegi Departman Performansi ile Hizalama

- Ekibim Nabiz kolonunun Departman Performansi `Insan Sagligi Sinyalleri (Nabiz)` kartiyla ayni cevaplardan gelip gelmedigi incelendi.
- Tespit:
  - Iki ekran da `survey_responses` tablosunda `survey_type='weekly_pulse'` kayitlarini kullanir.
  - Departman Performansi 100'luk skala, Ekibim ise bazi yerlerde 5'lik skala gosteriyordu.
- Duzeltme:
  - Ekibim `Nabiz Ortalamasi` ust karti primary value olarak `66.0/100` gibi 100'luk skala dondurur; hint icinde `3.3/5` saklanir.
  - Ekibim tablo Nabiz sutunu kisi pulse skorunu `/100`, alt satirda `/5`, MTE etiketi ve `Ayrilma riski x/100` olarak gosterir.
- Smoke:
  - Departman Performansi weekly pulse: `motivationAverage=66.0`, `stressLevel=49.0`, `attritionRisk=49.0`, `responseCount=30`.
  - Ekibim team-health: `pulse_average=66.0/100`, hint `Son weekly pulse ortalamasi: 3.3/5`, `pulse_response_count=30`.
- Dogrulama:
  - `python -m py_compile propel-backend/app/services/employee_service.py` basarili.
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` ve `docker restart propel_frontend` calistirildi.

## 2026-06-05 Satis Manager ML Egitim Kontrollerini Admin Kaynagina Alma

- Satis manager KPI/ML ekraninda model egitiminin admin tarafinda kalmasi gerektigi icin manager tarafindaki egitim/model durumu kontrolleri incelendi.
- Tespit:
  - Satis manager sidebar'inda `Model Durumu` linki `/manager/sales-analytics` route'una gidiyordu.
  - `/manager/sales-analytics` adminle ayni `SalesAnalyticsView.vue` bilesenini kullandigi icin manager tarafinda `Model Egit` gorunebiliyordu.
  - `/manager/sales-kpi-analysis` icinde ayrica `Model Egit` butonu vardi.
- Frontend:
  - Satis manager sidebar'indan `Model Durumu` kaldirildi.
  - `/manager/sales-analytics` manager icin `/manager/sales-kpi-analysis?section=department` sayfasina redirect edildi.
  - `SalesAnalyticsView.vue` icindeki `Model Egit` butonu sadece admin rolunde gorunecek sekilde sinirlandi.
  - `SalesManagerAnalyticsView.vue` icindeki `Model Egit` butonu kaldirildi; panel `Admin ML Kaynagi` olarak guncellendi.
  - Tahmin/toplu tarama butonlari sadece secili target icin admin current model varsa aktif olur.
  - Dataset secimi current egitilmis modeli olan dataset'i otomatik secer.
- Smoke:
  - Satis model state kontrolunde 4 hedef de current dataset icin `stacking_lgbm_xgb_rf_lr`, train/test `1240/372`.
- Dogrulama:
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_frontend` calistirildi.

## 2026-06-06 Satis Takim Analizi Admin ML Sonuclari ile Hizalama

- Satis manager KPI/ML `Takim Analizi` sayfasi yazilim manager deneyimine benzer, ancak satis departmani bilesenlerine gore yeniden duzenlendi.
- Backend:
  - `SalesMLService._team_analytics()` artik `risk_score` ve `trend_values` yaninda `employee_count`, `high_risk_count`, `medium_risk_count`, `low_risk_count`, `high_risk_rate`, `monitored_count`, `top_reason`, `role_counts`, `sales_pressure_score`, `pipeline_pressure_score` alanlarini da uretir.
  - Takim `top_reason`, admin artifact `top_features` + son donem feature satirlari uzerinden hesaplanir.
  - 6 aylik takim trendi admin stacking ensemble bulk prediction skorlarinin ay bazli ortalamasindan gelir.
- Frontend:
  - `SalesManagerAnalyticsView.vue` icinde yeni satis `Takim Analizi` dashboard'u eklendi.
  - Sol takim listesi, gradient takim header'i, 4 KPI karti, ana neden karti, 6 aylik satis risk trendi SVG grafigi, AI aksiyon paneli, takim yorumu ve `Takim Uyeleri - Detayli Risk Analizi` kartlari eklendi.
  - Kartlar ve grafik `bulkResult.team_analytics` + `bulkResult.items` alanlarindan beslenir; manager tarafinda model egitimi yoktur.
- Smoke:
  - `manager.satis@propel.com`, `upload_id=10`, `Performance_Drop_Target` bulk prediction calisti.
  - Ornek takim: `team=Dogu Anadolu`, `employee_count=7`, `high_risk_count=6`, `risk_score=70`, `top_reason=Tekliften Kazanima Donusum Orani`, `sales_pressure_score=22`, `pipeline_pressure_score=38`, `trend_values=71,75,69,72,72,70`.
- Dogrulama:
  - `python -m py_compile propel-backend/app/services/sales_ml_service.py` basarili.
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` ve `docker restart propel_frontend` calistirildi.

### 2026-06-06 Satis Takim Analizi Route Tazeleme Notu

- Kullanici satis manager `Takim Analizi` ekraninin hala eski gorundugunu bildirdi.
- Kontrol:
  - Frontend container icinde `SalesManagerAnalyticsView.vue` yeni `Satis Takim Analizi` template'ini iceriyor.
  - Vite dev server `http://localhost:5173/src/views/sales/SalesManagerAnalyticsView.vue` modulu uzerinden yeni template'i servis ediyor.
- Duzeltme:
  - Satis manager login/default redirect'i eski `/manager/sales-analytics` yerine dogrudan `/manager/sales-kpi-analysis?section=department` olarak guncellendi.
  - Frontend type-check tekrar calistirildi ve `docker restart propel_frontend` ile container tazelendi.
- Dogrulama:
  - `npm.cmd run type-check` basarili.
  - `python -m py_compile propel-backend/app/services/sales_ml_service.py` basarili.

## 2026-06-06 CLAUDE.md Gunluk Senkronizasyonu

- Kullanici bundan sonra `AGENTS.MD` icine kaydedilen tum calisma gunlugu notlarinin `CLAUDE.md` icine de kaydedilmesini istedi.
- `CLAUDE.md` kalici talimatlarina `AGENTS.MD` ile birlikte `CLAUDE.md` de ayni calisma gunluguyle guncellenecek notu eklendi.
- Bu sohbette eksik kalan Ekibim KPI/Nabiz hizalama, satis manager admin-ML gecisi, Departman Performansi Gemini paneli, Satis Takim Analizi ve route tazeleme notlari `CLAUDE.md` sonuna eklendi.

## Sonraki Adim

- Bundan sonraki her calisma kapanisinda `AGENTS.MD` ve `CLAUDE.md` birlikte guncellenmelidir; biri guncellenip digeri eksik birakilmamalidir.
