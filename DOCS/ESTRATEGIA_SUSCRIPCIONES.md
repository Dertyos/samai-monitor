# Estrategia de Suscripciones y Go-to-Market
## Alertas Judiciales by Dertyos
### Fecha: 3 de abril de 2026

---

# 1. RESUMEN EJECUTIVO

Alertas Judiciales es un SaaS de monitoreo judicial especializado en SAMAI (jurisdiccion contencioso-administrativa de Colombia). El producto esta **funcionalmente maduro** (20 endpoints, 3 plataformas judiciales, alertas por email, etiquetas, exportacion CSV, dark mode) pero tiene **cero monetizacion**. Este documento define la estrategia de suscripciones, pricing y adquisicion de usuarios.

---

# 2. ANALISIS DEL MERCADO

## 2.1 Tamano del mercado

| Metrica | Valor |
|---------|-------|
| Abogados registrados en Colombia | 410,000+ (2024), ~500,000 estimado 2028 |
| Abogados por 100,000 habitantes | 779 (top mundial) |
| Nuevos abogados/ano | 12,000-20,000 |
| Juzgados administrativos | 342 |
| Tribunales administrativos | 176 camaras en 26 distritos |
| Consejo de Estado | 31 camaras |
| SAMAI obligatorio desde | 22 de enero de 2024 |
| Ranking legaltech LATAM | Colombia #2 |
| Empresas legaltech Colombia | 100+ |

**Mercado objetivo directo**: Abogados que litigan en lo contencioso-administrativo. Estimacion conservadora: 30,000-50,000 abogados activos en esta jurisdiccion.

**Tailwind clave**: SAMAI es obligatorio desde enero 2024 para TODA la jurisdiccion administrativa. Esto significa que cada proceso contencioso-administrativo en Colombia pasa por el sistema que nosotros monitoreamos.

## 2.2 Competidores directos

### Tier 1 - Competencia directa (monitoreo judicial)

| Competidor | Pricing | Modelo | Cubre SAMAI | Diferenciador |
|------------|---------|--------|-------------|---------------|
| **Monolegal** | COP $1,335/proceso/mes | Per-process, descuentos por volumen (10-50%) | Si | 5 fuentes, app movil, transparente |
| **ICARUS** | Por ciclo de escaneo (contactar) | Pay-per-scan | Parcial | Clasificacion por prioridad |
| **LitisData** | Contactar | Enterprise | Desconocido | 20+ anos, 1,200+ clientes |
| **Litigando** | Custom | Enterprise, 1 mes gratis | Desconocido | 6 paises LATAM, 837 municipios |
| **Vigilancia Judicial** | Contactar | Desconocido | Desconocido | Alertas + vencimientos |

### Tier 2 - Competencia emergente (con IA)

| Competidor | Pricing | Modelo | Cubre SAMAI | Diferenciador |
|------------|---------|--------|-------------|---------------|
| **JuridAI** | Contactar | Desconocido | Posible | IA predictiva, analytics |
| **Sentinel Procesal** | Contactar | Enterprise | Si (explicito) | WhatsApp bot, voicebot |

### Tier 3 - Competencia indirecta (gestion legal con monitoreo como add-on)

| Competidor | Pricing | Modelo | Cubre SAMAI | Diferenciador |
|------------|---------|--------|-------------|---------------|
| **PleGlex** | COP $1,000/proceso/mes | Add-on a gestion legal | Parcial | Suite completa de gestion |
| **LegalSoft App** | Suscripcion (contactar) | All-in-one | Desconocido | Gestion + monitoreo |
| **LEXIUS** | COP $42,000/mes flat | Suscripcion | Desconocido | IA, precio fijo |
| **Litigiovirtual** | Contactar | Hibrido humano+software | Desconocido | Verificacion humana |

### Benchmark de precios del mercado

- **Per-process**: COP $1,000-1,335/proceso/mes (Monolegal, PleGlex)
- **Flat**: COP $42,000/mes (LEXIUS)
- **Para 20 procesos**: COP $20,000-27,000/mes (~USD $5-7/mes)
- **Para 100 procesos**: COP $100,000-133,500/mes (~USD $25-33/mes)

---

# 3. VENTAJA COMPETITIVA

## 3.1 Nuestro moat: Especializacion en SAMAI

La mayoria de competidores son **generalistas** (cubren Rama Judicial civil, penal, laboral, etc.). Nosotros somos el **unico producto 100% especializado en contencioso-administrativo**.

