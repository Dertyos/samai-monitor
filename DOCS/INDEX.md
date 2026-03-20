# ÍNDICE MAESTRO — samai-monitor (MVP)
## Última actualización: 20 de marzo de 2026

---

# ESTADO DEL PROYECTO

| Fase | Estado | Notas |
|------|--------|-------|
| Fase 0: Setup | COMPLETADA | Python 3.13, SAM CLI, venv, fixtures, CLAUDE.md |
| Fase 1: Capa compartida (TDD) | COMPLETADA | 50 tests, 4 módulos |
| Fase 2: API Handler Lambda | COMPLETADA | 11 tests, 6 endpoints |
| Fase 3: Monitor Lambda | COMPLETADA | 5 tests, check+alertas |
| Fase 4: Deploy AWS | PENDIENTE | SAM template + deploy |
| Fase 5: Frontend React | PENDIENTE | Login, Dashboard, Radicados |
| Fase 6: Deploy frontend + E2E | PENDIENTE | S3/CloudFront + tests E2E |

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
| `models.py` | Dataclasses: Radicado, Actuacion, Alerta (from_api, to/from_dynamo) | HECHO |
| `radicado_utils.py` | normalizar, formatear, validar, extraer_corporacion | HECHO |
| `samai_client.py` | get_actuaciones, get_actuaciones_nuevas, buscar_proceso | HECHO |
| `db.py` | guardar/obtener/eliminar radicados, actuaciones, alertas, dedup | HECHO |

## backend/functions/ — Lambdas
| Archivo | Contenido | Estado |
|---------|-----------|--------|
| `api_handler/app.py` | POST/GET/DELETE radicados, GET alertas/historial/buscar | HECHO |
| `monitor/app.py` | check_radicado + handler (dedup → SAMAI → alertas → email) | HECHO |

## backend/tests/ — Tests
| Archivo | Contenido | Estado |
|---------|-----------|--------|
| `conftest.py` | Fixtures pytest: moto DynamoDB, JSON fixtures | CREADO |
| `test_radicado_utils.py` | 22 tests: normalizar, formatear, validar, extraer | HECHO |
| `test_samai_client.py` | 14 tests: actuaciones, buscar, errores (requests-mock) | HECHO |
| `test_db.py` | 14 tests: CRUD radicados, actuaciones, alertas (moto) | HECHO |
| `test_api_handler.py` | 11 tests: todos los endpoints HTTP | HECHO |
| `test_monitor.py` | 5 tests: check_radicado, multi-usuario, handler | HECHO |
| `fixtures/samai_actuaciones.json` | 177 actuaciones reales (radicado 73001233300020190034300) | GRABADO |
| `fixtures/samai_proceso.json` | Datos completos de proceso real | GRABADO |
| `fixtures/estados_extraidos.json` | 9 estados extraidos por scraping | COPIADO |

## DOCS/ — Documentación
| Archivo | Contenido |
|---------|-----------|
| `INDEX.md` | **ESTE ARCHIVO** |
| `DEV_LOG.md` | Log de desarrollo por sesión |

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
