# INVESTIGACIÓN: Nuevas Plataformas Judiciales para Integrar
## Fecha: 25 de marzo de 2026
## Estado: VERIFICADA CON PRUEBAS REALES — integración viable sin pagar CAPTCHA

---

# RESUMEN EJECUTIVO

Se investigaron y **probaron técnicamente** 3 plataformas adicionales a SAMAI.

**Resultado sorprendente:**

| Plataforma | API directa | CAPTCHA servidor | Accesible sin CAPTCHA | Dificultad real |
|-----------|------------|-----------------|----------------------|-----------------|
| **SAMAI** ✅ ya impl. | ✅ REST oficial | ❌ No | ✅ Sí | Hecho |
| **CPNU / Siglo XXI** | ✅ REST en puerto 448 | ❌ No | ✅ Sí | **Fácil** |
| **SIUGJ** | Endpoint PHP | ❌ No (solo JS) | ✅ Sí | **Media** |
| **TYBA** (legado) | ASP.NET | ✅ Sí (reCAPTCHA v3) | ❌ No | No necesario |
| **SPOA (Fiscalía)** | No existe | ✅ Sí | ❌ No | No viable |

**El CAPTCHA en SIUGJ y CPNU es solo decoración del cliente JavaScript. El servidor no lo valida.**

---

# 1. CPNU — Consulta Procesos Nacional Unificada (Siglo XXI)

**URL frontend:** `https://consultaprocesos.ramajudicial.gov.co/Procesos/NumeroRadicacion`
**URL API REST:** `https://consultaprocesos.ramajudicial.gov.co:448/api/v2/`
**Swagger:** `https://consultaprocesos.ramajudicial.gov.co:448/swagger/index.html`
**Swagger JSON:** `https://consultaprocesos.ramajudicial.gov.co:448/swagger/v2/swagger.json`

## ¿Qué es?

La plataforma de consulta pública de la **Rama Judicial ordinaria** — procesos civiles, penales, laborales, de familia. Cubre despachos en todo Colombia. Esto es lo que monitorea Monolegal como "Rama Judicial" y lo que busca la mayoría de abogados colombianos.

## API REST descubierta (sin auth, sin CAPTCHA)

La SPA Vue.js llama a un backend REST separado en el **puerto 448**. El backend tiene Swagger documentado públicamente. **14 endpoints disponibles, todos sin autenticación.**

### Endpoints principales

| Endpoint | Descripción | Respuesta |
|----------|-------------|-----------|
| `GET /api/v2/Procesos/Consulta/{tipoConsulta}` | Buscar procesos | JSON con lista + paginación |
| `GET /api/v2/Proceso/Actuaciones/{idProceso}` | Actuaciones de un proceso | JSON con array de actuaciones |
| `GET /api/v2/Proceso/Detalle/{idProceso}` | Detalle completo | JSON con metadatos |
| `GET /api/v2/Proceso/Sujetos/{idProceso}` | Partes procesales | JSON |
| `GET /api/v2/Lista/{tipoLista}/{codigoFiltro}` | Departamentos, ciudades, despachos | JSON |
| `GET /api/v2/Descarga/CSV/Procesos/{tipoConsulta}` | Exportar resultados | CSV |
| `GET /api/v2/Descarga/DOCX/Proceso/{idProceso}` | Documento del proceso | DOCX |
| `GET /api/v2/Descarga/Documento/{gidDocumento}` | Documentos adjuntos | binario |
| `GET /api/v2/Lista/Ponentes/{ponente}` | Buscar jueces/magistrados | JSON |

### Tipos de consulta disponibles (`tipoConsulta`)

| Valor | Busca por |
|-------|-----------|
| `NumeroRadicacion` | Número de radicado de 23 dígitos |
| `NombreRazonSocial` | Nombre o razón social |
| `MagistradoPonente` | Juez o magistrado |

### Flujo para monitorear un proceso

```
1. GET /api/v2/Procesos/Consulta/NumeroRadicacion?numero=08573408900320230024200
   → Obtener idProceso (ej: 161456211)

2. GET /api/v2/Proceso/Actuaciones/161456211
   → Array de actuaciones con fechaActuacion + tipo

3. Comparar contra última actuación conocida → si hay nuevas, alertar
```

### Respuesta real de actuaciones (verificada 2026-03-25)

```json
{
  "actuaciones": [
    {
      "idRegActuacion": 3399541291,
      "fechaActuacion": "2026-03-26T00:00:00",
      "actuacion": "Fijacion Estado",
      "conDocumentos": false
    },
    {
      "idRegActuacion": 3399541281,
      "fechaActuacion": "2026-03-25T00:00:00",
      "actuacion": "Auto Requiere",
      "conDocumentos": true
    }
  ]
}
```