Ventajas de la especializacion:

1. **API propia de SAMAI**: Integracion directa con los 79 endpoints de SAMAI, no scraping generico
2. **Multi-plataforma judicial ya implementada**: SAMAI + Rama Judicial (CPNU) + SIUGJ
3. **Conocimiento del dominio**: Alertas especificas para derecho administrativo (admision demanda, fijacion en lista, sentencia, apelacion)
4. **Self-service**: Registro instantaneo, no requiere llamada de ventas (a diferencia de Sentinel, Litigando, LitisData)
5. **UX moderna**: React SPA con dark mode, responsive, vs interfaces legacy de competidores
6. **Pricing transparente**: Sin "contactenos para cotizacion"

## 3.2 Debilidades a resolver

| Debilidad | Impacto | Solucion propuesta | Prioridad |
|-----------|---------|---------------------|-----------|
| Sin app movil | Alto | PWA con push notifications | P1 |
| Sin alertas WhatsApp | Alto | Integracion Twilio/WhatsApp Business API | P2 |
| Solo email como canal | Alto | Push notifications (PWA) como paso intermedio | P1 |
| Sin IA/analytics | Medio | Clasificacion de actuaciones por urgencia | P2 |
| Sin multi-usuario | Medio | Equipos/firmas compartiendo procesos | P2 |
| Sin free trial visible | Alto | Implementar tier gratuito | P0 |

---

# 4. ESTRATEGIA DE PRICING

## 4.1 Modelo: Freemium + Tiers por volumen

Modelo hibrido: **tier gratuito generoso** para adopcion + **tiers pagos por volumen de procesos** para monetizacion. Esto combina lo mejor de los modelos del mercado:

- Per-process pricing (como Monolegal) para alinear precio con valor
- Tiers predecibles (como LEXIUS) para simplificar la decision
- Freemium (unico en el mercado) para eliminar friccion de adopcion

## 4.2 Planes propuestos

### Plan Gratuito - "Basico"
- **Precio**: $0/mes
- **Procesos**: Hasta 5 procesos monitoreados
- **Alertas**: Email diario
- **Features**: Dashboard, historial, etiquetas, exportacion CSV, busqueda SAMAI
- **Limite**: 1 usuario, sin soporte prioritario
- **Objetivo**: Capturar abogados independientes, generar boca a boca, product-led growth

### Plan Profesional - "Pro"
- **Precio**: COP $19,900/mes (~USD $5)
- **Procesos**: Hasta 25 procesos
- **Alertas**: Email + push notifications (PWA)
- **Features**: Todo lo gratuito + alertas configurables, frecuencia personalizable
- **Equivalente per-process**: ~COP $796/proceso (mas barato que PleGlex)
- **Objetivo**: Abogados independientes y consultorios pequenos

### Plan Firma - "Business"
- **Precio**: COP $79,900/mes (~USD $20)
- **Procesos**: Hasta 150 procesos
- **Alertas**: Email + push + WhatsApp (futuro)
- **Features**: Todo Pro + multi-usuario (hasta 5), reportes avanzados, soporte prioritario
- **Equivalente per-process**: ~COP $533/proceso (mas barato que Monolegal)
- **Objetivo**: Firmas de abogados pequenas y medianas

### Plan Corporativo - "Enterprise"
- **Precio**: COP $249,900/mes (~USD $62)
- **Procesos**: Hasta 1,000 procesos
- **Alertas**: Todos los canales + API webhooks
- **Features**: Todo Business + hasta 20 usuarios, API access, integraciones, account manager
- **Equivalente per-process**: ~COP $250/proceso (imbatible)
- **Objetivo**: Departamentos juridicos corporativos, entidades publicas

### Comparacion con competencia

| Escenario | Nosotros | Monolegal | PleGlex |
|-----------|----------|-----------|---------|
| 5 procesos | **$0 (gratis)** | $6,675 | $5,000 |
| 20 procesos | **$29,900** | $26,700 | $20,000 |
| 50 procesos | **$79,900** | $66,750 | $50,000 |
| 100 procesos | **$79,900** | $133,500 | $100,000 |
| 500 procesos | **$249,900** | $667,500* | $500,000 |

*Monolegal da descuentos por volumen, pero aun asi somos significativamente mas baratos en escala.

