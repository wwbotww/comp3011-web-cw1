from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
import sys

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings

BODS_VEHICLE_URL = "https://data.bus-data.dft.gov.uk/api/v1/datafeed/"


def infer_extension(content_type: str) -> str:
    lowered = content_type.lower()
    if "xml" in lowered or "text/plain" in lowered:
        return ".xml"
    if "json" in lowered:
        return ".json"
    return ".bin"


def clear_directory_files(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for path in directory.iterdir():
        if path.is_file() and path.name != ".gitkeep":
            path.unlink()


def load_operator_ref() -> str:
    operators_path = settings.data_root / "processed" / "operators.csv"
    if not operators_path.exists():
        raise RuntimeError("operators.csv must exist before fetching vehicle snapshots.")

    with operators_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        first_row = next(reader, None)

    if not first_row or not first_row.get("noc"):
        raise RuntimeError("No operator NOC found in operators.csv.")
    return first_row["noc"]


def fetch_vehicle_snapshot() -> tuple[bytes, str]:
    if not settings.bods_api_key:
        raise RuntimeError("BODS_API_KEY is required to fetch vehicle snapshots.")

    operator_ref = load_operator_ref()

    response = requests.get(
        BODS_VEHICLE_URL,
        params={"api_key": settings.bods_api_key, "operatorRef": operator_ref},
        timeout=30,
    )
    response.raise_for_status()
    return response.content, response.headers.get("Content-Type", "")


def main() -> None:
    raw_dir = settings.data_root / "raw" / "bods_vehicle_snapshots"
    clear_directory_files(raw_dir)

    try:
        payload, content_type = fetch_vehicle_snapshot()
    except Exception as exc:  # pragma: no cover - script side effect
        print(f"Skipping vehicle snapshot fetch: {exc}")
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = raw_dir / f"{timestamp}{infer_extension(content_type)}"
    output_path.write_bytes(payload)
    print(f"Saved vehicle snapshot to {output_path}")


if __name__ == "__main__":
    main()
