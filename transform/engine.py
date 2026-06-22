import pandas as pd
from datetime import date


def hotels_to_df(hotel_rows: list[dict]) -> pd.DataFrame:
    if not hotel_rows:
        return pd.DataFrame()
    df = pd.DataFrame(hotel_rows)
    df["check_in"] = pd.to_datetime(df["check_in"])
    return df


def flights_to_df(flight_rows: list[dict]) -> pd.DataFrame:
    if not flight_rows:
        return pd.DataFrame()
    df = pd.DataFrame(flight_rows)
    df["depart_date"] = pd.to_datetime(df["depart_date"])
    return df


def cheapest_hotel_per_date(hotels_df: pd.DataFrame) -> pd.DataFrame:
    """For each (check_in, nights), find the single cheapest hotel across all sources."""
    if hotels_df.empty:
        return pd.DataFrame()
    idx = hotels_df.groupby(["check_in", "nights"])["price_gbp"].idxmin()
    return hotels_df.loc[idx].reset_index(drop=True)


def cheapest_flight_per_route_date(flights_df: pd.DataFrame) -> pd.DataFrame:
    """For each (origin, depart_date, nights), find the cheapest fare."""
    if flights_df.empty:
        return pd.DataFrame()
    idx = flights_df.groupby(["origin", "depart_date", "nights"])["price_gbp"].idxmin()
    return flights_df.loc[idx].reset_index(drop=True)


def build_packages(hotels_df: pd.DataFrame, flights_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join cheapest hotel + cheapest flight per (origin, date, nights).
    Returns a DataFrame with total package price.
    """
    if hotels_df.empty or flights_df.empty:
        return pd.DataFrame()

    best_hotels  = cheapest_hotel_per_date(hotels_df)
    best_flights = cheapest_flight_per_route_date(flights_df)

    # Merge on date and nights
    merged = best_flights.merge(
        best_hotels,
        left_on=["depart_date", "nights"],
        right_on=["check_in", "nights"],
        suffixes=("_flight", "_hotel"),
    )

    merged["total_package_gbp"] = merged["price_gbp_flight"] + merged["price_gbp_hotel"]
    merged = merged.rename(columns={
        "price_gbp_flight": "flight_price_gbp",
        "price_gbp_hotel":  "hotel_price_gbp",
    })

    merged = merged.sort_values(["origin", "depart_date", "nights"]).reset_index(drop=True)
    return merged


def flight_price_pivot(flights_df: pd.DataFrame, origin: str, night_durations: list[int]) -> pd.DataFrame:
    """
    Pivot table: rows = dates, columns = night durations.
    Matches the Flights tab layout in your Excel.
    """
    sub = flights_df[flights_df["origin"] == origin].copy()
    if sub.empty:
        return pd.DataFrame()
    sub["date_label"] = sub["depart_date"].dt.strftime("%-d-%b")
    pivot = sub.pivot_table(
        index="depart_date",
        columns="nights",
        values="price_gbp",
        aggfunc="min",
    )
    pivot.columns = [f"{n} Nights" for n in pivot.columns]
    pivot.index = pd.to_datetime(pivot.index)
    pivot = pivot.sort_index()
    return pivot


def hotel_price_pivot(hotels_df: pd.DataFrame, hotel_name: str, night_durations: list[int]) -> pd.DataFrame:
    """
    Pivot table for one hotel: rows = dates, columns = night durations.
    Matches the Hotel tab layout.
    """
    sub = hotels_df[hotels_df["hotel_name"] == hotel_name].copy()
    if sub.empty:
        return pd.DataFrame()
    pivot = sub.pivot_table(
        index="check_in",
        columns="nights",
        values="price_gbp",
        aggfunc="min",
    )
    pivot.columns = [f"{n} Nights" for n in pivot.columns]
    pivot = pivot.sort_index()
    return pivot


def package_price_pivot(packages_df: pd.DataFrame, origin: str) -> pd.DataFrame:
    """
    Pivot of total package prices for one departure city.
    Matches the LON Final / MAN Final / EDI Final / BRS Final tabs.
    """
    sub = packages_df[packages_df["origin"] == origin].copy()
    if sub.empty:
        return pd.DataFrame()
    pivot = sub.pivot_table(
        index="depart_date",
        columns="nights",
        values="total_package_gbp",
        aggfunc="min",
    )
    pivot.columns = [f"{n} Nights" for n in pivot.columns]
    pivot = pivot.sort_index()
    return pivot
