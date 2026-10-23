def test_openapi_exposes_module_contracts(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    spec = response.json()
    for path in (
        "/health",
        "/users",
        "/users/login",
        "/voice/commands",
        "/vision/analyze",
        "/narration",
        "/places/routes/active",
        "/places/routes/history",
    ):
        assert path in spec["paths"]
    for schema in ("UserCreate", "TokenPair", "ActiveRoute", "RouteHistoryPage"):
        assert schema in spec["components"]["schemas"]


def test_docs_are_served(client):
    assert client.get("/docs").status_code == 200


def test_stub_endpoints_return_501(client):
    assert client.get("/places/routes/active").status_code == 501