**Posicionamiento**: Mas barato que la competencia en TODOS los niveles, con tier gratuito que nadie ofrece.

---

# 5. ESTRATEGIA DE ADQUISICION DE USUARIOS

## 5.1 Fase 1: Product-Led Growth (Meses 1-3)

**Objetivo**: 500 usuarios registrados, 50 pagando

### Tacticas

#### A. Tier gratuito como motor de adopcion
- El plan gratuito (5 procesos) es el arma principal
- Ningun competidor ofrece un tier 100% gratuito permanente
- Abogados prueban sin riesgo, se enganchan con el valor, upgraden cuando necesitan mas

#### B. SEO y contenido
- **Keywords objetivo**:
  - "consulta procesos SAMAI" (alto volumen, baja competencia)
  - "alertas judiciales contencioso administrativo"
  - "monitoreo procesos consejo de estado"
  - "como consultar actuaciones SAMAI"
- **Contenido**:
  - Blog con guias practicas de derecho administrativo
  - Tutoriales de uso de SAMAI (posicionarnos como expertos)
  - Calculadora de terminos procesales (herramienta gratuita viral)

#### C. Comunidades juridicas
- Presencia en grupos de Facebook de abogados colombianos (hay varios con 10,000+ miembros)
- LinkedIn targeting abogados administrativistas
- Foros de Ambito Juridico y Asuntos Legales

#### D. Referral program
- "Invita a un colega, ambos obtienen 1 mes de Pro gratis"
- Los abogados son una comunidad cerrada donde el boca a boca es poderoso

#### E. Landing Page de conversion (CRITICO)

La landing page es el **primer punto de contacto** para todo el trafico de publicidad (Google Ads, Facebook Ads, LinkedIn Ads). Sin ella, el dinero en ads se desperdicia.

**URL**: `alertas-judiciales.dertyos.com` (ruta `/` publica, sin auth)

**Estructura de la landing page**:

1. **Hero section**
   - Headline: "Nunca pierdas una actuacion judicial" (o similar orientado al dolor)
   - Subheadline: "Monitoreo automatico de procesos en SAMAI. Alertas diarias por email. Gratis para siempre."
   - CTA principal: boton "Empieza gratis" (lleva a `/login` con modo registro)
   - CTA secundario: "Ver planes" (scroll a seccion de pricing)
   - Imagen/mockup del dashboard en accion

2. **Seccion de dolor / problema**
   - "Revisar SAMAI manualmente todos los dias consume horas"
   - "Un auto que se te pasa puede costarle el caso a tu cliente"
   - "Los vencimientos de terminos no esperan"
   - Estadistica: "342 juzgados administrativos generan miles de actuaciones diarias"

3. **Seccion de solucion / features**
   - Monitoreo automatico diario (7 AM)
   - Alertas por email instantaneas
   - Dashboard con todos tus procesos en un solo lugar
   - Historial completo de actuaciones
   - Descarga de providencias PDF
   - Etiquetas y filtros personalizados
   - Dark mode (detalle que demuestra cuidado en UX)
   - Cada feature con icono + descripcion breve + screenshot

4. **Social proof / confianza**
   - "Usado por X abogados en Colombia" (counter en vivo cuando tengamos traccion)
   - Testimonios (conseguir 3-5 beta testers que den feedback)
   - Logos de universidades/firmas aliadas (cuando existan)
   - "Datos 100% publicos — usamos la API oficial de SAMAI"

5. **Seccion de pricing**
   - Tabla comparativa de los 4 planes (Gratis, Pro, Firma, Corporativo)
   - Highlight en plan Pro como "Mas popular"
   - Toggle mensual/anual (con descuento del 20% anual)
   - CTA en cada plan: "Empezar" / "Empezar gratis"
   - Comparacion vs competencia: "5 procesos gratis. La competencia cobra desde el primero."

6. **FAQ**
   - "Es seguro?" -> Datos publicos, API oficial, AWS, Cognito
   - "Que pasa si me paso del limite?" -> No pierdes datos, solo se bloquea agregar nuevos
   - "Puedo cancelar cuando quiera?" -> Si, sin compromisos
   - "Cubren Rama Judicial?" -> Proximo, ya en desarrollo
   - "Necesito tarjeta de credito para el plan gratis?" -> No

7. **CTA final**
   - "Empieza a monitorear tus procesos hoy. Es gratis."
   - Boton grande "Crear cuenta gratis"

