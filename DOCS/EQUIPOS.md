# Equipos — Planes Compartidos

Guia completa del sistema de equipos para planes Firma y Enterprise.

---

## Concepto

Un usuario con plan **Firma** ($79,900/mes, 150 procesos) o **Enterprise** (1000 procesos) puede crear un equipo e invitar miembros. Todos los radicados de todos los miembros cuentan contra el limite del equipo. Si 2 miembros siguen el mismo radicado, cuenta como 1.

**Regla fundamental**: un usuario solo tiene UNA suscripcion activa a la vez. No existe "radicados personales" y "radicados del equipo" simultaneamente. Si perteneces a un equipo con suscripcion activa, TODOS tus radicados cuentan contra el limite del equipo.

---

## Limites

| Plan | Procesos | Miembros max |
|------|----------|-------------|
| Firma | 150 | 5 |
| Enterprise | 1000 | 30 |

---

## Tablas DynamoDB

### samai-teams
```
PK: teamId (string, UUID hex 16 chars)
Attributes:
  teamId, name, ownerUserId, planId, createdAt
  pendingConfirmation (bool, opcional — true tras renovar suscripcion)
```

### samai-team-members
```
PK: teamId
SK: userId
GSI: userId-index (PK: userId) — para buscar equipos de un usuario
Attributes:
  teamId, userId, role ("owner" | "member"), joinedAt
```

No hay campo `teamId` en la tabla de radicados. Los radicados de un equipo se calculan obteniendo todos los miembros y luego todos los radicados de cada miembro.

---

## Endpoints API

### CRUD Equipos

| Metodo | Path | Descripcion | Quien |
|--------|------|-------------|-------|
| `POST /teams` | Crear equipo | Solo usuarios con plan Firma o Enterprise |
| `GET /teams` | Listar equipos del usuario (con estado, miembros, conteo) | Cualquier miembro |
| `POST /teams/{teamId}/members` | Invitar miembro por email | Solo el owner |
| `DELETE /teams/{teamId}/members/{uid}` | Quitar miembro (o salir del equipo) | Owner o el propio miembro |
| `POST /teams/{teamId}/confirm` | Confirmar equipo tras renovar suscripcion | Solo el owner |

### Respuesta de GET /teams

```json
[
  {
    "teamId": "abc123...",
    "name": "Firma Aviles & Asoc.",
    "ownerUserId": "user-xxx",
    "planId": "plan-firma",
    "createdAt": "2026-04-03T...",
    "active": true,
    "pendingConfirmation": false,
    "processLimit": 150,
    "processCount": 47,
    "members": [
      {"teamId": "abc123", "userId": "user-xxx", "role": "owner", "joinedAt": "..."},
      {"teamId": "abc123", "userId": "user-yyy", "role": "member", "joinedAt": "..."}
    ]
  }
]
```

- `active`: true si el owner tiene suscripcion Firma/Enterprise activa
- `pendingConfirmation`: true si el equipo necesita confirmacion del owner tras renovar

---

## Enforcement de limites

### Al agregar un radicado (POST /radicados)

```
1. Buscar si el usuario pertenece a un equipo (via userId-index en team-members)
2. Si pertenece a un equipo:
   a. Verificar que el owner tiene suscripcion activa (Firma/Enterprise)
   b. Si NO tiene → equipo inactivo, caer a enforcement personal (paso 3)
   c. Si SI tiene → contar procesos del equipo (todos los miembros, dedup)
   d. Si count >= limite → 403 PLAN_LIMIT_REACHED
3. Si NO pertenece a equipo (o equipo inactivo):
   a. Contar radicados personales del usuario
   b. Comparar con su plan personal (o gratis = 5)
   c. Si count >= limite → 403 PLAN_LIMIT_REACHED
```

Archivo: `backend/functions/api_handler/app.py`, lineas ~315-355

### Monitor diario (_enforce_plan_limits)

