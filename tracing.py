from datetime import datetime, timedelta
import json
import uuid


def file_tracing(outfile):
    global _tracer

    _tracer = FileTracer(outfile)
    return _tracer


class NullTracer:
    def open_span(self, span_name, context=None):
        pass

    def close_span(self):
        pass


class FileTracer:
    def __init__(self, outfile):
        self._outfile = outfile
        self._span_stack = []

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def open_span(self, span_name, context=None):
        span = {"id": uuid.uuid4(), "name": span_name, "start_time": datetime.utcnow()}
        if context:
            span.update(context)
        if self._span_stack:
            span["parent_id"] = self._span_stack[-1]["id"]

        self._span_stack.append(span)

    def close_span(self):
        span = self._span_stack.pop()
        span["end_time"] = datetime.utcnow()
        microsecond = timedelta(microseconds=1)
        span["duration_us"] = (span["end_time"] - span["start_time"]) // microsecond
        span_str = json.dumps(span, default=str)  # Make sure the whole thing serialises
        self._outfile.write(span_str + "\n")


def open_span(span_name, context=None):
    _tracer.open_span(span_name, context)


def close_span():
    _tracer.close_span()


def span(span_name, context=None):
    return SpanContextManager(_tracer, span_name, context)


class SpanContextManager:
    def __init__(self, tracer, span_name, context):
        self._tracer = tracer
        self._span_name = span_name
        self._context = context

    def __enter__(self):
        self._tracer.open_span(self._span_name, self._context)

    def __exit__(self, type, value, traceback):
        self._tracer.close_span()


_tracer = NullTracer()
