"""Modelos de datos del sistema Alertas Judiciales by Dertyos."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Actuacion:
    """Una actuación procesal devuelta por la API SAMAI."""

    radicado: str  # sin guiones, 23 dígitos
    orden: int  # incremental, clave para detectar novedades
    nombre: str  # NombreActuacion
    fecha: str  # fecha de la actuación (ISO date string)
    anotacion: str  # detalle/nota
    registro: str  # timestamp de registro en SAMAI
    codigo: str = ""  # CodiActuacion
    estado: str = ""  # Estado (REGISTRADA, etc.)
    decision: str | None = None  # DescripcionDecision
    doc_hash: str | None = None  # Hash para descargar providencia

    @classmethod
    def from_api(cls, data: dict) -> Actuacion:
        """Crea Actuacion desde respuesta JSON de la API SAMAI."""
        # Extraer hash del primer documento en SIERJU (si existe)
        sierju = data.get("SIERJU") or []
        doc_hash = sierju[0].get("HashDocumento") if sierju else None

        return cls(
            radicado=data["A110LLAVPROC"],
            orden=int(data["Orden"]),
            nombre=data.get("NombreActuacion", ""),
            fecha=data.get("Actuacion", ""),
            anotacion=data.get("Anotacion", ""),
            registro=data.get("Registro", ""),
            codigo=data.get("CodiActuacion", ""),
            estado=data.get("Estado", ""),
            decision=data.get("DescripcionDecision"),
            doc_hash=doc_hash,
        )

    @classmethod
    def from_rama_judicial_api(cls, data: dict) -> Actuacion:
        """Crea Actuacion desde respuesta JSON de la API CPNU (Rama Judicial).

        Mapeo de campos:
          consActuacion → orden
          actuacion     → nombre
          fechaActuacion → fecha
          anotacion     → anotacion
          fechaRegistro  → registro
          codRegla       → codigo
        """
        return cls(
            radicado=data.get("llaveProceso", ""),
            orden=int(data["consActuacion"]),
            nombre=(data.get("actuacion") or "").strip(),
            fecha=data.get("fechaActuacion") or "",
            anotacion=data.get("anotacion") or "",
            registro=data.get("fechaRegistro") or "",
            codigo=(data.get("codRegla") or "").strip(),
            estado="",
            decision=None,
            doc_hash=None,
        )

    @classmethod
    def from_siugj_api(cls, data: dict, radicado: str = "") -> Actuacion:
        """Crea Actuacion desde respuesta JSON de SIUGJ.

        Mapeo de campos:
          idRegistro    → orden  (clave de diff, int incremental)
          actuacion     → nombre
          fechaActuacion → fecha
          anotacion     → anotacion
          fechaInicia   → registro
        """
        return cls(
            radicado=radicado,
            orden=int(data["idRegistro"]),
            nombre=(data.get("actuacion") or "").strip(),
            fecha=data.get("fechaActuacion") or "",
            anotacion=data.get("anotacion") or "",
            registro=data.get("fechaInicia") or "",
            codigo="",
            estado="",
            decision=None,
            doc_hash=None,
        )

    def to_dynamo(self) -> dict:
        """Convierte a dict para DynamoDB."""
        item = {
            "radicado": self.radicado,
            "orden": self.orden,
            "nombre": self.nombre,
            "fecha": self.fecha,
            "anotacion": self.anotacion,
            "registro": self.registro,
            "codigo": self.codigo,
            "estado": self.estado,
        }
        if self.decision:
            item["decision"] = self.decision
        if self.doc_hash:
            item["docHash"] = self.doc_hash
        return item


@dataclass
class Radicado:
    """Un radicado monitoreado por un usuario."""

    user_id: str
    radicado: str  # sin guiones, 23 dígitos
    corporacion: str  # código de 7 dígitos (solo relevante para fuente="samai")
    radicado_formato: str  # con guiones
    alias: str = ""  # nombre descriptivo dado por el usuario
    ultimo_orden: int = 0  # último Orden/consActuacion conocido
    activo: bool = True
    created_at: str = ""  # ISO datetime
    fuente: str = "samai"  # "samai" | "rama_judicial"
    id_proceso: int | None = None  # idProceso del CPNU (solo para fuente="rama_judicial")
    pending_init: bool = False  # True cuando max_orden no se pudo determinar al registrar
    fecha_ultima_actuacion: str = ""  # fecha ISO de la última actuación conocida
    # Metadata enriquecida para filtros
    despacho: str = ""  # nombre del juzgado/tribunal
    ciudad: str = ""  # ciudad (normalizada)
    especialidad: str = ""  # especialidad judicial (ej: "Contencioso Administrativo")
    instancia: str = ""  # instancia (ej: "PRIMERA INSTANCIA")
    vigente: str = ""  # SI/NO — si el caso está activo en el sistema judicial
    fecha_inicio_proceso: str = ""  # fecha ISO de creación del caso en el juzgado

    def to_dynamo(self) -> dict:
        """Convierte a dict para DynamoDB."""
        item: dict = {
            "userId": self.user_id,
            "radicado": self.radicado,
            "radicadoFormato": self.radicado_formato,
            "alias": self.alias,
            "ultimoOrden": self.ultimo_orden,
            "activo": self.activo,
            "createdAt": self.created_at,
            "fuente": self.fuente,
        }
        # Only store corporacion if non-empty (it's a GSI key; empty strings not allowed)
        if self.corporacion:
            item["corporacion"] = self.corporacion
        if self.id_proceso is not None:
            item["idProceso"] = self.id_proceso
        if self.pending_init:
            item["pendingInit"] = True
        if self.fecha_ultima_actuacion:
            item["fechaUltimaActuacion"] = self.fecha_ultima_actuacion
        if self.despacho:
            item["despacho"] = self.despacho
        if self.ciudad:
            item["ciudad"] = self.ciudad
        if self.especialidad:
            item["especialidad"] = self.especialidad
        if self.instancia:
            item["instancia"] = self.instancia
        if self.vigente:
            item["vigente"] = self.vigente
        if self.fecha_inicio_proceso:
            item["fechaInicioProceso"] = self.fecha_inicio_proceso
        return item

    @classmethod
    def from_dynamo(cls, item: dict) -> Radicado:
        """Crea Radicado desde item DynamoDB."""
        id_proceso_raw = item.get("idProceso")
        return cls(
            user_id=item["userId"],
            radicado=item["radicado"],
            corporacion=item.get("corporacion", ""),
            radicado_formato=item.get("radicadoFormato", ""),
            alias=item.get("alias", ""),
            ultimo_orden=int(item.get("ultimoOrden", 0)),
            activo=item.get("activo", True),
            created_at=item.get("createdAt", ""),
            fuente=item.get("fuente", "samai"),
            id_proceso=int(id_proceso_raw) if id_proceso_raw is not None else None,
            pending_init=item.get("pendingInit", False),
            fecha_ultima_actuacion=item.get("fechaUltimaActuacion", ""),
            despacho=item.get("despacho", ""),
            ciudad=item.get("ciudad", ""),
            especialidad=item.get("especialidad", ""),
            instancia=item.get("instancia", ""),
            vigente=item.get("vigente", ""),
            fecha_inicio_proceso=item.get("fechaInicioProceso", ""),
        )


@dataclass
class Alerta:
    """Una alerta generada cuando se detecta una actuación nueva."""

    user_id: str
    radicado: str
    orden: int
    nombre_actuacion: str
    fecha_actuacion: str
    anotacion: str
    created_at: str = ""
    enviado: bool = False
    leido: bool = False
    read_at: str = ""  # ISO datetime cuando se marcó como leída
    fuente: str = "samai"  # "samai" | "rama_judicial"

    @property
    def sk(self) -> str:
        """Sort key para DynamoDB: timestamp#radicado#orden."""
        return f"{self.created_at}#{self.radicado}#{self.orden}"

    def to_dynamo(self) -> dict:
        """Convierte a dict para DynamoDB."""
        item: dict = {
            "userId": self.user_id,
            "sk": self.sk,
            "radicado": self.radicado,
            "orden": self.orden,
            "nombreActuacion": self.nombre_actuacion,
            "fechaActuacion": self.fecha_actuacion,
            "anotacion": self.anotacion,
            "createdAt": self.created_at,
            "enviado": self.enviado,
            "leido": self.leido,
            "fuente": self.fuente,
        }
        if self.read_at:
            item["readAt"] = self.read_at
        return item

    @classmethod
    def from_dynamo(cls, item: dict) -> Alerta:
        """Crea Alerta desde item DynamoDB."""
        return cls(
            user_id=item["userId"],
            radicado=item["radicado"],
            orden=int(item.get("orden", 0)),
            nombre_actuacion=item.get("nombreActuacion", ""),
            fecha_actuacion=item.get("fechaActuacion", ""),
            anotacion=item.get("anotacion", ""),
            created_at=item.get("createdAt", ""),
            enviado=item.get("enviado", False),
            leido=item.get("leido", False),
            read_at=item.get("readAt", ""),
            fuente=item.get("fuente", "samai"),
        )
