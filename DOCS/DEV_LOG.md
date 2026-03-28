# Log de Desarrollo — Alertas Judiciales by Dertyos

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

## 2026-03-21 — Sprint 1: UI Foundation

- **Completado**:
  - React Router con rutas reales: `/login`, `/dashboard`, `/radicado/:id`, `/perfil`
  - CSS modular: `theme.css`, `global.css`, `forms.css`, `layout.css`, `modal.css` + 7 CSS modules
  - Forgot Password: flujo completo Cognito (codigo → nueva contraseña)
  - Perfil/Cuenta: email, cambiar contraseña, cerrar sesión
  - Toast Notifications: sistema reutilizable (success/error/info) con auto-dismiss
  - Confirm Modal: reemplaza `window.confirm()` con modal CSS nativo
  - Cascade Delete alertas: al borrar radicado se borran sus alertas (TDD, 2 tests)
  - Total: 71 tests backend en verde, frontend build limpio

- **Archivos creados**:
  - `frontend/src/components/ConfirmModal.tsx` + `.module.css`
  - `frontend/src/components/Toast.tsx` + `.module.css`
  - `frontend/src/context/ToastContext.tsx`
  - `frontend/src/pages/Profile.tsx` + `.module.css`
  - `frontend/src/styles/theme.css`, `global.css`, `forms.css`, `layout.css`, `modal.css`

---

## 2026-03-21 — Sprint 2: Funcionalidad Core

- **Completado**:
  - PATCH /alertas/{sk}/read: marcar alertas como leídas (TDD, 2 tests)
  - Búsqueda/filtro de radicados en Dashboard (client-side por número o alias)
  - PATCH /radicados/{id}: editar alias de radicado (TDD, 2 tests)
  - Búsqueda SAMAI integrada en AddRadicadoModal (buscar → seleccionar → autocompletar)
  - Total: 73 tests backend en verde, frontend build limpio

- **Archivos creados**:
  - `frontend/src/components/AddRadicadoModal.module.css`

- **Endpoints nuevos**:
  - `PATCH /alertas/{sk}/read` → marcar alerta como leída
  - `PATCH /radicados/{id}` → actualizar alias

- **Modelo Alerta actualizado**: nuevo campo `leido: bool = False`

---

## 2026-03-21 — Sprint 3: Funcionalidad Avanzada

- **Completado**:
  - PATCH /radicados/{id} `activo` toggle: pausar/reactivar monitoreo por radicado (TDD, 2 tests)
  - POST /alertas/mark-all-read: marcar todas las alertas como leídas (TDD, 1 test)
  - Descarga de documentos desde historial de actuaciones (link directo a SAMAI)
  - Stale time en React Query + botón manual refresh en Dashboard y Detalle
  - Badge de alertas sin leer en header + título del documento (`(3) Alertas Judiciales`)
  - Ordenar radicados: por recientes, alias (A-Z), o estado (activo primero)
  - Total: 78 tests backend en verde

- **Endpoints nuevos**:
  - `PATCH /radicados/{id}` → toggle campo `activo` (true/false)
  - `POST /alertas/mark-all-read` → marcar todas como leídas

- **Modelo Radicado actualizado**: nuevo campo `activo: bool = True`

---

## 2026-03-21 — Sprint 4: UX Polish

- **Completado**:
  - Filtro/búsqueda de actuaciones en página de detalle (por nombre o anotación)
  - ErrorBoundary global con UI amigable de fallback
  - Stats bar en Dashboard: total radicados, activos, alertas sin leer
  - Exportar actuaciones a CSV desde vista de detalle
  - RadicadoCard: menú dropdown para acciones (editar, pausar, eliminar)
  - Escape key cierra todos los modales abiertos
  - Auto-refresh de alertas cada 60 segundos (polling)
  - Loading skeletons en Dashboard (reemplazan spinners)
  - Empty state mejorado para búsqueda sin resultados
  - Filtro de radicados refactorizado a `useMemo` para mejor rendimiento
  - Timestamp "última actualización" en sección de alertas

