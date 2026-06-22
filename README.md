# FARE MATRIX — Travel Price Intelligence

Automated aggregation of hotel and flight prices across Bedsonline, Acerooms, and Amadeus — refreshed on a schedule, ranked by cheapest deal, and delivered as a formatted Excel report.

## What it does

- Fetches hotel prices from **Bedsonline** (Hotelbeds API) and **Acerooms** simultaneously
- Fetches flight prices from **Amadeus** for UK departure cities (LON, MAN, EDI, BRS) to any destination
- Applies live **currency conversion** (GBP / EUR / INR) via Open Exchange Rates
- Joins hotel + flight prices into **total package prices**, ranked cheapest first
- Generates a formatted **Excel workbook** matching the Amsterdam New Deal layout (Flights, Hotel, Final tabs per city, Prices summary, CSV export)
- Sends the report by **email** on every run
- Fires a **deal alert** if any package drops below a price threshold

## Setup

### 1. Prerequisites

- Python 3.11+ — download from [python.org](https://python.org)
- API credentials:
  - Bedsonline: your existing B2B agent keys
  - Acerooms: your agent account username + password
  - Amadeus: free at [amadeus.com/developers](https://amadeus.com/developers)
  - Open Exchange Rates: free at [openexchangerates.org](https://openexchangerates.org)

### 2. First-time setup

```
Double-click setup.bat
```

This creates a virtual environment, installs all dependencies, and opens `.env` for you to fill in.

### 3. Configure

Copy `.env.example` to `.env` and fill in your credentials:

```env
HOTELBEDS_API_KEY=...
HOTELBEDS_SECRET=...
ACEROOMS_USERNAME=...
ACEROOMS_PASSWORD=...
AMADEUS_API_KEY=...
AMADEUS_API_SECRET=...
```

### 4. Run

```
Double-click run.bat
```

Excel report is saved to the `data/` folder.

### 5. Schedule (optional)

```
Double-click schedule_task.bat
```

Registers a Windows Task Scheduler job that runs every day at 7:00 AM automatically.

## Project structure

```
fare-matrix/
├── main.py                  # Entry point — orchestrates the full pipeline
├── config.py                # Loads settings from .env
├── fetchers/
│   ├── bedsonline.py        # Hotelbeds API integration
│   ├── acerooms.py          # Acerooms XML API integration
│   ├── amadeus.py           # Amadeus flight search
│   └── fx_rates.py          # Currency conversion
├── transform/
│   └── engine.py            # Joins hotel + flight data, builds package prices
├── reports/
│   └── excel_builder.py     # Generates the Excel workbook
├── notify/
│   └── email_sender.py      # Sends report + deal alerts by email
├── setup.bat                # First-time setup (Windows)
├── run.bat                  # Run the pipeline
└── schedule_task.bat        # Register daily Task Scheduler job
```

## Output

Each run generates an Excel file in `data/` named `AMS_deals_YYYYMMDD_HHMM.xlsx` with tabs:

| Tab | Contents |
|-----|----------|
| Flights | Cheapest flight prices per date and duration |
| Hotel | Hotel prices per date and duration |
| LON Final | Total package prices from London |
| MAN Final | Total package prices from Manchester |
| EDI Final | Total package prices from Edinburgh |
| BRS Final | Total package prices from Bristol |
| Prices | Best deal summary across all cities |
| CSV | Raw data export |

## Destinations

Currently configured for Amsterdam (AMS). To run for a different destination, update `DESTINATION` in `.env`.
