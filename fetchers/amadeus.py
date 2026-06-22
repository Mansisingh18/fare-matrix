"""
Amadeus Flight Cheapest Date Search.

Uses /v1/shopping/flight-dates which returns the cheapest fare for EVERY
date in the next 12 months in a single API call — not one call per date.

1 call per (origin × duration) vs 365 calls per (origin × duration).
This makes a global airport sweep feasible on the free tier.
"""

import requests
import logging
import time
from datetime import date, timedelta

logger = logging.getLogger(__name__)

TOKEN_URL  = "https://test.api.amadeus.com/v1/security/oauth2/token"
DATES_URL  = "https://test.api.amadeus.com/v1/shopping/flight-dates"

# Switch to production once ready:
# TOKEN_URL = "https://api.amadeus.com/v1/security/oauth2/token"
# DATES_URL = "https://api.amadeus.com/v1/shopping/flight-dates"


def _get_token(api_key: str, api_secret: str) -> str:
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": api_key,
            "client_secret": api_secret,
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_cheapest_dates(
    token: str,
    origin: str,
    destination: str,
    duration: int,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """
    Fetches cheapest round-trip fares from origin → destination for
    every available departure date within the window, at a fixed duration.

    Returns a list of: {origin, destination, depart_date, return_date,
                        nights, price_gbp, airline, source}
    """
    params = {
        "originLocationCode":      origin,
        "destinationLocationCode": destination,
        "departureDate":           f"{start_date.isoformat()},{end_date.isoformat()}",
        "duration":                duration,
        "currencyCode":            "GBP",
        "nonStop":                 "false",
        "viewBy":                  "DATE",
    }

    try:
        resp = requests.get(
            DATES_URL,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=30,
        )
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except requests.RequestException as e:
        logger.warning("Amadeus flight-dates error %s->%s %dN: %s", origin, destination, duration, e)
        return []

    results = []
    for item in data:
        dep_str = item.get("departureDate", "")
        ret_str = item.get("returnDate", "")
        price   = float(item.get("price", {}).get("total", 0))
        if not dep_str or price == 0:
            continue
        results.append({
            "origin":       origin,
            "destination":  destination,
            "depart_date":  date.fromisoformat(dep_str),
            "return_date":  date.fromisoformat(ret_str) if ret_str else None,
            "nights":       duration,
            "price_gbp":    price,
            "airline":      item.get("links", {}).get("flightOffers", ""),
            "source":       "Amadeus",
        })

    return results


def fetch_all_flights(
    api_key: str,
    api_secret: str,
    departure_cities: list[str],
    destination: str,
    start_date: date,
    days_ahead: int,
    night_durations: list[int],
    adults: int = 2,
) -> list[dict]:
    token      = _get_token(api_key, api_secret)
    end_date   = start_date + timedelta(days=days_ahead)
    all_results = []
    call_count  = 0
    total_calls = len(departure_cities) * len(night_durations)

    logger.info(
        "Amadeus: fetching %d origins × %d durations = %d calls (full year each)",
        len(departure_cities), len(night_durations), total_calls,
    )

    for city in departure_cities:
        # Skip if origin == destination
        if city == destination:
            continue

        for duration in night_durations:
            rows = fetch_cheapest_dates(token, city, destination, duration, start_date, end_date)
            all_results.extend(rows)
            call_count += 1

            if call_count % 20 == 0:
                logger.info("Amadeus progress: %d / %d routes done", call_count, total_calls)

            # Refresh token every 1500 calls
            if call_count % 1500 == 0:
                token = _get_token(api_key, api_secret)

            # Small delay to respect rate limits
            time.sleep(0.3)

    logger.info(
        "Amadeus: %d fare records from %d routes (%d origins)",
        len(all_results), call_count, len(departure_cities),
    )
    return all_results