- **Archivos creados**:
  - `frontend/src/components/ErrorBoundary.tsx`
  - `frontend/src/components/RadicadoCard.module.css`
  - `frontend/src/components/StatsBar.tsx` (o inline en Dashboard)

- **Decisiones**:
  - Polling 60s para alertas — balance entre frescura y carga de red
  - Skeletons en lugar de spinners para perceived performance
  - Dropdown menu en tarjeta evita botones visualmente pesados
  - CSV export usa Blob + URL.createObjectURL — sin dependencias extra

---

## Checklist de Testeo Manual (post Sprint 4)

Flujos a verificar antes de deploy:

1. **Auth básico**: Login → register → confirm email → login exitoso
2. **Forgot password**: Solicitar código → ingresar código → nueva contraseña → login
3. **Agregar radicado (directo)**: Modal → escribir 23 dígitos → alias → Agregar
4. **Agregar radicado (búsqueda SAMAI)**: Modal → buscar número parcial → seleccionar resultado → alias → Agregar
5. **Editar alias**: Doble click en alias → escribir nuevo → Enter
6. **Ver detalle**: Click en tarjeta → datos proceso + partes + historial actuaciones
7. **Filtrar actuaciones**: Buscar por nombre o anotación en detalle
8. **Exportar CSV**: Botón exportar → descarga CSV con todas las actuaciones
9. **Descargar documento**: Click en ícono de descarga → abre PDF de SAMAI
10. **Marcar alerta como leída**: Click checkmark → alerta cambia a estilo leída
11. **Marcar todas leídas**: Botón "Marcar todas" → todas las alertas cambian
12. **Badge alertas**: Header muestra número de alertas sin leer + título del documento
13. **Pausar monitoreo**: Dropdown → "Pausar" → tarjeta muestra estado inactivo
14. **Eliminar radicado**: Dropdown → "Eliminar" → ConfirmModal → cascade delete alertas
15. **Ordenar radicados**: Selector: recientes / alias / activo
16. **Buscar/filtrar radicados**: Barra → filtro instantáneo por número o alias
17. **Stats bar**: Muestra total radicados, activos, alertas sin leer
18. **Cambiar contraseña**: Perfil → contraseña actual + nueva → confirmar
19. **Tema dark/light**: Toggle en header → persiste en localStorage
20. **Toast notifications**: Verificar en: agregar (success), eliminar (success), error (error)
21. **Loading skeletons**: Dashboard carga con skeletons, no spinners
22. **Auto-refresh alertas**: Esperar 60s → alertas se actualizan solas
23. **ErrorBoundary**: Provocar error → UI amigable con botón reintentar
24. **Responsive**: Mobile (≤640px) → tarjetas apiladas, modal full-width

---

## 2026-03-22 — Deploy: CI/CD + SES Production

- **Completado**:
  - GitLab CI/CD pipeline (`.gitlab-ci.yml`): test → build → deploy automático en push a main
  - IAM user `samai-gitlab-ci` con policy custom `samai-gitlab-ci-deploy` (least privilege)
  - Variables CI/CD configuradas en GitLab (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION)
  - Fix CORS: agregado método PATCH a AllowMethods en API Gateway (faltaba para nuevos endpoints)
  - SES domain identity creada: `samai-monitor.dertyos.com` con DKIM habilitado
  - Solicitud de SES production access enviada (salir del sandbox)
  - Deploy completo: backend (SAM) + frontend (S3 + CloudFront invalidation)
  - SES sender actualizado: `alertas@samai-monitor.dertyos.com`

- **Archivos creados**:
  - `.gitlab-ci.yml` — Pipeline CI/CD de GitLab (4 stages: test, build, deploy)
  - `scripts/gitlab-ci-policy.json` — IAM policy para el usuario CI/CD

- **Pendiente (acción del usuario)**:
  - Agregar 3 registros CNAME DKIM en Cloudflare DNS (ver tokens en SES)
  - Esperar aprobación de AWS para SES production access (~24h)

---

## 2026-03-26 — Registro sin código de verificación (PreSignUp trigger)

