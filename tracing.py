import attr
from contextlib import contextmanager
from datetime import datetime, timedelta
import json
import os

from opentelemetry import trace
from opentelemetry.sdk.trace import Span, TracerProvider
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SimpleExportSpanProcessor,
)

from types import TracebackType
from typing import (
    Generator,
    Dict,
    List,
    IO,
    Optional,
    Mapping,
    Protocol,
    Type,
)
import uuid

Context = Optional[Mapping[str, str]]


class Tracer(Protocol):
    def open_span(self, span_name: str, context: Context) -> None:
        ...

    def close_span(self) -> None:
        ...


def single_line_json(span: Span) -> str:
    """Format tracing spans as single-line JSON.

    By default, the ConsoleSpanExporter spits out verbose JSON across multiple lines.
    I'd like to be able to slurp these spans up into some kind of data store so that I
    can poke at them, and the easiest way to do that is to have one span per line.
    """
    json = span.to_json(indent=None)
    assert isinstance(json, str)
    return json + os.linesep


def init(tracefile: Optional[IO[str]] = None) -> None:
    tracer_provider = TracerProvider()
    if tracefile is not None:
        tracer_provider.add_span_processor(
            SimpleExportSpanProcessor(
                ConsoleSpanExporter(out=tracefile, formatter=single_line_json)
            )
        )
    trace.set_tracer_provider(tracer_provider)


@contextmanager
def span(span_name: str, context: Context = None) -> Generator[None, None, None]:
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span(span_name, attributes=context):
        yield
