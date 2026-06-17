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

## 2026-06-06 Satis Takim Analizi Yazilim Sayfasi Bloklari ile Hizalama

- Kullanici satis manager `Takim Analizi` ekraninda takimlar gorunmesine ragmen yazilim sayfasindaki `Bu Hafta Konusulacak Konular`, `Takim Uyeleri - Detayli Risk Analizi`, `6 Aylik Performans Trendi` gibi manager calisma bloklarinin eksik kaldigini belirtti.
- Frontend duzeltmeleri:
  - `SalesManagerAnalyticsView.vue` satis takim detayina `6 Aylik Performans Trendi` karti eklendi. Bu seri admin ensemble modelinin 6 aylik takim risk trendinden `100 - risk` olarak uretilen performans sagligi sinyalidir.
  - `Bu Hafta Konusulacak Konular` bolumu eklendi; ana driver, pipeline/hedef baskisi ve riskli calisan destek plani satis KPI baglaminda uretilir.
  - `Takim Uyeleri - Detayli Risk Analizi` bolumu bos eslesme durumunda da gorunur ve dataset bolge/takim eslesmesi kontrol mesaji verir.
  - Mevcut AI aksiyon paneli ve uye kartlari admin bulk prediction `team_analytics` + `items` kaynagini kullanmaya devam eder.
- Dogrulama:
  - `npm.cmd run type-check` basarili.
  - `python -m py_compile propel-backend/app/services/sales_ml_service.py` basarili.
  - `docker restart propel_frontend` calistirildi.

## Sonraki Adim

- Satis `Takim Analizi` ekrani artik yazilim manager sayfasindaki ana calisma bolumleriyle uyumlu okunmalidir; sonraki inceleme satis `Calisan Analizi` tarafinda kisi bazli LLM/driver yorumlarinin ayni admin ML kaynagina baglanmasi olabilir.

### 2026-06-06 Satis Takim Uyeleri Eslesme Duzeltmesi

- Kullanici satis `Takim Uyeleri - Detayli Risk Analizi` bolumunde `6 kisi yuksek risk seviyesinde` yazarken `0 kisi listeleniyor` ve `admin bulk prediction sonucunda eslesen calisan bulunamadi` mesaji gorundugunu bildirdi.
- Tespit:
  - `team_analytics` takim adlari dataset tarafindan mojibake/Turkce karakterli geliyordu (`DoÄu Anadolu`, `GÃ¼neydoÄu Anadolu`, `Ä°Ã§ Anadolu`).
  - Kisi kartlari ise DB employee profilinden ASCII takim adlari kullaniyordu (`Dogu Anadolu`, `Guneydogu Anadolu`, `Ic Anadolu`).
  - Frontend birebir string karsilastirdigi icin takim agregasyonu 6 kisi bulsa da kisi listesi 0 gorunuyordu.
- Frontend duzeltmesi:
  - `SalesManagerAnalyticsView.vue` icinde `normalizeSalesTeamKey()` ve `salesItemTeamName()` helper'lari eklendi.
  - `selectedTeamPeople` filtrelemesi artik takim adlarini normalize ederek eslestirir.
  - Rol dagilimi `role_counts` bos gelirse eslesen `selectedTeamPeople` uzerinden hesaplanir.
- Dogrulama:
  - Normalize testi: `DoÄu Anadolu` / `Dogu Anadolu`, `GÃ¼neydoÄu Anadolu` / `Guneydogu Anadolu`, `Ä°Ã§ Anadolu` / `Ic Anadolu` ayni anahtara dustu.
  - `npm.cmd run type-check` basarili.
  - `python -m py_compile propel-backend/app/services/sales_ml_service.py` basarili.
  - `docker restart propel_frontend` calistirildi.

### 2026-06-06 Satis Takim Analizi Sayisal Kaynak Audit'i

- Kullanici satis manager `Takim Analizi` ekranindaki tum sayisal bilgilerin gercekten admin ML sonucundan gelip gelmedigini ve dogru analiz olup olmadigini sordu.
- Tespit:
  - Takim kartlari (`Toplam Kisi`, `Takim Riski`, `Yuksek Riskli`, `Pipeline/Hedef Baskisi`) `bulkResult.team_analytics` alanindan beslenir.
  - `team_analytics` backend `SalesMLService._team_analytics()` icinde admin current artifact ile yapilan bulk prediction skorlarindan ve ayni upload feature satirlarindan uretilir.
  - `6 Aylik Performans Trendi` dogrudan ham ML skoru degil; admin modelinin 6 aylik takim risk trendinden `100 - risk` olarak turetilen performans sagligi sinyalidir.
  - `Bu Hafta Konusulacak Konular` sayisal ML sonucu degil; admin ML driver/risk/pressure degerlerinden uretilen deterministik manager checklist'idir.
  - Kisi kartlarindaki risk skoru frontendde tekrar hesaplanmasin diye `SalesPredictionResponse.risk_score` backend alanina eklendi ve frontend `personRiskScore()` once bu alanı kullanacak sekilde guncellendi.
- Smoke:
  - `upload_id=10`, `Performance_Drop_Target`: `prediction_count=31`.
  - Ilk takim `Doğu Anadolu`: `team_employee_count=7`, `team_high=6`, `team_risk_score=70`, `trend=71,75,69,72,72,70`, `matching_items=7`.
  - Ilk kisi `Nihan Korkmaz`: `risk_score=89`, `predicted_band=1`, `top_driver=Tekliften Kazanima Donusum Orani`.
