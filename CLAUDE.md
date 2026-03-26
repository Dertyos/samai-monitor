# CLAUDE.md — Alertas Judiciales by Dertyos

## Proyecto
SaaS de monitoreo judicial para SAMAI (jurisdicción contencioso-administrativa, Colombia).
Abogados registran radicados, el sistema detecta actuaciones nuevas via API REST y envía alertas.

## Documentación
- **Índice maestro**: `DOCS/INDEX.md`
- **Log de desarrollo**: `DOCS/DEV_LOG.md`
- **Investigación original**: `../EstadosUpdates/DOCS/INDEX.md`

## Arquitectura
- **2 Lambdas**: `api_handler` (CRUD API Gateway) + `monitor` (EventBridge diario)
- **Capa compartida**: `backend/layers/shared/python/` (samai_client, db, radicado_utils, models)
- **Frontend**: React + Vite + TypeScript
- **IaC**: AWS SAM (`template.yaml`)
- **Auth**: Cognito User Pool con JWT

## API SAMAI (externa)
- Base: `https://samaicore.consejodeestado.gov.co/api/`
- Historial: `GET /api/Procesos/HistorialActuaciones/{corp}/{radicado}/2`
- Datos proceso: `GET /api/ObtenerDatosProcesoGet/{corp}/{numProceso}/2`
- Buscar: `GET /api/BuscarProcesoTodoSamai/{numProceso}/2`
- Partes: `GET /api/Procesos/SujetosProcesales/{corp}/{radicado}/2`
- Descargar PDF: `GET /api/DescargarProvidenciaPublica/{corp}/{numProceso}/{hash}/2`
- Parámetro `modo`: siempre `2` (consulta pública)

## Reglas Python (backend)

### Tipado estricto
- TODOS los parámetros y retornos con type hints
- Usar `from __future__ import annotations` en cada archivo
- Usar tipos modernos: `list[str]` no `List[str]`, `dict[str, Any]` no `Dict`

### Modelos
- Usar `@dataclass` para modelos (`Radicado`, `Actuacion`, `Alerta`)
- NO usar dicts sueltos para datos estructurados
- Cada modelo en `models.py`

### Inyección de dependencias
- `SamaiClient` se pasa como parámetro, no se importa como global
- Funciones DB reciben `table` como parámetro (boto3 Table resource)
- Lambdas instancian dependencias en el handler, las pasan a funciones de negocio

### SOLID
- `samai_client.py`: solo habla con la API REST de SAMAI
- `db.py`: solo habla con DynamoDB
- `radicado_utils.py`: solo validación y formato de radicados
- `models.py`: solo dataclasses
- Lambdas (`app.py`): solo orquestan, no tienen lógica de negocio

### TDD estricto
- NO se escribe código de producción sin test previo
- Flujo: test rojo → implementar mínimo → test verde → refactor
- `@pytest.mark.unit` para tests con mocks
- `@pytest.mark.integration` para tests contra SAMAI real
- Ejecutar: `make test` (solo unit), `make test-integration` (SAMAI real)

### Logging
- Usar `logging` con niveles (DEBUG, INFO, WARNING, ERROR)
- NO usar `print()`
- Logger por módulo: `logger = logging.getLogger(__name__)`

## Reglas TypeScript (frontend)
- `strict: true` en tsconfig.json
- NO usar `any` — tipos explícitos en todo
- React Query para data fetching
- Componentes funcionales con hooks

## Reglas generales
- Commits atómicos por feature/fix
- Cada fase termina con tests en verde
- No agregar dependencias innecesarias
- Preferir stdlib sobre librería externa cuando sea razonable

## Deploy
- **GitLab CI/CD** (`.gitlab-ci.yml`) despliega automáticamente al hacer push a `main`
- Pipeline: tests backend → tests frontend → SAM build → SAM deploy + S3 sync + CloudFront invalidation
- NO hacer `sam deploy` ni `aws s3 sync` manualmente

## Comandos locales
```bash
make test              # Unit tests (pytest + moto + requests-mock)
make test-integration  # Tests contra SAMAI real
make build             # SAM build (solo local, CI lo hace en main)
make lint              # (futuro) ruff/mypy
```
