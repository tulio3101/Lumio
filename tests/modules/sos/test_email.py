import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

from app.core.config import Settings
from app.modules.sos import email
from app.modules.sos.email import (
    EmailDeliveryError,
    LogEmailSender,
    SesEmailSender,
    UnconfiguredEmailSender,
    get_email_sender,
)


class FakeSesClient:
    def __init__(self, error: Exception | None = None) -> None:
        self.calls: list[dict] = []
        self.error = error

    def send_email(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return {"MessageId": "abc"}


def ses_sender(client: FakeSesClient) -> SesEmailSender:
    sender = SesEmailSender("no-reply@lumio.test", "us-east-1")
    sender._client = client
    return sender


def test_ses_sends_a_plain_text_email_from_the_configured_sender():
    client = FakeSesClient()

    ses_sender(client).send(to="maria@example.com", subject="Asunto ñ", body="Cuerpo")

    call = client.calls[0]
    assert call["FromEmailAddress"] == "no-reply@lumio.test"
    assert call["Destination"] == {"ToAddresses": ["maria@example.com"]}
    simple = call["Content"]["Simple"]
    assert simple["Subject"] == {"Data": "Asunto ñ", "Charset": "UTF-8"}
    assert simple["Body"] == {"Text": {"Data": "Cuerpo", "Charset": "UTF-8"}}


@pytest.mark.parametrize(
    "error",
    [
        ClientError(
            {"Error": {"Code": "MessageRejected", "Message": "no verificado"}}, "SendEmail"
        ),
        EndpointConnectionError(endpoint_url="https://email.us-east-1.amazonaws.com"),
    ],
)
def test_ses_errors_become_delivery_errors(error):
    with pytest.raises(EmailDeliveryError):
        ses_sender(FakeSesClient(error)).send(to="a@b.co", subject="s", body="b")


def test_the_log_sender_does_not_raise(caplog):
    with caplog.at_level("INFO"):
        LogEmailSender().send(to="a@b.co", subject="Asunto", body="Cuerpo")

    assert "Asunto" in caplog.text


def test_the_unconfigured_sender_fails_loudly():
    with pytest.raises(EmailDeliveryError):
        UnconfiguredEmailSender().send(to="a@b.co", subject="s", body="b")


@pytest.mark.parametrize(
    ("settings", "expected"),
    [
        ({"environment": "local"}, LogEmailSender),
        ({"environment": "dev"}, UnconfiguredEmailSender),
        ({"environment": "prod", "jwt_secret": "x" * 40}, UnconfiguredEmailSender),
        (
            {
                "environment": "dev",
                "jwt_secret": "x" * 40,
                "email_backend": "ses",
                "ses_sender_email": "a@b.co",
            },
            SesEmailSender,
        ),
        (
            {"environment": "local", "email_backend": "ses", "ses_sender_email": "a@b.co"},
            SesEmailSender,
        ),
    ],
)
def test_the_sender_depends_on_the_environment(monkeypatch, settings, expected):
    monkeypatch.setattr(email, "get_settings", lambda: Settings(_env_file=None, **settings))
    get_email_sender.cache_clear()
    try:
        assert isinstance(get_email_sender(), expected)
    finally:
        get_email_sender.cache_clear()


def test_ses_requires_a_sender_address():
    with pytest.raises(ValueError, match="SES_SENDER_EMAIL"):
        Settings(_env_file=None, email_backend="ses")
