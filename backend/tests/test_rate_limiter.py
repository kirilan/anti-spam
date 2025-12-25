"""Tests for the rate limiter service"""

from unittest.mock import MagicMock, patch

import pytest
from redis.exceptions import RedisError

from app.services.rate_limiter import RateLimiter, RateLimitResult


class TestRateLimiter:
    """Tests for RateLimiter class"""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client"""
        with patch("app.services.rate_limiter.redis.Redis.from_url") as mock:
            mock_client = MagicMock()
            mock.return_value = mock_client
            yield mock_client

    def test_first_request_allowed(self, mock_redis):
        """Test that the first request is always allowed"""
        mock_redis.incr.return_value = 1
        mock_redis.ttl.return_value = 3600

        limiter = RateLimiter()
        result = limiter.check_limit(
            user_id="user-123",
            action="scan",
            limit=5,
            window_seconds=3600,
        )

        assert result.allowed is True
        assert result.remaining == 4
        mock_redis.expire.assert_called_once_with("rate:scan:user-123", 3600)

    def test_request_within_limit_allowed(self, mock_redis):
        """Test that requests within limit are allowed"""
        mock_redis.incr.return_value = 3
        mock_redis.ttl.return_value = 1800

        limiter = RateLimiter()
        result = limiter.check_limit(
            user_id="user-123",
            action="scan",
            limit=5,
            window_seconds=3600,
        )

        assert result.allowed is True
        assert result.remaining == 2
        assert result.retry_after == 1800

    def test_request_at_limit_allowed(self, mock_redis):
        """Test that request exactly at limit is allowed"""
        mock_redis.incr.return_value = 5
        mock_redis.ttl.return_value = 1000

        limiter = RateLimiter()
        result = limiter.check_limit(
            user_id="user-123",
            action="scan",
            limit=5,
            window_seconds=3600,
        )

        assert result.allowed is True
        assert result.remaining == 0

    def test_request_over_limit_blocked(self, mock_redis):
        """Test that requests over limit are blocked"""
        mock_redis.incr.return_value = 6
        mock_redis.ttl.return_value = 500

        limiter = RateLimiter()
        result = limiter.check_limit(
            user_id="user-123",
            action="scan",
            limit=5,
            window_seconds=3600,
        )

        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after == 500

    def test_different_actions_tracked_separately(self, mock_redis):
        """Test that different actions have separate limits"""
        mock_redis.incr.return_value = 1
        mock_redis.ttl.return_value = 3600

        limiter = RateLimiter()

        # First action
        limiter.check_limit(
            user_id="user-123",
            action="scan",
            limit=5,
            window_seconds=3600,
        )

        # Second action
        limiter.check_limit(
            user_id="user-123",
            action="response_scan",
            limit=5,
            window_seconds=3600,
        )

        # Verify different keys were used
        calls = mock_redis.incr.call_args_list
        assert calls[0][0][0] == "rate:scan:user-123"
        assert calls[1][0][0] == "rate:response_scan:user-123"

    def test_different_users_tracked_separately(self, mock_redis):
        """Test that different users have separate limits"""
        mock_redis.incr.return_value = 1
        mock_redis.ttl.return_value = 3600

        limiter = RateLimiter()

        # First user
        limiter.check_limit(
            user_id="user-123",
            action="scan",
            limit=5,
            window_seconds=3600,
        )

        # Second user
        limiter.check_limit(
            user_id="user-456",
            action="scan",
            limit=5,
            window_seconds=3600,
        )

        # Verify different keys were used
        calls = mock_redis.incr.call_args_list
        assert calls[0][0][0] == "rate:scan:user-123"
        assert calls[1][0][0] == "rate:scan:user-456"

    def test_redis_error_fails_open(self, mock_redis):
        """Test that Redis errors result in allowing the request (fail open)"""
        mock_redis.incr.side_effect = RedisError("Connection refused")

        limiter = RateLimiter()
        result = limiter.check_limit(
            user_id="user-123",
            action="scan",
            limit=5,
            window_seconds=3600,
        )

        # Should fail open - allow the request
        assert result.allowed is True
        assert result.remaining == 5
        assert result.retry_after == 0

    def test_ttl_returns_negative_uses_window(self, mock_redis):
        """Test that negative TTL uses window_seconds as retry_after"""
        mock_redis.incr.return_value = 6
        mock_redis.ttl.return_value = -1  # Key has no TTL

        limiter = RateLimiter()
        result = limiter.check_limit(
            user_id="user-123",
            action="scan",
            limit=5,
            window_seconds=3600,
        )

        assert result.retry_after == 3600

    def test_ttl_returns_zero_uses_window(self, mock_redis):
        """Test that zero TTL uses window_seconds as retry_after"""
        mock_redis.incr.return_value = 2
        mock_redis.ttl.return_value = 0

        limiter = RateLimiter()
        result = limiter.check_limit(
            user_id="user-123",
            action="scan",
            limit=5,
            window_seconds=3600,
        )

        assert result.retry_after == 3600

    def test_expire_only_called_on_first_request(self, mock_redis):
        """Test that expire is only called when counter is 1"""
        mock_redis.incr.return_value = 2
        mock_redis.ttl.return_value = 1800

        limiter = RateLimiter()
        limiter.check_limit(
            user_id="user-123",
            action="scan",
            limit=5,
            window_seconds=3600,
        )

        # expire should not be called since incr returned 2
        mock_redis.expire.assert_not_called()

    def test_remaining_never_negative(self, mock_redis):
        """Test that remaining is never negative even when way over limit"""
        mock_redis.incr.return_value = 100
        mock_redis.ttl.return_value = 1000

        limiter = RateLimiter()
        result = limiter.check_limit(
            user_id="user-123",
            action="scan",
            limit=5,
            window_seconds=3600,
        )

        assert result.remaining == 0

    def test_retry_after_minimum_one(self, mock_redis):
        """Test that retry_after is at least 1 second"""
        mock_redis.incr.return_value = 1
        mock_redis.ttl.return_value = 0

        limiter = RateLimiter()
        result = limiter.check_limit(
            user_id="user-123",
            action="scan",
            limit=5,
            window_seconds=0,  # Edge case
        )

        assert result.retry_after >= 1


class TestRateLimitResult:
    """Tests for RateLimitResult dataclass"""

    def test_dataclass_creation(self):
        """Test that RateLimitResult can be created"""
        result = RateLimitResult(allowed=True, remaining=5, retry_after=3600)

        assert result.allowed is True
        assert result.remaining == 5
        assert result.retry_after == 3600

    def test_dataclass_equality(self):
        """Test that RateLimitResult supports equality comparison"""
        result1 = RateLimitResult(allowed=True, remaining=5, retry_after=3600)
        result2 = RateLimitResult(allowed=True, remaining=5, retry_after=3600)

        assert result1 == result2

    def test_dataclass_inequality(self):
        """Test that RateLimitResult supports inequality comparison"""
        result1 = RateLimitResult(allowed=True, remaining=5, retry_after=3600)
        result2 = RateLimitResult(allowed=False, remaining=0, retry_after=3600)

        assert result1 != result2
