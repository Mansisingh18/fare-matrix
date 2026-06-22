"""
Global airport list — organised by region.
Each entry is an IATA code.

To search ALL airports: set DEPARTURE_CITIES=ALL in .env
To search a region:     set DEPARTURE_CITIES=EUROPE or ASIA etc.
To search specific:     set DEPARTURE_CITIES=LON,DXB,SIN
"""

AIRPORTS = {
    "UK": [
        "LHR",  # London Heathrow
        "LGW",  # London Gatwick
        "MAN",  # Manchester
        "EDI",  # Edinburgh
        "BRS",  # Bristol
        "BHX",  # Birmingham
        "GLA",  # Glasgow
        "LBA",  # Leeds Bradford
        "NCL",  # Newcastle
        "LPL",  # Liverpool
    ],
    "EUROPE": [
        "CDG",  # Paris
        "FRA",  # Frankfurt
        "AMS",  # Amsterdam
        "MAD",  # Madrid
        "BCN",  # Barcelona
        "FCO",  # Rome
        "MXP",  # Milan
        "ZRH",  # Zurich
        "VIE",  # Vienna
        "BRU",  # Brussels
        "CPH",  # Copenhagen
        "OSL",  # Oslo
        "ARN",  # Stockholm
        "HEL",  # Helsinki
        "ATH",  # Athens
        "LIS",  # Lisbon
        "WAW",  # Warsaw
        "PRG",  # Prague
        "BUD",  # Budapest
        "DUB",  # Dublin
    ],
    "MIDDLE_EAST": [
        "DXB",  # Dubai
        "DOH",  # Doha
        "AUH",  # Abu Dhabi
        "KWI",  # Kuwait
        "BAH",  # Bahrain
        "AMM",  # Amman
        "BEY",  # Beirut
        "CAI",  # Cairo
        "TLV",  # Tel Aviv
        "MCT",  # Muscat
    ],
    "ASIA": [
        "SIN",  # Singapore
        "HKG",  # Hong Kong
        "NRT",  # Tokyo Narita
        "HND",  # Tokyo Haneda
        "PEK",  # Beijing
        "PVG",  # Shanghai
        "ICN",  # Seoul
        "BKK",  # Bangkok
        "KUL",  # Kuala Lumpur
        "CGK",  # Jakarta
        "MNL",  # Manila
        "BOM",  # Mumbai
        "DEL",  # Delhi
        "BLR",  # Bangalore
        "MAA",  # Chennai
        "CMB",  # Colombo
        "DAC",  # Dhaka
        "KTM",  # Kathmandu
    ],
    "NORTH_AMERICA": [
        "JFK",  # New York JFK
        "EWR",  # New York Newark
        "LAX",  # Los Angeles
        "ORD",  # Chicago
        "MIA",  # Miami
        "ATL",  # Atlanta
        "SFO",  # San Francisco
        "BOS",  # Boston
        "IAD",  # Washington DC
        "YYZ",  # Toronto
        "YVR",  # Vancouver
        "YUL",  # Montreal
        "MEX",  # Mexico City
        "CUN",  # Cancun
    ],
    "SOUTH_AMERICA": [
        "GRU",  # São Paulo
        "EZE",  # Buenos Aires
        "BOG",  # Bogota
        "LIM",  # Lima
        "SCL",  # Santiago
        "GIG",  # Rio de Janeiro
        "MVD",  # Montevideo
        "UIO",  # Quito
    ],
    "AFRICA": [
        "JNB",  # Johannesburg
        "CPT",  # Cape Town
        "NBO",  # Nairobi
        "ADD",  # Addis Ababa
        "LOS",  # Lagos
        "ACC",  # Accra
        "CMN",  # Casablanca
        "TUN",  # Tunis
    ],
    "OCEANIA": [
        "SYD",  # Sydney
        "MEL",  # Melbourne
        "BNE",  # Brisbane
        "PER",  # Perth
        "AKL",  # Auckland
        "CHC",  # Christchurch
    ],
}

# Flat list of all airports
ALL_AIRPORTS = [code for region in AIRPORTS.values() for code in region]

REGION_ALIASES = {
    "ALL": ALL_AIRPORTS,
    "UK": AIRPORTS["UK"],
    "EUROPE": AIRPORTS["UK"] + AIRPORTS["EUROPE"],
    "ASIA": AIRPORTS["ASIA"],
    "MIDDLE_EAST": AIRPORTS["MIDDLE_EAST"],
    "NORTH_AMERICA": AIRPORTS["NORTH_AMERICA"],
    "SOUTH_AMERICA": AIRPORTS["SOUTH_AMERICA"],
    "AFRICA": AIRPORTS["AFRICA"],
    "OCEANIA": AIRPORTS["OCEANIA"],
}


def resolve_departure_cities(config_value: str) -> list[str]:
    """
    Resolves DEPARTURE_CITIES config into a flat list of IATA codes.
    Handles: ALL, region names, or comma-separated IATA codes.
    """
    val = config_value.strip().upper()
    if val in REGION_ALIASES:
        return REGION_ALIASES[val]
    return [c.strip().upper() for c in config_value.split(",") if c.strip()]
