# Log de Desarrollo — SAMAI Monitor

---

## 2026-03-20 — Fase 0: Setup del Proyecto

- **Completado**:
  - Verificado Python 3.13.12 (brew), SAM CLI 1.156.0
  - Creada estructura de directorios completa
  - Inicializado git repo (branch: main)
  - Creado `CLAUDE.md` con reglas de código
  - Creado `.gitignore`
  - Creado venv con Python 3.13 (`.venv/`)
  - Instaladas dependencias: pytest, moto, requests-mock, freezegun, boto3, requests
  - Creado `Makefile` con targets: test, test-integration, test-cov, build, deploy
  - Creado `pytest.ini` con markers (unit, integration) y pythonpath
  - Creado `conftest.py` con fixtures moto (3 tablas DynamoDB)
  - Grabada respuesta real API SAMAI: 177 actuaciones (`samai_actuaciones.json`)
  - Grabada respuesta real datos proceso (`samai_proceso.json`)
  - Copiado `estados_extraidos.json` de investigación previa
  - Creado `DOCS/INDEX.md` y `DOCS/DEV_LOG.md`

- **Archivos creados**:
  - `CLAUDE.md`, `.gitignore`, `Makefile`, `pytest.ini`
  - `backend/requirements.txt`, `backend/requirements-dev.txt`
  - `backend/tests/conftest.py`
  - `backend/tests/fixtures/samai_actuaciones.json` (177 records)
  - `backend/tests/fixtures/samai_proceso.json`
  - `backend/tests/fixtures/estados_extraidos.json` (9 records)
  - `DOCS/INDEX.md`, `DOCS/DEV_LOG.md`

- **Decisiones**:
  - Campo `Orden` (numérico incremental) en respuesta API es la clave para detectar actuaciones nuevas
  - 3 tablas DynamoDB: radicados, actuaciones, alertas
  - GSIs: radicado-index (dedup consultas), corporacion-index (agrupar por corp)

- **Siguiente**: Fase 1

---

## 2026-03-20 — Fase 1: Capa Compartida (TDD)

- **Completado**:
  - `radicado_utils.py`: normalizar, formatear, validar, extraer corporación (22 tests)
  - `models.py`: dataclasses Actuacion, Radicado, Alerta con `from_api()`, `to_dynamo()`, `from_dynamo()`
  - `samai_client.py`: cliente REST con get_actuaciones, get_actuaciones_nuevas, get_max_orden, buscar_proceso (14 tests)
  - `db.py`: CRUD DynamoDB — guardar/obtener/eliminar radicados, dedup, actuaciones, alertas (14 tests)
  - Total: 50 tests en verde

- **Archivos creados**:
  - `backend/layers/shared/python/radicado_utils.py`
  - `backend/layers/shared/python/models.py`
  - `backend/layers/shared/python/samai_client.py`
  - `backend/layers/shared/python/db.py`
  - `backend/tests/test_radicado_utils.py` (22 tests)
  - `backend/tests/test_samai_client.py` (14 tests)
  - `backend/tests/test_db.py` (14 tests)

- **Decisiones**:
  - `SamaiApiError` wraps tanto `requests.RequestException` como `ConnectionError`
  - `obtener_radicados_unicos()` usa scan + dedup en memoria (OK para MVP con <1000 radicados)
  - Actuacion.from_api() mapea campos SAMAI (A110LLAVPROC, Orden, NombreActuacion, etc.) a nombres legibles

---

## 2026-03-20 — Fase 2: API Handler Lambda (TDD)

- **Completado**:
  - POST /radicados (201, 400 validación, 409 duplicado)
  - GET /radicados (listar)
  - DELETE /radicados/{id} (204, 404)
  - GET /radicados/{id}/historial (proxy a SAMAI API)
  - GET /buscar/{numProceso} (proxy a SAMAI)
  - GET /alertas (listar)
  - Total: 11 tests nuevos, 61 acumulados

- **Archivos creados**:
  - `backend/functions/api_handler/app.py`
  - `backend/functions/api_handler/__init__.py`
  - `backend/functions/__init__.py`
  - `backend/tests/test_api_handler.py` (11 tests)

- **Decisiones**:
  - Router simple por method+path (sin framework HTTP extra)
  - `samai_client` como variable de módulo para permitir mocking en tests
  - JWT claims extraídos de `event.requestContext.authorizer.jwt.claims.sub`

---

## 2026-03-20 — Fase 3: Monitor Lambda (TDD)

- **Completado**:
  - `check_radicado()`: consulta SAMAI, detecta novedades, crea alertas por usuario
  - Deduplicación: consulta mínimo último_orden entre seguidores de un radicado
  - Alertas personalizadas: cada usuario recibe solo las actuaciones nuevas para él
  - Actualización automática de último_orden tras detectar novedades
  - `handler()`: orquesta flujo completo (dedup → check → alertas → email)
  - `_send_email_alerts()`: placeholder para SES (solo loguea por ahora)
  - Total: 5 tests nuevos, 66 acumulados — todos en verde

