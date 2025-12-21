"""Tests for broker API endpoints"""

from fastapi.testclient import TestClient

from app.models.data_broker import DataBroker


def test_list_brokers_unauthorized(client: TestClient):
    """Test that listing brokers requires authentication"""
    response = client.get("/brokers/")
    assert response.status_code == 401


def test_list_brokers_empty(client: TestClient, auth_headers: dict):
    """Test listing brokers when none exist"""
    response = client.get("/brokers/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_list_brokers_with_data(client: TestClient, auth_headers: dict, test_broker: DataBroker):
    """Test listing brokers returns existing brokers"""
    response = client.get("/brokers/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Broker"
    assert "testbroker.com" in data[0]["domains"]


def test_get_broker_by_id(client: TestClient, auth_headers: dict, test_broker: DataBroker):
    """Test getting a specific broker by ID"""
    response = client.get(f"/brokers/{test_broker.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Broker"
    assert data["privacy_email"] == "privacy@testbroker.com"


def test_get_broker_not_found(client: TestClient, auth_headers: dict):
    """Test getting a non-existent broker returns 404"""
    response = client.get("/brokers/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert response.status_code == 404


def test_create_broker_requires_admin(client: TestClient, auth_headers: dict):
    """Test that creating a broker requires admin privileges"""
    broker_data = {
        "name": "New Broker",
        "domains": ["newbroker.com"],
        "privacy_email": "privacy@newbroker.com",
    }
    response = client.post("/brokers/", json=broker_data, headers=auth_headers)
    assert response.status_code == 403


def test_create_broker_as_admin(client: TestClient, admin_auth_headers: dict):
    """Test creating a broker as admin"""
    broker_data = {
        "name": "New Broker",
        "domains": ["newbroker.com"],
        "privacy_email": "privacy@newbroker.com",
        "opt_out_url": "https://newbroker.com/opt-out",
        "category": "data_aggregator",
    }
    response = client.post("/brokers/", json=broker_data, headers=admin_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Broker"
    assert "newbroker.com" in data["domains"]


def test_create_broker_duplicate_name(
    client: TestClient, admin_auth_headers: dict, test_broker: DataBroker
):
    """Test creating a broker with duplicate name fails"""
    broker_data = {
        "name": "Test Broker",  # Same as test_broker
        "domains": ["different.com"],
    }
    response = client.post("/brokers/", json=broker_data, headers=admin_auth_headers)
    assert response.status_code == 400


def test_create_broker_invalid_data(client: TestClient, admin_auth_headers: dict):
    """Test creating a broker with invalid data fails"""
    # Missing required field 'domains'
    broker_data = {"name": "Incomplete Broker"}
    response = client.post("/brokers/", json=broker_data, headers=admin_auth_headers)
    assert response.status_code == 422
