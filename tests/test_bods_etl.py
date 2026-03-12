from pathlib import Path

from scripts.bods_utils import parse_xml_bytes
from scripts.build_reliability_metrics import build_metrics, load_route_code_map, parse_siri_vm_records
from scripts.fetch_bods_timetables import build_processed_outputs


TIMETABLE_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<TransXChange xmlns="http://www.transxchange.org.uk/">
  <Operators>
    <Operator id="OP1">
      <NationalOperatorCode>LDS1</NationalOperatorCode>
      <OperatorShortName>Leeds City Buses</OperatorShortName>
    </Operator>
  </Operators>
  <StopPoints>
    <AnnotatedStopPointRef>
      <StopPointRef>STOP100</StopPointRef>
      <CommonName>Leeds Station</CommonName>
      <LocalityName>Leeds</LocalityName>
      <Location>
        <Translation>
          <Latitude>53.794</Latitude>
          <Longitude>-1.548</Longitude>
        </Translation>
      </Location>
    </AnnotatedStopPointRef>
    <AnnotatedStopPointRef>
      <StopPointRef>STOP200</StopPointRef>
      <CommonName>Headingley Arndale</CommonName>
      <LocalityName>Headingley</LocalityName>
      <Location>
        <Translation>
          <Latitude>53.819</Latitude>
          <Longitude>-1.579</Longitude>
        </Translation>
      </Location>
    </AnnotatedStopPointRef>
  </StopPoints>
  <Services>
    <Service>
      <ServiceCode>SC1</ServiceCode>
      <RegisteredOperatorRef>OP1</RegisteredOperatorRef>
      <Lines>
        <Line id="L1">
          <LineName>1</LineName>
        </Line>
      </Lines>
      <Description>City Centre to Headingley</Description>
      <StandardService>
        <Origin>Leeds City Centre</Origin>
        <Destination>Headingley</Destination>
        <JourneyPattern id="JP1">
          <JourneyPatternSectionRefs>JPS1</JourneyPatternSectionRefs>
        </JourneyPattern>
      </StandardService>
    </Service>
  </Services>
  <JourneyPatternSections>
    <JourneyPatternSection id="JPS1">
      <JourneyPatternTimingLink id="TL1">
        <From>
          <StopPointRef>STOP100</StopPointRef>
        </From>
        <To>
          <StopPointRef>STOP200</StopPointRef>
        </To>
      </JourneyPatternTimingLink>
    </JourneyPatternSection>
  </JourneyPatternSections>
</TransXChange>
"""

SIRI_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<Siri xmlns="http://www.siri.org.uk/siri">
  <ServiceDelivery>
    <VehicleMonitoringDelivery>
      <VehicleActivity>
        <RecordedAtTime>2026-03-01T08:15:00Z</RecordedAtTime>
        <MonitoredVehicleJourney>
          <PublishedLineName>1</PublishedLineName>
          <LineRef>1</LineRef>
          <Delay>PT4M</Delay>
          <VehicleStatus>inProgress</VehicleStatus>
        </MonitoredVehicleJourney>
      </VehicleActivity>
      <VehicleActivity>
        <RecordedAtTime>2026-03-01T08:45:00Z</RecordedAtTime>
        <MonitoredVehicleJourney>
          <PublishedLineName>1</PublishedLineName>
          <LineRef>1</LineRef>
          <Delay>PT7M</Delay>
          <VehicleStatus>inProgress</VehicleStatus>
        </MonitoredVehicleJourney>
      </VehicleActivity>
    </VehicleMonitoringDelivery>
  </ServiceDelivery>
</Siri>
"""


def test_build_processed_outputs_from_transxchange(tmp_path: Path):
    root = parse_xml_bytes(TIMETABLE_XML)
    build_processed_outputs([root], tmp_path)

    operators = (tmp_path / "operators.csv").read_text(encoding="utf-8")
    routes = (tmp_path / "routes.csv").read_text(encoding="utf-8")
    stops = (tmp_path / "stops.csv").read_text(encoding="utf-8")
    route_stops = (tmp_path / "route_stops.csv").read_text(encoding="utf-8")

    assert "Leeds City Buses" in operators
    assert "City Centre to Headingley" in routes
    assert "Leeds Station" in stops
    assert "1,1,1" in route_stops
    assert "1,2,2" in route_stops


def test_build_metrics_from_siri_vm_xml(tmp_path: Path):
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(parents=True)
    (processed_dir / "routes.csv").write_text(
        "id,operator_id,route_code,route_name,origin,destination\n1,1,1,Route 1,A,B\n",
        encoding="utf-8",
    )

    records = parse_siri_vm_records(parse_xml_bytes(SIRI_XML))
    route_code_map = load_route_code_map(processed_dir)
    metrics = build_metrics(records, route_code_map)

    assert len(metrics) == 1
    assert metrics[0]["route_id"] == "1"
    assert metrics[0]["avg_delay_minutes"] == 5.5
    assert metrics[0]["on_time_rate"] == 0.5
    assert metrics[0]["observation_count"] == 2