- **Archivos creados**:
  - `backend/functions/monitor/app.py`
  - `backend/functions/monitor/__init__.py`
  - `backend/tests/test_monitor.py` (5 tests)

- **Decisiones**:
  - check_radicado recibe dependencias como parámetros (DI) para testabilidad
  - GSI radicado-index para encontrar todos los seguidores de un radicado
  - Errores parciales: si un radicado falla, continúa con los demás y cuenta errores
  - SES pendiente: se implementará cuando haya dominio verificado

- **Siguiente**: Fase 4 — template.yaml SAM + primer deploy AWS

---

## 2026-03-20 — Fase 4: Deploy AWS

- **Completado**:
  - `template.yaml` completo: 2 Lambdas, 3 DynamoDB, Cognito, API Gateway v2, EventBridge, S3, CloudFront
  - `samconfig.toml` para deploy no interactivo
  - Stack `samai-monitor` desplegado en us-east-1
  - Usuario de prueba creado en Cognito: `juliansalcedo4@gmail.com`
  - Todos los 6 endpoints API verificados con JWT token real
  - Monitor Lambda invocado manualmente: 177 actuaciones detectadas, 177 alertas creadas
  - SES email implementado (sender verificado: juliansalcedo4@gmail.com)
  - Monitor envía correos HTML con resumen de actuaciones nuevas

- **Bugs encontrados y corregidos**:
  1. `USER_PASSWORD_AUTH` no habilitado en Cognito → agregado a ExplicitAuthFlows
  2. JWT Authorizer `Forbidden` → removido `AuthorizationScopes: [openid]`
  3. Lambda `ImportModuleError` (No module named 'models') → ContentUri apuntaba mal, doble nesting `python/python/`
  4. API rutas retornaban "Ruta no encontrada" → API Gateway v2 incluye stage prefix en path (`/prod/radicados`), se agregó strip del stage prefix en el handler
  5. Alerta `sk` no era único → `created_at#radicado` duplicaba, se agregó `#orden` al sk
  6. `BuscarProcesoTodoSamai` retorna body vacío → `_get()` ahora maneja respuestas vacías

- **Archivos creados/modificados**:
  - `template.yaml` (creado y modificado varias veces)
  - `samconfig.toml`
  - `backend/functions/api_handler/app.py` (stage prefix strip)
  - `backend/functions/monitor/app.py` (SES email: _send_email_alerts, _get_user_email, _build_alert_email)
  - `backend/layers/shared/python/models.py` (sk con orden)
  - `backend/layers/shared/python/samai_client.py` (empty response handling)

- **Recursos AWS desplegados**:
  - API URL: `https://weo3vfe321.execute-api.us-east-1.amazonaws.com/prod`
  - User Pool: `us-east-1_fD99TyD9S`
  - Client ID: `2a1dun36pjrsgdj3bg0plms81k`
  - Monitor ARN: `arn:aws:lambda:us-east-1:236578428550:function:samai-monitor`
  - CloudFront: `https://drwlltutwjjfd.cloudfront.net`
  - S3 bucket: `samai-frontend-236578428550`

---

## 2026-03-20 — Fase 5: Frontend React + Vite + TypeScript

- **Completado**:
  - Scaffolded con `npm create vite@latest -- --template react-ts`
  - Dependencias: `amazon-cognito-identity-js`, `react-router-dom`, `@tanstack/react-query`
  - Cognito auth completo: sign in, sign up, confirm, sign out
  - API client con fetch + JWT bearer token
  - Páginas: Login (con registro/confirmación), Dashboard, Historial
  - Componentes: RadicadoCard, AlertasList, AddRadicadoModal
  - CSS responsive (mobile-friendly)
  - TypeScript strict, 0 errores de compilación
  - Build de producción: 325KB JS + 5.7KB CSS (gzipped: ~100KB)

- **Archivos creados**:
  - `frontend/src/config/auth.ts` — Cognito config + API URL
  - `frontend/src/lib/cognito.ts` — Cognito SDK wrapper
  - `frontend/src/lib/api.ts` — API client (typed DTOs)
  - `frontend/src/hooks/useAuth.ts` — Auth state hook
  - `frontend/src/pages/Login.tsx` — Login/registro/confirmación
  - `frontend/src/pages/Dashboard.tsx` — Lista radicados + alertas
  - `frontend/src/pages/Historial.tsx` — Timeline actuaciones
  - `frontend/src/components/RadicadoCard.tsx`
  - `frontend/src/components/AlertasList.tsx`
  - `frontend/src/components/AddRadicadoModal.tsx`
  - `frontend/src/App.tsx`, `frontend/src/App.css`

