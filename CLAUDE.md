# AGENTS.MD â€” KUTUP Agent KÄ±lavuzu

> Bu dosya hem AI agent'lar iÃ§in canlÄ± bir proje rehberi hem de geliÅŸtirme gÃ¼nlÃ¼ÄŸÃ¼dÃ¼r.
> Her sohbetin sonunda yapÄ±lan Ã§alÄ±ÅŸma Ã¶zeti, kalÄ±nan nokta ve sonraki adÄ±mlar buraya eklenir.

---

## KalÄ±cÄ± Talimatlar

- Her sohbet sonunda yapÄ±lan Ã§alÄ±ÅŸma Ã¶zeti, kalÄ±nan nokta ve sonraki adÄ±mlar bu dosyaya kaydedilecek.
- Kod deÄŸiÅŸikliklerinden Ã¶nce `py_compile` (backend) ve `npm.cmd run type-check` (frontend) doÄŸrulamasÄ± yapÄ±lacak.
- Container yeniden baÅŸlatma: `docker compose restart backend` / `docker compose restart frontend`.
- Backend kod deÄŸiÅŸikliklerinden sonra **mutlaka** `docker restart propel_backend` Ã§alÄ±ÅŸtÄ±r â€” uvicorn hot-reload kapalÄ±.
- Yeni Python baÄŸÄ±mlÄ±lÄ±klarÄ± eklenirse `docker compose build backend` ile image yeniden build et.

---

## Proje Genel BakÄ±ÅŸ

**KUTUP**, yapay zeka destekli bir performans yÃ¶netim platformudur. YazÄ±lÄ±m ve SatÄ±ÅŸ departmanlarÄ± iÃ§in ML tabanlÄ± KPI analizi, 360 derece geri bildirim, haftalÄ±k nabÄ±z anketleri ve departman/takÄ±m raporlama Ã¶zellikleri sunar.

| BileÅŸen | Teknoloji | Port |
|---|---|---|
| Frontend | Vue 3 + TypeScript + Tailwind CSS | 5173 |
| Backend | FastAPI + SQLAlchemy | 8001 |
| VeritabanÄ± | PostgreSQL 15 + pgvector | 5432 |

---

## Mimari

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚         Vue.js 3 SPA (propel-frontend)        â”‚
â”‚  Admin / Manager / Employee Dashboard'larÄ±    â”‚
â”‚  Analytics Views Â· Feedback Â· Reports         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                     â”‚ REST / Axios + JWT
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚         FastAPI (propel-backend)              â”‚
â”‚  /api/v1/auth Â· /analytics Â· /kpis           â”‚
â”‚  /employees Â· /meetings Â· /notifications      â”‚
â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
       â”‚ SQLAlchemy ORM
  â”Œâ”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
  â”‚            Services Layer                  â”‚
  â”‚  SoftwareMLService Â· SalesMLService       â”‚
  â”‚  SoftwareNarrativeService                 â”‚
  â”‚  SalesNarrativeService                    â”‚
  â”‚  AnalyticsService Â· TeamReportExportSvc   â”‚
  â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
       â”‚
  â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
  â”‚         Analytics / ML Layer              â”‚
  â”‚  analytics/departments/  (adapters)       â”‚
  â”‚    software.py Â· sales.py                 â”‚
  â”‚  analytics/features/                      â”‚
  â”‚    software.py Â· sales.py (feature eng.)  â”‚
  â”‚  analytics/training/                      â”‚
  â”‚    software.py (RF/HGB/LR)               â”‚
  â”‚    sales.py    (LightGBM+XGB+RFâ†’LR stack) â”‚
  â”‚  analytics/prediction/                    â”‚
  â”‚    software.py Â· sales.py                 â”‚
  â”‚  analytics/artifacts/                     â”‚
  â”‚    software.py Â· sales.py (joblib store)  â”‚
  â”‚  analytics/explain/                       â”‚
  â”‚    software.py Â· sales.py (KPI drivers)   â”‚
  â”‚  analytics/importers/                     â”‚
  â”‚    software.py Â· sales.py (KPI import)    â”‚
  â”‚  analytics/kpi_registry.py                â”‚
  â”‚    SOFTWARE_KPI_REGISTRY (20 KPI)         â”‚
  â”‚    SALES_KPI_REGISTRY    (25 KPI)         â”‚
  â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
       â”‚
  â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
  â”‚ PostgreSQL + pgvector â”‚
  â”‚ 15+ tablo, embedding  â”‚
  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## Teknoloji YÄ±ÄŸÄ±nÄ±

