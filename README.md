# SAMAI Monitor

Monitor automatizado de estados judiciales del sistema SAMAI (jurisdicción contencioso-administrativa, Colombia).

Abogados registran radicados y el sistema detecta actuaciones nuevas vía la API pública de SAMAI, enviando alertas por correo electrónico.

## Stack

- **Backend**: Python 3.13, AWS Lambda, DynamoDB, Cognito, SES
- **Frontend**: React + Vite + TypeScript
- **Infraestructura**: AWS SAM (IaC), API Gateway v2, EventBridge, S3, CloudFront
- **Testing**: pytest + moto + requests-mock (66 tests)

## Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Frontend    │────▶│ API Gateway  │────▶│  API Handler     │
│  React SPA   │     │  + Cognito   │     │  Lambda          │
│  (CloudFront)│     │  JWT Auth    │     │  (CRUD radicados)│
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                    ┌──────────────┐     ┌─────────▼────────┐
                    │  EventBridge │────▶│  Monitor Lambda   │
                    │  (cron diario)│     │  (detecta nuevas  │
                    └──────────────┘     │   actuaciones)    │
                                         └────────┬────────┘
                                                   │
                    ┌──────────────┐     ┌─────────▼────────┐
                    │  DynamoDB    │     │  API SAMAI        │
                    │  (radicados, │     │  (Consejo de      │
                    │   alertas)   │     │   Estado)         │
                    └──────────────┘     └──────────────────┘
                                                   │
                                         ┌─────────▼────────┐
                                         │  SES (email       │
                                         │   alertas)        │
                                         └──────────────────┘
```

## Estructura del proyecto

```
samai-monitor/
├── backend/
│   ├── functions/
│   │   ├── api_handler/app.py    # CRUD API (6 endpoints)
│   │   └── monitor/app.py        # Detección de actuaciones nuevas
│   ├── layers/shared/python/
│   │   ├── samai_client.py       # Cliente REST para API SAMAI
│   │   ├── db.py                 # CRUD DynamoDB
│   │   ├── models.py             # Dataclasses (Radicado, Actuacion, Alerta)
│   │   └── radicado_utils.py     # Validación y formato de radicados
│   └── tests/                    # 66 unit tests
├── frontend/
│   └── src/
│       ├── pages/                # Login, Dashboard, Historial
│       ├── components/           # RadicadoCard, AlertasList, AddRadicadoModal
│       ├── hooks/                # useAuth, useTheme
│       └── lib/                  # API client, Cognito wrapper, utils
├── template.yaml                 # AWS SAM (IaC completo)
├── samconfig.toml                # Config de deploy
└── Makefile                      # test, build, deploy
```

## Endpoints API

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/radicados` | Registrar radicado para monitoreo |
| GET | `/radicados` | Listar radicados del usuario |
| DELETE | `/radicados/{id}` | Eliminar radicado |
| GET | `/radicados/{id}/historial` | Historial de actuaciones |
| GET | `/buscar/{numProceso}` | Buscar proceso en SAMAI |
| GET | `/alertas` | Listar alertas del usuario |

## Desarrollo local

```bash
# Requisitos
python 3.13+
node 18+
aws-sam-cli

# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt -r backend/requirements-dev.txt

# Tests
make test                # Unit tests (moto + requests-mock)
make test-integration    # Tests contra SAMAI real

# Frontend
cd frontend
npm install
npm run dev              # http://localhost:5173

# Deploy
make build && make deploy
```

## Licencia

Uso privado.
