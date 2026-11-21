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


def test_delete_account_contract_documents_errors(client):
    spec = client.get("/openapi.json").json()
    delete = spec["paths"]["/users/me"]["delete"]

    assert {"204", "401", "500", "503"} <= delete["responses"].keys()
    assert {"HTTPBearer": []} in delete["security"]


def test_profile_contracts_document_errors(client):
    spec = client.get("/openapi.json").json()
    patch = spec["paths"]["/users/me"]["patch"]
    password = spec["paths"]["/users/me/password"]["put"]

    assert {"200", "401", "422", "500", "503"} <= patch["responses"].keys()
    assert {"204", "401", "403", "409", "422", "500", "503"} <= password["responses"].keys()
    assert {"display_name", "phone"} <= spec["components"]["schemas"]["UserRead"][
        "properties"
    ].keys()
    assert "UserProfileUpdate" in spec["components"]["schemas"]


def test_docs_are_served(client):
    assert client.get("/docs").status_code == 200


def test_stub_endpoints_return_501(client):
    assert client.delete("/places/routes/active").status_code == 501


def test_active_route_contract_documents_errors(client):
    spec = client.get("/openapi.json").json()
    put = spec["paths"]["/places/routes/active"]["put"]

    assert {"401", "409", "422", "503"} <= put["responses"].keys()
    assert {"HTTPBearer": []} in put["security"]
    assert "ErrorResponse" in spec["components"]["schemas"]
