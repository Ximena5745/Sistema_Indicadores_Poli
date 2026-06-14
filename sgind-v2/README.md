# SGIND v2 — Sistema de Gestión de Indicadores (Migración)

Sistema destino independiente del Streamlit actual. Stack: **Next.js 14 + FastAPI + PostgreSQL**.

## Estructura

```
sgind-v2/
├── frontend/          # Next.js 14 (App Router, TypeScript, Tailwind)
├── backend/           # FastAPI (async, SQLAlchemy 2.0, Pydantic v2)
├── database/          # Migraciones y scripts SQL
├── docs/              # Arquitectura, ADRs, estado de migración
└── docker-compose.yml # Orquestación local (fe + be + db)
```

## Requisitos

- Node.js 20+
- Python 3.11+
- Docker Desktop (opcional, recomendado)

## Inicio rápido (desarrollo local)

### 1. Variables de entorno

```bash
cp .env.example .env
# Editar .env con credenciales Microsoft OIDC y rutas de datos
```

### 2. Con Docker (recomendado)

```bash
docker compose up --build
```

| Servicio   | URL                          |
|------------|------------------------------|
| Frontend   | http://localhost:3000        |
| Backend    | http://localhost:8000        |
| API Docs   | http://localhost:8000/docs   |
| PostgreSQL | localhost:5432               |

### 3. Sin Docker

**Backend:**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Relación con el sistema Streamlit

| Aspecto        | Streamlit (actual)     | SGIND v2 (este proyecto)   |
|----------------|------------------------|----------------------------|
| Ubicación      | `streamlit_app/`, `core/` | `sgind-v2/`             |
| Datos Excel    | `data/` (compartido vía volumen) | Lectura read-only |
| Base de datos  | SQLite / Supabase      | PostgreSQL dedicado        |
| Estrategia     | Producción actual      | Parallel run (coexistencia) |

Los datos Excel del sistema legacy se montan como volumen de solo lectura (`SGIND_DATA_PATH`).

## Fases del plan de migración

| Fase | Estado   | Entregable en sgind-v2                    |
|------|----------|-------------------------------------------|
| 0    | Referencia | Auditoría en `docs/migration-plan/`     |
| 1    | Iniciada | ADRs, docker-compose, estructura modular  |
| 2    | Iniciada | `database/migrations/001_initial.sql`     |
| 4-5  | Scaffold | Backend + Frontend base con rutas         |

Ver [docs/migration/STATUS.md](docs/migration/STATUS.md) para el detalle de avance.

## Roles (RBAC)

| Rol        | Permisos                                      |
|------------|-----------------------------------------------|
| `procesos` | Lectura de dashboards e indicadores           |
| `calidad`  | Lectura + gestión OM + administración          |
| `desempeno`| Lectura + gestión OM + administración          |
