# Gestion de Suscripciones — Upgrade, Downgrade, Cancelacion, Reembolso

---

## Resumen de escenarios

| Caso | Que pasa | Endpoint |
|------|----------|----------|
| **Upgrade** (Pro → Firma) | Inmediato. Cobra diferencia prorrateada via Wompi | `POST /billing/upgrade` |
| **Downgrade** (Firma → Pro) | Programado al fin del periodo. Sin cobro | `POST /billing/downgrade` |
| **Cancelar < 24h (tarjeta)** | Void automatico via Wompi API. Reembolso inmediato | `DELETE /billing/subscription` |
| **Cancelar < 24h (PSE/Nequi)** | No se puede void. Acceso hasta fin del periodo | `DELETE /billing/subscription` |
| **Cancelar > 24h** | Acceso hasta fin del periodo. Sin reembolso | `DELETE /billing/subscription` |
| **Invitado a equipo con plan** | Se notifica que ya esta cubierto por equipo. Puede cancelar personal | UI en Perfil |

---

## Limitacion clave: Wompi y reembolsos

Wompi NO tiene API publica de reembolso (`refund`). Solo tiene:

- `POST /v1/transactions/{id}/void` — anula la transaccion
  - Solo funciona con **tarjetas** (VISA, Mastercard)
  - Solo funciona el **mismo dia** de la transaccion
  - NO funciona con PSE, Nequi, Bancolombia, Daviplata

Para reembolsos despues del mismo dia o con metodos diferentes a tarjeta:
- Manual por dashboard Wompi (comercios.wompi.co)
- O contactar soporte Wompi

---

## Endpoints

### POST /billing/upgrade

Upgrade inmediato con cobro prorrateado.

**Request:**
```json
{ "planId": "plan-firma" }
```

**Logica de prorrateo:**
```
dias_restantes = (periodo_fin - hoy).days
dias_totales = (periodo_fin - periodo_inicio).days
diferencia = precio_nuevo - precio_actual
cobro = (dias_restantes / dias_totales) * diferencia
```

**Respuesta si hay cobro (> $1,000 COP):**
```json
{
  "upgraded": false,
  "reference": "upg_userId_plan-firma_1712160000",
  "amountInCents": 3333300,
  "proratedAmount": 33333,
  "currency": "COP",
  "integrityHash": "abc123...",
  "publicKey": "pub_test_...",
  "newPlanName": "Firma",
  "remainingDays": 20
}
```
El frontend abre el widget de Wompi con estos datos. Cuando se confirma el pago, el webhook reconoce el prefijo `upg_` y actualiza el plan (mantiene el periodo original).

**Respuesta si la diferencia es minima (< $1,000 COP):**
```json
{
  "upgraded": true,
  "message": "Upgrade a Firma completado sin cobro adicional.",
  "proratedAmount": 0
}
```

### POST /billing/downgrade

Programa downgrade al fin del periodo. Sin cobro ni reembolso.

**Request:**
```json
{ "planId": "plan-pro" }
```

**Respuesta:**
```json
{
  "message": "Downgrade a Pro programado para el fin del periodo actual.",
  "pendingPlanId": "plan-pro",
  "effectiveAt": "2026-05-03T10:00:00+00:00"
}
```

Se guarda `pendingPlanId` en la suscripcion. Cuando el periodo termina y el usuario renueva, se usa el plan pendiente.

**IMPORTANTE**: Falta implementar la logica de renovacion que aplica el `pendingPlanId`. Esto va en el webhook cuando detecta que es renovacion de un usuario con `pendingPlanId`.

### DELETE /billing/subscription

Cancelar suscripcion. Si < 24h y fue tarjeta, intenta void.

**Respuesta void exitoso:**
```json
{
  "message": "Suscripcion cancelada y pago reembolsado.",
  "refunded": true
}
```

