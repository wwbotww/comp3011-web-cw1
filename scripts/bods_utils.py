from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Optional
from xml.etree import ElementTree as ET


HTTP_FILE_PATTERN = re.compile(r"^https?://", re.IGNORECASE)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def iter_local(root: ET.Element, element_name: str) -> Iterable[ET.Element]:
    for element in root.iter():
        if local_name(element.tag) == element_name:
            yield element


def first_child(root: ET.Element, element_name: str) -> Optional[ET.Element]:
    for child in list(root):
        if local_name(child.tag) == element_name:
            return child
    return None


def first_child_text(root: ET.Element, *element_names: str) -> Optional[str]:
    for name in element_names:
        child = first_child(root, name)
        if child is not None and child.text and child.text.strip():
            return child.text.strip()
    return None


def descendant_text(root: ET.Element, *element_names: str) -> Optional[str]:
    target_names = set(element_names)
    for element in root.iter():
        if local_name(element.tag) in target_names and element.text and element.text.strip():
            return element.text.strip()
    return None


def split_refs(raw_value: Optional[str]) -> list[str]:
    if not raw_value:
        return []
    return [part.strip() for part in re.split(r"[\s,]+", raw_value) if part.strip()]


def safe_float(raw_value: Optional[str]) -> Optional[float]:
    if raw_value in (None, ""):
        return None
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return None


def normalise_text(raw_value: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (raw_value or "").strip())


def normalise_route_code(*values: Optional[str]) -> str:
    for value in values:
        text = normalise_text(value)
        if text:
            return text
    return ""


def parse_xml_bytes(payload: bytes) -> ET.Element:
    return ET.fromstring(payload)


def is_probable_data_url(candidate: str) -> bool:
    lower = candidate.lower()
    if not HTTP_FILE_PATTERN.match(candidate):
        return False
    disallowed_suffixes = (".json",)
    if lower.endswith(disallowed_suffixes):
        return False
    return any(token in lower for token in ("download", ".zip", ".xml", ".txc", "/api/v1/dataset/", "/api/v1/datafeed/"))


def parse_iso8601_duration_to_minutes(raw_value: Optional[str]) -> float:
    if not raw_value:
        return 0.0

    sign = -1 if raw_value.startswith("-") else 1
    value = raw_value[1:] if sign == -1 else raw_value
    match = re.fullmatch(
        r"P(?:T(?:(?P<hours>\d+(?:\.\d+)?)H)?(?:(?P<minutes>\d+(?:\.\d+)?)M)?(?:(?P<seconds>\d+(?:\.\d+)?)S)?)",
        value,
    )
    if not match:
        return 0.0

    hours = float(match.group("hours") or 0.0)
    minutes = float(match.group("minutes") or 0.0)
    seconds = float(match.group("seconds") or 0.0)
    total_minutes = hours * 60 + minutes + (seconds / 60)
    return round(sign * total_minutes, 2)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