- Dogrulama:
  - `python -m py_compile propel-backend/app/schemas/analytics.py propel-backend/app/services/sales_ml_service.py` basarili.
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` ve `docker restart propel_frontend` calistirildi.

### 2026-06-06 Satis Konusulacak Konular Dinamiklestirme

- Kullanici `Bu Hafta Konusulacak Konular` bolumunun admin ML driver/risk/pressure degerlerinden uretilen deterministik checklist oldugunu duyunca bunun surekli ayni seyleri yazma riski tasidigini ve degistirilmeli mi diye sordu.
- Karar:
  - Sadece sabit 3 maddelik deterministik checklist manager icin zayif kalir.
  - Otomatik Gemini cagrisi maliyet/gecikme yaratacagi icin deterministik fallback korunmali, fakat kisi/driver/trend/pressure verisine gore dinamiklesmelidir.
- Frontend duzeltmesi:
  - `selectedTeamTalkingPointItems` artik secili takim kisilerini risk skoruna gore siralar, top driver dagilimini sayar, 6 aylik trend farkini ve pipeline/hedef baskisini okur.
  - Checklist sabit 3 madde yerine duruma gore 2-4 madde uretir.
  - Maddelerde en riskli kisiler isimleri ve backend `risk_score` degerleriyle referanslanir; ana driver ve ikinci driver farklilasir.
  - Pipeline maddesi sadece pressure/driver baglami anlamliysa eklenir; trend maddesi belirgin trend farkinda eklenir.
- Dogrulama:
  - `npm.cmd run type-check` basarili.
  - `python -m py_compile propel-backend/app/schemas/analytics.py propel-backend/app/services/sales_ml_service.py` basarili.
  - `docker restart propel_frontend` calistirildi.

### 2026-06-06 Yazilim Calisan Analizi LLM/Fallback Yorum Iyilestirmesi

- Kullanici yazilim KPI/ML `Calisan Analizi` ekraninda secili calisan icin LLM yaniti alinamadigini, yorumun yuzeysel kaldigini ve tum calisanlarda `trend olumsuzlesiyor` gibi benzer/anlasilmaz ifadeler gordugunu belirtti.
- Tespit:
  - Ekrandaki sari uyari Gemini tarafindan gelen `HTTP 429 quota exceeded` hatasiydi; yani LLM provider gecici/kota kaynakli cevap veremedi.
  - Hata mesaji frontendde ham Gemini JSON metni gibi gorunuyordu.
  - LLM fallback metinleri KPI threshold/trend etiketlerini fazla teknik ve tekrarli kullaniyordu.
- Backend duzeltmeleri:
  - `SoftwareNarrativeService._llm_fallback()` artik ham hata yerine kullanici dostu fallback reason doner: Gemini kotasi dolduysa bunu sade soyleyip admin ML + KPI driver kurallariyla analiz uretildigini belirtir.
  - Bireysel deterministic fallback manager summary ve risk yorumlari daha acik hale getirildi.
  - `trend olumsuzlesiyor` gibi ham etiketler `_human_trend_text()` ile `son 4 haftada yon kotulesiyor` gibi daha okunur dile cevrildi.
  - Threshold etiketleri `_human_status_text()` ile manager diline cevrildi.
  - Driver etkisi `_driver_manager_impact()` ile gorev/t teslim/bug/motivasyon/is yuku baglaminda aciklanir.
  - Action plan tekrarlarini azaltmak icin ayni kok nedenleri `_plan_group_key()` ile gruplayip yinelenen aksiyonlar filtrelendi.
- Smoke:
  - `manager.yazilim@propel.com`, `upload_id=6`, `employee_id=6`, `target_column=performance_band`, `use_llm_narrative=true` ile tekil tahmin denendi.
  - Son denemede Gemini cevap verdi (`fallback_reason=null`); onceki ekrandaki hata 429 kota durumundan kaynakliydi.
- Dogrulama:
  - `python -m py_compile propel-backend/app/services/software_narrative_service.py` basarili.
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` calistirildi.

### 2026-06-06 Satis Calisan Analizi Yazilim Gorunumu Uyumu

- Kullanici satis manager KPI/ML `Calisan Analizi` sayfasindaki verilerin admin ekraninda egitilen model sonuclarindan gelip gelmedigini ve yazilim manager `Calisan Analizi` gorunumuyle ayni hizaya getirilmesini istedi.
- Backend guvencesi:
  - `SalesMLService._load_current_artifact_for_upload()` eklendi.
  - `predict_latest_from_upload()` ve `predict_all_from_upload()` artik artifact metadata `upload_id` degeri secili dataset `upload_id` ile eslesmezse 409 doner.
  - `predict_all_targets()` 409 gibi current dataset uyumsuzluklarini yutmaz; yalnizca eksik artifact 404 durumunda ilgili hedefi bos gecebilir.
  - `get_my_performance()` mevcut calisan upload'i ile eslesen Performance_Drop artifact'i yoksa modeli sessizce yok sayar.
- Frontend uyumu:
  - `SalesManagerAnalyticsView.vue` watchlist bolumu yazilim manager ekranindaki duzene yaklastirildi: calisan listesi, risk skoru bar'i, KPI trend, ana sinyal, haftalik odak, sagda secili calisan detay paneli ve oncelikli takip kartlari.
  - Liste satirina tiklayinca `getLatestSalesPrediction()` ile canli tekil satis tahmini cekilir; bulk sonucu ilk secim olarak paneli doldurur.
  - Target degisince eski bulk/tekil tahmin state'i sifirlanir.
  - Arama calisan adi, takim/rol ve external employee code uzerinden calisir.
- Canli smoke:
  - `manager.satis@propel.com` ile API login basarili.
  - `upload_id=10`, `sales_dataset_v3.xlsx`, `Performance_Drop_Target`: current model true, trained_at `2026-06-05T10:27:27.773193+00:00`, weighted_f1 `0.75904`, `prediction_count=31`.
  - Ilk bulk calisani `Burcu Arslan`, `risk_score=91`, `predicted_band=1`.
  - Ortamda tek satis dataset'i oldugu icin 409 mismatch canli tetiklenemedi; kod path'i current artifact upload guard ile kapatildi.
- Dogrulama:
  - Baslangicta ve degisiklik sonrasi `python -m py_compile propel-backend/app/services/sales_ml_service.py propel-backend/app/schemas/analytics.py propel-backend/app/api/routers/analytics.py` basarili.
  - Baslangicta ve degisiklik sonrasi `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` ve `docker restart propel_frontend` calistirildi.
  - In-app Browser iki kez denenmesine ragmen `windows sandbox failed: spawn setup refresh` hatasiyla acilamadi; gorsel browser smoke tamamlanamadi.

### 2026-06-06 Satis Teknik Detaylar Model Denetimi

- Kullanici KPI/ML `Teknik Detaylar` sayfasinin neden gerekli oldugunu ve buraya ne konmasi gerektigini sordu; karar sayfanin kisi risk listesi degil model denetimi/guvenilirlik ekrani olmasi yonunde verildi.
- Frontend duzeltmesi:
  - `SalesManagerAnalyticsView.vue` teknik bolumu yeni `Model Denetimi` yapisina cevrildi.
  - Ana bloklar: `Aktif Model Ozeti`, `Dataset ve Artifact Eslesmesi`, `Target Bazli Model Performansi`, `KPI Driver Ozeti`, `Model Uyarilari`.
  - Ham prediction tablosu ana ekran olmaktan cikarildi ve en altta kapali `details` denetim tablosu olarak birakildi.
  - `technicalAuditCards`, `technicalDriverRows`, `technicalWarnings`, `trainedCurrentTargetCount`, `selectedDataset` computed helper'lari eklendi.
  - Sayfa artik manager'a "kim riskli?" yerine "bu model/dataset sonucu guvenilir mi, hangi driver'lar tahmini tasiyor?" sorusunu cevaplar.
- Dogrulama:
  - `npm.cmd run type-check` basarili.
  - `python -m py_compile propel-backend/app/services/sales_ml_service.py propel-backend/app/schemas/analytics.py propel-backend/app/api/routers/analytics.py` basarili.
  - `docker restart propel_frontend` calistirildi.
  - In-app Browser tekrar denenmesine ragmen `windows sandbox failed: spawn setup refresh` hatasiyla acilamadi; gorsel browser smoke tamamlanamadi.

### 2026-06-06 Yazilim Teknik Detaylar Model Denetimi Duzeltmesi

- Kullanici ekranin hala degismedigini soyledi; tespit edilen sorun onceki degisikligin satis manager teknik sayfasina uygulanmis olmasi, kullanicinin ekran goruntusunun ise `Yazilim` secili `ManagerAnalyticsView.vue` teknik sayfasi olmasiydi.
- Duzeltme:
  - `propel-frontend/src/views/manager/ManagerAnalyticsView.vue` teknik bolumu guncellendi.
  - Eski acik `Teknik detaylari ve kisi bazli tabloyu goster` ham tablo blogu `v-if=false` ile gizlendi.
  - Yeni bloklar eklendi: `Aktif Model Ozeti`, `Dataset ve Artifact Eslesmesi`, `Target Bazli Model Performansi`, `KPI Driver Ozeti`, `Model Uyarilari`.
  - Ham prediction tablosu ana ekran olmaktan cikarilip kapali `details` denetim tablosuna alindi.
  - `softwareTechnicalAuditCards`, `softwareTechnicalDriverRows`, `softwareTechnicalWarnings`, `softwareCurrentTargetCount`, `selectedSoftwareUpload` computed helper'lari eklendi.
  - Teknik detay meta basligi `Model denetimi ve veri kaynagi kontrolu` olarak degistirildi.