Se ejecuta ANTES de consultar SAMAI. Para cada usuario:

```
1. Calcular limite efectivo:
   - Si pertenece a equipo activo → limite del equipo
   - Si no → limite de su plan personal (o gratis = 5)
2. Ordenar radicados por createdAt (primero agregado = primero conservado)
3. Los primeros N → activo=True (reactivar si estaban inactivos)
4. Los demas → activo=False (desactivar)
```

Los radicados con `activo=False` NO se consultan en el monitoreo.

Archivo: `backend/functions/monitor/app.py`, funcion `_enforce_plan_limits`

---

## Flujo de pago / renovacion

### Primera vez (nuevo equipo)

```
1. Usuario compra plan Firma/Enterprise en /billing
2. Webhook Wompi confirma pago → activa suscripcion
3. Monitor reactivates radicados del owner (async)
4. Owner va a Perfil > Mi Equipo > Crear equipo
5. Invita miembros por email
6. Los miembros ahora tienen sus radicados contando contra el limite del equipo
```

### Renovacion (equipo existente)

```
1. Wompi confirma pago
2. Webhook:
   a. Activa suscripcion
   b. Marca equipo como pendingConfirmation=true
   c. Invoca monitor async → reactivar solo radicados del OWNER
3. Owner entra al Dashboard:
   a. Ve banner: "Tu suscripcion esta activa. Tu equipo X tiene N miembros."
   b. [Confirmar equipo] → POST /teams/{id}/confirm
      - Quita pendingConfirmation
      - Invoca monitor async para cada miembro → reactivar sus radicados
   c. [Administrar miembros] → va a Perfil, ajusta miembros, luego confirma
```

**Por que pendingConfirmation?** Porque el owner podria querer cambiar miembros antes de reactivar a todos. Si se reactivaran automaticamente, podria haber sorpresas (miembros que ya no deberian estar, radicados de gente que salio, etc).

### Suscripcion vencida

```
1. El monitor diario ejecuta _enforce_plan_limits
2. El owner ya no tiene suscripcion activa
3. Cada miembro cae a su plan personal:
   - Sin suscripcion propia → gratis = 5 radicados (los primeros por createdAt)
   - Con suscripcion propia → limite de su plan
4. Los radicados excedentes pasan a activo=False
5. El equipo sigue existiendo en DynamoDB pero con active=false
6. En Perfil se muestra "Inhabilitado (suscripcion vencida)" con boton "Renovar"
7. No se pueden agregar nuevos radicados al equipo ni invitar miembros
```

---

## Frontend

### Dashboard
- **Banner de confirmacion**: aparece cuando `pendingTeam` existe (equipo activo + pendingConfirmation). Dos botones: "Confirmar equipo" y "Administrar miembros".

### Perfil > Mi Equipo
- **Crear equipo**: solo si tiene plan Firma/Enterprise y no tiene equipo
- **Estado**: Activo (verde) o Inhabilitado (rojo)
- **Conteo**: procesos usados / limite
- **Lista de miembros**: con boton "Quitar" para cada uno (excepto owner)
- **Invitar**: formulario de email (solo si equipo activo)
- **Suscripcion vencida**: mensaje amarillo con boton "Renovar suscripcion"

### AddRadicadoModal
- No tiene selector de equipo. Si el usuario pertenece a un equipo activo, el backend automaticamente cuenta contra el limite del equipo.

---

## Archivos clave

