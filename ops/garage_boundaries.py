#!/usr/bin/env python3
"""Validated Garage runtime/storage boundary helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from ops.garage_schemas import (
    GarageSchemaRegistry,
    SchemaRegistryError,
    SchemaValidationError,
    load_schema_registry,
    validate_call,
    validate_event,
    validate_object,
)

T = TypeVar("T")


@dataclass(frozen=True)
class GarageBoundaryError(ValueError):
    """Boundary-friendly wrapper for schema validation failures."""

    boundary: str
    schema_name: str
    dispatch_value: str
    detail: str

    def __str__(self) -> str:
        dispatch = f" ({self.dispatch_value})" if self.dispatch_value else ""
        return (
            f"{self.boundary} validation failed for "
            f"{self.schema_name}{dispatch}: {self.detail}"
        )


_GARAGE_SCHEMA_REGISTRY: GarageSchemaRegistry = load_schema_registry()


def get_garage_schema_registry() -> GarageSchemaRegistry:
    """Return the singleton Garage schema registry used by boundary code."""

    return _GARAGE_SCHEMA_REGISTRY


def _wrap_schema_error(
    *,
    boundary: str,
    schema_name: str,
    dispatch_value: str,
    exc: Exception,
) -> GarageBoundaryError:
    return GarageBoundaryError(
        boundary=boundary,
        schema_name=schema_name,
        dispatch_value=dispatch_value,
        detail=str(exc),
    )


def validate_inbound_garage_call(data: dict[str, Any]) -> dict[str, Any]:
    """Validate an inbound Garage call object before handling."""

    call_type = str(data.get("call_type") or "")
    try:
        validate_call(data)
    except (SchemaValidationError, SchemaRegistryError) as exc:
        raise _wrap_schema_error(
            boundary="call",
            schema_name="call",
            dispatch_value=call_type,
            exc=exc,
        ) from exc
    return data


def handle_inbound_garage_call(
    data: dict[str, Any],
    handler: Callable[[dict[str, Any]], T],
) -> T:
    """Validate a Garage call before passing it to the handler."""

    validate_inbound_garage_call(data)
    return handler(data)


def validate_garage_event_record(data: dict[str, Any]) -> dict[str, Any]:
    """Validate a Garage event object before record/emission."""

    event_type = str(data.get("event_type") or "")
    try:
        validate_event(data)
    except (SchemaValidationError, SchemaRegistryError) as exc:
        raise _wrap_schema_error(
            boundary="event",
            schema_name="event",
            dispatch_value=event_type,
            exc=exc,
        ) from exc
    return data


def record_garage_event(
    data: dict[str, Any],
    recorder: Callable[[dict[str, Any]], T],
) -> T:
    """Validate a Garage event before handing it to the recorder/emitter."""

    validate_garage_event_record(data)
    return recorder(data)


def validate_garage_persisted_record(
    schema_name: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Validate a persisted/shared Garage record before write/save."""

    try:
        validate_object(schema_name, data)
    except (SchemaValidationError, SchemaRegistryError) as exc:
        raise _wrap_schema_error(
            boundary="persisted-record",
            schema_name=schema_name,
            dispatch_value=schema_name,
            exc=exc,
        ) from exc
    return data


def write_garage_persisted_record(
    schema_name: str,
    data: dict[str, Any],
    writer: Callable[[str, dict[str, Any]], T],
) -> T:
    """Validate a Garage persisted/shared record before writing it."""

    validate_garage_persisted_record(schema_name, data)
    return writer(schema_name, data)
