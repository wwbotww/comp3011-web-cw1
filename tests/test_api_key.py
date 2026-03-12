def test_write_requires_api_key(client):
    response = client.post(
        "/incidents",
        json={
            "title": "Blocked lane",
            "description": "Temporary blockage",
            "incident_type": "delay",
            "severity": "high",
            "status": "open",
            "route_id": 1,
            "stop_id": 1,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key."


def test_write_accepts_valid_api_key(client):
    response = client.post(
        "/incidents",
        headers={"X-API-Key": "change-me"},
        json={
            "title": "Blocked lane",
            "description": "Temporary blockage",
            "incident_type": "delay",
            "severity": "high",
            "status": "open",
            "route_id": 1,
            "stop_id": 1,
        },
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Blocked lane"
