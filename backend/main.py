import json
import functions_framework
from google.cloud import storage
import config

_storage_client = None

def get_storage():
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client()
    return _storage_client


def check_auth(request):
    if not config.MASTER_KEY:
        raise ValueError("MASTER_KEY not configured on server")
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or auth[7:] != config.MASTER_KEY:
        raise ValueError("Invalid access code")


def data_blob():
    bucket = get_storage().bucket(config.BUCKET_NAME)
    return bucket.blob(f"{config.APP_NAME}/data.json")


def cors(request) -> dict:
    return {
        "Access-Control-Allow-Origin":  request.headers.get("Origin", "*"),
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
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
        check_auth(request)
    except ValueError as e:
        return json_response({"error": str(e)}, 401, h)

    blob = data_blob()

    # GET — read app data
    if request.method == "GET":
        data = json.loads(blob.download_as_text()) if blob.exists() else {}
        return json_response(data, 200, h)

    # POST/PUT — write app data (replace entire document)
    if request.method in ("POST", "PUT"):
        body = request.get_json(silent=True)
        if body is None:
            return json_response({"error": "Invalid JSON"}, 400, h)
        blob.upload_from_string(json.dumps(body), content_type="application/json")
        return json_response({"ok": True}, 200, h)

    # DELETE — wipe app data
    if request.method == "DELETE":
        if blob.exists():
            blob.delete()
        return json_response({"ok": True}, 200, h)

    return json_response({"error": "Method not allowed"}, 405, h)
