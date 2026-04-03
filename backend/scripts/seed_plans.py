"""Seed billing plans en DynamoDB.

Ejecutar después del primer deploy para crear los planes en la tabla samai-billing-plans.

Uso:
    python backend/scripts/seed_plans.py
    python backend/scripts/seed_plans.py --delete  # eliminar todos los planes primero
"""
from __future__ import annotations

import argparse
import sys

import boto3

TABLE_NAME = "samai-billing-plans"

PLANS = [
    {
        "planId": "plan-gratuito",
        "name": "Gratuito",
        "amount": 0,
        "currency": "cop",
        "interval": "month",
        "intervalCount": 1,
        "trialDays": 0,
        "active": True,
        "features": {
            "max_processes": 5,
            "alertas_email": True,
            "historial": True,
            "etiquetas": True,
            "exportacion_csv": True,
            "busqueda_samai": True,
        },
    },
    {
        "planId": "plan-pro",
        "name": "Pro",
        "amount": 29900,
        "currency": "cop",
        "interval": "month",
        "intervalCount": 1,
        "trialDays": 7,
        "active": True,
        "features": {
            "max_processes": 30,
            "alertas_email": True,
            "alertas_push": True,
            "frecuencia_personalizable": True,
            "historial": True,
            "etiquetas": True,
            "exportacion_csv": True,
            "busqueda_samai": True,
        },
    },
    {
        "planId": "plan-firma",
        "name": "Firma",
        "amount": 79900,
        "currency": "cop",
        "interval": "month",
        "intervalCount": 1,
        "trialDays": 7,
        "active": True,
        "features": {
            "max_processes": 150,
            "max_users": 5,
            "alertas_email": True,
            "alertas_push": True,
            "alertas_whatsapp": False,  # futuro
            "frecuencia_personalizable": True,
            "reportes_avanzados": True,
            "soporte_prioritario": True,
            "historial": True,
            "etiquetas": True,
            "exportacion_csv": True,
            "busqueda_samai": True,
        },
    },
    {
        "planId": "plan-enterprise",
        "name": "Enterprise",
        "amount": 249900,
        "currency": "cop",
        "interval": "month",
        "intervalCount": 1,
        "trialDays": 14,
        "active": True,
        "features": {
            "max_processes": 1000,
            "max_users": 20,
            "alertas_email": True,
            "alertas_push": True,
            "alertas_whatsapp": True,
            "api_access": True,
            "integraciones": True,
            "account_manager": True,
            "frecuencia_personalizable": True,
            "reportes_avanzados": True,
            "soporte_prioritario": True,
            "historial": True,
            "etiquetas": True,
            "exportacion_csv": True,
            "busqueda_samai": True,
        },
    },
]


def seed(table_name: str, delete_first: bool = False) -> None:
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    if delete_first:
        print(f"Eliminando planes existentes de {table_name}...")
        resp = table.scan(ProjectionExpression="planId")
        for item in resp.get("Items", []):
            table.delete_item(Key={"planId": item["planId"]})
            print(f"  Eliminado: {item['planId']}")

    print(f"Creando {len(PLANS)} planes en {table_name}...")
    for plan in PLANS:
        table.put_item(Item=plan)
        print(f"  {plan['planId']}: {plan['name']} — COP ${plan['amount']:,}/mes — {plan['features']['max_processes']} procesos")

    print("Seed completado.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed billing plans")
    parser.add_argument("--delete", action="store_true", help="Delete existing plans first")
    parser.add_argument("--table", default=TABLE_NAME, help=f"Table name (default: {TABLE_NAME})")
    args = parser.parse_args()

    try:
        seed(args.table, delete_first=args.delete)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
