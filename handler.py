import json
import os
import urllib.request
import urllib.error


CHATWOOT_BASE_URL = os.environ.get("CHATWOOT_BASE_URL", "").rstrip("/")
VERIFY_TOKENS = [t.strip() for t in os.environ.get("VERIFY_TOKENS", "").split(",") if t.strip()]
FORWARD_TIMEOUT = int(os.environ.get("FORWARD_TIMEOUT_SECONDS", "10"))


def lambda_handler(event, context):
    http_context = event.get("requestContext", {}).get("http", {})
    method = http_context.get("method") or event.get("httpMethod", "GET")

    if method == "GET":
        return handle_verification(event)

    if method == "POST":
        return handle_webhook(event)

    return {"statusCode": 405, "body": "Method Not Allowed"}


def handle_verification(event):
    params = event.get("queryStringParameters") or {}
    mode = params.get("hub.mode")
    challenge = params.get("hub.challenge", "")
    token = params.get("hub.verify_token")

    if mode == "subscribe" and token in VERIFY_TOKENS:
        print(f"WEBHOOK VERIFIED — token accepted")
        return {"statusCode": 200, "body": challenge}

    print(f"WEBHOOK VERIFICATION FAILED — mode={mode!r} token={token!r}")
    return {"statusCode": 403, "body": "Forbidden"}


def handle_webhook(event):
    raw_body = event.get("body", "{}")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON body: {e}")
        # Still return 200 so Meta doesn't retry garbage payloads
        return {"statusCode": 200, "body": "OK"}

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            metadata = change.get("value", {}).get("metadata", {})
            phone = metadata.get("display_phone_number")

            if not phone:
                print(f"No display_phone_number in change metadata — skipping: {json.dumps(change)}")
                continue

            forward_to_chatwoot(phone, raw_body)

    return {"statusCode": 200, "body": "OK"}


def forward_to_chatwoot(phone_number: str, body: str):
    if not phone_number.startswith("+"):
        phone_number = "+" + phone_number

    url = f"{CHATWOOT_BASE_URL}/{phone_number}"

    req = urllib.request.Request(
        url,
        data=body.encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=FORWARD_TIMEOUT) as response:
            print(f"Forwarded to {url} → {response.status}")
    except urllib.error.HTTPError as e:
        print(f"HTTP error forwarding to {url}: {e.code} {e.reason}")
    except Exception as e:
        print(f"Error forwarding to {url}: {e}")
