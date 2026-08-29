# Historical-performance and evidence methodology

Read this file whenever the answer contains historical returns, drawdowns, volatility, fees, holdings, current product terms, or a numeric product comparison.

## 1. Resolve the instrument before collecting data

Record the exact product name, ticker or ISIN, share class, listing venue, trading currency, base currency, distribution/accumulation policy, currency-hedging status, leverage/inverse multiplier, benchmark, and inception date. Do not treat similarly named funds as interchangeable.

Distinguish these layers:

1. **Economic exposure:** the underlying stocks, bonds, commodities, loans, properties, cash flows, or derivatives.
2. **Benchmark:** the index or reference rate, which may be a calculation rather than an investable asset.
3. **Vehicle:** ETF, mutual fund, QDII fund, bank wealth product, policy, note, or account.
4. **Investor outcome:** vehicle performance after fees, taxes, tracking, trading, currency conversion, premium/discount, and investor timing.

## 2. Source hierarchy

Use current research for time-sensitive facts. Prefer, in order:

1. official prospectus, key information document, annual/semiannual report, factsheet, fund or issuer page;
2. exchange, regulator, central bank, government statistics, or index-provider methodology and index data;
3. audited filings and established institutional data providers;
4. reputable secondary databases for cross-checking;
5. media or commentary only for contextual interpretation, not as the sole source for product terms.

Use at least one primary source for product identity, fees, holdings, maturity/redemption rules, guarantees, leverage, and benchmark. Use direct links and state `截至 YYYY-MM-DD`. If two sources disagree, show the discrepancy and prefer the source closest to the legal product record.

Do not cite a search-result snippet. Do not assert a historical drawdown cause solely because a news event occurred nearby; label causal attribution as a likely interpretation unless supported by stronger evidence.

## 3. Return convention

Prefer an official total-return index, adjusted close, or NAV series that reinvests distributions. State whether the result is:

- **price return**, which ignores cash distributions;
- **total return**, which reinvests dividends/coupons/distributions;
- **NAV return**, which measures the fund's net asset value;
- **market-price return**, which also reflects ETF premium/discount and trading conditions;
- gross or net of fees and taxes.

Never compare one product's price return with another product's total return without prominently disclosing the mismatch. For a user whose spending currency differs from the asset currency, either calculate base-currency return or show local-asset and FX effects separately:

`(1 + base-currency return) = (1 + local-asset return) × (1 + FX return)`

Here, `FX return` is the percentage change in the amount of the user's base currency received for one unit of the asset currency. Currency-hedged share classes require their own series; do not simulate them by simply deleting spot FX movement because hedge costs and basis matter.

## 4. Metrics and formulas

Let `V0` be the starting adjusted value, `VT` the ending adjusted value, and `Y` the elapsed years.

- Cumulative return: `VT / V0 − 1`. It answers how much one lump-sum investment changed over the whole interval.
- Annualized return (CAGR): `(VT / V0)^(1/Y) − 1`. It is the constant yearly rate that would connect the endpoints; it does not mean each year earned that rate.
- Period return: `Vt / V(t−1) − 1`.
- Annualized volatility: sample standard deviation of periodic returns multiplied by the square root of observations per year. It describes dispersion, not the probability of permanent loss.
- Drawdown at time `t`: `Vt / max(V up to t) − 1`.
- Maximum drawdown: the most negative drawdown. Report the prior peak date, trough date, depth, and the first date the prior peak was regained. If not regained by the data end date, say so.

Maximum drawdown is sample-dependent: a daily series can reveal a deeper intraperiod fall than monthly data. State the frequency. A since-inception record excludes all crises before inception.

Also show, when useful, worst calendar year, rolling-period outcome range, and real return after inflation. Sharpe ratios or similar risk-adjusted measures require a stated risk-free rate and consistent frequency; do not use them as a universal ranking.

## 5. Fair comparison rules

For high-risk versus low-risk comparisons:

- use the intersection of available dates for the primary side-by-side table;
- use the same base currency, total/price-return convention, frequency, and tax/fee treatment;
- separately show longer individual histories if decision-relevant;
- identify whether the “low-risk” comparator matches the user's horizon and currency (for example, a three-month Treasury bill is not the same liability match as a ten-year bond);
- show drawdown and recovery, not only average return;
- note survivorship, backfill, benchmark changes, and delisted/closed-product bias where relevant.

A benchmark history before product launch is **proxy history**. Backtests, simulated index histories, and hypothetical reinvestment must be labelled; they are not live investor returns.

## 6. Running the bundled calculator

The input CSV must contain one row per observation, a date column, and a strictly positive adjusted-price, total-return-index, or adjusted-NAV column. Sort order and duplicate dates are handled, but the economic meaning of the values must be verified first.

```bash
python scripts/analyze_returns.py prices.csv --date-column Date --value-column Adj_Close
```

Use `--format json` for machine-readable output. The script calculates endpoint returns, inferred-frequency volatility, maximum drawdown and recovery, trailing windows, and calendar-year returns. It does not fetch data, adjust distributions, convert currency, infer fees, or explain causes. Cite the original data source rather than the script.

## 7. Minimum disclosure beside numbers

Every performance table should state:

- exact instrument and share class;
- start and end dates, data frequency, and data end date;
- currency and whether converted;
- total return, price return, or NAV return;
- distribution reinvestment assumption;
- fee/tax treatment;
- source links;
- proxy, simulation, or missing-data limitations.

Round percentages sensibly—normally one decimal place. Extra decimals do not create accuracy.