- Dogrulama:
  - `npm.cmd run type-check` basarili.
  - `python -m py_compile propel-backend/app/services/sales_ml_service.py propel-backend/app/schemas/analytics.py propel-backend/app/api/routers/analytics.py` basarili.
  - `docker restart propel_frontend` calistirildi.

### 2026-06-06 Klasik 360 Feedback NLP Entegrasyonu

- Kullanici haftalik feedback/nabiz ile klasik 360 feedback ayrimini sordu ve tezde 360 derece feedback icin NLP analizi anlatildigi icin klasik 360 tarafindaki eksikligin hemen kapatilmasini istedi.
- Tespit:
  - Dinamik haftalik feedback (`/api/v1/feedbacks/submit`) zaten `AIService.analyze_weekly_feedback`, `FeedbackNLPAnalysis`, `EmployeeNLPProfile` ve RAG hafiza hattina bagliydi.
  - Klasik 360 feedback (`/api/v1/feedback/`) sadece `Feedback` kaydi olusturuyordu; `NLPService.save_classic_feedback_analysis()` ve `RAGService.upsert_classic_feedback_memory()` hazir olmasina ragmen cagrilmiyordu.
- Duzeltme:
  - `feedback.py` klasik feedback create endpoint'ine `BackgroundTasks` eklendi; her 360 feedback kaydindan sonra `process_classic_feedback_analysis_in_background()` tetikleniyor.
  - `FeedbackService.process_classic_feedback_analysis()` eklendi.
  - Klasik 360 metin alanlari (`strength_text`, `improvement_text`, `general_comment`) tek NLP girdisine donusturuluyor.
  - Mevcut AI analiz kontrati kullaniliyor; sonuc `source_type=classic_feedback` olarak `feedback_nlp_analyses` tablosuna yaziliyor.
  - `feedback.nlp_result`, calisan NLP profili, aylik rozetler ve `feedback_memory_chunks` RAG hafizasi guncelleniyor.
  - `NLPService` 360 calisan/departman ozetleri, NLP chart/deep analysis ve RAG raporlarinda artik sadece `weekly_feedback` degil klasik 360 analizlerini de kapsiyor.
- Canli smoke:
  - `developer1@propel.com` ile API login yapildi.
  - `/api/v1/feedback/` uzerinden Alper Sen icin klasik 360 feedback olusturuldu (`feedback_id=1`, `reviewee_id=408`).
  - DB dogrulamasi: `feedback_nlp_analyses` icinde `source_type=classic_feedback`, `classic_feedback_id=1`, `model_provider=gemini`, `model_name=gemini-2.5-flash-lite`, `sentiment_label=positive`, `has_summary=true`.
  - DB dogrulamasi: `feedback_memory_chunks` icinde `source_type=classic_feedback`, `classic_feedback_id=1`, `embedding_provider=hash`, `embedding_dimension=128`.
  - DB dogrulamasi: `employee_nlp_profiles` icinde `employee_id=408`, `period_year=2026`, `period_month=6`, `period_week=1`, `feedback_count=2`.
  - `manager.yazilim@propel.com` ile `/api/v1/feedbacks/reports/employee/408` cagrildi; rapor `report_summary`, `recommended_action`, 5 metrik ve guclu/risk/destek bolumlerini dondu.
- Dogrulama:
  - Baslangicta `python -m py_compile propel-backend/app/api/routers/feedback.py propel-backend/app/services/feedback_service.py propel-backend/app/services/nlp_service.py propel-backend/app/services/ai_service.py` basarili.
  - Baslangicta `npm.cmd run type-check` basarili.
  - Degisiklik sonrasi ayni backend `py_compile` basarili.
  - Degisiklik sonrasi `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` calistirildi.

### 2026-06-06 Calisan 360 Analizinde Tekrarlayan RAG Metni Duzeltmesi

- Kullanici `Calisan Analizi` ekraninda farkli calisanlarda ayni aylik/RAG metinlerinin gorundugunu, Cenk Uysal ekraninda Alper Sen metninin belirdigini bildirdi.
- Koken neden:
  - DB'de calisan bazli NLP kayitlari dogru filtreleniyordu; Cenk, Asli ve Alper kayitlari kendi `employee_id` degerleriyle duruyordu.
  - Cogu calisanda yalnizca 1 NLP kaydi oldugu icin seed/veri temalari dogal olarak benzerdi.
  - `build_employee_monthly_rag_report()` benzer RAG bellegi 0 olsa bile LLM raporu uretmeye devam ediyordu; bu durumda model onceki/benzer isimli metni karistirabiliyordu.
  - Frontend calisan degistiginde eski monthly/RAG state'ini hemen temizlemiyor ve gec gelen istekler secili calisani ezebiliyordu.
- Duzeltme:
  - `NLPService.build_employee_monthly_rag_report()` icinde `retrieved_memories` bos ise LLM cagrisi kapatildi.
  - Bos RAG bellegi durumunda deterministik, kisi adini backend employee kaydindan alan ve "kisiyi ayirt edecek kadar zengin 360 NLP hafizasi olusmadi" diyen rapor donuyor.
  - Tekil feedbackli calisanlarda yonetici aksiyonu "ek 360 feedback toplayin" olarak veriliyor.
  - `EmployeeAnalysisView.vue` calisan degisiminde `selectedEmployeeReport`, `monthlyDeepAnalysis`, `monthlyRagReport` state'lerini hemen temizliyor.
  - `employeeReportRequestId` ve `monthlyAnalysisRequestId` eklendi; gec gelen eski istekler artik yeni secili calisanin state'ini ezmiyor.
- Canli smoke:
  - `manager.yazilim@propel.com` ile Cenk Uysal (`employee_id=411`), Alper Sen (`408`) ve Asli Cetin (`421`) icin `/monthly-rag` cagrildi.
  - Cenk ve Asli raporlari `model_provider=deterministic`, `retrieved_memory_count=0` ve kendi calisan adlariyla dondu; Alper metni artik Cenk ekranina sizmiyor.
