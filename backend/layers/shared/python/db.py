"""Helpers CRUD para DynamoDB.

Responsabilidad única: leer y escribir en DynamoDB.
Cada función recibe la tabla como parámetro (inyección de dependencias).
"""
from __future__ import annotations

import logging
from typing import Any

from boto3.dynamodb.conditions import Key

from models import Radicado, Actuacion, Alerta, Etiqueta

logger = logging.getLogger(__name__)


# --- Radicados ---


def guardar_radicado(table: Any, radicado: Radicado) -> None:
    """Guarda o actualiza un radicado en DynamoDB."""
    table.put_item(Item=radicado.to_dynamo())


def obtener_radicados_usuario(table: Any, user_id: str) -> list[Radicado]:
    """Obtiene todos los radicados de un usuario."""
    resp = table.query(KeyConditionExpression=Key("userId").eq(user_id))
    return [Radicado.from_dynamo(item) for item in resp.get("Items", [])]


def obtener_radicado(table: Any, user_id: str, radicado: str) -> Radicado | None:
    """Obtiene un radicado específico de un usuario."""
    resp = table.get_item(Key={"userId": user_id, "radicado": radicado})
    item = resp.get("Item")
    if item is None:
        return None
    return Radicado.from_dynamo(item)


def eliminar_radicado(table: Any, user_id: str, radicado: str) -> bool:
    """Elimina un radicado. Retorna True si existía, False si no."""
    existing = obtener_radicado(table, user_id, radicado)
    if existing is None:
        return False
    table.delete_item(Key={"userId": user_id, "radicado": radicado})
    return True


def actualizar_corporacion(table: Any, user_id: str, radicado: str, corporacion: str) -> None:
    """Actualiza la corporacion de un radicado en DynamoDB."""
    table.update_item(
        Key={"userId": user_id, "radicado": radicado},
        UpdateExpression="SET corporacion = :c",
        ExpressionAttributeValues={":c": corporacion},
    )


def actualizar_alias(table: Any, user_id: str, radicado: str, alias: str) -> bool:
    """Actualiza el alias de un radicado. Retorna True si existia."""
    try:
        table.update_item(
            Key={"userId": user_id, "radicado": radicado},
            UpdateExpression="SET alias = :a",
            ExpressionAttributeValues={":a": alias},
            ConditionExpression="attribute_exists(userId)",
        )
        return True
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        return False


def toggle_activo(table: Any, user_id: str, radicado: str) -> bool | None:
    """Alterna el campo activo de un radicado. Retorna el nuevo valor, o None si no existe."""
    rad = obtener_radicado(table, user_id, radicado)
    if rad is None:
        return None
    new_val = not rad.activo
    table.update_item(
        Key={"userId": user_id, "radicado": radicado},
        UpdateExpression="SET activo = :a",
        ExpressionAttributeValues={":a": new_val},
    )
    return new_val