### Respuesta real de detalle de proceso (verificada)

```json
{
  "llaveProceso": "08573408900320230024200",
  "despacho": "JUZGADO 003 PROMISCUO MUNICIPAL DE PUERTO COLOMBIA",
  "ponente": "david andres arboleda hurtado",
  "tipoProceso": "Codigo General del Proceso",
  "claseProceso": "DIVISORIOS, DE DESLINDE Y AMOJONAMIENTO Y PERTENENCIAS",
  "ubicacion": "Software: Justicia XXI Web",
  "ultimaActualizacion": "2026-03-25T18:03:36.427"
}
```

### Formato del número de radicado (23 dígitos)

```
[DANE 5d][Entidad 2d][Especialidad 2d][Despacho 3d][Año 4d][Código 5d][Instancia 2d]
Ejemplo:  08573408900320230024200
          DANE=08573 | Entidad=40 | Esp=89 | Despacho=003 | Año=2023 | Cod=00242 | Inst=00
```

### Límite de búsqueda por nombre

Retorna hasta 1,000 procesos. Si hay más de 1,000 resultados, devuelve:
```json
{"StatusCode": 400, "Message": "Hay más de mil registros con los criterios especificados..."}
```

### CAPTCHA
**No existe en el servidor.** El frontend Vue.js no implementa CAPTCHA. La API en `:448` responde directamente a cualquier request HTTP.

### Autenticación
Ninguna para consultas públicas.

---

# 2. SIUGJ — Sistema Integrado de Uso de la Gestión Judicial

**URL pública (ciudadano):** `https://siugj.ramajudicial.gov.co/principalPortal/consultarProceso.php`
**Endpoint backend PHP:** `https://siugj.ramajudicial.gov.co/modulosEspeciales_SIUGJ/paginasFunciones/funcionesBuscadorProceso.php`

## ¿Qué es?

Sistema de la Rama Judicial para procesos bajo sistema **Justicia XXI cliente-servidor** (jurisdicción ordinaria, más antigua que CPNU). Complementa a CPNU cubriendo procesos que aún no migraron al sistema web.

## Endpoint PHP accesible sin CAPTCHA

El frontend JavaScript muestra reCAPTCHA v2 (sitekey: `6Lcvvp4qAAAAAJEw9aGuLtqzOPGGy4RkCvx9jmF3`), pero **el servidor PHP nunca valida el token**. Se verificó empíricamente: llamadas directas al PHP sin ningún token retornan datos reales.

### Técnica de llamada

```
POST https://siugj.ramajudicial.gov.co/modulosEspeciales_SIUGJ/paginasFunciones/funcionesBuscadorProceso.php
Content-Type: application/x-www-form-urlencoded
Origin: https://siugj.ramajudicial.gov.co
Referer: https://siugj.ramajudicial.gov.co/principalPortal/consultarProceso.php
```

**IMPORTANTE:** El parámetro JSON debe enviarse **en base64**. El JS del sitio usa una función `bE()` para codificarlo. Sin base64, devuelve `numReg: 0` aunque no hay error HTTP.

### Buscar procesos (`funcion=2`)

```
Body: funcion=2&cadObj=<base64({"remino":"garcia","pagina":1})>
```

**Nota:** el campo se llama `"remino"` (typo en el JS original del sitio, NO `"termino"`).

Respuesta real obtenida:
```json
{
  "numReg": 5,
  "registros": [
    {
      "idFormulario": "698",
      "codigoUnicoProceso": "66170310500120160001100",
      "nombreEspecialidad": "Laboral",
      "despacho": "JUZGADO 001 LABORAL DEL CIRCUITO DE DOSQUEBRADAS",
      "estadoProceso": "1",
      "nombreTipoProceso": "Ordinario de primera Instancia",
      "actor": "ALBERTO BURITICA SALGADO",
      "demandado": "ALBERTO BURITICA SALGADO",
      "folioRegistro": "TYBA___DOS_66170310500120160001100"
    }
  ],
  "hasMore": true,
  "page": 1,
  "pageSize": 5
}
```

### Obtener actuaciones (`funcion=3`)

```
Body: funcion=3&cA=<base64("66170310500120160001100")>
```

Respuesta real:
```json
{
  "numReg": 5,
  "registros": [
    {
      "idRegistro": 201956,
      "fechaActuacion": "2022-01-12 18:57:36",
      "actuacion": "Recepción O Publicación De Providencias",
      "anotacion": "fija fecha audiencia art. 80 31.03.2022 - 8:00 am.",
      "fechaInicia": "2022-01-12",
      "fechaTermina": null
    }
  ]
}
```

