from __future__ import annotations

from datetime import datetime, timezone

import requests

from app.core.config import settings

BODS_VEHICLE_URL = "https://data.bus-data.dft.gov.uk/api/v1/datafeed/"
LEEDS_ADMIN_AREA = "450"


def infer_extension(content_type: str) -> str:
    lowered = content_type.lower()
    if "xml" in lowered or "text/plain" in lowered:
        return ".xml"
    if "json" in lowered:
        return ".json"
    return ".bin"


def fetch_vehicle_snapshot() -> tuple[bytes, str]:
    if not settings.bods_api_key:
        raise RuntimeError("BODS_API_KEY is required to fetch vehicle snapshots.")

    response = requests.get(
        BODS_VEHICLE_URL,
        params={"api_key": settings.bods_api_key, "adminArea": LEEDS_ADMIN_AREA},
        timeout=30,
    )
    response.raise_for_status()
    return response.content, response.headers.get("Content-Type", "")


def main() -> None:
    raw_dir = settings.data_root / "raw" / "bods_vehicle_snapshots"
    raw_dir.mkdir(parents=True, exist_ok=True)

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
