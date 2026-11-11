"""Error types shared by the loader, targets, judges and the retry loop.

They live in one small module so that targets and judges can raise them without
importing the runner, and so the retry loop can classify failures by type alone.
"""


class SuiteError(Exception):
    def __init__(self, errors: str | list[str]) -> None:
        # Validation collects every problem first, so the CLI can print them all at once.
        self.errors = [errors] if isinstance(errors, str) else list(errors)
        super().__init__("\n".join(self.errors))


class JudgeError(Exception): ...


class RetryableError(Exception):
    def __init__(self, message: str = "", *, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class HttpStatusRetryable(RetryableError):
    def __init__(self, status: int, retry_after: float | None = None) -> None:
        super().__init__(f"HTTP {status}", retry_after=retry_after)
        self.status = status


class RetriesExhausted(Exception):
    def __init__(self, last: BaseException, attempts: int) -> None:
        super().__init__(f"{type(last).__name__}: {last}")
        self.last = last
        self.attempts = attempts
