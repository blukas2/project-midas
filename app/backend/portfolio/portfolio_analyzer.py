from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from yfinance import Ticker

from backend.portfolio.components import Asset, CrossFx
from backend.globals.config import CURRENCY

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.portfolio.portfolio import Portfolio

logger = logging.getLogger(__name__)

BENCHMARK_TICKER = "^990100-USD-STRD"
BENCHMARK_CURRENCY = "USD"
RISK_FREE_RATE = 0.03
VAR_CONFIDENCE = 0.95
TRADING_DAYS_PER_YEAR = 252


@dataclass
class AnalysisResult:
    annualized_return_10y: float = 0.0
    annualized_return_10y_text: str = ""
    annualized_return_5y: float = 0.0
    annualized_return_5y_text: str = ""
    beta: float = 0.0
    beta_text: str = ""
    alpha: float = 0.0
    alpha_text: str = ""
    information_ratio: float = 0.0
    information_ratio_text: str = ""
    sharpe_ratio: float = 0.0
    sharpe_text: str = ""
    var_95: float = 0.0
    var_text: str = ""
    cvar_95: float = 0.0
    cvar_text: str = ""
    max_drawdown: float = 0.0
    max_drawdown_text: str = ""
    max_drawdown_duration_days: int = 0
    max_drawdown_duration_text: str = ""
    diversification_ratio: float = 0.0
    diversification_text: str = ""
    effective_bets: float = 0.0
    effective_bets_text: str = ""
    risk_contributions: dict[str, float] = field(default_factory=dict)
    risk_contributions_text: str = ""
    return_contributions: dict[str, float] = field(default_factory=dict)
    return_contributions_text: str = ""
    num_assets: int = 0


