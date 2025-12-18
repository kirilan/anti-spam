import logging
from dataclasses import dataclass
from typing import Optional

import redis
from redis.exceptions import RedisError

from app.config import settings


@dataclass
class RateLimitResult:
    """Represents the outcome of a limiter check."""

    allowed: bool
    remaining: int
    retry_after: int


class RateLimiter:
    """Simple Redis-backed fixed window rate limiter."""

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)
        self._client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    def check_limit(
        self,
        user_id: str,
        action: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """
        Increment usage for a given user+action and determine if the call is allowed.
        Falls back to allowing the request if Redis is unavailable.
        """
        key = f"rate:{action}:{user_id}"
        try:
            current = self._client.incr(key)
            if current == 1:
                self._client.expire(key, window_seconds)

            ttl = self._client.ttl(key)
            retry_after = ttl if ttl and ttl > 0 else window_seconds
            remaining = max(limit - current, 0)
            allowed = current <= limit

            return RateLimitResult(
                allowed=allowed,
                remaining=remaining,
                retry_after=max(retry_after, 1),
            )
        except RedisError as exc:
            self._logger.warning("Rate limiter unavailable, allowing request: %s", exc)
            # Fail open if Redis is unavailable
            return RateLimitResult(
                allowed=True,
                remaining=limit,
                retry_after=0,
            )


rate_limiter = RateLimiter()
