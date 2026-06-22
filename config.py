import os
from dotenv import load_dotenv
from fetchers.airports import resolve_departure_cities

load_dotenv()

HOTELBEDS_API_KEY  = os.getenv("HOTELBEDS_API_KEY")
HOTELBEDS_SECRET   = os.getenv("HOTELBEDS_SECRET")
ACEROOMS_USERNAME  = os.getenv("ACEROOMS_USERNAME")
ACEROOMS_PASSWORD  = os.getenv("ACEROOMS_PASSWORD")
AMADEUS_API_KEY    = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")
FX_APP_ID          = os.getenv("FX_APP_ID")

DESTINATION        = os.getenv("DESTINATION", "AMS")
DEPARTURE_CITIES   = resolve_departure_cities(os.getenv("DEPARTURE_CITIES", "UK"))
NIGHT_DURATIONS    = [int(n) for n in os.getenv("NIGHT_DURATIONS", "2,3,4").split(",")]
SEARCH_DAYS_AHEAD  = int(os.getenv("SEARCH_DAYS_AHEAD", "365"))
OCCUPANCY_ADULTS   = int(os.getenv("OCCUPANCY_ADULTS", "2"))
ALERT_THRESHOLD    = float(os.getenv("ALERT_THRESHOLD_GBP", "200"))

EMAIL_FROM    = os.getenv("EMAIL_FROM")
EMAIL_TO      = os.getenv("EMAIL_TO")
SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(os.path.dirname(__file__), "data"))
os.makedirs(OUTPUT_DIR, exist_ok=True)
