import attr
from contextlib import contextmanager
from datetime import datetime, timedelta
import json
from types import TracebackType
from typing import (
    ContextManager,
    Generator,
    Dict,
    List,
    Optional,
    Mapping,
    Protocol,
    Type,
)
import uuid

Context = Optional[Mapping[str, object]]


class Tracer(Protocol):
    def open_span(self, span_name: str, context: Context) -> None:
        ...

    def close_span(self) -> None:
        ...


class Writable(Protocol):
    def write(self, out: str) -> int:
        ...


def file_tracing(outfile: Writable) -> ContextManager[Tracer]:
    global _tracer

    _tracer = FileTracer(outfile)
    return _tracer


class NullTracer:
    def open_span(self, span_name: str, context: Context = None) -> None:
        pass

    def close_span(self) -> None:
        pass


@attr.s(auto_attribs=True)
class Span:
    id: uuid.UUID
    name: str
    start_time: datetime
    context: Dict[str, object]

    parent_id: Optional[uuid.UUID] = None
    end_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, object]:
        if not self.end_time:
            raise ValueError("Cannot serialise spans without an end time")
        duration = self.end_time - self.start_time
        span_dict = {
            "id": self.id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_us": duration // timedelta(microseconds=1),
        }
        span_dict.update(self.context)
        return span_dict


class FileTracer:
    def __init__(self, outfile: Writable):
        self._outfile = outfile
        self._span_stack: List[Span] = []

    def __enter__(self) -> Tracer:
        return self

    def __exit__(
        self,
        type: Optional[Type[BaseException]],
        value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        pass

    def open_span(self, span_name: str, context: Context = None) -> None:
        parent_id = self._span_stack[-1].id if self._span_stack else None
        span = Span(
            id=uuid.uuid4(),
            name=span_name,
            start_time=datetime.utcnow(),
            context={},
            parent_id=parent_id,
        )
        if context:
            span.context.update(context)

        self._span_stack.append(span)

    def close_span(self) -> None:
        span = self._span_stack.pop()
        span.end_time = datetime.utcnow()
        span_str = json.dumps(span.to_dict(), default=str)
        self._outfile.write(span_str + "\n")


def open_span(span_name: str, context: Context = None) -> None:
    _tracer.open_span(span_name, context)


def close_span() -> None:
    _tracer.close_span()


@contextmanager
def span(span_name: str, context: Context = None) -> Generator[None, None, None]:
    open_span(span_name, context)
    try:
        yield
    finally:
        close_span()


_tracer = NullTracer()  # type: Tracer
