import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side, numbers
)
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from datetime import date, datetime

# Colours matching your existing workbook
HEADER_FILL   = PatternFill("solid", fgColor="1F3864")   # dark navy
CHEAPEST_FILL = PatternFill("solid", fgColor="2DD4BF")   # teal highlight
ALT_ROW_FILL  = PatternFill("solid", fgColor="F0F4F8")   # light blue-grey
WHITE_FILL    = PatternFill("solid", fgColor="FFFFFF")
HEADER_FONT   = Font(name="Calibri", bold=True, color="FFFFFF", size=10)
BODY_FONT     = Font(name="Calibri", size=10)
PRICE_FORMAT  = '£#,##0.00'
DATE_FORMAT   = 'D-MMM'

thin = Side(border_style="thin", color="D0D7DE")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)


def _write_pivot(ws, pivot_df: pd.DataFrame, title: str):
    """Write a pivot table (dates × night durations) to a worksheet."""
    ws.title = title

    # Header row
    ws.append(["Date"] + list(pivot_df.columns))
    for cell in ws[1]:
        cell.fill   = HEADER_FILL
        cell.font   = HEADER_FONT
        cell.border = BORDER
        cell.alignment = Alignment(horizontal="center")

    # Data rows
    for row_idx, (dt_index, row) in enumerate(pivot_df.iterrows(), start=2):
        date_val = dt_index.date() if hasattr(dt_index, "date") else dt_index
        ws.cell(row=row_idx, column=1, value=date_val)
        ws.cell(row=row_idx, column=1).number_format = DATE_FORMAT
        ws.cell(row=row_idx, column=1).font   = BODY_FONT
        ws.cell(row=row_idx, column=1).border = BORDER

        fill = ALT_ROW_FILL if row_idx % 2 == 0 else WHITE_FILL
        for col_idx, val in enumerate(row.values, start=2):
            cell = ws.cell(row=row_idx, column=col_idx)
            if pd.notna(val):
                cell.value         = round(float(val), 2)
                cell.number_format = PRICE_FORMAT
            cell.font      = BODY_FONT
            cell.fill      = fill
            cell.border    = BORDER
            cell.alignment = Alignment(horizontal="right")

    # Highlight cheapest per row
    for row in ws.iter_rows(min_row=2, min_col=2):
        prices = [c.value for c in row if isinstance(c.value, (int, float))]
        if not prices:
            continue
        min_price = min(prices)
        for cell in row:
            if cell.value == min_price:
                cell.fill = CHEAPEST_FILL
                cell.font = Font(name="Calibri", bold=True, size=10)

    # Column widths
    ws.column_dimensions["A"].width = 12
    for col in range(2, pivot_df.shape[1] + 2):
        ws.column_dimensions[get_column_letter(col)].width = 13


def _write_packages(ws, packages_df: pd.DataFrame, origin: str, title: str):
    from transform.engine import package_price_pivot
    pivot = package_price_pivot(packages_df, origin)
    if pivot.empty:
        ws.title = title
        ws["A1"] = "No data available"
        return
    _write_pivot(ws, pivot, title)


def _write_raw_csv_sheet(ws, packages_df: pd.DataFrame):
    ws.title = "CSV"
    cols = [
        "origin", "depart_date", "nights",
        "flight_price_gbp", "hotel_name", "hotel_price_gbp",
        "total_package_gbp", "airline", "board_basis",
    ]
    available = [c for c in cols if c in packages_df.columns]
    ws.append(available)
    for cell in ws[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
    for r in dataframe_to_rows(packages_df[available], index=False, header=False):
        ws.append(r)


def build_excel(
    hotels_df: pd.DataFrame,
    flights_df: pd.DataFrame,
    packages_df: pd.DataFrame,
    departure_cities: list[str],
    night_durations: list[int],
    output_dir: str,
    destination: str = "AMS",
) -> str:
    wb = Workbook()
    wb.remove(wb.active)

    # --- Flights tab ---
    from transform.engine import flight_price_pivot
    ws_flights = wb.create_sheet("Flights")
    all_flight_pivots = {}
    for city in departure_cities:
        p = flight_price_pivot(flights_df, city, night_durations)
        all_flight_pivots[city] = p

    # Write LON flights as the default flights tab (first city)
    first_city = departure_cities[0] if departure_cities else "LON"
    if not all_flight_pivots.get(first_city, pd.DataFrame()).empty:
        _write_pivot(ws_flights, all_flight_pivots[first_city], "Flights")
        ws_flights["A1"].value = f"Date ({first_city}→{destination})"
    else:
        ws_flights.title = "Flights"

    # --- Hotel tab ---
    from transform.engine import hotel_price_pivot
    ws_hotel = wb.create_sheet("Hotel")
    hotel_names = hotels_df["hotel_name"].unique().tolist() if not hotels_df.empty else []
    if hotel_names:
        first_hotel_pivot = hotel_price_pivot(hotels_df, hotel_names[0], night_durations)
        if not first_hotel_pivot.empty:
            _write_pivot(ws_hotel, first_hotel_pivot, "Hotel")
            ws_hotel["A1"].value = f"Date ({hotel_names[0][:20]})"
    else:
        ws_hotel.title = "Hotel"

    # --- Final tabs per departure city ---
    for city in departure_cities:
        ws = wb.create_sheet(f"{city} Final")
        _write_packages(ws, packages_df, city, f"{city} Final")

    # --- Prices summary tab ---
    ws_prices = wb.create_sheet("Prices")
    ws_prices.title = "Prices"
    ws_prices["A1"] = "Cheapest Package per Departure City"
    ws_prices["A1"].font = Font(bold=True, size=12)
    row = 3
    for city in departure_cities:
        sub = packages_df[packages_df["origin"] == city] if not packages_df.empty else pd.DataFrame()
        if sub.empty:
            continue
        best_idx  = sub["total_package_gbp"].idxmin()
        best_row  = sub.loc[best_idx]
        ws_prices.cell(row=row, column=1, value=f"{city} → {destination}")
        ws_prices.cell(row=row, column=1).font = Font(bold=True)
        ws_prices.cell(row=row, column=2, value=f"£{best_row['total_package_gbp']:.2f}")
        ws_prices.cell(row=row, column=3, value=str(best_row.get("depart_date", "")[:10] if isinstance(best_row.get("depart_date"), str) else best_row.get("depart_date", "")))
        ws_prices.cell(row=row, column=4, value=f"{int(best_row.get('nights', 0))} nights")
        row += 1

    # --- CSV raw export ---
    if not packages_df.empty:
        ws_csv = wb.create_sheet("CSV")
        _write_raw_csv_sheet(ws_csv, packages_df)

    # Save
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M")
    filename   = f"{destination}_deals_{timestamp}.xlsx"
    filepath   = os.path.join(output_dir, filename)
    wb.save(filepath)
    return filepath