def obtener_radicados_unicos(table: Any) -> list[dict]:
    """Obtiene todos los radicados únicos (deduplicados) para el monitor.

    Escanea la tabla completa y deduplica por radicado.
    Retorna lista de dicts con las claves necesarias para cada fuente:
      - radicado, fuente, corporacion (samai), id_proceso (rama_judicial)
    """
    resp = table.scan(
        ProjectionExpression="corporacion, radicado, fuente, idProceso"
    )
    items = resp.get("Items", [])

    # Paginar si hay más
    while "LastEvaluatedKey" in resp:
        resp = table.scan(
            ProjectionExpression="corporacion, radicado, fuente, idProceso",
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        items.extend(resp.get("Items", []))

    seen: set[str] = set()
    unicos: list[dict] = []
    for item in items:
        rad = item["radicado"]
        if rad not in seen:
            seen.add(rad)
            unicos.append({
                "radicado": rad,
                "fuente": item.get("fuente", "samai"),
                "corporacion": item.get("corporacion", ""),
                "id_proceso": int(item["idProceso"]) if item.get("idProceso") else None,
            })

    return unicos


def actualizar_ultimo_orden(
    table: Any, user_id: str, radicado: str, orden: int, fecha_ultima: str = ""
) -> None:
    """Actualiza el último Orden conocido y la fecha de última actuación de un radicado."""
    if fecha_ultima:
        table.update_item(
            Key={"userId": user_id, "radicado": radicado},
            UpdateExpression="SET ultimoOrden = :o, fechaUltimaActuacion = :f",
            ExpressionAttributeValues={":o": orden, ":f": fecha_ultima},
        )
    else:
        table.update_item(
            Key={"userId": user_id, "radicado": radicado},
            UpdateExpression="SET ultimoOrden = :o",
            ExpressionAttributeValues={":o": orden},
        )


def limpiar_pending_init(table: Any, user_id: str, radicado: str) -> None:
    """Elimina el flag pendingInit de un radicado (inicialización completada)."""
    table.update_item(
        Key={"userId": user_id, "radicado": radicado},
        UpdateExpression="REMOVE pendingInit",
    )


# --- Actuaciones ---


def guardar_actuaciones(table: Any, actuaciones: list[Actuacion]) -> None:
    """Guarda múltiples actuaciones en batch."""
    with table.batch_writer() as batch:
        for act in actuaciones:
            batch.put_item(Item=act.to_dynamo())


def obtener_ultimo_orden_local(table: Any, radicado: str) -> int:
    """Obtiene el Orden más alto almacenado localmente para un radicado."""
    resp = table.query(
        KeyConditionExpression=Key("radicado").eq(radicado),
        ScanIndexForward=False,  # descendente por sort key (orden)
        Limit=1,
    )
    items = resp.get("Items", [])
    if not items:
        return 0
    return int(items[0]["orden"])


# --- Alertas ---


def eliminar_alertas_radicado(table: Any, user_id: str, radicado: str) -> int:
    """Elimina todas las alertas de un usuario para un radicado específico."""
    deleted = 0
    resp = table.query(
        KeyConditionExpression=Key("userId").eq(user_id),
        FilterExpression="radicado = :r",
        ExpressionAttributeValues={":r": radicado},
    )
    with table.batch_writer() as batch:
        for item in resp.get("Items", []):
            batch.delete_item(Key={"userId": item["userId"], "sk": item["sk"]})
            deleted += 1
    return deleted


def marcar_alerta_leida(table: Any, user_id: str, sk: str) -> bool:
    """Marca una alerta como leida con timestamp y TTL de 7 días."""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    ttl_epoch = int((now + timedelta(days=7)).timestamp())
    try:
        table.update_item(
            Key={"userId": user_id, "sk": sk},
            UpdateExpression="SET leido = :v, readAt = :r, #t = :ttl",
            ExpressionAttributeNames={"#t": "ttl"},
            ExpressionAttributeValues={
                ":v": True,
                ":r": now.isoformat(),
                ":ttl": ttl_epoch,
            },
            ConditionExpression="attribute_exists(userId)",
        )
        return True
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        return False


def marcar_todas_leidas(table: Any, user_id: str) -> int:
    """Marca todas las alertas no leidas de un usuario como leidas. Retorna cantidad."""
    from datetime import datetime, timezone, timedelta

    from boto3.dynamodb.conditions import Attr

    resp = table.query(
        KeyConditionExpression=Key("userId").eq(user_id),
        FilterExpression=Attr("leido").eq(False) | Attr("leido").not_exists(),
    )
    items = resp.get("Items", [])

    while "LastEvaluatedKey" in resp:
        resp = table.query(
            KeyConditionExpression=Key("userId").eq(user_id),
            FilterExpression=Attr("leido").eq(False) | Attr("leido").not_exists(),
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        items.extend(resp.get("Items", []))

    now = datetime.now(timezone.utc)
    ttl_epoch = int((now + timedelta(days=7)).timestamp())
    count = 0
    for item in items:
        table.update_item(
            Key={"userId": user_id, "sk": item["sk"]},
            UpdateExpression="SET leido = :v, readAt = :r, #t = :ttl",
            ExpressionAttributeNames={"#t": "ttl"},
            ExpressionAttributeValues={
                ":v": True,
                ":r": now.isoformat(),
                ":ttl": ttl_epoch,
            },
        )
        count += 1
    return count


def guardar_alerta(table: Any, alerta: Alerta) -> None:
    """Guarda una alerta."""
    table.put_item(Item=alerta.to_dynamo())


def obtener_alertas_usuario(
    table: Any, user_id: str, limit: int = 50
) -> list[Alerta]:
    """Obtiene alertas de un usuario, ordenadas por sk (más recientes primero)."""
    resp = table.query(
        KeyConditionExpression=Key("userId").eq(user_id),
        ScanIndexForward=False,
        Limit=limit,
    )
    return [Alerta.from_dynamo(item) for item in resp.get("Items", [])]


# --- Etiquetas ---


def guardar_etiqueta(table: Any, etiqueta: Etiqueta) -> None:
    """Guarda una etiqueta en DynamoDB."""
    table.put_item(Item=etiqueta.to_dynamo())


def obtener_etiquetas_usuario(table: Any, user_id: str) -> list[Etiqueta]:
    """Obtiene todas las etiquetas de un usuario."""
    resp = table.query(KeyConditionExpression=Key("userId").eq(user_id))
    return [Etiqueta.from_dynamo(item) for item in resp.get("Items", [])]


def obtener_etiqueta(table: Any, user_id: str, etiqueta_id: str) -> Etiqueta | None:
    """Obtiene una etiqueta específica de un usuario."""
    resp = table.get_item(Key={"userId": user_id, "etiquetaId": etiqueta_id})
    item = resp.get("Item")
    if item is None:
        return None
    return Etiqueta.from_dynamo(item)


def actualizar_etiqueta(
    table: Any, user_id: str, etiqueta_id: str, nombre: str, color: str
) -> bool:
    """Actualiza nombre y color de una etiqueta. Retorna True si existía."""
    try:
        table.update_item(
            Key={"userId": user_id, "etiquetaId": etiqueta_id},
            UpdateExpression="SET nombre = :n, color = :c",
            ExpressionAttributeValues={":n": nombre, ":c": color},
            ConditionExpression="attribute_exists(userId)",
        )
        return True
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        return False


def eliminar_etiqueta(table: Any, user_id: str, etiqueta_id: str) -> bool:
    """Elimina una etiqueta. Retorna True si existía."""
    existing = obtener_etiqueta(table, user_id, etiqueta_id)
    if existing is None:
        return False
    table.delete_item(Key={"userId": user_id, "etiquetaId": etiqueta_id})
    return True


def actualizar_etiquetas_radicado(
    table: Any, user_id: str, radicado: str, etiquetas: list[str]
) -> bool:
    """Actualiza las etiquetas asignadas a un radicado. Retorna True si existía."""
    try:
        if etiquetas:
            table.update_item(
                Key={"userId": user_id, "radicado": radicado},
                UpdateExpression="SET etiquetas = :e",
                ExpressionAttributeValues={":e": etiquetas},
                ConditionExpression="attribute_exists(userId)",
            )
        else:
            table.update_item(
                Key={"userId": user_id, "radicado": radicado},
                UpdateExpression="REMOVE etiquetas",
                ConditionExpression="attribute_exists(userId)",
            )
        return True
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        return False


def quitar_etiqueta_de_radicados(
    table: Any, user_id: str, etiqueta_id: str
) -> int:
    """Quita una etiqueta de todos los radicados del usuario. Retorna cantidad afectada."""
    radicados = obtener_radicados_usuario(table, user_id)
    count = 0
    for rad in radicados:
        if etiqueta_id in rad.etiquetas:
            nuevas = [e for e in rad.etiquetas if e != etiqueta_id]
            actualizar_etiquetas_radicado(table, user_id, rad.radicado, nuevas)
            count += 1
    return count
