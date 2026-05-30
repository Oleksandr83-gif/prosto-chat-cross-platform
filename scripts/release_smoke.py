import asyncio
import os
import time
from uuid import uuid4

import httpx
import websockets


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api")
WS_BASE_URL = os.getenv("WS_BASE_URL", "ws://127.0.0.1:8000/ws")
HEALTH_URL = os.getenv("HEALTH_URL", "http://127.0.0.1:8000/health")

SMOKE_PASSWORD = os.getenv("SMOKE_PASSWORD", "SmokePass123")


def wait_for_backend(timeout_seconds: int = 60) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            response = httpx.get(HEALTH_URL, timeout=5)
            response.raise_for_status()
            print(f"[ok] backend health: {response.json()}")
            return
        except Exception as exc:
            last_error = exc
            time.sleep(2)

    raise RuntimeError(f"Backend did not become healthy: {last_error}")


def api_request(client: httpx.Client, method: str, path: str, token: str | None = None, **kwargs) -> httpx.Response:
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = client.request(method, f"{API_BASE_URL}{path}", headers=headers, timeout=15, **kwargs)
    response.raise_for_status()
    return response


def register_smoke_user(client: httpx.Client, suffix: str, label: str) -> dict:
    # Smoke-test створює тимчасового користувача через той самий REST API, яким користується frontend.
    response = api_request(
        client,
        "POST",
        "/auth/register",
        json={
            "display_name": f"Smoke {label} {suffix}",
            "email": f"smoke-{suffix.lower()}-{label.lower()}@example.com",
            "phone": None,
            "password": SMOKE_PASSWORD,
            "age": 20,
        },
    ).json()
    user = response["user"]
    print(f"[ok] registered user: {user['display_name']} / {user['user_number']}")
    return response


async def websocket_check(chat_id: str, token: str) -> None:
    uri = f"{WS_BASE_URL}/chats/{chat_id}?token={token}"
    async with websockets.connect(uri, open_timeout=10) as websocket:
        await websocket.send(
            '{"event":"message.send","payload":{"type":"text","body":"release smoke websocket"}}'
        )
        raw = await asyncio.wait_for(websocket.recv(), timeout=15)
        if "release smoke websocket" not in raw or "message.created" not in raw:
            raise AssertionError(f"Unexpected websocket event: {raw}")
        print("[ok] websocket message.created received")


def main() -> None:
    wait_for_backend()

    with httpx.Client() as client:
        suffix = uuid4().hex[:10]
        owner = register_smoke_user(client, suffix, "Owner")
        contact_account = register_smoke_user(client, suffix, "Contact")
        token = owner["access_token"]
        user = owner["user"]
        contact_user = contact_account["user"]

        login = api_request(
            client,
            "POST",
            "/auth/login",
            json={"login": user["email"], "password": SMOKE_PASSWORD},
        ).json()
        token = login["access_token"]
        print(f"[ok] login: {login['user']['display_name']} / {login['user']['user_number']}")

        contact = api_request(
            client,
            "POST",
            "/contacts",
            token=token,
            json={"user_number": contact_user["user_number"]},
        ).json()
        contact_user = contact["contact_user"]
        print(f"[ok] contact added: {contact_user['display_name']} / {contact_user['user_number']}")

        chat = api_request(
            client,
            "POST",
            "/chats/private",
            token=token,
            json={"contact_user_id": contact_user["id"]},
        ).json()
        chat_id = chat["id"]
        print(f"[ok] private chat: {chat_id}")

        rest_message = api_request(
            client,
            "POST",
            f"/chats/{chat_id}/messages",
            token=token,
            json={"type": "text", "body": "release smoke rest"},
        ).json()
        print(f"[ok] REST message saved: {rest_message['id']}")

        history = api_request(client, "GET", f"/chats/{chat_id}/messages", token=token).json()
        if not any(message["body"] == "release smoke rest" for message in history):
            raise AssertionError("REST message was not found in message history")
        print(f"[ok] message history contains {len(history)} messages")

    asyncio.run(websocket_check(chat_id, token))
    print("RELEASE_SMOKE_OK")


if __name__ == "__main__":
    main()