| Archivo | Que hace |
|---------|----------|
| `template.yaml` | Tablas TeamsTable, TeamMembersTable + env vars + permisos |
| `models.py` | Dataclasses `Team` (con pendingConfirmation), `TeamMember` |
| `db.py` | CRUD teams, miembros, contar_procesos_equipo (dedup), confirmar_team |
| `api_handler/app.py` | 5 endpoints de teams + enforcement en _post_radicado |
| `monitor/app.py` | _enforce_plan_limits, _reactivate_and_check_user, _get_user_effective_limit |
| `billing_webhook/app.py` | Post-pago: marca pendingConfirmation, invoca monitor async |
| `frontend/src/lib/api.ts` | TeamDTO, TeamMemberDTO, getTeams, createTeam, confirmTeam, etc. |
| `frontend/src/pages/Dashboard.tsx` | Banner de confirmacion post-renovacion |
| `frontend/src/pages/Perfil.tsx` | Seccion "Mi Equipo" |
| `frontend/src/pages/Invite.tsx` | Pagina publica /invite/{token} |
| `backend/functions/post_confirmation/app.py` | PostConfirmation Lambda — auto-acepta invitaciones al registrarse |

---

## Constantes

```python
# api_handler/app.py
TEAM_ELIGIBLE_PLANS = {"plan-firma", "plan-enterprise"}
MAX_TEAM_MEMBERS = {"plan-firma": 5, "plan-enterprise": 30}
FREE_PLAN_LIMIT = 5

# Limites por plan
PLAN_LIMITS = {
    "plan-gratuito": 5,
    "plan-pro": 25,
    "plan-pro-plus": 70,
    "plan-firma": 150,
    "plan-enterprise": 1000,
}
```

---

## Sistema de Invitaciones

### Tabla DynamoDB: samai-team-invitations
```
PK: inviteId (UUID hex 16 chars)
GSI: email-index (PK: email) — buscar invitaciones pendientes al registrarse
GSI: teamId-index (PK: teamId) — listar invitaciones del equipo
TTL: ttl (epoch, 7 dias) — DynamoDB auto-elimina expiradas
Attributes:
  inviteId, teamId, email, role, invitedBy, status, token (UUID hex), createdAt, ttl
```

### Flujo de invitacion

**Email registrado en Cognito:**
```
1. Owner invita por email → POST /teams/{id}/members
2. Backend busca en Cognito → usuario encontrado
3. Agrega al equipo de inmediato
4. Envia email de notificacion: "Te agregaron al equipo X"
5. Si tiene plan personal activo → avisa al owner en la respuesta
```

**Email NO registrado:**
```
1. Owner invita por email → POST /teams/{id}/members
2. Backend busca en Cognito → no encontrado
3. Crea invitacion pendiente (token UUID, TTL 7 dias)
4. Envia email de invitacion: "Te invitaron a X" con link /invite/{token}
5. El invitado abre el link:
   a. Si ya tiene cuenta → login → POST /invitations/{token}/accept → se agrega al equipo
   b. Si no tiene cuenta → signup → PostConfirmation Lambda procesa la invitacion automaticamente
6. Invitacion expira en 7 dias. El owner puede reenviar (crea nueva invitacion).
```

### Endpoints de invitaciones

| Metodo | Path | Auth | Descripcion |
|--------|------|------|-------------|
| `GET /invitations/{token}` | NO | Consultar info de invitacion (publica, para la pagina /invite) |
| `POST /invitations/{token}/accept` | SI | Aceptar invitacion (requiere login) |

### PostConfirmation Lambda

`backend/functions/post_confirmation/app.py` — trigger de Cognito que se ejecuta cuando un usuario confirma su cuenta. Busca invitaciones pendientes para su email y lo agrega a los equipos automaticamente.

### Frontend: /invite/{token}

Pagina publica que muestra la invitacion. Si el usuario esta logueado → boton "Aceptar". Si no → boton "Registrarse" que redirige a /login?invite={token}.

---

## Posibles mejoras futuras

- **Transferir ownership**: cambiar el owner del equipo sin recrearlo
- **Historial de equipo**: log de quien entro, salio, confirmo
- **Dashboard de equipo**: vista consolidada de todos los radicados del equipo con dedup
- **Reenviar invitacion**: boton en el admin del equipo para reenviar invitaciones expiradas
