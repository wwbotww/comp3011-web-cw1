def test_route_reliability_summary(client):
    response = client.get("/analytics/routes/1/reliability")

    assert response.status_code == 200
    body = response.json()
    assert body["route_id"] == 1
    assert body["avg_delay_minutes"] == 4.0
    assert body["on_time_rate"] == 0.8
    assert body["observation_count"] == 20


def test_route_reliability_for_missing_route(client):
    response = client.get("/analytics/routes/999/reliability")

    assert response.status_code == 404
