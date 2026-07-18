import uuid

from fastapi.testclient import TestClient

from crmToVoice.webhook import app


def test_webhook_answers_realistic_read_only_utterance():
    client = TestClient(app)

    response = client.post(
        "/webhook",
        json={"session_id": str(uuid.uuid4()), "text": "Que visitas tenho hoje?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["reply_text"], str)
    assert body["reply_text"].strip() != ""
    assert body["done"] is True
