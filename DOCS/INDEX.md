# ÍNDICE MAESTRO — samai-monitor (MVP)
## Última actualización: 3 de abril de 2026

---

# ESTADO DEL PROYECTO

| Fase | Estado | Notas |
|------|--------|-------|
| Fase 0: Setup | COMPLETADA | Python 3.13, SAM CLI, venv, fixtures, CLAUDE.md |
| Fase 1: Capa compartida (TDD) | COMPLETADA | 50 tests, 4 módulos |
| Fase 2: API Handler Lambda | COMPLETADA | 11 tests, 6 endpoints |
| Fase 3: Monitor Lambda | COMPLETADA | 5 tests, check+alertas |
| Fase 4: Deploy AWS | COMPLETADA | SAM stack desplegado, SES verificado |
| Fase 5: Frontend React | COMPLETADA | Login, Dashboard, Detalle, Perfil |
| Fase 6: Deploy frontend | COMPLETADA | S3 + CloudFront + OAC |
| Fase 7: Dark mode + UX | COMPLETADA | Tema, auto-format, empty states |
| Sprint 1: UI Foundation | COMPLETADA | Router, CSS modular, forgot pw, toasts, cascade delete |
| Sprint 2: Core Features | COMPLETADA | Alertas leídas, búsqueda, editar alias, SAMAI search |
| Sprint 3: Advanced Features | COMPLETADA | Pausar monitoreo, mark-all, descarga docs, sort, badge |
| Sprint 4: UX Polish | COMPLETADA | Skeletons, CSV export, dropdown, polling, ErrorBoundary |
| Deploy: CI/CD + SES | COMPLETADA | GitLab CI/CD, IAM user, SES production request, CORS fix |

| Billing: Wompi | COMPLETADA | Suscripciones, planes, enforcement, webhook SHA256 |
| Equipos (Planes compartidos) | COMPLETADA | Teams CRUD, enforcement unificado, pendingConfirmation, reactivacion async |

**Total**: 143 tests backend, 50+ commits, 35+ features implementadas

---

# MAPA DE ARCHIVOS

## Raíz
| Archivo | Contenido |
|---------|-----------|
| `CLAUDE.md` | Reglas de código y arquitectura (la IA lee esto primero) |
| `Makefile` | `make test`, `make build`, `make deploy` |
| `template.yaml` | SAM — todos los recursos AWS (PENDIENTE) |
| `pytest.ini` | Config pytest con markers y paths |
| `.gitignore` | Exclusiones estándar |

## backend/layers/shared/python/ — Capa compartida
| Archivo | Contenido | Estado |
|---------|-----------|--------|
| `models.py` | Dataclasses: Radicado, Actuacion, Alerta, Etiqueta, Team, TeamMember | HECHO |
| `radicado_utils.py` | normalizar, formatear, validar, extraer_corporacion | HECHO |
| `samai_client.py` | get_actuaciones, get_actuaciones_nuevas, buscar_proceso | HECHO |
| `db.py` | guardar/obtener/eliminar radicados, actuaciones, alertas, dedup | HECHO |

## backend/functions/ — Lambdas
| Archivo | Contenido | Estado |
|---------|-----------|--------|
| `api_handler/app.py` | CRUD radicados, alertas, buscar, etiquetas, billing status, teams | HECHO |
| `monitor/app.py` | check_radicado + handler (dedup → SAMAI → alertas → email) | HECHO |
| `billing_webhook/app.py` | Webhook Wompi: valida firma SHA256, activa suscripciones | HECHO |
| `billing_api/app.py` | Planes, suscripciones, facturas, Wompi widget config | HECHO |
| `cognito_email_sender/app.py` | Custom email sender (verificacion, reset password) | HECHO |
| `pre_signup/app.py` | PreSignUp trigger (enlaza Google con cuentas nativas) | HECHO |

## backend/scripts/
| Archivo | Contenido | Estado |
|---------|-----------|--------|
| `seed_plans.py` | Seed de 5 planes de billing en DynamoDB | HECHO |

