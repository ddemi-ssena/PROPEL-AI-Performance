# Sekil 3.3. Veritabani Varlik-Iliski (ER) Diyagrami

Bu diyagram KUTUP performans yonetim platformunun SQLAlchemy modellerinden cikarilmistir. Ortak `BaseModel` yapisi nedeniyle tum tablolarda `id`, `created_at` ve `updated_at` alanlari bulunur. Diyagram; kullanici-calisan-departman omurgasini, KPI kayitlarini, haftalik nabiz anketlerini, 360 derece geri bildirim surecini, NLP/RAG analiz kayitlarini, toplantilari, bildirimleri ve veri yukleme gecmisini birlikte gosterir.

```mermaid
erDiagram
    USERS {
        int id PK
        datetime created_at
        datetime updated_at
        string email UK
        string hashed_password
        string full_name
        enum role "admin | department_manager | employee"
        boolean is_active
    }

    DEPARTMENTS {
        int id PK
        datetime created_at
        datetime updated_at
        string name UK
        text description
    }

    EMPLOYEES {
        int id PK
        datetime created_at
        datetime updated_at
        int user_id FK_UK
        int department_id FK
        string external_employee_code UK
        string team
        string position
        float experience_years
        date hire_date
    }

    KPIS {
        int id PK
        datetime created_at
        datetime updated_at
        string name
        text description
        enum unit "numeric | percentage | currency | hours"
        int department_id FK
        float target_value
    }

    KPI_RECORDS {
        int id PK
        datetime created_at
        datetime updated_at
        int kpi_id FK
        int employee_id FK
        float value
        date period_date
    }

    SURVEY_RESPONSES {
        int id PK
        datetime created_at
        datetime updated_at
        int employee_id FK
        string survey_type
        float score
        date period_date
        string comments
        json raw_data
        float mte_score
        float ars_score
    }

    FEEDBACKS {
        int id PK
        datetime created_at
        datetime updated_at
        int reviewer_id FK
        int reviewee_id FK
        enum feedback_type
        date period_date
        float score_communication
        float score_teamwork
        float score_problem_solving
        float score_leadership
        float score_technical
        text strength_text
        text improvement_text
        text general_comment
        boolean is_voice_input
        boolean is_anonymous
        json nlp_result
        int request_id FK
    }

    FEEDBACK_REQUESTS {
        int id PK
        datetime created_at
        datetime updated_at
        int requester_id FK
        int target_id FK
        enum status "pending | completed | declined | expired"
        date period_date
        date deadline
        string message
    }

    EMPLOYEE_BADGES {
        int id PK
        datetime created_at
        datetime updated_at
        int employee_id FK
        enum badge_type
        enum badge_level "bronze | silver | gold"
        date period_date
        json source_feedback_ids
    }

    FEEDBACK_QUESTIONS {
        int id PK
        datetime created_at
        datetime updated_at
        int week_number
        enum direction
        text question_text
        string category
        int department_id FK
        boolean is_ai_generated
    }

    FEEDBACK_ASSIGNMENTS {
        int id PK
        datetime created_at
        datetime updated_at
        int sender_id FK
        int target_id FK
        enum assignment_type
        enum status "pending | completed | expired"
        int period_week
        int period_month
        int period_year
        int completed_feedback_response_id FK
    }

    FEEDBACK_RESPONSES {
        int id PK
        datetime created_at
        datetime updated_at
        int sender_id FK
        int receiver_id FK
        int question_id FK
        text response_text
        int score_communication
        int score_teamwork
        int score_leadership
        int score_technical
        int period_week
        int period_month
        int period_year
        json nlp_analysis
    }

    FEEDBACK_NLP_ANALYSES {
        int id PK
        datetime created_at
        datetime updated_at
        enum source_type "weekly_feedback | classic_feedback"
        int weekly_feedback_id FK_UK
        int classic_feedback_id FK_UK
        int employee_id FK
        int reviewer_employee_id FK
        int department_id FK
        text direction
        text theme
        text analysis_version
        text model_provider
        text model_name
        enum sentiment_label
        float sentiment_score
        float motivation_score
        enum burnout_risk
        enum flight_risk
        float psychological_safety_score
        float collaboration_score
        float growth_signal_score
        float leadership_support_score
        json key_strengths
        json risk_flags
        json support_needs
        json keywords
        text manager_summary
        json raw_analysis
    }

    EMPLOYEE_NLP_PROFILES {
        int id PK
        datetime created_at
        datetime updated_at
        int employee_id FK
        int department_id FK
        enum period_type "weekly | monthly"
        int period_year
        int period_month
        int period_week
        int feedback_count
        float avg_sentiment_score
        float avg_motivation_score
        float avg_psychological_safety_score
        float avg_collaboration_score
        float avg_growth_signal_score
        enum burnout_risk_level
        enum flight_risk_level
        json top_strengths
        json top_risk_areas
        json top_support_needs
        text manager_summary
        text recommended_action
    }

    FEEDBACK_MEMORY_CHUNKS {
        int id PK
        datetime created_at
        datetime updated_at
        enum source_type "weekly_feedback | classic_feedback"
        int weekly_feedback_id FK_UK
        int classic_feedback_id FK_UK
        int employee_id FK
        int reviewer_employee_id FK
        int department_id FK
        text content_text
        text content_summary
        json theme_labels
        json metadata_json
        text embedding_provider
        text embedding_model
        int embedding_dimension
        json embedding_vector
    }

    MEETINGS {
        int id PK
        datetime created_at
        datetime updated_at
        string title
        string team
        date scheduled_date
        time scheduled_time
        int duration_minutes
        string meeting_url
        text note
        json agenda_items
        string source
        int created_by_user_id FK
    }

    MEETING_ATTENDEES {
        int id PK
        datetime created_at
        datetime updated_at
        int meeting_id FK
        int employee_id FK
        int dataset_employee_id
        string display_name
        string role
        int notification_id FK
    }

    NOTIFICATIONS {
        int id PK
        datetime created_at
        datetime updated_at
        int recipient_user_id FK
        int recipient_employee_id FK
        string recipient_label
        int meeting_id FK
        string title
        text body
        string channel
        string status
        string notification_type
        string read_at
    }

    DATA_UPLOADS {
        int id PK
        datetime created_at
        datetime updated_at
        string file_name
        string file_type
        datetime upload_date
        int record_count
        string status
        string error_message
        int uploaded_by_id FK
        json raw_info
    }

    USERS ||--o| EMPLOYEES : "user profile"
    DEPARTMENTS ||--o{ EMPLOYEES : "contains"
    DEPARTMENTS ||--o{ KPIS : "defines"
    KPIS ||--o{ KPI_RECORDS : "measured by"
    EMPLOYEES ||--o{ KPI_RECORDS : "has"
    EMPLOYEES ||--o{ SURVEY_RESPONSES : "submits"

    EMPLOYEES ||--o{ FEEDBACKS : "reviewer"
    EMPLOYEES ||--o{ FEEDBACKS : "reviewee"
    FEEDBACK_REQUESTS ||--o| FEEDBACKS : "completed as"
    EMPLOYEES ||--o{ FEEDBACK_REQUESTS : "requester"
    EMPLOYEES ||--o{ FEEDBACK_REQUESTS : "target"
    EMPLOYEES ||--o{ EMPLOYEE_BADGES : "earns"

    DEPARTMENTS ||--o{ FEEDBACK_QUESTIONS : "scopes"
    FEEDBACK_QUESTIONS ||--o{ FEEDBACK_RESPONSES : "answered by"
    EMPLOYEES ||--o{ FEEDBACK_RESPONSES : "sender"
    EMPLOYEES ||--o{ FEEDBACK_RESPONSES : "receiver"
    EMPLOYEES ||--o{ FEEDBACK_ASSIGNMENTS : "assignment sender"
    EMPLOYEES ||--o{ FEEDBACK_ASSIGNMENTS : "assignment target"
    FEEDBACK_RESPONSES ||--o| FEEDBACK_ASSIGNMENTS : "completes"

    FEEDBACK_RESPONSES ||--o| FEEDBACK_NLP_ANALYSES : "weekly source"
    FEEDBACKS ||--o| FEEDBACK_NLP_ANALYSES : "classic source"
    EMPLOYEES ||--o{ FEEDBACK_NLP_ANALYSES : "analyzed employee"
    EMPLOYEES ||--o{ FEEDBACK_NLP_ANALYSES : "reviewer employee"
    DEPARTMENTS ||--o{ FEEDBACK_NLP_ANALYSES : "analysis scope"
    EMPLOYEES ||--o{ EMPLOYEE_NLP_PROFILES : "summarized by"
    DEPARTMENTS ||--o{ EMPLOYEE_NLP_PROFILES : "profile scope"

    FEEDBACK_RESPONSES ||--o| FEEDBACK_MEMORY_CHUNKS : "weekly memory"
    FEEDBACKS ||--o| FEEDBACK_MEMORY_CHUNKS : "classic memory"
    EMPLOYEES ||--o{ FEEDBACK_MEMORY_CHUNKS : "memory employee"
    EMPLOYEES ||--o{ FEEDBACK_MEMORY_CHUNKS : "memory reviewer"
    DEPARTMENTS ||--o{ FEEDBACK_MEMORY_CHUNKS : "memory scope"

    USERS ||--o{ MEETINGS : "creates"
    MEETINGS ||--o{ MEETING_ATTENDEES : "includes"
    EMPLOYEES ||--o{ MEETING_ATTENDEES : "attends"
    MEETING_ATTENDEES ||--o| NOTIFICATIONS : "invite notification"
    MEETINGS ||--o{ NOTIFICATIONS : "generates"
    USERS ||--o{ NOTIFICATIONS : "recipient user"
    EMPLOYEES ||--o{ NOTIFICATIONS : "recipient employee"

    USERS ||--o{ DATA_UPLOADS : "uploads"
```