### Problema
El flujo de registro anterior requería:
1. Usuario ingresa email + contraseña → `signUp`
2. Cognito llama `CognitoEmailSenderFunction` → envía código por email
3. Usuario copia el código → `confirmSignUp`
4. Login automático → dashboard

Esto añade fricción innecesaria para un sistema B2B de bajo volumen.

### Solución: PreSignUp Lambda trigger

Cognito permite un trigger `PreSignUp` que se ejecuta **antes** de crear el usuario.
Si la Lambda retorna `autoConfirmUser=True` y `autoVerifyEmail=True`, Cognito
marca al usuario como `CONFIRMED` de inmediato, sin enviar ningún código.

**Flujo nuevo:**
1. Usuario ingresa email + contraseña → `signUp`
2. Cognito llama `PreSignUpFunction` → auto-confirma
3. Login automático → dashboard

### Archivos modificados

| Archivo | Cambio |
|---|---|
| `backend/functions/pre_signup/app.py` | **NUEVO** — Lambda de 4 líneas, retorna `autoConfirmUser=True` |
| `template.yaml` | `PreSignUpFunction` + `PreSignUpPermission` + trigger en `UserPool.LambdaConfig.PreSignUp` |
| `frontend/src/pages/Login.tsx` | Eliminado modo `"confirm"`, registro hace `signUp` → `signIn` directo |

### Decisiones de diseño

- **¿Por qué PreSignUp y no `AdminConfirmSignUp` en el backend?**
  PreSignUp es síncrono y más simple: no requiere credenciales admin en el frontend
  ni un endpoint adicional. Cognito lo llama automáticamente.

- **¿Se sigue enviando email de bienvenida/verificación?**
  No. `autoConfirmUser=True` suprime el envío de código de verificación.
  El email de `forgot password` sigue funcionando normalmente (ese usa un trigger diferente).

- **¿Se puede agregar verificación de dominio más adelante?**
  Sí: cambiar `autoConfirmUser` a condicional por dominio de email, o mover
  a una lista de dominios permitidos. El trigger es el lugar correcto para esa lógica.

- **¿Qué pasa con usuarios ya existentes?**
  Sin impacto. El trigger solo aplica a registros nuevos.

---

## 2026-03-26 — Fix correo de verificación en registro (parte 2)

### Contexto
El commit `3d76b21` re-habilitó el flujo de verificación por email al registrarse
(revirtió el auto-confirm del PreSignUp trigger). Sin embargo, la Lambda
`samai-cognito-email-sender` seguía fallando con `InvalidCiphertextException`.

### Causa raíz
`_decrypt_code` usaba `kms_client.decrypt()` directamente (raw KMS API), pero
Cognito cifra el código de verificación usando el **formato del AWS Encryption SDK**
(mensaje envuelto con header + data key cifrada + cuerpo AES-GCM). El raw KMS
no puede leer este formato → `InvalidCiphertextException`.

### Fix 1: AWS Encryption SDK
- Reemplazado `kms_client.decrypt(CiphertextBlob=...)` por
  `aws_encryption_sdk.EncryptionSDKClient.decrypt(source=..., key_provider=...)`
- `aws-encryption-sdk>=3.1.0` ya estaba en `backend/layers/shared/python/requirements.txt`
  pero nunca había sido importado por ninguna Lambda.

### Fix 2: Arquitectura Lambda x86_64
Al importar `aws_encryption_sdk`, la Lambda carga `cryptography/_rust.abi3.so`
(binario nativo Rust). El CI/CD corre en x86_64 y compilaba el `.so` para x86_64,
pero Lambda estaba configurado como `arm64` → fallo de arquitectura.

**Solución**: cambiar `Architectures: arm64` → `x86_64` en `template.yaml`.
El CI siempre corre en x86_64, por lo que los binarios ahora coinciden.

### Verificación en producción
Logs de CloudWatch tras el deploy:
```
[INFO] Cognito email trigger: CustomEmailSender_ResendCode for julian100@dertyos.com
[INFO] Email sent to julian100@dertyos.com for trigger CustomEmailSender_ResendCode
```
Sin `InvalidCiphertextException`. Correos enviados via Resend con dominio `@dertyos.com`.

