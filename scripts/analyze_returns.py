#!/usr/bin/env python3
"""Calculate transparent historical-return statistics from a clean value series.

The input value must already represent the intended economic series, such as an
adjusted close, total-return index, or adjusted NAV. This script does not fetch,
currency-convert, or distribution-adjust data.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    import pandas as pd
except ImportError as exc:  # pragma: no cover - environment-specific
    raise SystemExit("pandas is required: install it with `python -m pip install pandas`.") from exc


@dataclass
class WindowResult:
    label: str
    start_date: str
    end_date: str
    years: float
    cumulative_return: float
    annualized_return: float | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze an adjusted-price, total-return-index, or adjusted-NAV CSV series."
    )
    parser.add_argument("csv", type=Path, help="Input CSV path")
    parser.add_argument("--date-column", default="Date", help="Date column name")
    parser.add_argument("--value-column", default="Adj_Close", help="Positive value column name")
    parser.add_argument(
        "--format", choices=("markdown", "json"), default="markdown", help="Output format"
    )
    return parser.parse_args()


def load_series(path: Path, date_column: str, value_column: str) -> pd.Series:
    frame = pd.read_csv(path)
    missing = [name for name in (date_column, value_column) if name not in frame.columns]
    if missing:
        raise ValueError(f"Missing column(s) {missing}; available columns: {list(frame.columns)}")

    dates = pd.to_datetime(frame[date_column], errors="coerce", utc=True).dt.tz_localize(None)
    values = pd.to_numeric(frame[value_column], errors="coerce")
    clean = pd.DataFrame({"date": dates, "value": values}).dropna()
    if clean.empty:
        raise ValueError("No valid date/value rows remain after parsing.")
    if (clean["value"] <= 0).any():
        raise ValueError("All values must be strictly positive.")

    clean = clean.sort_values("date").drop_duplicates("date", keep="last")
    if len(clean) < 3:
        raise ValueError("At least three distinct observations are required.")
    series = clean.set_index("date")["value"].astype(float)
    if series.index[-1] <= series.index[0]:
        raise ValueError("The series must span more than one date.")
    return series


def years_between(start: pd.Timestamp, end: pd.Timestamp) -> float:
    return (end - start).total_seconds() / (365.2425 * 24 * 60 * 60)


def infer_periods_per_year(index: pd.DatetimeIndex) -> tuple[int, str, float]:
    gaps = index.to_series().diff().dropna().dt.total_seconds() / 86400
    median_days = float(gaps.median())
    if median_days <= 2:
        return 252, "daily", median_days
    if median_days <= 10:
        return 52, "weekly", median_days
    if median_days <= 45:
        return 12, "monthly", median_days
    if median_days <= 120:
        return 4, "quarterly", median_days
    return 1, "annual/irregular", median_days


def make_window(series: pd.Series, start: pd.Timestamp, label: str) -> WindowResult | None:
    eligible = series.loc[series.index >= start]
    if len(eligible) < 2:
        return None
    first_date, last_date = eligible.index[0], eligible.index[-1]
    elapsed = years_between(first_date, last_date)
    cumulative = float(eligible.iloc[-1] / eligible.iloc[0] - 1)
    annualized = float((eligible.iloc[-1] / eligible.iloc[0]) ** (1 / elapsed) - 1) if elapsed > 0 else None
    return WindowResult(
        label=label,
        start_date=first_date.date().isoformat(),
        end_date=last_date.date().isoformat(),
        years=elapsed,
        cumulative_return=cumulative,
        annualized_return=annualized,
    )


def calendar_returns(series: pd.Series) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    years = sorted(series.index.year.unique())
    prior_year_end: float | None = None
    first_observation = series.index[0]

    for year in years:
        year_series = series.loc[series.index.year == year]
        if prior_year_end is None:
            base = float(year_series.iloc[0])
            partial = first_observation.month != 1 or first_observation.day > 7
        else:
            base = prior_year_end
            partial = False
        ending = float(year_series.iloc[-1])
        rows.append(
            {
                "year": int(year),
                "return": ending / base - 1,
                "partial_start_year": partial,
            }
        )
        prior_year_end = ending
    return rows


def analyze(series: pd.Series) -> dict[str, object]:
    start_date, end_date = series.index[0], series.index[-1]
    elapsed = years_between(start_date, end_date)
    cumulative = float(series.iloc[-1] / series.iloc[0] - 1)
    cagr = float((series.iloc[-1] / series.iloc[0]) ** (1 / elapsed) - 1)

    periodic_returns = series.pct_change().dropna()
    periods_per_year, frequency, median_gap = infer_periods_per_year(series.index)
    volatility = float(periodic_returns.std(ddof=1) * math.sqrt(periods_per_year))

    running_peak = series.cummax()
    drawdowns = series / running_peak - 1
    trough_date = drawdowns.idxmin()
    max_drawdown = float(drawdowns.loc[trough_date])
    peak_value = float(running_peak.loc[trough_date])
    peak_candidates = series.loc[:trough_date]
    peak_date = peak_candidates.loc[peak_candidates == peak_value].index[-1]
    after_trough = series.loc[trough_date:]
    recovered = after_trough.loc[after_trough >= peak_value]
    recovery_date = recovered.index[0].date().isoformat() if not recovered.empty else None

    windows: list[WindowResult] = []
    for years, label in ((1, "1Y"), (3, "3Y"), (5, "5Y"), (10, "10Y")):
        target = end_date - pd.DateOffset(years=years)
        if start_date <= target:
            result = make_window(series, target, label)
            if result:
                windows.append(result)

    calendars = calendar_returns(series)
    complete_calendars = [row for row in calendars if not row["partial_start_year"]]
    worst_calendar = min(complete_calendars, key=lambda row: row["return"]) if complete_calendars else None

    return {
        "series": {
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "observations": int(len(series)),
            "inferred_frequency": frequency,
            "median_gap_days": median_gap,
            "elapsed_years": elapsed,
        },
        "performance": {
            "cumulative_return": cumulative,
            "annualized_return": cagr,
            "annualized_volatility": volatility,
            "volatility_periods_per_year": periods_per_year,
        },
        "maximum_drawdown": {
            "drawdown": max_drawdown,
            "peak_date": peak_date.date().isoformat(),
            "trough_date": trough_date.date().isoformat(),
            "recovery_date": recovery_date,
            "recovered_by_end": recovery_date is not None,
        },
        "trailing_windows": [asdict(item) for item in windows],
        "calendar_year_returns": calendars,
        "worst_complete_calendar_year": worst_calendar,
        "warnings": [
            "Results inherit the economic meaning and quality of the input series.",
            "The script does not adjust distributions, fees, taxes, inflation, or currency.",
            "Maximum drawdown is historical and frequency-dependent, not a worst-case forecast.",
        ],
    }


def pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.2f}%"


def render_markdown(result: dict[str, object]) -> str:
    series = result["series"]
    performance = result["performance"]
    drawdown = result["maximum_drawdown"]
    lines = [
        "# Historical return analysis",
        "",
        f"Series: {series['start_date']} to {series['end_date']} | {series['observations']} observations | inferred {series['inferred_frequency']} frequency",
        "",
        "| Metric | Result |",
        "| --- | ---: |",
        f"| Cumulative return | {pct(performance['cumulative_return'])} |",
        f"| Annualized return (CAGR) | {pct(performance['annualized_return'])} |",
        f"| Annualized volatility | {pct(performance['annualized_volatility'])} |",
        f"| Maximum drawdown | {pct(drawdown['drawdown'])} |",
        f"| Drawdown peak | {drawdown['peak_date']} |",
        f"| Drawdown trough | {drawdown['trough_date']} |",
        f"| Recovery | {drawdown['recovery_date'] or 'not recovered by series end'} |",
        "",
        "## Trailing windows",
        "",
        "| Window | Actual dates | Cumulative | Annualized |",
        "| --- | --- | ---: | ---: |",
    ]
    for item in result["trailing_windows"]:
        lines.append(
            f"| {item['label']} | {item['start_date']} to {item['end_date']} | "
            f"{pct(item['cumulative_return'])} | {pct(item['annualized_return'])} |"
        )
    if not result["trailing_windows"]:
        lines.append("| n/a | Series is shorter than one complete year | n/a | n/a |")

    lines.extend(["", "## Calendar-year returns", "", "| Year | Return | Note |", "| ---: | ---: | --- |"])
    for row in result["calendar_year_returns"]:
        note = "partial start year" if row["partial_start_year"] else ""
        lines.append(f"| {row['year']} | {pct(row['return'])} | {note} |")
    lines.extend(["", "Warnings:"])
    lines.extend(f"- {warning}" for warning in result["warnings"])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    try:
        series = load_series(args.csv, args.date_column, args.value_column)
        result = analyze(series)
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