**Respuesta sin void (> 24h o no tarjeta):**
```json
{
  "message": "Suscripcion cancelada. Activa hasta fin del periodo.",
  "refunded": false
}
```

---

## Webhook: reconocimiento de upgrades

El webhook de Wompi ahora reconoce dos formatos de reference:

| Prefijo | Significado | Accion |
|---------|-------------|--------|
| `sub_` | Nueva suscripcion o renovacion | Crear suscripcion con periodo nuevo (30 dias) |
| `upg_` | Upgrade mid-cycle | Cambiar plan manteniendo periodo actual |

---

## Invitacion a equipo con plan personal

Cuando se invita a un miembro que tiene plan personal activo, la respuesta del endpoint incluye:

```json
{
  "teamId": "abc123",
  "userId": "user-xxx",
  "role": "member",
  "joinedAt": "...",
  "hasPersonalPlan": true,
  "personalPlanName": "Pro"
}
```

El frontend debe mostrar un aviso al owner:
> "Este usuario tiene plan Pro activo. Al pertenecer al equipo, sus radicados ya cuentan contra el limite del equipo. Puede cancelar su plan personal desde su perfil."

No cancelamos automaticamente el plan personal — es decision del usuario.

---

## Flujo completo por escenario

### Usuario con Pro quiere Firma

```
1. POST /billing/upgrade {planId: "plan-firma"}
2. Backend calcula prorrateo: ej $33,333
3. Frontend abre Wompi widget con $33,333
4. Wompi confirma pago
5. Webhook recibe "upg_" → cambia planId a plan-firma, mantiene periodo
6. Usuario ya tiene 150 procesos disponibles
```

### Usuario con Firma quiere bajar a Pro

```
1. POST /billing/downgrade {planId: "plan-pro"}
2. Backend guarda pendingPlanId="plan-pro"
3. Usuario sigue con Firma hasta fin del periodo
4. Al renovar, se cobra Pro ($29,900) en vez de Firma ($79,900)
5. Los radicados que exceden 25 se desactivan en el proximo ciclo del monitor
```

### Usuario se arrepiente (< 24h, tarjeta)

```
1. DELETE /billing/subscription
2. Backend: createdAt fue hace < 24h, payment_method fue tarjeta
3. Backend: POST /v1/transactions/{txnId}/void → 200 OK
4. Suscripcion pasa a status="refunded"
5. Usuario cae a plan gratuito inmediatamente
6. Monitor desactiva radicados excedentes en el proximo ciclo
```

### Usuario se arrepiente (> 24h o PSE/Nequi)

```
1. DELETE /billing/subscription
2. Backend: void no disponible
3. Suscripcion pasa a status="cancelled", cancelAtPeriodEnd=true
4. Usuario mantiene acceso hasta fin del periodo
5. Despues del periodo: plan gratuito, radicados excedentes desactivados
```

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `billing_api/app.py` | Nuevos endpoints upgrade, downgrade. Cancel mejorado con void |
| `billing_webhook/app.py` | Reconoce prefijo `upg_` para upgrades |
| `api_handler/app.py` | `_post_team_member` retorna `hasPersonalPlan` si aplica |
| `template.yaml` | Rutas PostUpgrade, PostDowngrade en BillingApiFunction |
| `frontend/src/lib/api.ts` | Tipos y funciones para upgrade, downgrade, cancel mejorado |

---

## Implementado

- [x] Logica de renovacion con `pendingPlanId` en el webhook
- [x] UI de upgrade/downgrade en /billing y /planes
- [x] Aviso "tiene plan personal" al invitar miembro con plan activo
- [x] Pagina Planes: botones dicen "Upgrade" o "Downgrade" segun plan actual
- [x] Billing: detecta si plan seleccionado es upgrade/downgrade y actua en consecuencia

## Pendientes futuros

- [ ] Email de confirmacion de cancelacion/reembolso
- [ ] Considerar contactar Wompi para preguntar por API de refund no documentada
