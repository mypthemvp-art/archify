"""OpenTelemetry instrumentation for the registry gateway."""

from __future__ import annotations

import os
from typing import Any

SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "agent-ops-registry-gateway")
OTLP_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")

_tracer = None
_meter = None
_invoke_counter = None
_policy_counter = None
_latency_hist = None
_configured = False


def configure_telemetry(app: Any | None = None) -> None:
    global _tracer, _meter, _invoke_counter, _policy_counter, _latency_hist, _configured
    if _configured:
        return
    try:
        from opentelemetry import metrics, trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
    except ImportError:
        # Soft-dep: gateway still runs without OTEL packages in minimal installs
        _configured = True
        return

    resource = Resource.create({"service.name": SERVICE_NAME})
    tracer_provider = TracerProvider(resource=resource)
    if OTLP_ENDPOINT:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{OTLP_ENDPOINT}/v1/traces")))
        except Exception:
            tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    elif os.environ.get("OTEL_CONSOLE", "0") == "1":
        tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(tracer_provider)
    _tracer = trace.get_tracer(SERVICE_NAME)

    readers = []
    if OTLP_ENDPOINT:
        try:
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

            readers.append(PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=f"{OTLP_ENDPOINT}/v1/metrics")))
        except Exception:
            readers.append(PeriodicExportingMetricReader(ConsoleMetricExporter()))
    elif os.environ.get("OTEL_CONSOLE", "0") == "1":
        readers.append(PeriodicExportingMetricReader(ConsoleMetricExporter()))
    if readers:
        metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=readers))
    else:
        metrics.set_meter_provider(MeterProvider(resource=resource))
    _meter = metrics.get_meter(SERVICE_NAME)
    _invoke_counter = _meter.create_counter("mcp.gateway.invokes", unit="1")
    _policy_counter = _meter.create_counter("mcp.gateway.policy_decisions", unit="1")
    _latency_hist = _meter.create_histogram("mcp.gateway.invoke.latency", unit="ms")

    if app is not None:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(app)
        except Exception:
            pass
    _configured = True


def tracer():
    return _tracer


def record_policy(decision: str, connector: str, tool: str) -> None:
    if _policy_counter:
        _policy_counter.add(1, {"decision": decision, "connector": connector, "tool": tool})


def record_invoke(connector: str, tool: str, status: str, latency_ms: float) -> None:
    if _invoke_counter:
        _invoke_counter.add(1, {"connector": connector, "tool": tool, "status": status})
    if _latency_hist:
        _latency_hist.record(latency_ms, {"connector": connector, "tool": tool})


class span_ctx:
    """Lightweight span context manager that no-ops without OTEL."""

    def __init__(self, name: str, **attrs: Any):
        self.name = name
        self.attrs = attrs
        self._span = None
        self._token = None

    def __enter__(self):
        if _tracer is None:
            return self
        from opentelemetry import trace

        self._span = _tracer.start_span(self.name)
        for k, v in self.attrs.items():
            if v is not None:
                self._span.set_attribute(k, v)
        self._token = trace.use_span(self._span, end_on_exit=False)
        self._token.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._token:
            self._token.__exit__(exc_type, exc, tb)
        if self._span:
            if exc:
                self._span.record_exception(exc)
            self._span.end()
        return False
