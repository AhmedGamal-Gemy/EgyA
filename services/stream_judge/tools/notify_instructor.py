"""See plan section 7.5 — Stream Judge tools.

Pushes a flag to the instructor's live dashboard. This is the one piece
NOT covered by Redis/MCP discussions elsewhere in the plan — it's the
app's own push layer to the browser, separate from persistence.
"""

from fastapi import WebSocket

from shared.schemas.flag import Flag

# Simple in-memory registry of connected dashboard WebSockets per session.
# Fine for a hackathon single-instance deployment; would need a proper
# pub/sub (e.g. Redis pub/sub) if this ever ran across multiple replicas.
_connected_dashboards: dict[str, list[WebSocket]] = {}


def register_dashboard(session_id: str, websocket: WebSocket) -> None:
    _connected_dashboards.setdefault(session_id, []).append(websocket)


def unregister_dashboard(session_id: str, websocket: WebSocket) -> None:
    if session_id in _connected_dashboards:
        _connected_dashboards[session_id] = [
            ws for ws in _connected_dashboards[session_id] if ws is not websocket
        ]


async def notify_instructor(flag: Flag) -> None:
    for websocket in _connected_dashboards.get(flag.session_id, []):
        try:
            await websocket.send_json(flag.model_dump(mode="json"))
        except Exception:
            # Non-fatal — a dropped dashboard connection shouldn't crash
            # judgment processing. Cleanup of dead connections happens via
            # unregister_dashboard when the WebSocket endpoint itself
            # detects a disconnect (see main.py, TODO: add the actual
            # WebSocket endpoint for the dashboard to connect to).
            pass