- Dogrulama:
  - `python -m py_compile propel-backend/app/services/nlp_service.py propel-backend/app/api/routers/feedbacks.py` basarili.
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` ve `docker restart propel_frontend` calistirildi.

### 2026-06-06 3 Aylik Kapsamli 360 Feedback/NLP Demo Verisi

- Kullanici 360 derece feedback calisan analizinde `Motivasyon: Stabil`, `Duygu Trendi: Stabil`, `Ayrilma Risk: -/10` gibi zayif/eksik analiz gorundugunu soyledi; her calisana 3 ay boyunca haftada 3 adet cesitli feedback uretmeyi istedi.
- Yeni script:
  - `propel-backend/scripts/seed_demo_360_history.py` eklendi.
  - Varsayilan plan: `--department all --weeks 12 --feedbacks-per-week 3`.
  - Yazilim ve satis departmanlarini otomatik buluyor.
  - Her calisan icin haftada 3 farkli feedback uretir: ayni takim, capraz takim ve manager/upward senaryolari.
  - Konular haftalara yayilir: teslim/planlama, kalite, is birligi, liderlik, gelisim, risk.
  - NLP payload sentetik demo icin dogrudan cesitlendirilir: motivation_score, sentiment_score, flight_risk_score, complaint_topics, praise_topics, support_needs, theme_labels.
  - Her feedback icin `FeedbackResponse`, `FeedbackNLPAnalysis`, `FeedbackMemoryChunk` RAG hafizasi ve haftalik `EmployeeNLPProfile` guncellenir.
  - Reset varsayilan olarak onceki `synthetic_seed_360_history` kayitlarini temizler.
- Analiz duzeltmeleri:
  - `EmployeeMonthlyRAGReportResponse.flight_risk_score` int yerine float kabul edecek sekilde guncellendi; ortalama risk skorlarinda `5.2` gibi degerler 500 hatasi vermiyor.
  - `build_employee_monthly_rag_report()` RAG esigi nedeniyle 0 sonuc alirsa ayni calisan icin `min_score=0.0` fallback retrieval yapar.
  - Synthetic history verisi kullaniliyorsa aylik RAG raporu Gemini/Ollama beklemeden yerel deterministic fallback ile uretilir; ornek 3 calisan sorgusu 888ms civarina indi.
  - Aylik trend hesaplamasi tek tek feedback sirasi yerine haftalik ortalama serisine gore yapiliyor; ay icindeki karisik feedbackler net yukselis/dusus sinyalini bastirmiyor.
- Canli seed:
  - Dry-run: 2 departman, 62 calisan, 2208 planlanan feedback.
  - Gercek run: 2208 eski synthetic history kaydi temizlendi, 2208 yeni feedback/NLP/RAG kaydi yazildi.
  - DB dogrulamasi: `feedback_nlp_analyses` icinde 2208 kayit, 62 calisan, tarih araligi `2026-04-08` - `2026-06-24`.
  - DB dogrulamasi: `feedback_memory_chunks` icinde 2208 RAG hafiza kaydi olustu.
  - API smoke (`manager.yazilim@propel.com`, Haziran 2026): Elif Ozturk ve Alper Sen `motivation_trend_direction=yukselis`; Cenk Uysal, Asli Cetin ve Kaan Oz `dusus`; flight risk skorlari dolu (`4.2`-`5.5` araligi); RAG memory 1-5 arasi donuyor.
- Dogrulama:
  - `python -m py_compile propel-backend/scripts/seed_demo_360_history.py propel-backend/app/services/nlp_service.py propel-backend/app/schemas/feedbacks.py` basarili.
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` calistirildi.

### 2026-06-07 360 Analiz Basliklarinda Kisi Bazli NER/Topic Cesitliligi

- Kullanici `Sikayet Konulari`, `Guclu Alanlar`, `One Cikan Temalar` altinda herkes icin `blokajlarin gec paylasilmasi`, `ekip ici iletisim kopuklugu`, `Backend`, `Mid Backend Engineer` gibi ayni/sinirli ifadelerin gorundugunu soyledi ve bunlarin kisiye verilen feedbacklerden NER/topic extraction mantigiyla gelmesi gerektigini belirtti.
- Tespit:
  - Seed verisi once sinirli `complaint_map/praise_map` listelerinden uretiliyordu; bu yuzden dominant topic secimi ayni basliklara yigiliyordu.
  - `NLPService._analysis_text_blob()` feedback cevap metnini yeterince kullanmiyor, daha cok raw list alanlarina bakiyordu.
  - `top_themes` icine `Backend`, `QA`, `Mid Backend Engineer` gibi entity/rol etiketleri tema gibi girebiliyordu.
- Duzeltme:
  - `seed_demo_360_history.py` icinde `personal_patterns()` eklendi.
  - Yazilim calisanlari artik takim/role gore ayri persona aliyor: Backend -> code review/API, QA -> test otomasyonu/regresyon, DevOps -> deploy/monitoring, Frontend -> arayuz/tasarim, Yonetim -> mentorluk/karar netligi.
  - Satis icin de bolge/role gore musteri takip, CRM, sikayet, quota ve ekip destegi persona setleri eklendi.
  - Feedback metinlerine kisiye ozel guclu alan, sikayet ve tema ifadeleri enjekte edildi.
  - NLP payload icinde `complaint_topics`, `praise_topics`, `key_strengths`, `theme_labels`, `entity_mentions`, `flight_risk_reasons`, `support_needs` kisi personasina gore cesitlendirildi.
  - `NLPService._analysis_text_blob()` artik weekly/classic feedback ham metinlerini de okuyor.
  - `NLPService._distinctive_feedback_phrases()` eklendi; feedback metninden NER/topic benzeri ayirt edici ifadeleri yakalayip aylik basliklarin onune aliyor.
  - `NLPService._filter_topic_items()` eklendi; `Backend`, `Frontend`, `QA`, pozisyon adi ve calisan adi gibi rol/entity etiketlerini tema listesinden filtreliyor.
- Canli seed ve smoke:
  - `docker exec propel_backend python scripts/seed_demo_360_history.py --department all --weeks 12 --feedbacks-per-week 3` calistirildi; 2208 eski synthetic kayit temizlendi, 2208 yeni feedback/NLP/RAG kaydi uretildi.
  - `manager.yazilim@propel.com` ile Haziran 2026 employee monthly-deep smoke:
    - Elif Ozturk: sikayet `blokaj eskalasyonu gecikmesi`, `dokumantasyon eksigi`, `api bagimliligi gec bildirme`; guclu alan `code review sahiplenmesi`, `api entegrasyon takibi`.
    - Alper Sen/Kaan Oz: DevOps odakli `deploy sonrasi takip eksigi`, `alarm onceligi belirsizligi`; guclu alan `deploy sorumlulugu`, `ortam stabilitesi takibi`.
    - Cenk Uysal: QA odakli `test kapsaminda acik`, `regresyon senaryosu gecikmesi`; guclu alan `test otomasyonu disiplini`.
    - Baris Eren: Frontend odakli `arayuz kabul kriteri belirsizligi`, `tasarim revizyonu gecikmesi`; guclu alan `arayuz detay kalitesi`.
  - Tema listelerinde rol/takim etiketi yerine `code review`, `api entegrasyonu`, `deploy stabilitesi`, `test otomasyonu`, `arayuz teslimi`, `mentorluk` gibi konu ifadeleri donuyor.