### Archivos modificados
| Archivo | Cambio |
|---|---|
| `backend/functions/cognito_email_sender/app.py` | `_decrypt_code` usa AWS Encryption SDK |
| `backend/tests/test_cognito_email_sender.py` | Test actualizado para mockear `_enc_client` |
| `template.yaml` | `Architectures: x86_64` (era arm64) |

---

## 2026-03-26 — Fix React Query: caché contaminada entre sesiones de usuario

### Problema
Al cerrar sesión e iniciar con otra cuenta, el nuevo usuario veía brevemente los
radicados de la sesión anterior (caché de React Query no se limpiaba al hacer signOut).
El caso inverso también fallaba: cerrar sesión desde una cuenta con radicados e iniciar
con una cuenta vacía → los radicados de la sesión anterior seguían visibles.

### Causa raíz
`queryClient` estaba definido como variable de módulo en `App.tsx`. React Query mantiene
la caché en memoria durante toda la vida del proceso — al cambiar de usuario, los datos
del usuario anterior seguían en caché y se mostraban hasta el siguiente refetch.

### Solución
1. Extraído `queryClient` a `frontend/src/lib/queryClient.ts` (módulo compartido).
2. Llamar `queryClient.clear()` en `signIn` (para limpiar caché de sesión anterior)
   y en `signOut` (para no exponer datos al siguiente usuario).

### Archivos modificados
| Archivo | Cambio |
|---|---|
| `frontend/src/lib/queryClient.ts` | **NUEVO** — `QueryClient` con `staleTime: 30s, retry: 1` |
| `frontend/src/App.tsx` | Import `queryClient` desde `lib/queryClient` |
| `frontend/src/hooks/useAuth.ts` | `queryClient.clear()` en `signIn` y `signOut` |

---

## 2026-03-26 — Fix SAMAI caído: 503 claro + reducción de timeout

### Problema 1: "Error interno" cuando SAMAI está caído
Al abrir el detalle de un radicado mientras SAMAI devuelve 502/timeout, la `SamaiApiError`
no estaba capturada en `_get_detalle` → propagaba al handler global → devolvía HTTP 500
con mensaje genérico "Error interno". El frontend mostraba "Error: Error interno".

### Solución 1
Envolver `get_datos_proceso`, `get_sujetos_procesales` y `get_actuaciones` en `try/except`:
- Si `get_datos_proceso` falla → retornar HTTP 503 con mensaje claro al usuario.
- Si `get_sujetos_procesales` o `get_actuaciones` fallan → retornar listas vacías (graceful degradation).

### Problema 2: Frontend colgado para siempre
El timeout del cliente SAMAI era 30 segundos, pero API Gateway HTTP corta las Lambda
a los 29 segundos. Si SAMAI no respondía en 30s, Lambda era terminada por API Gateway
antes de poder retornar un error → el frontend recibía un timeout sin mensaje, la UI
mostraba el spinner "Consultando datos del proceso..." indefinidamente.

### Solución 2
Reducido `TIMEOUT = 30` → `TIMEOUT = 15` en `samai_client.py`. 15 segundos deja margen
para que Lambda retorne un 503 limpio antes del corte de API Gateway.

### Archivos modificados
| Archivo | Cambio |
|---|---|
| `backend/layers/shared/python/samai_client.py` | `TIMEOUT = 15` (era 30) |
| `backend/functions/api_handler/app.py` | `_get_detalle`: try/except para SamaiApiError, 503 con mensaje claro |

---

## 2026-03-26 — Fix corporación incorrecta en "Ver en SAMAI" (auto-heal)

### Problema
El botón "Ver en SAMAI" construye la URL con el código de corporación almacenado:
```
https://samai.consejodeestado.gov.co/...?guid={radicado}-{corporacion}
```
Algunos radicados mostraban el error: **"El proceso XXX no Existe en la Corporación 1100133"**.

