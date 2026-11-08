from typing import Any


def route_payload(**overrides: Any) -> dict[str, Any]:
    """Cuerpo válido de PUT /places/routes/active, como lo envía el cliente iOS."""
    payload: dict[str, Any] = {
        "origin": {"name": "Ubicación actual", "latitude": 4.6097, "longitude": -74.0817},
        "destination": {"name": "Farmacia Central", "latitude": 4.6110, "longitude": -74.0790},
        "steps": [
            {
                "order": 0,
                "instruction": "Camina hacia el norte por la Carrera 7",
                "distance_meters": 120.0,
                "latitude": 4.6097,
                "longitude": -74.0817,
            },
            {
                "order": 1,
                "instruction": "Gira a la derecha en la Calle 19",
                "distance_meters": 200.0,
                "latitude": 4.6108,
                "longitude": -74.0815,
            },
            {
                "order": 2,
                "instruction": "El destino está a tu izquierda",
                "distance_meters": 0.0,
            },
        ],
        "distance_meters": 320.0,
        "expected_travel_time_seconds": 260.0,
    }
    payload.update(overrides)
    return payload
