import requests
import logging

logger = logging.getLogger(__name__)


def get_rate_to_gbp(app_id: str | None, from_currency: str = "GBP") -> float:
    """
    Returns the conversion rate FROM from_currency TO GBP.
    If source is already GBP, returns 1.0.
    """
    if from_currency.upper() == "GBP" or not app_id:
        return 1.0

    try:
        resp = requests.get(
            f"https://openexchangerates.org/api/latest.json",
            params={"app_id": app_id, "base": "USD"},
            timeout=10,
        )
        resp.raise_for_status()
        rates = resp.json()["rates"]
        gbp_per_usd = rates.get("GBP", 1.0)
        src_per_usd = rates.get(from_currency.upper(), 1.0)
        rate = gbp_per_usd / src_per_usd
        logger.info("FX: 1 %s = %.4f GBP", from_currency, rate)
        return rate
    except requests.RequestException as e:
        logger.error("FX rate fetch failed: %s — defaulting to 1.0", e)
        return 1.0
