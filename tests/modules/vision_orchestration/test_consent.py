"""SCRUM-324: sin consentimiento vigente el backend no procesa ninguna imagen."""

from datetime import UTC, datetime

import pytest

FRAME = {"frame_base64": "aGVsbG8=", "captured_at": datetime.now(UTC).isoformat()}


@pytest.mark.parametrize(
    "consent",
    [
        {"consent_given": False, "consent_version": "2026-11-1"},
        {"consent_given": True},
        {"consent_given": True, "consent_version": None},
    ],
)
def test_frame_without_consent_is_rejected(client, consent):
    response = client.post("/vision/analyze", json={**FRAME, **consent})

    assert response.status_code == 403
    assert response.json()["code"] == "consent_required"


def test_empty_consent_version_is_invalid(client):
    response = client.post(
        "/vision/analyze", json={**FRAME, "consent_given": True, "consent_version": ""}
    )

    assert response.status_code == 422


def test_frame_with_consent_reaches_the_service(client):
    response = client.post(
        "/vision/analyze", json={**FRAME, "consent_given": True, "consent_version": "2026-11-1"}
    )

    # La narración todavía no existe (SCRUM-38): pasa la comprobación y responde 501.
    assert response.status_code == 501


def test_contract_documents_consent_error(client):
    spec = client.get("/openapi.json").json()
    analyze = spec["paths"]["/vision/analyze"]["post"]

    assert "403" in analyze["responses"]
    assert "consent_version" in spec["components"]["schemas"]["FrameSubmission"]["properties"]