### Otros endpoints PHP descubiertos en el JS

| Endpoint | Uso |
|----------|-----|
| `../paginasFunciones/funciones.php` (funcion=8) | Login de usuarios |
| `../paginasFunciones/funciones.php` (funcion=12/13) | 2FA |
| `../modulosEspeciales_SGJ/registroUsuario.php` | Registro |
| `../gestorDocumental/validaDocumentos.php` | Documentos |

### Relación con CPNU

El campo `folioRegistro` en las respuestas SIUGJ tiene prefijo `TYBA___`, indicando que estos procesos son del sistema Justicia XXI cliente-servidor. Algunos procesos SIUGJ también aparecen en CPNU (que maneja la versión web del mismo sistema).

---

# 3. TYBA (Justicia XXI Web — legado)

**URL:** `https://procesojudicial.ramajudicial.gov.co/Justicia21/Administracion/Ciudadanos/frmConsulta`

## Resultado de prueba real

**El servidor SÍ valida reCAPTCHA v3 en el backend.**

Prueba enviada: POST con VIEWSTATE real + cookie de sesión + `recaptchaResponse=""` (vacío).
Respuesta: HTTP 200 con mensaje `"¡Error! El valor de la Capcha no coincide."` visible en HTML.

**Conclusión: No es accesible sin CAPTCHA.** Sin embargo, esto no importa porque:
- Los mismos datos de TYBA están disponibles en CPNU (API `:448` sin CAPTCHA)
- SIUGJ también indexa procesos TYBA (`folioRegistro` con prefijo `TYBA___`)

**No es necesario integrar TYBA.**

---

# 4. SPOA — Sistema Penal Oral Acusatorio (Fiscalía)

**URL consulta pública:** `https://consulta-web.fiscalia.gov.co/`

## Resultado

- Sin API pública de ningún tipo
- CAPTCHA obligatorio por cada consulta individual
- Requiere NUNC (número que asigna la Fiscalía — no calculable)
- Sistema anti-automatización por diseño

**No recomendado integrar.**

---

# 5. COMPARATIVA FINAL

| Aspecto | SAMAI (actual) | CPNU / Siglo XXI | SIUGJ | SPOA |
|---------|---------------|------------------|-------|------|
| Jurisdicción | Contencioso-Administrativo | Ordinaria (civil, penal, laboral, familia) | Ordinaria (procesos más antiguos) | Fiscal |
| API propia | ✅ REST oficial documentada | ✅ REST en `:448` con Swagger | ❌ PHP semi-expuesto | ❌ No existe |
| CAPTCHA servidor | ❌ No | ❌ No | ❌ No (solo JS) | ✅ Sí |
| Acceso directo | ✅ Sí | ✅ Sí | ✅ Sí (con base64) | ❌ No |
| Volumen audiencia | Mediano (admin) | **Grande (mayoría abogados)** | Medio (complementa CPNU) | Pequeño |
| Dificultad integración | ✅ Hecho | 🟢 Fácil | 🟡 Media | 🔴 No viable |
| Prioridad | ✅ Hecho | 🥇 Primera | 🥈 Segunda | Descartar |

---

# 6. PLAN DE INTEGRACIÓN — SIN ROMPER LO ACTUAL

## Principio: Arquitectura multi-fuente con provider pattern

```
[Monitor Lambda]
    ├── SamaiClient    → API samaicore.consejodeestado.gov.co (actual)
    ├── CpnuClient     → API consultaprocesos.ramajudicial.gov.co:448 (nuevo)
    └── SiugjClient    → PHP endpoint + base64 (nuevo)

[Mismo pipeline existente]
    → DynamoDB (alertas)  ← sin cambios
    → SES (email)         ← sin cambios
    → Frontend            ← cambio mínimo (dropdown fuente + badge)
```

## Cambios mínimos al modelo de datos

Agregar campo `fuente` al radicado:

```json
{
  "radicado": "08573408900320230024200",
  "fuente": "cpnu",              // "samai" | "cpnu" | "siugj"
  "alias": "Proceso civil Barranquilla",
  "id_proceso": "161456211"      // idProceso de CPNU (para evitar re-consultar)
}
```

## Diferencia clave en el diff

| Sistema | Clave para detectar novedad |
|---------|-----------------------------|
| SAMAI | Campo `Orden` (numérico incremental) |
| CPNU | Campo `idRegActuacion` (numérico) o `fechaActuacion` más reciente |
| SIUGJ | Campo `idRegistro` (numérico) |

## Cambios al frontend (mínimos)

