#  KUTUP – AI‑Driven Performance Management Platform

[![Backend CI](https://github.com/ddemi-ssena/PROPEL-AI-Performance/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/ddemi-ssena/PROPEL-AI-Performance/actions/workflows/backend-ci.yml)
[![Frontend CI](https://github.com/ddemi-ssena/PROPEL-AI-Performance/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/ddemi-ssena/PROPEL-AI-Performance/actions/workflows/frontend-ci.yml)
[![Docker Build & Push](https://github.com/ddemi-ssena/PROPEL-AI-Performance/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/ddemi-ssena/PROPEL-AI-Performance/actions/workflows/docker-publish.yml)
![License](https://img.shields.io/github/license/USERNAME/KUTUP)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Node](https://img.shields.io/badge/node-18%2B-green)

> **KUTUP**, organizations track, analyze, and optimize employee & department performance using **AI‑powered analytics, predictive models, and role‑based dashboards**.
> Modern HR analytics meets real machine learning.

---

## 📋 Table of Contents

* Overview
* Why KUTUP?
* Key Features
* Tech Stack
* System Architecture
* Project Structure
* Getting Started
* API Documentation
* Machine Learning Models
* Role‑Based Access Control
* Testing
* CI/CD Pipeline
* Deployment
* Roadmap
* Contributing
* License
* Contact

---

## 🎯 Overview

**KUTUP** is a modern, enterprise‑grade performance management platform designed to replace subjective, reactive HR processes with **objective, data‑driven, and predictive insights**.

It centralizes performance data, applies machine learning to detect trends and risks, and presents everything through intuitive dashboards tailored to each role.

---

## ❓ Why KUTUP?

Traditional systems struggle with:

❌ Subjective evaluations & manager bias
❌ Disconnected data sources
❌ Late reaction to performance issues
❌ Expensive, bloated enterprise tools
❌ Poor UX that users avoid

**KUTUP fixes this by:**

✅ Quantifiable KPIs & objective analytics
✅ Unified performance data platform
✅ Predictive AI models (forecasting & risk detection)
✅ Open‑source & SME‑friendly
✅ Clean, role‑based UX people actually enjoy

---

## ✨ Key Features

### 📊 Core Analytics

* Real‑time dashboards (Admin / Manager / Employee)
* Department‑specific KPI tracking
* Survey management (Motivation, Satisfaction, Stress)
* Trend visualization & comparisons
* 9‑Box Talent Matrix (Performance × Potential)

### 🤖 AI / ML Capabilities

* Performance forecasting (Prophet)
* Risk detection (Random Forest)
* Anomaly detection (Isolation Forest)
* AI‑generated development recommendations
* Employee clustering & segmentation

### 🔐 Security & Compliance

* Role‑Based Access Control (RBAC)
* JWT authentication
* Data anonymization
* GDPR / KVKK‑aware design

### 📈 Advanced

* Custom KPI definitions
* CSV / Excel import
* Exportable PDF & Excel reports
* Multi‑language support (TR / EN)

---

## 🛠️ Tech Stack

### Backend

* **FastAPI** – REST API
* **PostgreSQL** – Relational database
* **SQLAlchemy 2.0** – ORM
* **Pydantic** – Data validation
* **JWT (python‑jose)** – Auth
* **Prophet** – Time‑series forecasting
* **scikit‑learn** – ML models
* **Docker** – Containerization

### Frontend

* **Vue.js 3 + TypeScript**
* **Vite**
* **Pinia** (state)
* **Vue Router**
* **Tailwind CSS**
* **Chart.js**

### DevOps

* **GitHub Actions** – CI/CD
* **Docker Compose**
* **pytest**
* **Black / Flake8 / ESLint**

---

## 🏗️ System Architecture

KUTUP follows a clean layered architecture:

* **Client Layer**: Vue.js dashboards
* **API Layer**: FastAPI REST services
* **Business Logic Layer**: Services
* **ML Layer**: Forecasting, classification, anomaly detection
* **Data Layer**: PostgreSQL via SQLAlchemy

---

## 📁 Project Structure

```
KUTUP/
├── propel-backend/
├── propel-frontend/
├── .github/workflows/
│   ├── backend-ci.yml
│   ├── frontend-ci.yml
│   └── docker-publish.yml
├── docker-compose.yml
├── LICENSE
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

* Docker & Docker Compose
* Python 3.10+
* Node.js 18+
* Git

### Quick Start (Docker)

```bash
git clone https://github.com/USERNAME/KUTUP.git
cd KUTUP
docker-compose up -d
```

Backend → [http://localhost:8000](http://localhost:8000)
Frontend → [http://localhost:5173](http://localhost:5173)

---

## 📚 API Documentation

* Swagger UI: `http://localhost:8000/docs`
* ReDoc: `http://localhost:8000/redoc`

JWT required:

```http
Authorization: Bearer <token>
```

---

## 🤖 Machine Learning Models

| Model            | Purpose                 |
| ---------------- | ----------------------- |
| Prophet          | Performance forecasting |
| Random Forest    | Risk classification     |
| Isolation Forest | Anomaly detection       |
| K‑Means          | Talent segmentation     |

---

## 🔐 Role‑Based Access Control

| Role     | Access             |
| -------- | ------------------ |
| Admin    | Full system access |
| Manager  | Department‑level   |
| Employee | Personal data only |

---

## 🧪 Testing

### Backend

```bash
pytest --cov=app
```

### Frontend

```bash
npm run lint
npm run type-check
```

Target coverage: **80%**

---

## 🔄 CI/CD Pipeline

### GitHub Actions

* **Backend CI**: tests, lint, coverage
* **Frontend CI**: lint, type‑check, build
* **Docker Publish**: build & push images

Workflows live in `.github/workflows/`

---

## 🌐 Deployment

* Docker Compose (recommended)
* AWS / DigitalOcean / Railway
* Frontend: Vercel / Netlify

---

## 🛣️ Roadmap

* [ ] Notification system
* [ ] Real‑time analytics (WebSockets)
* [ ] Advanced ML explainability
* [ ] Mobile‑friendly dashboards

---

## 🤝 Contributing

Pull requests welcome.
Please follow code style and include tests.

---

## 📄 License

MIT License

---

## 📬 Contact

Maintained by **KUTUP Team**
Questions? Open an issue 🚀
