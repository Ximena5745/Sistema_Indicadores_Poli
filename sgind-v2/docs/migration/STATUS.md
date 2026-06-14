# Estado de Migración — SGIND v2

**Última actualización:** 2026-06-13

## Resumen

| Fase | Nombre              | Estado      | Notas                                      |
|------|---------------------|-------------|--------------------------------------------|
| 0    | Levantamiento       | **Completada** | 8 entregables en `docs/phase-0/`        |
| 1    | Arquitectura        | **Completada**| 8 ADRs, RBAC, dominio portado, docker-compose |
| 2    | Modelo de Datos     | **Completada**| Esquema PG, migración, docs E2.1–E2.6     |
| 3    | UX/UI               | Pendiente   | Wireframes, design system                  |
| 4    | Backend             | **En progreso**| ETL, indicators, CMI, dashboard extendido |
| 5    | Frontend            | **En progreso**| 4 páginas conectadas a API real           |
| 6-12 | Resto               | Pendiente   | Ver plan completo                          |

## Fase 5 — Avance

- [x] Cliente API Axios (`src/lib/api.ts`)
- [x] Resumen General: KPIs + semáforo + tendencia + tabla
- [x] CMI Estratégico y CMI Procesos
- [x] Gestión OM (lectura)
- [x] Dev login en header
- [x] Build Next.js OK
- [ ] CRUD OM en UI
- [ ] 5 páginas secundarias restantes

## Docker

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| Backend  | http://localhost:8000/docs |
| PostgreSQL | localhost:5433 |

```bash
cd sgind-v2 && docker compose up -d
```

## Uso rápido

1. Abrir http://localhost:3000
2. Clic en **Dev login** (desarrollo)
3. Ir a **Resumen General** — ver KPIs y gráficos

## Comandos

```bash
# Frontend
cd sgind-v2/frontend && npm run build

# Backend tests
cd sgind-v2/backend && SGIND_DATA_PATH=../../data PYTHONPATH=. pytest tests/ -q
```
