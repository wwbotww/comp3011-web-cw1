from __future__ import annotations

import csv
import json
import sys
import zipfile
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from scripts.bods_utils import (
    descendant_text,
    ensure_parent,
    first_child_text,
    is_probable_data_url,
    iter_local,
    local_name,
    normalise_route_code,
    normalise_text,
    parse_xml_bytes,
    safe_float,
    split_refs,
)

BODS_TIMETABLE_URL = "https://data.bus-data.dft.gov.uk/api/v1/dataset/"
LEEDS_ADMIN_AREA = "450"


def next_id(sequence: list[dict]) -> int:
    return len(sequence) + 1


def clear_directory_files(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for path in directory.iterdir():
        if path.is_file() and path.name != ".gitkeep":
            path.unlink()


def dataset_priority(record: dict) -> tuple:
    preferred = settings.bods_preferred_locality.lower().strip()
    localities = record.get("localities") or []
    locality_names = [
        normalise_text(item.get("name"))
        for item in localities
        if isinstance(item, dict) and item.get("name")
    ]
    text_blob = " ".join(
        [
            normalise_text(record.get("operatorName")),
            normalise_text(record.get("name")),
            normalise_text(record.get("description")),
            " ".join(locality_names),
        ]
    ).lower()

    has_preferred_locality = preferred in text_blob
    has_leeds_noc = "flds" in [str(noc).lower() for noc in (record.get("noc") or [])]
    line_count = len(record.get("lines") or [])
    modified = record.get("modified") or ""
    dataset_id = int(record.get("id") or 0)
    # Sort by most Leeds-like first, then smaller datasets first, then newest, then id.
    return (
        0 if has_preferred_locality else 1,
        0 if has_leeds_noc else 1,
        line_count,
        modified,
        dataset_id,
    )


def select_demo_datasets(records: list[dict]) -> list[dict]:
    sorted_records = sorted(records, key=dataset_priority)
    preferred = settings.bods_preferred_locality.lower().strip()

    strict_matches = []
    fallback_matches = []
    for record in sorted_records:
        localities = record.get("localities") or []
        locality_names = [
            normalise_text(item.get("name"))
            for item in localities
            if isinstance(item, dict) and item.get("name")
        ]
        text_blob = " ".join(
            [
                normalise_text(record.get("operatorName")),
                normalise_text(record.get("name")),
                normalise_text(record.get("description")),
                " ".join(locality_names),
            ]
        ).lower()
        if preferred in text_blob:
            strict_matches.append(record)
        else:
            fallback_matches.append(record)

    chosen_pool = strict_matches or fallback_matches
    return chosen_pool[: settings.bods_max_datasets]


def ensure_processed_templates(processed_dir: Path) -> None:
    processed_dir.mkdir(parents=True, exist_ok=True)
    templates = {
        "operators.csv": ["id", "noc", "name", "region"],
        "routes.csv": ["id", "operator_id", "route_code", "route_name", "origin", "destination"],
        "stops.csv": ["id", "stop_code", "stop_name", "locality", "latitude", "longitude"],
        "route_stops.csv": ["route_id", "stop_id", "stop_sequence"],
    }
    for filename, headers in templates.items():
        path = processed_dir / filename
        if path.exists():
            continue
        with path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers)