- Dogrulama:
  - `python -m py_compile propel-backend/scripts/seed_demo_360_history.py propel-backend/app/services/nlp_service.py propel-backend/app/schemas/feedbacks.py` basarili.
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` calistirildi.

### 2026-06-07 Frontend Takiminda Kisi Bazli 360 Baslik Ayrisma Duzeltmesi

- Kullanici ayni takim icindeki Frontend calisanlarinda bile `Sikayet Konulari`, `Guclu Alanlar`, `One Cikan Temalar` basliklarinin ayni kaldigini ve sahte gorundugunu belirtti.
- Tespit:
  - Onceki seed takim/role persona kullaniyordu; bu nedenle ayni Frontend takimindaki calisanlar ayni arayuz/tasarim basliklarina yigiliyordu.
  - Aylik analizde sabit pattern listeleri raw feedback topic'lerinden once baskin cikabiliyordu.
- Duzeltme:
  - `seed_demo_360_history.py` icinde `individual_focus()` eklendi.
  - Frontend calisanlari icin explicit kisi->odak eslemesi yapildi; her Frontend calisaninin ilk sikayet/guclu alan/tema basligi ayriliyor.
  - Ornek bireysel odaklar: `pr dokumantasyonu`, `edge case sahiplenme`, `bagimlilik yonetimi`, `erisilebilirlik`, `kullanici senaryolari`, `refactor kapsami`, `release iletisimi`, `urun analitigi`, `test verisi cesitliligi`.
  - `NLPService._raw_dominant_items()` eklendi; aylik analiz raw `complaint_topics`, `praise_topics`, `key_strengths`, `theme_labels`, `entity_mentions` alanlarini sabit patternlerden once degerlendiriyor.
- Canli smoke:
  - `docker exec propel_backend python scripts/seed_demo_360_history.py --department all --weeks 12 --feedbacks-per-week 3` calistirildi; 2208 eski synthetic kayit temizlendi, 2208 yeni feedback/NLP/RAG kaydi uretildi.
  - `manager.yazilim@propel.com` ile Haziran 2026 Frontend takimi kontrol edildi:
    - Murat Kaya: `acceptance criteria sorularini gec netlestirme` / `pull request aciklama kalitesi` / `pr dokumantasyonu`
    - Zeynep Celik: `edge case senaryolarini sprint sonuna birakma` / `karmasik buglari sade anlatma` / `edge case sahiplenme`
    - Emre Kilic: `bagimli ekiplerden onay beklerken sessiz kalma` / `cross-team bagimlilik takibi` / `bagimlilik yonetimi`
    - Derya Koc: `risk etkisini sayisal olarak ifade etmeme` / `teknik riskleri erken isaretleme` / `erisilebilirlik`
    - Merve Tetik: `happy path disi akislarin gec test edilmesi` / `kullanici senaryosu dusunme` / `kullanici senaryolari`
    - Kerem Tunc: `refactor kapsam sinirini net cizememe` / `refactor firsatlarini yakalama` / `refactor kapsami`
    - Baris Eren: `release etkisini paydaslara gec duyurma` / `release notu hazirlama` / `release iletisimi`
    - Yigit Ari: `olcumleme eventlerini sonradan ekleme` / `analitik event takibi` / `urun analitigi`
    - Deniz Soylu: `mock veri varyasyonlarini sinirli tutma` / `test verisi hazirlama` / `test verisi cesitliligi`
- Dogrulama:
  - `python -m py_compile propel-backend/scripts/seed_demo_360_history.py propel-backend/app/services/nlp_service.py propel-backend/app/schemas/feedbacks.py` basarili.
  - `npm.cmd run type-check` basarili.
### 2026-06-07 Veritabanı ER Diyagramı Dokümantasyonu

- `docs/sekil-3-3-veritabani-er-diyagrami.md` oluşturuldu.
- SQLAlchemy modellerindeki gerçek tablolar ve ilişkiler temel alınarak Mermaid formatında detaylı "Şekil 3.3. Veritabanı Varlık-İlişki (ER) Diyagramı" hazırlandı.
- Diyagram; kullanıcı, çalışan, departman, KPI, nabız anketi, 360 feedback, haftalık feedback, NLP/RAG, toplantı, bildirim ve veri yükleme tablolarını kapsıyor.
- Kod değişikliği yapılmadığı için `py_compile`, frontend type-check veya container restart çalıştırılmadı.

### 2026-06-15 NLP Kullanim Analizi ve Sunum Notlari

- Kullanici projede NLP'nin teknik olarak nasil kullanildigini, hangi dosyalarda oldugunu, sunumda nasil anlatilabilecegini ve analizlerin dogrulugunu sordu.
- Incelenen ana hat:
  - `app/services/ai_service.py`: Gemini/Ollama/fallback uzerinden sentiment, motivasyon, burnout, flight risk, tema, entity, destek ihtiyaci ve yonetici ozeti uretimi.
  - `app/services/feedback_service.py`: haftalik feedback ve klasik 360 feedback sonrasi NLP arka plan islemleri, dusuk kalite ve karsilikli puan bias kontrolleri.
  - `app/services/nlp_service.py`: NLP sonuc kaydi, calisan profili, departman ozeti, chart, aylik deep analysis ve RAG raporlari.
  - `app/services/rag_service.py` ve `app/db/models/rag.py`: feedback metinlerinin embedding hafizasi.
  - `app/db/models/nlp.py`: `FeedbackNLPAnalysis` ve `EmployeeNLPProfile` kalici NLP tablolari.
  - Frontend: `FeedbackView.vue`, `DepartmentAnalysisView.vue`, `SalesFeedbackView.vue`, `ManagerDashboard.vue`, `TeamManagement.vue`.
- Tespit:
  - NLP sadece metin ozetleme degil; sentiment/risk skorlari, tema cikarma, kalite sinyali, profil agregasyonu ve RAG hafizasi olarak kullaniliyor.
  - Benchmark raporunda heuristik modda 50 ornekte exact match %68; sentiment %86, burnout %94, flight risk %84 dogruluk goruluyor. Bu nedenle analizler demo/karar-destek icin anlamli, fakat tek basina kesin IK karari olarak pazarlanmamali.
- Kod degisikligi yapilmadi; `py_compile`, `npm.cmd run type-check` veya container restart calistirilmadi.

### 2026-06-15 NLP Embedding, Confidence ve Insan Onayi Iyilestirmesi

- Kullanici NLP analizleri icin hash embedding yerine gercek embedding, risklerde kategori + sayisal confidence ve insan onayi/karar destek uyarisi istedi.
- Backend:
  - `RAGService.generate_embedding()` provider katmani genisletildi; `hash` fallback korunarak `gemini`, `openai`, `sentence_transformer`/`local` ve `auto` secenekleri eklendi.
  - Yeni config alanlari: `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`, `SENTENCE_TRANSFORMER_MODEL`.
  - Local sentence-transformer modeli servis icinde cache'lendi; paket/model yoksa servis hash fallback'e dusuyor.
  - `FeedbackNLPAnalysisResponse` ve `EmployeeNLPProfileResponse` icin `burnout_risk_confidence` ve `flight_risk_confidence` eklendi; DB migration gerektirmeden model property'lerinden turetiliyor.
  - Team health payload'una feedback flight/burnout risk confidence alanlari eklendi.
  - 360 summary metric payload'larinda risk metrikleri icin `confidence` tasinmaya baslandi.
- Frontend:
  - `FeedbackView.vue` NLP kartinda flight/burnout risk confidence yuzdeleri gosterildi.
  - NLP sonucunun otomatik uretilmis karar destek onerisi oldugu ve yonetici onayi gerektirdigi uyarisi eklendi.
  - Feedback/employee API tipleri yeni confidence alanlariyla guncellendi.
- Dogrulama:
  - Kod degisikligi oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Kod degisikligi sonrasi `python -m py_compile propel-backend\app\core\config.py propel-backend\app\services\rag_service.py propel-backend\app\db\models\nlp.py propel-backend\app\schemas\nlp.py propel-backend\app\schemas\feedbacks.py propel-backend\app\schemas\employee.py propel-backend\app\services\employee_service.py propel-backend\app\services\nlp_service.py` basarili.
  - Kod degisikligi sonrasi `npm.cmd run type-check` basarili.
  - Container runtime smoke ve `docker restart propel_backend` denendi ancak Docker Desktop daemon pipe bulunamadigi icin calistirilamadi.

### 2026-06-15 NLP Insan Onayi Faz 2 - Kalici Yonetici Incelemesi

- Kullanici ikinci faza gecilmesini istedi; ilk fazdaki uyari/karar destek notu kalici DB/API akisi haline getirildi.
- Backend:
  - `EmployeeNLPReview` modeli ve `NLPReviewStatus` enum'u eklendi.
  - Review kaydi calisan + NLP donemi bazinda unique tutuluyor; status degerleri `pending`, `approved`, `false_alarm`, `follow_up_required`.
  - `GET /feedbacks/nlp/employee/{employee_id}/review` review durumunu okuyor.
  - `PUT /feedbacks/nlp/employee/{employee_id}/review` admin/yonetici icin review upsert ediyor; departman yoneticisi yalnizca kendi departmanindaki calisan icin yazabiliyor.
  - `WeeklyNLPInsightResponse` icine `human_review` eklendi.
  - `employees/team-health` payload'una `nlp_review_status`, `nlp_review_note`, `nlp_reviewed_at`, `nlp_reviewer_name` alanlari eklendi.
- Frontend:
  - `TeamManagement.vue` 360/NLP hucresinde review rozeti ve `Onayla`, `Takip`, `Yanlis alarm` aksiyonlari eklendi.
  - Aksiyonlar `PUT /feedbacks/nlp/employee/{id}/review` ile DB'ye yaziyor ve ardindan team-health tekrar yukleniyor.
  - Feedback/employee API tipleri review status ve payload alanlariyla guncellendi.
- Dogrulama:
  - Kod degisikligi oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Kod degisikligi sonrasi `python -m py_compile propel-backend\app\db\models\nlp.py propel-backend\app\db\models\__init__.py propel-backend\app\schemas\nlp.py propel-backend\app\schemas\feedbacks.py propel-backend\app\schemas\employee.py propel-backend\app\services\nlp_service.py propel-backend\app\services\employee_service.py propel-backend\app\api\routers\feedbacks.py` basarili.
  - Kod degisikligi sonrasi `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` tekrar denendi ancak Docker Desktop daemon pipe bulunamadigi icin container restart/runtime smoke calistirilamadi.

### 2026-06-15 NLP Aciklanabilir Risk Driverlari - Faz 3

- Kullanici raporlarda sadece `Burnout Risk = High` yazmasi yerine `neden high?` sorusunu cevaplayan driver ve kanit listesi istedi.
- Backend:
  - `RiskDriver` schema'si eklendi; risk metrikleri artik `drivers` listesi tasiyabiliyor.
  - `NLPService._burnout_risk_drivers()` eklendi.
  - Driverlar deterministik olarak mevcut NLP verisinden uretiliyor:
    - haftalik motivasyon serisi dususu,
    - psikolojik guven serisi dususu,
    - tekrar eden is yuku/destek/sikayet temalari,
    - tekil analizlerdeki explicit high burnout sinyalleri.
  - `build_employee_360_summary_report()` icinde `Burnout Risk` metric'i driver listesi ve confidence ile donuyor.
  - `build_employee_monthly_deep_analysis()` icinde `burnout_risk_level`, `burnout_risk_drivers`, `burnout_risk_evidence` alanlari donuyor.
- Frontend:
  - `EmployeeAnalysisView.vue` aylik derin analiz bolumune `Burnout Risk Drivers` paneli eklendi.
  - Panel, ornek olarak `Motivasyon 4.2 -> 2.7 dustu` veya tekrar eden tema kanitlarini kartlar halinde gosteriyor.
  - API tipleri `RiskDriver`, metric `drivers` ve monthly deep burnout alanlariyla guncellendi.
- Dogrulama:
  - Kod degisikligi oncesi `py_compile` ve `npm.cmd run type-check` basarili.
  - Kod degisikligi sonrasi `python -m py_compile propel-backend\app\services\nlp_service.py propel-backend\app\schemas\feedbacks.py` basarili.
  - Kod degisikligi sonrasi `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` denendi ancak Docker Desktop daemon pipe bulunamadigi icin container restart/runtime smoke calistirilamadi.

### 2026-06-15 Calisan Analizi Liste ve KPI Gorunumu Duzeltmesi

- Kullanici 360 Calisan Raporu ekraninda `Calisan Bulunamadi` gorundugunu ve KPI analizlerinin de gelmedigini bildirdi.
- Tespit:
  - `EmployeeAnalysisView.vue` calisan listesini yalnizca `feedback/candidates` endpoint'inden cekiyordu; bu endpoint feedback adayi amacli oldugu icin bazi yonetici/departman durumlarinda bos donebiliyor.
  - Ekran metni ve veri modeli yalnizca 360 feedback/NLP raporuna odakliydi; KPI performans ozeti bu sayfada gosterilmiyordu.
  - Backend restart sonrasi `app.schemas.feedbacks` import'u `NameError: RiskDriver is not defined` hatasiyla dusuyordu; `RiskDriver`, `SummaryMetric` icinde kullanilmadan once tanimlanacak sekilde siralandi.
- Frontend:
  - Calisan listesi birincil olarak `employeeApi.getEmployees()` ile gercek calisan endpoint'inden cekilmeye baslandi; hata durumunda eski `feedbackApi.getFeedbackCandidates()` fallback olarak korundu.
  - Liste filtrelemesi `user.role` eksik oldugunda calisanlari yanlislikla dislamayacak hale getirildi.
  - Departman, calisan ve KPI summary yukleme hatlari ayrildi; departman/analytics hatasi calisan listesini sifirlamiyor.
  - `analyticsApi.getPerformanceSummary()` ayni yukleme akisine eklendi.
  - Secili calisan icin `KPI / ML Performans Ozeti` karti eklendi; KPI skoru, trend, kayit sayisi, son donem ve durum rozeti gosteriliyor.
  - Calisan icin KPI kaydi yoksa ekranda acik bir bos durum mesaji gosteriliyor.
- Dogrulama:
  - `npm.cmd run type-check` basarili.
  - `python -m py_compile propel-backend\app\services\nlp_service.py propel-backend\app\schemas\feedbacks.py` basarili.
  - `git diff --check` whitespace hatasi vermedi; yalnizca mevcut Windows CRLF uyarilari goruldu.
  - `docker restart propel_frontend` ve `docker restart propel_backend` basarili.
  - Container icinde `python -c "import app.schemas.feedbacks"` basarili.
  - Canli API smoke: `manager.yazilim@propel.com` ile `/employees/` 31 kayit, `/analytics/performance/summary` 30 KPI calisan kaydi dondurdu.
  - Browser smoke: `/manager/feedback-reports/employees` ekraninda `30 calisan listeleniyor`, `Calisan Bulunamadi=false`, `KPI / ML Performans Ozeti=true`.

### 2026-06-15 Calisan Analizi Kisisel Yonetici Ozeti

- Kullanici haftalik yonetici ozetinde tum calisanlar icin ayni pozitif cumlenin gorundugunu ve sayfada gercek dataya dayali, kisiye ozel analiz istedigini bildirdi.
- Tespit:
  - `build_employee_360_summary_report()` rapor ozetinde `profile.manager_summary` alanini oncelikli kullaniyordu.
  - Bu alan daha onceki NLP/seed akislariyla bircok calisan icin benzer sablon cumleye donusmustu; frontend de bu alanı dogrudan bastigi icin ekranda kisi adi degisen ayni yorum gorunuyordu.
- Backend:
  - `NLPService._latest_kpi_context()` eklendi; calisanin son KPI kayitlarindan KPI skoru, trend, son donem, kayit sayisi ve en guclu KPI sinyali hesaplanıyor.
  - `NLPService._employee_manager_summary()` eklendi; ozet artik her istekte mevcut KPI, 360/NLP profil, risk confidence, burnout driver, rozet ve son feedback kanitlarindan deterministik olarak yeniden uretiliyor.
  - Eski `profile.manager_summary` ana rapor ozeti olarak kullanilmiyor; seed kaynakli tekrar eden cumleler ekrana tasinmiyor.
  - Response `sections` icine `Yonetici Kanitlari` eklendi.
- Frontend:
  - `EmployeeAnalysisView.vue` haftalik yonetici ozeti kutusuna `Veriye Dayali Kanitlar` paneli eklendi.
  - Panel KPI skoru/trend, motivasyon, psikolojik guven, is birligi, guclu yon/risk/destek kanitlarini madde madde gosteriyor.
- Dogrulama:
  - `python -m py_compile propel-backend\app\services\nlp_service.py propel-backend\app\schemas\feedbacks.py` basarili.
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` ve `docker restart propel_frontend` basarili.
  - Container icinde `python -c "import app.services.nlp_service"` basarili.
  - Canli API smoke: Canan, Zeynep ve Burak rapor ozetleri farkli dondu; Burak icin `KPI skoru 58.6/100, +0.5 trend`, Zeynep icin `KPI skoru 56.0/100, -2.7 trend` gibi kisiye ozel kanitlar goruldu.