---

## 2026-03-20 — Fase 6: Deploy Frontend + E2E

- **Completado**:
  - S3 bucket `samai-frontend-236578428550` creado via SAM
  - CloudFront distribution con OAC (Origin Access Control)
  - SPA routing: 403/404 → index.html (para React Router)
  - Frontend desplegado: `aws s3 sync dist/ s3://...`
  - Cognito callback URLs actualizadas para CloudFront + dominio personalizado
  - Frontend live en: `https://drwlltutwjjfd.cloudfront.net`

- **Pendiente**:
  - Custom domain `samai-monitor.dertyos.com` (requiere ACM certificate + Cloudflare DNS)
  - E2E test completo (el flujo funciona pero falta test automatizado)

- **Siguiente**: Configurar dominio personalizado cuando el usuario esté disponible

---

## 2026-03-20 — Fase 7: UI/UX Improvements + Dark Mode

- **Completado**:
  - Dark mode completo con CSS custom properties (`[data-theme="dark"]`)
  - `useTheme` hook: persiste preferencia en localStorage, respeta `prefers-color-scheme`
  - Toggle de tema en Dashboard header y Login page
  - Decodificación de entidades HTML (&#233; → é) en anotaciones y nombres de actuaciones
  - AlertasList mejorada: muestra `timeAgo` de cuándo se creó cada alerta
  - Empty states mejorados con iconos y textos descriptivos
  - AddRadicadoModal: auto-formateo del radicado con guiones mientras se escribe, validación visual (23 dígitos), botón deshabilitado hasta input válido
  - Loading states mejorados con spinners en lugar de texto plano
  - Eliminada variable `selectedRadicado` no utilizada
  - CSS: estilos para `.empty-state`, `.input-warning`, `.input-hint`, `.alerta-time-ago`, `.login-theme-toggle`
  - Build: 328KB JS + 10.7KB CSS (gzipped: ~100KB + 2.7KB)
  - Deploy a S3 + CloudFront invalidación
  - 66 tests backend siguen en verde

- **Archivos creados**:
  - `frontend/src/hooks/useTheme.ts`

- **Archivos modificados**:
  - `frontend/src/App.tsx` (spinner en loading screen)
  - `frontend/src/App.css` (input-warning, empty-state, alerta-time-ago, login-theme-toggle)
  - `frontend/src/pages/Dashboard.tsx` (useTheme, toggle, empty states, spinners)
  - `frontend/src/pages/Login.tsx` (useTheme, toggle button)
  - `frontend/src/pages/Historial.tsx` (decodeHtml en nombres y anotaciones)
  - `frontend/src/components/AlertasList.tsx` (decodeHtml, timeAgo)
  - `frontend/src/components/AddRadicadoModal.tsx` (auto-format, validación)
  - `frontend/src/lib/utils.ts` (decodeHtml helper)

- **Decisiones**:
  - Dark mode usa CSS custom properties — fácil de mantener y extender
  - Preferencia de tema persiste en localStorage, con fallback a OS preference
  - HTML entity decoding via `textarea.innerHTML` — seguro y handles all entities
  - Radicado auto-format inserta guiones automáticamente — UX más intuitiva

---

## Fases Futuras (v2+)

### Fase 8: Custom Domain + SSL
- Solicitar certificado ACM en us-east-1 para `samai-monitor.dertyos.com`
- Configurar Cloudflare DNS: CNAME apuntando a CloudFront
- Actualizar CloudFront con Alias + certificado ACM
- Actualizar Cognito callback URLs

### Fase 9: SES Production Access
- Salir del sandbox de SES para poder enviar a cualquier email
- Verificar dominio `dertyos.com` en SES (DNS TXT + DKIM)
- Crear plantilla HTML profesional para emails de alertas

### Fase 10: Mejoras de Monitoreo
- Dashboard de salud: última ejecución del monitor, errores recientes
- Configurar frecuencia de monitoreo por radicado (diario, cada 6h, etc.)
- Notificaciones push (web push notifications)
- Exportar historial a PDF/Excel

### Fase 11: Multi-jurisdicción
- Agregar soporte para Rama Judicial (TYBA) además de SAMAI
- Normalizar modelo de datos para múltiples fuentes
- UI para seleccionar jurisdicción al agregar radicado

### Fase 12: Planes y Facturación
- Stripe integration para pagos
- Plan gratuito: hasta 3 radicados
- Plan Pro: radicados ilimitados + notificaciones frecuentes
- Admin dashboard para ver métricas de usuarios

### Fase 13: Seguridad y Compliance
- Rate limiting en API Gateway
- WAF rules para proteger endpoints
- Audit logging (CloudTrail)
- GDPR/Habeas Data compliance (eliminación de datos de usuario)
