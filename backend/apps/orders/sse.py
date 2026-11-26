"""Redis Pub/Sub helpers for the real-time kitchen and order-tracking streams.

The HTTP layer only formats Server-Sent Events; all payload construction and
Redis access lives here so the polling endpoints and the streaming endpoints
always describe an order with the same fields.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterator
from typing import Any

from django.http import StreamingHttpResponse
from django.utils import timezone
from redis.exceptions import RedisError

from common.redis_client import get_redis

from .models import Order

logger = logging.getLogger(__name__)

POS_CHANNEL = "fastfood:sse:pos"
ORDER_CHANNEL_PREFIX = "fastfood:sse:order:"
KEEPALIVE_SECONDS = 15
POLL_TIMEOUT_SECONDS = 1.0


def order_channel(order_id: int) -> str:
    """Return the per-order tracking channel name."""
    return f"{ORDER_CHANNEL_PREFIX}{order_id}"


def build_order_event(
    order: Order,
    event_type: str,
    *,
    timestamp: Any = None,
) -> dict[str, Any]:
    """Build the JSON-serializable payload shared by both SSE channels."""
    return {
        "event_type": event_type,
        "order_id": order.pk,
        "daily_number": order.daily_number,
        "status": order.status,
        "payment_status": order.payment_status,
        "expected_ready_at": (
            order.expected_ready_at.isoformat()
            if order.expected_ready_at
            else None
        ),
        "cancellation_requested": order.cancellation_requested,
        "timestamp": (timestamp or timezone.now()).isoformat(),
    }


def publish_order_event(order: Order, event_type: str) -> None:
    """
    Publish an order event to the kitchen and per-order channels.

    Redis outages must never break an order transition, so this is best-effort:
    the polling endpoints remain the fallback when no subscriber is reachable.
    """
    payload = json.dumps(build_order_event(order, event_type))
    try:
        redis = get_redis()
        redis.publish(POS_CHANNEL, payload)
        redis.publish(order_channel(order.pk), payload)
    except (RedisError, OSError, ValueError):
        logger.warning(
            "Could not publish SSE event %s for order %s.",
            event_type,
            order.pk,
            exc_info=True,
        )


def make_sse_response(channels: list[str]) -> StreamingHttpResponse:
    """Build the standard no-cache SSE response for the given channels."""
    response = StreamingHttpResponse(
        event_stream(channels),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


def event_stream(channels: list[str]) -> Iterator[str]:
    """
    Yield SSE frames for the given Redis channels until the client disconnects.

    A comment frame is emitted every ``KEEPALIVE_SECONDS`` so reverse proxies
    do not close an idle connection. The pub/sub connection is always released
    in the ``finally`` block when Django closes the generator.
    """
    try:
        pubsub = get_redis().pubsub()
        pubsub.subscribe(*channels)
    except (RedisError, OSError, ValueError):
        logger.warning("Could not subscribe to SSE channels %s.", channels, exc_info=True)
        yield ": error\n\n"
        return

    try:
        last_ping = time.monotonic()
        while True:
            message = pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=POLL_TIMEOUT_SECONDS,
            )
            if message is not None:
                data = message.get("data")
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                if data:
                    event_type = _extract_event_type(data)
                    yield f"event: {event_type}\ndata: {data}\n\n"
                    last_ping = time.monotonic()

            if time.monotonic() - last_ping >= KEEPALIVE_SECONDS:
                yield ": ping\n\n"
                last_ping = time.monotonic()
    finally:
        try:
            pubsub.unsubscribe(*channels)
            pubsub.close()
        except (RedisError, OSError, ValueError):
            logger.debug("Error while closing SSE pubsub.", exc_info=True)


def _extract_event_type(data: str) -> str:
    """Read the named SSE event from the payload, falling back to ``message``."""
    try:
        parsed = json.loads(data)
    except (TypeError, ValueError):
        return "message"
    if isinstance(parsed, dict) and parsed.get("event_type"):
        return str(parsed["event_type"])
    return "message"
