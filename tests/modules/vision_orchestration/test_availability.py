"""SCRUM-41: GET /vision/status dice si la narración está disponible, sin llamar al VLM."""

import pytest

from app.main import app
from app.modules.narration.availability import NarrationAvailability, get_narration_availability
from app.modules.narration.rate_limit import NarrationRateLimiter, get_rate_limiter
from app.modules.narration.vlm import (
    SceneDescriptionError,
    SceneDescriptionTimeout,
    UnconfiguredSceneDescriber,
    get_scene_describer,
)

from .conftest import bearer, form, jpeg


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def availability(client, clock) -> NarrationAvailability:
    instance = NarrationAvailability(failure_threshold=3, cooldown_seconds=30, clock=clock)
    app.dependency_overrides[get_narration_availability] = lambda: instance
    return instance


def analyze(client, token):
    return client.post(
        "/vision/analyze",
        headers=bearer(token),
        data=form(),
        files={"image": ("frame.jpg", jpeg(), "image/jpeg")},
    )


def status(client):
    return client.get("/vision/status")


def test_available_without_session_and_without_calling_the_vlm(client, describer, availability):
    response = status(client)

    assert response.status_code == 200
    assert response.json() == {
        "available": True,
        "reason": "available",
        "retry_after_seconds": None,
    }
    assert describer.calls == []


def test_not_configured_when_the_vlm_is_off(client, availability):
    app.dependency_overrides[get_scene_describer] = lambda: UnconfiguredSceneDescriber()

    body = status(client).json()

    assert body["available"] is False
    assert body["reason"] == "not_configured"


def test_degraded_after_three_consecutive_failures(client, token, describer, limiter, availability):
    describer.error = SceneDescriptionError("ThrottlingException")
    for _ in range(2):
        assert analyze(client, token).status_code == 503
    assert status(client).json()["available"] is True

    assert analyze(client, token).status_code == 503

    body = status(client).json()
    assert body == {"available": False, "reason": "degraded", "retry_after_seconds": 30}


def test_timeouts_and_empty_answers_count_as_failures(
    client, token, describer, limiter, availability
):
    describer.error = SceneDescriptionTimeout("ReadTimeoutError")
    assert analyze(client, token).status_code == 504
    assert analyze(client, token).status_code == 504
    describer.error = None
    describer.text = "   "
    assert analyze(client, token).status_code == 503

    assert status(client).json()["reason"] == "degraded"


def test_a_success_resets_the_count(client, token, describer, limiter, availability):
    describer.error = SceneDescriptionError("ServiceUnavailable")
    analyze(client, token)
    analyze(client, token)
    describer.error = None
    assert analyze(client, token).status_code == 200
    describer.error = SceneDescriptionError("ServiceUnavailable")
    analyze(client, token)

    assert status(client).json()["available"] is True


def test_available_again_after_the_cooldown(client, token, describer, limiter, availability, clock):
    describer.error = SceneDescriptionError("ThrottlingException")
    for _ in range(3):
        analyze(client, token)

    clock.now += 20
    assert status(client).json()["retry_after_seconds"] == 10

    clock.now += 10
    assert status(client).json() == {
        "available": True,
        "reason": "available",
        "retry_after_seconds": None,
    }


def test_rate_limited_requests_do_not_count(client, token, describer, availability):
    strict = NarrationRateLimiter(min_interval_seconds=3600, daily_limit=1000)
    app.dependency_overrides[get_rate_limiter] = lambda: strict
    describer.error = SceneDescriptionError("ThrottlingException")
    analyze(client, token)
    for _ in range(3):
        assert analyze(client, token).status_code == 429

    assert status(client).json()["available"] is True


def test_monitor_unit_snapshot_is_never_below_one_second(clock):
    monitor = NarrationAvailability(failure_threshold=1, cooldown_seconds=30, clock=clock)
    monitor.record_failure()

    clock.now += 29.9

    snapshot = monitor.snapshot()
    assert snapshot.degraded is True
    assert snapshot.retry_after_seconds == 1
