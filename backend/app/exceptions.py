class GmailQuotaExceededError(Exception):
    """Raised when Gmail API returns a quota or rate limit error."""

    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after
