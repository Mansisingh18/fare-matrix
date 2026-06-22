"""
Acerooms B2B hotel search via their XML API.

Acerooms uses a SOAP/XML-over-HTTP interface for agent integrations.
Credentials (username + password) come from your agent account.

If Acerooms provides you with a different base URL or XML schema,
update BASE_URL and the _build_request / _parse_response functions below.
"""

import requests
import logging
import xml.etree.ElementTree as ET
from datetime import date, timedelta

logger = logging.getLogger(__name__)

BASE_URL = "https://xml.acerooms.com/api/hotel/search"


def _build_request(username: str, password: str, destination: str,
                   check_in: date, check_out: date, adults: int) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<OTA_HotelAvailRQ xmlns="http://www.opentravel.org/OTA/2003/05" Version="1.0">
  <POS>
    <Source>
      <RequestorID Type="1" ID="{username}" MessagePassword="{password}"/>
    </Source>
  </POS>
  <AvailRequestSegments>
    <AvailRequestSegment>
      <StayDateRange Start="{check_in.isoformat()}" End="{check_out.isoformat()}"/>
      <DestinationSystemCodes>
        <DestinationSystemCode>{destination}</DestinationSystemCode>
      </DestinationSystemCodes>
      <RoomStayCandidates>
        <RoomStayCandidate Quantity="1">
          <GuestCounts>
            <GuestCount AgeQualifyingCode="10" Count="{adults}"/>
          </GuestCounts>
        </RoomStayCandidate>
      </RoomStayCandidates>
    </AvailRequestSegment>
  </AvailRequestSegments>
</OTA_HotelAvailRQ>"""


def _parse_response(xml_text: str, check_in: date, check_out: date) -> list[dict]:
    nights = (check_out - check_in).days
    results = []
    try:
        root = ET.fromstring(xml_text)
        ns = {"ota": "http://www.opentravel.org/OTA/2003/05"}

        for room_stay in root.findall(".//ota:RoomStay", ns):
            hotel_el    = room_stay.find("ota:BasicPropertyInfo", ns)
            hotel_code  = hotel_el.get("HotelCode", "") if hotel_el is not None else ""
            hotel_name  = hotel_el.get("HotelName", "Unknown") if hotel_el is not None else "Unknown"

            for rate_plan in room_stay.findall(".//ota:RatePlan", ns):
                total_el = rate_plan.find("ota:Total", ns)
                if total_el is None:
                    continue
                price_str   = total_el.get("AmountAfterTax", "0")
                currency    = total_el.get("CurrencyCode", "GBP")
                board_code  = rate_plan.get("MealPlanIndicator", "RO")

                try:
                    price = float(price_str)
                except ValueError:
                    continue

                if price == 0:
                    continue

                results.append({
                    "hotel_code":  hotel_code,
                    "hotel_name":  hotel_name,
                    "check_in":    check_in,
                    "check_out":   check_out,
                    "nights":      nights,
                    "price_gbp":   price,
                    "currency":    currency,
                    "board_basis": board_code,
                    "source":      "Acerooms",
                })
    except ET.ParseError as e:
        logger.error("Acerooms XML parse error: %s", e)
    return results


def fetch_hotels(
    username: str,
    password: str,
    destination: str,
    check_in: date,
    check_out: date,
    adults: int = 2,
) -> list[dict]:
    payload = _build_request(username, password, destination, check_in, check_out, adults)
    try:
        resp = requests.post(
            BASE_URL,
            data=payload.encode("utf-8"),
            headers={"Content-Type": "application/xml; charset=utf-8"},
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error("Acerooms API error %s->%s: %s", check_in, check_out, e)
        return []

    results = _parse_response(resp.text, check_in, check_out)
    logger.info("Acerooms: %d hotels for %s (%dN)", len(results), check_in, (check_out - check_in).days)
    return results


def fetch_all_dates(
    username: str,
    password: str,
    destination: str,
    start_date: date,
    days_ahead: int,
    night_durations: list[int],
    adults: int = 2,
) -> list[dict]:
    all_results = []
    for offset in range(days_ahead):
        check_in = start_date + timedelta(days=offset)
        for nights in night_durations:
            check_out = check_in + timedelta(days=nights)
            rows = fetch_hotels(username, password, destination, check_in, check_out, adults)
            all_results.extend(rows)
    return all_results
