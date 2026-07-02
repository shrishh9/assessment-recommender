"""Catalog ingestion pipeline for SHL assessments.

This module loads the official SHL product catalog JSON, validates each record,
and writes a cleaned, retrieval-friendly catalog to data/assessments.json.

The implementation is intentionally simple and readable so it can be extended
later without changing the overall structure.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "data" / "assessments.json"
CATALOG_URL = "https://tcp-us-prod-rnd.shl.com/voiceRater/shl-ai-hiring/shl_product_catalog.json"


def _clean_text(value: Any) -> str:
    """Return a normalized string for scalar values."""

    if value is None:
        return ""
    if isinstance(value, str):
        cleaned = re.sub(r"[\x00-\x1f]+", " ", value)
        return cleaned.strip()
    return str(value).strip()


def _normalize_list(value: Any) -> List[str]:
    """Normalize lists and comma-separated strings into a list of strings."""

    if value is None:
        return []
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        parts = [part.strip() for part in value.split(",")]
        items = [part for part in parts if part]
    else:
        items = [value]

    return [_clean_text(item) for item in items if _clean_text(item)]


def is_valid_shl_product_url(url: str) -> bool:
    """Return True when a URL points to a valid SHL product catalog page."""

    if not url:
        return False

    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False

    host = parsed.netloc.lower()
    if "shl.com" not in host:
        return False

    path = parsed.path.lower()
    return "/products/product-catalog/view/" in path


def load_catalog_raw(url: str = CATALOG_URL) -> List[Dict[str, Any]]:
    """Fetch and parse the remote catalog JSON.

    The source payload appears to contain control characters in a few places, so
    we sanitize that before parsing to make the loader more robust.
    """

    with urlopen(url) as response:
        raw_text = response.read().decode("utf-8")

    cleaned_text = re.sub(r"[\x00-\x1f]+", " ", raw_text)
    parsed = json.loads(cleaned_text)

    if not isinstance(parsed, list):
        raise ValueError("Expected the catalog payload to be a JSON array.")

    return parsed


def normalize_record(raw_record: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Normalize one raw catalog record into a retrieval-friendly shape."""

    record = dict(raw_record) if isinstance(raw_record, dict) else {}

    name = _clean_text(record.get("name"))
    url = _clean_text(record.get("link")) or _clean_text(record.get("url"))
    entity_id = _clean_text(record.get("entity_id"))

    normalized = {
        "id": entity_id or f"assessment-{index}",
        "entity_id": entity_id,
        "name": name,
        "url": url,
        "description": _clean_text(record.get("description")),
        "test_type": _clean_text(record.get("test_type")) or _clean_text(record.get("type")),
        "job_levels": _normalize_list(record.get("job_levels")),
        "job_levels_raw": _clean_text(record.get("job_levels_raw")),
        "languages": _normalize_list(record.get("languages")),
        "languages_raw": _clean_text(record.get("languages_raw")),
        "duration": _clean_text(record.get("duration")),
        "duration_raw": _clean_text(record.get("duration_raw")),
        "status": _clean_text(record.get("status")),
        "adaptive": _clean_text(record.get("adaptive")),
        "remote": _clean_text(record.get("remote")),
        "scraped_at": _clean_text(record.get("scraped_at")),
        "keys": _normalize_list(record.get("keys")),
    }

    return normalized


def validate_record(record: Dict[str, Any]) -> List[str]:
    """Return a list of validation issues for a normalized record."""

    issues: List[str] = []
    required_fields = ["id", "name", "url"]
    for field in required_fields:
        if not record.get(field):
            issues.append(field)

    if record.get("url") and not is_valid_shl_product_url(record.get("url")):
        issues.append("invalid_url")

    return issues


def summarize_missing_fields(records: List[Dict[str, Any]]) -> Counter[str]:
    """Count empty values for key fields in the normalized catalog."""

    fields_to_check = ["name", "url", "description", "test_type", "job_levels", "languages", "duration", "status", "adaptive", "remote", "scraped_at"]
    missing_counter: Counter[str] = Counter()

    for record in records:
        for field in fields_to_check:
            value = record.get(field)
            if isinstance(value, list):
                is_missing = not value
            else:
                is_missing = not value
            if is_missing:
                missing_counter[field] += 1

    return missing_counter


def deduplicate_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicates by ID and then by URL when ID is missing."""

    seen: Dict[str, Dict[str, Any]] = {}
    duplicates_removed = 0

    for record in records:
        dedupe_key = record.get("id") or record.get("url") or ""
        if not dedupe_key:
            continue

        if dedupe_key in seen:
            duplicates_removed += 1
            continue

        seen[dedupe_key] = record

    return list(seen.values()), duplicates_removed


def write_catalog(records: List[Dict[str, Any]], output_path: Path = DATA_PATH) -> None:
    """Persist cleaned catalog to disk as JSON."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def build_catalog(url: str = CATALOG_URL, output_path: Path = DATA_PATH) -> Dict[str, Any]:
    """Build the cleaned catalog and return a summary of what happened."""

    raw_records = load_catalog_raw(url)
    normalized_records = [normalize_record(record, index) for index, record in enumerate(raw_records)]

    missing_fields_counter: Counter[str] = Counter()
    valid_records: List[Dict[str, Any]] = []
    invalid_url_count = 0

    for record in normalized_records:
        issues = validate_record(record)
        for field in issues:
            if field != "invalid_url":
                missing_fields_counter[field] += 1

        if "invalid_url" in issues:
            invalid_url_count += 1
            continue

        valid_records.append(record)

    missing_fields_counter.update(summarize_missing_fields(valid_records))

    deduped_records, duplicates_removed = deduplicate_records(valid_records)

    write_catalog(deduped_records, output_path)

    sample_records = deduped_records[:5]
    summary = {
        "total_records": len(raw_records),
        "records_written": len(deduped_records),
        "duplicates_removed": duplicates_removed,
        "invalid_url_records": invalid_url_count,
        "missing_fields": dict(missing_fields_counter),
        "sample_records": sample_records,
    }
    return summary


def print_summary(summary: Dict[str, Any]) -> None:
    """Print a human-readable validation summary."""

    print("Catalog ingestion summary")
    print(f"- total assessments: {summary['total_records']}")
    print(f"- duplicates removed: {summary['duplicates_removed']}")
    print(f"- records written: {summary['records_written']}")
    print(f"- invalid SHL URLs removed: {summary['invalid_url_records']}")
    print("- missing fields summary:")
    for field, count in summary["missing_fields"].items():
        print(f"  - {field}: {count}")
    print("- five sample records:")
    for record in summary["sample_records"]:
        print(json.dumps(record, indent=2, ensure_ascii=False))
        print("-" * 40)


if __name__ == "__main__":
    summary = build_catalog()
    print_summary(summary)