### 2026-06-15 KPI ML Ekrani Durum Karti Tutarliligi

- Kullanici KPI & ML Analizi ekraninda ustte `Veri bekleniyor` yazarken altta departman sagligi, KPI/ML skoru, 360 kapsamı gibi sayisal verilerin gorunmesini celiskili buldu.
- Tespit:
  - Ust metrik grid'i `overview.metrics` fallback'inden besleniyordu.
  - Alttaki `Birlesik Departman ML Analizi` ise `departmentDashboard` endpoint'inden dolu veri gosteriyordu.
  - Bu nedenle farkli kaynaklar ayni sayfada celiskili durum mesaji uretiyordu.
- Frontend:
  - `ManagerAnalyticsView.vue` icin `topStatusCards` computed'i eklendi.
  - `departmentDashboard` doluysa ust kartlar artik dashboard ile ayni kaynaktan konusuyor:
    - `Durum: Analiz hazir`
    - KPI/ML kapsami
    - Nabiz kapsami
    - 360 kapsami
    - Veri guveni
  - Dashboard yok ama KPI summary varsa `KPI verisi hazir` mesaji gosteriliyor.
  - Gercekten veri yoksa eski overview fallback metrikleri korunuyor.
- Dogrulama:
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_frontend` basarili.
  - `git diff --check` whitespace hatasi vermedi; yalnizca mevcut Windows CRLF uyarilari goruldu.

### 2026-06-15 Demo Haftalik Nabiz Seed

- Kullanici demo haftasi icin eksik haftalik nabiz verilerinin sahte/gercekci yanitlarla tamamlanmasini istedi.
- DB veri ekleme:
  - `2026-06-15` tarihli `weekly_pulse` kayitlari olusturuldu.
  - Mevcut kayitlar ezilmeden, yalnizca bu haftada kaydi olmayan calisanlara eklendi.
  - Toplam 60 calisan icin kayit eklendi: 30 Yazilim, 30 Satis.
  - Her kayitta `score`, `raw_data.q1-q6`, `mte_score`, `ars_score` alanlari dolduruldu.
  - Cevaplar ekip/rol/employee id bazli deterministik ve farkli olacak sekilde uretildi; `raw_data.demo_seed=true` ile isaretlendi.
- Ek duzeltme:
  - Software dashboard coverage yuzdeleri 100 ustune cikabiliyordu (`360 Kapsami %103`, `Veri Guveni %100.8`).
  - `SoftwareMLService._dashboard_coverage()` icinde KPI, nabiz, 360 ve confidence yuzdeleri `0-100` araligina clamp edildi.
- Dogrulama:
  - DB smoke: `2026-06-15` icin 60 pulse kaydi, 60 tekil calisan, ortalama skor 3.93/5.
  - Yazilim dashboard API: `pulse_response_count=30`, `pulse_employee_count=30`, `pulse_percentage=100.0`.
  - Yazilim dashboard API: `feedback_percentage=100.0`, `confidence_score=100.0`.
  - `python -m py_compile propel-backend\app\services\software_ml_service.py` basarili.
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` basarili.

