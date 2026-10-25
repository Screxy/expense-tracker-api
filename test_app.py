from datetime import date

import pytest
from fastapi.testclient import TestClient

import app_final
from app_final import app


@pytest.fixture(autouse=True)
def clean_storage():
    app_final.expenses.clear()
    app_final.next_id = 1
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_version(client):
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json()["version"] == app_final.APP_VERSION


def test_create_and_list_expenses(client):
    response = client.post("/expenses", json={"amount": 350.5, "category": "Food", "description": "Lunch"})
    assert response.status_code == 201
    created = response.json()
    assert created["id"] == 1
    assert created["category"] == "food"

    response = client.get("/expenses")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_expense_by_id(client):
    client.post("/expenses", json={"amount": 100, "category": "transport"})
    response = client.get("/expenses/1")
    assert response.status_code == 200
    assert response.json()["amount"] == 100


def test_get_missing_expense_returns_404(client):
    response = client.get("/expenses/999")
    assert response.status_code == 404


def test_unknown_category_is_rejected(client):
    response = client.post("/expenses", json={"amount": 10, "category": "casino"})
    assert response.status_code == 422
    assert "Unknown category" in response.json()["detail"]


def test_negative_amount_is_rejected(client):
    response = client.post("/expenses", json={"amount": -5, "category": "food"})
    assert response.status_code == 422


def test_filter_by_category(client):
    client.post("/expenses", json={"amount": 100, "category": "food"})
    client.post("/expenses", json={"amount": 200, "category": "transport"})
    response = client.get("/expenses", params={"category": "transport"})
    items = response.json()
    assert len(items) == 1
    assert items[0]["category"] == "transport"


def test_delete_expense(client):
    client.post("/expenses", json={"amount": 100, "category": "food"})
    assert client.delete("/expenses/1").status_code == 204
    assert client.get("/expenses/1").status_code == 404


def test_summary_and_budget(client, monkeypatch):
    monkeypatch.setattr(app_final, "MONTHLY_BUDGET", 1000.0)
    today = date.today().isoformat()
    client.post("/expenses", json={"amount": 700, "category": "food", "spent_on": today})
    client.post("/expenses", json={"amount": 500, "category": "health", "spent_on": today})
    client.post("/expenses", json={"amount": 300, "category": "food", "spent_on": "2020-01-15"})

    data = client.get("/summary").json()
    assert data["total"] == 1200
    assert data["by_category"] == {"food": 700, "health": 500}
    assert data["remaining"] == -200
    assert data["over_budget"] is True


def test_summary_rejects_bad_month_format(client):
    response = client.get("/summary", params={"month": "January"})
    assert response.status_code == 422
