from datetime import date
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from backend.portfolio.portfolio_analyzer import (
    BENCHMARK_CURRENCY,
    BENCHMARK_TICKER,
    AnalysisInterpreter,
    AnalysisResult,
    PortfolioAnalyzer,
)


class TestAnalysisInterpreter:
    @pytest.mark.parametrize(
        ("value", "word"),
        [(-1, "lost"), (2, "modest"), (7, "solid"), (12, "strong")],
    )
    def test_annualized_return_interpretations(self, value, word):
        assert word in AnalysisInterpreter().interpret_annualized_return(value)

    def test_empty_contribution_interpretation(self):
        assert AnalysisInterpreter().interpret_return_contributions({}) == "No return contribution data available."


class TestPortfolioAnalyzer:
    def test_prepare_benchmark_prices_converts_non_eur_currency(self, monkeypatch):
        analyzer = PortfolioAnalyzer.__new__(PortfolioAnalyzer)
        benchmark = SimpleNamespace(fast_info={"currency": "USD"})
        dates = pd.to_datetime(["2024-01-01", "2024-01-02"])
        fx = SimpleNamespace(
            price_history=pd.DataFrame({"Date": dates.date, "FX Rate": [2.0, 2.0]})
        )
        monkeypatch.setattr(
            "backend.portfolio.portfolio_analyzer.CrossFx",
            lambda target_fx, source_fx: fx,
        )
        frame = pd.DataFrame({"Close": [20.0, 22.0]}, index=pd.DatetimeIndex(dates, name="Date"))

        actual = analyzer._prepare_benchmark_prices(frame, benchmark)

        assert actual["Price"].tolist() == [10.0, 11.0]
        assert actual.index.tolist() == dates.date.tolist()

    def test_load_benchmark_returns_handles_empty_and_populated_history(self, monkeypatch):
        analyzer = PortfolioAnalyzer.__new__(PortfolioAnalyzer)
        monkeypatch.setattr(
            "backend.portfolio.portfolio_analyzer.Ticker",
            lambda ticker: SimpleNamespace(
                history=lambda **kwargs: pd.DataFrame(
                    {"Close": [10, 12]},
                    index=pd.DatetimeIndex(["2024-01-01", "2024-01-02"], name="Date"),
                ),
                fast_info={"currency": "EUR"},
            ),
        )

        returns = analyzer._load_benchmark_returns()

        assert returns.iloc[0] == pytest.approx(0.2)
        assert BENCHMARK_TICKER.startswith("^")
        assert BENCHMARK_CURRENCY == "USD"

    def test_latest_asset_values_and_weights_use_current_values(self):
        analyzer = PortfolioAnalyzer.__new__(PortfolioAnalyzer)
        assets = {
            "A": SimpleNamespace(price_history=pd.DataFrame({"Value": [20]})),
            "B": SimpleNamespace(price_history=pd.DataFrame({"Value": [30]})),
        }
        prices = pd.DataFrame({"A": [10, 11], "B": [20, 21]})
        analyzer.portfolio = SimpleNamespace(
            content=assets,
            build_combined_price_dataframe=lambda: prices,
        )

        weights, returns = analyzer._compute_weights_and_asset_returns()

        assert analyzer._get_latest_asset_values() == {"A": 20, "B": 30}
        assert weights.tolist() == pytest.approx([0.4, 0.6])
        assert list(returns.columns) == ["A", "B"]

    def test_fill_annualized_returns_sets_value_or_insufficient_history_text(self):
        analyzer = PortfolioAnalyzer.__new__(PortfolioAnalyzer)
        analyzer.interpreter = AnalysisInterpreter()
        analyzer.portfolio = SimpleNamespace(annualized_returns={"10y": 6.234})
        result = AnalysisResult()

        analyzer._fill_annualized_return(result)

        assert result.annualized_return_10y == 6.23
        assert "solid growth" in result.annualized_return_10y_text
        assert "Not enough history" in result.annualized_return_5y_text

    def test_fill_beta_alpha_and_information_ratio(self):
        analyzer = PortfolioAnalyzer.__new__(PortfolioAnalyzer)
        analyzer.interpreter = AnalysisInterpreter()
        aligned = pd.DataFrame(
            {
                "portfolio": [0.01, 0.02, -0.01, 0.03],
                "benchmark": [0.005, 0.01, -0.005, 0.015],
            }
        )
        result = AnalysisResult()

        analyzer._fill_beta_alpha(result, aligned)
        analyzer._fill_information_ratio(result, aligned)

        assert result.beta == pytest.approx(2.0)
        assert result.beta_text
        assert result.alpha_text
        assert result.information_ratio_text

    def test_fill_sharpe_var_and_cvar(self):
        analyzer = PortfolioAnalyzer.__new__(PortfolioAnalyzer)
        analyzer.interpreter = AnalysisInterpreter()
        returns = pd.Series(
            [0.01, -0.03, 0.02, -0.01, 0.04, 0.01],
            index=pd.to_datetime(
                ["2024-01-02", "2024-01-10", "2024-02-02", "2024-02-10", "2024-03-02", "2024-03-10"]
            ),
        )
        result = AnalysisResult()

        analyzer._fill_sharpe(result, returns)
        analyzer._fill_var(result, returns)
        analyzer._fill_cvar(result, returns)

        assert result.sharpe_text
        assert result.var_text
        assert result.cvar_text

    def test_diversification_and_effective_bets(self):
        analyzer = PortfolioAnalyzer.__new__(PortfolioAnalyzer)
        analyzer.interpreter = AnalysisInterpreter()
        analyzer.portfolio = SimpleNamespace(correlation_matrix=pd.DataFrame(np.eye(2)))
        returns = pd.DataFrame({"A": [0.01, 0.02, -0.01], "B": [0.002, 0.018, -0.005]})
        result = AnalysisResult(num_assets=2)

        analyzer._fill_diversification(result, np.array([0.5, 0.5]), returns)
        analyzer._fill_effective_bets(result)

        assert result.diversification_ratio > 1
        assert result.effective_bets == 2

    def test_risk_and_return_contributions_are_populated(self):
        analyzer = PortfolioAnalyzer.__new__(PortfolioAnalyzer)
        analyzer.interpreter = AnalysisInterpreter()
        result = AnalysisResult()
        asset_returns = pd.DataFrame(
            {
                "A": [0.01, -0.01, 0.02, -0.02],
                "B": [-0.02, 0.02, -0.01, 0.01],
            }
        )
        weights = np.array([0.5, 0.5])

        analyzer._fill_risk_contributions(result, weights, asset_returns)
        analyzer._fill_return_contributions(result, weights, asset_returns)

        assert sum(result.risk_contributions.values()) == pytest.approx(100)
        assert set(result.return_contributions) == {"A", "B"}
        assert result.risk_contributions_text
        assert result.return_contributions_text

    def test_alignment_drops_nonoverlapping_dates(self):
        analyzer = PortfolioAnalyzer.__new__(PortfolioAnalyzer)
        portfolio = pd.Series([0.1, 0.2], index=["a", "b"])
        benchmark = pd.Series([0.3, 0.4], index=["b", "c"])

        aligned = analyzer._align_return_series(portfolio, benchmark)

        assert aligned.index.tolist() == ["b"]
        assert aligned.iloc[0].tolist() == [0.2, 0.3]

    def test_annualize_return_handles_empty_and_loss_series(self):
        analyzer = PortfolioAnalyzer.__new__(PortfolioAnalyzer)

        assert analyzer._annualize_return(pd.Series(dtype=float)) == 0
        assert analyzer._annualize_return(pd.Series([-1.1])) == -1

    def test_max_drawdown_and_duration(self):
        analyzer = PortfolioAnalyzer.__new__(PortfolioAnalyzer)
        analyzer.interpreter = AnalysisInterpreter()
        analyzer.portfolio = SimpleNamespace(
            history=pd.DataFrame(
                {
                    "Date": pd.to_datetime(["2024-01-01", "2024-01-03", "2024-01-06"]).date,
                    "Value": [100, 80, 90],
                }
            )
        )
        result = AnalysisResult()

        analyzer._fill_max_drawdown(result)

        assert result.max_drawdown == -20
        assert result.max_drawdown_duration_days == 3

    def test_fill_portfolio_weights_as_percentages(self):
        analyzer = PortfolioAnalyzer.__new__(PortfolioAnalyzer)
        result = AnalysisResult()

        analyzer._fill_portfolio_weights(result, np.array([0.25, 0.75]), pd.DataFrame(columns=["A", "B"]))

        assert result.portfolio_weights == {"A": 25.0, "B": 75.0}

    def test_compute_portfolio_daily_returns(self):
        analyzer = PortfolioAnalyzer.__new__(PortfolioAnalyzer)
        analyzer.portfolio = SimpleNamespace(
            history=pd.DataFrame(
                {
                    "Date": [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)],
                    "Value": [100, 110, 99],
                }
            )
        )

        assert analyzer._get_portfolio_daily_returns().tolist() == pytest.approx([0.1, -0.1])

    def test_monthly_resampling_compounds_daily_returns(self):
        analyzer = PortfolioAnalyzer.__new__(PortfolioAnalyzer)
        daily = pd.Series([0.1, 0.1], index=pd.to_datetime(["2024-01-02", "2024-01-03"]))

        monthly = analyzer._resample_to_monthly(daily)

        assert monthly.iloc[0] == pytest.approx(0.21)

    def test_analyze_integrates_all_portfolio_metrics(self, monkeypatch):
        dates = pd.bdate_range("2022-01-01", periods=520).date
        price_a = np.linspace(80, 120, len(dates)) + np.sin(np.arange(len(dates)))
        price_b = np.linspace(120, 90, len(dates)) + np.cos(np.arange(len(dates)))
        portfolio = SimpleNamespace(
            content={"A": object(), "B": object()},
            history=pd.DataFrame(
                {"Date": dates, "Value": price_a * 0.6 + price_b * 0.4}
            ),
            annualized_returns={"10y": 4.5, "5y": 6.5},
            correlation_matrix=pd.DataFrame(
                np.corrcoef(np.diff(price_a), np.diff(price_b)), index=["A", "B"], columns=["A", "B"]
            ),
            build_combined_price_dataframe=lambda: pd.DataFrame({"A": price_a, "B": price_b}),
        )
        portfolio.content = {
            "A": SimpleNamespace(price_history=pd.DataFrame({"Value": [price_a[-1]]})),
            "B": SimpleNamespace(price_history=pd.DataFrame({"Value": [price_b[-1]]})),
        }
        analyzer = PortfolioAnalyzer(portfolio)
        benchmark_returns = pd.Series(
            np.diff(np.log(np.linspace(100, 150, len(dates)))),
            index=pd.Index(dates[1:]),
        )
        monkeypatch.setattr(analyzer, "_load_benchmark_returns", lambda: benchmark_returns)

        result = analyzer.analyze()

        assert result.num_assets == 2
        assert result.portfolio_weights.keys() == {"A", "B"}
        assert result.risk_contributions
        assert result.return_contributions