## Iliski Ozeti

- `users` tablosu kimlik dogrulama ve rol bilgisini tutar. Her kullanici en fazla bir `employees` profiline baglanir.
- `departments` tablosu calisanlari ve departman bazli KPI tanimlarini gruplar.
- `kpis` KPI katalogudur; `kpi_records` her calisanin belirli donemdeki olcum degerlerini saklar.
- `survey_responses` haftalik nabiz, motivasyon, stres ve memnuniyet gibi calisan anketlerini tutar.
- `feedbacks` klasik 360 derece geri bildirimleri; `feedback_requests` ise geri bildirim talep surecini temsil eder.
- `feedback_questions`, `feedback_assignments` ve `feedback_responses` haftalik dinamik feedback akisini temsil eder.
- `feedback_nlp_analyses` hem klasik hem haftalik feedback metinlerinden uretilen NLP risk, duygu ve gelisim sinyallerini saklar.
- `employee_nlp_profiles` calisan bazli haftalik/aylik NLP ozet profilidir.
- `feedback_memory_chunks` RAG/embedding tabanli geri bildirim hafizasi icin metin parcasi ve embedding bilgisini saklar.
- `meetings`, `meeting_attendees` ve `notifications` risk toplantisi planlama ve bildirim akisini temsil eder.
- `data_uploads` admin tarafindan yuklenen CSV/XLSX veri setlerinin durumunu ve metadatasini tutar.

## Dokumana Ekleme Notu

Tez veya raporda bu blok su baslikla kullanilabilir:

> Sekil 3.3. Veritabani Varlik-Iliski (ER) Diyagrami

Mermaid destekleyen araclarda dogrudan render edilebilir. Word/PDF icin Mermaid Live Editor, draw.io veya VS Code Mermaid eklentisiyle PNG/SVG olarak disa aktarilabilir.