8. **Footer**
   - Links: Terminos de servicio, Politica de privacidad, Contacto
   - Email de soporte
   - Redes sociales

**Requisitos tecnicos de la landing page**:

| Aspecto | Detalle |
|---------|---------|
| Framework | Misma app React (ruta `/` publica) o pagina estatica separada en S3 |
| SEO | SSR o pre-rendering para indexacion (meta tags, Open Graph, schema.org) |
| Velocidad | Lighthouse score 90+, lazy load imagenes, above-the-fold optimizado |
| Responsive | Mobile-first (70%+ del trafico colombiano es movil) |
| Analytics | Google Analytics 4 + pixel de Facebook Ads + LinkedIn Insight Tag |
| A/B testing | Variantes del headline y CTA (Google Optimize o similar) |
| UTM tracking | Parametros UTM en todas las URLs de ads para medir ROI por canal |
| Conversion tracking | Eventos: page_view, cta_click, signup_started, signup_completed |

**Flujo de conversion desde publicidad**:

```
Ad (Google/FB/LinkedIn)
  -> Landing page (/)
    -> CTA "Empieza gratis"
      -> Registro (/login?mode=register)
        -> Onboarding (agregar primer proceso)
          -> Dashboard (valor inmediato)
            -> Upgrade a Pro (cuando llegue al limite de 5)
```

**Presupuesto de ads sugerido (Fase 1 - bootstrap)**:

Presupuesto lean para validar canales antes de escalar. Priorizar el canal con mejor CPA y duplicar ahi.

| Canal | Presupuesto/mes (COP) | ~USD | Targeting |
|-------|----------------------|------|-----------|
| Google Ads | $50,000 | $12.50 | Keywords exactas: "consulta SAMAI", "alertas judiciales" (long-tail, bajo CPC) |
| Facebook/Instagram Ads | $50,000 | $12.50 | Abogados Colombia, interes en derecho administrativo, 25-55 anos |
| LinkedIn Ads | $0 (pausado) | $0 | Muy caro por click, activar solo si sobra presupuesto |
| **Total** | **$100,000** | **$25** | |

**Nota**: Con COP $100,000/mes y un CPC estimado de $500-1,000, obtenemos ~100-200 clicks/mes.
Si la landing convierte al 5-10%, eso son 5-20 registros/mes solo de ads. El resto viene de SEO,
comunidades y referrals (canales gratuitos que deben ser el motor principal en esta fase).

**Metricas de la landing page**:

| Metrica | Meta |
|---------|------|
| Tasa de conversion (visita -> registro) | 5-10% |
| Costo por registro (CPA) | < COP $5,000 (~USD $1.25) — con $100K/mes eso son ~20 registros pagos |
| Bounce rate | < 50% |
| Tiempo en pagina | > 60 segundos |
| CTR en ads | > 2% |

## 5.2 Fase 2: Partnerships (Meses 3-6)

**Objetivo**: 2,000 usuarios registrados, 200 pagando

### Tacticas

#### A. Universidades y facultades de derecho
- Alianzas con programas de especializacion en derecho administrativo
- Ofrecer plan gratuito extendido (10 procesos) para estudiantes
- Webinars co-organizados con universidades

#### B. Asociaciones de abogados
- Acercamiento a la Camara de Comercio, colegios de abogados regionales
- Descuento corporativo para miembros de asociaciones
- Patrocinio de eventos de derecho administrativo

#### C. Integraciones
- Plugin/extension para navegadores (acceso rapido desde SAMAI web)
- Integracion con calendarios (Google Calendar, Outlook) para audiencias

## 5.3 Fase 3: Expansion (Meses 6-12)

**Objetivo**: 5,000+ usuarios registrados, 500+ pagando

### Tacticas

#### A. Multi-jurisdiccion como upgrade
- Rama Judicial (CPNU) y SIUGJ ya estan implementados en backend
- Activarlos como feature premium del plan Business+
- Esto abre el mercado a TODOS los abogados litigantes, no solo administrativistas

#### B. Features de IA
- Clasificacion automatica de actuaciones por urgencia (NLP sobre anotaciones)
- Deteccion de audiencias parseando texto de actuaciones
- Resumen automatico de providencias descargadas

#### C. Gobierno y entidades publicas
- Las entidades publicas son DEMANDADAS constantemente en lo contencioso-administrativo
- Ofrecer plan Enterprise a oficinas juridicas de alcaldias, gobernaciones, ministerios
- Licitaciones publicas (SECOP II)

