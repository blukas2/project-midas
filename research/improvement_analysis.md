# Project Midas — Improvement Analysis Report

*Generated: March 29, 2026*

## What the App Does Today

Project Midas is a desktop portfolio analysis tool (tkinter + yfinance) that lets you create portfolios of stocks/ETFs, fetch 15 years of history, and view returns, volatility, and correlations. It supports EUR conversion, backcasting via linear regression, and side-by-side asset comparison.

**Currently calculated metrics:** periodic returns (1m–3y), annualized returns (1y–10y), volatility (1y–10y), correlation matrix, and indexed price series.

---

## Metrics the Application Should Calculate

### 1. Risk-Adjusted Return Metrics (Highest Priority)

These are the foundation of any investment decision. Raw returns are meaningless without context on the risk taken.

| Metric | What It Tells You | Formula Sketch |
|---|---|---|
| **Sharpe Ratio** (already in TODO) | Return per unit of *total* risk vs. risk-free rate | (Rp - Rf) / σp |
| **Sortino Ratio** | Return per unit of *downside* risk — penalizes only negative volatility | (Rp - Rf) / σ_downside |
| **Calmar Ratio** | Return relative to worst drawdown | Annualized Return / Max Drawdown |
| **Information Ratio** | Active return per unit of tracking error vs. a benchmark | (Rp - Rb) / σ(p-b) |
| **Treynor Ratio** | Return per unit of *systematic* (market) risk | (Rp - Rf) / βp |

**Why it matters:** The app currently shows volatility and returns separately. A user seeing "Fund A: 12% return, 18% vol" vs "Fund B: 10% return, 8% vol" has no single number to compare. Sharpe/Sortino solve this instantly.

### 2. Drawdown Metrics (High Priority)

Understanding worst-case scenarios is critical for portfolio sizing and risk tolerance.

| Metric | What It Tells You |
|---|---|
| **Maximum Drawdown** | Largest peak-to-trough decline — "how much could I have lost?" |
| **Maximum Drawdown Duration** | How long until recovery — "how long would I be underwater?" |
| **Current Drawdown** | Distance from all-time high — "am I buying at a discount or peak?" |
| **Drawdown Chart** | Visual timeline of underwater periods |

**Why it matters:** A portfolio with 15% annualized return but a 60% max drawdown is very different from one with 12% return and 20% max drawdown. Most investors can't stomach large drawdowns psychologically, so this directly affects decision quality.

### 3. Portfolio Construction Metrics (High Priority)

These help answer "is my portfolio well-constructed?"

