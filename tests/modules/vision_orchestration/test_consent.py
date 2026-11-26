"""SCRUM-324: sin consentimiento vigente el backend no procesa ninguna imagen."""

import pytest

from .conftest import bearer, form, jpeg


@pytest.mark.parametrize("consent_version", [None, "", "   "])
def test_frame_without_consent_is_rejected(client, token, describer, limiter, consent_version):
    response = client.post(
        "/vision/analyze",
        headers=bearer(token),
        data=form(consent_version=consent_version),
        files={"image": ("frame.jpg", jpeg(), "image/jpeg")},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "consent_required"
    # Sin consentimiento la foto ni siquiera llega al VLM.
    assert describer.calls == []


def test_consent_is_checked_before_the_image(client, token, describer, limiter):
    response = client.post(
        "/vision/analyze",
        headers=bearer(token),
        data=form(consent_version=None),
        files={"image": ("frame.jpg", b"no es un jpeg", "image/jpeg")},
    )

    assert response.status_code == 403


def test_frame_with_consent_reaches_the_service(client, token, describer, limiter):
    response = client.post(
        "/vision/analyze",
        headers=bearer(token),
        data=form(),
        files={"image": ("frame.jpg", jpeg(), "image/jpeg")},
    )

    assert response.status_code == 200
    assert len(describer.calls) == 1


def test_contract_documents_consent_error(client):
    spec = client.get("/openapi.json").json()
    analyze = spec["paths"]["/vision/analyze"]["post"]

    assert "403" in analyze["responses"]
    body = analyze["requestBody"]["content"]["multipart/form-data"]["schema"]["$ref"]
    schema = spec["components"]["schemas"][body.rsplit("/", 1)[-1]]
    assert "consent_version" in schema["properties"]
