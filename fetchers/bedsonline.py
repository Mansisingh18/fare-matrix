import hashlib
import time
import requests
import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

BASE_URL = "https://api.hotelbeds.com/hotel-api/1.0"


BOARD_BASIS_LABELS = {
    "RO": "Room Only",
    "BB": "Bed & Breakfast",
    "HB": "Half Board",
    "FB": "Full Board",
    "AI": "All Inclusive",
    "SC": "Self Catering",
}

WANTED_BOARDS = {"RO", "BB", "HB", "FB", "AI"}


def _parse_stars(category_code: str) -> str:
    code = str(category_code).upper().strip()
    for n in ["7", "6", "5", "4", "3", "2", "1"]:
        if code.startswith(n):
            return f"{n}★"
    return "N/A"


def _headers(api_key: str, secret: str) -> dict:
    timestamp = str(int(time.time()))
    raw = f"{api_key}{secret}{timestamp}"
    signature = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return {
        "Api-key": api_key,
        "X-Signature": signature,
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/json",
    }


def fetch_hotels(
    api_key: str,
    secret: str,
    destination: str,
    check_in: date,
    check_out: date,
    adults: int = 2,
) -> list[dict]:
    """
    Returns a list of available hotels for one check-in/check-out window.
    Each item: {hotel_code, hotel_name, check_in, check_out, nights, price_gbp, board_basis, source}
    """
    nights = (check_out - check_in).days
    payload = {
        "stay": {
            "checkIn": check_in.isoformat(),
            "checkOut": check_out.isoformat(),
        },
        "occupancies": [{"rooms": 1, "adults": adults, "children": 0}],
        "destination": {"code": destination},
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/hotels",
            json=payload,
            headers=_headers(api_key, secret),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error("Bedsonline API error %s -> %s: %s", check_in, check_out, e)
        return []

    hotels = data.get("hotels", {}).get("hotels", [])
    results = []
    for h in hotels:
        stars = _parse_stars(h.get("categoryCode", ""))
        for room in h.get("rooms", []):
            for rate in room.get("rates", []):
                price      = float(rate.get("net", 0))
                board_code = rate.get("boardCode", "RO").upper()
                if price == 0:
                    continue
                if board_code not in WANTED_BOARDS:
                    continue
                results.append({
                    "hotel_code": h.get("code"),
                    "hotel_name": h.get("name", "Unknown"),
                    "stars":      stars,
                    "check_in":   check_in,
                    "check_out":  check_out,
                    "nights":     nights,
                    "price_gbp":  price,
                    "board_basis": board_code,
                    "board_label": BOARD_BASIS_LABELS.get(board_code, board_code),
                    "source":     "Bedsonline",
                })

    logger.info("Bedsonline: %d hotels for %s -> %s (%dN)", len(results), check_in, check_out, nights)
    return results


def fetch_all_dates(
    api_key: str,
    secret: str,
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
            rows = fetch_hotels(api_key, secret, destination, check_in, check_out, adults)
            all_results.extend(rows)
    return all_results
