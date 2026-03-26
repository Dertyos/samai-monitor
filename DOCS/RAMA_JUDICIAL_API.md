# API Rama Judicial CPNU — Documentación Técnica

**Fecha de verificación:** 2026-03-25
**Estado:** ✅ Todos los endpoints confirmados funcionando

---

## Base URL

```
https://consultaprocesos.ramajudicial.gov.co:448/api/v2
```

- Puerto no estándar: **448** (HTTPS)
- Servidor: Microsoft IIS 10.0
- SPA: Vue.js — la API fue descubierta por ingeniería inversa del bundle JS

---

## Autenticación

Los endpoints de **consulta pública** no requieren autenticación.
`Access-Control-Allow-Origin: *` — sin restricciones de CORS.

---

## Headers recomendados

```python
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://consultaprocesos.ramajudicial.gov.co",
    "Referer": "https://consultaprocesos.ramajudicial.gov.co/",
    "Accept": "application/json, text/plain, */*",
}
```

---

## Endpoints confirmados

### 1. Buscar proceso por número de radicación

```
GET /Procesos/Consulta/NumeroRadicacion
  ?numero={23_digitos}
  &SoloActivos={true|false}
  &pagina={int}
```

**Parámetros:**
- `numero`: radicado de 23 dígitos SIN guiones (ej: `11001400300120240012600`)
- `SoloActivos`: `false` = todos, `true` = solo con actuaciones recientes (últimos 30 días)
- `pagina`: página (default 1, 20 registros por página)

**Response:**
```json
{
  "tipoConsulta": "NumeroRadicacion",
  "procesos": [
    {
      "idProceso": 149525880,
      "idConexion": 259,
      "llaveProceso": "11001400300120240012600",
      "fechaProceso": "2024-02-12T00:00:00",
      "fechaUltimaActuacion": "2024-03-05T00:00:00",
      "despacho": "JUZGADO 001 CIVIL MUNICIPAL DE BOGOTÁ",
      "departamento": "BOGOTÁ",
      "sujetosProcesales": "Demandante: JUAN PEREZ | Demandado: ENTIDAD X",
      "esPrivado": false,
      "cantFilas": -1
    }
  ],
  "paginacion": {
    "cantidadRegistros": 1,
    "registrosPagina": 20,
    "cantidadPaginas": 1,
    "pagina": 1
  }
}
```

**⚠️ Edge cases confirmados:**
- Radicado no encontrado → `procesos: []`, `cantidadRegistros: 0` (HTTP 200)
- Un radicado puede retornar **múltiples procesos** (misma llave en distintos despachos por apelación/traslado). Cada uno tiene `idProceso` diferente e `idConexion` diferente.
- `cantFilas: -1` es normal (no indica error)

---

### 2. Actuaciones de un proceso

```
GET /Proceso/Actuaciones/{idProceso}
  ?pagina={int}
  [&fechaIni=YYYY-MM-DD]
  [&fechaFin=YYYY-MM-DD]
```

**Campo clave para detección de novedades:** `consActuacion` (int incremental, equivalente al campo `Orden` de SAMAI)

**Response:**
```json
{
  "actuaciones": [
    {
      "idRegActuacion": 1383136310,
      "llaveProceso": "11001400300120240012600",
      "consActuacion": 5,
      "fechaActuacion": "2024-03-05T00:00:00",
      "actuacion": "Envío Expediente",
      "anotacion": "SE ENVIA A LA CORTE CONSTITUCIONAL...",
      "fechaInicial": null,
      "fechaFinal": null,
      "fechaRegistro": "2024-03-05T00:00:00",
      "codRegla": "00",
      "conDocumentos": false,
      "cant": 5
    }
  ],
  "paginacion": {
    "cantidadRegistros": 5,
    "registrosPagina": 40,
    "cantidadPaginas": 1,
    "pagina": 1
  }
}
```

**Notas:**
- Ordenadas **descendente** por `consActuacion` (la más reciente primero)
- `cant` = total de actuaciones del proceso (campo en cada item, igual en todos)
- `conDocumentos`: si la actuación tiene providencia adjunta
- Sin `fechaIni`/`fechaFin` retorna todas (paginadas, 40 por página)

---

### 3. Detalle del proceso

```
GET /Proceso/Detalle/{idProceso}
```

**Response:**
```json
{
  "idRegProceso": 14952588,
  "llaveProceso": "11001400300120240012600",
  "idConexion": 259,
  "esPrivado": false,
  "fechaProceso": "2024-02-12T00:00:00",
  "codDespachoCompleto": "110014003001",
  "despacho": "JUZGADO 001 CIVIL MUNICIPAL DE BOGOTÁ",
  "ponente": "EDUARDO ANDRES CABRALES ALARCON",
  "tipoProceso": "Acción de Tutela",
  "claseProceso": "Tutelas",
  "subclaseProceso": "Sin Subclase de Proceso",
  "recurso": "Sin Tipo de Recurso",
  "ubicacion": "Corte Constitucional",
  "contenidoRadicacion": null,
  "fechaConsulta": "2026-03-25T19:31:50.08",
  "ultimaActualizacion": "2026-03-25T19:30:01.197"
}
```

---

### 4. Sujetos procesales

```
GET /Proceso/Sujetos/{idProceso}
  ?pagina={int}
  [&nombre={filtro}]
```

**Response:**
```json
{
  "sujetos": [
    {
      "idRegSujeto": 150862026,
      "tipoSujeto": "Demandante",
      "esEmplazado": false,
      "identificacion": null,
      "nombreRazonSocial": "OSCAR IVAN HERNANDEZ SALAZAR",
      "cant": 2
    }
  ],
  "paginacion": { "cantidadRegistros": 2, "registrosPagina": 40, "cantidadPaginas": 1, "pagina": 1 }
}
```

