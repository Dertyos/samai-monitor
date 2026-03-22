"""Modelos de datos del sistema SAMAI Monitor."""
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
    corporacion: str  # código de 7 dígitos
    radicado_formato: str  # con guiones
    alias: str = ""  # nombre descriptivo dado por el usuario
    ultimo_orden: int = 0  # último Orden conocido
    activo: bool = True
    created_at: str = ""  # ISO datetime

    def to_dynamo(self) -> dict:
        """Convierte a dict para DynamoDB."""
        return {
            "userId": self.user_id,
            "radicado": self.radicado,
            "corporacion": self.corporacion,
            "radicadoFormato": self.radicado_formato,
            "alias": self.alias,
            "ultimoOrden": self.ultimo_orden,
            "activo": self.activo,
            "createdAt": self.created_at,
        }

    @classmethod
    def from_dynamo(cls, item: dict) -> Radicado:
        """Crea Radicado desde item DynamoDB."""
        return cls(
            user_id=item["userId"],
            radicado=item["radicado"],
            corporacion=item["corporacion"],
            radicado_formato=item.get("radicadoFormato", ""),
            alias=item.get("alias", ""),
            ultimo_orden=int(item.get("ultimoOrden", 0)),
            activo=item.get("activo", True),
            created_at=item.get("createdAt", ""),
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
        )
