# AUVSoftware

Custom AUV control and telemetry backend inspired by the KSU AUV team software architecture.

This project provides:

* FastAPI-based API for telemetry and control endpoints
* SQLAlchemy-backed database layer
* Modular sensor & actuator models
* Click-based CLI for database and server management
* Docker-based development environment

---

# Project Structure

```
.
├── configs
├── docker-compose.yml
├── LICENSE
├── pyproject.toml
├── README.md
└── src
    └── auvsoftware
        ├── api
        │   ├── app.py
        │   └── routes/
        ├── cli
        │   └── main.py
        ├── database
        │   ├── models/
        │   ├── repositories/
        │   ├── scripts/init_db.py
        │   └── session.py
        ├── hardware_interface
        ├── movement_package
        ├── simulation
        ├── visualizer
        └── utils
```

---

# Features Implemented

### API Routes

* `/runs`
* `/imu`
* `/depth`
* `/power`
* `/inputs`
* `/motor`
* `/servo`
* `/sonar`
* `/range_finder`
* `/rgb`

Each route connects to a corresponding SQLAlchemy model under:

```
auvsoftware/database/models/
```

---

# Getting Started

## 1️⃣ Clone Repository

```bash
git clone https://github.com/msle237-lees/AUVSoftware.git
cd AUVSoftware
```

---

## 2️⃣ Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3️⃣ Install Project (Editable Mode)

This installs your package and CLI entry points.

```bash
pip install -e .
```

---

## 4️⃣ Environment Variables

Copy the example file:

```bash
cp .env.example .env
```

Edit `.env` to configure:

* Database URL
* Credentials
* Any environment-specific settings

---

## 5️⃣ Start Database (Docker)

```bash
docker compose up -d
```

> Uses `docker-compose.yml` in the project root.

---

## 6️⃣ Initialize Database Schema

Your database models are created via:

```
auvsoftware/database/scripts/init_db.py
```

Run:

```bash
python -m auvsoftware.cli.main initdb
```

Or if entry points are configured:

```bash
auvsoftware initdb
```

---

## 7️⃣ Run API Server

### Development Mode (with reload)

```bash
python -m auvsoftware.cli.main dbonly --reload
```

Or:

```bash
auvsoftware dbonly --reload
```

This runs:

```
uvicorn auvsoftware.api.app:app --reload
```

---

## API Documentation

Once running:

* Swagger UI:
  [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

* OpenAPI Schema:
  [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

# CLI Commands

| Command  | Description                 |
| -------- | --------------------------- |
| `initdb` | Create database tables      |
| `status` | Check database connectivity |
| `dbonly` | Run FastAPI server          |

Example:

```bash
auvsoftware status
```

---

# Architecture Overview

### API Layer

* FastAPI application in `api/app.py`
* Route grouping by telemetry type
* Dependency injection via `deps.py`

### Database Layer

* SQLAlchemy engine + session management
* Model-per-sensor architecture
* Repository abstraction for telemetry writes

### CLI Layer

* Click-based management interface
* Handles:

  * DB initialization
  * Health checks
  * API startup

---

# Development Notes

* All models are located under `database/models`
* New telemetry types require:

  1. Model
  2. Repository logic (if needed)
  3. API route
  4. Router registration in `app.py`

---

# Future Improvements

* Logging integration (Python logging)
* Migration support (Alembic)
* Hardware integration layer expansion
* Simulation bridge
* Real-time streaming (WebSockets)
