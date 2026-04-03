# Setup de Billing — Wompi

Pasos manuales para activar pagos en produccion.

---

## 1. Crear cuenta Wompi

1. Ir a [comercios.wompi.co](https://comercios.wompi.co) y registrarse
2. Verificar identidad y datos del comercio
3. En el dashboard, ir a **Desarrolladores > Llaves** y copiar:

| Llave | Prefijo Sandbox | Prefijo Prod | Variable GitLab |
|-------|----------------|--------------|-----------------|
| **Public Key** | `pub_test_` | `pub_prod_` | `WOMPI_PUBLIC_KEY` |
| **Private Key** | `prv_test_` | `prv_prod_` | `WOMPI_PRIVATE_KEY` |
| **Events Key** | `test_events_` | `prod_events_` | `WOMPI_EVENTS_KEY` |
| **Integrity Key** | `test_integrity_` | `prod_integrity_` | `WOMPI_INTEGRITY_KEY` |

---

## 2. Agregar variables en GitLab

GitLab → samai-monitor → **Settings > CI/CD > Variables**:

| Key | Protected | Masked |
|-----|-----------|--------|
| `WOMPI_PUBLIC_KEY` | si | si |
| `WOMPI_PRIVATE_KEY` | si | si |
| `WOMPI_EVENTS_KEY` | si | si |
| `WOMPI_INTEGRITY_KEY` | si | si |

---

## 3. Deploy + seed

```bash
git push origin main              # CI/CD despliega
python backend/scripts/seed_plans.py   # crear planes en DynamoDB
```

---

## 4. Configurar webhook en Wompi

Dashboard Wompi → **Desarrolladores > Webhooks**:

- **URL**: `https://tu-api-url/prod/billing/webhook`
  (La URL sale en los outputs del deploy: `ApiUrl`)
- **Eventos**: `transaction.updated`

Configurar URLs separadas para sandbox y produccion.

---

## 5. Probar en sandbox

Con `WompiSandbox=true` (por defecto), usa estos datos de prueba:

### Tarjetas
| Numero | Resultado |
|--------|-----------|
| `4242 4242 4242 4242` | APPROVED |
| `4111 1111 1111 1111` | DECLINED |

Cualquier fecha futura y cualquier CVC de 3 digitos.

### PSE
| Codigo banco | Resultado |
|--------------|-----------|
| `1` | APPROVED |
| `2` | DECLINED |

### Nequi
| Telefono | Resultado |
|----------|-----------|
| `3991111111` | APPROVED |
| `3992222222` | DECLINED |

---

## 6. Flujo de pago

```
1. Usuario click "Upgrade a Pro" en /billing
2. Frontend → POST /billing/subscribe {planId}
3. Backend genera reference + integrity hash
4. Frontend abre Wompi Widget con esos datos
5. Usuario paga (tarjeta, PSE, Nequi, etc.)
6. Wompi procesa el pago
7. Wompi envia webhook → POST /billing/webhook
8. Backend valida firma SHA256, activa suscripcion en DynamoDB
9. Frontend refresca → usuario ve plan activo
```

---

## 7. Pasar a produccion

1. Cambiar `WompiSandbox=false` en el deploy
2. Usar llaves `pub_prod_*`, `prv_prod_*`, `prod_events_*`, `prod_integrity_*`
3. Configurar webhook de produccion en Wompi
4. Probar con pago real

---

## Metodos de pago soportados

- Tarjetas Visa, Mastercard (credito y debito)
- PSE (transferencia bancaria)
- Nequi
- Bancolombia Transfer
- Bancolombia QR
- Daviplata

---

## Comisiones Wompi

| Concepto | Costo |
|----------|-------|
| Mensualidad | **$0** |
| Comision por transaccion exitosa | 2.65% + $700 COP + IVA |
| Transacciones fallidas | $0 |

---

## Facturacion electronica DIAN (futuro, opcional)

Wompi NO genera factura electronica. Para agregarla despues:
- **Siigo** (gratis, 5 facturas/mes) — mas barato
- **Alegra** (~$70,000/mes) — mas features
- **Factus** (~$30,000/mes) — enfocado en devs

Se puede integrar un `siigo_client.py` en el webhook handler cuando lo necesites.

---

## Checklist

- [ ] Cuenta Wompi creada en comercios.wompi.co
- [ ] 4 llaves copiadas (public, private, events, integrity)
- [ ] Variables agregadas en GitLab CI/CD
- [ ] Deploy ejecutado (push a main)
- [ ] Seed de planes ejecutado (`python backend/scripts/seed_plans.py`)
- [ ] Webhook URL configurada en dashboard Wompi
- [ ] Flujo probado en sandbox (tarjeta 4242...)
- [ ] (Produccion) Cambiar llaves a prod + WompiSandbox=false
