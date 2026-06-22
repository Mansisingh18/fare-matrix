import requests
import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
SEARCH_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

# Switch to production URLs once ready:
# TOKEN_URL  = "https://api.amadeus.com/v1/security/oauth2/token"
# SEARCH_URL = "https://api.amadeus.com/v2/shopping/flight-offers"

# City → nearest airport IATA code
CITY_TO_IATA = {
    "LON": "LHR",
    "MAN": "MAN",
    "EDI": "EDI",
    "BRS": "BRS",
}


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


def fetch_cheapest_fare(
    token: str,
    origin_city: str,
    destination: str,
    depart_date: date,
    return_date: date,
    adults: int = 2,
) -> dict | None:
    """
    Returns the cheapest round-trip fare for one departure city and date window.
    Returns: {origin, destination, depart_date, return_date, nights, price_gbp, airline, source}
    """
    origin_iata = CITY_TO_IATA.get(origin_city, origin_city)
    nights = (return_date - depart_date).days

    params = {
        "originLocationCode": origin_iata,
        "destinationLocationCode": destination,
        "departureDate": depart_date.isoformat(),
        "returnDate": return_date.isoformat(),
        "adults": adults,
        "currencyCode": "GBP",
        "max": 5,
    }

    try:
        resp = requests.get(
            SEARCH_URL,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        offers = resp.json().get("data", [])
    except requests.RequestException as e:
        logger.error("Amadeus error %s %s->%s: %s", depart_date, origin_city, destination, e)
        return None

    if not offers:
        return None

    cheapest = offers[0]
    price = float(cheapest["price"]["total"])
    carrier = cheapest["validatingAirlineCodes"][0] if cheapest.get("validatingAirlineCodes") else "N/A"

    return {
        "origin": origin_city,
        "destination": destination,
        "depart_date": depart_date,
        "return_date": return_date,
        "nights": nights,
        "price_gbp": price,
        "airline": carrier,
        "source": "Amadeus",
    }


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
    token = _get_token(api_key, api_secret)
    all_results = []

    for city in departure_cities:
        for offset in range(days_ahead):
            depart = start_date + timedelta(days=offset)
            for nights in night_durations:
                return_d = depart + timedelta(days=nights)
                fare = fetch_cheapest_fare(token, city, destination, depart, return_d, adults)
                if fare:
                    all_results.append(fare)

    logger.info("Amadeus: %d flight fares fetched", len(all_results))
    return all_results
