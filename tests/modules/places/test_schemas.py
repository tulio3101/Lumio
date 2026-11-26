import pytest
from pydantic import ValidationError

from app.modules.places.schemas import MAX_ROUTE_STEPS, RouteCreate, RouteStep
from tests.factories import route_payload


def test_valid_payload_is_accepted():
    route = RouteCreate.model_validate(route_payload())

    assert [step.order for step in route.steps] == [0, 1, 2]
    assert route.steps[2].latitude is None


def test_route_requires_at_least_one_step():
    with pytest.raises(ValidationError):
        RouteCreate.model_validate(route_payload(steps=[]))


def test_route_rejects_too_many_steps():
    steps = [
        {"order": i, "instruction": "Sigue recto", "distance_meters": 1.0}
        for i in range(MAX_ROUTE_STEPS + 1)
    ]
    with pytest.raises(ValidationError):
        RouteCreate.model_validate(route_payload(steps=steps))


@pytest.mark.parametrize("orders", [[1, 2, 3], [0, 2, 3], [0, 0, 1], [2, 1, 0]])
def test_step_order_must_be_consecutive_from_zero(orders):
    payload = route_payload()
    for step, order in zip(payload["steps"], orders, strict=True):
        step["order"] = order

    with pytest.raises(ValidationError, match="order consecutivo"):
        RouteCreate.model_validate(payload)


def test_step_coordinates_must_come_in_pairs():
    with pytest.raises(ValidationError, match="juntas"):
        RouteStep(order=0, instruction="Gira", distance_meters=5, latitude=4.6)


@pytest.mark.parametrize(
    "field, value",
    [
        ("distance_meters", 0),
        ("distance_meters", -1),
        ("expected_travel_time_seconds", -1),
    ],
)
def test_route_summary_must_be_positive(field, value):
    with pytest.raises(ValidationError):
        RouteCreate.model_validate(route_payload(**{field: value}))


@pytest.mark.parametrize(
    "place",
    [
        {"name": "", "latitude": 0, "longitude": 0},
        {"name": "X" * 201, "latitude": 0, "longitude": 0},
        {"name": "Polo", "latitude": 91, "longitude": 0},
        {"name": "Antimeridiano", "latitude": 0, "longitude": -181},
    ],
)
def test_destination_must_be_a_valid_place(place):
    with pytest.raises(ValidationError):
        RouteCreate.model_validate(route_payload(destination=place))


def test_empty_instruction_is_rejected():
    with pytest.raises(ValidationError):
        RouteStep(order=0, instruction="", distance_meters=1)


def test_nan_is_rejected():
    body = (
        '{"origin": {"name": "A", "latitude": NaN, "longitude": 0},'
        ' "destination": {"name": "B", "latitude": 1, "longitude": 1},'
        ' "steps": [{"order": 0, "instruction": "Sigue", "distance_meters": 1}],'
        ' "distance_meters": 1, "expected_travel_time_seconds": 1}'
    )
    with pytest.raises(ValidationError):
        RouteCreate.model_validate_json(body)
