"""Observability: structured logging, tracing, and cost tracking.

Provides:
- Structured JSON logging with trace IDs
- Token and cost tracking per stage
- Performance metrics
"""

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

# Context variable for trace ID (thread-safe)
_trace_id: ContextVar[str] = ContextVar("trace_id", default="")
_campaign_id: ContextVar[str] = ContextVar("campaign_id", default="")


def get_trace_id() -> str:
    """Get current trace ID."""
    return _trace_id.get() or generate_trace_id()


def set_trace_id(trace_id: str) -> None:
    """Set trace ID for current context."""
    _trace_id.set(trace_id)


def generate_trace_id() -> str:
    """Generate a new trace ID."""
    return uuid.uuid4().hex[:12]


def get_campaign_id() -> str:
    """Get current campaign ID."""
    return _campaign_id.get()


def set_campaign_id(campaign_id: str) -> None:
    """Set campaign ID for current context."""
    _campaign_id.set(campaign_id)


@dataclass
class TokenUsage:
    """Token usage for a single operation."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @property
    def cost_usd(self) -> float:
        """Estimate cost in USD (using Gemini pricing)."""
        # Gemini 1.5 Flash pricing (approx)
        # Input: $0.075 per 1M tokens, Output: $0.30 per 1M tokens
        input_cost = self.prompt_tokens * 0.000000075
        output_cost = self.completion_tokens * 0.0000003
        return input_cost + output_cost


@dataclass
class StageMetrics:
    """Metrics for a single stage execution."""

    stage: str
    campaign_id: str
    trace_id: str
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: int = 0
    tokens: TokenUsage | None = None
    success: bool = True
    error: str | None = None
    retries: int = 0

    def complete(self, success: bool = True, error: str | None = None) -> None:
        """Mark stage as complete."""
        self.end_time = datetime.now()
        self.duration_ms = int((self.end_time - self.start_time).total_seconds() * 1000)
        self.success = success
        self.error = error


class StructuredLogger:
    """JSON structured logger with trace context."""

    def __init__(
        self,
        name: str = "agentcy",
        level: int = logging.INFO,
        log_file: Path | None = None,
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Avoid duplicate handlers
        if not self.logger.handlers:
            # Console handler
            console = logging.StreamHandler(sys.stderr)
            console.setFormatter(self._create_formatter())
            self.logger.addHandler(console)

            # File handler if specified
            if log_file:
                log_file.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(self._create_formatter(json_format=True))
                self.logger.addHandler(file_handler)

    def _create_formatter(self, json_format: bool = False) -> logging.Formatter:
        """Create log formatter."""
        if json_format:
            return JsonFormatter()
        return logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def _add_context(self, extra: dict[str, Any] | None) -> dict[str, Any]:
        """Add trace context to log record."""
        context = {
            "trace_id": get_trace_id(),
            "campaign_id": get_campaign_id(),
        }
        if extra:
            context.update(extra)
        return context

    def info(self, msg: str, **kwargs: Any) -> None:
        """Log info message."""
        self.logger.info(msg, extra={"context": self._add_context(kwargs)})

    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.logger.warning(msg, extra={"context": self._add_context(kwargs)})

    def error(self, msg: str, **kwargs: Any) -> None:
        """Log error message."""
        self.logger.error(msg, extra={"context": self._add_context(kwargs)})

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.logger.debug(msg, extra={"context": self._add_context(kwargs)})

    def stage_start(self, stage: str, **kwargs: Any) -> None:
        """Log stage start."""
        self.info(f"Stage started: {stage}", stage=stage, event="stage_start", **kwargs)

    def stage_complete(self, metrics: StageMetrics) -> None:
        """Log stage completion with metrics."""
        event = "stage_complete" if metrics.success else "stage_failed"
        level = "info" if metrics.success else "error"

        log_data = {
            "stage": metrics.stage,
            "event": event,
            "duration_ms": metrics.duration_ms,
            "success": metrics.success,
            "retries": metrics.retries,
        }

        if metrics.tokens:
            log_data["tokens"] = asdict(metrics.tokens)
            log_data["cost_usd"] = metrics.tokens.cost_usd

        if metrics.error:
            log_data["error"] = metrics.error

        msg = f"Stage {'completed' if metrics.success else 'failed'}: {metrics.stage}"
        if level == "error":
            self.error(msg, **log_data)
        else:
            self.info(msg, **log_data)


class JsonFormatter(logging.Formatter):
    """JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Add context if present
        if hasattr(record, "context"):
            log_data.update(record.context)

        return json.dumps(log_data)


class CostTracker:
    """Track token usage and costs across a campaign."""

    def __init__(self):
        self.stages: dict[str, TokenUsage] = {}
        self.total = TokenUsage()

    def add_usage(self, stage: str, usage: TokenUsage) -> None:
        """Add token usage for a stage."""
        if stage not in self.stages:
            self.stages[stage] = TokenUsage()

        self.stages[stage].prompt_tokens += usage.prompt_tokens
        self.stages[stage].completion_tokens += usage.completion_tokens
        self.stages[stage].total_tokens += usage.total_tokens

        self.total.prompt_tokens += usage.prompt_tokens
        self.total.completion_tokens += usage.completion_tokens
        self.total.total_tokens += usage.total_tokens

    def get_summary(self) -> dict[str, Any]:
        """Get cost summary."""
        return {
            "total_tokens": self.total.total_tokens,
            "total_cost_usd": self.total.cost_usd,
            "by_stage": {
                stage: {
                    "tokens": usage.total_tokens,
                    "cost_usd": usage.cost_usd,
                }
                for stage, usage in self.stages.items()
            },
        }


def timed(logger: StructuredLogger | None = None) -> Callable:
    """Decorator to time function execution.

    Args:
        logger: Optional logger for timing output

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                if logger:
                    logger.debug(
                        f"{func.__name__} completed",
                        function=func.__name__,
                        duration_ms=round(elapsed, 2),
                    )
                return result
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                if logger:
                    logger.error(
                        f"{func.__name__} failed",
                        function=func.__name__,
                        duration_ms=round(elapsed, 2),
                        error=str(e),
                    )
                raise

        return wrapper

    return decorator


# Default logger instance
_default_logger: StructuredLogger | None = None


def get_logger() -> StructuredLogger:
    """Get the default structured logger."""
    global _default_logger
    if _default_logger is None:
        _default_logger = StructuredLogger()
    return _default_logger


def configure_logging(
    level: int = logging.INFO,
    log_file: Path | None = None,
) -> StructuredLogger:
    """Configure the default logger.

    Args:
        level: Log level
        log_file: Optional file path for JSON logs

    Returns:
        Configured logger
    """
    global _default_logger
    _default_logger = StructuredLogger(level=level, log_file=log_file)
    return _default_logger
