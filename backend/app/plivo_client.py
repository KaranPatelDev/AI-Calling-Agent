import plivo

from app.config import settings

_client = None


def get_client() -> plivo.RestClient:
    global _client
    if _client is None:
        _client = plivo.RestClient(settings.plivo_auth_id, settings.plivo_auth_token)
    return _client


def place_call(call_id, phone_number: str) -> str:
    """Places the Plivo call for a given `calls.id` and returns the call UUID."""
    base = settings.public_base_url.rstrip("/")
    response = get_client().calls.create(
        from_=settings.plivo_from_number,
        to_=phone_number,
        answer_url=f"{base}/voice/answer/{call_id}",
        answer_method="POST",
        hangup_url=f"{base}/voice/hangup/{call_id}",
        hangup_method="POST",
        machine_detection="true",
        machine_detection_url=f"{base}/voice/machine-detection/{call_id}",
        # ponytail: bumped from Plivo's 5000ms default — real calls showed false-positive machine
        # detection on human pickups (likely Hindi speech patterns confusing the English-tuned
        # heuristic); more analysis time may reduce that. Revisit if still inaccurate at 10s.
        machine_detection_time="10000",
    )
    return response["request_uuid"]
