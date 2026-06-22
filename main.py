"""
FARE MATRIX — main entry point.
Run manually: python main.py
Scheduled:    Windows Task Scheduler points to run.bat
"""

import logging
import sys
from datetime import date, timedelta

import config
from fetchers.bedsonline import fetch_all_dates as bedsonline_fetch
from fetchers.acerooms   import fetch_all_dates as acerooms_fetch
from fetchers.amadeus    import fetch_all_flights
from fetchers.fx_rates   import get_rate_to_gbp
from transform.engine    import hotels_to_df, flights_to_df
from reports.excel_builder import build_excel
from notify.email_sender   import send_report, send_deal_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("fare_matrix.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def run():
    logger.info("=== FARE MATRIX starting ===")
    start_date = date.today() + timedelta(days=1)

    # ── 1. Fetch hotel prices (Bedsonline + Acerooms combined) ───────────────
    logger.info("Fetching hotel prices from Bedsonline...")
    raw_hotels_bs = bedsonline_fetch(
        api_key=config.HOTELBEDS_API_KEY,
        secret=config.HOTELBEDS_SECRET,
        destination=config.DESTINATION,
        start_date=start_date,
        days_ahead=config.SEARCH_DAYS_AHEAD,
        night_durations=config.NIGHT_DURATIONS,
        adults=config.OCCUPANCY_ADULTS,
    )
    logger.info("Bedsonline: %d rows", len(raw_hotels_bs))

    logger.info("Fetching hotel prices from Acerooms...")
    raw_hotels_ac = acerooms_fetch(
        username=config.ACEROOMS_USERNAME,
        password=config.ACEROOMS_PASSWORD,
        destination=config.DESTINATION,
        start_date=start_date,
        days_ahead=config.SEARCH_DAYS_AHEAD,
        night_durations=config.NIGHT_DURATIONS,
        adults=config.OCCUPANCY_ADULTS,
    )
    logger.info("Acerooms: %d rows", len(raw_hotels_ac))

    raw_hotels = raw_hotels_bs + raw_hotels_ac
    logger.info("Hotels total (both sources): %d rows", len(raw_hotels))

    # ── 2. Fetch flight prices ───────────────────────────────────────────────
    raw_flights = []
    if config.AMADEUS_API_KEY and config.AMADEUS_API_SECRET:
        logger.info("Fetching flight prices from Amadeus...")
        raw_flights = fetch_all_flights(
            api_key=config.AMADEUS_API_KEY,
            api_secret=config.AMADEUS_API_SECRET,
            departure_cities=config.DEPARTURE_CITIES,
            destination=config.DESTINATION,
            start_date=start_date,
            days_ahead=config.SEARCH_DAYS_AHEAD,
            night_durations=config.NIGHT_DURATIONS,
            adults=config.OCCUPANCY_ADULTS,
        )
        logger.info("Flights fetched: %d rows", len(raw_flights))
    else:
        logger.info("Amadeus not configured — skipping flights, running hotels only")

    # ── 3. Currency conversion (prices are already in GBP from both APIs) ───
    # If Bedsonline ever returns EUR prices, apply conversion here:
    # fx = get_rate_to_gbp(config.FX_APP_ID, from_currency="EUR")
    # for row in raw_hotels: row["price_gbp"] *= fx

    # ── 4. Build DataFrames ──────────────────────────────────────────────────
    hotels_df  = hotels_to_df(raw_hotels)
    flights_df = flights_to_df(raw_flights)

    if hotels_df.empty:
        logger.warning("No hotel data — check Bedsonline credentials and destination code")
    if flights_df.empty and raw_flights:
        logger.warning("No flight data — check Amadeus credentials and route codes")

    # ── 5. Build packages (hotel + flight joined) ────────────────────────────
    from transform.engine import build_packages
    packages_df = build_packages(hotels_df, flights_df)
    logger.info("Packages built: %d combinations", len(packages_df))

    # ── 6. Generate Excel ────────────────────────────────────────────────────
    logger.info("Generating Excel report...")
    excel_path = build_excel(
        hotels_df=hotels_df,
        flights_df=flights_df,
        packages_df=packages_df,
        departure_cities=config.DEPARTURE_CITIES,
        night_durations=config.NIGHT_DURATIONS,
        output_dir=config.OUTPUT_DIR,
        destination=config.DESTINATION,
    )
    logger.info("Excel saved: %s", excel_path)

    # ── 7. Check for deal alerts ─────────────────────────────────────────────
    deal_lines = []
    if not packages_df.empty:
        deals = packages_df[packages_df["total_package_gbp"] < config.ALERT_THRESHOLD]
        for _, row in deals.iterrows():
            line = (
                f"  {row['origin']} → {config.DESTINATION} | "
                f"{int(row['nights'])} nights departing {row['depart_date'].date()} | "
                f"£{row['total_package_gbp']:.2f} total"
            )
            deal_lines.append(line)

    deal_summary = ""
    if deal_lines:
        deal_summary = "DEALS BELOW £{} THRESHOLD:\n{}".format(
            config.ALERT_THRESHOLD, "\n".join(deal_lines)
        )
        logger.info("Deals found below threshold:\n%s", deal_summary)

    # ── 8. Send email ────────────────────────────────────────────────────────
    if config.EMAIL_FROM and config.EMAIL_TO and config.SMTP_PASSWORD:
        logger.info("Sending report email...")
        send_report(
            excel_path=excel_path,
            from_addr=config.EMAIL_FROM,
            to_addr=config.EMAIL_TO,
            smtp_host=config.SMTP_HOST,
            smtp_port=config.SMTP_PORT,
            smtp_password=config.SMTP_PASSWORD,
            deal_summary=deal_summary,
        )
        if deal_lines:
            send_deal_alert(
                deal_text=deal_summary,
                from_addr=config.EMAIL_FROM,
                to_addr=config.EMAIL_TO,
                smtp_host=config.SMTP_HOST,
                smtp_port=config.SMTP_PORT,
                smtp_password=config.SMTP_PASSWORD,
            )
    else:
        logger.info("Email not configured — skipping (set EMAIL_FROM, EMAIL_TO, SMTP_PASSWORD in .env)")

    logger.info("=== FARE MATRIX complete ===")
    return excel_path


if __name__ == "__main__":
    run()
