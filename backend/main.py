import json
import functions_framework
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google.cloud import storage
import config

_storage_client = None

def get_storage():
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client()
    return _storage_client


def verify_google_token(token: str) -> str | None:
    """Returns the user's email if the Google ID token is valid, else None."""
    try:
        info = id_token.verify_oauth2_token(
            token, google_requests.Request(), config.GOOGLE_CLIENT_ID
        )
        return info.get("email")
    except Exception:
        return None


def get_identity(request) -> tuple[str, str]:
    """
    Returns (user_id, auth_type).
    Priority: Google Bearer token > Device ID header.
    Raises ValueError with a user-facing message on failure.
    """
    auth = request.headers.get("Authorization", "")

    if auth.startswith("Bearer "):
        email = verify_google_token(auth[7:])
        if email is None:
            raise ValueError("Invalid or expired Google token")
        if not config.ALLOW_ALL and email not in config.ALLOWED_USERS:
            raise ValueError("Account not authorized for this app")
        return email, "google"

    device_id = request.headers.get("X-Device-ID", "").strip()
    if device_id:
        if not config.ALLOW_DEVICE_AUTH and not config.ALLOW_ALL:
            raise ValueError("Device auth is disabled. Sign in with Google.")
        return f"device_{device_id}", "device"

    raise ValueError("No authentication provided")


def data_blob(user_id: str):
    bucket = get_storage().bucket(config.BUCKET_NAME)
    return bucket.blob(f"{config.APP_NAME}/{user_id}/data.json")


def cors(request) -> dict:
    return {
        "Access-Control-Allow-Origin":  request.headers.get("Origin", "*"),
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, X-Device-ID, X-App-Name, Content-Type",
        "Access-Control-Max-Age":       "3600",
    }


def json_response(body, status=200, extra_headers=None):
    headers = {"Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    return (json.dumps(body), status, headers)


@functions_framework.http
def handler(request):
    h = cors(request)

    if request.method == "OPTIONS":
        return ("", 204, h)

    try:
        user_id, auth_type = get_identity(request)
    except ValueError as e:
        return json_response({"error": str(e)}, 401, h)

    blob = data_blob(user_id)

    if request.method == "GET":
        data = json.loads(blob.download_as_text()) if blob.exists() else {}
        return json_response({**data, "_user": user_id, "_auth": auth_type}, 200, h)

    if request.method in ("POST", "PUT"):
        body = request.get_json(silent=True)
        if body is None:
            return json_response({"error": "Invalid JSON"}, 400, h)
        blob.upload_from_string(json.dumps(body), content_type="application/json")
        return json_response({"ok": True, "_user": user_id}, 200, h)

    if request.method == "DELETE":
        if blob.exists():
            blob.delete()
        return json_response({"ok": True}, 200, h)

    return json_response({"error": "Method not allowed"}, 405, h)
