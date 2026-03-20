from __future__ import annotations

import os
import json
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

# Force moto to use us-east-1
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def samai_actuaciones_response() -> list[dict]:
    """Real SAMAI API response for HistorialActuaciones."""
    path = FIXTURES_DIR / "samai_actuaciones.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def samai_proceso_response() -> dict:
    """Real SAMAI API response for ObtenerDatosProcesoGet."""
    path = FIXTURES_DIR / "samai_proceso.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


@pytest.fixture
def estados_extraidos() -> list[dict]:
    """Extracted estados from scraping (reference data)."""
    path = FIXTURES_DIR / "estados_extraidos.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def aws_credentials():
    """Mocked AWS credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def dynamodb_resource(aws_credentials):
    """Mocked DynamoDB resource with tables created."""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        # Radicados table
        dynamodb.create_table(
            TableName="samai-radicados",
            KeySchema=[
                {"AttributeName": "userId", "KeyType": "HASH"},
                {"AttributeName": "radicado", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "userId", "AttributeType": "S"},
                {"AttributeName": "radicado", "AttributeType": "S"},
                {"AttributeName": "corporacion", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "radicado-index",
                    "KeySchema": [
                        {"AttributeName": "radicado", "KeyType": "HASH"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "corporacion-index",
                    "KeySchema": [
                        {"AttributeName": "corporacion", "KeyType": "HASH"},
                        {"AttributeName": "radicado", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Actuaciones table
        dynamodb.create_table(
            TableName="samai-actuaciones",
            KeySchema=[
                {"AttributeName": "radicado", "KeyType": "HASH"},
                {"AttributeName": "orden", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "radicado", "AttributeType": "S"},
                {"AttributeName": "orden", "AttributeType": "N"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Alertas table
        dynamodb.create_table(
            TableName="samai-alertas",
            KeySchema=[
                {"AttributeName": "userId", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "userId", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        yield dynamodb


@pytest.fixture
def radicados_table(dynamodb_resource):
    """Mocked Radicados DynamoDB table."""
    return dynamodb_resource.Table("samai-radicados")


@pytest.fixture
def actuaciones_table(dynamodb_resource):
    """Mocked Actuaciones DynamoDB table."""
    return dynamodb_resource.Table("samai-actuaciones")


@pytest.fixture
def alertas_table(dynamodb_resource):
    """Mocked Alertas DynamoDB table."""
    return dynamodb_resource.Table("samai-alertas")