### Backend (`propel-backend/`)
- **FastAPI** 0.104.1, **Uvicorn** 0.24.0
- **SQLAlchemy** 2.0.23, **Pydantic** 2.5.0
- **JWT**: python-jose 3.3.0, bcrypt 3.1.7
- **ML**: scikit-learn 1.3.2, pandas 2.1.3, numpy 1.26.2, joblib 1.3.2
- **Stacking Ensemble (SatÄ±ÅŸ)**: **lightgbm 4.3.0**, **xgboost 2.0.3** + scikit-learn StackingClassifier
- **LLM**: Ollama (yerel) veya Google Gemini API
- **Export**: openpyxl 3.1.5
- **System dep**: `libgomp1` (LightGBM iÃ§in, Dockerfile'da yÃ¼klÃ¼)

### Frontend (`propel-frontend/`)
- **Vue 3.4.0** + **TypeScript 5.3.0**, **Vite 5.0.12**
- **Pinia** 2.1.7 (state), **Vue Router** 4.2.5
- **Tailwind CSS** 3.4.1, **Chart.js** 4.4.1 + vue-chartjs 5.3.0
- **axios** 1.6.0

---

## Dizin YapÄ±sÄ±

```
kutup-neww/
â”œâ”€â”€ propel-backend/
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ api/routers/
â”‚   â”‚   â”‚   â”œâ”€â”€ analytics.py        # TÃ¼m ML/analytics endpoint'leri (software + sales)
â”‚   â”‚   â”‚   â”œâ”€â”€ admin_uploads.py    # CSV/XLSX upload (department_key desteÄŸiyle)
â”‚   â”‚   â”‚   â”œâ”€â”€ auth.py Â· employees.py Â· kpis.py
â”‚   â”‚   â”‚   â”œâ”€â”€ meetings.py Â· notifications.py
â”‚   â”‚   â”‚   â””â”€â”€ feedback.py Â· survey_responses.py
â”‚   â”‚   â”œâ”€â”€ db/models/              # SQLAlchemy modelleri
â”‚   â”‚   â”œâ”€â”€ schemas/
â”‚   â”‚   â”‚   â””â”€â”€ analytics.py        # Software + Sales Pydantic ÅŸemalarÄ±
â”‚   â”‚   â”œâ”€â”€ services/
â”‚   â”‚   â”‚   â”œâ”€â”€ software_ml_service.py
â”‚   â”‚   â”‚   â”œâ”€â”€ software_narrative_service.py
â”‚   â”‚   â”‚   â”œâ”€â”€ sales_ml_service.py       # â˜… YENÄ°
â”‚   â”‚   â”‚   â”œâ”€â”€ sales_narrative_service.py # â˜… YENÄ°
â”‚   â”‚   â”‚   â”œâ”€â”€ analytics_service.py
â”‚   â”‚   â”‚   â””â”€â”€ team_report_export_service.py
â”‚   â”‚   â”œâ”€â”€ analytics/
â”‚   â”‚   â”‚   â”œâ”€â”€ kpi_registry.py     # SOFTWARE_KPI_REGISTRY + SALES_KPI_REGISTRY
â”‚   â”‚   â”‚   â”œâ”€â”€ registry.py         # Adapter kayÄ±t (software + sales)
â”‚   â”‚   â”‚   â”œâ”€â”€ contracts.py        # Shared data contracts
â”‚   â”‚   â”‚   â”œâ”€â”€ departments/
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ base.py
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ software.py
â”‚   â”‚   â”‚   â”‚   â””â”€â”€ sales.py        # â˜… YENÄ° (tam implementasyon)
â”‚   â”‚   â”‚   â”œâ”€â”€ features/
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ software.py
â”‚   â”‚   â”‚   â”‚   â””â”€â”€ sales.py        # â˜… YENÄ° (25 KPI + derived features)
â”‚   â”‚   â”‚   â”œâ”€â”€ training/
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ software.py     # RF/HGB/LR
â”‚   â”‚   â”‚   â”‚   â””â”€â”€ sales.py        # â˜… YENÄ° (LightGBM+XGB+RFâ†’LR stacking)
â”‚   â”‚   â”‚   â”œâ”€â”€ prediction/
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ software.py
â”‚   â”‚   â”‚   â”‚   â””â”€â”€ sales.py        # â˜… YENÄ°
â”‚   â”‚   â”‚   â”œâ”€â”€ artifacts/
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ software.py
â”‚   â”‚   â”‚   â”‚   â””â”€â”€ sales.py        # â˜… YENÄ°
â”‚   â”‚   â”‚   â”œâ”€â”€ explain/
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ software.py
â”‚   â”‚   â”‚   â”‚   â””â”€â”€ sales.py        # â˜… YENÄ° (KPI eÅŸik/trend aÃ§Ä±klamalarÄ±)
â”‚   â”‚   â”‚   â”œâ”€â”€ importers/
â”‚   â”‚   â”‚   â”‚   â”œâ”€â”€ software.py
â”‚   â”‚   â”‚   â”‚   â””â”€â”€ sales.py        # â˜… YENÄ°
â”‚   â”‚   â”‚   â””â”€â”€ artifacts_store/
â”‚   â”‚   â”‚       â”œâ”€â”€ software/       # YazÄ±lÄ±m model artifact'larÄ± (joblib)
â”‚   â”‚   â”‚       â””â”€â”€ sales/          # â˜… YENÄ° â€” SatÄ±ÅŸ model artifact'larÄ±
â”‚   â”‚   â”œâ”€â”€ ml/                     # Genel ML (sentiment, risk)
â”‚   â”‚   â””â”€â”€ core/                   # Config + gÃ¼venlik
â”‚   â”œâ”€â”€ main.py
â”‚   â”œâ”€â”€ seed_data.py
â”‚   â”œâ”€â”€ Dockerfile                  # libgomp1 eklendi (LightGBM gereksinimi)
â”‚   â””â”€â”€ requirements.txt            # lightgbm==4.3.0, xgboost==2.0.3 eklendi
â”œâ”€â”€ propel-frontend/
â”‚   â”œâ”€â”€ src/
â”‚   â”‚   â”œâ”€â”€ views/
â”‚   â”‚   â”‚   â”œâ”€â”€ admin/
â”‚   â”‚   â”‚   â”œâ”€â”€ manager/
â”‚   â”‚   â”‚   â”œâ”€â”€ employee/
â”‚   â”‚   â”‚   â”œâ”€â”€ feedback/
â”‚   â”‚   â”‚   â””â”€â”€ auth/
â”‚   â”‚   â”œâ”€â”€ components/
â”‚   â”‚   â”œâ”€â”€ services/api/
â”‚   â”‚   â”œâ”€â”€ stores/
â”‚   â”‚   â”œâ”€â”€ composables/
â”‚   â”‚   â””â”€â”€ router/index.ts
â”‚   â””â”€â”€ package.json
â”œâ”€â”€ docker-compose.yml
â”œâ”€â”€ AGENTS.MD                       # Bu dosya
â””â”€â”€ CLAUDE.md                       # AGENTS.MD kopyasÄ± (Claude Code iÃ§in)
```

---

## API Endpoint'leri

### Kimlik DoÄŸrulama
| YÃ¶ntem | Yol | AÃ§Ä±klama |
|---|---|---|
| POST | `/api/v1/auth/login` | GiriÅŸ â†’ JWT (form-data: username + password) |
| POST | `/api/v1/auth/register` | KayÄ±t |
| GET | `/api/v1/auth/me` | Mevcut kullanÄ±cÄ± |

### Analitik & ML â€” YazÄ±lÄ±m DepartmanÄ±
| YÃ¶ntem | Yol | AÃ§Ä±klama |
|---|---|---|
| GET | `/api/v1/analytics/departments` | Departman konfigÃ¼rasyonlarÄ± |
| GET | `/api/v1/analytics/departments/{key}/overview` | Departman Ã¶zeti |
| GET | `/api/v1/analytics/departments/software/datasets` | YÃ¼klÃ¼ dataset'ler |
| GET | `/api/v1/analytics/departments/software/datasets/{id}/employees` | Dataset Ã§alÄ±ÅŸanlarÄ± |
| GET | `/api/v1/analytics/departments/software/datasets/{id}/model-state` | Model durumu |
| POST | `/api/v1/analytics/departments/software/models/train` | ML modeli eÄŸit |
| GET | `/api/v1/analytics/departments/software/predictions/latest` | Tekil tahmin |
| GET | `/api/v1/analytics/departments/software/predictions/bulk` | Toplu tahmin |
| POST | `/api/v1/analytics/departments/software/team-report/export` | Excel raporu indir |
| GET | `/api/v1/analytics/performance/summary` | KPI/performans Ã¶zeti |

### Analitik & ML â€” SatÄ±ÅŸ DepartmanÄ± â˜… YENÄ°
| YÃ¶ntem | Yol | AÃ§Ä±klama |
|---|---|---|
| GET | `/api/v1/analytics/departments/sales/datasets` | SatÄ±ÅŸ dataset'leri |
| GET | `/api/v1/analytics/departments/sales/datasets/{id}/employees` | Dataset Ã§alÄ±ÅŸanlarÄ± |
| GET | `/api/v1/analytics/departments/sales/datasets/{id}/model-state` | 4 hedef model durumu |
| POST | `/api/v1/analytics/departments/sales/models/train` | Stacking ensemble eÄŸit |
| GET | `/api/v1/analytics/departments/sales/predictions/latest` | Tekil satÄ±ÅŸ tahmini |
| GET | `/api/v1/analytics/departments/sales/predictions/bulk` | Toplu satÄ±ÅŸ tahmini |

### KPI
| YÃ¶ntem | Yol | AÃ§Ä±klama |
|---|---|---|
| GET | `/api/v1/kpis` | KPI tanÄ±mlarÄ± |
| POST | `/api/v1/kpis` | KPI oluÅŸtur |
| GET | `/api/v1/kpis/records` | KPI kayÄ±tlarÄ± (sayfalÄ±) |
| POST | `/api/v1/kpis/records` | KPI kaydÄ± ekle |

### Ã‡alÄ±ÅŸanlar, Departmanlar, ToplantÄ±lar, Bildirimler
| YÃ¶ntem | Yol | AÃ§Ä±klama |
|---|---|---|
| GET/POST/PUT | `/api/v1/employees[/{id}]` | CRUD |
| GET/POST | `/api/v1/departments` | CRUD |
| POST | `/api/v1/meetings/team-risk` | Risk toplantÄ±sÄ± planla + bildirim gÃ¶nder |
| GET | `/api/v1/meetings` | ToplantÄ± listesi |
| GET | `/api/v1/notifications/me` | KullanÄ±cÄ± bildirimleri |
| POST | `/api/v1/notifications/team-report` | Rapor paylaÅŸ |
| POST | `/api/v1/admin/uploads` | CSV/XLSX yÃ¼kle (department_key parametresi ile) |
| GET/POST | `/api/v1/surveys[/responses]` | Anket |
| GET/POST | `/api/v1/feedback` | 360 geri bildirim |

---

## VeritabanÄ± Modelleri

| Model | Ã–nemli Alanlar |
|---|---|
| `User` | id, email, hashed_password, role (admin/department_manager/employee) |
| `Employee` | id, user_idâ†’User, department_idâ†’Department, team, position, experience_years, external_employee_code |
| `Department` | id, name (unique) |
| `KPI` | id, name, unit, department_id, target_value |
| `KPIRecord` | id, kpi_id, employee_id, value, period_date |
| `SurveyResponse` | id, employee_id, q1_motivationâ€¦q6_suggestion |
| `Feedback` / `FeedbackRequest` / `FeedbackQuestion` | 360 derece feedback sistemi |
| `Meeting` + `MeetingAttendee` | id, title, department_id, team, scheduled_at |
| `Notification` | id, recipient_id, notification_type, title, message, is_read |
| `DataUpload` | id, file_name, department_key (raw_info.department_key), row_count, status |
| `FeedbackNLPAnalysis` / `EmployeeNLPProfile` | NLP/sentiment sonuÃ§larÄ± |
| `FeedbackMemoryChunk` | embedding (pgvector) â€” RAG desteÄŸi |

---

## Rol BazlÄ± EriÅŸim (RBAC)

| Rol | EriÅŸim |
|---|---|
| **admin** | TÃ¼m sistem, veri yÃ¶netimi, tÃ¼m departmanlar, ML model eÄŸitimi |
| **department_manager** | Kendi departmanÄ± analitik, takÄ±m yÃ¶netimi, Ã§alÄ±ÅŸan deÄŸerlendirme |
| **employee** | KiÅŸisel performans verisi, self-assessment, geri bildirim |

---

## ML Sistemi

### YazÄ±lÄ±m DepartmanÄ± Pipeline

**Hedefler**: `performance_band`, `attrition_risk_band`

**Model seÃ§enekleri**: `logistic_regression`, `random_forest`, `hist_gradient_boosting`

1. **Upload**: CSV/XLSX `POST /admin/uploads?department_key=software` ile yÃ¼klenir.
2. **Train**: `POST /analytics/departments/software/models/train` â†’ sklearn pipeline eÄŸitilir, `artifacts_store/software/` altÄ±na joblib.
3. **Predict**: Tekil (`/predictions/latest`) veya toplu (`/predictions/bulk`).
4. **Team Analytics**: DÃ¶nem Ã— takÄ±m kÄ±rÄ±lÄ±mÄ±nda aggregated risk trend.
5. **Narrative**: `use_llm_narrative=true` â†’ LLM, aksi halde deterministik fallback.

**KPI Registry**: `SOFTWARE_KPI_REGISTRY` â€” 20 KPI (GTO, ZTO, GKE, KKKE, BY, KBO, CRKO vb.)

---

### SatÄ±ÅŸ DepartmanÄ± Pipeline â˜… YENÄ°

**Hedefler**: `Performance_Drop_Target`, `Burnout_Target`, `Resignation_Target`, `High_Risk_Target`

**Model**: `stacking_lgbm_xgb_rf_lr` â€” LightGBM + XGBoost + RandomForest â†’ LogisticRegression meta-learner (sklearn StackingClassifier, cv=3)

**Fallback**: EÄŸitim setinde herhangi bir sÄ±nÄ±fta < 6 Ã¶rnek varsa `random_forest_fallback` pipeline kullanÄ±lÄ±r (Ã¶r. Burnout_Target Ã§ok seyrek ise).

**Veri AkÄ±ÅŸÄ±**:
1. **Upload**: CSV/XLSX `POST /admin/uploads` body'de `department_key=sales` ile yÃ¼klenir.
2. **Feature Engineering** (`analytics/features/sales.py`):
   - DoÄŸrudan kolonlar: `Total_Activity`, `Lead_to_Win_Conversion`, `Average_Sales_Cycle_Days`, `Sales_Workload_Index`, `Followup_OnTime_Rate`, `Customer_Satisfaction`, `CRM_Usage_Rate`, `Motivation_Score`, `Peer_Support_Count` vb.
   - TÃ¼retilen Ã¶zellikler: `sales_goal_attainment` (rev/target), `new_customer_rate`, `win_rate`, `pipeline_coverage`, `aged_pipeline_rate`, `complaint_rate`, `team_contribution`, `training_completion`
   - Time features: lag_1, rolling_4, trend_4 (her KPI iÃ§in)
   - TakÄ±m-relatif: `revenue_vs_team` (KPI-8 GKP)
   - Rolling SIYS (iÅŸ yÃ¼kÃ¼ stres skoru), motivasyon eÄŸimi (MTE)
   - Kolon normalizasyonu: case-insensitive (Excel'deki `Employee_ID`, `Week` vb. otomatik tanÄ±nÄ±r)
   - `employee_id` parseri: `EMP_001`, `SA-003`, `1` formatlarÄ± desteklenir
   - `year` eksikse â†’ 2024 varsayÄ±lan
3. **Train**: `POST /analytics/departments/sales/models/train` â†’ `test_period_count` dÃ¶nem test seti.
4. **Bulk Predict**: `GET /predictions/bulk` â†’ 30 Ã§alÄ±ÅŸan Ã— bÃ¶lge/rol bazlÄ± sonuÃ§, takÄ±m narratifi, team_analytics.
5. **Narrative**: LLM destekli veya deterministik satÄ±ÅŸ odaklÄ± yorum.

**KPI Registry**: `SALES_KPI_REGISTRY` â€” 25 KPI:

| # | Kod | Ad | Kaynak |
|---|---|---|---|
| 1 | SHGO | SatÄ±ÅŸ Hedef GerÃ§ekleÅŸme OranÄ± | rev/target veya `Sales_Target_Achievement` |
| 2 | SAY | SatÄ±ÅŸ Aktivite YoÄŸunluÄŸu | `Total_Activity` |
| 3 | NMKO | Yeni MÃ¼ÅŸteri KazanÄ±m OranÄ± | new/total veya `New_Customer_Acquisition_Rate` |
| 4 | LMDO | Leadâ†’MÃ¼ÅŸteri DÃ¶nÃ¼ÅŸÃ¼m OranÄ± | `Lead_to_Win_Conversion` |
| 5 | TKO | Tekliften KazanÄ±ma DÃ¶nÃ¼ÅŸÃ¼m | won/(won+lost) veya `Proposal_Win_Rate` |
| 6 | OSDS | Ort. SatÄ±ÅŸ DÃ¶ngÃ¼sÃ¼ SÃ¼resi | `Average_Sales_Cycle_Days` |
| 7 | OSD | Ortalama SatÄ±ÅŸ DeÄŸeri | `Average_Sale_Value` |
| 8 | GKP | GÃ¶reli KazanÄ±m PerformansÄ± | rev/team_avg (hesaplanan) |
| 9 | KKS | KazanÄ±m Kalite Skoru | `Won_Deal_Count` |
| 10 | PSO | Pipeline SaÄŸlÄ±k OranÄ± | pipeline/target veya `Pipeline_Health_Ratio` |
| 11 | PYO | Pipeline YaÅŸta Olma OranÄ± | aged/open veya `Pipeline_Aging_Rate` |
| 12 | SIYE | SatÄ±ÅŸ Ä°ÅŸ YÃ¼kÃ¼ Endeksi | `Sales_Workload_Index` |
| 13 | SIYS | SÃ¼rekli Ä°ÅŸ YÃ¼kÃ¼ Stres Skoru | rolling overload (hesaplanan) |
| 14 | TDO | Takip Disiplini OranÄ± | `Followup_OnTime_Rate` |
| 15 | CSAT | MÃ¼ÅŸteri Memnuniyeti | `Customer_Satisfaction` |
| 16 | SO | Åikayet OranÄ± | complaints/won veya `Complaint_Rate` |
| 17 | CRMD | CRM Disiplin MetriÄŸi | `CRM_Usage_Rate` |
| 18 | SEKS | SatÄ±ÅŸ Ekibi KatkÄ± Skoru | mentor+peer veya `Team_Contribution_Score` |
| 19 | MS | Motivasyon Skoru | `Motivation_Score` |
| 20 | EKS | Ekip Destek KatkÄ± Skoru | `Peer_Support_Count` |
| 21 | MTE | Motivasyon Trend EÄŸimi | son 4 hafta lineer eÄŸim (hesaplanan) |
| 22 | GKS | GeliÅŸim KatÄ±lÄ±m Skoru | completed/recommended veya `Development_Participation_Rate` |
| 23-25 | SPS/BRS/PPE | BileÅŸik KPI'lar | target_candidate, model feature deÄŸil |

**Dataset Kolon UyumluluÄŸu**: Excel/CSV'deki `Employee_ID`, `Week`, `Region`, `Role_Level` gibi Pascal/mixed case kolonlar otomatik normalize edilir. `year` kolonu olmayan dataset'lerde 2024 varsayÄ±lan.

**Ã–nemli KÄ±sÄ±t**: Yeni dataset (1612 satÄ±r, 31 Ã§alÄ±ÅŸan) ile tÃ¼m 4 hedef baÅŸarÄ±yla eÄŸitiliyor:
- Performance_Drop: %100 F1, 1240/372 train/test
- Burnout: %99.4 F1
- Resignation: %99.5 F1
- High_Risk: %98.9 F1

**Aktif Dataset**: `KUTUP_Sales_52Week_2024.xlsx` â€” 31 Ã§alÄ±ÅŸan (SA-001..SA-031) Ã— 52 hafta = 1612 satÄ±r.
- SA-031: Hatice YÄ±ldÄ±rÄ±m (Sales Department Manager, Genel bÃ¶lge)
- TÃ¼m "Manager" pozisyon unvanlarÄ± â†’ "Sales Team Lead" olarak gÃ¼ncellendi (sadece Hatice YÄ±ldÄ±rÄ±m "Manager")

---

### Ortak ML AltyapÄ±sÄ±

- **Artifact store**: `analytics/artifacts_store/{department}/{target_column}/runs/{run_id}/` â€” `model.joblib` + `metadata.json` + `latest.json` pointer
- **Feature importance**: Stacking'de base learner'larÄ±n feature importance ortalamasÄ± alÄ±nÄ±r
- **Explanation**: `top_drivers` â€” KPI Registry'den eÅŸik durumu (`threshold_status`), 4 haftalÄ±k trend sinyali (`trend_signal`), rasyonel metin
- **Narrative layer**: Deterministic fallback (her zaman) + LLM enhancement (isteÄŸe baÄŸlÄ±, `use_llm_narrative=true`)

---

## Ortam YapÄ±landÄ±rmasÄ±

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

**Not**: `config.py`'de `extra="forbid"` var â†’ `.env`'e tanÄ±msÄ±z field ekleme!

### Docker Compose Servisleri
| Servis | Image | Port | Notlar |
|---|---|---|---|
| db | pgvector/pgvector:pg15 | 5432 | POSTGRES_PASSWORD=123456 |
| backend | FastAPI (custom) | 8001â†’8000 | env_file + DATABASE_URL override |
| frontend | Vue dev server | 5173 | VITE_API_URL=http://localhost:8001/api/v1 |

### HÄ±zlÄ± BaÅŸlatma
```bash
docker compose up -d
docker exec propel_backend python seed_data.py
# Admin: admin@propel.com / admin123
# Swagger: http://localhost:8001/docs
```

---

## GeliÅŸtirme NotlarÄ± ve Bilinen KÄ±sÄ±tlamalar

- **Backend Restart Zorunlu**: uvicorn `--reload` olmadan Ã§alÄ±ÅŸÄ±yor. Kod deÄŸiÅŸikliÄŸi sonrasÄ± `docker restart propel_backend` ÅŸart.
- **SatÄ±ÅŸ ML Kolon Normalizasyonu**: `SalesFeatureBuilder` tÃ¼m satÄ±r key'lerini lowercase yapÄ±yor. `Employee_ID` â†’ `employee_id`, `Region` â†’ team olarak kullanÄ±lÄ±r.
- **Burnout_Target**: GerÃ§ek dataset'te genellikle Ã§ok seyrek. EÄŸitim baÅŸarÄ±sÄ±z olabilir (normal).
- **TÃ¼rkÃ§e Karakter Encoding**: JSON response'larÄ±nda bazÄ± client'lar `DoÃ„u Anadolu` gÃ¶sterebilir â€” bu UTF-8 display artifact, gerÃ§ek veri doÄŸru.
- **Testler**: `pytest` yapÄ±landÄ±rÄ±lmÄ±ÅŸ fakat `app/tests/` dizini henÃ¼z boÅŸ.
- **Playwright**: Yerel ortamda yÃ¼klÃ¼ deÄŸil; browser smoke testi Ã§alÄ±ÅŸmÄ±yor.
- **LLM Gecikme**: Narrative LLM Ã§aÄŸrÄ±larÄ± 18-24 sn bloklayÄ±cÄ±. Default `use_llm_narrative=false` ile deterministik ve hÄ±zlÄ±.
- **pgvector**: `ENABLE_PGVECTOR=true` gerektirir, varsayÄ±lan `false`.
- **Swagger Login**: `/api/v1/auth/login` form-data (username/password), JSON deÄŸil!

---

## Test KullanÄ±cÄ±larÄ± (seed_data.py)

| Email | Åifre | Rol | YÃ¶nlendirme |
|---|---|---|---|
| admin@propel.com | admin123 | Admin | `/admin` |
| manager.yazilim@propel.com | manager123 | YazÄ±lÄ±m YÃ¶neticisi | `/manager` â†’ YazÄ±lÄ±m nav |
| manager.satis@propel.com | manager123 | SatÄ±ÅŸ YÃ¶neticisi | `/manager` â†’ SatÄ±ÅŸ nav |
| developer1@propel.com | dev123 | Ã‡alÄ±ÅŸan (YazÄ±lÄ±m) | `/employee` |
| satis.employee@propel.com | satis123 | Ã‡alÄ±ÅŸan (SatÄ±ÅŸ, SA-011) | `/employee/sales` |
| sl-001@propel.com | satis123 | Ã‡alÄ±ÅŸan (SatÄ±ÅŸ, SA-001) | `/employee/sales` |

**SatÄ±ÅŸ Dataset Ã‡alÄ±ÅŸanlarÄ±** (SA-001..SA-030, hepsi ÅŸifre: `satis123`):

| Kod | Ä°sim | BÃ¶lge | Rol |
|---|---|---|---|
| SA-001 | Ali YÄ±lmaz | Marmara | Senior |
| SA-002 | AyÅŸe Demir | Ege | Junior |
| SA-003 | Mehmet Kaya | Karadeniz | Manager |
| SA-004 | Fatma Ã‡elik | Marmara | Mid-Level |
| SA-005 | Mustafa KoÃ§ | Karadeniz | Manager |
| SA-006 | Zeynep Åahin | DoÄŸu Anadolu | Manager |
| SA-007 | Ahmet Ã–ztÃ¼rk | Ä°Ã§ Anadolu | Senior |
| SA-008 | Elif AydÄ±n | Marmara | Mid-Level |
| SA-009 | Caner YÄ±ldÄ±z | Akdeniz | Mid-Level |
| SA-010 | Burcu Arslan | Akdeniz | Junior |
| SA-011 | Zeynep Kaya (satis.employee) | Akdeniz | Senior |
| SA-012 | Kerem Arslan | GÃ¼neydoÄŸu Anadolu | Team Lead |
| SA-013 | Selin YÄ±lmaz | Ä°Ã§ Anadolu | Manager |
| SA-014 | Tuncay DoÄŸan | DoÄŸu Anadolu | Senior |
| SA-015 | Nihan Korkmaz | DoÄŸu Anadolu | Junior |
| SA-016 | Baran Ã–zdemir | GÃ¼neydoÄŸu Anadolu | Junior |
| SA-017 | Derya Kaplan | GÃ¼neydoÄŸu Anadolu | Team Lead |
| SA-018 | Serhat Bulut | DoÄŸu Anadolu | Senior |
| SA-019 | Merve Polat | Akdeniz | Senior |
| SA-020 | Ozan Ã‡etin | DoÄŸu Anadolu | Junior |
| SA-021 | Gamze Kurt | Ege | Mid-Level |
| SA-022 | Hakan Acar | Ä°Ã§ Anadolu | Manager |
| SA-023 | Rana ÅimÅŸek | Akdeniz | Junior |
| SA-024 | Emre YÄ±ldÄ±z | Marmara | Senior |
| SA-025 | PÄ±nar GÃ¼l | Marmara | Manager |
| SA-026 | Tolga Kara | Akdeniz | Team Lead |
| SA-027 | AslÄ± ErdoÄŸan | DoÄŸu Anadolu | Mid-Level |
| SA-028 | Volkan Åahin | Ege | Manager |
| SA-029 | Ä°rem Ã–zkan | DoÄŸu Anadolu | Team Lead |
| SA-030 | Burak Ã‡alÄ±ÅŸkan | Ä°Ã§ Anadolu | Mid-Level |

---

## GeliÅŸtirme GÃ¼nlÃ¼ÄŸÃ¼

### 2026-05-10 KPI / ML Analizi - TakÄ±m Analizi UI

- `ManagerAnalyticsView.vue` iÃ§inde TakÄ±m Analizi ekranÄ± yÃ¶netici odaklÄ± mini dashboard haline getirildi.
- SeÃ§ili takÄ±m iÃ§in gradient header, KPI kartlarÄ±, ana sorun kartÄ±, 12 haftalÄ±k risk trend grafiÄŸi, AI aksiyon paneli, takÄ±m Ã¼yeleri kart grid'i eklendi.
- Sahte takvim etiketleri â†’ `D1..Dn` dÃ¶nem etiketleri; sparkline polyline gerÃ§ek serilerden.

### 2026-05-10 Backend Performans Ã–lÃ§Ã¼mÃ¼ ve Refactor

- `_team_analytics` batch prediction refactor: `team_analytics_ms` 43562ms â†’ 736ms.

### 2026-05-10 ToplantÄ± ve Bildirim Backend AkÄ±ÅŸÄ±

- `Meeting`, `MeetingAttendee`, `Notification` modelleri + `POST /meetings/team-risk`, `GET /notifications/me` eklendi.

### 2026-05-10 TakÄ±m Analizi - Excel Export (5 Sheet)

- `TeamReportExportService` + 5 sheet Excel export endpoint eklendi.

### 2026-05-10 Rapor GÃ¶nder AkÄ±ÅŸÄ±

- `POST /notifications/team-report` endpoint'i + frontend modal eklendi.

### 2026-05-14 Uygulama Ã‡alÄ±ÅŸtÄ±rma ve Seed Ä°ÅŸlemi

- `.env` dosyasÄ± oluÅŸturuldu, Docker baÅŸlatÄ±ldÄ±, DB seed edildi (40 Ã§alÄ±ÅŸan, 5100 KPI).

### 2026-05-14 SatÄ±ÅŸ DepartmanÄ± KullanÄ±cÄ±larÄ±

- `manager.satis@propel.com`, `satis.employee@propel.com` eklendi.

### 2026-05-14 TakÄ±m â†’ Ã‡alÄ±ÅŸan Analizi YÃ¶nlendirmesi

- `ManagerAnalyticsView.vue` â†’ `manager-kpi-ml-analysis` deep-link yÃ¶nlendirmesi.

### 2026-05-14 Departman Analizi KPI ML Ãœst BÃ¶lÃ¼m

- 6 KPI kartÄ± + bubble chart + AI Analiz Ã–zeti paneli eklendi.

### 2026-05-14 Ã‡alÄ±ÅŸan Analizi Modern Performans Tablosu

- Full-width KPI ML tablosu, filtre bar, pagination, Excel export eklendi.

### 2026-05-14 Departman Analizi AI LLM Modal

- AI Analiz butonu + LLM modal eklendi.

### 2026-05-14 KPI ML Analizi Backend BaÄŸlantÄ±sÄ±

- `GET /analytics/performance/summary` endpoint'i + servis eklendi. DepartmentAnalysis + EmployeeAnalysis gerÃ§ek veriye baÄŸlandÄ±.

### 2026-05-14 SatÄ±ÅŸ DepartmanÄ± Tam ML Pipeline â˜… BÃœYÃœK

**Eklenen Dosyalar**:
- `analytics/kpi_registry.py` â†’ `SALES_KPI_REGISTRY` (25 KPI) eklendi
- `analytics/features/sales.py` â†’ `SalesFeatureBuilder` (114 feature, column normalization, derived ratios, time features, team-relative GKP, motivation trend)
- `analytics/training/sales.py` â†’ `SalesStackingTrainer` (LightGBM + XGBoost + RandomForest â†’ LogisticRegression meta-learner via StackingClassifier)
- `analytics/artifacts/sales.py` â†’ `SalesArtifactStore`
- `analytics/explain/sales.py` â†’ `SalesExplanationBuilder`
- `analytics/prediction/sales.py` â†’ `SalesPredictionService`
- `analytics/departments/sales.py` â†’ `SalesAnalyticsAdapter` (tam implementasyon, canlÄ± KPI veritabanÄ± gÃ¶rÃ¼nÃ¼mÃ¼)
- `analytics/importers/sales.py` â†’ `SalesKPIImportService`
- `services/sales_ml_service.py` â†’ `SalesMLService` (list, train, predict, bulk_predict, team_analytics)
- `services/sales_narrative_service.py` â†’ `SalesNarrativeService`

**GÃ¼ncellenen Dosyalar**:
- `schemas/analytics.py` â†’ Sales ÅŸemalarÄ± eklendi
- `api/routers/analytics.py` â†’ 6 sales endpoint eklendi
- `requirements.txt` â†’ lightgbm==4.3.0, xgboost==2.0.3
- `Dockerfile` â†’ `libgomp1` sistem baÄŸÄ±mlÄ±lÄ±ÄŸÄ±

**Test SonuÃ§larÄ±** (gerÃ§ek dataset: 30 Ã§alÄ±ÅŸan Ã— 52 hafta):
- Performance_Drop_Target: acc=1.0, macro_f1=1.0, train=1320, test=240
- Resignation_Target: acc=1.0, macro_f1=1.0
- High_Risk_Target: acc=0.996, macro_f1=0.996
- Top features: `kpi_1_shgo`, `average_sale_value`, `revenue_vs_team`

**Dataset Kolon SorunlarÄ± Ã‡Ã¶zÃ¼ldÃ¼**:
- `Employee_ID` (bÃ¼yÃ¼k harf), `Week` (bÃ¼yÃ¼k harf), `Region` (team yerine), `Role_Level` (role yerine) â€” hepsi normalize edildi
- `year` kolonu yoktu â†’ 2024 varsayÄ±lan
- `employee_id` `EMP_001` formatÄ±ndaydÄ± â†’ numeric parse

---

### 2026-05-17 SatÄ±ÅŸ DepartmanÄ± Frontend Dashboard â˜… BÃœYÃœK

**Eklenen Frontend DosyalarÄ±**:
- `propel-frontend/src/views/sales/SalesAnalyticsView.vue` â†’ SatÄ±ÅŸ yÃ¶neticisi ML analiz ekranÄ± (dataset seÃ§imi, 4 target, model eÄŸit/tahmin/toplu tara, takÄ±m tablosu, kiÅŸi kartlarÄ±, narratif)
- `propel-frontend/src/views/sales/SalesEmployeeDashboard.vue` â†’ SatÄ±ÅŸ Ã§alÄ±ÅŸanÄ± kiÅŸisel dashboard (emerald tema, 4 KPI kartÄ±, 9 satÄ±ÅŸ metriÄŸi, AI koÃ§, nabÄ±z anketi, rozet)

**GÃ¼ncellenen Frontend DosyalarÄ±**:
- `services/api/analytics.api.ts` â†’ Sales tipleri + 6 yeni API fonksiyonu (`getSalesDatasets`, `getSalesDatasetEmployees`, `getSalesModelState`, `trainSalesModel`, `getLatestSalesPrediction`, `getBulkSalesPredictions`)
- `router/index.ts` â†’ `/manager/sales-analytics`, `/admin/sales-analytics`, `/employee/sales` rotalarÄ±; login sonrasÄ± satÄ±ÅŸ Ã§alÄ±ÅŸanÄ± otomatik `/employee/sales`'e yÃ¶nlendirme
- `layouts/AppLayout.vue` â†’ `isSalesDept` computed (dept_id=2 veya 18); departmana gÃ¶re dinamik sidebar nav (yazÄ±lÄ±m yÃ¶neticisi â‰  satÄ±ÅŸ yÃ¶neticisi nav items)
- `stores/auth.ts` â†’ `satis.employee@propel.com` (Zeynep Kaya, dept_id=18) mock kullanÄ±cÄ±sÄ± eklendi
- `views/auth/LoginView.vue` â†’ Login sonrasÄ± `department_id` kontrolÃ¼ ile satÄ±ÅŸ Ã§alÄ±ÅŸanÄ± `/employee/sales`'e yÃ¶nlendirildi

**GÃ¼ncellenen Backend DosyalarÄ±**:
- `schemas/user.py` â†’ `UserResponse`'a `department_id: int | None = None` eklendi
- `api/routers/auth.py` â†’ `/me` endpoint'i `Employee` tablosuna join yaparak `department_id` dÃ¶nÃ¼yor
- `seed_data.py` â†’ `SALES_EMPLOYEE_SPECS` SA-001..SA-030 (30 kiÅŸi) olarak gÃ¼ncellendi

**VeritabanÄ± GÃ¼ncellemeleri**:
- `external_employee_code` SA-001..SA-010 olarak gÃ¼ncellendi (SL-xxx â†’ SA-xxx)
- SA-011 (satis.employee) eklendi
- SA-012..SA-030 arasÄ± 19 yeni kullanÄ±cÄ± + Employee kaydÄ± oluÅŸturuldu (email: `sa-12@propel.com`..`sa-30@propel.com`, ÅŸifre: `satis123`)

**Navigasyon MantÄ±ÄŸÄ±** (`department_id` bazlÄ±):
- `dept_id=1` (YazÄ±lÄ±m YÃ¶neticisi) â†’ KPI & ML Analizi grubu â†’ `/manager/kpi-ml-analysis`
- `dept_id=2` (SatÄ±ÅŸ YÃ¶neticisi) â†’ SatÄ±ÅŸ KPI & ML grubu â†’ `/manager/sales-analytics`
- Admin â†’ her iki departman + SatÄ±ÅŸ ML Analizi linki
- SatÄ±ÅŸ Ã§alÄ±ÅŸanÄ± â†’ SatÄ±ÅŸ PerformansÄ±m â†’ `/employee/sales`

**ML Target Durumu** (upload_id=4, 31 Ã§alÄ±ÅŸan Ã— 52 hafta = 1612 satÄ±r):
- `Performance_Drop_Target` âœ… F1=100%, 1240/372
- `Burnout_Target` âœ… F1=99.4%, 1240/372
- `Resignation_Target` âœ… F1=99.5%, 1240/372
- `High_Risk_Target` âœ… F1=98.9%, 1240/372

**Riskli Ã‡alÄ±ÅŸanlar** (Performans DÃ¼ÅŸÃ¼ÅŸÃ¼ hedefine gÃ¶re):
Nihan Korkmaz, Baran Ã–zdemir, Ozan Ã‡etin, Tuncay DoÄŸan, AslÄ± ErdoÄŸan, Burcu Arslan, Serhat Bulut, Derya Kaplan

**Ã–nemli KeÅŸif**: `/api/v1/auth/me` endpoint'i `department_id` dÃ¶ndÃ¼rmÃ¼yordu â†’ `department_name` de eklendi. Frontend sidebar artÄ±k email + department_name + route Ã¼zerinden satÄ±ÅŸ tespiti yapÄ±yor.

---

## GeliÅŸtirme GÃ¼nlÃ¼ÄŸÃ¼ (Devam)

### 2026-05-21 SatÄ±ÅŸ Ã‡alÄ±ÅŸan Dashboard Backend BaÄŸlantÄ±sÄ± â˜…

**Yeni Backend Endpoint**:
- `GET /analytics/departments/sales/my-performance` â€” kimlik doÄŸrulamalÄ± Ã§alÄ±ÅŸan iÃ§in kiÅŸisel dashboard verisi
  - 9 KPI metriÄŸi (SHGO, LMDO, TKO, OSDS, CSAT, CRMD, TDO, PSO, MS) â€” gerÃ§ek Excel verisi
  - 8 haftalÄ±k bileÅŸik performans trendi
  - ML tahmini (Performance_Drop_Target) â€” `predicted_band`, `recommended_actions`, `top_drivers`
  - `bar_pct` (0-1) â€” frontend progress bar iÃ§in

**Yeni Åemalar** (`schemas/analytics.py`):
- `SalesKPIMetric` â€” code, name, raw_value, unit, direction, threshold_status, trend_signal, bar_pct
- `SalesWeeklyTrendPoint` â€” label, score
- `SalesEmployeePerformanceResponse` â€” tÃ¼m dashboard verisi

**Auth `/me` GÃ¼ncelleme** (`api/routers/auth.py`, `schemas/user.py`):
- `department_name` alanÄ± eklendi â†’ sidebar ve router yÃ¶nlendirmesi iÃ§in

**Frontend GÃ¼ncellemeleri**:
- `SalesEmployeeDashboard.vue` â€” tÃ¼m hardcoded veriler gerÃ§ek `getMyPerformance()` API'sine baÄŸlandÄ±
- `survey.api.ts` â€” `createSurvey()` metodu eklendi (nabÄ±z anketi gerÃ§ek POST /surveys/)
- `analytics.api.ts` â€” `getMyPerformance()`, `SalesEmployeePerformanceResponse`, `SalesKPIMetric`, `SalesWeeklyTrendPoint` eklendi
- `AppLayout.vue` â€” `isSalesDept` email + department_name + route tabanlÄ± tespit
- `router/index.ts` â€” satÄ±ÅŸ mÃ¼dÃ¼rÃ¼ login sonrasÄ± `/manager/sales-analytics`'e yÃ¶nlendirilir
- `EmployeePulseView.vue` â€” "Personel Paneline DÃ¶n" butonu kaldÄ±rÄ±ldÄ±

**EMP_XXX Format DesteÄŸi**: `get_my_performance()` metodunda `SA-011` â†’ `EMP_011` eÅŸleÅŸtirmesi dÃ¼zeltildi

### 2026-05-21 SatÄ±ÅŸ Dataset ve Seed GÃ¼ncellemesi â˜…

**Yeni Dataset**: `KUTUP_Sales_52Week_2024.xlsx`
- 31 Ã§alÄ±ÅŸan (SA-001..SA-031) Ã— 52 hafta = 1612 satÄ±r
- SA-031: Hatice YÄ±ldÄ±rÄ±m (Sales Department Manager)
- TÃ¼m pozisyon unvanlarÄ±: "Sales Manager" â†’ "Sales Team Lead" (sadece SA-031 "Manager")
- 28 kolon, 4 hedef deÄŸiÅŸken
- Target daÄŸÄ±lÄ±mlarÄ±: PerfDrop=%34, Burnout=%3.3, Resignation=%5, HighRisk=%6.3
- Generator script: `generate_sales_dataset.py`

**Seed Data GÃ¼ncellemeleri** (`seed_data.py`):
- TÃ¼m isimler TÃ¼rkÃ§e karakterlerle gÃ¼ncellendi (Ä±, ÅŸ, ÄŸ, Ã§, Ã¶, Ã¼)
- `manager.satis@propel.com` â†’ `Hatice YÄ±ldÄ±rÄ±m` (department_manager, SA-031, Genel bÃ¶lgesi)
- `satis.employee@propel.com` â†’ `Zeynep Kaya` (SA-011)
- SALES_EMPLOYEE_SPECS takÄ±m isimleri Excel Region sÃ¼tunuyla birebir eÅŸleÅŸiyor
- SA-011 loop'tan hariÃ§ tutuldu (ayrÄ±ca satis.employee olarak ekleniyor)

**Test KullanÄ±cÄ±larÄ± (GÃ¼ncel)**:
| Email | Åifre | Rol | YÃ¶nlendirme |
|---|---|---|---|
| admin@propel.com | admin123 | Admin | /admin |
| manager.satis@propel.com | manager123 | Hatice YÄ±ldÄ±rÄ±m â€” SatÄ±ÅŸ MÃ¼dÃ¼rÃ¼ | /manager/sales-analytics |
| manager.yazilim@propel.com | manager123 | Ahmet YÄ±lmaz â€” YazÄ±lÄ±m MÃ¼dÃ¼rÃ¼ | /manager |
| satis.employee@propel.com | satis123 | Zeynep Kaya (SA-011) | /employee/sales |
| sa-020@propel.com | employee123 | Ozan Ã‡etin â€” Riskli profil | /employee/sales |
| sa-001@propel.com | employee123 | Ali YÄ±lmaz â€” GÃ¼venli profil | /employee/sales |

---

### 2026-05-22 SatÄ±ÅŸ Ã‡alÄ±ÅŸanÄ± Login Redirect DÃ¼zeltmesi â˜…

**Sorun**: `satis.employee@propel.com` ile giriÅŸ yapÄ±ldÄ±ÄŸÄ±nda `/employee/sales` (SalesEmployeeDashboard, emerald tema) yerine `/employee` (genel EmployeeDashboard, lacivert tema) aÃ§Ä±lÄ±yordu. Sayfa yenilendikten sonra veya eski oturumda da aynÄ± sorun tekrar ediyordu.

**KÃ¶k Neden**: Pinia store'da `token` localStorage'dan restore ediliyordu (`ref(localStorage.getItem('token'))`) fakat `user` objesi `null` kalÄ±yordu. Router guard `user = null` iken `isSales` kontrolÃ¼ yapÄ±nca `false` dÃ¶ndÃ¼rÃ¼yor ve `/employee`'ye yÃ¶nlendiriyordu.

**DÃ¼zeltilen Dosyalar**:

`propel-frontend/src/stores/auth.ts`:
- `login()` fonksiyonu: baÅŸarÄ±lÄ± giriÅŸten sonra `userEmail` ve `deptId` localStorage'a kaydediliyor
- `tryMockLogin()`: mock giriÅŸ iÃ§in de aynÄ± ÅŸekilde `userEmail` ve `deptId` kaydediliyor
- `logout()`: `userEmail` ve `deptId` localStorage'dan temizleniyor

`propel-frontend/src/router/index.ts`:
- `isSalesUser()` yardÄ±mcÄ± fonksiyonu eklendi: `user` objesi yokken `localStorage.getItem('userEmail')` ve `localStorage.getItem('deptId')` fallback olarak kullanÄ±lÄ±yor; `department_id === 14/18` kontrolÃ¼ eklendi
- `router.beforeEach` guard `async` yapÄ±ldÄ±: token varken `user = null` ise (sayfa yenileme / eski oturum) `/me` Ã§ekilip user restore ediliyor
- `requiresGuest` guard: `authStore.userRole || localStorage.getItem('role')` ile role tespiti gÃ¼Ã§lendirildi
- `employee-dashboard` guard eklendi: satÄ±ÅŸ Ã§alÄ±ÅŸanÄ± `/employee`'ye gelirse otomatik `/employee/sales`'e yÃ¶nlendiriliyor

**Ã–nemli Teknik Not**: Windows'ta Docker Desktop volume sync gecikmesi nedeniyle HMR Ã§alÄ±ÅŸmayabiliyor. Dosya deÄŸiÅŸikliklerinden sonra `docker cp` ile container'a manuel kopyalama gerekebilir:
```bash
docker cp propel-frontend/src/router/index.ts propel_frontend:/app/src/router/index.ts
docker cp propel-frontend/src/stores/auth.ts propel_frontend:/app/src/stores/auth.ts
docker restart propel_frontend
```

---

## Sonraki AdÄ±mlar / Roadmap

- [x] SatÄ±ÅŸ departmanÄ± frontend dashboard'u (Vue 3) â€” employee/manager/admin gÃ¶rÃ¼nÃ¼mleri
- [x] SatÄ±ÅŸ Ã§alÄ±ÅŸanÄ± dashboard KPI kartlarÄ±nÄ± backend'e baÄŸla
- [x] TÃ¼m 4 ML hedefi eÄŸitilebilir hale getirildi
- [x] TÃ¼rkÃ§e karakter dÃ¼zeltmesi (tÃ¼m isimler)
- [x] Hatice YÄ±ldÄ±rÄ±m â€” tek satÄ±ÅŸ mÃ¼dÃ¼rÃ¼ (SA-031, dataset'e eklendi)
- [x] SatÄ±ÅŸ Ã§alÄ±ÅŸanÄ± login redirect dÃ¼zeltmesi (router guard async + user restore)
- [ ] "Veri bekleniyor" durumu â€” satÄ±ÅŸ mÃ¼dÃ¼rÃ¼ KPI overview endpoint baÄŸlantÄ±sÄ±
- [ ] Personel listesi performans skorlarÄ± ML pipeline'Ä±na baÄŸlanacak
- [ ] `app/tests/` dizinine temel pytest test suite'i (hedef: %80 coverage)
- [ ] Playwright kurulumu ile frontend smoke testleri
- [ ] LLM narrative endpoint'ini async/background job olarak ayÄ±r
- [ ] Departman Analizi AI Modal â†’ PDF Ä°ndir ve Email GÃ¶nder backend baÄŸlantÄ±sÄ±
- [ ] Yeni departman desteÄŸi (Ä°K, Pazarlama): registry + kpi_registry + seed geniÅŸletme
- [ ] WebSocket ile gerÃ§ek zamanlÄ± bildirimler
- [ ] GDPR/KVKK uyumluluk Ã¶zellikleri
