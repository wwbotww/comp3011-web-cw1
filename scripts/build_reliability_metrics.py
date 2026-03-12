from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from scripts.bods_utils import (
    descendant_text,
    iter_local,
    normalise_route_code,
    parse_iso8601_duration_to_minutes,
    parse_xml_bytes,
)


def get_time_band(hour: int) -> str:
    if 7 <= hour < 10:
        return "morning_peak"
    if 10 <= hour < 16:
        return "midday"
    if 16 <= hour < 19:
        return "evening_peak"
    return "off_peak"


def load_snapshot_records(snapshot_dir: Path) -> list[dict]:
    records: list[dict] = []
    for path in sorted(snapshot_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            records.extend(item for item in payload if isinstance(item, dict))
        elif isinstance(payload, dict):
            candidate = payload.get("records") or payload.get("results") or payload.get("vehicles") or []
            if isinstance(candidate, list):
                records.extend(item for item in candidate if isinstance(item, dict))
    for path in sorted(snapshot_dir.glob("*.xml")):
        root = parse_xml_bytes(path.read_bytes())
        records.extend(parse_siri_vm_records(root))
    return records


def parse_siri_vm_records(root: ET.Element) -> list[dict]:
    records: list[dict] = []
    for activity in iter_local(root, "VehicleActivity"):
        monitored = next(iter_local(activity, "MonitoredVehicleJourney"), None)
        if monitored is None:
            continue

        recorded_at = descendant_text(activity, "RecordedAtTime", "ResponseTimestamp", "ValidUntilTime")
        route_code = normalise_route_code(
            descendant_text(monitored, "PublishedLineName"),
            descendant_text(monitored, "LineRef"),
        )
        if not route_code or not recorded_at:
            continue

        delay_value = descendant_text(monitored, "Delay")
        vehicle_status = descendant_text(monitored, "VehicleStatus", "ProgressStatus") or ""
        records.append(
            {
                "route_code": route_code,
                "timestamp": recorded_at,
                "delay_minutes": parse_iso8601_duration_to_minutes(delay_value),
                "cancelled": "cancel" in vehicle_status.lower(),
            }
        )
    return records


def load_route_code_map(processed_dir: Path) -> dict[str, int]:
    mapping: dict[str, int] = {}
    path = processed_dir / "routes.csv"
    if not path.exists():
        return mapping
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            route_code = normalise_route_code(row.get("route_code"))
            if route_code:
                mapping[route_code] = int(row["id"])
    return mapping


def build_metrics(records: list[dict], route_code_map: dict[str, int]) -> list[dict]:
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for record in records:
        raw_route_code = normalise_route_code(record.get("route_code"), record.get("route_id"), record.get("routeId"))
        route_id = route_code_map.get(raw_route_code)
        timestamp = record.get("timestamp") or record.get("recorded_at")
        if route_id is None or not timestamp:
            continue

        dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        key = (str(route_id), dt.date().isoformat(), get_time_band(dt.hour))
        grouped[key].append(record)

    output: list[dict] = []
    for (route_id, metric_date, time_band), items in grouped.items():
        delays = [float(item.get("delay_minutes", 0.0) or 0.0) for item in items]
        cancelled = [1 for item in items if bool(item.get("cancelled", False))]
        on_time = [1 for delay in delays if delay <= 5.0]
        count = len(items)
        output.append(
            {
                "id": len(output) + 1,
                "route_id": route_id,
                "metric_date": metric_date,
                "time_band": time_band,
                "avg_delay_minutes": round(sum(delays) / count, 2) if count else 0.0,
                "on_time_rate": round(sum(on_time) / count, 4) if count else 0.0,
                "cancellation_rate": round(sum(cancelled) / count, 4) if count else 0.0,
                "observation_count": count,
            }
        )
    return output


def write_metrics(path: Path, metrics: list[dict]) -> None:
    headers = [
        "id",
        "route_id",
        "metric_date",
        "time_band",
        "avg_delay_minutes",
        "on_time_rate",
        "cancellation_rate",
        "observation_count",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(metrics)


def main() -> None:
    snapshot_dir = settings.data_root / "raw" / "bods_vehicle_snapshots"
    processed_dir = settings.data_root / "processed"
    output_path = processed_dir / "reliability_metrics.csv"
    records = load_snapshot_records(snapshot_dir)
    route_code_map = load_route_code_map(processed_dir)
    write_metrics(output_path, build_metrics(records, route_code_map))
    print(f"Wrote reliability metrics to {output_path}")


if __name__ == "__main__":
    main()
