import pytest

from app.main import app
from app.modules.sos.email import EmailDeliveryError, get_email_sender

CREDENTIALS = {"email": "ana@example.com", "password": "clave-segura-1"}


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class FakeEmailSender:
    """Guarda lo «enviado». `fail_for` son los destinatarios cuyo envío falla."""

    def __init__(self) -> None:
        self.sent: list[dict] = []
        self.fail_for: set[str] = set()
        self.fail_all = False

    def send(self, *, to: str, subject: str, body: str) -> None:
        if self.fail_all or to in self.fail_for:
            raise EmailDeliveryError("rechazado")
        self.sent.append({"to": to, "subject": subject, "body": body})

    @property
    def recipients(self) -> list[str]:
        return [mail["to"] for mail in self.sent]


@pytest.fixture
def mail(client) -> FakeEmailSender:
    sender = FakeEmailSender()
    app.dependency_overrides[get_email_sender] = lambda: sender
    return sender


@pytest.fixture
def token(client) -> str:
    client.post("/users", json=CREDENTIALS)
    return client.post("/users/login", json=CREDENTIALS).json()["access_token"]