def fetch_timetable_metadata() -> list[dict]:
    if not settings.bods_api_key:
        raise RuntimeError("BODS_API_KEY is required to fetch timetable metadata.")

    session = requests.Session()
    url: Optional[str] = BODS_TIMETABLE_URL
    params: Optional[dict] = {
        "api_key": settings.bods_api_key,
        "adminArea": LEEDS_ADMIN_AREA,
        "limit": 100,
        "status": "published",
    }
    results: list[dict] = []

    while url:
        response = session.get(url, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()

        if isinstance(payload, dict) and isinstance(payload.get("results"), list):
            results.extend(item for item in payload["results"] if isinstance(item, dict))
            url = payload.get("next")
            params = None
        elif isinstance(payload, list):
            results.extend(item for item in payload if isinstance(item, dict))
            break
        else:
            break

    return results


def discover_candidate_urls(value: object) -> list[str]:
    discovered: list[str] = []

    def _walk(item: object) -> None:
        if isinstance(item, dict):
            for key, nested in item.items():
                key_lower = key.lower()
                if isinstance(nested, str) and is_probable_data_url(nested):
                    if any(token in key_lower for token in ("url", "download", "file", "xml", "zip")):
                        discovered.append(nested)
                else:
                    _walk(nested)
        elif isinstance(item, list):
            for nested in item:
                _walk(nested)
        elif isinstance(item, str) and is_probable_data_url(item):
            discovered.append(item)

    _walk(value)
    # Keep order stable while removing duplicates.
    seen: set[str] = set()
    output: list[str] = []
    for url in discovered:
        if url not in seen:
            output.append(url)
            seen.add(url)
    return output


def download_dataset_files(metadata_records: list[dict], raw_dir: Path) -> list[Path]:
    if not settings.bods_api_key:
        raise RuntimeError("BODS_API_KEY is required to download timetable files.")

    session = requests.Session()
    downloaded: list[Path] = []
    visited_urls: set[str] = set()

    def _download(url: str, dataset_prefix: str) -> None:
        if url in visited_urls:
            return
        visited_urls.add(url)

        response = session.get(url, params={"api_key": settings.bods_api_key}, timeout=60)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()
        parsed = urlparse(response.url)
        suffix = Path(parsed.path).suffix.lower()

        if "application/json" in content_type or suffix == ".json":
            try:
                payload = response.json()
            except ValueError:
                return
            for candidate in discover_candidate_urls(payload):
                _download(candidate, dataset_prefix)
            return

        if suffix not in {".zip", ".xml"}:
            if "zip" in content_type:
                suffix = ".zip"
            elif "xml" in content_type or "text/plain" in content_type or "octet-stream" in content_type:
                suffix = ".xml"
            else:
                return

        base_name = Path(parsed.path).name or "dataset"
        if Path(base_name).suffix.lower() != suffix:
            base_name = f"{base_name}{suffix}"
        filename = f"{dataset_prefix}_{base_name}"
        output_path = raw_dir / filename
        ensure_parent(output_path)
        output_path.write_bytes(response.content)
        downloaded.append(output_path)

    for index, record in enumerate(metadata_records, start=1):
        dataset_prefix = f"dataset_{record.get('id', index)}"
        for candidate in discover_candidate_urls(record):
            _download(candidate, dataset_prefix)

    return downloaded


def extract_xml_roots(raw_dir: Path) -> list[ET.Element]:
    roots: list[ET.Element] = []
    for path in sorted(raw_dir.glob("*")):
        if path.suffix.lower() == ".xml":
            roots.append(parse_xml_bytes(path.read_bytes()))
        elif path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as archive:
                xml_members = [member for member in archive.namelist() if member.lower().endswith(".xml")]
                for member in xml_members[: settings.bods_max_xml_files_per_dataset]:
                    if member.lower().endswith(".xml"):
                        roots.append(parse_xml_bytes(archive.read(member)))
    return roots


def build_journey_pattern_map(root: ET.Element) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    for section in iter_local(root, "JourneyPatternSection"):
        section_id = section.attrib.get("id") or section.attrib.get("ID")
        if not section_id:
            continue
        ordered_stops: list[str] = []
        for link in list(section):
            if local_name(link.tag) != "JourneyPatternTimingLink":
                continue
            from_element = next((child for child in list(link) if local_name(child.tag) == "From"), None)
            to_element = next((child for child in list(link) if local_name(child.tag) == "To"), None)
            from_ref = descendant_text(from_element, "StopPointRef") if from_element is not None else None
            to_ref = descendant_text(to_element, "StopPointRef") if to_element is not None else None
            if from_ref and not ordered_stops:
                ordered_stops.append(from_ref)
            elif from_ref and ordered_stops and ordered_stops[-1] != from_ref and from_ref not in ordered_stops:
                ordered_stops.append(from_ref)
            if to_ref and (not ordered_stops or ordered_stops[-1] != to_ref):
                ordered_stops.append(to_ref)
        if ordered_stops:
            sections[section_id] = ordered_stops
    return sections


def parse_stop_catalogue(root: ET.Element) -> dict[str, dict]:
    stop_catalogue: dict[str, dict] = {}
    for stop in iter_local(root, "AnnotatedStopPointRef"):
        stop_code = first_child_text(stop, "StopPointRef")
        if not stop_code:
            continue
        if stop_code not in stop_catalogue:
            stop_catalogue[stop_code] = {
                "stop_code": stop_code,
                "stop_name": normalise_text(first_child_text(stop, "CommonName")) or stop_code,
                "locality": normalise_text(first_child_text(stop, "LocalityName")) or None,
                "latitude": safe_float(descendant_text(stop, "Latitude")),
                "longitude": safe_float(descendant_text(stop, "Longitude")),
            }
    return stop_catalogue


def parse_operators(root: ET.Element, metadata_record: Optional[dict] = None) -> dict[str, dict]:
    operators: dict[str, dict] = {}
    for operator in iter_local(root, "Operator"):
        operator_id = operator.attrib.get("id") or operator.attrib.get("ID") or ""
        noc = first_child_text(operator, "NationalOperatorCode", "OperatorCode") or operator_id
        name = normalise_text(
            first_child_text(operator, "TradingName", "OperatorShortName", "OperatorName")
        ) or normalise_text(metadata_record.get("operator_name") if metadata_record else None)
        if not noc or not name:
            continue
        operators[operator_id or noc] = {"noc": noc, "name": name, "region": "Leeds"}

    if not operators and metadata_record:
        noc = normalise_text(metadata_record.get("noc") or metadata_record.get("operator_noc"))
        name = normalise_text(metadata_record.get("operator_name") or metadata_record.get("operator"))
        if noc and name:
            operators[noc] = {"noc": noc, "name": name, "region": "Leeds"}

    return operators


def parse_services(
    root: ET.Element,
    operator_by_ref: dict[str, dict],
    stop_catalogue: dict[str, dict],
) -> list[dict]:
    journey_sections = build_journey_pattern_map(root)
    services: list[dict] = []

    for service in iter_local(root, "Service"):
        service_code = normalise_text(first_child_text(service, "ServiceCode"))
        line_name = ""
        lines = next((child for child in list(service) if local_name(child.tag) == "Lines"), None)
        if lines is not None:
            line = next((child for child in lines.iter() if local_name(child.tag) == "Line"), None)
            if line is not None:
                line_name = normalise_route_code(first_child_text(line, "LineName"), first_child_text(line, "LineRef"))

        standard_service = next((child for child in service.iter() if local_name(child.tag) == "StandardService"), None)
        origin = normalise_text(first_child_text(standard_service, "Origin")) if standard_service is not None else ""
        destination = normalise_text(first_child_text(standard_service, "Destination")) if standard_service is not None else ""
        route_name = normalise_text(first_child_text(service, "Description")) or line_name or service_code

        operator_ref = descendant_text(service, "RegisteredOperatorRef", "OperatorRef")
        operator = operator_by_ref.get(operator_ref or "", next(iter(operator_by_ref.values()), None))
        if operator is None:
            continue

        stop_refs: list[str] = []
        if standard_service is not None:
            for journey_pattern in standard_service.iter():
                if local_name(journey_pattern.tag) != "JourneyPattern":
                    continue
                for ref in split_refs(first_child_text(journey_pattern, "JourneyPatternSectionRefs")):
                    for stop_ref in journey_sections.get(ref, []):
                        if stop_ref not in stop_refs:
                            stop_refs.append(stop_ref)

        if not stop_refs:
            for stop_ref in stop_catalogue:
                if stop_ref not in stop_refs:
                    stop_refs.append(stop_ref)

        services.append(
            {
                "service_code": service_code,
                "route_code": line_name or service_code,
                "route_name": route_name,
                "origin": origin or None,
                "destination": destination or None,
                "operator_noc": operator["noc"],
                "stop_refs": [stop_ref for stop_ref in stop_refs if stop_ref in stop_catalogue],
            }
        )

    return services


def write_csv(path: Path, headers: list[str], rows: list[dict]) -> None:
    ensure_parent(path)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def build_processed_outputs(roots: list[ET.Element], processed_dir: Path) -> None:
    operator_rows: list[dict] = []
    route_rows: list[dict] = []
    stop_rows: list[dict] = []
    route_stop_rows: list[dict] = []

    operator_ids: dict[str, int] = {}
    route_ids: dict[tuple[str, str, str, str], int] = {}
    stop_ids: dict[str, int] = {}

    for root in roots:
        stop_catalogue = parse_stop_catalogue(root)
        parsed_operators = parse_operators(root)

        for operator_ref, operator in parsed_operators.items():
            if operator["noc"] not in operator_ids:
                operator_id = next_id(operator_rows)
                operator_ids[operator["noc"]] = operator_id
                operator_rows.append(
                    {
                        "id": operator_id,
                        "noc": operator["noc"],
                        "name": operator["name"],
                        "region": operator["region"],
                    }
                )
            parsed_operators[operator_ref]["id"] = operator_ids[operator["noc"]]

        for stop_code, stop in stop_catalogue.items():
            if stop_code not in stop_ids:
                stop_id = next_id(stop_rows)
                stop_ids[stop_code] = stop_id
                stop_rows.append(
                    {
                        "id": stop_id,
                        "stop_code": stop_code,
                        "stop_name": stop["stop_name"],
                        "locality": stop["locality"] or "",
                        "latitude": stop["latitude"] if stop["latitude"] is not None else "",
                        "longitude": stop["longitude"] if stop["longitude"] is not None else "",
                    }
                )

        for service in parse_services(root, parsed_operators, stop_catalogue):
            operator_id = operator_ids.get(service["operator_noc"])
            if operator_id is None or not service["route_code"]:
                continue
            route_key = (
                service["operator_noc"],
                service["route_code"],
                service["origin"] or "",
                service["destination"] or "",
            )
            if route_key not in route_ids:
                route_id = next_id(route_rows)
                route_ids[route_key] = route_id
                route_rows.append(
                    {
                        "id": route_id,
                        "operator_id": operator_id,
                        "route_code": service["route_code"],
                        "route_name": service["route_name"],
                        "origin": service["origin"] or "",
                        "destination": service["destination"] or "",
                    }
                )
            route_id = route_ids[route_key]
            for index, stop_ref in enumerate(service["stop_refs"], start=1):
                stop_id = stop_ids.get(stop_ref)
                if stop_id is None:
                    continue
                route_stop_record = {
                    "route_id": route_id,
                    "stop_id": stop_id,
                    "stop_sequence": index,
                }
                if route_stop_record not in route_stop_rows:
                    route_stop_rows.append(route_stop_record)

    write_csv(processed_dir / "operators.csv", ["id", "noc", "name", "region"], operator_rows)
    write_csv(
        processed_dir / "routes.csv",
        ["id", "operator_id", "route_code", "route_name", "origin", "destination"],
        route_rows,
    )
    write_csv(
        processed_dir / "stops.csv",
        ["id", "stop_code", "stop_name", "locality", "latitude", "longitude"],
        stop_rows,
    )
    write_csv(processed_dir / "route_stops.csv", ["route_id", "stop_id", "stop_sequence"], route_stop_rows)


def main() -> None:
    raw_dir = settings.data_root / "raw" / "bods_timetables"
    processed_dir = settings.data_root / "processed"
    clear_directory_files(raw_dir)
    clear_directory_files(processed_dir)
    ensure_processed_templates(processed_dir)

    try:
        metadata_records = fetch_timetable_metadata()
    except Exception as exc:  # pragma: no cover - script side effect
        print(f"Skipping BODS fetch: {exc}")
        return

    selected_records = select_demo_datasets(metadata_records)
    output_path = raw_dir / "datasets.json"
    output_path.write_text(json.dumps(selected_records, indent=2), encoding="utf-8")
    downloaded_files = download_dataset_files(selected_records, raw_dir)
    roots = extract_xml_roots(raw_dir)
    build_processed_outputs(roots, processed_dir)
    print(f"Saved timetable metadata to {output_path}")
    print(f"Selected {len(selected_records)} datasets for demo mode.")
    print(f"Downloaded {len(downloaded_files)} timetable files and processed {len(roots)} XML documents.")


if __name__ == "__main__":
    main()