---

# 6. IMPLEMENTACION TECNICA DEL BILLING

## 6.1 Stack recomendado

| Componente | Tecnologia | Razon |
|------------|-----------|-------|
| Procesador de pagos | **Wompi** (Bancolombia) | $0 mensual, tarjetas, PSE, Nequi, Bancolombia, Daviplata |
| Facturacion electronica | **(futuro) Siigo/Factus** | Se activa cuando haya ingresos que lo justifiquen |
| Gestion de suscripciones | **Custom (DynamoDB + cron)** | Tokenizacion Wompi + cobro desde Lambda |
| Limite de features | **DynamoDB** | 3 tablas billing (plans, subscriptions, events) |
| Frontend billing | **Wompi Widget + React** | Widget embebido para checkout, paginas custom para gestion |
| Webhooks | **Lambda** | Procesar confirmaciones de pago de Wompi (firma SHA256) |

**Nota**: Stripe NO opera en Colombia. ePayco cobra $49,900+/mes solo por API.
Wompi (Bancolombia) es la mejor opcion: API gratis, solo comision por transaccion
(2.65% + $700 COP + IVA), soporta tarjetas, PSE, Nequi, Bancolombia, Daviplata.

## 6.2 Modulo de billing (plug & play)

Implementacion directa en samai-monitor (2 Lambdas + 3 tablas DynamoDB).
Wompi Widget en el frontend para el checkout, webhooks para confirmacion.

### Componentes
- `billing_webhook/app.py`: Lambda que recibe webhooks de Wompi, valida firma SHA256
- `billing_api/app.py`: Lambda con 6 endpoints REST (planes, suscripcion, facturas, config Wompi)
- `api_handler/app.py`: plan enforcement en POST /radicados + GET /billing/status
- `scripts/seed_plans.py`: seed de planes en DynamoDB

### DynamoDB - 3 tablas nuevas
```
samai-billing-plans        PK: planId
samai-billing-subscriptions PK: userId + planId, GSI: status-index
samai-billing-events       PK: userId + sk, GSI: transaction-id-index, TTL: 365 dias
```

### API Endpoints nuevos (billing)
```
GET    /billing/plans         -> Listar planes (con auth)
GET    /billing/subscription  -> Plan actual del usuario (con auth)
POST   /billing/subscribe     -> Suscribirse a un plan (con auth)
DELETE /billing/subscription  -> Cancelar suscripcion (con auth)
GET    /billing/invoices      -> Historial de facturas (con auth)
POST   /billing/webhook       -> Confirmacion de pago ePayco (SIN auth, firma SHA256)
```

### Enforcement de limites
- `POST /radicados` debe verificar `currentProcessCount < processLimit`
- Retornar HTTP 403 con mensaje claro: "Has alcanzado el limite de tu plan. Upgrade a Pro para monitorear hasta 30 procesos."
- Los procesos existentes siguen monitoreandose si se hace downgrade (no se eliminan, solo se bloquea agregar nuevos)
- Usuarios sin suscripcion = plan gratuito (5 procesos)

### Frontend - Nuevas paginas
- `/planes` - Pagina publica con planes y precios (seccion de Landing + pagina dedicada)
- `/billing` - Dashboard de suscripcion (plan actual, uso, upgrade/downgrade, historial facturas)
- Indicador de uso en Dashboard: "3/5 procesos usados" con barra de progreso
- Prompt de upgrade cuando el usuario llega al limite

## 6.3 Orden de implementacion

1. **Sprint 1**: Integrar billing-module al template.yaml + enforcement de limites en POST /radicados
2. **Sprint 2**: Frontend billing (pagina de planes, formulario suscripcion, historial facturas)
3. **Sprint 3**: Landing page publica con seccion de pricing + analytics (GA4, pixels)
4. **Sprint 4**: PWA + push notifications (feature Pro)
5. **Sprint 5**: Multi-usuario (feature Business)

---

# 7. METRICAS CLAVE (KPIs)

