"""The `json_schema` scorer: the reply must be JSON that fits a JSON Schema (Draft 2020-12).

Structured replies break in two ways: the JSON does not parse, or it parses but has the
wrong shape. This scorer reports which one, and where. The schema is resolved and checked
once at load time, so a typo in a schema file stops the suite before any paid call.
"""

from __future__ import annotations

import builtins
import json
import re
from pathlib import Path
from typing import Any, ClassVar, cast

import yaml
from jsonschema import Draft202012Validator, SchemaError
from pydantic import BaseModel, ConfigDict, Field

from casegate.models import Case, Output, Score
from casegate.scorers.base import DeterministicScorer, ScoreContext, from_expected

_FENCE = re.compile(r"```[A-Za-z0-9_-]*[ \t]*\r?\n(.*?)```", re.S)


class JsonSchemaParams(BaseModel):
    # A field named `schema` would shadow BaseModel.schema (FACTS §7); the YAML key stays `schema`.
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    schema_: dict[str, Any] | None = Field(default=None, alias="schema")
    schema_path: str | None = None


def _load_schema_file(raw_path: str, suite_root: Path) -> tuple[Any, list[str]]:
    path = suite_root / raw_path
    if path.suffix not in (".json", ".yaml", ".yml"):
        return None, [f"json_schema: schema_path must end in .json, .yaml or .yml: {raw_path}"]
    if not path.is_file():
        return None, [f"json_schema: schema_path not found: {raw_path}"]
    try:
        text = path.read_text(encoding="utf-8")
        loaded = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    except (ValueError, yaml.YAMLError) as exc:
        return None, [f"json_schema: cannot parse {raw_path}: {exc}"]
    return loaded, []


def _resolve_schema(case: Case, p: JsonSchemaParams, suite_root: Path) -> tuple[Any, list[str]]:
    if p.schema_ is not None and p.schema_path is not None:
        return None, ["json_schema: schema and schema_path are mutually exclusive"]
    if p.schema_ is not None:
        return p.schema_, []
    if p.schema_path is not None:
        return _load_schema_file(p.schema_path, suite_root)
    value, errors = from_expected(JsonSchemaParams, case, "schema", "schema", attr="schema_")
    if errors:
        return None, errors
    if value is None:
        return None, ["json_schema: needs schema, schema_path or expected.schema"]
    return value, []


def extract_json_text(text: str) -> str:
    """Use the first fenced block if the reply has one; models often wrap JSON in ```json."""
    m = _FENCE.search(text)
    return m.group(1) if m else text.strip()


class JsonSchemaScorer(DeterministicScorer):
    type: ClassVar[str] = "json_schema"
    Params: ClassVar[builtins.type[BaseModel]] = JsonSchemaParams

    @classmethod
    def check(cls, case: Case, params: BaseModel, suite_root: Path) -> list[str]:
        p = cast(JsonSchemaParams, params)
        schema, errors = _resolve_schema(case, p, suite_root)
        if errors:
            return errors
        if not isinstance(schema, dict):
            return ["json_schema: schema must be an object"]
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            return [f"json_schema: invalid schema: {exc.message}"]
        # score() reads only schema_, whatever the source was.
        p.schema_ = schema
        return []

    async def score(self, case: Case, output: Output, ctx: ScoreContext) -> Score:
        schema = cast(JsonSchemaParams, self.params).schema_
        if schema is None:
            raise ValueError("json_schema: schema not resolved; build the scorer with check()")
        try:
            doc = json.loads(extract_json_text(output.text))
        except json.JSONDecodeError as exc:
            return self.make_score(0.0, f"invalid JSON: {exc}")
        errors = list(Draft202012Validator(schema).iter_errors(doc))
        if not errors:
            return self.make_score(1.0, None)
        first = min(
            errors,
            key=lambda e: (len(e.absolute_path), [str(p) for p in e.absolute_path], e.message),
        )
        where = "$" + "".join(f".{p}" for p in first.absolute_path)
        return self.make_score(0.0, f"{where}: {first.message}")