**Nota:** `identificacion` es `null` en consulta pública (solo visible con auth y rol `VerCedulas`).

---

### 5. Documentos de actuación

```
GET /Proceso/DocumentosActuacion/{idRegActuacion}
GET /Descarga/DocumentoActuacion/{idDocumento}   → blob PDF
```

---

### 6. Búsqueda por nombre (>1000 → HTTP 400)

```
GET /Procesos/Consulta/NombreRazonSocial
  ?nombre={str}
  &tipoPersona={NAT|JUR}
  &SoloActivos={bool}
  &codificacionDespacho={str}
  &pagina={int}
```

Si hay más de 1000 resultados → HTTP 400:
```json
{
  "StatusCode": 400,
  "Message": "Hay más de mil registros con los criterios especificados..."
}
```

---

## Diferencias clave vs API SAMAI

| Característica | SAMAI | Rama Judicial CPNU |
|---|---|---|
| Campo consecutivo | `Orden` | `consActuacion` |
| ID proceso | radicado 23 dígitos directo | requiere búsqueda → `idProceso` |
| Flujo de consulta | 1 llamada (radicado → actuaciones) | 2 llamadas (radicado → idProceso → actuaciones) |
| Un radicado = un proceso | ✅ Siempre | ⚠️ Puede haber varios (distintos despachos) |
| Auth requerida | No | No (consulta pública) |
| Rate limiting | No detectado | No detectado |
| Timeout recomendado | 30s | 20s |
| Velocidad promedio | ~1-2s | ~0.45-0.55s ✅ más rápido |
| Jurisdicción | Contencioso-administrativa | Civil, penal, familia, laboral, tutelas, etc. |

---

## Decisión de arquitectura: múltiples idProceso por radicado

Un radicado puede existir en **múltiples despachos simultáneamente** (e.g., el mismo proceso en primera instancia y en apelación). Esto ocurre porque el mismo `llaveProceso` puede estar registrado en distintas conexiones.

**Solución para el monitor:**
- Al registrar un radicado, almacenar `idProceso` en DynamoDB (no recalcular en cada run)
- Si hay múltiples procesos para el mismo radicado, monitorear **todos** (crear un registro por idProceso)
- En el frontend, mostrarlos agrupados bajo el mismo radicado

**Campos adicionales necesarios en la tabla `radicados`:**
- `fuente` (S): `"samai"` | `"rama_judicial"` — distingue el origen
- `idProceso` (N): solo para `rama_judicial` — evita re-buscar en cada run

---

## Ejemplo Python completo

```python
import requests

BASE = "https://consultaprocesos.ramajudicial.gov.co:448/api/v2"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://consultaprocesos.ramajudicial.gov.co",
    "Referer": "https://consultaprocesos.ramajudicial.gov.co/",
    "Accept": "application/json, text/plain, */*",
}

def buscar_por_radicado(numero: str) -> list[dict]:
    """Busca procesos por número de radicación (23 dígitos sin guiones)."""
    r = requests.get(
        f"{BASE}/Procesos/Consulta/NumeroRadicacion",
        params={"numero": numero, "SoloActivos": "false", "pagina": 1},
        headers=HEADERS,
        timeout=20,
    )
    r.raise_for_status()
    return r.json().get("procesos", [])

def get_actuaciones(id_proceso: int, pagina: int = 1) -> list[dict]:
    """Retorna actuaciones de un proceso (descendente por consActuacion)."""
    r = requests.get(
        f"{BASE}/Proceso/Actuaciones/{id_proceso}",
        params={"pagina": pagina},
        headers=HEADERS,
        timeout=20,
    )
    r.raise_for_status()
    return r.json().get("actuaciones", [])

def get_max_cons_actuacion(id_proceso: int) -> int:
    """Retorna el consActuacion más alto (0 si no hay actuaciones)."""
    acts = get_actuaciones(id_proceso, pagina=1)
    if not acts:
        return 0
    return max(a["consActuacion"] for a in acts)

def get_actuaciones_nuevas(id_proceso: int, desde_cons: int) -> list[dict]:
    """Retorna solo las actuaciones con consActuacion > desde_cons."""
    todas = []
    pagina = 1
    while True:
        acts = get_actuaciones(id_proceso, pagina=pagina)
        if not acts:
            break
        for a in acts:
            if a["consActuacion"] <= desde_cons:
                # Están ordenadas desc, así que podemos cortar
                return [x for x in todas if x["consActuacion"] > desde_cons]
            todas.append(a)
        # Si la última actuación sigue siendo > desde_cons, hay más páginas
        if acts[-1]["consActuacion"] > desde_cons:
            pagina += 1
        else:
            break
    return [a for a in todas if a["consActuacion"] > desde_cons]
```

---

## Rate limiting y comportamiento

| Métrica | Valor |
|---|---|
| Rate limit detectado | Ninguno |
| Tiempo de respuesta | ~0.45–0.55s por request |
| Timeout recomendado | 20s |
| Requests concurrentes | No probados aún (prueba pendiente) |
| Bloqueo por User-Agent | No detectado |
| reCAPTCHA / CAPTCHA | No (consulta pública) |

---

## URLs del portal oficial

- Portal consulta: `https://consultaprocesos.ramajudicial.gov.co/procesos/Index`
- Manual usuario: `https://consultaprocesos.ramajudicial.gov.co/manual/`
- Publicaciones procesales: `https://publicacionesprocesales.ramajudicial.gov.co/`