class PortfolioAnalyzer:
    """Computes advanced risk/return metrics for a portfolio."""

    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio
        self.interpreter = AnalysisInterpreter()

    def analyze(self) -> AnalysisResult:
        """Run all portfolio analysis metrics and return results."""
        benchmark_returns = self._load_benchmark_returns()
        portfolio_returns = self._get_portfolio_daily_returns()
        aligned = self._align_return_series(portfolio_returns, benchmark_returns)
        weights, asset_returns = self._compute_weights_and_asset_returns()

        result = AnalysisResult(num_assets=len(self.portfolio.content))
        self._fill_annualized_return(result)
        self._fill_beta_alpha(result, aligned)
        self._fill_information_ratio(result, aligned)
        self._fill_sharpe(result, portfolio_returns)
        self._fill_var(result, portfolio_returns)
        self._fill_cvar(result, portfolio_returns)
        self._fill_max_drawdown(result)
        self._fill_diversification(result, weights, asset_returns)
        self._fill_effective_bets(result)
        self._fill_risk_contributions(result, weights, asset_returns)
        self._fill_return_contributions(result, weights, asset_returns)
        return result

    def _load_benchmark_returns(self) -> pd.Series:
        """Load MSCI World daily returns converted to EUR."""
        benchmark = Ticker(BENCHMARK_TICKER)
        df = benchmark.history(period="15y")
        if df.empty:
            logger.warning("No benchmark data found for %s.", BENCHMARK_TICKER)
            return pd.Series(dtype=float)
        df = self._prepare_benchmark_prices(df, benchmark)
        return df['Price'].pct_change().dropna()

    def _prepare_benchmark_prices(self, df: pd.DataFrame, benchmark: Ticker) -> pd.DataFrame:
        """Convert benchmark prices to EUR and index by Date."""
        df = df.rename(columns={'Close': 'Price'})
        df.reset_index(inplace=True)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        if benchmark.fast_info['currency'] != CURRENCY:
            cross_fx = CrossFx(target_fx=CURRENCY, source_fx=BENCHMARK_CURRENCY)
            fx = cross_fx.price_history[['Date', 'FX Rate']].set_index('Date')
            df = df.join(fx, on='Date', how='left')
            df['Price'] = df['Price'] / df['FX Rate']
        return df.set_index('Date')[['Price']].dropna()

    def _get_portfolio_daily_returns(self) -> pd.Series:
        """Compute daily returns from portfolio value history."""
        history = self.portfolio.history.set_index('Date')
        return history['Value'].pct_change().dropna()

    def _align_return_series(self, portfolio: pd.Series, benchmark: pd.Series) -> pd.DataFrame:
        """Align portfolio and benchmark returns to common dates."""
        df = pd.DataFrame({'portfolio': portfolio, 'benchmark': benchmark})
        return df.dropna()

    def _compute_weights_and_asset_returns(self) -> tuple[np.ndarray, pd.DataFrame]:
        """Compute asset weights (by value) and a DataFrame of daily returns per asset."""
        prices_df = self.portfolio.build_combined_price_dataframe()
        returns_df = prices_df.pct_change().dropna()

        latest_values = self._get_latest_asset_values()
        total_value = sum(latest_values.values())
        tickers = list(returns_df.columns)
        weights = np.array([latest_values.get(t, 0) / total_value for t in tickers])
        return weights, returns_df

    def _get_latest_asset_values(self) -> dict[str, float]:
        """Get each asset's latest value from its price history."""
        values = {}
        for ticker, asset in self.portfolio.content.items():
            last_row = asset.price_history.iloc[-1]
            values[ticker] = last_row['Value']
        return values

    # --- Annualized Return (10y & 5y) ---

    def _fill_annualized_return(self, result: AnalysisResult):
        """Read the 10-year and 5-year annualized returns from the portfolio."""
        self._fill_annualized_return_for_period(result, '10y')
        self._fill_annualized_return_for_period(result, '5y')

    def _fill_annualized_return_for_period(self, result: AnalysisResult, period: str):
        annualized = self.portfolio.annualized_returns.get(period)
        value_attr = f'annualized_return_{period}'
        text_attr = f'annualized_return_{period}_text'
        if annualized is None:
            setattr(result, text_attr, f"Not enough history for a {period} annualized return.")
            return
        rounded = round(annualized, 2)
        setattr(result, value_attr, rounded)
        setattr(result, text_attr, self.interpreter.interpret_annualized_return(rounded))

    # --- Beta & Alpha ---

    def _fill_beta_alpha(self, result: AnalysisResult, aligned: pd.DataFrame):
        cov_matrix = aligned.cov()
        beta = cov_matrix.loc['portfolio', 'benchmark'] / cov_matrix.loc['benchmark', 'benchmark']
        result.beta = round(beta, 3)
        result.beta_text = self.interpreter.interpret_beta(beta)

        alpha = self._compute_alpha(aligned, beta)
        result.alpha = round(alpha, 3)
        result.alpha_text = self.interpreter.interpret_alpha(alpha)

    def _compute_alpha(self, aligned: pd.DataFrame, beta: float) -> float:
        """Jensen's Alpha: annualized portfolio return minus CAPM-expected return."""
        port_annual = self._annualize_return(aligned['portfolio'])
        bench_annual = self._annualize_return(aligned['benchmark'])
        expected = RISK_FREE_RATE + beta * (bench_annual - RISK_FREE_RATE)
        return (port_annual - expected) * 100

    def _annualize_return(self, daily_returns: pd.Series) -> float:
        n_days = len(daily_returns)
        if n_days == 0:
            return 0.0
        cumulative = (1 + daily_returns).prod()
        if cumulative <= 0:
            return -1.0
        return cumulative ** (TRADING_DAYS_PER_YEAR / n_days) - 1

    # --- Information Ratio ---

    def _fill_information_ratio(self, result: AnalysisResult, aligned: pd.DataFrame):
        active_returns = aligned['portfolio'] - aligned['benchmark']
        tracking_error = active_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
        excess_return = self._annualize_return(aligned['portfolio']) - self._annualize_return(aligned['benchmark'])
        ir = excess_return / tracking_error if tracking_error != 0 else 0
        result.information_ratio = round(ir, 3)
        result.information_ratio_text = self.interpreter.interpret_information_ratio(ir)

    # --- Sharpe Ratio ---

    def _fill_sharpe(self, result: AnalysisResult, portfolio_returns: pd.Series):
        annual_return = self._annualize_return(portfolio_returns)
        annual_vol = portfolio_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
        sharpe = (annual_return - RISK_FREE_RATE) / annual_vol if annual_vol != 0 else 0
        result.sharpe_ratio = round(sharpe, 3)
        result.sharpe_text = self.interpreter.interpret_sharpe(sharpe)

    # --- Value at Risk ---

    def _fill_var(self, result: AnalysisResult, portfolio_returns: pd.Series):
        monthly_returns = self._resample_to_monthly(portfolio_returns)
        var_value = np.percentile(monthly_returns, (1 - VAR_CONFIDENCE) * 100)
        result.var_95 = round(var_value * 100, 2)
        result.var_text = self.interpreter.interpret_var(result.var_95)

    def _resample_to_monthly(self, daily_returns: pd.Series) -> pd.Series:
        """Resample daily returns to monthly returns via compounding."""
        daily_returns = daily_returns.copy()
        daily_returns.index = pd.to_datetime(daily_returns.index)
        monthly = (1 + daily_returns).resample('M').prod() - 1
        return monthly.dropna()

    # --- Conditional Value at Risk ---

    def _fill_cvar(self, result: AnalysisResult, portfolio_returns: pd.Series):
        """CVaR (Expected Shortfall): average loss beyond the VaR threshold."""
        monthly_returns = self._resample_to_monthly(portfolio_returns)
        var_threshold = np.percentile(monthly_returns, (1 - VAR_CONFIDENCE) * 100)
        tail_losses = monthly_returns[monthly_returns <= var_threshold]
        cvar = tail_losses.mean() if len(tail_losses) > 0 else var_threshold
        result.cvar_95 = round(cvar * 100, 2)
        result.cvar_text = self.interpreter.interpret_cvar(result.cvar_95)

    # --- Maximum Drawdown & Duration ---

    def _fill_max_drawdown(self, result: AnalysisResult):
        """Compute maximum drawdown percentage and its duration in days."""
        history = self.portfolio.history.copy()
        history = history.sort_values('Date')
        cumulative_max = history['Value'].cummax()
        drawdown = (history['Value'] - cumulative_max) / cumulative_max
        result.max_drawdown = round(drawdown.min() * 100, 2)
        result.max_drawdown_text = self.interpreter.interpret_max_drawdown(result.max_drawdown)

        duration = self._compute_max_drawdown_duration(history, cumulative_max)
        result.max_drawdown_duration_days = duration
        result.max_drawdown_duration_text = self.interpreter.interpret_drawdown_duration(duration)

    def _compute_max_drawdown_duration(self, history: pd.DataFrame, cumulative_max: pd.Series) -> int:
        """Find the longest period (in calendar days) spent below a previous peak."""
        dates = history['Date'].values
        is_at_peak = (history['Value'].values >= cumulative_max.values)
        max_duration = 0
        current_start = None
        for i, at_peak in enumerate(is_at_peak):
            if not at_peak and current_start is None:
                current_start = dates[i]
            elif at_peak and current_start is not None:
                duration = (dates[i] - current_start).days
                max_duration = max(max_duration, duration)
                current_start = None
        if current_start is not None:
            duration = (dates[-1] - current_start).days
            max_duration = max(max_duration, duration)
        return max_duration

    # --- Diversification Ratio ---

    def _fill_diversification(self, result: AnalysisResult, weights: np.ndarray, asset_returns: pd.DataFrame):
        individual_vols = asset_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
        if individual_vols.isna().any():
            result.diversification_ratio = 1.0
            result.diversification_text = self.interpreter.interpret_diversification(1.0)
            return
        weighted_avg_vol = np.dot(weights, individual_vols.values)
        portfolio_vol = self._compute_portfolio_volatility(weights, asset_returns)
        ratio = weighted_avg_vol / portfolio_vol if portfolio_vol != 0 else 1.0
        result.diversification_ratio = round(ratio, 3)
        result.diversification_text = self.interpreter.interpret_diversification(ratio)

    def _compute_portfolio_volatility(self, weights: np.ndarray, asset_returns: pd.DataFrame) -> float:
        cov_matrix = asset_returns.cov() * TRADING_DAYS_PER_YEAR
        port_var = weights @ cov_matrix.values @ weights
        if np.isnan(port_var) or port_var < 0:
            return 0.0
        return np.sqrt(port_var)

    # --- Effective Independent Bets ---

    def _fill_effective_bets(self, result: AnalysisResult):
        corr_matrix = self.portfolio.correlation_matrix.values
        eigenvalues = np.linalg.eigh(corr_matrix)[0]
        eigenvalues = eigenvalues[eigenvalues > 0]
        sum_eig = eigenvalues.sum()
        sum_eig_sq = (eigenvalues ** 2).sum()
        effective = (sum_eig ** 2) / sum_eig_sq if sum_eig_sq != 0 else 1.0
        result.effective_bets = round(effective, 2)
        result.effective_bets_text = self.interpreter.interpret_effective_bets(
            effective, result.num_assets
        )

    # --- Risk Contribution Breakdown ---

    def _fill_risk_contributions(self, result: AnalysisResult, weights: np.ndarray, asset_returns: pd.DataFrame):
        cov_matrix = asset_returns.cov().values * TRADING_DAYS_PER_YEAR
        port_var = weights @ cov_matrix @ weights
        if np.isnan(port_var) or port_var <= 0:
            tickers = list(asset_returns.columns)
            result.risk_contributions = {t: 0.0 for t in tickers}
            result.risk_contributions_text = self.interpreter.interpret_risk_contributions(
                result.risk_contributions
            )
            return
        port_vol = np.sqrt(port_var)
        marginal = (cov_matrix @ weights) / port_vol

        tickers = list(asset_returns.columns)
        contributions = weights * marginal
        total = contributions.sum()
        result.risk_contributions = {
            tickers[i]: round(contributions[i] / total * 100, 1) if total != 0 else 0
            for i in range(len(tickers))
        }
        result.risk_contributions_text = self.interpreter.interpret_risk_contributions(
            result.risk_contributions
        )


    # --- Return Contribution Breakdown ---

    def _fill_return_contributions(self, result: AnalysisResult, weights: np.ndarray, asset_returns: pd.DataFrame):
        """Compute each asset's weighted contribution to the portfolio's annualized return."""
        tickers = list(asset_returns.columns)
        annualized_per_asset = self._annualize_asset_returns(asset_returns, tickers)
        contributions = {t: round(weights[i] * annualized_per_asset[t] * 100, 2) for i, t in enumerate(tickers)}
        result.return_contributions = contributions
        result.return_contributions_text = self.interpreter.interpret_return_contributions(contributions)

    def _annualize_asset_returns(self, asset_returns: pd.DataFrame, tickers: list[str]) -> dict[str, float]:
        """Annualize daily returns for each asset."""
        return {t: self._annualize_return(asset_returns[t]) for t in tickers}