1. **Agregar radicado**: Dropdown selector de fuente (SAMAI / Rama Judicial / SIUGJ)
2. **Lista de radicados**: Badge de color por fuente (azul=SAMAI, verde=Rama Judicial, naranja=SIUGJ)
3. **Validación de formato**: 23 dígitos para SAMAI y CPNU, CUP para SIUGJ

## Lo que NO cambia

- Autenticación (Cognito)
- Pipeline de alertas (DynamoDB + SES)
- Dashboard general y páginas de alertas
- CI/CD (GitLab)
- Infraestructura AWS base

---

# 7. RESPUESTA A LA PREGUNTA ORIGINAL

**"¿También funciona con SIUGJ, consultaprocesos (Rama Judicial) y el SPOA?"**

| Sistema | Respuesta | Detalle |
|---------|-----------|---------|
| **SIUGJ** | Se puede integrar sin pagar CAPTCHA | Endpoint PHP accesible directamente. El CAPTCHA es solo JavaScript del cliente. |
| **Consulta Procesos (Rama Judicial)** | Se puede integrar — tiene API REST propia | API completa en puerto 448 con Swagger. Sin CAPTCHA, sin auth. Fácil como SAMAI. |
| **SPOA (Fiscalía)** | No recomendado | Sin API, CAPTCHA real servidor, NUNC no calculable. |

**"¿No hay otra manera? ¿Ir una capa más allá?"**

Sí. Al probar directamente los servidores (en lugar de solo analizar el frontend) descubrimos que:

1. **CPNU tiene una API REST completa en `:448`** — igual que SAMAI. El frontend SPA la llama, nosotros podemos llamarla también. Tiene Swagger. Es pública.

2. **SIUGJ tiene CAPTCHA de pantalla pero no de servidor** — el PHP responde datos reales sin ningún token de CAPTCHA. Solo hay que codificar el JSON en base64.

No hay que pagar por solucionadores de CAPTCHA para ninguno de los dos.

---

# 8. ENDPOINTS DE REFERENCIA RÁPIDA

## CPNU (Siglo XXI)

```
Base: https://consultaprocesos.ramajudicial.gov.co:448/api/v2/

Buscar: GET /Procesos/Consulta/NumeroRadicacion?numero={23digitos}&SoloActivos=false&pagina=1
Actuaciones: GET /Proceso/Actuaciones/{idProceso}
Detalle: GET /Proceso/Detalle/{idProceso}
Partes: GET /Proceso/Sujetos/{idProceso}
CSV: GET /Descarga/CSV/Procesos/NumeroRadicacion?numero={23digitos}
```

## SIUGJ

```
Base: POST https://siugj.ramajudicial.gov.co/modulosEspeciales_SIUGJ/paginasFunciones/funcionesBuscadorProceso.php

Buscar:  funcion=2&cadObj=<base64({"remino":"texto","pagina":1})>
Detalle: funcion=3&cA=<base64("codigoUnicoProceso")>

Headers requeridos:
  Content-Type: application/x-www-form-urlencoded
  Origin: https://siugj.ramajudicial.gov.co
  Referer: https://siugj.ramajudicial.gov.co/principalPortal/consultarProceso.php
```

## SAMAI (referencia, ya implementado)

```
Base: https://samaicore.consejodeestado.gov.co/api/

Actuaciones: GET /Procesos/HistorialActuaciones/{corp}/{radicado}/2
Detalle: GET /ObtenerDatosProcesoGet/{corp}/{radicado}/2
Buscar: GET /BuscarProcesoTodoSamai/{radicado}/2
```

---

# 9. REFERENCIAS

| Recurso | URL |
|---------|-----|
| CPNU Swagger | `https://consultaprocesos.ramajudicial.gov.co:448/swagger/index.html` |
| CPNU API base | `https://consultaprocesos.ramajudicial.gov.co:448/api/v2/` |
| CPNU manual oficial | `https://consultaprocesos.ramajudicial.gov.co/manual/` |
| SIUGJ consulta pública | `https://siugj.ramajudicial.gov.co/principalPortal/consultarProceso.php` |
| SIUGJ endpoint PHP | `https://siugj.ramajudicial.gov.co/modulosEspeciales_SIUGJ/paginasFunciones/funcionesBuscadorProceso.php` |
| TYBA (no viable) | `https://procesojudicial.ramajudicial.gov.co/Justicia21/Administracion/Ciudadanos/frmConsulta` |
| SPOA Fiscalía (descartado) | `https://consulta-web.fiscalia.gov.co/` |
| SAMAI Swagger | `https://samaicore.consejodeestado.gov.co/swagger` |
| Análisis competidores | `../EstadosUpdates/DOCS/ANALISIS_COMPETIDORES.md` |
