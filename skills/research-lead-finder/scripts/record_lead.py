#!/usr/bin/env python3
"""Validate a research lead against lead-schema.json and append it to the archive.

This is the deterministic spine of research-lead-finder. It does NOT judge whether
a lead is good, relevant, or truly grounded -- those are agent decisions made under
SKILL.md. It enforces the structural contract only: required fields, types, enums,
non-empty strings, at least one source, a verbatim supporting quote per source, and
an honest grounding block. A lead that fails is rejected (exit 1); fix it or drop it.

Known limit (MVP): this checks that a supporting_quote EXISTS and is attributed. It
does not verify the quote actually appears in the source abstract. That semantic check
is the v1 grounding-check module. The obvious first hardening is to pass retrieved
abstracts in and assert each supporting_quote is a substring of its source text.

Usage:
  python3 record_lead.py --lead lead.json --archive "$HERMES_HOME/data/research-leads.jsonl"
  cat lead.json | python3 record_lead.py --lead - --archive PATH
  python3 record_lead.py --lead lead.json --validate-only
Schema defaults to ../references/lead-schema.json relative to this script.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SCHEMA = os.path.join(SCRIPT_DIR, "..", "references", "lead-schema.json")


def normalize_claim(text):
    return re.sub(r"\s+", " ", text.strip().lower())


def claim_id(text):
    return hashlib.sha1(normalize_claim(text).encode("utf-8")).hexdigest()


def validate(node, schema, path="lead"):
    """Minimal recursive validator for the JSON Schema subset used by lead-schema.json.
    Supports: type, required, properties, additionalProperties:false, enum, minItems,
    minLength, items. Returns a list of error strings (empty == valid)."""
    errors = []
    t = schema.get("type")
    type_map = {
        "object": dict, "array": list, "string": str,
        "boolean": bool, "number": (int, float), "integer": int,
    }
    if t:
        expected = type_map[t]
        # bool is a subclass of int; guard so a bool never satisfies number/integer
        if t in ("number", "integer") and isinstance(node, bool):
            errors.append(f"{path}: expected {t}, got boolean")
            return errors
        if not isinstance(node, expected):
            errors.append(f"{path}: expected {t}, got {type(node).__name__}")
            return errors

    if "enum" in schema and node not in schema["enum"]:
        errors.append(f"{path}: '{node}' not in allowed {schema['enum']}")

    if t == "string" and "minLength" in schema:
        if len(node.strip()) < schema["minLength"]:
            errors.append(f"{path}: must be a non-empty string")

    if t == "object":
        for key in schema.get("required", []):
            if key not in node:
                errors.append(f"{path}: missing required field '{key}'")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in node:
                if key not in props:
                    errors.append(f"{path}: unexpected field '{key}'")
        for key, subschema in props.items():
            if key in node:
                errors.extend(validate(node[key], subschema, f"{path}.{key}"))

    if t == "array":
        if "minItems" in schema and len(node) < schema["minItems"]:
            errors.append(f"{path}: needs at least {schema['minItems']} item(s)")
        item_schema = schema.get("items")
        if item_schema:
            for i, item in enumerate(node):
                errors.extend(validate(item, item_schema, f"{path}[{i}]"))

    return errors


def load_lead(arg):
    raw = sys.stdin.read() if arg == "-" else open(arg, encoding="utf-8").read()
    return json.loads(raw)


def archive_ids(archive_path):
    ids = set()
    if not os.path.exists(archive_path):
        return ids
    with open(archive_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                ids.add(json.loads(line)["id"])
            except (json.JSONDecodeError, KeyError):
                continue
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lead", required=True, help="path to lead JSON, or - for stdin")
    ap.add_argument("--archive", help="path to JSONL archive (env vars expanded)")
    ap.add_argument("--schema", default=DEFAULT_SCHEMA)
    ap.add_argument("--validate-only", action="store_true")
    args = ap.parse_args()

    if not args.validate_only and not args.archive:
        print("FAIL: --archive is required unless --validate-only", file=sys.stderr)
        return 1

    try:
        lead = load_lead(args.lead)
    except (OSError, json.JSONDecodeError) as e:
        print(f"FAIL: could not read lead: {e}", file=sys.stderr)
        return 1

    schema = json.load(open(args.schema, encoding="utf-8"))

    # Fill server-derivable fields so the agent need not compute them by hand.
    if "claim" in lead and isinstance(lead["claim"], str) and not lead.get("id"):
        lead["id"] = claim_id(lead["claim"])
    lead.setdefault("created_at", datetime.now(timezone.utc).isoformat())

    errors = validate(lead, schema)
    if errors:
        print("FAIL: lead does not satisfy the contract:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    if args.validate_only:
        print(f"PASS: lead {lead['id'][:10]} is valid (not written)")
        return 0

    archive_path = os.path.expanduser(os.path.expandvars(args.archive))
    if lead["id"] in archive_ids(archive_path):
        print(f"SKIP: lead {lead['id'][:10]} already in archive (duplicate id)")
        return 0

    os.makedirs(os.path.dirname(archive_path) or ".", exist_ok=True)
    with open(archive_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(lead, ensure_ascii=False) + "\n")
    print(f"PASS: lead {lead['id'][:10]} appended to {archive_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