class AnalysisInterpreter:
    """Converts raw metric values into human-readable descriptions."""

    def interpret_annualized_return(self, annual_pct: float) -> str:
        if annual_pct < 0:
            return f"Annualized return of {annual_pct:.2f}%: the portfolio lost value."
        elif annual_pct < 5:
            return f"Annualized return of {annual_pct:.2f}%: modest growth."
        elif annual_pct < 10:
            return f"Annualized return of {annual_pct:.2f}%: solid growth."
        else:
            return f"Annualized return of {annual_pct:.2f}%: strong growth."

    def interpret_beta(self, beta: float) -> str:
        if beta < 0.8:
            return f"Beta of {beta:.2f}: your portfolio is defensive, moving less than the market."
        elif beta <= 1.2:
            return f"Beta of {beta:.2f}: your portfolio tracks the market closely."
        else:
            return f"Beta of {beta:.2f}: your portfolio is aggressive, amplifying market moves."

    def interpret_alpha(self, alpha: float) -> str:
        if alpha < 0:
            return f"Alpha of {alpha:.2f}%: the portfolio underperforms what beta alone would predict."
        elif alpha <= 2:
            return f"Alpha of {alpha:.2f}%: modest excess return above the CAPM expectation."
        else:
            return f"Alpha of {alpha:.2f}%: strong outperformance beyond market exposure."

    def interpret_information_ratio(self, ir: float) -> str:
        if ir < 0:
            return f"IR of {ir:.2f}: negative excess return per unit of active risk."
        elif ir < 0.4:
            return f"IR of {ir:.2f}: low consistency of excess returns over the benchmark."
        elif ir < 0.7:
            return f"IR of {ir:.2f}: moderate, fairly consistent outperformance."
        else:
            return f"IR of {ir:.2f}: strong, consistent alpha generation."

    def interpret_sharpe(self, sharpe: float) -> str:
        if sharpe < 0:
            return f"Sharpe of {sharpe:.2f}: returns are below the risk-free rate."
        elif sharpe < 0.5:
            return f"Sharpe of {sharpe:.2f}: poor risk-adjusted returns."
        elif sharpe < 1.0:
            return f"Sharpe of {sharpe:.2f}: adequate risk-adjusted returns."
        elif sharpe < 2.0:
            return f"Sharpe of {sharpe:.2f}: good risk-adjusted returns."
        else:
            return f"Sharpe of {sharpe:.2f}: excellent risk-adjusted returns."

    def interpret_var(self, var_pct: float) -> str:
        return (
            f"At 95% confidence, the worst monthly loss is {var_pct:.2f}%."
            f" In 1 out of 20 months, losses could exceed this."
        )

    def interpret_cvar(self, cvar_pct: float) -> str:
        return (
            f"When monthly losses exceed VaR, the average loss is {cvar_pct:.2f}%."
            f" This measures the severity of tail-risk events."
        )

    def interpret_max_drawdown(self, drawdown_pct: float) -> str:
        if drawdown_pct > -10:
            return f"Max drawdown of {drawdown_pct:.2f}%: relatively shallow, low historical risk."
        elif drawdown_pct > -25:
            return f"Max drawdown of {drawdown_pct:.2f}%: moderate — typical for diversified equity."
        elif drawdown_pct > -40:
            return f"Max drawdown of {drawdown_pct:.2f}%: significant — requires strong conviction to hold."
        else:
            return f"Max drawdown of {drawdown_pct:.2f}%: severe — very painful for most investors."

    def interpret_drawdown_duration(self, days: int) -> str:
        if days == 0:
            return "No drawdown period detected."
        months = days / 30
        if months < 6:
            return f"Longest underwater period: {days} days (~{months:.0f} months) — quick recovery."
        elif months < 24:
            return f"Longest underwater period: {days} days (~{months:.0f} months) — extended recovery."
        else:
            years = months / 12
            return f"Longest underwater period: {days} days (~{years:.1f} years) — very long recovery."

    def interpret_diversification(self, ratio: float) -> str:
        if ratio < 1.05:
            return "Ratio near 1.0: little diversification benefit between holdings."
        elif ratio < 1.5:
            return f"Ratio of {ratio:.2f}: moderate diversification benefit."
        else:
            return f"Ratio of {ratio:.2f}: strong diversification — holdings offset each other well."

    def interpret_effective_bets(self, bets: float, num_assets: int) -> str:
        if num_assets <= 1:
            return f"{bets:.1f} independent bet from {num_assets} asset."
        ratio = bets / num_assets
        if ratio > 0.7:
            return f"{bets:.1f} independent bets from {num_assets} assets — most holdings are distinct."
        elif ratio > 0.4:
            return f"{bets:.1f} independent bets from {num_assets} assets — some overlap between holdings."
        else:
            return f"{bets:.1f} independent bets from {num_assets} assets — many holdings move together."

    def interpret_risk_contributions(self, contributions: dict[str, float]) -> str:
        dominant = [f"{t} ({v:.1f}%)" for t, v in contributions.items() if v > 30]
        if dominant:
            return f"Dominant risk contributors: {', '.join(dominant)}. Consider rebalancing."
        return "Risk is reasonably spread across holdings."

    def interpret_return_contributions(self, contributions: dict[str, float]) -> str:
        total = sum(contributions.values())
        top = max(contributions, key=contributions.get) if contributions else None
        if top is None:
            return "No return contribution data available."
        return f"Portfolio annualized return: {total:.2f}%. Largest contributor: {top} ({contributions[top]:.2f}%)."