### 2026-06-15 KPI ML Yonetici Ozeti Dili

- Kullanici KPI & ML dashboard yonetici ozeti bolumunde `Deterministic` etiketinin ve `backend kural bazli analiz katmani` ifadesinin sacma/teknik gorundugunu belirtti.
- Backend:
  - `SoftwareMLService._dashboard_ai_summary_fallback()` yonetici diliyle yeniden duzenlendi.
  - Summary artik teknik kaynak aciklamasi yerine karar destek yorumu veriyor:
    - departman sagligi,
    - KPI/ML performansi,
    - insan sagligi,
    - birlesik risk,
    - veri guveni,
    - hangi aksiyonun onde oldugu.
  - `strengths`, `risks`, `recommendations` bos kalmayacak sekilde skor tabanli fallback maddeleri eklendi.
  - Coverage yuksekken yanlis bicimde gorunen `dusuk kapsama` onerisi filtrelendi.
- Frontend:
  - `narrativeSourceLabel()` icinde `deterministic` etiketi `Kural tabanli karar destegi` olarak gosteriliyor.
  - `deterministic_llm_fallback` etiketi `Karar destek ozeti` olarak gosteriliyor.
- Dogrulama:
  - `python -m py_compile propel-backend\app\services\software_ml_service.py` basarili.
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` ve `docker restart propel_frontend` basarili.
  - Canli dashboard API: summary dogal yonetici diliyle dondu; risk ve oneriler dolu geldi.

### 2026-06-15 KPI ML Yonetici Ozeti Uzun AI Anlatim ve Alan Duzeni

- Kullanici yonetici ozetinin deterministik olmamasini, daha mantikli/uzun cumleler kurmasini ve genis bos alanin kucultulmesini istedi.
- Backend:
  - `SoftwareMLService._dashboard_ai_summary_fallback()` daha detayli analitik anlatim uretecek sekilde genisletildi.
  - Fallback source `analytic_narrative` oldu; kullaniciya `deterministic` kaynak etiketi tasinmiyor.
  - LLM provider yoksa teknik `LLM provider ayarli degil` mesaji onerilere eklenmiyor.
  - Riskler ve oneriler artik baslik seviyesinde kalmiyor; skor ve kaynak baglamini aciklayan daha uzun maddeler uretiyor.
- Frontend:
  - `loadDepartmentDashboard()` varsayilan olarak `use_llm=true` cagiriyor; Gemini/Ollama mevcutsa yonetici ozeti LLM ile zenginlesiyor.
  - `narrativeSourceLabel()` icinde teknik deterministic etiketleri `AI karar destek ozeti` olarak gosteriliyor.
  - Yonetici ozeti karti `self-start` ve daha kompakt padding ile sag aksiyon kolonunun boyuna esnemiyor.
  - Summary metni `h3` yerine okunabilir paragraf olarak, `whitespace-pre-line` ve daha iyi satir araligi ile gosteriliyor.
  - Guclu sinyal/risk/oneri kutularinin padding ve font boyutu sikilastirildi.
- Dogrulama:
  - `python -m py_compile propel-backend\app\services\software_ml_service.py` basarili.
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` ve `docker restart propel_frontend` basarili.
  - Canli dashboard API `use_llm=true` ile `source=gemini`, `fallback_used=false` dondu; summary, riskler ve oneriler detayli geldi.

