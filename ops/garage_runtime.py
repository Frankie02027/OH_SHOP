#!/usr/bin/env python3
"""Minimal Garage-facing processor built on the validated boundary helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from ops.garage_boundaries import (
    GarageBoundaryError,
    get_garage_schema_registry,
    record_garage_event,
    validate_inbound_garage_call,
    write_garage_persisted_record,
)


@dataclass(frozen=True)
class GarageRecordWrite:
    """One explicit persisted/shared record write request from a handler."""

    schema_name: str
    data: dict[str, Any]


@dataclass(frozen=True)
class GarageHandlerOutput:
    """Normalized handler output for the first runtime-shaped processor."""

    result: Any = None
    events: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    records: tuple[GarageRecordWrite, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GarageProcessingResult:
    """Result bundle returned after validated handler dispatch and side effects."""

    call_type: str
    result: Any
    recorded_events: tuple[Any, ...] = field(default_factory=tuple)
    written_records: tuple[Any, ...] = field(default_factory=tuple)


class GarageProcessorError(RuntimeError):
    """Raised when dispatch or handler output shape is invalid."""


Handler = Callable[[dict[str, Any]], Any]
EventRecorder = Callable[[dict[str, Any]], Any]
RecordWriter = Callable[[str, dict[str, Any]], Any]


def _default_event_recorder(event: dict[str, Any]) -> dict[str, Any]:
    return event


def _default_record_writer(schema_name: str, data: dict[str, Any]) -> GarageRecordWrite:
    return GarageRecordWrite(schema_name=schema_name, data=data)


class GarageRuntimeProcessor:
    """Small validated processor for official Garage calls, events, and records."""

    def __init__(
        self,
        *,
        event_recorder: EventRecorder | None = None,
        record_writer: RecordWriter | None = None,
    ) -> None:
        self._registry = get_garage_schema_registry()
        self._handlers: dict[str, Handler] = {}
        self._event_recorder = event_recorder or _default_event_recorder
        self._record_writer = record_writer or _default_record_writer

    def register_handler(self, call_type: str, handler: Handler) -> None:
        """Register a handler for one known Garage call type."""

        if call_type not in self._registry.available_call_types():
            raise GarageProcessorError(
                f"Cannot register handler for unknown call_type '{call_type}'"
            )
        self._handlers[call_type] = handler

    def process_call(self, data: dict[str, Any]) -> GarageProcessingResult:
        """Validate, dispatch, and process handler-produced events/records."""

        validated_call = validate_inbound_garage_call(data)
        call_type = str(data.get("call_type") or "")
        handler = self._handlers.get(call_type)
        if handler is None:
            raise GarageProcessorError(
                f"No handler registered for call_type '{call_type or '<missing>'}'"
            )

        handler_output = handler(validated_call)
        normalized = self._normalize_handler_output(call_type, handler_output)

        recorded_events = tuple(
            record_garage_event(event, self._event_recorder)
            for event in normalized.events
        )
        written_records = tuple(
            write_garage_persisted_record(
                record_write.schema_name,
                record_write.data,
                self._record_writer,
            )
            for record_write in normalized.records
        )

        return GarageProcessingResult(
            call_type=call_type,
            result=normalized.result,
            recorded_events=recorded_events,
            written_records=written_records,
        )

    def _normalize_handler_output(
        self,
        call_type: str,
        handler_output: Any,
    ) -> GarageHandlerOutput:
        if handler_output is None:
            return GarageHandlerOutput()
        if isinstance(handler_output, GarageHandlerOutput):
            return handler_output
        if isinstance(handler_output, Mapping):
            return GarageHandlerOutput(
                result=handler_output.get("result"),
                events=self._normalize_events(call_type, handler_output.get("events", ())),
                records=self._normalize_records(
                    call_type, handler_output.get("records", ())
                ),
            )
        return GarageHandlerOutput(result=handler_output)

    @staticmethod
    def _normalize_events(call_type: str, raw_events: Any) -> tuple[dict[str, Any], ...]:
        if raw_events in (None, ()):
            return ()
        if not isinstance(raw_events, (list, tuple)):
            raise GarageProcessorError(
                f"Handler for {call_type} returned invalid events payload; expected list/tuple"
            )

        normalized: list[dict[str, Any]] = []
        for event in raw_events:
            if not isinstance(event, dict):
                raise GarageProcessorError(
                    f"Handler for {call_type} returned a non-dict event"
                )
            normalized.append(event)
        return tuple(normalized)

    @staticmethod
    def _normalize_records(
        call_type: str,
        raw_records: Any,
    ) -> tuple[GarageRecordWrite, ...]:
        if raw_records in (None, ()):
            return ()
        if not isinstance(raw_records, (list, tuple)):
            raise GarageProcessorError(
                f"Handler for {call_type} returned invalid records payload; expected list/tuple"
            )

        normalized: list[GarageRecordWrite] = []
        for record in raw_records:
            if isinstance(record, GarageRecordWrite):
                normalized.append(record)
                continue
            if (
                isinstance(record, tuple)
                and len(record) == 2
                and isinstance(record[0], str)
                and isinstance(record[1], dict)
            ):
                normalized.append(
                    GarageRecordWrite(schema_name=record[0], data=record[1])
                )
                continue
            raise GarageProcessorError(
                f"Handler for {call_type} returned an invalid record write entry"
            )
        return tuple(normalized)


__all__ = [
    "GarageHandlerOutput",
    "GarageProcessingResult",
    "GarageProcessorError",
    "GarageRecordWrite",
    "GarageRuntimeProcessor",
    "GarageBoundaryError",
]
