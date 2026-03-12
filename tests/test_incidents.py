def test_list_incidents(client):
    response = client.get("/incidents")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Test incident"


def test_get_incident_by_id(client):
    response = client.get("/incidents/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_update_incident(client):
    response = client.put(
        "/incidents/1",
        headers={"X-API-Key": "change-me"},
        json={"status": "resolved", "severity": "low"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "resolved"
    assert response.json()["severity"] == "low"


def test_delete_incident(client):
    response = client.delete("/incidents/1", headers={"X-API-Key": "change-me"})

    assert response.status_code == 204
    follow_up = client.get("/incidents/1")
    assert follow_up.status_code == 404
