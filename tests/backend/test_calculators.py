from datetime import date

import pandas as pd
import pytest
import numpy as np

from backend.globals.calculators import ReturnsCalculator


class TestReturnsCalculator:
    def test_calculate_percentage_change(self):
        calculator = ReturnsCalculator()
        calculator.history = pd.DataFrame(
            {"Date": [date(2024, 1, 1), date(2024, 1, 2)], "Value": [100, 125]}
        )
        calculator.source_column = "Value"

        assert calculator._calculate_percentage_change(date(2024, 1, 2), date(2024, 1, 1)) == 25

    def test_calculate_annualized_percentage_change(self):
        calculator = ReturnsCalculator()
        calculator.history = pd.DataFrame(
            {"Date": [date(2022, 1, 1), date(2024, 1, 1)], "Value": [100, 121]}
        )
        calculator.source_column = "Value"

        assert calculator._calculate_annualized_percentage_change(date(2024, 1, 1), date(2022, 1, 1)) == pytest.approx(10, abs=0.15)

    def test_reference_dates_use_last_available_date_before_cutoff(self):
        calculator = ReturnsCalculator()
        calculator.history = pd.DataFrame(
            {"Date": [date(2023, 11, 30), date(2023, 12, 1), date(2024, 1, 2)]}
        )

        assert calculator._get_reference_date_directly(date(2023, 12, 31)) == date(2023, 12, 1)
        assert calculator._get_reference_date_directly(date(2023, 11, 1)) is None

    def test_calculate_returns_omits_unavailable_periods(self):
        history = pd.DataFrame(
            {"Date": [date(2024, 1, 1), date(2024, 2, 1)], "Value": [10, 12]}
        )

        assert ReturnsCalculator().calculate_returns(history, "Value") == {"1m": 20.0, "ytd": 20.0}

    def test_annualized_returns_cover_periods_with_enough_history(self):
        dates = pd.bdate_range("2018-01-01", "2024-01-01").date
        history = pd.DataFrame(
            {"Date": dates, "Value": [100 + index for index in range(len(dates))]}
        )

        actual = ReturnsCalculator().calculate_annualized_returns(history, "Value")

        assert set(actual).issuperset({"1y", "3y", "5y"})
        assert "10y" not in actual

    def test_calculate_volatility_matches_sample_standard_deviation(self):
        history = pd.DataFrame(
            {
                "Date": pd.bdate_range("2020-01-01", periods=5).date,
                "Value": [100, 102, 99, 103, 101],
            }
        )
        calculator = ReturnsCalculator()
        calculator.history = history
        calculator.source_column = "Value"

        actual = calculator._calculate_volatility_for_a_given_period(date(2020, 1, 1))
        expected = history["Value"].pct_change().dropna().std() * (252**0.5) * 100

        assert actual == pytest.approx(expected)

    def test_calculate_volatility_omits_periods_without_exact_reference_date(self):
        history = pd.DataFrame(
            {
                "Date": pd.bdate_range("2020-01-01", periods=10).date,
                "Value": range(10, 20),
            }
        )

        actual = ReturnsCalculator().calculate_volatility(history, "Value")

        assert actual == {}

    def test_zero_reference_value_produces_infinity(self):
        calculator = ReturnsCalculator()
        calculator.history = pd.DataFrame(
            {"Date": [date(2024, 1, 1), date(2024, 1, 2)], "Value": [0, 10]}
        )
        calculator.source_column = "Value"

        with pytest.warns(RuntimeWarning, match="divide by zero"):
            change = calculator._calculate_percentage_change(date(2024, 1, 2), date(2024, 1, 1))
        assert np.isinf(change)
