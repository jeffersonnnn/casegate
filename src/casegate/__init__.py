"""casegate: an eval harness and CI gate for LLM agents.

The package root holds the version that hatch and `casegate --version` read,
and re-exports the three errors that user code (targets, suites) may raise or catch.
"""

from casegate.errors import JudgeError, RetryableError, SuiteError

__version__ = "0.1.0"

__all__ = ["JudgeError", "RetryableError", "SuiteError", "__version__"]