### Causa raíz
Cuando se registra un radicado y SAMAI está caído en ese momento, `encontrar_corporacion()`
falla en todos sus 28 requests → retorna `None` → el radicado se guarda con la corporación
por defecto (`extraer_corporacion()` = primeros 7 dígitos del radicado, ej. `1100133`).
Cuando SAMAI vuelve a estar disponible, la corporación almacenada puede ser incorrecta
(el proceso puede estar en Consejo de Estado `1100103` o en un Tribunal diferente).

### Solución: Auto-heal en `_get_detalle`
Al consultar el detalle, si `get_datos_proceso(corp_almacenada, radicado)` retorna vacío
(la corporación es incorrecta pero SAMAI está disponible):
1. Llamar `encontrar_corporacion(radicado, excluir=[corp_almacenada])` — búsqueda paralela en 28 corporaciones.
2. Si se encuentra una corporación correcta, actualizar DynamoDB con `actualizar_corporacion()`.
3. Reintentar `get_datos_proceso`, `get_sujetos_procesales` y `get_actuaciones` con la corporación nueva.
4. Retornar `corporacion: corp_usada` en la respuesta → el frontend usa el valor correcto para la URL de SAMAI.

La corrección es **permanente**: los siguientes accesos ya usan la corporación correcta directamente.

### Archivos modificados
| Archivo | Cambio |
|---|---|
| `backend/layers/shared/python/db.py` | **NUEVO** `actualizar_corporacion()` — `update_item` sobre campo `corporacion` |
| `backend/functions/api_handler/app.py` | Import `actualizar_corporacion` + lógica auto-heal en `_get_detalle` |

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

---

## 2026-03-28 — Bug Fix: Alertas históricas al agregar proceso nuevo

### Problema
Al agregar un proceso nuevo, si `get_max_orden` falla (timeout, API down) devuelve 0 y se
guarda `ultimoOrden=0`. En la siguiente ejecución del monitor, TODAS las actuaciones
históricas (orden > 0) se trataban como "nuevas" → spam de alertas con actuaciones viejas.

Ejemplo real: proceso `25000-23-42-000-2024-00350-00` notificó actuaciones de 2025-09 y
2026-02 como si fueran nuevas al ser agregado.

### Causa raíz
El API handler hacía `max_orden = 0` silenciosamente al recibir `SamaiApiError`, sin
distinguir entre "genuinamente 0 actuaciones" (proceso nuevo sin historia) vs
"no se pudo consultar la API". Con `ultimoOrden=0` guardado, el monitor enviaba alertas
para todo lo que tuviera `orden > 0`, es decir, toda la historia del proceso.

### Fix: campo `pendingInit`
- **`models.py`**: Campo `pending_init: bool = False` en `Radicado`. Se persiste como
  `pendingInit` en DynamoDB solo cuando `True`.
- **`api_handler/app.py`**: Cuando la API lanza excepción Y el `max_orden` queda en 0
  después de todos los fallbacks, se guarda `pendingInit=True`. Para rama_judicial y siugj
  también se setea en el respectivo `ApiError`.
- **`monitor/app.py`**: En las 3 funciones `check_radicado*`, si `pendingInit=True`:
  actualizar `ultimoOrden` al máximo actual y limpiar el flag SIN crear alertas.
- **`db.py`**: Nueva función `limpiar_pending_init()` que hace `REMOVE pendingInit` en
  DynamoDB.

### Nota sobre registros existentes
Los procesos ya registrados con `ultimoOrden=0` que YA generaron alertas: el monitor ya
actualizó su `ultimoOrden` al correr. No generarán más alertas incorrectas.

### Archivos modificados
- `backend/layers/shared/python/models.py`
- `backend/layers/shared/python/db.py`
- `backend/functions/api_handler/app.py`
- `backend/functions/monitor/app.py`

---

### Fase 13: Seguridad y Compliance
- Rate limiting en API Gateway
- WAF rules para proteger endpoints
- Audit logging (CloudTrail)
- GDPR/Habeas Data compliance (eliminación de datos de usuario)
