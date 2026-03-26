# INVENTARIO COMPLETO DE FEATURES — SAMAI
## Fecha: 22 de marzo de 2026
## Fuentes: web scraping, API Swagger (79 endpoints), manuales oficiales, artículos de prensa

---

# TABLA DE CONTENIDOS

1. [Modulos del Sistema](#1-modulos-del-sistema)
2. [Consulta de Procesos (Mis Procesos)](#2-consulta-de-procesos-mis-procesos)
3. [Secretaria Online / Notificaciones](#3-secretaria-online--notificaciones)
4. [Consulta de Estados](#4-consulta-de-estados)
5. [Ventanilla Virtual](#5-ventanilla-virtual)
6. [Relatoria (Mi Relatoria)](#6-relatoria-mi-relatoria)
7. [Biblioteca Digital](#7-biblioteca-digital)
8. [Sentencias TIC](#8-sentencias-tic)
9. [Calendario de Audiencias](#9-calendario-de-audiencias)
10. [Gestion de Usuarios y Autenticacion](#10-gestion-de-usuarios-y-autenticacion)
11. [API REST (79 endpoints)](#11-api-rest-79-endpoints)
12. [Datos del Proceso (detalle completo)](#12-datos-del-proceso-detalle-completo)
13. [Datos de Actuaciones](#13-datos-de-actuaciones)
14. [Datos de Documentos](#14-datos-de-documentos)
15. [Features de Competidores (referencia)](#15-features-de-competidores-referencia)
16. [Backlog Priorizado para samai-monitor](#16-backlog-priorizado-para-samai-monitor)

---

# 1. MODULOS DEL SISTEMA

SAMAI es el "sede electronica" de la Jurisdiccion Contencioso-Administrativa de Colombia. Tiene estos modulos principales:

| Modulo | URL | Requiere Auth | Estado en nuestro monitor |
|--------|-----|---------------|---------------------------|
| Mis Procesos | `/Vistas/Casos/procesos.aspx` | No (consulta publica) | IMPLEMENTADO (parcial) |
| Secretaria Online | `/Vistas/servicios/WSecretariaOnLine.aspx` | No | NO IMPLEMENTADO |
| Consulta de Estados | `/Vistas/utiles/WEstados.aspx` | No | NO IMPLEMENTADO |
| Notificaciones Art. 69 | `/Vistas/utiles/WONotificaciones.aspx?guid=VavisosCpaca` | No | NO IMPLEMENTADO |
| Estado Sentencia | `/Vistas/utiles/WONotificaciones.aspx?guid=VEstadoSentencia` | No | NO IMPLEMENTADO |
| Aviso a la Comunidad | `/Vistas/utiles/WONotificaciones.aspx?guid=Vcomunidad` | No | NO IMPLEMENTADO |
| Fijacion en Lista | `/Vistas/utiles/WFijacionLista.aspx` | No | NO IMPLEMENTADO |
| Edictos | `/Vistas/utiles/WONotificaciones.aspx?guid=Vedictos` | No | NO IMPLEMENTADO |
| Traslados | `/Vistas/utiles/WTraslados.aspx` | No | NO IMPLEMENTADO |
| Emplazados | `/Vistas/utiles/WONotificaciones.aspx?guid=Vemplazados` | No | NO IMPLEMENTADO |
| Ventanilla Virtual | `ventanillavirtual.consejodeestado.gov.co` | No (formularios) | NO IMPLEMENTADO |
| Mi Relatoria | `/TitulacionRelatoria/BuscadorProvidenciasTituladas.aspx` | No | NO IMPLEMENTADO |
| Biblioteca Digital | `/Vistas/servicios/WBibliotecaDigital.aspx` | No | NO IMPLEMENTADO |
| Sentencias TIC | `/Vistas/utiles/SentenciasTIC.aspx` | No | NO IMPLEMENTADO |
| Calendario Audiencias | `consejodeestado.gov.co/audiencia-virtuales/` | No | NO IMPLEMENTADO |
| Login / Registro | `/login.aspx`, `/Register.aspx` | Si | N/A (usamos Cognito) |
| Proceso Individual | `/Vistas/Casos/list_procesos.aspx?guid={radicado}` | No | IMPLEMENTADO (detalle) |

---

# 2. CONSULTA DE PROCESOS (MIS PROCESOS)

**URL**: `https://samai.consejodeestado.gov.co/Vistas/Casos/procesos.aspx`

## 2.1. Criterios de busqueda

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| Numero de radicado | Text (23 digitos) | Busqueda por radicado completo o parcial, sin guiones |
| Clase de proceso | Dropdown | Tipo/clase de proceso judicial |
| Sujeto procesal | Text | Busqueda por nombre de parte procesal |
| Corporacion | Dropdown | Seleccionar corporacion especifica |
| Seccion/Sala | Dropdown | Filtrar por seccion de la corporacion |
| Despacho | Dropdown | Filtrar por despacho judicial |
| Ponente | Dropdown | Filtrar por magistrado ponente |

## 2.2. Datos mostrados en resultados

| Columna | Descripcion |
|---------|-------------|
| Radicacion | Numero de radicado con formato (enlace al proceso) |
| Ponente | Nombre del magistrado ponente |
| Demandante (Actor) | Nombre del demandante |
| Demandado | Nombre(s) del(los) demandado(s) |
| Clase de Proceso | Tipo: Acciones Populares, Nulidad, etc. |
| Estado | Vigente/Archivado |

## 2.3. Acciones disponibles

- **Ver detalle del proceso**: Click en radicado abre pagina de detalle
- **Ver historial de actuaciones**: Timeline completa del proceso
- **Ver sujetos procesales**: Partes del proceso con roles
- **Descargar documentos**: PDFs de providencias y autos
- **Enlace permanente**: URL directa al proceso via GUID

---

# 3. SECRETARIA ONLINE / NOTIFICACIONES

**URL**: `https://samai.consejodeestado.gov.co/Vistas/servicios/WSecretariaOnLine.aspx`

## 3.1. Tipos de notificaciones disponibles

| Tipo | URL param | Descripcion |
|------|-----------|-------------|
| Avisos Art. 69 (CPACA) | `guid=VavisosCpaca` | Notificacion por aviso segun Ley 1437/2011 |
| Estado Sentencia | `guid=VEstadoSentencia` | Notificacion de sentencias publicadas |
| Aviso a la Comunidad (Art. 171.5) | `guid=Vcomunidad` | Publicaciones de interes comunitario |
| Edictos | `guid=Vedictos` | Edictos judiciales (cuando no se puede notificar personalmente) |
| Emplazados | `guid=Vemplazados` | Lista de personas emplazadas judicialmente |

## 3.2. Fijacion en Lista

**URL**: `/Vistas/utiles/WFijacionLista.aspx`

- Lista de procesos fijados para notificacion en cartelera
- Filtros por corporacion y seccion
- Periodo de fijacion visible

## 3.3. Traslados

**URL**: `/Vistas/utiles/WTraslados.aspx`

- Notificaciones de traslados entre despachos
- Informacion del proceso trasladado
- Filtros por corporacion

## 3.4. Estructura comun de todas las notificaciones

Cada notificacion incluye:
- Corporacion emisora
- Seccion/Sala
- Fecha de publicacion
- Radicado del proceso
- Tipo de providencia
- Detalle/Anotacion
- Enlace de descarga del documento (cuando aplica)

---

# 4. CONSULTA DE ESTADOS

**URL**: `https://samai.consejodeestado.gov.co/Vistas/utiles/WEstados.aspx`

## 4.1. Flujo de consulta (3 pasos HTTP)

```
PASO 1: GET  WEstados.aspx                    --> HTML con dropdown de 76 corporaciones
PASO 2: POST (seleccionar corporacion)         --> Aparecen 4 dropdowns adicionales
PASO 3: POST (CmdBuscar = "Consultar")         --> Tabla GridView con resultados
```

## 4.2. Controles del formulario ASP.NET

| Control | Nombre ASP.NET | Tipo | Descripcion |
|---------|----------------|------|-------------|
| Corporacion | `ctl00$MainContent$LstCorpHabilitada` | Dropdown | 76 opciones (Consejo + Tribunales + Juzgados) |
| Seccion/Sala | `ctl00$MainContent$LstCoorporacion` | Dropdown | Se puebla segun corporacion |
| Fecha | `ctl00$MainContent$LstUEstados` | Dropdown | 15 fechas mas recientes (DD/MM/YYYY) |
| Ponente | `ctl00$MainContent$LstPonente` | Dropdown | Magistrados de la seccion |
| Criterio | `ctl00$MainContent$LstCriterio` | Dropdown | Na, Dte, Ddo, Rad, Fec |
| Texto busqueda | `ctl00$MainContent$Txtcriterio` | Search input | Aparece cuando criterio != Na |
| Boton buscar 1 | `ctl00$MainContent$ImgBuscar2` | Image button | Primera busqueda |
| Boton buscar 2 | `ctl00$MainContent$ImgBuscar3` | Image button | Segunda busqueda |
| Boton consultar | `ctl00$MainContent$CmdBuscar` | Submit | Ejecutar consulta |

## 4.3. Criterios de filtro

| Criterio | Codigo | Funcionalidad |
|----------|--------|---------------|
| Sin criterio | Na | Muestra TODOS los estados del dia seleccionado |
| Demandante | Dte | Busca por nombre de demandante |
| Demandado | Ddo | Busca por nombre de demandado |
| Radicacion | Rad | Busca por numero de radicado (devuelve historial completo) |
| Fechas | Fec | Permite rango de fechas |

## 4.4. Columnas de la tabla de resultados (GridView)

| Columna | Campo | Ejemplo |
|---------|-------|---------|
| Reg | Numero de fila | 1, 2, 3... |
| Radicacion | Radicado con formato | 73001-23-33-000-2019-00343-00 (enlace) |
| Ponente | Magistrado | BELISARIO BELTRAN BASTIDAS |
| Demandante | Actor | JOYCE ALEXANDRA AVILES LOZANO |
| Demandado | Demandado | MUNICIPIO DEL CARMEN DE APICALA... |
| Clase | Tipo de proceso | ACCIONES POPULARES |
| Fecha Providencia | Fecha | 19/03/2026 |
| Actuacion | Tipo de actuacion | Auto reconoce personeria |
| Docum. a notif. | Detalle/Anotacion | BBB-RECONOCER personeria... |
| Descargar | URL descarga | Link al PDF de la providencia |

## 4.5. Corporaciones (76 totales)

Muestra representativa:

| Codigo | Corporacion |
|--------|-------------|
| 1100103 | Consejo de Estado |
| 1100133 | Juzgado Administrativo de Bogota |
| 0500133 | Juzgado Administrativo de Medellin |
| 7600133 | Juzgado Administrativo de Cali |
| 0800133 | Juzgado Administrativo de Barranquilla |
| 7300123 | Tribunal Administrativo del Tolima |
| 2500023 | Tribunal Administrativo de Cundinamarca |
| 0500123 | Tribunal Administrativo de Antioquia |

## 4.6. GUID de proceso en URLs de SAMAI

El `guid` que aparece en `list_procesos.aspx?guid=...` es la concatenacion de:
```
GUID (30 chars) = radicado_23_digitos + corporacion_7_digitos
```
Ejemplo: `guid=110013335030202400100012500023`
- Radicado: `11001333503020240010001` (23 digitos)
- Corporacion: `2500023` = Tribunal Administrativo de Cundinamarca

**IMPORTANTE - Los primeros 7 digitos del radicado NO siempre coinciden con el codigo SAMAI:**
- Un radicado `11001333...` puede estar en el Tribunal de Cundinamarca (`2500023`), no en el Juzgado de Bogota (`1100133`)
- Esto ocurre cuando el proceso es llevado por un Tribunal de la region, aunque el radicado encode la ciudad (Bogota=`11001`)
- Nuestro `extraer_corporacion` usa primeros 7 digitos como default, y hace fallback probando
  los 28 Tribunales + Consejo de Estado en paralelo (ThreadPoolExecutor) cuando el default falla

---

# 5. VENTANILLA VIRTUAL

**URL**: `https://ventanillavirtual.consejodeestado.gov.co/`

## 5.1. Recepcion de Demandas

| Servicio | Descripcion |
|----------|-------------|
| Tutelas y Habeas Corpus | Radicacion de acciones de tutela y habeas corpus |
| Sala de Consulta | Consultas del Gobierno y conflictos de competencia administrativa |
| Otras demandas | Acciones constitucionales y recursos extraordinarios |

## 5.2. Solicitudes y Servicios en Linea

| Servicio | Descripcion |
|----------|-------------|
| Copias simples | Copias digitales enviadas por email |
| Copias autenticas | Informacion sobre tramite y costos |
| Memoriales | Presentacion de documentos para procesos en curso (PDF, DOCX, DOC, max 10MB) |
| Acceso virtual a expedientes | Solicitud de autorizacion para acceder a SAMAI |
| Citas virtuales | Solicitar callback del personal de secretaria |
| Consulta de estado de solicitud | Rastrear envios y reclamos por la ventanilla |

## 5.3. Cartelera Virtual (Tablero de publicaciones)

| Publicacion | Descripcion |
|-------------|-------------|
| Notificaciones por estado | Estados publicados diariamente |
| Notificacion por estado de sentencias | Sentencias publicadas |
| Traslados | Documentos trasladados entre despachos |
| Fijacion en lista | Avisos fijados en cartelera |
| Edictos | Edictos judiciales |
| Consulta de procesos | Acceso a busqueda de procesos |

## 5.4. Horarios

- **Ventanilla Virtual**: 24/7 (pero no afecta terminos judiciales)
- **Atencion presencial**: Lunes-Viernes, 8:00-13:00 y 14:00-17:00
- **Regla de radicacion**: Documentos recibidos fuera de horario se registran como presentados el siguiente dia habil

---

# 6. RELATORIA (MI RELATORIA)

**URL**: `https://samai.consejodeestado.gov.co/TitulacionRelatoria/BuscadorProvidenciasTituladas.aspx`

## 6.1. Funcionalidades de busqueda

| Feature | Descripcion |
|---------|-------------|
| Busqueda por concepto | Escribir temas, frases clave, conceptos legales |
| Busqueda por radicado | Numero de proceso completo |
| Filtros de control | Medios especificos de decision |
| Filtros de refinamiento | Refinar resultados por multiples criterios |
| Precision en resultados | Motor de busqueda semantica |

## 6.2. Tipos de documentos descargables

| Tipo | Descripcion |
|------|-------------|
| Providencias | Sentencias, autos, conceptos |
| Aclaraciones de voto | Notas de magistrados disidentes |
| Salvamentos de voto | Votos en contra documentados |
| Fichas de titulacion | Metadata de la providencia |

## 6.3. Features avanzadas

| Feature | Descripcion |
|---------|-------------|
| Descarga masiva | Descargar multiples providencias en ZIP |
| Descarga individual | Descargar una providencia especifica |
| Reporte de busqueda por email | Enviar resultados de busqueda al correo |
| Enlaces permanentes | URL con criterios de busqueda para reutilizar |
| Boletin mensual de jurisprudencia | Suscripcion gratuita por email |
| Cobertura temporal | Providencias tituladas desde diciembre 2021 |
| Sistema legado | Acceso a providencias anteriores a dic 2021 |

---

# 7. BIBLIOTECA DIGITAL

**URL**: `https://samai.consejodeestado.gov.co/Vistas/servicios/WBibliotecaDigital.aspx`

- Acceso a documentos y recursos legales digitalizados
- Coleccion de publicaciones del Consejo de Estado
- Documentos de referencia juridica

---

# 8. SENTENCIAS TIC

**URL**: `https://samai.consejodeestado.gov.co/Vistas/utiles/SentenciasTIC.aspx`

- Sentencias relacionadas con tecnologias de la informacion
- Decisiones del Consejo de Estado, Corte Suprema y Corte Constitucional sobre TIC
- Busqueda especializada por temas tecnologicos

---

# 9. CALENDARIO DE AUDIENCIAS

**URL**: `https://www.consejodeestado.gov.co/audiencia-virtuales/index.htm`

- Calendario de audiencias programadas (virtuales y presenciales)
- Filtros por fecha y seccion
- Enlaces a las audiencias virtuales

---

# 10. GESTION DE USUARIOS Y AUTENTICACION

## 10.1. Tipos de usuarios

| Tipo | Descripcion | Acceso |
|------|-------------|--------|
| Servidor judicial | Magistrados, secretarios, asistentes | Completo (gestion interna) |
| Sujeto procesal | Abogados, partes del proceso | Limitado (consulta + memoriales) |
| Publico general | Cualquier ciudadano | Solo consulta publica |

## 10.2. Flujo de registro (usuario externo)

1. Solicitar acceso via Ventanilla Virtual -> "Acceso virtual a expedientes"
2. Aceptar terminos y condiciones de proteccion de datos (Ley 1581/2012)
3. Llenar formulario: identificacion, nombre, apellido, email
4. Subir documento de identidad (PDF/DOCX/XLSX, max 20MB)
5. Ingresar radicado de 23 digitos -> "Buscar radicacion"
6. Verificar datos del caso y "Anadir esta radicacion" (puede ser multiple)
7. Enviar formulario -> Esperar respuesta por email del despacho
8. Si aprobado -> Registrarse en SAMAI:
   - Aceptar acuerdo de confidencialidad
   - Ingresar datos (num. identificacion, nombre, apellido, email)
   - Recibir codigo de validacion por email
   - Crear contrasena (min 8 caracteres: mayuscula + minuscula + numero + especial)
9. Login con identificacion + contrasena

## 10.3. Features post-login (sujeto procesal)

| Feature | Descripcion |
|---------|-------------|
| Consultar procesos | Ver detalle de procesos autorizados |
| Subir memoriales | Presentar documentos al despacho |
| Validar documentos | Verificar documentos del expediente |
| Descargar expediente | Bajar documentos del caso |
| Ver expediente digital | Acceso al expediente electronico completo |

---

# 11. API REST (79 ENDPOINTS)

**Base URL**: `https://samaicore.consejodeestado.gov.co/api/`
**Swagger**: `https://samaicore.consejodeestado.gov.co/swagger`
**Spec JSON**: `https://samaicore.consejodeestado.gov.co/swagger/v1/swagger.json`
**Titulo**: "Servicios SAMAI Para Integraciones"
**Total**: 79 endpoints, 92 schemas

## 11.1. Endpoints PUBLICOS (sin autenticacion, modo=2)

| Metodo | Endpoint | Descripcion | En nuestro monitor |
|--------|----------|-------------|---------------------|
| GET | `/api/Procesos/HistorialActuaciones/{corp}/{rad}/{modo}` | Historial completo de actuaciones | SI |
| GET | `/api/ObtenerDatosProcesoGet/{corp}/{numProc}/{modo}` | Datos completos del proceso + archivos | SI |
| GET | `/api/BuscarProcesoTodoSamai/{numProc}/{modo}` | Buscar proceso en todo SAMAI | SI |
| GET | `/api/Procesos/SujetosProcesales/{corp}/{rad}/{modo}` | Partes procesales del caso | SI |
| GET | `/api/DescargarProvidenciaPublica/{corp}/{numProc}/{hash}/{modo}` | Descargar PDF de providencia | SI |
| GET | `/api/Procesos/AvisoAlaComunidad/{corp}/{modo}` | Avisos a la comunidad | NO |
| GET | `/api/ObtenerListadoProcesos/{corp}/{modo}` | Listado de procesos con filtro de fecha | NO |
| GET | `/api/ObtenerNovedadesReparto/{corp}/{codipadr}/{modo}/{f1}/{f2}` | Novedades de reparto en rango de fechas | NO |
| GET | `/` | Health check | N/A |

## 11.2. Endpoints de GESTION DOCUMENTAL

| Metodo | Endpoint | Descripcion | Auth |
|--------|----------|-------------|------|
| GET | `/api/DescargarProvidenciaPublica/{corp}/{numProc}/{hash}/{modo}` | Descargar providencia/auto PDF | No |
| GET | `/api/DescargarProvidenciaSAMAI?tokendoc=` | Descargar archivo SAMAI con token | Si (token) |
| GET | `/api/DescargarProvidenciaSAMAIZipDossierIE?tokendoc=` | Descargar ZIP expediente electronico IE | Si (token) |
| GET | `/api/DescargarProvidenciaSAMAIZipExpediente?tokendoc=` | Descargar ZIP expediente no IE | Si (token) |
| GET | `/api/DescargarTitulacion/{corp}/{numProc}/{hash}/{modo}` | Descargar ficha de titulacion | Modo 2 |
| GET | `/api/DescargarDossierIEJSON/{corp}/{tracker}/{modo}` | Descargar JSON del expediente electronico | Modo 2 |
| GET | `/api/DescargarDossierIEPDF/{corp}/{tracker}/{modo}` | Descargar PDF del expediente electronico | Modo 2 |
| GET | `/api/DescargarZipTitulacionPagina/{corp}/{pag}/{total}/{modo}` | Descargar ZIP de titulaciones paginado | Modo 2 |

## 11.3. Endpoints de INDICE ELECTRONICO (IE)

| Metodo | Endpoint | Descripcion | Auth |
|--------|----------|-------------|------|
| POST | `/api/CrearExpedienteIESAMAI` | Crear expediente electronico | JWT |
| POST | `/api/SubirArchivoIESAMAI` | Subir archivo al expediente | JWT |
| GET | `/api/ObtenerDocumentosIEProceso/{corp}/{numProc}/{modo}` | Obtener documentos del IE | Modo 2 |
| GET | `/api/TiposDocumentalesSubSerie/{corp}/{subSeries}/{modo}` | Tipos documentales por sub-serie | Modo 2 |

## 11.4. Endpoints de ALMACENAMIENTO AZURE

| Metodo | Endpoint | Descripcion | Auth |
|--------|----------|-------------|------|
| GET | `/api/ListadoArchivosBlobStorage/{cont}/{corp}/{numProc}/{modo}` | Listar documentos en Azure Storage | JWT |
| GET | `/api/BuscarArchivoBlobStorageEnContenedores/{corp}/{numProc}/{modo}` | Buscar archivo en contenedores | JWT |
| GET | `/api/PropiedadesArchivoBlobStorage/{corp}/{numProc}/{nombre}/{modo}` | Propiedades de archivo en blob | JWT |
| POST | `/api/SubirArchivoBlobStorage` | Subir archivo a Azure Storage | JWT |
| POST | `/api/MoverArchivosDeProcesoAzure` | Mover archivos entre procesos | JWT |
| POST | `/api/MoverBlobDeContainer` | Mover blob entre containers | JWT |
| POST | `/api/MoverDesdetTmpDataBlob` | Mover desde TmpData | JWT |
| POST | `/api/RenombrarBlob` | Renombrar archivo | JWT |
| POST | `/api/RestaurarBlob` | Restaurar blob eliminado | JWT |

## 11.5. Endpoints ADMINISTRATIVOS

| Metodo | Endpoint | Descripcion | Auth |
|--------|----------|-------------|------|
| POST | `/api/AutenticarAdministrador` | Obtener token admin (envio por email) | APIKEY |
| DELETE | `/api/BorrarUltimaActuacionDuplicada` | Borrar actuacion duplicada | JWT |
| PUT | `/api/CambiarCorreoUsuario` | Cambiar email de usuario judicial | JWT |
| PUT | `/api/CambiarCorreoUsuarioVentanilla` | Cambiar email usuario ventanilla | JWT |
| PUT | `/api/CambiarDependenciaUsuario` | Cambiar dependencia de usuario | JWT |
| GET | `/api/ObtenerCorreosUsuario/{numDoc}` | Obtener emails de usuario | JWT |
| GET | `/api/ObtenerDependencias` | Listar dependencias | JWT |
| GET | `/api/ObtenerNivelUsuario` | Obtener nivel de acceso | JWT |
| GET | `/api/ObtenerValidacionArchivoExpediente` | Validar archivo de expediente | JWT |
| POST | `/api/ForzarAcuse` | Forzar acuse de recibo | JWT |
| POST | `/api/PublicarBanner` | Publicar banner/noticia | JWT |
| GET | `/api/ValidarTokenAutenticacion` | Validar token JWT | JWT |

## 11.6. Endpoints de INTEROPERABILIDAD

| Metodo | Endpoint | Descripcion | Auth |
|--------|----------|-------------|------|
| POST | `/api/AutenticarLinkCE` | Token para LinkCE (interoperabilidad) | APIKEY |
| GET | `/api/ModuloActuacionesProceso/{corp}/{numProc}` | Actuaciones con filtros avanzados (ubicacion, tipo, codigos) | JWT |
| GET | `/api/ModuloFirmas/{corp}` | Modulo de firmas digitales | JWT |
| GET | `/api/ModuloGestionProceso/{corp}/{numProc}` | Gestion integral del proceso | JWT |
| GET | `/api/ModuloPartesSujetos/{corp}/{numProc}` | Partes y sujetos (con filtro codsjue) | JWT |
| GET | `/api/ModuloSeguimientoOficios/{corp}/{codEsp}` | Seguimiento de oficios | JWT |
| POST | `/api/AutenticarSIUJ` | Token para SIUJ | APIKEY |
| POST | `/api/ConocimientoPrevioSIUJ` | Procesos de instancia superior | JWT |
| POST | `/api/ProcesosSimilaresSIUJ` | Procesos similares ya repartidos | JWT |
| POST | `/api/RadicarProcesoSIUJ` | Radicar proceso desde SIUJ | JWT |

## 11.7. Endpoints de REPORTES

| Metodo | Endpoint | Descripcion | Auth |
|--------|----------|-------------|------|
| GET | `/api/AuditoriaRelatoria/{corp}/{modo}` | Auditoria de repartos de relatoria | Modo 2 |
| POST | `/api/ProvidenciasTituladas` | Reporte de providencias tituladas (CENDOJ) | JWT |
| POST | `/api/ReporteTitulacion` | Reporte de titulacion por rango de fechas | JWT |
| POST | `/api/Reporte` | Reporte Observatorio Ley 2080 | JWT |
| GET | `/api/ReportesT802REPORTESAUDITORIA/{cat}` | Reportes de auditoria | JWT |

## 11.8. Endpoints de SERVICIOS EXTERNOS

| Metodo | Endpoint | Descripcion | Auth |
|--------|----------|-------------|------|
| POST | `/api/AcuseReciboNotificaciones` | Acuse de recibo de notificaciones (Azure) | -- |
| POST | `/api/CorreosMasivosAlDespachoPorReparto` | Envio de emails masivos por reparto | JWT |
| GET | `/api/RNCConsultaCedula/{identificacion}` | Consultar cedula en RNC | JWT |
| GET | `/api/SIRNAConsultaAbogado/{id}/{tipoId}` | Consultar abogado en SIRNA | JWT |
| POST | `/api/CorteConstitucionalDatosBasicos` | Datos basicos para Corte Constitucional | JWT |
| POST | `/api/CorteConstitucionalDatosExpediente` | Expediente para Corte Constitucional | JWT |
| GET | `/api/RecibirDocumentosDIAN/{corp}/{numProc}/{expId}/{modo}` | Recibir documentos de la DIAN | JWT |

## 11.9. Endpoints de VENTANILLA VIRTUAL (API)

| Metodo | Endpoint | Descripcion | Auth |
|--------|----------|-------------|------|
| GET | `/api/VentanillaVirtual/ConsultarDatosDespachoCorreo/{desp}/{corp}/{modo}` | Datos del despacho y correo | JWT |
| GET | `/api/VentanillaVirtual/DatosProceso/{corp}/{rad}/{tipoSol}/{modo}` | Datos de proceso para ventanilla | JWT |

## 11.10. Endpoints de VOCABULARIO CONTROLADO

| Metodo | Endpoint | Descripcion | Auth |
|--------|----------|-------------|------|
| GET | `/api/VocabularioControlado/BuscarTerminos/{term}` | Buscar terminos juridicos | -- |
| GET | `/api/VocabularioControlado/ObtenerTerminosdeID/{id}` | Obtener termino por ID | -- |

## 11.11. Otros endpoints

| Metodo | Endpoint | Descripcion | Auth |
|--------|----------|-------------|------|
| GET | `/api/BuscarIdRelatoriaAntigua/{id}/{corp}/{modo}` | Buscar en relatoria antigua (pre-dic 2021) | Modo 2 |
| GET | `/api/BuscarIdRelatoriaAntiguaDatosCreacion/{id}/{corp}/{modo}` | Datos de creacion relatoria antigua | Modo 2 |
| GET | `/api/BuscarTitulacionAntigua/{rad}/{dd}/{mm}/{yyyy}/{corp}/{modo}` | Buscar titulacion antigua por fecha | Modo 2 |
| GET | `/api/TiposDocumentalesCuadernos/{corp}/{modo}` | Tipos documentales por cuaderno | Modo 2 |
| POST | `/api/SincronizarSARJIntermedia` | Sincronizar SAMAI con BD intermedia de reparto | JWT |
| POST | `/api/SolicitarConsecutivoRadicacion` | Solicitar consecutivo de radicacion | JWT |
| POST | `/api/RenombrarRadicado` | Renombrar radicado de proceso | JWT |
| POST | `/api/SubirArchivoSAMAI` | Subir archivo y crear registros | JWT |
| PUT | `/api/SubirArchivoLocal` | Subir a carpeta local | APIKEY |
| POST | `/api/ValidarArchivoLocal` | Validar archivo local | APIKEY |
| DELETE | `/api/DeleteArchivoLocal` | Eliminar archivo local | APIKEY |
| PUT | `/api/DescargarArchivoARutaLocal` | Descargar de SAMAI a ruta local | JWT |

---

# 12. DATOS DEL PROCESO (DETALLE COMPLETO)

Campos retornados por `GET /api/ObtenerDatosProcesoGet/{corp}/{numProc}/{modo}`:

## 12.1. Datos principales del proceso

| Campo | Tipo | Ejemplo | Descripcion |
|-------|------|---------|-------------|
| radicado | string(23) | 73001233300020190034300 | Radicado sin guiones |
| Instancia | string | 0001 | Codigo de instancia |
| DescripcionInstancia | string | Primera Instancia | Nombre legible |
| Interno | string | SE DECLARE QUE... | Asunto/pretensiones del proceso |
| FECHAPROC | datetime | 2019-08-12 | Fecha del proceso |
| FECHREGI | datetime | 2019-08-12 | Fecha de registro |
| cityCode | string(5) | 73001 | Codigo DANE de la ciudad |
| cityName | string | IBAGUE (TOLIMA) | Ciudad y departamento |
| CodigoProceso | string | 3005 | Codigo interno del tipo |
| tipoProceso | string | Especiales | Tipo de proceso |
| CodigoClase | string | 0008 | Codigo de clase |
| claseProceso | string | ACCIONES POPULARES | Clase de proceso |
| claseProcesoComplemento1 | string | -- | Complemento 1 |
| claseProcesoComplemento2 | string | -- | Complemento 2 |
| CodEspecialidad | string | 23 | Codigo de especialidad |
| CodNuenRadi | string | 000 | Consecutivo de recurso |
| EntidadRadicadora | string | 730012333000 | Entidad que radico |
| Seccion | string | JUZGADO ADMINISTRATIVO | Seccion del despacho |
| NombreSalaDecision | string | JUZGADO ADMINISTRATIVO | Sala de decision |
| CodigoSalaDecision | string | 33 | Codigo de sala |
| NombreSalaRadicacion | string | JUZGADO ADMINISTRATIVO | Sala de radicacion |
| SubSeccion | string | (vacio) | Sub-seccion |
| CodigoPonente | string | 1105 | Codigo del magistrado |
| Ponente | string | BELISARIO BELTRAN BASTIDAS | Nombre del ponente |
| A101NUMEDOCU | string | 14228251 | Documento del ponente |
| CodDespacho | string | 730012333005 | Codigo del despacho |
| IdSeccion | string | 33 | ID seccion |
| NaturalezaProceso | string | Sin Naturaleza | Naturaleza |
| Vigente | string | SI | Si el proceso esta activo |
| Actor | string | JOYCE ALEXANDRA AVILES... | Demandante(s) |
| Demandado | string | MUNICIPIO DEL CARMEN... | Demandado(s) |
| UltimaActuacionSecretariaFechas | string | 2026-03-19 | Fecha ultima act. secretaria |
| UltimaActuacionSecretariaDescripciones | string | POR NOTIFICAR | Descripcion ultima act. sec. |
| UltimaActuacionDespachoFecha | string | Mar 19 2026 4:31PM | Fecha ultima act. despacho |
| UltimaActuacionDespachoDescripcion | string | Fijacion estado | Descripcion ultima act. desp. |
| UltimaActuacionDespachoAnotacion | string | LMB- | Anotacion ultima act. desp. |
| ProcesoArchivado | string | NO | Si esta archivado |
| FechaFinalizacionProceso | datetime? | null | Fecha de finalizacion |
| CodigoEtapa | int | 52989 | Codigo de etapa procesal |
| Etapa | string | Admision | Etapa actual del proceso |
| seriesCode | string? | null | Codigo de serie documental |
| subSeriesCode | string? | null | Codigo sub-serie |

## 12.2. Contadores

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| cantidadDocumentos | int | Total de documentos en el expediente |
| cantidadActuaciones | int | Total de actuaciones registradas |

---

# 13. DATOS DE ACTUACIONES

Campos retornados por `GET /api/Procesos/HistorialActuaciones/{corp}/{rad}/{modo}`:

| Campo | Tipo | Ejemplo | Descripcion |
|-------|------|---------|-------------|
| A110LLAVPROC | string(23) | 73001233300020190034300 | Radicado del proceso |
| Orden | int | 177 | Numero secuencial (clave para detectar novedades) |
| CodiActuacion | string | 00000108 | Codigo de la actuacion |
| Indice | int | 177 | Indice de la actuacion |
| Registro | datetime | 2026-03-19T16:31:57 | Timestamp exacto de registro |
| Actuacion | datetime | 2026-03-20T00:00:00 | Fecha de la actuacion |
| NombreActuacion | string | Fijacion estado | Tipo de actuacion |
| ActuacionEnProceso | string | Fijacion estado | Nombre en contexto del proceso |
| Anotacion | string | LMB-... | Detalle/notas de la actuacion |
| Estado | string | REGISTRADA | Estado de la actuacion |
| CodigoDecision | string? | null | Codigo de decision (cuando aplica) |
| DescripcionDecision | string? | null | Descripcion de la decision |
| CantidadDocumentos | int | 0 o 1+ | Documentos asociados |
| SIERJU | array | [] | Referencias SIERJU |
| Documentos | array | [...] | Documentos adjuntos |

---

# 14. DATOS DE DOCUMENTOS

Campos de cada documento dentro de una actuacion:

| Campo | Tipo | Ejemplo | Descripcion |
|-------|------|---------|-------------|
| physicalLocation | string | Electronico | Ubicacion fisica |
| creationDate | datetime | 2026-03-19T10:48:26 | Fecha de creacion |
| Cuaderno | string | Cuaderno principal | Cuaderno del expediente |
| TIPODOCUMENTAL | string | (vacio) | Tipo documental |
| nombreActuacion | string | Auto reconoce personeria | Actuacion asociada |
| CONSACTU | int | 175 | Consecutivo de actuacion |
| A121DESCDOCU | string | 103Autoreconocep_0002... | Descripcion del documento |
| comment | string | 103Autoreconocep... Indice: 175 | Comentario |
| ORDENDOCU | string | 103 | Orden del documento |
| NOMBDOCU | string | 103_Autoreconocep_...pdf | Nombre del archivo |
| NombreCompletoArchivo | string | 103_Autoreconocep_...pdf | Nombre completo con extension |
| A121TIPODOCU | string | P | Tipo: P=Providencia |
| contenedorBlob | string | 7300123 | Container en Azure Blob |
| FUNCHASH | string | F8D9D86C24D8... | Hash para descarga |
| A121SIZEKB | int | 88 | Tamano en KB |
| QUIENFIRMA | string | Ponente | Quien firmo |
| CantidadFirmantes | int | 1 | Numero de firmantes |
| Validado | bool | true | Si esta validado |
| ArchivoEnNube | string | True | Si esta en cloud |
| Firmantes | array | [...] | Lista de firmantes con detalle |

### Datos de firmante

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| IDFIRMA | int | ID de la firma |
| FECHAFIRMA | datetime | Fecha y hora de la firma |
| IDFIRMANTE | string | Documento del firmante |
| NOMBREFIRMANTE | string | Nombre completo |
| ESTADO | string | "Firmado en SAMAI (fecha)" |
| Voto | string | Tipo de voto (vacio si no aplica) |
| SinAclaracion | int | 1/0 - sin aclaracion |
| ConAclaracionDeVoto | int | 1/0 - con aclaracion |
| ConSalvamentoDeVoto | int | 1/0 - con salvamento |
| ConSalvamentoParcialDeVoto | int | 1/0 - con salvamento parcial |

---

# 15. FEATURES DE COMPETIDORES (REFERENCIA)

Features que los competidores ofrecen y que podemos considerar para nuestro backlog:

| Feature | Monolegal | Expedientes.co | Nuestro monitor |
|---------|-----------|----------------|-----------------|
| Monitoreo diario de actuaciones | Si | Si | SI |
| Alertas por email | Si (<8AM) | Si | SI |
| Alertas push movil | Si | No | NO |
| App movil nativa | Si (iOS+Android) | No (solo Chrome ext) | NO |
| Multi-sistema (SAMAI+SIUGJ+Siglo21+TYBA) | Si (5 fuentes) | Si | NO (solo SAMAI) |
| Deteccion de audiencias con IA | Si (desde 2017) | No | NO |
| Deteccion cambio de instancia | Si | No | NO |
| Expediente digital completo | Si | Si | PARCIAL |
| Exportacion Excel/CSV | Si | Si | SI (CSV) |
| Multi-usuario por cuenta | Si | Si | NO |
| Dashboard/estadisticas | Basico | Si | BASICO |
| Busqueda por nombre/cedula | No | Si (33M procesos) | NO |
| Busqueda por sujetos procesales | No | Si (80M sujetos) | SI (SAMAI search) |
| Alertas configurables (tipo/urgencia) | Si | No | NO |
| Frecuencia configurable | Si (diaria/semanal) | No | NO (solo diaria) |
| Descarga de providencias PDF | Si | Si | SI |
| Free trial | 15 dias | No | NO |

---

# 16. BACKLOG PRIORIZADO PARA SAMAI-MONITOR

Basado en el inventario completo, priorizamos features por impacto y viabilidad:

## P0 - Ya implementado

- [x] Monitoreo de actuaciones por radicado (API HistorialActuaciones)
- [x] Alertas por email (SES)
- [x] Busqueda de procesos (API BuscarProcesoTodoSamai)
- [x] Ver detalle de proceso (API ObtenerDatosProcesoGet)
- [x] Ver sujetos procesales (API SujetosProcesales)
- [x] Descargar providencias PDF (API DescargarProvidenciaPublica)
- [x] Dashboard con lista de radicados monitoreados
- [x] Dark mode
- [x] Exportacion CSV
- [x] Pausar/reanudar monitoreo
- [x] Marcar alertas como leidas
- [x] Editar alias de radicado

## P1 - Alta prioridad (alto impacto, datos disponibles via API publica)

- [ ] Consulta de Estados diaria (scraping WEstados.aspx) -- alerta proactiva sin necesidad de registrar radicado
- [ ] Avisos a la Comunidad (API AvisoAlaComunidad) -- endpoint publico no explorado
- [ ] Listado de Procesos por corporacion (API ObtenerListadoProcesos) -- endpoint publico con filtro de fechas
- [ ] Novedades de Reparto (API ObtenerNovedadesReparto) -- novedades en rango de fechas
- [ ] Multi-usuario por cuenta (compartir procesos en equipo de abogados)
- [ ] Alertas configurables (filtrar por tipo de actuacion, urgencia)
- [ ] Free trial (15 dias como Monolegal)

## P2 - Media prioridad (diferenciadores)

- [ ] Notificaciones (Art. 69, edictos, traslados, fijacion lista, emplazados) -- scraping de cada pagina
- [ ] Relatoria / Jurisprudencia -- busqueda de providencias tituladas
- [ ] Deteccion de audiencias (parsear anotaciones buscando "audiencia", "fecha", "hora")
- [ ] Deteccion de cambio de instancia (comparar instancia actual vs anterior)
- [ ] Deteccion de sentencia (actuacion con tipo sentencia)
- [ ] Calendario de audiencias del despacho
- [ ] Alertas push (web notifications / PWA)
- [ ] Frecuencia configurable (diaria/semanal/personalizada)

## P3 - Baja prioridad (nice to have)

- [ ] App movil nativa (iOS + Android)
- [ ] Multi-sistema (integrar SIUGJ, Siglo XXI, TYBA, Publicaciones Procesales)
- [ ] Busqueda por cedula/nombre en toda la base de datos
- [ ] Vocabulario Controlado (API BuscarTerminos) -- glosario juridico integrado
- [ ] Biblioteca Digital -- acceso a documentos legales
- [ ] Sentencias TIC -- busqueda especializada
- [ ] Estadisticas avanzadas / reportes
- [ ] IA para clasificar actuaciones por urgencia
- [ ] Integracion con otros sistemas judiciales (Corte Constitucional, DIAN)

## P4 - Exploratorio (requiere investigacion adicional)

- [ ] Expediente Electronico completo (API CrearExpedienteIESAMAI + ObtenerDocumentosIEProceso)
- [ ] Descarga masiva de titulaciones (API DescargarZipTitulacionPagina)
- [ ] Integracion SIRNA (verificar abogado por tarjeta profesional)
- [ ] Integracion RNC (verificar cedula)
- [ ] Relatoria Antigua (providencias pre-dic 2021)
- [ ] Observatorio Ley 2080 (reportes especializados)

---

# FUENTES

- [SAMAI Main](https://samai.consejodeestado.gov.co/)
- [Mis Procesos](https://samai.consejodeestado.gov.co/Vistas/Casos/procesos.aspx)
- [Secretaria Online](https://samai.consejodeestado.gov.co/Vistas/servicios/WSecretariaOnLine.aspx)
- [Consulta de Estados](https://samai.consejodeestado.gov.co/Vistas/utiles/WEstados.aspx)
- [Ventanilla Virtual](https://ventanillavirtual.consejodeestado.gov.co/)
- [Servicios en Linea](https://www.consejodeestado.gov.co/servicios-en-linea/index.htm)
- [Mi Relatoria](https://samai.consejodeestado.gov.co/TitulacionRelatoria/BuscadorProvidenciasTituladas.aspx)
- [Notificaciones](https://www.consejodeestado.gov.co/notificaciones/index.htm)
- [Manual Sujetos Procesales](https://www.consejodeestado.gov.co/manuales/manualsujetos/knowledge-base/ventanilla-virtual/index.htm)
- [Manual Servidores Judiciales (PDF)](https://www.consejodeestado.gov.co/manuales/servidores/docs/manual-pdf/Manual-de-usuario-SAMAI-Servidores-judiciales.pdf)
- [Instructivo Consulta Procesos (PDF)](https://www.ramajudicial.gov.co/documents/2344051/0/INSTRUCTIVO+CONSULTA+DE+PROCESOS+POR+USUARIOS+-+SISTEMA+SAMAI+(1).pdf)
- [Premio SAMAI - CEJ](https://www.consejodeestado.gov.co/news/samai-el-sistema-de-gestion-del-consejo-de-estado-recibe-premio-a-mejor-practica-judicial-por-parte-de-la-corporacion-excelencia-en-la-justicia/)
- [Consulta de Jurisprudencia](https://www.consejodeestado.gov.co/buscador-de-jurisprudencia2/index.htm)
- [Registro de Usuario (Manual)](https://www.consejodeestado.gov.co/manuales/manualsujetos/knowledge-base/registro-de-usuario/index.htm)
- [Swagger API Spec (local)](../EstadosUpdates/swagger_spec.json) -- 79 endpoints, 92 schemas
- [Hallazgos de Investigacion](../EstadosUpdates/DOCS/HALLAZGOS_INVESTIGACION.md)
- [Analisis de Competidores](../EstadosUpdates/DOCS/ANALISIS_COMPETIDORES.md)