### 2026-06-15 Dashboard Aksiyon Kaynagi ve Kanit Dili

- Kullanici KPI & ML dashboard aksiyonlarinin neye gore yazildigini ve gercek analizlere dayanip dayanmadigini sordu.
- Tespit:
  - Ilk aksiyonlar LLM/Gemini tarafindan dashboard payload'indaki KPI/ML, nabiz, 360, risk ve coverage verileri yorumlanarak uretiliyor.
  - Takim bazli aksiyonlar backend tarafinda `team_breakdown` skor kirilimindan deterministik uretiliyor.
  - UI bu ayrimi gostermedigi icin kullanici aksiyonun AI yorumu mu, takim skor kirilimi mi oldugunu anlayamiyordu.
- Backend:
  - `DepartmentDashboardActionResponse.source` artik insight kaynagini tasiyor (`gemini:critical`, `analytic_narrative:risk_overlap`, `team_breakdown`, `coverage`).
  - LLM insight prompt'una nedensellik siniri eklendi:
    - `X, Y'den kaynaklaniyor` gibi kesin neden-sonuc cumleleri kurma.
    - Evidence zayifsa once dogrulama aksiyonu oner.
    - Ayrilma riski/burnout/motivasyon krizi gibi yuksek etkili yorumlari sadece payload'da ilgili sinyal varsa yaz.
- Frontend:
  - Aksiyon kartlarina kaynak rozeti eklendi.
  - `gemini:*` -> `Kaynak: AI icgoru (Gemini)`.
  - `team_breakdown` -> `Kaynak: takim skor kirilimi`.
  - `coverage` -> `Kaynak: veri kapsami`.
- Dogrulama:
  - `python -m py_compile propel-backend\app\services\software_ml_service.py` basarili.
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_backend` ve `docker restart propel_frontend` basarili.
  - Canli dashboard API'de aksiyon source alanlari `gemini:critical`, `gemini:warning`, `gemini:info`, `team_breakdown` olarak dondu.

### 2026-06-15 KPI ML Aksiyonlar Yatay Duzen

- Kullanici KPI & ML dashboard'da aksiyon kartlarinin sagda dikey kolon olarak durdugunu, sol alanda buyuk bosluk yarattigini ve yatay duzen istedigini belirtti.
- Frontend:
  - `ManagerAnalyticsView.vue` yonetici ozeti + aksiyonlar bolumu iki kolonlu `xl:grid-cols-[minmax(0,1.2fr)_360px]` duzenden tek kolonlu `space-y-5` duzene alindi.
  - Aksiyonlar sag aside kolonundan cikarilip yonetici ozetinin altinda responsive yatay grid olarak gosteriliyor.
  - Grid `grid-cols-1 md:grid-cols-2 2xl:grid-cols-3`; aksiyon sayisi rozeti eklendi.
  - Aksiyon kartlari kaynak/owner chiplerini koruyor ve `min-h-[180px]` ile dengeli gorunuyor.
- Dogrulama:
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_frontend` basarili.

### 2026-06-16 KPI ML Rol/Takim Dashboard Okunurlugu

- Kullanici KPI & ML sayfasindaki "Rol bazli performans ve trend" grafiginin profesyonel ve anlasilir durmadigini, sayilarin gercek analiz sonucuna dayanmasi gerektigini belirtti.
- Tespit:
  - Bolum `GET /api/v1/analytics/performance/summary` cevabindaki `roles` ve `teams` alanlarini kullaniyor.
  - Backend `AnalyticsService` bu alanlari calisan KPI kayitlarindan hesapliyor; frontend tarafinda rastgele veya sabit sayi uretilmiyor.
- Frontend:
  - Cift eksenli Chart.js bar grafigi kaldirildi.
  - Rol bazli gorunum, skor barlari, trend etiketi, analiz kapsami, en yuksek ve izlenecek calisan bilgilerini gosteren responsive kart dashboard'a donusturuldu.
  - Takim KPI ozeti sag dikey listeden cikarilip yatay responsive kart grid'e alindi.
  - Takim kartlari ortalama KPI, kapsam, trend ve dusus sayisini API verisiyle gosteriyor.
  - UI'a veri kaynagi notu eklendi: `Kaynak: /analytics/performance/summary`.
- Dogrulama:
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_frontend` basarili.

### 2026-06-16 KPI ML Teknik Omurga Yerine Yonetici Karar Paneli

- Kullanici KPI & ML sayfasindaki "Analytics Omurgasi" ve "Sprint 1" bloklarinin manager icin ne anlattigini ve ne aksiyon urettigini sorguladi.
- Frontend:
  - Teknik mimari/sprint bloklari manager ekraninda gizlendi.
  - Yerine "Yonetici Karar Paneli" eklendi.
  - Panel kartlari `performance/summary` verisinden turetiliyor: KPI kapsami, oncelikli takim, izlenecek rol grubu ve guclu ornek takim.
  - Kartlar manager'a dogrudan ne yapacagini soyluyor: eksik KPI kapsamini tamamlama, takim lideriyle blokaj/capacity gorusmesi, rol grubu icin mentorluk/review kontrolu, guclu takim pratiklerini yayma.
- Dogrulama:
  - `npm.cmd run type-check` basarili.
  - `docker restart propel_frontend` basarili.

### 2026-06-17 PR 40 Master Merge Conflict Cozumu

- `pr-40` branch'ine `origin/master` merge edilirken olusan conflictler cozuldu.
- Conflict dosyalari:
  - `propel-backend/app/services/nlp_service.py`
  - `propel-frontend/src/services/api/feedback.api.ts`
  - `propel-frontend/src/views/manager/EmployeeAnalysisView.vue`
- Cozum:
  - 360 employee summary backend'inde PR 40 burnout/risk driver akisina master'dan gelen gercek 1-5 `skill_scores` hesaplamasi eklendi.
  - Duplicate badge sorgusu tekrar edilmeden mevcut badge akisi korundu.
  - Frontend API tiplerinde `RiskDriver` ve `SkillScore` birlikte tutuldu.
  - Manager employee analysis ekraninda KPI row/burnout driver computed'lari ile gercek yetenek skoru computed'lari birlikte korundu.
  - Merge sonrasi type-check'te yakalanan `EmployeeManagement.vue` `survey_ars` null durumu UI'da tire fallback'iyle duzeltildi.
- Dogrulama:
  - `python -m py_compile propel-backend/app/services/nlp_service.py propel-backend/app/schemas/feedbacks.py` basarili.
  - `npm.cmd run type-check` basarili.