## backend/tests/ — Tests
| Archivo | Contenido | Estado |
|---------|-----------|--------|
| `conftest.py` | Fixtures pytest: moto DynamoDB, JSON fixtures | CREADO |
| `test_radicado_utils.py` | 22 tests: normalizar, formatear, validar, extraer | HECHO |
| `test_samai_client.py` | 14 tests: actuaciones, buscar, errores (requests-mock) | HECHO |
| `test_db.py` | 36 tests: CRUD radicados, actuaciones, alertas, etiquetas, teams (moto) | HECHO |
| `test_api_handler.py` | 11 tests: todos los endpoints HTTP | HECHO |
| `test_monitor.py` | 14 tests: check_radicado, multi-usuario, handler, plan enforcement | HECHO |
| `fixtures/samai_actuaciones.json` | 177 actuaciones reales (radicado 73001233300020190034300) | GRABADO |
| `fixtures/samai_proceso.json` | Datos completos de proceso real | GRABADO |
| `fixtures/estados_extraidos.json` | 9 estados extraidos por scraping | COPIADO |

## DOCS/ — Documentación
| Archivo | Contenido |
|---------|-----------|
| `INDEX.md` | **ESTE ARCHIVO** |
| `DEV_LOG.md` | Log de desarrollo por sesión |
| `OPS_RUNBOOK.md` | Runbook de operaciones: AWS, CI/CD, SES, deploy, troubleshooting |
| `NUEVAS_PLATAFORMAS.md` | Investigación técnica: SIUGJ, Siglo XXI (CPNU), SPOA — APIs, CAPTCHAs, dificultad, plan de integración |
| `DESIGN_CRITIQUE.md` | Auditoría de diseño y accesibilidad (26 mar 2026) — hallazgos WCAG, jerarquía visual, plan P0/P1/P2 |
| `ESTRATEGIA_SUSCRIPCIONES.md` | Estrategia de suscripciones, pricing, go-to-market, análisis competitivo (3 abr 2026) |
| `SETUP_BILLING.md` | Guía paso a paso: configurar Wompi, llaves, webhook, seed, sandbox, producción |
| `EQUIPOS.md` | Equipos / Planes compartidos: tablas, endpoints, enforcement, flujo de renovacion, pendingConfirmation |
| `GESTION_SUSCRIPCIONES.md` | Upgrade, downgrade, cancelacion, reembolso (void Wompi), prorrateo, pendingPlanId |
| `VENCIMIENTO_TERMINOS.md` | Vencimiento de términos procesales: investigación APIs, plan técnico, preguntas para abogado |

## Investigación previa (referencia)
| Archivo | Ubicación |
|---------|-----------|
| Índice investigación | `../EstadosUpdates/DOCS/INDEX.md` |
| API SAMAI (Swagger spec) | `../EstadosUpdates/swagger_spec.json` |
| Análisis legal | `../EstadosUpdates/DOCS/ANALISIS_LEGAL.md` |
| Análisis competidores | `../EstadosUpdates/DOCS/ANALISIS_COMPETIDORES.md` |
| Arquitectura original | `../EstadosUpdates/DOCS/ARQUITECTURA_AWS.md` |

---

# REFERENCIA RÁPIDA API SAMAI

| Endpoint | Devuelve |
|----------|----------|
| `GET /api/Procesos/HistorialActuaciones/{corp}/{rad}/2` | Array de actuaciones, campo `Orden` incremental |
| `GET /api/ObtenerDatosProcesoGet/{corp}/{numProc}/2` | Datos completos del proceso |
| `GET /api/BuscarProcesoTodoSamai/{numProc}/2` | Buscar proceso |
| `GET /api/Procesos/SujetosProcesales/{corp}/{rad}/2` | Partes procesales |

## Campos clave de una actuación
```json
{
  "A110LLAVPROC": "73001233300020190034300",  // radicado sin guiones
  "Orden": 177,                                // incremental, clave para diff
  "NombreActuacion": "Fijacion estado",
  "Actuacion": "2026-03-20T00:00:00",         // fecha
  "Anotacion": "BBB-...",                      // detalle
  "Estado": "REGISTRADA"
}
```