| Metric | What It Tells You |
|---|---|
| **Beta** (to benchmark) | Systematic risk exposure — how much the portfolio moves with the market |
| **Alpha** (Jensen's Alpha) | Excess return above what beta alone would predict |
| **R-squared** | How much of the portfolio's movement is explained by the benchmark |
| **Tracking Error** | Standard deviation of active returns vs. benchmark |
| **Concentration Risk** (HHI) | Herfindahl-Hirschman Index of portfolio weights — is the portfolio too concentrated? |
| **Effective Number of Assets** | 1 / Σwi² — "how diversified am I really?" |

**Why it matters:** The app shows a correlation matrix, but doesn't tie it back to portfolio-level diversification quality. A user could have 10 assets that are all 0.95 correlated — effectively one bet. These metrics expose that.

### 4. Distribution & Tail Risk Metrics (Medium Priority)

Returns aren't normally distributed. Fat tails matter enormously.

| Metric | What It Tells You |
|---|---|
| **Skewness** | Asymmetry of returns — negative skew = more large losses than gains |
| **Kurtosis** | Tail fatness — high kurtosis = extreme events more likely than normal |
| **Value at Risk (VaR)** | "At 95% confidence, the worst daily/monthly loss is X%" |
| **Conditional VaR (CVaR/ES)** | "When losses exceed VaR, the *average* loss is X%" — better tail measure |

**Why it matters:** Two portfolios can have identical volatility but very different tail risk. VaR/CVaR are standard institutional measures that would make the app significantly more sophisticated.

### 5. Income & Total Return Metrics (Medium Priority)

The app currently only tracks price returns, missing a major component.

| Metric | What It Tells You |
|---|---|
| **Dividend Yield** | Current income stream |
| **Total Return** (price + dividends) | True investment return — can differ massively from price return over 10+ years |
| **Dividend Growth Rate** | Sustainability and growth of income |
| **Yield on Cost** | Current dividend relative to original purchase price |

**Why it matters:** Over 10 years, dividends can account for 30–50% of total return for equity portfolios. Ignoring them materially misrepresents performance. yfinance provides dividend data — it's already accessible.

### 6. Benchmark Comparison Metrics (Medium Priority)

Currently there's no way to answer "am I beating the market?"

| Feature | What It Tells You |
|---|---|
| **Benchmark Overlay** | Portfolio value vs. a chosen index (S&P 500, MSCI World, etc.) |
| **Relative Performance Chart** | Portfolio return minus benchmark return over time |
| **Rolling Alpha/Beta** | How alpha and beta change over time (not static) |
| **Up/Down Capture Ratio** | In up markets, do you capture more? In down markets, do you lose less? |

**Why it matters:** Without a benchmark, there's no way to evaluate whether the portfolio's complexity and risk are justified. A portfolio returning 8%/year when a simple index fund returns 10% is destroying value.

### 7. Rolling Window Analysis (Medium Priority)

Static metrics over fixed periods hide regime changes.

| Metric | What It Tells You |
|---|---|
| **Rolling Returns** (e.g., 1y rolling) | Performance consistency over time |
| **Rolling Volatility** | Is risk stable or spiking? |
| **Rolling Sharpe** | Is the risk-return tradeoff deteriorating? |
| **Rolling Correlation** | Are diversification benefits stable or breaking down in crises? |

**Why it matters:** A 5-year Sharpe of 0.8 could mean consistent 0.8 — or it could mean 1.5 for 4 years then -0.5 for the last year. Rolling windows expose whether recent behavior matches the aggregate.

### 8. What-If / Scenario Analysis (Lower Priority but High Value)

| Feature | What It Tells You |
|---|---|
| **Stress Testing** | "What would happen in a 2008-style crash?" Apply historical drawdowns to current portfolio |
| **Monte Carlo Simulation** | Projected distribution of future outcomes with confidence bands |
| **Rebalancing Impact** | "What if I shift 10% from asset A to B?" — preview the risk/return impact |
| **Position Sizing** | Given a target volatility, what % should each asset be? |

---

## Structural / UX Improvements to Support Better Decisions

| Area | Current Gap | Recommendation |
|---|---|---|
| **Benchmark selection** | No benchmarks exist | Let users pick a reference index per portfolio |
| **Risk-free rate** | Not configurable | Needed for Sharpe/Sortino — pull from ECB/Treasury yields or let user set |
| **Time period flexibility** | Fixed periods (1y, 3y, 5y, 10y) | Allow custom date ranges for all metrics |
| **Dashboard summary** | 6 separate charts, no single number | Add a summary card: total value, total return, Sharpe, max drawdown, current drawdown |
| **Portfolio comparison** | Only single-asset comparison exists | Compare two entire portfolios side-by-side |
| **Export/reporting** | No export capability | PDF/CSV report generation for periodic review |
| **Alerts / thresholds** | None | Flag when drawdown exceeds X%, correlation spikes, etc. |
| **Total return mode** | Price-only returns | Toggle between price return and total return (with dividends) |

---

## Prioritized Implementation Roadmap (Suggested)

**Phase 1 — Core risk-adjusted metrics:**
Sharpe ratio, Sortino ratio, max drawdown, max drawdown duration, total return (with dividends), benchmark overlay

**Phase 2 — Portfolio quality:**
Beta, alpha, concentration risk (HHI), VaR/CVaR, up/down capture ratio

**Phase 3 — Dynamic analysis:**
Rolling windows (returns, vol, Sharpe, correlation), drawdown chart, relative performance chart

**Phase 4 — Forward-looking tools:**
Stress testing with historical scenarios, Monte Carlo projection, rebalancing preview, position sizing

---

## Key Architectural Observations

- The `ReturnsCalculator` class is a good starting point but will need to grow into a broader `MetricsEngine` or be supplemented by parallel calculator classes (risk calculator, drawdown calculator, etc.) to keep class sizes under 200 lines per the repo's coding standards.
- Dividend data from yfinance (`ticker.dividends`) is already available through the existing data pipeline — no new data source needed for total returns.
- A risk-free rate configuration belongs in `config.py` alongside the existing currency setting.
- The hardcoded user path in `location.py` / `settings.py` should be resolved before any new features compound the technical debt.