| Metrica | Meta Mes 3 | Meta Mes 6 | Meta Mes 12 |
|---------|-----------|-----------|------------|
| Usuarios registrados | 500 | 2,000 | 5,000 |
| Usuarios pagando | 50 | 200 | 500 |
| MRR (COP) | $1,500,000 | $6,000,000 | $15,000,000 |
| MRR (USD) | ~$375 | ~$1,500 | ~$3,750 |
| Tasa de conversion free->pago | 10% | 10% | 10% |
| Churn mensual | <5% | <5% | <3% |
| Procesos monitoreados (total) | 2,500 | 15,000 | 50,000 |
| ARPU (COP) | $30,000 | $30,000 | $30,000 |
| CAC (COP) | <$15,000 | <$20,000 | <$25,000 |
| LTV/CAC ratio | >3x | >3x | >3x |

---

# 8. RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| SAMAI cambia/bloquea API | Media | Critico | Diversificar fuentes (CPNU, SIUGJ ya implementados), rate limiting respetuoso |
| Monolegal baja precios | Media | Alto | Competir en UX y especializacion, no solo en precio |
| Baja conversion free->pago | Media | Alto | Optimizar limites del tier gratuito (3-5 procesos), onboarding emails |
| Wompi downtime o cambio API | Baja | Alto | Fallback: Bold, MercadoPago |
| Regulacion de datos judiciales | Baja | Medio | Datos son publicos por ley (principio de publicidad procesal) |

---

# 9. TIMELINE GENERAL

```
Mes 1:    Integrar billing-module (ePayco + Alegra) + enforcement limites + billing UI
Mes 1-2:  Landing page publica + analytics + pixels de ads
Mes 2-3:  Lanzar tier gratuito + Pro, encender ads, SEO, presencia en comunidades
Mes 3-4:  PWA + push notifications, referral program, optimizar landing (A/B)
Mes 4-6:  Plan Business (multi-usuario), partnerships universidades
Mes 6-9:  Activar multi-jurisdiccion (CPNU, SIUGJ), features IA basicas
Mes 9-12: Plan Enterprise, gobierno, expansion LATAM (investigar)
```

---

# 10. CONCLUSION

El mercado de monitoreo judicial en Colombia tiene **demanda comprobada** (Monolegal, LitisData, ICARUS llevan anos operando) pero **ninguno ofrece un tier gratuito** y **ninguno se especializa en contencioso-administrativo**. 

Nuestra estrategia se basa en tres pilares:

1. **Freemium agresivo**: 5 procesos gratis, permanente. Esto es inedito en el mercado.
2. **Especializacion**: Somos LOS expertos en SAMAI. Conocemos cada endpoint, cada tipo de actuacion.
3. **Precio competitivo con valor superior**: Mas barato que Monolegal en todos los niveles, con mejor UX.

El producto ya esta listo. Solo falta el billing y el go-to-market.

---

## FUENTES

- [Monolegal - Precios](https://monolegal.co/precios-y-descuentos-en-la-consulta-de-tus-procesos-judiciales)
- [ICARUS](https://www.icarus.com.co/)
- [JuridAI](https://www.juridai.co/)
- [Sentinel Procesal](https://www.sentinelprocesal.com/)
- [Litigando](https://www.litigando.com/)
- [LitisData](https://www.litisdata.com/)
- [PleGlex - Vigilancia Judicial](https://pleglex.com/servicios/vigilancia-judicial-en-colombia/)
- [LEXIUS Colombia](https://appcolombia.lexius.io/)
- [Litigiovirtual](https://litigiovirtual.com/)
- [LegalSoft App](https://legalsoftapp.com/)
- [Vigilancia Judicial](https://www.vigilanciajudicial.com/)
- [CEJ - Abogados en Colombia](https://cej.org.co/destacados-home-page/entre-1996-y-2022-el-numero-de-abogados-inscritos-aumento-472-advierte-informe-de-la-cej/)
- [779 abogados por 100K habitantes](https://www.asuntoslegales.com.co/actualidad/hay-779-abogados-por-cada-100-000-habitantes-en-colombia-4119855)
- [100+ emprendimientos LegalTech Colombia](https://www.asuntoslegales.com.co/consumidor/hay-mas-de-100-enprendimientos-de-legaltech-en-el-mercado-nacional-2998002)
- [SAMAI obligatorio](https://www.ambitojuridico.com/noticias/tecnologia/administracion-publica/samai-es-obligatorio-en-la-jurisdiccion-de-lo)
- [Legaltech Colombia - Lemontech](https://blog.lemontech.com/firmas-legales/legaltech-colombia)
- [B2B SaaS Pricing 2025](https://www.artisangrowthstrategies.com/blog/b2b-saas-pricing-models-complete-2025-guide)
