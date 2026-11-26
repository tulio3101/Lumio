"""SCRUM-38: POST /vision/analyze describe la foto con el VLM y no guarda nada."""

import logging

from app.modules.narration.vlm import SceneDescriptionError, SceneDescriptionTimeout
from app.modules.vision_orchestration.image import MAX_IMAGE_BYTES

from .conftest import bearer, form, jpeg


def analyze(client, token, image=None, **fields):
    return client.post(
        "/vision/analyze",
        headers=bearer(token) if token else {},
        data=form(**fields),
        files={"image": ("frame.jpg", image if image is not None else jpeg(), "image/jpeg")},
    )


def test_describes_the_image(client, token, describer, limiter):
    response = analyze(client, token)

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "Delante hay un cruce peatonal con semáforo."
    assert body["model"] == "modelo-de-prueba"
    assert body["latency_ms"] >= 0
    # Nunca viene un nivel de alerta de la red (ADR-308).
    assert set(body) == {"text", "model", "latency_ms"}
    assert describer.calls == [{"bytes": len(jpeg()), "language": "es"}]


def test_description_is_normalized_before_returning(client, token, describer, limiter):
    describer.text = "**Delante** hay una puerta.  A tu derecha, escaleras. Al fondo, un letrero"

    response = analyze(client, token)

    assert response.json()["text"] == "Delante hay una puerta. A tu derecha, escaleras."


def test_requires_a_session(client, describer, limiter):
    response = analyze(client, None)

    assert response.status_code == 401
    assert describer.calls == []


def test_rejects_an_image_larger_than_1_mb(client, token, describer, limiter):
    response = analyze(client, token, image=jpeg(padding=MAX_IMAGE_BYTES))

    assert response.status_code == 413
    assert response.json()["code"] == "image_too_large"
    assert describer.calls == []


def test_rejects_a_long_side_over_1024_px(client, token, describer, limiter):
    response = analyze(client, token, image=jpeg(width=1440, height=1920))

    assert response.status_code == 413
    assert response.json()["code"] == "image_too_large"


def test_rejects_something_that_is_not_a_jpeg(client, token, describer, limiter):
    response = analyze(client, token, image=b"\x89PNG\r\n\x1a\n")

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_image"


def test_rejects_an_unknown_trigger(client, token, describer, limiter):
    assert analyze(client, token, trigger="cada-segundo").status_code == 422


def test_requires_captured_at(client, token, describer, limiter):
    assert analyze(client, token, captured_at=None).status_code == 422


def test_vlm_failure_is_503_and_does_not_leak_details(client, token, describer, limiter):
    describer.error = SceneDescriptionError("ThrottlingException")

    response = analyze(client, token)

    assert response.status_code == 503
    assert response.json() == {
        "detail": "La narración del entorno no está disponible en este momento.",
        "code": "narration_unavailable",
    }


def test_vlm_timeout_is_504(client, token, describer, limiter):
    describer.error = SceneDescriptionTimeout("ReadTimeoutError")

    response = analyze(client, token)

    assert response.status_code == 504
    assert response.json()["code"] == "narration_timeout"


def test_empty_description_counts_as_unavailable(client, token, describer, limiter):
    describer.text = "  **  "

    response = analyze(client, token)

    assert response.status_code == 503
    assert response.json()["code"] == "narration_unavailable"


def test_rate_limit_per_user(client, token, describer, limiter):
    limiter._min_interval = 3.0

    first = analyze(client, token)
    second = analyze(client, token)

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["code"] == "narration_rate_limited"
    assert len(describer.calls) == 1


def test_auto_requests_are_throttled_but_the_button_still_works(client, token, describer, limiter):
    limiter._auto_min_interval = 10.0

    first = analyze(client, token, trigger="auto")
    second = analyze(client, token, trigger="auto")
    button = analyze(client, token, trigger="gesture")

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["code"] == "narration_rate_limited"
    # Una automática rechazada no llega al VLM ni gasta cupo del botón.
    assert button.status_code == 200
    assert len(describer.calls) == 2


def test_logs_only_metadata(client, token, describer, limiter, caplog):
    describer.text = "Hay un letrero que dice Farmacia Central."

    with caplog.at_level(logging.DEBUG):
        analyze(client, token)

    logged = caplog.text
    assert "Farmacia Central" not in logged
    assert "Narración servida" in logged


def test_contract_documents_errors(client):
    spec = client.get("/openapi.json").json()
    analyze_op = spec["paths"]["/vision/analyze"]["post"]

    assert {"200", "401", "403", "413", "422", "429", "503", "504"} <= analyze_op[
        "responses"
    ].keys()
    assert {"HTTPBearer": []} in analyze_op["security"]
    assert "multipart/form-data" in analyze_op["requestBody"]["content"]
    response = spec["components"]["schemas"]["VisionAnalysisResponse"]["properties"]
    assert set(response) == {"text", "model", "latency_ms"}
    assert "/narration" not in spec["paths"]
