#!/usr/bin/env python3
"""Local schema registry and validation helpers for Garage v0.1 objects."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas"


@dataclass(frozen=True)
class ValidationIssue:
    """One concrete schema validation failure."""

    path: str
    message: str
    validator: str


class SchemaValidationError(ValueError):
    """Raised when schema validation fails."""

    def __init__(self, schema_name: str, issues: list[ValidationIssue]) -> None:
        self.schema_name = schema_name
        self.issues = issues
        issue_lines = [
            f"- {issue.path}: {issue.message} [{issue.validator}]"
            for issue in issues
        ]
        message = "\n".join(
            [f"Schema validation failed for {schema_name}:"] + issue_lines
        )
        super().__init__(message)


class SchemaRegistryError(RuntimeError):
    """Raised when the schema registry cannot be loaded cleanly."""


class GarageSchemaRegistry:
    """Loads, indexes, and validates the local schema tree."""

    def __init__(self, schema_root: Path) -> None:
        self.schema_root = schema_root
        self._schema_by_id: dict[str, dict[str, Any]] = {}
        self._schema_by_name: dict[str, dict[str, Any]] = {}
        self._schema_id_by_name: dict[str, str] = {}
        self._call_schema_id_by_type: dict[str, str] = {}
        self._event_schema_id_by_type: dict[str, str] = {}
        self._registry = self._load_registry()

    def _load_registry(self) -> Registry:
        if not self.schema_root.exists():
            raise SchemaRegistryError(f"Schema root missing: {self.schema_root}")

        registry = Registry()
        schema_files = sorted(self.schema_root.rglob("*.json"))
        if not schema_files:
            raise SchemaRegistryError(f"No schema files found in {self.schema_root}")

        for schema_file in schema_files:
            schema = self._load_json(schema_file)
            schema_id = schema.get("$id")
            if not isinstance(schema_id, str) or not schema_id:
                raise SchemaRegistryError(f"Schema missing $id: {schema_file}")

            self._schema_by_id[schema_id] = schema
            schema_name = self._schema_name_for(schema_file)
            self._schema_by_name[schema_name] = schema
            self._schema_id_by_name[schema_name] = schema_id

            registry = registry.with_resource(
                schema_id, DRAFT202012.create_resource(schema)
            )

            rel_parts = schema_file.relative_to(self.schema_root).parts
            if rel_parts[0] == "calls":
                call_type = schema_name
                self._call_schema_id_by_type[call_type] = schema_id
            elif rel_parts[0] == "events":
                event_type = schema_name
                self._event_schema_id_by_type[event_type] = schema_id

        return registry

    @staticmethod
    def _load_json(schema_file: Path) -> dict[str, Any]:
        try:
            return json.loads(schema_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SchemaRegistryError(
                f"Invalid JSON in schema {schema_file}: {exc}"
            ) from exc
        except OSError as exc:
            raise SchemaRegistryError(f"Failed to read schema {schema_file}: {exc}") from exc

    @staticmethod
    def _schema_name_for(schema_file: Path) -> str:
        name = schema_file.name
        if not name.endswith(".schema.json"):
            raise SchemaRegistryError(f"Unexpected schema filename: {schema_file}")
        return name.removesuffix(".schema.json")

    def available_schema_names(self) -> list[str]:
        return sorted(self._schema_by_name)

    def available_call_types(self) -> list[str]:
        return sorted(self._call_schema_id_by_type)

    def available_event_types(self) -> list[str]:
        return sorted(self._event_schema_id_by_type)

    def get_schema(self, schema_name: str) -> dict[str, Any]:
        try:
            return self._schema_by_name[schema_name]
        except KeyError as exc:
            raise SchemaRegistryError(
                f"Unknown schema name '{schema_name}'. "
                f"Known schemas: {', '.join(self.available_schema_names())}"
            ) from exc

    def _get_validator(self, schema_name: str) -> Draft202012Validator:
        schema = self.get_schema(schema_name)
        return Draft202012Validator(schema, registry=self._registry)

    def _raise_for_errors(
        self, schema_name: str, validator: Draft202012Validator, data: Any
    ) -> None:
        errors = sorted(
            validator.iter_errors(data),
            key=lambda err: (list(err.absolute_path), err.message),
        )
        if not errors:
            return

        issues = [
            ValidationIssue(
                path=self._format_error_path(error),
                message=error.message,
                validator=error.validator,
            )
            for error in errors
        ]
        raise SchemaValidationError(schema_name, issues)

    @staticmethod
    def _format_error_path(error: Any) -> str:
        if not error.absolute_path:
            return "<root>"
        return ".".join(str(part) for part in error.absolute_path)

    def validate_object(self, schema_name: str, data: Any) -> None:
        validator = self._get_validator(schema_name)
        self._raise_for_errors(schema_name, validator, data)

    def validate_call_envelope(self, data: Any) -> None:
        self.validate_object("call-envelope", data)

    def validate_call(self, data: Any) -> None:
        self.validate_call_envelope(data)
        call_type = data.get("call_type")
        if not isinstance(call_type, str):
            raise SchemaValidationError(
                "call-envelope",
                [
                    ValidationIssue(
                        path="call_type",
                        message="Missing or invalid call_type for call dispatch",
                        validator="dispatch",
                    )
                ],
            )
        schema_id = self._call_schema_id_by_type.get(call_type)
        if not schema_id:
            raise SchemaRegistryError(f"Unknown call_type '{call_type}'")
        self.validate_object(call_type, data)

    def validate_event(self, data: Any) -> None:
        self.validate_object("event-object", data)
        event_type = data.get("event_type")
        if not isinstance(event_type, str):
            raise SchemaValidationError(
                "event-object",
                [
                    ValidationIssue(
                        path="event_type",
                        message="Missing or invalid event_type for event dispatch",
                        validator="dispatch",
                    )
                ],
            )
        schema_id = self._event_schema_id_by_type.get(event_type)
        if not schema_id:
            raise SchemaRegistryError(f"Unknown event_type '{event_type}'")
        self.validate_object(event_type, data)


@lru_cache(maxsize=1)
def load_schema_registry(schema_root: Path | None = None) -> GarageSchemaRegistry:
    """Load the local Garage schema registry once."""

    return GarageSchemaRegistry(schema_root or SCHEMA_ROOT)


def validate_call_envelope(data: Any) -> None:
    """Validate only the shared call-envelope shape."""

    load_schema_registry().validate_call_envelope(data)


def validate_call(data: Any) -> None:
    """Validate a call envelope and dispatch to the concrete call schema."""

    load_schema_registry().validate_call(data)


def validate_event(data: Any) -> None:
    """Validate an event object and dispatch to the concrete event schema."""

    load_schema_registry().validate_event(data)


def validate_object(schema_name: str, data: Any) -> None:
    """Validate a shared or persisted object by explicit schema name."""

    load_schema_registry().validate_object(schema_name, data)
